# Candidate Generation Summary

**Task:** #008  
**Frozen input base:** `14df4a18d7e67e6d9f0d0b4a3d39b3a6b712a15a`  
**External evidence retrieval:** none

## Result

The registry retains all **29,606** genes tested in the primary
Tumor–Normal analysis. Differential expression is used only to generate
candidates for later evidence retrieval; these outputs do not select or rank
therapeutic targets.

## Candidate layers

- U0 tested: **29,606**
- U1 primary BH FDR < 0.05: **21,232**
- U2 U1 plus |primary logFC| ≥ 0.5: **14,064**

## Primary-effect bands

- A, |logFC| ≥ 2: **2,542**
- B, 1 ≤ |logFC| < 2: **4,814**
- C, 0.5 ≤ |logFC| < 1: **7,005**
- D, |logFC| < 0.5: **15,245**

## Biotype tracks

- Protein-coding (`canonical_protein_target`): **17,656**
- All other gene types (`noncanonical_target_modality`): **11,950**

## First-pass retrieval queues

- Queue A — canonical: **8,188**
- Queue B — model-sensitive: **133**
- Queue C — noncanonical: **5,743**
- Primary DE with small effect: **7,168**
- Not primary DE: **8,374**

Queues A–C contain all **14,064** U2 genes. Queue membership is a retrieval
workflow label, not a target rank or statement of target quality.

## Sensitivity observations

- Genes whose expression sign is stable across all S1–S6: **26,171**
- Unique genes in at least one committed model-dependent top-50 list: **261**
- Genes whose S6 expression sign differs from S0: **1,499**

These features describe model robustness. No composite robustness score was
created, and no gene was removed because of a sensitivity result.

## Identifier audit

- Malformed Ensembl IDs: 0
- Ensembl IDs without a terminal version suffix: 0
- Duplicate `EnsemblID_base` values: 0
- Missing gene symbols: 0
- Duplicated non-empty symbol values: 60 (covering 139 genes; maximum multiplicity 9)

Repeated symbols are not treated as identifiers. The unique, versioned
`EnsemblID` remains the immutable key, and the version-free identifier is kept
only as a separate convenience field. External identifier fields remain
`NOT_RETRIEVED`.

## Explicit non-claims

Task #008 generated no final target rank, numerical score, therapeutic
direction, causality claim, druggability conclusion, clinical actionability
claim, or novelty claim. The target-evidence schema defines what later
milestones may retrieve and normalize.
