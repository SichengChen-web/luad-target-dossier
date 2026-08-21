#!/usr/bin/env python3
"""Build the Task #021 deterministic profile-materialization contract.

This standard-library builder defines future inputs, component-specific state
resolution, provenance propagation, dependency preservation, canonical output
serialization, and non-inference rules. It materializes no target profiles.
"""

from __future__ import annotations

import csv
import hashlib
import os
import platform
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
TASK020_BASE_COMMIT = "6ebce1dbc38706a5d8143c311da2e27f81f1e442"
EXPECTED_BRANCH = "main"
EXPECTED_REMOTE_FRAGMENT = "SichengChen-web/luad-target-dossier"

SCRIPT_PATH = ROOT / "analysis/21_build_profile_materialization_framework.py"
PLAN_PATH = ROOT / "docs/profile_materialization_framework_v0.1.md"
OUTPUT_DIR = ROOT / "outputs/profile_materialization"
SCHEMA_PATH = OUTPUT_DIR / "materialization_schema.csv"
STATE_PATH = OUTPUT_DIR / "component_state_resolution_registry.csv"
CONTRACT_PATH = OUTPUT_DIR / "profile_builder_contract.md"
SUMMARY_PATH = OUTPUT_DIR / "profile_materialization_summary.md"
SESSION_PATH = OUTPUT_DIR / "session_info.txt"

GOVERNED_RECORD_PATH = ROOT / "outputs/evidence_claim_architecture/evidence_record_registry.csv"
GOVERNED_RECORD_SHA256 = "76ec5056fb4e468176073073532204d231765d4f0cd70dbb6cfe4ad8bf752343"
GOVERNED_RECORD_SIZE = 139_836_748

INPUTS = {
    "governance_plan": ROOT / "docs/artifact_governance_plan_v0.1.md",
    "artifact_manifest": ROOT / "outputs/artifact_governance/artifact_manifest.csv",
    "artifact_classification": ROOT / "outputs/artifact_governance/artifact_classification.csv",
    "reproducibility_contract": ROOT / "outputs/artifact_governance/reproducibility_contract.md",
    "artifact_governance_summary": ROOT / "outputs/artifact_governance/artifact_governance_summary.md",
    "artifact_governance_session": ROOT / "outputs/artifact_governance/session_info.txt",
    "decision_context_plan": ROOT / "docs/decision_context_framework_v0.1.md",
    "decision_context_registry": ROOT / "outputs/decision_context/decision_context_registry.csv",
    "evidence_context_matrix": ROOT / "outputs/decision_context/evidence_context_matrix.csv",
    "interpretation_boundaries": ROOT / "outputs/decision_context/interpretation_boundary_registry.csv",
    "decision_context_summary": ROOT / "outputs/decision_context/decision_framework_summary.md",
    "decision_context_session": ROOT / "outputs/decision_context/session_info.txt",
    "profile_plan": ROOT / "docs/target_evidence_profile_framework_v0.1.md",
    "profile_schema": ROOT / "outputs/evidence_profiles/profile_schema.csv",
    "profile_components": ROOT / "outputs/evidence_profiles/profile_component_registry.csv",
    "profile_rules": ROOT / "outputs/evidence_profiles/profile_interpretation_rules.csv",
    "profile_summary": ROOT / "outputs/evidence_profiles/evidence_profile_summary.md",
    "profile_session": ROOT / "outputs/evidence_profiles/session_info.txt",
}

EXPECTED_HASHES = {
    "governance_plan": "92557a1e2002c841d9acd41b0bd58177a92b18105bc555b57ecd8df1ef841c7a",
    "artifact_manifest": "f8cb7150b2a6e51f74f04ba2a542348c973359aaab172d903385073f21a62b24",
    "artifact_classification": "c53b52bff0357ef5d69bf85a007ce7c214ecf4f3e7f2b4ff6b47fcd6e2b75c12",
    "reproducibility_contract": "e4bcfeca738a78ae7047d0fdbd0f5f285044c1f9585565f70cc0d61744e52f79",
    "artifact_governance_summary": "9287140c9671a7c8e3d56d43d6b2a4868b1deb36eca3c83ac14ac467d3d3d4a6",
    "artifact_governance_session": "ee2761523fec18ff4782c5edfaf67a547dce283d3f8db0e2c134c35afe7dc312",
    "decision_context_plan": "59383d1397d55202ae9a999415d7d2a2f75c6fadfb9b7845f5159c10b0e05718",
    "decision_context_registry": "41fa351ce36920362a93513591372b819db4127b297872e392b028bcaaa71c4d",
    "evidence_context_matrix": "b698ca3ada409beb1d4172d3c2c3608ff97a74e52d147a1803791f57a726d834",
    "interpretation_boundaries": "59e123beabf46f4b767bcd11e9c8bf6a2b6c86829a29d441517d9d0cf8e8e779",
    "decision_context_summary": "448048391cfd3a9918e0aa6f9f3c210d2bfbf0304cc01a656c9cf2c6910dbe74",
    "decision_context_session": "230dadf883400295e1c0c3151c7bcbfe08a80f1e22312ba54308263b2406253b",
    "profile_plan": "da4ef0cc822835ae23e14dff3a7a8937dd6807ecc969610306c92dfbf3fb2b69",
    "profile_schema": "71fce3919f8c9f7b782faee40aeadce9010825410ca640d5453523b0424275ed",
    "profile_components": "0f21103d27a5e8c503f0c48785febd69b1150e9266522d67f98447a4d2aae009",
    "profile_rules": "210471df693f4cd373f7de8ab06c158162b91b55dba61f6a8a65bbaa0d26890b",
    "profile_summary": "f8722637c6318d4352472899a8aaa9f77160351a6779910f8b65b3c02e73ff9f",
    "profile_session": "62d951c0fd6596cfb82789f27c4abaac27466e7ba7a6efbf9561abcbf6e13820",
}

ALLOWED_UNTRACKED_FILES = {
    "analysis/21_build_profile_materialization_framework.py",
    "docs/profile_materialization_framework_v0.1.md",
}
ALLOWED_UNTRACKED_PREFIX = "outputs/profile_materialization/"

PROFILE_STATES = ["OBSERVED", "PARTIAL", "MISSING", "NOT_QUERIED", "CONFLICTING"]
STATE_PRECEDENCE = {
    "CONFLICTING": 1,
    "OBSERVED": 2,
    "MISSING": 3,
    "PARTIAL": 4,
    "NOT_QUERIED": 5,
}

CURRENT_RECORD_ROLES = {
    "TRANSCRIPT_PRIMARY",
    "TRANSCRIPT_ROBUSTNESS",
    "OT_LUAD_ASSOCIATION",
    "OT_DRUG_CANDIDATE",
    "CHEMBL_TARGET_ANNOTATION",
    "OT_TRACTABILITY_SUMMARY",
    "OT_SAFETY_SUMMARY",
}

FORBIDDEN_EXACT_FIELDS = {
    "score",
    "rank",
    "priority",
    "target_selection",
    "recommendation",
    "therapeutic_direction",
}

MATERIALIZATION_CONTRACTS = [
    {
        "id": "MAT_INPUT_TARGET_MANIFEST",
        "type": "FUTURE_REQUIRED_INPUT",
        "order": 1,
        "name": "Frozen target universe manifest",
        "artifact": "FUTURE_TARGET_MANIFEST_NOT_SUPPLIED_IN_TASK021",
        "fields": "EnsemblID|target_order|input_artifact_id|input_sha256",
        "key": "EnsemblID",
        "cardinality": "ONE_ROW_PER_UNIQUE_ENSEMBLID",
        "validation": "EnsemblID unique/nonempty; exact order frozen; manifest path/size/SHA256 governed before materialization.",
        "propagation": "EnsemblID|input_artifact_id|input_sha256",
        "determinism": "Target rows follow target_order exactly; symbols are never used as keys or fallback mappings.",
        "failure": "STOP_IF_MISSING_DUPLICATED_REORDERED_OR_HASH_MISMATCH",
    },
    {
        "id": "MAT_INPUT_PROFILE_SCHEMA",
        "type": "FROZEN_RULE_INPUT",
        "order": 2,
        "name": "Task #020 profile schema",
        "artifact": "outputs/evidence_profiles/profile_schema.csv",
        "fields": "field_order|field_name|data_type|required|allowed_values|interpretation_boundary",
        "key": "field_name",
        "cardinality": "28_UNIQUE_FIELDS_IN_FIELD_ORDER",
        "validation": "Task #020 SHA256 matches; exact 28-field vocabulary and order retained.",
        "propagation": "profile_version|schema_artifact_id|schema_sha256",
        "determinism": "Output header follows numeric field_order; no extra or omitted profile fields.",
        "failure": "STOP_ON_SCHEMA_OR_HASH_CHANGE",
    },
    {
        "id": "MAT_INPUT_COMPONENT_REGISTRY",
        "type": "FROZEN_RULE_INPUT",
        "order": 3,
        "name": "Task #020 component registry",
        "artifact": "outputs/evidence_profiles/profile_component_registry.csv",
        "fields": "profile_section_id|component_id|evidence_domains|evidence_types|allowed_states|required_provenance|dependency_boundary",
        "key": "component_id",
        "cardinality": "11_UNIQUE_COMPONENTS_IN_FILE_ORDER",
        "validation": "Task #020 SHA256 matches; 4/4/3 sections and exact state vocabulary retained.",
        "propagation": "component_id|profile_section_id|evidence_domain_ids|evidence_type_ids|component_registry_sha256",
        "determinism": "For each target, component rows follow registry file order exactly.",
        "failure": "STOP_ON_COMPONENT_OR_HASH_CHANGE",
    },
    {
        "id": "MAT_INPUT_INTERPRETATION_RULES",
        "type": "FROZEN_RULE_INPUT",
        "order": 4,
        "name": "Task #019–#020 interpretation boundaries",
        "artifact": "outputs/decision_context/interpretation_boundary_registry.csv|outputs/evidence_profiles/profile_interpretation_rules.csv",
        "fields": "evidence_type|what_it_supports|what_it_does_not_support|rule_id|prohibited_conclusion|required_handling",
        "key": "evidence_type|rule_id",
        "cardinality": "17_EVIDENCE_BOUNDARIES_AND_18_PROFILE_RULES",
        "validation": "Both SHA256 values match; every acceptable evidence type has exactly one boundary.",
        "propagation": "interpretation_boundary_ids|profile_rule_version_hash",
        "determinism": "Boundaries constrain state rationale templates and are never inferred from free text.",
        "failure": "STOP_ON_MISSING_BOUNDARY_RULE_OR_HASH_CHANGE",
    },
    {
        "id": "MAT_INPUT_CLAIMS",
        "type": "FUTURE_PROFILE_DATA_INPUT",
        "order": 5,
        "name": "Bounded evidence claim registry",
        "artifact": "outputs/evidence_claim_architecture/evidence_claim_registry.csv_OR_VERSIONED_SUCCESSOR",
        "fields": "claim_id|EnsemblID|domain_id|claim_type|claim_status|supporting_record_count|uncertainty_status",
        "key": "claim_id",
        "cardinality": "UNIQUE_CLAIM_ID_MANY_CLAIMS_PER_ENSEMBLID",
        "validation": "Every claim links to a frozen target and controlled ontology domain; claim IDs and artifact hash are unique/frozen.",
        "propagation": "claim_ids|uncertainty_categories|input_artifact_ids|input_sha256s",
        "determinism": "Eligible claims are selected by EnsemblID plus controlled domain/type, then sorted lexically by claim_id.",
        "failure": "STOP_ON_ORPHAN_DUPLICATE_UNKNOWN_DOMAIN_OR_HASH_MISMATCH",
    },
    {
        "id": "MAT_INPUT_EVIDENCE_RECORDS",
        "type": "FUTURE_PROFILE_DATA_INPUT",
        "order": 6,
        "name": "Atomic evidence record registry",
        "artifact": "outputs/evidence_claim_architecture/evidence_record_registry.csv_OR_VERSIONED_SUCCESSOR",
        "fields": "record_id|claim_id|source_id|source_record_type|source_record_identifier|observation_status|missingness_status|uncertainty_status|provenance_notes",
        "key": "record_id",
        "cardinality": "UNIQUE_RECORD_ID_MANY_RECORDS_PER_CLAIM",
        "validation": "Every record links to one claim/source; type is component-acceptable; source-native ID, missingness, uncertainty, and provenance are explicit.",
        "propagation": "evidence_record_ids|source_entity_ids|missingness_statuses|uncertainty_categories|evidence_record_count|observed_record_count",
        "determinism": "Eligible records are selected by linked claim and acceptable type, deduplicated only by identical record_id, and sorted lexically.",
        "failure": "STOP_ON_ORPHAN_DUPLICATE_UNKNOWN_TYPE_OR_HASH_MISMATCH",
    },
    {
        "id": "MAT_INPUT_SOURCE_ENTITIES",
        "type": "FUTURE_PROFILE_DATA_INPUT",
        "order": 7,
        "name": "Source entity and version registry",
        "artifact": "outputs/evidence_claim_architecture/source_entity_registry.csv_OR_VERSIONED_SUCCESSOR",
        "fields": "source_id|source_name|provider|source_type|version|retrieval_information|dependency_notes",
        "key": "source_id",
        "cardinality": "ONE_ROW_PER_UNIQUE_SOURCE_ID",
        "validation": "Every observed record resolves to one versioned source entity; UNKNOWN version prevents provenance_complete=TRUE.",
        "propagation": "source_entity_ids|source_versions",
        "determinism": "Source IDs and key=value version pairs are sorted lexically; missing versions use UNKNOWN explicitly.",
        "failure": "STOP_ON_MISSING_SOURCE;MARK_PROVENANCE_INCOMPLETE_ON_UNKNOWN_VERSION",
    },
    {
        "id": "MAT_INPUT_MISSINGNESS_UNCERTAINTY",
        "type": "FUTURE_PROFILE_DATA_INPUT",
        "order": 8,
        "name": "Missingness and uncertainty registry",
        "artifact": "outputs/evidence_claim_architecture/missingness_uncertainty_registry.csv_OR_VERSIONED_SUCCESSOR",
        "fields": "entity_id|entity_type|status_type|status_value|explanation",
        "key": "entity_id|status_type",
        "cardinality": "ONE_MISSINGNESS_AND_ONE_UNCERTAINTY_STATE_PER_REQUIRED_ENTITY",
        "validation": "Only controlled Task #014 values; NOT_FOUND, NOT_QUERIED, UNKNOWN, and conflicts remain distinct.",
        "propagation": "missingness_statuses|uncertainty_categories|state_rationale|conflict_description",
        "determinism": "States are copied, never inferred from zero/blank values, and emitted in controlled vocabulary order.",
        "failure": "STOP_ON_UNKNOWN_STATUS_OR_MISSING_REQUIRED_STATE",
    },
    {
        "id": "MAT_INPUT_DEPENDENCIES",
        "type": "FUTURE_PROFILE_DATA_INPUT",
        "order": 9,
        "name": "Evidence record dependency graph",
        "artifact": "outputs/evidence_claim_architecture/evidence_dependency_graph.csv_OR_VERSIONED_SUCCESSOR",
        "fields": "dependency_id|record_a|record_b|relationship|dependency_level|reason|review_status",
        "key": "dependency_id",
        "cardinality": "UNIQUE_UNORDERED_RECORD_PAIR_PER_DEPENDENCY_ASSERTION",
        "validation": "Both record endpoints exist; relationship/level controlled; absence of an edge never becomes INDEPENDENT.",
        "propagation": "dependency_relationships|dependency_levels|state_rationale",
        "determinism": "Induced edges among component records are sorted by canonical unordered pair then dependency_id.",
        "failure": "STOP_ON_ORPHAN_OR_INVALID_EDGE;PRESERVE_UNKNOWN_DEPENDENCY",
    },
    {
        "id": "MAT_INPUT_ARTIFACT_GOVERNANCE",
        "type": "FROZEN_PROVENANCE_INPUT",
        "order": 10,
        "name": "Task #018 artifact manifest and run manifest",
        "artifact": "outputs/artifact_governance/artifact_manifest.csv|FUTURE_MATERIALIZATION_INPUT_MANIFEST",
        "fields": "artifact_id|relative_path_or_uri|file_size_bytes|sha256|generated_by|input_dependencies|tracking_or_storage_status",
        "key": "artifact_id",
        "cardinality": "ONE_ROW_PER_FROZEN_INPUT_ARTIFACT",
        "validation": "Every input exists at its governed location and exactly matches size/SHA256 before and after generation.",
        "propagation": "input_artifact_ids|input_sha256s|generated_by",
        "determinism": "Artifact IDs/hashes are sorted by artifact_id and embedded unchanged in every affected component row.",
        "failure": "STOP_ON_MISSING_ARTIFACT_OR_HASH_MISMATCH",
    },
    {
        "id": "MAT_INPUT_RUN_CONFIGURATION",
        "type": "FUTURE_REQUIRED_INPUT",
        "order": 11,
        "name": "Frozen materialization run configuration",
        "artifact": "FUTURE_VERSIONED_CONFIGURATION_NOT_SUPPLIED_IN_TASK021",
        "fields": "profile_version|generator_version|rules_hash|input_manifest_hash|materialization_snapshot_time_utc|csv_format_version",
        "key": "profile_version|input_manifest_hash",
        "cardinality": "ONE_FROZEN_CONFIGURATION_PER_MATERIALIZATION",
        "validation": "All values explicit; snapshot time is frozen ISO8601 UTC and never read from the wall clock during row generation.",
        "propagation": "profile_version|generated_by|generated_at_utc|profile_id inputs",
        "determinism": "profile_id=SHA256(EnsemblID|profile_version|input_manifest_hash|rules_hash); no randomness, locale, or current time.",
        "failure": "STOP_ON_MISSING_UNVERSIONED_OR_NONCANONICAL_CONFIGURATION",
    },
    {
        "id": "MAT_STAGE_COMPONENT_EXPANSION",
        "type": "DETERMINISTIC_STAGE",
        "order": 12,
        "name": "Target-by-component expansion",
        "artifact": "IN_MEMORY_LONG_FORM_PROFILE_ROWS",
        "fields": "EnsemblID|profile_id|profile_section_id|component_id|evidence_domain_ids|evidence_type_ids",
        "key": "EnsemblID|component_id",
        "cardinality": "EXACTLY_11_ROWS_PER_TARGET",
        "validation": "Cross-product is complete and unique; no target/component silently omitted.",
        "propagation": "Identity and controlled component fields copied without biological inference.",
        "determinism": "Target order first, Task #020 component order second.",
        "failure": "STOP_ON_DUPLICATE_MISSING_OR_EXTRA_COMPONENT_ROW",
    },
    {
        "id": "MAT_STAGE_STATE_RESOLUTION",
        "type": "DETERMINISTIC_STAGE",
        "order": 13,
        "name": "Component-specific state resolution",
        "artifact": "component_state_resolution_registry.csv",
        "fields": "component_id|resolved_state|evaluation_precedence|deterministic_predicate|required_provenance_predicate|missingness_handling|dependency_preservation",
        "key": "component_id|resolved_state",
        "cardinality": "FIVE_STATE_RULES_PER_COMPONENT",
        "validation": "Exactly one state resolves per component; every predicate is evaluated in frozen precedence order.",
        "propagation": "component_state|state_rationale|conflict_present|conflict_description|provenance_complete|maturity_description",
        "determinism": "CONFLICTING→OBSERVED→MISSING→PARTIAL→NOT_QUERIED; first satisfied mutually validated predicate wins.",
        "failure": "STOP_IF_ZERO_OR_MULTIPLE_FINAL_STATES_RESOLVE",
    },
    {
        "id": "MAT_STAGE_CANONICAL_SERIALIZATION",
        "type": "DETERMINISTIC_STAGE",
        "order": 14,
        "name": "Canonical profile serialization",
        "artifact": "FUTURE_TARGET_EVIDENCE_PROFILE.csv",
        "fields": "All 28 Task #020 profile fields in field_order",
        "key": "EnsemblID|component_id",
        "cardinality": "TARGET_COUNT_MULTIPLIED_BY_11_ROWS",
        "validation": "UTF-8, LF line endings, comma delimiter, RFC-compatible quoting, explicit NONE sentinel, no blank required cells.",
        "propagation": "All list-valued provenance fields retained as lexically sorted pipe-delimited unique tokens.",
        "determinism": "Stable header/order/quoting; integers in base-10; booleans TRUE/FALSE/UNKNOWN; no locale-dependent formatting.",
        "failure": "STOP_ON_SCHEMA_SERIALIZATION_OR_REQUIRED_VALUE_ERROR",
    },
    {
        "id": "MAT_STAGE_QC_AND_HASH_FREEZE",
        "type": "DETERMINISTIC_STAGE",
        "order": 15,
        "name": "Materialization QC and hash freeze",
        "artifact": "FUTURE_PROFILE_QC.csv|FUTURE_PROFILE_SESSION_INFO.txt",
        "fields": "row_count|target_count|11_rows_per_target|unique_keys|state_counts|provenance_failures|input_hashes|output_sha256",
        "key": "materialization_run_id|check_id",
        "cardinality": "ONE_QC_BUNDLE_PER_OUTPUT_SNAPSHOT",
        "validation": "All identities, cardinalities, referential links, vocabularies, provenance, dependencies, and hashes pass.",
        "propagation": "Input/output hashes and generator/rule versions frozen in the session record.",
        "determinism": "Hash after canonical serialization; repeat generation must match byte-for-byte before release.",
        "failure": "STOP_AND_DO_NOT_RELEASE_PROFILE_ON_ANY_QC_OR_HASH_FAILURE",
    },
]

COMPONENT_RULES = {
    "COMP_TRANSCRIPTOMIC_EVIDENCE": {
        "roles": "TRANSCRIPT_PRIMARY|TRANSCRIPT_ROBUSTNESS",
        "observed": "Both primary and robustness records are OBSERVED; primary effect/significance fields are valid; provenance is complete; no prespecified material direction conflict.",
        "partial": "At least one transcript record is observed or assessed, but the companion record, required field, QC/provenance element, or coverage is incomplete; fully queried zero-record and conflict predicates are false.",
        "missing": "Both required transcript record roles were expected and successfully assessed for the target, neither has a qualifying result, no UNKNOWN/failure exists, and no conflict predicate is true.",
        "not_queried": "Neither transcript role was analyzed for the target under the frozen cohort/design and no eligible claim or record exists.",
        "conflicting": "The frozen primary and prespecified sensitivity evidence meet the Task #020 material direction-conflict definition or traceable transcript records report incompatible target identities/effects.",
    },
    "COMP_DISEASE_ASSOCIATION": {
        "roles": "OT_LUAD_ASSOCIATION",
        "observed": "A traceable Open Targets LUAD association record contains a returned direct or ontology-qualified association observation, provenance is complete, and no material source conflict is present.",
        "partial": "The target/query is represented but association coverage, datasource lineage, disease specificity, or provenance is incomplete; or only a literature-volume qualifier is available.",
        "missing": "The mapped target was queried for the frozen LUAD disease identifier, retrieval completed, no qualifying association record was returned, and coverage is not UNKNOWN.",
        "not_queried": "No valid target mapping/query was performed for the LUAD disease identifier and no association assessment exists.",
        "conflicting": "Traceable disease-association records make materially incompatible disease-specific claims under the prespecified comparison rule; direct/indirect overlap alone is dependency, not conflict.",
    },
    "COMP_GENETIC_EVIDENCE": {
        "roles": "FUTURE_GENETIC_CANCER_RECORD",
        "observed": "At least one LUAD-relevant genetic alteration record passes its cohort/statistical QC, has complete variant/gene/disease provenance, and no material genetic conflict is present.",
        "partial": "A genetic record or query exists but cohort relevance, alteration mapping, effect/statistical provenance, replication, or source coverage is incomplete.",
        "missing": "Every frozen genetic source in the component contract was successfully queried for the target/LUAD scope and returned no qualifying record, without UNKNOWN or failure states.",
        "not_queried": "No dedicated genetic evidence acquisition covered the target; this is the current Task #020 architecture state.",
        "conflicting": "Qualifying genetic records report materially incompatible alteration-effect or disease relationships after harmonized allele, direction, cohort, and endpoint comparison.",
    },
    "COMP_FUNCTIONAL_DEPENDENCY": {
        "roles": "FUTURE_FUNCTIONAL_DEPENDENCY_RECORD",
        "observed": "At least one LUAD-relevant model-level dependency/perturbation record passes screen QC with complete model/reagent/effect provenance and no material conflict.",
        "partial": "Some functional evidence exists but LUAD model coverage, reagent/assay QC, replicate support, effect definition, or provenance is incomplete.",
        "missing": "All frozen eligible functional sources and LUAD model scopes were queried successfully and returned no qualifying dependency record, without UNKNOWN/failure.",
        "not_queried": "No dedicated functional-dependency acquisition covered the target; this is the current Task #020 architecture state.",
        "conflicting": "Comparable, QC-qualified perturbation records show materially incompatible dependency direction or phenotype under the prespecified model/context comparison.",
    },
    "COMP_PHARMACOLOGY": {
        "roles": "CHEMBL_TARGET_ANNOTATION|OT_DRUG_CANDIDATE|FUTURE_CHEMBL_COMPOUND_TARGET",
        "observed": "At least one qualifying compound-target assay/mechanism record has complete target-confidence, activity, potency/unit, mechanism, compound/assay/source provenance and no material conflict.",
        "partial": "Only target annotation or drug/candidate count records exist, or a compound record lacks required assay, potency, selectivity, mechanism, source lineage, or provenance completeness.",
        "missing": "All frozen pharmacology sources were successfully queried for a valid target mapping and returned no target annotation, candidate, or qualifying compound-target evidence, without UNKNOWN/failure.",
        "not_queried": "No valid target mapping or pharmacology acquisition was performed and no pharmacology record exists.",
        "conflicting": "Comparable compound-target records contain materially incompatible target assignment, mechanism, or normalized activity after assay-context harmonization.",
    },
    "COMP_TRACTABILITY": {
        "roles": "OT_TRACTABILITY_SUMMARY",
        "observed": "At least one source-native modality assessment record is present with target, modality, assessment/bucket, release, upstream-evidence provenance and no material conflict.",
        "partial": "A target/tractability object is represented but modality identity, assessment/bucket provenance, upstream lineage, or retrieval coverage is incomplete.",
        "missing": "The mapped target was queried for every frozen modality scope, retrieval completed, and no tractability assessment record was returned, without UNKNOWN/failure.",
        "not_queried": "No valid target mapping or tractability query was performed and no assessment record exists.",
        "conflicting": "Comparable source/version assessments assign materially incompatible modality states after accounting for release and bucket definitions; multiple modalities alone are not conflict.",
    },
    "COMP_SAFETY": {
        "roles": "OT_SAFETY_SUMMARY",
        "observed": "At least one traceable safety-liability observation is present with liability/datasource/context provenance and no material attribution conflict.",
        "partial": "A liability summary or candidate record exists but on/off-target attribution, context, human relevance, source lineage, or required provenance is incomplete.",
        "missing": "The mapped target was queried in every frozen safety source, retrieval completed, and no qualifying liability record was returned, without UNKNOWN/failure; this does not mean safe.",
        "not_queried": "No valid target mapping or safety-liability acquisition was performed and no safety assessment exists.",
        "conflicting": "Traceable liability records provide materially incompatible on-target attribution or outcome interpretation under comparable exposure/context definitions.",
    },
    "COMP_CLINICAL_DEVELOPMENT": {
        "roles": "FUTURE_CLINICAL_TRIAL_DEVELOPMENT_RECORD",
        "observed": "At least one trial-level record has validated intervention-target-disease linkage plus registry/version, trial, phase/status provenance and no material linkage conflict.",
        "partial": "A trial, intervention, candidate, or target record exists but intervention-target-LUAD linkage, phase/status currency, registry version, or provenance is incomplete.",
        "missing": "All frozen trial sources and target/disease linkage queries completed successfully and found no qualifying trial-level record, without UNKNOWN/failure.",
        "not_queried": "No dedicated trial-level clinical-development acquisition covered the target; this is the current Task #020 architecture state.",
        "conflicting": "Traceable trial/linkage records materially disagree on intervention-target identity, LUAD relevance, phase/status, or record identity after version reconciliation.",
    },
    "COMP_HUMAN_EVIDENCE": {
        "roles": "FUTURE_GENETIC_CANCER_RECORD|FUTURE_CLINICAL_TRIAL_DEVELOPMENT_RECORD",
        "observed": "At least one provenance-complete record is explicitly human-derived by cohort/trial metadata and meets its genetic or interventional component criterion without material conflict.",
        "partial": "Candidate genetic/interventional evidence exists but human origin, disease relevance, target linkage, source version, or provenance is incomplete.",
        "missing": "All frozen human genetic and interventional sources were queried successfully for the target/LUAD scope and found no qualifying human-derived record, without UNKNOWN/failure.",
        "not_queried": "Neither human genetic nor trial-level evidence acquisition covered the target.",
        "conflicting": "Comparable human-derived records provide materially incompatible target-disease, alteration-effect, or intervention-linkage evidence after lineage and context reconciliation.",
    },
    "COMP_CLINICAL_LINKAGE": {
        "roles": "OT_LUAD_ASSOCIATION|FUTURE_CHEMBL_COMPOUND_TARGET|FUTURE_CLINICAL_TRIAL_DEVELOPMENT_RECORD|FUTURE_INTERVENTION_TARGET_DISEASE_LINKAGE",
        "observed": "One validated record chain explicitly links intervention, target, LUAD disease identifier, and trial/development record with complete source lineage and no material conflict.",
        "partial": "Separate association, compound, intervention, candidate, or trial records exist but the full intervention-target-LUAD-development linkage is incomplete or based only on co-occurrence/counts.",
        "missing": "All frozen linkage sources/queries completed successfully and no qualifying intervention-target-LUAD-development linkage was found, without UNKNOWN/failure.",
        "not_queried": "No trial-level linkage acquisition was performed for the target/LUAD scope.",
        "conflicting": "Traceable records materially disagree on intervention identity, target assignment, LUAD disease linkage, or trial linkage after identifier/version reconciliation.",
    },
    "COMP_RISK_CONTEXT": {
        "roles": "OT_SAFETY_SUMMARY",
        "observed": "The current ontology-bounded safety-liability evidence meets the COMP_SAFETY observed predicate; maturity_description still records absent normal-tissue, essentiality, exposure, and toxicology domains.",
        "partial": "A risk/liability record exists but provenance, attribution, human relevance, exposure context, or interpretation is incomplete; broader unmodeled risk gaps are recorded in maturity_description.",
        "missing": "Every frozen current safety-liability source was queried successfully and returned no qualifying record, without UNKNOWN/failure; this is missing risk evidence, not low risk.",
        "not_queried": "No current safety-liability acquisition covered the target.",
        "conflicting": "Traceable risk/liability records materially disagree on attribution or outcome context; reused safety records across profile sections remain the same record lineage.",
    },
}


def fail(message: str) -> None:
    raise RuntimeError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    if path.is_symlink():
        digest.update(os.readlink(path).encode("utf-8"))
        return digest.hexdigest()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
    )
    if check and result.returncode != 0:
        fail(f"Git command failed: git {' '.join(args)}\n{result.stderr.strip()}")
    return result.stdout.strip()


def git_paths(*args: str) -> set[str]:
    result = subprocess.run(
        ["git", *args, "-z"], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
    )
    if result.returncode != 0:
        fail(result.stderr.decode(errors="replace").strip())
    return {item.decode("utf-8") for item in result.stdout.split(b"\0") if item}


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            fail(f"CSV has no header: {relative(path)}")
        return list(reader.fieldnames), list(reader)


def read_session(path: Path) -> dict[str, str]:
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


def validate_repository() -> dict[str, str]:
    branch = run_git("branch", "--show-current")
    head = run_git("rev-parse", "HEAD")
    remote = run_git("remote", "get-url", "origin")
    if branch != EXPECTED_BRANCH:
        fail(f"Expected branch {EXPECTED_BRANCH!r}; observed {branch!r}.")
    if EXPECTED_REMOTE_FRAGMENT not in remote:
        fail(f"Unexpected origin remote: {remote!r}.")
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", TASK020_BASE_COMMIT, "HEAD"], cwd=ROOT, check=False
    ).returncode != 0:
        fail(f"Frozen Task #020 commit is not an ancestor of HEAD {head}.")
    if run_git("diff", "--name-only") or run_git("diff", "--cached", "--name-only"):
        fail("Unexpected tracked or staged changes exist.")
    untracked = git_paths("ls-files", "--others", "--exclude-standard")
    unexpected = {
        path
        for path in untracked
        if not (path in ALLOWED_UNTRACKED_FILES or path.startswith(ALLOWED_UNTRACKED_PREFIX))
    }
    if unexpected:
        fail(f"Unexpected untracked files exist: {sorted(unexpected)}")
    for path in INPUTS.values():
        rel = relative(path)
        if not path.is_file():
            fail(f"Frozen input missing: {rel}")
        if not run_git("ls-files", "--error-unmatch", rel, check=False):
            fail(f"Frozen input is not committed: {rel}")
        if run_git("diff", "--name-only", TASK020_BASE_COMMIT, "HEAD", "--", rel):
            fail(f"Frozen input changed after Task #020: {rel}")
    return {"branch": branch, "head": head, "remote": remote}


def validate_hashes() -> dict[str, str]:
    observed = {}
    for name, path in INPUTS.items():
        actual = sha256(path)
        if actual != EXPECTED_HASHES[name]:
            fail(f"Frozen hash mismatch for {relative(path)}: {actual}")
        observed[name] = actual
    return observed


def validate_governance() -> tuple[int, int]:
    _, manifest = read_csv(INPUTS["artifact_manifest"])
    if len(manifest) != 193:
        fail(f"Expected 193 Task #018 artifacts; observed {len(manifest)}.")
    manifest_by_path = {row["relative_path"]: row for row in manifest}
    if len(manifest_by_path) != 193:
        fail("Task #018 manifest paths are duplicated.")
    for row in manifest:
        path = ROOT / row["relative_path"]
        if not (path.is_file() or path.is_symlink()):
            fail(f"Governed artifact missing: {row['relative_path']}")
        if path.lstat().st_size != int(row["file_size_bytes"]) or sha256(path) != row["sha256"]:
            fail(f"Governed artifact changed: {row['relative_path']}")
    governed_rel = relative(GOVERNED_RECORD_PATH)
    governed = manifest_by_path.get(governed_rel)
    if (
        governed is None
        or governed["sha256"] != GOVERNED_RECORD_SHA256
        or int(governed["file_size_bytes"]) != GOVERNED_RECORD_SIZE
    ):
        fail("Governed Task #014 record registry does not match its frozen manifest entry.")
    session = read_session(INPUTS["artifact_governance_session"])
    for name in ("artifact_manifest", "artifact_classification", "reproducibility_contract", "artifact_governance_summary"):
        path = INPUTS[name]
        if session.get(f"output_sha256.{relative(path)}") != sha256(path):
            fail(f"Task #018 session hash mismatch: {relative(path)}")
    return len(manifest), sum(row["artifact_class"] == "D" for row in manifest)


def validate_frozen_frameworks() -> tuple[list[dict[str, str]], dict[str, int]]:
    _, profile_schema = read_csv(INPUTS["profile_schema"])
    _, components = read_csv(INPUTS["profile_components"])
    _, profile_rules = read_csv(INPUTS["profile_rules"])
    _, boundaries = read_csv(INPUTS["interpretation_boundaries"])
    _, contexts = read_csv(INPUTS["decision_context_registry"])
    _, context_matrix = read_csv(INPUTS["evidence_context_matrix"])
    if len(profile_schema) != 28 or len(components) != 11 or len(profile_rules) != 18:
        fail("Task #020 schema/component/rule counts changed.")
    if len(boundaries) != 17 or len(contexts) != 3 or len(context_matrix) != 24:
        fail("Task #019 boundary/context counts changed.")
    if {row["component_id"] for row in components} != set(COMPONENT_RULES):
        fail("Component-specific materialization rules do not match Task #020 component IDs.")
    for row in components:
        if row["allowed_states"].split("|") != PROFILE_STATES:
            fail(f"Task #020 component state vocabulary changed: {row['component_id']}")

    _, records = read_csv(GOVERNED_RECORD_PATH)
    record_roles = {row["source_record_type"] for row in records}
    if len(records) != 207_242 or record_roles != CURRENT_RECORD_ROLES:
        fail("Task #014 evidence-record count or current source-record roles changed.")
    return components, {
        "profile_schema_field_count": len(profile_schema),
        "profile_component_count": len(components),
        "profile_rule_count": len(profile_rules),
        "interpretation_boundary_count": len(boundaries),
        "decision_context_count": len(contexts),
        "evidence_context_matrix_count": len(context_matrix),
        "governed_record_count": len(records),
        "current_record_role_count": len(record_roles),
    }


def materialization_rows() -> list[dict[str, str]]:
    return [
        {
            "contract_id": row["id"],
            "contract_type": row["type"],
            "stage_order": str(row["order"]),
            "input_or_stage_name": row["name"],
            "required_artifact_or_role": row["artifact"],
            "required_fields": row["fields"],
            "immutable_key": row["key"],
            "cardinality_or_order": row["cardinality"],
            "validation_rule": row["validation"],
            "provenance_propagation": row["propagation"],
            "deterministic_rule": row["determinism"],
            "failure_behavior": row["failure"],
        }
        for row in MATERIALIZATION_CONTRACTS
    ]


def state_rows(components: list[dict[str, str]]) -> list[dict[str, str]]:
    component_map = {row["component_id"]: row for row in components}
    rows = []
    for component in components:
        component_id = component["component_id"]
        rule = COMPONENT_RULES[component_id]
        roles = rule["roles"].split("|")
        invalid = [role for role in roles if role not in CURRENT_RECORD_ROLES and not role.startswith("FUTURE_")]
        if invalid:
            fail(f"Unknown materialization record roles for {component_id}: {invalid}")
        for state in sorted(PROFILE_STATES, key=lambda value: STATE_PRECEDENCE[value]):
            rows.append(
                {
                    "component_id": component_id,
                    "component_name": component["component_name"],
                    "profile_section": component["profile_section"],
                    "required_evidence_record_roles": rule["roles"],
                    "acceptable_evidence_types": component["evidence_types"],
                    "resolved_state": state,
                    "evaluation_precedence": str(STATE_PRECEDENCE[state]),
                    "deterministic_predicate": rule[state.lower()],
                    "required_provenance_predicate": component["required_provenance"],
                    "missingness_handling": (
                        "Copy source missingness exactly. NOT_FOUND may support MISSING only after complete defined queries; "
                        "NOT_QUERIED never becomes MISSING; UNKNOWN prevents OBSERVED/MISSING and resolves PARTIAL when any assessment exists."
                    ),
                    "dependency_preservation": component["dependency_boundary"],
                    "state_rationale_requirement": (
                        "Name the satisfied predicate, linked claim/record/source IDs, query coverage, provenance status, "
                        "conflict rule, and all unresolved uncertainty; do not state biological or therapeutic conclusions."
                    ),
                }
            )
    return rows


def validate_outputs(
    schema: list[dict[str, str]],
    states: list[dict[str, str]],
    components: list[dict[str, str]],
) -> list[dict[str, str]]:
    checks = []

    def check(name: str, passed: bool, observed: object, expected: object, detail: str) -> None:
        checks.append({"check": name, "status": "PASS" if passed else "FAIL", "observed": str(observed), "expected": str(expected), "detail": detail})
        if not passed:
            fail(f"Output validation failed: {name}")

    state_by_component = defaultdict(list)
    for row in states:
        state_by_component[row["component_id"]].append(row)
    all_fields = set(schema[0]) | set(states[0])
    forbidden = all_fields.intersection(FORBIDDEN_EXACT_FIELDS)
    check("materialization_contract_count", len(schema) == 15, len(schema), 15, "Eleven inputs/rules plus four deterministic stages.")
    check("materialization_stage_order", [int(row["stage_order"]) for row in schema] == list(range(1, 16)), [row["stage_order"] for row in schema], "1..15", "Canonical pipeline order.")
    check("state_rule_count", len(states) == 55, len(states), 55, "Five component-specific rules for eleven components.")
    check("component_state_coverage", set(state_by_component) == {row["component_id"] for row in components}, len(state_by_component), 11, "Every Task #020 component covered.")
    check("states_exact_per_component", all({row["resolved_state"] for row in values} == set(PROFILE_STATES) and len(values) == 5 for values in state_by_component.values()), "all exact", "five exact states", "No missing or additional state.")
    check("precedence_exact", all(STATE_PRECEDENCE[row["resolved_state"]] == int(row["evaluation_precedence"]) for row in states), "all exact", str(STATE_PRECEDENCE), "Conflict-first deterministic precedence.")
    check("acceptable_types_match_task020", all({row["acceptable_evidence_types"] for row in values} == {next(component["evidence_types"] for component in components if component["component_id"] == component_id)} for component_id, values in state_by_component.items()), "all matched", "all matched", "No evidence type invented or dropped.")
    check("required_record_roles_explicit", all(row["required_evidence_record_roles"] != "" for row in states), "all explicit", "all explicit", "Current and future record roles named.")
    check("provenance_propagation_explicit", all(row["required_provenance_predicate"] and row["dependency_preservation"] for row in states), "all explicit", "all explicit", "Provenance and dependencies retained.")
    check("no_profile_population_contract", schema[0]["required_artifact_or_role"] == "FUTURE_TARGET_MANIFEST_NOT_SUPPLIED_IN_TASK021", schema[0]["required_artifact_or_role"], "FUTURE_TARGET_MANIFEST_NOT_SUPPLIED_IN_TASK021", "No target universe supplied.")
    check("forbidden_fields_absent", not forbidden, sorted(forbidden), [], "No assessment fields.")
    check("all_cells_nonblank", all(all(value != "" for value in row.values()) for table in (schema, states) for row in table), "all nonblank", "all nonblank", "Contracts are explicit.")
    return checks


def write_csv(path: Path, fields: list[str], rows: Iterable[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_contract() -> None:
    CONTRACT_PATH.write_text(
        """# Deterministic Target Evidence Profile Builder Contract v0.1

## Scope

This contract specifies how a future builder must transform a frozen target manifest and evidence architecture into Task #020 long-form target-component profiles. Task #021 supplies no target manifest and creates no target profiles.

The builder is an evidence-organization component. It must not perform biological analysis, reinterpret source records, infer missing linkages, aggregate component states, or generate therapeutic conclusions.

## Required frozen inputs

A future materialization requires one hash-pinned run manifest containing:

1. immutable target-universe manifest with unique EnsemblIDs and explicit target order;
2. Task #020 profile schema, component registry, and interpretation rules;
3. Task #019 evidence-type interpretation boundaries and decision contexts;
4. controlled evidence ontology and source lineage;
5. bounded claim registry;
6. atomic evidence-record registry;
7. source-entity/version registry;
8. missingness/uncertainty registry;
9. record dependency graph;
10. Task #018-style artifact manifest with path/URI, size, SHA256, generator, and dependencies; and
11. versioned run configuration containing profile version, generator version, rules hash, input-manifest hash, frozen materialization timestamp, and serialization format.

No gene symbol may replace EnsemblID or be used as a fallback join. A missing artifact, identifier, version, required field, or hash is a hard failure unless the profile schema explicitly represents the condition as missingness.

## Cardinality and identity

For `N` frozen targets, materialization creates exactly `N × 11` component rows. The unique row key is `(EnsemblID, component_id)`. Target order comes from the frozen target manifest; component order comes from Task #020. No target or component may be silently omitted.

`profile_id` is deterministic:

```text
SHA256(EnsemblID + "|" + profile_version + "|" + input_manifest_hash + "|" + rules_hash)
```

No random UUID, process ID, filesystem traversal order, locale, or wall-clock value may affect profile content.

## Evidence selection

For each target-component row:

1. select bounded claims by immutable EnsemblID and controlled component domain;
2. select linked records by claim ID and acceptable component evidence type/record role;
3. preserve stable claim, record, and source IDs;
4. validate each record against the frozen source/version and artifact hash;
5. attach source-specific missingness and uncertainty without recoding;
6. induce the dependency subgraph among linked records;
7. preserve unknown dependencies as unknown; and
8. evaluate the component-specific state predicates in frozen precedence.

Records are deduplicated only when `record_id` is identical. Similar values, shared targets, matching symbols, repeated publications, or related database fields are not sufficient grounds for deletion or merging.

## Deterministic state resolution

Each component uses the exact Task #020 vocabulary. Predicates are evaluated in this order:

1. `CONFLICTING`
2. `OBSERVED`
3. `MISSING`
4. `PARTIAL`
5. `NOT_QUERIED`

The first satisfied, fully validated predicate is emitted. Exactly one state must resolve.

### CONFLICTING

Requires a component-specific, prespecified comparison rule and traceable incompatible records. Conflict takes precedence over otherwise observed evidence. Every conflicting record remains in the profile.

### OBSERVED

Requires the component-specific qualifying evidence criterion, complete minimum provenance, no material conflict, and valid record/source/artifact links. Record presence alone is insufficient.

### MISSING

Requires completion of every source/query scope defined for the component, zero qualifying evidence, and no unknown coverage, retrieval failure, or unresolved identifier problem. `MISSING` is absence of qualifying evidence in the frozen scope, not negative biological evidence.

### PARTIAL

Applies when some assessment or evidence exists but the observed or missing predicate cannot be satisfied because coverage, linkage, provenance, source version, quality characterization, or dependency resolution is incomplete. `UNKNOWN` with any attempted assessment resolves here unless a defined conflict takes precedence.

### NOT_QUERIED

Applies only when no eligible evidence acquisition or assessment occurred for the component. It cannot be inferred from a zero value, blank field, or identifier failure hidden as absence.

## Provenance propagation

Every profile row must carry:

- claim IDs;
- evidence-record IDs;
- source-entity IDs;
- source versions;
- input artifact IDs;
- input SHA256 hashes;
- missingness and uncertainty categories;
- dependency relationships and qualitative levels;
- conflict status and rationale;
- provenance-completeness state;
- generator/rules versions; and
- frozen materialization timestamp.

Pipe-delimited identifiers are unique and lexically sorted. Empty lists use the explicit sentinel `NONE`. Counts reconcile to the propagated record IDs and remain audit metadata only.

## Dependency preservation

The builder computes the induced dependency subgraph among component records. It never infers independence from the absence of an edge. `UNKNOWN` remains `UNKNOWN`. Reusing one record in multiple profile components preserves the same record ID and source/dependency lineage and does not create another observation.

No source, column, modality bucket, candidate count, publication count, compound, or trial may be treated as an independent vote without an explicit reviewed dependency assertion.

## Explicit non-inference rules

The builder must not:

- combine component states into an overall state, score, weighted sum, or ordering;
- compute a completeness percentage;
- upgrade evidence maturity automatically because a record, source, or component was added;
- convert `MISSING`, `NOT_FOUND`, `NOT_QUERIED`, `UNKNOWN`, or retrieval failure into negative biological evidence;
- interpret `OBSERVED` as favorable evidence;
- treat record quantity as evidence quality;
- treat dependent or unknown-lineage records as independent;
- infer intervention–target–disease linkage from co-occurrence or counts;
- infer causality, efficacy, safety, clinical benefit, target selection, or therapeutic conclusions; or
- use an LLM or free-text judgment to resolve a deterministic state.

`maturity_description` is generated from fixed qualitative templates naming characterized and unresolved elements. It cannot change the component state or produce an aggregate assessment.

## Canonical serialization

Future CSV output must use:

- UTF-8;
- LF line endings;
- comma delimiter;
- RFC-compatible quoting;
- Task #020 header in numeric `field_order`;
- target order then component order;
- base-10 integers without grouping;
- `TRUE`, `FALSE`, or `UNKNOWN` booleans;
- ISO8601 UTC timestamp copied from frozen run configuration;
- lexically sorted unique pipe-delimited lists; and
- `NONE` for empty required list/text fields.

The wall clock must not populate `generated_at_utc`. A repeated run with identical inputs, generator version, rule hashes, frozen timestamp, and serialization version must produce byte-identical output.

## QC and release gate

Before release, validate:

- all input hashes before and after generation;
- unique EnsemblIDs and profile IDs;
- exactly 11 component rows per target;
- unique `(EnsemblID, component_id)` keys;
- controlled states and exactly one resolved state per component;
- all claims/records/sources/dependencies resolve;
- record counts reconcile to propagated IDs;
- all required provenance fields are explicit;
- no forbidden assessment fields exist;
- canonical row/header/list order;
- output SHA256; and
- byte-identical recovery generation.

Any failure stops release. The builder must not repair, substitute, drop, reorder, or reinterpret evidence silently.
""",
        encoding="utf-8",
    )


def write_summary(
    schema: list[dict[str, str]],
    states: list[dict[str, str]],
    checks: list[dict[str, str]],
) -> None:
    sections = Counter(row["profile_section"] for row in states if row["resolved_state"] == "CONFLICTING")
    lines = [
        "# Task #021 profile materialization framework summary",
        "",
        "**Target profiles populated:** 0  ",
        f"**Materialization contracts/stages:** {len(schema)}  ",
        f"**Component-specific state rules:** {len(states)}  ",
        f"**Components covered:** {len({row['component_id'] for row in states})}  ",
        f"**Validation checks passed:** {sum(row['status'] == 'PASS' for row in checks)}/{len(checks)}  ",
        "**Scores, rankings, selections, recommendations, or therapeutic conclusions generated:** No",
        "",
        "## Architecture",
        "",
        "A future builder accepts a frozen target manifest, the Task #020 schema/component/rule bundle, bounded claims and atomic evidence records, source/version metadata, missingness/uncertainty records, dependency edges, interpretation boundaries, and an artifact/run manifest. Task #021 supplies no target manifest, so no profile row can be generated.",
        "",
        "For every future target, the builder creates exactly 11 component rows in the frozen 4/4/3 section order. Claims and records are joined only through immutable IDs. All evidence/source/artifact/dependency identifiers propagate to the component row.",
        "",
        "## State resolution",
        "",
        "Each of 11 components has five explicit predicates, producing 55 rules. Evaluation order is:",
        "",
        "1. `CONFLICTING`",
        "2. `OBSERVED`",
        "3. `MISSING`",
        "4. `PARTIAL`",
        "5. `NOT_QUERIED`",
        "",
        "`OBSERVED` requires the component-specific evidence criterion and complete provenance. `MISSING` requires complete source/query coverage with zero qualifying evidence. `PARTIAL` preserves incomplete coverage, linkage, provenance, quality characterization, or unknown status. `NOT_QUERIED` is reserved for no acquisition. None of these states is favorable or unfavorable.",
        "",
        "## Provenance and dependency",
        "",
        "Every profile row preserves claim IDs, record IDs, source IDs/versions, artifact IDs/hashes, missingness, uncertainty, conflicts, dependency relationships/levels, generator version, and frozen snapshot time. Reused records retain their identity across components. Absence of a dependency edge never proves independence.",
        "",
        "## Determinism",
        "",
        "Identical frozen inputs, input-manifest hash, generator/rules versions, frozen materialization timestamp, and CSV format must yield byte-identical output. Target/component/list ordering and serialization are canonical. Wall-clock time, randomness, locale, filesystem order, symbols, and free-text judgment cannot affect output.",
        "",
        "## Explicit boundaries",
        "",
        "The contract prohibits component aggregation, automatic maturity upgrades, missing-to-negative conversion, record-count quality inference, dependency inflation, inferred clinical linkage, and any causal, efficacy, safety, clinical-benefit, target-selection, or therapeutic conclusion.",
        "",
        "## Validation",
        "",
        "All frozen Task #018, Task #019, and Task #020 hashes matched. All 193 Task #018 governed artifacts retained size and SHA256, including the governed 207,242-row Task #014 evidence-record registry. No target manifest was supplied and zero profile records were populated.",
    ]
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate_postflight(start_head: str) -> None:
    if run_git("rev-parse", "HEAD") != start_head:
        fail("Git HEAD changed during Task #021.")
    if run_git("diff", "--name-only") or run_git("diff", "--cached", "--name-only"):
        fail("An existing tracked file changed during Task #021.")
    validate_hashes()
    validate_governance()


def write_session(
    started: datetime,
    git_info: dict[str, str],
    hashes: dict[str, str],
    input_counts: dict[str, int],
    checks: list[dict[str, str]],
) -> None:
    values = {
        "task": "021",
        "purpose": "deterministic target evidence profile materialization contract",
        "started_at_utc": started.isoformat(),
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "git_branch": git_info["branch"],
        "git_head_before": git_info["head"],
        "git_head_after": run_git("rev-parse", "HEAD"),
        "git_origin": git_info["remote"],
        "frozen_task020_base_commit": TASK020_BASE_COMMIT,
        "target_profiles_populated": "0",
        "profile_rows_populated": "0",
        "materialization_contract_count": "15",
        "component_state_rule_count": "55",
        "network_access": "NOT_USED",
        "packages_installed_or_updated": "FALSE",
        "existing_files_modified": "FALSE",
        "scoring_generated": "FALSE",
        "ranking_generated": "FALSE",
        "candidate_selection_generated": "FALSE",
        "target_recommendations_generated": "FALSE",
        "therapeutic_conclusions_generated": "FALSE",
        "git_commit_or_push": "FALSE",
        "script_sha256": sha256(SCRIPT_PATH),
        "plan_sha256": sha256(PLAN_PATH),
        "governed_record_registry_sha256": GOVERNED_RECORD_SHA256,
    }
    for name, value in input_counts.items():
        values[f"input_validation.{name}"] = str(value)
    for name, digest in hashes.items():
        values[f"frozen_input_sha256.{relative(INPUTS[name])}"] = digest
    for row in checks:
        values[f"output_validation.{row['check']}"] = row["status"]
    for path in (SCHEMA_PATH, STATE_PATH, CONTRACT_PATH, SUMMARY_PATH):
        values[f"output_sha256.{relative(path)}"] = sha256(path)
    SESSION_PATH.write_text(
        "".join(f"{key}={values[key]}\n" for key in sorted(values)), encoding="utf-8"
    )


def main() -> None:
    started = datetime.now(timezone.utc)
    git_info = validate_repository()
    hashes = validate_hashes()
    artifact_count, class_d_count = validate_governance()
    components, counts = validate_frozen_frameworks()
    counts["task018_artifact_count"] = artifact_count
    counts["task018_class_d_count"] = class_d_count

    schema = materialization_rows()
    states = state_rows(components)
    checks = validate_outputs(schema, states, components)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    allowed = {SCHEMA_PATH.name, STATE_PATH.name, CONTRACT_PATH.name, SUMMARY_PATH.name, SESSION_PATH.name}
    unexpected = {path.name for path in OUTPUT_DIR.iterdir() if path.name not in allowed}
    if unexpected:
        fail(f"Unexpected Task #021 output files: {sorted(unexpected)}")

    write_csv(SCHEMA_PATH, list(schema[0]), schema)
    write_csv(STATE_PATH, list(states[0]), states)
    write_contract()
    write_summary(schema, states, checks)
    validate_postflight(git_info["head"])
    write_session(started, git_info, hashes, counts, checks)

    print("Created files:")
    for path in (SCHEMA_PATH, STATE_PATH, CONTRACT_PATH, SUMMARY_PATH, SESSION_PATH):
        print(f"- {relative(path)}")
    print(f"Materialization contracts/stages: {len(schema)}")
    print(f"Component-specific state rules: {len(states)}")
    print(f"Validation checks passed: {sum(row['status'] == 'PASS' for row in checks)}/{len(checks)}")
    print("Target profiles populated: 0")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
