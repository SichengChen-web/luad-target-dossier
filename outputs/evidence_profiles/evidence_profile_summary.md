# Task #020 target evidence profile architecture summary

**Profile records populated:** 0  
**Profile schema fields:** 28  
**Profile components:** 11  
**Interpretation rules:** 18  
**Validation checks passed:** 12/12  
**Scores, rankings, selections, or therapeutic conclusions generated:** No

## Architecture

A future profile is a long-form collection of one row per immutable EnsemblID and component. It organizes bounded claims and evidence records while retaining source entities, artifact hashes, missingness, uncertainty, conflict, and dependency metadata. It does not combine components into a single assessment.

| Profile section | Components |
| --- | ---: |
| Biological Discovery Profile | 4 |
| Therapeutic Development Profile | 4 |
| Translational Profile | 3 |

## Component states

- `OBSERVED`: qualifying records exist with traceable provenance under the component rule.
- `PARTIAL`: some evidence exists, but coverage, linkage, or provenance remains incomplete.
- `MISSING`: a defined assessment found no qualifying record; this is not negative evidence.
- `NOT_QUERIED`: the evidence class was not acquired or could not be queried.
- `CONFLICTING`: materially incompatible records are retained under a prespecified comparison rule.

These states describe evidence organization. They have no numerical order and do not encode favorable or unfavorable target properties.

## Composite translational views

Human evidence, clinical linkage, and risk context reuse existing ontology records. Reuse retains the same record IDs and dependencies; it does not create new observations. Clinical linkage requires record-level intervention–target–disease linkage and cannot be inferred from co-occurring counts.

## What a profile can describe

- evidence availability by component;
- qualitative evidence maturity, meaning which components are sufficiently characterized for bounded interpretation; and
- unresolved missingness, conflict, temporal, source, coverage, and dependency uncertainty.

## What a profile cannot establish

- biological or disease causality;
- drug or modality efficacy;
- safety or an acceptable therapeutic window;
- clinical benefit, utility, approval, or benefit-risk; or
- target ordering, selection, or therapeutic conclusions.

Profile completeness is not target quality. Evidence-record quantity is not evidence quality. Dependent records are not independent votes. No completeness percentage, aggregation formula, or overall score is part of this architecture.

## Validation

All frozen Task #018 governance and Task #019 decision-context hashes matched. All 193 Task #018 governed artifacts retained their recorded hashes and sizes. The schema covers all eight ontology domains and all 17 evidence types, preserves the Task #014 missingness/uncertainty/dependency vocabularies, and introduces no gene-level profile data.
