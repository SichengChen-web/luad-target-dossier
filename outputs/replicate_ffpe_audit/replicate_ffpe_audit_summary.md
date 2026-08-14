# TCGA-LUAD RNA replicate and FFPE audit

Generated: 2026-08-14 04:31:10 UTC

## Scope

This audit reloaded the original 63856 × 601 TCGA-LUAD recount3 `gencode_v26` object and inspected all 937 current `colData()` fields. It did not filter, normalize, aggregate, delete, or perform differential-expression analysis.

## 1. Why GDC sample_id alone was insufficient

A GDC `sample_id` identifies the current sample entity, but one such entity can still contain more than one RNA aliquot or more than one recount3 expression record. In this dataset, 11 RNA analytes have multiple aliquots, and one aliquot has two recount3 expression records. Therefore, matching only on `sample_id` does not prove that columns are sequencing lanes or technical replicates that should be summed.

## 2. Biospecimen hierarchy and validated barcode parser

The documented TCGA hierarchy used here is:

`case → TCGA sample type → vial → portion → analyte → aliquot → recount3 expression record`

A vial is an ordered subdivision of a TCGA sample; a portion is material cut from the vial; an analyte is the molecular material extracted from the portion; and an aliquot is a plate/well distribution of that analyte. The letter `R` is the RNA analyte code. `A278` occupies the plate segment of the aliquot barcode—it is not a sample, vial, portion, or analyte code.
All 601 aliquot barcodes matched the documented structure, and every aliquot was reconstructed exactly. Case, vial, analyte, sample-type code, and analyte code agreed with current recount3/GDC metadata. Two FFPE records have inconsistent parallel portion metadata: TCGA-44-6146-01B-04R-A277-07 encodes portion 04 while the portion fields say 03, and TCGA-44-4112-01B-06R-A277-07 encodes portion 06 while those fields say 05. The validation table preserves these discrepancies.

## 3. What current colData can and cannot tell us

Current `tcga.gdc_cases.samples.is_ffpe` identifies 12 records as FFPE; the parallel CGC field agrees. All are the 12 Christiana 01B/01C A277 RNA records.
No preservation-method, tumour-descriptor, or tissue-type field is present in this recount3 `colData()`. Sample- and portion-level annotation columns exist but contain no values for these 601 records. The field inventories make these absences explicit rather than filling them by guesswork.

## 4. The 12 Christiana B/C records and the Task #004 anomaly

The 12 lowest PC2 sample-level values from Task #004 are exactly the 12 current GDC FFPE 01B/01C samples: TRUE. All 12 have RLE IQR above 2.0; 11 of them occupy the 12 highest RLE-IQR ranks. Thus FFPE status explains the discrete low-PC2 cluster and most of the extreme RLE spread, although high RLE is not unique to FFPE records.
The archived 2016 LUAD FFPE report independently lists these exact A277 RNA barcodes as `Item is noncanonical` with note `FFPE`. This audit does not delete them; it labels them `ffpe_exclude_candidate` provisionally.
PCA, RLE, and TMM columns are carried over from Task #004. For a B/C sample with one expression record they are record-specific; for an 01A sample with two aliquots they describe the previously aggregated GDC sample and are explicitly labelled `aggregated_sample_level_not_record_specific`. They must not be interpreted as separate A278-versus-older-aliquot metrics.

## 5. What A278 represents

There are 12 current A278 RNA aliquots. Current GDC sample-level `is_ffpe` is FALSE for them because they belong to 01A sample entities. However, the archived 2014 GDAC FFPE report lists every exact A278 RNA barcode here as `Item is noncanonical` / `FFPE Validation`. This is aliquot-level historical evidence that is absent from current `colData()`.
11 of the 12 A278 records have an older aliquot from the same current GDC RNA analyte; the TCGA-44-3917 A278 record has no older RNA aliquot in this recount3 object. Nine pairs are also explicitly present in the cited 2017 GDAC mRNA replicate table, where the generic later-plate rule chose A278. The two remaining current pairs are not independently listed as mRNA pairs in that snapshot.
For the 11 current A278/older-aliquot pairs, raw reconstructed read-count Pearson correlations range from 0.04462 to 0.3745. Record-level library sizes, mapped-read fields, and pairwise correlations are retained in the A278 and pairwise-QC tables without normalization or summing.
These historical records encode two different ideas: GDAC's generic replicate filter preferred a later plate, while the earlier FFPE report identified A278 as noncanonical FFPE-validation material. For a canonical non-FFPE cohort, the latter evidence is directly relevant; the apparent conflict must not be hidden by summing the two aliquots.

## 6. Why sumTechReps() was not automatically justified

The repeated 01A columns are distinct aliquots of the same RNA analyte, not documented sequencing lanes. One aliquot may be canonical material while the A278 aliquot is historical FFPE-validation material. Summing would mix different biospecimen statuses and erase the evidence needed to choose the canonical observation. The separate TCGA-38-4625 case contains two recount3 records for the exact same aliquot, but even there this audit does not choose or aggregate a record because their provenance and count differences require a dedicated decision.

## 7. Provisional decision table

The repeated-sample table uses only the requested provisional labels:

- `canonical_candidate`: 11
- `ffpe_exclude_candidate`: 24
- `replicate_review`: 2

`canonical_candidate` marks non-FFPE 01A RNA records where a competing historical FFPE/FFPE-validation record exists. `ffpe_exclude_candidate` marks current FFPE or exact historically noncanonical FFPE-validation barcodes. `replicate_review` marks the unresolved exact-aliquot duplicate. No label has been applied as a cohort operation.

## 8. What a canonical non-FFPE scenario would look like

Starting with 599 primary tumour/normal expression records, a provisional rule that removes the 12 current FFPE A277 records and the 12 historical FFPE-validation A278 records would leave 575 candidate records: 516 Primary Tumor and 59 Solid Tissue Normal.
Those records represent 574 TCGA sample barcodes and 516 cases. One TCGA sample barcode still has two recount3 records for the same aliquot, so a true one-record-per-sample cohort would contain 574 observations only after that separate replicate choice is justified. This scenario is descriptive and was not applied.

## 9. Evidence sources

- [GDC TCGA Barcode documentation](https://docs.gdc.cancer.gov/Encyclopedia/pages/TCGA_Barcode/) — barcode hierarchy.
- [GDC Portion / Analyte Codes](https://gdc.cancer.gov/resources-tcga-users/tcga-code-tables/portion-analyte-codes) — `R` means RNA.
- [Broad GDAC 2014 FFPE Cases](https://gdac.broadinstitute.org/runs/stddata__2014_04_16/samples_report/FFPE_Cases.html) — exact A278 noncanonical FFPE-validation annotations.
- [Broad GDAC 2016 LUAD FFPE Cases](https://gdac.broadinstitute.org/runs/stddata__latest/samples_report/LUAD_FFPE_Cases.html) — exact B/C A277 noncanonical FFPE annotations.
- [Broad GDAC 2017 Replicate Samples](https://gdac.broadinstitute.org/runs/gdc/report_2017_10_29/Replicate_Samples.html) — later-plate RNA replicate-selection records.

## Explicitly not performed

- gene filtering or normalization;
- TMM recalculation or new PCA/RLE analysis;
- record aggregation or deletion;
- differential-expression testing;
- batch correction;
- final cohort selection.

