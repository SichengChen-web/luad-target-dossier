# Task #012 integrated target evidence registry summary

**Genes retained:** 29,606  
**U2 genes retained:** 14,064  
**Immutable join key:** `EnsemblID` only

## Purpose and interpretation boundary

This registry joins the frozen Task #008–#011 evidence layers into one gene-level table. It preserves identity, differential-expression, robustness, identifier, Open Targets, drug/candidate, tractability, and safety evidence without ranking, scoring, prioritizing, recommending, selecting, or inferring therapeutic direction.

Open Targets fields explicitly ending in `_score_native` are source-native upstream evidence values. They are not project-defined scores and were not used to order or select genes.

## Integrated coverage

| Scope | Genes | OT mapped | LUAD direct association | OT drug/candidate count >0 | Tractability record(s) | Safety record(s) |
| --- | --- | --- | --- | --- | --- | --- |
| All tested genes | 29606 | 28893 | 8393 | 1443 | 16894 | 898 |
| U2 genes | 14064 | 13691 | 4871 | 815 | 8014 | 520 |

Identifier coverage:

| Identifier | All mapped | U2 mapped |
| --- | --- | --- |
| HGNC_ID | 24474 | 11647 |
| Entrez_ID | 24268 | 11544 |
| UniProt_ID | 17699 | 8441 |
| OpenTargets_target_ID | 28893 | 13691 |
| ChEMBL_target_ID | 5963 | 2767 |

## Robustness evidence retained

The integrated table preserves the Task #008 primary DE fields and all prespecified S1–S6 robustness diagnostics, including sign concordance, sensitivity FDR counts, effect-size deviations, S6 sign flips, model-dependence flags, and residual-degrees-of-freedom flags. No new DE analysis or model fitting was performed.

## Explicit missingness

Source retrieval and mapping states are preserved rather than converted into negative biological evidence. Each row also contains `integrated_missingness_status_json`, which records mapping, target retrieval, LUAD association, tractability, and safety states without collapsing them.

In particular, `TARGET_PRESENT_NO_SAFETY_RECORD_RETURNED` means no curated record was returned for that mapped target. It does not mean the target is safe or has low risk. Likewise, `NO_ASSOCIATION_RETURNED`, `NOT_FOUND`, `NOT_AVAILABLE`, and `TARGET_NOT_MAPPED` remain explicit evidence states rather than zero-valued evidence.

Upstream empty model-set fields are represented as `NONE`; absent mapping notes are represented as `NONE`; otherwise unexplained empty cells are represented as `NOT_AVAILABLE`. No integrated output cell is blank.

## Evidence-overlap boundary

Open Targets tractability may incorporate ChEMBL or clinical-precedence sources. It must not automatically be treated as independent of Task #010 drug/candidate evidence or future clinical-development evidence.

## Non-claims

The row order is the frozen Task #008 EnsemblID order and has no ranking meaning. No project score, rank, priority, recommendation, target selection, or therapeutic direction was generated.
