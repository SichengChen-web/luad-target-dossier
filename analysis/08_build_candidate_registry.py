#!/usr/bin/env python3
"""Build the Task #008 DE-derived candidate registry using committed local data."""

from __future__ import annotations

import csv
import hashlib
import math
import platform
import re
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


BASE_COMMIT = "14df4a18d7e67e6d9f0d0b4a3d39b3a6b712a15a"
EXPECTED_ROWS = 29_606
EXPECTED_U1 = 21_232
EXPECTED_U2 = 14_064
MODELS = tuple(f"S{i}" for i in range(1, 7))

PRIMARY = Path("outputs/differential_expression/primary_de_results.csv")
SENSITIVITY = {
    model: Path(f"outputs/de_sensitivity/results/{model}_de_results.csv")
    for model in MODELS
}
MODEL_DEPENDENT = Path("outputs/de_sensitivity/model_dependent_genes.csv")
REDUCED_DF = Path("outputs/de_sensitivity/reduced_residual_df_genes.csv")
COMPARISON = Path("outputs/de_sensitivity/comparison_metrics.csv")
INPUTS = (PRIMARY, *SENSITIVITY.values(), MODEL_DEPENDENT, REDUCED_DF, COMPARISON)

OUTPUT_DIR = Path("outputs/candidate_registry")
REGISTRY = OUTPUT_DIR / "candidate_registry.csv"
QUEUE = OUTPUT_DIR / "candidate_queue.csv"
LAYER_COUNTS = OUTPUT_DIR / "candidate_layer_counts.csv"
GENE_TYPE_COUNTS = OUTPUT_DIR / "gene_type_counts_by_layer.csv"
ROBUSTNESS = OUTPUT_DIR / "robustness_summary.csv"
SUMMARY = OUTPUT_DIR / "candidate_generation_summary.md"
SESSION = OUTPUT_DIR / "session_info.txt"

ALLOWED_UNTRACKED = {
    "analysis/08_build_candidate_registry.py",
    "docs/candidate_generation_decision_v0.1.md",
    "docs/target_evidence_schema_v0.1.md",
}
ALLOWED_UNTRACKED_PREFIX = "outputs/candidate_registry/"


def fail(message: str) -> None:
    raise RuntimeError(message)


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args], text=True, capture_output=True, check=False
    )
    if check and result.returncode != 0:
        fail(
            f"Git command failed: git {' '.join(args)}\n"
            f"stdout: {result.stdout.strip()}\nstderr: {result.stderr.strip()}"
        )
    return result.stdout.strip()


def validate_repository() -> tuple[str, str, str]:
    root = Path(git("rev-parse", "--show-toplevel")).resolve()
    if root != Path.cwd().resolve():
        fail(f"Run from repository root {root}; current directory is {Path.cwd().resolve()}")

    branch = git("branch", "--show-current")
    if branch != "main":
        fail(f"Task #008 requires branch main; observed {branch!r}")

    head = git("rev-parse", "HEAD")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASE_COMMIT, head],
        capture_output=True,
        text=True,
        check=False,
    )
    if ancestor.returncode != 0:
        fail(f"Frozen base commit {BASE_COMMIT} is not an ancestor of HEAD {head}")

    remote = git("remote", "get-url", "origin")
    if not re.search(r"(?:github\.com[:/])SichengChen-web/luad-target-dossier(?:\.git)?$", remote):
        fail(f"Unexpected origin remote: {remote}")

    if subprocess.run(["git", "diff", "--quiet"], check=False).returncode != 0:
        fail("Unexpected tracked working-tree modifications are present")
    if subprocess.run(["git", "diff", "--cached", "--quiet"], check=False).returncode != 0:
        fail("Unexpected staged modifications are present")

    untracked = git("ls-files", "--others", "--exclude-standard").splitlines()
    unexpected = [
        path
        for path in untracked
        if path not in ALLOWED_UNTRACKED and not path.startswith(ALLOWED_UNTRACKED_PREFIX)
    ]
    if unexpected:
        fail("Unexpected untracked files are present: " + ", ".join(unexpected))

    for path in INPUTS:
        if not path.is_file():
            fail(f"Required input is missing: {path}")
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", str(path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if tracked.returncode != 0:
            fail(f"Required input is not committed: {path}")
        unchanged = subprocess.run(
            ["git", "diff", "--quiet", BASE_COMMIT, "--", str(path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if unchanged.returncode != 0:
            fail(f"Required input differs from frozen base commit: {path}")

    return head, branch, remote


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            fail(f"CSV has no header: {path}")
        rows = list(reader)
        return list(reader.fieldnames), rows


def require_columns(path: Path, columns: list[str], required: set[str]) -> None:
    missing = required.difference(columns)
    if missing:
        fail(f"{path} is missing required columns: {sorted(missing)}")


def parse_float(value: str, field: str, path: Path) -> float:
    try:
        result = float(value)
    except ValueError as exc:
        raise RuntimeError(f"Invalid {field} value {value!r} in {path}") from exc
    if not math.isfinite(result):
        fail(f"Non-finite {field} value {value!r} in {path}")
    return result


def format_number(value: float) -> str:
    return format(value, ".17g")


def bool_text(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def sign(value: float) -> str:
    if value > 0:
        return "UP"
    if value < 0:
        return "DOWN"
    return "ZERO"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ordered_models(models: set[str]) -> str:
    unknown = models.difference(MODELS)
    if unknown:
        fail(f"Unexpected sensitivity model labels: {sorted(unknown)}")
    return ";".join(model for model in MODELS if model in models)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def load_de_tables() -> tuple[list[dict[str, str]], dict[str, dict[str, dict[str, str]]]]:
    primary_header, primary_rows = read_csv(PRIMARY)
    require_columns(
        PRIMARY,
        primary_header,
        {
            "EnsemblID", "Symbol", "gene_type", "logFC", "AveExpr", "P.Value",
            "adj.P.Val", "mean_logCPM_Tumor", "mean_logCPM_Normal",
        },
    )
    if len(primary_rows) != EXPECTED_ROWS:
        fail(f"S0 row count is {len(primary_rows)}, expected {EXPECTED_ROWS}")
    primary_ids = [row["EnsemblID"] for row in primary_rows]
    if len(set(primary_ids)) != EXPECTED_ROWS:
        fail("S0 EnsemblID is not unique")
    primary_by_id = {row["EnsemblID"]: row for row in primary_rows}

    sensitivity_by_model: dict[str, dict[str, dict[str, str]]] = {}
    for model, path in SENSITIVITY.items():
        header, rows = read_csv(path)
        require_columns(
            path,
            header,
            {"EnsemblID", "Symbol", "gene_type", "logFC", "adj.P.Val"},
        )
        identifiers = [row["EnsemblID"] for row in rows]
        if len(rows) != EXPECTED_ROWS or len(set(identifiers)) != EXPECTED_ROWS:
            fail(f"{model} must contain exactly {EXPECTED_ROWS} unique EnsemblIDs")
        if set(identifiers) != set(primary_ids):
            missing = set(primary_ids).difference(identifiers)
            extra = set(identifiers).difference(primary_ids)
            fail(f"{model} identifier mismatch: missing={len(missing)}, extra={len(extra)}")
        by_id = {row["EnsemblID"]: row for row in rows}
        for identifier in primary_ids:
            primary_row = primary_by_id[identifier]
            sensitivity_row = by_id[identifier]
            for annotation in ("Symbol", "gene_type"):
                if sensitivity_row[annotation] != primary_row[annotation]:
                    fail(f"{model} {annotation} differs from S0 for {identifier}")
        sensitivity_by_model[model] = by_id

    return primary_rows, sensitivity_by_model


def load_auxiliary(primary_ids: set[str]) -> tuple[dict[str, set[str]], dict[str, set[str]], dict[str, int], list[dict[str, str]]]:
    model_header, model_rows = read_csv(MODEL_DEPENDENT)
    require_columns(MODEL_DEPENDENT, model_header, {"model", "EnsemblID"})
    model_dependent: dict[str, set[str]] = defaultdict(set)
    for row in model_rows:
        if row["EnsemblID"] not in primary_ids:
            fail(f"Unknown EnsemblID in {MODEL_DEPENDENT}: {row['EnsemblID']}")
        if row["model"] not in MODELS:
            fail(f"Unknown model in {MODEL_DEPENDENT}: {row['model']}")
        model_dependent[row["EnsemblID"]].add(row["model"])

    df_header, df_rows = read_csv(REDUCED_DF)
    require_columns(REDUCED_DF, df_header, {"model", "EnsemblID", "df_loss"})
    reduced_models: dict[str, set[str]] = defaultdict(set)
    max_df_loss: dict[str, int] = defaultdict(int)
    for row in df_rows:
        identifier = row["EnsemblID"]
        model = row["model"]
        if identifier not in primary_ids:
            fail(f"Unknown EnsemblID in {REDUCED_DF}: {identifier}")
        if model not in MODELS:
            fail(f"Unknown model in {REDUCED_DF}: {model}")
        try:
            df_loss = int(row["df_loss"])
        except ValueError as exc:
            raise RuntimeError(f"Invalid df_loss in {REDUCED_DF}: {row['df_loss']!r}") from exc
        if df_loss < 0:
            fail(f"Negative df_loss for {identifier} in {model}")
        reduced_models[identifier].add(model)
        max_df_loss[identifier] = max(max_df_loss[identifier], df_loss)

    comparison_header, comparison_rows = read_csv(COMPARISON)
    require_columns(
        COMPARISON,
        comparison_header,
        {
            "model", "pearson_logFC", "spearman_logFC", "sign_concordance",
            "genes_compared", "delta_logFC_median", "delta_logFC_median_absolute",
            "delta_logFC_maximum_absolute",
        },
    )
    if [row["model"] for row in comparison_rows] != list(MODELS):
        fail(f"{COMPARISON} must contain S1-S6 once each in order")

    return model_dependent, reduced_models, max_df_loss, comparison_rows


def assign_effect_band(logfc: float) -> str:
    magnitude = abs(logfc)
    if magnitude >= 2:
        return "A"
    if magnitude >= 1:
        return "B"
    if magnitude >= 0.5:
        return "C"
    return "D"


def assign_queue(u1: bool, u2: bool, gene_type: str, all_signs: bool, model_dependent: bool) -> str:
    if not u1:
        return "NOT_PRIMARY_DE"
    if not u2:
        return "DE_SMALL_EFFECT"
    if gene_type != "protein_coding":
        return "QUEUE_C_NONCANONICAL"
    if not all_signs or model_dependent:
        return "QUEUE_B_MODEL_SENSITIVE"
    return "QUEUE_A_CANONICAL"


def build_registry(
    primary_rows: list[dict[str, str]],
    sensitivity: dict[str, dict[str, dict[str, str]]],
    model_dependent: dict[str, set[str]],
    reduced_models: dict[str, set[str]],
    max_df_loss: dict[str, int],
) -> tuple[list[str], list[dict[str, object]], dict[str, object]]:
    rows: list[dict[str, object]] = []
    base_ids: list[str] = []
    malformed_ids: list[str] = []
    versionless_ids: list[str] = []

    for primary in primary_rows:
        identifier = primary["EnsemblID"]
        match = re.fullmatch(r"(ENSG\d+)(?:\.(\d+))?", identifier)
        if match is None:
            malformed_ids.append(identifier)
            base_id = re.sub(r"\.\d+$", "", identifier)
        else:
            base_id = match.group(1)
            if match.group(2) is None:
                versionless_ids.append(identifier)
        base_ids.append(base_id)

        logfc = parse_float(primary["logFC"], "logFC", PRIMARY)
        fdr = parse_float(primary["adj.P.Val"], "adj.P.Val", PRIMARY)
        if not 0 <= fdr <= 1:
            fail(f"S0 FDR outside [0,1] for {identifier}")
        u1 = fdr < 0.05
        u2 = u1 and abs(logfc) >= 0.5

        sensitivity_logfc: dict[str, float] = {}
        sensitivity_fdr: dict[str, float] = {}
        for model in MODELS:
            source = sensitivity[model][identifier]
            sensitivity_logfc[model] = parse_float(source["logFC"], "logFC", SENSITIVITY[model])
            sensitivity_fdr[model] = parse_float(source["adj.P.Val"], "adj.P.Val", SENSITIVITY[model])
            if not 0 <= sensitivity_fdr[model] <= 1:
                fail(f"{model} FDR outside [0,1] for {identifier}")

        sign_s0 = sign(logfc)
        concordance = [sign(sensitivity_logfc[model]) == sign_s0 for model in MODELS]
        deltas = [abs(sensitivity_logfc[model] - logfc) for model in MODELS]
        all_signs = all(concordance)
        is_model_dependent = identifier in model_dependent
        queue = assign_queue(u1, u2, primary["gene_type"], all_signs, is_model_dependent)

        row: dict[str, object] = {
            "EnsemblID": identifier,
            "EnsemblID_base": base_id,
            "Symbol": primary["Symbol"],
            "gene_type": primary["gene_type"],
            "HGNC_ID": "NOT_RETRIEVED",
            "UniProt_ID": "NOT_RETRIEVED",
            "OpenTargets_target_ID": "NOT_RETRIEVED",
            "ChEMBL_target_ID": "NOT_RETRIEVED",
            "U0_tested": "TRUE",
            "U1_DE": bool_text(u1),
            "U2_effect_supported_DE": bool_text(u2),
            "effect_band": assign_effect_band(logfc),
            "biotype_track": (
                "canonical_protein_target"
                if primary["gene_type"] == "protein_coding"
                else "noncanonical_target_modality"
            ),
            "retrieval_queue": queue,
            "logFC_S0": primary["logFC"],
            "FDR_S0": primary["adj.P.Val"],
            "P_value_S0": primary["P.Value"],
            "AveExpr_S0": primary["AveExpr"],
            "mean_logCPM_Tumor": primary["mean_logCPM_Tumor"],
            "mean_logCPM_Normal": primary["mean_logCPM_Normal"],
        }
        for model in MODELS:
            source = sensitivity[model][identifier]
            row[f"logFC_{model}"] = source["logFC"]
            row[f"FDR_{model}"] = source["adj.P.Val"]
        row.update(
            {
                "sign_S0": sign_s0,
                "sign_concordant_S1_S6_count": sum(concordance),
                "sign_concordant_all_S1_S6": bool_text(all_signs),
                "n_sensitivity_FDR05": sum(sensitivity_fdr[model] < 0.05 for model in MODELS),
                "median_abs_delta_logFC_vs_S0": format_number(statistics.median(deltas)),
                "max_abs_delta_logFC_vs_S0": format_number(max(deltas)),
                "S6_sign_flip_vs_S0": bool_text(not concordance[-1]),
                "model_dependent_any_top50": bool_text(is_model_dependent),
                "model_dependent_models": ordered_models(model_dependent.get(identifier, set())),
                "reduced_residual_df_any": bool_text(identifier in reduced_models),
                "reduced_residual_df_models": ordered_models(reduced_models.get(identifier, set())),
                "max_residual_df_loss": max_df_loss.get(identifier, 0),
            }
        )
        rows.append(row)

    if len(set(base_ids)) != len(base_ids):
        fail("EnsemblID_base is not unique after terminal version removal")

    fieldnames = list(rows[0].keys())
    forbidden_fragments = ("score", "rank", "therapeutic_direction")
    forbidden = [name for name in fieldnames if any(fragment in name.lower() for fragment in forbidden_fragments)]
    if forbidden:
        fail(f"Forbidden score/rank/therapeutic-direction fields were generated: {forbidden}")

    symbol_counts = Counter(row["Symbol"] for row in primary_rows if row["Symbol"])
    duplicate_symbol_values = {symbol: count for symbol, count in symbol_counts.items() if count > 1}
    anomalies: dict[str, object] = {
        "malformed_ensembl_ids": malformed_ids,
        "versionless_ensembl_ids": versionless_ids,
        "duplicate_ensembl_base_ids": len(base_ids) - len(set(base_ids)),
        "missing_symbols": sum(not row["Symbol"] for row in primary_rows),
        "duplicate_symbol_value_count": len(duplicate_symbol_values),
        "genes_with_duplicated_symbols": sum(duplicate_symbol_values.values()),
        "max_symbol_multiplicity": max(duplicate_symbol_values.values(), default=1),
    }
    return fieldnames, rows, anomalies


def validate_registry(rows: list[dict[str, object]]) -> None:
    if len(rows) != EXPECTED_ROWS:
        fail(f"Registry row count is {len(rows)}, expected {EXPECTED_ROWS}")
    identifiers = [str(row["EnsemblID"]) for row in rows]
    if len(set(identifiers)) != EXPECTED_ROWS:
        fail("Registry EnsemblID is not unique")
    u1 = sum(row["U1_DE"] == "TRUE" for row in rows)
    u2 = sum(row["U2_effect_supported_DE"] == "TRUE" for row in rows)
    if u1 != EXPECTED_U1:
        fail(f"U1 count is {u1}, expected {EXPECTED_U1}")
    if u2 != EXPECTED_U2:
        fail(f"U2 count is {u2}, expected {EXPECTED_U2}")
    queued = [row for row in rows if row["U2_effect_supported_DE"] == "TRUE"]
    if len(queued) != EXPECTED_U2:
        fail("Candidate queue does not equal the complete U2 set")
    if any(not str(row["retrieval_queue"]).startswith("QUEUE_") for row in queued):
        fail("A U2 gene lacks a Queue A/B/C retrieval label")


def make_layer_counts(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for label in ("U0_tested", "U1_DE", "U2_effect_supported_DE"):
        output.append({"dimension": "candidate_layer", "category": label, "count": sum(row[label] == "TRUE" for row in rows)})
    for band in ("A", "B", "C", "D"):
        output.append({"dimension": "effect_band", "category": band, "count": sum(row["effect_band"] == band for row in rows)})
    for track in ("canonical_protein_target", "noncanonical_target_modality"):
        output.append({"dimension": "biotype_track", "category": track, "count": sum(row["biotype_track"] == track for row in rows)})
    for queue in ("QUEUE_A_CANONICAL", "QUEUE_B_MODEL_SENSITIVE", "QUEUE_C_NONCANONICAL", "DE_SMALL_EFFECT", "NOT_PRIMARY_DE"):
        output.append({"dimension": "retrieval_queue", "category": queue, "count": sum(row["retrieval_queue"] == queue for row in rows)})
    return output


def make_gene_type_counts(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    gene_types = sorted({str(row["gene_type"]) for row in rows})
    for layer in ("U0_tested", "U1_DE", "U2_effect_supported_DE"):
        selected = [row for row in rows if row[layer] == "TRUE"]
        counts = Counter(str(row["gene_type"]) for row in selected)
        for gene_type in gene_types:
            output.append({"candidate_layer": layer, "gene_type": gene_type, "count": counts[gene_type]})
    return output


def close_enough(observed: float, expected: float, tolerance: float = 5e-12) -> bool:
    return math.isclose(observed, expected, rel_tol=tolerance, abs_tol=tolerance)


def make_robustness_summary(
    rows: list[dict[str, object]], comparison_rows: list[dict[str, str]]
) -> list[dict[str, object]]:
    comparison_by_model = {row["model"]: row for row in comparison_rows}
    output: list[dict[str, object]] = []
    for model in MODELS:
        deltas = [float(row[f"logFC_{model}"]) - float(row["logFC_S0"]) for row in rows]
        abs_deltas = [abs(value) for value in deltas]
        sign_count = sum(sign(float(row[f"logFC_{model}"])) == row["sign_S0"] for row in rows)
        sign_rate = sign_count / len(rows)
        committed = comparison_by_model[model]
        checks = {
            "genes_compared": (float(len(rows)), float(committed["genes_compared"])),
            "sign_concordance": (sign_rate, float(committed["sign_concordance"])),
            "delta_logFC_median": (statistics.median(deltas), float(committed["delta_logFC_median"])),
            "delta_logFC_median_absolute": (statistics.median(abs_deltas), float(committed["delta_logFC_median_absolute"])),
            "delta_logFC_maximum_absolute": (max(abs_deltas), float(committed["delta_logFC_maximum_absolute"])),
        }
        for metric, (observed, expected) in checks.items():
            if not close_enough(observed, expected):
                fail(f"Derived {model} {metric}={observed} does not reproduce committed value {expected}")

        output.append(
            {
                "model": model,
                "genes_compared": committed["genes_compared"],
                "pearson_logFC_committed": committed["pearson_logFC"],
                "spearman_logFC_committed": committed["spearman_logFC"],
                "sign_concordance_committed": committed["sign_concordance"],
                "sign_concordant_gene_count": sign_count,
                "sensitivity_FDR05_gene_count": sum(float(row[f"FDR_{model}"]) < 0.05 for row in rows),
                "delta_logFC_median_committed": committed["delta_logFC_median"],
                "delta_logFC_median_absolute_committed": committed["delta_logFC_median_absolute"],
                "delta_logFC_maximum_absolute_committed": committed["delta_logFC_maximum_absolute"],
                "model_dependent_top50_gene_count": sum(model in str(row["model_dependent_models"]).split(";") for row in rows),
                "reduced_residual_df_gene_count": sum(model in str(row["reduced_residual_df_models"]).split(";") for row in rows),
            }
        )
    return output


def count_map(rows: list[dict[str, object]], field: str) -> Counter[str]:
    return Counter(str(row[field]) for row in rows)


def write_summary(rows: list[dict[str, object]], anomalies: dict[str, object]) -> None:
    bands = count_map(rows, "effect_band")
    tracks = count_map(rows, "biotype_track")
    queues = count_map(rows, "retrieval_queue")
    u1 = sum(row["U1_DE"] == "TRUE" for row in rows)
    u2 = sum(row["U2_effect_supported_DE"] == "TRUE" for row in rows)
    sign_stable = sum(row["sign_concordant_all_S1_S6"] == "TRUE" for row in rows)
    model_dependent = sum(row["model_dependent_any_top50"] == "TRUE" for row in rows)
    s6_flips = sum(row["S6_sign_flip_vs_S0"] == "TRUE" for row in rows)

    anomaly_lines = [
        f"- Malformed Ensembl IDs: {len(anomalies['malformed_ensembl_ids'])}",
        f"- Ensembl IDs without a terminal version suffix: {len(anomalies['versionless_ensembl_ids'])}",
        f"- Duplicate `EnsemblID_base` values: {anomalies['duplicate_ensembl_base_ids']}",
        f"- Missing gene symbols: {anomalies['missing_symbols']}",
        f"- Duplicated non-empty symbol values: {anomalies['duplicate_symbol_value_count']} "
        f"(covering {anomalies['genes_with_duplicated_symbols']} genes; maximum multiplicity "
        f"{anomalies['max_symbol_multiplicity']})",
    ]
    text = f"""# Candidate Generation Summary

**Task:** #008  
**Frozen input base:** `{BASE_COMMIT}`  
**External evidence retrieval:** none

## Result

The registry retains all **{len(rows):,}** genes tested in the primary
Tumor–Normal analysis. Differential expression is used only to generate
candidates for later evidence retrieval; these outputs do not select or rank
therapeutic targets.

## Candidate layers

- U0 tested: **{len(rows):,}**
- U1 primary BH FDR < 0.05: **{u1:,}**
- U2 U1 plus |primary logFC| ≥ 0.5: **{u2:,}**

## Primary-effect bands

- A, |logFC| ≥ 2: **{bands['A']:,}**
- B, 1 ≤ |logFC| < 2: **{bands['B']:,}**
- C, 0.5 ≤ |logFC| < 1: **{bands['C']:,}**
- D, |logFC| < 0.5: **{bands['D']:,}**

## Biotype tracks

- Protein-coding (`canonical_protein_target`): **{tracks['canonical_protein_target']:,}**
- All other gene types (`noncanonical_target_modality`): **{tracks['noncanonical_target_modality']:,}**

## First-pass retrieval queues

- Queue A — canonical: **{queues['QUEUE_A_CANONICAL']:,}**
- Queue B — model-sensitive: **{queues['QUEUE_B_MODEL_SENSITIVE']:,}**
- Queue C — noncanonical: **{queues['QUEUE_C_NONCANONICAL']:,}**
- Primary DE with small effect: **{queues['DE_SMALL_EFFECT']:,}**
- Not primary DE: **{queues['NOT_PRIMARY_DE']:,}**

Queues A–C contain all **{u2:,}** U2 genes. Queue membership is a retrieval
workflow label, not a target rank or statement of target quality.

## Sensitivity observations

- Genes whose expression sign is stable across all S1–S6: **{sign_stable:,}**
- Unique genes in at least one committed model-dependent top-50 list: **{model_dependent:,}**
- Genes whose S6 expression sign differs from S0: **{s6_flips:,}**

These features describe model robustness. No composite robustness score was
created, and no gene was removed because of a sensitivity result.

## Identifier audit

{chr(10).join(anomaly_lines)}

Repeated symbols are not treated as identifiers. The unique, versioned
`EnsemblID` remains the immutable key, and the version-free identifier is kept
only as a separate convenience field. External identifier fields remain
`NOT_RETRIEVED`.

## Explicit non-claims

Task #008 generated no final target rank, numerical score, therapeutic
direction, causality claim, druggability conclusion, clinical actionability
claim, or novelty claim. The target-evidence schema defines what later
milestones may retrieve and normalize.
"""
    SUMMARY.write_text(text, encoding="utf-8")


def write_session_info(head: str, branch: str, remote: str) -> None:
    lines = [
        "Task #008 candidate-registry build session",
        f"generated_at_utc={datetime.now(timezone.utc).isoformat()}",
        f"python_version={platform.python_version()}",
        f"python_implementation={platform.python_implementation()}",
        f"platform={platform.platform()}",
        f"git_branch={branch}",
        f"git_head={head}",
        f"frozen_base_commit={BASE_COMMIT}",
        f"git_origin={remote}",
        "network_access=not_used",
        "external_data_retrieved=FALSE",
        "packages_installed_or_updated=FALSE",
        "",
        "Frozen input SHA256:",
    ]
    lines.extend(f"{file_sha256(path)}  {path}" for path in INPUTS)
    SESSION.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    head, branch, remote = validate_repository()
    primary_rows, sensitivity = load_de_tables()
    primary_ids = {row["EnsemblID"] for row in primary_rows}
    model_dependent, reduced_models, max_df_loss, comparison_rows = load_auxiliary(primary_ids)
    fieldnames, registry_rows, anomalies = build_registry(
        primary_rows, sensitivity, model_dependent, reduced_models, max_df_loss
    )
    validate_registry(registry_rows)

    output_dir_existed = OUTPUT_DIR.exists()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        write_csv(REGISTRY, fieldnames, registry_rows)
        queue_rows = [row for row in registry_rows if row["U2_effect_supported_DE"] == "TRUE"]
        write_csv(QUEUE, fieldnames, queue_rows)
        layer_rows = make_layer_counts(registry_rows)
        write_csv(LAYER_COUNTS, ["dimension", "category", "count"], layer_rows)
        gene_type_rows = make_gene_type_counts(registry_rows)
        write_csv(GENE_TYPE_COUNTS, ["candidate_layer", "gene_type", "count"], gene_type_rows)
        robustness_rows = make_robustness_summary(registry_rows, comparison_rows)
        write_csv(ROBUSTNESS, list(robustness_rows[0].keys()), robustness_rows)
        write_summary(registry_rows, anomalies)
        write_session_info(head, branch, remote)
    except Exception:
        # Preserve any pre-existing output directory; ordinary reruns overwrite
        # only the seven declared Task #008 files.
        if not output_dir_existed and OUTPUT_DIR.exists() and not any(OUTPUT_DIR.iterdir()):
            OUTPUT_DIR.rmdir()
        raise

    print(f"Wrote {REGISTRY} ({len(registry_rows)} rows)")
    print(f"Wrote {QUEUE} ({sum(row['U2_effect_supported_DE'] == 'TRUE' for row in registry_rows)} rows)")
    print(f"U1={sum(row['U1_DE'] == 'TRUE' for row in registry_rows)}; U2={sum(row['U2_effect_supported_DE'] == 'TRUE' for row in registry_rows)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
