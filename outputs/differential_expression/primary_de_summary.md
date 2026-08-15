# Primary TCGA-LUAD differential-expression analysis

Generated: 2026-08-14 14:35:16 UTC

## Frozen input reconstruction

Task #006 reconstructed the pinned TCGA-LUAD recount3 gene-level `gencode_v26` object from exact already-cached files without a network download. The 574-observation Task #005 manifest was reproduced exactly: 515 Primary Tumor, 59 Solid Tissue Normal, 516 unique cases, and 58 matched tumor-normal cases. Only the frozen two-record same-aliquot aggregation for `TCGA-38-4625-01` was applied.
The authoritative Task #005 gene mask retained 29606 of 63856 genes. An independent `filterByExpr()` assertion matched that mask exactly. TMM factors were reconstructed with maximum absolute difference 5.107026e-15 versus the stored Task #005 factors, within the prespecified strict tolerance 1e-12.

## Primary model

The fixed-effect design was `~ 0 + group + batch_number`.

`batch_number` came specifically from `tcga.cgc_case_batch_number`. It is a TCGA/BCR case-batch structure used as a prespecified nuisance adjustment. It is not described as a proven RNA-seq sequencing, lane, library-preparation, or run batch.
The design was 574 × 21 with rank 21 and nominal fixed-effect residual df 553. `case_id` was used only as the blocking variable in `voomLmFit`; it was not a fixed effect. `sample.weights = FALSE`, while ordinary voom observation-level precision weights remained enabled.
The estimated consensus intra-case correlation was 0.2432825. The explicit contrast was `Tumor_vs_Normal = Tumor - Normal`: positive logFC means higher expression in Tumor and negative logFC means lower expression in Tumor.

## Differential-expression results

All 29606 frozen genes were tested for the null hypothesis logFC(Tumor - Normal) = 0. BH FDR was used for multiple-testing control. No fold-change cutoff was part of the primary hypothesis test.
- BH FDR < 0.05: 21232 total (10841 Up; 10391 Down).
- BH FDR < 0.01: 18930 total (9539 Up; 9391 Down).
- BH FDR < 0.05 and |logFC| >= 0.5: 14064 total (6831 Up; 7233 Down).
- BH FDR < 0.05 and |logFC| >= 1: 7340 total (3223 Up; 4117 Down).
- BH FDR < 0.05 and |logFC| >= 2: 2542 total (1056 Up; 1486 Down).
`mean_logCPM_Tumor` and `mean_logCPM_Normal` are descriptive, unadjusted group means of TMM-aware log-CPM. They are not model-adjusted coefficients.

## Diagnostics

Gene-specific residual df had min 485, Q1 553, median 553, mean 552.9799, Q3 553, and max 553. 22 genes were below the nominal maximum 553.
The voom mean-variance plot, empirical-Bayes plotSA diagnostic, MD plot, raw-P-value histogram, residual-df histogram, and communication-oriented volcano plot are saved under `figures/`. An excess of small raw P values is not automatically interpreted as statistical inflation in this strong Tumor-versus-Normal biological comparison.

## Scope boundary

Task #006 fitted exactly one primary model. None of the six prespecified Task #007 sensitivity analyses was fitted. This task did not run TREAT, pathway enrichment, target selection, candidate ranking, druggability scoring, batch correction, or expression-matrix correction.
