# Evidence Landscape Component Composition Policy v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Task:** #033A  
**Version:** v0.1  
**Status:** Governance policy; no component or landscape materialization authorized

## 1. Purpose

This policy governs how multiple registered evidence components may be projected from one frozen Target Evidence Profile into one Multi-component Evidence Landscape. Composition is structural organization only. It does not aggregate, compare, weigh, evaluate, or interpret evidence.

The policy is compatible with [Target Evidence Profile Governance v0.1](target_evidence_profile_governance_v0.1.md), [Evidence Component Interface Specification v0.1](evidence_component_interface_specification_v0.1.md), and the Task #032C [profile manifest](../../outputs/evidence_profile_integration_v0.1/profile_manifest.json).

## 2. Composition unit and source boundary

The composition unit is one complete source profile identified by immutable EnsemblID and its frozen profile identity. A landscape must consume all component objects from that one profile and must not assemble components by querying independent tables at runtime.

Forbidden source combinations include:

- components from different EnsemblIDs;
- components from different profile versions;
- components from different evidence-snapshot versions;
- a newer component silently inserted into an older source profile;
- symbol-based component matching;
- component selection based on evidence state, record count, perceived importance, or therapeutic interest.

If a source profile, component, or hash cannot be resolved exactly, composition must stop for that release rather than repair the record silently.

## 3. Current registered component set

The frozen Task #032C component order is:

1. `COMP_TRANSCRIPTOMIC_EVIDENCE_V0.1`;
2. `COMP_DISEASE_ASSOCIATION_V0.1`.

Every one of the 29,606 Task #032C profiles contains both components. A v0.2 landscape projection of that release must therefore contain exactly two component projections per EnsemblID. Component order is inherited for deterministic serialization only and does not express priority.

A future component cannot enter the landscape until it is registered, validated, materialized into a new governed profile version, and included in that source profile's component set. This policy does not authorize future components.

## 4. Component availability

Availability answers only whether a declared component object is present and resolvable in the exact source profile. For the current Task #032C source, the allowed materialized value is:

`PRESENT_IN_SOURCE_PROFILE`

Absence of either expected component is a source-profile or integration validation failure. The landscape must not synthesize a component and label it `MISSING` or `NOT_QUERIED`; those are component states determined inside a registered component contract, not substitutes for an absent component object.

Future profile versions with optional components require a separately versioned availability vocabulary and explicit profile contract. Task #033A does not define such optionality.

## 5. Component identity preservation

Each landscape component projection must retain:

- `component_id`;
- `component_version` and compatible `component_definition_version`;
- exact source component-record or source profile-component identity;
- source component content hash;
- component schema and generator versions where supplied;
- feature-schema, extractor, and state-rule versions where supplied;
- source snapshot or evidence-snapshot version;
- source artifact reference.

The landscape must not create a generic component version that hides component-specific axes. Missing version metadata must fail validation or remain an explicit governed unresolved condition; it must not be inferred by an LLM or copied from another component.

## 6. Feature composition

Features remain inside their source component namespace. For every source feature, the landscape must preserve:

- `component_id`;
- `feature_id` and feature name;
- exact `missingness_status`;
- source feature reference and source feature-value hash where available;
- every evidence-record and dependency relationship required by the landscape schema.

The landscape may omit the full feature value only when it retains a deterministic, hash-validated source feature reference and the schema explicitly defines the landscape as a structural projection. Omission must not prevent lineage validation. The landscape must never transform, harmonize, compare, or overwrite feature values during composition.

Feature names that resemble one another across components are not join keys and do not imply equivalent meaning. Cross-component feature merging is prohibited.

## 7. State composition

Every component retains its exact source state from:

- `OBSERVED`;
- `PARTIAL`;
- `CONFLICTING`;
- `MISSING`;
- `NOT_QUERIED`.

The landscape may contain multiple different states for one EnsemblID because they describe different evidence domains. It must not generate:

- an overall state;
- a majority state;
- a best or worst state;
- a state precedence across components;
- a target-level conflict inferred from differing component states.

State precedence remains internal to each component's executable rules. Cross-component order has no scientific meaning.

## 8. Missingness composition

Feature missingness remains component- and feature-specific:

- `OBSERVED`;
- `NOT_FOUND`;
- `NOT_QUERIED`;
- `NOT_APPLICABLE`;
- `UNKNOWN`.

One component must not fill, reinterpret, or negate another component's missingness. In particular:

- `NOT_FOUND` is not negative evidence;
- `NOT_QUERIED` is not biological absence;
- `NOT_APPLICABLE` is not evidence against a target;
- `UNKNOWN` is not repaired from another component;
- component state `MISSING` is not a feature missingness value.

## 9. Provenance and dependency composition

Every source feature-to-record relationship must remain a distinct landscape relationship. The cross-component relationship key is:

`(component_id, feature_id, evidence_record_id)`

This key supplements but does not replace each component's governed `(feature_id, evidence_record_id)` key. It prevents namespace collision when relationships from multiple components share a landscape artifact.

Each relationship must retain or resolve claim, record, source, artifact, extraction-rule, extractor-version, source component, and source profile lineage. Dependency IDs, relationship types, and levels remain attached to their member evidence records.

Composition must not:

- collapse multiple relationships into a count;
- deduplicate records across components solely because identifiers look similar;
- treat different source IDs as proof of independence;
- erase shared dataset or source origin;
- convert `NOT_APPLICABLE` or `UNKNOWN` into `INDEPENDENT`;
- use relationship quantity as confidence or evidence strength.

Cross-component dependency can be asserted only when an existing governed dependency record supports it. No runtime inference is permitted.

## 10. Limitations and historical boundaries

Limitations must be copied only when their declared scope applies to the current source profile and component version. A historical limitation is not automatically current.

Specifically, Task #031 limitation `LIM_ONLY_TRANSCRIPTOMIC_COMPONENT` describes the Task #030 single-component source and must not be presented as a limitation of the Task #032C two-component source. The v0.2 landscape must instead manifest current component-specific and release-specific limitations without rewriting Task #031.

## 11. Deterministic ordering

The global landscape order is Task #032C `universe_ordinal`. Within each landscape:

1. components follow the exact Task #032C source component order;
2. features follow their source component order;
3. provenance/dependency relationships follow the source canonical order or a separately frozen lossless order rule;
4. limitation IDs use a frozen deterministic order.

Ordering must not depend on component state, missingness, record count, gene symbol, worker completion time, or evidence content.

## 12. Composition validation checklist

- [ ] One source profile resolves for each immutable EnsemblID.
- [ ] Source profile identity, content hash, and evidence snapshot match the frozen manifest.
- [ ] Exactly the source component set is represented once per landscape.
- [ ] Component order and versions match the source profile.
- [ ] Every component state is unchanged.
- [ ] Every feature missingness value is unchanged.
- [ ] Every required feature/record relationship remains present and unique.
- [ ] Dependency types and levels remain attached to the correct evidence records.
- [ ] No cross-component state, feature, evidence, or dependency aggregation occurs.
- [ ] Historical limitations are not misapplied to the current source release.
- [ ] No score, ranking, priority, target selection, recommendation, interpretation, or runtime AI decision exists.

## 13. Related governance

- [Multi-component Evidence Landscape Specification v0.2](multi_component_evidence_landscape_specification_v0.2.md)
- [Evidence Landscape Versioning Policy v0.1](evidence_landscape_versioning_policy_v0.1.md)
- [Evidence Landscape Validation Requirements v0.1](evidence_landscape_validation_requirements_v0.1.md)
- [Component Dependency Model v0.1](component_dependency_model_v0.1.md)

