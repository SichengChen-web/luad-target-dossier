# Disease Association Component Scope v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Version:** v0.1  
**Component:** `COMP_DISEASE_ASSOCIATION`  
**Status:** Proposal-stage scope; no retrieval authorization

## 1. Purpose

This document defines the scientific scope and interpretation boundary for the proposed disease-association component. It constrains what future records may enter the component and what the representation may describe.

It does not select a source, define a source query, retrieve evidence, or authorize materialization.

## 2. Bounded observation question

**For an immutable `EnsemblID` and a prespecified LUAD disease context, what governed disease-association records, if any, are available in the frozen component source snapshot, and what record, mapping, provenance, dependency, missingness, and structural-conflict conditions do those records carry?**

The unit of scientific representation is record availability and structure, not a judgement about the gene or disease.

## 3. In scope

The component may represent:

- query-scope and query-completion records;
- source-native target–disease association records;
- source target-identity mapping to immutable `EnsemblID`;
- source disease-identity mapping to the frozen LUAD context;
- source-native record identifiers and record granularity;
- source-native evidence-type identifiers as uninterpreted structural labels;
- record-level provenance and artifact lineage;
- same-source, shared-dataset, partial, unknown, independent, and not-applicable dependency relationships;
- feature-level controlled missingness;
- structural conflicts in record identity, mapping, provenance, or incompatible duplicate payloads;
- explicit limitations and unresolved coverage.

## 4. Out of scope

The component must not represent or infer:

- disease-driver status;
- causal effect or causal direction;
- target importance or biological importance;
- therapeutic relevance or target suitability;
- pharmacology, tractability, safety, clinical development, or therapeutic direction;
- source-native association metrics as normalized strength, confidence, quality, priority, or ranking features;
- a combined value across records, sources, evidence types, or components;
- a therapeutic recommendation or candidate selection.

Source-native fields outside the normalized component contract may remain in immutable raw records for provenance. Their preservation does not authorize interpretation or feature extraction.

## 5. Disease-context boundary

The project disease is lung adenocarcinoma, but this registration does not guess a disease ontology identifier or hierarchy rule.

A future reviewed source contract must define:

- exact disease-context identifier and ontology version;
- whether exact-match records only are included;
- whether ontology descendants, ancestors, broader lung cancer terms, histologic subtypes, or mixed cohorts are excluded or separately labelled;
- how source disease identifiers are mapped;
- how ambiguous, obsolete, multiple, or conflicting mappings are represented;
- whether mapping is source-native or produced by a frozen mapping artifact.

Until these decisions are frozen, no record can be declared in-scope for retrieval.

## 6. Target-identity boundary

The only component entity key is exact immutable `EnsemblID`.

If a future source uses another target identifier:

1. the source identifier remains preserved;
2. mapping must use a frozen identifier artifact and deterministic rule;
3. one-to-many, many-to-one, ambiguous, obsolete, or unresolved mappings remain explicit;
4. gene symbols must not be used as join keys or manual inference;
5. a mapping conflict contributes only to structural conflict representation.

Mapping success does not imply disease association validity or target relevance.

## 7. Evidence record boundary

### 7.1 Source-native record preservation

One evidence record is one immutable source-returned association object with a stable source identity or a deterministic record identity derived from the frozen payload.

The raw record must retain:

- source target identity;
- source disease identity;
- source record identity;
- source version and snapshot;
- source-native evidence-type label where present;
- complete raw payload or immutable artifact reference;
- query and retrieval provenance when retrieval is later authorized.

### 7.2 Atomic and aggregate records

Record granularity must be labelled as:

- `SOURCE_ATOMIC`;
- `SOURCE_AGGREGATE`;
- `MIXED`;
- `UNKNOWN`.

A `SOURCE_AGGREGATE` remains one record. Internal counts or categories exposed by that aggregate must not be expanded into independent records unless the source provides stable atomic records and a reviewed extraction contract permits them.

### 7.3 Duplicate and revised records

Exact duplicate records must retain source lineage without creating additional apparent observations. Records with the same source identity but incompatible payloads or versions must be represented as a structural conflict or version boundary, not silently merged.

## 8. Source-role boundary

The component recognizes only these generic roles:

- `ROLE_QUERY_SCOPE_RECORD`;
- `ROLE_DISEASE_ASSOCIATION_RECORD`;
- `ROLE_DISEASE_CONTEXT_MAPPING`;
- `ROLE_TARGET_IDENTITY_MAPPING`;
- `ROLE_DEPENDENCY_ASSERTION`.

No provider is registered by naming these roles. A future source proposal must demonstrate how its records populate the roles and how missing roles affect component state.

## 9. Structural conflict boundary

`CONFLICTING` may represent only a deterministic structural conflict such as:

- incompatible target mappings for the same source entity;
- incompatible disease-context mappings for the same source disease identity;
- the same source record identity resolving to incompatible immutable payloads within one snapshot;
- irreconcilable source record granularity or role assignment;
- inconsistent provenance identifiers that cannot be reconciled under a registered rule.

The component must not create a biological conflict based on differing publication conclusions, association magnitudes, or researcher interpretation unless a future reviewed evidence-type contract defines a purely structural representation and preserves the original claims.

## 10. Dependency boundary

Records may share a source, dataset, cohort, upstream record, literature claim, or aggregate. Dependency must be represented before any cross-record summary is produced.

Different sources are not automatically independent. `UNKNOWN` dependence remains unknown, and `NOT_APPLICABLE` is not affirmative independence. The component must not count dependent records as independent evidence.

## 11. Missingness boundary

Feature-level missingness remains:

- `OBSERVED`;
- `NOT_FOUND`;
- `NOT_QUERIED`;
- `NOT_APPLICABLE`;
- `UNKNOWN`.

No missingness value is a biological conclusion. In particular, a completed query returning no in-scope records can support structural component state `MISSING`, but it cannot establish absence of disease involvement.

## 12. Interpretation boundary

The component can describe:

- that a governed source record exists or was not returned within a frozen scope;
- how it is identified and structured;
- how its target and disease identities map;
- whether its provenance and dependency structure resolve;
- which missingness, conflict, coverage, and limitation conditions remain.

The component cannot establish:

- disease causality or driver status;
- target importance;
- biological validity;
- therapeutic relevance, actionability, or suitability;
- efficacy, safety, or clinical benefit;
- comparative target quality;
- a score, ranking, confidence metric, priority, recommendation, or selection.

## 13. Scope-change policy

A change to the bounded question, disease-context semantics, evidence record unit, accepted record types, source roles, mapping rules, feature meanings, dependency contract, state meanings, or interpretation boundary requires a new `component_version`.

A new source snapshot alone does not change component semantics, but it requires a new `source_snapshot_version` and containing profile `evidence_snapshot_version`.

## 14. Scope checklist

- [x] One observation-only question is defined.
- [x] Target identity is exact `EnsemblID`.
- [x] Disease-context identity is explicitly unresolved rather than guessed.
- [x] Record unit and granularity boundaries are defined.
- [x] Generic source roles are defined without registering a provider.
- [x] Structural conflict, dependency, missingness, and non-claim boundaries are explicit.
- [x] Scoring, ranking, confidence, importance, causal, and therapeutic interpretations are prohibited.
- [ ] Exact disease ontology, sources, and query scope are reviewed and frozen.

## 15. Related documents

- [Disease Association Component Registration v0.1](disease_association_component_registration_v0.1.md)
- [Disease Association Component Feature Contract v0.1](disease_association_component_feature_contract_v0.1.md)
- [Disease Association Component Validation Plan v0.1](disease_association_component_validation_plan_v0.1.md)

