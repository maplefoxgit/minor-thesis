# Experiment Summary

## Summary
- Overall status: `pass`
- Passed experiments: 5
- Failed experiments: 0
- Thesis interpretation: the bounded proof of concept demonstrates only local, model-based evidence for the fixed two-slice scenario and does not claim production assurance.

## Experiment Results
### E1 Schema expressiveness
- Status: `pass`
- Schema coverage: 1.00
- Accepted-intent ambiguity count: 0
- Ambiguous invalid case rejection count: 1
- Unsupported case count: 0
- valid_intent: `pass`; valid intent accepted
- third_slice: `pass`; exactly two slices named slice_a and slice_b are required
- missing_shared_service: `pass`; exactly one shared service named shared_auth_log is required
- ambiguous_direction: `pass`; ambiguous direction 'bidirectional' for rule slice_a_workload -> shared_auth_log
- conflicting_allow_deny: `pass`; conflicting allow and deny rule for slice_a_workload -> shared_auth_log
- shared_service_transit: `pass`; shared_auth_log must declare transit_allowed=false
- duplicate_endpoint: `pass`; duplicate workload endpoint 'slice_a_workload' across slice_a and slice_b

### E2 Compiler coherence
- Status: `pass`
- Policy artefact count: 3
- Unresolved conflict count: 0
- exact_policy_artifact_count: `True`
- snssai_present: `True`
- slice_ids_consistent: `True`
- shared_auth_log_references_consistent: `True`
- transport_segment_references_consistent: `True`
- ocloud_namespace_labels_consistent: `True`
- snssai_values_consistent: `True`
- determinism_passed: `True`

### E3 Reachability verification
- Status: `pass`
- Required reachable checks passed: 2
- Forbidden unreachable checks passed: 4
- Graph size: nodes=8, edges=5
- Required path slice_a_workload -> shared_auth_log: `pass`; slice_a_workload -> tn_segment_slice_a -> tn_segment_shared -> shared_auth_log
- Required path slice_b_workload -> shared_auth_log: `pass`; slice_b_workload -> tn_segment_slice_b -> tn_segment_shared -> shared_auth_log

### E4 Negative-control misconfiguration
- Status: `pass`
- bad_direct_cross_slice.yaml: expected=`reject`, actual=`rejected`, control_passed=`True`; direct cross-slice workload edge is not allowed
- bad_transport_misbinding.yaml: expected=`reject`, actual=`rejected`, control_passed=`True`; node 'slice_a_workload' must set transport_segment='tn_segment_slice_a'
- bad_transport_cross_slice_edge.yaml: expected=`reject`, actual=`rejected`, control_passed=`True`; transport edge tn_segment_slice_a -> tn_segment_slice_b is not permitted by the compiled transport policy
- bad_shared_service_transit.yaml: expected=`reject`, actual=`rejected`, control_passed=`True`; shared_auth_log must declare transit_allowed=false
- bad_missing_default_deny.yaml: expected=`reject`, actual=`rejected`, control_passed=`True`; topology must declare default_deny.enforced=true
- bad_missing_shared_service_path.yaml: expected=`reject`, actual=`rejected`, control_passed=`True`; missing required reachable path(s): slice_a_workload -> shared_auth_log, slice_b_workload -> shared_auth_log

### E5 Practical overhead
- Status: `pass`
- Graph size: nodes=8, edges=5
- Generated rule count: 10
- Peak Python tracemalloc bytes (max stage): 208254 bytes
- Overall wall-clock time: 0.052091 seconds
- Overall CPU time: 0.052038 seconds
- Memory measurement basis: Python tracemalloc peak bytes (not process RSS)
- Local overhead note: These measurements report modest local proof-of-concept overhead only. They do not establish production scalability.

## Result Files
- Verification report JSON: `results/reports/verification_report.json`
- Verification report Markdown: `results/reports/verification_report.md`
- Experiment summary JSON: `results/reports/experiment_summary.json`
- Experiment summary Markdown: `results/reports/experiment_summary.md`
- Overhead metrics JSON: `results/metrics/overhead_metrics.json`

## Limitations
This evidence proves only bounded, model-based static behavior in the local proof-of-concept representation. It does not establish runtime security, packet delivery outcomes, live O-RAN control behavior, or production scalability.
