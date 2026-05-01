from __future__ import annotations

from pathlib import Path

from oran_slice_security.compiler import compile_policy_bundle
from oran_slice_security.io import load_json_file
from oran_slice_security.report import JSON_REPORT_FILENAME, MARKDOWN_REPORT_FILENAME
from oran_slice_security.verifier import verify_from_paths


ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schemas" / "slice_security_intent.schema.json"
INTENT_PATH = ROOT / "intents" / "two_slice_shared_auth_log.valid.yaml"
TOPOLOGY_PATH = ROOT / "topology" / "base_topology.yaml"
QUERIES_PATH = ROOT / "verifier" / "queries" / "baseline_queries.yaml"


def test_verification_reports_are_written_in_json_and_markdown(tmp_path: Path) -> None:
    policies_directory = tmp_path / "generated"
    reports_directory = tmp_path / "reports"
    compile_policy_bundle(SCHEMA_PATH, INTENT_PATH, TOPOLOGY_PATH, policies_directory)

    verify_from_paths(
        topology_path=TOPOLOGY_PATH,
        policies_directory=policies_directory,
        queries_path=QUERIES_PATH,
        output_directory=reports_directory,
    )

    json_report = load_json_file(reports_directory / JSON_REPORT_FILENAME)
    markdown_report = (reports_directory / MARKDOWN_REPORT_FILENAME).read_text(
        encoding="utf-8"
    )

    assert json_report["overall_status"] == "pass"
    assert "## Summary" in markdown_report
    assert "## Required Paths" in markdown_report
    assert "## Forbidden Paths" in markdown_report
    assert "## Negative-Control Status" in markdown_report
    assert "This proves only model-based static non-reachability" in markdown_report
