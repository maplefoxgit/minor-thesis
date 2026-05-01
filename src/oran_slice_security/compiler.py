from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .io import dump_json_file, dump_yaml_file, load_json_file, load_yaml_file, sha256_bytes
from .models import IntentModel, TopologyModel
from .policy_models import (
    ArtifactManifest,
    DirectedLink,
    ManifestEntry,
    OCloudMicrosegmentationPolicy,
    OranSlicePolicy,
    OranSlicePolicyEntry,
    Provenance,
    SharedServiceMetadata,
    TransportPolicy,
)
from .validation import (
    DocumentValidationError,
    validate_intent_document,
    validate_topology_document,
)


TRANSPORT_POLICY_FILENAME = "transport_policy.generated.json"
OCLOUD_POLICY_FILENAME = "ocloud_microsegmentation.generated.yaml"
ORAN_POLICY_FILENAME = "oran_slice_policy.generated.json"
MANIFEST_FILENAME = "manifest.json"
GENERATED_POLICY_FILENAMES = (
    OCLOUD_POLICY_FILENAME,
    ORAN_POLICY_FILENAME,
    TRANSPORT_POLICY_FILENAME,
)
ALL_ALLOWED_OUTPUT_FILENAMES = GENERATED_POLICY_FILENAMES + (MANIFEST_FILENAME,)


class CompilationError(DocumentValidationError):
    """Raised when deterministic policy compilation cannot proceed."""


@dataclass(frozen=True)
class CompiledArtifact:
    filename: str
    format_name: str
    document: dict[str, Any]


def compile_policy_documents(
    schema_document: dict[str, Any],
    intent_document: dict[str, Any],
    topology_document: dict[str, Any],
    output_directory: str | Path,
) -> dict[str, str]:
    """Compile the bounded intent and topology into deterministic policy artefacts."""
    intent_model = validate_intent_document(intent_document, schema_document)
    topology_model = validate_topology_document(topology_document)
    _validate_compiler_preconditions(intent_model, topology_model)

    output_path = Path(output_directory)
    output_path.mkdir(parents=True, exist_ok=True)
    _reject_unexpected_generated_policy_artifacts(output_path)

    artifacts = _build_compiled_artifacts(intent_model)
    written_hashes: dict[str, str] = {}
    for artifact in artifacts:
        payload = _serialize_artifact(artifact)
        target = output_path / artifact.filename
        if artifact.format_name == "json":
            dump_json_file(target, artifact.document)
        elif artifact.format_name == "yaml":
            dump_yaml_file(target, artifact.document)
        else:
            raise CompilationError(f"unsupported artifact format: {artifact.format_name}")
        written_hashes[artifact.filename] = sha256_bytes(payload)

    _assert_exact_policy_artifact_set(output_path)

    manifest = ArtifactManifest(
        generated_policy_artifacts=tuple(
            ManifestEntry(artifact=filename, sha256=written_hashes[filename])
            for filename in sorted(written_hashes)
        )
    )
    dump_json_file(output_path / MANIFEST_FILENAME, manifest.to_dict())
    return written_hashes


def compile_policy_bundle(
    schema_path: str | Path,
    intent_path: str | Path,
    topology_path: str | Path,
    output_directory: str | Path,
) -> dict[str, str]:
    """Load inputs from disk, validate them, and compile deterministic outputs."""
    schema_document = load_json_file(schema_path)
    intent_document = load_yaml_file(intent_path)
    topology_document = load_yaml_file(topology_path)
    return compile_policy_documents(
        schema_document=schema_document,
        intent_document=intent_document,
        topology_document=topology_document,
        output_directory=output_directory,
    )


def _build_compiled_artifacts(intent_model: IntentModel) -> tuple[CompiledArtifact, ...]:
    provenance = _build_provenance(intent_model)
    slices = tuple(sorted(intent_model.slices, key=lambda item: item.slice_id))
    shared_service = intent_model.shared_services[0]

    allowed_pairs = sorted(
        {
            (rule.source, rule.destination)
            for rule in intent_model.access_policies.allowed_shared_service_access
        }
    )
    forbidden_pairs = sorted(
        {
            (rule.source, rule.destination)
            for rule in intent_model.access_policies.forbidden_inter_slice_communication
        }
    )

    transport_policy = TransportPolicy(
        provenance=provenance,
        default_action="deny",
        transport_segments=tuple(
            _unique_preserving_order(
                [
                    *(slice_definition.transport_segment for slice_definition in slices),
                    shared_service.transport_segment,
                ]
            )
        ),
        allowed_directed_adjacencies=tuple(
            DirectedLink(
                source=slice_definition.transport_segment,
                destination=shared_service.transport_segment,
            )
            for slice_definition in slices
        ),
        forbidden_directed_adjacencies=tuple(
            DirectedLink(source=source, destination=destination, reason="inter_slice_isolation")
            for source, destination in (
                (slices[0].transport_segment, slices[1].transport_segment),
                (slices[1].transport_segment, slices[0].transport_segment),
            )
        ),
    )

    ocloud_policy = OCloudMicrosegmentationPolicy(
        provenance=provenance,
        default_deny=True,
        workloads=tuple(
            [
                *(workload.endpoint for slice_definition in slices for workload in slice_definition.workloads),
                shared_service.endpoint,
            ]
        ),
        allowed_flows=tuple(
            DirectedLink(source=source, destination=destination)
            for source, destination in allowed_pairs
        ),
        forbidden_flows=tuple(
            DirectedLink(source=source, destination=destination)
            for source, destination in forbidden_pairs
        ),
        shared_service_metadata=SharedServiceMetadata(
            name=shared_service.service_id,
            transit_allowed=shared_service.transit_allowed,
        ),
    )

    slice_policies = tuple(
        OranSlicePolicyEntry(
            slice_id=slice_definition.slice_id,
            snssai={
                "sst": slice_definition.snssai.sst,
                "sd": slice_definition.snssai.sd,
            },
            ocloud_namespace=slice_definition.ocloud_namespace,
            transport_segment=slice_definition.transport_segment,
            permitted_shared_service_exception={
                "service_id": shared_service.service_id,
                "endpoint": shared_service.endpoint,
            },
            forbidden_peer_slice=_peer_slice_id(slice_definition.slice_id),
        )
        for slice_definition in slices
    )
    oran_policy = OranSlicePolicy(
        provenance=provenance,
        note=(
            "This artefact is minimal slice-scoped O-RAN policy metadata, not live "
            "RIC/xApp/rApp control."
        ),
        slice_policies=slice_policies,
    )

    return (
        CompiledArtifact(
            filename=TRANSPORT_POLICY_FILENAME,
            format_name="json",
            document=transport_policy.to_dict(),
        ),
        CompiledArtifact(
            filename=OCLOUD_POLICY_FILENAME,
            format_name="yaml",
            document=ocloud_policy.to_dict(),
        ),
        CompiledArtifact(
            filename=ORAN_POLICY_FILENAME,
            format_name="json",
            document=oran_policy.to_dict(),
        ),
    )


def _build_provenance(intent_model: IntentModel) -> Provenance:
    if intent_model.thesis_id:
        return Provenance(
            intent_identity_field="thesis_id",
            intent_identity_value=intent_model.thesis_id,
        )

    if intent_model.scenario_id:
        return Provenance(
            intent_identity_field="scenario_id",
            intent_identity_value=intent_model.scenario_id,
        )

    raise CompilationError("validated intent is missing thesis_id or scenario_id")


def _validate_compiler_preconditions(
    intent_model: IntentModel, topology_model: TopologyModel
) -> None:
    node_map = {node.node_id: node for node in topology_model.nodes}
    policy_scope_slices = {
        node.slice_id for node in topology_model.nodes if node.layer == "policy" and node.slice_id
    }
    transport_nodes = {
        node.node_id for node in topology_model.nodes if node.layer == "transport"
    }

    for slice_definition in intent_model.slices:
        policy_node_id = f"oran_policy_{slice_definition.slice_id}"
        if policy_node_id not in node_map or slice_definition.slice_id not in policy_scope_slices:
            raise CompilationError(
                f"missing O-RAN policy scope for {slice_definition.slice_id}"
            )
        if slice_definition.transport_segment not in transport_nodes:
            raise CompilationError(
                f"missing transport segment for {slice_definition.slice_id}"
            )


def _serialize_artifact(artifact: CompiledArtifact) -> bytes:
    if artifact.format_name == "json":
        import json

        return (json.dumps(artifact.document, indent=2, sort_keys=False) + "\n").encode(
            "utf-8"
        )

    if artifact.format_name == "yaml":
        import yaml

        return yaml.safe_dump(
            artifact.document,
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=False,
        ).encode("utf-8")

    raise CompilationError(f"unsupported artifact format: {artifact.format_name}")


def _reject_unexpected_generated_policy_artifacts(output_directory: Path) -> None:
    unexpected = sorted(
        file.name
        for file in output_directory.iterdir()
        if file.is_file()
        and ".generated." in file.name
        and file.name not in GENERATED_POLICY_FILENAMES
    )
    if unexpected:
        unexpected_list = ", ".join(unexpected)
        raise CompilationError(
            f"unexpected generated policy artefact present in output directory: "
            f"{unexpected_list}"
        )


def _assert_exact_policy_artifact_set(output_directory: Path) -> None:
    generated_policy_files = {
        file.name
        for file in output_directory.iterdir()
        if file.is_file() and ".generated." in file.name
    }
    if generated_policy_files != set(GENERATED_POLICY_FILENAMES):
        expected = ", ".join(sorted(GENERATED_POLICY_FILENAMES))
        actual = ", ".join(sorted(generated_policy_files))
        raise CompilationError(
            f"expected exactly three policy artefacts ({expected}), found: {actual}"
        )


def _peer_slice_id(slice_id: str) -> str:
    return "slice_b" if slice_id == "slice_a" else "slice_a"


def _unique_preserving_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered
