from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


def load_yaml_file(path: str | Path) -> dict[str, Any]:
    """Load a YAML document from disk."""
    with Path(path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    if not isinstance(data, dict):
        raise ValueError(f"Expected a YAML mapping in {path}")

    return data


def load_json_file(path: str | Path) -> dict[str, Any]:
    """Load a JSON document from disk."""
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object in {path}")

    return data


def dump_json_file(path: str | Path, document: dict[str, Any]) -> None:
    """Write a JSON document with deterministic formatting."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(document, indent=2, sort_keys=False) + "\n"
    target.write_text(text, encoding="utf-8")


def dump_yaml_file(path: str | Path, document: dict[str, Any]) -> None:
    """Write a YAML document with deterministic formatting."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.safe_dump(
        document,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=False,
    )
    target.write_text(text, encoding="utf-8")


def sha256_bytes(payload: bytes) -> str:
    """Compute the SHA256 hash for an in-memory payload."""
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: str | Path) -> str:
    """Compute the SHA256 hash for a file on disk."""
    return sha256_bytes(Path(path).read_bytes())
