from __future__ import annotations

from pathlib import Path
from typing import Any

from .compiler import GENERATED_POLICY_FILENAMES, MANIFEST_FILENAME
from .io import load_json_file, sha256_file
from .validation import DocumentValidationError


class ArtifactIntegrityError(DocumentValidationError):
    """Raised when a compiled policy bundle no longer matches its manifest."""


def verify_compiled_policy_manifest(
    policies_directory: str | Path,
) -> dict[str, Any]:
    """Verify the exact generated-policy set and SHA-256 values before use.

    The compiler already writes manifest.json. This gate makes the verifier
    consume that manifest instead of treating it as documentation only. The
    check covers the three generated policy artefacts. It does not claim
    authenticity, signature validation, or runtime drift detection.
    """

    directory = Path(policies_directory)
    manifest_path = directory / MANIFEST_FILENAME

    if not directory.is_dir():
        raise ArtifactIntegrityError(
            f"compiled policy directory does not exist: {directory}"
        )
    if not manifest_path.is_file():
        raise ArtifactIntegrityError(
            f"compiled policy manifest is missing: {MANIFEST_FILENAME}"
        )

    try:
        manifest = load_json_file(manifest_path)
    except (OSError, ValueError) as exc:
        raise ArtifactIntegrityError(
            f"compiled policy manifest could not be read: {MANIFEST_FILENAME}: {exc}"
        ) from exc

    entries = manifest.get("generated_policy_artifacts")
    artifact_count = manifest.get("artifact_count")
    expected_names = set(GENERATED_POLICY_FILENAMES)

    if type(artifact_count) is not int or artifact_count != len(expected_names):
        raise ArtifactIntegrityError(
            "compiled policy manifest has the wrong artifact_count: "
            f"expected {len(expected_names)}, found {artifact_count!r}"
        )
    if not isinstance(entries, list):
        raise ArtifactIntegrityError(
            "compiled policy manifest must define generated_policy_artifacts as a list"
        )
    if len(entries) != artifact_count:
        raise ArtifactIntegrityError(
            "compiled policy manifest entry count does not match artifact_count"
        )

    expected_hashes: dict[str, str] = {}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ArtifactIntegrityError(
                f"compiled policy manifest entry {index} must be an object"
            )
        if set(entry) != {"artifact", "sha256"}:
            raise ArtifactIntegrityError(
                f"compiled policy manifest entry {index} must contain only artifact and sha256"
            )

        artifact = entry.get("artifact")
        expected_hash = entry.get("sha256")
        if not isinstance(artifact, str) or not artifact:
            raise ArtifactIntegrityError(
                f"compiled policy manifest entry {index} has an invalid artifact name"
            )
        if Path(artifact).name != artifact or artifact in {".", ".."}:
            raise ArtifactIntegrityError(
                f"compiled policy manifest entry {index} has an unsafe artifact name"
            )
        if artifact in expected_hashes:
            raise ArtifactIntegrityError(
                f"compiled policy manifest contains duplicate artifact: {artifact}"
            )
        if not _is_sha256_hex(expected_hash):
            raise ArtifactIntegrityError(
                f"compiled policy manifest contains an invalid SHA-256 value for {artifact}"
            )
        expected_hashes[artifact] = expected_hash

    manifest_names = set(expected_hashes)
    if manifest_names != expected_names:
        missing = sorted(expected_names - manifest_names)
        unexpected = sorted(manifest_names - expected_names)
        details: list[str] = []
        if missing:
            details.append("missing=" + ", ".join(missing))
        if unexpected:
            details.append("unexpected=" + ", ".join(unexpected))
        raise ArtifactIntegrityError(
            "compiled policy manifest does not describe the exact policy set: "
            + "; ".join(details)
        )

    actual_generated_names = {
        path.name
        for path in directory.iterdir()
        if path.is_file() and ".generated." in path.name
    }
    if actual_generated_names != expected_names:
        missing = sorted(expected_names - actual_generated_names)
        unexpected = sorted(actual_generated_names - expected_names)
        details = []
        if missing:
            details.append("missing=" + ", ".join(missing))
        if unexpected:
            details.append("unexpected=" + ", ".join(unexpected))
        raise ArtifactIntegrityError(
            "compiled policy directory does not contain the exact policy set: "
            + "; ".join(details)
        )

    verified_artifacts: list[dict[str, str]] = []
    mismatches: list[str] = []
    for artifact in sorted(expected_names):
        artifact_path = directory / artifact
        if not artifact_path.is_file():
            mismatches.append(f"{artifact}: file is missing")
            continue

        actual_hash = sha256_file(artifact_path)
        expected_hash = expected_hashes[artifact]
        if actual_hash != expected_hash:
            mismatches.append(
                f"{artifact}: expected sha256={expected_hash}, actual sha256={actual_hash}"
            )
            continue

        verified_artifacts.append(
            {
                "artifact": artifact,
                "sha256": actual_hash,
            }
        )

    if mismatches:
        raise ArtifactIntegrityError(
            "compiled policy integrity check failed: " + "; ".join(mismatches)
        )

    return {
        "status": "pass",
        "manifest": MANIFEST_FILENAME,
        "artifact_count": len(verified_artifacts),
        "verified_artifacts": verified_artifacts,
        "boundary": (
            "The check binds verification to the three manifest-listed generated policy "
            "files as they exist when the gate runs. It does not authenticate the manifest, "
            "eliminate a concurrent check-to-use race, cover topology or query files, or "
            "detect runtime drift."
        ),
    }


def _is_sha256_hex(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True
