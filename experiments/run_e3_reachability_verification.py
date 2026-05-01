from __future__ import annotations

from typing import Any

from _common import (
    POLICIES_DIR,
    compile_baseline_to_repository,
    print_json,
    rel,
    verify_baseline_to_repository,
)


def run() -> dict[str, Any]:
    compile_baseline_to_repository()
    report = verify_baseline_to_repository()

    required_paths_present = all(
        result["status"] == "pass" and result["path"] is not None
        for result in report["required_reachable"]
    )
    forbidden_paths_blocked = all(
        result["status"] == "pass" and result["violation_path"] is None
        for result in report["forbidden_unreachable"]
    )
    shared_auth_log_not_transit = all(
        result["status"] == "pass"
        and result["service"] == "shared_auth_log"
        and not result["outgoing_edges"]
        and not result["violation_paths"]
        for result in report["terminal_service_transit"]
    )

    overall_status = (
        "pass"
        if report["overall_status"] == "pass"
        and required_paths_present
        and forbidden_paths_blocked
        and shared_auth_log_not_transit
        else "fail"
    )

    return {
        "experiment_id": "E3",
        "title": "Reachability verification",
        "status": overall_status,
        "policies_directory": rel(POLICIES_DIR),
        "required_reachable_pass_count": sum(
            result["status"] == "pass" for result in report["required_reachable"]
        ),
        "forbidden_unreachable_pass_count": sum(
            result["status"] == "pass" for result in report["forbidden_unreachable"]
        ),
        "shared_auth_log_not_transit": shared_auth_log_not_transit,
        "verification_report": report,
    }


def main() -> int:
    result = run()
    print_json(result)
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
