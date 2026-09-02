#!/usr/bin/env python3
"""Run a bounded N-slice scaling study of the existing verifier layer.

The study uses deterministic synthetic graphs with the same structural
property as the two-slice baseline. It does not claim that the current intent
schema or compiler supports more than two slices.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import resource
import statistics
import subprocess
import sys
import time
import tracemalloc
from pathlib import Path
from typing import Any, Callable, Iterable


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for candidate in (ROOT, SRC):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from oran_slice_security.scaling import (  # noqa: E402
    MultisliceVerifierFixture,
    build_faulty_multislice_verifier_fixture,
    build_multislice_verifier_fixture,
)
from oran_slice_security.verifier import verify_graph  # noqa: E402


JSON_PATH = ROOT / "results" / "metrics" / "multislice_verifier_scaling.json"
CSV_PATH = ROOT / "results" / "metrics" / "multislice_verifier_scaling.csv"
MARKDOWN_PATH = ROOT / "results" / "reports" / "multislice_verifier_scaling.md"


def _summary(values: Iterable[float | int]) -> dict[str, float | int]:
    data = [float(value) for value in values]
    if not data:
        raise ValueError("cannot summarise an empty sequence")
    q1, median, q3 = statistics.quantiles(data, n=4, method="inclusive")
    mean = statistics.fmean(data)
    stdev = statistics.stdev(data) if len(data) > 1 else 0.0
    return {
        "n": len(data),
        "min": min(data),
        "q1": q1,
        "median": median,
        "mean": mean,
        "q3": q3,
        "max": max(data),
        "stdev": stdev,
        "coefficient_of_variation": stdev / mean if mean else 0.0,
    }


def _measure(callable_: Callable[[], Any]) -> tuple[Any, dict[str, float | int]]:
    tracemalloc.start()
    wall_start = time.perf_counter()
    cpu_start = time.process_time()
    value = callable_()
    cpu_seconds = time.process_time() - cpu_start
    wall_seconds = time.perf_counter() - wall_start
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return value, {
        "wall_clock_seconds": wall_seconds,
        "cpu_seconds": cpu_seconds,
        "peak_python_tracemalloc_bytes": peak_bytes,
    }


def _normalised_peak_rss_bytes() -> int:
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if sys.platform == "darwin" else value * 1024


def _run_rss_worker(slice_count: int) -> int:
    fixture = build_multislice_verifier_fixture(slice_count)
    report = verify_graph(fixture.graph, fixture.queries)
    print(
        json.dumps(
            {
                "slice_count": slice_count,
                "status": report["overall_status"],
                "peak_process_rss_bytes": _normalised_peak_rss_bytes(),
            }
        )
    )
    return 0 if report["overall_status"] == "pass" else 1


def _isolated_rss_samples(slice_count: int, count: int) -> list[int]:
    samples: list[int] = []
    for _ in range(count):
        completed = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--rss-worker", str(slice_count)],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        worker_result = json.loads(completed.stdout)
        if worker_result["status"] != "pass":
            raise RuntimeError(f"RSS worker failed for {slice_count} slices")
        samples.append(int(worker_result["peak_process_rss_bytes"]))
    return samples


def _environment() -> dict[str, Any]:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    ).stdout.strip()
    return {
        "captured_utc": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "logical_cpu_count": os.cpu_count(),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "git_commit": commit or None,
        "git_status_porcelain": subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=ROOT,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        ).stdout.strip(),
    }


def _run_one_size(
    slice_count: int,
    warmups: int,
    trials: int,
    rss_trials: int,
) -> dict[str, Any]:
    negative_fixture = build_faulty_multislice_verifier_fixture(slice_count)
    negative_report = verify_graph(negative_fixture.graph, negative_fixture.queries)
    failed_forbidden_count = sum(
        result["status"] == "fail"
        for result in negative_report["forbidden_unreachable"]
    )
    negative_control_passed = (
        negative_report["overall_status"] == "fail" and failed_forbidden_count >= 1
    )
    if not negative_control_passed:
        raise RuntimeError(f"negative control was not detected for {slice_count} slices")

    for _ in range(warmups):
        fixture = build_multislice_verifier_fixture(slice_count)
        report = verify_graph(fixture.graph, fixture.queries)
        if report["overall_status"] != "pass":
            raise RuntimeError(f"warm-up failed for {slice_count} slices")

    rows: list[dict[str, float | int | str]] = []
    fixture: MultisliceVerifierFixture | None = None
    for trial in range(1, trials + 1):
        fixture, build_metrics = _measure(
            lambda: build_multislice_verifier_fixture(slice_count)
        )
        report, verify_metrics = _measure(
            lambda: verify_graph(fixture.graph, fixture.queries)
        )
        if report["overall_status"] != "pass":
            raise RuntimeError(f"trial {trial} failed for {slice_count} slices")
        rows.append(
            {
                "slice_count": slice_count,
                "trial": trial,
                "status": report["overall_status"],
                "model_build_wall_clock_seconds": build_metrics["wall_clock_seconds"],
                "model_build_cpu_seconds": build_metrics["cpu_seconds"],
                "model_build_peak_python_tracemalloc_bytes": build_metrics[
                    "peak_python_tracemalloc_bytes"
                ],
                "verification_wall_clock_seconds": verify_metrics["wall_clock_seconds"],
                "verification_cpu_seconds": verify_metrics["cpu_seconds"],
                "verification_peak_python_tracemalloc_bytes": verify_metrics[
                    "peak_python_tracemalloc_bytes"
                ],
                "property_criteria_per_second": (
                    fixture.total_check_count
                    / float(verify_metrics["wall_clock_seconds"])
                ),
                "path_searches_per_second": (
                    fixture.path_search_invocation_count
                    / float(verify_metrics["wall_clock_seconds"])
                ),
            }
        )

    if fixture is None:
        raise RuntimeError("no measured trials were run")

    rss_samples = _isolated_rss_samples(slice_count, rss_trials)
    result = {
        "slice_count": slice_count,
        "status": "pass" if negative_control_passed else "fail",
        "graph_node_count": len(fixture.graph.nodes),
        "graph_edge_count": len(fixture.graph.edges),
        "rule_equivalent_count": fixture.rule_equivalent_count,
        "required_query_count": fixture.required_query_count,
        "forbidden_query_count": fixture.forbidden_query_count,
        "terminal_query_count": fixture.terminal_query_count,
        "total_check_count": fixture.total_check_count,
        "path_search_invocation_count": fixture.path_search_invocation_count,
        "negative_control": {
            "changed_factor": (
                "one direct edge from slice_001_workload to slice_002_workload"
            ),
            "expected_status": "fail",
            "actual_status": negative_report["overall_status"],
            "failed_forbidden_query_count": failed_forbidden_count,
            "control_passed": negative_control_passed,
        },
        "model_build_wall_clock_seconds": _summary(
            row["model_build_wall_clock_seconds"] for row in rows
        ),
        "verification_wall_clock_seconds": _summary(
            row["verification_wall_clock_seconds"] for row in rows
        ),
        "verification_cpu_seconds": _summary(
            row["verification_cpu_seconds"] for row in rows
        ),
        "verification_peak_python_tracemalloc_bytes": _summary(
            row["verification_peak_python_tracemalloc_bytes"] for row in rows
        ),
        "isolated_worker_peak_process_rss_bytes": _summary(rss_samples),
        "property_criteria_per_second": _summary(
            row["property_criteria_per_second"] for row in rows
        ),
        "path_searches_per_second": _summary(
            row["path_searches_per_second"] for row in rows
        ),
        "trials": rows,
    }
    return result


def _write_outputs(document: dict[str, Any]) -> None:
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    MARKDOWN_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

    flat_rows: list[dict[str, Any]] = []
    for result in document["results"]:
        flat_rows.append(
            {
                "slice_count": result["slice_count"],
                "status": result["status"],
                "graph_node_count": result["graph_node_count"],
                "graph_edge_count": result["graph_edge_count"],
                "rule_equivalent_count": result["rule_equivalent_count"],
                "required_query_count": result["required_query_count"],
                "forbidden_query_count": result["forbidden_query_count"],
                "total_check_count": result["total_check_count"],
                "path_search_invocation_count": result[
                    "path_search_invocation_count"
                ],
                "negative_control_passed": result["negative_control"][
                    "control_passed"
                ],
                "median_model_build_ms": result["model_build_wall_clock_seconds"][
                    "median"
                ]
                * 1000.0,
                "median_verification_ms": result["verification_wall_clock_seconds"][
                    "median"
                ]
                * 1000.0,
                "verification_q1_ms": result["verification_wall_clock_seconds"]["q1"]
                * 1000.0,
                "verification_q3_ms": result["verification_wall_clock_seconds"]["q3"]
                * 1000.0,
                "median_property_criteria_per_second": result[
                    "property_criteria_per_second"
                ]["median"],
                "median_path_searches_per_second": result[
                    "path_searches_per_second"
                ]["median"],
                "median_python_peak_bytes": result[
                    "verification_peak_python_tracemalloc_bytes"
                ]["median"],
                "median_process_peak_rss_bytes": result[
                    "isolated_worker_peak_process_rss_bytes"
                ]["median"],
            }
        )
    with CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(flat_rows[0].keys()))
        writer.writeheader()
        writer.writerows(flat_rows)

    lines = [
        "# Bounded Multi-Slice Verifier Scaling Study",
        "",
        "## Result",
        "",
        (
            "The existing graph verifier passed every required, forbidden, and terminal "
            "check for deterministic synthetic scenarios containing 2, 3, 4, and 10 "
            "slices. No functional breaking point was observed within that tested range."
        ),
        "",
        "| Slices | Nodes | Edges | Estimated rules | Property criteria | Path searches | Negative control | Median pure verification | Median path searches per second | Median worker peak RSS |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |",
    ]
    for result in document["results"]:
        lines.append(
            "| {slices} | {nodes} | {edges} | {rules} | {checks} | {searches} | {negative} | {time:.3f} ms | {rate:,.0f} | {rss:.2f} MiB |".format(
                slices=result["slice_count"],
                nodes=result["graph_node_count"],
                edges=result["graph_edge_count"],
                rules=result["rule_equivalent_count"],
                checks=result["total_check_count"],
                searches=result["path_search_invocation_count"],
                negative="pass" if result["negative_control"]["control_passed"] else "fail",
                time=result["verification_wall_clock_seconds"]["median"] * 1000.0,
                rate=result["path_searches_per_second"]["median"],
                rss=result["isolated_worker_peak_process_rss_bytes"]["median"]
                / (1024.0 * 1024.0),
            )
        )
    lines.extend(
        [
            "",
            "## Measurement boundary",
            "",
            (
                "Pure verification time measures verify_graph on a prebuilt graph and "
                "preloaded queries. Model-build time measures only this study's synthetic "
                "fixture construction. Peak resident memory is the maximum for an isolated "
                "Python worker that imports the package, builds one fixture, and verifies it. "
                "Property criteria count reported outcomes. Path-search invocations count "
                "every breadth-first search, including one terminal-service search per workload."
            ),
            (
                "The estimated rule count uses 2N squared plus N for the pairwise policy "
                "shape. It is analytical only because this verifier-only study does not "
                "compile N-slice policy files."
            ),
            "",
            "## Comparison boundary",
            "",
            document["comparison_boundary"],
            "",
            "## Scope boundary",
            "",
            document["scope_boundary"],
            "",
        ]
    )
    MARKDOWN_PATH.write_text("\n".join(lines), encoding="utf-8")


def run(
    slice_counts: list[int],
    warmups: int,
    trials: int,
    rss_trials: int,
) -> dict[str, Any]:
    results = [
        _run_one_size(slice_count, warmups, trials, rss_trials)
        for slice_count in slice_counts
    ]
    status = "pass" if all(result["status"] == "pass" for result in results) else "fail"
    document = {
        "study_id": "S1",
        "title": "Bounded multi-slice verifier scaling",
        "status": status,
        "slice_counts": slice_counts,
        "warmup_runs_per_size": warmups,
        "measured_runs_per_size": trials,
        "isolated_rss_runs_per_size": rss_trials,
        "environment": _environment(),
        "results": results,
        "breaking_point_result": (
            "No functional breaking point was observed within the predefined 2, 3, 4, "
            "and 10-slice range, and each injected cross-slice route was detected. A "
            "capacity breaking point was not claimed because no "
            "time or memory failure threshold was predeclared."
        ),
        "comparison_boundary": (
            "The metric families align with verification studies such as Scylla: model "
            "size, rule-equivalent count, query count, pure verification time, throughput, "
            "and process memory. The workloads, hardware, implementation, architecture, "
            "and repetition rules are different, so no speed or memory ratio is valid."
        ),
        "scope_boundary": (
            "This is a verifier-layer scale study using generated in-memory graphs. It "
            "does not show that the current two-slice intent schema, semantic validator, "
            "compiler, or graph loader supports more than two slices."
        ),
    }
    _write_outputs(document)
    return document


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--slices",
        nargs="+",
        type=int,
        default=[2, 3, 4, 10],
        help="Slice counts to test (default: 2 3 4 10)",
    )
    parser.add_argument("--warmups", type=int, default=5)
    parser.add_argument("--trials", type=int, default=30)
    parser.add_argument("--rss-trials", type=int, default=3)
    parser.add_argument("--rss-worker", type=int, default=None, help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.rss_worker is not None:
        return _run_rss_worker(args.rss_worker)
    if any(slice_count < 2 for slice_count in args.slices):
        parser.error("all slice counts must be at least 2")
    if args.warmups < 0 or args.trials < 4 or args.rss_trials < 1:
        parser.error("warmups must be non-negative, trials at least 4, and rss-trials at least 1")

    document = run(args.slices, args.warmups, args.trials, args.rss_trials)
    print(json.dumps(document, indent=2))
    return 0 if document["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
