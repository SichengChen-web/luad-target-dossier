# Final canonical TCGA-LUAD RNA cohort and QC

Generated: 2026-08-14 06:59:14 UTC

## Scope and software

The original TCGA-LUAD recount3 `gencode_v26` object contained 63856 genes and 601 expression records. This run used R 4.5.1, recount3 1.20.0, SummarizedExperiment 1.40.0, edgeR 4.8.2, and limma 3.66.0.

## 1. Why Task #004's 587 observations were provisional

Task #004 grouped every primary tumour/normal record by GDC `sample_id` before the lower biospecimen hierarchy had been audited. Task #004B then showed that one GDC sample can contain biologically consequential distinct RNA aliquots, so most of those apparent repeats could not be assumed to be technical lanes or summed safely.

## 2. Evidence-backed exclusions

The two official `Recurrent Tumor` records were outside the primary groups. Twelve primary-tumour records with current GDC `is_ffpe == TRUE` were excluded because they are current sample-level FFPE records and were the A277 01B/01C records responsible for the prior low-PC2 cluster.
A separate exact list of 12 A278 aliquots was excluded because Task #004B source-traced each barcode to the historical annotation `Item is noncanonical; FFPE Validation`. They are described as historically annotated noncanonical FFPE-validation aliquots—not as current GDC FFPE samples. No exclusion was generalized from vial letter or plate code.

## 3. The one justified technical aggregation

After exclusions, only TCGA-38-4625-01 remained repeated. Its two records have the same UUID-defined case, GDC sample, vial, portion, RNA analyte, exact aliquot, and biological sample type. They share Illumina HiSeq RNA-seq and UNC center metadata, but have distinct filenames, file IDs, experiment IDs, run IDs, recount3 IDs, and library sizes. Their raw read-count correlation is Pearson 0.9989. These two gene-count columns were therefore summed as sequencing replication of one exact RNA aliquot. No other records were summed.

## 4. Final cohort and case structure

The frozen cohort has 574 biological observations: 515 Primary Tumor and 59 Solid Tissue Normal, from 516 unique cases. There are 58 matched tumour-normal cases, 457 tumour-only cases, and 1 normal-only case. No case has multiple observations within either biological group.

## 5. Gene filtering and TMM after cohort cleanup

All gene types were retained initially. Final-cohort `filterByExpr()` kept 29,606 of 63,856 genes; Task #004 had kept 29,927 of 63,856. After filtering, library sizes were recalculated and TMM factors were recomputed from scratch. Final factors range from 0.63407 to 1.2939 (median 1.0096), compared with Task #004's 0.53022 to 1.2919 (median 1.0136). TMM changes downstream scaling; it does not rewrite the raw counts.

## 6. From-scratch PCA, MDS, and RLE assessment

All coordinates and RLE summaries were recomputed using only the final cohort. PC1 and PC2 explain 12.28% and 5.68%. The exact 12 current-FFPE records are absent. The final cohort contains 62 Christiana observations; 2 are among the 12 lowest PC2 values and 0 are among the 12 highest RLE-IQR values. More directly, the 12 prior FFPE-affected cases contribute 11 retained canonical Primary Tumor observations; 1 is among the 12 lowest PC2 values and 0 are among the 12 highest RLE-IQR values. Those retained tumours exactly occupy the lowest 11 PC2 positions = FALSE. Thus the previous discrete FFPE-defined low-PC2 cluster is absent after the prespecified exclusions.
Final RLE IQR ranges from 0.69331 to 2.0818; 2 final observations exceed 2. No sample was excluded because of its PCA, MDS, library-size, TMM, or RLE position.

## 7. Batch, tissue-source-site, and candidate designs

The final cohort contains 20 CGC batch levels; 7 contain both groups. It contains 33 tissue-source-site levels; 7 contain both groups. 20 batches span more than one TSS, and 28 TSS levels span more than one batch. The contingency tables show the remaining imbalance and confounding.
- Design A (`~group`): n = 574, coefficients = 2, rank = 2, residual df = 572, full rank = TRUE, tumour-vs-normal estimable = TRUE; no non-estimable coefficients.
- Design B (`~group + batch_number`): n = 574, coefficients = 21, rank = 21, residual df = 553, full rank = TRUE, tumour-vs-normal estimable = TRUE; no non-estimable coefficients.
- Design C (`~group + tissue_source_site`): n = 574, coefficients = 34, rank = 34, residual df = 540, full rank = TRUE, tumour-vs-normal estimable = TRUE; no non-estimable coefficients.
- Design D (`~group + batch_number + tissue_source_site`): n = 574, coefficients = 53, rank = 53, residual df = 521, full rank = TRUE, tumour-vs-normal estimable = TRUE; no non-estimable coefficients.

## 8. Decision still unresolved before differential expression

The final statistical design is not yet selected. The next scientific decision must determine whether batch, tissue-source site, neither, or a different justified adjustment belongs in the model, and how the 58 matched cases should be handled relative to the much larger unpaired cohort. These diagnostics describe estimability; they do not choose a model.

## Explicitly not performed

This task did **not** perform:

- `voomLmFit`;
- `eBayes`;
- `topTable`;
- differential-expression testing;
- batch correction;
- candidate selection;
- scoring.

