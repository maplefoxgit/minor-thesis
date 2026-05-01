# Limitations

This repository is intentionally bounded. It does **not** provide or claim:

- production O-RAN deployment,
- live RIC, xApp, or rApp integration,
- Kubernetes dependency,
- runtime drift detection,
- cryptographic enforcement,
- packet-delivery assurance,
- complete O-RAN security assurance.

Additional boundaries:

- The model is fixed to exactly two slices, `slice_a` and `slice_b`.
- The model is fixed to exactly one shared terminal service, `shared_auth_log`.
- The assurance claim is static and model-based only.
- The overhead evidence is modest local proof-of-concept evidence only and does not establish production scalability.
