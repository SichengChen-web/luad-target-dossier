# Component Registration Policy v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Version:** v0.1  
**Status:** Frozen governance specification

## 1. Purpose

This policy governs how an evidence component moves from a documented proposal to an authorized materialization interface. Registration controls meanings and reproducibility; it is not approval of a target, evidence source, or therapeutic claim.

No component registration may itself retrieve external evidence, generate a target profile, or introduce scoring, ranking, confidence metrics, target quality, therapeutic recommendations, or runtime AI decisions.

## 2. Registration object

Every proposal must create a version-controlled registration record containing the following sections.

### 2.1 Identity

- `component_id`;
- `component_version`, bound exactly to profile `component_definition_version`;
- `schema_version`;
- `source_snapshot_version`;
- `generator_version`;
- `state_rule_version`;
- `extractor_version`.

### 2.2 Scientific scope

- bounded observation question;
- evidence domain and unit of observation;
- permitted evidence-record types;
- required and optional source roles;
- inclusion, exclusion, and applicability rules;
- what the component can describe;
- what it cannot establish;
- known limitations and uncertainty boundaries.

### 2.3 Data contract

- immutable `EnsemblID` binding;
- feature dictionary and data types;
- accepted controlled vocabularies;
- source-record cardinalities;
- feature-level missingness rules;
- component-state predicates and frozen precedence;
- provenance relationship schema;
- dependency relationship schema;
- artifact and hash requirements.

### 2.4 Validation and governance

- deterministic generator contract;
- state and missingness fixtures;
- provenance and dependency fixtures;
- identity and schema checks;
- interpretation-boundary checks;
- technical reviewer status;
- scientific reviewer status;
- authorized materialization scope;
- change, correction, and withdrawal policy.

## 3. Component lifecycle

Component lifecycle is separate from Target Evidence Profile release lifecycle. Component stage does not evaluate any gene and does not automatically advance a profile release from `PILOT_VALIDATION_ONLY`, `INTERNAL_VALIDATION`, `SCIENTIFIC_REVIEWED`, or `PUBLIC_RELEASE`.

### 3.1 `PROPOSAL`

Purpose: define the intended observation question and interface before implementation.

Required outcomes:

- stable draft `component_id`;
- bounded scope and explicit non-claims;
- proposed version axes;
- proposed feature, provenance, dependency, and missingness contracts;
- identified scientific and technical reviewers;
- documented unresolved decisions.

Prohibited at this stage:

- evidence retrieval under the proposed interface;
- feature extraction;
- state assignment;
- profile materialization.

### 3.2 `REVIEW`

Purpose: review whether the proposal preserves evidence meaning and fits the governed profile ontology.

Review must cover:

- identity and version boundaries;
- bounded scientific question;
- observation-only interpretation boundary;
- source-role and evidence-type definitions;
- missingness distinctions;
- dependency semantics and independence claims;
- provenance completeness;
- executable-state feasibility;
- foreseeable source bias and coverage limitations.

Allowed dispositions are:

- `APPROVED_FOR_VALIDATION`;
- `CHANGES_REQUIRED`;
- `REJECTED_WITH_RATIONALE`.

Independent scientific-review status must remain explicit. Approval for validation does not imply completion of the review required for a `SCIENTIFIC_REVIEWED` or `PUBLIC_RELEASE` profile lifecycle state.

### 3.3 `VALIDATION`

Purpose: test a deterministic implementation against the approved registration without treating validation artifacts as scientific conclusions.

Required outcomes:

- exact schema validation;
- fixtures for all five component states;
- fixtures for all feature-missingness values;
- provenance and dependency reconciliation;
- forbidden-field validation;
- byte-identical regeneration;
- no unresolved identity or lineage failures;
- validation report and artifact hashes.

Validation-only pilot or local-candidate materialization may occur solely to test the interface when its profile release is explicitly labelled accordingly. Pending scientific-review status must be propagated and blocks lifecycle destinations requiring completed scientific review.

### 3.4 `MATERIALIZATION`

Purpose: authorize deterministic component generation for a declared profile universe, source snapshot, and profile-release lifecycle destination.

Before authorization, the registration must record:

- exact component, schema, source-snapshot, extractor, rule, and generator versions;
- frozen input manifest and hashes;
- approved universe and canonical order;
- validation outcome;
- reviewer status sufficient for the intended profile lifecycle destination;
- artifact storage and provenance strategy;
- limitations carried into profiles and evidence landscapes.

Materialization authorization is scoped. It does not authorize a new source snapshot, a new universe, a new component version, or a higher profile lifecycle state.

## 4. Registration decision boundaries

### 4.1 Registration does not authorize retrieval

A component may name the source roles and required source contract needed for future work, but registration does not permit external queries. A separate authorized task must define retrieval scope, source version, licensing, query provenance, snapshot freezing, and network policy.

### 4.2 Registration does not authorize interpretation

Registration approval confirms that the component can represent observations safely. It does not confirm biological validity, therapeutic relevance, evidence strength, target quality, or suitability for target selection.

### 4.3 Registration does not authorize cross-component aggregation

Components remain separate modules. A registration must not add, average, weight, vote, or otherwise aggregate component states, feature availability, record counts, or completeness into an evaluative field.

## 5. Identifier assignment and immutability

1. `component_id` is assigned once and never reused for a different bounded question.
2. Material semantic changes require a new `component_version`.
3. A superseding registration references its predecessor and states the governed reason for change.
4. Frozen registrations and materialized artifacts are immutable.
5. Withdrawal preserves the historical registration, hashes, rationale, and replacement reference if one exists.
6. Gene symbols never replace `EnsemblID` as entity identity.

## 6. Source-snapshot registration

The registration must distinguish:

- source identity and version;
- retrieval/query specification;
- retrieved immutable artifact;
- `source_snapshot_version`;
- profile-level `evidence_snapshot_version` that manifests one or more component snapshots.

A mutable endpoint response is not a source snapshot. Any byte, record, source release, mapping, or query-scope change creates a new source snapshot identity.

## 7. Required review record

Each lifecycle transition must preserve:

- transition from and to;
- registration version;
- review scope;
- technical findings;
- scientific findings;
- unresolved issues;
- disposition;
- reviewer role and non-runtime human authorization record;
- referenced artifact IDs, versions, sizes, and hashes.

An LLM may not approve a transition, resolve an unresolved scientific judgement, or assign a lifecycle status at runtime.

## 8. Current-component compatibility

`COMP_TRANSCRIPTOMIC_EVIDENCE` is the only currently materialized component. Task #030 is a validated local release candidate and Task #031 is a deterministic representation layer. The Task #025 state rules retain `AWAITING_INDEPENDENT_SCIENTIFIC_REVIEW`.

This policy does not retroactively promote that component or release. The existing review limitation remains visible and must be considered against the gate for any future lifecycle destination.

## 9. Registration checklist

- [ ] The proposal contains one bounded observation question.
- [ ] Identity and version fields satisfy the universal interface.
- [ ] `component_version` and `component_definition_version` bind exactly.
- [ ] Feature, state, missingness, provenance, and dependency contracts are complete.
- [ ] No source retrieval has been performed merely by registration.
- [ ] Review disposition and unresolved decisions are explicit.
- [ ] Validation fixtures cover all controlled states and missingness values.
- [ ] Materialization scope and intended profile lifecycle destination are declared.
- [ ] Frozen artifacts are immutable and hash-manifested.
- [ ] No score, rank, confidence metric, target-quality field, therapeutic recommendation, or runtime AI decision exists.

## 10. Related specifications

- [Evidence Component Interface Specification v0.1](evidence_component_interface_specification_v0.1.md)
- [Component Validation Requirements v0.1](component_validation_requirements_v0.1.md)
- [Component Dependency Model v0.1](component_dependency_model_v0.1.md)
- [Profile Lifecycle Specification v0.1](profile_lifecycle_specification_v0.1.md)

