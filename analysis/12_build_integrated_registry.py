#!/usr/bin/env python3
"""Build the Task #012 one-gene-per-row integrated evidence registry."""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPECTED_ROWS = 29_606
EXPECTED_U2 = 14_064

CANDIDATE_INPUT = Path("outputs/candidate_registry/candidate_registry.csv")
MAPPING_INPUT = Path("outputs/identifier_normalization/identifier_mapping.csv")
EVIDENCE_INPUT = Path("outputs/evidence_layer/evidence_registry.csv")
TRACTABILITY_SAFETY_INPUT = Path(
    "outputs/tractability_safety/tractability_safety_registry.csv"
)
INPUT_HASHES = {
    CANDIDATE_INPUT: "8055a9d99d058d219399957e62f6a3cccc3dd2217bc028d1d11dd4dc667f90e2",
    MAPPING_INPUT: "ff50b9cc50006710e681bd0d0f21fa3790becc3cd20a476dbbb6ac5459c1594e",
    EVIDENCE_INPUT: "13b6db140c920a60ae3f827ac9df4c4e08916472aa8daafb349acd3a60192405",
    TRACTABILITY_SAFETY_INPUT: "83d085383c60ecc68815ad02c12ae74ef52e67a45501880581bc53276b658f84",
}

SCRIPT = Path("analysis/12_build_integrated_registry.py")
PLAN = Path("docs/integrated_registry_plan_v0.1.md")
OUTPUT_DIR = Path("outputs/integrated_registry")
REGISTRY = OUTPUT_DIR / "integrated_target_registry.csv"
QC = OUTPUT_DIR / "integrated_registry_qc.csv"
SUMMARY = OUTPUT_DIR / "integrated_registry_summary.md"
SESSION = OUTPUT_DIR / "session_info.txt"

IDENTITY_FIELDS = ["EnsemblID", "EnsemblID_base", "Symbol", "gene_type"]
CANDIDATE_PLACEHOLDER_ID_FIELDS = [
    "HGNC_ID",
    "UniProt_ID",
    "OpenTargets_target_ID",
    "ChEMBL_target_ID",
]
CANDIDATE_EVIDENCE_FIELDS = [
    "U0_tested",
    "U1_DE",
    "U2_effect_supported_DE",
    "effect_band",
    "biotype_track",
    "retrieval_queue",
    "logFC_S0",
    "FDR_S0",
    "P_value_S0",
    "AveExpr_S0",
    "mean_logCPM_Tumor",
    "mean_logCPM_Normal",
    "logFC_S1",
    "FDR_S1",
    "logFC_S2",
    "FDR_S2",
    "logFC_S3",
    "FDR_S3",
    "logFC_S4",
    "FDR_S4",
    "logFC_S5",
    "FDR_S5",
    "logFC_S6",
    "FDR_S6",
    "sign_S0",
    "sign_concordant_S1_S6_count",
    "sign_concordant_all_S1_S6",
    "n_sensitivity_FDR05",
    "median_abs_delta_logFC_vs_S0",
    "max_abs_delta_logFC_vs_S0",
    "S6_sign_flip_vs_S0",
    "model_dependent_any_top50",
    "model_dependent_models",
    "reduced_residual_df_any",
    "reduced_residual_df_models",
    "max_residual_df_loss",
]
MAPPING_FIELDS = [
    "HGNC_ID",
    "HGNC_ID_status",
    "HGNC_ID_source",
    "Entrez_ID",
    "Entrez_ID_status",
    "Entrez_ID_source",
    "UniProt_ID",
    "UniProt_ID_status",
    "UniProt_ID_source",
    "OpenTargets_target_ID",
    "OpenTargets_target_ID_status",
    "OpenTargets_target_ID_source",
    "ChEMBL_target_ID",
    "ChEMBL_target_ID_status",
    "ChEMBL_target_ID_source",
    "ChEMBL_mapping_basis",
    "ChEMBL_matched_UniProt_ID",
    "current_HGNC_symbol",
    "symbol_qc_status",
    "one_to_many_fields",
    "ambiguous_mapping",
    "ambiguous_fields",
    "mapping_note",
]
EXTERNAL_EVIDENCE_FIELDS = [
    "ot_target_retrieval_status",
    "ot_target_approved_name",
    "ot_target_approved_symbol",
    "ot_target_biotype",
    "ot_literature_occurrence_count",
    "ot_literature_filtered_count",
    "ot_drug_clinical_candidate_record_count",
    "ot_target_annotation_source",
    "ot_luad_disease_id",
    "ot_luad_disease_name",
    "ot_luad_direct_association_status",
    "ot_luad_direct_association_count",
    "ot_luad_direct_association_score_native",
    "ot_luad_direct_datasource_scores_native_json",
    "ot_luad_direct_datatype_scores_native_json",
    "ot_luad_indirect_association_status",
    "ot_luad_indirect_association_count",
    "ot_luad_indirect_association_score_native",
    "ot_luad_association_source",
    "chembl_target_retrieval_status",
    "chembl_target_record_count",
    "chembl_target_annotations_json",
    "chembl_target_annotation_source",
]
TRACTABILITY_SAFETY_FIELDS = [
    "tractability_retrieval_status",
    "tractability_record_count",
    "tractability_true_assessment_count",
    "tractability_true_SM_count",
    "tractability_true_AB_count",
    "tractability_true_PR_count",
    "tractability_true_OC_count",
    "tractability_true_assessment_ids_by_modality_json",
    "safety_retrieval_status",
    "safety_liability_record_count",
]
OUTPUT_FIELDS = (
    IDENTITY_FIELDS
    + MAPPING_FIELDS
    + CANDIDATE_EVIDENCE_FIELDS
    + EXTERNAL_EVIDENCE_FIELDS
    + TRACTABILITY_SAFETY_FIELDS
    + [
        "tractability_safety_source_name",
        "tractability_safety_source_release",
        "integrated_missingness_status_json",
    ]
)

# These exact project-defined field names are prohibited. Source-native Open
# Targets fields ending in `_score_native` are retained as upstream evidence
# and are explicitly not project scores.
FORBIDDEN_EXACT_FIELDS = {
    "score",
    "ranking",
    "priority",
    "rank",
    "recommendation",
    "therapeutic_direction",
    "target_selection",
}


def fail(message: str) -> None:
    raise RuntimeError(message)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def deterministic_json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True, ensure_ascii=False)


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.is_file():
        fail(f"Required frozen input is missing: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            fail(f"CSV has no header: {path}")
        return list(reader.fieldnames), list(reader)


def validate_hashes() -> dict[str, str]:
    observed: dict[str, str] = {}
    for path, expected in INPUT_HASHES.items():
        value = file_sha256(path)
        observed[str(path)] = value
        if value != expected:
            fail(f"Frozen input hash mismatch for {path}: {value} != {expected}")
    return observed


def require_fields(label: str, header: list[str], fields: list[str]) -> None:
    missing = set(fields).difference(header)
    if missing:
        fail(f"{label} lacks required fields: {sorted(missing)}")


def index_layer(
    label: str, header: list[str], rows: list[dict[str, str]], required: list[str]
) -> tuple[list[str], dict[str, dict[str, str]]]:
    require_fields(label, header, required)
    if len(rows) != EXPECTED_ROWS:
        fail(f"{label} has {len(rows)} rows; expected {EXPECTED_ROWS}")
    identifiers = [row["EnsemblID"] for row in rows]
    if len(set(identifiers)) != EXPECTED_ROWS:
        duplicates = [key for key, count in Counter(identifiers).items() if count > 1]
        fail(f"{label} contains duplicate EnsemblID values: {duplicates[:10]}")
    if any(not identifier for identifier in identifiers):
        fail(f"{label} contains an empty EnsemblID")
    return identifiers, {row["EnsemblID"]: row for row in rows}


def explicit_value(value: str, *, empty_token: str = "NOT_AVAILABLE") -> str:
    return empty_token if value == "" else value


def validate_inputs() -> tuple[
    list[dict[str, str]],
    dict[str, dict[str, str]],
    dict[str, dict[str, str]],
    dict[str, dict[str, str]],
]:
    candidate_header, candidate_rows = read_csv(CANDIDATE_INPUT)
    mapping_header, mapping_rows = read_csv(MAPPING_INPUT)
    evidence_header, evidence_rows = read_csv(EVIDENCE_INPUT)
    tract_header, tract_rows = read_csv(TRACTABILITY_SAFETY_INPUT)

    candidate_ids, _ = index_layer(
        "Task #008 candidate registry",
        candidate_header,
        candidate_rows,
        IDENTITY_FIELDS + CANDIDATE_PLACEHOLDER_ID_FIELDS + CANDIDATE_EVIDENCE_FIELDS,
    )
    mapping_ids, mapping = index_layer(
        "Task #009 identifier mapping",
        mapping_header,
        mapping_rows,
        IDENTITY_FIELDS + MAPPING_FIELDS,
    )
    evidence_ids, evidence = index_layer(
        "Task #010 evidence registry",
        evidence_header,
        evidence_rows,
        IDENTITY_FIELDS
        + ["U2_effect_supported_DE", "OpenTargets_target_ID", "ChEMBL_target_ID"]
        + EXTERNAL_EVIDENCE_FIELDS,
    )
    tract_ids, tractability_safety = index_layer(
        "Task #011 tractability/safety registry",
        tract_header,
        tract_rows,
        IDENTITY_FIELDS
        + ["U2_effect_supported_DE", "OpenTargets_target_ID"]
        + TRACTABILITY_SAFETY_FIELDS
        + ["source_name", "source_release"],
    )

    if not (candidate_ids == mapping_ids == evidence_ids == tract_ids):
        fail("Frozen inputs differ in EnsemblID identity or row order")

    for row in candidate_rows:
        for field in CANDIDATE_PLACEHOLDER_ID_FIELDS:
            if row[field] != "NOT_RETRIEVED":
                fail(
                    f"Task #008 placeholder {field} changed at {row['EnsemblID']}: "
                    f"{row[field]!r}"
                )

    for candidate in candidate_rows:
        ensembl_id = candidate["EnsemblID"]
        mapped = mapping[ensembl_id]
        external = evidence[ensembl_id]
        target = tractability_safety[ensembl_id]
        for field in ("EnsemblID_base", "Symbol", "gene_type"):
            values = {candidate[field], mapped[field], external[field], target[field]}
            if len(values) != 1:
                fail(f"Cross-layer identity mismatch for {field} at {ensembl_id}: {values}")
        if candidate["U2_effect_supported_DE"] != external["U2_effect_supported_DE"]:
            fail(f"Task #008/#010 U2 mismatch at {ensembl_id}")
        if candidate["U2_effect_supported_DE"] != target["U2_effect_supported_DE"]:
            fail(f"Task #008/#011 U2 mismatch at {ensembl_id}")
        if candidate["U2_effect_supported_DE"] not in {"TRUE", "FALSE"}:
            fail(f"Invalid U2 value at {ensembl_id}")
        for field in ("OpenTargets_target_ID", "ChEMBL_target_ID"):
            if mapped[field] != external[field]:
                fail(f"Task #009/#010 {field} mismatch at {ensembl_id}")
        if mapped["OpenTargets_target_ID"] != target["OpenTargets_target_ID"]:
            fail(f"Task #009/#011 OpenTargets_target_ID mismatch at {ensembl_id}")

        if candidate["model_dependent_models"] == "" and candidate["model_dependent_any_top50"] != "FALSE":
            fail(f"Blank model_dependent_models is not explained by FALSE at {ensembl_id}")
        if candidate["reduced_residual_df_models"] == "" and candidate["reduced_residual_df_any"] != "FALSE":
            fail(f"Blank reduced_residual_df_models is not explained by FALSE at {ensembl_id}")

    u2_count = sum(row["U2_effect_supported_DE"] == "TRUE" for row in candidate_rows)
    if u2_count != EXPECTED_U2:
        fail(f"Task #008 contains {u2_count} U2 genes; expected {EXPECTED_U2}")
    if len(OUTPUT_FIELDS) != len(set(OUTPUT_FIELDS)):
        fail("Integrated output schema contains duplicate field names")
    forbidden = FORBIDDEN_EXACT_FIELDS.intersection(
        field.lower() for field in OUTPUT_FIELDS
    )
    if forbidden:
        fail(f"Integrated output contains forbidden exact fields: {sorted(forbidden)}")
    return candidate_rows, mapping, evidence, tractability_safety


def build_registry(
    candidates: list[dict[str, str]],
    mapping: dict[str, dict[str, str]],
    evidence: dict[str, dict[str, str]],
    tractability_safety: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for candidate in candidates:
        ensembl_id = candidate["EnsemblID"]
        mapped = mapping[ensembl_id]
        external = evidence[ensembl_id]
        target = tractability_safety[ensembl_id]
        row: dict[str, str] = {field: candidate[field] for field in IDENTITY_FIELDS}
        for field in MAPPING_FIELDS:
            row[field] = explicit_value(
                mapped[field], empty_token="NONE" if field == "mapping_note" else "NOT_AVAILABLE"
            )
        for field in CANDIDATE_EVIDENCE_FIELDS:
            if field == "model_dependent_models" and candidate[field] == "":
                row[field] = "NONE"
            elif field == "reduced_residual_df_models" and candidate[field] == "":
                row[field] = "NONE"
            else:
                row[field] = explicit_value(candidate[field])
        for field in EXTERNAL_EVIDENCE_FIELDS:
            row[field] = explicit_value(external[field])
        for field in TRACTABILITY_SAFETY_FIELDS:
            row[field] = explicit_value(target[field])
        row["tractability_safety_source_name"] = explicit_value(target["source_name"])
        row["tractability_safety_source_release"] = explicit_value(target["source_release"])
        row["integrated_missingness_status_json"] = deterministic_json(
            {
                "ChEMBL_mapping": mapped["ChEMBL_target_ID_status"],
                "ChEMBL_target_annotation": external["chembl_target_retrieval_status"],
                "Entrez_mapping": mapped["Entrez_ID_status"],
                "HGNC_mapping": mapped["HGNC_ID_status"],
                "OpenTargets_LUAD_direct_association": external[
                    "ot_luad_direct_association_status"
                ],
                "OpenTargets_LUAD_indirect_association": external[
                    "ot_luad_indirect_association_status"
                ],
                "OpenTargets_mapping": mapped["OpenTargets_target_ID_status"],
                "OpenTargets_target_annotation": external["ot_target_retrieval_status"],
                "UniProt_mapping": mapped["UniProt_ID_status"],
                "safety_liability": target["safety_retrieval_status"],
                "tractability": target["tractability_retrieval_status"],
            }
        )
        if list(row) != OUTPUT_FIELDS:
            fail(f"Integrated field order mismatch at {ensembl_id}")
        if any(value == "" for value in row.values()):
            fail(f"Integrated output contains an unexplained blank at {ensembl_id}")
        output.append(row)
    return output


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        fail(f"Refusing to write empty CSV: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS if path == REGISTRY else list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def percent(numerator: int, denominator: int) -> str:
    return format(100 * numerator / denominator, ".6f") if denominator else "NOT_AVAILABLE"


def make_qc_rows(
    registry: list[dict[str, str]], observed_hashes: dict[str, str]
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    def add(
        category: str,
        scope: str,
        metric: str,
        value: int | str,
        denominator: int | str = "NOT_APPLICABLE",
        status: str = "INFO",
        detail: str = "",
    ) -> None:
        rows.append(
            {
                "category": category,
                "scope": scope,
                "metric": metric,
                "value": str(value),
                "denominator": str(denominator),
                "percent": (
                    percent(value, denominator)
                    if isinstance(value, int) and isinstance(denominator, int)
                    else "NOT_APPLICABLE"
                ),
                "status": status,
                "detail": detail,
            }
        )

    for path, expected in INPUT_HASHES.items():
        observed = observed_hashes[str(path)]
        add(
            "ASSERTION",
            "FROZEN_INPUT",
            f"SHA256_{path.name}",
            "MATCH" if observed == expected else "MISMATCH",
            status="PASS" if observed == expected else "FAIL",
            detail=f"expected={expected};observed={observed};path={path}",
        )

    ids = [row["EnsemblID"] for row in registry]
    add("ASSERTION", "ALL_TESTED", "ROW_COUNT", len(registry), EXPECTED_ROWS, "PASS" if len(registry) == EXPECTED_ROWS else "FAIL")
    add("ASSERTION", "ALL_TESTED", "UNIQUE_ENSEMBL_ID_COUNT", len(set(ids)), EXPECTED_ROWS, "PASS" if len(set(ids)) == EXPECTED_ROWS else "FAIL")
    add("ASSERTION", "ALL_TESTED", "ORIGINAL_ENSEMBL_ID_ORDER_PRESERVED", "TRUE", status="PASS")
    u2_count = sum(row["U2_effect_supported_DE"] == "TRUE" for row in registry)
    add("ASSERTION", "U2_EFFECT_SUPPORTED_DE", "GENE_COUNT", u2_count, EXPECTED_U2, "PASS" if u2_count == EXPECTED_U2 else "FAIL")
    add("ASSERTION", "ALL_TESTED", "JOIN_KEY", "EnsemblID_ONLY", status="PASS")
    add("ASSERTION", "ALL_TESTED", "GENE_SYMBOL_USED_AS_JOIN_KEY", "FALSE", status="PASS")
    add("ASSERTION", "ALL_TESTED", "BLANK_OUTPUT_CELL_COUNT", sum(value == "" for row in registry for value in row.values()), 0, "PASS")
    add("ASSERTION", "ALL_TESTED", "FORBIDDEN_EXACT_FIELD_COUNT", len(FORBIDDEN_EXACT_FIELDS.intersection(field.lower() for field in OUTPUT_FIELDS)), 0, "PASS")
    add("ASSERTION", "ALL_TESTED", "PROJECT_SCORE_OR_RANKING_GENERATED", "FALSE", status="PASS")
    add("ASSERTION", "ALL_TESTED", "THERAPEUTIC_RECOMMENDATION_GENERATED", "FALSE", status="PASS")

    for scope, selected in (
        ("ALL_TESTED", registry),
        ("U2_EFFECT_SUPPORTED_DE", [row for row in registry if row["U2_effect_supported_DE"] == "TRUE"]),
    ):
        denominator = len(selected)
        metrics = {
            "U0_TESTED_TRUE": sum(row["U0_tested"] == "TRUE" for row in selected),
            "U1_DE_TRUE": sum(row["U1_DE"] == "TRUE" for row in selected),
            "U2_EFFECT_SUPPORTED_DE_TRUE": sum(row["U2_effect_supported_DE"] == "TRUE" for row in selected),
            "SIGN_CONCORDANT_ALL_S1_S6_TRUE": sum(row["sign_concordant_all_S1_S6"] == "TRUE" for row in selected),
            "S6_SIGN_FLIP_TRUE": sum(row["S6_sign_flip_vs_S0"] == "TRUE" for row in selected),
            "MODEL_DEPENDENT_ANY_TOP50_TRUE": sum(row["model_dependent_any_top50"] == "TRUE" for row in selected),
            "HGNC_ID_MAPPED": sum(row["HGNC_ID"] != "NOT_FOUND" for row in selected),
            "ENTREZ_ID_MAPPED": sum(row["Entrez_ID"] != "NOT_FOUND" for row in selected),
            "UNIPROT_ID_MAPPED": sum(row["UniProt_ID"] != "NOT_FOUND" for row in selected),
            "OPEN_TARGETS_ID_MAPPED": sum(row["OpenTargets_target_ID"] != "NOT_FOUND" for row in selected),
            "CHEMBL_ID_MAPPED": sum(row["ChEMBL_target_ID"] != "NOT_FOUND" for row in selected),
            "OPEN_TARGETS_TARGET_PRESENT": sum(row["ot_target_retrieval_status"] == "PRESENT" for row in selected),
            "LUAD_DIRECT_ASSOCIATION_PRESENT": sum(row["ot_luad_direct_association_status"] == "PRESENT" for row in selected),
            "LUAD_INDIRECT_ASSOCIATION_PRESENT": sum(row["ot_luad_indirect_association_status"] == "PRESENT" for row in selected),
            "OPEN_TARGETS_DRUG_CANDIDATE_COUNT_NONZERO": sum(row["ot_drug_clinical_candidate_record_count"].isdigit() and int(row["ot_drug_clinical_candidate_record_count"]) > 0 for row in selected),
            "CHEMBL_TARGET_PRESENT": sum(row["chembl_target_retrieval_status"] == "PRESENT" for row in selected),
            "TRACTABILITY_RECORD_PRESENT": sum(row["tractability_retrieval_status"] == "TRACTABILITY_RECORD_PRESENT" for row in selected),
            "SAFETY_RECORD_PRESENT": sum(row["safety_retrieval_status"] == "SAFETY_RECORD_PRESENT" for row in selected),
            "TARGET_PRESENT_NO_SAFETY_RECORD_RETURNED": sum(row["safety_retrieval_status"] == "TARGET_PRESENT_NO_SAFETY_RECORD_RETURNED" for row in selected),
        }
        for metric, count in metrics.items():
            add("DESCRIPTIVE_COVERAGE", scope, metric, count, denominator)
        for field in (
            "HGNC_ID_status",
            "Entrez_ID_status",
            "UniProt_ID_status",
            "OpenTargets_target_ID_status",
            "ChEMBL_target_ID_status",
            "ot_target_retrieval_status",
            "ot_luad_direct_association_status",
            "ot_luad_indirect_association_status",
            "chembl_target_retrieval_status",
            "tractability_retrieval_status",
            "safety_retrieval_status",
        ):
            for value, count in sorted(Counter(row[field] for row in selected).items()):
                add("MISSINGNESS_STATE", scope, f"{field}::{value}", count, denominator)
    return rows


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


def write_summary(registry: list[dict[str, str]]) -> None:
    u2 = [row for row in registry if row["U2_effect_supported_DE"] == "TRUE"]
    lines = [
        "# Task #012 integrated target evidence registry summary",
        "",
        f"**Genes retained:** {len(registry):,}  ",
        f"**U2 genes retained:** {len(u2):,}  ",
        "**Immutable join key:** `EnsemblID` only",
        "",
        "## Purpose and interpretation boundary",
        "",
        "This registry joins the frozen Task #008–#011 evidence layers into one gene-level table. It preserves identity, differential-expression, robustness, identifier, Open Targets, drug/candidate, tractability, and safety evidence without ranking, scoring, prioritizing, recommending, selecting, or inferring therapeutic direction.",
        "",
        "Open Targets fields explicitly ending in `_score_native` are source-native upstream evidence values. They are not project-defined scores and were not used to order or select genes.",
        "",
        "## Integrated coverage",
        "",
    ]
    coverage: list[list[Any]] = []
    for scope, selected in (("All tested genes", registry), ("U2 genes", u2)):
        coverage.append(
            [
                scope,
                len(selected),
                sum(row["OpenTargets_target_ID"] != "NOT_FOUND" for row in selected),
                sum(row["ot_luad_direct_association_status"] == "PRESENT" for row in selected),
                sum(row["ot_drug_clinical_candidate_record_count"].isdigit() and int(row["ot_drug_clinical_candidate_record_count"]) > 0 for row in selected),
                sum(row["tractability_retrieval_status"] == "TRACTABILITY_RECORD_PRESENT" for row in selected),
                sum(row["safety_retrieval_status"] == "SAFETY_RECORD_PRESENT" for row in selected),
            ]
        )
    lines.extend(
        markdown_table(
            [
                "Scope",
                "Genes",
                "OT mapped",
                "LUAD direct association",
                "OT drug/candidate count >0",
                "Tractability record(s)",
                "Safety record(s)",
            ],
            coverage,
        )
    )
    lines.extend(["", "Identifier coverage:", ""])
    identifier_rows = []
    for field in ("HGNC_ID", "Entrez_ID", "UniProt_ID", "OpenTargets_target_ID", "ChEMBL_target_ID"):
        identifier_rows.append(
            [
                field,
                sum(row[field] != "NOT_FOUND" for row in registry),
                sum(row[field] != "NOT_FOUND" for row in u2),
            ]
        )
    lines.extend(markdown_table(["Identifier", "All mapped", "U2 mapped"], identifier_rows))

    lines.extend(
        [
            "",
            "## Robustness evidence retained",
            "",
            "The integrated table preserves the Task #008 primary DE fields and all prespecified S1–S6 robustness diagnostics, including sign concordance, sensitivity FDR counts, effect-size deviations, S6 sign flips, model-dependence flags, and residual-degrees-of-freedom flags. No new DE analysis or model fitting was performed.",
            "",
            "## Explicit missingness",
            "",
            "Source retrieval and mapping states are preserved rather than converted into negative biological evidence. Each row also contains `integrated_missingness_status_json`, which records mapping, target retrieval, LUAD association, tractability, and safety states without collapsing them.",
            "",
            "In particular, `TARGET_PRESENT_NO_SAFETY_RECORD_RETURNED` means no curated record was returned for that mapped target. It does not mean the target is safe or has low risk. Likewise, `NO_ASSOCIATION_RETURNED`, `NOT_FOUND`, `NOT_AVAILABLE`, and `TARGET_NOT_MAPPED` remain explicit evidence states rather than zero-valued evidence.",
            "",
            "Upstream empty model-set fields are represented as `NONE`; absent mapping notes are represented as `NONE`; otherwise unexplained empty cells are represented as `NOT_AVAILABLE`. No integrated output cell is blank.",
            "",
            "## Evidence-overlap boundary",
            "",
            "Open Targets tractability may incorporate ChEMBL or clinical-precedence sources. It must not automatically be treated as independent of Task #010 drug/candidate evidence or future clinical-development evidence.",
            "",
            "## Non-claims",
            "",
            "The row order is the frozen Task #008 EnsemblID order and has no ranking meaning. No project score, rank, priority, recommendation, target selection, or therapeutic direction was generated.",
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
    started: datetime, observed_hashes: dict[str, str], registry: list[dict[str, str]]
) -> None:
    metadata = {
        "task": "012",
        "purpose": "one-gene-per-row frozen evidence integration",
        "started_at_utc": started.isoformat(),
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "join_key": "EnsemblID_ONLY",
        "gene_symbols_used_as_join_keys": "FALSE",
        "network_access": "NOT_USED",
        "packages_installed_or_updated": "FALSE",
        "project_score_generated": "FALSE",
        "ranking_generated": "FALSE",
        "therapeutic_recommendation_generated": "FALSE",
        "therapeutic_direction_inferred": "FALSE",
        "row_count": len(registry),
        "unique_ensembl_id_count": len({row["EnsemblID"] for row in registry}),
        "u2_count": sum(row["U2_effect_supported_DE"] == "TRUE" for row in registry),
        "frozen_inputs": {
            str(path): {
                "expected_sha256": INPUT_HASHES[path],
                "observed_sha256": observed_hashes[str(path)],
            }
            for path in INPUT_HASHES
        },
        "script_sha256": file_sha256(SCRIPT),
        "plan_sha256": file_sha256(PLAN),
        "output_sha256": {
            str(REGISTRY): file_sha256(REGISTRY),
            str(QC): file_sha256(QC),
            str(SUMMARY): file_sha256(SUMMARY),
        },
    }
    SESSION.write_text("\n".join(flatten("", metadata)) + "\n", encoding="utf-8")


def validate_outputs(
    registry: list[dict[str, str]], qc_rows: list[dict[str, str]]
) -> None:
    if len(registry) != EXPECTED_ROWS:
        fail("Integrated registry row-count assertion failed")
    identifiers = [row["EnsemblID"] for row in registry]
    if len(set(identifiers)) != EXPECTED_ROWS:
        fail("Integrated registry EnsemblID uniqueness assertion failed")
    if sum(row["U2_effect_supported_DE"] == "TRUE" for row in registry) != EXPECTED_U2:
        fail("Integrated registry U2 assertion failed")
    if any(value == "" for row in registry for value in row.values()):
        fail("Integrated registry contains blank cells")
    if any(row["status"] == "FAIL" for row in qc_rows):
        fail("Integrated registry QC contains failed assertions")


def main() -> None:
    started = datetime.now(timezone.utc)
    observed_hashes = validate_hashes()
    candidates, mapping, evidence, tractability_safety = validate_inputs()
    registry = build_registry(candidates, mapping, evidence, tractability_safety)
    qc_rows = make_qc_rows(registry, observed_hashes)
    validate_outputs(registry, qc_rows)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(REGISTRY, registry)
    write_csv(QC, qc_rows)
    write_summary(registry)
    write_session(started, observed_hashes, registry)

    print("Created files:")
    for path in (REGISTRY, QC, SUMMARY, SESSION):
        print(f"- {path}")
    print(f"Integrated rows: {len(registry)}")
    print(f"Unique EnsemblIDs: {len({row['EnsemblID'] for row in registry})}")
    print(f"U2 genes: {sum(row['U2_effect_supported_DE'] == 'TRUE' for row in registry)}")
    print(f"QC assertions passed: {sum(row['status'] == 'PASS' for row in qc_rows)}")
    print("QC assertion failures: 0")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
