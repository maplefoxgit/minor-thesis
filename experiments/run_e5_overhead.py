from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from _common import (
    METRICS_DIR,
    OVERHEAD_METRICS_JSON,
    QUERIES_PATH,
    TOPOLOGY_PATH,
    collect_file_sizes,
    count_generated_rules,
    load_baseline_documents,
    measure_stage,
    print_json,
    write_json,
)
from oran_slice_security.compiler import compile_policy_documents
from oran_slice_security.graph_builder import build_graph_from_paths
from oran_slice_security.validation import validate_intent_document, validate_topology_document
from oran_slice_security.verifier import verify_from_paths


def _validate_pipeline(schema: dict[str, Any], intent: dict[str, Any], topology: dict[str, Any]) -> None:
    validate_intent_document(intent, schema)
    validate_topology_document(topology)


def run() -> dict[str, Any]:
    schema, intent, topology = load_baseline_documents()
    METRICS_DIR.mkdir(parents=True, exist_ok=True)

    with TemporaryDirectory() as working_dir:
        working_path = Path(working_dir)
        policies_dir = working_path / "generated"
        reports_dir = working_path / "reports"

        _, validation_metrics = measure_stage(
            "validation",
            _validate_pipeline,
            schema,
            intent,
            topology,
        )
        _, compile_metrics = measure_stage(
            "compile",
            compile_policy_documents,
            schema,
            intent,
            topology,
            policies_dir,
        )
        graph, graph_metrics = measure_stage(
            "graph_construction",
            build_graph_from_paths,
            TOPOLOGY_PATH,
            policies_dir,
        )
        verification_report, verification_metrics = measure_stage(
            "verification",
            verify_from_paths,
            TOPOLOGY_PATH,
            policies_dir,
            QUERIES_PATH,
            reports_dir,
        )

        file_sizes = collect_file_sizes(policies_dir)
        rule_counts = count_generated_rules(policies_dir)

    peak_memory_bytes_max = max(
        validation_metrics["peak_memory_bytes"],
        compile_metrics["peak_memory_bytes"],
        graph_metrics["peak_memory_bytes"],
        verification_metrics["peak_memory_bytes"],
    )
    overall_wall_clock_seconds = (
        validation_metrics["wall_clock_seconds"]
        + compile_metrics["wall_clock_seconds"]
        + graph_metrics["wall_clock_seconds"]
        + verification_metrics["wall_clock_seconds"]
    )
    overall_cpu_seconds = (
        validation_metrics["cpu_seconds"]
        + compile_metrics["cpu_seconds"]
        + graph_metrics["cpu_seconds"]
        + verification_metrics["cpu_seconds"]
    )
    status = (
        "pass"
        if verification_report["overall_status"] == "pass"
        and all(size > 0 for size in file_sizes.values())
        and rule_counts["generated_rule_count"] > 0
        else "fail"
    )

    metrics_document = {
        "experiment_id": "E5",
        "title": "Practical overhead",
        "status": status,
        "validation_time": validation_metrics,
        "compile_time": compile_metrics,
        "graph_construction_time": graph_metrics,
        "verification_time": verification_metrics,
        "generated_policy_file_sizes_bytes": file_sizes,
        "generated_rule_count": rule_counts["generated_rule_count"],
        "generated_rule_breakdown": rule_counts,
        "graph_node_count": verification_report["graph_node_count"],
        "graph_edge_count": verification_report["graph_edge_count"],
        "peak_memory_bytes_max": peak_memory_bytes_max,
        "overall_wall_clock_seconds": overall_wall_clock_seconds,
        "overall_cpu_seconds": overall_cpu_seconds,
        "local_overhead_statement": (
            "These measurements report modest local proof-of-concept overhead only. "
            "They do not establish production scalability."
        ),
    }
    write_json(OVERHEAD_METRICS_JSON, metrics_document)
    return metrics_document


def main() -> int:
    result = run()
    print_json(result)
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
