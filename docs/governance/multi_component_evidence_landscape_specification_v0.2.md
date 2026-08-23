# Multi-component Evidence Landscape Specification v0.2

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Task:** #033A  
**Version:** v0.2  
**Status:** Governance specification; no landscape payload authorized or generated

## 1. Purpose and boundary

This specification defines how a future Multi-component Evidence Landscape v0.2 may represent the frozen Task #032C Target Evidence Profiles. A landscape is a deterministic structural projection of evidence already present in a governed profile. It describes component availability, component states, feature missingness, provenance relationships, dependency relationships, and declared limitations without evaluating a target.

This document does not generate code, schemas, profiles, landscapes, evidence, scores, rankings, priorities, candidate selections, recommendations, or biological or therapeutic interpretations. It does not authorize evidence retrieval or profile lifecycle promotion. Runtime AI or LLM judgement is prohibited.

The governed source is the Task #032C multi-component integration candidate described by its [profile manifest](../../outputs/evidence_profile_integration_v0.1/profile_manifest.json) and [validation report](../../outputs/evidence_profile_integration_v0.1/validation_report.md). This specification does not modify that source or the earlier Task #031 single-component landscape.

## 2. Landscape ontology

### 2.1 Entity

The immutable entity key is the versioned `EnsemblID`. A symbol, label, component state, evidence count, or source identifier must not replace it or be used as a fallback join key.

### 2.2 Component

A component is a registered, independently versioned evidence-domain representation governed by the [Evidence Component Interface Specification v0.1](evidence_component_interface_specification_v0.1.md). The v0.2 source profile contains exactly:

- `COMP_TRANSCRIPTOMIC_EVIDENCE_V0.1`;
- `COMP_DISEASE_ASSOCIATION_V0.1`.

Components remain scientifically and structurally separate. Presence of two components does not create a combined component state, evidence-strength measure, confidence measure, score, rank, priority, vote, or recommendation.

### 2.3 Target Evidence Profile

A Target Evidence Profile is the canonical component-bearing representation for one EnsemblID under one profile schema, profile version, and evidence snapshot. It retains feature values and complete evidence-record lineage. Its governance is defined in [Target Evidence Profile Governance v0.1](target_evidence_profile_governance_v0.1.md).

The frozen Task #032C profile identity is:

`(EnsemblID, profile_schema_version, profile_version, evidence_snapshot_version)`

The landscape consumes that profile identity; it must not reconstruct a profile from independently selected components or mix components from different evidence snapshots.

### 2.4 Evidence landscape

An evidence landscape is a non-evaluative projection of one source profile. It may expose:

- source-profile identity and content hash;
- registered component identities and versions;
- whether each component is present in the source profile;
- exact structural component state;
- exact feature missingness;
- feature and evidence-record references;
- dependency relationship references;
- artifact and version lineage;
- applicable governed limitation identifiers.

A landscape must not alter feature values or state meanings, resolve conflicts, fill missing data, infer cross-component agreement, or generate target-level conclusions.

## 3. Landscape identity

One landscape object is identified by the tuple:

`(EnsemblID, landscape_schema_version, landscape_version, source_profile_id, source_evidence_snapshot_version)`

For this governance version:

- `landscape_schema_version = EVIDENCE_LANDSCAPE_SCHEMA_V0.2`;
- `landscape_version = MULTI_COMPONENT_EVIDENCE_LANDSCAPE_V0.2`;
- `source_profile_version = TARGET_EVIDENCE_PROFILE_MULTICOMPONENT_V0.1`;
- `source_evidence_snapshot_version = EVIDENCE_SNAPSHOT_32C_CBFD2625F8B0CBB855DB90CBC8E2D605`.

A deterministic `landscape_id` may encode the identity tuple. It must not depend on gene symbol, component state, feature availability, evidence quantity, partition position, wall-clock time, randomness, mutable network state, or AI judgement.

Landscape identity is distinct from profile identity. A landscape never becomes the canonical source profile and must retain `source_profile_id` plus the exact source-profile content SHA256.

## 4. Relationship between profile, component, and landscape

The required lineage is:

```text
immutable EnsemblID
        ↓
source Target Evidence Profile
        ↓
registered component instance
        ↓
normalized feature reference
        ↓
evidence-record relationship
        ↓
source artifact and dependency relationship
```

The profile is the canonical component-bearing evidence object. The component retains evidence-domain semantics. The landscape is a deterministic view of profile structure and limitations. A landscape may summarize counts for reconciliation, but counts cannot replace feature-, record-, artifact-, or dependency-level references.

The landscape must contain exactly one projection for each component object in the source profile and no component that is absent from it. Component composition is governed by [Evidence Landscape Component Composition Policy v0.1](evidence_landscape_component_composition_policy_v0.1.md).

## 5. Multi-component landscape structure

Each landscape object must contain:

- immutable `EnsemblID`;
- deterministic landscape identity and universe ordinal;
- landscape schema, landscape, and generator versions;
- exact source-profile identity, schema version, profile version, evidence-snapshot version, and content hash;
- an ordered component array matching the source-profile component order;
- component identity, component version, exact state, state-rule metadata, and source component-record reference;
- feature references with exact missingness and provenance/dependency relationships;
- stable limitation identifiers and a resolvable limitation registry.

The current component order is:

1. `COMP_TRANSCRIPTOMIC_EVIDENCE`;
2. `COMP_DISEASE_ASSOCIATION`.

Order is deterministic serialization metadata, not a ranking or priority.

## 6. State preservation

Each component projection must preserve its exact source state:

- `OBSERVED`;
- `PARTIAL`;
- `CONFLICTING`;
- `MISSING`;
- `NOT_QUERIED`.

States remain component-specific, non-ordinal structural labels. The landscape must not:

- calculate an overall profile state;
- choose one component state over another;
- convert `MISSING` into negative evidence;
- convert `NOT_QUERIED` into biological absence;
- treat `OBSERVED` as evidence strength or target quality;
- infer agreement or conflict between components from their labels.

Release-level component-state counts and joint cross-tabs may be recorded only as clearly labelled audit reconciliation metadata. They must not appear as target-level derived features and must not drive filtering, ranking, or lifecycle promotion.

## 7. Missingness preservation

Feature missingness must remain exactly one of:

- `OBSERVED`;
- `NOT_FOUND`;
- `NOT_QUERIED`;
- `NOT_APPLICABLE`;
- `UNKNOWN`.

The landscape must copy the source feature missingness without substitution, null collapsing, default filling, or cross-component repair. Component state and feature missingness remain distinct vocabularies. A missingness count is audit metadata and does not establish biological absence or evidence quality.

## 8. Provenance requirements

Every landscape feature reference must resolve to the source profile, component, and feature. Every source feature-to-record relationship must remain separately representable using at least:

- `component_id` and component version;
- `feature_id`;
- `claim_id` where supplied by the component contract;
- `evidence_record_id`;
- `source_id`;
- `artifact_id` and resolvable artifact hash/reference;
- `dependency_id` or governed sentinel;
- `extraction_rule_id` and `extractor_version` at the relationship or parent-feature level defined by the component;
- source component-record and source-profile references.

The source provenance relationship key remains `(feature_id, evidence_record_id)` within a component. A landscape projection may use `(component_id, feature_id, evidence_record_id)` as its cross-component uniqueness key so identical feature identifiers in different component namespaces cannot collide.

Provenance counts, hashes, or component summaries do not replace the full logical relationship set. Large provenance payloads may be stored externally only under the artifact policy in Section 11.

## 9. Dependency representation

Dependency metadata must remain attached to the evidence-record relationship it qualifies. The landscape must preserve the governed relationship types and levels from [Component Dependency Model v0.1](component_dependency_model_v0.1.md), including:

- `SAME_SOURCE / DEPENDENT`;
- `SHARED_DATASET / DEPENDENT`;
- `PARTIAL / PARTIALLY_DEPENDENT`;
- `UNKNOWN / UNKNOWN`;
- affirmatively supported `INDEPENDENT / INDEPENDENT`;
- `NOT_APPLICABLE / NOT_APPLICABLE`.

`NOT_APPLICABLE` must not become `INDEPENDENT`. Missing dependency information must not default to independence. Component boundaries must not erase shared upstream origin, and multiple dependent records must not be presented as independent votes.

## 10. Limitations

Limitations must be identified by stable IDs, scoped to `LANDSCAPE`, `PROFILE`, `COMPONENT`, `FEATURE`, `SOURCE`, or `ARTIFACT`, and resolved through a manifested registry. A limitation from Task #031 that states only the transcriptomic component was present applies only to the Task #031 source release and must not be propagated as a current v0.2 limitation after Task #032C.

Removing, resolving, or revising a limitation requires evidence in the frozen source and a versioned governance change. A limitation must not be converted into a score, penalty, confidence decrement, or target-selection rule.

## 11. Artifact classification and storage policy

The Task #018 artifact classes apply:

| Artifact | Class | Default governance |
|---|---|---|
| Specifications, schemas, controlled vocabularies, generator source | Class A | Ordinary Git after review |
| Small manifests, indexes, QC summaries, validation reports | Class B | Ordinary Git when reviewable; externalize if size threshold is crossed |
| Source release and evidence-snapshot metadata | Class C | Git for small metadata; immutable external storage for large snapshots |
| Landscape JSONL, provenance/dependency tables, large indexes or payloads | Class D | Immutable external storage plus Git-managed manifest |

Any generated output at or above 50,000,000 bytes requires storage review. A file above 100,000,000 bytes must not enter ordinary Git. Git LFS requires a separate explicit decision before first commit; otherwise immutable external/object storage is preferred.

Every externally managed object must have a stable artifact ID, schema version, exact byte size, SHA256, generation task, generator version, frozen input manifest, immutable storage reference, and validation status. A manifest or count does not replace the canonical payload.

## 12. Validation and lifecycle boundary

Before a v0.2 landscape candidate may be treated as reproducible, it must pass [Evidence Landscape Validation Requirements v0.1](evidence_landscape_validation_requirements_v0.1.md). Version changes follow [Evidence Landscape Versioning Policy v0.1](evidence_landscape_versioning_policy_v0.1.md).

Landscape generation does not promote the source profile or the landscape to `INTERNAL_VALIDATION`, `SCIENTIFIC_REVIEWED`, or `PUBLIC_RELEASE`. Lifecycle transitions remain separate human governance actions under [Profile Lifecycle Specification v0.1](profile_lifecycle_specification_v0.1.md).

## 13. Explicit prohibitions

Multi-component Evidence Landscape v0.2 must not create or imply:

- evidence scores or weighted aggregates;
- confidence metrics or evidence strength;
- overall component/profile states;
- target ranks, priorities, selections, or recommendations;
- biological importance, causality, therapeutic value, direction, efficacy, safety, or clinical benefit;
- cross-component voting;
- runtime AI or LLM decisions.

## 14. Related governance

- [Evidence Landscape Component Composition Policy v0.1](evidence_landscape_component_composition_policy_v0.1.md)
- [Evidence Landscape Versioning Policy v0.1](evidence_landscape_versioning_policy_v0.1.md)
- [Evidence Landscape Validation Requirements v0.1](evidence_landscape_validation_requirements_v0.1.md)
- [Target Evidence Profile Governance v0.1](target_evidence_profile_governance_v0.1.md)
- [Evidence Component Interface Specification v0.1](evidence_component_interface_specification_v0.1.md)
- [Task #026 Provenance Artifact Governance v0.1](task026_provenance_artifact_governance_v0.1.md)

