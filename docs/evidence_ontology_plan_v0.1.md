# Evidence Ontology and Independence Plan v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Task:** #013 — evidence ontology and independence framework  
**Version:** v0.1  
**Date:** 21 August 2026  
**Status:** Implemented metadata architecture

## Purpose and boundaries

Task #013 defines how evidence in the integrated registry is named, traced, and assessed for dependency before any future aggregation. It creates architecture, not scientific conclusions.

This task does not rank, score, prioritize, recommend, select, or infer therapeutic direction for any target. It introduces no numerical weights, independence penalties, confidence values, or aggregation formula.

## Why evidence independence matters

Apparent agreement is informative only to the extent that the observations have distinct lineages. Two columns can look like separate evidence while deriving from the same samples, transformation, database record, publication, compound, trial, or upstream aggregator. Counting those columns separately can create false certainty without adding a genuinely independent observation.

Independence in this framework is therefore about evidence generation and lineage, not simply about different field names, API endpoints, or output files. An `INDEPENDENT` classification means no source-lineage dependency was identified for that specific pair under documented assumptions. It does not prove statistical independence or make either evidence type sufficient.

## Why evidence count is not confidence

Evidence counts report retrieved records or source-native summaries. They do not automatically measure causal support, quality, reproducibility, or confidence.

Examples in the current registry include:

- S0 and S1–S6 statistics are related analyses of the same TCGA expression cohort, not seven independent replications.
- Open Targets direct and indirect LUAD associations overlap because the indirect view expands through the disease ontology.
- Multiple literature records may describe the same underlying experiment or claim.
- Multiple tractability buckets share one Open Targets framework and can reuse ChEMBL or clinical-precedence information.
- Multiple safety records can share a datasource, publication, study, event, or mechanism.

Therefore, more records or more positive source buckets do not necessarily mean greater independent support.

## Controlled evidence domains

The v0.1 ontology defines eight evidence domains:

1. transcriptomic discovery;
2. disease association;
3. genetic evidence;
4. functional dependency;
5. pharmacology;
6. tractability;
7. clinical development;
8. safety.

Each domain is defined by a distinct biological or translational question in `evidence_domain_registry.csv`. Genetic evidence, functional dependency, and clinical development are future-compatible domains: the ontology reserves their scientific roles but does not assert that Task #012 already contains dedicated evidence for them.

Identifier normalization and evidence integration are provenance infrastructure rather than additional biological evidence domains. Joining records into Task #012 improves auditability but does not create an independent observation.

## Source lineage

`evidence_source_lineage.csv` distinguishes original datasets, delivery/processing layers, external aggregators, and project-derived artifacts:

- TCGA-LUAD is the underlying biological expression dataset.
- recount3 is the uniformly processed delivery/annotation layer for that TCGA dataset, not an independent cohort.
- the project S0–S6 outputs are derived analyses of the same frozen expression cohort.
- Open Targets is a multi-source aggregator supporting disease association, drug/candidate, tractability, and safety fields.
- ChEMBL provides target annotations now and is a future pharmacology source; some Open Targets evidence may reuse ChEMBL.
- the Task #012 integrated registry is a derived integration artifact and contains no new scientific observation.

Every evolving source or derived artifact requires version tracking. Open Targets Task #010 and Task #011 fields share data release 26.06/API 26.6.3 and must not be assumed independent merely because they were retrieved in separate tasks.

## Qualitative relationship categories

The independence map permits only:

| Category | Meaning |
|---|---|
| `INDEPENDENT` | No source-lineage dependency is currently identified for the stated pair and assumptions |
| `PARTIALLY_DEPENDENT` | Some upstream records, cohorts, concepts, or provider lineage may overlap |
| `DERIVED_FROM_SAME_SOURCE` | Both evidence types derive from the same cohort, source object, analysis family, or directly overlapping view |
| `UNKNOWN` | Required lineage is unavailable or the future source has not been selected |

Dependency levels are qualitative metadata only: `NONE_IDENTIFIED`, `PARTIAL`, `HIGH`, and `UNRESOLVED`. They are not numbers and must not be converted into penalties without a separately reviewed scientific specification.

## Rules for future aggregation

Future evidence aggregation must operate at the evidence-domain level rather than summing raw features.

1. Within a domain, source fields describe, qualify, or challenge the same scientific question. They are not automatically separate votes.
2. Direct duplicates and known shared-source views must be collapsed or represented once for aggregation purposes while retaining their raw audit records.
3. Partially dependent evidence requires record-level lineage review and explicit overlap handling.
4. Unknown relationships remain unknown; they must not be assumed independent.
5. Cross-domain convergence may be considered only after checking pairwise lineage and scientific compatibility.
6. Missing records remain missing and must not be converted into negative evidence or safety.
7. Conflicting evidence must remain visible; aggregation must not hide inconsistency.
8. Any future weights or numerical model require a separate versioned specification, sensitivity analysis, and validation protocol.

These rules prevent a large collection of correlated fields from dominating simply because one source exposes many columns or records.

## Important current dependencies

- TCGA logFC, FDR, and model-sensitivity fields share the same cohort and analysis lineage.
- Open Targets direct and indirect LUAD association views overlap.
- Open Targets association, literature, drug/candidate, tractability, and safety fields share a Platform release and may share upstream data.
- ChEMBL pharmacology can overlap Open Targets drug/candidate and tractability evidence.
- Open Targets clinical-precedence tractability can overlap future trial evidence.
- Future genetic evidence may share TCGA samples or may already contribute to Open Targets association evidence.

The independence map records these boundaries as qualitative relationships with reasons and future warnings. It does not create scores.

## Safety and missingness boundary

Safety is a separate scientific assessment block. Open Targets safety evidence and TCGA expression are treated as source-lineage independent in the current map, but this does not mean either is conclusive.

Most importantly, absence of a curated safety-liability record means absence of retrieved evidence, not evidence of safety. Presence of a liability likewise does not automatically determine target rejection.

## Frozen input and validation

The framework is grounded in the committed Task #012 registry:

`outputs/integrated_registry/integrated_target_registry.csv`

Pinned Task #012 SHA256:

`0587fc6901267b18c8144644571f89ac2cc46053b57ea5def4093795fdbc4c26`

The builder also verifies the committed Task #010–#012 evidence-layer plans by hash. It requires 29,606 unique EnsemblIDs, exactly 14,064 U2 genes, the expected integrated evidence fields, and valid explicit missingness JSON.

Output validation requires all mandated columns, all eight controlled domains, valid source-to-domain references, defined evidence types, unique unordered evidence pairs, and only allowed relationship categories. It fails if prior committed files have working-tree modifications or if any required frozen file differs from the Task #012 base.

## Outputs

- `evidence_domain_registry.csv`: controlled domains and their scientific questions.
- `evidence_source_lineage.csv`: provider, data type, supported domains, and known dependencies.
- `evidence_independence_map.csv`: qualitative pairwise relationships, reasons, and aggregation warnings.
- `evidence_ontology_summary.md`: counts, central rules, and warnings.
- `session_info.txt`: hashes, environment, Git provenance, input validation, and explicit non-generation of scoring/ranking.

Only Python standard-library modules are used. No network access or package installation is required.

## Explicit non-claims

This ontology does not determine target quality, causal validity, actionability, safety, clinical readiness, therapeutic direction, priority, or rank. It is a versioned framework for preventing double-counting and making later scientific assumptions auditable.
