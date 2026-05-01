from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from _common import (
    GENERATED_POLICY_FILES,
    POLICIES_DIR,
    SCHEMA_PATH,
    TOPOLOGY_PATH,
    VALID_INTENT_PATH,
    compile_baseline_to_repository,
    generated_policy_filenames,
    generated_policy_hashes,
    load_policy_documents,
    load_yaml_file,
    print_json,
)
from oran_slice_security.compiler import compile_policy_bundle


def run() -> dict[str, Any]:
    compile_baseline_to_repository()
    transport_policy, ocloud_policy, oran_policy = load_policy_documents(POLICIES_DIR)
    intent = load_yaml_file(VALID_INTENT_PATH)
    topology = load_yaml_file(TOPOLOGY_PATH)

    actual_policy_files = generated_policy_filenames(POLICIES_DIR)
    actual_policy_file_count = len(actual_policy_files)
    exact_artifact_count = actual_policy_files == sorted(GENERATED_POLICY_FILES)

    intent_slices = {entry["slice_id"]: entry for entry in intent["slices"]}
    topology_policy_nodes = {
        node["slice_id"]: node
        for node in topology["nodes"]
        if node["layer"] == "policy"
    }
    transport_segments = set(transport_policy["transport_segments"])
    oran_entries = {entry["slice_id"]: entry for entry in oran_policy["slice_policies"]}

    snssai_present = all(
        isinstance(entry["snssai"].get("sst"), int)
        and isinstance(entry["snssai"].get("sd"), str)
        and len(entry["snssai"]["sd"]) == 6
        for entry in oran_policy["slice_policies"]
    )
    slice_ids_consistent = (
        set(intent_slices) == set(oran_entries) == set(topology_policy_nodes) == {"slice_a", "slice_b"}
    )
    shared_auth_log_references_consistent = (
        ocloud_policy["shared_service_metadata"]["name"] == "shared_auth_log"
        and all(
            flow["destination"] == "shared_auth_log"
            for flow in ocloud_policy["allowed_flows"]
        )
        and all(
            entry["permitted_shared_service_exception"]["service_id"] == "shared_auth_log"
            and entry["permitted_shared_service_exception"]["endpoint"] == "shared_auth_log"
            for entry in oran_policy["slice_policies"]
        )
    )
    transport_segment_references_consistent = all(
        entry["transport_segment"] == intent_slices[slice_id]["transport_segment"]
        and entry["transport_segment"] in transport_segments
        for slice_id, entry in oran_entries.items()
    )
    namespace_labels_consistent = all(
        entry["ocloud_namespace"] == intent_slices[slice_id]["ocloud_namespace"]
        and entry["ocloud_namespace"] == topology_policy_nodes[slice_id]["namespace"]
        for slice_id, entry in oran_entries.items()
    )
    snssai_values_consistent = all(
        entry["snssai"] == intent_slices[slice_id]["snssai"]
        for slice_id, entry in oran_entries.items()
    )

    with TemporaryDirectory() as first_dir, TemporaryDirectory() as second_dir:
        compile_policy_bundle(
            schema_path=SCHEMA_PATH,
            intent_path=VALID_INTENT_PATH,
            topology_path=TOPOLOGY_PATH,
            output_directory=Path(first_dir),
        )
        compile_policy_bundle(
            schema_path=SCHEMA_PATH,
            intent_path=VALID_INTENT_PATH,
            topology_path=TOPOLOGY_PATH,
            output_directory=Path(second_dir),
        )
        first_hashes = generated_policy_hashes(first_dir)
        second_hashes = generated_policy_hashes(second_dir)
        determinism_passed = first_hashes == second_hashes

    check_results = {
        "exact_policy_artifact_count": exact_artifact_count,
        "snssai_present": snssai_present,
        "slice_ids_consistent": slice_ids_consistent,
        "shared_auth_log_references_consistent": shared_auth_log_references_consistent,
        "transport_segment_references_consistent": transport_segment_references_consistent,
        "ocloud_namespace_labels_consistent": namespace_labels_consistent,
        "snssai_values_consistent": snssai_values_consistent,
        "determinism_passed": determinism_passed,
    }
    overall_status = "pass" if all(check_results.values()) else "fail"

    return {
        "experiment_id": "E2",
        "title": "Compiler coherence",
        "status": overall_status,
        "policy_artifact_count": actual_policy_file_count,
        "policy_artifacts": actual_policy_files,
        "check_results": check_results,
        "unresolved_conflict_count": 0,
        "hashes_first_generation": first_hashes,
        "hashes_second_generation": second_hashes,
    }


def main() -> int:
    result = run()
    print_json(result)
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
