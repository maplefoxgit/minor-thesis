from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from _common import (
    ARTIFACT_INTEGRITY_JSON,
    ARTIFACT_INTEGRITY_MD,
    QUERIES_PATH,
    SCHEMA_PATH,
    TOPOLOGY_PATH,
    VALID_INTENT_PATH,
    print_json,
    write_json,
    write_markdown,
)
from oran_slice_security.compiler import (
    MANIFEST_FILENAME,
    TRANSPORT_POLICY_FILENAME,
    compile_policy_bundle,
)
from oran_slice_security.integrity import (
    ArtifactIntegrityError,
    verify_compiled_policy_manifest,
)
from oran_slice_security.io import load_json_file, sha256_file
from oran_slice_security.verifier import verify_from_paths


def _manifest_hashes(manifest: dict[str, Any]) -> dict[str, str]:
    return {
        entry["artifact"]: entry["sha256"]
        for entry in manifest["generated_policy_artifacts"]
    }


def _render_markdown(result: dict[str, Any]) -> str:
    mutation = result["mutation"]
    rejection = result["mutated_bundle"]
    recovery = result["clean_regeneration"]
    lines = [
        "# Post-Compilation Policy Integrity Experiment",
        "",
        "## Question",
        "",
        result["question"],
        "",
        "## Controlled conditions",
        "",
        "| Condition | Parsed policy meaning | SHA-256 state | Verification result |",
        "| --- | --- | --- | --- |",
        (
            "| Unchanged compiler output | unchanged | 3/3 manifest hashes match | "
            f"{result['baseline']['verification_status']} |"
        ),
        (
            "| Byte-only mutation to transport_policy.generated.json | "
            f"{'unchanged' if mutation['semantic_document_unchanged'] else 'changed'} | "
            "target hash differs from manifest | "
            f"{rejection['result']} before graph construction |"
        ),
        (
            "| Clean regeneration | unchanged | original manifest restored | "
            f"{recovery['verification_status']} |"
        ),
        "",
        "## Mutation evidence",
        "",
        f"- Artifact: {mutation['artifact']}",
        f"- Mutation: {mutation['description']}",
        f"- Manifest SHA-256: {mutation['manifest_sha256']}",
        f"- Mutated SHA-256: {mutation['mutated_sha256']}",
        f"- Parsed document unchanged: {mutation['semantic_document_unchanged']}",
        "",
        "## Rejection evidence",
        "",
        f"- Result: {rejection['result']}",
        f"- Stage: {rejection['rejection_stage']}",
        f"- Pass report created after mutation: {rejection['pass_report_created']}",
        f"- Reason: {rejection['reason']}",
        "",
        "## Interpretation boundary",
        "",
        result["interpretation_boundary"],
        "",
    ]
    return "\n".join(lines)


def run() -> dict[str, Any]:
    with TemporaryDirectory() as working_directory:
        root = Path(working_directory)
        policies_directory = root / "generated"
        baseline_reports = root / "baseline_reports"
        mutated_reports = root / "mutated_reports"
        recovered_reports = root / "recovered_reports"

        compile_policy_bundle(
            schema_path=SCHEMA_PATH,
            intent_path=VALID_INTENT_PATH,
            topology_path=TOPOLOGY_PATH,
            output_directory=policies_directory,
        )

        original_manifest = load_json_file(policies_directory / MANIFEST_FILENAME)
        original_hashes = _manifest_hashes(original_manifest)
        target_path = policies_directory / TRANSPORT_POLICY_FILENAME
        original_document = load_json_file(target_path)

        baseline_integrity = verify_compiled_policy_manifest(policies_directory)
        baseline_verification = verify_from_paths(
            topology_path=TOPOLOGY_PATH,
            policies_directory=policies_directory,
            queries_path=QUERIES_PATH,
            output_directory=baseline_reports,
        )

        target_path.write_bytes(target_path.read_bytes() + b" \n")
        mutated_document = load_json_file(target_path)
        mutated_hash = sha256_file(target_path)
        semantic_document_unchanged = mutated_document == original_document

        rejection_result = "accepted"
        rejection_stage = "none"
        rejection_reason = "mutated policy bundle unexpectedly verified"
        try:
            verify_from_paths(
                topology_path=TOPOLOGY_PATH,
                policies_directory=policies_directory,
                queries_path=QUERIES_PATH,
                output_directory=mutated_reports,
            )
        except ArtifactIntegrityError as exc:
            rejection_result = "rejected"
            rejection_stage = "pre-graph integrity gate"
            rejection_reason = str(exc)

        pass_report_created = (mutated_reports / "verification_report.json").exists()

        compile_policy_bundle(
            schema_path=SCHEMA_PATH,
            intent_path=VALID_INTENT_PATH,
            topology_path=TOPOLOGY_PATH,
            output_directory=policies_directory,
        )
        regenerated_manifest = load_json_file(policies_directory / MANIFEST_FILENAME)
        regenerated_hashes = _manifest_hashes(regenerated_manifest)
        recovered_integrity = verify_compiled_policy_manifest(policies_directory)
        recovered_verification = verify_from_paths(
            topology_path=TOPOLOGY_PATH,
            policies_directory=policies_directory,
            queries_path=QUERIES_PATH,
            output_directory=recovered_reports,
        )

    status = (
        "pass"
        if baseline_integrity["status"] == "pass"
        and baseline_verification["overall_status"] == "pass"
        and semantic_document_unchanged
        and mutated_hash != original_hashes[TRANSPORT_POLICY_FILENAME]
        and rejection_result == "rejected"
        and rejection_stage == "pre-graph integrity gate"
        and TRANSPORT_POLICY_FILENAME in rejection_reason
        and "expected sha256=" in rejection_reason
        and "actual sha256=" in rejection_reason
        and not pass_report_created
        and regenerated_hashes == original_hashes
        and recovered_integrity["status"] == "pass"
        and recovered_verification["overall_status"] == "pass"
        else "fail"
    )

    result = {
        "experiment_id": "E7",
        "title": "Post-compilation policy integrity",
        "status": status,
        "question": (
            "Can a manifest-listed generated policy be changed after compilation "
            "without invalidating the verification evidence?"
        ),
        "controlled_variables": {
            "intent": "intents/two_slice_shared_auth_log.valid.yaml",
            "topology": "topology/base_topology.yaml",
            "queries": "verifier/queries/baseline_queries.yaml",
            "compiler": "unchanged",
            "verifier": "unchanged except for the manifest integrity gate",
            "changed_factor": "bytes of one generated policy artefact",
        },
        "baseline": {
            "integrity_status": baseline_integrity["status"],
            "verified_artifact_count": baseline_integrity["artifact_count"],
            "verification_status": baseline_verification["overall_status"],
        },
        "mutation": {
            "artifact": TRANSPORT_POLICY_FILENAME,
            "description": (
                "One trailing whitespace sequence was appended. The JSON remained valid "
                "and parsed to the same policy document."
            ),
            "manifest_sha256": original_hashes[TRANSPORT_POLICY_FILENAME],
            "mutated_sha256": mutated_hash,
            "semantic_document_unchanged": semantic_document_unchanged,
        },
        "mutated_bundle": {
            "result": rejection_result,
            "rejection_stage": rejection_stage,
            "reason": rejection_reason,
            "pass_report_created": pass_report_created,
        },
        "clean_regeneration": {
            "manifest_hashes_match_original": regenerated_hashes == original_hashes,
            "integrity_status": recovered_integrity["status"],
            "verification_status": recovered_verification["overall_status"],
        },
        "interpretation_boundary": (
            "E7 detects post-compilation byte changes to the three generated policy files "
            "listed in the retained manifest when the integrity gate executes. It does not "
            "authenticate the manifest, eliminate a concurrent check-to-use race, detect "
            "coordinated modification of both a policy and its manifest, bind topology, query, "
            "or report files to the same run, detect a compromised compiler or verifier, or "
            "observe runtime network drift."
        ),
    }
    write_json(ARTIFACT_INTEGRITY_JSON, result)
    write_markdown(ARTIFACT_INTEGRITY_MD, _render_markdown(result))
    return result


def main() -> int:
    result = run()
    print_json(result)
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
