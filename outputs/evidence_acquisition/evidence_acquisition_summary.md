# Task #017 evidence acquisition framework summary

**Task #016 gene profiles represented:** 29,606  
**Acquisition-framework categories:** 16  
**QC checks passed:** 8/8  
**Scores, rankings, candidate selections, or target recommendations created:** No

## What this framework answers

For each Task #016 missing-evidence or uncertainty category, the framework names an additional evidence class that could reduce uncertainty. It also states the scientific question, acquisition unit, identifier keys, minimum provenance, quality checks, dependency controls, adequacy criterion, and interpretation boundary.

Affected-gene counts describe the Task #016 snapshot. They do not determine acquisition order and are not weights.

## Framework coverage

| Evidence layer | Framework categories |
| --- | ---: |
| Discovery | 2 |
| Mechanistic | 3 |
| Development | 3 |
| Risk | 4 |
| Cross Cutting | 4 |

## Project-wide acquisition needs

8 categories affect all 29,606 profiles in Task #016:

- `GENETIC_EVIDENCE` → `CANCER_GENETIC_EVIDENCE`
- `FUNCTIONAL_DEPENDENCY` → `CRISPR_FUNCTIONAL_DEPENDENCY`
- `PERTURBATIONAL_EVIDENCE` → `PERTURBATIONAL_MECHANISM`
- `CLINICAL_DEVELOPMENT` → `TRIAL_LEVEL_CLINICAL_DEVELOPMENT`
- `NORMAL_TISSUE_CONTEXT` → `NORMAL_TISSUE_EXPRESSION`
- `ESSENTIALITY` → `ESSENTIALITY_GENETIC_CONSTRAINT`
- `TOXICITY_EVIDENCE` → `TOXICITY_EVIDENCE`
- `INCOMPLETE_COVERAGE` → `SOURCE_COVERAGE_AND_COMPLETENESS_AUDIT`

## Scientific boundary

An evidence-acquisition class is not a conclusion about a gene. A complete query can return an explicit `NOT_FOUND` state, and that state must remain distinct from a negative biological finding. Likewise, adding records does not automatically establish source independence, causality, druggability, safety, clinical validity, or therapeutic direction.

The framework does not choose databases, authorize network retrieval, define gene subsets, or specify an acquisition sequence. Each future retrieval requires its own frozen source, query, identifier, provenance, missingness, and validation specification.

## Validation

All five Task #016 input hashes matched. The 29,606-row registry was unique by EnsemblID; Task #016 category counts reconciled to the row-level token fields; all 11 missing-evidence and five uncertainty categories were represented exactly once; and all 12 Task #016 future-evidence types were retained.
