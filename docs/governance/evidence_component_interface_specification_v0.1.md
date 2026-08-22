# Evidence Component Interface Specification v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Version:** v0.1  
**Status:** Frozen governance specification

## 1. Purpose

This specification defines the universal interface by which a future evidence component may be registered, validated, and materialized within a governed Target Evidence Profile.

A component represents bounded evidence observations and their uncertainty. It does not evaluate a target. The interface therefore preserves identity, provenance, missingness, dependency, determinism, and interpretation boundaries without introducing scoring, ranking, confidence metrics, target quality, therapeutic recommendations, or runtime AI decisions.

This task defines an interface only. It does not authorize evidence retrieval, register a new source, implement a future component, or alter any Task #028, #030, or #031 artifact.

## 2. Compatibility and canonical terminology

This interface extends the ontology frozen in Task #028 and must remain compatible with the Task #030 profile universe and Task #031 evidence landscape.

| Interface term | Existing governed term | Binding rule |
|---|---|---|
| `component_id` | `component_id` | Exact equality |
| `component_version` | `component_definition_version` | These are two names for one semantic version axis; a materialized profile serializes it as `component_definition_version` |
| `schema_version` | Profile or registered component schema version | Identifies the exact schema validating the component representation |
| `source_snapshot_version` | Component contribution to `evidence_snapshot_version` | Identifies the frozen source inputs for this component; the profile evidence snapshot manifests all component source snapshots |
| `generator_version` | Component or profile materializer generator version | Identifies deterministic assembly behavior and must remain traceable independently of the extractor |

`component_version` and `component_definition_version` must never diverge within one registration or materialized artifact. The compatibility name does not create a second component version.

Component structural states and feature missingness use different controlled vocabularies and must not be conflated:

- component states: `OBSERVED`, `PARTIAL`, `CONFLICTING`, `MISSING`, `NOT_QUERIED`;
- feature missingness: `OBSERVED`, `NOT_FOUND`, `NOT_QUERIED`, `NOT_APPLICABLE`, `UNKNOWN`.

Profile lifecycle state, component lifecycle stage, component structural state, and feature missingness are four separate concepts.

## 3. Component identity contract

### 3.1 Registration identity

Every component registration must declare:

- `component_id` — stable opaque identifier, conventionally `COMP_<DOMAIN_NAME>`;
- `component_version` — semantic version of the bounded question, feature contract, missingness rules, dependency contract, state meanings, and interpretation boundary;
- `schema_version` — exact machine-readable serialization contract;
- `source_snapshot_version` — immutable identity of all source artifacts and source versions consumed by the component;
- `generator_version` — deterministic component-assembly implementation;
- `state_rule_version` — executable state predicates and precedence;
- `extractor_version` — deterministic source-record-to-feature behavior.

The required identity fields are independent version axes. They must not be replaced by one generic project version.

### 3.2 Materialized component identity

One materialized component instance is identified by:

`(EnsemblID, component_id, component_version, source_snapshot_version)`

The containing profile remains identified by:

`(EnsemblID, profile_version, evidence_snapshot_version)`

`EnsemblID` is the immutable entity binding. Gene symbols may be displayed as annotations but must not be used for identity, joins, fallback mapping, or silent repair.

### 3.3 Version-change boundaries

| Change | Required version action |
|---|---|
| Scientific question, allowed evidence types, feature meaning, missingness rule, dependency rule, state meaning, or interpretation boundary changes | New `component_version` |
| Serialized fields, types, cardinalities, or constraints change without semantic change | New `schema_version` |
| Any source record, source release, retrieval scope, artifact byte, or source-version declaration changes | New `source_snapshot_version`, and therefore a new containing profile `evidence_snapshot_version` |
| Extraction behavior changes | New `extractor_version` |
| Component assembly or deterministic serialization behavior changes | New `generator_version` |
| State predicate or precedence changes | New `state_rule_version` |

A change must never overwrite an existing frozen component artifact.

## 4. Scientific scope contract

Each component proposal must define one bounded question about available observations. Its registration must specify:

- evidence domain;
- bounded scientific question;
- unit of observation;
- accepted evidence-record types;
- required and optional source roles;
- feature contract and data types;
- explicit inclusion and exclusion boundaries;
- known limitations;
- what the component can describe;
- what it cannot establish.

Components may describe evidence availability, recorded observations, controlled missingness, structural conflicts, unresolved uncertainty, and provenance relationships.

Components must not establish or imply:

- target quality or biological importance;
- causality, efficacy, safety, or clinical benefit;
- therapeutic direction or recommendation;
- a score, ranking, priority, confidence metric, or evidence-strength measure.

Observation quantity and provenance-link quantity are audit metadata only. They are not independent votes or evaluation variables.

## 5. Feature contract

Every normalized component feature must have:

- stable `feature_id` and `feature_name`;
- governed data type and controlled values where applicable;
- exact value or a value derived by a registered deterministic extraction rule;
- controlled `missingness_status`;
- at least one resolvable provenance relationship when required by its feature contract;
- declared applicability and cardinality;
- explicit interpretation boundary.

Feature values must not be supplied by free-text judgement, manual runtime annotation, or an AI/LLM decision. A feature absent from the frozen source contract cannot be inferred from another component.

## 6. Shared component-state interface

All components use the following structural state vocabulary:

| State | Universal structural meaning |
|---|---|
| `OBSERVED` | The component-specific qualifying observation and required governed context are present under the registered predicate |
| `PARTIAL` | Assessment was attempted or records exist, but one or more required roles, fields, context, provenance, or coverage conditions are incomplete |
| `CONFLICTING` | A registered deterministic conflict predicate identifies incompatible governed records, identities, effects, or required structural conditions |
| `MISSING` | The registered assessment scope was completed, but the required qualifying component representation is absent; this is not negative evidence or biological absence |
| `NOT_QUERIED` | The registered assessment was not attempted for this entity and snapshot |

The frozen precedence is:

`CONFLICTING > OBSERVED > MISSING > PARTIAL > NOT_QUERIED`

Precedence resolves simultaneously matched structural predicates. It is not an ordinal quality scale.

Every component must supply deterministic, component-specific executable predicates and fixtures for all five states. An LLM or manual reviewer must not choose a runtime state.

## 7. Mandatory provenance interface

Every feature-to-record relationship must logically preserve:

- `feature_id`;
- `claim_id`;
- `evidence_record_id`;
- `source_id`;
- `artifact_id`;
- `dependency_id` or an explicit controlled sentinel;
- `extraction_rule_id`;
- `extractor_version`.

The source registry or release manifest must additionally resolve:

- source version;
- source snapshot version;
- artifact relative path or immutable storage reference;
- artifact SHA256 and size;
- component, schema, state-rule, and generator versions.

The governed feature-provenance key remains:

`(feature_id, evidence_record_id)`

Multiple records linked to one feature remain separate relationships. Counts or summaries must not replace record-level lineage.

## 8. Dependency interface

Every provenance relationship must carry a `dependency_id` or a controlled `NOT_APPLICABLE`/`UNKNOWN` status. A dependency record must declare its members, relationship type, dependency level, rationale, governing artifact, and version.

Absence of a known dependency must not be treated as proof of independence. `INDEPENDENT` requires affirmative, source-traceable justification. Dependent or partially dependent records must remain linked and must not be represented as independent corroboration.

The normative dependency contract is defined in [Component Dependency Model v0.1](component_dependency_model_v0.1.md).

## 9. Missingness interface

Feature-level missingness uses:

| Status | Meaning |
|---|---|
| `OBSERVED` | The governed feature value is present |
| `NOT_FOUND` | The registered source operation completed within its declared scope and the requested mapped item was not returned |
| `NOT_QUERIED` | The registered source operation was not attempted for this feature/entity/snapshot |
| `NOT_APPLICABLE` | The feature is outside the component contract for this record under a deterministic applicability rule |
| `UNKNOWN` | Retrieval, parsing, mapping, coverage, or status could not be resolved |

Missingness must be propagated exactly. `NOT_FOUND` is not negative evidence, `NOT_QUERIED` is not missing biology, `NOT_APPLICABLE` is not absence, and `UNKNOWN` must not be silently repaired.

Component-level `MISSING` is a structural state and must not be serialized as a feature missingness value.

## 10. Deterministic materialization contract

The following must determine every component byte:

`frozen input manifest + component version + schema version + source snapshot version + extractor version + state-rule version + generator version`

Identical inputs and versions must produce byte-identical outputs. Component materialization must not depend on randomness, wall-clock values, mutable network responses, manual runtime decisions, or AI/LLM judgement.

External retrieval, when separately authorized in a future task, must end before governed component materialization and must produce an immutable source snapshot with hashes and query provenance.

## 11. Current compatibility reference

The existing component maps to this interface as follows:

| Interface field | Current value |
|---|---|
| `component_id` | `COMP_TRANSCRIPTOMIC_EVIDENCE` |
| `component_version` / `component_definition_version` | `COMP_TRANSCRIPTOMIC_EVIDENCE_V0.1` |
| Profile `schema_version` | `TARGET_EVIDENCE_PROFILE_FULL_SCHEMA_V0.1` |
| `source_snapshot_version` | `TASK026_TRANSCRIPTOMIC_FEATURES_SHA256_4014469439ff14d27c451a356cf7711daa7a5331c58326eced2cf96edb298844` |
| `state_rule_version` | `STATE_RULE_REGISTRY_V0.1` |
| `extractor_version` | `TRANSCRIPTOMIC_FEATURE_EXTRACTOR_V0.1` |
| Profile `generator_version` | `FULL_PROFILE_MATERIALIZER_V0.1` |

Task #031 represents component availability separately as `PRESENT_IN_SOURCE_PROFILE`, preserves the five-state schema, retains feature missingness, and projects `SHARED_DATASET / DEPENDENT` relationships without interpreting them.

This compatibility mapping does not retroactively change Task #030 or Task #031 serialization.

## 12. Interface conformance checklist

- [ ] Component identity and all version axes are declared and distinct.
- [ ] `component_version` binds exactly to serialized `component_definition_version`.
- [ ] The immutable entity binding is `EnsemblID` only.
- [ ] One bounded observation question and its limitations are explicit.
- [ ] Feature names, types, values, applicability, and missingness are deterministic.
- [ ] All five component states have executable predicates and boundary fixtures.
- [ ] Every required provenance field resolves to a frozen record and artifact.
- [ ] Dependency relationships and unknown dependency status are preserved.
- [ ] Missingness values remain distinct and unchanged.
- [ ] Identical frozen inputs regenerate byte-identical artifacts.
- [ ] No scoring, ranking, confidence metric, target-quality field, recommendation, or runtime AI decision exists.
- [ ] Registration, validation, materialization, and profile-release lifecycle records remain separate.

## 13. Related specifications

- [Component Registration Policy v0.1](component_registration_policy_v0.1.md)
- [Component Validation Requirements v0.1](component_validation_requirements_v0.1.md)
- [Component Dependency Model v0.1](component_dependency_model_v0.1.md)
- [Target Evidence Profile Governance v0.1](target_evidence_profile_governance_v0.1.md)
- [Profile Component Model v0.1](profile_component_model_v0.1.md)

