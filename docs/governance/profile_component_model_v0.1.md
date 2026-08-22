# Profile Component Model v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Version:** v0.1  
**Status:** Frozen governance specification

## 1. Purpose

This document defines the governed interface for evidence components within a Target Evidence Profile. It specifies the current transcriptomic component and the registration contract for future components without implementing any future evidence extractor, rule, or profile field.

A component organizes bounded evidence observations. It does not score, rank, prioritize, select, or recommend targets and does not generate biological or therapeutic interpretations.

## 2. Component ontology

Each component is a versioned module with:

- stable `component_id`;
- `component_definition_version`;
- bounded scientific question;
- evidence domain and acceptable evidence types;
- required evidence-record roles;
- normalized feature interface;
- controlled missingness contract;
- dependency-preservation contract;
- executable state-rule registry and precedence;
- complete provenance contract;
- validation fixtures and release status;
- explicit interpretation boundaries.

Components remain semantically distinct. Presence of multiple components does not authorize cross-component aggregation, voting, scoring, ranking, or prioritization.

## 3. Current component: `COMP_TRANSCRIPTOMIC_EVIDENCE`

### 3.1 Bounded question

What frozen tumour-versus-normal transcriptomic observations, statistical threshold states, and prespecified model-sensitivity structures are available for this EnsemblID?

The component represents association and analysis structure only. It does not establish causality, biological importance, target validity, therapeutic relevance, or therapeutic direction.

### 3.2 Current inputs

The current component consumes the frozen Task #026 normalized transcriptomic feature contract. It preserves exact feature strings, governed missingness, extraction-rule identities, extractor version, and every record-level provenance relationship.

The current source roles are:

- `TRANSCRIPT_PRIMARY`
- `TRANSCRIPT_ROBUSTNESS`

These roles share the same TCGA-LUAD dataset and remain linked as `SHARED_DATASET` with dependency level `DEPENDENT`. They are not independent replications or votes.

### 3.3 Current profile representation

The Task #027 pilot component object contains:

- `component_id`;
- structural `state`;
- `state_rule_id`;
- `state_rule_version`;
- `state_rule_review_status`;
- ordered feature objects.

Each feature object contains:

- `feature_id`;
- `feature_name`;
- exact source `value`;
- governed `data_type`;
- controlled `missingness_status`;
- one or more uncompressed `provenance_links`.

Each provenance link preserves:

- `feature_id`;
- `evidence_record_id`;
- `claim_id`;
- `source_id`;
- `artifact_id`;
- `dependency_id`;
- `extraction_rule_id`;
- `extractor_version`.

### 3.4 Structural states

The component uses the five frozen Task #025 states and precedence:

1. `CONFLICTING`
2. `OBSERVED`
3. `MISSING`
4. `PARTIAL`
5. `NOT_QUERIED`

These states describe structural evidence conditions under versioned predicates. They do not form an ordinal scale, quality grade, confidence level, ranking, or recommendation. Precedence is conflict-resolution logic for deterministic state assignment, not a statement that one target is better than another.

### 3.5 Current limitations

- Only transcriptomic evidence is materialized.
- The Task #027 pilot exercised `OBSERVED` and `CONFLICTING`, not all five states.
- Current Task #026 transcriptomic provenance is entirely `OBSERVED`; non-observed missingness paths remain incompletely tested.
- Task #025 rules retain `AWAITING_INDEPENDENT_SCIENTIFIC_REVIEW`.
- The component describes differential-expression observations and sensitivity structure only; it is not causal or therapeutic evidence.

## 4. Component, profile, and version boundaries

Component definition, profile assembly, and serialization are governed independently:

- `component_definition_version` changes when the component question, record roles, feature interface, missingness rules, dependency rules, provenance requirements, or state meaning changes.
- `state_rule_version` changes when executable predicates or precedence change.
- `extractor_version` changes when source evidence is normalized differently.
- `profile_version` changes when component inclusion or profile assembly semantics change.
- `schema_version` changes when serialized fields or constraints change.
- `evidence_snapshot_version` changes when evidence inputs or source releases change.

A component update does not silently rewrite existing profiles. Existing profiles remain bound to their recorded component, rule, extractor, profile, schema, and evidence-snapshot versions.

## 5. Future component interface

No future component is implemented or authorized by this document. Before implementation, a future component must be registered with all of the following:

| Interface element | Required definition |
|---|---|
| Component identity | Stable `component_id` and `component_definition_version` |
| Scientific scope | One bounded evidence-representation question |
| Evidence domain | Registered ontology domain and allowed evidence types |
| Source contract | Frozen sources, source versions, retrieval scope, and licensing constraints |
| Identity contract | `EnsemblID` linkage with no symbol-based fallback |
| Record roles | Required and optional evidence-record roles and cardinalities |
| Feature contract | Stable feature names, types, controlled values, and extraction rules |
| Missingness contract | Deterministic handling of all allowed missingness states |
| Dependency contract | Rules for same-source, shared-dataset, partial, unknown, and independent relationships |
| State contract | Five-state applicability, deterministic predicates, precedence, and rule version |
| Provenance contract | Claim, record, source, artifact, dependency, rule, extractor, and generator lineage |
| Validation contract | Fixtures for observed, conflicting, missing, partial, and not-queried boundaries where applicable |
| Interpretation boundary | What the component describes and explicitly cannot establish |
| Review status | Technical validation and independent scientific review state |

Registration must precede extractor implementation and profile materialization. A missing field cannot be supplied by an LLM judgement or inferred from a different component.

## 6. Cross-component rules

1. Components cannot consume another component's state as evidence unless a future version explicitly registers that dependency and preserves lineage.
2. Component states cannot be added, averaged, weighted, counted, or voted into a profile-level score.
3. Agreement between components may be described only through a separately governed, provenance-aware representation; it cannot be assumed from field proximity.
4. Dependent sources shared across components must retain dependency links.
5. Missingness remains component-specific and cannot be filled from another domain without a registered evidence relationship.
6. A profile with more populated components is not a higher-quality target profile.
7. No component interface may introduce target prioritization, therapeutic recommendation, biological interpretation, or AI runtime decisions.

## 7. Component validation checklist

- [ ] Stable component identifier and definition version exist.
- [ ] The bounded scientific question and interpretation boundary are explicit.
- [ ] Allowed evidence types and source versions are registered.
- [ ] Required record roles and cardinalities are explicit.
- [ ] Feature names, types, values, and extraction rules are deterministic and versioned.
- [ ] Every feature preserves complete uncompressed provenance.
- [ ] Controlled missingness states are distinct and tested.
- [ ] Dependency relationships are retained and validated.
- [ ] Executable state predicates and precedence are versioned and fixture-tested.
- [ ] State assignment uses no LLM or manual runtime judgement.
- [ ] No state or count is interpreted as score, rank, quality, priority, or recommendation.
- [ ] Schema, profile, evidence-snapshot, component, rule, extractor, and generator versions remain distinct.
- [ ] Independent scientific review status is recorded.
- [ ] Existing frozen profiles are not overwritten by a component revision.

