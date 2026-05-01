from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from oran_slice_security.io import load_yaml_file
from oran_slice_security.validation import (
    SemanticValidationError,
    validate_intent_semantics,
)


ROOT = Path(__file__).resolve().parent.parent
VALID_INTENT_PATH = ROOT / "intents" / "two_slice_shared_auth_log.valid.yaml"
INVALID_CASES = [
    (
        "third_slice.invalid.yaml",
        "exactly two slices named slice_a and slice_b are required",
    ),
    (
        "missing_shared_service.invalid.yaml",
        "exactly one shared service named shared_auth_log is required",
    ),
    (
        "ambiguous_direction.invalid.yaml",
        "ambiguous direction 'bidirectional'",
    ),
    (
        "conflicting_allow_deny.invalid.yaml",
        "conflicting allow and deny rule for slice_a_workload -> shared_auth_log",
    ),
    (
        "shared_service_transit.invalid.yaml",
        "shared_auth_log must declare transit_allowed=false",
    ),
    (
        "duplicate_endpoint.invalid.yaml",
        "duplicate workload endpoint 'slice_a_workload'",
    ),
]


def _load_valid_intent() -> dict:
    return load_yaml_file(VALID_INTENT_PATH)


def test_valid_intent_passes_semantic_validation() -> None:
    model = validate_intent_semantics(_load_valid_intent())

    assert {slice_definition.slice_id for slice_definition in model.slices} == {
        "slice_a",
        "slice_b",
    }


@pytest.mark.parametrize(("fixture_name", "expected_message"), INVALID_CASES)
def test_invalid_intents_fail_for_expected_reason(
    fixture_name: str, expected_message: str
) -> None:
    intent = load_yaml_file(ROOT / "intents" / "invalid" / fixture_name)

    with pytest.raises(SemanticValidationError, match=expected_message):
        validate_intent_semantics(intent)


def test_missing_default_deny_posture_is_rejected() -> None:
    intent = deepcopy(_load_valid_intent())
    intent["access_policies"]["default_deny"]["inter_slice"] = False

    with pytest.raises(SemanticValidationError, match="default-deny posture"):
        validate_intent_semantics(intent)


def test_missing_forbidden_direction_between_slices_is_rejected() -> None:
    intent = deepcopy(_load_valid_intent())
    intent["access_policies"]["forbidden_inter_slice_communication"].pop()

    with pytest.raises(
        SemanticValidationError,
        match="missing forbidden directions between slice_a and slice_b",
    ):
        validate_intent_semantics(intent)


def test_missing_transport_segment_for_slice_is_rejected() -> None:
    intent = deepcopy(_load_valid_intent())
    intent["slices"][1]["transport_segment"] = ""

    with pytest.raises(
        SemanticValidationError, match="slice slice_b is missing a transport segment"
    ):
        validate_intent_semantics(intent)
