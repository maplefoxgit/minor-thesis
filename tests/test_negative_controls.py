from __future__ import annotations

from pathlib import Path

import pytest

from oran_slice_security.compiler import compile_policy_bundle
from oran_slice_security.validation import DocumentValidationError, TopologyValidationError
from oran_slice_security.verifier import verify_from_paths


ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schemas" / "slice_security_intent.schema.json"
INTENT_PATH = ROOT / "intents" / "two_slice_shared_auth_log.valid.yaml"
QUERIES_PATH = ROOT / "verifier" / "queries" / "baseline_queries.yaml"
NEGATIVE_CASES = [
    (
        "bad_direct_cross_slice.yaml",
        "direct cross-slice workload edge is not allowed",
    ),
    (
        "bad_transport_misbinding.yaml",
        "node 'slice_a_workload' must set transport_segment='tn_segment_slice_a'",
    ),
    (
        "bad_shared_service_transit.yaml",
        "shared_auth_log must declare transit_allowed=false",
    ),
    (
        "bad_missing_default_deny.yaml",
        "topology must declare default_deny.enforced=true",
    ),
]


@pytest.mark.parametrize(("fixture_name", "expected_message"), NEGATIVE_CASES)
def test_negative_control_topologies_fail_verification(
    fixture_name: str, expected_message: str, tmp_path: Path
) -> None:
    policies_directory = tmp_path / "generated"
    reports_directory = tmp_path / "reports"
    compile_policy_bundle(
        SCHEMA_PATH,
        INTENT_PATH,
        ROOT / "topology" / "base_topology.yaml",
        policies_directory,
    )

    with pytest.raises(TopologyValidationError, match=expected_message):
        verify_from_paths(
            topology_path=ROOT / "topology" / "negative_controls" / fixture_name,
            policies_directory=policies_directory,
            queries_path=QUERIES_PATH,
            output_directory=reports_directory,
        )


def test_missing_shared_service_path_fails_reachability_verification(tmp_path: Path) -> None:
    policies_directory = tmp_path / "generated"
    reports_directory = tmp_path / "reports"
    compile_policy_bundle(
        SCHEMA_PATH,
        INTENT_PATH,
        ROOT / "topology" / "base_topology.yaml",
        policies_directory,
    )

    report = verify_from_paths(
        topology_path=ROOT / "topology" / "negative_controls" / "bad_missing_shared_service_path.yaml",
        policies_directory=policies_directory,
        queries_path=QUERIES_PATH,
        output_directory=reports_directory,
    )

    assert report["overall_status"] == "fail"
    assert [
        (entry["source"], entry["destination"])
        for entry in report["required_reachable"]
        if entry["status"] == "fail"
    ] == [
        ("slice_a_workload", "shared_auth_log"),
        ("slice_b_workload", "shared_auth_log"),
    ]


def test_transport_cross_slice_edge_fails_verification(tmp_path: Path) -> None:
    policies_directory = tmp_path / "generated"
    reports_directory = tmp_path / "reports"
    compile_policy_bundle(
        SCHEMA_PATH,
        INTENT_PATH,
        ROOT / "topology" / "base_topology.yaml",
        policies_directory,
    )

    with pytest.raises(
        DocumentValidationError,
        match="transport edge tn_segment_slice_a -> tn_segment_slice_b is not permitted by the compiled transport policy",
    ):
        verify_from_paths(
            topology_path=ROOT / "topology" / "negative_controls" / "bad_transport_cross_slice_edge.yaml",
            policies_directory=policies_directory,
            queries_path=QUERIES_PATH,
            output_directory=reports_directory,
        )
