from __future__ import annotations

import pytest

from oran_slice_security.scaling import (
    build_faulty_multislice_verifier_fixture,
    build_multislice_verifier_fixture,
)
from oran_slice_security.verifier import verify_graph


@pytest.mark.parametrize(
    ("slice_count", "nodes", "edges", "rules", "required", "forbidden", "checks"),
    [
        (2, 8, 5, 10, 2, 4, 7),
        (3, 11, 7, 21, 3, 12, 16),
        (4, 14, 9, 36, 4, 24, 29),
        (10, 32, 21, 210, 10, 180, 191),
    ],
)
def test_multislice_verifier_fixture_cardinalities_and_results(
    slice_count: int,
    nodes: int,
    edges: int,
    rules: int,
    required: int,
    forbidden: int,
    checks: int,
) -> None:
    fixture = build_multislice_verifier_fixture(slice_count)
    report = verify_graph(fixture.graph, fixture.queries)

    assert len(fixture.graph.nodes) == nodes
    assert len(fixture.graph.edges) == edges
    assert fixture.rule_equivalent_count == rules
    assert fixture.required_query_count == required
    assert fixture.forbidden_query_count == forbidden
    assert fixture.total_check_count == checks
    assert fixture.path_search_invocation_count == 2 * slice_count * slice_count
    assert report["overall_status"] == "pass"


@pytest.mark.parametrize("slice_count", [2, 3, 4, 10])
def test_multislice_negative_control_detects_forbidden_cross_slice_route(
    slice_count: int,
) -> None:
    fixture = build_faulty_multislice_verifier_fixture(slice_count)
    report = verify_graph(fixture.graph, fixture.queries)

    assert report["overall_status"] == "fail"
    failed_forbidden = [
        result
        for result in report["forbidden_unreachable"]
        if result["status"] == "fail"
    ]
    assert failed_forbidden
    assert failed_forbidden[0]["source"] == "slice_001_workload"
    assert failed_forbidden[0]["destination"] == "slice_002_workload"


def test_multislice_verifier_fixture_rejects_single_slice() -> None:
    with pytest.raises(ValueError, match="at least 2"):
        build_multislice_verifier_fixture(1)
