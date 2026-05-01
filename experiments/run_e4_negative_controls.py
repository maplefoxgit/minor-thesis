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
)
from oran_slice_security.validation import DocumentValidationError
from oran_slice_security.verifier import verify_from_paths


NEGATIVE_CASES = [
    (
        "bad_direct_cross_slice.yaml",
        "direct cross-slice workload edge is not allowed",
    ),
    (
        "bad_transport_cross_slice.yaml",
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


def run() -> dict[str, Any]:
    compile_baseline_to_repository()
    control_results: list[dict[str, Any]] = []

    for filename, expected_reason in NEGATIVE_CASES:
        topology_path = NEGATIVE_TOPOLOGY_DIR / filename
        with TemporaryDirectory() as report_dir:
            try:
                verify_from_paths(
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
                        "status": "pass" if passed else "fail",
                        "reason": message,
                    }
                )
            else:
                control_results.append(
                    {
                        "topology": filename,
                        "status": "fail",
                        "reason": "negative-control topology unexpectedly verified",
                    }
                )

    overall_status = (
        "pass" if all(result["status"] == "pass" for result in control_results) else "fail"
    )
    return {
        "experiment_id": "E4",
        "title": "Negative-control misconfiguration",
        "status": overall_status,
        "result_directory": str(REPORTS_DIR),
        "control_results": control_results,
    }


def main() -> int:
    result = run()
    print_json(result)
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
