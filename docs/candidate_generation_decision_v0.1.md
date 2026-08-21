# Candidate Generation Decision v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Task:** #008 — DE-derived candidate registry  
**Version:** v0.1  
**Date:** 20 August 2026  
**Status:** Frozen candidate-generation decision

## Purpose

Task #008 converts the committed Task #006 primary differential-expression
result and the committed Task #007 sensitivity results into one auditable
gene-level registry and a first-pass evidence-retrieval queue. It does not
select therapeutic targets.

Differential expression remains a candidate-generation signal. No registry
field or queue assignment establishes causality, druggability, therapeutic
direction, clinical actionability, safety, or novelty.

## Frozen inputs

The required starting/base commit is
`14df4a18d7e67e6d9f0d0b4a3d39b3a6b712a15a`. The builder reads only the
committed Task #006 and Task #007 files named in Task #008:

- the Task #006 primary DE table (`S0`);
- the six Task #007 sensitivity DE tables (`S1`–`S6`);
- the Task #007 model-dependent-gene table;
- the Task #007 reduced-residual-df table;
- the Task #007 model-level comparison table.

The script requires the frozen base commit to be an ancestor of current HEAD
and requires these committed inputs to be unchanged relative to that base.
No external identifier or evidence source is queried.

## Identifier policy

`EnsemblID` from Task #006 is the immutable internal primary key. The original
value, including any version suffix, is never overwritten. `EnsemblID_base`
removes only a terminal dot followed by digits, for example
`ENSG00000123456.7` → `ENSG00000123456`.

`Symbol` and `gene_type` are preserved from S0. S1–S6 must contain the same
identifier universe and must agree with S0 where those annotations are
present. HGNC, UniProt, Open Targets, and ChEMBL identifier fields are reserved
as `NOT_RETRIEVED`; Task #008 performs no external mapping.

## Master universe and candidate layers

All 29,606 S0-tested genes remain in `candidate_registry.csv`.

| Field | Deterministic definition |
|---|---|
| `U0_tested` | `TRUE` for every registry row |
| `U1_DE` | `FDR_S0 < 0.05` |
| `U2_effect_supported_DE` | `FDR_S0 < 0.05` and `abs(logFC_S0) >= 0.5` |

The inequalities reproduce the prespecified definitions exactly. They do not
create a therapeutic-target threshold.

## Descriptive effect bands

| Band | Definition |
|---|---|
| `A` | `abs(logFC_S0) >= 2` |
| `B` | `1 <= abs(logFC_S0) < 2` |
| `C` | `0.5 <= abs(logFC_S0) < 1` |
| `D` | `abs(logFC_S0) < 0.5` |

These bands describe primary expression effect size only. They are not
additional statistical tests.

## Biotype tracks

- `canonical_protein_target` when `gene_type == "protein_coding"`;
- `noncanonical_target_modality` for every other `gene_type`.

Non-protein-coding genes remain in the master registry and may enter the
noncanonical retrieval queue.

## Robustness features

S1–S6 are joined to S0 by exact `EnsemblID`. For sign comparisons:

- `UP` means `logFC > 0`;
- `DOWN` means `logFC < 0`;
- `ZERO` means `logFC == 0` exactly.

These are expression directions, not therapeutic directions.

The registry retains `logFC` and BH FDR for S0–S6 and derives:

- the number of S1–S6 signs matching S0;
- whether all six sensitivity signs match S0;
- the number of sensitivities with BH FDR below 0.05;
- median and maximum absolute logFC change from S0;
- whether S6 flips sign relative to S0;
- whether the gene appears in any committed model-dependent top-50 list and
  the contributing models;
- whether reduced residual df was reported, the contributing models, and the
  largest reported df loss.

No composite robustness score is created. Significance or direction changes
do not remove a gene.

## Retrieval-queue assignment

`retrieval_queue` is a mutually exclusive workflow label, not a rank. Queue
assignment uses the following precedence:

1. `NOT_PRIMARY_DE` when `U1_DE == FALSE`.
2. `DE_SMALL_EFFECT` when `U1_DE == TRUE` and
   `U2_effect_supported_DE == FALSE`.
3. `QUEUE_C_NONCANONICAL` for U2 genes whose `gene_type` is not
   `protein_coding`.
4. `QUEUE_B_MODEL_SENSITIVE` for protein-coding U2 genes when at least one
   sensitivity sign differs from S0 **or** the gene occurs in a committed
   model-dependent top-50 list.
5. `QUEUE_A_CANONICAL` for all remaining protein-coding U2 genes.

Queue B therefore takes precedence over Queue A for a sign-stable gene that
nevertheless appears in a model-dependent top-50 list. This resolves the
logical overlap in the stated criteria without adding a score or target-value
judgment.

`candidate_queue.csv` contains every U2 gene and only U2 genes. Row order in
both registry files inherits the committed S0 table order. That order is not a
therapeutic-target ranking.

## Output interpretation

The registry is an auditable bridge between transcriptomic discovery and
future evidence retrieval. Future evidence fields and missingness rules are
defined in `target_evidence_schema_v0.1.md`. All external evidence remains
unretrieved in Task #008.

Task #008 does not produce:

- a final target list;
- an actionability or under-exploration rank;
- a numerical score or scoring weight;
- a therapeutic activation/inhibition recommendation;
- a causality, druggability, safety, clinical, or novelty conclusion.

## Frozen validation expectations

The builder must fail unless:

- S0 contains exactly 29,606 unique `EnsemblID` values;
- every S1–S6 table contains exactly the same identifier set;
- `U1_DE` contains exactly 21,232 genes;
- `U2_effect_supported_DE` contains exactly 14,064 genes;
- the candidate queue contains exactly all U2 genes;
- no score, final rank, or therapeutic-direction field is emitted.
