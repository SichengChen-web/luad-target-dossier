# Evidence Acquisition Strategy Framework v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Task:** #017 — evidence acquisition strategy framework  
**Version:** v0.1  
**Date:** 21 August 2026  
**Status:** Working descriptive acquisition framework

## Purpose

Task #017 translates the evidence gaps documented by Task #016 into explicit classes of additional evidence that could reduce uncertainty. It answers:

> For each evidence-gap category, what additional evidence class would make the evidence profile more interpretable?

This is a framework-design task. It does not retrieve new evidence, choose genes, rank or score targets, recommend targets, or infer therapeutic direction.

## Frozen Task #016 inputs

Only these committed Task #016 outputs are used:

| Input | SHA256 |
| --- | --- |
| `outputs/evidence_gap_analysis/evidence_gap_registry.csv` | `3e509ef36d57c553a36e36429a42955c02c0eef209cf2d77b0adbd2d217c60f6` |
| `outputs/evidence_gap_analysis/evidence_gap_category_counts.csv` | `03357115a1237c87921415221e1e3876462eb771f1c4950c9056ad2c3a27ad6b` |
| `outputs/evidence_gap_analysis/validation_strategy_matrix.csv` | `6f915616019265583103cee945d0ccfcc1328628e374f989ff8b74bf0e93d981` |
| `outputs/evidence_gap_analysis/evidence_gap_summary.md` | `b779986769ab1aa08cb536330b959fe0761d60ff1755b6ef592a0f7fc377d5f4` |
| `outputs/evidence_gap_analysis/session_info.txt` | `71df0b77d97fa49bc0e6e3262546121cc34493134f5242ae03dddfba81bd2fcd` |

The builder fails if these hashes change. It also reconciles Task #016 aggregate category counts against the 29,606 row-level gap profiles.

## Unit of the framework

The framework contains one row for each Task #016 category in either:

- `MISSING_EVIDENCE_DOMAIN` — 11 categories; or
- `KNOWN_UNCERTAINTY` — five cross-cutting categories.

These 16 rows are framework categories, not genes. `affected_gene_count` and `affected_gene_percent` reproduce descriptive Task #016 coverage. A larger affected count does not establish greater scientific importance and does not determine acquisition order.

Every Task #016 `FUTURE_EVIDENCE_TYPE` is represented. Cross-cutting uncertainties additionally receive provenance, coverage, independence, or temporal-refresh evidence classes.

## Framework fields

Each category records:

- its Task #016 category group and evidence layer;
- the additional evidence class;
- the number and percentage of profiles affected;
- the scientific question to be answered;
- the potential data-source class;
- the atomic acquisition unit;
- immutable or source-specific identifier keys;
- minimum provenance fields;
- evidence-quality checks;
- source-dependency controls;
- the uncertainty expected to be reduced;
- an adequacy criterion; and
- an interpretation boundary.

The adequacy criterion describes what a properly characterized retrieval would contain. It does not require a positive record: a traceable, coverage-aware `NOT_FOUND` result remains valid retrieval evidence and must not be converted into negative biological evidence.

## Discovery evidence acquisition

### LUAD disease-association detail

Acquire source-level target–disease records keyed by EnsemblID, an explicit LUAD disease identifier, and the upstream record identifier. Preserve the originating source and reference so that multiple records derived from the same publication or database are not mistaken for independent support.

### Independent LUAD replication

For expression conflicts, an independent LUAD tumour/normal cohort could clarify whether effect direction and magnitude reproduce outside TCGA/recount3. Independence of samples and processing lineage must be demonstrated. Replication still supports association rather than causality.

## Mechanistic evidence acquisition

### Cancer genetic evidence

Acquire LUAD-relevant somatic mutation, copy-number, or germline association records at alteration/study resolution. Cohort overlap with TCGA and reused Open Targets records must remain visible.

### Functional dependency

Acquire gene-by-model CRISPR dependency observations with LUAD lineage, screen version, guide-quality, model, and replicate metadata. Cell-line fitness effects cannot establish patient benefit or safe therapeutic direction.

### Perturbational mechanism

Acquire controlled genetic or pharmacological perturbation observations at experiment/model/endpoint resolution. Target engagement, controls, dose or time context, replication, and source lineage are necessary to interpret the result.

## Therapeutic-development evidence acquisition

### Pharmacology

Acquire compound-target assay and mechanism records with target confidence, assay type, potency units, selectivity context, and compound/assay identifiers. Activity records do not prove in-vivo efficacy or LUAD relevance.

### Modality-specific tractability

Acquire target-by-modality assessments with evidence-bucket provenance for small molecules, antibodies, protein degraders, or other explicitly defined modalities. Tractability is distinct from biological validity.

### Clinical development

Acquire trial-level intervention–target–disease linkages with registry identifier, intervention identity, phase, status, record version, and target-linkage basis. Clinical investigation is development precedent, not proof of efficacy or target validity.

## Risk evidence acquisition

### Normal-tissue context

Acquire gene-by-tissue or cell-type measurements with donor, assay, dataset, and RNA-versus-protein provenance. Normal expression provides exposure context but does not prove toxicity.

### Essentiality and genetic constraint

Acquire context-specific human constraint, normal-cell essentiality, and cancer-dependency records without collapsing these distinct concepts. Genetic intolerance does not directly quantify pharmacological safety.

### Safety liabilities and toxicity

Keep target-liability records separate from compound- or modality-exposure toxicology. Preserve evidence type, exposure context, species or human relevance, on-target versus off-target attribution, study/report identifiers, and duplicate lineage. Adverse-event associations do not automatically demonstrate causality.

## Cross-cutting uncertainty acquisition

Four additional evidence classes address uncertainties that cannot be resolved merely by collecting more biological records:

- `SOURCE_LINEAGE_AND_DEPENDENCY_AUDIT` distinguishes independent, derived, duplicated, and unresolved records.
- `SOURCE_COVERAGE_AND_COMPLETENESS_AUDIT` reconciles eligible, queried, returned, failed, `NOT_FOUND`, and `NOT_APPLICABLE` denominators.
- `INDEPENDENT_SOURCE_CORROBORATION` tests whether source-specific observations reproduce in a genuinely independent data lineage.
- `TIMESTAMPED_SOURCE_REFRESH` records versioned changes without treating a newer snapshot as an independent source.

## Acquisition controls for future tasks

Any later evidence retrieval should receive its own versioned specification that freezes:

1. the scientific question and evidence class;
2. the eligible gene and identifier universe;
3. official source, release, endpoint, and query;
4. atomic source-record unit and deduplication rule;
5. raw and normalized provenance;
6. missingness semantics and failed-query handling;
7. source-dependency and upstream-lineage rules;
8. quality-control and adequacy assertions; and
9. interpretation limitations.

This Task #017 framework does not choose a database, authorize network use, establish an acquisition sequence, or define evidence weights.

## Validation and non-claims

The builder validates:

- all frozen Task #016 hashes;
- 29,606 unique Task #016 EnsemblIDs;
- row-level reconciliation of gap, uncertainty, and future-evidence counts;
- coverage of all 11 missing-evidence and five uncertainty categories;
- coverage of all 12 future-evidence types;
- explicit, nonblank acquisition and provenance fields; and
- absence of fields for scoring, ranking, target selection, prioritization, recommendations, or therapeutic direction.

Task #017 does not assert that additional evidence will support a target. It states only what kind of evidence could reduce a documented uncertainty.
