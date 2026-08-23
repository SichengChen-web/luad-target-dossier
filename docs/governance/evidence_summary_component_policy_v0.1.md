# Evidence Summary Component Policy v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Task:** #034A  
**Version:** v0.1  
**Status:** Governance policy; no summary payload authorized or generated

## 1. Purpose

This policy defines how a component already present in one governed Multi-component Evidence Landscape is represented in an Evidence Summary. Component summarization is lossless structural indexing of state, feature missingness, dependency references, and limitations. It is not evidence evaluation or cross-component aggregation.

## 2. Source boundary

Each component summary must originate from exactly one component projection in exactly one source landscape. A generator must not select components from separate landscapes, rebuild components from raw evidence, retrieve newer source data, or join by gene symbol.

For the current source landscape the ordered component set is:

1. `COMP_TRANSCRIPTOMIC_EVIDENCE_V0.1`;
2. `COMP_DISEASE_ASSOCIATION_V0.1`.

This order is deterministic serialization metadata only. It is not a rank or priority. A future summary materializer must copy exactly the component set and order present in its frozen source landscape.

## 3. Component identity

Every component summary must retain:

- `component_id`;
- `component_version`;
- source component-record ID;
- source component content SHA256;
- exact source component state;
- ordered feature-missingness references;
- ordered dependency summaries;
- applicable limitation identifiers.

Component IDs and versions must not be normalized into a generic component label. Missing identity or version metadata is a validation failure, not a field to infer.

## 4. Component state

The only component states are:

- `OBSERVED`;
- `PARTIAL`;
- `CONFLICTING`;
- `MISSING`;
- `NOT_QUERIED`.

The summary copies the exact state from the landscape. States are domain-specific, non-ordinal labels. A summary must not create an overall state, compare component states, apply cross-component precedence, or interpret `OBSERVED` as stronger evidence.

## 5. Feature-missingness representation

Every source feature remains individually addressable through a `feature_missingness` entry containing:

- stable `feature_id`;
- exact `missingness_status`;
- source component-record ID;
- source feature-value SHA256 when the landscape provides one.

Allowed missingness values are:

- `OBSERVED`;
- `NOT_FOUND`;
- `NOT_QUERIED`;
- `NOT_APPLICABLE`;
- `UNKNOWN`.

An ordered list of per-feature entries is required. A count or percentage cannot replace it. The summary must not convert `NOT_FOUND` into negative evidence, `NOT_QUERIED` into biological absence, `NOT_APPLICABLE` into evidence against the entity, or `UNKNOWN` into a guessed value.

## 6. Component composition rules

Within each component summary:

1. feature entries follow source landscape order;
2. dependency summaries follow the source feature/provenance order;
3. limitation identifiers follow source order;
4. each feature and dependency reference remains in its component namespace;
5. the source component state and missingness values remain unchanged.

Feature names shared across components do not imply equivalent meaning and must not be merged. Record quantity, feature completeness, or component presence must not be converted into evidence strength or target quality.

## 7. Cross-component boundary

Evidence Summary v0.1 permits an ordered array of independent component summaries. It prohibits:

- overall or consensus component states;
- cross-component voting;
- best/worst component selection;
- state precedence across components;
- missingness repair across components;
- merging dependency records solely because identifiers resemble one another;
- target-level conclusions derived from component combinations.

Any future cross-component dependency must already be represented by a governed source dependency relationship. It cannot be inferred during summarization.

## 8. Prohibitions

A component summary must not contain or imply a score, ranking, priority, confidence, recommendation, target quality, evidence strength, biological importance, causal conclusion, therapeutic interpretation, or runtime AI decision.

## 9. Validation checklist

- [ ] Source landscape and component identities resolve exactly.
- [ ] Component ID and version are unchanged.
- [ ] Source component record and content hash are preserved.
- [ ] Component state equals the landscape state.
- [ ] Every source feature has one ordered missingness entry.
- [ ] Every missingness value equals the landscape value.
- [ ] Dependency summaries remain attached to the correct component and feature.
- [ ] Limitation identifiers remain explicit.
- [ ] No cross-component aggregation or prohibited field exists.
- [ ] Regeneration from identical frozen inputs is byte-identical.

## 10. Related governance

- [Evidence Aggregation Representation Specification v0.1](evidence_aggregation_representation_specification_v0.1.md)
- [Evidence Summary Dependency Policy v0.1](evidence_summary_dependency_policy_v0.1.md)
- [Evidence Summary Validation Requirements v0.1](evidence_summary_validation_requirements_v0.1.md)
- [Evidence Landscape Component Composition Policy v0.1](evidence_landscape_component_composition_policy_v0.1.md)

