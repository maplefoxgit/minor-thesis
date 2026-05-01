# Limitations

This repository is intentionally bounded. It does **not** provide or claim:

- no production O-RAN deployment,
- no live RIC, xApp, or rApp integration,
- no Kubernetes dependency,
- no runtime drift claim,
- no cryptographic enforcement claim,
- no packet-delivery claim,
- no complete O-RAN security claim.

Additional boundaries:

- The model is fixed to exactly two slices, `slice_a` and `slice_b`.
- The model is fixed to exactly one shared terminal service, `shared_auth_log`.
- The assurance claim is static and model-based only.
- The overhead evidence is modest local proof-of-concept evidence only and does not establish production scalability.
