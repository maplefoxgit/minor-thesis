.PHONY: install test validate compile verify integrity baseline-performance scale experiments run-all clean-generated

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(PYTHON) -m pip
INSTALL_STAMP := $(VENV)/.installed

install: $(INSTALL_STAMP)

$(INSTALL_STAMP): pyproject.toml
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e .[dev]
	touch $(INSTALL_STAMP)

test: $(INSTALL_STAMP)
	$(PYTHON) -m pytest

validate: $(INSTALL_STAMP)
	$(PYTHON) -m oran_slice_security validate-intent --schema schemas/slice_security_intent.schema.json --intent intents/two_slice_shared_auth_log.valid.yaml
	$(PYTHON) -m oran_slice_security validate-topology --topology topology/base_topology.yaml

compile: $(INSTALL_STAMP)
	$(PYTHON) -m oran_slice_security compile --schema schemas/slice_security_intent.schema.json --intent intents/two_slice_shared_auth_log.valid.yaml --topology topology/base_topology.yaml --out policies/generated

verify: $(INSTALL_STAMP)
	$(PYTHON) -m oran_slice_security verify --topology topology/base_topology.yaml --policies policies/generated --queries verifier/queries/baseline_queries.yaml --out results/reports

integrity: $(INSTALL_STAMP)
	$(PYTHON) experiments/run_e7_artifact_integrity.py

baseline-performance: $(INSTALL_STAMP)
	$(PYTHON) experiments/run_e6_repeated_performance.py

scale: $(INSTALL_STAMP)
	$(PYTHON) experiments/run_s1_multislice_verifier_scaling.py

experiments: $(INSTALL_STAMP)
	$(PYTHON) experiments/run_all_experiments.py

run-all: $(INSTALL_STAMP)
	$(MAKE) validate
	$(MAKE) compile
	$(MAKE) verify
	$(MAKE) test
	$(MAKE) experiments

clean-generated:
	rm -f policies/generated/transport_policy.generated.json
	rm -f policies/generated/ocloud_microsegmentation.generated.yaml
	rm -f policies/generated/oran_slice_policy.generated.json
	rm -f policies/generated/manifest.json
