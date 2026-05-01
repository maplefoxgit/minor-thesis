# Methodology Traceability

| Research question | Repository mapping in this phase | Status |
| --- | --- | --- |
| RQ1: Bounded slice-security intent formalization and validation for the two-slice proof of concept | `schemas/slice_security_intent.schema.json`, `intents/two_slice_shared_auth_log.valid.yaml`, `intents/invalid/*.yaml`, `tests/test_schema_validation.py`, `tests/test_semantic_validation.py`, `topology/base_topology.yaml`, `tests/test_topology_load.py` | Implemented in this repository phase |
| RQ2: Transport-aware compilation from validated intent into policy artefacts | `src/oran_slice_security/compiler.py`, `src/oran_slice_security/policy_models.py`, `policies/generated/transport_policy.generated.json`, `policies/generated/ocloud_microsegmentation.generated.yaml`, `policies/generated/oran_slice_policy.generated.json`, `policies/generated/manifest.json`, `tests/test_compiler_outputs.py`, `tests/test_compiler_determinism.py`, `tests/test_compiler_conflicts.py` | Implemented in this repository phase |
| RQ3: Static graph-based reachability verification over compiled policy and topology representations | `src/oran_slice_security/graph_builder.py`, `src/oran_slice_security/verifier.py`, `src/oran_slice_security/report.py`, `verifier/queries/baseline_queries.yaml`, `results/reports/verification_report.json`, `results/reports/verification_report.md`, `tests/test_graph_builder.py`, `tests/test_reachability_verifier.py`, `tests/test_negative_controls.py`, `tests/test_report_generation.py` | Implemented in this repository phase |

## Notes

- This phase is limited to local Python validation, deterministic representational compilation, fixture loading, and test coverage.
- The bounded static assurance claim is limited to model-based reachability and non-reachability in the local compiled policy-and-topology graph.
- Runtime auditing, packet testing, and live O-RAN components are intentionally out of scope.
- No production O-RAN control path is claimed by the generated artefacts.
