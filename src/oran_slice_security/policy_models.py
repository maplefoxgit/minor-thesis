from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Provenance:
    intent_identity_field: str
    intent_identity_value: str
    validation_state: str = "validated"

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent_identity_field": self.intent_identity_field,
            "intent_identity_value": self.intent_identity_value,
            "validation_state": self.validation_state,
        }


@dataclass(frozen=True)
class DirectedLink:
    source: str
    destination: str
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "source": self.source,
            "destination": self.destination,
        }
        if self.reason is not None:
            payload["reason"] = self.reason
        return payload


@dataclass(frozen=True)
class SharedServiceMetadata:
    name: str
    transit_allowed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "transit_allowed": self.transit_allowed,
        }


@dataclass(frozen=True)
class TransportPolicy:
    provenance: Provenance
    default_action: str
    transport_segments: tuple[str, ...]
    allowed_directed_adjacencies: tuple[DirectedLink, ...]
    forbidden_directed_adjacencies: tuple[DirectedLink, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_type": "transport_segmentation",
            "default_action": self.default_action,
            "transport_segments": list(self.transport_segments),
            "allowed_directed_adjacencies": [
                adjacency.to_dict() for adjacency in self.allowed_directed_adjacencies
            ],
            "forbidden_directed_adjacencies": [
                adjacency.to_dict() for adjacency in self.forbidden_directed_adjacencies
            ],
            "provenance": self.provenance.to_dict(),
        }


@dataclass(frozen=True)
class OCloudMicrosegmentationPolicy:
    provenance: Provenance
    default_deny: bool
    workloads: tuple[str, ...]
    allowed_flows: tuple[DirectedLink, ...]
    forbidden_flows: tuple[DirectedLink, ...]
    shared_service_metadata: SharedServiceMetadata

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_type": "ocloud_microsegmentation",
            "default_deny": self.default_deny,
            "workloads": list(self.workloads),
            "allowed_flows": [flow.to_dict() for flow in self.allowed_flows],
            "forbidden_flows": [flow.to_dict() for flow in self.forbidden_flows],
            "shared_service_metadata": self.shared_service_metadata.to_dict(),
            "provenance": self.provenance.to_dict(),
        }


@dataclass(frozen=True)
class OranSlicePolicyEntry:
    slice_id: str
    snssai: dict[str, Any]
    ocloud_namespace: str
    transport_segment: str
    permitted_shared_service_exception: dict[str, Any]
    forbidden_peer_slice: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "slice_id": self.slice_id,
            "snssai": self.snssai,
            "ocloud_namespace": self.ocloud_namespace,
            "transport_segment": self.transport_segment,
            "permitted_shared_service_exception": self.permitted_shared_service_exception,
            "forbidden_peer_slice": self.forbidden_peer_slice,
        }


@dataclass(frozen=True)
class OranSlicePolicy:
    provenance: Provenance
    note: str
    slice_policies: tuple[OranSlicePolicyEntry, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_type": "oran_slice_policy",
            "note": self.note,
            "slice_policies": [entry.to_dict() for entry in self.slice_policies],
            "provenance": self.provenance.to_dict(),
        }


@dataclass(frozen=True)
class ManifestEntry:
    artifact: str
    sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact": self.artifact,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class ArtifactManifest:
    generated_policy_artifacts: tuple[ManifestEntry, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_count": len(self.generated_policy_artifacts),
            "generated_policy_artifacts": [
                entry.to_dict() for entry in self.generated_policy_artifacts
            ],
        }
