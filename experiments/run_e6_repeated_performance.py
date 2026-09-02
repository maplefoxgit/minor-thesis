#!/usr/bin/env python3
"""Measure repeated verification cost for the three E6 policy conditions."""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import statistics
import subprocess
import sys
import time
import tracemalloc
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for candidate in (ROOT, SRC):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from _common import (  # noqa: E402
    POLICIES_DIR,
    QUERIES_PATH,
    TOPOLOGY_PATH,
    compile_baseline_to_repository,
)
from oran_slice_security.graph_builder import build_graph_from_paths  # noqa: E402
from oran_slice_security.io import load_yaml_file  # noqa: E402
from oran_slice_security.verifier import (  # noqa: E402
    load_verification_queries,
    verify_graph,
)
from run_e6_controlled_baselines import (  # noqa: E402
    DENY_ALL_CONDITION,
    PERMISSIVE_CONDITION,
    PROPOSED_CONDITION,
    _deny_all_graph,
    _permissive_graph,
    _summarize_condition,
)


JSON_PATH = ROOT / "results" / "metrics" / "baseline_performance_repeated.json"
CSV_PATH = ROOT / "results" / "metrics" / "baseline_performance_repeated.csv"
MARKDOWN_PATH = ROOT / "results" / "reports" / "baseline_performance_repeated.md"
CONDITION_ORDER = (
    PERMISSIVE_CONDITION,
    DENY_ALL_CONDITION,
    PROPOSED_CONDITION,
)


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
    }


def _measure_batch(
    graph: Any,
    queries_document: dict[str, Any],
    iterations: int,
) -> dict[str, Any]:
    wall_start = time.perf_counter()
    cpu_start = time.process_time()
    last_report: dict[str, Any] | None = None
    for _ in range(iterations):
        last_report = verify_graph(graph, queries_document)
    cpu_seconds = time.process_time() - cpu_start
    wall_seconds = time.perf_counter() - wall_start

    tracemalloc.start()
    for _ in range(iterations):
        verify_graph(graph, queries_document)
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    if last_report is None:
        raise RuntimeError("verification batch did not run")
    return {
        "batch_iterations": iterations,
        "batch_wall_clock_seconds": wall_seconds,
        "batch_cpu_seconds": cpu_seconds,
        "wall_clock_seconds_per_verification": wall_seconds / iterations,
        "cpu_seconds_per_verification": cpu_seconds / iterations,
        "batch_peak_python_tracemalloc_bytes": peak_bytes,
        "last_report_status": last_report["overall_status"],
    }


def _render_markdown(document: dict[str, Any]) -> str:
    lines = [
        "# Repeated E6 Verification Performance",
        "",
        "## Result",
        "",
        (
            "The same eight nodes, seven queries, verifier implementation, Python "
            "process, warm-up count, trial count, and batch size were used for all "
            "three conditions. Only the permitted communication edges changed."
        ),
        "",
        "| Condition | Edges | Functional outcome | Median pure verification | Interquartile range |",
        "| --- | ---: | --- | ---: | ---: |",
    ]
    for condition_id in CONDITION_ORDER:
        condition = document["conditions"][condition_id]
        timing = condition["wall_clock_seconds_per_verification"]
        functional = (
            "balanced pass"
            if condition["functional_result"]["balanced_objective_passed"]
            else "balanced fail"
        )
        lines.append(
            "| {name} | {edges} | {functional} | {median:.4f} ms | {q1:.4f} to {q3:.4f} ms |".format(
                name=condition_id,
                edges=condition["functional_result"]["graph_edge_count"],
                functional=functional,
                median=timing["median"] * 1000.0,
                q1=timing["q1"] * 1000.0,
                q3=timing["q3"] * 1000.0,
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            document["interpretation"],
            "",
            "## Measurement boundary",
            "",
            document["measurement_boundary"],
            "",
            "## Comparison boundary",
            "",
            document["comparison_boundary"],
            "",
        ]
    )
    return "\n".join(lines)


def run(warmups: int, trials: int, iterations: int) -> dict[str, Any]:
    topology_document = load_yaml_file(TOPOLOGY_PATH)
    queries_document = load_verification_queries(QUERIES_PATH)
    compile_baseline_to_repository()
    graphs = {
        PERMISSIVE_CONDITION: _permissive_graph(topology_document),
        DENY_ALL_CONDITION: _deny_all_graph(topology_document),
        PROPOSED_CONDITION: build_graph_from_paths(TOPOLOGY_PATH, POLICIES_DIR),
    }
    functional_results = {
        condition_id: _summarize_condition(
            condition_id,
            "Functional result retained from the controlled E6 condition.",
            graph,
            queries_document,
        )
        for condition_id, graph in graphs.items()
    }

    for _ in range(warmups):
        for condition_id in CONDITION_ORDER:
            _measure_batch(graphs[condition_id], queries_document, iterations)

    rows: list[dict[str, Any]] = []
    for trial in range(1, trials + 1):
        rotation = (trial - 1) % len(CONDITION_ORDER)
        trial_order = CONDITION_ORDER[rotation:] + CONDITION_ORDER[:rotation]
        for condition_id in trial_order:
            measurement = _measure_batch(
                graphs[condition_id],
                queries_document,
                iterations,
            )
            rows.append(
                {
                    "trial": trial,
                    "condition": condition_id,
                    **measurement,
                }
            )

    conditions: dict[str, Any] = {}
    for condition_id in CONDITION_ORDER:
        condition_rows = [row for row in rows if row["condition"] == condition_id]
        functional = functional_results[condition_id]
        conditions[condition_id] = {
            "functional_result": {
                "graph_node_count": functional["graph_node_count"],
                "graph_edge_count": functional["graph_edge_count"],
                "required_reachability_rate": functional[
                    "required_reachability_rate"
                ],
                "forbidden_path_block_rate": functional[
                    "forbidden_path_block_rate"
                ],
                "terminal_service_passed": functional["terminal_service_passed"],
                "balanced_objective_passed": functional[
                    "balanced_objective_passed"
                ],
            },
            "wall_clock_seconds_per_verification": _summary(
                row["wall_clock_seconds_per_verification"] for row in condition_rows
            ),
            "cpu_seconds_per_verification": _summary(
                row["cpu_seconds_per_verification"] for row in condition_rows
            ),
            "batch_peak_python_tracemalloc_bytes": _summary(
                row["batch_peak_python_tracemalloc_bytes"] for row in condition_rows
            ),
        }

    document = {
        "study_id": "E6-P",
        "title": "Repeated verification cost for controlled E6 conditions",
        "status": "pass",
        "warmup_batches_per_condition": warmups,
        "measured_batches_per_condition": trials,
        "verifications_per_batch": iterations,
        "environment": _environment(),
        "controlled_variables": {
            "node_count": 8,
            "query_count": 7,
            "verification_algorithm": "deterministic breadth-first search",
            "measurement_function": "verify_graph on a prebuilt graph and preloaded queries",
            "changed_factor": "permitted communication-edge condition",
        },
        "conditions": conditions,
        "trials": rows,
        "interpretation": (
            "This experiment adds execution-cost measurements to the existing E6 "
            "functional comparison. The compiled-policy condition remains the only "
            "condition that satisfies the balanced functional objective. Timing values "
            "describe the cost of evaluating each local graph condition and are not an "
            "effectiveness score."
        ),
        "measurement_boundary": (
            "Each retained value is the batch elapsed or processor time divided by the "
            "number of pure verify_graph calls. Graph construction, query loading, file "
            "input and output, and report generation are excluded. Timing batches run "
            "without tracemalloc. A separate repeated batch records peak Python allocation "
            "and does not represent process memory."
        ),
        "comparison_boundary": (
            "The three local conditions can be compared with one another because their "
            "measurement protocol is controlled. They cannot be ranked directly against "
            "INTPOL or Scylla because the workloads, algorithms, hardware, execution "
            "boundaries, and summary statistics differ."
        ),
    }

    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    MARKDOWN_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    with CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0].keys()),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    MARKDOWN_PATH.write_text(_render_markdown(document), encoding="utf-8")
    return document


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--warmups", type=int, default=5)
    parser.add_argument("--trials", type=int, default=30)
    parser.add_argument("--iterations", type=int, default=500)
    args = parser.parse_args()
    if args.warmups < 0 or args.trials < 4 or args.iterations < 1:
        parser.error(
            "warmups must be non-negative, trials at least 4, and iterations at least 1"
        )
    document = run(args.warmups, args.trials, args.iterations)
    print(json.dumps(document, indent=2))
    return 0 if document["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
