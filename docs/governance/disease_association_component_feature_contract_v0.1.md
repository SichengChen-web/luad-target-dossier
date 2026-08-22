# Disease Association Component Feature Contract v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Version:** v0.1  
**Component:** `COMP_DISEASE_ASSOCIATION`  
**Component version:** `COMP_DISEASE_ASSOCIATION_V0.1`  
**Status:** Controlled-prose contract; no extractor or executable rules authorized

## 1. Purpose

This document defines the normalized structural features proposed for the future disease-association component. Features represent availability, record structure, provenance, dependency, and missingness only.

No feature evaluates association strength, confidence, importance, causality, target quality, therapeutic relevance, ranking, or suitability.

## 2. Universal feature object

Every future feature object must contain:

- stable `feature_id`;
- stable `feature_name`;
- governed data type;
- exact value from a frozen record or deterministic extraction rule;
- one feature-level `missingness_status`;
- `extraction_rule_id`;
- `extractor_version`;
- one or more record-level provenance relationships where required;
- explicit applicability and interpretation boundary.

Every provenance relationship preserves `claim_id`, `evidence_record_id`, `source_id`, `artifact_id`, and `dependency_id`. Source version, source snapshot, artifact SHA256, component version, schema version, state-rule version, and generator version must resolve through frozen manifests.

## 3. Proposed feature dictionary

These stable identifiers define component semantics. They do not authorize implementation.

| `feature_id` | `feature_name` | Data type / controlled values | State input | Structural meaning |
|---|---|---|---|---|
| `DAF_ASSESSMENT_ATTEMPTED_V0_1` | `disease_association_assessment_attempted` | Boolean | Yes | Whether the registered assessment was attempted for this entity and source snapshot |
| `DAF_QUERY_SCOPE_COMPLETE_V0_1` | `disease_association_query_scope_complete` | Boolean | Yes | Whether every required source/query scope completed without unresolved coverage |
| `DAF_RECORD_AVAILABILITY_V0_1` | `disease_association_record_availability` | `RECORDS_PRESENT`, `NO_RECORDS_RETURNED`, `NOT_QUERIED`, `UNKNOWN` | Yes | Structural availability of in-scope records |
| `DAF_RECORD_COUNT_V0_1` | `disease_association_record_count` | Non-negative integer | Yes | Number of distinct in-scope source records after identity-preserving duplicate reconciliation; audit metadata only |
| `DAF_RECORD_ROLE_SET_V0_1` | `disease_association_record_role_set` | Canonically sorted set of registered role IDs | No | Source roles represented by the frozen records |
| `DAF_RECORD_GRANULARITY_SET_V0_1` | `disease_association_record_granularity_set` | Canonically sorted subset of `SOURCE_ATOMIC`, `SOURCE_AGGREGATE`, `MIXED`, `UNKNOWN` | No | Source-native granularity represented without decomposition |
| `DAF_SOURCE_EVIDENCE_TYPE_SET_V0_1` | `disease_association_source_evidence_type_id_set` | Canonically sorted source-native string IDs | No | Uninterpreted source evidence-type identifiers present in records |
| `DAF_SOURCE_DISEASE_ID_SET_V0_1` | `disease_association_source_disease_id_set` | Canonically sorted source-native string IDs | No | Source disease identifiers present in records |
| `DAF_SOURCE_TARGET_ID_SET_V0_1` | `disease_association_source_target_id_set` | Canonically sorted source-native string IDs | No | Source target identifiers present in records |
| `DAF_DISEASE_MAPPING_STATUS_V0_1` | `disease_context_mapping_status` | `RESOLVED`, `NOT_REQUIRED`, `UNRESOLVED`, `CONFLICTING`, `UNKNOWN` | Yes | Structural status of mapping source disease identity to frozen LUAD context |
| `DAF_TARGET_MAPPING_STATUS_V0_1` | `target_identity_mapping_status` | `RESOLVED`, `NOT_REQUIRED`, `UNRESOLVED`, `CONFLICTING`, `UNKNOWN` | Yes | Structural status of mapping source target identity to immutable `EnsemblID` |
| `DAF_PROVENANCE_COMPLETE_V0_1` | `disease_association_provenance_complete` | Boolean | Yes | Whether all required record, source, artifact, rule, version, query, and mapping lineage resolves |
| `DAF_DEPENDENCY_COMPLETE_V0_1` | `disease_association_dependency_complete` | Boolean | Yes | Whether every applicable or unknown dependency relationship is explicitly represented |
| `DAF_DEPENDENCY_STATUS_SET_V0_1` | `disease_association_dependency_status_set` | Canonically sorted subset of `SAME_SOURCE`, `SHARED_DATASET`, `PARTIAL`, `UNKNOWN`, `INDEPENDENT`, `NOT_APPLICABLE` | No | Dependency relationship types present; never an independence count |
| `DAF_CONFLICT_COUNT_V0_1` | `disease_association_structural_conflict_count` | Non-negative integer | Yes | Count of registered identity, mapping, payload, role, or provenance conflicts; audit metadata only |
| `DAF_PARTIAL_CONDITION_COUNT_V0_1` | `disease_association_partial_condition_count` | Non-negative integer | Yes | Count of registered incomplete scope, role, mapping, provenance, dependency, or coverage conditions; audit metadata only |
| `DAF_RETRIEVAL_FAILURE_V0_1` | `disease_association_retrieval_failure` | Boolean | Yes | Whether a separately authorized frozen retrieval operation failed |
| `DAF_UNKNOWN_COVERAGE_V0_1` | `disease_association_unknown_coverage` | Boolean | Yes | Whether required coverage remains unresolved |
| `DAF_RECORDS_MISSINGNESS_V0_1` | `disease_association_records_missingness_status` | `OBSERVED`, `NOT_FOUND`, `NOT_QUERIED`, `NOT_APPLICABLE`, `UNKNOWN` | Yes | Controlled missingness for the association-record collection |

Record counts, conflict counts, and partial-condition counts are reconciliation inputs for deterministic state predicates. They must not be presented as evidence quantity, strength, quality, confidence, or target evaluation.

## 4. Prohibited normalized fields

The v0.1 normalized component must not include:

- source or cross-source association scores;
- strength categories;
- confidence values or confidence categories;
- publication, record, or evidence counts interpreted as support;
- target importance or disease importance;
- causal direction or causal status;
- target quality, ranking, priority, or selection;
- therapeutic relevance, direction, or recommendation;
- free-text biological interpretation.

If a future source record contains such a source-native field, the raw value may remain in the immutable raw record for provenance. It must not become a normalized v0.1 feature without a new reviewed component contract.

## 5. Feature-level missingness

In addition to the collection-level feature `disease_association_records_missingness_status`, every feature object carries its own `missingness_status`:

| Status | Component-specific use |
|---|---|
| `OBSERVED` | The governed feature value is present and traceable |
| `NOT_FOUND` | The registered source operation completed and the mapped structural item was not returned |
| `NOT_QUERIED` | The source operation needed for the feature was not attempted |
| `NOT_APPLICABLE` | A deterministic applicability rule excludes the feature for this record/entity |
| `UNKNOWN` | Retrieval, parsing, mapping, query coverage, or provenance status cannot be resolved |

Empty strings, blank lists, zero, and false must not silently substitute for missingness. Each feature contract must define whether an empty collection is a valid observed value or a controlled missingness condition.

## 6. Controlled-prose component-state predicates

These predicates constrain future executable rules. They are not executable in v0.1 and cannot be used for materialization until assigned a reviewed `state_rule_version`.

### 6.1 `CONFLICTING`

Match when `disease_association_structural_conflict_count > 0` or either mapping status is `CONFLICTING`.

Conflict is structural only: incompatible target identity, disease-context mapping, record identity/payload, role assignment, or required provenance. It is not a judgement about biological disagreement.

### 6.2 `OBSERVED`

Match when all are true:

- assessment attempted;
- query scope complete;
- record availability is `RECORDS_PRESENT`;
- record count is greater than zero;
- record-collection missingness is `OBSERVED`;
- target and disease mapping statuses are `RESOLVED` or validly `NOT_REQUIRED`;
- provenance complete;
- dependency complete;
- partial-condition count is zero;
- retrieval failure is false;
- unknown coverage is false.

`OBSERVED` means structurally complete records are represented. It does not mean that the target is associated strongly, causally, or therapeutically with disease.

### 6.3 `MISSING`

Match when all are true:

- assessment attempted;
- query scope complete;
- record availability is `NO_RECORDS_RETURNED`;
- record count is zero;
- record-collection missingness is `NOT_FOUND`;
- target and disease query/mapping context is resolved or validly `NOT_REQUIRED`;
- query provenance is complete;
- retrieval failure is false;
- unknown coverage is false.

`MISSING` means no qualifying records were returned within the frozen scope. It is not negative evidence and does not establish absence of disease involvement.

### 6.4 `PARTIAL`

Match when assessment was attempted and at least one registered incomplete condition exists, including:

- query scope incomplete;
- records present with incomplete required mapping, provenance, dependency, role, or coverage;
- retrieval failure;
- unknown coverage;
- unresolved mapping;
- partial-condition count greater than zero.

Precedence applies after all predicates are evaluated, so a registered conflict remains `CONFLICTING` rather than `PARTIAL`.

### 6.5 `NOT_QUERIED`

Match when all are true:

- assessment attempted is false;
- record availability is `NOT_QUERIED`;
- record count is zero;
- record-collection missingness is `NOT_QUERIED`.

`NOT_QUERIED` is an acquisition-status observation, not a biological statement.

## 7. State precedence

The future executable registry must preserve:

`CONFLICTING > OBSERVED > MISSING > PARTIAL > NOT_QUERIED`

Precedence resolves predicate overlap only. It must not be displayed as comparative value, maturity, evidence strength, or target quality.

## 8. Provenance cardinality

Each feature must identify which source roles can support it and the required relationship cardinality. Before extractor implementation, a future machine-readable dictionary must freeze those role-to-feature mappings.

Minimum logical provenance includes:

- the query-scope record for assessment and coverage features;
- every association record contributing to availability and structural-set features;
- mapping records for disease and target mapping features;
- dependency assertions for dependency features;
- the raw evidence artifact and source snapshot for all derived values.

No feature may use a record count as a substitute for its individual record relationships.

## 9. Dependency rules

1. Every association record retains a dependency reference or controlled sentinel.
2. Records from one source aggregate remain dependent.
3. Records derived from the same underlying dataset remain `SHARED_DATASET / DEPENDENT`.
4. Partial overlap remains `PARTIAL / PARTIALLY_DEPENDENT`.
5. Unresolved relationships remain `UNKNOWN / UNKNOWN`.
6. `NOT_APPLICABLE` does not become independent.
7. `INDEPENDENT` requires affirmative source-traceable justification.
8. Dependency-status sets are structural labels, not corroboration categories.

## 10. Determinism contract

Feature values must be produced only from:

`frozen source records + frozen mapping artifacts + versioned extraction rules + controlled vocabularies`

Sorting, duplicate reconciliation, missingness, and set serialization rules must be explicit before implementation. No randomness, wall-clock value, mutable network response, manual runtime edit, or AI/LLM judgement may affect a feature.

## 11. Feature-contract blockers

Before implementation, review must freeze:

- exact machine-readable data types and JSON/CSV serialization;
- feature order and cardinality;
- role-to-feature provenance cardinalities;
- empty-set versus missingness behavior for every set-valued feature;
- disease and target mapping status rules;
- duplicate-record reconciliation;
- conflict and partial-condition definitions;
- source-specific granularity and evidence-type vocabularies;
- executable state predicates and fixtures;
- schema, extractor, rule, source-snapshot, and generator versions.

## 12. Feature-contract checklist

- [x] Only availability, structure, provenance, dependency, and missingness features are proposed.
- [x] Every feature has a stable ID, name, type, and structural meaning.
- [x] State inputs are explicit.
- [x] Five component states and five missingness values are distinct.
- [x] Controlled-prose predicates and precedence are documented.
- [x] Association strength, confidence, importance, ranking, causality, and therapeutic interpretation are prohibited.
- [ ] Machine-readable schema and extraction rules are reviewed and frozen.
- [ ] Executable state registry and fixtures are reviewed and frozen.
- [ ] A source snapshot exists under separate authorization.

## 13. Related documents

- [Disease Association Component Registration v0.1](disease_association_component_registration_v0.1.md)
- [Disease Association Component Scope v0.1](disease_association_component_scope_v0.1.md)
- [Disease Association Component Validation Plan v0.1](disease_association_component_validation_plan_v0.1.md)
- [Component Validation Requirements v0.1](component_validation_requirements_v0.1.md)

