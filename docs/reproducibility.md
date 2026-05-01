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

## Reference Environment Capture

The committed evidence under `results/` was regenerated on May 1, 2026 in a local macOS environment after activating `.venv`.

Commands recorded for reproducibility:

```bash
python --version
pip freeze
uname -a
make run-all
pytest
```

Observed reference outputs:

- `python --version`: `Python 3.14.3`
- `uname -a`: `Darwin ryans-MacBook-Pro.local 25.4.0 Darwin Kernel Version 25.4.0: Thu Mar 19 19:33:43 PDT 2026; root:xnu-12377.101.15~1/RELEASE_ARM64_T8142 arm64`
- `pip freeze`: recorded in `docs/reference_pip_freeze.txt`, with the editable local path normalized to `-e .` for portability
- `make run-all`: completed successfully, including validation, compilation, verification, `pytest`, and `python experiments/run_all_experiments.py`
- `pytest`: `48 passed`

## Interpretation Boundary

Successful reproduction shows only that the bounded local proof of concept behaves as designed in the repository's static model. It does not demonstrate runtime enforcement, live O-RAN security, production deployment readiness, or complete operational assurance.
