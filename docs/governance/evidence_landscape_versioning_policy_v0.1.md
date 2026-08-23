# Evidence Landscape Versioning Policy v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Task:** #033A  
**Version:** v0.1  
**Status:** Governance policy; no landscape release created

## 1. Purpose

This policy separates the version axes required to identify, reproduce, supersede, and validate a Multi-component Evidence Landscape without conflating source evidence, profile assembly, landscape representation, component semantics, or storage layout.

Versioning is infrastructure governance. A higher version does not indicate stronger evidence, better targets, greater confidence, therapeutic value, or scientific review status.

## 2. Landscape identity

One landscape object is identified by:

`(EnsemblID, landscape_schema_version, landscape_version, source_profile_id, source_evidence_snapshot_version)`

A landscape release is identified by a deterministic release identifier plus:

- exact landscape object universe and canonical order;
- landscape schema and landscape versions;
- source profile schema, profile, and evidence-snapshot versions;
- component set and component versions;
- state-rule, extractor, component-generator, profile-generator, and landscape-generator versions;
- partition strategy where applicable;
- input and output artifact hashes;
- lifecycle and validation status.

A deterministic identifier must not depend on wall-clock time, randomness, hostname, storage path, gene symbol, component state, evidence count, or AI judgement.

## 3. Frozen v0.2 representation identifiers

Task #033A reserves the following representation identifiers:

- `landscape_schema_version = EVIDENCE_LANDSCAPE_SCHEMA_V0.2`;
- `landscape_version = MULTI_COMPONENT_EVIDENCE_LANDSCAPE_V0.2`.

The source profile axes remain:

- `profile_schema_version = TARGET_EVIDENCE_PROFILE_MULTICOMPONENT_SCHEMA_V0.1`;
- `profile_version = TARGET_EVIDENCE_PROFILE_MULTICOMPONENT_V0.1`;
- `evidence_snapshot_version = EVIDENCE_SNAPSHOT_32C_CBFD2625F8B0CBB855DB90CBC8E2D605`.

Task #033A does not assign a landscape generator version, release identifier, artifact identifier, partition-set hash, storage reference, or lifecycle promotion. Those values require a future implementation and validated artifacts.

## 4. Independent version axes

| Axis | Governs | Must change when |
|---|---|---|
| `landscape_schema_version` | Serialized landscape fields, types, cardinalities, and constraints | Landscape serialization contract changes |
| `landscape_version` | Projection semantics, component composition, state/missingness/dependency representation, and limitations contract | Landscape meaning or projection rules change |
| `source_profile_schema_version` | Serialized source-profile contract | Source profile structure changes |
| `source_profile_version` | Source-profile component assembly semantics | Included components or profile assembly changes |
| `source_evidence_snapshot_version` | Exact source feature values, records, artifacts, and source releases | Any governed source evidence changes |
| `component_version` | Component question, feature interface, state, missingness, dependency, or interpretation boundary | Component semantics change |
| `state_rule_version` | Component-specific predicates and precedence | A state predicate or precedence changes |
| `extractor_version` | Source-record-to-feature behavior | Feature extraction behavior changes |
| `component_generator_version` | Component materialization and serialization | Component assembly behavior changes |
| `source_profile_generator_version` | Profile integration/materialization | Source profile bytes or assembly behavior changes |
| `landscape_generator_version` | Landscape projection and canonical serialization | Landscape generation behavior changes |
| `partition_strategy_version` | Physical partition assignment and ordering contract | Partition function or layout changes |

No generic project version may replace these axes. A change to one axis must not silently rewrite another.

## 5. Change-control matrix

| Change | Required action |
|---|---|
| Add, remove, or reorder a component in the source profile | New source `profile_version`, new source profile release, new landscape version or reviewed compatibility determination, and full validation |
| Change a component feature meaning, missingness rule, dependency rule, or state meaning | New `component_version`; regenerate affected profile and landscape releases |
| Change evidence values, evidence records, source release, or artifact bytes | New source `evidence_snapshot_version`; regenerate affected components, profiles, and landscapes |
| Change only landscape field names/types/cardinalities | New `landscape_schema_version`; prove projection semantics unchanged or also change landscape version |
| Change landscape composition, availability, provenance, dependency, or limitation semantics | New `landscape_version` and normally a new schema version |
| Change canonical JSON, CSV, or partition serialization without changing meaning | New landscape generator and/or schema version; regenerate and rehash affected artifacts |
| Move unchanged bytes to another immutable storage system | Preserve artifact ID, size, and SHA256; add a versioned storage reference without changing scientific versions |
| Correct any frozen byte | Create a new artifact/release identity; do not overwrite the previous frozen object |
| Documentation clarification only | New document version; record explicitly that governed data semantics and payloads are unchanged |

## 6. Relationship to Task #031

Task #031 remains `EVIDENCE_LANDSCAPE_REPRESENTATION_V0.1` with schema `EVIDENCE_LANDSCAPE_SCHEMA_V0.1` and one transcriptomic component. Multi-component v0.2 is a new projection contract over Task #032C. It does not modify, relabel, or retroactively upgrade the Task #031 artifacts.

The Task #031 lifecycle, hashes, limitations, and validation report remain historically traceable. A v0.2 release cannot inherit Task #031 validation automatically; it must pass the v0.2 validation requirements independently.

## 7. Evidence snapshot and component-set binding

The landscape release manifest must bind the exact source profile evidence snapshot and component set. A profile with the same EnsemblID but different profile version or evidence snapshot is a different landscape input.

Component identifiers and versions must be declared as an ordered set for serialization and as independent semantic modules. The ordered set is not a priority list. A component change cannot be hidden behind an unchanged landscape release identifier.

## 8. Partition and storage changes

Partition identity is physical infrastructure, not landscape identity. Moving a landscape to a different partition must not change its scientific identity when the canonical landscape content is unchanged. Changing the partition function requires a new `partition_strategy_version`, new partition artifacts, indexes, manifests, sizes, and hashes.

Large payload storage changes follow [Task #026 Provenance Artifact Governance v0.1](task026_provenance_artifact_governance_v0.1.md) and the artifact policy in [Multi-component Evidence Landscape Specification v0.2](multi_component_evidence_landscape_specification_v0.2.md). A mutable `latest` location is insufficient as the sole reference.

## 9. Lifecycle boundary

Landscape version, source profile lifecycle, and landscape release maturity are different concepts. A v0.2 version label does not imply `INTERNAL_VALIDATION`, `SCIENTIFIC_REVIEWED`, or `PUBLIC_RELEASE`.

Lifecycle promotion requires a separate recorded human governance action after validation. State counts, component completeness, evidence quantity, or byte-identical regeneration cannot by themselves promote a release.

## 10. Versioning validation checklist

- [ ] Landscape identity tuple is complete and unique.
- [ ] Source profile ID, profile schema, profile version, and evidence snapshot are exact.
- [ ] Component IDs and versions match the source profile manifest.
- [ ] State-rule, extractor, component-generator, profile-generator, and landscape-generator versions are independently recorded.
- [ ] Schema, landscape, profile, evidence-snapshot, component, generator, and partition axes are not collapsed.
- [ ] Every changed input or semantic contract triggers the required new version.
- [ ] Frozen releases are never overwritten.
- [ ] Storage migration preserves or explicitly versions artifact identity and hashes.
- [ ] No version label is interpreted as evidence quality, confidence, rank, priority, or scientific validity.

## 11. Related governance

- [Multi-component Evidence Landscape Specification v0.2](multi_component_evidence_landscape_specification_v0.2.md)
- [Evidence Landscape Component Composition Policy v0.1](evidence_landscape_component_composition_policy_v0.1.md)
- [Evidence Landscape Validation Requirements v0.1](evidence_landscape_validation_requirements_v0.1.md)
- [Profile Release Policy v0.1](profile_release_policy_v0.1.md)

