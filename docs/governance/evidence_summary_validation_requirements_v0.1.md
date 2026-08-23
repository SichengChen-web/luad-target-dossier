# Evidence Summary Validation Requirements v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Task:** #034A  
**Version:** v0.1  
**Status:** Governance requirements; no evidence-summary payload generated

## 1. Purpose and boundary

These requirements govern validation of the Evidence Summary representation and any future materializer. Task #034A validates governance terminology and the machine-readable schema only. It does not generate target summaries or evaluate biological or therapeutic evidence.

## 2. Frozen context validation

Before schema generation, verify exact hashes for the relevant frozen Task #028 profile governance, Task #033A landscape governance, Task #033B-1.1 schema contract, and Task #033B-2 landscape release metadata. Repeat the hash check after generation.

An unexpected missing, modified, or substituted artifact must fail validation. A schema task must not modify source profiles, components, landscapes, manifests, indexes, payloads, or earlier governance.

## 3. Terminology and version validation

Confirm exact use of:

- `EnsemblID` as immutable identity;
- `EVIDENCE_LANDSCAPE_SCHEMA_V0.2.1` as source serialization contract;
- `MULTI_COMPONENT_EVIDENCE_LANDSCAPE_V0.2` as source semantic version;
- `EVIDENCE_SUMMARY_SCHEMA_V0.1` as summary schema version;
- `EVIDENCE_AGGREGATION_REPRESENTATION_V0.1` as summary representation version;
- the five component states and five feature-missingness values;
- ordered dependency relationship objects;
- separate source-native artifact IDs and namespaces.

Schema, summary, landscape, profile, evidence-snapshot, component, extractor, rule, and generator versions must remain independent.

## 4. Schema structural validation

The schema must:

- declare JSON Schema Draft 2020-12;
- use closed objects so undeclared fields fail;
- require immutable identity and source-landscape identity;
- require at least one component summary;
- require per-feature missingness references rather than counts alone;
- require per-record dependency summaries with ordered relationship arrays;
- require source-native artifact ID, namespace, and SHA256;
- require explicit limitation identifier arrays;
- constrain controlled vocabularies and compatible dependency type/level pairs.

Every local `$ref` must resolve. Every object definition must declare `additionalProperties: false`.

## 5. Identity validation

A future materializer must verify:

- one source landscape produces exactly one summary;
- summary `EnsemblID` equals source landscape `EnsemblID`;
- source universe ordinal and landscape identity are unchanged;
- summary identity tuple is complete and deterministic;
- no gene symbol join, fallback mapping, or identifier rewriting occurs.

## 6. Component, state, and missingness validation

For every source component and feature:

- component ID and version match exactly;
- source component-record ID and content hash resolve;
- summary component state equals landscape state;
- every source feature has one ordered missingness entry;
- summary missingness equals landscape missingness;
- no component or feature is added, removed, merged, or reordered.

Boundary fixtures must accept all five component states and all five feature-missingness values and reject uncontrolled values, null collapse, default filling, and cross-component repair.

## 7. Dependency and artifact validation

For every source provenance/dependency relationship:

- `(component_id, feature_id, evidence_record_id)` resolves uniquely;
- `dependency_id` is retained;
- ordered relationship type/level pairs reconcile exactly;
- multiple `SAME_SOURCE` and `SHARED_DATASET` entries remain separate;
- relationship type and level are compatible;
- source-native artifact ID, namespace, and SHA256 are unchanged;
- no relationship is replaced by a count or digest.

Fixtures must include a multi-relationship dependency and a non-`ART` artifact namespace.

## 8. Limitation validation

Every summary and component limitation identifier must match an applicable source landscape limitation identifier and preserve order. A limitation cannot be invented, silently dropped, interpreted, or converted into an evaluation field.

## 9. Prohibited-field validation

Recursively reject exact fields:

- `score`;
- `ranking`;
- `priority`;
- `confidence`;
- `overall_state`;
- `recommendation`;
- `target_quality`;
- `evidence_strength`.

Also reject aliases or structures that perform scoring, ranking, target selection, recommendation, biological interpretation, therapeutic interpretation, confidence estimation, evidence-strength estimation, or hidden aggregation.

Prohibition language in governance and validation reports is allowed when clearly stated as a non-claim.

## 10. Determinism validation

Identical frozen inputs, schema-generator version, and canonical serialization rules must produce byte-identical schema bytes. A future materializer must independently regenerate complete summary artifacts and compare bytes, sizes, hashes, identity order, and relationship cardinality.

No governed value may depend on wall-clock time, randomness, hostname, mutable network state, manual editing, or runtime AI/LLM decisions.

## 11. Documentation validation

Validate that:

- terminology matches Tasks #028, #033A, and #033B;
- every local Markdown link resolves;
- every referenced identifier and version is exact;
- no document claims that Task #034A generated summary payloads;
- no existing artifact changed.

## 12. Payload and network boundary

Task #034A may create only the four governance documents, the schema-generator source, and the schema contract. It must not create evidence-summary records, indexes, manifests, target-level summaries, external payloads, or evidence artifacts. Network/API access and package installation are prohibited.

## 13. Release gate for future materialization

- [ ] Frozen source landscape manifest, index, schema, payload reference, and hashes resolve.
- [ ] Identity and canonical order reconcile completely.
- [ ] Component IDs, versions, states, and feature missingness reconcile.
- [ ] Dependency relationships and artifact namespaces reconcile without loss.
- [ ] Limitation identifiers reconcile.
- [ ] Prohibited-field scan passes recursively.
- [ ] Complete regeneration is byte-identical.
- [ ] Artifact classification and storage governance pass.
- [ ] No scoring, ranking, prioritization, recommendation, or interpretation exists.
- [ ] Lifecycle promotion remains a separate human governance action.

## 14. Related governance

- [Evidence Aggregation Representation Specification v0.1](evidence_aggregation_representation_specification_v0.1.md)
- [Evidence Summary Component Policy v0.1](evidence_summary_component_policy_v0.1.md)
- [Evidence Summary Dependency Policy v0.1](evidence_summary_dependency_policy_v0.1.md)
- [Evidence Landscape Validation Requirements v0.1](evidence_landscape_validation_requirements_v0.1.md)
- [Evidence Summary schema v0.1](../../schemas/evidence_summary_schema_v0.1.json)

