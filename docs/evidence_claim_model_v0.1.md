# Evidence Claim and Provenance Model v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Task:** #014 — evidence claim and provenance architecture  
**Version:** v0.1  
**Date:** 21 August 2026  
**Status:** Implemented interpretation architecture

## Purpose and boundaries

Task #014 defines how evidence is expressed as bounded claims, linked to traceable records and source entities, annotated for dependency, and kept explicit when missing or uncertain.

It does not rank, score, prioritize, recommend, select, infer therapeutic direction, or determine therapeutic value. Supporting-record counts are audit counts only; they are not confidence measures.

## Layer 1: evidence claims

An evidence claim is a bounded statement answering one scientific question for one immutable Ensembl gene in one Task #013 evidence domain. It reports an evidence state without extending beyond what the source can support.

Examples of permitted claim scope include:

- an Ensembl gene has a recorded TCGA-LUAD tumour-versus-normal transcriptomic result;
- an Ensembl gene has a recorded Open Targets LUAD association evidence state;
- an Ensembl gene has a recorded pharmacology-annotation evidence state;
- an Ensembl gene has a recorded modality-specific tractability evidence state;
- an Ensembl gene has a recorded safety-liability evidence state.

Claims may state that a source record was present, absent, not mapped, or not queried. They do not say that a gene is a good target, should be inhibited or activated, is safe, is the best candidate, or has therapeutic value.

The current architecture instantiates five claims for every one of the 29,606 genes: transcriptomic discovery, disease association, pharmacology, tractability, and safety. The future-compatible genetic, functional-dependency, and clinical-development domains remain explicitly `NOT_QUERIED` at the domain level rather than being instantiated as negative gene-level claims.

`supporting_record_count` counts traceable records with a positive bounded observation status. It is not a score and does not imply that the records are independent.

## Layer 2: evidence records

An evidence record is the smallest unit that can be traced to a source row or source-native summary without misleadingly splitting related scalar fields into separate observations.

Each gene has seven record slots:

1. primary S0 transcriptomic result;
2. S1–S6 robustness result;
3. Open Targets LUAD association record;
4. Open Targets drug/candidate count record;
5. ChEMBL target-annotation record;
6. Open Targets tractability summary record;
7. Open Targets safety-liability summary record.

The `raw_value_reference` points to the frozen Task #012 `EnsemblID` row and the exact fields represented. It does not use a gene symbol as an identifier. The `source_record_identifier` is a stable project pointer to that source-specific record slot.

A record row is retained when its source observation is absent or was not queried. In those cases its `missingness_status` is explicit and the record is not included in the claim's supporting count. This preserves the difference between a defined retrieval returning no record and a retrieval that could not be performed.

Open Targets direct and indirect LUAD association fields are kept together in one evidence record because the views overlap. Tractability modalities are kept together in one source summary because their buckets share a framework. ChEMBL target presence remains target metadata and is not relabeled compound activity, potency, mechanism, or clinical evidence.

## Layer 3: source entities

A source entity represents an evidence origin or transformation layer separately from individual evidence records. The current registry preserves the six Task #013 source identities:

- TCGA-LUAD biological cohort;
- recount3 processed TCGA-LUAD representation;
- project primary/sensitivity DE analyses;
- Open Targets Platform;
- ChEMBL;
- Task #012 derived integration registry.

Each entity records provider, source type, version or version pointer, retrieval information, and dependency notes. The Task #012 integration is explicitly a derived artifact, not a new scientific observation.

The current frozen input does not expose publication-, compound-, or trial-level records as independent rows. Therefore no publication, compound, or trial source entity is invented in v0.1. Future retrieval tasks must create separate source entities for those origins and link their records directly.

## Dependency representation

`evidence_dependency_graph.csv` links observed evidence records using only the controlled relationships:

- `SAME_SOURCE`;
- `SHARED_PUBLICATION`;
- `SHARED_DATASET`;
- `SHARED_COMPOUND`;
- `SHARED_TRIAL`;
- `UNKNOWN`.

Dependency level is separately recorded as `INDEPENDENT`, `PARTIALLY_DEPENDENT`, `DEPENDENT`, or `UNKNOWN`. No numerical dependency value is created.

Primary and robustness transcriptomic records are always connected by `SHARED_DATASET`/`DEPENDENT`. Observed Open Targets records receive `SAME_SOURCE` edges where Task #013 establishes a shared Platform lineage. Possible ChEMBL/Open Targets overlap that cannot be resolved from gene-level summaries uses `UNKNOWN` with `PARTIALLY_DEPENDENT` and a required record-level review status.

Edges are instantiated only when both records are observed. Absence of an edge does not prove independence; the Task #013 evidence-type independence map remains authoritative for higher-level relationships and future sources.

## Missingness semantics

The controlled missingness states are:

| Category | Meaning |
|---|---|
| `OBSERVED` | The defined analysis or source retrieval produced the represented record/state |
| `NOT_FOUND` | The source was queried for the mapped target but returned no corresponding evidence record |
| `NOT_QUERIED` | The source could not be queried because no mapping existed, or the future evidence domain has not been retrieved |
| `NOT_APPLICABLE` | The retrieval concept does not apply to the entity, such as an external query for a local integration artifact |
| `UNKNOWN` | Required source or retrieval lineage has not yet been selected or resolved |

`NOT_FOUND` and `NOT_QUERIED` are not negative biological evidence. A source-native numeric count of zero is an observed retrieval result and remains zero; it is not silently changed to missing or interpreted as a therapeutic conclusion.

Most importantly, absence of a returned safety-liability record means absence of retrieved evidence, not evidence of safety.

## Uncertainty handling

The controlled uncertainty categories are:

| Category | Meaning |
|---|---|
| `SOURCE_LIMITATION` | The source answers only a bounded question and cannot establish a broader conclusion |
| `INCOMPLETE_COVERAGE` | Identifier or public-database coverage may omit relevant evidence |
| `CONFLICTING_RECORDS` | Prespecified records or analyses conflict, such as an expression sensitivity sign conflict |
| `DEPENDENCY_UNCERTAIN` | Cross-source or cross-domain record overlap is possible but unresolved |
| `TEMPORAL_UNCERTAINTY` | An evolving external database can change across releases |

Uncertainty is retained alongside observations. It is not converted into a numerical confidence deduction, and conflicting records are not removed.

## Preventing evidence inflation

Future aggregation must use the Task #013 evidence domains and Task #014 record lineage rather than summing raw columns or record counts.

1. Related scalar fields from one source row remain one record.
2. S0 and S1–S6 records remain dependent views of the same expression dataset.
3. Direct and indirect Open Targets disease associations remain one overlapping source record.
4. Tractability modality buckets remain one record and cannot become multiple votes.
5. Open Targets and ChEMBL records require overlap review before being treated as separate evidence.
6. Missing records do not contribute negative evidence.
7. Supporting-record counts remain audit metadata and do not become confidence scores.
8. Any future numerical aggregation requires a separate versioned scientific specification, dependency-aware model, sensitivity analysis, and validation protocol.

## Frozen inputs and reproducibility

The architecture is grounded in these hash-pinned inputs:

- Task #012 integrated registry: `0587fc6901267b18c8144644571f89ac2cc46053b57ea5def4093795fdbc4c26`;
- Task #013 domain registry: `ee62ce66f2ca4726c9365da347198251b9bd77d2dead87b8409221505f2d03b8`;
- Task #013 source lineage: `e9496e8bbf953fdffdbaed7e09936a8493230fc74939597537f8960fabf19f2c`;
- Task #013 independence map: `d99bbaa8fe5e6229774ac2bf73d84de8fbd367e585d692eb1273ecc7b5c53945`.

At execution, Task #012 was committed and unchanged. Task #013 artifacts were still uncommitted review outputs, so Task #014 treats them as immutable hash-pinned inputs and does not modify them. The session file records that state explicitly.

The builder requires 29,606 unique EnsemblIDs and exactly 14,064 U2 genes, validates Task #013 schemas and counts, and checks every output relationship.

Only Python standard-library modules are used. No network access or package installation is required.

## Validation guarantees

The builder fails unless:

- all frozen hashes match;
- no previous committed file is modified;
- every claim, record, source, and dependency identifier is unique;
- every gene has exactly five current-domain claims and seven record slots;
- every claim links to a valid Task #013 domain;
- every record links to a valid claim and source entity;
- every dependency links to two valid observed records;
- claim supporting-record counts reconcile exactly to supporting observation statuses;
- all missingness and uncertainty values use the controlled vocabularies;
- all five missingness and all five uncertainty categories are represented;
- no forbidden output field is created.

## Explicit non-claims

This architecture does not determine target validity, causal status, safety, actionability, clinical readiness, quality, priority, rank, selection, recommendation, therapeutic direction, or therapeutic value.
