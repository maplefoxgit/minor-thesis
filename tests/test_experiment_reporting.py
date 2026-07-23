from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
EXPERIMENTS_DIR = ROOT / "experiments"
for candidate in (ROOT, EXPERIMENTS_DIR):
    candidate_text = str(candidate)
    if candidate_text not in sys.path:
        sys.path.insert(0, candidate_text)

from run_e1_schema_expressiveness import run as run_e1  # noqa: E402
from run_e3_reachability_verification import run as run_e3  # noqa: E402
from run_e4_negative_controls import run as run_e4  # noqa: E402
from run_e5_overhead import run as run_e5  # noqa: E402
from run_e6_controlled_baselines import run as run_e6  # noqa: E402
from run_all_experiments import run as run_all_experiments  # noqa: E402


def test_e1_reporting_separates_accepted_intent_ambiguity_from_rejected_invalid_ambiguity() -> None:
    result = run_e1()

    assert result["accepted_intent_ambiguity_count"] == 0
    assert result["ambiguous_invalid_case_rejection_count"] == 1
    assert "ambiguity_count" not in result


def test_e4_reporting_uses_explicit_rejection_fields() -> None:
    result = run_e4()
    missing_path_control = next(
        entry
        for entry in result["control_results"]
        if entry["topology"] == "bad_missing_shared_service_path.yaml"
    )

    assert missing_path_control["expected_result"] == "reject"
    assert missing_path_control["actual_result"] == "rejected"
    assert missing_path_control["control_passed"] is True
    assert missing_path_control["rejection_stage"] == "verification"
    assert "missing required reachable path(s):" in missing_path_control["reason"]

    edge_control = next(
        entry
        for entry in result["control_results"]
        if entry["topology"] == "bad_transport_cross_slice_edge.yaml"
    )
    assert edge_control["actual_result"] == "rejected"
    assert edge_control["control_passed"] is True
    assert edge_control["rejection_stage"] == "validation"


def test_experiment_reports_use_repository_relative_paths() -> None:
    e3_result = run_e3()
    all_result = run_all_experiments()

    assert e3_result["policies_directory"] == "policies/generated"
    assert all_result["experiments"]["E4"]["result_directory"] == "results/reports"
    assert all_result["result_files"] == {
        "verification_report_json": "results/reports/verification_report.json",
        "verification_report_md": "results/reports/verification_report.md",
        "experiment_summary_json": "results/reports/experiment_summary.json",
        "experiment_summary_md": "results/reports/experiment_summary.md",
        "overhead_metrics_json": "results/metrics/overhead_metrics.json",
        "baseline_comparison_json": "results/reports/baseline_comparison.json",
        "baseline_comparison_md": "results/reports/baseline_comparison.md",
    }


def test_e5_memory_reporting_is_labelled_as_tracemalloc() -> None:
    result = run_e5()

    assert result["memory_measurement_basis"] == "Python tracemalloc peak bytes (not process RSS)"
    assert "peak_python_tracemalloc_bytes_max" in result
    assert "peak_memory_bytes_max" not in result


def test_e6_reports_controlled_comparison_outputs() -> None:
    result = run_e6()

    assert result["status"] == "pass"
    assert result["comparison"]["only_condition_satisfying_all_objectives"] == (
        "proposed_compiled_policy"
    )
