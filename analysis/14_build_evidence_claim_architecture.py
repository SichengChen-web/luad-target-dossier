#!/usr/bin/env python3
"""Build the Task #014 evidence claim and provenance architecture."""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


TASK012_BASE_COMMIT = "50a7be68cf8cbb6cd59aae3d3deac4120d27c553"
EXPECTED_GENES = 29_606
EXPECTED_U2 = 14_064
CURRENT_CLAIMS_PER_GENE = 5
RECORDS_PER_GENE = 7

INTEGRATED = Path("outputs/integrated_registry/integrated_target_registry.csv")
DOMAINS = Path("outputs/evidence_ontology/evidence_domain_registry.csv")
SOURCES = Path("outputs/evidence_ontology/evidence_source_lineage.csv")
INDEPENDENCE = Path("outputs/evidence_ontology/evidence_independence_map.csv")
FROZEN_HASHES = {
    INTEGRATED: "0587fc6901267b18c8144644571f89ac2cc46053b57ea5def4093795fdbc4c26",
    DOMAINS: "ee62ce66f2ca4726c9365da347198251b9bd77d2dead87b8409221505f2d03b8",
    SOURCES: "e9496e8bbf953fdffdbaed7e09936a8493230fc74939597537f8960fabf19f2c",
    INDEPENDENCE: "d99bbaa8fe5e6229774ac2bf73d84de8fbd367e585d692eb1273ecc7b5c53945",
}

SCRIPT = Path("analysis/14_build_evidence_claim_architecture.py")
PLAN = Path("docs/evidence_claim_model_v0.1.md")
OUTPUT_DIR = Path("outputs/evidence_claim_architecture")
CLAIMS = OUTPUT_DIR / "evidence_claim_registry.csv"
RECORDS = OUTPUT_DIR / "evidence_record_registry.csv"
SOURCE_ENTITIES = OUTPUT_DIR / "source_entity_registry.csv"
DEPENDENCIES = OUTPUT_DIR / "evidence_dependency_graph.csv"
MISSINGNESS = OUTPUT_DIR / "missingness_uncertainty_registry.csv"
SUMMARY = OUTPUT_DIR / "claim_architecture_summary.md"
SESSION = OUTPUT_DIR / "session_info.txt"

CLAIM_COLUMNS = [
    "claim_id",
    "EnsemblID",
    "domain_id",
    "claim_type",
    "claim_description",
    "claim_status",
    "supporting_record_count",
    "uncertainty_status",
]
RECORD_COLUMNS = [
    "record_id",
    "claim_id",
    "source_id",
    "source_record_type",
    "source_record_identifier",
    "raw_value_reference",
    "observation_status",
    "missingness_status",
    "uncertainty_status",
    "provenance_notes",
]
SOURCE_ENTITY_COLUMNS = [
    "source_id",
    "source_name",
    "provider",
    "source_type",
    "version",
    "retrieval_information",
    "dependency_notes",
]
DEPENDENCY_COLUMNS = [
    "dependency_id",
    "record_a",
    "record_b",
    "relationship",
    "dependency_level",
    "reason",
    "review_status",
]
MISSINGNESS_COLUMNS = [
    "entity_id",
    "entity_type",
    "status_type",
    "status_value",
    "explanation",
]

CURRENT_DOMAIN_TYPES = {
    "DOM_TRANSCRIPTOMIC_DISCOVERY": "TRANSCRIPTOMIC_ANALYSIS_RESULT",
    "DOM_DISEASE_ASSOCIATION": "LUAD_DISEASE_ASSOCIATION_EVIDENCE_STATE",
    "DOM_PHARMACOLOGY": "PHARMACOLOGY_ANNOTATION_EVIDENCE_STATE",
    "DOM_TRACTABILITY": "MODALITY_TRACTABILITY_EVIDENCE_STATE",
    "DOM_SAFETY": "SAFETY_LIABILITY_EVIDENCE_STATE",
}
DOMAIN_ORDER = list(CURRENT_DOMAIN_TYPES)

RECORD_TYPES = {
    "TRANSCRIPT_PRIMARY": (
        "DOM_TRANSCRIPTOMIC_DISCOVERY",
        "SRC_PROJECT_DE_ROBUSTNESS",
        [
            "U0_tested", "U1_DE", "U2_effect_supported_DE", "effect_band",
            "logFC_S0", "FDR_S0", "P_value_S0", "AveExpr_S0",
            "mean_logCPM_Tumor", "mean_logCPM_Normal", "sign_S0",
        ],
    ),
    "TRANSCRIPT_ROBUSTNESS": (
        "DOM_TRANSCRIPTOMIC_DISCOVERY",
        "SRC_PROJECT_DE_ROBUSTNESS",
        [
            "logFC_S1", "FDR_S1", "logFC_S2", "FDR_S2", "logFC_S3",
            "FDR_S3", "logFC_S4", "FDR_S4", "logFC_S5", "FDR_S5",
            "logFC_S6", "FDR_S6", "sign_concordant_S1_S6_count",
            "sign_concordant_all_S1_S6", "n_sensitivity_FDR05",
            "median_abs_delta_logFC_vs_S0", "max_abs_delta_logFC_vs_S0",
            "S6_sign_flip_vs_S0", "model_dependent_any_top50",
            "model_dependent_models", "reduced_residual_df_any",
            "reduced_residual_df_models", "max_residual_df_loss",
        ],
    ),
    "OT_LUAD_ASSOCIATION": (
        "DOM_DISEASE_ASSOCIATION",
        "SRC_OPEN_TARGETS_PLATFORM",
        [
            "OpenTargets_target_ID", "ot_target_retrieval_status",
            "ot_luad_disease_id", "ot_luad_disease_name",
            "ot_luad_direct_association_status",
            "ot_luad_direct_association_count",
            "ot_luad_direct_association_score_native",
            "ot_luad_direct_datasource_scores_native_json",
            "ot_luad_direct_datatype_scores_native_json",
            "ot_luad_indirect_association_status",
            "ot_luad_indirect_association_count",
            "ot_luad_indirect_association_score_native",
        ],
    ),
    "OT_DRUG_CANDIDATE": (
        "DOM_PHARMACOLOGY",
        "SRC_OPEN_TARGETS_PLATFORM",
        [
            "OpenTargets_target_ID", "ot_target_retrieval_status",
            "ot_drug_clinical_candidate_record_count",
            "ot_target_annotation_source",
        ],
    ),
    "CHEMBL_TARGET_ANNOTATION": (
        "DOM_PHARMACOLOGY",
        "SRC_CHEMBL",
        [
            "ChEMBL_target_ID", "chembl_target_retrieval_status",
            "chembl_target_record_count", "chembl_target_annotations_json",
            "chembl_target_annotation_source",
        ],
    ),
    "OT_TRACTABILITY_SUMMARY": (
        "DOM_TRACTABILITY",
        "SRC_OPEN_TARGETS_PLATFORM",
        [
            "OpenTargets_target_ID", "tractability_retrieval_status",
            "tractability_record_count", "tractability_true_assessment_count",
            "tractability_true_SM_count", "tractability_true_AB_count",
            "tractability_true_PR_count", "tractability_true_OC_count",
            "tractability_true_assessment_ids_by_modality_json",
            "tractability_safety_source_release",
        ],
    ),
    "OT_SAFETY_SUMMARY": (
        "DOM_SAFETY",
        "SRC_OPEN_TARGETS_PLATFORM",
        [
            "OpenTargets_target_ID", "safety_retrieval_status",
            "safety_liability_record_count",
            "tractability_safety_source_release",
        ],
    ),
}

ALLOWED_DEPENDENCY_RELATIONSHIPS = {
    "SAME_SOURCE",
    "SHARED_PUBLICATION",
    "SHARED_DATASET",
    "SHARED_COMPOUND",
    "SHARED_TRIAL",
    "UNKNOWN",
}
ALLOWED_DEPENDENCY_LEVELS = {
    "INDEPENDENT",
    "PARTIALLY_DEPENDENT",
    "DEPENDENT",
    "UNKNOWN",
}
MISSINGNESS_CATEGORIES = {
    "OBSERVED",
    "NOT_FOUND",
    "NOT_QUERIED",
    "NOT_APPLICABLE",
    "UNKNOWN",
}
UNCERTAINTY_CATEGORIES = {
    "SOURCE_LIMITATION",
    "INCOMPLETE_COVERAGE",
    "CONFLICTING_RECORDS",
    "DEPENDENCY_UNCERTAIN",
    "TEMPORAL_UNCERTAINTY",
}
FORBIDDEN_EXACT_COLUMNS = {
    "score",
    "rank",
    "priority",
    "confidence_score",
    "target_quality",
    "recommendation",
    "therapeutic_direction",
    "selection",
}
SUPPORTING_OBSERVATION_STATUSES = {
    "PRIMARY_ANALYSIS_RESULT_PRESENT",
    "ROBUSTNESS_ANALYSIS_RESULT_PRESENT",
    "ASSOCIATION_RECORD_PRESENT",
    "COUNT_RETRIEVED_POSITIVE",
    "TARGET_ANNOTATION_PRESENT",
    "ASSESSMENT_RECORD_PRESENT",
    "LIABILITY_RECORD_PRESENT",
}

ALLOWED_UNTRACKED = {
    "analysis/13_build_evidence_ontology.py",
    "docs/evidence_ontology_plan_v0.1.md",
    str(SCRIPT),
    str(PLAN),
}
ALLOWED_UNTRACKED_PREFIXES = (
    "outputs/evidence_ontology/",
    f"{OUTPUT_DIR}/",
)


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


def stable_id(prefix: str, value: str) -> str:
    return f"{prefix}_{hashlib.sha256(value.encode('utf-8')).hexdigest()[:24].upper()}"


def validate_repository() -> dict[str, str]:
    root = Path(git("rev-parse", "--show-toplevel")).resolve()
    if root != Path.cwd().resolve():
        fail(f"Run from repository root {root}; observed {Path.cwd().resolve()}")
    branch = git("branch", "--show-current")
    if branch != "main":
        fail(f"Task #014 requires branch main; observed {branch!r}")
    head = git("rev-parse", "HEAD")
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", TASK012_BASE_COMMIT, head],
        capture_output=True,
        text=True,
        check=False,
    ).returncode != 0:
        fail(f"Task #012 base {TASK012_BASE_COMMIT} is not an ancestor of HEAD {head}")
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
        if path not in ALLOWED_UNTRACKED
        and not any(path.startswith(prefix) for prefix in ALLOWED_UNTRACKED_PREFIXES)
    ]
    if unexpected:
        fail("Unexpected untracked files are present: " + ", ".join(unexpected))
    for path, expected_hash in FROZEN_HASHES.items():
        if not path.is_file():
            fail(f"Required frozen input is missing: {path}")
        observed = file_sha256(path)
        if observed != expected_hash:
            fail(f"Frozen input hash mismatch for {path}: {observed} != {expected_hash}")
    # Task #012 is committed and must remain identical to its base. Task #013
    # artifacts are hash-pinned even when still uncommitted during review.
    if subprocess.run(
        ["git", "diff", "--quiet", TASK012_BASE_COMMIT, "--", str(INTEGRATED)],
        capture_output=True,
        text=True,
        check=False,
    ).returncode != 0:
        fail("Task #012 integrated registry differs from its frozen base")
    return {"root": str(root), "branch": branch, "head": head, "remote": remote}


def read_small_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            fail(f"CSV has no header: {path}")
        return list(reader.fieldnames), list(reader)


def validate_ontology_inputs() -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    domain_header, domain_rows = read_small_csv(DOMAINS)
    source_header, source_rows = read_small_csv(SOURCES)
    independence_header, independence_rows = read_small_csv(INDEPENDENCE)
    required_domain_header = [
        "domain_id", "domain_name", "description", "scientific_question",
        "example_sources", "evidence_type", "future_role", "independence_notes",
    ]
    required_source_header = [
        "source_id", "source_name", "provider", "data_type",
        "domains_supported", "known_dependencies", "version_tracking_required",
        "notes",
    ]
    required_independence_header = [
        "evidence_pair", "relationship", "dependency_level", "reason",
        "future_aggregation_warning",
    ]
    if domain_header != required_domain_header:
        fail("Task #013 domain registry schema changed")
    if source_header != required_source_header:
        fail("Task #013 source lineage schema changed")
    if independence_header != required_independence_header:
        fail("Task #013 independence map schema changed")
    domain_ids = [row["domain_id"] for row in domain_rows]
    source_ids = [row["source_id"] for row in source_rows]
    if len(domain_ids) != 8 or len(set(domain_ids)) != 8:
        fail("Task #013 domain registry identity assertion failed")
    if len(source_ids) != 6 or len(set(source_ids)) != 6:
        fail("Task #013 source lineage identity assertion failed")
    if len(independence_rows) != 31:
        fail("Task #013 independence relationship count changed")
    if not set(CURRENT_DOMAIN_TYPES).issubset(domain_ids):
        fail("Task #013 ontology lacks a current evidence domain")
    required_sources = {
        "SRC_PROJECT_DE_ROBUSTNESS",
        "SRC_OPEN_TARGETS_PLATFORM",
        "SRC_CHEMBL",
    }
    if not required_sources.issubset(source_ids):
        fail("Task #013 source lineage lacks a source required by Task #014")
    return (
        {row["domain_id"]: row for row in domain_rows},
        {row["source_id"]: row for row in source_rows},
    )


def integrated_header() -> list[str]:
    with INTEGRATED.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        try:
            return next(reader)
        except StopIteration:
            fail("Integrated registry is empty")


def iter_integrated() -> Iterator[dict[str, str]]:
    with INTEGRATED.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            fail("Integrated registry has no header")
        yield from reader


def validate_integrated_input() -> dict[str, int]:
    header = integrated_header()
    required = {"EnsemblID", "U1_DE", "U2_effect_supported_DE"}
    for _, _, fields in RECORD_TYPES.values():
        required.update(fields)
    missing = required.difference(header)
    if missing:
        fail(f"Integrated registry lacks required fields: {sorted(missing)}")
    identifiers: set[str] = set()
    row_count = 0
    u2_count = 0
    for row in iter_integrated():
        row_count += 1
        ensembl_id = row["EnsemblID"]
        if not ensembl_id or ensembl_id in identifiers:
            fail(f"Empty or duplicate EnsemblID: {ensembl_id!r}")
        identifiers.add(ensembl_id)
        if row["U2_effect_supported_DE"] == "TRUE":
            u2_count += 1
        elif row["U2_effect_supported_DE"] != "FALSE":
            fail(f"Invalid U2 state at {ensembl_id}")
    if row_count != EXPECTED_GENES or len(identifiers) != EXPECTED_GENES:
        fail(
            f"Integrated identity failed: rows={row_count}, unique={len(identifiers)}"
        )
    if u2_count != EXPECTED_U2:
        fail(f"Integrated U2 count is {u2_count}; expected {EXPECTED_U2}")
    return {
        "row_count": row_count,
        "unique_ensembl_id_count": len(identifiers),
        "u2_count": u2_count,
    }


def claim_id(ensembl_id: str, domain_id: str) -> str:
    return stable_id("CLM", f"{ensembl_id}|{domain_id}")


def record_id(ensembl_id: str, record_type: str) -> str:
    return stable_id("REC", f"{ensembl_id}|{record_type}")


def dependency_id(record_a: str, record_b: str, relationship_name: str) -> str:
    ordered = "|".join(sorted((record_a, record_b)))
    return stable_id("DEP", f"{ordered}|{relationship_name}")


def positive_integer(value: str, label: str) -> bool:
    if not value.isdigit():
        fail(f"{label} is not a non-negative integer: {value!r}")
    return int(value) > 0


def transcript_uncertainty(row: dict[str, str]) -> str:
    if (
        row["S6_sign_flip_vs_S0"] == "TRUE"
        or row["sign_concordant_all_S1_S6"] == "FALSE"
    ):
        return "CONFLICTING_RECORDS"
    return "SOURCE_LIMITATION"


def domain_state(row: dict[str, str], domain_id: str) -> dict[str, Any]:
    ensembl_id = row["EnsemblID"]
    if domain_id == "DOM_TRANSCRIPTOMIC_DISCOVERY":
        if row["U2_effect_supported_DE"] == "TRUE":
            status = "EFFECT_SUPPORTED_DE"
        elif row["U1_DE"] == "TRUE":
            status = "DE_THRESHOLD_MET_EFFECT_BELOW_U2"
        else:
            status = "TESTED_NO_U1_THRESHOLD"
        return {
            "description": f"{ensembl_id} has a recorded TCGA-LUAD tumour-versus-normal transcriptomic analysis result.",
            "status": status,
            "support": 2,
            "missingness": "OBSERVED",
            "uncertainty": transcript_uncertainty(row),
            "missingness_explanation": "Primary and prespecified robustness analysis records are present; this is association evidence, not causality.",
        }
    if domain_id == "DOM_DISEASE_ASSOCIATION":
        direct = row["ot_luad_direct_association_status"] == "PRESENT"
        indirect = row["ot_luad_indirect_association_status"] == "PRESENT"
        target_present = row["ot_target_retrieval_status"] == "PRESENT"
        if direct:
            status, support, missingness = "DIRECT_ASSOCIATION_RECORD_PRESENT", 1, "OBSERVED"
        elif indirect:
            status, support, missingness = "INDIRECT_ASSOCIATION_RECORD_PRESENT_ONLY", 1, "OBSERVED"
        elif target_present:
            status, support, missingness = "NO_ASSOCIATION_RECORD_RETURNED", 0, "NOT_FOUND"
        else:
            status, support, missingness = "TARGET_NOT_MAPPED_OR_RETURNED", 0, "NOT_QUERIED"
        explanation = (
            "At least one source-native LUAD association view returned a record."
            if support
            else "No LUAD association record was retrieved; this is not negative biological evidence."
        )
        return {
            "description": f"{ensembl_id} has a recorded Open Targets LUAD disease-association evidence state.",
            "status": status,
            "support": support,
            "missingness": missingness,
            "uncertainty": "TEMPORAL_UNCERTAINTY" if support else "INCOMPLETE_COVERAGE",
            "missingness_explanation": explanation,
        }
    if domain_id == "DOM_PHARMACOLOGY":
        ot_mapped = row["ot_target_retrieval_status"] == "PRESENT"
        ot_positive = ot_mapped and positive_integer(
            row["ot_drug_clinical_candidate_record_count"],
            f"Open Targets drug/candidate count at {ensembl_id}",
        )
        chembl_present = row["chembl_target_retrieval_status"] in {"PRESENT", "PARTIAL"}
        support = int(ot_positive) + int(chembl_present)
        if ot_positive and chembl_present:
            status = "MULTISOURCE_ANNOTATION_PRESENT"
        elif ot_positive:
            status = "OPEN_TARGETS_DRUG_CANDIDATE_RECORD_PRESENT"
        elif chembl_present:
            status = "CHEMBL_TARGET_ANNOTATION_PRESENT"
        elif ot_mapped or row["ChEMBL_target_ID"] != "NOT_FOUND":
            status = "RETRIEVAL_COMPLETED_NO_POSITIVE_ANNOTATION"
        else:
            status = "TARGET_NOT_MAPPED_FOR_PHARMACOLOGY"
        missingness = "OBSERVED" if (ot_mapped or chembl_present) else "NOT_QUERIED"
        return {
            "description": f"{ensembl_id} has a recorded Open Targets and/or ChEMBL pharmacology-annotation evidence state.",
            "status": status,
            "support": support,
            "missingness": missingness,
            "uncertainty": "DEPENDENCY_UNCERTAIN" if missingness == "OBSERVED" else "INCOMPLETE_COVERAGE",
            "missingness_explanation": "Retrieved target/drug annotation states are preserved; target availability or a zero count is not therapeutic evidence.",
        }
    if domain_id == "DOM_TRACTABILITY":
        status = row["tractability_retrieval_status"]
        if status == "TRACTABILITY_RECORD_PRESENT":
            support, missingness, uncertainty = 1, "OBSERVED", "DEPENDENCY_UNCERTAIN"
        elif status == "TARGET_PRESENT_NO_TRACTABILITY_RECORD_RETURNED":
            support, missingness, uncertainty = 0, "NOT_FOUND", "INCOMPLETE_COVERAGE"
        else:
            support, missingness, uncertainty = 0, "NOT_QUERIED", "INCOMPLETE_COVERAGE"
        return {
            "description": f"{ensembl_id} has a recorded Open Targets modality-specific tractability evidence state.",
            "status": status,
            "support": support,
            "missingness": missingness,
            "uncertainty": uncertainty,
            "missingness_explanation": "A missing assessment remains missing and a positive source bucket is not a project decision.",
        }
    if domain_id == "DOM_SAFETY":
        status = row["safety_retrieval_status"]
        if status == "SAFETY_RECORD_PRESENT":
            support, missingness, uncertainty = 1, "OBSERVED", "SOURCE_LIMITATION"
        elif status == "TARGET_PRESENT_NO_SAFETY_RECORD_RETURNED":
            support, missingness, uncertainty = 0, "NOT_FOUND", "INCOMPLETE_COVERAGE"
        else:
            support, missingness, uncertainty = 0, "NOT_QUERIED", "INCOMPLETE_COVERAGE"
        return {
            "description": f"{ensembl_id} has a recorded Open Targets safety-liability evidence state.",
            "status": status,
            "support": support,
            "missingness": missingness,
            "uncertainty": uncertainty,
            "missingness_explanation": "Absence of a returned safety-liability record is absence of retrieved evidence, not evidence of safety.",
        }
    fail(f"Unsupported current domain: {domain_id}")


def raw_reference(ensembl_id: str, fields: list[str]) -> str:
    return (
        f"{INTEGRATED}#EnsemblID={ensembl_id}&fields=" + "|".join(fields)
    )


def record_state(row: dict[str, str], record_type: str) -> dict[str, str]:
    ensembl_id = row["EnsemblID"]
    if record_type == "TRANSCRIPT_PRIMARY":
        return {
            "observation": "PRIMARY_ANALYSIS_RESULT_PRESENT",
            "missingness": "OBSERVED",
            "uncertainty": "SOURCE_LIMITATION",
            "notes": "One derived S0 gene-level result record; logFC, FDR, p-value, expression summaries, and direction are fields of the same analysis result, not independent evidence.",
        }
    if record_type == "TRANSCRIPT_ROBUSTNESS":
        return {
            "observation": "ROBUSTNESS_ANALYSIS_RESULT_PRESENT",
            "missingness": "OBSERVED",
            "uncertainty": transcript_uncertainty(row),
            "notes": "S1-S6 are prespecified related model views of the same frozen cohort and qualify the S0 result; they are not independent replications.",
        }
    if record_type == "OT_LUAD_ASSOCIATION":
        claim = domain_state(row, "DOM_DISEASE_ASSOCIATION")
        observation = (
            "ASSOCIATION_RECORD_PRESENT"
            if claim["support"]
            else claim["status"]
        )
        return {
            "observation": observation,
            "missingness": claim["missingness"],
            "uncertainty": claim["uncertainty"],
            "notes": "Direct and indirect Open Targets LUAD views are retained in one source record because they overlap and must not be counted independently.",
        }
    if record_type == "OT_DRUG_CANDIDATE":
        if row["ot_target_retrieval_status"] != "PRESENT":
            observation, missingness = "TARGET_NOT_MAPPED_OR_RETURNED", "NOT_QUERIED"
        elif positive_integer(
            row["ot_drug_clinical_candidate_record_count"],
            f"Open Targets drug/candidate count at {ensembl_id}",
        ):
            observation, missingness = "COUNT_RETRIEVED_POSITIVE", "OBSERVED"
        else:
            observation, missingness = "COUNT_RETRIEVED_ZERO", "OBSERVED"
        return {
            "observation": observation,
            "missingness": missingness,
            "uncertainty": "TEMPORAL_UNCERTAINTY" if missingness == "OBSERVED" else "INCOMPLETE_COVERAGE",
            "notes": "The source-native count is a retrieval result, not a project score; zero is an observed source count and not negative therapeutic evidence.",
        }
    if record_type == "CHEMBL_TARGET_ANNOTATION":
        status = row["chembl_target_retrieval_status"]
        if status in {"PRESENT", "PARTIAL"}:
            observation, missingness = "TARGET_ANNOTATION_PRESENT", "OBSERVED"
        elif status == "NOT_MAPPED":
            observation, missingness = "TARGET_NOT_MAPPED", "NOT_QUERIED"
        else:
            observation, missingness = "TARGET_ANNOTATION_NOT_FOUND", "NOT_FOUND"
        return {
            "observation": observation,
            "missingness": missingness,
            "uncertainty": "SOURCE_LIMITATION" if missingness == "OBSERVED" else "INCOMPLETE_COVERAGE",
            "notes": "ChEMBL target annotation/availability is not compound activity, potency, mechanism, or therapeutic value evidence.",
        }
    if record_type == "OT_TRACTABILITY_SUMMARY":
        status = row["tractability_retrieval_status"]
        if status == "TRACTABILITY_RECORD_PRESENT":
            observation, missingness = "ASSESSMENT_RECORD_PRESENT", "OBSERVED"
        elif status == "TARGET_PRESENT_NO_TRACTABILITY_RECORD_RETURNED":
            observation, missingness = status, "NOT_FOUND"
        else:
            observation, missingness = status, "NOT_QUERIED"
        return {
            "observation": observation,
            "missingness": missingness,
            "uncertainty": "DEPENDENCY_UNCERTAIN" if missingness == "OBSERVED" else "INCOMPLETE_COVERAGE",
            "notes": "This is a source-native assessment summary; modalities and positive buckets share a framework and are not independent votes or a project score.",
        }
    if record_type == "OT_SAFETY_SUMMARY":
        status = row["safety_retrieval_status"]
        if status == "SAFETY_RECORD_PRESENT":
            observation, missingness = "LIABILITY_RECORD_PRESENT", "OBSERVED"
        elif status == "TARGET_PRESENT_NO_SAFETY_RECORD_RETURNED":
            observation, missingness = status, "NOT_FOUND"
        else:
            observation, missingness = status, "NOT_QUERIED"
        return {
            "observation": observation,
            "missingness": missingness,
            "uncertainty": "SOURCE_LIMITATION" if missingness == "OBSERVED" else "INCOMPLETE_COVERAGE",
            "notes": "The summary points to source-native liability records; absence of a returned record is not evidence of safety and a present record is not an automatic rejection decision.",
        }
    fail(f"Unsupported record type: {record_type}")


def open_writer(path: Path, columns: list[str]) -> tuple[Any, csv.DictWriter]:
    handle = path.open("w", newline="", encoding="utf-8")
    writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    return handle, writer


def write_claims() -> dict[str, Counter[str]]:
    handle, writer = open_writer(CLAIMS, CLAIM_COLUMNS)
    status_counts: Counter[str] = Counter()
    uncertainty_counts: Counter[str] = Counter()
    try:
        for row in iter_integrated():
            for domain_id in DOMAIN_ORDER:
                state = domain_state(row, domain_id)
                writer.writerow(
                    {
                        "claim_id": claim_id(row["EnsemblID"], domain_id),
                        "EnsemblID": row["EnsemblID"],
                        "domain_id": domain_id,
                        "claim_type": CURRENT_DOMAIN_TYPES[domain_id],
                        "claim_description": state["description"],
                        "claim_status": state["status"],
                        "supporting_record_count": str(state["support"]),
                        "uncertainty_status": state["uncertainty"],
                    }
                )
                status_counts[state["status"]] += 1
                uncertainty_counts[state["uncertainty"]] += 1
    finally:
        handle.close()
    return {"status": status_counts, "uncertainty": uncertainty_counts}


def write_records() -> dict[str, Counter[str]]:
    handle, writer = open_writer(RECORDS, RECORD_COLUMNS)
    observation_counts: Counter[str] = Counter()
    missingness_counts: Counter[str] = Counter()
    uncertainty_counts: Counter[str] = Counter()
    try:
        for row in iter_integrated():
            ensembl_id = row["EnsemblID"]
            for record_type, (domain_id, source_id, fields) in RECORD_TYPES.items():
                state = record_state(row, record_type)
                writer.writerow(
                    {
                        "record_id": record_id(ensembl_id, record_type),
                        "claim_id": claim_id(ensembl_id, domain_id),
                        "source_id": source_id,
                        "source_record_type": record_type,
                        "source_record_identifier": f"TASK012::{ensembl_id}::{record_type}",
                        "raw_value_reference": raw_reference(ensembl_id, fields),
                        "observation_status": state["observation"],
                        "missingness_status": state["missingness"],
                        "uncertainty_status": state["uncertainty"],
                        "provenance_notes": state["notes"],
                    }
                )
                observation_counts[state["observation"]] += 1
                missingness_counts[state["missingness"]] += 1
                uncertainty_counts[state["uncertainty"]] += 1
    finally:
        handle.close()
    return {
        "observation": observation_counts,
        "missingness": missingness_counts,
        "uncertainty": uncertainty_counts,
    }


SOURCE_TYPE_AND_VERSION = {
    "SRC_TCGA_LUAD": (
        "BIOLOGICAL_COHORT",
        "PROJECT_FROZEN_TCGA_LUAD_COHORT_V0.1",
        "TCGA-LUAD data obtained through recount3; cohort resolution and biospecimen provenance are recorded in Tasks #001-#005.",
    ),
    "SRC_RECOUNT3_TCGA_LUAD": (
        "PROCESSED_DATA_RESOURCE",
        "GENCODE_V26;RECOUNT3_VERSION_RECORDED_UPSTREAM",
        "Programmatic recount3 retrieval with the gene annotation pinned to gencode_v26.",
    ),
    "SRC_PROJECT_DE_ROBUSTNESS": (
        "DERIVED_ANALYSIS",
        "PRIMARY_S0_AND_SENSITIVITY_S1-S6_V0.1",
        "Frozen Task #006 primary DE and Task #007 sensitivity outputs integrated by Task #008/Task #012.",
    ),
    "SRC_OPEN_TARGETS_PLATFORM": (
        "INTEGRATED_DATABASE",
        "DATA_26.06;API_26.6.3",
        "Official Open Targets Platform retrieval in Tasks #010-#011; exact request/response provenance is recorded in their session files.",
    ),
    "SRC_CHEMBL": (
        "CURATED_DATABASE",
        "CHEMBL_37",
        "Official ChEMBL target retrieval in Task #010; only target annotations/availability are represented here.",
    ),
    "SRC_PROJECT_INTEGRATED_REGISTRY": (
        "DERIVED_INTEGRATION",
        f"TASK012_SHA256_{FROZEN_HASHES[INTEGRATED]}",
        "Local standard-library integration of frozen Tasks #008-#011; no new scientific observation was generated.",
    ),
}


def write_source_entities(source_rows: dict[str, dict[str, str]]) -> int:
    handle, writer = open_writer(SOURCE_ENTITIES, SOURCE_ENTITY_COLUMNS)
    count = 0
    try:
        for source_id in source_rows:
            row = source_rows[source_id]
            if source_id not in SOURCE_TYPE_AND_VERSION:
                fail(f"No Task #014 source-entity mapping for {source_id}")
            source_type, version, retrieval = SOURCE_TYPE_AND_VERSION[source_id]
            writer.writerow(
                {
                    "source_id": source_id,
                    "source_name": row["source_name"],
                    "provider": row["provider"],
                    "source_type": source_type,
                    "version": version,
                    "retrieval_information": retrieval,
                    "dependency_notes": row["known_dependencies"] + "; " + row["notes"],
                }
            )
            count += 1
    finally:
        handle.close()
    return count


def write_dependency_graph() -> dict[str, Counter[str]]:
    handle, writer = open_writer(DEPENDENCIES, DEPENDENCY_COLUMNS)
    relationship_counts: Counter[str] = Counter()
    level_counts: Counter[str] = Counter()
    try:
        for row in iter_integrated():
            ensembl_id = row["EnsemblID"]
            states = {
                record_type: record_state(row, record_type)
                for record_type in RECORD_TYPES
            }
            edge_specs = [
                (
                    "TRANSCRIPT_PRIMARY", "TRANSCRIPT_ROBUSTNESS",
                    "SHARED_DATASET", "DEPENDENT",
                    "Primary and S1-S6 records are derived from the same frozen TCGA-LUAD expression cohort and related contrasts.",
                    "REVIEWED_TASK013",
                ),
                (
                    "OT_LUAD_ASSOCIATION", "OT_DRUG_CANDIDATE",
                    "SAME_SOURCE", "DEPENDENT",
                    "Both records are delivered by the same Open Targets target/release framework; upstream record overlap is possible.",
                    "REVIEWED_TASK013",
                ),
                (
                    "OT_LUAD_ASSOCIATION", "OT_TRACTABILITY_SUMMARY",
                    "SAME_SOURCE", "PARTIALLY_DEPENDENT",
                    "Disease association and tractability address different questions but share the Open Targets target object and release.",
                    "REVIEWED_LINEAGE_ONLY",
                ),
                (
                    "OT_LUAD_ASSOCIATION", "OT_SAFETY_SUMMARY",
                    "SAME_SOURCE", "PARTIALLY_DEPENDENT",
                    "Disease association and safety records share the Open Targets delivery source and may share target annotations or literature.",
                    "RECORD_LEVEL_OVERLAP_UNRESOLVED",
                ),
                (
                    "OT_DRUG_CANDIDATE", "OT_TRACTABILITY_SUMMARY",
                    "SAME_SOURCE", "PARTIALLY_DEPENDENT",
                    "Drug/candidate counts can overlap clinical-precedence or pharmacology evidence used by tractability.",
                    "REVIEWED_TASK013",
                ),
                (
                    "OT_DRUG_CANDIDATE", "OT_SAFETY_SUMMARY",
                    "SAME_SOURCE", "PARTIALLY_DEPENDENT",
                    "Drug/candidate and safety summaries share a Platform release; exact upstream record overlap is unresolved.",
                    "RECORD_LEVEL_OVERLAP_UNRESOLVED",
                ),
                (
                    "OT_TRACTABILITY_SUMMARY", "OT_SAFETY_SUMMARY",
                    "SAME_SOURCE", "PARTIALLY_DEPENDENT",
                    "Tractability and safety are separate blocks but share the Open Targets target object and may reference overlapping pharmacology or literature.",
                    "REVIEWED_TASK013",
                ),
                (
                    "OT_DRUG_CANDIDATE", "CHEMBL_TARGET_ANNOTATION",
                    "UNKNOWN", "PARTIALLY_DEPENDENT",
                    "Open Targets drug/candidate information may use ChEMBL, but exact record-level overlap is not present in the integrated summary.",
                    "RECORD_LEVEL_OVERLAP_UNRESOLVED",
                ),
                (
                    "CHEMBL_TARGET_ANNOTATION", "OT_TRACTABILITY_SUMMARY",
                    "UNKNOWN", "PARTIALLY_DEPENDENT",
                    "Open Targets tractability may use ChEMBL-derived information; exact shared records cannot be resolved from gene-level summaries.",
                    "RECORD_LEVEL_OVERLAP_UNRESOLVED",
                ),
            ]
            for left, right, relation, level, reason, review in edge_specs:
                # A dependency edge is instantiated only when both traceable
                # record slots contain an observed retrieval/analysis record.
                if (
                    states[left]["missingness"] != "OBSERVED"
                    or states[right]["missingness"] != "OBSERVED"
                ):
                    continue
                record_a = record_id(ensembl_id, left)
                record_b = record_id(ensembl_id, right)
                writer.writerow(
                    {
                        "dependency_id": dependency_id(record_a, record_b, relation),
                        "record_a": record_a,
                        "record_b": record_b,
                        "relationship": relation,
                        "dependency_level": level,
                        "reason": reason,
                        "review_status": review,
                    }
                )
                relationship_counts[relation] += 1
                level_counts[level] += 1
    finally:
        handle.close()
    return {"relationship": relationship_counts, "level": level_counts}


def write_missingness_registry() -> dict[str, Counter[str]]:
    handle, writer = open_writer(MISSINGNESS, MISSINGNESS_COLUMNS)
    missing_counts: Counter[str] = Counter()
    uncertainty_counts: Counter[str] = Counter()
    try:
        for row in iter_integrated():
            for domain_id in DOMAIN_ORDER:
                state = domain_state(row, domain_id)
                entity = claim_id(row["EnsemblID"], domain_id)
                writer.writerow(
                    {
                        "entity_id": entity,
                        "entity_type": "EVIDENCE_CLAIM",
                        "status_type": "MISSINGNESS",
                        "status_value": state["missingness"],
                        "explanation": state["missingness_explanation"],
                    }
                )
                writer.writerow(
                    {
                        "entity_id": entity,
                        "entity_type": "EVIDENCE_CLAIM",
                        "status_type": "UNCERTAINTY",
                        "status_value": state["uncertainty"],
                        "explanation": uncertainty_explanation(state["uncertainty"], domain_id),
                    }
                )
                missing_counts[state["missingness"]] += 1
                uncertainty_counts[state["uncertainty"]] += 1

        architecture_rows = [
            ("DOM_GENETIC_EVIDENCE", "EVIDENCE_DOMAIN", "MISSINGNESS", "NOT_QUERIED", "No dedicated genetic evidence source has been retrieved in the current project snapshot."),
            ("DOM_FUNCTIONAL_DEPENDENCY", "EVIDENCE_DOMAIN", "MISSINGNESS", "NOT_QUERIED", "No dedicated functional-dependency source has been retrieved in the current project snapshot."),
            ("DOM_CLINICAL_DEVELOPMENT", "EVIDENCE_DOMAIN", "MISSINGNESS", "NOT_QUERIED", "No dedicated trial-level clinical-development source has been retrieved in the current project snapshot."),
            ("SRC_PROJECT_INTEGRATED_REGISTRY", "SOURCE_ENTITY", "MISSINGNESS", "NOT_APPLICABLE", "External retrieval missingness is not applicable to this locally derived integration artifact."),
            ("ARCH_FUTURE_SOURCE_SELECTION", "ARCHITECTURE", "MISSINGNESS", "UNKNOWN", "The providers and versions for future genetic, functional, and clinical sources have not been selected."),
        ]
        for entity_id, entity_type, status_type, status_value, explanation in architecture_rows:
            writer.writerow(
                {
                    "entity_id": entity_id,
                    "entity_type": entity_type,
                    "status_type": status_type,
                    "status_value": status_value,
                    "explanation": explanation,
                }
            )
            missing_counts[status_value] += 1
    finally:
        handle.close()
    return {"missingness": missing_counts, "uncertainty": uncertainty_counts}


def uncertainty_explanation(category: str, domain_id: str) -> str:
    messages = {
        "SOURCE_LIMITATION": "The source answers a bounded question and cannot by itself establish causality, therapeutic value, or complete safety.",
        "INCOMPLETE_COVERAGE": "Public source coverage or identifier mapping is incomplete; absence of a record is not negative evidence.",
        "CONFLICTING_RECORDS": "At least one prespecified sensitivity diagnostic conflicts with the primary expression direction or full sign concordance.",
        "DEPENDENCY_UNCERTAIN": "The record may overlap another source/domain through Open Targets, ChEMBL, or clinical-precedence lineage.",
        "TEMPORAL_UNCERTAINTY": "The external database is versioned and may change in later releases.",
    }
    if category not in messages:
        fail(f"Unknown uncertainty category for {domain_id}: {category}")
    return messages[category]


def validate_columns() -> None:
    for name, columns in (
        ("claims", CLAIM_COLUMNS),
        ("records", RECORD_COLUMNS),
        ("source entities", SOURCE_ENTITY_COLUMNS),
        ("dependencies", DEPENDENCY_COLUMNS),
        ("missingness", MISSINGNESS_COLUMNS),
    ):
        forbidden = FORBIDDEN_EXACT_COLUMNS.intersection(column.lower() for column in columns)
        if forbidden:
            fail(f"{name} table contains forbidden columns: {sorted(forbidden)}")


def validate_outputs(
    valid_domains: set[str], valid_sources: set[str]
) -> dict[str, Any]:
    validate_columns()
    claim_ids: set[str] = set()
    claim_support_expected: dict[str, int] = {}
    gene_claim_counts: Counter[str] = Counter()
    with CLAIMS.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != CLAIM_COLUMNS:
            fail("Claim registry schema mismatch")
        for row in reader:
            if row["claim_id"] in claim_ids:
                fail(f"Duplicate claim_id: {row['claim_id']}")
            claim_ids.add(row["claim_id"])
            gene_claim_counts[row["EnsemblID"]] += 1
            if row["domain_id"] not in valid_domains:
                fail(f"Claim references invalid domain: {row['domain_id']}")
            if row["uncertainty_status"] not in UNCERTAINTY_CATEGORIES:
                fail(f"Claim has invalid uncertainty: {row['claim_id']}")
            if not row["supporting_record_count"].isdigit():
                fail(f"Claim has invalid supporting count: {row['claim_id']}")
            claim_support_expected[row["claim_id"]] = int(row["supporting_record_count"])
            lower_description = row["claim_description"].lower()
            for forbidden_phrase in (
                "good therapeutic target", "should be inhibited", "best candidate",
                "should be activated", "therapeutic value",
            ):
                if forbidden_phrase in lower_description:
                    fail(f"Prohibited interpretation in claim {row['claim_id']}")
    expected_claims = EXPECTED_GENES * CURRENT_CLAIMS_PER_GENE
    if len(claim_ids) != expected_claims:
        fail(f"Claim count is {len(claim_ids)}; expected {expected_claims}")
    if len(gene_claim_counts) != EXPECTED_GENES or set(gene_claim_counts.values()) != {CURRENT_CLAIMS_PER_GENE}:
        fail("Every EnsemblID must have exactly five current-domain claims")

    record_ids: set[str] = set()
    source_record_ids: set[str] = set()
    observed_support: Counter[str] = Counter()
    with RECORDS.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != RECORD_COLUMNS:
            fail("Evidence record registry schema mismatch")
        for row in reader:
            if row["record_id"] in record_ids:
                fail(f"Duplicate record_id: {row['record_id']}")
            if row["source_record_identifier"] in source_record_ids:
                fail(f"Duplicate source_record_identifier: {row['source_record_identifier']}")
            record_ids.add(row["record_id"])
            source_record_ids.add(row["source_record_identifier"])
            if row["claim_id"] not in claim_ids:
                fail(f"Record references invalid claim: {row['record_id']}")
            if row["source_id"] not in valid_sources:
                fail(f"Record references invalid source: {row['record_id']}")
            if row["missingness_status"] not in MISSINGNESS_CATEGORIES:
                fail(f"Record has invalid missingness: {row['record_id']}")
            if row["uncertainty_status"] not in UNCERTAINTY_CATEGORIES:
                fail(f"Record has invalid uncertainty: {row['record_id']}")
            if row["observation_status"] in SUPPORTING_OBSERVATION_STATUSES:
                observed_support[row["claim_id"]] += 1
    expected_records = EXPECTED_GENES * RECORDS_PER_GENE
    if len(record_ids) != expected_records:
        fail(f"Record count is {len(record_ids)}; expected {expected_records}")
    if any(observed_support[claim] != expected for claim, expected in claim_support_expected.items()):
        fail("Claim supporting_record_count does not match traceable supporting records")

    source_entity_ids: set[str] = set()
    with SOURCE_ENTITIES.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != SOURCE_ENTITY_COLUMNS:
            fail("Source entity registry schema mismatch")
        for row in reader:
            if row["source_id"] in source_entity_ids:
                fail(f"Duplicate source entity: {row['source_id']}")
            source_entity_ids.add(row["source_id"])
    if source_entity_ids != valid_sources:
        fail("Source entity registry does not preserve Task #013 source identities")

    dependency_ids: set[str] = set()
    dependency_relationships: Counter[str] = Counter()
    dependency_levels: Counter[str] = Counter()
    with DEPENDENCIES.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != DEPENDENCY_COLUMNS:
            fail("Dependency graph schema mismatch")
        for row in reader:
            if row["dependency_id"] in dependency_ids:
                fail(f"Duplicate dependency_id: {row['dependency_id']}")
            dependency_ids.add(row["dependency_id"])
            if row["record_a"] not in record_ids or row["record_b"] not in record_ids:
                fail(f"Dependency references invalid record: {row['dependency_id']}")
            if row["record_a"] == row["record_b"]:
                fail(f"Self-dependency: {row['dependency_id']}")
            if row["relationship"] not in ALLOWED_DEPENDENCY_RELATIONSHIPS:
                fail(f"Invalid dependency relationship: {row['relationship']}")
            if row["dependency_level"] not in ALLOWED_DEPENDENCY_LEVELS:
                fail(f"Invalid dependency level: {row['dependency_level']}")
            dependency_relationships[row["relationship"]] += 1
            dependency_levels[row["dependency_level"]] += 1

    missingness_counts: Counter[str] = Counter()
    uncertainty_counts: Counter[str] = Counter()
    with MISSINGNESS.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != MISSINGNESS_COLUMNS:
            fail("Missingness/uncertainty registry schema mismatch")
        for row in reader:
            if row["status_type"] == "MISSINGNESS":
                if row["status_value"] not in MISSINGNESS_CATEGORIES:
                    fail(f"Invalid missingness category: {row['status_value']}")
                missingness_counts[row["status_value"]] += 1
            elif row["status_type"] == "UNCERTAINTY":
                if row["status_value"] not in UNCERTAINTY_CATEGORIES:
                    fail(f"Invalid uncertainty category: {row['status_value']}")
                uncertainty_counts[row["status_value"]] += 1
            else:
                fail(f"Invalid status_type: {row['status_type']}")
    if set(missingness_counts) != MISSINGNESS_CATEGORIES:
        fail("Not all controlled missingness categories are represented")
    if set(uncertainty_counts) != UNCERTAINTY_CATEGORIES:
        fail("Not all controlled uncertainty categories are represented")

    all_id_sets = [claim_ids, record_ids, source_entity_ids, dependency_ids]
    total_ids = sum(len(values) for values in all_id_sets)
    if len(set().union(*all_id_sets)) != total_ids:
        fail("Claim, record, source, and dependency identifiers are not globally unique")
    return {
        "claim_count": len(claim_ids),
        "record_count": len(record_ids),
        "source_entity_count": len(source_entity_ids),
        "dependency_count": len(dependency_ids),
        "dependency_relationship_counts": dict(sorted(dependency_relationships.items())),
        "dependency_level_counts": dict(sorted(dependency_levels.items())),
        "missingness_counts": dict(sorted(missingness_counts.items())),
        "uncertainty_counts": dict(sorted(uncertainty_counts.items())),
        "all_ids_unique": True,
        "all_links_valid": True,
        "scoring_generated": False,
    }


def markdown_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    output = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    output.extend(
        "| " + " | ".join(str(value).replace("|", "\\|") for value in row) + " |"
        for row in rows
    )
    return output


def write_summary(validation: dict[str, Any]) -> None:
    lines = [
        "# Task #014 evidence claim and provenance architecture summary",
        "",
        f"**Bounded evidence claims:** {validation['claim_count']:,}  ",
        f"**Traceable evidence records:** {validation['record_count']:,}  ",
        f"**Source entities:** {validation['source_entity_count']:,}  ",
        f"**Instantiated dependency relationships:** {validation['dependency_count']:,}  ",
        "**Scoring, ranking, prioritization, or recommendations created:** No",
        "",
        "## Architecture instantiated",
        "",
        "Each of the 29,606 Ensembl genes has five bounded current-domain claims: transcriptomic discovery, LUAD disease association, pharmacology annotation, tractability, and safety liability. Future genetic, functional-dependency, and clinical-development domains remain explicitly `NOT_QUERIED` at the domain level.",
        "",
        "Each gene has seven traceable record slots: primary transcriptomic result, transcriptomic robustness result, Open Targets LUAD association, Open Targets drug/candidate count, ChEMBL target annotation, Open Targets tractability summary, and Open Targets safety summary. A record can carry `NOT_FOUND` or `NOT_QUERIED`; such a placeholder preserves missingness and is not counted as supporting evidence.",
        "",
        "## Dependency relationships",
        "",
    ]
    lines.extend(
        markdown_table(
            ["Relationship", "Count"],
            [[key, value] for key, value in validation["dependency_relationship_counts"].items()],
        )
    )
    lines.extend(["", "Dependency levels:", ""])
    lines.extend(
        markdown_table(
            ["Dependency level", "Count"],
            [[key, value] for key, value in validation["dependency_level_counts"].items()],
        )
    )
    lines.extend(
        [
            "",
            "Dependency edges are instantiated only when both records are observed. Primary and robustness expression records are explicitly linked by `SHARED_DATASET`. Open Targets records are linked by `SAME_SOURCE` where appropriate. Potential Open Targets/ChEMBL overlap that cannot be resolved from gene-level summaries is marked `UNKNOWN` with `PARTIALLY_DEPENDENT` level and requires record-level review.",
            "",
            "The absence of an edge does not prove independence; Task #013 remains the higher-level evidence-type independence framework.",
            "",
            "## Missingness categories",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            ["Category", "Registry rows"],
            [[key, value] for key, value in validation["missingness_counts"].items()],
        )
    )
    lines.extend(["", "## Uncertainty categories", ""])
    lines.extend(
        markdown_table(
            ["Category", "Registry rows"],
            [[key, value] for key, value in validation["uncertainty_counts"].items()],
        )
    )
    lines.extend(
        [
            "",
            "## Evidence-inflation controls",
            "",
            "- Scalar fields from one source row are referenced together rather than promoted to separate independent claims.",
            "- S0 and S1-S6 are separate traceable records but explicitly share a dataset and are dependent; sensitivity models are not replications.",
            "- Open Targets direct/indirect association fields remain one disease-association record because the views overlap.",
            "- Tractability modality counts remain one source summary and are not a score or multiple votes.",
            "- ChEMBL target availability is not interpreted as compound activity, potency, mechanism, or therapeutic value.",
            "- Supporting-record counts are audit counts only and are never converted into confidence or rank.",
            "",
            "## Critical missingness boundary",
            "",
            "`NOT_FOUND` means the defined retrieval returned no corresponding record; `NOT_QUERIED` means no query could be made or the future domain has not been retrieved. Neither is negative biological evidence. In particular, absence of a safety-liability record is not evidence of safety.",
            "",
            "## Validation",
            "",
            "All claim, record, source, and dependency identifiers are unique. Every record links to a valid claim and source, every claim links to a Task #013 domain, every dependency links to two valid records, every supporting-record count reconciles to traceable records, and all controlled missingness and uncertainty categories are represented.",
            "",
            "No score, rank, priority, confidence score, target quality, recommendation, therapeutic direction, selection, target prioritization, or therapeutic interpretation was generated.",
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
    input_validation: dict[str, int],
    output_validation: dict[str, Any],
) -> None:
    metadata = {
        "task": "014",
        "purpose": "bounded evidence claim and provenance architecture",
        "started_at_utc": started.isoformat(),
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "git_branch": repo["branch"],
        "git_head": repo["head"],
        "git_origin": repo["remote"],
        "frozen_task012_base_commit": TASK012_BASE_COMMIT,
        "task013_inputs_commit_state_at_execution": "HASH_PINNED_UNCOMMITTED_REVIEW_ARTIFACTS",
        "network_access": "NOT_USED",
        "packages_installed_or_updated": "FALSE",
        "previous_committed_files_modified": "FALSE",
        "scoring_generated": "FALSE",
        "ranking_generated": "FALSE",
        "target_prioritization_generated": "FALSE",
        "therapeutic_interpretation_generated": "FALSE",
        "frozen_input_sha256": {str(path): file_sha256(path) for path in FROZEN_HASHES},
        "integrated_input_validation": input_validation,
        "output_validation": output_validation,
        "script_sha256": file_sha256(SCRIPT),
        "plan_sha256": file_sha256(PLAN),
        "output_sha256": {
            str(CLAIMS): file_sha256(CLAIMS),
            str(RECORDS): file_sha256(RECORDS),
            str(SOURCE_ENTITIES): file_sha256(SOURCE_ENTITIES),
            str(DEPENDENCIES): file_sha256(DEPENDENCIES),
            str(MISSINGNESS): file_sha256(MISSINGNESS),
            str(SUMMARY): file_sha256(SUMMARY),
        },
    }
    SESSION.write_text("\n".join(flatten("", metadata)) + "\n", encoding="utf-8")


def main() -> None:
    started = datetime.now(timezone.utc)
    repo = validate_repository()
    domains, sources = validate_ontology_inputs()
    input_validation = validate_integrated_input()
    validate_columns()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_claims()
    write_records()
    write_source_entities(sources)
    write_dependency_graph()
    write_missingness_registry()
    output_validation = validate_outputs(set(domains), set(sources))
    write_summary(output_validation)
    write_session(started, repo, input_validation, output_validation)

    print("Created files:")
    for path in (
        CLAIMS, RECORDS, SOURCE_ENTITIES, DEPENDENCIES, MISSINGNESS, SUMMARY, SESSION
    ):
        print(f"- {path}")
    print(f"Claims: {output_validation['claim_count']}")
    print(f"Evidence records: {output_validation['record_count']}")
    print(f"Source entities: {output_validation['source_entity_count']}")
    print(f"Dependency relationships: {output_validation['dependency_count']}")
    print("All Task #014 assertions passed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
