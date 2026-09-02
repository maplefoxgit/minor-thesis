# Post-Compilation Policy Integrity Experiment

## Question

Can a manifest-listed generated policy be changed after compilation without invalidating the verification evidence?

## Controlled conditions

| Condition | Parsed policy meaning | SHA-256 state | Verification result |
| --- | --- | --- | --- |
| Unchanged compiler output | unchanged | 3/3 manifest hashes match | pass |
| Byte-only mutation to transport_policy.generated.json | unchanged | target hash differs from manifest | rejected before graph construction |
| Clean regeneration | unchanged | original manifest restored | pass |

## Mutation evidence

- Artifact: transport_policy.generated.json
- Mutation: One trailing whitespace sequence was appended. The JSON remained valid and parsed to the same policy document.
- Manifest SHA-256: 8fa30f637b66293d34e56d75f4fc6470fc455d7d9f4d987ef5f22b497ee571a5
- Mutated SHA-256: 9e62e0192aafad950a58306a09fd1e37e66e99929f8e3689f9f4a32ca92ffaea
- Parsed document unchanged: True

## Rejection evidence

- Result: rejected
- Stage: pre-graph integrity gate
- Pass report created after mutation: False
- Reason: compiled policy integrity check failed: transport_policy.generated.json: expected sha256=8fa30f637b66293d34e56d75f4fc6470fc455d7d9f4d987ef5f22b497ee571a5, actual sha256=9e62e0192aafad950a58306a09fd1e37e66e99929f8e3689f9f4a32ca92ffaea

## Interpretation boundary

E7 detects post-compilation byte changes to the three generated policy files listed in the retained manifest when the integrity gate executes. It does not authenticate the manifest, eliminate a concurrent check-to-use race, detect coordinated modification of both a policy and its manifest, bind topology, query, or report files to the same run, detect a compromised compiler or verifier, or observe runtime network drift.
