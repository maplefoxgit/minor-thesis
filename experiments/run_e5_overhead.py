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
from oran_slice_security.report import write_verification_reports
from oran_slice_security.validation import validate_intent_document, validate_topology_document
from oran_slice_security.verifier import load_verification_queries, verify_graph


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
        queries_document, query_loading_metrics = measure_stage(
            "query_loading",
            load_verification_queries,
            QUERIES_PATH,
        )
        verification_report, verification_metrics = measure_stage(
            "verification",
            verify_graph,
            graph,
            queries_document,
        )
        _, report_generation_metrics = measure_stage(
            "report_generation",
            write_verification_reports,
            verification_report,
            reports_dir,
        )

        file_sizes = collect_file_sizes(policies_dir)
        rule_counts = count_generated_rules(policies_dir)

    peak_python_tracemalloc_bytes_max = max(
        validation_metrics["peak_python_tracemalloc_bytes"],
        compile_metrics["peak_python_tracemalloc_bytes"],
        graph_metrics["peak_python_tracemalloc_bytes"],
        query_loading_metrics["peak_python_tracemalloc_bytes"],
        verification_metrics["peak_python_tracemalloc_bytes"],
        report_generation_metrics["peak_python_tracemalloc_bytes"],
    )
    overall_wall_clock_seconds = (
        validation_metrics["wall_clock_seconds"]
        + compile_metrics["wall_clock_seconds"]
        + graph_metrics["wall_clock_seconds"]
        + query_loading_metrics["wall_clock_seconds"]
        + verification_metrics["wall_clock_seconds"]
        + report_generation_metrics["wall_clock_seconds"]
    )
    overall_cpu_seconds = (
        validation_metrics["cpu_seconds"]
        + compile_metrics["cpu_seconds"]
        + graph_metrics["cpu_seconds"]
        + query_loading_metrics["cpu_seconds"]
        + verification_metrics["cpu_seconds"]
        + report_generation_metrics["cpu_seconds"]
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
        "query_loading_time": query_loading_metrics,
        "verification_time": verification_metrics,
        "report_generation_time": report_generation_metrics,
        "generated_policy_file_sizes_bytes": file_sizes,
        "generated_rule_count": rule_counts["generated_rule_count"],
        "generated_rule_breakdown": rule_counts,
        "graph_node_count": verification_report["graph_node_count"],
        "graph_edge_count": verification_report["graph_edge_count"],
        "peak_python_tracemalloc_bytes_max": peak_python_tracemalloc_bytes_max,
        "memory_measurement_basis": "Python tracemalloc peak bytes (not process RSS)",
        "overall_wall_clock_seconds": overall_wall_clock_seconds,
        "overall_cpu_seconds": overall_cpu_seconds,
        "measurement_boundaries": {
            "validation_time": (
                "Standalone schema, semantic intent, and topology validation."
            ),
            "compile_time": (
                "Compiler entrypoint time, including its internal revalidation, policy "
                "serialization, file writing, and manifest writing."
            ),
            "graph_construction_time": (
                "Topology loading, manifest integrity verification, policy loading and "
                "validation, and construction of the policy-filtered graph."
            ),
            "query_loading_time": (
                "Loading and validation of the predefined verification queries."
            ),
            "verification_time": (
                "Pure in-memory evaluation of the prebuilt graph and preloaded queries. "
                "It excludes graph construction, query loading, and report generation."
            ),
            "report_generation_time": (
                "Serialization and writing of the JSON and Markdown verification reports."
            ),
            "overall_stage_sum": (
                "Sum of validation, compilation, graph construction, query loading, "
                "pure verification, and report generation measurements. The explicit "
                "validation stage and compiler revalidation both occur, so the sum is "
                "the implemented pipeline sequence rather than six mutually exclusive "
                "algorithmic components."
            ),
            "timing_and_memory": (
                "Timing calls run without tracemalloc. Peak Python allocation is measured "
                "in a separate repeated call for each stage."
            ),
        },
        "local_overhead_statement": (
            "These measurements report local proof-of-concept overhead only. "
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
