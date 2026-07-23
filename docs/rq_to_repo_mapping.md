# RQ-to-Repo Mapping and Related-Work Methodology Alignment

This document explains how the GitHub repository maps to the thesis research questions, methodology, and related-work patterns.

The repository is not a separate coding exercise. It is the practical proof-of-concept implementation of the thesis pipeline.

## Main research question

For supervisor discussion, the three research questions can be summarised by the following umbrella question:

> How can a compact, transport-aware slice-security intent be represented, compiled into coordinated policy artefacts, and statically verified to show that forbidden cross-slice reachability is absent while required shared-service reachability remains available?

In simpler terms:

> Can we write a small security intent, turn it into policy files, and then check whether the resulting model blocks the paths that should be blocked while keeping the one required shared service reachable?

The three research questions remain distinct stages of one pipeline:

- **RQ1 — Intent representation:** compact slice-security intent and schema validation.
- **RQ2 — Policy compilation:** deterministic compiler producing three coordinated representational artefacts.
- **RQ3 — Verification:** graph-based reachability checking over the compiled policy-and-topology model.

## What this repository is trying to show

The repository demonstrates one bounded assurance workflow:

```text
slice-security intent
→ validation
→ policy compilation
→ graph construction
→ reachability verification
→ evidence reports
```

The focus is deliberately narrow:

- two slices: `slice_a` and `slice_b`
- one shared service: `shared_auth_log`
- three generated policy artefacts
- one static graph-based reachability verifier
- one bounded assurance property: forbidden cross-slice paths should be absent while required shared-service paths remain available

The repository does **not** claim to implement a full production O-RAN deployment or a complete O-RAN/3GPP slice lifecycle.

## Methodology pipeline

```mermaid
flowchart LR
    A["RQ1<br/>Intent + Schema<br/>What security behaviour do we want?"]
    B["Validation<br/>Check intent and topology are valid"]
    C["RQ2<br/>Compiler<br/>Turn intent into policy artefacts"]

    D1["transport_policy.generated.json"]
    D2["ocloud_microsegmentation.generated.yaml"]
    D3["oran_slice_policy.generated.json"]

    E["Topology + Policy Graph<br/>Combine topology and compiled artefacts"]
    F["RQ3<br/>Reachability Verifier<br/>Check what can reach what"]
    G["Results / Evidence<br/>Reports, experiments, overhead"]

    P1["Allowed<br/>slice_a_workload → shared_auth_log"]
    P2["Allowed<br/>slice_b_workload → shared_auth_log"]
    X1["Blocked<br/>slice_a_workload ✕ slice_b_workload"]
    X2["Blocked<br/>slice_b_workload ✕ slice_a_workload"]

    A --> B
    B --> C
    C --> D1
    C --> D2
    C --> D3

    D1 --> E
    D2 --> E
    D3 --> E

    E --> F
    F --> P1
    F --> P2
    F --> X1
    F --> X2

    P1 --> G
    P2 --> G
    X1 --> G
    X2 --> G

    classDef rq fill:#d9e8fb,stroke:#2f6fdb,stroke-width:2px,color:#111;
    classDef process fill:#e8f5e9,stroke:#43a047,stroke-width:2px,color:#111;
    classDef artefact fill:#fff3cd,stroke:#d39e00,stroke-width:2px,color:#111;
    classDef allow fill:#d4edda,stroke:#2e7d32,stroke-width:2px,color:#111;
    classDef block fill:#f8d7da,stroke:#c62828,stroke-width:2px,color:#111;
    classDef result fill:#ede7f6,stroke:#6a1b9a,stroke-width:2px,color:#111;

    class A,C,F rq;
    class B,E process;
    class D1,D2,D3 artefact;
    class P1,P2 allow;
    class X1,X2 block;
    class G result;
```

**Figure:** Mapping of the thesis research questions to the repository pipeline: RQ1 defines the intent, RQ2 compiles it into three representational artefacts, and RQ3 verifies the resulting policy-and-topology graph.

## RQ1: compact machine-readable slice-security intent schema

### Plain-English meaning

RQ1 asks whether the required security behaviour can be written in a compact form that a machine can validate.

The intent describes:

- which slices exist
- which shared service is allowed
- which cross-slice paths are forbidden
- whether default deny is enforced
- which minimum transport and O-Cloud controls are required

### Main repo files

- `schemas/slice_security_intent.schema.json`
- `intents/two_slice_shared_auth_log.valid.yaml`
- `intents/invalid/*.yaml`
- `src/oran_slice_security/validation.py`
- `topology/base_topology.yaml`

### Demonstrated by

```bash
make validate
```

or:

```bash
python -m oran_slice_security validate-intent \
  --schema schemas/slice_security_intent.schema.json \
  --intent intents/two_slice_shared_auth_log.valid.yaml

python -m oran_slice_security validate-topology \
  --topology topology/base_topology.yaml
```

### Evidence

- the valid intent is accepted
- invalid intents are rejected
- schema and semantic validation tests pass
- E1 reports schema expressiveness results

Relevant outputs include:

- `results/reports/experiment_summary.json`
- `results/reports/experiment_summary.md`

### What RQ1 proves

RQ1 shows that the bounded slice-security scenario can be represented in a compact, machine-readable form.

### What RQ1 does not prove

RQ1 does not prove that this schema is a full industry O-RAN slice descriptor, a complete 3GPP slice lifecycle model, or a general slice-security language for every possible deployment.

## RQ2: compiler generating coordinated policy artefacts

### Plain-English meaning

RQ2 asks whether one validated intent can be translated into three coordinated policy representations.

The compiler produces exactly three policy artefacts:

- transport segmentation policy
- O-Cloud micro-segmentation policy
- minimal slice-scoped O-RAN policy representation

These are representational and graph-consumable artefacts, not production deployment files.

### Main repo files

- `src/oran_slice_security/compiler.py`
- `src/oran_slice_security/policy_models.py`
- `policies/generated/transport_policy.generated.json`
- `policies/generated/ocloud_microsegmentation.generated.yaml`
- `policies/generated/oran_slice_policy.generated.json`
- `policies/generated/manifest.json`

### Demonstrated by

```bash
make compile
```

or:

```bash
python -m oran_slice_security compile \
  --schema schemas/slice_security_intent.schema.json \
  --intent intents/two_slice_shared_auth_log.valid.yaml \
  --topology topology/base_topology.yaml \
  --out policies/generated
```

### Evidence

RQ2 is shown by:

- exactly three generated policy artefacts
- consistent slice identifiers
- consistent S-NSSAI-style values
- consistent shared-service references
- consistent transport-segment references
- consistent O-Cloud labels
- deterministic output hashes
- conflict rejection

Relevant outputs include:

- `policies/generated/transport_policy.generated.json`
- `policies/generated/ocloud_microsegmentation.generated.yaml`
- `policies/generated/oran_slice_policy.generated.json`
- `policies/generated/manifest.json`
- `results/reports/experiment_summary.json`
- `results/reports/experiment_summary.md`

### What RQ2 proves

RQ2 shows that the same validated slice-security intent can be compiled into three coordinated representational policy artefacts.

### What RQ2 does not prove

RQ2 does not prove that the generated artefacts are production-ready Kubernetes policies, live RIC policies, xApp/rApp policies, carrier transport-controller rules, or complete O-RAN deployment artefacts.

## RQ3: static graph-based reachability verification

### Plain-English meaning

RQ3 asks whether the compiled policy-and-topology model actually produces the expected reachability result.

The verifier checks whether:

- both slices can reach the approved shared service
- the two slice workloads cannot reach each other
- the transport slice segments cannot directly reach each other
- `shared_auth_log` cannot act as a bridge between slices

### Main repo files

- `src/oran_slice_security/graph_builder.py`
- `src/oran_slice_security/verifier.py`
- `src/oran_slice_security/report.py`
- `verifier/queries/baseline_queries.yaml`
- `topology/negative_controls/*.yaml`
- `results/reports/verification_report.json`
- `results/reports/verification_report.md`

### Demonstrated by

```bash
make verify
```

or:

```bash
python -m oran_slice_security verify \
  --topology topology/base_topology.yaml \
  --policies policies/generated \
  --queries verifier/queries/baseline_queries.yaml \
  --out results/reports
```

The full evidence set can be generated with:

```bash
make run-all
```

or:

```bash
python experiments/run_all_experiments.py
```

### Evidence

RQ3 is shown by:

- `slice_a_workload` can reach `shared_auth_log`
- `slice_b_workload` can reach `shared_auth_log`
- `slice_a_workload` cannot reach `slice_b_workload`
- `slice_b_workload` cannot reach `slice_a_workload`
- `tn_segment_slice_a` cannot reach `tn_segment_slice_b`
- `tn_segment_slice_b` cannot reach `tn_segment_slice_a`
- `shared_auth_log` has no outgoing transit path
- negative-control misconfigurations are rejected
- overhead metrics are reported
- the proposed condition is compared with permissive topology-only and deny-all controls

Relevant outputs include:

- `results/reports/verification_report.json`
- `results/reports/verification_report.md`
- `results/reports/experiment_summary.json`
- `results/reports/experiment_summary.md`
- `results/metrics/overhead_metrics.json`
- `results/metrics/overhead_repeated.json`
- `results/reports/baseline_comparison.json`
- `results/reports/baseline_comparison.md`

### What RQ3 proves

RQ3 shows that, in the bounded local policy-and-topology model, the compiled artefacts preserve required shared-service reachability and remove forbidden cross-slice reachability. E6 further shows that the proposed condition is the only tested condition that satisfies both availability and isolation objectives simultaneously: the permissive condition preserves access but exposes forbidden paths, while deny-all blocks forbidden paths but removes required access.

### What RQ3 does not prove

RQ3 does not prove runtime packet delivery, production scalability, runtime drift detection, cryptographic enforcement, xApp trustworthiness, full O-RAN security, or correctness for arbitrary large networks.

## E6: controlled baseline comparison

E6 compares three conditions while holding the source topology, eight-node set, two required queries, four forbidden queries, terminal-service query, and deterministic breadth-first verifier constant:

- **Permissive topology-only:** each non-governance topology adjacency is available bidirectionally. Required shared-service paths remain available, but none of the four forbidden paths is blocked and the shared service can become transit.
- **Deny-all:** all communication edges are removed. Forbidden paths are blocked, but both required shared-service paths are lost.
- **Proposed compiled policy:** the five policy-permitted edges preserve both required paths, block all four forbidden paths, and keep `shared_auth_log` terminal.

The comparison isolates a safety-availability trade-off inside the synthetic model. It does not compare the prototype with production O-RAN products or establish operational superiority. Primary outputs are `results/reports/baseline_comparison.json` and `results/reports/baseline_comparison.md`.

## Why the slice model is abstracted

The slice model is deliberately simplified because the thesis tests one bounded assurance workflow, not a full industry slice implementation.

In real deployments, slice definitions may be spread across many layers and artefacts, including:

- RAN configuration
- transport configuration
- core-network configuration
- O-Cloud configuration
- orchestration descriptors
- policy files
- runtime monitoring systems

This repository does not try to reproduce all of those layers.

Instead, it uses a compact model that is sufficient to test the thesis claim:

> Can a slice-security intent be represented, compiled, and statically checked for forbidden cross-slice reachability?

This abstraction keeps the work feasible, reproducible, and aligned with the research questions.

## Why graph verification matters

The intent says what should happen.

The compiler generates policy artefacts that are supposed to implement that intent.

The topology describes the modelled environment.

The graph verifier checks the combined result.

This matters because mistakes can happen between the original intent and the compiled model. For example:

- the intent may be valid but the compiler may generate inconsistent artefacts
- the transport policy may allow something the workload policy denies
- the topology may contain an unsafe direct cross-slice edge
- the shared service may accidentally become a transit bridge
- policy and topology may disagree about what is reachable

The graph step is therefore an assurance check over the post-compilation model, not just a restatement of the original intent.

Negative controls are included to show that the verifier is not merely restating the intended configuration; unsafe or inconsistent cases must be rejected.

## Methodology foundation

Hevner et al. and Peffers et al. justify the design-science framing used in this thesis. Their role is not to provide O-RAN evidence, but to justify artefact construction, demonstration, evaluation, and communication as a valid research method.

This is the relevant methodological pattern for the repository: a bounded problem is defined, artefacts are built, those artefacts are demonstrated in a controlled setting, and the resulting behaviour is evaluated against explicit criteria.

## Methodology and related-work alignment

The repository follows a research style used in several related works, while keeping the actual contribution narrower and more bounded.

The common pattern is:

- build a proof-of-concept artefact
- validate or constrain intent before execution
- translate intent into policy or deployment artefacts
- evaluate the result in a controlled model, testbed, or prototype
- report bounded evidence rather than claiming production-wide assurance

The purpose of this comparison is not to argue that any one related work is identical to this thesis. Instead, each work supports one methodological part of the pipeline: intent representation, validation, compilation, multi-domain coordination, zero-trust enforcement, prototype evaluation, or reachability verification. The distinct contribution of this thesis is the bounded integration of these parts around one static cross-slice non-reachability property.

### Related-work alignment chart

```mermaid
flowchart TD
    DS["Design Science<br/>Build + evaluate artefacts"]
    IV["CAIF / INTPOL<br/>Intent validation + policy translation"]
    MD["NASP / ORANSlice / Limani et al.<br/>Slicing + multi-domain context"]
    IF["Dik & Berger / Groen et al. / Hung et al.<br/>Transport + interface security context"]
    SC["Scylla<br/>Intent-scoped verification"]
    ZT["OZTrust / THAALOUB<br/>Zero-trust + micro-segmentation motivation"]

    M["This repository<br/>compact slice-security intent<br/>→ compiler<br/>→ policy graph<br/>→ reachability evidence"]

    DS --> M
    IV --> M
    MD --> M
    IF --> M
    SC --> M
    ZT --> M

    classDef source fill:#eef2ff,stroke:#4f46e5,stroke-width:2px,color:#111;
    classDef mine fill:#e8f5e9,stroke:#2e7d32,stroke-width:3px,color:#111;

    class DS,IV,MD,IF,SC,ZT source;
    class M mine;
```

### Related work mapped to methodology and evidence

| Related work | Similar methodology or evidence style | What it evaluates | How it supports this thesis | Why this repository remains distinct |
| --- | --- | --- | --- | --- |
| **CAIF** | Intent-based O-RAN slicing pipeline with contract-style validation before actuation | Safer handling of O-RAN slicing intent before downstream execution | Supports the RQ1/RQ2 logic that O-RAN slicing intent benefits from structured validation before execution | This thesis uses structured security intent and static verification, whereas CAIF focuses on agentic/O-RAN slicing intent and contract-guarded actuation |
| **NASP** | Higher-level slice requests translated into coordinated multi-domain deployment artefacts | Network-slice-as-a-service orchestration across domains | Supports RQ2 by showing that slice requests need coordinated multi-domain outputs | NASP is orchestration and deployment focused, whereas this repository is security-assurance focused |
| **INTPOL** | Security intent translated into controller-level policy and checked with bounded formal methods | Intent translation, policy conflict detection, and invariant checking | Strongly supports the intent → policy → verification pattern behind RQ2 and RQ3 | INTPOL is the closest methodological analogue, but it is SDN-focused rather than O-RAN slice-security focused |
| **Scylla** | Intent-specific reachability and segmentation verification rather than one monolithic network model | Data-plane verification using intent-based slices and performance measurements | Supports RQ3 by showing that verification can be scoped around specific intents rather than requiring a full monolithic model | Scylla is a large-scale data-plane verifier, whereas this repository is a bounded local verifier tied to compiled slice-security artefacts |
| **ORANSlice** | Open-source O-RAN slicing platform with practical testbed evaluation | Programmable O-RAN slicing, xApps, E2 service models, and slicing demonstrations | Supports O-RAN slicing as a realistic implementation context | ORANSlice is a slicing platform, whereas this repository abstracts the slice model to verify one security property |
| **Limani et al.** | End-to-end 5G slice isolation proof of concept across RAN, transport, and core | Practical isolation principles across multiple 5G domains | Supports the importance of cross-domain isolation and transport-aware reasoning | Their work engineers isolation in a deployment, whereas this repository compiles security intent and verifies reachability in a small model |
| **Dik & Berger / Groen et al. / Hung et al.** | Interface and transport security analysis using implementation, emulation, or experimental evidence | Fronthaul, E2, xApp/API, encryption, and open-interface security exposure | Supports the transport-aware and open-interface threat context | These works focus on interface protection and exposure, whereas this repository focuses on slice-security intent compilation and cross-slice reachability assurance |
| **OZTrust / THAALOUB** | Zero-trust access control, micro-segmentation, and prototype-based evaluation | Least-privilege enforcement, access control, service mesh/CNI, or xApp-level security | Supports the default-deny, allowed-path, blocked-path, and O-Cloud micro-segmentation vocabulary | This repository is not a zero-trust enforcement platform; it is a slice-level static assurance pipeline |
| **Dzeparoska** | Intent-based management with intent decomposition, policy structures, and assurance/control logic | Intent formalisation, policy decomposition, and autonomic management | Supports the broader intent-management framing around the thesis pipeline | This thesis is narrower, static, and security-specific; it does not claim runtime closed-loop control as a core contribution |

## Which part of the thesis pipeline each work resembles

| Pipeline part | This repository | CAIF | NASP | INTPOL | Scylla | ORANSlice | Limani et al. | OZTrust / THAALOUB |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Intent representation | ✓ compact slice-security intent | ✓ slicing/SLA intent | ✓ higher-level slice request | ✓ security intent | △ intent-specific verification target | △ slicing use-case framing | △ isolation objective | △ access-control or zero-trust intent |
| Safety / semantic validation | ✓ schema and semantic validation | ✓ contract validation | △ orchestration-side validation | ✓ conflict/invariant checking | △ verifier-side checks | △ platform validation | △ PoC validation | △ policy validation |
| Policy compilation | ✓ deterministic compiler | △ intent-to-action translation | ✓ multi-domain artefact generation | ✓ intent-to-policy translation | — | △ slicing/control configuration | — | △ policy derivation/enforcement configuration |
| Multi-domain slice artefacts | ✓ transport + O-Cloud + O-RAN metadata | △ O-RAN actuation path | ✓ core strength | △ controller-level policies | — | ✓ practical slicing artefacts | ✓ RAN/TN/5GC isolation setup | △ multi-layer enforcement rather than slice artefacts |
| O-Cloud micro-segmentation / zero trust | ✓ representational O-Cloud micro-segmentation | — | △ domain coordination only | △ security-policy viewpoint | — | — | △ isolation motivation | ✓ core emphasis |
| Reachability or invariant verification | ✓ graph reachability checks | △ safety guardrail | — | ✓ bounded checking/invariants | ✓ strong reachability verification | — | — | △ policy/access-control verification |
| Prototype / testbed evaluation | ✓ bounded local PoC and evidence pipeline | ✓ O-RAN slicing prototype/testbed | ✓ platform/prototype | ✓ prototype and formal evaluation | ✓ experimental evaluation | ✓ open-source platform/testbed | ✓ practical PoC | ✓ prototype/performance evaluation |
| Runtime monitoring / future work | Not part of the core claim; treated as future work or optional extension | △ runtime/agentic actuation context | ✓ orchestration/runtime orientation | △ controller/runtime policy context | △ operational verification context | ✓ live slicing platform context | △ deployment context | ✓ enforcement/runtime control context |

Legend: ✓ = strong resemblance, △ = partial resemblance, — = not a major emphasis.

## Evidence style and evaluation logic

The evidence style used in this thesis is consistent with bounded systems and design-science research. Comparable systems papers often rely on bounded prototypes, emulated or testbed environments, generated artefacts, validation steps, negative or unsafe cases, performance or overhead measurements, and explicit limitation statements.

The evidence style here is model-based and bounded rather than production-operational. The repository does not try to prove deployment realism across a full O-RAN stack. Its evidence is deliberately compact:

- schema and semantic validation for a bounded slice-security intent
- deterministic compilation into exactly three coordinated representational artefacts
- a policy-and-topology graph built after compilation
- static reachability checks for required and forbidden paths
- negative controls showing that unsafe or inconsistent cases are rejected
- modest local overhead reporting with explicit limitations

This narrower evidence style is a feature of the thesis framing, not a weakness in itself. It matches the bounded claim: one reproducible static assurance workflow for one cross-slice non-reachability property in a small O-RAN-aligned proof of concept.

## What the repository proves

Within the bounded local model, the repository demonstrates that:

- a compact slice-security intent can be validated
- invalid or unsafe bounded cases can be rejected
- a deterministic compiler can emit exactly three coordinated policy artefacts
- those artefacts can be combined with topology into a reachability graph
- required paths to `shared_auth_log` are preserved
- forbidden cross-slice paths are absent
- negative-control misconfigurations are detected
- modest local proof-of-concept overhead can be reported
- controlled baselines show that neither permissive connectivity nor deny-all satisfies the balanced objective

## What the repository does not prove

The repository does not claim:

- complete O-RAN security
- production-grade network slicing
- full 3GPP or O-RAN slice lifecycle modelling
- live RIC, xApp, or rApp enforcement
- Kubernetes or container-platform enforcement
- cryptographic protection
- runtime packet delivery guarantees
- runtime drift detection
- fronthaul confidentiality
- xApp trustworthiness
- operator-grade deployment readiness
- production scalability

The claim is intentionally narrower:

> This repository demonstrates a bounded, model-based, static assurance workflow for one cross-slice non-reachability property in a small O-RAN-aligned proof of concept.

## Quick command summary

Install and run the full workflow:

```bash
make install
make run-all
```

Run individual stages:

```bash
make validate
make compile
make verify
make test
make experiments
python experiments/run_e6_controlled_baselines.py
python experiments/run_e5_repeated.py --warmups 5 --trials 30
```

Inspect evidence:

```bash
cat results/reports/verification_report.md
cat results/reports/experiment_summary.md
cat results/metrics/overhead_metrics.json
cat results/metrics/overhead_repeated.json
cat results/reports/baseline_comparison.md
```

## One-line summary

RQ1 defines the security intent, RQ2 compiles it into three coordinated policy artefacts, and RQ3 checks the compiled policy-and-topology model for required and forbidden reachability.

The comparison shows that the thesis is not isolated from the field: its individual components are supported by established patterns in intent-based management, slice orchestration, zero-trust enforcement, prototype evaluation, and reachability verification.

Similar works cover parts of the pipeline, but this thesis integrates compact slice-security intent, coordinated policy compilation, and static cross-slice reachability verification in one small O-RAN-aligned proof of concept.

This is presented as a bounded integration contribution, not as a claim that the repository replaces production O-RAN slicing, live RIC/xApp control, Kubernetes enforcement, or complete zero-trust deployment.
