# Evidence Landscape Validation Requirements v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Task:** #033A  
**Version:** v0.1  
**Status:** Governance requirements; no validation payload or landscape generated

## 1. Purpose and validation boundary

This document defines the validation required before a Multi-component Evidence Landscape v0.2 may be accepted as a reproducible structural projection of the frozen Task #032C Target Evidence Profiles.

Validation tests identity, representation fidelity, state and missingness preservation, lineage, dependency, determinism, artifact integrity, and interpretation safety. It does not validate targets biologically and must not generate scoring, ranking, prioritization, selection, recommendations, evidence strength, confidence, or runtime AI decisions.

## 2. Required frozen inputs

Before generation, a future validator must freeze and verify at least:

- Task #032C profile manifest, index, validation report, generator version, and governed profile payload hash/storage reference;
- Task #028 profile governance documents;
- Task #032A component interface, validation, and dependency governance;
- registered component identities, versions, schemas, source snapshots, generators, and state rules;
- landscape schema, landscape version, generator version, limitation registry, partition strategy, and output contract.

Every file or external object requires a stable artifact identifier, exact size, SHA256, and resolvable immutable reference. A missing source profile payload must fail validation; a manifest or count cannot substitute for it.

## 3. Identity and universe validation

Validate exhaustively:

- exactly 29,606 landscape objects for the frozen Task #032C universe;
- exactly 29,606 unique immutable `EnsemblID` values;
- one landscape per source profile;
- exact Task #032C `universe_ordinal` order;
- exact landscape identity tuple;
- exact `source_profile_id` and source-profile content SHA256;
- no gene-symbol join, fallback mapping, or identity repair;
- no duplicate landscape or source-profile identity.

An identity mismatch must stop the release rather than produce a partial landscape.

## 4. Component composition validation

For every landscape:

1. confirm the source profile resolves and its hash matches;
2. confirm exactly two current component projections;
3. confirm component order is `COMP_TRANSCRIPTOMIC_EVIDENCE`, then `COMP_DISEASE_ASSOCIATION`;
4. confirm component IDs and versions exactly match the source profile;
5. confirm each source component appears once and no extra component appears;
6. confirm availability is `PRESENT_IN_SOURCE_PROFILE` for both current components;
7. confirm source component-record identities, content hashes, artifacts, and version axes resolve;
8. reject any overall state or cross-component aggregate.

Component counts are reconciliation metadata only and must not be interpreted as profile completeness quality.

## 5. State preservation validation

The schema must permit exactly:

- `OBSERVED`;
- `PARTIAL`;
- `CONFLICTING`;
- `MISSING`;
- `NOT_QUERIED`.

For every component instance, landscape state must equal source component state byte-for-byte. Validate per-component state distributions against the Task #032C manifest and reconcile all 59,212 component instances.

Required boundary fixtures cover all five states for each component interface, including states absent from the current materialized snapshot. Fixtures must also reject:

- source/landscape state mismatch;
- missing state;
- uncontrolled state value;
- synthetic overall profile state;
- cross-component precedence or voting;
- conversion of `MISSING` to negative evidence;
- conversion of `NOT_QUERIED` to biological absence.

## 6. Missingness preservation validation

The schema must permit exactly:

- `OBSERVED`;
- `NOT_FOUND`;
- `NOT_QUERIED`;
- `NOT_APPLICABLE`;
- `UNKNOWN`.

For every feature reference, compare landscape missingness to source feature missingness. Validate per-component and release-level reconciliation counts without using them as evidence metrics.

Boundary fixtures must distinguish all five values and reject null collapsing, blank substitution, default `OBSERVED`, cross-component filling, and substitution of component state for feature missingness.

## 7. Feature and provenance validation

For every source feature:

- resolve `component_id`, component version, `feature_id`, and source feature reference;
- confirm feature name and missingness are unchanged;
- confirm source feature-value hash where present;
- reconcile every source `(feature_id, evidence_record_id)` relationship;
- enforce uniqueness of `(component_id, feature_id, evidence_record_id)` in the landscape;
- resolve claim, evidence record, source, artifact, dependency, extraction-rule, extractor, component-record, and source-profile lineage required by the component contract;
- confirm relationship cardinality is unchanged.

The expected current source contains 1,213,846 feature references and 2,517,118 feature-to-record provenance relationships. These are frozen reconciliation expectations, not measures of evidence quality.

Validation must fail if any relationship is replaced by a count, summary, aggregate identifier, or inferred link.

## 8. Dependency validation

Validate every dependency reference against the governed source component and [Component Dependency Model v0.1](component_dependency_model_v0.1.md):

- dependency ID resolves or uses an allowed controlled sentinel;
- relationship type and dependency level are compatible;
- members resolve to the correct evidence records;
- same-source and shared-dataset records remain dependent;
- `PARTIAL` and `UNKNOWN` remain explicit;
- `NOT_APPLICABLE` never becomes `INDEPENDENT`;
- `INDEPENDENT` appears only with affirmative source-traceable support;
- component boundaries do not erase a governed cross-component dependency;
- relationship quantity is not presented as corroboration or confidence.

Required fixtures cover all governed relationship-type/level pairs, invalid combinations, missing members, duplicate members, and unresolved foreign keys.

## 9. Limitation validation

Every limitation ID must resolve through the release limitation registry and declare scope, statement, source/version, and review status. Validate that:

- current component and profile limitations are present;
- resolved limitations are removed only through a versioned decision;
- historical Task #031 limitation `LIM_ONLY_TRANSCRIPTOMIC_COMPONENT` is not applied to the Task #032C two-component source;
- limitations are not converted to scores, penalties, ranks, confidence modifiers, or filtering rules.

## 10. Determinism validation

Given identical frozen inputs and version axes, require:

- byte-identical landscape objects;
- byte-identical indexes, manifests, limitation registries, and validation summaries;
- byte-identical provenance/dependency projections where generated;
- identical canonical order and partition assignment;
- identical file sizes and SHA256 hashes;
- no wall-clock-derived governed values, randomness, mutable network responses, manual row edits, or AI/LLM decisions.

Complete independent regeneration is required. Sampling cannot replace deterministic full comparison.

## 11. Artifact and storage validation

Classify each artifact before release:

- Class A: schemas, specifications, controlled vocabularies, generator source;
- Class B: small reproducible indexes, manifests, QC, validation reports;
- Class C: source release and snapshot metadata;
- Class D: landscape payloads, provenance/dependency payloads, and any large index.

Files at or above 50,000,000 bytes require storage review. Files above 100,000,000 bytes must not enter ordinary Git. For every external artifact, validate stable artifact ID, schema, size, SHA256, generating task, generator version, frozen inputs, immutable storage reference, and retrieval integrity.

Externalization must not compress logical provenance, discard relationships, or substitute metadata for canonical bytes.

## 12. Interpretation-safety validation

Inspect schemas, keys, controlled values, manifests, indexes, reports, and payloads for prohibited fields or conclusions. Reject:

- scores or weighted aggregates;
- ranks, priorities, selections, or recommendations;
- confidence metrics or evidence strength;
- overall states or cross-component votes;
- target quality, biological importance, causality, therapeutic value, direction, efficacy, safety, or clinical benefit;
- free-text runtime interpretation;
- AI/LLM-generated values, states, mappings, or release decisions.

Prohibition text in governance or validation reports is allowed when clearly labelled as a non-claim.

## 13. Documentation validation

Before implementation review, validate:

- terminology matches Task #028 profile governance, Task #032A component governance, and Task #032C profile integration;
- all relative Markdown links resolve from their containing document;
- every referenced version and component identifier is exact;
- no document claims that Task #033A generated a schema, code, landscape, profile, or evidence payload;
- frozen previous artifact hashes remain unchanged.

## 14. Required validation outputs for a future implementation

A future materialization task must produce, at minimum:

- frozen input manifest;
- landscape schema and limitation registry;
- one-row-per-EnsemblID landscape index;
- partition/artifact manifest when payloads are partitioned or externalized;
- complete automated validation results;
- boundary-fixture results;
- deterministic regeneration results;
- artifact hashes and immutable storage references;
- interpretation-safety report;
- session/runtime record without wall-clock-dependent governed values.

Task #033A creates none of these payloads.

## 15. Release gate checklist

- [ ] Frozen source profile payload and all hashes resolve.
- [ ] 29,606 identities and canonical order reconcile.
- [ ] Both components are present once per landscape.
- [ ] Component identities, versions, states, features, missingness, and limitations match source.
- [ ] All 2,517,118 provenance relationships reconcile without loss.
- [ ] Dependency relationships and uncertainty remain explicit.
- [ ] Full regeneration is byte-identical.
- [ ] Artifact classification and immutable storage requirements pass.
- [ ] No prohibited evaluation or interpretation field exists.
- [ ] No runtime AI/LLM decision participates.
- [ ] Lifecycle promotion remains a separate human governance action.

## 16. Related governance

- [Multi-component Evidence Landscape Specification v0.2](multi_component_evidence_landscape_specification_v0.2.md)
- [Evidence Landscape Component Composition Policy v0.1](evidence_landscape_component_composition_policy_v0.1.md)
- [Evidence Landscape Versioning Policy v0.1](evidence_landscape_versioning_policy_v0.1.md)
- [Component Validation Requirements v0.1](component_validation_requirements_v0.1.md)
- [Profile Release Policy v0.1](profile_release_policy_v0.1.md)

