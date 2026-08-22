# Target Evidence Profile Governance v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Version:** v0.1  
**Status:** Frozen governance specification

## 1. Purpose

This document defines the ontology and governance boundaries of a Target Evidence Profile. A Target Evidence Profile is an auditable, versioned representation of evidence observations for one immutable target entity. It organizes evidence without evaluating the target.

The framework must not score, rank, prioritize, select, or recommend targets. It must not infer target quality, biological importance, therapeutic direction, efficacy, safety, or clinical benefit. Profile generation is deterministic evidence representation, not biological interpretation.

This specification governs future profile artifacts. It does not modify the frozen Task #026 features or provenance, the Task #025 state rules, or the Task #027 pilot profiles.

## 2. Target Evidence Profile ontology

### 2.1 Target entity

The target entity is identified only by immutable, versioned `EnsemblID`. A gene symbol may be displayed as annotation in a future schema but must never replace `EnsemblID`, serve as a join key, or silently repair identity.

### 2.2 Profile

A profile is the complete structured representation for one `EnsemblID` under one profile version and one evidence snapshot. It contains one or more registered evidence components and the release metadata needed to reproduce their materialization.

A profile describes:

- available evidence features;
- controlled missingness;
- structural component states;
- unresolved conflicts and uncertainty;
- complete record-level provenance;
- the versions and hashes that generated the representation.

A profile does not establish:

- causality;
- biological importance;
- therapeutic relevance or direction;
- efficacy or safety;
- target quality, suitability, or priority;
- clinical benefit;
- a recommendation.

Profile completeness is not target quality. Evidence quantity is not evidence quality. Component count and provenance-link count are audit metadata, not confidence measures.

### 2.3 Component

A component is a governed evidence-domain module within a profile. Each component has a stable identifier, a bounded scientific question, a typed feature contract, deterministic state rules, missingness rules, dependency rules, provenance requirements, and explicit interpretation boundaries.

The only currently materialized component is:

`COMP_TRANSCRIPTOMIC_EVIDENCE`

Its current evidence is derived from the frozen Task #026 transcriptomic feature layer and is governed in [Profile Component Model v0.1](profile_component_model_v0.1.md).

### 2.4 Feature

A feature is a normalized structural observation with:

- stable `feature_id`;
- governed `feature_name` and data type;
- exact value copied or deterministically derived under a versioned extraction rule;
- controlled missingness state;
- one or more uncompressed provenance relationships.

Feature names and values must not encode scores, rankings, priorities, recommendations, target quality, or hidden biological judgements.

### 2.5 Provenance relationship

A provenance relationship connects one feature value to one evidence record. Its governed key is:

`(feature_id, evidence_record_id)`

The relationship preserves claim, source, artifact, dependency, extraction-rule, and extractor-version lineage. Multiple evidence records connected to one feature remain separate relationships and retain their dependency metadata. They are not independent votes merely because multiple rows exist.

Large provenance artifacts follow [Task #026 Provenance Artifact Governance v0.1](task026_provenance_artifact_governance_v0.1.md).

### 2.6 Evidence snapshot

An evidence snapshot is the immutable set of input evidence artifacts, source versions, controlled schemas, and hashes available to a materialization run. Changing any evidence value, evidence record, source release, or governed missingness value creates a new evidence snapshot version.

### 2.7 Profile lifecycle state

Lifecycle state records the governance maturity of a profile release:

- `PILOT_VALIDATION_ONLY`
- `INTERNAL_VALIDATION`
- `SCIENTIFIC_REVIEWED`
- `PUBLIC_RELEASE`

Lifecycle state is not a component evidence state and is not a target assessment. Lifecycle transitions are governed by [Profile Lifecycle Specification v0.1](profile_lifecycle_specification_v0.1.md).

### 2.8 Release

A release is an immutable, manifested collection of profiles with a named lifecycle state. It includes the exact schema, profile, evidence-snapshot, component, rule, generator, input, output, and provenance identities required for regeneration and audit.

## 3. Identity and version boundaries

### 3.1 Profile identity

One materialized profile is scientifically identified by the tuple:

`(EnsemblID, profile_version, evidence_snapshot_version)`

A deterministic `profile_id` may encode this tuple. It must not depend on gene symbol, row position, wall-clock time, random values, or an AI decision.

### 3.2 Independent version axes

The following versions have separate meanings and must not be collapsed:

| Version | Governs | Changes when |
|---|---|---|
| `schema_version` | Serialized fields, types, cardinalities, and validation constraints | The structural contract changes |
| `profile_version` | Profile assembly semantics, component inclusion, and materialization contract | The meaning or assembly of the profile changes |
| `evidence_snapshot_version` | Exact evidence values, source releases, evidence records, and input hashes | Any governed evidence input changes |
| `component_definition_version` | One component's question, feature interface, missingness, dependency, or state contract | Component semantics change |
| `state_rule_version` | Executable component-state predicates and precedence | A predicate or precedence changes |
| `extractor_version` | Source-record-to-feature transformation | Feature extraction behavior changes |
| `generator_version` | Deterministic profile serialization/materialization implementation | Materializer behavior changes |

A schema-only serialization migration may retain the profile and evidence-snapshot versions only when evidence meaning and profile assembly are demonstrably unchanged. A new evidence snapshot does not by itself authorize changes to profile semantics. Every release manifest must record all applicable axes.

## 4. Governance principles

1. `EnsemblID` remains immutable throughout feature extraction and profile materialization.
2. Feature values must be identical to their governed normalized source unless a separately versioned deterministic transformation is explicitly registered.
3. Missingness remains controlled and distinct: `OBSERVED`, `NOT_FOUND`, `NOT_QUERIED`, `NOT_APPLICABLE`, and `UNKNOWN` must not be collapsed.
4. Missing evidence is not negative evidence. `NOT_QUERIED` is not biological absence.
5. Dependent records retain dependency links and are never counted as independent confirmation.
6. Every profile feature has complete, uncompressed record-level provenance.
7. The same frozen inputs, versions, rules, and generator must produce byte-identical governed outputs.
8. Runtime AI or LLM decisions are prohibited in feature values, component states, profile assembly, lifecycle transitions, and release validation.
9. A profile may expose uncertainty and conflict but must not resolve them through unstated judgement.
10. No component or profile may contain or imply scoring, ranking, target prioritization, therapeutic recommendation, or biological interpretation.

## 5. Current governed scope

Task #027 established a ten-entity pilot with:

- lifecycle state `PILOT_VALIDATION_ONLY`;
- schema `TARGET_EVIDENCE_PROFILE_PILOT_SCHEMA_V0.1`;
- profile version `PILOT_TARGET_EVIDENCE_PROFILE_V0.1`;
- one component, `COMP_TRANSCRIPTOMIC_EVIDENCE`;
- exact Task #026 feature values;
- uncompressed Task #026 provenance relationships;
- deterministic Task #025 structural state resolution.

The pilot validates architecture only. It is not evidence that the framework has passed internal, scientific, or public-release review. It does not authorize materialization of unregistered future components.

## 6. Validation checklist

Every governed profile build must confirm:

- [ ] Exactly one immutable `EnsemblID` identifies each profile.
- [ ] `schema_version`, `profile_version`, and `evidence_snapshot_version` are present and semantically distinct.
- [ ] Every component is registered under a stable component identifier and version.
- [ ] Every feature name, type, value, and extraction rule matches the frozen feature contract.
- [ ] Every feature has at least one complete provenance relationship.
- [ ] Every `(feature_id, evidence_record_id)` relationship is unique.
- [ ] All claim, record, source, artifact, dependency, rule, extractor, and generator references resolve.
- [ ] Missingness states are valid and unchanged from governed inputs.
- [ ] Dependency relationships are preserved and no dependent records are treated as independent votes.
- [ ] Component states are produced only by the frozen executable rules and precedence.
- [ ] No score, rank, priority, target prioritization, recommendation, therapeutic direction, biological interpretation, or hidden aggregation exists.
- [ ] No AI or LLM runtime decision contributed to any value, state, transition, or release decision.
- [ ] Regeneration from identical frozen inputs is byte-identical.
- [ ] Input and output sizes and SHA256 hashes match the release manifest.
- [ ] The lifecycle gate required by the declared release state has passed.
- [ ] Limitations, unresolved conflicts, and untested state paths are explicit.

## 7. Related governance documents

- [Profile Lifecycle Specification v0.1](profile_lifecycle_specification_v0.1.md)
- [Profile Component Model v0.1](profile_component_model_v0.1.md)
- [Profile Release Policy v0.1](profile_release_policy_v0.1.md)
- [Task #026 Provenance Artifact Governance v0.1](task026_provenance_artifact_governance_v0.1.md)

