# Bounded Multi-Slice Verifier Scaling Study

## Result

The existing graph verifier passed every required, forbidden, and terminal check for deterministic synthetic scenarios containing 2, 3, 4, and 10 slices. No functional breaking point was observed within that tested range.

| Slices | Nodes | Edges | Estimated rules | Property criteria | Path searches | Negative control | Median pure verification | Median path searches per second | Median worker peak RSS |
| ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| 2 | 8 | 5 | 10 | 7 | 8 | pass | 0.015 ms | 531,866 | 32.44 MiB |
| 3 | 11 | 7 | 21 | 16 | 18 | pass | 0.027 ms | 655,537 | 32.44 MiB |
| 4 | 14 | 9 | 36 | 29 | 32 | pass | 0.042 ms | 759,276 | 32.45 MiB |
| 10 | 32 | 21 | 210 | 191 | 200 | pass | 0.278 ms | 719,602 | 32.61 MiB |

## Measurement boundary

Pure verification time measures verify_graph on a prebuilt graph and preloaded queries. Model-build time measures only this study's synthetic fixture construction. Peak resident memory is the maximum for an isolated Python worker that imports the package, builds one fixture, and verifies it. Stage timing runs without tracemalloc, and Python allocation is profiled in a separate repeated call. Property criteria count reported outcomes. Path-search invocations count every breadth-first search, including one terminal-service search per workload.
The estimated rule count uses 2N squared plus N for the pairwise policy shape. It is analytical only because this verifier-only study does not compile N-slice policy files.

## Comparison boundary

The metric families align with verification studies such as Scylla: model size, rule-equivalent count, query count, pure verification time, throughput, and process memory. The workloads, hardware, implementation, architecture, and repetition rules are different, so no speed or memory ratio is valid.

## Scope boundary

This is a verifier-layer scale study using generated in-memory graphs. It does not show that the current two-slice intent schema, semantic validator, compiler, or graph loader supports more than two slices.
