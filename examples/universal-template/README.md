# Universal Template: Two Protected Zones Plus One Shared Service

## What this is

This guide explains the repository as a reusable pattern in plain English first.

The pattern is simple:

1. You have **Zone A**.
2. You have **Zone B**.
3. Both zones are allowed to reach **one approved shared service**.
4. Everything else is denied by default unless it is explicitly allowed.
5. A compiler turns the high-level intent into a few small policy artefacts.
6. A graph-based verifier checks that the required paths exist and the forbidden paths do not.

This is the same pattern used by the thesis implementation in this repository. The thesis version is intentionally bounded to two slices, one shared service, local files, and static verification only.

## The pattern in plain English

Imagine two separate rooms with computers in them.

- Room A should stay mostly separate from Room B.
- Both rooms still need to talk to one trusted shared helper service.
- We write down the rules once at a high level.
- The repository checks whether the rules make sense.
- The repository translates them into small machine-readable policy files.
- The repository builds a graph of what can talk to what.
- The repository proves, in this small local model, that the trusted path exists and the forbidden paths do not.

That is the general reusable idea.

## The same pattern in slightly more technical terms

The repository implements a bounded policy pipeline:

1. A high-level intent document declares two isolated zones, one permitted shared service, default-deny requirements, and reachability expectations.
2. Validation checks the intent and the topology against the fixed bounded model.
3. Compilation emits exactly three representational policy artefacts:
   - one transport segmentation artefact,
   - one O-Cloud micro-segmentation artefact,
   - one minimal slice-scoped O-RAN metadata artefact.
4. Graph construction keeps only the topology edges that survive those policy artefacts.
5. Verification checks required reachability, forbidden non-reachability, and terminal-service behavior.
6. Experiments E1-E5 package the evidence into reproducible reports.

## How the current repository maps to this template

| Template idea | Current repo concept | Main files |
| --- | --- | --- |
| Zone A | `slice_a` and `slice_a_workload` | [`intents/two_slice_shared_auth_log.valid.yaml`](../../intents/two_slice_shared_auth_log.valid.yaml), [`topology/base_topology.yaml`](../../topology/base_topology.yaml) |
| Zone B | `slice_b` and `slice_b_workload` | [`intents/two_slice_shared_auth_log.valid.yaml`](../../intents/two_slice_shared_auth_log.valid.yaml), [`topology/base_topology.yaml`](../../topology/base_topology.yaml) |
| Approved shared service | `shared_auth_log` | [`intents/two_slice_shared_auth_log.valid.yaml`](../../intents/two_slice_shared_auth_log.valid.yaml), [`topology/base_topology.yaml`](../../topology/base_topology.yaml) |
| Default deny | `default_deny` plus bounded verification requirements | [`intents/two_slice_shared_auth_log.valid.yaml`](../../intents/two_slice_shared_auth_log.valid.yaml), [`topology/base_topology.yaml`](../../topology/base_topology.yaml) |
| Allowed paths | two workload-to-shared-service flows | [`intents/two_slice_shared_auth_log.valid.yaml`](../../intents/two_slice_shared_auth_log.valid.yaml), [`verifier/queries/baseline_queries.yaml`](../../verifier/queries/baseline_queries.yaml) |
| Forbidden paths | cross-zone workload and transport communication | [`intents/two_slice_shared_auth_log.valid.yaml`](../../intents/two_slice_shared_auth_log.valid.yaml), [`verifier/queries/baseline_queries.yaml`](../../verifier/queries/baseline_queries.yaml) |
| Intent validation | schema and semantic validation | [`schemas/slice_security_intent.schema.json`](../../schemas/slice_security_intent.schema.json), [`src/oran_slice_security/validation.py`](../../src/oran_slice_security/validation.py) |
| Policy compilation | deterministic compiler | [`src/oran_slice_security/compiler.py`](../../src/oran_slice_security/compiler.py), [`policies/generated/`](../../policies/generated/) |
| Graph building | surviving policy-and-topology graph | [`src/oran_slice_security/graph_builder.py`](../../src/oran_slice_security/graph_builder.py) |
| Static verification | path checks and terminal-service checks | [`src/oran_slice_security/verifier.py`](../../src/oran_slice_security/verifier.py), [`results/reports/verification_report.md`](../../results/reports/verification_report.md) |
| Evidence pack | E1-E5 experiments and reports | [`experiments/`](../../experiments/), [`results/reports/`](../../results/reports/), [`results/metrics/`](../../results/metrics/) |

## What can be customized safely

These are the easiest, thesis-safe ways to reuse the pattern mentally or explain it to someone else:

- Change the story around the model. For example, you can explain the two slices as departments, tenants, plants, labs, or business units.
- Add beginner-friendly documentation, diagrams, walkthroughs, or teaching material.
- Add more negative-control documentation or explanation around the current fixed fixtures.
- Rephrase the domain meaning of `slice_a`, `slice_b`, and `shared_auth_log` without changing the underlying code or bounded claim.

## What can be changed with some care

These changes are still compatible with the current bounded pattern, but they need more attention because they affect the reproducible thesis artefacts:

- Adding new example guides that map the same fixed code names into another story.
- Adding new negative-control fixtures that still respect the two-zone, one-shared-service structure.
- Adjusting namespaces, S-NSSAI values, or documentation wording while keeping the fixed two-slice structure intact.
- Extending tests or experiments in a way that stays within the current local, static, model-based boundary.

## What is fixed because of thesis scope

These parts are intentionally fixed in the current repository:

- exactly two slices: `slice_a` and `slice_b`,
- exactly one shared terminal service: `shared_auth_log`,
- exactly three generated policy artefacts,
- local file-based compilation and verification,
- static graph reachability only,
- bounded proof-of-concept evidence rather than production enforcement.

If you change those assumptions too much, you are no longer just reusing the current template. You are moving beyond the current thesis implementation.

## Copy this template mentally into another domain

You can reuse the pattern like this:

1. Pick two protected zones that should stay separated.
2. Pick one approved shared service they both still need.
3. Write the required allowed paths.
4. Write the forbidden cross-zone paths.
5. Keep a default-deny mindset.
6. Compile the high-level intent into representational policy artefacts.
7. Build a graph of the surviving communication paths.
8. Verify that required paths exist and forbidden paths do not.
9. Keep the claim narrow: this proves only what the local static model proves.

## Template takeaway

The universal pattern is:

**two protected zones + one approved shared service + default deny + compiled artefacts + graph verification + bounded evidence**

That is the reusable idea. The rest of this repository shows one thesis-bounded implementation of that idea.
