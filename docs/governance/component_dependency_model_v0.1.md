# Component Dependency Model v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Version:** v0.1  
**Status:** Frozen governance specification

## 1. Purpose

This specification defines how evidence-record dependencies are represented within and across evidence components. Its purpose is to preserve shared origin, overlap, partial dependence, unknown dependence, and affirmative independence without turning record quantity into an evaluative measure.

Dependency representation is structural provenance. It must not produce scoring, ranking, confidence metrics, target quality, therapeutic recommendations, biological interpretation, or runtime AI decisions.

## 2. Scientific principle

Multiple evidence records are not automatically independent observations. Records may share a source, dataset, cohort, analysis, upstream artifact, or derivation path. Treating dependent rows as independent can inflate apparent convergence.

Therefore:

`record multiplicity ≠ independent corroboration`

Dependency information must remain attached to record-level lineage. It must not be replaced by a count, weight, confidence value, or collapsed summary.

## 3. Dependency object

A governed dependency object must contain:

- `dependency_id` — stable relationship-group identifier;
- `relationship_type` — controlled description of the shared or assessed relationship;
- `dependency_level` — controlled structural classification;
- `member_evidence_record_ids` — ordered or canonically sorted record members;
- `member_source_ids` — source entities represented by the members;
- `component_ids` — components in which the members occur;
- `rationale_code` — controlled reason for the classification;
- `governing_artifact_id` and artifact SHA256;
- `dependency_model_version`;
- `review_status`;
- explicit limitations or uncertainty.

Every member evidence record must resolve through the provenance registry. A dependency object must not contain a gene-symbol-based identity repair.

## 4. Controlled relationship types

The universal interface permits:

| `relationship_type` | Structural meaning |
|---|---|
| `SAME_SOURCE` | Records originate from the same governed source entity or source record family |
| `SHARED_DATASET` | Records use the same underlying dataset, even if analyses or claims differ |
| `PARTIAL` | The registered evidence establishes partial overlap or dependence but not complete shared origin |
| `UNKNOWN` | Available provenance cannot establish whether the records are dependent or independent |
| `INDEPENDENT` | Affirmative source-traceable evidence establishes independence under the registered component definition |
| `NOT_APPLICABLE` | No inter-record dependency relationship is applicable to this provenance relationship; this is not proof of independence |

A future component may request a more specific subtype only through a new reviewed dependency-model version. It must map losslessly to one of these universal types or document why the interface itself must be revised.

## 5. Controlled dependency levels

| `dependency_level` | Meaning |
|---|---|
| `DEPENDENT` | The records share a governed origin sufficient to prohibit treatment as independent observations |
| `PARTIALLY_DEPENDENT` | Some origin or information is shared and must remain explicit |
| `UNKNOWN` | Independence cannot be determined from the frozen provenance |
| `INDEPENDENT` | Independence is affirmatively documented within the registered scope |
| `NOT_APPLICABLE` | No dependency classification applies to this single relationship; no independence claim is made |

Expected mappings include:

- `SAME_SOURCE` → `DEPENDENT`;
- `SHARED_DATASET` → `DEPENDENT`;
- `PARTIAL` → `PARTIALLY_DEPENDENT`;
- `UNKNOWN` → `UNKNOWN`;
- `INDEPENDENT` → `INDEPENDENT`;
- `NOT_APPLICABLE` → `NOT_APPLICABLE`.

Any exception requires an explicit reviewed rule and a new dependency-model version.

## 6. Record-level representation

Every feature-to-record provenance relationship retains:

- `feature_id`;
- `evidence_record_id`;
- `dependency_id` or controlled sentinel;
- source and artifact lineage required to resolve the dependency object.

The feature-provenance key remains `(feature_id, evidence_record_id)`. `dependency_id` does not replace either key field.

One `dependency_id` may connect multiple evidence records and multiple features. Repetition of the dependency identifier is required lineage, not duplicate evidence and not a vote.

## 7. `NOT_APPLICABLE` and `UNKNOWN` boundaries

### 7.1 `NOT_APPLICABLE`

`NOT_APPLICABLE` means that no inter-record dependency object applies to that specific provenance relationship under the registered model. It must not be rewritten as `INDEPENDENT`.

Task #031 correctly preserves `NOT_APPLICABLE` as an explicitly non-linked dependency-reference status.

### 7.2 `UNKNOWN`

`UNKNOWN` means the frozen provenance is insufficient to determine dependence. It is a substantive uncertainty state and must be propagated to profiles, landscapes, and validation reports.

Unknown dependence must not default to independence or be omitted from a dependency graph.

## 8. Independence requirements

`INDEPENDENT` may be assigned only when the registration defines independence for the evidence type and frozen records demonstrate it. The record must preserve:

- assessed dimensions of independence;
- source and dataset identifiers;
- cohort or sample-overlap information where applicable;
- analysis and artifact lineage;
- deterministic rule or reviewed source fact establishing the classification;
- limitations of the independence claim.

Different database rows, identifiers, publications, or claims do not by themselves establish independence.

## 9. Within-component and cross-component dependencies

### 9.1 Within one component

All records sharing a dataset, source family, cohort, or upstream artifact must retain a common dependency object where the registered model requires it.

### 9.2 Across components

If two components consume records derived from the same upstream evidence, the dependency relationship must cross component boundaries. Component separation must not erase shared origin.

Cross-component dependency representation does not authorize component-state aggregation or profile-level voting.

### 9.3 Current transcriptomic component

Task #028 defines the current `TRANSCRIPT_PRIMARY` and `TRANSCRIPT_ROBUSTNESS` roles as sharing the same TCGA-LUAD dataset. Their governed relationship is:

- `relationship_type = SHARED_DATASET`;
- `dependency_level = DEPENDENT`.

Task #031 preserves each `DEP_*` identifier with those semantics and preserves `NOT_APPLICABLE` separately. This specification does not alter those frozen relationships.

## 10. Dependency graph contract

A dependency graph must preserve:

- record nodes identified by `evidence_record_id`;
- optional feature, claim, source, artifact, and component nodes;
- dependency-group nodes identified by `dependency_id`;
- typed membership edges;
- relationship type and dependency level;
- artifact and version provenance;
- unresolved and not-applicable statuses.

Graph traversal may describe connectivity and lineage. It must not compute target quality, confidence, evidence strength, priority, or therapeutic conclusions.

## 11. Validation requirements

Validate:

- every dependency member resolves to one frozen evidence record;
- no duplicate member exists within a dependency group;
- every dependency reference resolves to its group or controlled sentinel;
- relationship type and dependency level are compatible;
- same-source and shared-dataset records remain dependent;
- partial and unknown relationships remain explicit;
- `NOT_APPLICABLE` never becomes `INDEPENDENT`;
- independence has affirmative source-traceable support;
- profile and landscape projections preserve exact dependency references;
- deterministic regeneration is byte-identical;
- counts are labelled as audit reconciliation only;
- no dependent record is presented as an independent vote.

Required boundary fixtures cover:

1. `SAME_SOURCE / DEPENDENT`;
2. `SHARED_DATASET / DEPENDENT`;
3. `PARTIAL / PARTIALLY_DEPENDENT`;
4. `UNKNOWN / UNKNOWN`;
5. affirmatively documented `INDEPENDENT / INDEPENDENT`;
6. `NOT_APPLICABLE / NOT_APPLICABLE`;
7. invalid type-level combinations;
8. missing members, duplicate members, and unresolved foreign keys.

## 12. Dependency governance checklist

- [ ] Dependency objects have stable IDs and versions.
- [ ] All members and source/artifact lineage resolve.
- [ ] Type and level use the controlled vocabulary.
- [ ] Partial and unknown relationships remain explicit.
- [ ] `NOT_APPLICABLE` is not treated as independence.
- [ ] Independence is affirmatively justified.
- [ ] Within- and cross-component shared origin is retained.
- [ ] Record multiplicity is not interpreted as independent corroboration.
- [ ] Full relationship structure is preserved in profile and landscape artifacts.
- [ ] No score, rank, confidence metric, target-quality field, recommendation, biological interpretation, or runtime AI decision is generated.

## 13. Related specifications

- [Evidence Component Interface Specification v0.1](evidence_component_interface_specification_v0.1.md)
- [Component Registration Policy v0.1](component_registration_policy_v0.1.md)
- [Component Validation Requirements v0.1](component_validation_requirements_v0.1.md)
- [Profile Component Model v0.1](profile_component_model_v0.1.md)

