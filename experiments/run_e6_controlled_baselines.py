from __future__ import annotations

from typing import Any, Iterable

from _common import (
    BASELINE_COMPARISON_JSON,
    BASELINE_COMPARISON_MD,
    POLICIES_DIR,
    QUERIES_PATH,
    TOPOLOGY_PATH,
    compile_baseline_to_repository,
    print_json,
    write_json,
    write_markdown,
)
from oran_slice_security.graph_builder import (
    DirectedLabelledGraph,
    GraphEdge,
    build_graph_from_paths,
)
from oran_slice_security.io import load_yaml_file
from oran_slice_security.verifier import load_verification_queries, verify_graph


PERMISSIVE_CONDITION = "permissive_topology_only"
DENY_ALL_CONDITION = "deny_all"
PROPOSED_CONDITION = "proposed_compiled_policy"


def _build_graph(
    topology_document: dict[str, Any],
    edge_pairs: Iterable[tuple[str, str]],
    provenance_label: str,
) -> DirectedLabelledGraph:
    nodes = tuple(sorted(node["node_id"] for node in topology_document["nodes"]))
    node_layers = {
        node["node_id"]: node["layer"] for node in topology_document["nodes"]
    }
    workload_nodes = tuple(
        sorted(
            node["node_id"]
            for node in topology_document["nodes"]
            if node["layer"] == "workload"
        )
    )

    unique_pairs = sorted(set(edge_pairs))
    edges = tuple(
        GraphEdge(
            source=source,
            destination=destination,
            provenance=(provenance_label,),
        )
        for source, destination in unique_pairs
    )
    adjacency_lists: dict[str, list[str]] = {node: [] for node in nodes}
    for edge in edges:
        adjacency_lists[edge.source].append(edge.destination)
    adjacency = {
        node: tuple(sorted(destinations))
        for node, destinations in adjacency_lists.items()
    }
    edge_provenance = {
        (edge.source, edge.destination): edge.provenance for edge in edges
    }

    return DirectedLabelledGraph(
        nodes=nodes,
        edges=edges,
        adjacency=adjacency,
        edge_provenance=edge_provenance,
        node_layers=node_layers,
        workload_nodes=workload_nodes,
    )


def _permissive_graph(topology_document: dict[str, Any]) -> DirectedLabelledGraph:
    """Build a no-policy baseline from the same physical/logical adjacencies.

    Each non-governance adjacency is treated as bidirectional. This represents the
    conservative connectivity available when generated default-deny, directed-flow,
    and terminal-service constraints are absent.
    """
    edge_pairs: set[tuple[str, str]] = set()
    for edge in topology_document["edges"]:
        if edge["relation"] == "governs":
            continue
        source = edge["source"]
        destination = edge["destination"]
        edge_pairs.add((source, destination))
        edge_pairs.add((destination, source))
    return _build_graph(
        topology_document,
        edge_pairs,
        provenance_label="permissive_topology_only_baseline",
    )


def _deny_all_graph(topology_document: dict[str, Any]) -> DirectedLabelledGraph:
    """Build a deny-all baseline while retaining the same node set."""
    return _build_graph(
        topology_document,
        (),
        provenance_label="deny_all_baseline",
    )


def _summarize_condition(
    condition_id: str,
    description: str,
    graph: DirectedLabelledGraph,
    queries_document: dict[str, Any],
) -> dict[str, Any]:
    report = verify_graph(graph=graph, queries_document=queries_document)
    required_count = len(report["required_reachable"])
    forbidden_count = len(report["forbidden_unreachable"])
    required_pass_count = sum(
        result["status"] == "pass" for result in report["required_reachable"]
    )
    forbidden_pass_count = sum(
        result["status"] == "pass" for result in report["forbidden_unreachable"]
    )
    terminal_pass = all(
        result["status"] == "pass" for result in report["terminal_service_transit"]
    )
    required_rate = required_pass_count / required_count
    forbidden_block_rate = forbidden_pass_count / forbidden_count
    balanced_objective_passed = (
        required_rate == 1.0 and forbidden_block_rate == 1.0 and terminal_pass
    )

    return {
        "condition_id": condition_id,
        "description": description,
        "graph_node_count": len(graph.nodes),
        "graph_edge_count": len(graph.edges),
        "required_reachable_pass_count": required_pass_count,
        "required_reachable_count": required_count,
        "required_reachability_rate": required_rate,
        "forbidden_unreachable_pass_count": forbidden_pass_count,
        "forbidden_unreachable_count": forbidden_count,
        "forbidden_path_block_rate": forbidden_block_rate,
        "terminal_service_passed": terminal_pass,
        "balanced_objective_passed": balanced_objective_passed,
        "verification_report": report,
    }


def _render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Controlled Baseline Comparison",
        "",
        "## Experimental control",
        "",
        (
            "The node set, source topology, reachability queries, and breadth-first "
            "verification algorithm were held constant. Only the communication-edge "
            "condition changed."
        ),
        "",
        "| Condition | Edges | Required paths preserved | Forbidden paths blocked | Terminal service | Balanced objective |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for condition_id in (
        PERMISSIVE_CONDITION,
        DENY_ALL_CONDITION,
        PROPOSED_CONDITION,
    ):
        condition = result["conditions"][condition_id]
        lines.append(
            "| {name} | {edges} | {required:.0%} | {forbidden:.0%} | {terminal} | {balanced} |".format(
                name=condition_id,
                edges=condition["graph_edge_count"],
                required=condition["required_reachability_rate"],
                forbidden=condition["forbidden_path_block_rate"],
                terminal="pass" if condition["terminal_service_passed"] else "fail",
                balanced="pass" if condition["balanced_objective_passed"] else "fail",
            )
        )

    comparison = result["comparison"]
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "- The permissive topology-only condition preserved both required "
                "shared-service paths but blocked none of the four forbidden paths."
            ),
            (
                "- The deny-all condition blocked all forbidden paths but removed both "
                "required shared-service paths."
            ),
            (
                "- The proposed compiled policy was the only condition that preserved "
                "all required paths, blocked all forbidden paths, and kept the shared "
                "service terminal."
            ),
            (
                "- Relative to the permissive condition, the proposed policy improved "
                f"the forbidden-path block rate by {comparison['safety_gain_vs_permissive_percentage_points']:.0f} "
                "percentage points while retaining 100% required reachability."
            ),
            (
                "- Relative to deny-all, the proposed policy improved required-path "
                f"availability by {comparison['availability_gain_vs_deny_all_percentage_points']:.0f} "
                "percentage points without reducing the forbidden-path block rate."
            ),
            "",
            "## Boundary",
            "",
            result["interpretation_boundary"],
            "",
        ]
    )
    return "\n".join(lines)


def run() -> dict[str, Any]:
    topology_document = load_yaml_file(TOPOLOGY_PATH)
    queries_document = load_verification_queries(QUERIES_PATH)

    compile_baseline_to_repository()
    proposed_graph = build_graph_from_paths(
        topology_path=TOPOLOGY_PATH,
        policies_directory=POLICIES_DIR,
    )

    conditions = {
        PERMISSIVE_CONDITION: _summarize_condition(
            PERMISSIVE_CONDITION,
            (
                "No generated policy: every non-governance topology adjacency is "
                "available in both directions."
            ),
            _permissive_graph(topology_document),
            queries_document,
        ),
        DENY_ALL_CONDITION: _summarize_condition(
            DENY_ALL_CONDITION,
            "All communication edges are removed.",
            _deny_all_graph(topology_document),
            queries_document,
        ),
        PROPOSED_CONDITION: _summarize_condition(
            PROPOSED_CONDITION,
            (
                "The validated intent is compiled into coordinated transport, O-Cloud, "
                "and slice-scoped O-RAN policy artefacts."
            ),
            proposed_graph,
            queries_document,
        ),
    }

    permissive = conditions[PERMISSIVE_CONDITION]
    deny_all = conditions[DENY_ALL_CONDITION]
    proposed = conditions[PROPOSED_CONDITION]
    uniquely_satisfying = [
        condition_id
        for condition_id, condition in conditions.items()
        if condition["balanced_objective_passed"]
    ]

    expected_profiles_passed = (
        permissive["required_reachability_rate"] == 1.0
        and permissive["forbidden_path_block_rate"] == 0.0
        and not permissive["terminal_service_passed"]
        and deny_all["required_reachability_rate"] == 0.0
        and deny_all["forbidden_path_block_rate"] == 1.0
        and deny_all["terminal_service_passed"]
        and proposed["required_reachability_rate"] == 1.0
        and proposed["forbidden_path_block_rate"] == 1.0
        and proposed["terminal_service_passed"]
        and uniquely_satisfying == [PROPOSED_CONDITION]
    )

    result = {
        "experiment_id": "E6",
        "title": "Controlled baseline comparison",
        "status": "pass" if expected_profiles_passed else "fail",
        "controlled_variables": {
            "source_topology": "topology/base_topology.yaml",
            "node_count": proposed["graph_node_count"],
            "required_query_count": proposed["required_reachable_count"],
            "forbidden_query_count": proposed["forbidden_unreachable_count"],
            "terminal_service_count": len(
                proposed["verification_report"]["terminal_service_transit"]
            ),
            "verification_algorithm": "deterministic breadth-first search",
            "changed_factor": "permitted communication-edge condition",
        },
        "conditions": conditions,
        "comparison": {
            "only_condition_satisfying_all_objectives": (
                uniquely_satisfying[0] if len(uniquely_satisfying) == 1 else None
            ),
            "safety_gain_vs_permissive_percentage_points": (
                proposed["forbidden_path_block_rate"]
                - permissive["forbidden_path_block_rate"]
            )
            * 100.0,
            "availability_retention_vs_permissive_percentage": (
                proposed["required_reachability_rate"]
                / permissive["required_reachability_rate"]
                * 100.0
            ),
            "availability_gain_vs_deny_all_percentage_points": (
                proposed["required_reachability_rate"]
                - deny_all["required_reachability_rate"]
            )
            * 100.0,
            "edge_reduction_vs_permissive_count": (
                permissive["graph_edge_count"] - proposed["graph_edge_count"]
            ),
            "edge_reduction_vs_permissive_percentage": (
                (permissive["graph_edge_count"] - proposed["graph_edge_count"])
                / permissive["graph_edge_count"]
                * 100.0
            ),
        },
        "interpretation_boundary": (
            "The comparison is controlled and deterministic within one synthetic "
            "eight-node model. It demonstrates the safety-availability trade-off of the "
            "three edge conditions, not superiority over production O-RAN policy systems."
        ),
    }
    write_json(BASELINE_COMPARISON_JSON, result)
    write_markdown(BASELINE_COMPARISON_MD, _render_markdown(result))
    return result


def main() -> int:
    result = run()
    print_json(result)
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
