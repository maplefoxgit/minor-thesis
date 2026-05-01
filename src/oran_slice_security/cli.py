from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .compiler import compile_policy_bundle
from .io import load_json_file, load_yaml_file
from .verifier import verify_from_paths
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

    verify_parser = subparsers.add_parser(
        "verify",
        help="Verify static reachability over the compiled policy-and-topology model.",
    )
    verify_parser.add_argument(
        "--topology", required=True, help="Path to the YAML topology."
    )
    verify_parser.add_argument(
        "--policies", required=True, help="Directory containing compiled policy artefacts."
    )
    verify_parser.add_argument(
        "--queries", required=True, help="Path to the YAML verification queries."
    )
    verify_parser.add_argument(
        "--out", required=True, help="Output directory for verification reports."
    )
    verify_parser.set_defaults(func=_run_verify)

    run_all_parser = subparsers.add_parser(
        "run-all",
        help="Run validate, compile, and verify with the repository's bounded baseline inputs.",
    )
    run_all_parser.set_defaults(func=_run_run_all)

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


def _run_verify(args: argparse.Namespace) -> int:
    report_document = verify_from_paths(
        topology_path=Path(args.topology),
        policies_directory=Path(args.policies),
        queries_path=Path(args.queries),
        output_directory=Path(args.out),
    )
    print(
        "Verification completed: "
        f"{args.out} (overall_status={report_document['overall_status']})"
    )
    return 0


def _run_run_all(args: argparse.Namespace) -> int:
    schema_path = Path("schemas/slice_security_intent.schema.json")
    intent_path = Path("intents/two_slice_shared_auth_log.valid.yaml")
    topology_path = Path("topology/base_topology.yaml")
    policies_directory = Path("policies/generated")
    queries_path = Path("verifier/queries/baseline_queries.yaml")
    reports_directory = Path("results/reports")

    schema = load_json_file(schema_path)
    intent = load_yaml_file(intent_path)
    topology = load_yaml_file(topology_path)

    validate_intent_document(intent, schema)
    validate_topology_document(topology)
    compile_policy_bundle(schema_path, intent_path, topology_path, policies_directory)
    report_document = verify_from_paths(
        topology_path=topology_path,
        policies_directory=policies_directory,
        queries_path=queries_path,
        output_directory=reports_directory,
    )

    print(
        "Run-all completed: "
        f"policies={policies_directory}, reports={reports_directory}, "
        f"overall_status={report_document['overall_status']}"
    )
    return 0
