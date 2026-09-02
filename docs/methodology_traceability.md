# Methodology Traceability

## Research Questions

| Research question | Repository mapping | Status |
| --- | --- | --- |
| RQ1: Bounded slice-security intent formalization and validation for the two-slice proof of concept | `schemas/slice_security_intent.schema.json`, `intents/two_slice_shared_auth_log.valid.yaml`, `intents/invalid/*.yaml`, `src/oran_slice_security/validation.py`, `tests/test_schema_validation.py`, `tests/test_semantic_validation.py`, `tests/test_topology_load.py` | Implemented |
| RQ2: Transport-aware compilation from validated intent into policy artefacts | `src/oran_slice_security/compiler.py`, `src/oran_slice_security/policy_models.py`, `policies/generated/transport_policy.generated.json`, `policies/generated/ocloud_microsegmentation.generated.yaml`, `policies/generated/oran_slice_policy.generated.json`, `policies/generated/manifest.json`, `tests/test_compiler_outputs.py`, `tests/test_compiler_determinism.py`, `tests/test_compiler_conflicts.py` | Implemented |
| RQ3: Static graph-based reachability verification over compiled policy and topology representations | `src/oran_slice_security/graph_builder.py`, `src/oran_slice_security/integrity.py`, `src/oran_slice_security/verifier.py`, `src/oran_slice_security/report.py`, `verifier/queries/baseline_queries.yaml`, `results/reports/verification_report.json`, `results/reports/artifact_integrity.json`, `tests/test_graph_builder.py`, `tests/test_artifact_integrity.py`, `tests/test_reachability_verifier.py`, `tests/test_negative_controls.py`, `tests/test_report_generation.py`, `tests/test_controlled_baselines.py` | Implemented for the fixed two-slice pipeline |

## Experiments

E1 to E4, E6, and E7 test functional or security behaviour. E5, E6-P, and S1 characterise local performance or scale and do not add a broader functional claim.

| Experiment | Methodology intent | Repository mapping | Primary evidence |
| --- | --- | --- | --- |
| E1 Schema expressiveness | Show the bounded schema plus semantic layer can represent the valid case and reject required invalid cases | `experiments/run_e1_schema_expressiveness.py`, invalid intent fixtures, validation tests | `results/reports/experiment_summary.json`, `results/reports/experiment_summary.md` |
| E2 Compiler coherence | Show the deterministic compiler emits exactly three coherent artefacts with stable identifiers and hashes | `experiments/run_e2_compiler_coherence.py`, compiler, generated policy artefacts | `policies/generated/*`, `results/reports/experiment_summary.json`, `results/reports/experiment_summary.md` |
| E3 Reachability verification | Show required slice-to-shared-service reachability and forbidden cross-slice non-reachability in the compiled graph | `experiments/run_e3_reachability_verification.py`, graph builder, verifier, baseline queries | `results/reports/verification_report.json`, `results/reports/verification_report.md`, experiment summary |
| E4 Negative-control misconfiguration | Show the bounded workflow rejects five unsafe topologies during validation and one over-restrictive topology during verification | `experiments/run_e4_negative_controls.py`, `topology/negative_controls/*.yaml` | `results/reports/experiment_summary.json`, `results/reports/experiment_summary.md` |
| E5 Practical overhead | Report local stage timing, processor time, Python allocation, file-size, rule-count, and graph-size evidence with timing separated from allocation profiling | `experiments/run_e5_overhead.py`, `experiments/run_e5_repeated.py` | `results/metrics/overhead_metrics.json`, `results/metrics/overhead_repeated.json`, `results/metrics/overhead_repeated.csv`, experiment summary |
| E6 Controlled baseline comparison | Compare the proposed compiled-policy condition with permissive topology-only and deny-all conditions while holding the node set, topology source, reachability queries, and deterministic breadth-first verifier constant | `experiments/run_e6_controlled_baselines.py`, `tests/test_controlled_baselines.py` | `results/reports/baseline_comparison.json`, `results/reports/baseline_comparison.md`, experiment summary |
| E6-P Repeated verification performance | Characterise pure verification cost for the three E6 graph conditions without treating time as functional or security evidence | `experiments/run_e6_repeated_performance.py` | `results/metrics/baseline_performance_repeated.json`, `results/metrics/baseline_performance_repeated.csv`, `results/reports/baseline_performance_repeated.md` |
| E7 Post-compilation policy integrity | Test whether a byte-only change to one manifest-listed policy is rejected before graph construction and before a passing report is written | `experiments/run_e7_artifact_integrity.py`, `src/oran_slice_security/integrity.py`, `tests/test_artifact_integrity.py` | `results/reports/artifact_integrity.json`, `results/reports/artifact_integrity.md`, experiment summary |
| S1 Bounded verifier-only scale characterisation | Measure verification time, median worker peak process resident memory, model size, criterion count, and path-search count for generated 2, 3, 4, and 10-slice graphs, with one injected forbidden route at each size | `experiments/run_s1_multislice_verifier_scaling.py`, `src/oran_slice_security/scaling.py`, `tests/test_multislice_scaling.py` | `results/metrics/multislice_verifier_scaling.json`, `results/metrics/multislice_verifier_scaling.csv`, `results/reports/multislice_verifier_scaling.md` |

## Notes

- The bounded static assurance claim is limited to model-based reachability and non-reachability in the local compiled policy-and-topology graph.
- The E6 comparison demonstrates a safety-availability contrast inside one synthetic eight-node model; it is not a comparison with production O-RAN security products.
- E6-P characterises the cost of pure verification for the three local E6 graph conditions. It is separate from their functional pass or fail result and is not security-effectiveness evidence.
- E7 binds the verifier to the bytes of the three generated policy files listed in the retained manifest. It does not provide manifest authentication, detection of coordinated policy and manifest tampering, protection against a change after the check, topology, query, or report binding, detection of a compromised compiler or verifier, or runtime drift observation.
- S1 is a verifier-layer characterisation using generated in-memory graphs. It bypasses the end-to-end intent schema, semantic validator, compiler, compiled-policy loader, and topology-to-policy graph builder.
- Runtime auditing, packet testing, and live O-RAN components are intentionally out of scope.
- No production O-RAN control path is claimed by the generated artefacts.
- The performance evidence reports local proof-of-concept cost only and does not claim production scalability, cross-platform performance, or superiority over another system.
