#!/usr/bin/env python3
"""Build the Task #020 target evidence profile architecture.

This local, standard-library builder defines a schema, component registry, and
interpretation rules. It does not populate profiles, analyze genes, aggregate
evidence, score, rank, select, recommend, or draw therapeutic conclusions.
"""

from __future__ import annotations

import csv
import hashlib
import os
import platform
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
TASK019_BASE_COMMIT = "8d58bcd4be560269d4dd096fce5f6fc9e5c69884"
EXPECTED_BRANCH = "main"
EXPECTED_REMOTE_FRAGMENT = "SichengChen-web/luad-target-dossier"

SCRIPT_PATH = ROOT / "analysis/20_build_target_evidence_profile_framework.py"
PLAN_PATH = ROOT / "docs/target_evidence_profile_framework_v0.1.md"
OUTPUT_DIR = ROOT / "outputs/evidence_profiles"
SCHEMA_PATH = OUTPUT_DIR / "profile_schema.csv"
COMPONENT_PATH = OUTPUT_DIR / "profile_component_registry.csv"
RULES_PATH = OUTPUT_DIR / "profile_interpretation_rules.csv"
SUMMARY_PATH = OUTPUT_DIR / "evidence_profile_summary.md"
SESSION_PATH = OUTPUT_DIR / "session_info.txt"

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
    "domain_registry": ROOT / "outputs/evidence_ontology/evidence_domain_registry.csv",
    "independence_map": ROOT / "outputs/evidence_ontology/evidence_independence_map.csv",
    "source_lineage": ROOT / "outputs/evidence_ontology/evidence_source_lineage.csv",
    "claim_registry": ROOT / "outputs/evidence_claim_architecture/evidence_claim_registry.csv",
    "dependency_graph": ROOT / "outputs/evidence_claim_architecture/evidence_dependency_graph.csv",
    "missingness_uncertainty_registry": ROOT
    / "outputs/evidence_claim_architecture/missingness_uncertainty_registry.csv",
    "source_entity_registry": ROOT / "outputs/evidence_claim_architecture/source_entity_registry.csv",
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
    "domain_registry": "ee62ce66f2ca4726c9365da347198251b9bd77d2dead87b8409221505f2d03b8",
    "independence_map": "d99bbaa8fe5e6229774ac2bf73d84de8fbd367e585d692eb1273ecc7b5c53945",
    "source_lineage": "e9496e8bbf953fdffdbaed7e09936a8493230fc74939597537f8960fabf19f2c",
    "claim_registry": "0d963a4c5c8f9586f81369e33df0a2b7e57bb37ac8ceab4ce54498baf2351a66",
    "dependency_graph": "011839f10c48e197f9f1c0e2262565e562d3a2cf53dd0936f21ddcb4ed5c2256",
    "missingness_uncertainty_registry": "3bbe080b1ed46dd159a86b53fb707572f988361af96e001188b69da0daa9147d",
    "source_entity_registry": "1b1379066226b5f69b626fe4a97628f7b6da6e585515aa8609218eef65bf8056",
}

ALLOWED_UNTRACKED_FILES = {
    "analysis/20_build_target_evidence_profile_framework.py",
    "docs/target_evidence_profile_framework_v0.1.md",
}
ALLOWED_UNTRACKED_PREFIX = "outputs/evidence_profiles/"

ALLOWED_PROFILE_STATES = [
    "OBSERVED",
    "PARTIAL",
    "MISSING",
    "NOT_QUERIED",
    "CONFLICTING",
]

TASK014_MISSINGNESS = ["OBSERVED", "NOT_FOUND", "NOT_QUERIED", "NOT_APPLICABLE", "UNKNOWN"]
TASK014_UNCERTAINTY = [
    "SOURCE_LIMITATION",
    "INCOMPLETE_COVERAGE",
    "CONFLICTING_RECORDS",
    "DEPENDENCY_UNCERTAIN",
    "TEMPORAL_UNCERTAINTY",
]
TASK014_DEPENDENCY_RELATIONSHIPS = [
    "SAME_SOURCE",
    "SHARED_PUBLICATION",
    "SHARED_DATASET",
    "SHARED_COMPOUND",
    "SHARED_TRIAL",
    "UNKNOWN",
]
TASK014_DEPENDENCY_LEVELS = ["INDEPENDENT", "PARTIALLY_DEPENDENT", "DEPENDENT", "UNKNOWN"]

FORBIDDEN_EXACT_FIELDS = {
    "score",
    "rank",
    "priority",
    "target_selection",
    "recommendation",
    "therapeutic_direction",
}

DOMAIN_ORDER = [
    "DOM_TRANSCRIPTOMIC_DISCOVERY",
    "DOM_DISEASE_ASSOCIATION",
    "DOM_GENETIC_EVIDENCE",
    "DOM_FUNCTIONAL_DEPENDENCY",
    "DOM_PHARMACOLOGY",
    "DOM_TRACTABILITY",
    "DOM_CLINICAL_DEVELOPMENT",
    "DOM_SAFETY",
]

PROFILE_SCHEMA = [
    (1, "profile_id", "PROFILE", "STRING", "TRUE", "UNIQUE_NONEMPTY", "Derived from immutable EnsemblID and profile_version", "Stable identifier for one versioned target evidence profile.", "Identity only; it contains no scientific assessment."),
    (2, "profile_version", "PROFILE", "STRING", "TRUE", "VERSIONED_VALUE", "Versioned profile configuration", "Version of the profile architecture and state-resolution rules.", "A newer version is not inherently better or more mature."),
    (3, "EnsemblID", "PROFILE", "STRING", "TRUE", "IMMUTABLE_ENSEMBL_GENE_ID", "Task #009–#014 immutable identifier", "Only immutable target join key.", "Gene symbols may be displayed separately but never replace or join this key."),
    (4, "profile_section_id", "COMPONENT", "STRING", "TRUE", "CONTROLLED_SECTION_ID", "profile_component_registry.csv", "Section containing the component.", "Section membership does not create independent evidence."),
    (5, "component_id", "COMPONENT", "STRING", "TRUE", "CONTROLLED_COMPONENT_ID", "profile_component_registry.csv", "Component represented by this long-form target-component row.", "A component is an organizational view, not a vote."),
    (6, "component_state", "COMPONENT", "CATEGORY", "TRUE", "OBSERVED|PARTIAL|MISSING|NOT_QUERIED|CONFLICTING", "Deterministic state-resolution rule", "Evidence-availability and uncertainty state for this component.", "The state is not favorable/unfavorable and has no numerical ordering."),
    (7, "state_rationale", "COMPONENT", "STRING", "TRUE", "NONEMPTY_TEXT", "Bounded claims, records, missingness, and uncertainty", "Traceable explanation for the component state.", "Narrative must not exceed the source-supported claim."),
    (8, "evidence_domain_ids", "COMPONENT", "PIPE_DELIMITED_ID_LIST", "TRUE", "TASK013_DOMAIN_IDS", "profile_component_registry.csv", "Ontology domains represented by the component.", "Multiple domains are not additive support."),
    (9, "evidence_type_ids", "COMPONENT", "PIPE_DELIMITED_ID_LIST", "TRUE", "TASK013_EVIDENCE_TYPE_IDS", "profile_component_registry.csv", "Evidence types eligible for the component.", "Eligibility does not mean that evidence was observed."),
    (10, "claim_ids", "PROVENANCE", "PIPE_DELIMITED_ID_LIST", "TRUE", "TASK014_CLAIM_IDS_OR_NONE", "Task #014 claim architecture", "Bounded claims linked to the component.", "A claim is an evidence state, not a therapeutic conclusion."),
    (11, "evidence_record_ids", "PROVENANCE", "PIPE_DELIMITED_ID_LIST", "TRUE", "TASK014_RECORD_IDS_OR_NONE", "Task #014 evidence records", "Atomic evidence records linked to the component.", "Record count does not measure evidence quality or independence."),
    (12, "source_entity_ids", "PROVENANCE", "PIPE_DELIMITED_ID_LIST", "TRUE", "TASK014_SOURCE_IDS_OR_NONE", "Task #014 source entities", "Source entities underlying linked records.", "Different source IDs still require dependency review."),
    (13, "source_versions", "PROVENANCE", "PIPE_DELIMITED_KEY_VALUE_LIST", "TRUE", "VERSION_OR_UNKNOWN", "Source lineage and retrieval sessions", "Version/release for every external or derived source.", "Unknown versions make interpretation incomplete."),
    (14, "input_artifact_ids", "PROVENANCE", "PIPE_DELIMITED_ID_LIST", "TRUE", "TASK018_ARTIFACT_IDS", "Task #018 artifact manifest", "Governed input artifacts used to construct the component.", "Artifact presence does not add scientific evidence."),
    (15, "input_sha256s", "PROVENANCE", "PIPE_DELIMITED_SHA256_LIST", "TRUE", "64_CHARACTER_SHA256_VALUES", "Task #018 artifact manifest and task session", "Frozen content hashes matching each input artifact.", "A hash establishes content identity, not scientific validity."),
    (16, "missingness_statuses", "UNCERTAINTY", "PIPE_DELIMITED_CATEGORY_LIST", "TRUE", "OBSERVED|NOT_FOUND|NOT_QUERIED|NOT_APPLICABLE|UNKNOWN", "Task #014 missingness registry", "Source/record missingness retained without collapse.", "NOT_FOUND and NOT_QUERIED are not negative biological evidence."),
    (17, "uncertainty_categories", "UNCERTAINTY", "PIPE_DELIMITED_CATEGORY_LIST", "TRUE", "SOURCE_LIMITATION|INCOMPLETE_COVERAGE|CONFLICTING_RECORDS|DEPENDENCY_UNCERTAIN|TEMPORAL_UNCERTAINTY", "Task #014 uncertainty registry", "Known uncertainty categories attached to the component.", "Uncertainty is not converted into a confidence penalty."),
    (18, "dependency_relationships", "DEPENDENCY", "PIPE_DELIMITED_CATEGORY_LIST", "TRUE", "SAME_SOURCE|SHARED_PUBLICATION|SHARED_DATASET|SHARED_COMPOUND|SHARED_TRIAL|UNKNOWN", "Task #014 dependency graph", "Relationships among linked evidence records.", "Absence of an edge does not prove independence."),
    (19, "dependency_levels", "DEPENDENCY", "PIPE_DELIMITED_CATEGORY_LIST", "TRUE", "INDEPENDENT|PARTIALLY_DEPENDENT|DEPENDENT|UNKNOWN", "Task #014 dependency graph", "Qualitative dependency levels for linked records.", "Levels are not numerical weights or penalties."),
    (20, "conflict_present", "UNCERTAINTY", "CATEGORY", "TRUE", "TRUE|FALSE|UNKNOWN", "Record comparison under component-specific rules", "Whether a material evidence conflict is documented.", "FALSE means no defined conflict was found, not universal agreement."),
    (21, "conflict_description", "UNCERTAINTY", "STRING", "TRUE", "NONEMPTY_TEXT_OR_NONE", "Conflicting records and comparison rule", "Preserves the nature and source of any conflict.", "Conflicts must not be averaged away or silently removed."),
    (22, "provenance_complete", "PROVENANCE", "CATEGORY", "TRUE", "TRUE|FALSE|UNKNOWN", "Required provenance-field validation", "Whether minimum provenance is present for every linked record.", "Complete provenance does not establish evidence quality."),
    (23, "evidence_record_count", "AUDIT", "INTEGER", "TRUE", "NONNEGATIVE_INTEGER", "Count of linked atomic evidence records", "Audit count of records represented in the component.", "Quantity is not quality, confidence, independence, or support strength."),
    (24, "observed_record_count", "AUDIT", "INTEGER", "TRUE", "NONNEGATIVE_INTEGER_NOT_EXCEEDING_RECORD_COUNT", "Count of linked records with observed status", "Audit count of observed bounded records.", "More observed records do not imply stronger evidence."),
    (25, "maturity_description", "INTERPRETATION", "STRING", "TRUE", "BOUNDED_QUALITATIVE_TEXT", "Component states, provenance, uncertainty, and missingness", "Qualitative description of what is sufficiently characterized and what remains unresolved.", "Maturity is evidence availability, not target quality or development merit."),
    (26, "interpretation_boundary_ids", "INTERPRETATION", "PIPE_DELIMITED_EVIDENCE_TYPE_IDS", "TRUE", "TASK019_EVIDENCE_TYPE_IDS", "Task #019 interpretation boundaries", "Evidence-type boundaries applicable to the component.", "Boundaries constrain claims and cannot be waived by record quantity."),
    (27, "generated_by", "REPRODUCIBILITY", "STRING", "TRUE", "VERSIONED_GENERATOR_PATH", "Future profile builder", "Versioned generator that materialized the profile.", "Generator identity does not validate its scientific logic."),
    (28, "generated_at_utc", "REPRODUCIBILITY", "DATETIME", "TRUE", "ISO8601_UTC", "Future profile builder runtime", "Timestamp for the generated profile snapshot.", "Recency does not make evidence independent or stronger."),
]

COMPONENTS = [
    {
        "section_id": "SEC_BIOLOGICAL_DISCOVERY",
        "section": "Biological Discovery Profile",
        "component_id": "COMP_TRANSCRIPTOMIC_EVIDENCE",
        "component": "Transcriptomic evidence",
        "domains": "DOM_TRANSCRIPTOMIC_DISCOVERY",
        "types": "EV_TCGA_DE_EFFECT|EV_TCGA_DE_SIGNIFICANCE|EV_TCGA_DE_ROBUSTNESS",
        "context": "Biological Discovery",
        "question": "Is a LUAD tumour-associated expression alteration present and robust to the prespecified related models?",
        "criterion": "OBSERVED requires a traceable primary effect/significance record and its model-robustness state; material direction conflict resolves to CONFLICTING.",
        "provenance": "TCGA cohort|recount3/gencode_v26|final cohort|design/contrast|S0-S6 analysis versions|record IDs|artifact hashes",
        "dependency": "Effect, significance, and S1-S6 robustness share the same TCGA cohort and are one dependent evidence family.",
    },
    {
        "section_id": "SEC_BIOLOGICAL_DISCOVERY",
        "section": "Biological Discovery Profile",
        "component_id": "COMP_DISEASE_ASSOCIATION",
        "component": "Disease association",
        "domains": "DOM_DISEASE_ASSOCIATION",
        "types": "EV_OT_LUAD_DIRECT_ASSOCIATION|EV_OT_LUAD_INDIRECT_ASSOCIATION|EV_OT_LITERATURE_COUNT",
        "context": "Biological Discovery",
        "question": "What source-grounded evidence associates the target with LUAD or its ontology context?",
        "criterion": "OBSERVED requires at least one traceable source-native association record; indirect and literature views remain qualifiers rather than independent confirmation.",
        "provenance": "Open Targets release/API|target ID|LUAD disease ID|datasource and publication lineage|query|artifact hashes",
        "dependency": "Direct, indirect, and literature views share the Open Targets platform and may reuse upstream records.",
    },
    {
        "section_id": "SEC_BIOLOGICAL_DISCOVERY",
        "section": "Biological Discovery Profile",
        "component_id": "COMP_GENETIC_EVIDENCE",
        "component": "Genetic evidence",
        "domains": "DOM_GENETIC_EVIDENCE",
        "types": "EV_GENETIC_CANCER",
        "context": "Biological Discovery",
        "question": "Do inherited or tumour-acquired genetic observations support a LUAD-relevant biological relationship?",
        "criterion": "Current state is NOT_QUERIED until a dedicated, provenance-complete genetic evidence task is available.",
        "provenance": "Source release|cohort|variant/alteration and gene IDs|disease definition|statistical model|sample overlap|artifact hashes",
        "dependency": "Future genetic evidence may share TCGA samples or already contribute to Open Targets association evidence.",
    },
    {
        "section_id": "SEC_BIOLOGICAL_DISCOVERY",
        "section": "Biological Discovery Profile",
        "component_id": "COMP_FUNCTIONAL_DEPENDENCY",
        "component": "Functional dependency",
        "domains": "DOM_FUNCTIONAL_DEPENDENCY",
        "types": "EV_FUNCTIONAL_CRISPR_DEPENDENCY",
        "context": "Biological Discovery",
        "question": "Does controlled perturbation affect LUAD-relevant cancer-model fitness or function?",
        "criterion": "Current state is NOT_QUERIED until model-level perturbation evidence with screen QC and lineage is available.",
        "provenance": "Screen release|model/lineage|guide or perturbation reagent|effect definition|replicates|QC|artifact hashes",
        "dependency": "Shared cell lines, guide libraries, or source screens must not be counted as independent experiments.",
    },
    {
        "section_id": "SEC_THERAPEUTIC_DEVELOPMENT",
        "section": "Therapeutic Development Profile",
        "component_id": "COMP_PHARMACOLOGY",
        "component": "Pharmacology",
        "domains": "DOM_PHARMACOLOGY",
        "types": "EV_CHEMBL_TARGET_ANNOTATION|EV_OT_DRUG_CANDIDATE_COUNT|EV_CHEMBL_COMPOUND_TARGET",
        "context": "Therapeutic Development",
        "question": "What source-grounded target annotations, compounds, activities, potency, selectivity, and mechanisms are available?",
        "criterion": "Target annotation or candidate counts alone resolve at most PARTIAL; OBSERVED requires qualifying compound-target evidence with assay/mechanism provenance.",
        "provenance": "Source release|target/compound/assay IDs|target confidence|activity value/unit|mechanism|query|artifact hashes",
        "dependency": "Open Targets drug records may reuse ChEMBL compounds and overlap tractability or clinical-precedence evidence.",
    },
    {
        "section_id": "SEC_THERAPEUTIC_DEVELOPMENT",
        "section": "Therapeutic Development Profile",
        "component_id": "COMP_TRACTABILITY",
        "component": "Tractability",
        "domains": "DOM_TRACTABILITY",
        "types": "EV_OT_TRACTABILITY_SM|EV_OT_TRACTABILITY_AB|EV_OT_TRACTABILITY_PR|EV_OT_TRACTABILITY_OC",
        "context": "Therapeutic Development",
        "question": "Which explicitly defined therapeutic modalities have source-grounded feasibility assessments?",
        "criterion": "OBSERVED requires a traceable modality-specific assessment; multiple positive modalities remain one shared-framework component.",
        "provenance": "Open Targets release/API|target ID|modality|assessment/bucket IDs|upstream evidence|artifact hashes",
        "dependency": "All modality buckets share the Open Targets tractability framework and may reuse pharmacology or clinical precedent.",
    },
    {
        "section_id": "SEC_THERAPEUTIC_DEVELOPMENT",
        "section": "Therapeutic Development Profile",
        "component_id": "COMP_SAFETY",
        "component": "Safety",
        "domains": "DOM_SAFETY",
        "types": "EV_OT_SAFETY_LIABILITY",
        "context": "Therapeutic Development",
        "question": "What curated target-related safety liabilities are documented, and what risk evidence remains absent?",
        "criterion": "OBSERVED means a traceable liability observation exists; MISSING means no qualifying record after a defined query and never means safe.",
        "provenance": "Open Targets release/API|target/liability/datasource IDs|study/publication|context|query|artifact hashes",
        "dependency": "Liability records can share datasource, study, publication, event, compound, or mechanism.",
    },
    {
        "section_id": "SEC_THERAPEUTIC_DEVELOPMENT",
        "section": "Therapeutic Development Profile",
        "component_id": "COMP_CLINICAL_DEVELOPMENT",
        "component": "Clinical development evidence",
        "domains": "DOM_CLINICAL_DEVELOPMENT",
        "types": "EV_CLINICAL_TRIAL_DEVELOPMENT",
        "context": "Therapeutic Development",
        "question": "Has a traceably target-linked intervention reached human investigation in a defined disease context?",
        "criterion": "Current state is NOT_QUERIED until trial-level intervention-target-disease linkage is retrieved and validated.",
        "provenance": "Registry/version|trial/intervention/target/disease IDs|linkage basis|phase/status|retrieval time|artifact hashes",
        "dependency": "Trial records may overlap Open Targets candidate counts and tractability clinical-precedence assessments.",
    },
    {
        "section_id": "SEC_TRANSLATIONAL",
        "section": "Translational Profile",
        "component_id": "COMP_HUMAN_EVIDENCE",
        "component": "Human evidence",
        "domains": "DOM_GENETIC_EVIDENCE|DOM_CLINICAL_DEVELOPMENT",
        "types": "EV_GENETIC_CANCER|EV_CLINICAL_TRIAL_DEVELOPMENT",
        "context": "Translational Context",
        "question": "What explicitly human-derived genetic or interventional evidence is available for the target hypothesis?",
        "criterion": "OBSERVED requires at least one explicitly human-derived, provenance-complete record; ontology membership alone does not certify human relevance.",
        "provenance": "Human cohort or trial identity|target/variant/intervention IDs|disease context|source version|record IDs|artifact hashes",
        "dependency": "Genetic cohorts and trials may overlap source aggregators; records reused in other components retain the same identity.",
    },
    {
        "section_id": "SEC_TRANSLATIONAL",
        "section": "Translational Profile",
        "component_id": "COMP_CLINICAL_LINKAGE",
        "component": "Clinical linkage",
        "domains": "DOM_DISEASE_ASSOCIATION|DOM_PHARMACOLOGY|DOM_CLINICAL_DEVELOPMENT",
        "types": "EV_OT_LUAD_DIRECT_ASSOCIATION|EV_CHEMBL_COMPOUND_TARGET|EV_CLINICAL_TRIAL_DEVELOPMENT",
        "context": "Translational Context",
        "question": "Can an intervention be traceably linked to the target and LUAD within a clinical-development record?",
        "criterion": "OBSERVED requires record-level intervention-target-disease linkage; co-occurring target, drug, and trial counts resolve at most PARTIAL.",
        "provenance": "Target/disease/compound/intervention/trial IDs|linkage method|source versions|record lineage|artifact hashes",
        "dependency": "Reusing association, compound, or trial records from other components does not create new evidence or independent support.",
    },
    {
        "section_id": "SEC_TRANSLATIONAL",
        "section": "Translational Profile",
        "component_id": "COMP_RISK_CONTEXT",
        "component": "Risk context",
        "domains": "DOM_SAFETY",
        "types": "EV_OT_SAFETY_LIABILITY",
        "context": "Translational Context",
        "question": "What current target-liability evidence and unresolved translational risk are represented?",
        "criterion": "The component state reflects the current safety-liability evidence state; maturity_description must separately state that risk characterization remains incomplete without normal-tissue, essentiality, exposure, and toxicology evidence.",
        "provenance": "Liability records|on/off-target attribution|human relevance|exposure context|source versions|artifact hashes",
        "dependency": "The same safety records can appear in therapeutic and translational views but remain one evidence lineage.",
    },
]

INTERPRETATION_RULES = [
    ("RULE_STATE_OBSERVED", "STATE", "OBSERVED", "Qualifying evidence records are present under the component criterion with traceable provenance.", "A favorable biological or therapeutic conclusion.", "Retain bounded claim, record, source, uncertainty, and dependency identifiers."),
    ("RULE_STATE_PARTIAL", "STATE", "PARTIAL", "Some relevant evidence or metadata is present but coverage, linkage, quality characterization, or provenance remains incomplete.", "Half-support, intermediate quality, or a numerical midpoint.", "State exactly which evidence or provenance elements remain incomplete."),
    ("RULE_STATE_MISSING", "STATE", "MISSING", "A defined and completed assessment found no qualifying evidence for the component.", "Absence of the biological property, lack of potential, safety, or unfavorable evidence.", "Preserve queried sources, scope, NOT_FOUND records, date, and coverage limitations."),
    ("RULE_STATE_NOT_QUERIED", "STATE", "NOT_QUERIED", "The component has not been acquired or could not be queried under the defined identifier/source requirements.", "A negative result or an assumption that no evidence exists.", "Record why it was not queried and what source/query would be required."),
    ("RULE_STATE_CONFLICTING", "STATE", "CONFLICTING", "Materially incompatible observations exist under a prespecified comparison rule.", "Permission to average away, delete, or choose the preferred record.", "Retain every conflicting record, provenance chain, comparison rule, and unresolved interpretation."),
    ("RULE_AVAILABILITY", "CAN_DESCRIBE", "ALL_COMPONENTS", "Which evidence types and records are observed, partial, missing, not queried, or conflicting.", "Target quality or therapeutic merit.", "Report states by component without cross-component arithmetic."),
    ("RULE_MATURITY", "CAN_DESCRIBE", "PROFILE", "Which components are sufficiently characterized for bounded interpretation and which remain immature or unresolved.", "Development stage, target quality, or probability of success.", "Use qualitative text tied to component states, provenance, and missingness; do not compute completeness percentages."),
    ("RULE_UNCERTAINTY", "CAN_DESCRIBE", "PROFILE", "Known source, coverage, temporal, conflict, and dependency uncertainties.", "A numerical confidence value or penalty.", "Preserve Task #014 categories and record-specific explanations."),
    ("RULE_MISSING_NOT_NEGATIVE", "BOUNDARY", "MISSING|NOT_QUERIED", "The current profile lacks qualifying evidence or acquisition.", "Negative biological evidence, lack of druggability, lack of clinical potential, or safety.", "Keep source-specific missingness and query coverage explicit."),
    ("RULE_QUANTITY_NOT_QUALITY", "BOUNDARY", "EVIDENCE_RECORD_COUNT", "How many atomic records are linked for audit purposes.", "Evidence quality, strength, confidence, or independent convergence.", "Assess study/assay quality and provenance separately; never use counts as a proxy."),
    ("RULE_DEPENDENCY_NOT_VOTES", "BOUNDARY", "DEPENDENT_RECORDS", "Known shared source, dataset, publication, compound, trial, or unresolved lineage.", "Multiple independent confirmations.", "Reuse stable record IDs and dependency edges across every component view."),
    ("RULE_COMPLETENESS_NOT_QUALITY", "BOUNDARY", "PROFILE", "How many components have characterized states and provenance.", "Target quality, biological importance, clinical readiness, or development merit.", "Do not calculate or expose an aggregate completeness score or percentage."),
    ("RULE_NO_AGGREGATION", "BOUNDARY", "PROFILE", "A structured collection of component states and provenance.", "An additive, weighted, ordinal, or hidden composite assessment.", "Present the component grid and unresolved evidence directly; no aggregation formula."),
    ("RULE_NO_CAUSALITY", "CANNOT_ESTABLISH", "PROFILE", "Associative and mechanistic evidence availability.", "Biological or disease causality.", "Require dedicated genetic and controlled perturbational validation with independent lineage."),
    ("RULE_NO_EFFICACY", "CANNOT_ESTABLISH", "PROFILE", "Pharmacology, tractability, and development evidence availability.", "Drug or modality efficacy.", "Require target engagement, disease-model efficacy, exposure, and appropriately designed clinical evidence."),
    ("RULE_NO_SAFETY", "CANNOT_ESTABLISH", "PROFILE", "Known safety-liability evidence and missing risk domains.", "Safety, acceptable therapeutic window, or absence of toxicity.", "Require exposure-contextualized on/off-target toxicology, normal-tissue, essentiality, and human safety evidence."),
    ("RULE_NO_CLINICAL_BENEFIT", "CANNOT_ESTABLISH", "PROFILE", "Human investigation and clinical-linkage evidence availability.", "Clinical benefit, utility, approval, or favorable benefit-risk.", "Require interpretable trial results, endpoints, comparator, population, exposure, and safety outcomes."),
    ("RULE_NO_TARGET_ORDERING", "CANNOT_ESTABLISH", "PROFILE", "A target's evidence organization and unresolved uncertainty.", "Any target ordering, selection, or therapeutic recommendation.", "Any future assessment requires a separate versioned scientific and validation specification."),
]


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
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        fail(
            f"Git command failed: git {' '.join(args)}\n"
            f"stdout: {result.stdout.strip()}\n"
            f"stderr: {result.stderr.strip()}"
        )
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
        ["git", "merge-base", "--is-ancestor", TASK019_BASE_COMMIT, "HEAD"], cwd=ROOT, check=False
    ).returncode != 0:
        fail(f"Frozen Task #019 commit is not an ancestor of HEAD {head}.")
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
            fail(f"Frozen input is missing: {rel}")
        if not run_git("ls-files", "--error-unmatch", rel, check=False):
            fail(f"Frozen input is not committed: {rel}")
        if run_git("diff", "--name-only", TASK019_BASE_COMMIT, "HEAD", "--", rel):
            fail(f"Frozen input changed after Task #019: {rel}")
    return {"branch": branch, "head": head, "remote": remote}


def validate_hashes() -> dict[str, str]:
    hashes = {}
    for name, path in INPUTS.items():
        actual = sha256(path)
        if actual != EXPECTED_HASHES[name]:
            fail(f"Frozen hash mismatch for {relative(path)}: {actual}")
        hashes[name] = actual
    return hashes


def validate_governance() -> tuple[int, int]:
    _, manifest = read_csv(INPUTS["artifact_manifest"])
    if len(manifest) != 193:
        fail(f"Expected 193 Task #018 artifacts; observed {len(manifest)}.")
    for row in manifest:
        path = ROOT / row["relative_path"]
        if not (path.is_file() or path.is_symlink()):
            fail(f"Governed artifact missing: {row['relative_path']}")
        if path.lstat().st_size != int(row["file_size_bytes"]) or sha256(path) != row["sha256"]:
            fail(f"Governed artifact changed: {row['relative_path']}")
    session = read_session(INPUTS["artifact_governance_session"])
    for key in ("artifact_manifest", "artifact_classification", "reproducibility_contract", "artifact_governance_summary"):
        path = INPUTS[key]
        session_key = f"output_sha256.{relative(path)}"
        if session.get(session_key) != sha256(path):
            fail(f"Task #018 session does not reconcile: {relative(path)}")
    return len(manifest), sum(row["artifact_class"] == "D" for row in manifest)


def validate_architecture() -> tuple[
    dict[str, dict[str, str]], dict[str, dict[str, str]], dict[str, int]
]:
    _, domains_raw = read_csv(INPUTS["domain_registry"])
    domains = {row["domain_id"]: row for row in domains_raw}
    if list(domains) != DOMAIN_ORDER:
        fail("Task #013 domain vocabulary/order changed.")
    evidence_type_to_domain = {}
    for row in domains_raw:
        for evidence_type in row["evidence_type"].split("|"):
            if evidence_type in evidence_type_to_domain:
                fail(f"Duplicate evidence type: {evidence_type}")
            evidence_type_to_domain[evidence_type] = row["domain_id"]
    if len(evidence_type_to_domain) != 17:
        fail("Expected 17 Task #013 evidence types.")

    _, contexts = read_csv(INPUTS["decision_context_registry"])
    if len(contexts) != 3 or len({row["decision_context_id"] for row in contexts}) != 3:
        fail("Expected three unique Task #019 contexts.")
    _, context_matrix = read_csv(INPUTS["evidence_context_matrix"])
    if len(context_matrix) != 24:
        fail("Expected 24 Task #019 evidence-context rows.")
    _, boundaries = read_csv(INPUTS["interpretation_boundaries"])
    boundary_map = {row["evidence_type"]: row for row in boundaries}
    if len(boundary_map) != 17 or set(boundary_map) != set(evidence_type_to_domain):
        fail("Task #019 interpretation boundaries do not cover the ontology.")

    _, independence = read_csv(INPUTS["independence_map"])
    if len(independence) != 31:
        fail("Expected 31 Task #013 independence relationships.")
    _, claims = read_csv(INPUTS["claim_registry"])
    if len(claims) != 148_030:
        fail("Expected 148,030 Task #014 claims.")
    _, dependencies = read_csv(INPUTS["dependency_graph"])
    if len(dependencies) != 77_202:
        fail("Expected 77,202 Task #014 dependency edges.")
    _, missingness_uncertainty = read_csv(INPUTS["missingness_uncertainty_registry"])
    if len(missingness_uncertainty) != 296_065:
        fail("Expected 296,065 Task #014 missingness/uncertainty rows.")
    status_values: dict[str, set[str]] = {"MISSINGNESS": set(), "UNCERTAINTY": set()}
    for row in missingness_uncertainty:
        if row["status_type"] not in status_values:
            fail(f"Unexpected Task #014 status type: {row['status_type']}")
        status_values[row["status_type"]].add(row["status_value"])
    if status_values["MISSINGNESS"] != set(TASK014_MISSINGNESS):
        fail("Task #014 missingness vocabulary changed.")
    if status_values["UNCERTAINTY"] != set(TASK014_UNCERTAINTY):
        fail("Task #014 uncertainty vocabulary changed.")
    _, source_lineage = read_csv(INPUTS["source_lineage"])
    _, source_entities = read_csv(INPUTS["source_entity_registry"])
    if len(source_lineage) != 6 or len(source_entities) != 6:
        fail("Expected six Task #013 and six Task #014 source entities.")

    return domains, boundary_map, {
        "domain_count": len(domains),
        "evidence_type_count": len(evidence_type_to_domain),
        "decision_context_count": len(contexts),
        "context_matrix_count": len(context_matrix),
        "interpretation_boundary_count": len(boundaries),
        "independence_relationship_count": len(independence),
        "claim_count": len(claims),
        "dependency_edge_count": len(dependencies),
        "missingness_uncertainty_row_count": len(missingness_uncertainty),
        "source_lineage_count": len(source_lineage),
        "source_entity_count": len(source_entities),
    }


def schema_rows() -> list[dict[str, str]]:
    fields = [
        "field_order",
        "field_name",
        "profile_scope",
        "data_type",
        "required",
        "allowed_values",
        "source_or_derivation",
        "definition",
        "interpretation_boundary",
    ]
    return [dict(zip(fields, (str(order), name, scope, dtype, required, allowed, source, definition, boundary))) for order, name, scope, dtype, required, allowed, source, definition, boundary in PROFILE_SCHEMA]


def component_rows(domains: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    ontology_types = {
        evidence_type
        for row in domains.values()
        for evidence_type in row["evidence_type"].split("|")
    }
    rows = []
    for component in COMPONENTS:
        domain_ids = component["domains"].split("|")
        evidence_types = component["types"].split("|")
        if not set(domain_ids).issubset(domains):
            fail(f"Unknown component domain: {component['component_id']}")
        if not set(evidence_types).issubset(ontology_types):
            fail(f"Unknown component evidence type: {component['component_id']}")
        for evidence_type in evidence_types:
            if not any(evidence_type in domains[domain_id]["evidence_type"].split("|") for domain_id in domain_ids):
                fail(f"Evidence type/domain mismatch in {component['component_id']}: {evidence_type}")
        rows.append(
            {
                "profile_section_id": component["section_id"],
                "profile_section": component["section"],
                "component_id": component["component_id"],
                "component_name": component["component"],
                "evidence_domains": component["domains"],
                "evidence_types": component["types"],
                "allowed_states": "|".join(ALLOWED_PROFILE_STATES),
                "decision_context": component["context"],
                "scientific_question": component["question"],
                "state_resolution_rule": component["criterion"],
                "required_provenance": component["provenance"],
                "dependency_boundary": component["dependency"],
                "missingness_boundary": "MISSING is absence after a defined assessment; NOT_QUERIED is no assessment. Neither is negative evidence.",
            }
        )
    return rows


def rule_rows() -> list[dict[str, str]]:
    fields = [
        "rule_id",
        "rule_category",
        "applies_to",
        "permitted_description",
        "prohibited_conclusion",
        "required_handling",
        "provenance_basis",
    ]
    provenance = "Task #013 ontology and independence map|Task #014 claims/records/dependencies|Task #018 hashes|Task #019 interpretation boundaries"
    return [
        dict(zip(fields, (rule_id, category, applies, permitted, prohibited, handling, provenance)))
        for rule_id, category, applies, permitted, prohibited, handling in INTERPRETATION_RULES
    ]


def validate_outputs(
    schema: list[dict[str, str]],
    components: list[dict[str, str]],
    rules: list[dict[str, str]],
    domains: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    checks = []

    def check(name: str, passed: bool, observed: object, expected: object, detail: str) -> None:
        checks.append({"check": name, "status": "PASS" if passed else "FAIL", "observed": str(observed), "expected": str(expected), "detail": detail})
        if not passed:
            fail(f"Output validation failed: {name}")

    sections = Counter(row["profile_section"] for row in components)
    all_ontology_types = {
        value for row in domains.values() for value in row["evidence_type"].split("|")
    }
    component_types = {
        value for row in components for value in row["evidence_types"].split("|")
    }
    all_fields = {row["field_name"] for row in schema}
    all_headers = set(schema[0]) | set(components[0]) | set(rules[0]) | all_fields
    forbidden = all_headers.intersection(FORBIDDEN_EXACT_FIELDS)

    check("schema_field_count", len(schema) == 28, len(schema), 28, "Long-form target-component schema.")
    check("schema_fields_unique", len(all_fields) == len(schema), len(all_fields), len(schema), "No duplicate profile fields.")
    check("component_count", len(components) == 11, len(components), 11, "Four biological, four development, and three translational components.")
    check("component_ids_unique", len({row["component_id"] for row in components}) == 11, len({row["component_id"] for row in components}), 11, "Stable component IDs.")
    check("section_structure", sections == Counter({"Biological Discovery Profile": 4, "Therapeutic Development Profile": 4, "Translational Profile": 3}), dict(sections), "4|4|3", "Prespecified profile sections.")
    check("allowed_states_exact", all(row["allowed_states"] == "|".join(ALLOWED_PROFILE_STATES) for row in components), "all exact", "OBSERVED|PARTIAL|MISSING|NOT_QUERIED|CONFLICTING", "Controlled component states.")
    check("ontology_types_covered", component_types == all_ontology_types, len(component_types), len(all_ontology_types), "Every ontology evidence type appears in at least one component.")
    check("interpretation_rule_count", len(rules) == 18 and len({row["rule_id"] for row in rules}) == 18, len(rules), 18, "State, capability, and boundary rules.")
    check("can_describe_covered", {"RULE_AVAILABILITY", "RULE_MATURITY", "RULE_UNCERTAINTY"}.issubset({row["rule_id"] for row in rules}), "3 capabilities", "3 capabilities", "Availability, maturity, and uncertainty are explicit.")
    check("cannot_establish_covered", {"RULE_NO_CAUSALITY", "RULE_NO_EFFICACY", "RULE_NO_SAFETY", "RULE_NO_CLINICAL_BENEFIT", "RULE_NO_TARGET_ORDERING"}.issubset({row["rule_id"] for row in rules}), "5 boundaries", "5 boundaries", "Required non-claims are explicit.")
    check("forbidden_fields_absent", not forbidden, sorted(forbidden), [], "No assessment or therapeutic-direction fields.")
    check("all_cells_nonblank", all(all(value != "" for value in row.values()) for table in (schema, components, rules) for row in table), "all nonblank", "all nonblank", "Provenance and interpretation fields are explicit.")
    return checks


def write_csv(path: Path, fields: list[str], rows: Iterable[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_summary(
    schema: list[dict[str, str]],
    components: list[dict[str, str]],
    rules: list[dict[str, str]],
    checks: list[dict[str, str]],
) -> None:
    sections = Counter(row["profile_section"] for row in components)
    lines = [
        "# Task #020 target evidence profile architecture summary",
        "",
        "**Profile records populated:** 0  ",
        f"**Profile schema fields:** {len(schema)}  ",
        f"**Profile components:** {len(components)}  ",
        f"**Interpretation rules:** {len(rules)}  ",
        f"**Validation checks passed:** {sum(row['status'] == 'PASS' for row in checks)}/{len(checks)}  ",
        "**Scores, rankings, selections, or therapeutic conclusions generated:** No",
        "",
        "## Architecture",
        "",
        "A future profile is a long-form collection of one row per immutable EnsemblID and component. It organizes bounded claims and evidence records while retaining source entities, artifact hashes, missingness, uncertainty, conflict, and dependency metadata. It does not combine components into a single assessment.",
        "",
        "| Profile section | Components |",
        "| --- | ---: |",
    ]
    for section in ("Biological Discovery Profile", "Therapeutic Development Profile", "Translational Profile"):
        lines.append(f"| {section} | {sections[section]} |")
    lines.extend(
        [
            "",
            "## Component states",
            "",
            "- `OBSERVED`: qualifying records exist with traceable provenance under the component rule.",
            "- `PARTIAL`: some evidence exists, but coverage, linkage, or provenance remains incomplete.",
            "- `MISSING`: a defined assessment found no qualifying record; this is not negative evidence.",
            "- `NOT_QUERIED`: the evidence class was not acquired or could not be queried.",
            "- `CONFLICTING`: materially incompatible records are retained under a prespecified comparison rule.",
            "",
            "These states describe evidence organization. They have no numerical order and do not encode favorable or unfavorable target properties.",
            "",
            "## Composite translational views",
            "",
            "Human evidence, clinical linkage, and risk context reuse existing ontology records. Reuse retains the same record IDs and dependencies; it does not create new observations. Clinical linkage requires record-level intervention–target–disease linkage and cannot be inferred from co-occurring counts.",
            "",
            "## What a profile can describe",
            "",
            "- evidence availability by component;",
            "- qualitative evidence maturity, meaning which components are sufficiently characterized for bounded interpretation; and",
            "- unresolved missingness, conflict, temporal, source, coverage, and dependency uncertainty.",
            "",
            "## What a profile cannot establish",
            "",
            "- biological or disease causality;",
            "- drug or modality efficacy;",
            "- safety or an acceptable therapeutic window;",
            "- clinical benefit, utility, approval, or benefit-risk; or",
            "- target ordering, selection, or therapeutic conclusions.",
            "",
            "Profile completeness is not target quality. Evidence-record quantity is not evidence quality. Dependent records are not independent votes. No completeness percentage, aggregation formula, or overall score is part of this architecture.",
            "",
            "## Validation",
            "",
            "All frozen Task #018 governance and Task #019 decision-context hashes matched. All 193 Task #018 governed artifacts retained their recorded hashes and sizes. The schema covers all eight ontology domains and all 17 evidence types, preserves the Task #014 missingness/uncertainty/dependency vocabularies, and introduces no gene-level profile data.",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate_postflight(start_head: str) -> None:
    if run_git("rev-parse", "HEAD") != start_head:
        fail("Git HEAD changed during Task #020.")
    if run_git("diff", "--name-only") or run_git("diff", "--cached", "--name-only"):
        fail("An existing tracked file changed during Task #020.")
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
        "task": "020",
        "purpose": "auditable target evidence profile architecture",
        "started_at_utc": started.isoformat(),
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "git_branch": git_info["branch"],
        "git_head_before": git_info["head"],
        "git_head_after": run_git("rev-parse", "HEAD"),
        "git_origin": git_info["remote"],
        "frozen_task019_base_commit": TASK019_BASE_COMMIT,
        "profile_records_populated": "0",
        "profile_schema_field_count": "28",
        "profile_component_count": "11",
        "profile_interpretation_rule_count": "18",
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
    }
    for name, value in input_counts.items():
        values[f"input_validation.{name}"] = str(value)
    for name, digest in hashes.items():
        values[f"frozen_input_sha256.{relative(INPUTS[name])}"] = digest
    for row in checks:
        values[f"output_validation.{row['check']}"] = row["status"]
    for path in (SCHEMA_PATH, COMPONENT_PATH, RULES_PATH, SUMMARY_PATH):
        values[f"output_sha256.{relative(path)}"] = sha256(path)
    SESSION_PATH.write_text(
        "".join(f"{key}={values[key]}\n" for key in sorted(values)), encoding="utf-8"
    )


def main() -> None:
    started = datetime.now(timezone.utc)
    git_info = validate_repository()
    hashes = validate_hashes()
    artifact_count, class_d_count = validate_governance()
    domains, _, counts = validate_architecture()
    counts["task018_artifact_count"] = artifact_count
    counts["task018_class_d_count"] = class_d_count

    schema = schema_rows()
    components = component_rows(domains)
    rules = rule_rows()
    checks = validate_outputs(schema, components, rules, domains)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    allowed = {SCHEMA_PATH.name, COMPONENT_PATH.name, RULES_PATH.name, SUMMARY_PATH.name, SESSION_PATH.name}
    unexpected = {path.name for path in OUTPUT_DIR.iterdir() if path.name not in allowed}
    if unexpected:
        fail(f"Unexpected Task #020 output files: {sorted(unexpected)}")

    write_csv(SCHEMA_PATH, list(schema[0]), schema)
    write_csv(COMPONENT_PATH, list(components[0]), components)
    write_csv(RULES_PATH, list(rules[0]), rules)
    write_summary(schema, components, rules, checks)
    validate_postflight(git_info["head"])
    write_session(started, git_info, hashes, counts, checks)

    print("Created files:")
    for path in (SCHEMA_PATH, COMPONENT_PATH, RULES_PATH, SUMMARY_PATH, SESSION_PATH):
        print(f"- {relative(path)}")
    print(f"Profile schema fields: {len(schema)}")
    print(f"Profile components: {len(components)}")
    print(f"Interpretation rules: {len(rules)}")
    print(f"Validation checks passed: {sum(row['status'] == 'PASS' for row in checks)}/{len(checks)}")
    print("No target profiles or therapeutic assessments were generated.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
