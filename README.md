# Transport-Aware Slice-Security Intent Compilation and Reachability Verification

This repository is the practical GitHub implementation for a bounded design-science proof of concept within the Master's minor thesis, *Transport-Aware Slice-Security Intent Compilation and Reachability Verification*.

The scope of this phase is intentionally narrow:

- Local Python implementation only.
- Exactly two slices: `slice_a` and `slice_b`.
- Exactly one shared service: `shared_auth_log`.
- Static validation and topology loading only.
- Static graph-based reachability verification is the target proof technique for later phases.

The following are deliberately out of scope in this repository phase:

- Kubernetes, Docker, ORANSlice, OAI, Open5GS, live RIC, xApps, rApps, or radio-stack integration.
- Runtime packet testing, runtime auditing, or live O-RAN control-plane enforcement.
- External network dependencies or remote services.
- Policy compilation or generated policy artefacts at this stage.

`shared_auth_log` is modeled as a terminal shared authentication-and-logging service and must always declare `transit_allowed: false`.

## Repository Structure

```text
.
├── README.md
├── pyproject.toml
├── Makefile
├── schemas/
│   └── slice_security_intent.schema.json
├── intents/
│   ├── two_slice_shared_auth_log.valid.yaml
│   └── invalid/
│       ├── third_slice.invalid.yaml
│       ├── missing_shared_service.invalid.yaml
│       ├── ambiguous_direction.invalid.yaml
│       ├── conflicting_allow_deny.invalid.yaml
│       ├── shared_service_transit.invalid.yaml
│       └── duplicate_endpoint.invalid.yaml
├── topology/
│   ├── base_topology.yaml
│   └── negative_controls/
│       ├── bad_direct_cross_slice.yaml
│       ├── bad_transport_cross_slice.yaml
│       ├── bad_shared_service_transit.yaml
│       └── bad_missing_default_deny.yaml
├── src/
│   └── oran_slice_security/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── validation.py
│       ├── models.py
│       └── io.py
├── tests/
│   ├── test_schema_validation.py
│   ├── test_semantic_validation.py
│   └── test_topology_load.py
└── docs/
    └── methodology_traceability.md
```

`policies/generated/` is reserved for later thesis phases and is intentionally empty in this validation-only baseline.

## Setup

Create the local virtual environment and install the package plus test dependencies:

```bash
make install
```

If you want to use the exact CLI form shown below, activate the environment first:

```bash
source .venv/bin/activate
```

## Validation Commands

Validate the bounded slice-security intent:

```bash
python -m oran_slice_security validate-intent --schema schemas/slice_security_intent.schema.json --intent intents/two_slice_shared_auth_log.valid.yaml
```

Validate the static base topology:

```bash
python -m oran_slice_security validate-topology --topology topology/base_topology.yaml
```

Or run the repository helpers:

```bash
make test
make validate
```

## Thesis Mapping to RQ1

This phase maps to **RQ1** by formalizing the bounded two-slice intent model, validating its schema, enforcing thesis-specific semantic rules, and loading the static topology used by later graph-based verification.

What RQ1 covers here:

- Schema-based validation for the intent document.
- Semantic rejection of invalid slice-security cases.
- Static topology loading for the proof-of-concept network graph.

What is not implemented yet:

- RQ2 policy compilation into generated artefacts.
- RQ3 reachability verification over compiled policy and topology graphs.

No generated policy artefacts are created in this phase.
