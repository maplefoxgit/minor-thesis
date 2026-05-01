from __future__ import annotations

from pathlib import Path

from oran_slice_security.compiler import compile_policy_bundle
from oran_slice_security.graph_builder import build_graph_from_paths


ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schemas" / "slice_security_intent.schema.json"
INTENT_PATH = ROOT / "intents" / "two_slice_shared_auth_log.valid.yaml"
TOPOLOGY_PATH = ROOT / "topology" / "base_topology.yaml"


def test_graph_builder_creates_bounded_surviving_graph(tmp_path: Path) -> None:
    policies_directory = tmp_path / "generated"
    compile_policy_bundle(SCHEMA_PATH, INTENT_PATH, TOPOLOGY_PATH, policies_directory)

    graph = build_graph_from_paths(TOPOLOGY_PATH, policies_directory)

    assert set(graph.nodes) == {
        "slice_a_workload",
        "slice_b_workload",
        "tn_segment_slice_a",
        "tn_segment_slice_b",
        "tn_segment_shared",
        "shared_auth_log",
        "oran_policy_slice_a",
        "oran_policy_slice_b",
    }
    assert len(graph.edges) == 5
    assert graph.adjacency["slice_a_workload"] == ("tn_segment_slice_a",)
    assert graph.adjacency["slice_b_workload"] == ("tn_segment_slice_b",)
    assert graph.adjacency["tn_segment_slice_a"] == ("tn_segment_shared",)
    assert graph.adjacency["tn_segment_slice_b"] == ("tn_segment_shared",)
    assert graph.adjacency["tn_segment_shared"] == ("shared_auth_log",)
    assert graph.adjacency["shared_auth_log"] == ()
    assert graph.edge_provenance[("tn_segment_slice_a", "tn_segment_shared")] == (
        "topology",
        "transport_policy",
        "oran_slice_policy",
    )
