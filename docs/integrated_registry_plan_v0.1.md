# Integrated Target Evidence Registry Plan v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Task:** #012 — integrated target evidence registry  
**Version:** v0.1  
**Date:** 21 August 2026  
**Status:** Implemented integration plan

## Purpose and scientific boundary

Task #012 creates a single one-gene-per-row registry by joining the frozen Task #008–#011 evidence layers. It integrates evidence without ranking genes, scoring targets, prioritizing candidates, selecting targets, recommending interventions, interpreting therapeutic suitability, or inferring therapeutic direction.

The integrated row order is inherited from the frozen Task #008 candidate registry and has no ranking meaning.

## Frozen inputs

The read-only inputs and pinned SHA256 values are:

| Layer | File | SHA256 |
|---|---|---|
| Task #008 candidate/DE/robustness | `outputs/candidate_registry/candidate_registry.csv` | `8055a9d99d058d219399957e62f6a3cccc3dd2217bc028d1d11dd4dc667f90e2` |
| Task #009 identifiers | `outputs/identifier_normalization/identifier_mapping.csv` | `ff50b9cc50006710e681bd0d0f21fa3790becc3cd20a476dbbb6ac5459c1594e` |
| Task #010 external evidence | `outputs/evidence_layer/evidence_registry.csv` | `13b6db140c920a60ae3f827ac9df4c4e08916472aa8daafb349acd3a60192405` |
| Task #011 tractability/safety | `outputs/tractability_safety/tractability_safety_registry.csv` | `83d085383c60ecc68815ad02c12ae74ef52e67a45501880581bc53276b658f84` |

The builder fails before integration if any hash differs.

## Join and identity policy

Versioned `EnsemblID` is the only join key. Gene symbols are never used as join keys. The builder independently requires each input to contain exactly 29,606 unique EnsemblIDs and requires identical identifier order across all four inputs.

For every row it cross-validates `EnsemblID_base`, `Symbol`, and `gene_type` across all layers; U2 membership across Tasks #008, #010, and #011; Open Targets IDs across Tasks #009–#011; and ChEMBL IDs across Tasks #009–#010. The Task #008 placeholder external identifiers must remain exactly `NOT_RETRIEVED` and are replaced in the integrated view by the audited Task #009 mappings rather than treated as competing identifiers.

## Integrated evidence domains

The registry retains:

- identity: immutable Ensembl ID, base Ensembl ID, symbol, and gene type;
- audited HGNC, Entrez, UniProt, Open Targets, and ChEMBL mappings, including mapping sources and ambiguity states;
- Task #008 U0/U1/U2 membership and effect/biotype/retrieval tracks;
- primary S0 differential-expression statistics;
- S1–S6 effect and FDR fields plus sign, sensitivity, model-dependence, and residual-degrees-of-freedom robustness diagnostics;
- Task #010 Open Targets target annotations, count-only literature fields, LUAD direct/indirect association evidence, and drug/candidate counts;
- Task #010 ChEMBL target availability and source annotations;
- Task #011 source-native tractability status/count summaries and positive assessment identifiers by modality;
- Task #011 safety-liability retrieval status and record counts.

Task #010 fields ending in `_score_native` are source-native Open Targets association values. They are retained as frozen evidence, not generated or interpreted as project scores.

## Explicit missingness

No missing mapping or absent returned evidence is converted to negative biological evidence. Source states such as `NOT_FOUND`, `NOT_AVAILABLE`, `NOT_MAPPED`, `NO_ASSOCIATION_RETURNED`, `TARGET_NOT_MAPPED`, and `TARGET_PRESENT_NO_SAFETY_RECORD_RETURNED` remain explicit.

Each output row includes deterministic `integrated_missingness_status_json` covering identifier mappings, target annotations, LUAD associations, tractability, and safety. This field records source states without collapsing them into a numerical feature.

An empty Task #008 model list controlled by a `FALSE` flag is represented as `NONE`; an empty Task #009 mapping note is represented as `NONE`; otherwise unexplained empty scalar fields are represented as `NOT_AVAILABLE`. The output contains no blank cells.

Most importantly, `TARGET_PRESENT_NO_SAFETY_RECORD_RETURNED` means absence of retrieved curated evidence and must not be interpreted as evidence of safety.

## Validation and QC

The build fails unless:

- all four frozen input hashes match;
- every input has exactly 29,606 unique EnsemblIDs;
- identifier sets and order match exactly;
- all cross-layer identity, U2, and external-ID assertions pass;
- exactly 14,064 U2 genes remain;
- every output cell has an explicit value;
- no exact forbidden project field is emitted;
- the integrated table remains in original EnsemblID order.

The QC table reports input-hash assertions, row/identity assertions, all-gene and U2 coverage, mapping/retrieval missingness-state counts, DE/robustness flags, Open Targets/ChEMBL availability, tractability records, and safety-liability records.

## Reproducibility

The builder uses only Python standard-library modules and performs no network access. `session_info.txt` records timestamps, environment details, input hashes, output hashes, join policy, row counts, and explicit non-generation of scoring, ranking, recommendations, or therapeutic direction.

No package is installed or updated. No existing Task #001–#011 file is modified.

## Forbidden outputs and non-claims

The integrated schema does not contain the exact project fields `score`, `ranking`, `priority`, `rank`, `recommendation`, `therapeutic_direction`, or `target_selection`.

Task #012 does not claim that evidence volume, a source-native association score, a positive tractability assessment, drug/candidate availability, or a safety-liability state establishes causality, target quality, clinical actionability, safety, or therapeutic value.
