from __future__ import annotations

from typing import Any

from _common import (
    load_baseline_documents,
    load_invalid_intent,
    print_json,
)
from oran_slice_security.validation import DocumentValidationError, validate_intent_document


CASES = [
    {
        "case_id": "valid_intent",
        "kind": "valid",
        "document_name": "two_slice_shared_auth_log.valid.yaml",
    },
    {
        "case_id": "third_slice",
        "kind": "invalid",
        "document_name": "third_slice.invalid.yaml",
        "expected_reason": "exactly two slices named slice_a and slice_b are required",
    },
    {
        "case_id": "missing_shared_service",
        "kind": "invalid",
        "document_name": "missing_shared_service.invalid.yaml",
        "expected_reason": "exactly one shared service named shared_auth_log is required",
    },
    {
        "case_id": "ambiguous_direction",
        "kind": "invalid",
        "document_name": "ambiguous_direction.invalid.yaml",
        "expected_reason": "ambiguous direction 'bidirectional'",
    },
    {
        "case_id": "conflicting_allow_deny",
        "kind": "invalid",
        "document_name": "conflicting_allow_deny.invalid.yaml",
        "expected_reason": "conflicting allow and deny rule for slice_a_workload -> shared_auth_log",
    },
    {
        "case_id": "shared_service_transit",
        "kind": "invalid",
        "document_name": "shared_service_transit.invalid.yaml",
        "expected_reason": "shared_auth_log must declare transit_allowed=false",
    },
    {
        "case_id": "duplicate_endpoint",
        "kind": "invalid",
        "document_name": "duplicate_endpoint.invalid.yaml",
        "expected_reason": "duplicate workload endpoint 'slice_a_workload'",
    },
]


def run() -> dict[str, Any]:
    schema, valid_intent, _ = load_baseline_documents()
    case_results: list[dict[str, Any]] = []

    for case in CASES:
        if case["kind"] == "valid":
            try:
                validate_intent_document(valid_intent, schema)
            except DocumentValidationError as exc:
                case_results.append(
                    {
                        "case_id": case["case_id"],
                        "status": "fail",
                        "reason": str(exc),
                    }
                )
            else:
                case_results.append(
                    {
                        "case_id": case["case_id"],
                        "status": "pass",
                        "reason": "valid intent accepted",
                    }
                )
            continue

        document = load_invalid_intent(case["document_name"])
        try:
            validate_intent_document(document, schema)
        except DocumentValidationError as exc:
            passed = case["expected_reason"] in str(exc)
            case_results.append(
                {
                    "case_id": case["case_id"],
                    "status": "pass" if passed else "fail",
                    "reason": str(exc),
                }
            )
        else:
            case_results.append(
                {
                    "case_id": case["case_id"],
                    "status": "fail",
                    "reason": "invalid intent unexpectedly passed validation",
                }
            )

    passed_case_count = sum(result["status"] == "pass" for result in case_results)
    total_case_count = len(case_results)
    overall_status = "pass" if passed_case_count == total_case_count else "fail"

    return {
        "experiment_id": "E1",
        "title": "Schema expressiveness",
        "status": overall_status,
        "schema_coverage": passed_case_count / total_case_count,
        "covered_case_count": passed_case_count,
        "required_case_count": total_case_count,
        "ambiguity_count": sum(
            result["case_id"] == "ambiguous_direction" and result["status"] == "pass"
            for result in case_results
        ),
        "unsupported_case_count": 0,
        "case_results": case_results,
    }


def main() -> int:
    result = run()
    print_json(result)
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
