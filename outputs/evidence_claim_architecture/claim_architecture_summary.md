# Task #014 evidence claim and provenance architecture summary

**Bounded evidence claims:** 148,030  
**Traceable evidence records:** 207,242  
**Source entities:** 6  
**Instantiated dependency relationships:** 77,202  
**Scoring, ranking, prioritization, or recommendations created:** No

## Architecture instantiated

Each of the 29,606 Ensembl genes has five bounded current-domain claims: transcriptomic discovery, LUAD disease association, pharmacology annotation, tractability, and safety liability. Future genetic, functional-dependency, and clinical-development domains remain explicitly `NOT_QUERIED` at the domain level.

Each gene has seven traceable record slots: primary transcriptomic result, transcriptomic robustness result, Open Targets LUAD association, Open Targets drug/candidate count, ChEMBL target annotation, Open Targets tractability summary, and Open Targets safety summary. A record can carry `NOT_FOUND` or `NOT_QUERIED`; such a placeholder preserves missingness and is not counted as supporting evidence.

## Dependency relationships

| Relationship | Count |
| --- | --- |
| SAME_SOURCE | 35718 |
| SHARED_DATASET | 29606 |
| UNKNOWN | 11878 |

Dependency levels:

| Dependency level | Count |
| --- | --- |
| DEPENDENT | 38012 |
| PARTIALLY_DEPENDENT | 39190 |

Dependency edges are instantiated only when both records are observed. Primary and robustness expression records are explicitly linked by `SHARED_DATASET`. Open Targets records are linked by `SAME_SOURCE` where appropriate. Potential Open Targets/ChEMBL overlap that cannot be resolved from gene-level summaries is marked `UNKNOWN` with `PARTIALLY_DEPENDENT` level and requires record-level review.

The absence of an edge does not prove independence; Task #013 remains the higher-level evidence-type independence framework.

## Missingness categories

| Category | Registry rows |
| --- | --- |
| NOT_APPLICABLE | 1 |
| NOT_FOUND | 60481 |
| NOT_QUERIED | 2855 |
| OBSERVED | 84697 |
| UNKNOWN | 1 |

## Uncertainty categories

| Category | Registry rows |
| --- | --- |
| CONFLICTING_RECORDS | 3435 |
| DEPENDENCY_UNCERTAIN | 45787 |
| INCOMPLETE_COVERAGE | 63333 |
| SOURCE_LIMITATION | 27069 |
| TEMPORAL_UNCERTAINTY | 8406 |

## Evidence-inflation controls

- Scalar fields from one source row are referenced together rather than promoted to separate independent claims.
- S0 and S1-S6 are separate traceable records but explicitly share a dataset and are dependent; sensitivity models are not replications.
- Open Targets direct/indirect association fields remain one disease-association record because the views overlap.
- Tractability modality counts remain one source summary and are not a score or multiple votes.
- ChEMBL target availability is not interpreted as compound activity, potency, mechanism, or therapeutic value.
- Supporting-record counts are audit counts only and are never converted into confidence or rank.

## Critical missingness boundary

`NOT_FOUND` means the defined retrieval returned no corresponding record; `NOT_QUERIED` means no query could be made or the future domain has not been retrieved. Neither is negative biological evidence. In particular, absence of a safety-liability record is not evidence of safety.

## Validation

All claim, record, source, and dependency identifiers are unique. Every record links to a valid claim and source, every claim links to a Task #013 domain, every dependency links to two valid records, every supporting-record count reconciles to traceable records, and all controlled missingness and uncertainty categories are represented.

No score, rank, priority, confidence score, target quality, recommendation, therapeutic direction, selection, target prioritization, or therapeutic interpretation was generated.
