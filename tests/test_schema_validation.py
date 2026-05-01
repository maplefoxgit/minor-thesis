from __future__ import annotations

from pathlib import Path

import pytest

from oran_slice_security.io import load_json_file, load_yaml_file
from oran_slice_security.validation import SchemaValidationError, validate_intent_schema


ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schemas" / "slice_security_intent.schema.json"
VALID_INTENT_PATH = ROOT / "intents" / "two_slice_shared_auth_log.valid.yaml"
INVALID_FIXTURE_NAMES = [
    "third_slice.invalid.yaml",
    "missing_shared_service.invalid.yaml",
    "ambiguous_direction.invalid.yaml",
    "conflicting_allow_deny.invalid.yaml",
    "shared_service_transit.invalid.yaml",
    "duplicate_endpoint.invalid.yaml",
]


def test_valid_intent_passes_schema() -> None:
    schema = load_json_file(SCHEMA_PATH)
    intent = load_yaml_file(VALID_INTENT_PATH)

    validate_intent_schema(intent, schema)


@pytest.mark.parametrize("fixture_name", INVALID_FIXTURE_NAMES)
def test_invalid_semantic_fixtures_still_pass_schema(fixture_name: str) -> None:
    schema = load_json_file(SCHEMA_PATH)
    intent = load_yaml_file(ROOT / "intents" / "invalid" / fixture_name)

    validate_intent_schema(intent, schema)


def test_schema_rejects_missing_required_section() -> None:
    schema = load_json_file(SCHEMA_PATH)
    intent = load_yaml_file(VALID_INTENT_PATH)
    intent.pop("slices")

    with pytest.raises(SchemaValidationError, match="required property"):
        validate_intent_schema(intent, schema)
