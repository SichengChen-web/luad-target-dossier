# TCGA-LUAD sample-level QC and design diagnostics

Generated: 2026-08-14 03:24:37 UTC

## Scope and verified input

Task #004 reloaded the unique TCGA-LUAD recount3 project as a gene-level `RangedSummarizedExperiment`, pinned to `gencode_v26`. The verified input had 63856 gene rows, 601 expression-record columns, and the sole assay `raw_counts`. The run used R 4.5.1, recount3 1.20.0, SummarizedExperiment 1.40.0, edgeR 4.8.2, and limma 3.66.0.

## 1. From expression records to biological samples

The input contained 601 expression records. 2 record(s) were explicitly excluded because their official GDC sample type was not `Primary Tumor` or `Solid Tissue Normal`. The remaining 599 eligible records mapped to 587 distinct GDC `sample_id` values. Counts for records sharing the same verified sample ID were summed gene by gene, leaving 528 Primary Tumor samples and 59 Solid Tissue Normal samples.
12 sample IDs required technical aggregation, and 12 redundant expression-record columns were collapsed. All invariant biological metadata agreed within each of those sample IDs. `technical_aggregation_audit.csv` traces all original records, including exclusions, to a final sample column where applicable.
The required sample-level case, sample, sample-type, group, batch, and tissue-source-site fields had no missing values in the retained cohort.

## 2. Why counts were summed

Expression records and aliquots below the same verified GDC sample are technical representations of one biological sample, so documented edgeR `sumTechReps()` was used to sum their counts. Summing preserves the total sequencing evidence. Different `sample_id` values were never combined, even when they came from one case, because they are distinct biological samples that may require repeated-measures handling later.

## 3. What the DGEList contains

An edgeR `DGEList` is an in-memory container with a gene-by-sample raw read-count table, per-sample information (including library sizes, group, case, batch, and tissue-source site), and per-gene annotation. Here the annotation retains Ensembl ID, gene symbol/name, and gene type. All gene types were retained; the analysis was not restricted to protein-coding genes because no such scientific filtering decision has yet been made.

## 4. Low-expression filtering

edgeR `filterByExpr()` used the tumour-versus-normal biological group to identify genes with enough reads in a worthwhile number of samples. Of 63,856 genes before filtering, 29,927 were retained and 33,929 were removed (46.87% retained). This is independent expression-sufficiency filtering, not differential-expression testing. Removing very low-expression genes reduces uninformative tests and helps later mean-variance estimation.

## 5. TMM normalization

After filtering, library sizes were recalculated from the retained raw counts and edgeR TMM factors were computed. Factors ranged from 0.53022 to 1.2919 (median 1.0136). Effective library size is raw filtered library size multiplied by the TMM factor. TMM adjusts the scale used by downstream methods for compositional differences; it does not rewrite counts or force equal library sizes. This is distinct from recount3 `compute_read_counts()`, which converts base-pair coverage to estimated integer read counts using average mapped read length.

## 6. Exploratory MDS, PCA, and RLE

MDS summarizes leading pairwise expression differences among samples. PCA summarizes major variance directions in TMM-aware log-CPM values; PC1 and PC2 explain 11.63% and 6.67%. RLE-style summaries subtract each gene's across-sample median log-CPM, then report each sample's median and IQR of those relative values. These are exploratory descriptions, not sample-exclusion tests.
For a readable numerical view of structure, eta-squared for PC1 was 0.491 by group, 0.091 by batch, and 0.149 by tissue-source site. The corresponding PC2 values were 0.052, 0.142, and 0.232. These descriptive fractions do not establish causation.

## 7. Sample-quality observations

Filtered raw library sizes ranged from 10,266,455 to 204,277,530. Sample RLE medians ranged from -0.16467 to 0.15777, and RLE IQRs ranged from 0.69088 to 2.7648. These ranges show heterogeneity worth reviewing in the figures, but no prespecified rule establishes an obvious sample failure here. No sample was removed or labelled an outlier.
The PCA and RLE figures nevertheless show a visibly separated low-PC2/high-RLE-spread subset of Primary Tumor samples concentrated at Christiana Healthcare. This is a concrete quality/structure concern for follow-up against source metadata, but it is not sufficient grounds for exclusion in this task.

## 8. Batch and tissue-source-site overlap after aggregation

At sample level, 20 CGC batch levels were present: 7 contained both groups, 13 were tumour-only, and 0 were normal-only.
33 tissue-source-site levels were present: 7 contained both groups, 26 were tumour-only, and 0 were normal-only.
Batch and tissue-source site formed 130 observed combinations. 20 of 20 batches spanned more than one site, while 28 of 33 sites spanned more than one batch. They are related but not interchangeable variables. Group-limited levels create potential confounding; no ComBat or other batch correction was performed.

## 9. Candidate design diagnostics only

- Design A (`~group`): 587 samples, 2 coefficients, rank 2, residual df 585, full rank = TRUE, tumour-vs-normal estimable = TRUE; no non-estimable columns.
- Design B (`~group + batch_number`): 587 samples, 21 coefficients, rank 21, residual df 566, full rank = TRUE, tumour-vs-normal estimable = TRUE; no non-estimable columns.
- Design C (`~group + tissue_source_site`): 587 samples, 34 coefficients, rank 34, residual df 553, full rank = TRUE, tumour-vs-normal estimable = TRUE; no non-estimable columns.
- Design D (`~group + batch_number + tissue_source_site`): 587 samples, 53 coefficients, rank 53, residual df 534, full rank = TRUE, tumour-vs-normal estimable = TRUE; no non-estimable columns.

The cohort has 517 unique cases; 64 contribute more than one biological sample; 58 have both tumour and normal samples; and 12 have multiple same-group Primary Tumor samples. No design was selected and no model was fitted. `case_id` remains reserved for later repeated-measures/blocking decisions.

## 10. Matched-case subset and no position-based exclusion

Among the 58 matched cases, 52 have exactly one tumour and one normal sample, 6 have multiple tumour samples, and 0 have multiple normal samples. No sample was chosen arbitrarily and no paired analysis was run. A distant PCA or MDS position can reflect biology, technical variation, or both; without an independent failure criterion it is not sufficient grounds for exclusion.

## 11. Decisions still unresolved before differential expression

- Whether the later analysis should use all samples, a matched subset, or both.
- How to model repeated biological samples and case-level pairing/blocking.
- Whether batch, tissue-source site, or neither belongs in the final design.
- How to address the observed tumour/normal imbalance.
- Whether any sample has independent technical evidence justifying exclusion.
- Whether additional gene-type restrictions are scientifically justified.

## Explicitly not performed

This task did **not** perform:

- differential-expression testing;
- `voomLmFit`;
- `eBayes`;
- `topTable`;
- batch correction;
- candidate-gene selection;
- scoring.

