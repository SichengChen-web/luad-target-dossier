# Task #036B Case Dossier Validation Report

## Scope

This release contains presentation-oriented structural case-pattern dossiers only. It does not identify optimal targets and contains no biological or therapeutic interpretation.

## Selection results

| Case category | Status | Eligible source records | Selected EnsemblID | Universe ordinal |
|---|---:|---:|---|---:|
| CASE_COMPLETE_PATTERN | FILLED | 7690 | ENSG00000168952.15 | 86 |
| CASE_PARTIAL_PATTERN | FILLED | 18481 | ENSG00000278376.1 | 3091 |
| CASE_CONFLICT_PATTERN | FILLED | 3435 | ENSG00000270890.1 | 27549 |
| CASE_LIMITATION_PATTERN | FILLED | 29606 | ENSG00000260630.6 | 13588 |

All 29,606 frozen Task #035B representations were evaluated independently for every Task #036A category. Category overlap was preserved. No fallback record was substituted for an empty eligible pool.

## Validation

- PASS — source identity and immutable EnsemblID reconciliation
- PASS — complete four-step source rule-trace reconciliation
- PASS — Task #036A category and predicate-trace reconciliation
- PASS — category-salted SHA256 token reproduction and lexicographic minimum selection
- PASS — every filled dossier validates against `CASE_STUDY_SELECTION_SCHEMA_V0.1`
- PASS — component IDs, versions, states, source record IDs, and limitations are unchanged
- PASS — recursive prohibited-field scan
- PASS — two complete 29,606-record regenerations are byte-identical
- PASS — all frozen Task #035B and Task #036A input hashes unchanged before and after generation

## Interpretation boundary

The selected records are deterministic examples of structural evidence patterns. Selection tokens are routing devices, not measurements. Category membership and selection do not establish biological importance, comparative merit, or therapeutic suitability.
