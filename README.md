# Transport-Aware Slice-Security Intent Compilation and Reachability Verification

## Project Purpose

This repository is the practical GitHub implementation for a bounded design-science proof of concept within the Master's minor thesis, *Transport-Aware Slice-Security Intent Compilation and Reachability Verification*.

It implements a fixed local pipeline that:

1. validates a bounded two-slice slice-security intent,
2. deterministically compiles exactly three representational policy artefacts,
3. verifies static reachability and non-reachability over the compiled local model,
4. runs the E1-E7 evaluation automation and writes thesis evidence under `results/`.

## Thesis Claim

The functional and security evidence supported by this repository is intentionally narrow:

- exactly two slices: `slice_a` and `slice_b`,
- exactly one shared service: `shared_auth_log`,
- deterministic representational policy compilation,
- deterministic static graph-based reachability verification,
- negative-control rejection for bounded misconfiguration cases,
- a controlled comparison against permissive topology-only and deny-all baselines,
- a pre-verification SHA-256 integrity gate for the three manifest-listed generated policies.

Performance and scale are characterised separately through:

- local E5 overhead reporting with a retained 5-warm-up, 30-run distribution,
- E6-P repeated pure-verification timing for the three E6 graph conditions,
- a verifier-only scale study using generated graphs representing 2, 3, 4, and 10 slices.

This proves only model-based static non-reachability in the local policy-and-topology model.

## Out Of Scope

The repository does **not** claim:

- production O-RAN deployment,
- live RIC, xApp, or rApp control,
- Kubernetes, Docker, ORANSlice, OAI, Open5GS, or radio-stack integration,
- runtime drift detection,
- runtime packet auditing or delivery assurance,
- authenticated cryptographic enforcement,
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

Run validation, compilation, verification, automated tests, and the E1 to E7 experiment pack:

```bash
make run-all
```

Run only the E1 to E7 experiment pack:

```bash
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
- `experiments/`: E1-E7 automation, repeated E5 and E6-P timing, and the S1 verifier-only scale study.
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

Run the core validation, compilation, and verification pipeline without tests or experiments:

```bash
python -m oran_slice_security run-all
```

Run the core pipeline, automated tests, and E1 to E7 experiments:

```bash
make run-all
```

Run the evaluation automation:

```bash
python experiments/run_e1_schema_expressiveness.py
python experiments/run_e2_compiler_coherence.py
python experiments/run_e3_reachability_verification.py
python experiments/run_e4_negative_controls.py
python experiments/run_e5_overhead.py
python experiments/run_e6_controlled_baselines.py
python experiments/run_e7_artifact_integrity.py
python experiments/run_all_experiments.py

# Final 5-warm-up, 30-trial E5 distribution
python experiments/run_e5_repeated.py --warmups 5 --trials 30

# E6-P repeated pure-verification cost for the three E6 conditions
python experiments/run_e6_repeated_performance.py --warmups 5 --trials 30 --iterations 500

# Bounded verifier-only scale study for 2, 3, 4, and 10 slices
python experiments/run_s1_multislice_verifier_scaling.py --slices 2 3 4 10 --warmups 5 --trials 30 --rss-trials 5
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
- `results/reports/baseline_comparison.json`
- `results/reports/baseline_comparison.md`
- `results/reports/artifact_integrity.json`
- `results/reports/artifact_integrity.md`

The repeated E5 measurement writes:

- `results/metrics/overhead_repeated.json`
- `results/metrics/overhead_repeated.csv`

The E6-P performance study writes:

- `results/metrics/baseline_performance_repeated.json`
- `results/metrics/baseline_performance_repeated.csv`
- `results/reports/baseline_performance_repeated.md`

The bounded verifier-only scale study writes:

- `results/metrics/multislice_verifier_scaling.json`
- `results/metrics/multislice_verifier_scaling.csv`
- `results/reports/multislice_verifier_scaling.md`

The retained final local evidence release also records:

- `results/reports/final_release_manifest.json`
- `results/reports/final_release_manifest.md`

These manifest files are a retained record of the frozen release. The reproduction commands do not recreate them. Verify the retained tag and manifest before rerunning commands that overwrite generated reports. Exact timing values and result-file hashes can differ on another host or software environment.

## Why The Policy Artefacts Are Representational

The generated policy artefacts are representational and graph-consumable rather than executable production policies. They exist to encode bounded transport segmentation, O-Cloud micro-segmentation, and minimal slice-scoped O-RAN metadata for later static analysis.

They do **not** claim:

- a production O-RAN control path,
- live RIC or xApp or rApp enforcement,
- runtime enforcement or packet-level behavior.

## Functional And Security Evidence

- `E1 Schema expressiveness`: confirms the accepted bounded intent remains unambiguous and the bounded invalid intents fail for the expected reasons, including explicit rejection of an ambiguous invalid case.
- `E2 Compiler coherence`: confirms exactly three policy artefacts, identifier consistency, and deterministic regeneration.
- `E3 Reachability verification`: confirms both permitted paths to `shared_auth_log` survive while forbidden cross-slice paths do not.
- `E4 Negative-control misconfiguration`: confirms five unsafe topologies are rejected during validation and one over-restrictive topology is rejected during verification because required shared-service reachability is missing.
- `E6 Controlled baseline comparison`: holds the node set, query set, source topology, and verifier constant while comparing permissive topology-only, deny-all, and proposed compiled-policy edge conditions.
- `E7 Post-compilation policy integrity`: changes only the bytes of one manifest-listed policy, confirms that its parsed meaning is unchanged, and requires verification to reject the mismatched bundle before graph construction or report writing.

## Performance And Scale Characterisation

- `E5 Practical overhead`: reports local stage timing, processor time, Python `tracemalloc` peak allocation, file size, rule count, and graph-size evidence. The retained repeated study contains 5 warm-ups and 30 measured runs. Its instrumented harness time is not the pure pipeline duration, and its Python allocation measure is not whole-process memory.
- `E6-P Repeated controlled-condition performance`: measures pure verification cost for the permissive, deny-all, and compiled-policy E6 graphs while holding the nodes, queries, verifier, trial count, and batch size constant. It does not change the functional result established by E6.
- `S1 Bounded multi-slice verifier scaling`: measures deterministic verifier-only scenarios representing 2, 3, 4, and 10 slices. It bypasses the end-to-end schema, semantic validator, compiler, compiled-policy loader, and topology-to-policy graph builder.

## How To Reproduce Reports

From a clean checkout:

```bash
make install
source .venv/bin/activate
make run-all
python experiments/run_e5_repeated.py --warmups 5 --trials 30
python experiments/run_e6_repeated_performance.py --warmups 5 --trials 30 --iterations 500
python experiments/run_s1_multislice_verifier_scaling.py --slices 2 3 4 10 --warmups 5 --trials 30 --rss-trials 5
```

A successful run from the retained `sit746-evidence-2026-09-02` tag should report 69 passing automated tests and seven passing E1 to E7 experiment groups with no failures. E5 repeated, E6-P, and S1 are separate runs. The retained release manifest is not regenerated, and exact timing values and result-file hashes can differ outside the retained environment. Then inspect:

- `results/reports/verification_report.json`
- `results/reports/verification_report.md`
- `results/reports/experiment_summary.json`
- `results/reports/experiment_summary.md`
- `results/metrics/overhead_metrics.json`
- `results/metrics/overhead_repeated.json`
- `results/reports/baseline_comparison.json`
- `results/reports/baseline_comparison.md`
- `results/reports/artifact_integrity.json`
- `results/reports/artifact_integrity.md`
- `results/metrics/baseline_performance_repeated.json`
- `results/metrics/baseline_performance_repeated.csv`
- `results/reports/baseline_performance_repeated.md`
- `results/metrics/multislice_verifier_scaling.json`
- `results/metrics/multislice_verifier_scaling.csv`
- `results/reports/multislice_verifier_scaling.md`
- `results/reports/final_release_manifest.json`
- `results/reports/final_release_manifest.md`

## How To Interpret Pass And Fail

- `pass` means the bounded local model behaved exactly as the fixed methodology requires.
- `fail` means the repository detected a structural, semantic, compilation, reachability, or negative-control violation relative to the fixed bounded design.
- A passing verification report means only the modeled graph satisfied the required reachability and non-reachability properties.
- A passing experiment summary means E1-E7 all completed successfully within the bounded local proof of concept.

## Bounded Limitations

This repository proves only model-based static non-reachability in the local policy-and-topology model. E7 adds a narrow fail-closed check for byte changes to manifest-listed generated policies. It does not provide manifest authentication, detection of coordinated policy and manifest tampering, protection against a change after the check, binding of topology, query, or report files, detection of a compromised compiler or verifier, or observation of runtime drift. S1 tests generated in-memory graphs directly at the verifier layer. It bypasses the end-to-end schema, semantic validator, compiler, compiled-policy loader, and topology-to-policy graph builder. The repository does not establish runtime enforcement, packet delivery guarantees, authenticated cryptographic protection, live O-RAN behavior, production scalability, or complete end-to-end O-RAN security.
