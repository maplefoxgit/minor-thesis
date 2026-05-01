from __future__ import annotations

from pathlib import Path
from typing import Any

from .io import dump_json_file


JSON_REPORT_FILENAME = "verification_report.json"
MARKDOWN_REPORT_FILENAME = "verification_report.md"


def write_verification_reports(
    report_document: dict[str, Any], output_directory: str | Path
) -> dict[str, Path]:
    """Write deterministic JSON and Markdown verification reports."""
    target_directory = Path(output_directory)
    target_directory.mkdir(parents=True, exist_ok=True)

    json_path = target_directory / JSON_REPORT_FILENAME
    markdown_path = target_directory / MARKDOWN_REPORT_FILENAME

    dump_json_file(json_path, report_document)
    markdown_path.write_text(render_markdown_report(report_document), encoding="utf-8")

    return {
        "json_report": json_path,
        "markdown_report": markdown_path,
    }


def render_markdown_report(report_document: dict[str, Any]) -> str:
    """Render a thesis-readable Markdown report."""
    lines: list[str] = [
        "# Verification Report",
        "",
        "## Summary",
        f"- Overall status: `{report_document['overall_status']}`",
        (
            "- Bounded static assurance claim: the local policy-and-topology model preserves "
            "the intended slice-to-`shared_auth_log` reachability while blocking modeled "
            "cross-slice reachability."
        ),
        "",
        "## Required Paths",
    ]

    for result in report_document["required_reachable"]:
        path_text = _format_path(result["path"]) if result["path"] else "No path found"
        lines.append(
            f"- `{result['source']}` -> `{result['destination']}`: `{result['status']}`; {path_text}"
        )

    lines.extend(["", "## Forbidden Paths"])
    for result in report_document["forbidden_unreachable"]:
        if result["violation_path"]:
            detail = _format_path(result["violation_path"])
        else:
            detail = "No path found"
        lines.append(
            f"- `{result['source']}` -> `{result['destination']}`: `{result['status']}`; {detail}"
        )

    lines.extend(["", "## Negative-Control Status"])
    for result in report_document["terminal_service_transit"]:
        if result["violation_paths"]:
            detail = "; ".join(_format_path(entry["path"]) for entry in result["violation_paths"])
        else:
            detail = "No transit path detected"
        lines.append(
            f"- Terminal service `{result['service']}`: `{result['status']}`; outgoing_edges="
            f"{result['outgoing_edges']}; {detail}"
        )

    lines.extend(
        [
            "",
            "## Graph Size",
            f"- Nodes: {report_document['graph_node_count']}",
            f"- Edges: {report_document['graph_edge_count']}",
            "",
            "## Limitations Statement",
            (
                "This proves only model-based static non-reachability in the local "
                "policy-and-topology model. It does not establish runtime enforcement, live "
                "O-RAN control behavior, packet-level outcomes, or production assurance."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def _format_path(path: list[str]) -> str:
    return " -> ".join(f"`{node}`" for node in path)
