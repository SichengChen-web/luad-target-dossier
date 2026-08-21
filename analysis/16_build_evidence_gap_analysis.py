#!/usr/bin/env python3
"""Build the Task #016 descriptive evidence-gap analysis."""

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
from typing import Any


TASK015_BASE_COMMIT = "0709aeba530d3d900edcd6b403cb4ec6399f1782"
EXPECTED_GENES = 29_606
EXPECTED_U2 = 14_064
EXPECTED_CLAIMS = 148_030
EXPECTED_RECORDS = 207_242

INTEGRATED = Path("outputs/integrated_registry/integrated_target_registry.csv")
CLAIMS_INPUT = Path(
    "outputs/evidence_claim_architecture/evidence_claim_registry.csv"
)
RECORDS_INPUT = Path(
    "outputs/evidence_claim_architecture/evidence_record_registry.csv"
)
MISSINGNESS_INPUT = Path(
    "outputs/evidence_claim_architecture/missingness_uncertainty_registry.csv"
)
FRAMEWORK_INPUT = Path("docs/target_prioritization_framework_v0.1.md")
INPUT_HASHES = {
    INTEGRATED: "0587fc6901267b18c8144644571f89ac2cc46053b57ea5def4093795fdbc4c26",
    CLAIMS_INPUT: "0d963a4c5c8f9586f81369e33df0a2b7e57bb37ac8ceab4ce54498baf2351a66",
    RECORDS_INPUT: "76ec5056fb4e468176073073532204d231765d4f0cd70dbb6cfe4ad8bf752343",
    MISSINGNESS_INPUT: "3bbe080b1ed46dd159a86b53fb707572f988361af96e001188b69da0daa9147d",
    FRAMEWORK_INPUT: "9d7c76235a9272cf62157eb322cc8d0f55dc2af697958d707b28e43c06334213",
}

SCRIPT = Path("analysis/16_build_evidence_gap_analysis.py")
PLAN = Path("docs/evidence_gap_analysis_plan_v0.1.md")
OUTPUT_DIR = Path("outputs/evidence_gap_analysis")
GAP_REGISTRY = OUTPUT_DIR / "evidence_gap_registry.csv"
CATEGORY_COUNTS = OUTPUT_DIR / "evidence_gap_category_counts.csv"
VALIDATION_MATRIX = OUTPUT_DIR / "validation_strategy_matrix.csv"
SUMMARY = OUTPUT_DIR / "evidence_gap_summary.md"
SESSION = OUTPUT_DIR / "session_info.txt"

GAP_COLUMNS = [
    "EnsemblID",
    "discovery_status",
    "mechanistic_status",
    "development_status",
    "risk_status",
    "evidence_maturity_status",
    "missing_evidence_domains",
    "known_uncertainties",
    "recommended_future_evidence_type",
]
CATEGORY_COLUMNS = [
    "category_group",
    "category",
    "count",
    "denominator",
    "percent",
]
VALIDATION_COLUMNS = [
    "evidence_gap",
    "evidence_layer",
    "potential_data_source_class",
    "scientific_question_answered",
    "expected_uncertainty_reduction",
    "dependency_review_required",
    "interpretation_boundary",
]

ALLOWED_STATUSES = {"OBSERVED", "PARTIAL", "MISSING", "UNKNOWN", "NOT_APPLICABLE"}
MISSINGNESS_STATES = {"OBSERVED", "NOT_FOUND", "NOT_QUERIED", "NOT_APPLICABLE", "UNKNOWN"}
UNCERTAINTY_STATES = {
    "SOURCE_LIMITATION",
    "INCOMPLETE_COVERAGE",
    "CONFLICTING_RECORDS",
    "DEPENDENCY_UNCERTAIN",
    "TEMPORAL_UNCERTAINTY",
}
CURRENT_DOMAINS = {
    "DOM_TRANSCRIPTOMIC_DISCOVERY",
    "DOM_DISEASE_ASSOCIATION",
    "DOM_PHARMACOLOGY",
    "DOM_TRACTABILITY",
    "DOM_SAFETY",
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
FORBIDDEN_EXACT_COLUMNS = {
    "score",
    "rank",
    "priority",
    "target_selection",
    "recommendation",
    "therapeutic_direction",
}
ALLOWED_UNTRACKED = {str(SCRIPT), str(PLAN)}
ALLOWED_OUTPUT_PREFIX = f"{OUTPUT_DIR}/"

# These gaps are current project-wide omissions. They describe the evidence
# snapshot, not a property of any gene.
UNIVERSAL_MISSING_DOMAINS = [
    "GENETIC_EVIDENCE",
    "FUNCTIONAL_DEPENDENCY",
    "PERTURBATIONAL_EVIDENCE",
    "CLINICAL_DEVELOPMENT",
    "NORMAL_TISSUE_CONTEXT",
    "ESSENTIALITY",
    "TOXICITY_EVIDENCE",
]
UNIVERSAL_FUTURE_EVIDENCE = [
    "CANCER_GENETIC_EVIDENCE",
    "CRISPR_FUNCTIONAL_DEPENDENCY",
    "PERTURBATIONAL_MECHANISM",
    "TRIAL_LEVEL_CLINICAL_DEVELOPMENT",
    "NORMAL_TISSUE_EXPRESSION",
    "ESSENTIALITY_GENETIC_CONSTRAINT",
    "TOXICITY_EVIDENCE",
]


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
        fail(f"Task #016 requires branch main; observed {branch!r}")
    head = git("rev-parse", "HEAD")
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", TASK015_BASE_COMMIT, head],
        capture_output=True,
        text=True,
        check=False,
    ).returncode != 0:
        fail(f"Task #015 base {TASK015_BASE_COMMIT} is not an ancestor of HEAD {head}")
    remote = git("remote", "get-url", "origin")
    if not re.search(
        r"(?:github\.com[:/])SichengChen-web/luad-target-dossier(?:\.git)?$",
        remote,
    ):
        fail(f"Unexpected origin remote: {remote}")
    if subprocess.run(["git", "diff", "--quiet"], check=False).returncode != 0:
        fail("A previous committed file has an unstaged modification")
    if subprocess.run(
        ["git", "diff", "--cached", "--quiet"], check=False
    ).returncode != 0:
        fail("A previous committed file has a staged modification")
    untracked = git("ls-files", "--others", "--exclude-standard").splitlines()
    unexpected = [
        path
        for path in untracked
        if path not in ALLOWED_UNTRACKED and not path.startswith(ALLOWED_OUTPUT_PREFIX)
    ]
    if unexpected:
        fail("Unexpected untracked files are present: " + ", ".join(unexpected))
    for path, expected in INPUT_HASHES.items():
        if not path.is_file():
            fail(f"Required frozen input is missing: {path}")
        if subprocess.run(
            ["git", "ls-files", "--error-unmatch", str(path)],
            capture_output=True,
            text=True,
            check=False,
        ).returncode != 0:
            fail(f"Required frozen input is not committed: {path}")
        if subprocess.run(
            ["git", "diff", "--quiet", TASK015_BASE_COMMIT, "--", str(path)],
            capture_output=True,
            text=True,
            check=False,
        ).returncode != 0:
            fail(f"Frozen input differs from Task #015 base: {path}")
        observed = file_sha256(path)
        if observed != expected:
            fail(f"SHA256 mismatch for {path}: {observed} != {expected}")
    return {"root": str(root), "branch": branch, "head": head, "remote": remote}


def read_integrated_identity() -> tuple[list[str], dict[str, dict[str, str]]]:
    required = {
        "EnsemblID",
        "U1_DE",
        "U2_effect_supported_DE",
        "S6_sign_flip_vs_S0",
        "sign_concordant_all_S1_S6",
    }
    order: list[str] = []
    selected: dict[str, dict[str, str]] = {}
    with INTEGRATED.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            fail("Integrated registry has no header")
        missing = required.difference(reader.fieldnames)
        if missing:
            fail(f"Integrated registry lacks required fields: {sorted(missing)}")
        for row in reader:
            ensembl_id = row["EnsemblID"]
            if not ensembl_id or ensembl_id in selected:
                fail(f"Empty or duplicate EnsemblID in integrated registry: {ensembl_id!r}")
            order.append(ensembl_id)
            selected[ensembl_id] = {field: row[field] for field in required}
    if len(order) != EXPECTED_GENES:
        fail(f"Integrated registry contains {len(order)} genes; expected {EXPECTED_GENES}")
    if sum(row["U2_effect_supported_DE"] == "TRUE" for row in selected.values()) != EXPECTED_U2:
        fail("Integrated registry U2 count changed")
    return order, selected


def read_claims(
    valid_genes: set[str],
) -> tuple[dict[str, dict[str, dict[str, str]]], dict[str, dict[str, str]]]:
    required = [
        "claim_id", "EnsemblID", "domain_id", "claim_type",
        "claim_description", "claim_status", "supporting_record_count",
        "uncertainty_status",
    ]
    claims_by_gene: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    claims_by_id: dict[str, dict[str, str]] = {}
    with CLAIMS_INPUT.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != required:
            fail("Evidence claim registry schema changed")
        for row in reader:
            claim_id = row["claim_id"]
            ensembl_id = row["EnsemblID"]
            domain_id = row["domain_id"]
            if claim_id in claims_by_id:
                fail(f"Duplicate claim_id: {claim_id}")
            if ensembl_id not in valid_genes:
                fail(f"Claim references unknown EnsemblID: {ensembl_id}")
            if domain_id not in CURRENT_DOMAINS or domain_id in claims_by_gene[ensembl_id]:
                fail(f"Unexpected or duplicate claim domain at {ensembl_id}: {domain_id}")
            if not row["supporting_record_count"].isdigit():
                fail(f"Invalid supporting record count: {claim_id}")
            if row["uncertainty_status"] not in UNCERTAINTY_STATES:
                fail(f"Invalid claim uncertainty: {claim_id}")
            claims_by_gene[ensembl_id][domain_id] = row
            claims_by_id[claim_id] = row
    if len(claims_by_id) != EXPECTED_CLAIMS:
        fail(f"Claim registry contains {len(claims_by_id)} claims; expected {EXPECTED_CLAIMS}")
    if len(claims_by_gene) != EXPECTED_GENES or any(
        set(domain_claims) != CURRENT_DOMAINS for domain_claims in claims_by_gene.values()
    ):
        fail("Every gene must have exactly the five current Task #014 claims")
    return dict(claims_by_gene), claims_by_id


def validate_records(
    claims_by_id: dict[str, dict[str, str]],
) -> dict[str, Counter[str]]:
    required = [
        "record_id", "claim_id", "source_id", "source_record_type",
        "source_record_identifier", "raw_value_reference", "observation_status",
        "missingness_status", "uncertainty_status", "provenance_notes",
    ]
    record_ids: set[str] = set()
    supporting_by_claim: Counter[str] = Counter()
    record_types_by_claim: defaultdict[str, set[str]] = defaultdict(set)
    missingness_counts: Counter[str] = Counter()
    uncertainty_counts: Counter[str] = Counter()
    with RECORDS_INPUT.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != required:
            fail("Evidence record registry schema changed")
        for row in reader:
            record_id = row["record_id"]
            claim_id = row["claim_id"]
            if record_id in record_ids:
                fail(f"Duplicate record_id: {record_id}")
            record_ids.add(record_id)
            if claim_id not in claims_by_id:
                fail(f"Record references invalid claim: {record_id}")
            if row["missingness_status"] not in MISSINGNESS_STATES:
                fail(f"Record has invalid missingness: {record_id}")
            if row["uncertainty_status"] not in UNCERTAINTY_STATES:
                fail(f"Record has invalid uncertainty: {record_id}")
            if row["source_record_type"] in record_types_by_claim[claim_id]:
                fail(f"Duplicate source record type within claim: {claim_id}")
            record_types_by_claim[claim_id].add(row["source_record_type"])
            if row["observation_status"] in SUPPORTING_OBSERVATION_STATUSES:
                supporting_by_claim[claim_id] += 1
            missingness_counts[row["missingness_status"]] += 1
            uncertainty_counts[row["uncertainty_status"]] += 1
    if len(record_ids) != EXPECTED_RECORDS:
        fail(f"Evidence record registry contains {len(record_ids)} rows; expected {EXPECTED_RECORDS}")
    for claim_id, claim in claims_by_id.items():
        if supporting_by_claim[claim_id] != int(claim["supporting_record_count"]):
            fail(f"Supporting-record reconciliation failed for {claim_id}")
    return {"missingness": missingness_counts, "uncertainty": uncertainty_counts}


def validate_missingness_registry(claims_by_id: dict[str, dict[str, str]]) -> dict[str, Counter[str]]:
    required = ["entity_id", "entity_type", "status_type", "status_value", "explanation"]
    claim_statuses: defaultdict[str, dict[str, str]] = defaultdict(dict)
    missingness_counts: Counter[str] = Counter()
    uncertainty_counts: Counter[str] = Counter()
    with MISSINGNESS_INPUT.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != required:
            fail("Missingness/uncertainty registry schema changed")
        for row in reader:
            status_type = row["status_type"]
            status_value = row["status_value"]
            if status_type == "MISSINGNESS":
                if status_value not in MISSINGNESS_STATES:
                    fail(f"Invalid missingness state: {status_value}")
                missingness_counts[status_value] += 1
            elif status_type == "UNCERTAINTY":
                if status_value not in UNCERTAINTY_STATES:
                    fail(f"Invalid uncertainty state: {status_value}")
                uncertainty_counts[status_value] += 1
            else:
                fail(f"Invalid status_type: {status_type}")
            if row["entity_type"] == "EVIDENCE_CLAIM":
                entity_id = row["entity_id"]
                if entity_id not in claims_by_id:
                    fail(f"Missingness registry references invalid claim: {entity_id}")
                if status_type in claim_statuses[entity_id]:
                    fail(f"Duplicate {status_type} state for claim {entity_id}")
                claim_statuses[entity_id][status_type] = status_value
    if len(claim_statuses) != EXPECTED_CLAIMS:
        fail("Missingness registry does not represent every evidence claim")
    for claim_id, states in claim_statuses.items():
        if set(states) != {"MISSINGNESS", "UNCERTAINTY"}:
            fail(f"Claim lacks missingness or uncertainty state: {claim_id}")
        if states["UNCERTAINTY"] != claims_by_id[claim_id]["uncertainty_status"]:
            fail(f"Claim uncertainty differs from missingness registry: {claim_id}")
    return {"missingness": missingness_counts, "uncertainty": uncertainty_counts}


def claim_support(claim: dict[str, str]) -> int:
    return int(claim["supporting_record_count"])


def derive_gap_row(
    ensembl_id: str,
    identity: dict[str, str],
    claims: dict[str, dict[str, str]],
) -> dict[str, str]:
    transcript = claims["DOM_TRANSCRIPTOMIC_DISCOVERY"]
    disease = claims["DOM_DISEASE_ASSOCIATION"]
    pharmacology = claims["DOM_PHARMACOLOGY"]
    tractability = claims["DOM_TRACTABILITY"]
    safety = claims["DOM_SAFETY"]

    u1_positive = identity["U1_DE"] == "TRUE"
    u2_positive = identity["U2_effect_supported_DE"] == "TRUE"
    disease_positive = claim_support(disease) > 0
    expression_conflict = transcript["uncertainty_status"] == "CONFLICTING_RECORDS"

    if u2_positive and disease_positive and not expression_conflict:
        discovery_status = "OBSERVED"
    elif u1_positive or disease_positive:
        discovery_status = "PARTIAL"
    else:
        discovery_status = "MISSING"

    # Dedicated genetic, functional-dependency, and perturbational evidence
    # have not been retrieved in the current snapshot.
    mechanistic_status = "MISSING"

    pharmacology_positive = claim_support(pharmacology) > 0
    tractability_positive = claim_support(tractability) > 0
    # Clinical-development evidence is not yet represented at trial level, so
    # current development characterization cannot be complete.
    development_status = (
        "PARTIAL" if pharmacology_positive or tractability_positive else "MISSING"
    )

    safety_positive = claim_support(safety) > 0
    # Normal-tissue, essentiality, and broader toxicity layers are absent, so
    # a returned safety record yields only partial risk characterization.
    risk_status = "PARTIAL" if safety_positive else "MISSING"

    observed_or_partial = any(
        status in {"OBSERVED", "PARTIAL"}
        for status in (discovery_status, development_status, risk_status)
    )
    # Maturity describes interpretability/coverage, not target quality. It
    # cannot be OBSERVED/complete while the mechanistic domain and multiple
    # development/risk subdomains remain missing.
    maturity_status = "PARTIAL" if observed_or_partial else "MISSING"

    missing_domains = list(UNIVERSAL_MISSING_DOMAINS)
    if not disease_positive:
        missing_domains.append("LUAD_DISEASE_ASSOCIATION")
    if not pharmacology_positive:
        missing_domains.append("PHARMACOLOGY")
    if not tractability_positive:
        missing_domains.append("TRACTABILITY")
    if not safety_positive:
        missing_domains.append("SAFETY_LIABILITY")

    uncertainties = {
        claim["uncertainty_status"] for claim in claims.values()
    }
    uncertainties.add("INCOMPLETE_COVERAGE")

    future_evidence = list(UNIVERSAL_FUTURE_EVIDENCE)
    if expression_conflict:
        future_evidence.insert(0, "INDEPENDENT_LUAD_COHORT_REPLICATION")
    if not disease_positive:
        future_evidence.append("LUAD_DISEASE_ASSOCIATION_DATASOURCE_DETAIL")
    if not pharmacology_positive:
        future_evidence.append("COMPOUND_ACTIVITY_POTENCY_MECHANISM")
    if not tractability_positive:
        future_evidence.append("MODALITY_SPECIFIC_TRACTABILITY")
    if not safety_positive:
        future_evidence.append("TARGET_SAFETY_LIABILITY")

    return {
        "EnsemblID": ensembl_id,
        "discovery_status": discovery_status,
        "mechanistic_status": mechanistic_status,
        "development_status": development_status,
        "risk_status": risk_status,
        "evidence_maturity_status": maturity_status,
        "missing_evidence_domains": "|".join(missing_domains),
        "known_uncertainties": "|".join(sorted(uncertainties)),
        "recommended_future_evidence_type": "|".join(future_evidence),
    }


def build_gap_registry(
    order: list[str],
    integrated: dict[str, dict[str, str]],
    claims_by_gene: dict[str, dict[str, dict[str, str]]],
) -> tuple[list[dict[str, str]], dict[str, Counter[str]]]:
    rows: list[dict[str, str]] = []
    status_counts: dict[str, Counter[str]] = {
        "discovery_status": Counter(),
        "mechanistic_status": Counter(),
        "development_status": Counter(),
        "risk_status": Counter(),
        "evidence_maturity_status": Counter(),
    }
    for ensembl_id in order:
        row = derive_gap_row(ensembl_id, integrated[ensembl_id], claims_by_gene[ensembl_id])
        rows.append(row)
        for field in status_counts:
            status_counts[field][row[field]] += 1
    return rows, status_counts


def percent(count: int, denominator: int) -> str:
    return format(100 * count / denominator, ".6f") if denominator else "NOT_AVAILABLE"


def build_category_counts(
    gap_rows: list[dict[str, str]], status_counts: dict[str, Counter[str]]
) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for field, counts in status_counts.items():
        for status in sorted(ALLOWED_STATUSES):
            count = counts[status]
            output.append(
                {
                    "category_group": field,
                    "category": status,
                    "count": str(count),
                    "denominator": str(EXPECTED_GENES),
                    "percent": percent(count, EXPECTED_GENES),
                }
            )
    for field, category_group in (
        ("missing_evidence_domains", "MISSING_EVIDENCE_DOMAIN"),
        ("known_uncertainties", "KNOWN_UNCERTAINTY"),
        ("recommended_future_evidence_type", "FUTURE_EVIDENCE_TYPE"),
    ):
        counts: Counter[str] = Counter(
            token for row in gap_rows for token in row[field].split("|") if token
        )
        for category, count in sorted(counts.items()):
            output.append(
                {
                    "category_group": category_group,
                    "category": category,
                    "count": str(count),
                    "denominator": str(EXPECTED_GENES),
                    "percent": percent(count, EXPECTED_GENES),
                }
            )
    return output


def build_validation_matrix() -> list[dict[str, str]]:
    return [
        {
            "evidence_gap": "Independent LUAD discovery replication",
            "evidence_layer": "DISCOVERY",
            "potential_data_source_class": "independent LUAD tumour/normal transcriptomic cohort",
            "scientific_question_answered": "Is the direction and magnitude of dysregulation reproducible outside the TCGA-LUAD cohort?",
            "expected_uncertainty_reduction": "CONFLICTING_RECORDS|SOURCE_LIMITATION",
            "dependency_review_required": "Confirm that samples and processing lineage are independent of TCGA/recount3.",
            "interpretation_boundary": "Replication strengthens an expression association but does not establish causality.",
        },
        {
            "evidence_gap": "LUAD disease-association datasource detail",
            "evidence_layer": "DISCOVERY",
            "potential_data_source_class": "record-level disease-association database evidence and source literature",
            "scientific_question_answered": "Which specific source records support or fail to support the target-LUAD association?",
            "expected_uncertainty_reduction": "SOURCE_LIMITATION|DEPENDENCY_UNCERTAIN",
            "dependency_review_required": "Deduplicate publications and upstream records already represented in Open Targets.",
            "interpretation_boundary": "Association evidence does not by itself identify a causal mechanism.",
        },
        {
            "evidence_gap": "Cancer genetic evidence",
            "evidence_layer": "MECHANISTIC",
            "potential_data_source_class": "somatic mutation/copy-number and germline association datasets",
            "scientific_question_answered": "Do tumour-acquired or inherited genetic observations support a causal role in LUAD biology?",
            "expected_uncertainty_reduction": "INCOMPLETE_COVERAGE|SOURCE_LIMITATION",
            "dependency_review_required": "Determine whether genetic and expression evidence share TCGA cases or Open Targets source records.",
            "interpretation_boundary": "Genetic association or alteration does not automatically predict pharmacological modulation.",
        },
        {
            "evidence_gap": "Functional dependency",
            "evidence_layer": "MECHANISTIC",
            "potential_data_source_class": "CRISPR dependency and cancer-cell fitness datasets",
            "scientific_question_answered": "Does target perturbation affect LUAD-relevant cancer-cell fitness?",
            "expected_uncertainty_reduction": "INCOMPLETE_COVERAGE|SOURCE_LIMITATION",
            "dependency_review_required": "Track cell-line lineage, assay version, guide quality, and overlap with external aggregators.",
            "interpretation_boundary": "Cell-line dependency does not establish patient benefit or safe therapeutic direction.",
        },
        {
            "evidence_gap": "Perturbational mechanism",
            "evidence_layer": "MECHANISTIC",
            "potential_data_source_class": "genetic or pharmacological perturbation experiments",
            "scientific_question_answered": "Does controlled modulation change a LUAD-relevant phenotype in the expected direction?",
            "expected_uncertainty_reduction": "SOURCE_LIMITATION|CONFLICTING_RECORDS",
            "dependency_review_required": "Separate independent experiments from reused cell lines, compounds, and publications.",
            "interpretation_boundary": "Model-specific perturbation results require replication and direction-of-action review.",
        },
        {
            "evidence_gap": "Compound activity, potency, and mechanism",
            "evidence_layer": "DEVELOPMENT",
            "potential_data_source_class": "compound-target activity databases and primary assay records",
            "scientific_question_answered": "Are there selective compounds with interpretable potency and mechanism against the target?",
            "expected_uncertainty_reduction": "INCOMPLETE_COVERAGE|DEPENDENCY_UNCERTAIN",
            "dependency_review_required": "Deduplicate assays, compounds, mechanisms, and ChEMBL/Open Targets overlap.",
            "interpretation_boundary": "Activity records do not prove efficacy, selectivity in vivo, or LUAD relevance.",
        },
        {
            "evidence_gap": "Modality-specific tractability",
            "evidence_layer": "DEVELOPMENT",
            "potential_data_source_class": "structural, ligandability, antibody-accessibility, and degrader evidence",
            "scientific_question_answered": "Which therapeutic modalities have direct feasibility evidence for the target?",
            "expected_uncertainty_reduction": "INCOMPLETE_COVERAGE|SOURCE_LIMITATION",
            "dependency_review_required": "Identify ChEMBL and clinical-precedence records reused by tractability frameworks.",
            "interpretation_boundary": "Tractability does not establish biological appropriateness or clinical success.",
        },
        {
            "evidence_gap": "Trial-level clinical development",
            "evidence_layer": "DEVELOPMENT",
            "potential_data_source_class": "clinical trial registries and curated development records",
            "scientific_question_answered": "Has target modulation reached human investigation, for which intervention and disease context?",
            "expected_uncertainty_reduction": "INCOMPLETE_COVERAGE|TEMPORAL_UNCERTAINTY",
            "dependency_review_required": "Deduplicate trials, interventions, sponsors, and Open Targets clinical-precedence records.",
            "interpretation_boundary": "Clinical investigation is development precedent, not proof of target validity or efficacy.",
        },
        {
            "evidence_gap": "Normal tissue context",
            "evidence_layer": "RISK",
            "potential_data_source_class": "normal tissue expression and protein-localization datasets",
            "scientific_question_answered": "Where is the target normally expressed and what physiological exposure context exists?",
            "expected_uncertainty_reduction": "INCOMPLETE_COVERAGE|SOURCE_LIMITATION",
            "dependency_review_required": "Track tissue, cell-type, assay, donor, and protein-versus-RNA measurement lineage.",
            "interpretation_boundary": "Normal expression suggests context for investigation but does not prove toxicity.",
        },
        {
            "evidence_gap": "Essentiality and genetic constraint",
            "evidence_layer": "RISK",
            "potential_data_source_class": "human genetic constraint and normal/cancer essentiality datasets",
            "scientific_question_answered": "Is target loss tolerated, and is essentiality context-specific?",
            "expected_uncertainty_reduction": "INCOMPLETE_COVERAGE|SOURCE_LIMITATION",
            "dependency_review_required": "Separate germline constraint, normal-cell essentiality, and cancer dependency lineages.",
            "interpretation_boundary": "Genetic intolerance does not directly quantify pharmacological safety or dose tolerance.",
        },
        {
            "evidence_gap": "Target and compound toxicity evidence",
            "evidence_layer": "RISK",
            "potential_data_source_class": "curated safety databases, toxicology assays, adverse-event data, and literature",
            "scientific_question_answered": "What on-target or compound-related toxicity observations exist and in what exposure context?",
            "expected_uncertainty_reduction": "INCOMPLETE_COVERAGE|TEMPORAL_UNCERTAINTY|SOURCE_LIMITATION",
            "dependency_review_required": "Separate on-target from off-target effects and deduplicate reports, studies, compounds, and publications.",
            "interpretation_boundary": "Adverse-event associations and report counts do not automatically establish causality.",
        },
    ]


def write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    if not rows:
        fail(f"Refusing to write empty CSV: {path}")
    if any(list(row) != columns for row in rows):
        fail(f"Output field order mismatch for {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def validate_outputs(
    order: list[str],
    gap_rows: list[dict[str, str]],
    category_rows: list[dict[str, str]],
    matrix_rows: list[dict[str, str]],
) -> dict[str, Any]:
    for name, columns in (
        ("evidence gap registry", GAP_COLUMNS),
        ("category counts", CATEGORY_COLUMNS),
        ("validation strategy matrix", VALIDATION_COLUMNS),
    ):
        forbidden = FORBIDDEN_EXACT_COLUMNS.intersection(column.lower() for column in columns)
        if forbidden:
            fail(f"{name} contains forbidden exact columns: {sorted(forbidden)}")
    if len(gap_rows) != EXPECTED_GENES:
        fail(f"Gap registry contains {len(gap_rows)} rows; expected {EXPECTED_GENES}")
    identifiers = [row["EnsemblID"] for row in gap_rows]
    if identifiers != order or len(set(identifiers)) != EXPECTED_GENES:
        fail("Gap registry did not preserve unique integrated EnsemblID order")
    status_fields = [
        "discovery_status", "mechanistic_status", "development_status",
        "risk_status", "evidence_maturity_status",
    ]
    for row in gap_rows:
        for field in status_fields:
            if row[field] not in ALLOWED_STATUSES:
                fail(f"Invalid {field} at {row['EnsemblID']}: {row[field]}")
        if any(row[field] == "" for field in GAP_COLUMNS):
            fail(f"Gap registry contains blank value at {row['EnsemblID']}")
        missing = set(row["missing_evidence_domains"].split("|"))
        if not set(UNIVERSAL_MISSING_DOMAINS).issubset(missing):
            fail(f"Universal current evidence gap missing at {row['EnsemblID']}")
        uncertainties = set(row["known_uncertainties"].split("|"))
        if not uncertainties.issubset(UNCERTAINTY_STATES) or "INCOMPLETE_COVERAGE" not in uncertainties:
            fail(f"Invalid/incomplete uncertainty representation at {row['EnsemblID']}")
    if not category_rows or not matrix_rows:
        fail("Category counts or validation matrix is empty")
    if any(value == "" for row in category_rows + matrix_rows for value in row.values()):
        fail("Category counts or validation matrix contains blank values")
    return {
        "row_count": len(gap_rows),
        "unique_ensembl_id_count": len(set(identifiers)),
        "category_count_rows": len(category_rows),
        "validation_strategy_rows": len(matrix_rows),
        "missingness_preserved": True,
        "scores_generated": False,
        "ranking_generated": False,
        "target_selection_generated": False,
        "therapeutic_recommendations_generated": False,
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


def write_summary(
    status_counts: dict[str, Counter[str]],
    gap_rows: list[dict[str, str]],
    validation: dict[str, Any],
) -> None:
    lines = [
        "# Task #016 evidence gap analysis summary",
        "",
        f"**Genes evaluated:** {len(gap_rows):,}  ",
        f"**Unique EnsemblIDs:** {validation['unique_ensembl_id_count']:,}  ",
        f"**Validation-strategy entries:** {validation['validation_strategy_rows']}  ",
        "**Scores, rankings, candidate selections, or therapeutic recommendations created:** No",
        "",
        "## Status results",
        "",
    ]
    display_names = {
        "discovery_status": "Discovery evidence",
        "mechanistic_status": "Mechanistic evidence",
        "development_status": "Therapeutic development evidence",
        "risk_status": "Risk evidence",
        "evidence_maturity_status": "Evidence maturity",
    }
    status_rows: list[list[Any]] = []
    for field, name in display_names.items():
        for status in sorted(ALLOWED_STATUSES):
            count = status_counts[field][status]
            if count:
                status_rows.append([name, status, count, percent(count, EXPECTED_GENES)])
    lines.extend(markdown_table(["Dimension", "Status", "Genes", "Percent"], status_rows))
    lines.extend(
        [
            "",
            "## Project-wide gaps",
            "",
            "Dedicated genetic, functional-dependency, perturbational, trial-level clinical-development, normal-tissue, essentiality, and broader toxicity evidence are missing for every current profile. These are project evidence gaps, not gene-level negative findings.",
            "",
            "Because dedicated mechanistic evidence is absent, no gene is classified as having complete mechanistic characterization. Because clinical-development and multiple risk subdomains are absent, development and risk can be at most `PARTIAL` in this snapshot. Evidence maturity likewise describes structural interpretability and cannot be complete under the current coverage.",
            "",
            "## Meaning of the future-evidence field",
            "",
            "`recommended_future_evidence_type` identifies evidence classes that could reduce the documented uncertainty for a profile. It is not a target recommendation, does not select genes, and does not define an order in which genes should be investigated. Pipe-delimited values are a gap inventory, not a ranking.",
            "",
            "## Validation strategy",
            "",
            "The validation matrix links each major gap to an appropriate data-source class, the scientific question it could answer, the uncertainty categories it could reduce, dependency checks, and an interpretation boundary. It does not authorize retrieval, experiments, or target progression.",
            "",
            "## Missingness boundary",
            "",
            "`MISSING` means the current evidence profile lacks the required evidence class. It does not mean the underlying biological property is absent. In particular:",
            "",
            "- no functional-dependency data does not imply lack of dependency;",
            "- no compound/mechanism record does not prove undruggability;",
            "- no trial-level evidence does not prove lack of therapeutic potential;",
            "- no safety-liability record does not imply safety;",
            "- no normal-tissue or essentiality evidence does not imply low translational risk.",
            "",
            "## Important limitations",
            "",
            "- Statuses describe evidence availability and bounded current claims, not target quality.",
            "- Discovery `OBSERVED` requires effect-supported DE, returned LUAD association evidence, and no expression sign-conflict flag; it still does not establish causality.",
            "- Development and risk statuses intentionally remain partial when only some subdomains are observed.",
            "- The same source can contribute to several fields; Task #013/#014 dependencies must be reviewed before future aggregation.",
            "- External evidence is temporally versioned and public-database coverage is incomplete.",
            "",
            "## Validation",
            "",
            "All frozen hashes matched. The integrated registry retained 29,606 unique EnsemblIDs and 14,064 U2 genes. Every gene retained five valid Task #014 claims, all 207,242 evidence records reconciled to their claims, claim missingness/uncertainty states remained consistent, output order was preserved, and no numerical score or ranking field was generated.",
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
    output_validation: dict[str, Any],
) -> None:
    metadata = {
        "task": "016",
        "purpose": "descriptive evidence gap analysis and validation strategy",
        "started_at_utc": started.isoformat(),
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "git_branch": repo["branch"],
        "git_head": repo["head"],
        "git_origin": repo["remote"],
        "frozen_task015_base_commit": TASK015_BASE_COMMIT,
        "network_access": "NOT_USED",
        "packages_installed_or_updated": "FALSE",
        "previous_committed_files_modified": "FALSE",
        "scoring_generated": "FALSE",
        "ranking_generated": "FALSE",
        "gene_prioritization_generated": "FALSE",
        "target_selection_generated": "FALSE",
        "therapeutic_recommendations_generated": "FALSE",
        "frozen_input_sha256": {str(path): file_sha256(path) for path in INPUT_HASHES},
        "input_validation": input_validation,
        "output_validation": output_validation,
        "script_sha256": file_sha256(SCRIPT),
        "plan_sha256": file_sha256(PLAN),
        "output_sha256": {
            str(GAP_REGISTRY): file_sha256(GAP_REGISTRY),
            str(CATEGORY_COUNTS): file_sha256(CATEGORY_COUNTS),
            str(VALIDATION_MATRIX): file_sha256(VALIDATION_MATRIX),
            str(SUMMARY): file_sha256(SUMMARY),
        },
    }
    SESSION.write_text("\n".join(flatten("", metadata)) + "\n", encoding="utf-8")


def main() -> None:
    started = datetime.now(timezone.utc)
    repo = validate_repository()
    order, integrated = read_integrated_identity()
    claims_by_gene, claims_by_id = read_claims(set(order))
    record_validation = validate_records(claims_by_id)
    missingness_validation = validate_missingness_registry(claims_by_id)

    gap_rows, status_counts = build_gap_registry(order, integrated, claims_by_gene)
    category_rows = build_category_counts(gap_rows, status_counts)
    matrix_rows = build_validation_matrix()
    output_validation = validate_outputs(order, gap_rows, category_rows, matrix_rows)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(GAP_REGISTRY, gap_rows, GAP_COLUMNS)
    write_csv(CATEGORY_COUNTS, category_rows, CATEGORY_COLUMNS)
    write_csv(VALIDATION_MATRIX, matrix_rows, VALIDATION_COLUMNS)
    write_summary(status_counts, gap_rows, output_validation)
    input_validation = {
        "integrated_row_count": len(order),
        "integrated_unique_ensembl_id_count": len(set(order)),
        "integrated_u2_count": sum(
            row["U2_effect_supported_DE"] == "TRUE" for row in integrated.values()
        ),
        "claim_count": len(claims_by_id),
        "record_count": EXPECTED_RECORDS,
        "record_missingness_counts": dict(sorted(record_validation["missingness"].items())),
        "record_uncertainty_counts": dict(sorted(record_validation["uncertainty"].items())),
        "claim_missingness_counts": dict(sorted(missingness_validation["missingness"].items())),
        "claim_uncertainty_counts": dict(sorted(missingness_validation["uncertainty"].items())),
    }
    write_session(started, repo, input_validation, output_validation)

    print("Created files:")
    for path in (GAP_REGISTRY, CATEGORY_COUNTS, VALIDATION_MATRIX, SUMMARY, SESSION):
        print(f"- {path}")
    print(f"Gap registry rows: {len(gap_rows)}")
    for field in (
        "discovery_status", "mechanistic_status", "development_status",
        "risk_status", "evidence_maturity_status",
    ):
        rendered = "|".join(
            f"{key}={status_counts[field][key]}" for key in sorted(status_counts[field])
        )
        print(f"{field}: {rendered}")
    print("All Task #016 assertions passed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
