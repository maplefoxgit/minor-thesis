from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .compiler import compile_policy_bundle
from .io import load_json_file, load_yaml_file
from .validation import (
    DocumentValidationError,
    validate_intent_document,
    validate_topology_document,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="oran_slice_security",
        description="Validation utilities for the bounded thesis proof of concept.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_intent = subparsers.add_parser(
        "validate-intent",
        help="Validate the bounded slice-security intent document.",
    )
    validate_intent.add_argument("--schema", required=True, help="Path to the JSON Schema.")
    validate_intent.add_argument("--intent", required=True, help="Path to the YAML intent.")
    validate_intent.set_defaults(func=_run_validate_intent)

    validate_topology = subparsers.add_parser(
        "validate-topology",
        help="Validate the bounded static topology document.",
    )
    validate_topology.add_argument(
        "--topology", required=True, help="Path to the YAML topology."
    )
    validate_topology.set_defaults(func=_run_validate_topology)

    compile_parser = subparsers.add_parser(
        "compile",
        help="Compile deterministic representational policy artefacts.",
    )
    compile_parser.add_argument("--schema", required=True, help="Path to the JSON Schema.")
    compile_parser.add_argument("--intent", required=True, help="Path to the YAML intent.")
    compile_parser.add_argument(
        "--topology", required=True, help="Path to the YAML topology."
    )
    compile_parser.add_argument(
        "--out", required=True, help="Output directory for generated artefacts."
    )
    compile_parser.set_defaults(func=_run_compile)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return args.func(args)
    except DocumentValidationError as exc:
        parser.exit(status=1, message=f"Validation failed: {exc}\n")


def _run_validate_intent(args: argparse.Namespace) -> int:
    schema = load_json_file(Path(args.schema))
    intent = load_yaml_file(Path(args.intent))
    validate_intent_document(intent, schema)
    print(f"Intent validation passed: {args.intent}")
    return 0


def _run_validate_topology(args: argparse.Namespace) -> int:
    topology = load_yaml_file(Path(args.topology))
    validate_topology_document(topology)
    print(f"Topology validation passed: {args.topology}")
    return 0


def _run_compile(args: argparse.Namespace) -> int:
    compile_policy_bundle(
        schema_path=Path(args.schema),
        intent_path=Path(args.intent),
        topology_path=Path(args.topology),
        output_directory=Path(args.out),
    )
    print(f"Compilation passed: {args.out}")
    return 0
