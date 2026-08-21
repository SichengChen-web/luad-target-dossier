# Task #013 evidence ontology and independence summary

**Evidence domains:** 8  
**Source-lineage records:** 6  
**Evidence dependency relationships:** 31  
**Scoring or ranking created:** No

## Controlled evidence domains

| Domain ID | Domain | Scientific question |
| --- | --- | --- |
| DOM_TRANSCRIPTOMIC_DISCOVERY | Transcriptomic discovery | Is the gene reproducibly and substantially dysregulated in LUAD tumour tissue relative to normal tissue? |
| DOM_DISEASE_ASSOCIATION | Disease association | Is the target associated with LUAD, and what source-derived evidence supports that association? |
| DOM_GENETIC_EVIDENCE | Genetic evidence | Do inherited or tumour-acquired genetic alterations support a causal role for the target in LUAD biology? |
| DOM_FUNCTIONAL_DEPENDENCY | Functional dependency | Does experimental perturbation of the target alter LUAD-relevant cellular fitness or function? |
| DOM_PHARMACOLOGY | Pharmacology | Is there source-grounded pharmacological evidence that compounds interact with or modulate the target? |
| DOM_TRACTABILITY | Tractability | What source-derived evidence indicates that the target can be modulated by a small molecule, antibody, PROTAC, or other clinical modality? |
| DOM_CLINICAL_DEVELOPMENT | Clinical development | Has target modulation or a closely related therapeutic strategy reached relevant human clinical investigation? |
| DOM_SAFETY | Safety | What source-grounded observations indicate possible on-target or target-related safety liabilities, in what context, and from which evidence lineage? |

## Source lineage

| Source ID | Source | Domains |
| --- | --- | --- |
| SRC_TCGA_LUAD | TCGA Lung Adenocarcinoma RNA-seq | DOM_TRANSCRIPTOMIC_DISCOVERY |
| SRC_RECOUNT3_TCGA_LUAD | recount3 TCGA-LUAD gencode_v26 representation | DOM_TRANSCRIPTOMIC_DISCOVERY |
| SRC_PROJECT_DE_ROBUSTNESS | Project primary DE and prespecified S1-S6 sensitivity analyses | DOM_TRANSCRIPTOMIC_DISCOVERY |
| SRC_OPEN_TARGETS_PLATFORM | Open Targets Platform | DOM_DISEASE_ASSOCIATION\|DOM_PHARMACOLOGY\|DOM_TRACTABILITY\|DOM_SAFETY |
| SRC_CHEMBL | ChEMBL | DOM_PHARMACOLOGY\|DOM_TRACTABILITY |
| SRC_PROJECT_INTEGRATED_REGISTRY | Task #012 integrated target evidence registry | DOM_TRANSCRIPTOMIC_DISCOVERY\|DOM_DISEASE_ASSOCIATION\|DOM_PHARMACOLOGY\|DOM_TRACTABILITY\|DOM_SAFETY |

## Dependency categories

| Relationship | Count |
| --- | --- |
| DERIVED_FROM_SAME_SOURCE | 12 |
| INDEPENDENT | 2 |
| PARTIALLY_DEPENDENT | 15 |
| UNKNOWN | 2 |

The map uses qualitative categories only. It creates no numerical independence penalty, correlation coefficient, weight, score, or rank.

## Central aggregation rules

- Multiple fields derived from the same cohort or source object are not independent votes. In particular, S0-S6 models are robustness views of the same expression data; Open Targets direct/indirect associations overlap; and tractability buckets share one framework.
- Evidence counts measure retrieved records or source-native summaries, not confidence. Several records can share a datasource, study, publication, compound, trial, or upstream database.
- Future aggregation must operate at the evidence-domain level. Within-domain features first describe and qualify that domain; convergence across domains is considered only after source lineage and pairwise dependencies are reviewed.
- Missing evidence remains missing. Absence of a returned association, tractability, pharmacology, or safety record is not converted into negative biological evidence.
- An `INDEPENDENT` label means no source-lineage dependency was identified for the stated evidence pair under the stated assumptions. It does not mean statistical independence, biological sufficiency, or certainty.

## Important current warnings

- TCGA logFC, FDR, and S1-S6 stability are derived from the same cohort and cannot be counted separately as replicated evidence.
- Open Targets disease association, literature, drug/candidate, tractability, and safety fields share a Platform release and may share upstream records.
- ChEMBL-derived pharmacology can overlap Open Targets tractability and drug/candidate evidence.
- Absence of an Open Targets safety-liability record is absence of retrieved evidence, not evidence of safety.
- Future genetic, functional, and clinical sources require a new lineage review before their independence categories are finalized.

## Validation

All required columns, controlled domain names, source-domain references, evidence-type references, relationship categories, and dependency levels validated. The frozen integrated registry remained unchanged at 29,606 unique EnsemblIDs and 14,064 U2 genes. No prior committed file was modified.

No target ranking, scoring, prioritization, recommendation, selection, or therapeutic interpretation was generated.
