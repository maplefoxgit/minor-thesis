# Controlled Baseline Comparison

## Experimental control

The node set, source topology, reachability queries, and breadth-first verification algorithm were held constant. Only the communication-edge condition changed.

| Condition | Edges | Required paths preserved | Forbidden paths blocked | Terminal service | Balanced objective |
| --- | ---: | ---: | ---: | --- | --- |
| permissive_topology_only | 10 | 100% | 0% | fail | fail |
| deny_all | 0 | 0% | 100% | pass | fail |
| proposed_compiled_policy | 5 | 100% | 100% | pass | pass |

## Interpretation

- The permissive topology-only condition preserved both required shared-service paths but blocked none of the four forbidden paths.
- The deny-all condition blocked all forbidden paths but removed both required shared-service paths.
- The proposed compiled policy was the only condition that preserved all required paths, blocked all forbidden paths, and kept the shared service terminal.
- Relative to the permissive condition, the proposed policy improved the forbidden-path block rate by 100 percentage points while retaining 100% required reachability.
- Relative to deny-all, the proposed policy improved required-path availability by 100 percentage points without reducing the forbidden-path block rate.

## Boundary

The comparison is controlled and deterministic within one synthetic eight-node model. It demonstrates the safety-availability trade-off of the three edge conditions, not superiority over production O-RAN policy systems.
