from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Snssai:
    sst: int
    sd: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Snssai":
        return cls(sst=payload["sst"], sd=payload["sd"])


@dataclass(frozen=True)
class Workload:
    workload_id: str
    endpoint: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Workload":
        return cls(workload_id=payload["workload_id"], endpoint=payload["endpoint"])


@dataclass(frozen=True)
class SliceDefinition:
    slice_id: str
    snssai: Snssai
    ocloud_namespace: str
    transport_segment: str
    workloads: tuple[Workload, ...]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SliceDefinition":
        workloads = tuple(Workload.from_dict(item) for item in payload["workloads"])
        return cls(
            slice_id=payload["slice_id"],
            snssai=Snssai.from_dict(payload["snssai"]),
            ocloud_namespace=payload["ocloud_namespace"],
            transport_segment=payload["transport_segment"],
            workloads=workloads,
        )


@dataclass(frozen=True)
class SharedService:
    service_id: str
    service_type: str
    endpoint: str
    transport_segment: str
    transit_allowed: bool

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SharedService":
        return cls(
            service_id=payload["service_id"],
            service_type=payload["service_type"],
            endpoint=payload["endpoint"],
            transport_segment=payload["transport_segment"],
            transit_allowed=payload["transit_allowed"],
        )


@dataclass(frozen=True)
class CommunicationRule:
    source: str
    destination: str
    direction: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CommunicationRule":
        return cls(
            source=payload["source"],
            destination=payload["destination"],
            direction=payload["direction"],
        )


@dataclass(frozen=True)
class DefaultDenyControls:
    inter_slice: bool
    intra_slice_unspecified: bool
    shared_service_transit: bool

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DefaultDenyControls":
        return cls(
            inter_slice=payload["inter_slice"],
            intra_slice_unspecified=payload["intra_slice_unspecified"],
            shared_service_transit=payload["shared_service_transit"],
        )


@dataclass(frozen=True)
class VerificationRequirements:
    static_graph_reachability_only: bool
    require_two_slice_boundary: bool
    require_shared_auth_log_terminal: bool
    require_default_deny: bool
    require_transport_segment_isolation: bool

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "VerificationRequirements":
        return cls(
            static_graph_reachability_only=payload["static_graph_reachability_only"],
            require_two_slice_boundary=payload["require_two_slice_boundary"],
            require_shared_auth_log_terminal=payload["require_shared_auth_log_terminal"],
            require_default_deny=payload["require_default_deny"],
            require_transport_segment_isolation=payload["require_transport_segment_isolation"],
        )


@dataclass(frozen=True)
class AccessPolicies:
    allowed_shared_service_access: tuple[CommunicationRule, ...]
    forbidden_inter_slice_communication: tuple[CommunicationRule, ...]
    default_deny: DefaultDenyControls

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AccessPolicies":
        allowed = tuple(
            CommunicationRule.from_dict(item)
            for item in payload["allowed_shared_service_access"]
        )
        forbidden = tuple(
            CommunicationRule.from_dict(item)
            for item in payload["forbidden_inter_slice_communication"]
        )
        return cls(
            allowed_shared_service_access=allowed,
            forbidden_inter_slice_communication=forbidden,
            default_deny=DefaultDenyControls.from_dict(payload["default_deny"]),
        )


@dataclass(frozen=True)
class IntentModel:
    thesis_id: str | None
    scenario_id: str | None
    slices: tuple[SliceDefinition, ...]
    shared_services: tuple[SharedService, ...]
    access_policies: AccessPolicies
    verification_requirements: VerificationRequirements

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "IntentModel":
        slices = tuple(SliceDefinition.from_dict(item) for item in payload["slices"])
        shared_services = tuple(
            SharedService.from_dict(item) for item in payload["shared_services"]
        )
        return cls(
            thesis_id=payload.get("thesis_id"),
            scenario_id=payload.get("scenario_id"),
            slices=slices,
            shared_services=shared_services,
            access_policies=AccessPolicies.from_dict(payload["access_policies"]),
            verification_requirements=VerificationRequirements.from_dict(
                payload["verification_requirements"]
            ),
        )


@dataclass(frozen=True)
class TopologyNode:
    node_id: str
    layer: str
    slice_id: str | None = None
    namespace: str | None = None
    transport_segment: str | None = None
    transit_allowed: bool | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TopologyNode":
        return cls(
            node_id=payload["node_id"],
            layer=payload["layer"],
            slice_id=payload.get("slice_id"),
            namespace=payload.get("namespace"),
            transport_segment=payload.get("transport_segment"),
            transit_allowed=payload.get("transit_allowed"),
        )


@dataclass(frozen=True)
class TopologyEdge:
    source: str
    destination: str
    relation: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TopologyEdge":
        return cls(
            source=payload["source"],
            destination=payload["destination"],
            relation=payload["relation"],
        )


@dataclass(frozen=True)
class TopologyDefaultDeny:
    enforced: bool
    controls: tuple[str, ...]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TopologyDefaultDeny":
        return cls(enforced=payload["enforced"], controls=tuple(payload["controls"]))


@dataclass(frozen=True)
class TopologyModel:
    topology_id: str
    nodes: tuple[TopologyNode, ...]
    edges: tuple[TopologyEdge, ...]
    default_deny: TopologyDefaultDeny

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TopologyModel":
        nodes = tuple(TopologyNode.from_dict(item) for item in payload["nodes"])
        edges = tuple(TopologyEdge.from_dict(item) for item in payload["edges"])
        default_deny = TopologyDefaultDeny.from_dict(payload["default_deny"])
        return cls(
            topology_id=payload["topology_id"],
            nodes=nodes,
            edges=edges,
            default_deny=default_deny,
        )
