# Methodology Traceability

## Research Questions

| Research question | Repository mapping | Status |
| --- | --- | --- |
| RQ1: Bounded slice-security intent formalization and validation for the two-slice proof of concept | `schemas/slice_security_intent.schema.json`, `intents/two_slice_shared_auth_log.valid.yaml`, `intents/invalid/*.yaml`, `src/oran_slice_security/validation.py`, `tests/test_schema_validation.py`, `tests/test_semantic_validation.py`, `tests/test_topology_load.py` | Implemented |
| RQ2: Transport-aware compilation from validated intent into policy artefacts | `src/oran_slice_security/compiler.py`, `src/oran_slice_security/policy_models.py`, `policies/generated/transport_policy.generated.json`, `policies/generated/ocloud_microsegmentation.generated.yaml`, `policies/generated/oran_slice_policy.generated.json`, `policies/generated/manifest.json`, `tests/test_compiler_outputs.py`, `tests/test_compiler_determinism.py`, `tests/test_compiler_conflicts.py` | Implemented |
| RQ3: Static graph-based reachability verification over compiled policy and topology representations | `src/oran_slice_security/graph_builder.py`, `src/oran_slice_security/verifier.py`, `src/oran_slice_security/report.py`, `verifier/queries/baseline_queries.yaml`, `results/reports/verification_report.json`, `results/reports/verification_report.md`, `tests/test_graph_builder.py`, `tests/test_reachability_verifier.py`, `tests/test_negative_controls.py`, `tests/test_report_generation.py`, `tests/test_controlled_baselines.py` | Implemented |

## Experiments

| Experiment | Methodology intent | Repository mapping | Primary evidence |
| --- | --- | --- | --- |
| E1 Schema expressiveness | Show the bounded schema plus semantic layer can represent the valid case and reject required invalid cases | `experiments/run_e1_schema_expressiveness.py`, invalid intent fixtures, validation tests | `results/reports/experiment_summary.json`, `results/reports/experiment_summary.md` |
| E2 Compiler coherence | Show the deterministic compiler emits exactly three coherent artefacts with stable identifiers and hashes | `experiments/run_e2_compiler_coherence.py`, compiler, generated policy artefacts | `policies/generated/*`, `results/reports/experiment_summary.json`, `results/reports/experiment_summary.md` |
| E3 Reachability verification | Show required slice-to-shared-service reachability and forbidden cross-slice non-reachability in the compiled graph | `experiments/run_e3_reachability_verification.py`, graph builder, verifier, baseline queries | `results/reports/verification_report.json`, `results/reports/verification_report.md`, experiment summary |
| E4 Negative-control misconfiguration | Show the bounded verifier fails usefully on intentionally bad topologies | `experiments/run_e4_negative_controls.py`, `topology/negative_controls/*.yaml` | `results/reports/experiment_summary.json`, `results/reports/experiment_summary.md` |
| E5 Practical overhead | Report modest local timing, CPU, memory, file-size, rule-count, and graph-size evidence | `experiments/run_e5_overhead.py` and optional `experiments/run_e5_repeated.py` | `results/metrics/overhead_metrics.json`, `results/metrics/overhead_repeated.json`, experiment summary |
| E6 Controlled baseline comparison | Compare the proposed compiled-policy condition with permissive topology-only and deny-all conditions while holding the node set, topology source, reachability queries, and deterministic breadth-first verifier constant | `experiments/run_e6_controlled_baselines.py`, `tests/test_controlled_baselines.py` | `results/reports/baseline_comparison.json`, `results/reports/baseline_comparison.md`, experiment summary |

## Notes

- The bounded static assurance claim is limited to model-based reachability and non-reachability in the local compiled policy-and-topology graph.
- The E6 comparison demonstrates a safety-availability contrast inside one synthetic eight-node model; it is not a comparison with production O-RAN security products.
- Runtime auditing, packet testing, and live O-RAN components are intentionally out of scope.
- No production O-RAN control path is claimed by the generated artefacts.
- The overhead evidence reports local proof-of-concept cost only and does not claim production scalability or cross-platform performance.
