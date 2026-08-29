# Task #039B.1 validation report

MMP11 is being used as an illustrative biological worked example. External evidence is organized to demonstrate provenance-aware evidence synthesis and does not constitute a project-level therapeutic target ranking, validation, or recommendation.

Overall validation: **PASS**

| Check | Result | Detail |
|---|---|---|
| `frozen_target_identity` | **PASS** | Exact EnsemblID and display symbol reconcile to Task #039A. |
| `frozen_task039a_hashes_pinned` | **PASS** | Task #039A inputs match their reviewed SHA256 values. |
| `pubmed_special_study_identity` | **PASS** | PMID 31024988 reconciles to exact title, PMCID, and DOI. |
| `raw_payload_integrity` | **PASS** | Every retained raw payload matches its frozen SHA256. |
| `unique_publication_ids` | **PASS** | No duplicate publication identifiers. |
| `unique_evidence_units` | **PASS** | No duplicate bounded evidence-unit identifiers. |
| `evidence_identity` | **PASS** | All project-side evidence joins use immutable EnsemblID. |
| `controlled_evidence_status` | **PASS** | All evidence statuses use the controlled vocabulary. |
| `traceable_evidence` | **PASS** | Every evidence unit has a publication and provenance link. |
| `included_publications_have_evidence` | **PASS** | Every included publication supplies at least one bounded evidence unit. |
| `model_publication_links` | **PASS** | Experimental-model publication foreign keys reconcile. |
| `dataset_model_references_resolve` | **PASS** | Every evidence dataset/cohort reference resolves to the dataset or model registry. |
| `disease_context_complete` | **PASS** | Every evidence unit has disease/histology context. |
| `provenance_status_complete` | **PASS** | Every evidence unit has provenance status. |
| `dataset_accessions_unique` | **PASS** | Dataset registry identifiers are unique. |
| `tcga_overlap_explicit` | **PASS** | TCGA-LUAD reuse is explicitly linked to Task #039A. |
| `publication_dependency_complete` | **PASS** | Every evidence unit has publication-level dependency. |
| `dependency_vocabulary` | **PASS** | Dependency relationships use allowed concepts. |
| `exclusion_reasons_complete` | **PASS** | All excluded screening records have reasons. |
| `null_context_retained` | **PASS** | Null and context-dependent evidence are retained. |
| `no_false_clinical_development` | **PASS** | No clinical-development unit was created without a relevant trial. |
| `clinicaltrials_false_positives_retained` | **PASS** | All five ClinicalTrials.gov lexical false positives are retained in the exclusion log. |
| `search_roles_explicit` | **PASS** | Every registered search has an allowed explicit search role. |
| `formal_denominator_roles_only` | **PASS** | Only primary-screening and overlap-orientation records contribute to the publication denominator. |
| `formal_publication_denominator` | **PASS** | Formal screening frame is 30 complete PubMed broad-query records plus 7 unique Task #039A orientation records. |
| `europe_pmc_supplementary_not_exhaustive` | **PASS** | Europe PMC's 1,383-hit high-recall query is explicitly supplementary and not exhaustively screened. |
| `clinicaltrials_outside_publication_denominator` | **PASS** | ClinicalTrials.gov lexical hits remain a separate clinical-development check. |
| `task039b_registry_counts_frozen` | **PASS** | Publication, evidence, provenance, and dependency counts remain frozen. |
| `forbidden_fields_absent` | **PASS** | No score/rank/recommendation/therapeutic-direction fields. |
| `frozen_inputs_unchanged` | **PASS** | Task #039A frozen inputs are byte-unchanged. |
| `task039b_biological_hashes_pinned` | **PASS** | All Task #039B biological registries retain their pre-patch SHA256 values. |
| `task039b_biological_content_unchanged` | **PASS** | Task #039B biological evidence content is byte-unchanged from the pre-patch state. |

## Reproducibility statement

- Deterministic transformation of the frozen retrieved payloads: **validated by repeat execution in completion checks**.
- Mutable external retrieval: **not claimed to be byte-identical in the future**.
- Retrieval timestamp: `2026-08-29T02:58:29Z`.
- Generator: `MMP11_EXTERNAL_EVIDENCE_ACQUISITION_GENERATOR_V0.1.1`.
- Documentation patch: `TASK039B_1_SEARCH_COVERAGE_PATCH_V0.1`.
