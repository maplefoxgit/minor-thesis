from __future__ import annotations

from pathlib import Path

from oran_slice_security.compiler import compile_policy_bundle
from oran_slice_security.verifier import verify_from_paths


ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schemas" / "slice_security_intent.schema.json"
INTENT_PATH = ROOT / "intents" / "two_slice_shared_auth_log.valid.yaml"
TOPOLOGY_PATH = ROOT / "topology" / "base_topology.yaml"
QUERIES_PATH = ROOT / "verifier" / "queries" / "baseline_queries.yaml"


def test_verifier_passes_for_valid_baseline_and_preserves_required_paths(
    tmp_path: Path,
) -> None:
    policies_directory = tmp_path / "generated"
    reports_directory = tmp_path / "reports"
    compile_policy_bundle(SCHEMA_PATH, INTENT_PATH, TOPOLOGY_PATH, policies_directory)

    report = verify_from_paths(
        topology_path=TOPOLOGY_PATH,
        policies_directory=policies_directory,
        queries_path=QUERIES_PATH,
        output_directory=reports_directory,
    )

    assert report["overall_status"] == "pass"
    assert report["graph_node_count"] == 8
    assert report["graph_edge_count"] == 5
    assert [entry["path"] for entry in report["required_reachable"]] == [
        [
            "slice_a_workload",
            "tn_segment_slice_a",
            "tn_segment_shared",
            "shared_auth_log",
        ],
        [
            "slice_b_workload",
            "tn_segment_slice_b",
            "tn_segment_shared",
            "shared_auth_log",
        ],
    ]
    assert all(entry["status"] == "pass" for entry in report["forbidden_unreachable"])
    assert all(entry["violation_path"] is None for entry in report["forbidden_unreachable"])
    assert report["terminal_service_transit"] == [
        {
            "service": "shared_auth_log",
            "status": "pass",
            "outgoing_edges": [],
            "violation_paths": [],
        }
    ]
