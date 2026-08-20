# Differential-Expression Sensitivity Analysis Plan v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Analysis:** Task #007 prespecified differential-expression sensitivities  
**Status:** Prespecified plan; the committed Task #006 analysis remains primary

## Frozen primary reference

The committed Task #006 result is sensitivity reference `S0`. It is not
refitted in Task #007.

- design: `~ 0 + group + batch_number`
- `batch_number`: `tcga.cgc_case_batch_number`, a TCGA/BCR case-batch
  structure and not a proven RNA-seq sequencing batch
- block: `case_id`
- sample-quality weights: `FALSE`
- contrast: `Tumor_vs_Normal = Tumor - Normal`
- empirical Bayes: `trend = FALSE`, `robust = TRUE`
- universe: 574 observations and 29,606 genes

Positive log2 fold change always means higher expression in Tumor.

## Prespecified sensitivities

The six sensitivities are fitted exactly as frozen in the Task #006 design
decision. No seventh or post-hoc model is added.

### S1 — Omit case blocking

- cohort: all 574 observations
- design: `~ 0 + group + batch_number`
- block: `NULL`
- sample-quality weights: `FALSE`

### S2 — Omit TCGA/BCR case-batch adjustment

- cohort: all 574 observations
- design: `~ 0 + group`
- block: `case_id`
- sample-quality weights: `FALSE`

### S3 — Use TSS instead of TCGA/BCR case-batch

- cohort: all 574 observations
- design: `~ 0 + group + tissue_source_site`
- block: `case_id`
- sample-quality weights: `FALSE`

### S4 — Adjust for TCGA/BCR case-batch and TSS

- cohort: all 574 observations
- design: `~ 0 + group + batch_number + tissue_source_site`
- block: `case_id`
- sample-quality weights: `FALSE`

### S5 — Enable sample-quality weights

- cohort: all 574 observations
- design: `~ 0 + group + batch_number`
- block: `case_id`
- sample-quality weights: `TRUE`

Ordinary voom observation-level precision weights remain enabled for every
model. S5 additionally estimates one empirical sample-quality weight per
observation; no sample is removed based on that weight.

### S6 — Matched pairs only

- cohort: exactly 58 matched cases and 116 observations
- design: `~ 0 + group + case_id`
- block: `NULL`
- sample-quality weights: `FALSE`

S6 retains the frozen 29,606-gene universe without rerunning
`filterByExpr()`. Library sizes and TMM factors are recalculated after
subsetting. `batch_number` and TSS are not added because `case_id` fixed
effects absorb case-level terms.

## Execution and checkpointing

The default execution order is `S1`, `S6`, `S2`, `S3`, `S4`, `S5`.
Each completed model is written to disk immediately with its diagnostics and
runtime. Recovery runs may explicitly request a subset, for example
`--models=S3,S4,S5`; requested models are always refitted rather than skipped
because a file exists. After all six model checkpoints exist, `--models=NONE`
is a comparison-only recovery mode: it validates every checkpoint and rebuilds
the combined outputs without refitting a model. In this mode, total runtime is
the sum of the recorded required reconstruction, model, and comparison
components across checkpoint/recovery executions; stopped pre-fit attempts and
orchestration gaps are explicitly excluded.

S1–S5 reuse one reconstruction of the frozen 29,606 × 574 TMM-normalized
DGEList. S6 derives its matched subset from that same reconstruction.

## Prespecified comparisons with S0

Each sensitivity is joined to S0 by `EnsemblID` and compared using:

- all-gene Pearson and Spearman logFC correlation;
- all-gene logFC sign concordance;
- top-100 and top-500 intersection and Jaccard overlap, using each
  `topTable(sort.by = "P")` ordering;
- BH FDR < 0.05 overlap, including S0-only, sensitivity-only, and Up/Down
  directional overlap;
- the 50 largest absolute changes in logFC, where
  `delta_logFC = logFC_sensitivity - logFC_primary`.

DE-count summaries are descriptive and are not used to choose a preferred
model. Reduced significance in S6 is expected from reducing the analysis from
574 to 116 observations and is not, by itself, evidence of effect-size
instability.

## Design diagnostics

For each design, singular values are saved. The normalized condition number
is calculated by scaling every nonzero design column to unit Euclidean/L2
norm, computing the singular values of that scaled matrix, and dividing the
largest singular value by the smallest nonzero singular value. It is a
descriptive diagnostic without an arbitrary pass/fail threshold.

## Interpretation boundary

Task #007 tests robustness to the six prespecified modelling choices. It does
not replace the committed primary analysis, select targets, run TREAT,
perform enrichment, rank candidates, score druggability, correct the
expression matrix, or make causal claims. Any instability is reported
factually for later scientific review.
