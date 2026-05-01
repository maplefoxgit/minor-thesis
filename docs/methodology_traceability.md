# Methodology Traceability

| Research question | Repository mapping in this phase | Status |
| --- | --- | --- |
| RQ1: Bounded slice-security intent formalization and validation for the two-slice proof of concept | `schemas/slice_security_intent.schema.json`, `intents/two_slice_shared_auth_log.valid.yaml`, `intents/invalid/*.yaml`, `tests/test_schema_validation.py`, `tests/test_semantic_validation.py`, `topology/base_topology.yaml`, `tests/test_topology_load.py` | Implemented in this repository phase |
| RQ2: Transport-aware compilation from validated intent into policy artefacts | Planned target outputs only: `policies/generated/transport_policy.generated.json`, `policies/generated/ocloud_microsegmentation.generated.yaml`, `policies/generated/oran_slice_policy.generated.json` | Planned, not yet implemented |
| RQ3: Static graph-based reachability verification over compiled policy and topology representations | Planned verifier stage only; no runtime auditing and no live O-RAN integration in this phase | Planned, not yet implemented |

## Notes

- This phase is limited to local Python validation, fixture loading, and test coverage.
- Runtime auditing, packet testing, and live O-RAN components are intentionally out of scope.
- No generated policy artefacts are produced yet.
