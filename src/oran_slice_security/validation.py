from __future__ import annotations

from typing import Any

from jsonschema import Draft202012Validator

from .models import IntentModel, TopologyModel


EXPECTED_SLICE_IDS = {"slice_a", "slice_b"}
EXPECTED_SHARED_SERVICE_ID = "shared_auth_log"
EXPECTED_DIRECTION = "source_to_destination"
REQUIRED_TOPOLOGY_NODES = {
    "slice_a_workload",
    "slice_b_workload",
    "tn_segment_slice_a",
    "tn_segment_slice_b",
    "tn_segment_shared",
    "shared_auth_log",
    "oran_policy_slice_a",
    "oran_policy_slice_b",
}
REQUIRED_TOPOLOGY_CONTROLS = {
    "inter_slice",
    "transport_cross_slice",
    "shared_service_transit",
}
EXPECTED_NODE_PROPERTIES = {
    "slice_a_workload": {
        "layer": "workload",
        "slice_id": "slice_a",
        "namespace_required": True,
        "transport_segment": "tn_segment_slice_a",
    },
    "slice_b_workload": {
        "layer": "workload",
        "slice_id": "slice_b",
        "namespace_required": True,
        "transport_segment": "tn_segment_slice_b",
    },
    "tn_segment_slice_a": {
        "layer": "transport",
        "transport_segment": "tn_segment_slice_a",
    },
    "tn_segment_slice_b": {
        "layer": "transport",
        "transport_segment": "tn_segment_slice_b",
    },
    "tn_segment_shared": {
        "layer": "transport",
        "transport_segment": "tn_segment_shared",
    },
    "shared_auth_log": {
        "layer": "shared_service",
        "namespace_required": True,
        "transport_segment": "tn_segment_shared",
        "transit_allowed": False,
    },
    "oran_policy_slice_a": {
        "layer": "policy",
        "slice_id": "slice_a",
        "namespace_required": True,
    },
    "oran_policy_slice_b": {
        "layer": "policy",
        "slice_id": "slice_b",
        "namespace_required": True,
    },
}


class DocumentValidationError(ValueError):
    """Base class for repository validation errors."""


class SchemaValidationError(DocumentValidationError):
    """Raised when a document fails JSON Schema validation."""


class SemanticValidationError(DocumentValidationError):
    """Raised when a schema-valid intent violates thesis constraints."""


class TopologyValidationError(DocumentValidationError):
    """Raised when a topology fixture violates thesis constraints."""


def validate_intent_schema(document: dict[str, Any], schema: dict[str, Any]) -> None:
    """Validate a YAML-loaded intent against the JSON Schema."""
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    errors = sorted(
        validator.iter_errors(document),
        key=lambda error: (tuple(str(part) for part in error.absolute_path), error.message),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise SchemaValidationError(f"{location}: {error.message}")


def validate_intent_semantics(document: IntentModel | dict[str, Any]) -> IntentModel:
    """Validate thesis-specific semantic constraints for the bounded intent."""
    model = _coerce_intent(document)

    slice_ids = {slice_definition.slice_id for slice_definition in model.slices}
    if len(model.slices) != 2 or slice_ids != EXPECTED_SLICE_IDS:
        raise SemanticValidationError(
            "exactly two slices named slice_a and slice_b are required"
        )

    for slice_definition in model.slices:
        if not slice_definition.transport_segment.strip():
            raise SemanticValidationError(
                f"slice {slice_definition.slice_id} is missing a transport segment"
            )

    workload_ownership: dict[str, str] = {}
    slice_endpoints: dict[str, list[str]] = {"slice_a": [], "slice_b": []}
    for slice_definition in model.slices:
        for workload in slice_definition.workloads:
            if workload.endpoint in workload_ownership:
                owner = workload_ownership[workload.endpoint]
                raise SemanticValidationError(
                    f"duplicate workload endpoint '{workload.endpoint}' across {owner} and "
                    f"{slice_definition.slice_id}"
                )
            workload_ownership[workload.endpoint] = slice_definition.slice_id
            slice_endpoints[slice_definition.slice_id].append(workload.endpoint)

    if len(model.shared_services) != 1:
        raise SemanticValidationError(
            "exactly one shared service named shared_auth_log is required"
        )

    shared_service = model.shared_services[0]
    if shared_service.service_id != EXPECTED_SHARED_SERVICE_ID:
        raise SemanticValidationError(
            "exactly one shared service named shared_auth_log is required"
        )
    if shared_service.transit_allowed:
        raise SemanticValidationError("shared_auth_log must declare transit_allowed=false")

    default_deny = model.access_policies.default_deny
    if not (
        default_deny.inter_slice
        and default_deny.intra_slice_unspecified
        and default_deny.shared_service_transit
    ):
        raise SemanticValidationError(
            "default-deny posture must set inter_slice, intra_slice_unspecified, and "
            "shared_service_transit to true"
        )

    shared_service_endpoints = {service.endpoint for service in model.shared_services}
    allowed_pairs: set[tuple[str, str]] = set()
    for rule in model.access_policies.allowed_shared_service_access:
        _validate_rule_direction(rule.direction, rule.source, rule.destination)
        if rule.source not in workload_ownership:
            raise SemanticValidationError(
                f"unknown workload source '{rule.source}' in allowed shared-service access"
            )
        if rule.destination not in shared_service_endpoints:
            raise SemanticValidationError(
                f"allowed shared-service access must target a shared service endpoint, got "
                f"'{rule.destination}'"
            )
        allowed_pairs.add((rule.source, rule.destination))

    forbidden_pairs: set[tuple[str, str]] = set()
    for rule in model.access_policies.forbidden_inter_slice_communication:
        _validate_rule_direction(rule.direction, rule.source, rule.destination)
        forbidden_pairs.add((rule.source, rule.destination))

    conflicts = allowed_pairs & forbidden_pairs
    if conflicts:
        source, destination = sorted(conflicts)[0]
        raise SemanticValidationError(
            f"conflicting allow and deny rule for {source} -> {destination}"
        )

    required_forbidden_pairs = {
        (source, destination)
        for source in slice_endpoints["slice_a"]
        for destination in slice_endpoints["slice_b"]
    }
    required_forbidden_pairs.update(
        {
            (source, destination)
            for source in slice_endpoints["slice_b"]
            for destination in slice_endpoints["slice_a"]
        }
    )
    if not required_forbidden_pairs.issubset(forbidden_pairs):
        raise SemanticValidationError(
            "missing forbidden directions between slice_a and slice_b"
        )

    return model


def validate_intent_document(
    document: dict[str, Any], schema: dict[str, Any]
) -> IntentModel:
    """Run schema and semantic validation for an intent document."""
    validate_intent_schema(document, schema)
    return validate_intent_semantics(document)


def validate_topology_document(document: TopologyModel | dict[str, Any]) -> TopologyModel:
    """Validate the bounded base topology and negative controls."""
    model = _coerce_topology(document)
    node_map: dict[str, Any] = {}

    for node in model.nodes:
        if node.node_id in node_map:
            raise TopologyValidationError(f"duplicate topology node '{node.node_id}'")
        node_map[node.node_id] = node

    missing_nodes = REQUIRED_TOPOLOGY_NODES - set(node_map)
    if missing_nodes:
        missing = ", ".join(sorted(missing_nodes))
        raise TopologyValidationError(f"topology is missing required nodes: {missing}")

    for node_id, expected in EXPECTED_NODE_PROPERTIES.items():
        _validate_expected_node(node_map[node_id], expected)

    if not model.default_deny.enforced:
        raise TopologyValidationError("topology must declare default_deny.enforced=true")
    if not REQUIRED_TOPOLOGY_CONTROLS.issubset(set(model.default_deny.controls)):
        raise TopologyValidationError(
            "topology default-deny controls must include inter_slice, "
            "transport_cross_slice, and shared_service_transit"
        )

    edge_pairs: set[tuple[str, str]] = set()
    for edge in model.edges:
        if edge.source not in node_map or edge.destination not in node_map:
            raise TopologyValidationError(
                f"edge {edge.source} -> {edge.destination} references an unknown node"
            )
        edge_pairs.add((edge.source, edge.destination))

    if (
        ("slice_a_workload", "slice_b_workload") in edge_pairs
        or ("slice_b_workload", "slice_a_workload") in edge_pairs
    ):
        raise TopologyValidationError("direct cross-slice workload edge is not allowed")

    if (
        ("slice_a_workload", "tn_segment_slice_b") in edge_pairs
        or ("slice_b_workload", "tn_segment_slice_a") in edge_pairs
    ):
        raise TopologyValidationError("workload connected to the wrong transport segment")

    if any(edge.source == EXPECTED_SHARED_SERVICE_ID for edge in model.edges):
        raise TopologyValidationError(
            "shared_auth_log must be terminal and cannot originate topology edges"
        )

    return model


def _coerce_intent(document: IntentModel | dict[str, Any]) -> IntentModel:
    if isinstance(document, IntentModel):
        return document
    return IntentModel.from_dict(document)


def _coerce_topology(document: TopologyModel | dict[str, Any]) -> TopologyModel:
    if isinstance(document, TopologyModel):
        return document
    return TopologyModel.from_dict(document)


def _validate_rule_direction(direction: str, source: str, destination: str) -> None:
    if direction != EXPECTED_DIRECTION:
        raise SemanticValidationError(
            f"ambiguous direction '{direction}' for rule {source} -> {destination}"
        )


def _validate_expected_node(node: Any, expected: dict[str, Any]) -> None:
    if node.layer != expected["layer"]:
        raise TopologyValidationError(
            f"node '{node.node_id}' must set layer='{expected['layer']}'"
        )

    expected_slice_id = expected.get("slice_id")
    if expected_slice_id is not None and node.slice_id != expected_slice_id:
        raise TopologyValidationError(
            f"node '{node.node_id}' must set slice_id='{expected_slice_id}'"
        )

    if expected.get("namespace_required") and not node.namespace:
        raise TopologyValidationError(f"node '{node.node_id}' must declare a namespace")

    expected_transport = expected.get("transport_segment")
    if expected_transport is not None and node.transport_segment != expected_transport:
        raise TopologyValidationError(
            f"node '{node.node_id}' must set transport_segment='{expected_transport}'"
        )

    if "transit_allowed" in expected and node.transit_allowed != expected["transit_allowed"]:
        raise TopologyValidationError("shared_auth_log must declare transit_allowed=false")


validate_topology = validate_topology_document
