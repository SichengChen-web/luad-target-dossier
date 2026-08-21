#!/usr/bin/env python3
"""Build the Task #013 evidence ontology and independence framework."""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK012_BASE_COMMIT = "50a7be68cf8cbb6cd59aae3d3deac4120d27c553"
EXPECTED_ROWS = 29_606
EXPECTED_U2 = 14_064

INTEGRATED_REGISTRY = Path(
    "outputs/integrated_registry/integrated_target_registry.csv"
)
EVIDENCE_PLAN = Path("docs/evidence_layer_plan_v0.1.md")
TRACTABILITY_SAFETY_PLAN = Path("docs/tractability_safety_plan_v0.1.md")
INTEGRATED_PLAN = Path("docs/integrated_registry_plan_v0.1.md")
FROZEN_HASHES = {
    INTEGRATED_REGISTRY: "0587fc6901267b18c8144644571f89ac2cc46053b57ea5def4093795fdbc4c26",
    EVIDENCE_PLAN: "6e72e4932f02d939498269387ff2e3904ff3ad409440a29f7f3bf7f87d99359c",
    TRACTABILITY_SAFETY_PLAN: "b05c85c310b80cd539be545e160364ed3b630639416b017001248011dc7d7090",
    INTEGRATED_PLAN: "71c759a0699a76070a369ce28c79456ddfc33064f901586a646e59a9649200d0",
}

SCRIPT = Path("analysis/13_build_evidence_ontology.py")
PLAN = Path("docs/evidence_ontology_plan_v0.1.md")
OUTPUT_DIR = Path("outputs/evidence_ontology")
DOMAIN_REGISTRY = OUTPUT_DIR / "evidence_domain_registry.csv"
SOURCE_LINEAGE = OUTPUT_DIR / "evidence_source_lineage.csv"
INDEPENDENCE_MAP = OUTPUT_DIR / "evidence_independence_map.csv"
SUMMARY = OUTPUT_DIR / "evidence_ontology_summary.md"
SESSION = OUTPUT_DIR / "session_info.txt"

DOMAIN_COLUMNS = [
    "domain_id",
    "domain_name",
    "description",
    "scientific_question",
    "example_sources",
    "evidence_type",
    "future_role",
    "independence_notes",
]
SOURCE_COLUMNS = [
    "source_id",
    "source_name",
    "provider",
    "data_type",
    "domains_supported",
    "known_dependencies",
    "version_tracking_required",
    "notes",
]
INDEPENDENCE_COLUMNS = [
    "evidence_pair",
    "relationship",
    "dependency_level",
    "reason",
    "future_aggregation_warning",
]

ALLOWED_RELATIONSHIPS = {
    "INDEPENDENT",
    "PARTIALLY_DEPENDENT",
    "DERIVED_FROM_SAME_SOURCE",
    "UNKNOWN",
}
ALLOWED_DEPENDENCY_LEVELS = {
    "NONE_IDENTIFIED",
    "PARTIAL",
    "HIGH",
    "UNRESOLVED",
}
FORBIDDEN_EXACT_COLUMNS = {
    "score",
    "ranking",
    "priority",
    "rank",
    "recommendation",
    "therapeutic_direction",
    "target_selection",
}
ALLOWED_UNTRACKED = {str(SCRIPT), str(PLAN)}
ALLOWED_OUTPUT_PREFIX = f"{OUTPUT_DIR}/"


def fail(message: str) -> None:
    raise RuntimeError(message)


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(["git", *args], text=True, capture_output=True, check=False)
    if check and result.returncode != 0:
        fail(
            f"Git command failed: git {' '.join(args)}\n"
            f"stdout: {result.stdout.strip()}\n"
            f"stderr: {result.stderr.strip()}"
        )
    return result.stdout.strip()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_repository() -> dict[str, str]:
    root = Path(git("rev-parse", "--show-toplevel")).resolve()
    if root != Path.cwd().resolve():
        fail(f"Run from repository root {root}; observed {Path.cwd().resolve()}")
    branch = git("branch", "--show-current")
    if branch != "main":
        fail(f"Task #013 requires branch main; observed {branch!r}")
    head = git("rev-parse", "HEAD")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", TASK012_BASE_COMMIT, head],
        capture_output=True,
        text=True,
        check=False,
    )
    if ancestor.returncode != 0:
        fail(
            f"Frozen Task #012 base {TASK012_BASE_COMMIT} is not an ancestor of HEAD {head}"
        )
    remote = git("remote", "get-url", "origin")
    if not re.search(
        r"(?:github\.com[:/])SichengChen-web/luad-target-dossier(?:\.git)?$",
        remote,
    ):
        fail(f"Unexpected origin remote: {remote}")
    if subprocess.run(["git", "diff", "--quiet"], check=False).returncode != 0:
        fail("A previously committed file has an unstaged modification")
    if subprocess.run(
        ["git", "diff", "--cached", "--quiet"], check=False
    ).returncode != 0:
        fail("A previously committed file has a staged modification")
    untracked = git("ls-files", "--others", "--exclude-standard").splitlines()
    unexpected = [
        path
        for path in untracked
        if path not in ALLOWED_UNTRACKED and not path.startswith(ALLOWED_OUTPUT_PREFIX)
    ]
    if unexpected:
        fail("Unexpected untracked files are present: " + ", ".join(unexpected))

    for path, expected_hash in FROZEN_HASHES.items():
        if not path.is_file():
            fail(f"Required frozen file is missing: {path}")
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", str(path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if tracked.returncode != 0:
            fail(f"Required frozen file is not committed: {path}")
        unchanged = subprocess.run(
            ["git", "diff", "--quiet", TASK012_BASE_COMMIT, "--", str(path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if unchanged.returncode != 0:
            fail(f"Frozen file differs from Task #012 base: {path}")
        observed_hash = file_sha256(path)
        if observed_hash != expected_hash:
            fail(
                f"SHA256 mismatch for {path}: {observed_hash} != {expected_hash}"
            )
    return {
        "root": str(root),
        "branch": branch,
        "head": head,
        "remote": remote,
    }


def validate_integrated_registry() -> dict[str, Any]:
    required = {
        "EnsemblID",
        "U2_effect_supported_DE",
        "logFC_S0",
        "FDR_S0",
        "sign_concordant_all_S1_S6",
        "ot_luad_direct_association_status",
        "ot_luad_direct_association_score_native",
        "ot_literature_occurrence_count",
        "ot_drug_clinical_candidate_record_count",
        "chembl_target_retrieval_status",
        "tractability_retrieval_status",
        "safety_retrieval_status",
        "integrated_missingness_status_json",
    }
    row_count = 0
    u2_count = 0
    identifiers: set[str] = set()
    with INTEGRATED_REGISTRY.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            fail("Integrated registry has no header")
        missing = required.difference(reader.fieldnames)
        if missing:
            fail(f"Integrated registry lacks required evidence fields: {sorted(missing)}")
        for row in reader:
            row_count += 1
            ensembl_id = row["EnsemblID"]
            if not ensembl_id or ensembl_id in identifiers:
                fail(f"Empty or duplicate EnsemblID in integrated registry: {ensembl_id!r}")
            identifiers.add(ensembl_id)
            if row["U2_effect_supported_DE"] == "TRUE":
                u2_count += 1
            elif row["U2_effect_supported_DE"] != "FALSE":
                fail(f"Invalid U2 state at {ensembl_id}")
            try:
                missingness = json.loads(row["integrated_missingness_status_json"])
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"Invalid integrated missingness JSON at {ensembl_id}"
                ) from exc
            if not isinstance(missingness, dict):
                fail(f"Integrated missingness value is not an object at {ensembl_id}")
    if row_count != EXPECTED_ROWS or len(identifiers) != EXPECTED_ROWS:
        fail(
            f"Integrated registry identity assertion failed: rows={row_count}, "
            f"unique={len(identifiers)}, expected={EXPECTED_ROWS}"
        )
    if u2_count != EXPECTED_U2:
        fail(f"Integrated registry has {u2_count} U2 genes; expected {EXPECTED_U2}")
    return {
        "row_count": row_count,
        "unique_ensembl_id_count": len(identifiers),
        "u2_count": u2_count,
    }


def build_domains() -> list[dict[str, str]]:
    return [
        {
            "domain_id": "DOM_TRANSCRIPTOMIC_DISCOVERY",
            "domain_name": "Transcriptomic discovery",
            "description": "Tumour-versus-normal RNA-seq discovery evidence and prespecified model-sensitivity diagnostics.",
            "scientific_question": "Is the gene reproducibly and substantially dysregulated in LUAD tumour tissue relative to normal tissue?",
            "example_sources": "TCGA-LUAD|recount3|project DE analyses S0-S6",
            "evidence_type": "EV_TCGA_DE_EFFECT|EV_TCGA_DE_SIGNIFICANCE|EV_TCGA_DE_ROBUSTNESS",
            "future_role": "Candidate-generation and expression-robustness domain; it must not be treated as causal or therapeutic evidence.",
            "independence_notes": "logFC, FDR, and S1-S6 stability are derived from the same expression cohort and related models; they are not independent votes.",
        },
        {
            "domain_id": "DOM_DISEASE_ASSOCIATION",
            "domain_name": "Disease association",
            "description": "Source-native evidence connecting a target to LUAD or its disease-ontology context.",
            "scientific_question": "Is the target associated with LUAD, and what source-derived evidence supports that association?",
            "example_sources": "Open Targets Platform",
            "evidence_type": "EV_OT_LUAD_DIRECT_ASSOCIATION|EV_OT_LUAD_INDIRECT_ASSOCIATION|EV_OT_LITERATURE_COUNT",
            "future_role": "Disease-relevance domain retaining direct and ontology-expanded views without treating them as independent.",
            "independence_notes": "Open Targets fields share a platform release and may share upstream literature, genetics, clinical, or other evidence records.",
        },
        {
            "domain_id": "DOM_GENETIC_EVIDENCE",
            "domain_name": "Genetic evidence",
            "description": "Future-compatible somatic, germline, or other genetic evidence linking a target to cancer biology.",
            "scientific_question": "Do inherited or tumour-acquired genetic alterations support a causal role for the target in LUAD biology?",
            "example_sources": "future cancer-genetics sources|future germline-association sources",
            "evidence_type": "EV_GENETIC_CANCER",
            "future_role": "Future causal/mechanistic domain; no dedicated Task #012 genetic feature is currently asserted.",
            "independence_notes": "Independence will depend on cohort and source lineage; TCGA-derived mutation and TCGA expression evidence may share samples.",
        },
        {
            "domain_id": "DOM_FUNCTIONAL_DEPENDENCY",
            "domain_name": "Functional dependency",
            "description": "Future-compatible perturbational evidence that target loss or modulation changes cancer-cell fitness or disease-relevant function.",
            "scientific_question": "Does experimental perturbation of the target alter LUAD-relevant cellular fitness or function?",
            "example_sources": "future CRISPR dependency datasets|future perturbational assays",
            "evidence_type": "EV_FUNCTIONAL_CRISPR_DEPENDENCY",
            "future_role": "Future causal/functional domain; no dedicated Task #012 dependency feature is currently asserted.",
            "independence_notes": "A separately generated perturbation dataset may be source-independent from TCGA expression, but shared cell-line or lineage context can still induce biological correlation.",
        },
        {
            "domain_id": "DOM_PHARMACOLOGY",
            "domain_name": "Pharmacology",
            "description": "Target annotations and future compound-target, activity, potency, and mechanism evidence.",
            "scientific_question": "Is there source-grounded pharmacological evidence that compounds interact with or modulate the target?",
            "example_sources": "ChEMBL|Open Targets drug and clinical candidate records|future pharmacology sources",
            "evidence_type": "EV_CHEMBL_TARGET_ANNOTATION|EV_OT_DRUG_CANDIDATE_COUNT|EV_CHEMBL_COMPOUND_TARGET",
            "future_role": "Current target-availability metadata plus future compound-level pharmacology; current Task #010 ChEMBL fields do not establish activity or mechanism.",
            "independence_notes": "Open Targets drug/candidate and tractability evidence may incorporate ChEMBL or clinical precedence, so records cannot automatically be counted independently.",
        },
        {
            "domain_id": "DOM_TRACTABILITY",
            "domain_name": "Tractability",
            "description": "Source-native assessments of whether a target may be addressable by specific therapeutic modalities.",
            "scientific_question": "What source-derived evidence indicates that the target can be modulated by a small molecule, antibody, PROTAC, or other clinical modality?",
            "example_sources": "Open Targets Platform",
            "evidence_type": "EV_OT_TRACTABILITY_SM|EV_OT_TRACTABILITY_AB|EV_OT_TRACTABILITY_PR|EV_OT_TRACTABILITY_OC",
            "future_role": "Modality-specific feasibility domain; positive assessment counts remain descriptive and are not a tractability score.",
            "independence_notes": "Assessment buckets and modalities share the Open Targets tractability framework and can reuse ChEMBL or clinical-precedence evidence.",
        },
        {
            "domain_id": "DOM_CLINICAL_DEVELOPMENT",
            "domain_name": "Clinical development",
            "description": "Future-compatible evidence of human investigation, development phase, intervention, and trial status.",
            "scientific_question": "Has target modulation or a closely related therapeutic strategy reached relevant human clinical investigation?",
            "example_sources": "future ClinicalTrials.gov retrieval|future curated development sources",
            "evidence_type": "EV_CLINICAL_TRIAL_DEVELOPMENT",
            "future_role": "Future translational-maturity domain; Task #012 has no dedicated trial-level evidence.",
            "independence_notes": "Future trial evidence may overlap Open Targets drug/candidate counts and tractability clinical-precedence assessments.",
        },
        {
            "domain_id": "DOM_SAFETY",
            "domain_name": "Safety",
            "description": "Curated/source-derived target safety-liability observations and future safety evidence.",
            "scientific_question": "What source-grounded observations indicate possible on-target or target-related safety liabilities, in what context, and from which evidence lineage?",
            "example_sources": "Open Targets safety liabilities|future openFDA evidence|future safety literature",
            "evidence_type": "EV_OT_SAFETY_LIABILITY",
            "future_role": "Structured liability and uncertainty domain; absence of a returned record is not evidence of safety.",
            "independence_notes": "Multiple records can share a datasource, study, publication, event, or target mechanism and must not automatically be treated as independent.",
        },
    ]


def build_sources() -> list[dict[str, str]]:
    return [
        {
            "source_id": "SRC_TCGA_LUAD",
            "source_name": "TCGA Lung Adenocarcinoma RNA-seq",
            "provider": "NCI Genomic Data Commons / The Cancer Genome Atlas",
            "data_type": "bulk tumour and adjacent-normal RNA sequencing plus biospecimen metadata",
            "domains_supported": "DOM_TRANSCRIPTOMIC_DISCOVERY",
            "known_dependencies": "primary biological dataset underlying the recount3 TCGA-LUAD project used here",
            "version_tracking_required": "YES",
            "notes": "Tumour/normal imbalance, shared cases, technical replication, FFPE provenance, and batch/TSS structure are documented upstream.",
        },
        {
            "source_id": "SRC_RECOUNT3_TCGA_LUAD",
            "source_name": "recount3 TCGA-LUAD gencode_v26 representation",
            "provider": "recount3 project",
            "data_type": "uniformly processed RNA-seq expression object and harmonized metadata",
            "domains_supported": "DOM_TRANSCRIPTOMIC_DISCOVERY",
            "known_dependencies": "derived from SRC_TCGA_LUAD; depends on recount3 processing semantics and pinned gencode_v26 annotation",
            "version_tracking_required": "YES",
            "notes": "This is a delivery/processing layer for TCGA expression, not an independent biological cohort.",
        },
        {
            "source_id": "SRC_PROJECT_DE_ROBUSTNESS",
            "source_name": "Project primary DE and prespecified S1-S6 sensitivity analyses",
            "provider": "LUAD target-dossier project Tasks #006-#008",
            "data_type": "derived differential-expression statistics and robustness diagnostics",
            "domains_supported": "DOM_TRANSCRIPTOMIC_DISCOVERY",
            "known_dependencies": "derived from SRC_RECOUNT3_TCGA_LUAD and the same frozen final cohort; S0-S6 are related model views",
            "version_tracking_required": "YES",
            "notes": "Primary and sensitivity models provide robustness characterization, not multiple independent datasets.",
        },
        {
            "source_id": "SRC_OPEN_TARGETS_PLATFORM",
            "source_name": "Open Targets Platform",
            "provider": "Open Targets",
            "data_type": "integrated target-disease associations, literature counts, drug/candidate records, tractability assessments, and safety liabilities",
            "domains_supported": "DOM_DISEASE_ASSOCIATION|DOM_PHARMACOLOGY|DOM_TRACTABILITY|DOM_SAFETY",
            "known_dependencies": "multi-source aggregator; may incorporate literature, genetics, ChEMBL, clinical precedence, and curated safety datasources",
            "version_tracking_required": "YES",
            "notes": "Task #010 and Task #011 use the same Platform data release 26.06/API 26.6.3; different fields are not automatically independent evidence.",
        },
        {
            "source_id": "SRC_CHEMBL",
            "source_name": "ChEMBL",
            "provider": "EMBL-EBI",
            "data_type": "curated target annotations and future compound-target pharmacology",
            "domains_supported": "DOM_PHARMACOLOGY|DOM_TRACTABILITY",
            "known_dependencies": "Task #010 stores target availability only; Open Targets tractability and drug records may reuse ChEMBL-derived information",
            "version_tracking_required": "YES",
            "notes": "Current ChEMBL target presence is not compound activity, potency, mechanism, or clinical actionability evidence.",
        },
        {
            "source_id": "SRC_PROJECT_INTEGRATED_REGISTRY",
            "source_name": "Task #012 integrated target evidence registry",
            "provider": "LUAD target-dossier project",
            "data_type": "one-gene-per-row frozen evidence integration",
            "domains_supported": "DOM_TRANSCRIPTOMIC_DISCOVERY|DOM_DISEASE_ASSOCIATION|DOM_PHARMACOLOGY|DOM_TRACTABILITY|DOM_SAFETY",
            "known_dependencies": "derived from Tasks #008-#011; contains no new independent scientific observation",
            "version_tracking_required": "YES",
            "notes": "Integration improves auditability but does not increase evidence independence or confidence by itself.",
        },
    ]


def relationship(
    left: str,
    right: str,
    category: str,
    level: str,
    reason: str,
    warning: str,
) -> dict[str, str]:
    return {
        "evidence_pair": f"{left} vs {right}",
        "relationship": category,
        "dependency_level": level,
        "reason": reason,
        "future_aggregation_warning": warning,
    }


def build_independence_map() -> list[dict[str, str]]:
    r = relationship
    return [
        r("EV_TCGA_DE_EFFECT", "EV_TCGA_DE_SIGNIFICANCE", "DERIVED_FROM_SAME_SOURCE", "HIGH", "Effect estimates and significance statistics are calculated from the same expression contrast and samples.", "Treat as complementary fields within one transcriptomic observation, not two votes."),
        r("EV_TCGA_DE_EFFECT", "EV_TCGA_DE_ROBUSTNESS", "DERIVED_FROM_SAME_SOURCE", "HIGH", "S1-S6 robustness statistics reanalyse the same frozen expression data under related model specifications.", "Use robustness to qualify the expression result, not to multiply transcriptomic support."),
        r("EV_TCGA_DE_SIGNIFICANCE", "EV_TCGA_DE_ROBUSTNESS", "DERIVED_FROM_SAME_SOURCE", "HIGH", "Primary FDR and sensitivity FDR values share samples, counts, preprocessing, and related contrasts.", "Do not count each sensitivity model as independent replication."),
        r("EV_TCGA_DE_EFFECT", "EV_OT_LUAD_DIRECT_ASSOCIATION", "PARTIALLY_DEPENDENT", "PARTIAL", "The sources are distinct, but Open Targets disease evidence can incorporate literature or external datasets discussing tumour expression and LUAD biology.", "Count cross-domain convergence only after checking the Open Targets datasource lineage."),
        r("EV_OT_LUAD_DIRECT_ASSOCIATION", "EV_OT_LUAD_INDIRECT_ASSOCIATION", "DERIVED_FROM_SAME_SOURCE", "HIGH", "Both views come from the same Open Targets association framework; the indirect view expands through disease-ontology descendants and contains overlapping evidence.", "Never aggregate direct and indirect association values as independent disease evidence."),
        r("EV_OT_LUAD_DIRECT_ASSOCIATION", "EV_OT_LITERATURE_COUNT", "PARTIALLY_DEPENDENT", "PARTIAL", "Open Targets association evidence and bibliography counts share the same platform and may refer to overlapping publications.", "Literature volume must not be added as an independent validation of an association without record-level lineage."),
        r("EV_OT_LUAD_INDIRECT_ASSOCIATION", "EV_OT_LITERATURE_COUNT", "PARTIALLY_DEPENDENT", "PARTIAL", "Ontology-expanded associations and target bibliography counts may reuse overlapping literature and platform records.", "Do not interpret both as independent disease-support observations."),
        r("EV_OT_LUAD_DIRECT_ASSOCIATION", "EV_OT_DRUG_CANDIDATE_COUNT", "DERIVED_FROM_SAME_SOURCE", "HIGH", "Both fields are delivered by the same Open Targets release and target/disease data model, even if upstream records differ.", "Retain as distinct questions within different domains but do not infer source independence from separate columns."),
        r("EV_OT_DRUG_CANDIDATE_COUNT", "EV_CHEMBL_TARGET_ANNOTATION", "PARTIALLY_DEPENDENT", "PARTIAL", "Open Targets drug/candidate information may use ChEMBL-derived target and drug records; Task #010 ChEMBL availability is also identifier-linked metadata.", "Do not count platform drug records plus ChEMBL target presence as two independent pharmacology findings."),
        r("EV_CHEMBL_COMPOUND_TARGET", "EV_OT_DRUG_CANDIDATE_COUNT", "PARTIALLY_DEPENDENT", "PARTIAL", "Future ChEMBL compound-target records may be upstream of or overlap Open Targets drug/candidate records.", "Perform compound, mechanism, and provenance deduplication before future aggregation."),
        r("EV_CHEMBL_COMPOUND_TARGET", "EV_OT_TRACTABILITY_SM", "PARTIALLY_DEPENDENT", "PARTIAL", "Open Targets small-molecule tractability may use ligandability and ChEMBL pharmacology evidence.", "Do not treat the same compound/target record as independent pharmacology and tractability support."),
        r("EV_OT_DRUG_CANDIDATE_COUNT", "EV_OT_TRACTABILITY_SM", "PARTIALLY_DEPENDENT", "PARTIAL", "Small-molecule tractability includes clinical-precedence or pharmacological buckets that may overlap platform drug/candidate records.", "Aggregate at domain level only after identifying shared clinical or ChEMBL lineage."),
        r("EV_OT_DRUG_CANDIDATE_COUNT", "EV_OT_TRACTABILITY_AB", "PARTIALLY_DEPENDENT", "PARTIAL", "Antibody tractability can include clinical-precedence evidence represented among platform drug/candidate records.", "Do not double-count the same biologic development precedent."),
        r("EV_OT_DRUG_CANDIDATE_COUNT", "EV_OT_TRACTABILITY_PR", "PARTIALLY_DEPENDENT", "PARTIAL", "PROTAC tractability and platform candidate records may share target-development precedent.", "Require source-record lineage before treating these as separate support."),
        r("EV_OT_DRUG_CANDIDATE_COUNT", "EV_OT_TRACTABILITY_OC", "PARTIALLY_DEPENDENT", "PARTIAL", "Other-clinical-modality tractability is explicitly related to clinical precedent and may overlap platform candidate records.", "Do not count clinical precedence twice."),
        r("EV_OT_TRACTABILITY_AB", "EV_OT_TRACTABILITY_SM", "DERIVED_FROM_SAME_SOURCE", "HIGH", "Both modality assessments are emitted by the same Open Targets tractability framework and target record.", "Modality buckets answer different feasibility questions but are not independent datasets."),
        r("EV_OT_TRACTABILITY_PR", "EV_OT_TRACTABILITY_SM", "DERIVED_FROM_SAME_SOURCE", "HIGH", "Both modality assessments are emitted by the same Open Targets tractability framework and can share underlying target properties.", "Do not use the number of positive modalities as a project confidence score."),
        r("EV_OT_TRACTABILITY_OC", "EV_OT_TRACTABILITY_SM", "DERIVED_FROM_SAME_SOURCE", "HIGH", "Both assessments come from the same source-native tractability object.", "Keep modality-specific evidence descriptive rather than additive."),
        r("EV_OT_TRACTABILITY_AB", "EV_OT_TRACTABILITY_PR", "DERIVED_FROM_SAME_SOURCE", "HIGH", "Both assessments come from the same target-level Open Targets tractability framework.", "Do not count source buckets as independent validations."),
        r("EV_OT_TRACTABILITY_AB", "EV_OT_TRACTABILITY_OC", "DERIVED_FROM_SAME_SOURCE", "HIGH", "Both assessments come from the same target-level Open Targets tractability framework.", "Do not count source buckets as independent validations."),
        r("EV_OT_TRACTABILITY_PR", "EV_OT_TRACTABILITY_OC", "DERIVED_FROM_SAME_SOURCE", "HIGH", "Both assessments come from the same target-level Open Targets tractability framework.", "Do not count source buckets as independent validations."),
        r("EV_OT_SAFETY_LIABILITY", "EV_TCGA_DE_EFFECT", "INDEPENDENT", "NONE_IDENTIFIED", "Open Targets curated safety-liability observations and TCGA tumour/normal expression are generated from different evidence processes and address different questions.", "Independence of source lineage does not imply that either domain is sufficient or that absence of safety records means safety."),
        r("EV_OT_SAFETY_LIABILITY", "EV_OT_LUAD_DIRECT_ASSOCIATION", "PARTIALLY_DEPENDENT", "PARTIAL", "The evidence types address different questions but are delivered through the same Open Targets release and may share literature or target annotations.", "Check record-level datasource and publication overlap before claiming independent convergence."),
        r("EV_OT_SAFETY_LIABILITY", "EV_OT_TRACTABILITY_SM", "PARTIALLY_DEPENDENT", "PARTIAL", "Safety and tractability are distinct assessment blocks but share the Open Targets target object and may reference overlapping pharmacology or literature.", "Keep safety and tractability separate and avoid source-count inflation."),
        r("EV_GENETIC_CANCER", "EV_TCGA_DE_EFFECT", "UNKNOWN", "UNRESOLVED", "Future genetic evidence could come from the same TCGA cases or from an independent cohort; the source has not yet been selected.", "Set the relationship only after cohort/sample lineage is known."),
        r("EV_FUNCTIONAL_CRISPR_DEPENDENCY", "EV_TCGA_DE_EFFECT", "INDEPENDENT", "NONE_IDENTIFIED", "A separately generated perturbational dependency experiment would use a distinct measurement process from bulk TCGA expression.", "Confirm dataset and sample independence; biological lineage correlation is still possible."),
        r("EV_CLINICAL_TRIAL_DEVELOPMENT", "EV_OT_DRUG_CANDIDATE_COUNT", "PARTIALLY_DEPENDENT", "PARTIAL", "Future trial records are likely to overlap drugs and development records already counted by Open Targets.", "Deduplicate interventions, trial identifiers, targets, and development events before aggregation."),
        r("EV_CLINICAL_TRIAL_DEVELOPMENT", "EV_OT_TRACTABILITY_SM", "PARTIALLY_DEPENDENT", "PARTIAL", "Open Targets tractability can include clinical precedence that future trial evidence would directly represent.", "Clinical precedence should contribute once at the clinical-development/tractability boundary."),
        r("EV_GENETIC_CANCER", "EV_OT_LUAD_DIRECT_ASSOCIATION", "PARTIALLY_DEPENDENT", "PARTIAL", "Open Targets disease association can include genetic evidence, so future cancer-genetics records may already contribute upstream.", "Inspect Open Targets datasource scores and genetic record identifiers before treating genetics as new evidence."),
        r("EV_FUNCTIONAL_CRISPR_DEPENDENCY", "EV_OT_LUAD_DIRECT_ASSOCIATION", "UNKNOWN", "UNRESOLVED", "Open Targets association inputs may or may not include the future functional dataset selected by this project.", "Resolve datasource and dataset lineage before aggregation."),
        r("EV_CHEMBL_TARGET_ANNOTATION", "EV_CHEMBL_COMPOUND_TARGET", "DERIVED_FROM_SAME_SOURCE", "HIGH", "Target annotations and future compound-target records are linked within the same ChEMBL release and identifier model.", "Target availability is metadata, not an additional independent pharmacology observation."),
    ]


def validate_table(
    name: str,
    rows: list[dict[str, str]],
    required_columns: list[str],
    id_column: str | None = None,
) -> None:
    if not rows:
        fail(f"{name} is empty")
    if any(list(row) != required_columns for row in rows):
        fail(f"{name} does not contain exactly the required columns in order")
    if any(value == "" for row in rows for value in row.values()):
        fail(f"{name} contains a blank value")
    if id_column is not None:
        values = [row[id_column] for row in rows]
        if len(values) != len(set(values)):
            fail(f"{name} contains duplicate {id_column} values")
    forbidden = FORBIDDEN_EXACT_COLUMNS.intersection(
        column.lower() for column in required_columns
    )
    if forbidden:
        fail(f"{name} contains forbidden columns: {sorted(forbidden)}")


def validate_ontology(
    domains: list[dict[str, str]],
    sources: list[dict[str, str]],
    relationships: list[dict[str, str]],
) -> dict[str, Any]:
    validate_table("Evidence domain registry", domains, DOMAIN_COLUMNS, "domain_id")
    validate_table("Evidence source lineage", sources, SOURCE_COLUMNS, "source_id")
    validate_table("Evidence independence map", relationships, INDEPENDENCE_COLUMNS)

    required_domain_names = {
        "Transcriptomic discovery",
        "Disease association",
        "Genetic evidence",
        "Functional dependency",
        "Pharmacology",
        "Tractability",
        "Clinical development",
        "Safety",
    }
    if {row["domain_name"] for row in domains} != required_domain_names:
        fail("Evidence domain registry does not exactly cover the required vocabulary")
    if any(not row["scientific_question"].endswith("?") for row in domains):
        fail("Every evidence domain must contain an explicit scientific question")

    domain_ids = {row["domain_id"] for row in domains}
    for source in sources:
        supported = set(source["domains_supported"].split("|"))
        if not supported or not supported.issubset(domain_ids):
            fail(
                f"Source {source['source_id']} references unknown domains: "
                f"{sorted(supported.difference(domain_ids))}"
            )
        if source["version_tracking_required"] not in {"YES", "NO"}:
            fail(f"Invalid version-tracking state for {source['source_id']}")

    evidence_types = {
        value
        for domain in domains
        for value in domain["evidence_type"].split("|")
    }
    seen_pairs: set[frozenset[str]] = set()
    for row in relationships:
        if row["relationship"] not in ALLOWED_RELATIONSHIPS:
            fail(f"Disallowed relationship category: {row['relationship']}")
        if row["dependency_level"] not in ALLOWED_DEPENDENCY_LEVELS:
            fail(f"Disallowed dependency level: {row['dependency_level']}")
        parts = row["evidence_pair"].split(" vs ")
        if len(parts) != 2 or parts[0] == parts[1]:
            fail(f"Malformed evidence pair: {row['evidence_pair']}")
        if not set(parts).issubset(evidence_types):
            fail(
                f"Evidence pair references undefined types: {row['evidence_pair']}"
            )
        canonical = frozenset(parts)
        if canonical in seen_pairs:
            fail(f"Duplicate unordered evidence pair: {row['evidence_pair']}")
        seen_pairs.add(canonical)

    return {
        "domain_count": len(domains),
        "source_count": len(sources),
        "relationship_count": len(relationships),
        "relationship_category_counts": dict(
            sorted(Counter(row["relationship"] for row in relationships).items())
        ),
        "all_required_columns_present": True,
        "all_relationship_categories_allowed": True,
        "score_fields_created": False,
        "ranking_fields_created": False,
        "target_prioritization_generated": False,
    }


def write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    output = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    output.extend(
        "| "
        + " | ".join(str(value).replace("|", "\\|") for value in row)
        + " |"
        for row in rows
    )
    return output


def write_summary(
    domains: list[dict[str, str]],
    sources: list[dict[str, str]],
    relationships: list[dict[str, str]],
    validation: dict[str, Any],
) -> None:
    category_counts = validation["relationship_category_counts"]
    lines = [
        "# Task #013 evidence ontology and independence summary",
        "",
        f"**Evidence domains:** {len(domains)}  ",
        f"**Source-lineage records:** {len(sources)}  ",
        f"**Evidence dependency relationships:** {len(relationships)}  ",
        "**Scoring or ranking created:** No",
        "",
        "## Controlled evidence domains",
        "",
    ]
    lines.extend(
        markdown_table(
            ["Domain ID", "Domain", "Scientific question"],
            [
                [row["domain_id"], row["domain_name"], row["scientific_question"]]
                for row in domains
            ],
        )
    )
    lines.extend(["", "## Source lineage", ""])
    lines.extend(
        markdown_table(
            ["Source ID", "Source", "Domains"],
            [
                [row["source_id"], row["source_name"], row["domains_supported"]]
                for row in sources
            ],
        )
    )
    lines.extend(["", "## Dependency categories", ""])
    lines.extend(
        markdown_table(
            ["Relationship", "Count"],
            [[category, category_counts.get(category, 0)] for category in sorted(ALLOWED_RELATIONSHIPS)],
        )
    )
    lines.extend(
        [
            "",
            "The map uses qualitative categories only. It creates no numerical independence penalty, correlation coefficient, weight, score, or rank.",
            "",
            "## Central aggregation rules",
            "",
            "- Multiple fields derived from the same cohort or source object are not independent votes. In particular, S0-S6 models are robustness views of the same expression data; Open Targets direct/indirect associations overlap; and tractability buckets share one framework.",
            "- Evidence counts measure retrieved records or source-native summaries, not confidence. Several records can share a datasource, study, publication, compound, trial, or upstream database.",
            "- Future aggregation must operate at the evidence-domain level. Within-domain features first describe and qualify that domain; convergence across domains is considered only after source lineage and pairwise dependencies are reviewed.",
            "- Missing evidence remains missing. Absence of a returned association, tractability, pharmacology, or safety record is not converted into negative biological evidence.",
            "- An `INDEPENDENT` label means no source-lineage dependency was identified for the stated evidence pair under the stated assumptions. It does not mean statistical independence, biological sufficiency, or certainty.",
            "",
            "## Important current warnings",
            "",
            "- TCGA logFC, FDR, and S1-S6 stability are derived from the same cohort and cannot be counted separately as replicated evidence.",
            "- Open Targets disease association, literature, drug/candidate, tractability, and safety fields share a Platform release and may share upstream records.",
            "- ChEMBL-derived pharmacology can overlap Open Targets tractability and drug/candidate evidence.",
            "- Absence of an Open Targets safety-liability record is absence of retrieved evidence, not evidence of safety.",
            "- Future genetic, functional, and clinical sources require a new lineage review before their independence categories are finalized.",
            "",
            "## Validation",
            "",
            "All required columns, controlled domain names, source-domain references, evidence-type references, relationship categories, and dependency levels validated. The frozen integrated registry remained unchanged at 29,606 unique EnsemblIDs and 14,064 U2 genes. No prior committed file was modified.",
            "",
            "No target ranking, scoring, prioritization, recommendation, selection, or therapeutic interpretation was generated.",
        ]
    )
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def flatten(prefix: str, value: Any) -> list[str]:
    if isinstance(value, dict):
        output: list[str] = []
        for key in sorted(value):
            output.extend(flatten(f"{prefix}.{key}" if prefix else key, value[key]))
        return output
    return [f"{prefix}={value}"]


def write_session(
    started: datetime,
    repo: dict[str, str],
    input_validation: dict[str, Any],
    ontology_validation: dict[str, Any],
) -> None:
    metadata = {
        "task": "013",
        "purpose": "evidence ontology and qualitative independence architecture",
        "started_at_utc": started.isoformat(),
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "git_branch": repo["branch"],
        "git_head": repo["head"],
        "git_origin": repo["remote"],
        "frozen_task012_base_commit": TASK012_BASE_COMMIT,
        "network_access": "NOT_USED",
        "packages_installed_or_updated": "FALSE",
        "previous_committed_files_modified": "FALSE",
        "scoring_generated": "FALSE",
        "ranking_generated": "FALSE",
        "target_prioritization_generated": "FALSE",
        "therapeutic_interpretation_generated": "FALSE",
        "frozen_file_sha256": {
            str(path): file_sha256(path) for path in FROZEN_HASHES
        },
        "integrated_registry_validation": input_validation,
        "ontology_validation": ontology_validation,
        "script_sha256": file_sha256(SCRIPT),
        "plan_sha256": file_sha256(PLAN),
        "output_sha256": {
            str(DOMAIN_REGISTRY): file_sha256(DOMAIN_REGISTRY),
            str(SOURCE_LINEAGE): file_sha256(SOURCE_LINEAGE),
            str(INDEPENDENCE_MAP): file_sha256(INDEPENDENCE_MAP),
            str(SUMMARY): file_sha256(SUMMARY),
        },
    }
    SESSION.write_text("\n".join(flatten("", metadata)) + "\n", encoding="utf-8")


def main() -> None:
    started = datetime.now(timezone.utc)
    repo = validate_repository()
    input_validation = validate_integrated_registry()
    domains = build_domains()
    sources = build_sources()
    relationships = build_independence_map()
    ontology_validation = validate_ontology(domains, sources, relationships)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(DOMAIN_REGISTRY, domains, DOMAIN_COLUMNS)
    write_csv(SOURCE_LINEAGE, sources, SOURCE_COLUMNS)
    write_csv(INDEPENDENCE_MAP, relationships, INDEPENDENCE_COLUMNS)
    write_summary(domains, sources, relationships, ontology_validation)
    write_session(started, repo, input_validation, ontology_validation)

    print("Created files:")
    for path in (DOMAIN_REGISTRY, SOURCE_LINEAGE, INDEPENDENCE_MAP, SUMMARY, SESSION):
        print(f"- {path}")
    print(f"Evidence domains: {len(domains)}")
    print(f"Source-lineage records: {len(sources)}")
    print(f"Dependency relationships: {len(relationships)}")
    print(
        "Relationship categories: "
        + deterministic_category_counts(relationships)
    )
    print("All Task #013 assertions passed.")


def deterministic_category_counts(relationships: list[dict[str, str]]) -> str:
    counts = Counter(row["relationship"] for row in relationships)
    return "|".join(f"{key}={counts[key]}" for key in sorted(counts))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
