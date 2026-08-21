# Target-Evidence Schema v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Version:** v0.1  
**Date:** 20 August 2026  
**Status:** Frozen field-level schema; external evidence not yet retrieved

## Schema principles

This schema defines fields that later milestones may populate from approved
sources. Task #008 populates only transcriptomic-discovery and sensitivity
fields. A row or evidence record must remain traceable to its source.

Missing evidence is not negative evidence. Source-native scores must remain
source-native and must not be treated as cross-source probabilities. No
scoring weights, therapeutic directions, or target rankings are defined here.

Allowed missingness states are defined in section 15. Until retrieval occurs,
reserved external fields use `NOT_RETRIEVED` rather than an unsupported value.

## 1. Identifiers

| Field | Meaning | Data type | Expected source class | Missing allowed | Role |
|---|---|---|---|---|---|
| `EnsemblID` | Immutable versioned internal gene key from Task #006 | string | Project transcriptomic analysis | No | metadata |
| `EnsemblID_base` | Ensembl gene identifier without terminal numeric version | string | Derived from `EnsemblID` | No | metadata |
| `Symbol` | Gene symbol preserved from Task #006 | string | Project transcriptomic analysis | Yes | metadata |
| `gene_type` | GENCODE v26 gene biotype | categorical string | GENCODE/recount3 annotation | No | metadata |
| `HGNC_ID` | HGNC identifier | string | HGNC or approved mapping source | Yes | metadata |
| `UniProt_ID` | UniProt accession | string or delimited list | UniProt or approved mapping source | Yes | metadata |
| `OpenTargets_target_ID` | Open Targets target identifier | string | Open Targets | Yes | metadata |
| `ChEMBL_target_ID` | ChEMBL target identifier | string or delimited list | ChEMBL | Yes | metadata |
| `identifier_mapping_status` | Mapping outcome using the missingness vocabulary | categorical string | Evidence normalizer | No | metadata |
| `identifier_mapping_note` | Ambiguity, one-to-many mapping, or version note | string | Evidence normalizer | Yes | metadata |

## 2. Transcriptomic discovery

| Field | Meaning | Data type | Expected source class | Missing allowed | Role |
|---|---|---|---|---|---|
| `discovery_dataset_id` | Identifier for the LUAD expression dataset | string | Project configuration/recount3 | No | metadata |
| `discovery_analysis_version` | Version of the primary DE analysis | string | Project analysis | No | metadata |
| `comparison_definition` | Tumor-versus-normal comparison definition | string | Project analysis | No | metadata |
| `logFC_S0` | Primary Tumor minus Normal log2 fold change | number | Task #006 | No | evidence |
| `FDR_S0` | Primary BH-adjusted p-value | number in [0,1] | Task #006 | No | evidence |
| `P_value_S0` | Primary unadjusted p-value | number in [0,1] | Task #006 | No | evidence |
| `AveExpr_S0` | Primary model average log-expression summary | number | Task #006 | No | evidence |
| `mean_logCPM_Tumor` | Mean log-CPM in the final Tumor cohort | number | Task #006 | Yes | evidence |
| `mean_logCPM_Normal` | Mean log-CPM in the final Normal cohort | number | Task #006 | Yes | evidence |
| `U0_tested` | Gene belonged to the frozen tested universe | boolean | Task #008 deterministic rule | No | future derived metric |
| `U1_DE` | Primary BH FDR below 0.05 | boolean | Task #008 deterministic rule | No | future derived metric |
| `U2_effect_supported_DE` | U1 plus absolute primary logFC at least 0.5 | boolean | Task #008 deterministic rule | No | future derived metric |
| `effect_band` | Descriptive A/B/C/D primary-effect band | categorical string | Task #008 deterministic rule | No | future derived metric |
| `biotype_track` | Canonical protein or noncanonical modality track | categorical string | Task #008 deterministic rule | No | future derived metric |
| `retrieval_queue` | First-pass evidence-retrieval workflow label | categorical string | Task #008 deterministic rule | No | future derived metric |

## 3. Sensitivity robustness

| Field | Meaning | Data type | Expected source class | Missing allowed | Role |
|---|---|---|---|---|---|
| `logFC_S1`–`logFC_S6` | Tumor-minus-Normal logFC from each prespecified sensitivity | six numbers | Task #007 | No | evidence |
| `FDR_S1`–`FDR_S6` | BH FDR from each prespecified sensitivity | six numbers in [0,1] | Task #007 | No | evidence |
| `sign_S0` | `UP`, `DOWN`, or exact `ZERO` expression sign | categorical string | Task #008 deterministic rule | No | future derived metric |
| `sign_concordant_S1_S6_count` | Number of sensitivity signs matching S0 | integer 0–6 | Task #008 deterministic rule | No | future derived metric |
| `sign_concordant_all_S1_S6` | All six sensitivity signs match S0 | boolean | Task #008 deterministic rule | No | future derived metric |
| `n_sensitivity_FDR05` | Number of sensitivities with BH FDR below 0.05 | integer 0–6 | Task #008 deterministic rule | No | future derived metric |
| `median_abs_delta_logFC_vs_S0` | Median absolute S1–S6 logFC difference from S0 | number ≥0 | Task #008 deterministic rule | No | future derived metric |
| `max_abs_delta_logFC_vs_S0` | Maximum absolute S1–S6 logFC difference from S0 | number ≥0 | Task #008 deterministic rule | No | future derived metric |
| `S6_sign_flip_vs_S0` | S6 sign differs from S0 | boolean | Task #008 deterministic rule | No | future derived metric |
| `model_dependent_any_top50` | Gene appears in any committed per-model top-50 delta list | boolean | Task #007 | No | future derived metric |
| `model_dependent_models` | Sensitivity models contributing that flag | delimited categorical list | Task #007 | Yes | metadata |
| `reduced_residual_df_any` | Reduced residual df reported in any sensitivity | boolean | Task #007 | No | future derived metric |
| `reduced_residual_df_models` | Models reporting reduced residual df | delimited categorical list | Task #007 | Yes | metadata |
| `max_residual_df_loss` | Largest reported nominal-minus-observed residual df | integer ≥0 | Task #007 | No | evidence |

## 4. Disease relevance

| Field | Meaning | Data type | Expected source class | Missing allowed | Role |
|---|---|---|---|---|---|
| `disease_id` | Stable LUAD disease/ontology identifier used in a query | string | Open Targets/ontology source | Yes | metadata |
| `disease_label` | Human-readable disease label | string | Open Targets/ontology source | Yes | metadata |
| `disease_evidence_type` | Source-defined association evidence category | categorical string | Open Targets | Yes | evidence |
| `disease_association_score_native` | Unmodified source-native association score | number | Open Targets | Yes | evidence |
| `disease_evidence_count` | Count of source records under a defined query | integer ≥0 | Open Targets | Yes | evidence |
| `disease_evidence_record_ids` | Identifiers of supporting source records | delimited list | Open Targets | Yes | metadata |
| `disease_relevance_note` | Conservative normalized summary or limitation | string | Evidence normalizer/reporter | Yes | metadata |

## 5. Genetics / cancer evidence

| Field | Meaning | Data type | Expected source class | Missing allowed | Role |
|---|---|---|---|---|---|
| `genetic_evidence_type` | Somatic, germline, driver, burden, or other evidence class | categorical string | Open Targets/cancer genetics source | Yes | evidence |
| `genetic_variant_or_event` | Variant, copy-number, fusion, or event identifier | string | Genetics/cancer database | Yes | evidence |
| `genetic_effect_direction` | Source-reported direction of genetic effect | categorical string | Genetics/cancer database | Yes | evidence |
| `cancer_driver_status` | Source-reported driver classification | categorical string | Cancer genetics database | Yes | evidence |
| `cancer_cohort_context` | Tumour type, cohort, and population context | string | Cancer genetics database | Yes | metadata |
| `genetic_statistic` | Reported odds ratio, effect, q-value, or other statistic | structured string or number | Genetics/cancer database | Yes | evidence |
| `genetic_evidence_record_ids` | Source identifiers supporting the record | delimited list | Genetics/cancer database | Yes | metadata |

## 6. Functional dependency

| Field | Meaning | Data type | Expected source class | Missing allowed | Role |
|---|---|---|---|---|---|
| `dependency_dataset` | Functional-screen dataset or release | string | Perturbational/dependency database | Yes | metadata |
| `dependency_model_system` | Cell line, organoid, or other model | string | Perturbational/dependency database | Yes | metadata |
| `dependency_disease_context` | Disease and subtype of the model | string | Perturbational/dependency database | Yes | metadata |
| `dependency_perturbation_type` | CRISPR, RNAi, compound, or other perturbation | categorical string | Perturbational/dependency database | Yes | evidence |
| `dependency_metric_name` | Name of the source-native dependency measure | string | Perturbational/dependency database | Yes | metadata |
| `dependency_metric_value` | Unmodified source-native dependency value | number | Perturbational/dependency database | Yes | evidence |
| `dependency_selectivity_context` | LUAD selectivity or comparator definition | string | Derived from defined screen comparison | Yes | metadata |
| `dependency_evidence_record_ids` | Source record identifiers | delimited list | Perturbational/dependency database | Yes | metadata |

## 7. Therapeutic directionality

| Field | Meaning | Data type | Expected source class | Missing allowed | Role |
|---|---|---|---|---|---|
| `proposed_therapeutic_action` | Inhibit, activate, degrade, replace, other, or `UNKNOWN` | categorical string | Integrated mechanistic evidence | No; initially `UNKNOWN` | future derived metric |
| `directionality_status` | Supportive, conflicting, or unknown | categorical string | Deterministic future rule | No; initially `unknown` | future derived metric |
| `directionality_evidence_types` | Functional/genetic/pharmacological evidence classes considered | delimited list | Integrated evidence | Yes | metadata |
| `directionality_support_record_ids` | Evidence records supporting a proposed action | delimited list | Integrated evidence | Yes | metadata |
| `directionality_conflict_record_ids` | Evidence records conflicting with a proposed action | delimited list | Integrated evidence | Yes | metadata |
| `directionality_rationale` | Evidence-grounded explanation of status | string | Evidence normalizer/reporter | Yes | metadata |
| `directionality_is_hypothesis` | Whether the action remains a hypothesis | boolean | Evidence normalizer | No | metadata |

Expression sign alone must never populate `proposed_therapeutic_action`.

## 8. Tractability / modality

| Field | Meaning | Data type | Expected source class | Missing allowed | Role |
|---|---|---|---|---|---|
| `modality` | Small molecule, antibody, degrader, RNA, gene therapy, or other | categorical string | Open Targets/ChEMBL/curated source | Yes | metadata |
| `tractability_assessment` | Source-defined tractability category | categorical string | Open Targets | Yes | evidence |
| `tractability_evidence_basis` | Structural, ligand, localization, precedent, or other basis | delimited list | Open Targets/ChEMBL | Yes | evidence |
| `subcellular_localization` | Localization relevant to modality feasibility | string | Curated protein database | Yes | evidence |
| `secreted_or_surface_status` | Source-reported extracellular/surface category | categorical string | Curated protein database | Yes | evidence |
| `known_ligandability_status` | Source-reported ligandability state | categorical string | ChEMBL/structural source | Yes | evidence |
| `tractability_record_ids` | Supporting source identifiers | delimited list | Tractability source | Yes | metadata |

## 9. Pharmacology

| Field | Meaning | Data type | Expected source class | Missing allowed | Role |
|---|---|---|---|---|---|
| `compound_id` | Stable source compound identifier | string | ChEMBL | Yes | metadata |
| `compound_name` | Preferred compound name | string | ChEMBL | Yes | metadata |
| `compound_development_status` | Approved, clinical, preclinical, tool, or unknown | categorical string | ChEMBL/regulatory source | Yes | evidence |
| `mechanism_of_action` | Source-reported target mechanism | string | ChEMBL | Yes | evidence |
| `action_type` | Inhibitor, agonist, antagonist, degrader, binder, or other | categorical string | ChEMBL | Yes | evidence |
| `assay_id` | Stable assay identifier | string | ChEMBL | Yes | metadata |
| `assay_type` | Binding, functional, ADME, toxicity, or other assay class | categorical string | ChEMBL | Yes | metadata |
| `target_confidence` | Source-native target-assignment confidence | number or category | ChEMBL | Yes | evidence |
| `potency_type` | IC50, EC50, Ki, Kd, or other measure | categorical string | ChEMBL | Yes | metadata |
| `potency_value` | Standardized potency value | number | ChEMBL | Yes | evidence |
| `potency_units` | Units associated with potency | string | ChEMBL | Yes | metadata |
| `pharmacology_record_id` | Stable activity/mechanism record identifier | string | ChEMBL | Yes | metadata |

## 10. Clinical development

| Field | Meaning | Data type | Expected source class | Missing allowed | Role |
|---|---|---|---|---|---|
| `trial_id` | ClinicalTrials.gov identifier | string | ClinicalTrials.gov | Yes | metadata |
| `trial_intervention` | Intervention name and type | string | ClinicalTrials.gov | Yes | metadata |
| `trial_target_mapping_basis` | Direct target, pathway proxy, class member, or uncertain mapping | categorical string | Evidence normalizer | Yes | metadata |
| `trial_condition` | Registered disease/condition | string | ClinicalTrials.gov | Yes | metadata |
| `trial_LUAD_relevance` | Direct LUAD, broader NSCLC/lung cancer, other cancer, or non-cancer | categorical string | Deterministic future rule | Yes | future derived metric |
| `trial_phase` | Registered development phase | categorical string | ClinicalTrials.gov | Yes | evidence |
| `trial_status` | Registered recruitment/completion status | categorical string | ClinicalTrials.gov | Yes | evidence |
| `trial_sponsor` | Lead sponsor | string | ClinicalTrials.gov | Yes | metadata |
| `clinical_record_last_updated` | Source record update date | date/time | ClinicalTrials.gov | Yes | metadata |

## 11. Safety liabilities

| Field | Meaning | Data type | Expected source class | Missing allowed | Role |
|---|---|---|---|---|---|
| `safety_evidence_type` | Genetic, animal, clinical, pharmacovigilance, or literature class | categorical string | Open Targets/openFDA/literature | Yes | evidence |
| `safety_event_or_phenotype` | Reported adverse event or phenotype | string | Safety source | Yes | evidence |
| `safety_context` | Exposure, population, model, dose, and disease context | string | Safety source | Yes | metadata |
| `on_target_attribution_status` | Supported, possible, unsupported, or unknown attribution | categorical string | Evidence normalizer | Yes | future derived metric |
| `seriousness_or_severity` | Source-reported seriousness/severity | categorical string | Safety source | Yes | evidence |
| `safety_signal_measure` | Source-native count, ratio, statistic, or finding | structured string or number | Safety source | Yes | evidence |
| `safety_confounding_note` | Reporting bias, indication, co-medication, or other limitation | string | Evidence normalizer | Yes | metadata |
| `safety_flag` | Conservative structured liability flag | categorical string | Deterministic future rule | Yes | future derived metric |
| `safety_record_ids` | Supporting source identifiers | delimited list | Safety source | Yes | metadata |

Adverse-event counts alone must not be interpreted as causal toxicity.

## 12. Normal-tissue / cell-type expression context

| Field | Meaning | Data type | Expected source class | Missing allowed | Role |
|---|---|---|---|---|---|
| `expression_context_source` | Dataset and release for normal expression | string | Normal-tissue/single-cell atlas | Yes | metadata |
| `normal_tissue_or_cell_type` | Tissue, organ, or cell-type label | string | Expression atlas | Yes | metadata |
| `normal_expression_metric_name` | Name of the source-native expression measure | string | Expression atlas | Yes | metadata |
| `normal_expression_metric_value` | Source-native expression value | number | Expression atlas | Yes | evidence |
| `expression_specificity_metric` | Source-native or defined specificity measure | number | Expression atlas/defined derivation | Yes | evidence |
| `critical_tissue_expression_flag` | Expression in a prespecified safety-relevant tissue | categorical string | Deterministic future rule | Yes | future derived metric |
| `cell_type_context_note` | Heterogeneity, composition, or localization limitation | string | Evidence normalizer | Yes | metadata |
| `expression_context_record_ids` | Supporting source records | delimited list | Expression atlas | Yes | metadata |

## 13. Development saturation / under-explored status

| Field | Meaning | Data type | Expected source class | Missing allowed | Role |
|---|---|---|---|---|---|
| `relevant_publication_count` | Disease-specific publications under a versioned query | integer ≥0 | Europe PMC | Yes | evidence |
| `mature_pharmacology_count` | Compounds meeting future prespecified quality rules | integer ≥0 | ChEMBL | Yes | future derived metric |
| `relevant_trial_count` | Trials meeting future relevance rules | integer ≥0 | ClinicalTrials.gov | Yes | future derived metric |
| `approved_drug_count` | Approved drugs with supported target mapping | integer ≥0 | ChEMBL/regulatory source | Yes | evidence |
| `therapeutic_competition_count` | Distinct relevant development programs under defined rules | integer ≥0 | Integrated clinical/pharmacology sources | Yes | future derived metric |
| `minimum_support_passed` | Future minimum biology/tractability gate | boolean | Deterministic future rule | Yes | future derived metric |
| `development_saturation_status` | High, medium, low, unknown, or conflicting | categorical string | Deterministic future rule | Yes | future derived metric |
| `under_explored_status` | Eligible, not eligible, unknown, or conflicting | categorical string | Deterministic future rule | Yes | future derived metric |
| `under_exploration_note` | Evidence-grounded explanation and limitations | string | Evidence normalizer/reporter | Yes | metadata |

Low evidence volume alone must not produce an attractive under-explored label.

## 14. Provenance / source traceability

| Field | Meaning | Data type | Expected source class | Missing allowed | Role |
|---|---|---|---|---|---|
| `evidence_record_id` | Project-unique normalized evidence-record identifier | string | Evidence normalizer | No for evidence records | metadata |
| `source_name` | Database, dataset, publication, or analysis name | string | Retrieval client/project analysis | No for evidence records | metadata |
| `source_version` | Release/API/data version when available | string | Source | Yes | metadata |
| `source_identifier` | Stable identifier in the source | string | Source | Yes | metadata |
| `source_url` | Direct resolvable source URL when available | string | Source | Yes | metadata |
| `query_text_or_payload` | Exact query or normalized payload used | string/JSON | Retrieval client | No after retrieval | metadata |
| `retrieved_at_utc` | Retrieval timestamp | ISO-8601 date/time | Retrieval client | No after retrieval | metadata |
| `raw_evidence_pointer` | Path, object key, or immutable pointer to raw response | string | Retrieval system | Yes | metadata |
| `raw_evidence_sha256` | SHA256 of retained raw evidence | string | Retrieval system | Yes | metadata |
| `normalizer_version` | Version of normalization code/schema | string | Project configuration | No after normalization | metadata |
| `claim_ids` | Dossier claims supported by the evidence record | delimited list | Reporter/validator | Yes | metadata |

## 15. Explicit missingness

Every externally populated field must carry or inherit an explicit status.

| Field | Meaning | Data type | Expected source class | Missing allowed | Role |
|---|---|---|---|---|---|
| `field_name` | Name of the field whose state is recorded | string | Evidence normalizer | No | metadata |
| `missingness_status` | `PRESENT`, `NOT_RETRIEVED`, `NOT_AVAILABLE`, `NOT_APPLICABLE`, `AMBIGUOUS`, `CONFLICTING`, or `RETRIEVAL_FAILED` | categorical string | Evidence normalizer | No | metadata |
| `missingness_reason` | Human-readable reason for non-present status | string | Evidence normalizer/retrieval client | Yes | metadata |
| `expected_source_class` | Source expected to populate the field | string | Schema/configuration | Yes | metadata |
| `retrieval_attempted` | Whether a retrieval attempt occurred | boolean | Retrieval client | No | metadata |
| `retrieval_attempt_id` | Identifier linking to an attempt log | string | Retrieval client | Yes | metadata |
| `last_checked_at_utc` | Most recent check timestamp | ISO-8601 date/time | Retrieval client | Yes | metadata |

`NOT_AVAILABLE` must not be converted to zero, false, or negative evidence.

## 16. Future deterministic scoring fields

These fields are reserved but are not calculated in Task #008. No numerical
weights are defined in v0.1.

| Field | Meaning | Data type | Expected source class | Missing allowed | Role |
|---|---|---|---|---|---|
| `scoring_model_version` | Version identifier for a future deterministic model | string | Versioned project configuration | Yes | metadata |
| `scoring_config_sha256` | Hash of the complete future scoring configuration | string | Versioned project configuration | Yes | metadata |
| `feature_name` | Name of a normalized scoring feature | string | Future scoring engine | Yes | future derived metric |
| `feature_value` | Deterministically normalized feature value | number/category | Future scoring engine | Yes | future derived metric |
| `feature_missingness_treatment` | Versioned rule applied to missing evidence | categorical string | Future scoring configuration | Yes | metadata |
| `dimension_score` | Future score for one evidence dimension | number | Future scoring engine | Yes | future derived metric |
| `actionability_score` | Future deterministic Ranking A score | number | Future scoring engine | Yes | future derived metric |
| `under_exploration_score` | Future deterministic Ranking B score after support gating | number | Future scoring engine | Yes | future derived metric |
| `score_eligibility_status` | Whether prespecified minimum evidence gates are met | categorical string | Future scoring engine | Yes | future derived metric |
| `score_sensitivity_summary` | Future stability result under reasonable configuration changes | structured string/JSON | Future validation engine | Yes | future derived metric |

Future scoring must be transparent, version-controlled, reproducible, and
separate from LLM narrative generation. The same evidence and configuration
must yield the same numerical result.
