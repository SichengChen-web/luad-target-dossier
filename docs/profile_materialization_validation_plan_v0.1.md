# Profile Materialization Validation Plan v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Task:** #023 — Profile Materialization Validation Framework  
**Version:** v0.1  
**Date:** 21 August 2026  
**Status:** Working validation specification

## Scientific question

The question is correctly formulated as a representation-fidelity problem:

> Can the Task #020–#022 architecture represent diverse evidence situations while retaining entity identity, evidence lineage, source provenance, dependency, missingness, uncertainty, and component-state meaning?

This is not a question about which targets are preferable. A validation fixture is selected because its frozen data structure tests a boundary condition, not because of its gene symbol, biological role, disease reputation, or therapeutic potential.

## Scope

Task #023 validates:

- immutable EnsemblID propagation;
- claim→record→source→artifact reconstruction;
- exact reuse of atomic record IDs;
- dependency-edge reconstruction;
- record-level missingness and uncertainty reconstruction;
- all five Task #021 component states;
- deterministic test-fixture selection and canonical serialization; and
- explicit limitations of the current architecture.

It does not generate final target profiles. The component-case output is a table of validation assertions and rule references, not a materialized 28-field target profile.

## Frozen inputs

The validation run hash-pins exactly:

- `outputs/integrated_registry/integrated_target_registry.csv`;
- `outputs/evidence_claim_architecture/evidence_claim_registry.csv`;
- `outputs/evidence_claim_architecture/evidence_record_registry.csv`;
- `outputs/evidence_claim_architecture/source_entity_registry.csv`;
- `outputs/evidence_claim_architecture/evidence_dependency_graph.csv`;
- `outputs/profile_materialization/materialization_schema.csv`;
- `outputs/profile_materialization/component_state_resolution_registry.csv`; and
- `outputs/target_universe_governance/target_universe_schema.csv`.

The 139.8 MB evidence-record registry remains an external governed Class D artifact and is not copied into Task #023 outputs.

## Validation cohort design

The cohort contains ten unique test fixtures assigned without replacement:

| Category | Number | Frozen eligibility criterion |
| --- | ---: | --- |
| Conflict boundary | 1 | Transcript claim carries `CONFLICTING_RECORDS` uncertainty and resolves to the conflict rule |
| Dependency heavy | 2 | Entity has the maximum dependency-edge count in the frozen graph |
| Evidence rich | 2 | At least four evidence domains have positive supporting-record counts |
| Evidence poor | 2 | At most one evidence domain has a positive supporting-record count |
| Missing boundary | 1 | At least one component resolves `MISSING` |
| Not-queried boundary | 1 | At least one current atomic record is explicitly `NOT_QUERIED` |
| Partial boundary | 1 | At least one component resolves `PARTIAL` |

Category order is frozen as shown. Within each eligible set, entities are ordered by:

```text
SHA256(PROFILE_MATERIALIZATION_VALIDATION_V0.1 | category | EnsemblID)
```

The first still-unassigned entities are taken. This prevents manual choice and makes reruns independent of CSV traversal order. Symbols and gene names are copied only after selection as display annotations.

This procedure is validation-fixture sampling. It is not therapeutic candidate selection and conveys no scientific preference.

## Validation model

### 1. Identity preservation

For every fixture:

- the integrated-registry EnsemblID must be unique;
- every claim must carry the same EnsemblID;
- every atomic record must resolve through its claim to that EnsemblID;
- every `raw_value_reference` must point to that same EnsemblID in the frozen integrated registry; and
- no Symbol-based join or fallback is permitted.

### 2. Evidence lineage preservation

Each validation component records exact claim IDs, evidence-record IDs, source IDs, source versions, input artifact paths, and input SHA256 hashes. The harness verifies every link against the frozen registries.

No similar-looking record is merged. Repeated use of one record in more than one component retains the same record ID.

### 3. Dependency preservation

For every dependency edge induced by the selected entities, both endpoints must:

- exist exactly once in the atomic evidence registry;
- resolve to the same immutable entity;
- retain their source and claim IDs; and
- retain the original dependency ID, relationship, qualitative level, and review status.

Dependency is not converted into a numerical penalty or vote. Absence of an edge is not interpreted as independence.

### 4. Missingness and uncertainty preservation

Record-level mappings are emitted as explicit `record_id=status` pairs in validation outputs. This checks that `OBSERVED`, `NOT_FOUND`, and `NOT_QUERIED` remain distinguishable and that source uncertainty is not discarded.

Component states retain separate meanings:

- `OBSERVED`: the component-specific qualifying condition is represented;
- `PARTIAL`: some assessment exists but required evidence, linkage, coverage, or provenance is incomplete;
- `MISSING`: a completed frozen scope found no qualifying record;
- `NOT_QUERIED`: no valid acquisition/query covered the component; and
- `CONFLICTING`: traceable incompatible records exist under a prespecified boundary.

Missing is never converted into negative biological evidence. Not queried is never converted into missing.

### 5. Component-state rule addressability

The validation harness maps controlled Task #014 claim/record states to an expected Task #021 component state, then verifies that exactly one frozen component/state rule exists at the required precedence.

This tests whether the architecture can represent the case. It does not claim that the English-language `deterministic_predicate` fields are executable code. Their conversion into a fully machine-executable, versioned rule configuration remains a release requirement for a future materializer.

### 6. Determinism

The run freezes:

- all eight input hashes;
- the Task #022 base commit;
- validation version;
- fixture category order and sizes;
- hash-based tie-breaking;
- component order;
- column order; and
- canonical UTF-8/LF CSV serialization.

All output content, including session metadata, uses the frozen base-commit timestamp rather than wall-clock time. The builder constructs every output twice in memory and requires byte identity before writing. External review additionally can rerun the script and compare SHA256 hashes.

## Interpretation boundaries

Passing validation means that the frozen architecture can preserve and reconstruct evidence meaning for the chosen structural cases. It does not mean:

- the evidence is scientifically strong;
- the entity is causal or actionable;
- the profile is complete;
- missing evidence is unfavorable;
- dependent records are independent confirmations;
- any drug is effective or safe;
- a target should be selected; or
- a target has a therapeutic direction.

## Known architecture limitations tested

### Controlled prose predicates

Task #021 supplies prespecified predicates for all 55 component/state combinations, but they are controlled prose. Task #023 can validate unique rule addressability and meaning preservation; it cannot prove automatic execution of natural language. A future release builder should use executable reviewed predicates or immutable predicate IDs linked to tested code.

### Relational reconstruction

The Task #020 profile schema carries lists of record IDs, missingness categories, dependency relationships, and dependency levels. It does not inline every record→status or record-pair→dependency mapping. Lossless meaning therefore depends on the frozen evidence-record and dependency-graph registries remaining available by artifact hash.

Task #023 validates this relational reconstruction explicitly. If standalone profiles become a requirement, a later schema version should add structured record-status and dependency-edge references rather than silently changing v0.1.

### Evidence domains not yet acquired

The frozen evidence records contain transcriptomic, disease-association, pharmacology-annotation, tractability, and safety summaries. Dedicated genetics, functional dependency, compound-assay/mechanism, clinical trial, and intervention–target–LUAD linkage evidence has not been acquired. `NOT_QUERIED` preserves that boundary and must not be interpreted as negative evidence.

## Release criteria

Task #023 passes with documented representation limitations only if:

- all frozen hashes match before and after generation;
- all 29,606 integrated entities, 148,030 claims, 207,242 records, six sources, and 77,202 dependency edges pass global integrity checks;
- the ten fixtures satisfy the frozen category plan;
- all 110 component cases resolve to one addressable Task #021 state rule;
- all five states occur in the validation results;
- all selected dependency edges and record-level missingness mappings reconstruct exactly;
- no Symbol join or forbidden assessment field is introduced;
- no final profile artifact is created; and
- repeated output construction is byte-identical.

Any data-integrity failure stops output release. Scientific limitations are reported as limitations rather than hidden or converted into target judgments.
