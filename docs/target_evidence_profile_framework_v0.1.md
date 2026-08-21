# Target Evidence Profile Architecture v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Task:** #020 — target evidence profile architecture  
**Version:** v0.1  
**Date:** 21 August 2026  
**Status:** Working profile schema

## Purpose

Task #020 defines how a future target can be represented as an auditable, structured evidence profile without creating a ranking or hidden composite assessment.

This task creates a schema, component vocabulary, and interpretation rules. It does not populate profiles for any gene. Evidence remains in the Task #013 ontology and Task #014 claim/record architecture; the profile is an organizational view over those records, constrained by Task #019 interpretation boundaries and frozen under Task #018 governance.

## Scientific separation

The architecture separates three activities:

1. **Evidence generation:** retrieving or producing source-grounded evidence in a dedicated task.
2. **Evidence organization:** linking bounded claims, records, sources, dependencies, missingness, and uncertainty into profile components.
3. **Evidence interpretation:** stating only what the organized evidence can and cannot support under Task #019 boundaries.

Task #020 performs only the second activity at schema level. It neither generates new evidence nor interprets a target.

## Profile representation

A future materialized profile uses a long-form structure:

```text
one immutable EnsemblID
        ↓
one versioned target profile
        ↓
one row per profile component
        ↓
bounded claims and atomic evidence records
        ↓
source entities, versions, dependencies, missingness, uncertainty, and hashes
```

EnsemblID remains the immutable target key. A symbol may be displayed in a future presentation layer but cannot replace EnsemblID or be used for joins.

No profile-level total, weighted sum, completeness percentage, or overall state is defined.

## Controlled component states

Every component uses exactly one of five organizational states:

| State | Meaning |
| --- | --- |
| `OBSERVED` | Qualifying evidence records are present under the component-specific rule with traceable provenance. |
| `PARTIAL` | Some relevant evidence exists, but coverage, record linkage, quality characterization, or provenance remains incomplete. |
| `MISSING` | A defined and completed assessment found no qualifying evidence. |
| `NOT_QUERIED` | The evidence class has not been acquired or could not be queried under the required identifiers/source. |
| `CONFLICTING` | Materially incompatible observations exist under a prespecified comparison rule. |

These states are categorical descriptions, not an ordinal scale. `OBSERVED` is not synonymous with favorable evidence. `PARTIAL` is not half-support. `MISSING` and `NOT_QUERIED` are not negative biological evidence. `CONFLICTING` preserves disagreement rather than choosing or averaging records.

The original Task #014 missingness states remain attached separately. The profile state never erases whether a source record was `OBSERVED`, `NOT_FOUND`, `NOT_QUERIED`, `NOT_APPLICABLE`, or `UNKNOWN`.

## Section 1 — Biological Discovery Profile

### Transcriptomic evidence

Represents primary TCGA-LUAD tumour-versus-normal effect/significance evidence and S1–S6 sensitivity diagnostics. These are related views of the same cohort. They characterize an expression association and model sensitivity, not causal biology or independent replication.

### Disease association

Represents Open Targets direct, indirect, and literature evidence states. These views share a platform and can share upstream records. Literature quantity is not quality, and indirect association is not independent confirmation of direct LUAD evidence.

### Genetic evidence

Reserves the existing `EV_GENETIC_CANCER` ontology type. The current architecture has not queried dedicated genetic evidence, so a future populated profile begins `NOT_QUERIED` unless a separate validated acquisition task exists.

### Functional dependency

Reserves `EV_FUNCTIONAL_CRISPR_DEPENDENCY`. Model-level screen, lineage, reagent, replicate, and QC provenance are required. Cell-line fitness does not establish patient efficacy or a safe therapeutic window.

## Section 2 — Therapeutic Development Profile

### Pharmacology

Combines target annotations, source-native drug/candidate records, and future compound-target evidence into one bounded component. Target presence or candidate counts resolve at most `PARTIAL`; an `OBSERVED` pharmacology state requires qualifying compound-target records with interpretable assay, potency, target confidence, selectivity, and mechanism provenance.

### Tractability

Retains small-molecule, antibody, PROTAC, and other-clinical-modality assessments. Multiple modality buckets share one Open Targets framework and are not independent votes. Tractability describes feasibility, not biological causality or efficacy.

### Safety

Represents current curated safety-liability observations. `MISSING` means no qualifying record was returned after a defined query; it never means safe. A returned liability does not by itself prove on-target toxicity or determine target rejection.

### Clinical development evidence

Reserves trial-level intervention–target–disease linkage. Current platform candidate counts do not substitute for trial records. This component remains `NOT_QUERIED` until a dedicated clinical-development retrieval validates trial, intervention, target, disease, phase, status, and linkage provenance.

## Section 3 — Translational Profile

The translational section is a set of composite views over existing records. It does not create additional evidence.

### Human evidence

Organizes explicitly human-derived cancer-genetic or interventional records. An ontology label alone cannot certify that evidence is human-derived; cohort/trial provenance must do so.

### Clinical linkage

Requires record-level linkage among an intervention, target, LUAD disease context, and clinical-development record. Separate target, drug, disease, or trial counts cannot be joined by co-occurrence or symbol matching. Reused records retain their original IDs and dependencies.

### Risk context

Reuses the existing safety domain while making its incompleteness explicit. The current ontology lacks dedicated normal-tissue, essentiality, exposure, and broader toxicology domains, so current safety-liability data alone cannot produce a complete risk characterization.

## Profile schema and provenance

`profile_schema.csv` defines 28 fields for future long-form target-component records. Required provenance includes:

- bounded claim IDs;
- atomic evidence-record IDs;
- source-entity IDs and source releases;
- Task #018 artifact IDs and SHA256 hashes;
- Task #014 missingness and uncertainty categories;
- dependency relationships and qualitative levels;
- conflict status and explanation;
- provenance-completeness status;
- component-specific interpretation-boundary IDs; and
- versioned generator and timestamp.

Record counts are retained only for audit reconciliation. They must never be interpreted as quality, strength, confidence, or independent convergence.

## Evidence maturity

A profile may describe evidence maturity qualitatively: which components have enough provenance and coverage for bounded interpretation, and which remain partial, missing, unqueried, or conflicting.

Maturity is not target quality, development stage, or probability of success. The architecture deliberately excludes a completeness percentage because a full profile can contain weak, dependent, or conflicting evidence, while a sparse profile may reflect an unqueried source rather than poor biology.

## Dependency and reuse

Evidence is identified at record and source level. When the same evidence appears in more than one component—for example, a safety record in both development and translational views—it retains the same record ID. It does not become a second observation.

Known dependencies remain explicit:

- effect, significance, and S1–S6 robustness share the TCGA cohort;
- Open Targets direct, indirect, literature, drug, tractability, and safety evidence share platform lineage and may share upstream records;
- ChEMBL compound evidence can be upstream of Open Targets drug and tractability records; and
- future trial records can overlap platform candidate counts and clinical-precedence tractability.

Absence of a dependency edge does not prove independence.

## Profile interpretation rules

The profile may describe:

- evidence availability;
- qualitative evidence maturity; and
- unresolved source, coverage, temporal, dependency, and conflict uncertainty.

The profile cannot establish:

- biological or disease causality;
- drug or modality efficacy;
- safety or an acceptable therapeutic window;
- clinical benefit, utility, approval, or a favorable benefit-risk balance; or
- target ordering, selection, or therapeutic conclusions.

Profile completeness is not target quality. Evidence quantity is not evidence quality. Dependent records are not independent votes. No aggregation calculation is permitted by this architecture.

## Frozen inputs and validation

The builder hash-pins the complete Task #018 governance framework and Task #019 decision-context framework together with the Task #013 ontology and Task #014 claim/dependency architecture. It validates all 193 Task #018 governed artifact hashes and sizes before and after generation.

Output validation requires:

- exactly 28 schema fields;
- exactly 11 components in a 4/4/3 section structure;
- the exact five allowed component states;
- coverage of all eight ontology domains and all 17 evidence types;
- exactly 18 interpretation rules covering availability, maturity, uncertainty, missingness, quantity, dependency, completeness, causality, efficacy, safety, clinical benefit, and target-ordering boundaries; and
- no assessment, aggregation, ranking, selection, recommendation, or therapeutic-direction fields.

Task #020 performs no network access, package installation, evidence retrieval, gene analysis, profile population, commit, or push.
