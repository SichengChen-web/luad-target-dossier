# Disease Association Component Registration v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Registration version:** v0.1  
**Component lifecycle stage:** `PROPOSAL`  
**Status:** Frozen registration specification; not authorized for retrieval or materialization

## 1. Purpose

This document registers the proposal-stage contract for a future disease-association evidence component. The component will represent available disease-association records and their provenance for an immutable target entity and a prespecified LUAD disease context.

The component represents observations only. It does not determine disease drivers, target importance, therapeutic relevance, target suitability, causality, efficacy, or therapeutic direction.

Registration does not authorize retrieval. This task performs no external query, download, evidence extraction, profile materialization, target scoring, or ranking.

## 2. Component identity

| Identity field | Registered value | Status |
|---|---|---|
| `component_id` | `COMP_DISEASE_ASSOCIATION` | Frozen |
| `component_version` | `COMP_DISEASE_ASSOCIATION_V0.1` | Frozen |
| Serialized compatibility field | `component_definition_version = COMP_DISEASE_ASSOCIATION_V0.1` | Frozen binding |
| `schema_version` | `UNASSIGNED_PENDING_SCHEMA_REGISTRATION` | Materialization blocker |
| `source_snapshot_version` | `UNASSIGNED_NO_RETRIEVAL_AUTHORIZED` | Materialization blocker |
| `extractor_version` | `UNASSIGNED_NO_EXTRACTOR_IMPLEMENTED` | Materialization blocker |
| `state_rule_version` | `UNASSIGNED_PENDING_EXECUTABLE_RULE_REVIEW` | Materialization blocker |
| `generator_version` | `UNASSIGNED_NO_GENERATOR_IMPLEMENTED` | Materialization blocker |

`component_version` is the Task #032A governance-interface term for the existing profile field `component_definition_version`. They are one semantic version axis and must always be equal.

The unassigned values are explicit governance statuses, not runtime values. They prevent validation or materialization from proceeding before a separately authorized task freezes each contract.

## 3. Bounded observation question

**For an immutable `EnsemblID` and a prespecified LUAD disease context, what governed disease-association records, if any, are available in the frozen component source snapshot, and what record, mapping, provenance, dependency, missingness, and structural-conflict conditions do those records carry?**

This question concerns record availability and structure. It does not ask whether the gene causes LUAD, is important in LUAD, is actionable, is therapeutically relevant, or should be selected.

## 4. Immutable entity and disease-context binding

### 4.1 Target identity

The materialized component instance must bind only through exact immutable `EnsemblID`. Gene symbols may be displayed but must not serve as join keys, mapping fallbacks, or silent identity repair.

### 4.2 Disease context

Before retrieval can be proposed, a future reviewed registration amendment must freeze:

- `disease_context_id`;
- `disease_context_ontology`;
- `disease_context_ontology_version`;
- accepted child/parent traversal behavior, if any;
- `disease_context_mapping_rule_version`;
- inclusion and exclusion boundaries for lung adenocarcinoma records.

No disease ontology identifier is guessed in this registration. Until those fields are frozen, the disease-context binding is unresolved and retrieval remains prohibited.

## 5. Evidence record unit

The evidence record unit is one immutable source-returned disease-association record connecting:

- one source target entity;
- one source disease entity;
- one source evidence-record identity;
- one source snapshot and source version;
- the source-native record payload and provenance.

If a future source exposes only an aggregate record, that object remains one `SOURCE_AGGREGATE` record. It must not be decomposed into apparent independent records. If a source exposes atomic records, each source-native atomic identity remains separate.

Source-native numeric association metrics, if present, remain in the raw evidence record and lineage. They are not normalized as component v0.1 features, state inputs, weights, confidence measures, or target-evaluation fields.

## 6. Registered source roles

This registration defines roles, not data providers.

| Source role | Purpose | Requirement |
|---|---|---|
| `ROLE_QUERY_SCOPE_RECORD` | Preserves whether the registered target/disease query was attempted, its scope, completion status, and frozen query provenance | Required for every entity, including `NOT_QUERIED` |
| `ROLE_DISEASE_ASSOCIATION_RECORD` | Preserves one source-native disease-association record | Required when association records are returned |
| `ROLE_DISEASE_CONTEXT_MAPPING` | Preserves mapping from source disease identity to the frozen LUAD disease context | Required unless the source identity exactly equals the frozen context under a documented `NOT_REQUIRED` rule |
| `ROLE_TARGET_IDENTITY_MAPPING` | Preserves mapping from source target identity to immutable `EnsemblID` | Required unless the source natively returns the exact immutable `EnsemblID` under a documented `NOT_REQUIRED` rule |
| `ROLE_DEPENDENCY_ASSERTION` | Preserves same-source, shared-dataset, partial, unknown, independent, or not-applicable dependency status | Required whenever dependency classification is applicable or unresolved |

A future source contract must map each source object to these roles deterministically. Registration of roles does not register or authorize an external source.

## 7. Feature contract reference

The normative feature contract is [Disease Association Component Feature Contract v0.1](disease_association_component_feature_contract_v0.1.md).

Only the following feature categories are allowed:

- availability features;
- record-structure features;
- provenance features;
- dependency and missingness features required for structural representation.

Forbidden feature categories include:

- association strength or evidence strength;
- confidence or confidence metrics;
- target or disease importance;
- ranking, priority, or target quality;
- causal interpretation;
- therapeutic relevance, suitability, or recommendation.

## 8. Shared component states

The component must use exactly:

- `OBSERVED`;
- `PARTIAL`;
- `CONFLICTING`;
- `MISSING`;
- `NOT_QUERIED`.

The frozen precedence is:

`CONFLICTING > OBSERVED > MISSING > PARTIAL > NOT_QUERIED`

States describe structural record conditions. They are not an ordinal scale and do not evaluate a target.

Controlled-prose predicates are specified in the feature contract. Before implementation, they must be converted into an executable, versioned rule registry with fixtures and independent review. Runtime manual or AI/LLM state assignment is prohibited.

## 9. Feature missingness

Every feature must preserve exactly one of:

- `OBSERVED`;
- `NOT_FOUND`;
- `NOT_QUERIED`;
- `NOT_APPLICABLE`;
- `UNKNOWN`.

Missingness is not evidence direction. `NOT_FOUND` is not negative evidence, `NOT_QUERIED` is not missing biology, `NOT_APPLICABLE` is not absence, and `UNKNOWN` must not be silently repaired.

## 10. Provenance contract

Every feature-to-record relationship must preserve:

- `feature_id`;
- `claim_id`;
- `evidence_record_id`;
- `source_id`;
- `artifact_id`;
- `dependency_id` or a controlled sentinel;
- `extraction_rule_id`;
- `extractor_version`.

The release or source manifest must resolve source version, source snapshot, artifact size, artifact SHA256, retrieval/query provenance, component version, schema version, state-rule version, and generator version.

The relationship key remains `(feature_id, evidence_record_id)`. Multiple records linked to one feature remain separate lineage relationships and are not independent votes.

## 11. Dependency contract

The component adopts Task #032A dependency terminology:

- relationship types: `SAME_SOURCE`, `SHARED_DATASET`, `PARTIAL`, `UNKNOWN`, `INDEPENDENT`, `NOT_APPLICABLE`;
- dependency levels: `DEPENDENT`, `PARTIALLY_DEPENDENT`, `UNKNOWN`, `INDEPENDENT`, `NOT_APPLICABLE`.

Records from the same source response, aggregate, dataset, or upstream evidence object must retain the appropriate dependency relationship. Cross-source records must not be assumed independent merely because their source IDs differ.

`INDEPENDENT` requires affirmative, source-traceable justification. `NOT_APPLICABLE` does not mean independent. Unknown dependency must remain `UNKNOWN`.

## 12. Component lifecycle disposition

| Stage | Current disposition | Gate to advance |
|---|---|---|
| `PROPOSAL` | Current | Registration documentation reviewed for scope and compatibility |
| `REVIEW` | Not entered | Scientific and technical reviewers assess disease context, sources, record unit, features, dependencies, missingness, and non-claims |
| `VALIDATION` | Not authorized | Schema, source snapshot, extractor, executable rules, generator, and deterministic fixtures frozen |
| `MATERIALIZATION` | Not authorized | All validation gates pass and a scoped human governance authorization is recorded |

Component lifecycle does not promote a Target Evidence Profile release lifecycle state.

## 13. Interpretation boundary

The future component may describe:

- whether a governed query was attempted;
- whether source records were returned;
- how returned records are structured;
- how target and disease identities map;
- record-level provenance;
- dependency, missingness, conflict, and limitation conditions.

It cannot establish:

- that a target is a disease driver;
- biological importance or causal involvement;
- therapeutic relevance, tractability, efficacy, or safety;
- target suitability, priority, rank, or quality;
- a therapeutic recommendation.

## 14. Registration blockers and unresolved decisions

The following must remain unresolved until separately reviewed:

- exact LUAD disease ontology identity and mapping rules;
- permitted external source identities and versions;
- source query and coverage semantics;
- treatment of source aggregate versus atomic records for each source;
- source-native evidence-type identifiers and normalization vocabulary;
- dependency classification using source-specific lineage;
- executable state rules and fixtures;
- machine-readable component schema;
- extractor and generator implementations;
- source snapshot and storage policy.

These blockers are deliberate. Resolving them without source inspection and review would invent scientific or provenance decisions.

## 15. Registration checklist

- [x] Stable component identity is defined.
- [x] One bounded observation question is defined.
- [x] Evidence record unit and generic source roles are defined.
- [x] Provenance, dependency, missingness, and state interfaces are defined.
- [x] Interpretation boundaries and prohibited outputs are explicit.
- [x] Compatibility with Task #032A is documented.
- [ ] Disease context and source contracts are frozen.
- [ ] Executable schemas, extraction rules, and state rules exist.
- [ ] Validation fixtures pass.
- [ ] Retrieval is separately authorized.
- [ ] Materialization is separately authorized.

## 16. Related documents

- [Disease Association Component Scope v0.1](disease_association_component_scope_v0.1.md)
- [Disease Association Component Feature Contract v0.1](disease_association_component_feature_contract_v0.1.md)
- [Disease Association Component Validation Plan v0.1](disease_association_component_validation_plan_v0.1.md)
- [Evidence Component Interface Specification v0.1](evidence_component_interface_specification_v0.1.md)

