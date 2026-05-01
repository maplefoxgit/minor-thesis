from __future__ import annotations

from pathlib import Path

from oran_slice_security.compiler import (
    MANIFEST_FILENAME,
    OCLOUD_POLICY_FILENAME,
    ORAN_POLICY_FILENAME,
    TRANSPORT_POLICY_FILENAME,
    compile_policy_bundle,
)


ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schemas" / "slice_security_intent.schema.json"
INTENT_PATH = ROOT / "intents" / "two_slice_shared_auth_log.valid.yaml"
TOPOLOGY_PATH = ROOT / "topology" / "base_topology.yaml"
OUTPUT_FILES = [
    MANIFEST_FILENAME,
    OCLOUD_POLICY_FILENAME,
    ORAN_POLICY_FILENAME,
    TRANSPORT_POLICY_FILENAME,
]


def test_compiler_outputs_are_byte_identical_across_repeated_runs(tmp_path: Path) -> None:
    first_output = tmp_path / "first"
    second_output = tmp_path / "second"

    compile_policy_bundle(
        schema_path=SCHEMA_PATH,
        intent_path=INTENT_PATH,
        topology_path=TOPOLOGY_PATH,
        output_directory=first_output,
    )
    compile_policy_bundle(
        schema_path=SCHEMA_PATH,
        intent_path=INTENT_PATH,
        topology_path=TOPOLOGY_PATH,
        output_directory=second_output,
    )

    for filename in OUTPUT_FILES:
        assert (first_output / filename).read_bytes() == (second_output / filename).read_bytes()
