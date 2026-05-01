from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from _common import (
    NEGATIVE_TOPOLOGY_DIR,
    POLICIES_DIR,
    QUERIES_PATH,
    REPORTS_DIR,
    compile_baseline_to_repository,
    print_json,
    rel,
)
from oran_slice_security.validation import DocumentValidationError
from oran_slice_security.verifier import verify_from_paths


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
        "bad_transport_cross_slice_edge.yaml",
        "transport edge tn_segment_slice_a -> tn_segment_slice_b is not permitted by the compiled transport policy",
    ),
    (
        "bad_shared_service_transit.yaml",
        "shared_auth_log must declare transit_allowed=false",
    ),
    (
        "bad_missing_default_deny.yaml",
        "topology must declare default_deny.enforced=true",
    ),
    (
        "bad_missing_shared_service_path.yaml",
        "missing required reachable path(s):",
    ),
]


def _summarize_failed_verification(report: dict[str, Any]) -> str:
    missing_required = [
        f"{result['source']} -> {result['destination']}"
        for result in report["required_reachable"]
        if result["status"] == "fail"
    ]
    if missing_required:
        return "missing required reachable path(s): " + ", ".join(missing_required)

    forbidden_violations = [
        f"{result['source']} -> {result['destination']}"
        for result in report["forbidden_unreachable"]
        if result["status"] == "fail"
    ]
    if forbidden_violations:
        return "forbidden reachable path(s) detected: " + ", ".join(forbidden_violations)

    transit_violations = [
        result["service"]
        for result in report["terminal_service_transit"]
        if result["status"] == "fail"
    ]
    if transit_violations:
        return "terminal service transit violation(s): " + ", ".join(transit_violations)

    return "verification report returned overall_status=fail"


def run() -> dict[str, Any]:
    compile_baseline_to_repository()
    control_results: list[dict[str, Any]] = []

    for filename, expected_reason in NEGATIVE_CASES:
        topology_path = NEGATIVE_TOPOLOGY_DIR / filename
        with TemporaryDirectory() as report_dir:
            try:
                report = verify_from_paths(
                    topology_path=topology_path,
                    policies_directory=POLICIES_DIR,
                    queries_path=QUERIES_PATH,
                    output_directory=Path(report_dir),
                )
            except DocumentValidationError as exc:
                message = str(exc)
                passed = expected_reason in message and len(message.strip()) > 0
                control_results.append(
                    {
                        "topology": filename,
                        "expected_result": "reject",
                        "actual_result": "rejected",
                        "control_passed": passed,
                        "rejection_stage": "validation",
                        "reason": message,
                    }
                )
            else:
                if report["overall_status"] == "fail":
                    message = _summarize_failed_verification(report)
                    passed = expected_reason in message and len(message.strip()) > 0
                    control_results.append(
                        {
                            "topology": filename,
                            "expected_result": "reject",
                            "actual_result": "rejected",
                            "control_passed": passed,
                            "rejection_stage": "verification",
                            "reason": message,
                        }
                    )
                    continue

                control_results.append(
                    {
                        "topology": filename,
                        "expected_result": "reject",
                        "actual_result": "accepted",
                        "control_passed": False,
                        "rejection_stage": "none",
                        "reason": "negative-control topology unexpectedly verified",
                    }
                )

    overall_status = (
        "pass" if all(result["control_passed"] for result in control_results) else "fail"
    )
    return {
        "experiment_id": "E4",
        "title": "Negative-control misconfiguration",
        "status": overall_status,
        "result_directory": rel(REPORTS_DIR),
        "control_results": control_results,
    }


def main() -> int:
    result = run()
    print_json(result)
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
