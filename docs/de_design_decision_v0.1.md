# Primary Differential-Expression Design Decision v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Analysis:** Task #006 primary differential expression  
**Status:** Frozen primary-model decision

## Primary biological comparison

The primary comparison is Primary Tumor versus Solid Tissue Normal in the frozen Task #005 cohort.

The contrast orientation is explicitly:

`Tumor_vs_Normal = Tumor - Normal`

Therefore, positive log2 fold change means higher expression in Tumor and negative log2 fold change means lower expression in Tumor.

## Primary fixed-effect design

The frozen primary design is:

`~ 0 + group + batch_number`

The group factor has explicit coefficients named `Normal` and `Tumor`. The analysis constructs the contrast `Tumor - Normal` explicitly and does not rely on an implicit reference-level sign convention.

`batch_number` is taken specifically from `tcga.cgc_case_batch_number`. It represents TCGA/BCR case-batch or cohort structure. It is included as a prespecified nuisance adjustment because this measured structure is imbalanced between Tumor and Normal observations.

This field is **not** treated or described as a proven RNA-seq sequencing batch, sequencing lane, library-preparation batch, or sequencing-run batch. Its inclusion does not prove that it represents a direct RNA-seq technical artifact.

## Case blocking

`case_id` is used as the repeated-measures blocking variable in `edgeR::voomLmFit(..., block = case_id)`. It is not included as a fixed effect in the primary design.

This strategy estimates a consensus within-case correlation from the 58 matched tumor-normal cases while retaining the larger unpaired cohort. The estimated correlation is a diagnostic and will not be used to change the frozen Task #006 model.

## Sample and observation weights

The primary analysis uses:

`sample.weights = FALSE`

This disables sample-quality weights only. Ordinary voom observation-level precision weights remain part of the analysis.

The call also uses `normalize.method = "none"` because the reconstructed DGEList already contains the frozen Task #005 TMM normalization factors. This setting does not discard TMM normalization.

## Prespecified Task #007 sensitivity analyses

The following six analyses are documented prospectively. **None is fitted or run in Task #006.**

### S1 — Omit case blocking

- design: `~ 0 + group + batch_number`
- block: `NULL`
- sample weights: `FALSE`

### S2 — Omit TCGA/BCR case-batch adjustment

- design: `~ 0 + group`
- block: `case_id`
- sample weights: `FALSE`

### S3 — Use TSS instead of TCGA/BCR case-batch

- design: `~ 0 + group + tissue_source_site`
- block: `case_id`
- sample weights: `FALSE`

### S4 — Adjust for both TCGA/BCR case-batch and TSS

- design: `~ 0 + group + batch_number + tissue_source_site`
- block: `case_id`
- sample weights: `FALSE`

### S5 — Enable sample-quality weights

- design: `~ 0 + group + batch_number`
- block: `case_id`
- sample weights: `TRUE`

### S6 — Matched-pairs-only analysis

- cohort: 58 matched cases, 116 observations
- design: `~ 0 + group + case_id`
- block: none
- sample weights: `FALSE`

`batch_number` is not added separately in S6 because it is a case-level variable and the case fixed effects absorb case-level terms.

## Planned Task #007 comparisons

Each sensitivity will be compared with the primary model using:

- all-gene Pearson logFC correlation;
- all-gene Spearman logFC correlation;
- logFC sign concordance;
- top-100 overlap;
- top-500 overlap;
- FDR-significant overlap;
- largest model-dependent genes.

No Task #007 sensitivity analysis was executed as part of Task #006.
