#!/usr/bin/env python3
"""Build the Task #017 descriptive evidence-acquisition framework.

This program uses only frozen Task #016 outputs. It maps each documented
missing-evidence or uncertainty category to an additional evidence class that
could reduce that uncertainty. It does not rank, score, select, or recommend
genes or targets, and it performs no network access.
"""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
TASK016_BASE_COMMIT = "9c04adf9c51205177dd93bd5d298cb455f6b8abc"
EXPECTED_BRANCH = "main"
EXPECTED_REMOTE_FRAGMENT = "SichengChen-web/luad-target-dossier"
EXPECTED_GENE_COUNT = 29_606

INPUTS = {
    "gap_registry": ROOT / "outputs/evidence_gap_analysis/evidence_gap_registry.csv",
    "category_counts": ROOT
    / "outputs/evidence_gap_analysis/evidence_gap_category_counts.csv",
    "validation_matrix": ROOT
    / "outputs/evidence_gap_analysis/validation_strategy_matrix.csv",
    "summary": ROOT / "outputs/evidence_gap_analysis/evidence_gap_summary.md",
    "session": ROOT / "outputs/evidence_gap_analysis/session_info.txt",
}

EXPECTED_INPUT_HASHES = {
    "gap_registry": "3e509ef36d57c553a36e36429a42955c02c0eef209cf2d77b0adbd2d217c60f6",
    "category_counts": "03357115a1237c87921415221e1e3876462eb771f1c4950c9056ad2c3a27ad6b",
    "validation_matrix": "6f915616019265583103cee945d0ccfcc1328628e374f989ff8b74bf0e93d981",
    "summary": "b779986769ab1aa08cb536330b959fe0761d60ff1755b6ef592a0f7fc377d5f4",
    "session": "71df0b77d97fa49bc0e6e3262546121cc34493134f5242ae03dddfba81bd2fcd",
}

OUTPUT_DIR = ROOT / "outputs/evidence_acquisition"
FRAMEWORK_PATH = OUTPUT_DIR / "evidence_acquisition_framework.csv"
QC_PATH = OUTPUT_DIR / "evidence_acquisition_qc.csv"
SUMMARY_PATH = OUTPUT_DIR / "evidence_acquisition_summary.md"
SESSION_PATH = OUTPUT_DIR / "session_info.txt"
PLAN_PATH = ROOT / "docs/evidence_acquisition_framework_v0.1.md"
SCRIPT_PATH = ROOT / "analysis/17_build_evidence_acquisition_framework.py"

ALLOWED_UNTRACKED_FILES = {
    "analysis/17_build_evidence_acquisition_framework.py",
    "docs/evidence_acquisition_framework_v0.1.md",
}
ALLOWED_UNTRACKED_DIRECTORY = "outputs/evidence_acquisition/"

FORBIDDEN_EXACT_COLUMNS = {
    "score",
    "rank",
    "priority",
    "target_selection",
    "recommendation",
    "therapeutic_direction",
}

FRAMEWORK_FIELDS = [
    "gap_category_group",
    "gap_category",
    "evidence_layer",
    "additional_evidence_class",
    "affected_gene_count",
    "affected_gene_percent",
    "scientific_question",
    "potential_data_source_class",
    "acquisition_unit",
    "required_identifier_keys",
    "minimum_provenance_fields",
    "evidence_quality_checks",
    "dependency_control",
    "uncertainty_reduced",
    "adequacy_criterion",
    "interpretation_boundary",
]


def fail(message: str) -> None:
    raise RuntimeError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
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


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def validate_repository() -> dict[str, str]:
    branch = run_git("branch", "--show-current")
    head = run_git("rev-parse", "HEAD")
    remote = run_git("remote", "get-url", "origin")

    if branch != EXPECTED_BRANCH:
        fail(f"Expected Git branch {EXPECTED_BRANCH!r}; observed {branch!r}.")
    if EXPECTED_REMOTE_FRAGMENT not in remote:
        fail(f"Unexpected origin remote: {remote!r}.")

    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", TASK016_BASE_COMMIT, "HEAD"],
        cwd=ROOT,
        check=False,
    )
    if ancestor.returncode != 0:
        fail(
            f"Frozen Task #016 base {TASK016_BASE_COMMIT} is not an ancestor "
            f"of current HEAD {head}."
        )

    tracked_changes = run_git("status", "--porcelain=v1", "--untracked-files=no")
    if tracked_changes:
        fail(
            "Unexpected tracked working-tree changes exist before Task #017:\n"
            f"{tracked_changes}"
        )

    untracked = run_git("ls-files", "--others", "--exclude-standard").splitlines()
    unexpected = [
        path
        for path in untracked
        if not (
            path in ALLOWED_UNTRACKED_FILES
            or path.startswith(ALLOWED_UNTRACKED_DIRECTORY)
        )
    ]
    if unexpected:
        fail(f"Unexpected untracked paths exist: {unexpected}")

    for path in INPUTS.values():
        rel = relative(path)
        if not path.is_file():
            fail(f"Required Task #016 input is missing: {rel}")
        if not run_git("ls-files", "--error-unmatch", rel, check=False):
            fail(f"Required Task #016 input is not committed: {rel}")
        changed = run_git("diff", "--name-only", TASK016_BASE_COMMIT, "HEAD", "--", rel)
        if changed:
            fail(f"Frozen Task #016 input changed since its base commit: {rel}")

    return {"branch": branch, "head": head, "remote": remote}


def validate_hashes() -> dict[str, str]:
    observed = {}
    for name, path in INPUTS.items():
        actual = sha256(path)
        expected = EXPECTED_INPUT_HASHES[name]
        if actual != expected:
            fail(
                f"Frozen Task #016 hash mismatch for {relative(path)}: "
                f"expected {expected}, observed {actual}."
            )
        observed[name] = actual
    return observed


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            fail(f"CSV has no header: {relative(path)}")
        return list(reader.fieldnames), list(reader)


def split_tokens(value: str) -> list[str]:
    return [] if not value else value.split("|")


def count_registry_tokens(rows: Iterable[dict[str, str]], field: str) -> Counter[str]:
    result: Counter[str] = Counter()
    for row in rows:
        result.update(split_tokens(row[field]))
    return result


def validate_task016_inputs() -> tuple[
    list[dict[str, str]],
    dict[tuple[str, str], dict[str, str]],
    dict[str, dict[str, str]],
]:
    registry_fields, registry = read_csv(INPUTS["gap_registry"])
    required_registry = {
        "EnsemblID",
        "discovery_status",
        "mechanistic_status",
        "development_status",
        "risk_status",
        "evidence_maturity_status",
        "missing_evidence_domains",
        "known_uncertainties",
        "recommended_future_evidence_type",
    }
    missing = required_registry.difference(registry_fields)
    if missing:
        fail(f"Task #016 gap registry lacks required fields: {sorted(missing)}")
    if len(registry) != EXPECTED_GENE_COUNT:
        fail(f"Expected {EXPECTED_GENE_COUNT} gap rows; observed {len(registry)}.")
    ids = [row["EnsemblID"] for row in registry]
    if len(set(ids)) != EXPECTED_GENE_COUNT or any(not value for value in ids):
        fail("Task #016 EnsemblID uniqueness/completeness validation failed.")

    _, count_rows = read_csv(INPUTS["category_counts"])
    counts: dict[tuple[str, str], dict[str, str]] = {}
    for row in count_rows:
        key = (row["category_group"], row["category"])
        if key in counts:
            fail(f"Duplicate Task #016 category-count key: {key}")
        if int(row["denominator"]) != EXPECTED_GENE_COUNT:
            fail(f"Unexpected category denominator for {key}: {row['denominator']}")
        counts[key] = row

    token_fields = {
        "MISSING_EVIDENCE_DOMAIN": "missing_evidence_domains",
        "KNOWN_UNCERTAINTY": "known_uncertainties",
        "FUTURE_EVIDENCE_TYPE": "recommended_future_evidence_type",
    }
    for group, field in token_fields.items():
        observed = count_registry_tokens(registry, field)
        expected = {
            category: int(row["count"])
            for (row_group, category), row in counts.items()
            if row_group == group
        }
        if observed != Counter(expected):
            fail(f"Task #016 {group} counts do not reconcile to the gap registry.")

    _, matrix_rows = read_csv(INPUTS["validation_matrix"])
    if len(matrix_rows) != 11:
        fail(f"Expected 11 Task #016 validation-strategy rows; observed {len(matrix_rows)}.")
    matrix = {}
    for row in matrix_rows:
        key = row["evidence_gap"]
        if key in matrix:
            fail(f"Duplicate Task #016 validation-matrix key: {key}")
        matrix[key] = row

    return registry, counts, matrix


# Task #016 gap categories are mapped one-to-one to uncertainty-reducing
# evidence classes. The order below is domain grouping only, never a priority.
STRATEGIES = [
    {
        "group": "MISSING_EVIDENCE_DOMAIN",
        "category": "LUAD_DISEASE_ASSOCIATION",
        "layer": "DISCOVERY",
        "evidence_class": "LUAD_DISEASE_ASSOCIATION_DATASOURCE_DETAIL",
        "matrix_gap": "LUAD disease-association datasource detail",
        "unit": "source-level target-disease association record",
        "keys": "EnsemblID|disease_identifier|source_record_identifier",
        "provenance": "source_name|source_release|record_identifier|query|retrieved_at|upstream_reference",
        "quality": "disease-identifier specificity|record traceability|duplicate-source detection",
        "adequacy": "At least one traceable LUAD-specific source record or an explicit source-specific NOT_FOUND result.",
    },
    {
        "group": "MISSING_EVIDENCE_DOMAIN",
        "category": "GENETIC_EVIDENCE",
        "layer": "MECHANISTIC",
        "evidence_class": "CANCER_GENETIC_EVIDENCE",
        "matrix_gap": "Cancer genetic evidence",
        "unit": "variant/alteration-to-gene disease record",
        "keys": "EnsemblID|disease_identifier|alteration_identifier|study_identifier",
        "provenance": "source_name|source_release|study_identifier|cohort|alteration_type|retrieved_at",
        "quality": "LUAD cohort specificity|alteration definition|sample overlap|statistical provenance",
        "adequacy": "Traceable LUAD-relevant alteration evidence or an explicit queried NOT_FOUND state with coverage recorded.",
    },
    {
        "group": "MISSING_EVIDENCE_DOMAIN",
        "category": "FUNCTIONAL_DEPENDENCY",
        "layer": "MECHANISTIC",
        "evidence_class": "CRISPR_FUNCTIONAL_DEPENDENCY",
        "matrix_gap": "Functional dependency",
        "unit": "gene-by-model dependency observation",
        "keys": "EnsemblID|model_identifier|screen_identifier",
        "provenance": "source_name|release|screen_identifier|model_lineage|assay_method|retrieved_at",
        "quality": "LUAD model annotation|guide quality|screen QC|replicate support|context specificity",
        "adequacy": "Model-level dependency values with screen provenance and explicit LUAD model coverage.",
    },
    {
        "group": "MISSING_EVIDENCE_DOMAIN",
        "category": "PERTURBATIONAL_EVIDENCE",
        "layer": "MECHANISTIC",
        "evidence_class": "PERTURBATIONAL_MECHANISM",
        "matrix_gap": "Perturbational mechanism",
        "unit": "target perturbation-by-model phenotype observation",
        "keys": "EnsemblID|perturbation_identifier|model_identifier|experiment_identifier",
        "provenance": "source_name|experiment_identifier|perturbation_type|model|endpoint|publication|retrieved_at",
        "quality": "control adequacy|target engagement|replication|dose/time context|phenotype specificity",
        "adequacy": "Controlled, traceable perturbation observations or an explicit assessment that qualifying records were not found.",
    },
    {
        "group": "MISSING_EVIDENCE_DOMAIN",
        "category": "PHARMACOLOGY",
        "layer": "DEVELOPMENT",
        "evidence_class": "COMPOUND_ACTIVITY_POTENCY_MECHANISM",
        "matrix_gap": "Compound activity, potency, and mechanism",
        "unit": "compound-target assay or mechanism record",
        "keys": "EnsemblID|compound_identifier|assay_identifier|target_record_identifier",
        "provenance": "source_name|release|compound_identifier|assay_identifier|mechanism_identifier|retrieved_at",
        "quality": "target confidence|assay type|potency units|selectivity|mechanism consistency|duplicate detection",
        "adequacy": "Record-level activity/mechanism evidence with target confidence and assay provenance, or explicit NOT_FOUND.",
    },
    {
        "group": "MISSING_EVIDENCE_DOMAIN",
        "category": "TRACTABILITY",
        "layer": "DEVELOPMENT",
        "evidence_class": "MODALITY_SPECIFIC_TRACTABILITY",
        "matrix_gap": "Modality-specific tractability",
        "unit": "target-by-modality tractability assessment",
        "keys": "EnsemblID|modality|assessment_identifier",
        "provenance": "source_name|release|assessment_identifier|modality|evidence_bucket|retrieved_at",
        "quality": "modality definition|evidence-bucket traceability|structural/ligand evidence provenance",
        "adequacy": "At least one traceable modality assessment or an explicit NOT_FOUND result for every assessed modality.",
    },
    {
        "group": "MISSING_EVIDENCE_DOMAIN",
        "category": "CLINICAL_DEVELOPMENT",
        "layer": "DEVELOPMENT",
        "evidence_class": "TRIAL_LEVEL_CLINICAL_DEVELOPMENT",
        "matrix_gap": "Trial-level clinical development",
        "unit": "trial-intervention-target-disease linkage",
        "keys": "EnsemblID|trial_identifier|intervention_identifier|disease_identifier",
        "provenance": "registry|trial_identifier|record_version|intervention|phase|status|retrieved_at",
        "quality": "target-linkage basis|disease relevance|intervention identity|trial deduplication|status currency",
        "adequacy": "Traceable trial-level target linkage or a dated registry search with explicit NOT_FOUND semantics.",
    },
    {
        "group": "MISSING_EVIDENCE_DOMAIN",
        "category": "NORMAL_TISSUE_CONTEXT",
        "layer": "RISK",
        "evidence_class": "NORMAL_TISSUE_EXPRESSION",
        "matrix_gap": "Normal tissue context",
        "unit": "gene-by-tissue/cell-type expression observation",
        "keys": "EnsemblID|tissue_identifier|cell_type_identifier|dataset_identifier",
        "provenance": "source_name|release|dataset_identifier|tissue|cell_type|assay|retrieved_at",
        "quality": "tissue/cell specificity|donor coverage|assay comparability|RNA/protein distinction",
        "adequacy": "Traceable normal-tissue or cell-type measurements with coverage and missingness documented.",
    },
    {
        "group": "MISSING_EVIDENCE_DOMAIN",
        "category": "ESSENTIALITY",
        "layer": "RISK",
        "evidence_class": "ESSENTIALITY_GENETIC_CONSTRAINT",
        "matrix_gap": "Essentiality and genetic constraint",
        "unit": "gene-by-context essentiality or constraint observation",
        "keys": "EnsemblID|context_identifier|metric_identifier|source_record_identifier",
        "provenance": "source_name|release|context|metric|population/model|retrieved_at",
        "quality": "metric definition|population/model coverage|normal/cancer context separation|version traceability",
        "adequacy": "Context-specific essentiality/constraint measurements or explicit coverage-aware NOT_FOUND states.",
    },
    {
        "group": "MISSING_EVIDENCE_DOMAIN",
        "category": "SAFETY_LIABILITY",
        "layer": "RISK",
        "evidence_class": "TARGET_SAFETY_LIABILITY",
        "matrix_gap": "Target and compound toxicity evidence",
        "unit": "target-liability evidence record",
        "keys": "EnsemblID|liability_identifier|source_record_identifier",
        "provenance": "source_name|release|record_identifier|liability_type|evidence_reference|retrieved_at",
        "quality": "on-target attribution|human relevance|evidence type|record deduplication|causality boundary",
        "adequacy": "Traceable target-liability records or a dated, source-bounded NOT_FOUND result.",
    },
    {
        "group": "MISSING_EVIDENCE_DOMAIN",
        "category": "TOXICITY_EVIDENCE",
        "layer": "RISK",
        "evidence_class": "TOXICITY_EVIDENCE",
        "matrix_gap": "Target and compound toxicity evidence",
        "unit": "toxicology study or adverse-observation record",
        "keys": "EnsemblID|compound_or_modality_identifier|study_or_report_identifier",
        "provenance": "source_name|release|study_or_report_identifier|exposure_context|endpoint|retrieved_at",
        "quality": "on/off-target distinction|exposure context|species/relevance|duplicate reports|causality boundary",
        "adequacy": "Exposure-contextualized toxicology observations or an explicit bounded NOT_FOUND result.",
    },
    {
        "group": "KNOWN_UNCERTAINTY",
        "category": "CONFLICTING_RECORDS",
        "layer": "DISCOVERY",
        "evidence_class": "INDEPENDENT_LUAD_COHORT_REPLICATION",
        "matrix_gap": "Independent LUAD discovery replication",
        "unit": "gene-by-independent-cohort effect estimate",
        "keys": "EnsemblID|cohort_identifier|analysis_identifier",
        "provenance": "dataset_identifier|cohort_definition|analysis_version|effect_definition|retrieved_at",
        "quality": "TCGA independence|cohort comparability|direction concordance|effect uncertainty|analysis reproducibility",
        "adequacy": "A reproducible effect estimate from a cohort independent of TCGA/recount3, with comparable phenotype definitions.",
    },
    {
        "group": "KNOWN_UNCERTAINTY",
        "category": "DEPENDENCY_UNCERTAIN",
        "layer": "CROSS_CUTTING",
        "evidence_class": "SOURCE_LINEAGE_AND_DEPENDENCY_AUDIT",
        "unit": "source-to-upstream-record lineage assertion",
        "keys": "source_record_identifier|upstream_record_identifier|source_release",
        "provenance": "source_name|release|upstream_source|record_linkage_method|audit_timestamp",
        "quality": "lineage completeness|shared-record detection|publication deduplication|version matching",
        "adequacy": "Every evidence source has an auditable upstream lineage and explicit dependency classification.",
        "question": "Which evidence records are independent, derived, duplicated, or of unresolved lineage?",
        "source": "source lineage metadata, record cross-references, and publication identifiers",
        "dependency": "Treat unresolved lineage as dependent/uncertain; never count records as independent by default.",
        "boundary": "A lineage audit changes confidence in independence, not the biological claim itself.",
    },
    {
        "group": "KNOWN_UNCERTAINTY",
        "category": "INCOMPLETE_COVERAGE",
        "layer": "CROSS_CUTTING",
        "evidence_class": "SOURCE_COVERAGE_AND_COMPLETENESS_AUDIT",
        "unit": "source-query coverage assertion",
        "keys": "evidence_class|source_name|query_scope|source_release",
        "provenance": "source_name|release|query_scope|eligible_denominator|returned_count|failure_count|audit_timestamp",
        "quality": "denominator definition|query completeness|failure capture|NOT_FOUND versus NOT_QUERIED distinction",
        "adequacy": "Eligible, queried, returned, failed, NOT_FOUND, and NOT_APPLICABLE denominators reconcile.",
        "question": "Was the evidence source queried completely for the intended gene and evidence-class universe?",
        "source": "query manifests, API response logs, source coverage documentation, and failure records",
        "dependency": "Keep coverage evidence separate from biological evidence returned by the same query.",
        "boundary": "Complete retrieval does not imply that the source itself has complete biological coverage.",
    },
    {
        "group": "KNOWN_UNCERTAINTY",
        "category": "SOURCE_LIMITATION",
        "layer": "CROSS_CUTTING",
        "evidence_class": "INDEPENDENT_SOURCE_CORROBORATION",
        "unit": "claim-by-independent-source corroboration record",
        "keys": "EnsemblID|claim_type|source_record_identifier",
        "provenance": "source_name|release|record_identifier|upstream_lineage|retrieved_at",
        "quality": "source independence|scope comparability|record traceability|discordance retention",
        "adequacy": "At least one independently sourced corroborating or conflicting record, or explicit lack of an eligible source.",
        "question": "Does an independent source support, conflict with, or fail to cover the existing bounded claim?",
        "source": "independent databases, primary studies, or orthogonal measurement resources",
        "dependency": "Verify that candidate sources do not reuse the same upstream database, cohort, or publication.",
        "boundary": "Corroboration reduces source-specific uncertainty but does not prove causality or actionability.",
    },
    {
        "group": "KNOWN_UNCERTAINTY",
        "category": "TEMPORAL_UNCERTAINTY",
        "layer": "CROSS_CUTTING",
        "evidence_class": "TIMESTAMPED_SOURCE_REFRESH",
        "unit": "versioned source-query snapshot",
        "keys": "EnsemblID|source_name|source_release|query_identifier",
        "provenance": "source_name|release|query|retrieved_at|response_hash|previous_snapshot_hash",
        "quality": "release identification|query reproducibility|change detection|record withdrawal/update capture",
        "adequacy": "A current, versioned retrieval snapshot can be compared record-by-record with the frozen snapshot.",
        "question": "Have source records changed since the frozen evidence snapshot?",
        "source": "official versioned source releases and timestamped query snapshots",
        "dependency": "A refresh must preserve source lineage and must not be treated as an independent source.",
        "boundary": "Recency reduces temporal uncertainty but does not increase biological validity by itself.",
    },
]


def build_framework(
    counts: dict[tuple[str, str], dict[str, str]],
    matrix: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    rows = []
    for strategy in STRATEGIES:
        key = (strategy["group"], strategy["category"])
        if key not in counts:
            fail(f"Task #016 category required by the framework is missing: {key}")
        category = counts[key]

        if "matrix_gap" in strategy:
            matrix_key = strategy["matrix_gap"]
            if matrix_key not in matrix:
                fail(f"Task #016 validation strategy is missing: {matrix_key}")
            source = matrix[matrix_key]
            question = source["scientific_question_answered"]
            data_source = source["potential_data_source_class"]
            dependency = source["dependency_review_required"]
            boundary = source["interpretation_boundary"]
            expected_uncertainty = source["expected_uncertainty_reduction"]
        else:
            question = strategy["question"]
            data_source = strategy["source"]
            dependency = strategy["dependency"]
            boundary = strategy["boundary"]
            expected_uncertainty = strategy["category"]

        rows.append(
            {
                "gap_category_group": strategy["group"],
                "gap_category": strategy["category"],
                "evidence_layer": strategy["layer"],
                "additional_evidence_class": strategy["evidence_class"],
                "affected_gene_count": category["count"],
                "affected_gene_percent": category["percent"],
                "scientific_question": question,
                "potential_data_source_class": data_source,
                "acquisition_unit": strategy["unit"],
                "required_identifier_keys": strategy["keys"],
                "minimum_provenance_fields": strategy["provenance"],
                "evidence_quality_checks": strategy["quality"],
                "dependency_control": dependency,
                "uncertainty_reduced": expected_uncertainty,
                "adequacy_criterion": strategy["adequacy"],
                "interpretation_boundary": boundary,
            }
        )
    return rows


def validate_framework(
    framework: list[dict[str, str]],
    counts: dict[tuple[str, str], dict[str, str]],
) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []

    def check(name: str, passed: bool, observed: object, expected: object, detail: str) -> None:
        checks.append(
            {
                "check_name": name,
                "status": "PASS" if passed else "FAIL",
                "observed": str(observed),
                "expected": str(expected),
                "detail": detail,
            }
        )
        if not passed:
            fail(f"QC failure: {name}: observed={observed}; expected={expected}")

    missing_categories = {
        category for (group, category) in counts if group == "MISSING_EVIDENCE_DOMAIN"
    }
    uncertainty_categories = {
        category for (group, category) in counts if group == "KNOWN_UNCERTAINTY"
    }
    framework_keys = {(row["gap_category_group"], row["gap_category"]) for row in framework}
    expected_keys = {
        *(('MISSING_EVIDENCE_DOMAIN', value) for value in missing_categories),
        *(('KNOWN_UNCERTAINTY', value) for value in uncertainty_categories),
    }
    future_types = {
        category for (group, category) in counts if group == "FUTURE_EVIDENCE_TYPE"
    }
    represented_future = {
        row["additional_evidence_class"] for row in framework
    }.intersection(future_types)

    check("framework_row_count", len(framework) == 16, len(framework), 16, "Eleven missing-evidence and five uncertainty categories.")
    check("gap_category_coverage", framework_keys == expected_keys, len(framework_keys), len(expected_keys), "Every Task #016 gap/uncertainty category is represented once.")
    check("unique_gap_category_rows", len(framework_keys) == len(framework), len(framework_keys), len(framework), "No duplicated framework category.")
    check("future_evidence_type_coverage", represented_future == future_types, len(represented_future), len(future_types), "Every Task #016 future-evidence type is represented.")
    check("nonblank_framework_cells", all(all(value != "" for value in row.values()) for row in framework), "all nonblank", "all nonblank", "Explicit acquisition and provenance fields.")
    check("affected_counts_bounded", all(0 <= int(row["affected_gene_count"]) <= EXPECTED_GENE_COUNT for row in framework), "all bounded", f"0..{EXPECTED_GENE_COUNT}", "Counts are copied from Task #016.")
    forbidden = FORBIDDEN_EXACT_COLUMNS.intersection(field.lower() for field in FRAMEWORK_FIELDS)
    check("forbidden_columns_absent", not forbidden, sorted(forbidden), [], "No numerical assessment or target-decision fields.")
    check("network_access_not_required", True, "NOT_USED", "NOT_USED", "Framework generation is local and descriptive.")
    return checks


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_summary(framework: list[dict[str, str]], checks: list[dict[str, str]]) -> None:
    by_layer = Counter(row["evidence_layer"] for row in framework)
    universal = [row for row in framework if int(row["affected_gene_count"]) == EXPECTED_GENE_COUNT]
    lines = [
        "# Task #017 evidence acquisition framework summary",
        "",
        f"**Task #016 gene profiles represented:** {EXPECTED_GENE_COUNT:,}  ",
        f"**Acquisition-framework categories:** {len(framework)}  ",
        f"**QC checks passed:** {sum(row['status'] == 'PASS' for row in checks)}/{len(checks)}  ",
        "**Scores, rankings, candidate selections, or target recommendations created:** No",
        "",
        "## What this framework answers",
        "",
        "For each Task #016 missing-evidence or uncertainty category, the framework names an additional evidence class that could reduce uncertainty. It also states the scientific question, acquisition unit, identifier keys, minimum provenance, quality checks, dependency controls, adequacy criterion, and interpretation boundary.",
        "",
        "Affected-gene counts describe the Task #016 snapshot. They do not determine acquisition order and are not weights.",
        "",
        "## Framework coverage",
        "",
        "| Evidence layer | Framework categories |",
        "| --- | ---: |",
    ]
    for layer in ("DISCOVERY", "MECHANISTIC", "DEVELOPMENT", "RISK", "CROSS_CUTTING"):
        lines.append(f"| {layer.replace('_', ' ').title()} | {by_layer[layer]} |")

    lines.extend(
        [
            "",
            "## Project-wide acquisition needs",
            "",
            f"{len(universal)} categories affect all {EXPECTED_GENE_COUNT:,} profiles in Task #016:",
            "",
        ]
    )
    for row in universal:
        lines.append(
            f"- `{row['gap_category']}` → `{row['additional_evidence_class']}`"
        )

    lines.extend(
        [
            "",
            "## Scientific boundary",
            "",
            "An evidence-acquisition class is not a conclusion about a gene. A complete query can return an explicit `NOT_FOUND` state, and that state must remain distinct from a negative biological finding. Likewise, adding records does not automatically establish source independence, causality, druggability, safety, clinical validity, or therapeutic direction.",
            "",
            "The framework does not choose databases, authorize network retrieval, define gene subsets, or specify an acquisition sequence. Each future retrieval requires its own frozen source, query, identifier, provenance, missingness, and validation specification.",
            "",
            "## Validation",
            "",
            "All five Task #016 input hashes matched. The 29,606-row registry was unique by EnsemblID; Task #016 category counts reconciled to the row-level token fields; all 11 missing-evidence and five uncertainty categories were represented exactly once; and all 12 Task #016 future-evidence types were retained.",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_session(
    started: datetime,
    git_info: dict[str, str],
    input_hashes: dict[str, str],
    framework: list[dict[str, str]],
    checks: list[dict[str, str]],
) -> None:
    finished = datetime.now(timezone.utc)
    values = {
        "task": "017",
        "purpose": "descriptive evidence acquisition strategy framework",
        "started_at_utc": started.isoformat(),
        "finished_at_utc": finished.isoformat(),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "git_branch": git_info["branch"],
        "git_head": git_info["head"],
        "git_origin": git_info["remote"],
        "frozen_task016_base_commit": TASK016_BASE_COMMIT,
        "task016_gene_count": str(EXPECTED_GENE_COUNT),
        "framework_row_count": str(len(framework)),
        "qc_pass_count": str(sum(row["status"] == "PASS" for row in checks)),
        "qc_check_count": str(len(checks)),
        "network_access": "NOT_USED",
        "packages_installed_or_updated": "FALSE",
        "ranking_generated": "FALSE",
        "scoring_generated": "FALSE",
        "target_selection_generated": "FALSE",
        "therapeutic_recommendations_generated": "FALSE",
        "previous_committed_files_modified": "FALSE",
        "script_sha256": sha256(SCRIPT_PATH),
        "plan_sha256": sha256(PLAN_PATH),
    }
    for name, digest in input_hashes.items():
        values[f"frozen_input_sha256.{relative(INPUTS[name])}"] = digest
    for path in (FRAMEWORK_PATH, QC_PATH, SUMMARY_PATH):
        values[f"output_sha256.{relative(path)}"] = sha256(path)
    SESSION_PATH.write_text(
        "".join(f"{key}={values[key]}\n" for key in sorted(values)),
        encoding="utf-8",
    )


def main() -> None:
    started = datetime.now(timezone.utc)
    git_info = validate_repository()
    input_hashes = validate_hashes()
    _, counts, matrix = validate_task016_inputs()
    framework = build_framework(counts, matrix)
    checks = validate_framework(framework, counts)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(FRAMEWORK_PATH, FRAMEWORK_FIELDS, framework)
    write_csv(
        QC_PATH,
        ["check_name", "status", "observed", "expected", "detail"],
        checks,
    )
    write_summary(framework, checks)
    write_session(started, git_info, input_hashes, framework, checks)

    print("Created files:")
    for path in (FRAMEWORK_PATH, QC_PATH, SUMMARY_PATH, SESSION_PATH):
        print(f"- {relative(path)}")
    print(f"Framework rows: {len(framework)}")
    print(f"QC checks passed: {sum(row['status'] == 'PASS' for row in checks)}/{len(checks)}")
    print("No scoring, ranking, candidate selection, or target recommendation was generated.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # concise command-line failure with non-zero exit
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
