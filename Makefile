.PHONY: install test validate compile clean-generated

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(PYTHON) -m pip

install:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e .[dev]

test:
	$(PYTHON) -m pytest

validate:
	$(PYTHON) -m oran_slice_security validate-intent --schema schemas/slice_security_intent.schema.json --intent intents/two_slice_shared_auth_log.valid.yaml
	$(PYTHON) -m oran_slice_security validate-topology --topology topology/base_topology.yaml

compile:
	$(PYTHON) -m oran_slice_security compile --schema schemas/slice_security_intent.schema.json --intent intents/two_slice_shared_auth_log.valid.yaml --topology topology/base_topology.yaml --out policies/generated

clean-generated:
	rm -f policies/generated/transport_policy.generated.json
	rm -f policies/generated/ocloud_microsegmentation.generated.yaml
	rm -f policies/generated/oran_slice_policy.generated.json
	rm -f policies/generated/manifest.json
