# Case Study Selection Framework v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Task:** #036A  
**Version:** v0.1  
**Status:** Governance and schema specification; no case selections authorized or generated

## 1. Purpose and boundary

This framework defines transparent selection of representative structural case patterns for scientific presentation. A case study is selected because its frozen representation exemplifies a governed evidence-structure pattern, not because the target is better, more important, more actionable, or more likely to succeed.

This task creates no case selections. It does not rank targets, identify optimal targets, recommend targets, claim biological importance, perform therapeutic interpretation, retrieve evidence, modify prioritization outputs, use gene symbols, or use external knowledge. Runtime AI or LLM decisions are prohibited.

## 2. Relationship to the source representation

The required one-way relationship is:

```text
frozen Transparent Prioritization Representation
                        ↓
          Representative Case Selection
```

The source prioritization representation remains canonical. A case-selection record is a presentation-routing view that preserves source identity, source Evidence Summary identity, rule traces, component states, and limitations. It must not rewrite the source category, component states, limitations, or rule results.

The frozen source identifiers are `prioritization_output_schema_version = PRIORITIZATION_OUTPUT_SCHEMA_V0.1` and `prioritization_representation_version = TRANSPARENT_PRIORITIZATION_PROTOTYPE_V0.1`.

## 3. Case-selection identity

One selected case is identified by:

`(EnsemblID, case_selection_schema_version, case_selection_framework_version, case_category, source_prioritization_representation_id, case_rule_catalog_version)`

The v0.1 identifiers are:

- `case_selection_schema_version = CASE_STUDY_SELECTION_SCHEMA_V0.1`;
- `case_selection_framework_version = CASE_STUDY_SELECTION_FRAMEWORK_V0.1`;
- `case_rule_catalog_version = CASE_STUDY_SELECTION_RULE_CATALOG_V0.1`.

A deterministic `case_selection_id` may encode this tuple. It must not depend on gene symbol, target name, manual judgement, wall-clock time, mutable network state, or an AI/LLM decision.

## 4. Non-ordinal case categories

The controlled presentation patterns are:

- `CASE_COMPLETE_PATTERN` — every preserved component state is `OBSERVED`;
- `CASE_PARTIAL_PATTERN` — no component is `CONFLICTING`, and the state pattern contains either `PARTIAL` or a mixture of `OBSERVED` with `MISSING`/`NOT_QUERIED`;
- `CASE_CONFLICT_PATTERN` — at least one preserved component state is `CONFLICTING`;
- `CASE_LIMITATION_PATTERN` — at least one summary-level or component-level limitation identifier is present.

These categories are independent presentation lenses and may overlap. They are not stages, tiers, grades, ranks, or priorities. `CASE_COMPLETE_PATTERN` does not mean biologically complete, valid, actionable, or favorable. `CASE_CONFLICT_PATTERN` does not mean the target is unsuitable. `CASE_LIMITATION_PATTERN` does not apply a penalty.

The category contract is explicitly non-ordinal.

Eligibility predicates are frozen in [Case Study Selection Rule Catalog v0.1](case_study_selection_rule_catalog_v0.1.md).

## 5. Deterministic representative selection

For a future authorized materialization, v0.1 defines one presentation slot per case category. Selection proceeds independently within each category:

1. evaluate all four case predicates for every frozen source representation;
2. form the eligible pool for the category without biological filtering;
3. calculate a category-salted deterministic token as SHA256 over canonical JSON containing `case_selection_framework_version`, `case_category`, immutable `EnsemblID`, source prioritization representation ID, and source representation content SHA256;
4. select the eligible record with the lexicographically smallest token;
5. preserve the token and all predicate traces for audit.

The token is a deterministic sampling device. It is not a score, rank, probability, quality measure, or evidence-strength measure and must not be reused to order targets. If a category has no eligible representation, its presentation slot remains explicitly unfilled; no fallback case may be invented.

Because categories can overlap, one EnsemblID may be eligible for or selected into more than one category. V0.1 does not silently substitute a different target for visual diversity. Any uniqueness constraint would require a new governed framework version.

## 6. Required selected-case representation

Every future selected-case record must contain:

- immutable `EnsemblID` and canonical universe ordinal;
- case-selection identity and version axes;
- exact source prioritization representation identity and content SHA256;
- exact source Evidence Summary identity;
- exact source prioritization category, assigned rule ID, and complete rule trace;
- exact component IDs, versions, states, source component-record IDs, and component limitation identifiers;
- exact summary-level limitation identifiers;
- selected case category and `case_rule_id`;
- complete ordered case `predicate_trace`;
- a non-interpretive `structural_reason` object;
- deterministic selection method ID and token SHA256.

## 7. Structural reason contract

The required reason is machine-readable structure, not narrative interpretation. It contains:

- a controlled `reason_code` mapped to the case category;
- the matched JSON-pointer input references;
- the exact controlled values observed at those paths.

Free-text rationales, biological explanations, therapeutic claims, LLM summaries, target fame, and external knowledge are prohibited as selection reasons.

## 8. Preservation rules

The selected-case record must preserve without reinterpretation:

- `EnsemblID`;
- `prioritization_representation_id` and its schema/framework/rule versions;
- source prioritization content SHA256;
- source Evidence Summary identity and content SHA256;
- all four source prioritization rule-trace steps;
- component IDs, versions, states, and source record IDs;
- summary-level and component-level `limitation_identifiers`.

The selector must not reconstruct Evidence Summaries or prioritization representations from earlier evidence layers.

## 9. Independent version axes

| Axis | Governs |
|---|---|
| `case_selection_schema_version` | Serialized selected-case fields and constraints |
| `case_selection_framework_version` | Case-pattern representation and sampling semantics |
| `case_rule_catalog_version` | Eligibility predicates, trace order, and category mapping |
| `case_selector_version` | Deterministic token generation and selection behavior |
| `source_prioritization_schema_version` | Source prioritization serialization |
| `source_prioritization_representation_version` | Source routing representation semantics |
| `source_prioritization_rule_catalog_version` | Source four-rule catalog |
| `source_evidence_summary_version` | Source Evidence Summary semantics |

These axes must remain separate. A version change does not imply scientific improvement or target quality.

## 10. Explicit prohibitions

The [Case Study Selection schema v0.1](../../schemas/case_study_selection_schema_v0.1.json) and every future selector must recursively reject:

- `best_target`;
- `top_target`;
- `rank`;
- `ranking`;
- `score`;
- `priority_score`;
- `recommendation`;
- `target_quality`;
- `evidence_strength`.

Aliases or hidden structures serving the same function are also prohibited. Case selection must not produce an ordered target list, optimization result, therapeutic recommendation, or biological interpretation.

## 11. Validation and authorization boundary

Validation follows [Case Study Selection Validation Requirements v0.1](case_study_selection_validation_requirements_v0.1.md). Task #036A creates only governance, schema, and schema-generator source. It does not authorize selection materialization, presentation claims, or lifecycle promotion.

## 12. Related governance

- [Case Study Selection Rule Catalog v0.1](case_study_selection_rule_catalog_v0.1.md)
- [Case Study Selection Validation Requirements v0.1](case_study_selection_validation_requirements_v0.1.md)
- [Transparent Prioritization Prototype Specification v0.1](prioritization_framework_specification_v0.1.md)
- [Prioritization Validation Requirements v0.1](prioritization_validation_requirements_v0.1.md)
