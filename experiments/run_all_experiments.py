from __future__ import annotations

from typing import Any

from _common import (
    EXPERIMENT_SUMMARY_JSON,
    EXPERIMENT_SUMMARY_MD,
    OVERHEAD_METRICS_JSON,
    REPORTS_DIR,
    print_json,
    write_json,
    write_markdown,
)
from run_e1_schema_expressiveness import run as run_e1
from run_e2_compiler_coherence import run as run_e2
from run_e3_reachability_verification import run as run_e3
from run_e4_negative_controls import run as run_e4
from run_e5_overhead import run as run_e5


EXPERIMENT_ORDER = [
    ("E1", run_e1),
    ("E2", run_e2),
    ("E3", run_e3),
    ("E4", run_e4),
    ("E5", run_e5),
]


def run() -> dict[str, Any]:
    experiment_results = {experiment_id: runner() for experiment_id, runner in EXPERIMENT_ORDER}
    pass_count = sum(result["status"] == "pass" for result in experiment_results.values())
    fail_count = len(experiment_results) - pass_count
    overall_status = "pass" if fail_count == 0 else "fail"

    summary_document = {
        "overall_status": overall_status,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "experiments": experiment_results,
        "bounded_claim": (
            "The evidence supports only bounded, local, model-based validation, compilation, "
            "static non-reachability verification, negative-control rejection, and modest "
            "local overhead reporting."
        ),
        "result_files": {
            "verification_report_json": str(REPORTS_DIR / "verification_report.json"),
            "verification_report_md": str(REPORTS_DIR / "verification_report.md"),
            "experiment_summary_json": str(EXPERIMENT_SUMMARY_JSON),
            "experiment_summary_md": str(EXPERIMENT_SUMMARY_MD),
            "overhead_metrics_json": str(OVERHEAD_METRICS_JSON),
        },
    }
    write_json(EXPERIMENT_SUMMARY_JSON, summary_document)
    write_markdown(EXPERIMENT_SUMMARY_MD, render_experiment_summary_markdown(summary_document))
    return summary_document


def render_experiment_summary_markdown(summary_document: dict[str, Any]) -> str:
    lines: list[str] = [
        "# Experiment Summary",
        "",
        "## Summary",
        f"- Overall status: `{summary_document['overall_status']}`",
        f"- Passed experiments: {summary_document['pass_count']}",
        f"- Failed experiments: {summary_document['fail_count']}",
        (
            "- Thesis interpretation: the bounded proof of concept demonstrates only local, "
            "model-based evidence for the fixed two-slice scenario and does not claim "
            "production assurance."
        ),
        "",
        "## Experiment Results",
    ]

    for experiment_id, result in summary_document["experiments"].items():
        lines.append(f"### {experiment_id} {result['title']}")
        lines.append(f"- Status: `{result['status']}`")

        if experiment_id == "E1":
            lines.append(f"- Schema coverage: {result['schema_coverage']:.2f}")
            lines.append(f"- Ambiguity count: {result['ambiguity_count']}")
            lines.append(f"- Unsupported case count: {result['unsupported_case_count']}")
            for case_result in result["case_results"]:
                lines.append(
                    f"- {case_result['case_id']}: `{case_result['status']}`; {case_result['reason']}"
                )

        if experiment_id == "E2":
            lines.append(f"- Policy artefact count: {result['policy_artifact_count']}")
            lines.append(f"- Unresolved conflict count: {result['unresolved_conflict_count']}")
            for check_name, passed in result["check_results"].items():
                lines.append(f"- {check_name}: `{passed}`")

        if experiment_id == "E3":
            report = result["verification_report"]
            lines.append(
                f"- Required reachable checks passed: {result['required_reachable_pass_count']}"
            )
            lines.append(
                f"- Forbidden unreachable checks passed: {result['forbidden_unreachable_pass_count']}"
            )
            lines.append(
                f"- Graph size: nodes={report['graph_node_count']}, edges={report['graph_edge_count']}"
            )
            for reachable in report["required_reachable"]:
                path_text = " -> ".join(reachable["path"]) if reachable["path"] else "No path found"
                lines.append(
                    f"- Required path {reachable['source']} -> {reachable['destination']}: "
                    f"`{reachable['status']}`; {path_text}"
                )

        if experiment_id == "E4":
            for control in result["control_results"]:
                lines.append(
                    f"- {control['topology']}: `{control['status']}`; {control['reason']}"
                )

        if experiment_id == "E5":
            lines.append(
                f"- Graph size: nodes={result['graph_node_count']}, edges={result['graph_edge_count']}"
            )
            lines.append(f"- Generated rule count: {result['generated_rule_count']}")
            lines.append(
                f"- Peak memory (max stage): {result['peak_memory_bytes_max']} bytes"
            )
            lines.append(
                f"- Overall wall-clock time: {result['overall_wall_clock_seconds']:.6f} seconds"
            )
            lines.append(
                f"- Overall CPU time: {result['overall_cpu_seconds']:.6f} seconds"
            )
            lines.append(f"- Local overhead note: {result['local_overhead_statement']}")

        lines.append("")

    lines.extend(
        [
            "## Result Files",
            f"- Verification report JSON: `{summary_document['result_files']['verification_report_json']}`",
            f"- Verification report Markdown: `{summary_document['result_files']['verification_report_md']}`",
            f"- Experiment summary JSON: `{summary_document['result_files']['experiment_summary_json']}`",
            f"- Experiment summary Markdown: `{summary_document['result_files']['experiment_summary_md']}`",
            f"- Overhead metrics JSON: `{summary_document['result_files']['overhead_metrics_json']}`",
            "",
            "## Limitations",
            (
                "This evidence proves only bounded, model-based static behavior in the local "
                "proof-of-concept representation. It does not establish runtime security, "
                "packet delivery outcomes, live O-RAN control behavior, or production "
                "scalability."
            ),
            "",
        ]
    )

    return "\n".join(lines)


def main() -> int:
    summary_document = run()
    print_json(summary_document)
    return 0 if summary_document["overall_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
