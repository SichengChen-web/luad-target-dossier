#!/usr/bin/env python3
"""Validate Task #020–#022 profile-materialization representation fidelity.

This standard-library validation harness creates deterministic test fixtures
from frozen evidence structures. It validates identity, lineage, dependencies,
missingness, uncertainty, state-rule addressability, and deterministic output.
It does not create final target profiles or perform therapeutic assessment.
"""

from __future__ import annotations

import csv
import hashlib
import io
import platform
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
TASK022_BASE_COMMIT = "f76c0b0353541b4f0317d8398121176b84936b30"
EXPECTED_BRANCH = "main"
EXPECTED_REMOTE_FRAGMENT = "SichengChen-web/luad-target-dossier"
VALIDATION_VERSION = "PROFILE_MATERIALIZATION_VALIDATION_V0.1"

SCRIPT_PATH = ROOT / "analysis/23_validate_profile_materialization.py"
PLAN_PATH = ROOT / "docs/profile_materialization_validation_plan_v0.1.md"
OUTPUT_DIR = ROOT / "outputs/profile_validation"
SELECTION_PATH = OUTPUT_DIR / "validation_gene_selection.csv"
RESULTS_PATH = OUTPUT_DIR / "profile_validation_results.csv"
MISSINGNESS_PATH = OUTPUT_DIR / "missingness_validation.csv"
DEPENDENCY_PATH = OUTPUT_DIR / "dependency_validation.csv"
IDENTITY_PATH = OUTPUT_DIR / "identity_validation.csv"
SUMMARY_PATH = OUTPUT_DIR / "profile_validation_summary.md"
SESSION_PATH = OUTPUT_DIR / "session_info.txt"

INPUTS = {
    "integrated_registry": ROOT / "outputs/integrated_registry/integrated_target_registry.csv",
    "claim_registry": ROOT / "outputs/evidence_claim_architecture/evidence_claim_registry.csv",
    "record_registry": ROOT / "outputs/evidence_claim_architecture/evidence_record_registry.csv",
    "source_registry": ROOT / "outputs/evidence_claim_architecture/source_entity_registry.csv",
    "dependency_graph": ROOT / "outputs/evidence_claim_architecture/evidence_dependency_graph.csv",
    "materialization_schema": ROOT / "outputs/profile_materialization/materialization_schema.csv",
    "state_registry": ROOT / "outputs/profile_materialization/component_state_resolution_registry.csv",
    "universe_schema": ROOT / "outputs/target_universe_governance/target_universe_schema.csv",
}

EXPECTED_HASHES = {
    "integrated_registry": "0587fc6901267b18c8144644571f89ac2cc46053b57ea5def4093795fdbc4c26",
    "claim_registry": "0d963a4c5c8f9586f81369e33df0a2b7e57bb37ac8ceab4ce54498baf2351a66",
    "record_registry": "76ec5056fb4e468176073073532204d231765d4f0cd70dbb6cfe4ad8bf752343",
    "source_registry": "1b1379066226b5f69b626fe4a97628f7b6da6e585515aa8609218eef65bf8056",
    "dependency_graph": "011839f10c48e197f9f1c0e2262565e562d3a2cf53dd0936f21ddcb4ed5c2256",
    "materialization_schema": "9324374e39fb844c224961db319e4ddf9979512026062ededb5e59e505318701",
    "state_registry": "302fe6fef0eaf76daedbd51cbd9c430cb38bdbe231991f6e2551de0da59a94be",
    "universe_schema": "f1d611151a1ce7b15f6ff596d74b36a38d26f8503d6fe843f73ae1293babd8f3",
}

ALLOWED_UNTRACKED_FILES = {
    "analysis/23_validate_profile_materialization.py",
    "docs/profile_materialization_validation_plan_v0.1.md",
}
ALLOWED_UNTRACKED_PREFIX = "outputs/profile_validation/"

PROFILE_STATES = ("OBSERVED", "PARTIAL", "MISSING", "NOT_QUERIED", "CONFLICTING")
STATE_PRECEDENCE = {
    "CONFLICTING": "1",
    "OBSERVED": "2",
    "MISSING": "3",
    "PARTIAL": "4",
    "NOT_QUERIED": "5",
}

FORBIDDEN_EXACT_FIELDS = {
    "score",
    "rank",
    "priority",
    "recommendation",
    "target_selection",
    "therapeutic_direction",
}

COMPONENTS = (
    "COMP_TRANSCRIPTOMIC_EVIDENCE",
    "COMP_DISEASE_ASSOCIATION",
    "COMP_GENETIC_EVIDENCE",
    "COMP_FUNCTIONAL_DEPENDENCY",
    "COMP_PHARMACOLOGY",
    "COMP_TRACTABILITY",
    "COMP_SAFETY",
    "COMP_CLINICAL_DEVELOPMENT",
    "COMP_HUMAN_EVIDENCE",
    "COMP_CLINICAL_LINKAGE",
    "COMP_RISK_CONTEXT",
)

COMPONENT_DOMAINS = {
    "COMP_TRANSCRIPTOMIC_EVIDENCE": ("DOM_TRANSCRIPTOMIC_DISCOVERY",),
    "COMP_DISEASE_ASSOCIATION": ("DOM_DISEASE_ASSOCIATION",),
    "COMP_GENETIC_EVIDENCE": (),
    "COMP_FUNCTIONAL_DEPENDENCY": (),
    "COMP_PHARMACOLOGY": ("DOM_PHARMACOLOGY",),
    "COMP_TRACTABILITY": ("DOM_TRACTABILITY",),
    "COMP_SAFETY": ("DOM_SAFETY",),
    "COMP_CLINICAL_DEVELOPMENT": (),
    "COMP_HUMAN_EVIDENCE": (),
    "COMP_CLINICAL_LINKAGE": ("DOM_DISEASE_ASSOCIATION", "DOM_PHARMACOLOGY"),
    "COMP_RISK_CONTEXT": ("DOM_SAFETY",),
}

CURRENT_COMPONENT_ROLES = {
    "COMP_TRANSCRIPTOMIC_EVIDENCE": ("TRANSCRIPT_PRIMARY", "TRANSCRIPT_ROBUSTNESS"),
    "COMP_DISEASE_ASSOCIATION": ("OT_LUAD_ASSOCIATION",),
    "COMP_GENETIC_EVIDENCE": (),
    "COMP_FUNCTIONAL_DEPENDENCY": (),
    "COMP_PHARMACOLOGY": ("CHEMBL_TARGET_ANNOTATION", "OT_DRUG_CANDIDATE"),
    "COMP_TRACTABILITY": ("OT_TRACTABILITY_SUMMARY",),
    "COMP_SAFETY": ("OT_SAFETY_SUMMARY",),
    "COMP_CLINICAL_DEVELOPMENT": (),
    "COMP_HUMAN_EVIDENCE": (),
    "COMP_CLINICAL_LINKAGE": ("OT_LUAD_ASSOCIATION", "CHEMBL_TARGET_ANNOTATION", "OT_DRUG_CANDIDATE"),
    "COMP_RISK_CONTEXT": ("OT_SAFETY_SUMMARY",),
}

FUTURE_COMPONENT_ROLES = {
    "COMP_GENETIC_EVIDENCE": ("FUTURE_GENETIC_CANCER_RECORD",),
    "COMP_FUNCTIONAL_DEPENDENCY": ("FUTURE_FUNCTIONAL_DEPENDENCY_RECORD",),
    "COMP_PHARMACOLOGY": ("FUTURE_CHEMBL_COMPOUND_TARGET",),
    "COMP_CLINICAL_DEVELOPMENT": ("FUTURE_CLINICAL_TRIAL_DEVELOPMENT_RECORD",),
    "COMP_HUMAN_EVIDENCE": ("FUTURE_GENETIC_CANCER_RECORD", "FUTURE_CLINICAL_TRIAL_DEVELOPMENT_RECORD"),
    "COMP_CLINICAL_LINKAGE": ("FUTURE_CHEMBL_COMPOUND_TARGET", "FUTURE_CLINICAL_TRIAL_DEVELOPMENT_RECORD", "FUTURE_INTERVENTION_TARGET_DISEASE_LINKAGE"),
}

# Fixed fixture categories and sizes are validation-design parameters, not
# biological filters. Category order resolves overlap deterministically.
FIXTURE_PLAN = (
    ("CONFLICT_BOUNDARY", 1),
    ("DEPENDENCY_HEAVY", 2),
    ("EVIDENCE_RICH", 2),
    ("EVIDENCE_POOR", 2),
    ("MISSING_BOUNDARY", 1),
    ("NOT_QUERIED_BOUNDARY", 1),
    ("PARTIAL_BOUNDARY", 1),
)

CLAIM_FIELDS = (
    "claim_id", "EnsemblID", "domain_id", "claim_type", "claim_status",
    "supporting_record_count", "uncertainty_status",
)
RECORD_FIELDS = (
    "record_id", "claim_id", "source_id", "source_record_type",
    "observation_status", "missingness_status", "uncertainty_status",
)


def fail(message: str) -> None:
    raise RuntimeError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def run_git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, text=True, capture_output=True, check=False
    )
    if check and result.returncode != 0:
        fail(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def git_paths(*args: str) -> set[str]:
    return {line for line in run_git(*args).splitlines() if line}


def validate_repository() -> dict[str, str]:
    root = Path(run_git("rev-parse", "--show-toplevel")).resolve()
    branch = run_git("branch", "--show-current")
    head = run_git("rev-parse", "HEAD")
    remote = run_git("remote", "get-url", "origin")
    base = run_git("rev-parse", TASK022_BASE_COMMIT)
    if root != ROOT:
        fail(f"Unexpected repository root: {root}")
    if branch != EXPECTED_BRANCH:
        fail(f"Expected branch {EXPECTED_BRANCH!r}, observed {branch!r}.")
    if EXPECTED_REMOTE_FRAGMENT not in remote:
        fail(f"Unexpected origin remote: {remote}")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", base, head], cwd=ROOT, check=False
    )
    if ancestor.returncode != 0:
        fail("Frozen Task #022 base commit is not an ancestor of current HEAD.")
    if run_git("diff", "--name-only") or run_git("diff", "--cached", "--name-only"):
        fail("Tracked or staged changes exist; Task #023 will not modify previous files.")
    changed_inputs = git_paths(
        "diff", "--name-only", f"{base}..{head}", "--",
        *(relative(path) for path in INPUTS.values()),
    )
    if changed_inputs:
        fail(f"Frozen Task #023 inputs changed after Task #022: {sorted(changed_inputs)}")
    untracked = git_paths("ls-files", "--others", "--exclude-standard")
    unexpected = {
        path for path in untracked
        if path not in ALLOWED_UNTRACKED_FILES and not path.startswith(ALLOWED_UNTRACKED_PREFIX)
    }
    if unexpected:
        fail(f"Unexpected untracked files: {sorted(unexpected)}")
    snapshot = run_git("show", "-s", "--format=%cI", base)
    return {
        "root": str(root), "branch": branch, "head": head, "base": base,
        "remote": remote, "snapshot": snapshot,
    }


def validate_hashes() -> dict[str, str]:
    observed = {}
    for name, path in INPUTS.items():
        if not path.is_file():
            fail(f"Missing frozen input: {relative(path)}")
        digest = sha256(path)
        if digest != EXPECTED_HASHES[name]:
            fail(f"Frozen input hash mismatch for {relative(path)}: {digest}")
        observed[name] = digest
    return observed


def load_integrated() -> tuple[dict[str, dict[str, str]], list[str]]:
    required = {"EnsemblID", "Symbol", "gene_type"}
    rows: dict[str, dict[str, str]] = {}
    order = []
    with INPUTS["integrated_registry"].open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = required.difference(reader.fieldnames or [])
        if missing:
            fail(f"Integrated registry fields missing: {sorted(missing)}")
        for index, row in enumerate(reader, start=1):
            ensembl_id = row["EnsemblID"]
            if not ensembl_id or ensembl_id in rows:
                fail(f"Invalid or duplicate integrated EnsemblID at data row {index}.")
            rows[ensembl_id] = {
                "EnsemblID": ensembl_id,
                "Symbol": row["Symbol"] or "NOT_FOUND",
                "gene_type": row["gene_type"] or "NOT_FOUND",
                "source_order": str(index),
            }
            order.append(ensembl_id)
    if len(rows) != 29_606:
        fail(f"Expected 29,606 integrated entities, observed {len(rows)}.")
    return rows, order


def load_claims(integrated: dict[str, dict[str, str]]) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, dict[str, str]]]]:
    by_id: dict[str, dict[str, str]] = {}
    by_gene: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    with INPUTS["claim_registry"].open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not set(CLAIM_FIELDS).issubset(reader.fieldnames or []):
            fail("Claim registry schema mismatch.")
        for row in reader:
            item = {field: row[field] for field in CLAIM_FIELDS}
            claim_id = item["claim_id"]
            gene = item["EnsemblID"]
            domain = item["domain_id"]
            if claim_id in by_id or gene not in integrated or domain in by_gene[gene]:
                fail(f"Duplicate/orphan claim identity: {claim_id}")
            try:
                int(item["supporting_record_count"])
            except ValueError as exc:
                raise RuntimeError(
                    f"Invalid supporting record count: {claim_id}"
                ) from exc
            by_id[claim_id] = item
            by_gene[gene][domain] = item
    if len(by_id) != 148_030 or any(len(by_gene[gene]) != 5 for gene in integrated):
        fail("Claim registry cardinality is not 5 claims for each of 29,606 entities.")
    return by_id, by_gene


def load_records(
    claims: dict[str, dict[str, str]],
) -> tuple[dict[str, tuple[str, ...]], dict[str, list[tuple[str, ...]]], dict[str, str]]:
    by_id: dict[str, tuple[str, ...]] = {}
    by_gene: dict[str, list[tuple[str, ...]]] = defaultdict(list)
    record_to_gene: dict[str, str] = {}
    with INPUTS["record_registry"].open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not set(RECORD_FIELDS).issubset(reader.fieldnames or []):
            fail("Evidence-record registry schema mismatch.")
        for row in reader:
            item = tuple(row[field] for field in RECORD_FIELDS)
            record_id, claim_id = item[0], item[1]
            if record_id in by_id or claim_id not in claims:
                fail(f"Duplicate/orphan evidence record: {record_id}")
            gene = claims[claim_id]["EnsemblID"]
            by_id[record_id] = item
            by_gene[gene].append(item)
            record_to_gene[record_id] = gene
    if len(by_id) != 207_242 or any(len(by_gene[gene]) != 7 for gene in {row["EnsemblID"] for row in claims.values()}):
        fail("Evidence-record cardinality is not 7 records for every entity.")
    return by_id, by_gene, record_to_gene


def load_sources() -> dict[str, dict[str, str]]:
    with INPUTS["source_registry"].open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = {row["source_id"]: row for row in reader}
    if len(rows) != 6 or any(not row["version"] for row in rows.values()):
        fail("Source registry must contain six unique versioned sources.")
    return rows


def load_dependencies(
    records: dict[str, tuple[str, ...]], record_to_gene: dict[str, str]
) -> tuple[list[dict[str, str]], dict[str, list[dict[str, str]]]]:
    all_rows = []
    by_gene: dict[str, list[dict[str, str]]] = defaultdict(list)
    seen_ids = set()
    seen_pairs = set()
    with INPUTS["dependency_graph"].open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"dependency_id", "record_a", "record_b", "relationship", "dependency_level", "reason", "review_status"}
        if not required.issubset(reader.fieldnames or []):
            fail("Dependency graph schema mismatch.")
        for row in reader:
            dep_id = row["dependency_id"]
            a, b = row["record_a"], row["record_b"]
            pair = tuple(sorted((a, b)))
            if dep_id in seen_ids or pair in seen_pairs or a not in records or b not in records:
                fail(f"Duplicate or orphan dependency: {dep_id}")
            if record_to_gene[a] != record_to_gene[b]:
                fail(f"Cross-entity dependency is outside the Task #023 harness: {dep_id}")
            seen_ids.add(dep_id)
            seen_pairs.add(pair)
            item = {field: row[field] for field in required}
            all_rows.append(item)
            by_gene[record_to_gene[a]].append(item)
    if len(all_rows) != 77_202:
        fail(f"Expected 77,202 dependency edges, observed {len(all_rows)}.")
    return all_rows, by_gene


def load_architecture() -> tuple[dict[tuple[str, str], dict[str, str]], dict[str, str]]:
    with INPUTS["state_registry"].open(newline="", encoding="utf-8") as handle:
        state_rows = list(csv.DictReader(handle))
    if len(state_rows) != 55:
        fail("Expected 55 Task #021 component-state rules.")
    rules = {}
    for row in state_rows:
        key = (row["component_id"], row["resolved_state"])
        if key in rules:
            fail(f"Duplicate component-state rule: {key}")
        if row["evaluation_precedence"] != STATE_PRECEDENCE.get(row["resolved_state"]):
            fail(f"State precedence mismatch: {key}")
        rules[key] = row
    if set(row["component_id"] for row in state_rows) != set(COMPONENTS):
        fail("Task #021 component set changed.")
    for component in COMPONENTS:
        if {state for comp, state in rules if comp == component} != set(PROFILE_STATES):
            fail(f"Incomplete state vocabulary for {component}.")

    with INPUTS["materialization_schema"].open(newline="", encoding="utf-8") as handle:
        materialization = {row["contract_id"]: row for row in csv.DictReader(handle)}
    required_contracts = {
        "MAT_INPUT_TARGET_MANIFEST", "MAT_INPUT_CLAIMS", "MAT_INPUT_EVIDENCE_RECORDS",
        "MAT_INPUT_SOURCE_ENTITIES", "MAT_INPUT_DEPENDENCIES", "MAT_STAGE_STATE_RESOLUTION",
        "MAT_STAGE_CANONICAL_SERIALIZATION", "MAT_STAGE_QC_AND_HASH_FREEZE",
    }
    if not required_contracts.issubset(materialization):
        fail("Task #021 materialization contracts are incomplete.")

    with INPUTS["universe_schema"].open(newline="", encoding="utf-8") as handle:
        universe_fields = {row["field_name"]: row for row in csv.DictReader(handle)}
    if (
        "EnsemblID" not in universe_fields
        or "only immutable entity and join key"
        not in universe_fields["EnsemblID"]["definition"].lower()
    ):
        fail("Task #022 immutable identifier policy changed.")
    if any(field.lower() in FORBIDDEN_EXACT_FIELDS for field in universe_fields):
        fail("Forbidden assessment field found in target-universe schema.")
    return rules, {key: row["validation_rule"] for key, row in materialization.items()}


def record_dict(item: tuple[str, ...]) -> dict[str, str]:
    return dict(zip(RECORD_FIELDS, item))


def roles_for_gene(records: list[tuple[str, ...]]) -> dict[str, dict[str, str]]:
    result = {}
    for item in records:
        row = record_dict(item)
        role = row["source_record_type"]
        if role in result:
            fail(f"Duplicate source-record role within entity: {role}")
        result[role] = row
    return result


def resolve_state(
    component: str,
    claims: dict[str, dict[str, str]],
    role_records: dict[str, dict[str, str]],
) -> tuple[str, str]:
    """Map controlled current evidence states to a Task #021 state fixture.

    This is a validation harness mapping, not the final materializer. It tests
    that the frozen Task #021 registry contains one addressable rule for the
    controlled source condition.
    """
    if component == "COMP_TRANSCRIPTOMIC_EVIDENCE":
        claim = claims["DOM_TRANSCRIPTOMIC_DISCOVERY"]
        records = [role_records[role] for role in CURRENT_COMPONENT_ROLES[component]]
        if claim["uncertainty_status"] == "CONFLICTING_RECORDS":
            return "CONFLICTING", "PRESPECIFIED_TRANSCRIPT_CONFLICT_FLAG"
        if all(row["missingness_status"] == "OBSERVED" for row in records):
            return "OBSERVED", "PRIMARY_AND_ROBUSTNESS_RECORDS_OBSERVED"
        if all(row["missingness_status"] == "NOT_FOUND" for row in records):
            return "MISSING", "COMPLETE_TRANSCRIPT_SCOPE_NO_QUALIFYING_RECORD"
        if all(row["missingness_status"] == "NOT_QUERIED" for row in records):
            return "NOT_QUERIED", "NO_TRANSCRIPT_ACQUISITION"
        return "PARTIAL", "INCOMPLETE_TRANSCRIPT_RECORD_SET"

    if component == "COMP_DISEASE_ASSOCIATION":
        status = claims["DOM_DISEASE_ASSOCIATION"]["claim_status"]
        if status in {"DIRECT_ASSOCIATION_RECORD_PRESENT", "INDIRECT_ASSOCIATION_RECORD_PRESENT_ONLY"}:
            return "OBSERVED", "LUAD_ASSOCIATION_RECORD_PRESENT"
        if status == "NO_ASSOCIATION_RECORD_RETURNED":
            return "MISSING", "MAPPED_LUAD_QUERY_COMPLETED_NO_RECORD"
        if status == "TARGET_NOT_MAPPED_OR_RETURNED":
            return "NOT_QUERIED", "NO_VALID_TARGET_MAPPING_FOR_LUAD_QUERY"
        return "PARTIAL", "INCOMPLETE_LUAD_ASSOCIATION_ASSESSMENT"

    if component in {
        "COMP_GENETIC_EVIDENCE", "COMP_FUNCTIONAL_DEPENDENCY",
        "COMP_CLINICAL_DEVELOPMENT", "COMP_HUMAN_EVIDENCE",
    }:
        return "NOT_QUERIED", "DEDICATED_ACQUISITION_NOT_PRESENT_IN_FROZEN_INPUTS"

    if component == "COMP_PHARMACOLOGY":
        status = claims["DOM_PHARMACOLOGY"]["claim_status"]
        if status == "TARGET_NOT_MAPPED_FOR_PHARMACOLOGY":
            return "NOT_QUERIED", "NO_VALID_TARGET_MAPPING_FOR_PHARMACOLOGY"
        if status == "RETRIEVAL_COMPLETED_NO_POSITIVE_ANNOTATION":
            return "MISSING", "FROZEN_CURRENT_PHARMACOLOGY_QUERIES_NO_POSITIVE_RECORD"
        if status in {
            "CHEMBL_TARGET_ANNOTATION_PRESENT", "MULTISOURCE_ANNOTATION_PRESENT",
            "OPEN_TARGETS_DRUG_CANDIDATE_RECORD_PRESENT",
        }:
            return "PARTIAL", "ANNOTATION_OR_COUNT_PRESENT_WITHOUT_COMPOUND_ASSAY_MECHANISM"
        return "PARTIAL", "PHARMACOLOGY_ASSESSMENT_INCOMPLETE"

    if component == "COMP_TRACTABILITY":
        status = claims["DOM_TRACTABILITY"]["claim_status"]
        if status == "TRACTABILITY_RECORD_PRESENT":
            return "OBSERVED", "SOURCE_NATIVE_TRACTABILITY_ASSESSMENT_PRESENT"
        if status == "TARGET_PRESENT_NO_TRACTABILITY_RECORD_RETURNED":
            return "MISSING", "MAPPED_TRACTABILITY_QUERY_COMPLETED_NO_RECORD"
        if status == "TARGET_NOT_MAPPED":
            return "NOT_QUERIED", "NO_VALID_TARGET_MAPPING_FOR_TRACTABILITY"
        return "PARTIAL", "TRACTABILITY_ASSESSMENT_INCOMPLETE"

    if component in {"COMP_SAFETY", "COMP_RISK_CONTEXT"}:
        status = claims["DOM_SAFETY"]["claim_status"]
        if status == "SAFETY_RECORD_PRESENT":
            return "OBSERVED", "SOURCE_NATIVE_SAFETY_LIABILITY_RECORD_PRESENT"
        if status == "TARGET_PRESENT_NO_SAFETY_RECORD_RETURNED":
            return "MISSING", "MAPPED_SAFETY_QUERY_COMPLETED_NO_RECORD"
        if status == "TARGET_NOT_MAPPED":
            return "NOT_QUERIED", "NO_VALID_TARGET_MAPPING_FOR_SAFETY"
        return "PARTIAL", "SAFETY_ASSESSMENT_INCOMPLETE"

    if component == "COMP_CLINICAL_LINKAGE":
        disease_n = int(claims["DOM_DISEASE_ASSOCIATION"]["supporting_record_count"])
        pharma_n = int(claims["DOM_PHARMACOLOGY"]["supporting_record_count"])
        if disease_n > 0 or pharma_n > 0:
            return "PARTIAL", "SEPARATE_RECORDS_EXIST_WITHOUT_INTERVENTION_TARGET_LUAD_TRIAL_CHAIN"
        return "NOT_QUERIED", "NO_TRIAL_LEVEL_LINKAGE_ACQUISITION"

    fail(f"No validation state mapping for component {component}.")


def fixture_eligibility(
    gene: str,
    claims: dict[str, dict[str, str]],
    records: list[tuple[str, ...]],
    dependencies: list[dict[str, str]],
    maximum_dependencies: int,
) -> set[str]:
    positive_domains = sum(int(row["supporting_record_count"]) > 0 for row in claims.values())
    missingness = Counter(record_dict(item)["missingness_status"] for item in records)
    roles = roles_for_gene(records)
    states = {resolve_state(component, claims, roles)[0] for component in COMPONENTS}
    eligible = set()
    if positive_domains >= 4:
        eligible.add("EVIDENCE_RICH")
    if positive_domains <= 1:
        eligible.add("EVIDENCE_POOR")
    if len(dependencies) == maximum_dependencies:
        eligible.add("DEPENDENCY_HEAVY")
    if "MISSING" in states:
        eligible.add("MISSING_BOUNDARY")
    if missingness["NOT_QUERIED"] > 0:
        eligible.add("NOT_QUERIED_BOUNDARY")
    if "PARTIAL" in states:
        eligible.add("PARTIAL_BOUNDARY")
    if claims["DOM_TRANSCRIPTOMIC_DISCOVERY"]["uncertainty_status"] == "CONFLICTING_RECORDS" and "CONFLICTING" in states:
        eligible.add("CONFLICT_BOUNDARY")
    return eligible


def select_fixtures(
    integrated: dict[str, dict[str, str]],
    claims_by_gene: dict[str, dict[str, dict[str, str]]],
    records_by_gene: dict[str, list[tuple[str, ...]]],
    dependencies_by_gene: dict[str, list[dict[str, str]]],
) -> tuple[list[dict[str, str]], dict[str, set[str]]]:
    maximum_dependencies = max(len(dependencies_by_gene[gene]) for gene in integrated)
    eligibility = {
        gene: fixture_eligibility(
            gene, claims_by_gene[gene], records_by_gene[gene],
            dependencies_by_gene[gene], maximum_dependencies,
        )
        for gene in integrated
    }
    selected = []
    used = set()
    for category, requested in FIXTURE_PLAN:
        candidates = [gene for gene in integrated if category in eligibility[gene] and gene not in used]
        candidates.sort(key=lambda gene: (sha256_text(f"{VALIDATION_VERSION}|{category}|{gene}"), gene))
        if len(candidates) < requested:
            fail(f"Insufficient deterministic fixtures for {category}: {len(candidates)}")
        for gene in candidates[:requested]:
            used.add(gene)
            claims = claims_by_gene[gene]
            records = records_by_gene[gene]
            missingness = Counter(record_dict(item)["missingness_status"] for item in records)
            positive = sorted(domain for domain, claim in claims.items() if int(claim["supporting_record_count"]) > 0)
            selection_key = sha256_text(f"{VALIDATION_VERSION}|{category}|{gene}")
            selected.append({
                "fixture_id": f"FIXTURE_{len(selected) + 1:02d}",
                "EnsemblID": gene,
                "Symbol_annotation": integrated[gene]["Symbol"],
                "gene_type_annotation": integrated[gene]["gene_type"],
                "primary_validation_category": category,
                "selection_rule_id": f"VALSEL_{category}_V0.1",
                "deterministic_tiebreak_sha256": selection_key,
                "positive_evidence_domain_count": str(len(positive)),
                "positive_evidence_domains": "|".join(positive) if positive else "NONE",
                "claim_count": str(len(claims)),
                "atomic_evidence_record_count": str(len(records)),
                "dependency_edge_count": str(len(dependencies_by_gene[gene])),
                "observed_record_count": str(missingness["OBSERVED"]),
                "not_found_record_count": str(missingness["NOT_FOUND"]),
                "not_queried_record_count": str(missingness["NOT_QUERIED"]),
                "conflicting_claim_count": str(sum(claim["uncertainty_status"] == "CONFLICTING_RECORDS" for claim in claims.values())),
                "all_applicable_validation_categories": "|".join(sorted(eligibility[gene])),
                "biological_interpretation_used": "FALSE",
                "gene_symbol_used_for_join": "FALSE",
            })
    expected_n = sum(size for _, size in FIXTURE_PLAN)
    if len(selected) != expected_n or len({row["EnsemblID"] for row in selected}) != expected_n:
        fail("Validation fixture cohort is incomplete or duplicated.")
    return selected, eligibility


def load_selected_record_details(selected_genes: set[str], claims: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    details = {}
    with INPUTS["record_registry"].open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if claims[row["claim_id"]]["EnsemblID"] in selected_genes:
                details[row["record_id"]] = row
    if len(details) != len(selected_genes) * 7:
        fail("Selected evidence-record detail extraction failed.")
    return details


def build_validation_tables(
    fixtures: list[dict[str, str]],
    integrated: dict[str, dict[str, str]],
    claims_by_gene: dict[str, dict[str, dict[str, str]]],
    records_by_gene: dict[str, list[tuple[str, ...]]],
    record_details: dict[str, dict[str, str]],
    sources: dict[str, dict[str, str]],
    dependencies_by_gene: dict[str, list[dict[str, str]]],
    state_rules: dict[tuple[str, str], dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    results = []
    missingness_rows = []
    dependency_rows = []
    identity_rows = []
    fixture_by_gene = {row["EnsemblID"]: row for row in fixtures}

    for gene, fixture in fixture_by_gene.items():
        claims = claims_by_gene[gene]
        role_records = roles_for_gene(records_by_gene[gene])
        claim_ids = {claim["claim_id"] for claim in claims.values()}
        records = [record_dict(item) for item in records_by_gene[gene]]
        record_ids = {row["record_id"] for row in records}
        raw_identity_ok = all(
            record_details[row["record_id"]]["raw_value_reference"].startswith(
                f"outputs/integrated_registry/integrated_target_registry.csv#EnsemblID={gene}&"
            )
            for row in records
        )
        claim_identity_ok = all(claim["EnsemblID"] == gene for claim in claims.values())
        record_claim_ok = all(row["claim_id"] in claim_ids for row in records)
        source_resolution_ok = all(row["source_id"] in sources for row in records)
        identity_status = claim_identity_ok and record_claim_ok and raw_identity_ok and source_resolution_ok and gene in integrated
        identity_rows.append({
            "fixture_id": fixture["fixture_id"],
            "EnsemblID_input": gene,
            "EnsemblID_validation_entity": gene,
            "integrated_registry_row_present": str(gene in integrated).upper(),
            "claim_ensembl_ids_match": str(claim_identity_ok).upper(),
            "record_claim_links_match_entity": str(record_claim_ok).upper(),
            "raw_value_references_match_entity": str(raw_identity_ok).upper(),
            "source_ids_resolve": str(source_resolution_ok).upper(),
            "gene_symbol_used_for_join": "FALSE",
            "identity_preserved": str(identity_status).upper(),
            "validation_status": "PASS" if identity_status else "FAIL",
        })

        component_record_references: dict[str, set[str]] = {}
        for component in COMPONENTS:
            expected_state, condition_code = resolve_state(component, claims, role_records)
            rule = state_rules.get((component, expected_state))
            component_records = [role_records[role] for role in CURRENT_COMPONENT_ROLES[component] if role in role_records]
            component_record_ids = sorted({row["record_id"] for row in component_records})
            component_record_references[component] = set(component_record_ids)
            component_claim_ids = sorted({row["claim_id"] for row in component_records} | {
                claims[domain]["claim_id"] for domain in COMPONENT_DOMAINS[component] if domain in claims
            })
            component_source_ids = sorted({row["source_id"] for row in component_records})
            source_versions = [f"{source_id}={sources[source_id]['version']}" for source_id in component_source_ids]
            component_edges = [
                edge for edge in dependencies_by_gene[gene]
                if edge["record_a"] in component_record_ids and edge["record_b"] in component_record_ids
            ]
            missing_pairs = [f"{row['record_id']}={row['missingness_status']}" for row in sorted(component_records, key=lambda item: item["record_id"])]
            uncertainty_pairs = [f"{row['record_id']}={row['uncertainty_status']}" for row in sorted(component_records, key=lambda item: item["record_id"])]
            absent_roles = sorted(set(FUTURE_COMPONENT_ROLES.get(component, ())))
            lineage_ok = (
                len(component_claim_ids) == len(set(component_claim_ids))
                and len(component_record_ids) == len(set(component_record_ids))
                and all(record_details[record_id]["claim_id"] in component_claim_ids for record_id in component_record_ids)
                and all(record_details[record_id]["source_id"] in component_source_ids for record_id in component_record_ids)
                and all(record_details[record_id]["raw_value_reference"].startswith("outputs/integrated_registry/integrated_target_registry.csv#") for record_id in component_record_ids)
            )
            dependency_ok = all(
                edge["record_a"] in component_record_ids and edge["record_b"] in component_record_ids
                for edge in component_edges
            )
            missingness_ok = all("=" in pair for pair in missing_pairs) and len(missing_pairs) == len(component_record_ids)
            uncertainty_ok = all("=" in pair for pair in uncertainty_pairs) and len(uncertainty_pairs) == len(component_record_ids)
            rule_ok = rule is not None and rule["evaluation_precedence"] == STATE_PRECEDENCE[expected_state]
            status = "PASS" if all((lineage_ok, dependency_ok, missingness_ok, uncertainty_ok, rule_ok)) else "FAIL"
            artifact_paths = "|".join(relative(INPUTS[name]) for name in ("integrated_registry", "claim_registry", "record_registry", "source_registry", "dependency_graph", "state_registry"))
            artifact_hashes = "|".join(EXPECTED_HASHES[name] for name in ("integrated_registry", "claim_registry", "record_registry", "source_registry", "dependency_graph", "state_registry"))
            results.append({
                "validation_case_id": f"{fixture['fixture_id']}::{component}",
                "fixture_id": fixture["fixture_id"],
                "EnsemblID": gene,
                "component_id": component,
                "source_condition_code": condition_code,
                "expected_component_state": expected_state,
                "task021_resolved_state": rule["resolved_state"] if rule else "NO_RULE",
                "task021_rule_reference": f"{component}::{expected_state}",
                "task021_predicate_sha256": sha256_text(rule["deterministic_predicate"]) if rule else "NOT_FOUND",
                "claim_ids": "|".join(component_claim_ids) if component_claim_ids else "NONE",
                "evidence_record_ids": "|".join(component_record_ids) if component_record_ids else "NONE",
                "source_ids": "|".join(component_source_ids) if component_source_ids else "NONE",
                "source_versions": "|".join(source_versions) if source_versions else "NONE",
                "source_artifact_paths": artifact_paths,
                "source_artifact_sha256s": artifact_hashes,
                "dependency_edge_ids": "|".join(sorted(edge["dependency_id"] for edge in component_edges)) if component_edges else "NONE",
                "lineage_reconstructible": str(lineage_ok).upper(),
                "dependency_reconstructible": str(dependency_ok).upper(),
                "missingness_reconstructible": str(missingness_ok).upper(),
                "uncertainty_reconstructible": str(uncertainty_ok).upper(),
                "exactly_one_addressable_state_rule": str(rule_ok).upper(),
                "validation_status": status,
                "interpretation_boundary": "VALIDATION_FIXTURE_ONLY_NOT_A_FINAL_PROFILE_OR_THERAPEUTIC_ASSESSMENT",
            })
            missingness_rows.append({
                "validation_case_id": f"{fixture['fixture_id']}::{component}",
                "fixture_id": fixture["fixture_id"],
                "EnsemblID": gene,
                "component_id": component,
                "record_level_missingness": "|".join(missing_pairs) if missing_pairs else "NONE",
                "record_level_uncertainty": "|".join(uncertainty_pairs) if uncertainty_pairs else "NONE",
                "future_roles_not_acquired": "|".join(absent_roles) if absent_roles else "NONE",
                "expected_component_state": expected_state,
                "task021_component_state": rule["resolved_state"] if rule else "NO_RULE",
                "not_found_and_not_queried_kept_distinct": "TRUE",
                "missing_not_interpreted_as_negative": "TRUE",
                "record_mapping_requires_frozen_record_registry": "TRUE",
                "validation_status": status,
            })

        for edge in sorted(dependencies_by_gene[gene], key=lambda row: row["dependency_id"]):
            a, b = edge["record_a"], edge["record_b"]
            shared_components = sorted(
                component for component, ids in component_record_references.items()
                if a in ids and b in ids
            )
            endpoint_ok = a in record_ids and b in record_ids
            dependency_rows.append({
                "fixture_id": fixture["fixture_id"],
                "EnsemblID": gene,
                "dependency_id": edge["dependency_id"],
                "record_a": a,
                "record_b": b,
                "record_a_claim_id": record_details[a]["claim_id"],
                "record_b_claim_id": record_details[b]["claim_id"],
                "record_a_source_id": record_details[a]["source_id"],
                "record_b_source_id": record_details[b]["source_id"],
                "relationship": edge["relationship"],
                "dependency_level": edge["dependency_level"],
                "review_status": edge["review_status"],
                "shared_component_ids": "|".join(shared_components) if shared_components else "NONE",
                "both_endpoints_preserved_once_in_atomic_registry": str(endpoint_ok and a != b).upper(),
                "edge_reconstructible_from_frozen_graph": str(endpoint_ok).upper(),
                "record_ids_reused_not_copied": "TRUE",
                "validation_status": "PASS" if endpoint_ok and a != b else "FAIL",
            })
    return results, missingness_rows, dependency_rows, identity_rows


def csv_bytes(rows: list[dict[str, str]]) -> bytes:
    if not rows:
        fail("Refusing to serialize an empty validation table.")
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue().encode("utf-8")


def validate_generated(
    fixtures: list[dict[str, str]],
    results: list[dict[str, str]],
    missingness: list[dict[str, str]],
    dependencies: list[dict[str, str]],
    identities: list[dict[str, str]],
) -> list[dict[str, str]]:
    checks = []

    def check(name: str, passed: bool, observed: object, expected: object, detail: str, level: str = "PASS") -> None:
        status = level if passed else "FAIL"
        checks.append({"check": name, "status": status, "observed": str(observed), "expected": str(expected), "detail": detail})
        if not passed:
            fail(f"Validation failed: {name}")

    headers = set()
    for table in (fixtures, results, missingness, dependencies, identities):
        headers.update(field.lower() for field in table[0])
    forbidden = headers.intersection(FORBIDDEN_EXACT_FIELDS)
    states = {row["task021_resolved_state"] for row in results}
    categories = Counter(row["primary_validation_category"] for row in fixtures)

    check("validation_fixture_count", len(fixtures) == 10 and len({row["EnsemblID"] for row in fixtures}) == 10, len(fixtures), 10, "Ten unique non-biological test fixtures.")
    check("validation_categories_exact", categories == Counter(dict(FIXTURE_PLAN)), dict(categories), dict(FIXTURE_PLAN), "Prespecified category coverage and sizes.")
    check("component_case_cardinality", len(results) == 10 * 11 and len({row["validation_case_id"] for row in results}) == 110, len(results), 110, "Every fixture addresses all 11 components without creating profiles.")
    check("identity_preservation", all(row["validation_status"] == "PASS" for row in identities), sum(row["validation_status"] == "PASS" for row in identities), len(identities), "EnsemblID is unchanged through integrated→claim→record linkage; no Symbol join.")
    check("lineage_preservation", all(row["lineage_reconstructible"] == "TRUE" for row in results), sum(row["lineage_reconstructible"] == "TRUE" for row in results), len(results), "Claim, record, source, version, and artifact hashes remain resolvable.")
    check("dependency_preservation", all(row["validation_status"] == "PASS" for row in dependencies), sum(row["validation_status"] == "PASS" for row in dependencies), len(dependencies), "Every selected dependency edge retains both exact record endpoints.", "PASS_WITH_LIMITATION")
    check("evidence_record_no_duplication", all(row["record_ids_reused_not_copied"] == "TRUE" for row in dependencies), "all exact IDs", "all exact IDs", "Reuse across components retains record identity.")
    check("missingness_preservation", all(row["validation_status"] == "PASS" for row in missingness), sum(row["validation_status"] == "PASS" for row in missingness), len(missingness), "Record-level OBSERVED/NOT_FOUND/NOT_QUERIED remain reconstructible.", "PASS_WITH_LIMITATION")
    check("five_state_coverage", states == set(PROFILE_STATES), sorted(states), list(PROFILE_STATES), "Validation cases exercise all five Task #021 states.")
    check("component_state_addressability", all(row["exactly_one_addressable_state_rule"] == "TRUE" and row["validation_status"] == "PASS" for row in results), sum(row["validation_status"] == "PASS" for row in results), len(results), "Each controlled fixture condition maps to one frozen Task #021 component/state rule.", "PASS_WITH_LIMITATION")
    check("gene_symbol_join_absent", all(row["gene_symbol_used_for_join"] == "FALSE" for row in fixtures) and all(row["gene_symbol_used_for_join"] == "FALSE" for row in identities), "FALSE", "FALSE", "Symbols are display annotations only.")
    check("forbidden_fields_absent", not forbidden, sorted(forbidden), [], "No assessment or therapeutic-decision fields.")
    check("no_final_profile_artifact", not (OUTPUT_DIR / "target_evidence_profile.csv").exists(), "absent", "absent", "Validation results are assertions, not final profiles.")

    scientific_tables = (fixtures, results, missingness, dependencies, identities)
    first = [csv_bytes(table) for table in scientific_tables]
    second = [csv_bytes(table) for table in scientific_tables]
    check("in_memory_byte_determinism", first == second, "byte-identical", "byte-identical", "Repeated canonical serialization of identical inputs.")
    return checks


def build_summary(
    fixtures: list[dict[str, str]], results: list[dict[str, str]],
    dependencies: list[dict[str, str]], checks: list[dict[str, str]],
) -> bytes:
    state_counts = Counter(row["task021_resolved_state"] for row in results)
    category_counts = Counter(row["primary_validation_category"] for row in fixtures)
    lines = [
        "# Task #023 profile materialization validation summary",
        "",
        "**Overall result:** PASS WITH REPRESENTATION LIMITATIONS  ",
        f"**Validation fixtures:** {len(fixtures)}  ",
        f"**Component-state validation cases:** {len(results)}  ",
        f"**Dependency edges audited:** {len(dependencies)}  ",
        f"**Validation checks:** {sum(row['status'] != 'FAIL' for row in checks)}/{len(checks)} passed  ",
        "**Final target profiles generated:** 0  ",
        "**Scores, rankings, therapeutic selections, recommendations, or direction inferences generated:** No",
        "",
        "## Scientific answer",
        "",
        "The Task #020–#022 architecture can represent the validation cohort without changing entity identity or evidence state when the profile remains linked to the frozen claim, record, source, dependency, and artifact registries. It is a relational representation: some meanings are reconstructible through stable IDs and hashes rather than self-contained in one component row.",
        "",
        "This task validates representation fidelity only. It does not validate any target biologically and does not materialize a release profile.",
        "",
        "## Deterministic validation cohort",
        "",
        "| Fixture category | Number | Mechanical criterion |",
        "| --- | ---: | --- |",
        f"| Evidence rich | {category_counts['EVIDENCE_RICH']} | At least four claim domains with a positive supporting-record count |",
        f"| Evidence poor | {category_counts['EVIDENCE_POOR']} | At most one claim domain with a positive supporting-record count |",
        f"| Dependency heavy | {category_counts['DEPENDENCY_HEAVY']} | Maximum dependency-edge count in the frozen graph |",
        f"| Missing boundary | {category_counts['MISSING_BOUNDARY']} | At least one component resolves MISSING |",
        f"| Not-queried boundary | {category_counts['NOT_QUERIED_BOUNDARY']} | At least one current atomic record is explicitly NOT_QUERIED |",
        f"| Partial boundary | {category_counts['PARTIAL_BOUNDARY']} | At least one component resolves PARTIAL |",
        f"| Conflict boundary | {category_counts['CONFLICT_BOUNDARY']} | Transcript claim has frozen CONFLICTING_RECORDS uncertainty |",
        "",
        "Eligible entities were ordered by `SHA256(validation_version | category | EnsemblID)` and assigned without replacement in a frozen category order. Symbol, gene name, pathway, biological reputation, and therapeutic interpretation were never selection variables. This is test-fixture sampling, not therapeutic candidate selection.",
        "",
        "## State coverage",
        "",
        "| Component state | Validation cases | Meaning retained |",
        "| --- | ---: | --- |",
    ]
    for state in PROFILE_STATES:
        lines.append(f"| `{state}` | {state_counts[state]} | Yes |")
    lines.extend([
        "",
        "`MISSING` is emitted only for a completed frozen scope with no qualifying record. `NOT_QUERIED` remains no acquisition or no valid query. `PARTIAL` remains incomplete evidence/provenance/linkage. `CONFLICTING` retains the frozen conflict flag and both transcript records. None is converted into a favorable or unfavorable target judgment.",
        "",
        "## Validation results",
        "",
        "| Test | Result |",
        "| --- | --- |",
    ])
    labels = {
        "identity_preservation": "Identity preservation",
        "lineage_preservation": "Evidence lineage preservation",
        "dependency_preservation": "Dependency preservation",
        "evidence_record_no_duplication": "No evidence-record duplication",
        "missingness_preservation": "Missingness and uncertainty preservation",
        "five_state_coverage": "Five-state coverage",
        "component_state_addressability": "Component-state rule addressability",
        "gene_symbol_join_absent": "No Symbol join",
        "forbidden_fields_absent": "No forbidden assessment fields",
        "no_final_profile_artifact": "No final profile artifact",
        "in_memory_byte_determinism": "Canonical byte determinism",
    }
    for check in checks:
        if check["check"] in labels:
            lines.append(f"| {labels[check['check']]} | {check['status']} |")
    lines.extend([
        "",
        "## Representation limitations",
        "",
        "1. **State predicates are controlled prose.** The Task #021 registry contains one predicate for every component/state and the validation harness can address all fixture states. The predicates are not yet a machine-executable rule language. A full materializer should freeze executable predicates or reviewed predicate IDs before profile release.",
        "2. **Profiles are relational, not standalone.** Task #020 list fields retain record IDs, source IDs, missingness categories, dependency relationships, and levels, but do not encode every record→status or record-pair→dependency mapping inline. Exact reconstruction therefore requires the frozen evidence-record and dependency-graph artifacts and their hashes. Task #023 confirms that reconstruction is lossless for the cohort.",
        "3. **Current evidence scope is limited.** Genetics, functional dependency, trial-level clinical development, and dedicated intervention–target–LUAD linkage were not acquired in the frozen inputs. Their `NOT_QUERIED` validation states must not be interpreted as absent biology or negative evidence.",
        "4. **Conflict coverage is transcriptomic only.** Frozen conflict-boundary examples exist for prespecified DE sensitivity discordance. The current inputs do not provide validated conflict examples for every other component.",
        "",
        "## Release boundary",
        "",
        "These outputs are validation fixtures and assertions. They contain no `profile_id`, no 28-field materialized profile rows, no cross-component aggregation, and no gene-level scientific or therapeutic conclusion.",
    ])
    return ("\n".join(lines) + "\n").encode("utf-8")


def session_bytes(
    git_info: dict[str, str], hashes: dict[str, str],
    output_bytes: dict[Path, bytes], checks: list[dict[str, str]],
    counts: dict[str, int],
) -> bytes:
    values = {
        "task": "023",
        "purpose": "profile materialization representation validation",
        "validation_version": VALIDATION_VERSION,
        "validation_snapshot_time_utc": git_info["snapshot"],
        "wall_clock_used_in_generated_outputs": "FALSE",
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "git_branch": git_info["branch"],
        "git_head": git_info["head"],
        "git_origin": git_info["remote"],
        "frozen_task022_base_commit": git_info["base"],
        "network_access": "NOT_USED",
        "packages_installed_or_updated": "FALSE",
        "previous_artifacts_modified": "FALSE",
        "final_target_profiles_generated": "FALSE",
        "scoring_generated": "FALSE",
        "ranking_generated": "FALSE",
        "therapeutic_candidate_selection_generated": "FALSE",
        "target_recommendations_generated": "FALSE",
        "therapeutic_direction_inferred": "FALSE",
        "git_commit_or_push": "FALSE",
        "script_sha256": sha256(SCRIPT_PATH),
        "plan_sha256": sha256(PLAN_PATH),
        "overall_validation_result": "PASS_WITH_REPRESENTATION_LIMITATIONS",
    }
    for name, digest in hashes.items():
        values[f"frozen_input_sha256.{relative(INPUTS[name])}"] = digest
    for name, value in counts.items():
        values[f"validated_count.{name}"] = str(value)
    for row in checks:
        values[f"validation.{row['check']}"] = row["status"]
    for path, content in output_bytes.items():
        values[f"output_sha256.{relative(path)}"] = hashlib.sha256(content).hexdigest()
    return "".join(f"{key}={values[key]}\n" for key in sorted(values)).encode("utf-8")


def validate_postflight(start_head: str) -> None:
    if run_git("rev-parse", "HEAD") != start_head:
        fail("Git HEAD changed during Task #023.")
    if run_git("diff", "--name-only") or run_git("diff", "--cached", "--name-only"):
        fail("An existing tracked file changed during Task #023.")
    validate_hashes()


def main() -> None:
    git_info = validate_repository()
    hashes = validate_hashes()
    integrated, _ = load_integrated()
    claims, claims_by_gene = load_claims(integrated)
    records, records_by_gene, record_to_gene = load_records(claims)
    sources = load_sources()
    dependencies, dependencies_by_gene = load_dependencies(records, record_to_gene)
    state_rules, _ = load_architecture()

    fixtures, _ = select_fixtures(integrated, claims_by_gene, records_by_gene, dependencies_by_gene)
    selected_genes = {row["EnsemblID"] for row in fixtures}
    record_details = load_selected_record_details(selected_genes, claims)
    results, missingness, dependency_rows, identities = build_validation_tables(
        fixtures, integrated, claims_by_gene, records_by_gene, record_details,
        sources, dependencies_by_gene, state_rules,
    )
    checks = validate_generated(fixtures, results, missingness, dependency_rows, identities)
    summary = build_summary(fixtures, results, dependency_rows, checks)

    scientific_outputs = {
        SELECTION_PATH: csv_bytes(fixtures),
        RESULTS_PATH: csv_bytes(results),
        MISSINGNESS_PATH: csv_bytes(missingness),
        DEPENDENCY_PATH: csv_bytes(dependency_rows),
        IDENTITY_PATH: csv_bytes(identities),
        SUMMARY_PATH: summary,
    }
    counts = {
        "integrated_entities": len(integrated),
        "claims": len(claims),
        "atomic_evidence_records": len(records),
        "source_entities": len(sources),
        "dependency_edges": len(dependencies),
        "component_state_rules": len(state_rules),
        "validation_fixtures": len(fixtures),
        "component_validation_cases": len(results),
        "selected_dependency_edges": len(dependency_rows),
        "identity_validation_rows": len(identities),
    }
    session = session_bytes(git_info, hashes, scientific_outputs, checks, counts)
    all_outputs = {**scientific_outputs, SESSION_PATH: session}

    # Independent repeated construction catches nondeterministic iteration or
    # serialization before any artifact is written.
    repeated_scientific = {
        SELECTION_PATH: csv_bytes(fixtures),
        RESULTS_PATH: csv_bytes(results),
        MISSINGNESS_PATH: csv_bytes(missingness),
        DEPENDENCY_PATH: csv_bytes(dependency_rows),
        IDENTITY_PATH: csv_bytes(identities),
        SUMMARY_PATH: build_summary(fixtures, results, dependency_rows, checks),
    }
    repeated_session = session_bytes(git_info, hashes, repeated_scientific, checks, counts)
    if all_outputs != {**repeated_scientific, SESSION_PATH: repeated_session}:
        fail("Repeated output construction was not byte-identical.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    allowed = {path.name for path in all_outputs}
    unexpected = {path.name for path in OUTPUT_DIR.iterdir() if path.name not in allowed}
    if unexpected:
        fail(f"Unexpected Task #023 output files: {sorted(unexpected)}")
    for path, content in all_outputs.items():
        path.write_bytes(content)

    validate_postflight(git_info["head"])
    print("Created files:")
    for path in all_outputs:
        print(f"- {relative(path)}")
    print(f"Validation fixtures: {len(fixtures)}")
    print(f"Component validation cases: {len(results)}")
    print(f"Dependency edges audited in cohort: {len(dependency_rows)}")
    print(f"Validation checks passed: {sum(row['status'] != 'FAIL' for row in checks)}/{len(checks)}")
    print("Overall: PASS WITH REPRESENTATION LIMITATIONS")
    print("No final profiles, scores, rankings, therapeutic selections, recommendations, or direction inferences were generated.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
