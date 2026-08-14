# TCGA-LUAD cohort structure and count diagnostics

Generated: 2026-08-14 02:16:27 UTC

## Scope and verified input

Task #003 reloaded the verified TCGA-LUAD gene-level `RangedSummarizedExperiment` with annotation `gencode_v26`. The object contains 63856 gene features and 601 expression columns, and its only assay is `raw_counts`.

## 1. Why 601 columns are not 601 independent patients

The 601 expression columns represent sequencing/expression records, not independent people. They map to 517 cases, 589 samples, and 600 aliquots. Repeated records at any level can create dependence that a later model must address.

## 2. Case, sample, aliquot, and expression record

- A **case** is the patient-level GDC record.
- A **sample** is a biospecimen collected from a case, such as tumour or normal tissue.
- An **aliquot** is a processed portion derived from a sample.
- An **expression record** is one column in the recount3 RSE, identified by its column/external ID.

The observed hierarchy is:

`case → sample → aliquot → expression record`

- Cases with multiple expression records: 66.
- Cases with multiple distinct sample IDs: 66.
- Cases with multiple distinct Primary Tumor sample IDs: 12.
- Samples with multiple distinct aliquot IDs: 11.
- Aliquots with multiple expression records: 1.

The 1 duplicate-aliquot pair(s) were compared gene by gene. Exact identity: FALSE; Pearson correlation: 0.998923; maximum absolute difference: 3792529. No duplicate was selected or removed.

## 3. Provisional primary-comparison status

599 records have sample type `Primary Tumor` or `Solid Tissue Normal`; 2 other records are not eligible for that comparison. Statuses are descriptive only and do not finalize a cohort.

- `eligible_unambiguous`: 562
- `excluded_nonprimary_sample_type`: 2
- `review_multiple_aliquots_same_sample`: 22
- `review_multiple_expression_same_aliquot`: 2
- `review_multiple_samples_same_case_and_group`: 13

The primary `provisional_status` above is mutually exclusive and uses the most specific observed repeat level (aliquot record, then sample aliquot, then case/group sample). Because review conditions can overlap, the ledger also retains independent Boolean flags. Their non-mutually-exclusive record counts are:

- `review_multiple_expression_same_aliquot`: 2
- `review_multiple_aliquots_same_sample`: 22
- `review_multiple_samples_same_case_and_group`: 35

The 562 `eligible_unambiguous` records are straightforward candidates based only on sample type and the repeat structures checked here. Review statuses remain unresolved; no first row, random row, average, sum, largest library, or highest mapped-read record was chosen.

## 4. What `compute_read_counts()` produced

Using recount3 `compute_read_counts(round = TRUE)` produced an 63856 × 601 matrix in memory. It converts raw base-pair coverage to estimated read counts by dividing each column by its average mapped read length and rounding. This is not normalization: it does not make library sizes equal or correct composition effects. The complete matrix was not saved.
Average mapped length had 0 missing, 0 zero, 0 negative, and 0 non-finite values before conversion; the same checks were repeated after conversion.
The read-count matrix contained 0 NA, 0 NaN, 0 infinite, and 0 negative values.

## 5. Gene read-count library-size diagnostics

- All expression records (n = 601): min 10,362,782, Q1 39,721,583, median 52,072,250, mean 57,776,827, Q3 74,422,793, max 124,642,938.
- Primary Tumor (n = 540): min 10,362,782, Q1 40,759,337, median 53,449,959, mean 58,859,774, Q3 75,622,582, max 124,642,938.
- Solid Tissue Normal (n = 59): min 23,418,571, Q1 33,978,050, median 40,509,332, mean 46,677,171, Q3 53,035,602, max 91,045,027.

Gene-level read-count library size versus STAR all mapped reads had Pearson correlation 0.909181 and Spearman correlation 0.907134 across 601 complete records. This is a sanity diagnostic, not proof that every mapped read belongs to an annotated gene.

## 6. Tumour/normal overlap across batch and tissue-source site

Among eligible records, 20 CGC batch levels were present and 7 contained both tumour and normal records.
33 tissue-source sites were present and 7 contained both tumour and normal records. Levels containing only one group make group/batch or group/site separation a potential modelling concern, but no correction was attempted.
Sequencing platform had 1 non-missing level(s): Illumina HiSeq. Sequencing center had 1 non-missing level(s): University of North Carolina.

## 7. Decisions still unresolved

The following still require an explicit scientific decision:

- how to resolve multiple expression records from one aliquot;
- how to handle multiple aliquots from one sample;
- how to handle multiple same-group samples from one case;
- whether and how to use matched tumour-normal pairs;
- the final eligible cohort and independence structure;
- whether batch or tissue-source-site variables belong in the later model;
- gene filtering, count normalization, and the differential-expression design.

## 8. Explicitly not performed

This task did **not** perform:

- gene filtering;
- normalization;
- TMM;
- PCA exclusion;
- differential expression;
- candidate-gene selection;
- batch correction;
- scoring.

