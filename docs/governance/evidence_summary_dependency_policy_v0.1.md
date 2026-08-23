# Evidence Summary Dependency Policy v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Task:** #034A  
**Version:** v0.1  
**Status:** Governance policy; no dependency summary payload authorized or generated

## 1. Purpose

This policy governs the lossless representation of evidence dependency relationships in an Evidence Summary. Dependency metadata prevents records with shared origins from appearing as independent support. It is lineage context, not a confidence adjustment or evidence metric.

## 2. Relationship unit

The dependency-summary unit is one source landscape provenance relationship identified within a component by:

`(component_id, feature_id, evidence_record_id)`

Each unit must retain:

- `component_id` and `component_version`;
- `feature_id`;
- `evidence_record_id`;
- `dependency_id` or governed sentinel;
- ordered `dependency_relationships` entries;
- source-native artifact reference.

No relationship may be replaced by a count, digest alone, or a component-level label.

## 3. Ordered relationship representation

One evidence relationship may have more than one dependency relationship. Each pair must remain a separate ordered object:

```json
{
  "dependency_relationships": [
    {
      "relationship_type": "SAME_SOURCE",
      "dependency_level": "DEPENDENT"
    },
    {
      "relationship_type": "SHARED_DATASET",
      "dependency_level": "DEPENDENT"
    }
  ]
}
```

The array must preserve source order. `SAME_SOURCE` and `SHARED_DATASET` must not be collapsed into a single value, a boolean, or a relationship count.

## 4. Controlled relationship semantics

The governed type/level pairs are:

| `relationship_type` | Required `dependency_level` |
|---|---|
| `SAME_SOURCE` | `DEPENDENT` |
| `SHARED_DATASET` | `DEPENDENT` |
| `PARTIAL` | `PARTIALLY_DEPENDENT` |
| `UNKNOWN` | `UNKNOWN` |
| `INDEPENDENT` | `INDEPENDENT` |
| `NOT_APPLICABLE` | `NOT_APPLICABLE` |

`INDEPENDENT` is permitted only when the source landscape contains affirmative governed support. Missing dependency metadata, a different source ID, or absence of a known link must not default to independence. `NOT_APPLICABLE` must not be converted to independence.

## 5. Artifact identity and namespace

Every dependency summary must retain the evidence relationship's artifact reference:

- source-native `artifact_id` preserved byte-for-byte;
- source-native `artifact_namespace` stored separately;
- exact artifact SHA256;
- immutable storage reference when the source landscape supplies one.

Artifact namespaces are not restricted to `ART`. Examples such as `INV` remain valid when present in the source. A summary must never rewrite a source identifier to make it resemble a project-local identifier.

## 6. Dependency preservation rules

The summary generator must:

1. copy every source dependency unit once;
2. retain all ordered type/level pairs;
3. retain the source evidence-record and feature association;
4. preserve explicit unknown and not-applicable states;
5. preserve cross-component dependency references only when already governed by the source;
6. reconcile source and summary relationship cardinality exactly.

The generator must not infer new dependencies, resolve uncertainty, deduplicate relationships across components, or treat multiple dependent records as independent votes.

## 7. Quantity and interpretation boundary

Relationship counts may appear only in release-level validation or reconciliation metadata. They must not be stored as a target-level feature, confidence measure, evidence-strength measure, score, rank, or priority.

Dependency does not determine whether an observation is true, important, causal, actionable, safe, or therapeutically useful. It records structural non-independence only.

## 8. Validation checklist

- [ ] Every source dependency unit has one summary unit.
- [ ] `(component_id, feature_id, evidence_record_id)` remains unique within the summary.
- [ ] Ordered type/level arrays are byte-order equivalent to the source representation.
- [ ] Every type/level pair is controlled and compatible.
- [ ] Multiple relationship types remain separate.
- [ ] Artifact IDs are unchanged.
- [ ] Artifact namespaces and SHA256 hashes are present and unchanged.
- [ ] Unknown and not-applicable values remain explicit.
- [ ] No count replaces record-level lineage.
- [ ] No confidence, evidence strength, scoring, ranking, or interpretation field exists.

## 9. Related governance

- [Evidence Aggregation Representation Specification v0.1](evidence_aggregation_representation_specification_v0.1.md)
- [Evidence Summary Component Policy v0.1](evidence_summary_component_policy_v0.1.md)
- [Evidence Summary Validation Requirements v0.1](evidence_summary_validation_requirements_v0.1.md)
- [Component Dependency Model v0.1](component_dependency_model_v0.1.md)

