from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .graph_builder import DirectedLabelledGraph, GraphEdge


@dataclass(frozen=True)
class MultisliceVerifierFixture:
    """Synthetic N-slice input for a bounded verifier-layer scale study."""

    slice_count: int
    graph: DirectedLabelledGraph
    queries: dict[str, Any]
    rule_equivalent_count: int

    @property
    def required_query_count(self) -> int:
        return len(self.queries["required_reachable"])

    @property
    def forbidden_query_count(self) -> int:
        return len(self.queries["forbidden_unreachable"])

    @property
    def terminal_query_count(self) -> int:
        return len(self.queries["terminal_services"])

    @property
    def total_check_count(self) -> int:
        """Return the number of reported property criteria."""
        return (
            self.required_query_count
            + self.forbidden_query_count
            + self.terminal_query_count
        )

    @property
    def path_search_invocation_count(self) -> int:
        """Return the number of breadth-first path searches per verification run."""
        return (
            self.required_query_count
            + self.forbidden_query_count
            + self.terminal_query_count * len(self.graph.workload_nodes)
        )


def build_multislice_verifier_fixture(slice_count: int) -> MultisliceVerifierFixture:
    """Create a deterministic verifier-only N-slice scenario.

    Each slice has one workload, one dedicated transport segment, and one
    policy-scope node. Every workload retains a directed route to one shared
    terminal service. Ordered cross-slice workload and transport routes are
    forbidden. The generator does not claim that the current intent schema or
    compiler supports N slices.
    """

    if slice_count < 2:
        raise ValueError("slice_count must be at least 2")

    slice_ids = tuple(f"slice_{index:03d}" for index in range(1, slice_count + 1))
    workloads = tuple(f"{slice_id}_workload" for slice_id in slice_ids)
    segments = tuple(f"tn_segment_{slice_id}" for slice_id in slice_ids)
    policy_nodes = tuple(f"oran_policy_{slice_id}" for slice_id in slice_ids)
    shared_segment = "tn_segment_shared"
    shared_service = "shared_auth_log"

    nodes = tuple(sorted(workloads + segments + policy_nodes + (shared_segment, shared_service)))
    node_layers = {
        **{node: "workload" for node in workloads},
        **{node: "transport" for node in segments},
        **{node: "policy" for node in policy_nodes},
        shared_segment: "transport",
        shared_service: "shared_service",
    }

    edges: list[GraphEdge] = []
    for workload, segment in zip(workloads, segments):
        edges.append(
            GraphEdge(
                source=workload,
                destination=segment,
                provenance=("synthetic_topology", "multislice_policy"),
            )
        )
        edges.append(
            GraphEdge(
                source=segment,
                destination=shared_segment,
                provenance=("synthetic_topology", "multislice_policy"),
            )
        )
    edges.append(
        GraphEdge(
            source=shared_segment,
            destination=shared_service,
            provenance=("synthetic_topology", "terminal_service_policy"),
        )
    )
    edge_tuple = tuple(sorted(edges, key=lambda edge: (edge.source, edge.destination)))

    adjacency_lists: dict[str, list[str]] = {node: [] for node in nodes}
    for edge in edge_tuple:
        adjacency_lists[edge.source].append(edge.destination)
    adjacency = {
        node: tuple(sorted(destinations))
        for node, destinations in adjacency_lists.items()
    }
    edge_provenance = {
        (edge.source, edge.destination): edge.provenance for edge in edge_tuple
    }
    graph = DirectedLabelledGraph(
        nodes=nodes,
        edges=edge_tuple,
        adjacency=adjacency,
        edge_provenance=edge_provenance,
        node_layers=node_layers,
        workload_nodes=tuple(sorted(workloads)),
    )

    required = [
        {"source": workload, "destination": shared_service}
        for workload in workloads
    ]
    forbidden: list[dict[str, str]] = []
    for source_index in range(slice_count):
        for destination_index in range(slice_count):
            if source_index == destination_index:
                continue
            forbidden.append(
                {
                    "source": workloads[source_index],
                    "destination": workloads[destination_index],
                }
            )
            forbidden.append(
                {
                    "source": segments[source_index],
                    "destination": segments[destination_index],
                }
            )

    queries = {
        "required_reachable": required,
        "forbidden_unreachable": forbidden,
        "terminal_services": [shared_service],
    }
    rule_equivalent_count = 2 * slice_count * slice_count + slice_count

    return MultisliceVerifierFixture(
        slice_count=slice_count,
        graph=graph,
        queries=queries,
        rule_equivalent_count=rule_equivalent_count,
    )


def build_faulty_multislice_verifier_fixture(
    slice_count: int,
) -> MultisliceVerifierFixture:
    """Add one forbidden cross-slice route for a deterministic negative control."""

    fixture = build_multislice_verifier_fixture(slice_count)
    source = "slice_001_workload"
    destination = "slice_002_workload"
    faulty_edge = GraphEdge(
        source=source,
        destination=destination,
        provenance=("synthetic_negative_control",),
    )
    edges = tuple(
        sorted(
            fixture.graph.edges + (faulty_edge,),
            key=lambda edge: (edge.source, edge.destination),
        )
    )
    adjacency_lists = {
        node: list(destinations)
        for node, destinations in fixture.graph.adjacency.items()
    }
    adjacency_lists[source].append(destination)
    adjacency = {
        node: tuple(sorted(set(destinations)))
        for node, destinations in adjacency_lists.items()
    }
    edge_provenance = dict(fixture.graph.edge_provenance)
    edge_provenance[(source, destination)] = faulty_edge.provenance
    graph = DirectedLabelledGraph(
        nodes=fixture.graph.nodes,
        edges=edges,
        adjacency=adjacency,
        edge_provenance=edge_provenance,
        node_layers=fixture.graph.node_layers,
        workload_nodes=fixture.graph.workload_nodes,
    )
    return MultisliceVerifierFixture(
        slice_count=fixture.slice_count,
        graph=graph,
        queries=fixture.queries,
        rule_equivalent_count=fixture.rule_equivalent_count + 1,
    )
