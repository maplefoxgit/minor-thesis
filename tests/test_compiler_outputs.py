from __future__ import annotations

from pathlib import Path

from oran_slice_security.compiler import (
    MANIFEST_FILENAME,
    OCLOUD_POLICY_FILENAME,
    ORAN_POLICY_FILENAME,
    TRANSPORT_POLICY_FILENAME,
    compile_policy_bundle,
)
from oran_slice_security.io import load_json_file, load_yaml_file, sha256_file


ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schemas" / "slice_security_intent.schema.json"
INTENT_PATH = ROOT / "intents" / "two_slice_shared_auth_log.valid.yaml"
TOPOLOGY_PATH = ROOT / "topology" / "base_topology.yaml"
EXPECTED_OUTPUTS = {
    MANIFEST_FILENAME,
    OCLOUD_POLICY_FILENAME,
    ORAN_POLICY_FILENAME,
    TRANSPORT_POLICY_FILENAME,
}


def _compile_to(output_directory: Path) -> None:
    compile_policy_bundle(
        schema_path=SCHEMA_PATH,
        intent_path=INTENT_PATH,
        topology_path=TOPOLOGY_PATH,
        output_directory=output_directory,
    )


def test_compile_creates_exact_expected_outputs_and_manifest_hashes(
    tmp_path: Path,
) -> None:
    output_directory = tmp_path / "generated"

    _compile_to(output_directory)

    assert {path.name for path in output_directory.iterdir() if path.is_file()} == EXPECTED_OUTPUTS

    manifest = load_json_file(output_directory / MANIFEST_FILENAME)
    artifact_entries = manifest["generated_policy_artifacts"]
    assert manifest["artifact_count"] == 3
    assert [entry["artifact"] for entry in artifact_entries] == [
        OCLOUD_POLICY_FILENAME,
        ORAN_POLICY_FILENAME,
        TRANSPORT_POLICY_FILENAME,
    ]
    for entry in artifact_entries:
        assert entry["sha256"] == sha256_file(output_directory / entry["artifact"])


def test_transport_policy_contains_only_required_adjacencies(tmp_path: Path) -> None:
    output_directory = tmp_path / "generated"

    _compile_to(output_directory)
    transport_policy = load_json_file(output_directory / TRANSPORT_POLICY_FILENAME)

    assert transport_policy["policy_type"] == "transport_segmentation"
    assert transport_policy["default_action"] == "deny"
    assert transport_policy["transport_segments"] == [
        "tn_segment_slice_a",
        "tn_segment_slice_b",
        "tn_segment_shared",
    ]
    assert transport_policy["allowed_directed_adjacencies"] == [
        {"source": "tn_segment_slice_a", "destination": "tn_segment_shared"},
        {"source": "tn_segment_slice_b", "destination": "tn_segment_shared"},
    ]
    assert transport_policy["forbidden_directed_adjacencies"] == [
        {
            "source": "tn_segment_slice_a",
            "destination": "tn_segment_slice_b",
            "reason": "inter_slice_isolation",
        },
        {
            "source": "tn_segment_slice_b",
            "destination": "tn_segment_slice_a",
            "reason": "inter_slice_isolation",
        },
    ]
    assert {
        (entry["source"], entry["destination"])
        for entry in transport_policy["allowed_directed_adjacencies"]
    } == {
        ("tn_segment_slice_a", "tn_segment_shared"),
        ("tn_segment_slice_b", "tn_segment_shared"),
    }


def test_ocloud_and_oran_outputs_match_bounded_scope(tmp_path: Path) -> None:
    output_directory = tmp_path / "generated"

    _compile_to(output_directory)
    ocloud_policy = load_yaml_file(output_directory / OCLOUD_POLICY_FILENAME)
    oran_policy = load_json_file(output_directory / ORAN_POLICY_FILENAME)

    assert ocloud_policy["policy_type"] == "ocloud_microsegmentation"
    assert ocloud_policy["default_deny"] is True
    assert ocloud_policy["workloads"] == [
        "slice_a_workload",
        "slice_b_workload",
        "shared_auth_log",
    ]
    assert ocloud_policy["allowed_flows"] == [
        {"source": "slice_a_workload", "destination": "shared_auth_log"},
        {"source": "slice_b_workload", "destination": "shared_auth_log"},
    ]
    assert ocloud_policy["forbidden_flows"] == [
        {"source": "slice_a_workload", "destination": "slice_b_workload"},
        {"source": "slice_b_workload", "destination": "slice_a_workload"},
    ]
    assert ocloud_policy["shared_service_metadata"] == {
        "name": "shared_auth_log",
        "transit_allowed": False,
    }

    assert oran_policy["policy_type"] == "oran_slice_policy"
    assert (
        oran_policy["note"]
        == "This artefact is minimal slice-scoped O-RAN policy metadata, not live "
        "RIC/xApp/rApp control."
    )
    assert [entry["slice_id"] for entry in oran_policy["slice_policies"]] == [
        "slice_a",
        "slice_b",
    ]
    assert oran_policy["slice_policies"][0]["snssai"] == {"sst": 1, "sd": "000001"}
    assert oran_policy["slice_policies"][1]["snssai"] == {"sst": 1, "sd": "000002"}
    assert oran_policy["slice_policies"][0]["permitted_shared_service_exception"] == {
        "service_id": "shared_auth_log",
        "endpoint": "shared_auth_log",
    }
    assert oran_policy["slice_policies"][0]["forbidden_peer_slice"] == "slice_b"
    assert oran_policy["slice_policies"][1]["forbidden_peer_slice"] == "slice_a"
