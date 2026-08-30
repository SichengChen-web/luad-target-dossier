# MMP11 cross-source evidence synthesis v0.1

MMP11 is an illustrative LUAD worked example. This synthesis organizes frozen evidence and dependencies; it is not a target score, ranking, therapeutic validation, clinical-efficacy claim, or recommendation.

## Scope

This synthesis references frozen Task #039A and Task #039B evidence without replacing any evidence identifier. It links one S0 source row, six sensitivity-model rows represented by two governed internal records, and all **56** bounded external evidence units. Counts below are audit metadata, not evidence strength.

## What the evidence package can support

- **Project expression association:** S0 reports MMP11 higher in LUAD tumour than normal tissue (Tumor minus Normal logFC **+5.18003235678542**; BH FDR **1.79025769607393e-37**).
- **Same-dataset robustness:** all **6** prespecified sensitivity models retain the tumour-higher direction. They use the same TCGA-LUAD biological dataset and are not independent replication.
- **External observation:** external transcriptomic and patient tissue/protein observations exist. Published TCGA analyses share project dataset lineage; accession-resolved GEO observations provide other dataset contexts, with reuse and histology limitations retained.
- **Preclinical functional context:** reported LUAD cell perturbation, xenograft depletion, and anti-MMP11 antibody experiments contain bounded phenotypic observations.
- **Clinical boundary:** clinical/prognostic records include all **7** null observations and context-dependent findings. The bounded registry check found no relevant MMP11 clinical-development record among five lexical false positives.

## Dependency-aware interpretation

The synthesis defines **43** evidence families and **251** qualitative dependency relationships. It distinguishes:

1. **Same-dataset robustness:** S0 versus S1-S6.
2. **Same-dataset reanalysis:** project TCGA-LUAD versus published TCGA analyses.
3. **Distinct dataset observation:** provenance-resolved non-TCGA cohorts, subject to accession reuse and overlap checks.
4. **Distinct evidence modality:** transcriptomics, protein/tissue, clinical association, cell perturbation, mechanistic, in-vivo, intervention, and clinical-development-check contexts.
5. **Same-publication multi-modality:** PMID 31024988 contributes transcriptomic, tissue, cell, xenograft, and antibody observations, but these retain shared publication, model, experiment, and reagent lineages.

`NO_DEPENDENCY_IDENTIFIED` and missing graph edges never establish statistical independence. The number of GEO accessions is not the number of independent transcriptomic replications, and the number of evidence units is not the number of independent sources.

## Dependency count semantics

- The frozen Task #039A dependency map contains **21 source relationship records**.
- **14** of those records carry two qualitative relationship types; **7** carry one.
- Task #039C represents each qualitative relationship type as an atomic graph row. The 21 Task #039A source records therefore become **35 normalized atomic edges**.
- Task #039B contributes **197 frozen dependency edges**.
- Task #039C adds **19 newly synthesized cross-task relationships**.
- The combined normalized dependency graph contains **251 rows**: 35 + 197 + 19 = 251.

**251 graph rows != 251 independent evidence sources.** Normalization expands representation granularity only; it does not add scientific observations or evidence strength.

## Important count semantics

- Frozen `F_IN_VIVO` domain evidence units: **1**.
- Total in-vivo experimental units: **2**, because `EXT_31024988_12` is classified under intervention while also being a xenograft experiment.
- `EXT_31024988_12` remains one evidence record and one family member; its relevance to two claims is not two observations.
- Distinct governed dataset/cohort lineages represented: **34**.
- Unresolved dependency relationships retained: **5**.

## What cannot be said

- Expression or prognostic association does not prove disease causality.
- Model robustness and published TCGA reanalysis are not independent biological replication.
- Protein or serum observations do not establish diagnostic validity.
- Cell perturbation and xenograft effects do not establish patient efficacy or safety.
- Preclinical antibody observations do not establish a validated therapeutic intervention.
- The bounded clinical-development search does not prove global absence.
- This synthesis does not rank MMP11, calculate a target or confidence score, or recommend therapy.

## Maximum bounded conclusion

MMP11 provides an illustrative LUAD worked example in which a strong, model-robust project-derived transcriptomic association can be connected to external observations across transcriptomic, tissue, functional, and preclinical experimental modalities. However, shared TCGA lineage, within-publication dependencies, context-dependent clinical associations, and the absence of clinical validation prevent these observations from being interpreted as proof of therapeutic efficacy or as a validated target recommendation.

This conclusion was emitted only after all claim, identity, provenance, dependency, count-semantic, and frozen-input checks passed.
