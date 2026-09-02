from __future__ import annotations

import json
import sys
import time
import tracemalloc
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
for candidate in (ROOT, SRC_DIR):
    candidate_text = str(candidate)
    if candidate_text not in sys.path:
        sys.path.insert(0, candidate_text)

from oran_slice_security.compiler import (  # noqa: E402
    OCLOUD_POLICY_FILENAME,
    ORAN_POLICY_FILENAME,
    TRANSPORT_POLICY_FILENAME,
    compile_policy_bundle,
)
from oran_slice_security.graph_builder import build_graph_from_paths  # noqa: E402
from oran_slice_security.io import (  # noqa: E402
    dump_json_file,
    load_json_file,
    load_yaml_file,
    sha256_file,
)
from oran_slice_security.validation import (  # noqa: E402
    validate_intent_document,
    validate_topology_document,
)
from oran_slice_security.verifier import verify_from_paths  # noqa: E402


SCHEMA_PATH = ROOT / "schemas" / "slice_security_intent.schema.json"
VALID_INTENT_PATH = ROOT / "intents" / "two_slice_shared_auth_log.valid.yaml"
INVALID_INTENTS_DIR = ROOT / "intents" / "invalid"
TOPOLOGY_PATH = ROOT / "topology" / "base_topology.yaml"
NEGATIVE_TOPOLOGY_DIR = ROOT / "topology" / "negative_controls"
POLICIES_DIR = ROOT / "policies" / "generated"
QUERIES_PATH = ROOT / "verifier" / "queries" / "baseline_queries.yaml"
REPORTS_DIR = ROOT / "results" / "reports"
METRICS_DIR = ROOT / "results" / "metrics"
EXPERIMENT_SUMMARY_JSON = REPORTS_DIR / "experiment_summary.json"
EXPERIMENT_SUMMARY_MD = REPORTS_DIR / "experiment_summary.md"
OVERHEAD_METRICS_JSON = METRICS_DIR / "overhead_metrics.json"
BASELINE_COMPARISON_JSON = REPORTS_DIR / "baseline_comparison.json"
BASELINE_COMPARISON_MD = REPORTS_DIR / "baseline_comparison.md"
ARTIFACT_INTEGRITY_JSON = REPORTS_DIR / "artifact_integrity.json"
ARTIFACT_INTEGRITY_MD = REPORTS_DIR / "artifact_integrity.md"
GENERATED_POLICY_FILES = [
    OCLOUD_POLICY_FILENAME,
    ORAN_POLICY_FILENAME,
    TRANSPORT_POLICY_FILENAME,
]


def rel(path: str | Path) -> str:
    candidate = Path(path).resolve()
    try:
        return str(candidate.relative_to(ROOT))
    except ValueError:
        return str(path)


def ensure_output_directories() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    POLICIES_DIR.mkdir(parents=True, exist_ok=True)


def load_baseline_documents() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    schema = load_json_file(SCHEMA_PATH)
    intent = load_yaml_file(VALID_INTENT_PATH)
    topology = load_yaml_file(TOPOLOGY_PATH)
    return schema, intent, topology


def compile_baseline_to_repository() -> dict[str, str]:
    ensure_output_directories()
    return compile_policy_bundle(
        schema_path=SCHEMA_PATH,
        intent_path=VALID_INTENT_PATH,
        topology_path=TOPOLOGY_PATH,
        output_directory=POLICIES_DIR,
    )


def verify_baseline_to_repository() -> dict[str, Any]:
    ensure_output_directories()
    return verify_from_paths(
        topology_path=TOPOLOGY_PATH,
        policies_directory=POLICIES_DIR,
        queries_path=QUERIES_PATH,
        output_directory=REPORTS_DIR,
    )


def generated_policy_filenames(directory: str | Path) -> list[str]:
    return sorted(
        path.name
        for path in Path(directory).iterdir()
        if path.is_file() and ".generated." in path.name
    )


def generated_policy_hashes(directory: str | Path) -> dict[str, str]:
    return {
        filename: sha256_file(Path(directory) / filename)
        for filename in generated_policy_filenames(directory)
    }


def collect_file_sizes(directory: str | Path) -> dict[str, int]:
    return {
        filename: (Path(directory) / filename).stat().st_size
        for filename in generated_policy_filenames(directory)
    }


def load_policy_documents(directory: str | Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    directory_path = Path(directory)
    return (
        load_json_file(directory_path / TRANSPORT_POLICY_FILENAME),
        load_yaml_file(directory_path / OCLOUD_POLICY_FILENAME),
        load_json_file(directory_path / ORAN_POLICY_FILENAME),
    )


def count_generated_rules(directory: str | Path) -> dict[str, int]:
    transport_policy, ocloud_policy, oran_policy = load_policy_documents(directory)
    transport_rule_count = len(transport_policy["allowed_directed_adjacencies"]) + len(
        transport_policy["forbidden_directed_adjacencies"]
    )
    ocloud_rule_count = len(ocloud_policy["allowed_flows"]) + len(
        ocloud_policy["forbidden_flows"]
    )
    oran_rule_count = len(oran_policy["slice_policies"])
    return {
        "transport_rule_count": transport_rule_count,
        "ocloud_rule_count": ocloud_rule_count,
        "oran_rule_count": oran_rule_count,
        "generated_rule_count": transport_rule_count + ocloud_rule_count + oran_rule_count,
    }


def measure_stage(
    name: str,
    func: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> tuple[Any, dict[str, Any]]:
    wall_start = time.perf_counter()
    cpu_start = time.process_time()
    result = func(*args, **kwargs)
    cpu_seconds = time.process_time() - cpu_start
    wall_seconds = time.perf_counter() - wall_start

    tracemalloc.start()
    func(*args, **kwargs)
    _, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    metrics = {
        "stage": name,
        "wall_clock_seconds": wall_seconds,
        "cpu_seconds": cpu_seconds,
        "peak_python_tracemalloc_bytes": peak_memory,
        "timing_basis": "one call measured without tracemalloc enabled",
        "memory_basis": "a separate repeated call measured with tracemalloc enabled",
    }
    return result, metrics


def write_json(path: str | Path, document: dict[str, Any]) -> None:
    dump_json_file(path, document)


def write_markdown(path: str | Path, text: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def print_json(document: dict[str, Any]) -> None:
    print(json.dumps(document, indent=2, sort_keys=False))


def load_invalid_intent(name: str) -> dict[str, Any]:
    return load_yaml_file(INVALID_INTENTS_DIR / name)


def load_negative_topology(name: str) -> dict[str, Any]:
    return load_yaml_file(NEGATIVE_TOPOLOGY_DIR / name)


def compile_to_temporary_directory() -> tuple[TemporaryDirectory[str], Path]:
    temporary_directory = TemporaryDirectory()
    output_directory = Path(temporary_directory.name)
    compile_policy_bundle(
        schema_path=SCHEMA_PATH,
        intent_path=VALID_INTENT_PATH,
        topology_path=TOPOLOGY_PATH,
        output_directory=output_directory,
    )
    return temporary_directory, output_directory


def validate_baseline_documents() -> None:
    schema, intent, topology = load_baseline_documents()
    validate_intent_document(intent, schema)
    validate_topology_document(topology)
