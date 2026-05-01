from __future__ import annotations

from pathlib import Path

import pytest

from oran_slice_security.io import load_yaml_file
from oran_slice_security.validation import (
    TopologyValidationError,
    validate_topology_document,
)


ROOT = Path(__file__).resolve().parent.parent
BASE_TOPOLOGY_PATH = ROOT / "topology" / "base_topology.yaml"
NEGATIVE_CASES = [
    ("bad_direct_cross_slice.yaml", "direct cross-slice workload edge is not allowed"),
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


def test_base_topology_loads_and_validates() -> None:
    topology = load_yaml_file(BASE_TOPOLOGY_PATH)

    model = validate_topology_document(topology)

    assert {node.node_id for node in model.nodes} >= {
        "slice_a_workload",
        "slice_b_workload",
        "shared_auth_log",
    }


@pytest.mark.parametrize(("fixture_name", "expected_message"), NEGATIVE_CASES)
def test_negative_control_topologies_fail_validation(
    fixture_name: str, expected_message: str
) -> None:
    topology = load_yaml_file(ROOT / "topology" / "negative_controls" / fixture_name)

    with pytest.raises(TopologyValidationError, match=expected_message):
        validate_topology_document(topology)
