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
cd Minor-Thesis
```

2. Create the local environment and install dependencies.

```bash
make install
source .venv/bin/activate
```

3. Run the bounded validation, compilation, verification, test, and experiment flow.

```bash
make run-all
python experiments/run_all_experiments.py
```

4. Inspect the generated evidence.

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
- `results/metrics/overhead_metrics.json`

## What A Successful Reproduction Looks Like

- `make run-all` exits successfully.
- `python experiments/run_all_experiments.py` exits successfully.
- `results/reports/verification_report.json` reports `overall_status: "pass"` for the bounded baseline.
- `results/reports/experiment_summary.json` reports all experiments E1-E5 as passing.
- `policies/generated/` contains exactly three `*.generated.*` policy artefacts.

## Interpretation Boundary

Successful reproduction shows only that the bounded local proof of concept behaves as designed in the repository's static model. It does not demonstrate runtime enforcement, live O-RAN security, production deployment readiness, or complete operational assurance.
