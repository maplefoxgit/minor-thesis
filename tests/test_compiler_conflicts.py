from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from oran_slice_security.compiler import CompilationError, compile_policy_documents
from oran_slice_security.io import load_json_file, load_yaml_file
from oran_slice_security.validation import SemanticValidationError, TopologyValidationError


ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schemas" / "slice_security_intent.schema.json"
VALID_INTENT_PATH = ROOT / "intents" / "two_slice_shared_auth_log.valid.yaml"
VALID_TOPOLOGY_PATH = ROOT / "topology" / "base_topology.yaml"


def _load_schema() -> dict:
    return load_json_file(SCHEMA_PATH)


def _load_valid_intent() -> dict:
    return load_yaml_file(VALID_INTENT_PATH)


def _load_valid_topology() -> dict:
    return load_yaml_file(VALID_TOPOLOGY_PATH)


def test_compiler_rejects_conflicting_allow_and_deny_rules(tmp_path: Path) -> None:
    schema = _load_schema()
    intent = load_yaml_file(ROOT / "intents" / "invalid" / "conflicting_allow_deny.invalid.yaml")
    topology = _load_valid_topology()

    with pytest.raises(
        SemanticValidationError,
        match="conflicting allow and deny rule for slice_a_workload -> shared_auth_log",
    ):
        compile_policy_documents(schema, intent, topology, tmp_path / "generated")


def test_compiler_rejects_transit_enabled_shared_auth_log(tmp_path: Path) -> None:
    schema = _load_schema()
    intent = load_yaml_file(ROOT / "intents" / "invalid" / "shared_service_transit.invalid.yaml")
    topology = _load_valid_topology()

    with pytest.raises(
        SemanticValidationError, match="shared_auth_log must declare transit_allowed=false"
    ):
        compile_policy_documents(schema, intent, topology, tmp_path / "generated")


def test_compiler_rejects_missing_default_deny(tmp_path: Path) -> None:
    schema = _load_schema()
    intent = deepcopy(_load_valid_intent())
    topology = _load_valid_topology()
    intent["access_policies"]["default_deny"]["inter_slice"] = False

    with pytest.raises(SemanticValidationError, match="default-deny posture"):
        compile_policy_documents(schema, intent, topology, tmp_path / "generated")


def test_compiler_rejects_missing_oran_policy_scope(tmp_path: Path) -> None:
    schema = _load_schema()
    intent = _load_valid_intent()
    topology = deepcopy(_load_valid_topology())
    topology["nodes"] = [
        node for node in topology["nodes"] if node["node_id"] != "oran_policy_slice_b"
    ]

    with pytest.raises(TopologyValidationError, match="oran_policy_slice_b"):
        compile_policy_documents(schema, intent, topology, tmp_path / "generated")


def test_compiler_rejects_missing_transport_segment(tmp_path: Path) -> None:
    schema = _load_schema()
    intent = deepcopy(_load_valid_intent())
    topology = _load_valid_topology()
    intent["slices"][0]["transport_segment"] = ""

    with pytest.raises(
        SemanticValidationError, match="slice slice_a is missing a transport segment"
    ):
        compile_policy_documents(schema, intent, topology, tmp_path / "generated")


def test_compiler_rejects_unexpected_fourth_generated_policy_artifact(
    tmp_path: Path,
) -> None:
    schema = _load_schema()
    intent = _load_valid_intent()
    topology = _load_valid_topology()
    output_directory = tmp_path / "generated"
    output_directory.mkdir(parents=True, exist_ok=True)
    (output_directory / "unexpected_fourth.generated.json").write_text("{}", encoding="utf-8")

    with pytest.raises(
        CompilationError, match="unexpected generated policy artefact present"
    ):
        compile_policy_documents(schema, intent, topology, output_directory)
