from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .compiler import (
    OCLOUD_POLICY_FILENAME,
    ORAN_POLICY_FILENAME,
    TRANSPORT_POLICY_FILENAME,
)
from .io import load_json_file, load_yaml_file
from .models import TopologyModel
from .validation import DocumentValidationError, validate_topology_document


EXPECTED_WORKLOADS = {"slice_a_workload", "slice_b_workload", "shared_auth_log"}
EXPECTED_TRANSPORT_SEGMENTS = {
    "tn_segment_slice_a",
    "tn_segment_slice_b",
    "tn_segment_shared",
}
EXPECTED_ALLOWED_TRANSPORT = {
    ("tn_segment_slice_a", "tn_segment_shared"),
    ("tn_segment_slice_b", "tn_segment_shared"),
}
EXPECTED_FORBIDDEN_TRANSPORT = {
    ("tn_segment_slice_a", "tn_segment_slice_b"),
    ("tn_segment_slice_b", "tn_segment_slice_a"),
}
EXPECTED_ALLOWED_FLOWS = {
    ("slice_a_workload", "shared_auth_log"),
    ("slice_b_workload", "shared_auth_log"),
}
EXPECTED_FORBIDDEN_FLOWS = {
    ("slice_a_workload", "slice_b_workload"),
    ("slice_b_workload", "slice_a_workload"),
}
EXPECTED_ORAN_SLICES = {"slice_a", "slice_b"}


class GraphBuildError(DocumentValidationError):
    """Raised when the graph model cannot be built from bounded inputs."""


@dataclass(frozen=True)
class GraphEdge:
    source: str
    destination: str
    provenance: tuple[str, ...]

    def to_provenance_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "destination": self.destination,
            "provenance": list(self.provenance),
        }


@dataclass(frozen=True)
class DirectedLabelledGraph:
    nodes: tuple[str, ...]
    edges: tuple[GraphEdge, ...]
    adjacency: dict[str, tuple[str, ...]]
    edge_provenance: dict[tuple[str, str], tuple[str, ...]]
    node_layers: dict[str, str]
    workload_nodes: tuple[str, ...]


@dataclass(frozen=True)
class PolicyBundle:
    transport_policy: dict[str, Any]
    ocloud_policy: dict[str, Any]
    oran_policy: dict[str, Any]


def load_compiled_policy_bundle(policies_directory: str | Path) -> PolicyBundle:
    """Load the three bounded compiled policy artefacts."""
    directory = Path(policies_directory)
    return PolicyBundle(
        transport_policy=load_json_file(directory / TRANSPORT_POLICY_FILENAME),
        ocloud_policy=load_yaml_file(directory / OCLOUD_POLICY_FILENAME),
        oran_policy=load_json_file(directory / ORAN_POLICY_FILENAME),
    )


def build_graph_from_paths(
    topology_path: str | Path,
    policies_directory: str | Path,
) -> DirectedLabelledGraph:
    """Load the bounded inputs from disk and build the surviving communication graph."""
    topology_document = load_yaml_file(topology_path)
    policy_bundle = load_compiled_policy_bundle(policies_directory)
    return build_graph_from_documents(
        topology_document=topology_document,
        transport_policy=policy_bundle.transport_policy,
        ocloud_policy=policy_bundle.ocloud_policy,
        oran_policy=policy_bundle.oran_policy,
    )


def build_graph_from_documents(
    topology_document: dict[str, Any],
    transport_policy: dict[str, Any],
    ocloud_policy: dict[str, Any],
    oran_policy: dict[str, Any],
) -> DirectedLabelledGraph:
    """Construct the bounded directed labelled graph G=(V,E,lambda)."""
    topology_model = validate_topology_document(topology_document)
    _validate_transport_policy(transport_policy)
    _validate_ocloud_policy(ocloud_policy)
    oran_scope = _validate_oran_policy(oran_policy, topology_model)

    node_map = {node.node_id: node for node in topology_model.nodes}
    allowed_transport = {
        (entry["source"], entry["destination"])
        for entry in transport_policy["allowed_directed_adjacencies"]
    }
    allowed_flows = {
        (entry["source"], entry["destination"])
        for entry in ocloud_policy["allowed_flows"]
    }

    edge_records: dict[tuple[str, str], GraphEdge] = {}
    for edge in sorted(topology_model.edges, key=lambda item: (item.source, item.destination)):
        if edge.relation == "governs":
            continue

        if edge.relation == "attached_to":
            node = node_map[edge.source]
            slice_scope = oran_scope[node.slice_id]
            if (
                node.layer == "workload"
                and node.transport_segment == edge.destination
                and (edge.source, "shared_auth_log") in allowed_flows
                and slice_scope["transport_segment"] == edge.destination
            ):
                edge_records[(edge.source, edge.destination)] = GraphEdge(
                    source=edge.source,
                    destination=edge.destination,
                    provenance=(
                        "topology",
                        "ocloud_microsegmentation",
                        "oran_slice_policy",
                    ),
                )
                continue
            raise GraphBuildError(
                f"topology edge {edge.source} -> {edge.destination} does not survive policy "
                "application"
            )

        if edge.relation == "routed_via":
            if (edge.source, edge.destination) in allowed_transport:
                edge_records[(edge.source, edge.destination)] = GraphEdge(
                    source=edge.source,
                    destination=edge.destination,
                    provenance=("topology", "transport_policy", "oran_slice_policy"),
                )
                continue
            raise GraphBuildError(
                f"transport edge {edge.source} -> {edge.destination} is not permitted by the "
                "compiled transport policy"
            )

        if edge.relation == "terminates_at":
            if (
                edge.source == "tn_segment_shared"
                and edge.destination == "shared_auth_log"
                and not ocloud_policy["shared_service_metadata"]["transit_allowed"]
            ):
                edge_records[(edge.source, edge.destination)] = GraphEdge(
                    source=edge.source,
                    destination=edge.destination,
                    provenance=(
                        "topology",
                        "ocloud_microsegmentation",
                        "oran_slice_policy",
                    ),
                )
                continue
            raise GraphBuildError(
                f"shared-service edge {edge.source} -> {edge.destination} violates the bounded "
                "shared_auth_log policy"
            )

        raise GraphBuildError(f"unsupported topology relation '{edge.relation}' in bounded model")

    if any(edge.source == "shared_auth_log" for edge in edge_records.values()):
        raise GraphBuildError("shared_auth_log must be terminal in the surviving graph")

    nodes = tuple(sorted(node_map))
    adjacency = _build_adjacency(nodes, edge_records.values())
    node_layers = {node.node_id: node.layer for node in topology_model.nodes}
    workload_nodes = tuple(
        sorted(node.node_id for node in topology_model.nodes if node.layer == "workload")
    )
    edge_provenance = {
        (edge.source, edge.destination): edge.provenance
        for edge in sorted(edge_records.values(), key=lambda item: (item.source, item.destination))
    }

    return DirectedLabelledGraph(
        nodes=nodes,
        edges=tuple(
            sorted(edge_records.values(), key=lambda item: (item.source, item.destination))
        ),
        adjacency=adjacency,
        edge_provenance=edge_provenance,
        node_layers=node_layers,
        workload_nodes=workload_nodes,
    )


def _validate_transport_policy(document: dict[str, Any]) -> None:
    if document.get("policy_type") != "transport_segmentation":
        raise GraphBuildError("transport policy must declare policy_type=transport_segmentation")
    if document.get("default_action") != "deny":
        raise GraphBuildError("transport policy must declare default_action=deny")

    transport_segments = set(document.get("transport_segments", []))
    if transport_segments != EXPECTED_TRANSPORT_SEGMENTS:
        raise GraphBuildError("transport policy must contain the three bounded transport segments")

    allowed = {
        (entry["source"], entry["destination"])
        for entry in document.get("allowed_directed_adjacencies", [])
    }
    if allowed != EXPECTED_ALLOWED_TRANSPORT:
        raise GraphBuildError(
            "transport policy must allow only slice-to-shared transport adjacencies"
        )

    forbidden = {
        (entry["source"], entry["destination"])
        for entry in document.get("forbidden_directed_adjacencies", [])
    }
    if not EXPECTED_FORBIDDEN_TRANSPORT.issubset(forbidden):
        raise GraphBuildError(
            "transport policy must forbid both cross-slice transport adjacencies"
        )


def _validate_ocloud_policy(document: dict[str, Any]) -> None:
    if document.get("policy_type") != "ocloud_microsegmentation":
        raise GraphBuildError(
            "O-Cloud policy must declare policy_type=ocloud_microsegmentation"
        )
    if document.get("default_deny") is not True:
        raise GraphBuildError("O-Cloud policy must declare default_deny=true")

    workloads = set(document.get("workloads", []))
    if workloads != EXPECTED_WORKLOADS:
        raise GraphBuildError("O-Cloud policy must cover the bounded workload set")

    allowed_flows = {
        (entry["source"], entry["destination"])
        for entry in document.get("allowed_flows", [])
    }
    if allowed_flows != EXPECTED_ALLOWED_FLOWS:
        raise GraphBuildError(
            "O-Cloud policy must allow only the bounded workload-to-shared_auth_log flows"
        )

    forbidden_flows = {
        (entry["source"], entry["destination"])
        for entry in document.get("forbidden_flows", [])
    }
    if not EXPECTED_FORBIDDEN_FLOWS.issubset(forbidden_flows):
        raise GraphBuildError("O-Cloud policy must forbid both cross-slice workload flows")

    metadata = document.get("shared_service_metadata", {})
    if metadata.get("name") != "shared_auth_log":
        raise GraphBuildError("O-Cloud policy must describe shared_auth_log metadata")
    if metadata.get("transit_allowed") is not False:
        raise GraphBuildError("shared_auth_log must remain terminal in O-Cloud policy metadata")


def _validate_oran_policy(
    document: dict[str, Any], topology_model: TopologyModel
) -> dict[str, dict[str, Any]]:
    if document.get("policy_type") != "oran_slice_policy":
        raise GraphBuildError("O-RAN policy must declare policy_type=oran_slice_policy")

    entries = document.get("slice_policies", [])
    scope_map = {entry["slice_id"]: entry for entry in entries}
    if set(scope_map) != EXPECTED_ORAN_SLICES:
        raise GraphBuildError("O-RAN policy must contain exactly one scoped entry per slice")

    node_map = {node.node_id: node for node in topology_model.nodes}
    for slice_id, entry in scope_map.items():
        policy_node_id = f"oran_policy_{slice_id}"
        if policy_node_id not in node_map:
            raise GraphBuildError(f"missing O-RAN policy scope for {slice_id}")
        if entry.get("transport_segment") not in EXPECTED_TRANSPORT_SEGMENTS:
            raise GraphBuildError(f"O-RAN policy for {slice_id} is missing a valid transport segment")

        permitted_exception = entry.get("permitted_shared_service_exception", {})
        if permitted_exception.get("service_id") != "shared_auth_log":
            raise GraphBuildError(
                f"O-RAN policy for {slice_id} must reference shared_auth_log as the permitted exception"
            )
        if permitted_exception.get("endpoint") != "shared_auth_log":
            raise GraphBuildError(
                f"O-RAN policy for {slice_id} must target the shared_auth_log endpoint"
            )
        if entry.get("forbidden_peer_slice") != _peer_slice_id(slice_id):
            raise GraphBuildError(
                f"O-RAN policy for {slice_id} must forbid the peer slice {_peer_slice_id(slice_id)}"
            )

    return scope_map


def _build_adjacency(
    nodes: tuple[str, ...], edges: Any
) -> dict[str, tuple[str, ...]]:
    adjacency_lists: dict[str, list[str]] = {node: [] for node in nodes}
    for edge in edges:
        adjacency_lists[edge.source].append(edge.destination)

    return {
        node: tuple(sorted(destinations))
        for node, destinations in adjacency_lists.items()
    }


def _peer_slice_id(slice_id: str) -> str:
    return "slice_b" if slice_id == "slice_a" else "slice_a"
