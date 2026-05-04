# Transport-Aware Slice-Security Intent Compilation and Reachability Verification

## Project Purpose

This repository is the practical GitHub implementation for a bounded design-science proof of concept within the Master's minor thesis, *Transport-Aware Slice-Security Intent Compilation and Reachability Verification*.

It implements a fixed local pipeline that:

1. validates a bounded two-slice slice-security intent,
2. deterministically compiles exactly three representational policy artefacts,
3. verifies static reachability and non-reachability over the compiled local model,
4. runs the E1-E5 evaluation automation and writes thesis evidence under `results/`.

## Thesis Claim

The thesis claim supported by this repository is intentionally narrow:

- exactly two slices: `slice_a` and `slice_b`,
- exactly one shared service: `shared_auth_log`,
- deterministic representational policy compilation,
- deterministic static graph-based reachability verification,
- negative-control rejection for bounded misconfiguration cases,
- modest local overhead reporting.

This proves only model-based static non-reachability in the local policy-and-topology model.

## Out Of Scope

The repository does **not** claim:

- production O-RAN deployment,
- live RIC, xApp, or rApp control,
- Kubernetes, Docker, ORANSlice, OAI, Open5GS, or radio-stack integration,
- runtime drift detection,
- runtime packet auditing or delivery assurance,
- cryptographic enforcement,
- complete O-RAN security assurance.

`shared_auth_log` is modeled as a terminal shared authentication-and-logging service and must always declare `transit_allowed: false`.

## Quickstart

Create the virtual environment and install dependencies:

```bash
make install
source .venv/bin/activate
```

Run the bounded workflow in the required order:

```bash
make validate
make compile
make verify
make test
```

Run the full evidence automation:

```bash
make run-all
python experiments/run_all_experiments.py
```

## Examples / Beginner-Friendly Guides

If you want an easier on-ramp before diving into the thesis-oriented details, start here:

- [`docs/examples_index.md`](docs/examples_index.md)
- [`examples/universal-template/README.md`](examples/universal-template/README.md)
- [`examples/hospital-example/README.md`](examples/hospital-example/README.md)

These guides are additive teaching layers. They do not replace the current bounded thesis framing, and they do not widen the repository's claim.

## Where To Start If You Are New

- Read [`examples/hospital-example/README.md`](examples/hospital-example/README.md) for the friendliest ELI5-style walkthrough.
- Read [`examples/universal-template/README.md`](examples/universal-template/README.md) for the domain-neutral reusable pattern.
- Come back to this main README when you want the exact commands, artefacts, and thesis boundaries.


## Methodology and RQ Mapping

For a supervisor-facing explanation of how the repository maps to the thesis research questions, methodology pipeline, generated artefacts, related-work patterns, and bounded evidence claim, see [`docs/rq_to_repo_mapping.md`](docs/rq_to_repo_mapping.md).

## Repository Structure

```text
.
├── README.md
├── pyproject.toml
├── Makefile
├── schemas/
├── intents/
├── examples/
├── topology/
├── policies/generated/
├── verifier/queries/
├── experiments/
├── results/
│   ├── reports/
│   └── metrics/
├── src/oran_slice_security/
├── tests/
├── docs/
└── .github/workflows/
```

Important implementation areas:

- `src/oran_slice_security/validation.py`: RQ1 validation rules.
- `src/oran_slice_security/compiler.py`: RQ2 deterministic compiler.
- `src/oran_slice_security/graph_builder.py`: compiled policy-and-topology graph construction.
- `src/oran_slice_security/verifier.py`: RQ3 deterministic breadth-first search verification.
- `experiments/`: E1-E5 automation.
- `results/`: generated thesis evidence.

## Commands

Validate intent and topology:

```bash
python -m oran_slice_security validate-intent --schema schemas/slice_security_intent.schema.json --intent intents/two_slice_shared_auth_log.valid.yaml
python -m oran_slice_security validate-topology --topology topology/base_topology.yaml
make validate
```

Compile the three required policy artefacts:

```bash
python -m oran_slice_security compile --schema schemas/slice_security_intent.schema.json --intent intents/two_slice_shared_auth_log.valid.yaml --topology topology/base_topology.yaml --out policies/generated
make compile
```

Verify static reachability:

```bash
python -m oran_slice_security verify --topology topology/base_topology.yaml --policies policies/generated --queries verifier/queries/baseline_queries.yaml --out results/reports
make verify
```

Run all bounded repository steps:

```bash
python -m oran_slice_security run-all
make run-all
```

Run the evaluation automation:

```bash
python experiments/run_e1_schema_expressiveness.py
python experiments/run_e2_compiler_coherence.py
python experiments/run_e3_reachability_verification.py
python experiments/run_e4_negative_controls.py
python experiments/run_e5_overhead.py
python experiments/run_all_experiments.py
```

## Expected Outputs

The compiler must create exactly three policy artefacts and one allowed manifest:

- `policies/generated/transport_policy.generated.json`
- `policies/generated/ocloud_microsegmentation.generated.yaml`
- `policies/generated/oran_slice_policy.generated.json`
- `policies/generated/manifest.json`

No fourth policy artefact is allowed.

The verifier writes:

- `results/reports/verification_report.json`
- `results/reports/verification_report.md`

The experiment automation writes:

- `results/reports/experiment_summary.json`
- `results/reports/experiment_summary.md`
- `results/metrics/overhead_metrics.json`

## Why The Policy Artefacts Are Representational

The generated policy artefacts are representational and graph-consumable rather than executable production policies. They exist to encode bounded transport segmentation, O-Cloud micro-segmentation, and minimal slice-scoped O-RAN metadata for later static analysis.

They do **not** claim:

- a production O-RAN control path,
- live RIC or xApp or rApp enforcement,
- runtime enforcement or packet-level behavior.

## Experiment Descriptions

- `E1 Schema expressiveness`: confirms the accepted bounded intent remains unambiguous and the bounded invalid intents fail for the expected reasons, including explicit rejection of an ambiguous invalid case.
- `E2 Compiler coherence`: confirms exactly three policy artefacts, identifier consistency, and deterministic regeneration.
- `E3 Reachability verification`: confirms both permitted paths to `shared_auth_log` survive while forbidden cross-slice paths do not.
- `E4 Negative-control misconfiguration`: confirms each negative-control topology is rejected with a useful reason, including an over-restrictive case that breaks required reachability to `shared_auth_log`.
- `E5 Practical overhead`: reports local timing, CPU, Python `tracemalloc` peak allocation, file size, rule count, and graph-size evidence without making a production scalability claim.

## How To Reproduce Reports

From a clean checkout:

```bash
make install
source .venv/bin/activate
make run-all
python experiments/run_all_experiments.py
```

Then inspect:

- `results/reports/verification_report.json`
- `results/reports/verification_report.md`
- `results/reports/experiment_summary.json`
- `results/reports/experiment_summary.md`
- `results/metrics/overhead_metrics.json`

## How To Interpret Pass And Fail

- `pass` means the bounded local model behaved exactly as the fixed methodology requires.
- `fail` means the repository detected a structural, semantic, compilation, reachability, or negative-control violation relative to the fixed bounded design.
- A passing verification report means only the modeled graph satisfied the required reachability and non-reachability properties.
- A passing experiment summary means E1-E5 all completed successfully within the bounded local proof of concept.

## Bounded Limitations

This repository proves only model-based static non-reachability in the local policy-and-topology model. It does not establish runtime enforcement, runtime drift resistance, packet delivery guarantees, cryptographic protection, live O-RAN behavior, or complete end-to-end O-RAN security.

