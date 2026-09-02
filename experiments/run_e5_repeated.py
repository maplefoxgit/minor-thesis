#!/usr/bin/env python3
"""Repeat the existing E5 overhead experiment and summarise run-to-run variation.

Run this script from the repository root after installing the project:

    source .venv/bin/activate
    python /path/to/run_e5_repeated.py --warmups 5 --trials 30

Outputs are written to results/metrics/overhead_repeated.json and
results/metrics/overhead_repeated.csv. The original committed
results/metrics/overhead_metrics.json is restored after the repeated run.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import statistics
import subprocess
import time
import sys
from pathlib import Path
from typing import Any, Iterable


STAGES = (
    "validation_time",
    "compile_time",
    "graph_construction_time",
    "query_loading_time",
    "verification_time",
    "report_generation_time",
)
METRICS = ("wall_clock_seconds", "cpu_seconds", "peak_python_tracemalloc_bytes")


def _run_command(command: list[str]) -> str | None:
    try:
        completed = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    value = completed.stdout.strip()
    return value or None


def _environment(repo_root: Path) -> dict[str, Any]:
    cpu_brand = _run_command(["sysctl", "-n", "machdep.cpu.brand_string"])
    if cpu_brand is None:
        cpu_brand = platform.processor() or None

    return {
        "captured_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": cpu_brand,
        "logical_cpu_count": os.cpu_count(),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "python_executable": (
            str(Path(sys.executable).relative_to(repo_root))
            if Path(sys.executable).is_absolute() and repo_root in Path(sys.executable).parents
            else Path(sys.executable).name
        ),
        "git_commit": _run_command(["git", "-C", str(repo_root), "rev-parse", "HEAD"]),
        "git_status_porcelain": _run_command(["git", "-C", str(repo_root), "status", "--porcelain"]) or "",
    }


def _summary(values: Iterable[float | int]) -> dict[str, float | int]:
    data = [float(value) for value in values]
    if not data:
        raise ValueError("Cannot summarise an empty sequence")

    q1, q2, q3 = statistics.quantiles(data, n=4, method="inclusive")
    mean = statistics.fmean(data)
    stdev = statistics.stdev(data) if len(data) > 1 else 0.0
    return {
        "n": len(data),
        "min": min(data),
        "q1": q1,
        "median": q2,
        "mean": mean,
        "q3": q3,
        "max": max(data),
        "stdev": stdev,
        "coefficient_of_variation": (stdev / mean) if mean else 0.0,
    }


def _flatten_trial(index: int, trial: dict[str, Any]) -> dict[str, Any]:
    row: dict[str, Any] = {
        "trial": index,
        "status": trial["status"],
        "summed_stage_wall_clock_seconds": trial["overall_wall_clock_seconds"],
        "summed_stage_cpu_seconds": trial["overall_cpu_seconds"],
        "end_to_end_wall_clock_seconds": trial["_end_to_end_wall_clock_seconds"],
        "end_to_end_cpu_seconds": trial["_end_to_end_cpu_seconds"],
        "peak_python_tracemalloc_bytes_max": trial["peak_python_tracemalloc_bytes_max"],
        "generated_rule_count": trial["generated_rule_count"],
        "graph_node_count": trial["graph_node_count"],
        "graph_edge_count": trial["graph_edge_count"],
    }
    for stage in STAGES:
        for metric in METRICS:
            row[f"{stage}.{metric}"] = trial[stage][metric]
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--warmups", type=int, default=5, help="Warm-up runs excluded from analysis (default: 5)")
    parser.add_argument("--trials", type=int, default=30, help="Measured runs (default: 30)")
    args = parser.parse_args()

    if args.warmups < 0:
        parser.error("--warmups must be zero or greater")
    if args.trials < 4:
        parser.error("--trials must be at least 4 so quartiles are meaningful")

    repo_root = Path.cwd().resolve()
    required = [
        repo_root / "pyproject.toml",
        repo_root / "experiments" / "run_e5_overhead.py",
        repo_root / "results" / "metrics",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        print("Run this script from the minor-thesis repository root.", file=sys.stderr)
        print("Missing: " + ", ".join(missing), file=sys.stderr)
        return 2

    experiments_dir = repo_root / "experiments"
    sys.path.insert(0, str(experiments_dir))
    try:
        from run_e5_overhead import run as run_e5  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover - user environment diagnostic
        print(f"Could not import the E5 experiment: {exc}", file=sys.stderr)
        print("Activate the repository virtual environment and run `make install` first.", file=sys.stderr)
        return 2

    metrics_dir = repo_root / "results" / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    existing_metrics_path = metrics_dir / "overhead_metrics.json"
    existing_bytes = existing_metrics_path.read_bytes() if existing_metrics_path.exists() else None

    measured: list[dict[str, Any]] = []
    try:
        for index in range(args.warmups):
            warmup = run_e5()
            if warmup.get("status") != "pass":
                raise RuntimeError(f"Warm-up run {index + 1} failed: {warmup}")

        for index in range(args.trials):
            wall_start = time.perf_counter()
            cpu_start = time.process_time()
            trial = run_e5()
            trial["_end_to_end_cpu_seconds"] = time.process_time() - cpu_start
            trial["_end_to_end_wall_clock_seconds"] = time.perf_counter() - wall_start
            if trial.get("status") != "pass":
                raise RuntimeError(f"Measured run {index + 1} failed: {trial}")
            measured.append(trial)
            print(
                f"trial {index + 1:02d}/{args.trials}: "
                f"end-to-end={trial['_end_to_end_wall_clock_seconds']:.6f}s, "
                f"stage-sum={trial['overall_wall_clock_seconds']:.6f}s, "
                f"cpu={trial['overall_cpu_seconds']:.6f}s, "
                f"peak={trial['peak_python_tracemalloc_bytes_max']}B"
            )
    finally:
        if existing_bytes is None:
            existing_metrics_path.unlink(missing_ok=True)
        else:
            existing_metrics_path.write_bytes(existing_bytes)

    invariant_fields = ("generated_rule_count", "graph_node_count", "graph_edge_count")
    invariant_values = {
        field: sorted({int(trial[field]) for trial in measured})
        for field in invariant_fields
    }
    if any(len(values) != 1 for values in invariant_values.values()):
        print(f"Invariant drift detected: {invariant_values}", file=sys.stderr)
        return 1

    summaries: dict[str, Any] = {
        "end_to_end_wall_clock_seconds": _summary(
            trial["_end_to_end_wall_clock_seconds"] for trial in measured
        ),
        "end_to_end_cpu_seconds": _summary(
            trial["_end_to_end_cpu_seconds"] for trial in measured
        ),
        "summed_stage_wall_clock_seconds": _summary(
            trial["overall_wall_clock_seconds"] for trial in measured
        ),
        "summed_stage_cpu_seconds": _summary(
            trial["overall_cpu_seconds"] for trial in measured
        ),
        "peak_python_tracemalloc_bytes_max": _summary(
            trial["peak_python_tracemalloc_bytes_max"] for trial in measured
        ),
        "stages": {},
    }
    for stage in STAGES:
        summaries["stages"][stage] = {
            metric: _summary(trial[stage][metric] for trial in measured)
            for metric in METRICS
        }

    output = {
        "experiment_id": "E5-repeated",
        "title": "Repeated practical-overhead validation",
        "status": "pass",
        "warmup_runs": args.warmups,
        "measured_runs": args.trials,
        "environment": _environment(repo_root),
        "functional_invariants": {
            field: values[0] for field, values in invariant_values.items()
        },
        "memory_measurement_basis": "Python tracemalloc peak bytes (not process RSS)",
        "profiling_protocol": (
            "Each stage timing is measured without tracemalloc. Each stage is then "
            "repeated separately with tracemalloc enabled to obtain its Python allocation peak."
        ),
        "summary": summaries,
        "trials": [_flatten_trial(index + 1, trial) for index, trial in enumerate(measured)],
        "timing_definitions": {
            "end_to_end_wall_clock_seconds": (
                "Elapsed time around the complete existing E5 run, including orchestration, "
                "temporary-directory work, metric aggregation, and JSON writing."
            ),
            "summed_stage_wall_clock_seconds": (
                "Sum of the six stage timings reported by the E5 implementation: "
                "validation, compilation, graph construction, query loading, pure "
                "verification, and report generation. This excludes work performed "
                "between measured stages."
            ),
        },
        "interpretation_boundary": (
            "These distributions characterise repeated execution in one local environment. "
            "They do not establish production scalability or cross-platform performance."
        ),
    }

    json_path = metrics_dir / "overhead_repeated.json"
    csv_path = metrics_dir / "overhead_repeated.csv"
    json_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")

    rows = output["trials"]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary = output["summary"]
    print("\nRepeated E5 summary")
    print(f"  commit: {output['environment']['git_commit']}")
    print(
        "  wall clock: "
        f"median={summary['end_to_end_wall_clock_seconds']['median']:.6f}s, "
        f"IQR={summary['end_to_end_wall_clock_seconds']['q1']:.6f} to "
        f"{summary['end_to_end_wall_clock_seconds']['q3']:.6f}s, "
        f"range={summary['end_to_end_wall_clock_seconds']['min']:.6f} to "
        f"{summary['end_to_end_wall_clock_seconds']['max']:.6f}s"
    )
    print(
        "  summed stage wall clock: "
        f"median={summary['summed_stage_wall_clock_seconds']['median']:.6f}s"
    )
    print(
        "  peak tracemalloc: "
        f"median={summary['peak_python_tracemalloc_bytes_max']['median']:.0f}B, "
        f"IQR={summary['peak_python_tracemalloc_bytes_max']['q1']:.0f} to "
        f"{summary['peak_python_tracemalloc_bytes_max']['q3']:.0f}B"
    )
    print(f"  wrote: {json_path}")
    print(f"  wrote: {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
