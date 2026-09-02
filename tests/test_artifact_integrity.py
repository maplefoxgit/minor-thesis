from __future__ import annotations

from pathlib import Path

import pytest

from oran_slice_security.compiler import (
    MANIFEST_FILENAME,
    TRANSPORT_POLICY_FILENAME,
    compile_policy_bundle,
)
from oran_slice_security.graph_builder import build_graph_from_paths
from oran_slice_security.integrity import (
    ArtifactIntegrityError,
    verify_compiled_policy_manifest,
)
from oran_slice_security.io import dump_json_file, load_json_file
from oran_slice_security.verifier import verify_from_paths


ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schemas" / "slice_security_intent.schema.json"
INTENT_PATH = ROOT / "intents" / "two_slice_shared_auth_log.valid.yaml"
TOPOLOGY_PATH = ROOT / "topology" / "base_topology.yaml"
QUERIES_PATH = ROOT / "verifier" / "queries" / "baseline_queries.yaml"


def _compile(tmp_path: Path) -> Path:
    policies_directory = tmp_path / "generated"
    compile_policy_bundle(
        schema_path=SCHEMA_PATH,
        intent_path=INTENT_PATH,
        topology_path=TOPOLOGY_PATH,
        output_directory=policies_directory,
    )
    return policies_directory


def test_clean_compiled_bundle_passes_integrity_gate(tmp_path: Path) -> None:
    policies_directory = _compile(tmp_path)

    result = verify_compiled_policy_manifest(policies_directory)
    graph = build_graph_from_paths(TOPOLOGY_PATH, policies_directory)

    assert result["status"] == "pass"
    assert result["artifact_count"] == 3
    assert len(graph.edges) == 5


def test_byte_only_policy_mutation_is_rejected_before_report(tmp_path: Path) -> None:
    policies_directory = _compile(tmp_path)
    reports_directory = tmp_path / "reports"
    target = policies_directory / TRANSPORT_POLICY_FILENAME
    parsed_before = load_json_file(target)

    target.write_bytes(target.read_bytes() + b" \n")

    assert load_json_file(target) == parsed_before
    with pytest.raises(ArtifactIntegrityError) as exc_info:
        verify_from_paths(
            topology_path=TOPOLOGY_PATH,
            policies_directory=policies_directory,
            queries_path=QUERIES_PATH,
            output_directory=reports_directory,
        )

    message = str(exc_info.value)
    assert TRANSPORT_POLICY_FILENAME in message
    assert "expected sha256=" in message
    assert "actual sha256=" in message
    assert not (reports_directory / "verification_report.json").exists()


def test_missing_manifest_is_rejected(tmp_path: Path) -> None:
    policies_directory = _compile(tmp_path)
    (policies_directory / MANIFEST_FILENAME).unlink()

    with pytest.raises(ArtifactIntegrityError, match="manifest is missing"):
        verify_compiled_policy_manifest(policies_directory)


def test_missing_policy_file_is_rejected(tmp_path: Path) -> None:
    policies_directory = _compile(tmp_path)
    (policies_directory / TRANSPORT_POLICY_FILENAME).unlink()

    with pytest.raises(ArtifactIntegrityError, match="exact policy set"):
        verify_compiled_policy_manifest(policies_directory)


def test_extra_generated_policy_file_is_rejected(tmp_path: Path) -> None:
    policies_directory = _compile(tmp_path)
    (policies_directory / "unexpected.generated.json").write_text(
        "{}\n", encoding="utf-8"
    )

    with pytest.raises(ArtifactIntegrityError, match="exact policy set"):
        verify_compiled_policy_manifest(policies_directory)


def test_manifest_must_describe_the_exact_generated_policy_set(tmp_path: Path) -> None:
    policies_directory = _compile(tmp_path)
    manifest_path = policies_directory / MANIFEST_FILENAME
    manifest = load_json_file(manifest_path)
    manifest["generated_policy_artifacts"] = manifest["generated_policy_artifacts"][:-1]
    manifest["artifact_count"] = 2
    dump_json_file(manifest_path, manifest)

    with pytest.raises(ArtifactIntegrityError, match="wrong artifact_count"):
        verify_compiled_policy_manifest(policies_directory)


def test_manifest_rejects_unsafe_artifact_name(tmp_path: Path) -> None:
    policies_directory = _compile(tmp_path)
    manifest_path = policies_directory / MANIFEST_FILENAME
    manifest = load_json_file(manifest_path)
    manifest["generated_policy_artifacts"][0]["artifact"] = "../outside.generated.json"
    dump_json_file(manifest_path, manifest)

    with pytest.raises(ArtifactIntegrityError, match="unsafe artifact name"):
        verify_compiled_policy_manifest(policies_directory)


def test_manifest_rejects_duplicate_artifact_entry(tmp_path: Path) -> None:
    policies_directory = _compile(tmp_path)
    manifest_path = policies_directory / MANIFEST_FILENAME
    manifest = load_json_file(manifest_path)
    manifest["generated_policy_artifacts"][1] = dict(
        manifest["generated_policy_artifacts"][0]
    )
    dump_json_file(manifest_path, manifest)

    with pytest.raises(ArtifactIntegrityError, match="duplicate artifact"):
        verify_compiled_policy_manifest(policies_directory)


def test_manifest_rejects_invalid_hash(tmp_path: Path) -> None:
    policies_directory = _compile(tmp_path)
    manifest_path = policies_directory / MANIFEST_FILENAME
    manifest = load_json_file(manifest_path)
    manifest["generated_policy_artifacts"][0]["sha256"] = "not-a-hash"
    dump_json_file(manifest_path, manifest)

    with pytest.raises(ArtifactIntegrityError, match="invalid SHA-256"):
        verify_compiled_policy_manifest(policies_directory)


def test_manifest_artifact_count_must_be_an_integer(tmp_path: Path) -> None:
    policies_directory = _compile(tmp_path)
    manifest_path = policies_directory / MANIFEST_FILENAME
    manifest = load_json_file(manifest_path)
    manifest["artifact_count"] = 3.0
    dump_json_file(manifest_path, manifest)

    with pytest.raises(ArtifactIntegrityError, match="wrong artifact_count"):
        verify_compiled_policy_manifest(policies_directory)
