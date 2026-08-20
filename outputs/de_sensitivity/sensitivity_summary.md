# Prespecified DE sensitivity-analysis summary

Generated: 2026-08-15 20:37:16 UTC

## Frozen reference and reconstruction

The committed Task #006 primary result was used as S0 and was not refitted. The frozen 29,606 × 574 DGEList was reconstructed once from exact cached TCGA-LUAD/gencode_v26 files. The Task #005 gene mask and TMM factors matched their committed references.

Every sensitivity used the explicit `Tumor - Normal` contrast; positive logFC means higher expression in Tumor. `batch_number`, where present, is `tcga.cgc_case_batch_number`: TCGA/BCR case-batch structure, not a proven RNA-seq sequencing batch.

## Exact model results

- **S1 — Omit case blocking:** formula `~ 0 + group + batch_number`; block `NULL`; sample.weights `FALSE`; design 574 × 21, rank 21, nominal residual df 553, genes below nominal residual df 22, normalized condition number 6.49623, block correlation not applicable, Pearson/Spearman logFC correlation with S0 0.999423/0.999113, sign concordance 0.98784.
- **S6 — Matched pairs only:** formula `~ 0 + group + case_id`; block `NULL`; sample.weights `FALSE`; design 116 × 59, rank 59, nominal residual df 57, genes below nominal residual df 2910, normalized condition number 15.1656, block correlation not applicable, Pearson/Spearman logFC correlation with S0 0.98548/0.984541, sign concordance 0.949368.
- **S2 — Omit TCGA/BCR case-batch adjustment:** formula `~ 0 + group`; block `case_id`; sample.weights `FALSE`; design 574 × 2, rank 2, nominal residual df 572, genes below nominal residual df 6, normalized condition number 1, block correlation 0.2541907, Pearson/Spearman logFC correlation with S0 0.993523/0.985845, sign concordance 0.945957.
- **S3 — TSS instead of TCGA/BCR case-batch:** formula `~ 0 + group + tissue_source_site`; block `case_id`; sample.weights `FALSE`; design 574 × 34, rank 34, nominal residual df 540, genes below nominal residual df 720, normalized condition number 9.99713, block correlation 0.2126154, Pearson/Spearman logFC correlation with S0 0.996222/0.992202, sign concordance 0.958725.
- **S4 — TCGA/BCR case-batch plus TSS:** formula `~ 0 + group + batch_number + tissue_source_site`; block `case_id`; sample.weights `FALSE`; design 574 × 53, rank 53, nominal residual df 521, genes below nominal residual df 726, normalized condition number 14.7282, block correlation 0.2198958, Pearson/Spearman logFC correlation with S0 0.99819/0.997383, sign concordance 0.979869.
- **S5 — Sample-quality weights:** formula `~ 0 + group + batch_number`; block `case_id`; sample.weights `TRUE`; design 574 × 21, rank 21, nominal residual df 553, genes below nominal residual df 22, normalized condition number 6.49623, block correlation 0.1339702, Pearson/Spearman logFC correlation with S0 0.997168/0.996029, sign concordance 0.971695.

Singular values and column-L2-normalized condition numbers are descriptive diagnostics only; no arbitrary pass/fail threshold was applied.

## Top-gene and FDR overlap

- **S1:** top-100/top-500 intersections 97/488; BH FDR < 0.05 intersection 20563 and Jaccard 0.962417.
- **S2:** top-100/top-500 intersections 77/431; BH FDR < 0.05 intersection 19879 and Jaccard 0.87538.
- **S3:** top-100/top-500 intersections 88/459; BH FDR < 0.05 intersection 20021 and Jaccard 0.903271.
- **S4:** top-100/top-500 intersections 90/444; BH FDR < 0.05 intersection 20488 and Jaccard 0.948562.
- **S5:** top-100/top-500 intersections 86/446; BH FDR < 0.05 intersection 21052 and Jaccard 0.90957.
- **S6:** top-100/top-500 intersections 54/322; BH FDR < 0.05 intersection 19814 and Jaccard 0.871903.

## Largest model-dependent genes

- **S1:** PRAME (Δ=0.39112); SLCO1B3 (Δ=0.32028); FGB (Δ=0.31830); SOX11 (Δ=-0.31748); PRSS2 (Δ=-0.30968)
- **S2:** CLC (Δ=-0.72844); PAGE1 (Δ=-0.64329); HOXB13 (Δ=-0.63379); ZDHHC11B (Δ=0.62027); AC104809.4 (Δ=0.61852)
- **S3:** PAGE1 (Δ=-0.54841); MAGEA1 (Δ=-0.51164); LA16c-312E8.4 (Δ=0.48886); INSL4 (Δ=-0.47332); IL17REL (Δ=0.47065)
- **S4:** RPS4Y1 (Δ=-0.62756); TXLNGY (Δ=-0.56415); ZIC1 (Δ=0.52623); GYG2P1 (Δ=-0.51389); EIF1AY (Δ=-0.50757)
- **S5:** BPIFA1 (Δ=0.73385); BPIFB1 (Δ=0.56956); MUC5B (Δ=0.50977); SCGB1A1 (Δ=0.49647); BPIFA2 (Δ=0.48999)
- **S6:** TFF2 (Δ=2.8330); PAX7 (Δ=2.5264); MUC6 (Δ=2.4932); CNMD (Δ=2.3469); MAGEC2 (Δ=2.1569)

These genes are ranked only by absolute `delta_logFC`; the list does not rank model quality or select therapeutic targets.

## S5 sample-quality weights

S5 weights ranged from 0.3037179 to 4.526745, with median 0.9746942. No sample was removed.

The descriptive median weight was 2.542658 for Normal and 0.9384622 for Tumor. The Pearson/Spearman associations with RLE IQR were -0.4835854/-0.7387007; associations with effective library size were -0.2291465/-0.1942765. These diagnostics did not trigger sample exclusion or model selection.

## S6 matched-pairs-only analysis

S6 used exactly 58 matched cases (116 observations), retained all 29,606 frozen genes, recalculated library sizes and TMM factors after sample subsetting, and used case_id fixed effects without blocking. Reduced statistical significance is expected from the reduction from 574 to 116 observations and is not by itself evidence of effect-size instability.

## Runtime

- frozen_DGE_reconstruction: 11.645 elapsed seconds.
- S1: 14.285 elapsed seconds.
- S6: 18.466 elapsed seconds.
- S2: 13309.2 elapsed seconds.
- S3: 13374.13 elapsed seconds.
- S4: 13421.16 elapsed seconds.
- S5: 21547.03 elapsed seconds.
- combined_comparison_output_generation: 1.023 elapsed seconds.
- total_Task_007_execution: 61696.94 elapsed seconds.

## Interpretation boundary

The six prespecified sensitivities are robustness diagnostics. No model replaces the committed primary result based on DE counts. Task #007 did not run a seventh model, TREAT, enrichment, target selection, candidate ranking, druggability analysis, batch correction, or causal inference.

