# Reproducibility

## Goal

These steps let a supervisor clone the repository and reproduce the complete bounded evidence pack from scratch on a local machine.

## Prerequisites

- Python 3.11 or newer
- `make`
- a local shell environment

No external networked runtime, Kubernetes environment, Docker environment, or O-RAN control-plane deployment is required.

## Fresh Reproduction Steps

1. Clone the repository and enter it.

```bash
git clone <repository-url>
cd minor-thesis
```

2. Create the local environment and install dependencies.

```bash
make install
source .venv/bin/activate
```

3. Run validation, compilation, verification, tests, and experiments E1-E6.

```bash
make run-all
```

4. Optionally reproduce the repeated E5 distribution.

```bash
python experiments/run_e5_repeated.py --warmups 5 --trials 30
```

5. Inspect the generated evidence.

```bash
ls policies/generated
ls results/reports
ls results/metrics
```

## Expected Reproducible Outputs

Policy artefacts:

- `policies/generated/transport_policy.generated.json`
- `policies/generated/ocloud_microsegmentation.generated.yaml`
- `policies/generated/oran_slice_policy.generated.json`
- `policies/generated/manifest.json`

Verification evidence:

- `results/reports/verification_report.json`
- `results/reports/verification_report.md`

Experiment evidence:

- `results/reports/experiment_summary.json`
- `results/reports/experiment_summary.md`
- `results/reports/baseline_comparison.json`
- `results/reports/baseline_comparison.md`
- `results/metrics/overhead_metrics.json`

Optional repeated-overhead evidence:

- `results/metrics/overhead_repeated.json`
- `results/metrics/overhead_repeated.csv`

## What A Successful Reproduction Looks Like

- `make run-all` exits successfully.
- `pytest` reports 50 passing tests.
- `results/reports/verification_report.json` reports `overall_status: "pass"` for the bounded baseline.
- `results/reports/experiment_summary.json` reports six passing experiment groups and zero failures.
- E6 reports the proposed compiled-policy condition as the only condition satisfying required reachability, forbidden-path blocking, and terminal-service constraints simultaneously.
- `policies/generated/` contains exactly three `*.generated.*` policy artefacts.

## Reference Repeated-Overhead Capture

A 5-warm-up, 30-trial E5 run was captured on 23 July 2026 using CPython 3.14.6 on Apple M5 hardware. The median end-to-end wall-clock time was approximately 0.117 seconds, with an interquartile range of approximately 0.1165-0.1181 seconds. The median maximum Python `tracemalloc` allocation was 208,258 bytes. These values describe one local environment only.

The repeated benchmark records the Git commit, platform, Python version, functional invariants, per-trial timings, quartiles, range, standard deviation, and coefficient of variation. It distinguishes the timer around the complete E5 run from the sum of the four individually measured stages.

## Interpretation Boundary

Successful reproduction shows only that the bounded local proof of concept behaves as designed in the repository's static model. It does not demonstrate runtime enforcement, live O-RAN security, production deployment readiness, complete operational assurance, or production scalability.
