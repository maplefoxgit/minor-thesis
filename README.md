# Transport-Aware Slice-Security Intent Compilation and Reachability Verification

This repository is the practical GitHub implementation for a bounded design-science proof of concept within the Master's minor thesis, *Transport-Aware Slice-Security Intent Compilation and Reachability Verification*.

The scope of this phase is intentionally narrow:

- Local Python implementation only.
- Exactly two slices: `slice_a` and `slice_b`.
- Exactly one shared service: `shared_auth_log`.
- Deterministic compilation of exactly three representational policy artefacts.
- Static graph-based reachability verification is the target proof technique for later phases.

The following are deliberately out of scope in this repository phase:

- Kubernetes, Docker, ORANSlice, OAI, Open5GS, live RIC, xApps, rApps, or radio-stack integration.
- Runtime packet testing, runtime auditing, or live O-RAN control-plane enforcement.
- External network dependencies or remote services.
- Any claim of a production O-RAN control path.

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
│       ├── compiler.py
│       ├── policy_models.py
│       ├── validation.py
│       ├── models.py
│       └── io.py
├── tests/
│   ├── test_schema_validation.py
│   ├── test_semantic_validation.py
│   ├── test_topology_load.py
│   ├── test_compiler_outputs.py
│   ├── test_compiler_determinism.py
│   └── test_compiler_conflicts.py
└── docs/
    └── methodology_traceability.md
```

The compiler writes exactly these files to `policies/generated/`:

- `transport_policy.generated.json`
- `ocloud_microsegmentation.generated.yaml`
- `oran_slice_policy.generated.json`
- `manifest.json`

No fourth policy artefact is produced. The manifest is allowed because it is not itself a policy artefact.

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

## Compilation

Compile the validated intent and topology into the deterministic RQ2 outputs:

```bash
python -m oran_slice_security compile --schema schemas/slice_security_intent.schema.json --intent intents/two_slice_shared_auth_log.valid.yaml --topology topology/base_topology.yaml --out policies/generated
```

Or use the repository helpers:

```bash
make compile
make clean-generated
```

The compiler always validates structure, semantics, and topology before writing outputs.

## Why These Artefacts Are Representational

The generated artefacts are intentionally representational and graph-consumable rather than executable production policies. They encode bounded transport segmentation, O-Cloud micro-segmentation, and slice-scoped O-RAN metadata in a deterministic form that later RQ3 graph analysis can consume.

What they are for:

- Static graph construction.
- Reachability and isolation reasoning in the bounded proof of concept.
- Traceable, deterministic inputs for later verification logic.

What they do not claim:

- No live RIC, xApp, or rApp control path.
- No production O-RAN enforcement.
- No runtime auditing or packet-level behavior.

## Thesis Mapping

### RQ1

RQ1 is covered by formalizing the bounded two-slice intent model, validating its schema, enforcing thesis-specific semantic rules, and loading the static topology used by later graph-based verification.

What RQ1 covers here:

- Schema-based validation for the intent document.
- Semantic rejection of invalid slice-security cases.
- Static topology loading for the proof-of-concept network graph.

### RQ2

RQ2 is covered by the deterministic compiler in `src/oran_slice_security/compiler.py`, which emits exactly three generated policy artefacts plus a hash manifest.

### RQ3

RQ3 is still planned as static graph-based reachability verification over the compiled policy and topology representations.
