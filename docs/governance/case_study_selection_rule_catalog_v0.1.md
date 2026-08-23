# Case Study Selection Rule Catalog v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Task:** #036A  
**Catalog version:** `CASE_STUDY_SELECTION_RULE_CATALOG_V0.1`  
**Status:** Structural presentation-rule specification; no case selected

## 1. Purpose

This catalog defines four transparent eligibility predicates for representative presentation cases. The rules classify structural patterns only. They do not evaluate target quality, biological importance, therapeutic value, or drug-development potential.

## 2. Controlled inputs

Rules may read only these frozen fields from one Task #035B representation:

- `/component_state_snapshot/*/component_state`;
- `/limitation_identifiers`;
- `/component_state_snapshot/*/limitation_identifiers`.

No gene symbol, target name, feature value, evidence quantity, source-native score, literature knowledge, or manually curated exception may enter a predicate.

## 3. Case rules

### `CSRULE_036A_001_COMPLETE_PATTERN`

- **Predicate ID:** `CSPRED_ALL_COMPONENTS_OBSERVED_V0.1`
- **Case category:** `CASE_COMPLETE_PATTERN`
- **Predicate:** every component state is `OBSERVED`.
- **Reason code:** `STRUCTURAL_ALL_COMPONENTS_OBSERVED`.
- **Non-claim:** observed structural states do not establish evidence completeness, quality, causality, or target suitability.

### `CSRULE_036A_002_PARTIAL_PATTERN`

- **Predicate ID:** `CSPRED_PARTIAL_OR_MIXED_AVAILABILITY_V0.1`
- **Case category:** `CASE_PARTIAL_PATTERN`
- **Predicate:** no component is `CONFLICTING`, and either at least one component is `PARTIAL` or at least one `OBSERVED` component coexists with at least one `MISSING`/`NOT_QUERIED` component.
- **Reason code:** `STRUCTURAL_PARTIAL_OR_MIXED_AVAILABILITY`.
- **Non-claim:** partial, missing, or unqueried structure is not negative evidence.

### `CSRULE_036A_003_CONFLICT_PATTERN`

- **Predicate ID:** `CSPRED_ANY_COMPONENT_CONFLICTING_V0.1`
- **Case category:** `CASE_CONFLICT_PATTERN`
- **Predicate:** at least one component state is `CONFLICTING`.
- **Reason code:** `STRUCTURAL_COMPONENT_CONFLICT_PRESENT`.
- **Non-claim:** this state does not establish biological contradiction, failure, or lack of therapeutic value.

### `CSRULE_036A_004_LIMITATION_PATTERN`

- **Predicate ID:** `CSPRED_ANY_LIMITATION_IDENTIFIER_V0.1`
- **Case category:** `CASE_LIMITATION_PATTERN`
- **Predicate:** at least one limitation identifier is present at summary or component scope.
- **Reason code:** `STRUCTURAL_LIMITATION_IDENTIFIER_PRESENT`.
- **Non-claim:** limitation presence is not a penalty, quality decrement, confidence estimate, or reason to reject a target.

## 4. Trace order and overlap

Every future case-selection evaluation records all four rules in fixed trace order:

1. complete pattern;
2. partial pattern;
3. conflict pattern;
4. limitation pattern.

The order makes serialization deterministic and is not a category priority. More than one predicate may be true because the limitation pattern can coexist with another structural pattern. A selected case's `case_rule_id` must identify a true predicate and must map exactly to its case category and reason code.

## 5. Representative token rule

For each category, eligible records receive:

`SHA256(canonical_json([framework_version, case_category, EnsemblID, source_prioritization_representation_id, source_representation_content_sha256]))`

The lexicographically smallest token fills the category's single v0.1 presentation slot. This is category-salted deterministic sampling, not target ranking. Tokens must not be compared across categories, transformed into numbers, displayed as quality measures, or reused for target ordering.

## 6. Structural reason mapping

| Case category | Case rule | Required reason code |
|---|---|---|
| `CASE_COMPLETE_PATTERN` | `CSRULE_036A_001_COMPLETE_PATTERN` | `STRUCTURAL_ALL_COMPONENTS_OBSERVED` |
| `CASE_PARTIAL_PATTERN` | `CSRULE_036A_002_PARTIAL_PATTERN` | `STRUCTURAL_PARTIAL_OR_MIXED_AVAILABILITY` |
| `CASE_CONFLICT_PATTERN` | `CSRULE_036A_003_CONFLICT_PATTERN` | `STRUCTURAL_COMPONENT_CONFLICT_PRESENT` |
| `CASE_LIMITATION_PATTERN` | `CSRULE_036A_004_LIMITATION_PATTERN` | `STRUCTURAL_LIMITATION_IDENTIFIER_PRESENT` |

Structural reasons must retain matched input paths and exact values. Free-text interpretation is not allowed.

## 7. Empty and overlapping categories

An empty eligible pool produces an unfilled case slot in release-level validation metadata; it does not trigger fallback selection. Overlap does not imply duplicate evidence or category ordering. The same source representation may fill multiple independent category slots if its category-specific token is selected.

## 8. Change control

Changing a predicate, input path, trace order, category, reason mapping, token inputs, hashing algorithm, slot count, or overlap policy requires a new rule-catalog and framework version. Frozen selections must never be overwritten.

## 9. Prohibitions

The catalog must not identify best or top targets, generate ranks, rankings, scores, priority scores, recommendations, target quality, evidence strength, biological interpretation, therapeutic interpretation, or runtime AI/LLM decisions.

## 10. Related governance

- [Case Study Selection Framework v0.1](case_study_selection_framework_v0.1.md)
- [Case Study Selection Validation Requirements v0.1](case_study_selection_validation_requirements_v0.1.md)
- [Prioritization Rule Catalog v0.1](prioritization_rule_catalog_v0.1.md)

