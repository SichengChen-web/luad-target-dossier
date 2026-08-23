# Transparent Prioritization Prototype Specification v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Task:** #035A  
**Version:** v0.1  
**Status:** Governance and schema specification; no category assignments or target outputs authorized

## 1. Purpose and scientific boundary

This specification defines a transparent categorical representation derived from a governed Evidence Summary. The representation exposes how a deterministic rule catalog maps structural component-state patterns to non-ordinal routing categories. It is a prototype for auditable rule tracing, not a scoring model, target ranking, biological assessment, or therapeutic decision system.

This task does not generate category assignments for project targets. It does not retrieve evidence, modify Evidence Summaries, estimate confidence or probability, predict drug success, select or recommend targets, or perform biological interpretation. Runtime AI or LLM decisions are prohibited.

## 2. Relationship to Evidence Summary

The required one-way relationship is:

```text
governed Evidence Summary
            ↓
Transparent Prioritization Representation
```

The Evidence Summary remains canonical. A prioritization representation is a deterministic categorical view of the exact component states already present in one frozen summary. It must retain the source summary identity and content SHA256, and it must not reconstruct evidence, alter component states, fill missingness, resolve conflicts, or combine summaries.

The frozen source identifiers are `evidence_summary_schema_version = EVIDENCE_SUMMARY_SCHEMA_V0.1` and `evidence_summary_version = EVIDENCE_AGGREGATION_REPRESENTATION_V0.1`.

The representation lineage is:

```text
Prioritization representation
            ↓
source Evidence Summary identity
            ↓
preserved component-state snapshot
            ↓
explicit rule identifiers and rule trace
            ↓
one non-ordinal category label
```

## 3. Identity

One representation is identified by:

`(EnsemblID, prioritization_output_schema_version, prioritization_representation_version, source_evidence_summary_id, rule_catalog_version)`

The v0.1 identifiers are:

- `prioritization_output_schema_version = PRIORITIZATION_OUTPUT_SCHEMA_V0.1`;
- `prioritization_representation_version = TRANSPARENT_PRIORITIZATION_PROTOTYPE_V0.1`;
- `rule_catalog_version = PRIORITIZATION_RULE_CATALOG_V0.1`.

A deterministic `prioritization_representation_id` may encode this tuple. It must not depend on gene symbol, row position, evidence quantity, wall-clock time, randomness, mutable network state, manual judgement, or an AI/LLM decision.

## 4. Non-ordinal categories

The controlled categories are:

- `CATEGORY_A` — structural pattern in which all registered source-summary components are `OBSERVED`;
- `CATEGORY_B` — structural pattern combining at least one `OBSERVED` component with at least one `MISSING` or `NOT_QUERIED` component, with no `PARTIAL` or `CONFLICTING` component;
- `CATEGORY_C` — structural pattern containing at least one `PARTIAL` or `CONFLICTING` component;
- `CATEGORY_UNASSIGNED` — structural pattern in which every component is `MISSING` or `NOT_QUERIED`, or no reviewed v0.1 assignment rule applies.

The letters are opaque stable identifiers. They are not grades, tiers, ranks, priorities, or ordered levels. No category is better, worse, more important, more promising, more actionable, or more likely to succeed than another. User interfaces and downstream artifacts must not sort these labels as a target order.

The category predicates are frozen in [Prioritization Rule Catalog v0.1](prioritization_rule_catalog_v0.1.md). They describe structural availability and review routing only. They do not establish biological truth.

## 5. Required assignment representation

Every future category assignment must contain:

- immutable `EnsemblID`;
- deterministic representation identity and version axes;
- exact source Evidence Summary identity and content SHA256;
- exact ordered source component IDs, versions, and states;
- exact source summary and component `limitation_identifiers`;
- one controlled category label;
- the stable identifier of the rule that assigned the category;
- an ordered rule trace covering every v0.1 catalog rule;
- the rule-catalog and generator versions.

The rule trace must record, for each evaluated rule:

- trace-step ordinal;
- `rule_id`;
- executable predicate identifier;
- boolean predicate result;
- exact JSON-pointer input references and observed controlled values.

Exactly one rule must evaluate `true` for a structurally valid v0.1 input. A trace is audit lineage, not an explanation generated from free text.

## 6. Preserved source fields

The representation must copy without reinterpretation:

- `EnsemblID`;
- `evidence_summary_id`;
- Evidence Summary schema and representation versions;
- source Evidence Summary content SHA256;
- component IDs, component versions, and exact component states;
- summary-level and component-level limitation identifiers.

Component states remain the controlled labels `OBSERVED`, `PARTIAL`, `CONFLICTING`, `MISSING`, and `NOT_QUERIED`. The prioritization representation must not alter these states or create an overall evidence state.

Feature values, missingness records, dependency records, and provenance remain in the source Evidence Summary. The representation may reference but must not rewrite them.

## 7. Limitations

Limitations are copied for audit and remain scoped to their source summary or component. They are not category inputs in v0.1 and must not become penalties, weights, exclusions, confidence adjustments, or inferred negative evidence.

A category does not resolve a limitation. Removing or changing a limitation requires a separately governed source-summary change.

## 8. Deterministic rule boundary

Rules operate only on the exact ordered component-state snapshot from one frozen Evidence Summary. They must not use:

- gene symbols or target names;
- feature quantities or record counts;
- source-native scores;
- literature or domain knowledge;
- target fame or perceived novelty;
- limitation counts;
- manually authored target exceptions;
- mutable external data;
- runtime AI/LLM judgement.

Identical source-summary bytes, rule catalog, schema, and generator version must yield a byte-identical representation.

## 9. Independent version axes

| Axis | Governs |
|---|---|
| `prioritization_output_schema_version` | Serialized fields, types, cardinalities, and constraints |
| `prioritization_representation_version` | Category-assignment representation semantics |
| `rule_catalog_version` | Category predicates, category mapping, and trace order |
| `prioritization_generator_version` | Deterministic evaluation and serialization behavior |
| `source_evidence_summary_schema_version` | Source Evidence Summary serialization |
| `source_evidence_summary_version` | Source summary projection semantics |
| `source_evidence_snapshot_version` | Evidence snapshot inherited through the source summary |

These axes must not be collapsed. A version change never implies a better category, stronger evidence, or scientific validation.

## 10. Explicitly prohibited fields and outputs

The [Prioritization Output schema v0.1](../../schemas/prioritization_output_schema_v0.1.json) and every future materializer must recursively reject:

- `score`;
- `ranking`;
- `rank`;
- `priority_score`;
- `confidence`;
- `probability`;
- `success_prediction`;
- `recommendation`;
- `target_quality`;
- `evidence_strength`.

Aliases or hidden structures with the same function are also prohibited. Task #035A creates no target assignments, output registry, target selection, ordered list, recommendation, or biological conclusion.

## 11. Interpretation boundary

A category supports only this statement:

> Under the frozen v0.1 structural rule catalog, the preserved source component-state pattern matched the recorded predicate.

It does not support statements about causality, importance, tractability, druggability, safety, efficacy, clinical relevance, development feasibility, target quality, target order, or probability of success.

## 12. Validation and authorization boundary

Schema and future materialization validation follow [Prioritization Validation Requirements v0.1](prioritization_validation_requirements_v0.1.md). Creating this governance and schema does not authorize full-universe category assignment. A separate task must freeze the evaluator, materialize outputs, validate every trace, and preserve source hashes before any categorical artifact exists.

## 13. Related governance

- [Prioritization Rule Catalog v0.1](prioritization_rule_catalog_v0.1.md)
- [Prioritization Validation Requirements v0.1](prioritization_validation_requirements_v0.1.md)
- [Evidence Aggregation Representation Specification v0.1](evidence_aggregation_representation_specification_v0.1.md)
- [Evidence Summary Validation Requirements v0.1](evidence_summary_validation_requirements_v0.1.md)
