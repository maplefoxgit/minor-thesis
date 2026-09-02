# Repeated E6 Verification Performance

## Result

The same eight nodes, seven queries, verifier implementation, Python process, warm-up count, trial count, and batch size were used for all three conditions. Only the permitted communication edges changed.

| Condition | Edges | Functional outcome | Median pure verification | Interquartile range |
| --- | ---: | --- | ---: | ---: |
| permissive_topology_only | 10 | balanced fail | 0.0238 ms | 0.0232 to 0.0247 ms |
| deny_all | 0 | balanced fail | 0.0061 ms | 0.0058 to 0.0062 ms |
| proposed_compiled_policy | 5 | balanced pass | 0.0124 ms | 0.0120 to 0.0127 ms |

## Interpretation

This experiment adds execution-cost measurements to the existing E6 functional comparison. The compiled-policy condition remains the only condition that satisfies the balanced functional objective. Timing values describe the cost of evaluating each local graph condition and are not an effectiveness score.

## Measurement boundary

Each retained value is the batch elapsed or processor time divided by the number of pure verify_graph calls. Graph construction, query loading, file input and output, and report generation are excluded. Timing batches run without tracemalloc. A separate repeated batch records peak Python allocation and does not represent process memory.

## Comparison boundary

The three local conditions can be compared with one another because their measurement protocol is controlled. They cannot be ranked directly against INTPOL or Scylla because the workloads, algorithms, hardware, execution boundaries, and summary statistics differ.
