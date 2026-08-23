# Evidence Aggregation Representation Specification v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Task:** #034A  
**Version:** v0.1  
**Status:** Governance and schema specification; no evidence-summary payload authorized or generated

## 1. Purpose and boundary

This specification defines a deterministic, non-evaluative Evidence Summary representation derived from a governed Multi-component Evidence Landscape. An Evidence Summary organizes component states, feature missingness, dependency relationships, artifact namespaces, and limitation identifiers into a smaller structural object without changing their meaning.

This is representation only. It does not retrieve evidence, rebuild a component, modify a profile or landscape, interpret biology, or authorize full-universe summary generation. It must not score, rank, prioritize, select, recommend, or evaluate a target. Runtime AI or LLM decisions are prohibited.

## 2. Evidence Summary ontology

### 2.1 Entity

The immutable entity key is the versioned `EnsemblID` copied from the source landscape. A gene symbol, component state, missingness value, record count, or artifact identifier must not replace `EnsemblID` or serve as a fallback join key.

### 2.2 Evidence Landscape

The governed source is one Multi-component Evidence Landscape with:

- `landscape_schema_version = EVIDENCE_LANDSCAPE_SCHEMA_V0.2.1`;
- `landscape_version = MULTI_COMPONENT_EVIDENCE_LANDSCAPE_V0.2`;
- a resolvable source landscape identity and content SHA256;
- component, feature-missingness, provenance, dependency, artifact, and limitation references.

The schema patch changed serialization compatibility only; it did not change the v0.2 landscape semantics.

### 2.3 Evidence Summary

An Evidence Summary is a deterministic structural projection of exactly one source landscape. It describes:

- the source landscape identity;
- each source component identity, version, and exact component state;
- each source feature's controlled missingness;
- each source evidence relationship's ordered dependency type/level pairs and artifact namespace;
- applicable limitation identifiers.

It does not establish evidence strength, confidence, target quality, causality, biological importance, therapeutic relevance, efficacy, safety, or clinical benefit. Summary completeness and relationship quantity are audit properties, not target properties.

## 3. Evidence Summary identity

One Evidence Summary is identified by:

`(EnsemblID, evidence_summary_schema_version, evidence_summary_version, source_landscape_id, source_landscape_schema_version, source_landscape_version)`

The v0.1 identifiers are:

- `evidence_summary_schema_version = EVIDENCE_SUMMARY_SCHEMA_V0.1`;
- `evidence_summary_version = EVIDENCE_AGGREGATION_REPRESENTATION_V0.1`.

A deterministic `evidence_summary_id` may encode the identity tuple. It must not depend on gene symbol, component state, evidence quantity, wall-clock time, randomness, storage path, mutable network state, or AI judgement.

## 4. Relationship to the source landscape

The required one-way relationship is:

```text
governed Multi-component Evidence Landscape
                    ↓
          structural Evidence Summary
```

The source landscape remains canonical. A summary is a view and must retain the source landscape ID, schema version, semantic version, generator version, evidence-snapshot reference, content SHA256, and universe ordinal. It must not reconstruct a landscape from independently selected components or combine records from different landscape identities.

The complete lineage is:

```text
Evidence Summary
      ↓
source Landscape
      ↓
source Component
      ↓
source Feature / missingness
      ↓
evidence-record dependency relationship
      ↓
source-native Artifact ID and namespace
```

## 5. Required representation

Each summary object must contain:

- immutable `EnsemblID` and source `universe_ordinal`;
- deterministic summary identity and independent schema, representation, and generator versions;
- exact source-landscape identity and content hash;
- an ordered `component_summaries` array;
- a `limitation_identifiers` array.

Each component summary must preserve:

- `component_id`;
- `component_version`;
- exact source `component_state`;
- source component-record identity and content hash;
- an ordered `feature_missingness` array;
- an ordered `dependency_summaries` array;
- applicable component limitation identifiers.

Component representation follows [Evidence Summary Component Policy v0.1](evidence_summary_component_policy_v0.1.md). Dependency representation follows [Evidence Summary Dependency Policy v0.1](evidence_summary_dependency_policy_v0.1.md).

## 6. State and missingness preservation

Component states remain exact non-ordinal structural labels:

- `OBSERVED`;
- `PARTIAL`;
- `CONFLICTING`;
- `MISSING`;
- `NOT_QUERIED`.

Feature missingness remains exact and feature-specific:

- `OBSERVED`;
- `NOT_FOUND`;
- `NOT_QUERIED`;
- `NOT_APPLICABLE`;
- `UNKNOWN`.

The summary must not infer an overall state, compare states across components, fill one component from another, convert missingness to negative evidence, or substitute a component state for feature missingness.

## 7. Dependency and artifact preservation

Every summarized dependency relationship must retain the source component, feature, evidence record, dependency identifier, ordered `dependency_relationships` array, and artifact reference. Each relationship object preserves both `relationship_type` and `dependency_level`.

Source-native `artifact_id` and `artifact_namespace` are separate mandatory fields. The summary must not rewrite an artifact identifier into a project-local namespace. Multiple relationship types attached to one evidence relationship remain separate ordered entries and are not collapsed into one label or a count.

## 8. Limitation preservation

Every applicable source limitation remains identifiable through a stable `limitation_id`. Summary-level and component-level limitation arrays preserve source order and scope. A limitation identifier must not be translated into a penalty, weight, score, confidence decrement, target filter, or interpretive conclusion.

Removing, resolving, or adding a limitation requires a separately governed source change and version decision. A summary generator must not decide that a limitation is obsolete.

## 9. Independent version axes

| Axis | Governs |
|---|---|
| `evidence_summary_schema_version` | Summary fields, types, cardinalities, and constraints |
| `evidence_summary_version` | Structural projection semantics |
| `summary_generator_version` | Deterministic generation and serialization behavior |
| `source_landscape_schema_version` | Source landscape serialization contract |
| `source_landscape_version` | Source landscape projection semantics |
| `source_evidence_snapshot_version` | Frozen evidence values and records inherited through the source landscape |
| `component_version` | Component-specific evidence representation semantics |

These axes must not be collapsed. A higher version is not evidence of quality, maturity, confidence, or target suitability.

## 10. Prohibited fields and inferences

The [Evidence Summary schema v0.1](../../schemas/evidence_summary_schema_v0.1.json) and every future materializer must reject these fields at every object level:

- `score`;
- `ranking`;
- `priority`;
- `confidence`;
- `overall_state`;
- `recommendation`;
- `target_quality`;
- `evidence_strength`.

Aliases or hidden aggregations with the same purpose are also prohibited. The representation must not imply target selection, biological interpretation, therapeutic direction, efficacy, safety, or clinical benefit.

## 11. Artifact and lifecycle boundary

This task creates only Class A governance documents, schema, and schema-generator source. It creates no evidence-summary records, indexes, releases, or external payloads. A future summary payload requires a separate authorized materialization task, frozen input manifest, deterministic generator, validation report, hashes, storage classification, and lifecycle decision.

Creating a schema does not promote any profile, landscape, component, summary, or release to scientific review or public release.

## 12. Validation

The schema and any future materializer must satisfy [Evidence Summary Validation Requirements v0.1](evidence_summary_validation_requirements_v0.1.md). At minimum validation must establish identity fidelity, component/state fidelity, feature-missingness fidelity, dependency and artifact-namespace fidelity, limitation preservation, prohibited-field rejection, deterministic regeneration, and frozen-input integrity.

## 13. Related governance

- [Target Evidence Profile Governance v0.1](target_evidence_profile_governance_v0.1.md)
- [Multi-component Evidence Landscape Specification v0.2](multi_component_evidence_landscape_specification_v0.2.md)
- [Evidence Landscape Component Composition Policy v0.1](evidence_landscape_component_composition_policy_v0.1.md)
- [Evidence Summary Component Policy v0.1](evidence_summary_component_policy_v0.1.md)
- [Evidence Summary Dependency Policy v0.1](evidence_summary_dependency_policy_v0.1.md)
- [Evidence Summary Validation Requirements v0.1](evidence_summary_validation_requirements_v0.1.md)

