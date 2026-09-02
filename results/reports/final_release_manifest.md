# SIT746 Final Evidence Manifest

## Source state

- Release identifier: `sit746-evidence-2026-09-02`
- Source commit: `0cd37db614413f773faceb593e08bdb456b70e95`
- Local branch: `feature/sit746-final-evidence`
- Source tree before measurement: clean
- Platform: macOS 26.6.2, arm64
- Python: CPython 3.12.13

## Verification result

- Automated tests: 69 passed
- Core experiments: E1 to E7 passed, with 0 failures
- Repeated E5 protocol: 5 warm-up runs and 30 measured runs
- Repeated E6 protocol: 5 warm-up batches and 30 measured batches per condition, with 500 pure verification calls per batch
- Verifier-only scale protocol: 5 warm-up runs, 30 measured runs, and 5 isolated resident-memory workers for each of 2, 3, 4 and 10 slices

## Main completed results

- E7 rejected a byte-only policy change at the pre-graph integrity gate and created no passing report for the changed bundle.
- Repeated E5 measured pure in-memory verification separately from graph construction, query loading and report writing.
- Repeated E6 measured the cost of the three controlled graph conditions while retaining the separate functional result.
- The scale study accepted each valid fixture and detected the injected forbidden cross-slice route at every tested size.

## Claim boundary

This release supports bounded local model-based evidence. It does not establish live enforcement, production scalability, formal proof, runtime drift resistance, or a matched performance ranking against prior systems.

The machine-readable manifest in `final_release_manifest.json` contains the SHA-256 value for each retained evidence file.
