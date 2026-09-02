# Limitations

This repository is intentionally bounded. It does **not** provide or claim:

- production O-RAN deployment,
- live RIC, xApp, or rApp integration,
- Kubernetes dependency,
- runtime drift detection,
- authenticated cryptographic enforcement,
- packet-delivery assurance,
- complete O-RAN security assurance.

Additional boundaries:

- The end-to-end intent schema, semantic validator, compiler, compiled-policy loader, and topology-to-policy graph builder are fixed to exactly two slices, `slice_a` and `slice_b`.
- The end-to-end pipeline is fixed to exactly one shared terminal service, `shared_auth_log`.
- The assurance claim is static and model-based only.
- The E5 timing and Python allocation results describe one host and one fixed workload. They do not establish production performance or cross-platform repeatability.
- E6-P characterises pure verification time for only three controlled local graph conditions. It is not functional or security evidence, an effectiveness score, or a benchmark against another system.
- E7 detects a byte change to a manifest-listed generated policy before graph construction. It does not provide manifest authentication, detection of coordinated policy and manifest tampering, protection against a change after the check, topology, query, or report binding, detection of a compromised compiler or verifier, or runtime drift observation.
- S1 characterises only the verifier on generated in-memory graphs representing 2, 3, 4, and 10 slices. It bypasses the end-to-end intent schema, semantic validator, compiler, compiled-policy loader, and topology-to-policy graph builder.
- No capacity breaking point is claimed because no time or memory failure threshold was declared before the S1 run.
