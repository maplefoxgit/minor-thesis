# Examples And Beginner-Friendly Guides

This page collects the beginner-friendly layers that sit on top of the thesis-oriented repository.

These guides are additive only. They do not replace the core thesis framing, and they do not widen the bounded claim.

## Guides

- [Universal template](../examples/universal-template/README.md)
  Explains the repository as a reusable two-zone plus one shared-service pattern in domain-neutral terms.
- [Hospital example](../examples/hospital-example/README.md)
  Re-explains the same bounded implementation as a Radiology and Pharmacy story for readers who are new to the topic.

## Best reading order if you are new

1. Start with the [Hospital example](../examples/hospital-example/README.md) if you want the friendliest explanation first.
2. Read the [Universal template](../examples/universal-template/README.md) if you want the general reusable pattern.
3. Return to the main [README](../README.md) for the thesis-oriented commands, outputs, and scope statement.
4. Use [Reproducibility](./reproducibility.md) if you want to run the full bounded evidence pipeline yourself.

## Boundary reminder

All of these guides describe the same narrow repository claim:

- local,
- static,
- model-based,
- proof-of-concept,
- an end-to-end pipeline fixed to two slices,
- one shared service,
- E5, E6-P, and S1 characterise local performance or scale and do not add a broader functional or security claim,
- E7 does not provide manifest authentication, detection of coordinated policy and manifest tampering, protection against a change after the check, topology, query, or report binding, detection of a compromised compiler or verifier, or runtime drift observation,
- S1 bypasses the intent schema, semantic validator, compiler, compiled-policy loader, and topology-to-policy graph builder,
- no production-scale assurance claim.
