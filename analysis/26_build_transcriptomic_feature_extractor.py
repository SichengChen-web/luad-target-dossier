#!/usr/bin/env python3
"""Build Task #026 deterministic transcriptomic structural features.

This extractor converts frozen Task #012 transcriptomic fields and Task #014
claim/record lineage into normalized, component-specific inputs for the Task
#025 evaluator. It does not execute state rules, materialize profiles, score,
rank, select, or interpret genes.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
import shutil
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
TASK025_BASE_COMMIT = "ae47a17348d6ade75f4cca9794480c9bc5cf6eaa"
EXPECTED_BRANCH = "main"
EXPECTED_REMOTE_FRAGMENT = "SichengChen-web/luad-target-dossier"
EXTRACTOR_VERSION = "TRANSCRIPTOMIC_FEATURE_EXTRACTOR_V0.1"
ARTIFACT_ID = "ART_TASK012_INTEGRATED_TARGET_REGISTRY"
EXPECTED_GENES = 29_606
EXPECTED_U1 = 21_232
EXPECTED_U2 = 14_064
EXPECTED_TRANSCRIPT_RECORDS = EXPECTED_GENES * 2
EXPECTED_DEPENDENCIES = EXPECTED_GENES

SCRIPT_PATH = ROOT / "analysis/26_build_transcriptomic_feature_extractor.py"
OUTPUT_DIR = ROOT / "outputs/feature_extraction"
FEATURES_PATH = OUTPUT_DIR / "transcriptomic_features.csv"
DICTIONARY_PATH = OUTPUT_DIR / "feature_dictionary.csv"
PROVENANCE_PATH = OUTPUT_DIR / "feature_provenance_registry.csv"
MANIFEST_PATH = OUTPUT_DIR / "extraction_manifest.json"
SUMMARY_PATH = OUTPUT_DIR / "extraction_summary.md"
SESSION_PATH = OUTPUT_DIR / "session_info.txt"

INPUTS = {
    "task012_integrated_registry": ROOT / "outputs/integrated_registry/integrated_target_registry.csv",
    "task013_domain_registry": ROOT / "outputs/evidence_ontology/evidence_domain_registry.csv",
    "task013_independence_map": ROOT / "outputs/evidence_ontology/evidence_independence_map.csv",
    "task013_source_lineage": ROOT / "outputs/evidence_ontology/evidence_source_lineage.csv",
    "task014_claim_registry": ROOT / "outputs/evidence_claim_architecture/evidence_claim_registry.csv",
    "task014_record_registry": ROOT / "outputs/evidence_claim_architecture/evidence_record_registry.csv",
    "task014_source_registry": ROOT / "outputs/evidence_claim_architecture/source_entity_registry.csv",
    "task014_dependency_graph": ROOT / "outputs/evidence_claim_architecture/evidence_dependency_graph.csv",
    "task021_materialization_schema": ROOT / "outputs/profile_materialization/materialization_schema.csv",
    "task021_state_resolution_registry": ROOT / "outputs/profile_materialization/component_state_resolution_registry.csv",
    "task021_builder_contract": ROOT / "outputs/profile_materialization/profile_builder_contract.md",
    "task025_state_rule_registry": ROOT / "outputs/state_rule_registry/state_rule_registry.csv",
}

EXPECTED_HASHES = {
    "task012_integrated_registry": "0587fc6901267b18c8144644571f89ac2cc46053b57ea5def4093795fdbc4c26",
    "task013_domain_registry": "ee62ce66f2ca4726c9365da347198251b9bd77d2dead87b8409221505f2d03b8",
    "task013_independence_map": "d99bbaa8fe5e6229774ac2bf73d84de8fbd367e585d692eb1273ecc7b5c53945",
    "task013_source_lineage": "e9496e8bbf953fdffdbaed7e09936a8493230fc74939597537f8960fabf19f2c",
    "task014_claim_registry": "0d963a4c5c8f9586f81369e33df0a2b7e57bb37ac8ceab4ce54498baf2351a66",
    "task014_record_registry": "76ec5056fb4e468176073073532204d231765d4f0cd70dbb6cfe4ad8bf752343",
    "task014_source_registry": "1b1379066226b5f69b626fe4a97628f7b6da6e585515aa8609218eef65bf8056",
    "task014_dependency_graph": "011839f10c48e197f9f1c0e2262565e562d3a2cf53dd0936f21ddcb4ed5c2256",
    "task021_materialization_schema": "9324374e39fb844c224961db319e4ddf9979512026062ededb5e59e505318701",
    "task021_state_resolution_registry": "302fe6fef0eaf76daedbd51cbd9c430cb38bdbe231991f6e2551de0da59a94be",
    "task021_builder_contract": "3b9ae40e670349be387e351426bf5418e7ede8de2ff780e19e63050d2e7bf29b",
    "task025_state_rule_registry": "858974ae9d13e9505393dfce50e746b7fd1c15adec56d66771cff238da59d13d",
}

ALLOWED_TASK026_PATHS = {
    "analysis/26_build_transcriptomic_feature_extractor.py",
}
ALLOWED_TASK026_PREFIX = "outputs/feature_extraction/"

PRIMARY_FIELDS = [
    "U0_tested", "U1_DE", "U2_effect_supported_DE", "effect_band",
    "logFC_S0", "FDR_S0", "P_value_S0", "AveExpr_S0",
    "mean_logCPM_Tumor", "mean_logCPM_Normal", "sign_S0",
]
ROBUSTNESS_FIELDS = [
    "logFC_S1", "FDR_S1", "logFC_S2", "FDR_S2", "logFC_S3",
    "FDR_S3", "logFC_S4", "FDR_S4", "logFC_S5", "FDR_S5",
    "logFC_S6", "FDR_S6", "sign_concordant_S1_S6_count",
    "sign_concordant_all_S1_S6", "n_sensitivity_FDR05",
    "median_abs_delta_logFC_vs_S0", "max_abs_delta_logFC_vs_S0",
    "S6_sign_flip_vs_S0", "model_dependent_any_top50",
    "model_dependent_models", "reduced_residual_df_any",
    "reduced_residual_df_models", "max_residual_df_loss",
]
REQUIRED_INTEGRATED_FIELDS = {"EnsemblID", *PRIMARY_FIELDS, *ROBUSTNESS_FIELDS}
MISSINGNESS_VOCABULARY = {
    "OBSERVED", "NOT_FOUND", "NOT_QUERIED", "NOT_APPLICABLE", "UNKNOWN"
}
FORBIDDEN_HEADER_TOKENS = {
    "score", "ranking", "rank", "priority", "recommendation",
    "therapeutic_direction", "target_selection", "confidence_score",
    "robustness_score", "stability_score",
}

FEATURE_DEFINITIONS: list[dict[str, Any]] = [
    {
        "feature_name": "transcriptomic_record_available",
        "feature_category": "EVIDENCE_AVAILABILITY",
        "data_type": "CONTROLLED_MISSINGNESS_STATE",
        "allowed_values": "OBSERVED|NOT_FOUND|NOT_QUERIED|NOT_APPLICABLE|UNKNOWN",
        "source_fields": "missingness_status",
        "source_record_roles": "TRANSCRIPT_PRIMARY|TRANSCRIPT_ROBUSTNESS",
        "roles": ("TRANSCRIPT_PRIMARY", "TRANSCRIPT_ROBUSTNESS"),
        "extraction_rule_id": "TXR_TRANSCRIPT_RECORD_AVAILABLE_V0_1",
        "rule": "OBSERVED iff both required transcript records are OBSERVED; otherwise preserve the source missingness boundary without converting absence into negative evidence.",
        "boundary": "Evidence-record availability only; not evidence strength, biological importance, or therapeutic relevance.",
        "task025_input": "FALSE",
    },
    {
        "feature_name": "primary_DE_result_available",
        "feature_category": "EVIDENCE_AVAILABILITY",
        "data_type": "CONTROLLED_MISSINGNESS_STATE",
        "allowed_values": "OBSERVED|NOT_FOUND|NOT_QUERIED|NOT_APPLICABLE|UNKNOWN",
        "source_fields": "U0_tested|missingness_status|observation_status",
        "source_record_roles": "TRANSCRIPT_PRIMARY",
        "roles": ("TRANSCRIPT_PRIMARY",),
        "extraction_rule_id": "TXR_PRIMARY_RESULT_AVAILABLE_V0_1",
        "rule": "OBSERVED iff the frozen primary record is OBSERVED, reports PRIMARY_ANALYSIS_RESULT_PRESENT, and U0_tested is TRUE.",
        "boundary": "Presence of a tested primary DE result; not a statement that the FDR or effect threshold was met.",
        "task025_input": "FALSE",
    },
    {
        "feature_name": "sensitivity_results_available",
        "feature_category": "EVIDENCE_AVAILABILITY",
        "data_type": "CONTROLLED_MISSINGNESS_STATE",
        "allowed_values": "OBSERVED|NOT_FOUND|NOT_QUERIED|NOT_APPLICABLE|UNKNOWN",
        "source_fields": "logFC_S1|FDR_S1|logFC_S2|FDR_S2|logFC_S3|FDR_S3|logFC_S4|FDR_S4|logFC_S5|FDR_S5|logFC_S6|FDR_S6|missingness_status",
        "source_record_roles": "TRANSCRIPT_ROBUSTNESS",
        "roles": ("TRANSCRIPT_ROBUSTNESS",),
        "extraction_rule_id": "TXR_SENSITIVITY_RESULTS_AVAILABLE_V0_1",
        "rule": "OBSERVED iff the frozen robustness record is OBSERVED and all S1-S6 logFC/FDR pairs are present and valid.",
        "boundary": "Availability of prespecified related model results; not independent replication.",
        "task025_input": "FALSE",
    },
    {
        "feature_name": "effect_direction_observed",
        "feature_category": "OBSERVED_EXPRESSION_CHARACTERISTIC",
        "data_type": "CONTROLLED_CATEGORY",
        "allowed_values": "TUMOR_HIGHER|TUMOR_LOWER|NO_EFFECT|UNKNOWN",
        "source_fields": "logFC_S0|sign_S0",
        "source_record_roles": "TRANSCRIPT_PRIMARY",
        "roles": ("TRANSCRIPT_PRIMARY",),
        "extraction_rule_id": "TXR_PRIMARY_EFFECT_DIRECTION_V0_1",
        "rule": "Map frozen sign_S0 UP/DOWN/ZERO to TUMOR_HIGHER/TUMOR_LOWER/NO_EFFECT; otherwise UNKNOWN.",
        "boundary": "Statistical tumour-minus-normal direction only; it does not imply biological or therapeutic direction.",
        "task025_input": "FALSE",
    },
    {
        "feature_name": "fdr_threshold_version",
        "feature_category": "STATISTICAL_OBSERVATION_STATUS",
        "data_type": "VERSION_IDENTIFIER",
        "allowed_values": "TASK008_U1_BH_FDR_LT_0_05_V0_1",
        "source_fields": "U1_DE|FDR_S0",
        "source_record_roles": "TRANSCRIPT_PRIMARY",
        "roles": ("TRANSCRIPT_PRIMARY",),
        "extraction_rule_id": "TXR_FDR_THRESHOLD_VERSION_V0_1",
        "rule": "Emit the frozen Task #008 U1 threshold identifier after verifying U1_DE equals FDR_S0 < 0.05.",
        "boundary": "Versioned statistical candidate-generation threshold; not a therapeutic decision threshold.",
        "task025_input": "FALSE",
    },
    {
        "feature_name": "fdr_pass_status",
        "feature_category": "STATISTICAL_OBSERVATION_STATUS",
        "data_type": "CONTROLLED_CATEGORY",
        "allowed_values": "THRESHOLD_MET|THRESHOLD_NOT_MET|UNKNOWN",
        "source_fields": "U1_DE|FDR_S0",
        "source_record_roles": "TRANSCRIPT_PRIMARY",
        "roles": ("TRANSCRIPT_PRIMARY",),
        "extraction_rule_id": "TXR_FDR_PASS_STATUS_V0_1",
        "rule": "THRESHOLD_MET iff frozen U1_DE is TRUE; THRESHOLD_NOT_MET iff FALSE; UNKNOWN only when the frozen observation is unavailable.",
        "boundary": "Describes the frozen BH FDR threshold result only; THRESHOLD_NOT_MET is not negative biological evidence.",
        "task025_input": "FALSE",
    },
    {
        "feature_name": "effect_threshold_version",
        "feature_category": "STATISTICAL_OBSERVATION_STATUS",
        "data_type": "VERSION_IDENTIFIER",
        "allowed_values": "TASK008_ABS_LOGFC_GE_0_5_V0_1",
        "source_fields": "U2_effect_supported_DE|logFC_S0",
        "source_record_roles": "TRANSCRIPT_PRIMARY",
        "roles": ("TRANSCRIPT_PRIMARY",),
        "extraction_rule_id": "TXR_EFFECT_THRESHOLD_VERSION_V0_1",
        "rule": "Emit the frozen Task #008 absolute logFC threshold identifier after verifying U2 membership semantics.",
        "boundary": "Versioned descriptive effect threshold; not target quality or therapeutic relevance.",
        "task025_input": "FALSE",
    },
    {
        "feature_name": "effect_threshold_status",
        "feature_category": "STATISTICAL_OBSERVATION_STATUS",
        "data_type": "CONTROLLED_CATEGORY",
        "allowed_values": "THRESHOLD_MET|THRESHOLD_NOT_MET|UNKNOWN",
        "source_fields": "logFC_S0",
        "source_record_roles": "TRANSCRIPT_PRIMARY",
        "roles": ("TRANSCRIPT_PRIMARY",),
        "extraction_rule_id": "TXR_EFFECT_THRESHOLD_STATUS_V0_1",
        "rule": "THRESHOLD_MET iff abs(logFC_S0) >= 0.5; otherwise THRESHOLD_NOT_MET; UNKNOWN only when unavailable.",
        "boundary": "Observed effect-size threshold status only; it does not establish causality or actionability.",
        "task025_input": "FALSE",
    },
    {
        "feature_name": "sensitivity_model_count_available",
        "feature_category": "SENSITIVITY_STRUCTURE",
        "data_type": "NONNEGATIVE_INTEGER",
        "allowed_values": "0..6",
        "source_fields": "logFC_S1|FDR_S1|logFC_S2|FDR_S2|logFC_S3|FDR_S3|logFC_S4|FDR_S4|logFC_S5|FDR_S5|logFC_S6|FDR_S6",
        "source_record_roles": "TRANSCRIPT_ROBUSTNESS",
        "roles": ("TRANSCRIPT_ROBUSTNESS",),
        "extraction_rule_id": "TXR_SENSITIVITY_MODEL_COUNT_V0_1",
        "rule": "Count S1-S6 models having both a finite logFC and an FDR in [0,1].",
        "boundary": "Availability count is audit metadata, not evidence quality or a confidence measure.",
        "task025_input": "FALSE",
    },
    {
        "feature_name": "sensitivity_direction_pattern",
        "feature_category": "SENSITIVITY_STRUCTURE",
        "data_type": "CONTROLLED_CATEGORY",
        "allowed_values": "TUMOR_HIGHER_ONLY|TUMOR_LOWER_ONLY|NO_EFFECT_ONLY|MIXED_DIRECTION|NOT_AVAILABLE|UNKNOWN",
        "source_fields": "logFC_S1|logFC_S2|logFC_S3|logFC_S4|logFC_S5|logFC_S6",
        "source_record_roles": "TRANSCRIPT_ROBUSTNESS",
        "roles": ("TRANSCRIPT_ROBUSTNESS",),
        "extraction_rule_id": "TXR_SENSITIVITY_DIRECTION_PATTERN_V0_1",
        "rule": "Classify the set of observed S1-S6 logFC signs without weighting or aggregation.",
        "boundary": "Pattern of related model directions; not therapeutic direction or independent confirmation.",
        "task025_input": "FALSE",
    },
    {
        "feature_name": "sensitivity_consistency_category",
        "feature_category": "SENSITIVITY_STRUCTURE",
        "data_type": "CONTROLLED_CATEGORY",
        "allowed_values": "CONSISTENT_DIRECTION|MIXED_DIRECTION|NOT_AVAILABLE|UNKNOWN",
        "source_fields": "sign_S0|logFC_S1|logFC_S2|logFC_S3|logFC_S4|logFC_S5|logFC_S6|sign_concordant_all_S1_S6",
        "source_record_roles": "TRANSCRIPT_PRIMARY|TRANSCRIPT_ROBUSTNESS",
        "roles": ("TRANSCRIPT_PRIMARY", "TRANSCRIPT_ROBUSTNESS"),
        "extraction_rule_id": "TXR_SENSITIVITY_CONSISTENCY_V0_1",
        "rule": "CONSISTENT_DIRECTION iff all six sensitivity signs equal sign_S0; otherwise MIXED_DIRECTION when all are available.",
        "boundary": "Directional consistency across related model views; no robustness, stability, or confidence score is produced.",
        "task025_input": "FALSE",
    },
]

TASK025_FEATURES = [
    ("identity_conflict_count", "NONNEGATIVE_INTEGER", "0..N", "TXR_IDENTITY_CONFLICT_COUNT_V0_1", "Count traceable EnsemblID mismatches across the integrated row, claim, source-record identifier, and raw-value reference.", "Identity reconciliation only; current frozen inputs must yield zero."),
    ("provenance_complete", "BOOLEAN", "TRUE|FALSE", "TXR_PROVENANCE_COMPLETE_V0_1", "TRUE iff claim, both records, source/version, artifact/hash, raw references, ontology, and dependency lineage resolve.", "Completeness of lineage only; not evidence quality."),
    ("transcript_conflict_count", "NONNEGATIVE_INTEGER", "0..N", "TXR_TRANSCRIPT_CONFLICT_COUNT_V0_1", "Count the frozen Task #014 transcript conflict assertion as one structural condition when uncertainty_status is CONFLICTING_RECORDS.", "Preserves a prespecified direction conflict; it does not interpret biology."),
    ("transcript_qualifying_record_count", "NONNEGATIVE_INTEGER", "0..2", "TXR_TRANSCRIPT_QUALIFYING_RECORD_COUNT_V0_1", "Count required primary/robustness roles that are OBSERVED and have their required valid fields.", "Audit record count only; records share a cohort and are not independent votes."),
    ("transcript_observed_context_complete", "BOOLEAN", "TRUE|FALSE", "TXR_TRANSCRIPT_CONTEXT_COMPLETE_V0_1", "TRUE iff both roles qualify and frozen cohort/design/source/dependency provenance is complete.", "Context completeness only; not profile state or target quality."),
    ("transcript_assessment_attempted", "BOOLEAN", "TRUE|FALSE", "TXR_TRANSCRIPT_ASSESSMENT_ATTEMPTED_V0_1", "TRUE iff a frozen transcriptomic claim and at least one required record role exist for the EnsemblID.", "Assessment execution metadata only."),
    ("transcript_query_scope_complete", "BOOLEAN", "TRUE|FALSE", "TXR_TRANSCRIPT_SCOPE_COMPLETE_V0_1", "TRUE iff both required record roles exist and neither has unresolved query coverage or retrieval failure.", "Coverage metadata only; no biological absence inference."),
    ("transcript_record_count", "NONNEGATIVE_INTEGER", "0..2", "TXR_TRANSCRIPT_RECORD_COUNT_V0_1", "Count atomic TRANSCRIPT_PRIMARY and TRANSCRIPT_ROBUSTNESS records before state evaluation.", "Audit count only; never a confidence measure."),
    ("transcript_partial_condition_count", "NONNEGATIVE_INTEGER", "0..N", "TXR_TRANSCRIPT_PARTIAL_CONDITION_COUNT_V0_1", "Count missing roles, invalid required fields, incomplete provenance, unknown coverage, or retrieval-failure conditions.", "Structural incompleteness count only; not a score."),
    ("transcript_unknown_coverage", "BOOLEAN", "TRUE|FALSE", "TXR_TRANSCRIPT_UNKNOWN_COVERAGE_V0_1", "TRUE iff required transcript acquisition or query coverage remains UNKNOWN.", "UNKNOWN is retained and is not converted to biological absence."),
    ("transcript_retrieval_failure", "BOOLEAN", "TRUE|FALSE", "TXR_TRANSCRIPT_RETRIEVAL_FAILURE_V0_1", "TRUE iff a required frozen transcript record reports a retrieval/parsing failure or its referenced fields cannot be resolved.", "Technical failure metadata only."),
]

for name, dtype, allowed, rule_id, rule, boundary in TASK025_FEATURES:
    FEATURE_DEFINITIONS.append({
        "feature_name": name,
        "feature_category": "TASK025_EVALUATOR_INPUT",
        "data_type": dtype,
        "allowed_values": allowed,
        "source_fields": "claim/record/source/dependency lineage plus frozen transcript fields",
        "source_record_roles": "TRANSCRIPT_PRIMARY|TRANSCRIPT_ROBUSTNESS",
        "roles": ("TRANSCRIPT_PRIMARY", "TRANSCRIPT_ROBUSTNESS"),
        "extraction_rule_id": rule_id,
        "rule": rule,
        "boundary": boundary,
        "task025_input": "TRUE",
    })

FEATURE_NAMES = [row["feature_name"] for row in FEATURE_DEFINITIONS]
FEATURE_BY_NAME = {row["feature_name"]: row for row in FEATURE_DEFINITIONS}

FEATURE_COLUMNS = ["EnsemblID", *FEATURE_NAMES, "extractor_version"]
DICTIONARY_COLUMNS = [
    "feature_name", "feature_category", "data_type", "allowed_values",
    "source_fields", "source_record_roles", "extraction_rule_id",
    "extractor_version", "deterministic_extraction_rule",
    "missingness_handling", "interpretation_boundary", "task025_input",
]
PROVENANCE_COLUMNS = [
    "feature_id", "EnsemblID", "feature_name", "claim_id",
    "evidence_record_id", "source_id", "artifact_id", "dependency_id",
    "feature_missingness_status", "extraction_rule_id", "extractor_version",
]
OUTPUT_NAMES = (
    "transcriptomic_features.csv", "feature_dictionary.csv",
    "feature_provenance_registry.csv", "extraction_manifest.json",
    "extraction_summary.md", "session_info.txt",
)


def fail(message: str) -> None:
    raise RuntimeError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_id(prefix: str, value: str) -> str:
    return f"{prefix}_{hashlib.sha256(value.encode('utf-8')).hexdigest()[:24].upper()}"


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def canonical_json(value: Any, *, pretty: bool = False) -> str:
    if pretty:
        return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n"
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def run_git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, text=True, capture_output=True, check=False
    )
    if check and result.returncode != 0:
        fail(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def validate_repository() -> dict[str, str]:
    root = Path(run_git("rev-parse", "--show-toplevel")).resolve()
    branch = run_git("branch", "--show-current")
    head = run_git("rev-parse", "HEAD")
    base = run_git("rev-parse", TASK025_BASE_COMMIT)
    remote = run_git("remote", "get-url", "origin")
    if root != ROOT or branch != EXPECTED_BRANCH or EXPECTED_REMOTE_FRAGMENT not in remote:
        fail(f"Repository identity mismatch: root={root}, branch={branch}, remote={remote}")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", base, head], cwd=ROOT, check=False
    )
    if ancestor.returncode != 0:
        fail("Frozen Task #025 base commit is not an ancestor of current HEAD.")

    changed = set(run_git("diff", "--name-only").splitlines())
    changed |= set(run_git("diff", "--cached", "--name-only").splitlines())
    untracked = set(
        run_git("ls-files", "--others", "--exclude-standard").splitlines()
    )
    unexpected = sorted(
        path for path in changed | untracked
        if path
        and path not in ALLOWED_TASK026_PATHS
        and not path.startswith(ALLOWED_TASK026_PREFIX)
    )
    if unexpected:
        fail("Unexpected working-tree paths outside Task #026: " + ", ".join(unexpected))
    return {
        "root": str(root), "branch": branch, "head": head,
        "base": base, "remote": remote,
    }


def validate_input_hashes() -> dict[str, dict[str, Any]]:
    manifest: dict[str, dict[str, Any]] = {}
    for key, path in INPUTS.items():
        if not path.is_file():
            fail(f"Missing frozen input: {relative(path)}")
        observed = sha256(path)
        expected = EXPECTED_HASHES[key]
        if observed != expected:
            fail(
                f"Frozen input hash mismatch for {relative(path)}: "
                f"observed={observed}, expected={expected}"
            )
        manifest[key] = {
            "artifact_id": {
                "task012_integrated_registry": ARTIFACT_ID,
            }.get(key, "ART_" + key.upper()),
            "relative_path": relative(path),
            "sha256": observed,
            "file_size_bytes": path.stat().st_size,
        }
    return manifest


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_bool(value: str, label: str) -> bool:
    if value == "TRUE":
        return True
    if value == "FALSE":
        return False
    fail(f"{label} is not TRUE/FALSE: {value!r}")


def parse_float(value: str, label: str) -> float:
    try:
        parsed = float(value)
    except ValueError:
        fail(f"{label} is not numeric: {value!r}")
    if not math.isfinite(parsed):
        fail(f"{label} is not finite: {value!r}")
    return parsed


def parse_int(value: str, label: str, lower: int, upper: int | None = None) -> int:
    if not value.isdigit():
        fail(f"{label} is not a non-negative integer: {value!r}")
    parsed = int(value)
    if parsed < lower or (upper is not None and parsed > upper):
        fail(f"{label} is outside [{lower}, {upper}]: {value!r}")
    return parsed


def bool_text(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def effect_sign(value: float) -> str:
    if value > 0:
        return "UP"
    if value < 0:
        return "DOWN"
    return "ZERO"


def direction_label(sign: str) -> str:
    return {
        "UP": "TUMOR_HIGHER",
        "DOWN": "TUMOR_LOWER",
        "ZERO": "NO_EFFECT",
    }.get(sign, "UNKNOWN")


def validate_architecture() -> dict[str, Any]:
    domains = {row["domain_id"]: row for row in read_csv(INPUTS["task013_domain_registry"])}
    domain = domains.get("DOM_TRANSCRIPTOMIC_DISCOVERY")
    if domain is None:
        fail("Task #013 lacks DOM_TRANSCRIPTOMIC_DISCOVERY.")
    expected_types = {
        "EV_TCGA_DE_EFFECT", "EV_TCGA_DE_SIGNIFICANCE", "EV_TCGA_DE_ROBUSTNESS"
    }
    if set(domain["evidence_type"].split("|")) != expected_types:
        fail("Task #013 transcriptomic evidence-type contract changed.")

    independence = read_csv(INPUTS["task013_independence_map"])
    tcga_pairs = [
        row for row in independence
        if row["evidence_pair"] in {
            "EV_TCGA_DE_EFFECT vs EV_TCGA_DE_SIGNIFICANCE",
            "EV_TCGA_DE_EFFECT vs EV_TCGA_DE_ROBUSTNESS",
            "EV_TCGA_DE_SIGNIFICANCE vs EV_TCGA_DE_ROBUSTNESS",
        }
    ]
    if len(tcga_pairs) != 3 or any(
        row["relationship"] != "DERIVED_FROM_SAME_SOURCE"
        or row["dependency_level"] != "HIGH"
        for row in tcga_pairs
    ):
        fail("Task #013 transcriptomic dependency semantics changed.")

    source_lineage = {
        row["source_id"]: row for row in read_csv(INPUTS["task013_source_lineage"])
    }
    if "SRC_PROJECT_DE_ROBUSTNESS" not in source_lineage:
        fail("Task #013 source lineage lacks SRC_PROJECT_DE_ROBUSTNESS.")

    component_rows = [
        row for row in read_csv(INPUTS["task021_state_resolution_registry"])
        if row["component_id"] == "COMP_TRANSCRIPTOMIC_EVIDENCE"
    ]
    if len(component_rows) != 5:
        fail("Task #021 must contain five transcriptomic state rows.")
    if any(
        row["required_evidence_record_roles"] != "TRANSCRIPT_PRIMARY|TRANSCRIPT_ROBUSTNESS"
        or set(row["acceptable_evidence_types"].split("|")) != expected_types
        for row in component_rows
    ):
        fail("Task #021 transcriptomic role/type contract changed.")

    rule_rows = [
        row for row in read_csv(INPUTS["task025_state_rule_registry"])
        if row["component_id"] == "COMP_TRANSCRIPTOMIC_EVIDENCE"
    ]
    if len(rule_rows) != 5:
        fail("Task #025 must contain five executable transcriptomic state rules.")
    contracts = [json.loads(row["input_feature_contract_json"]) for row in rule_rows]
    if any(contract != contracts[0] for contract in contracts[1:]):
        fail("Task #025 transcriptomic feature contracts differ by state.")
    expected_contract = {row["name"]: row["type"] for row in contracts[0]}
    implemented = {
        row["feature_name"]: row["data_type"]
        for row in FEATURE_DEFINITIONS if row["task025_input"] == "TRUE"
    }
    if expected_contract != implemented:
        fail(
            "Task #025 feature contract mismatch: "
            f"expected={expected_contract}, implemented={implemented}"
        )
    return {
        "transcriptomic_domain_present": True,
        "transcriptomic_evidence_types": sorted(expected_types),
        "dependent_pair_count": len(tcga_pairs),
        "task021_state_count": len(component_rows),
        "task025_rule_count": len(rule_rows),
        "task025_feature_count": len(expected_contract),
    }


def load_integrated() -> list[dict[str, str]]:
    path = INPUTS["task012_integrated_registry"]
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or not REQUIRED_INTEGRATED_FIELDS.issubset(reader.fieldnames):
            missing = sorted(REQUIRED_INTEGRATED_FIELDS - set(reader.fieldnames or []))
            fail(f"Task #012 integrated registry lacks fields: {missing}")
        rows = list(reader)
    identifiers = [row["EnsemblID"] for row in rows]
    if len(rows) != EXPECTED_GENES or len(set(identifiers)) != EXPECTED_GENES:
        fail(
            f"Integrated identity mismatch: rows={len(rows)}, unique={len(set(identifiers))}"
        )
    if any(not identifier.startswith("ENSG") for identifier in identifiers):
        fail("Integrated registry contains a non-Ensembl immutable key.")
    return rows


def load_lineage(valid_ids: set[str]) -> tuple[
    dict[str, dict[str, str]],
    dict[str, dict[str, dict[str, str]]],
    dict[tuple[str, str], dict[str, str]],
    dict[str, dict[str, str]],
]:
    claims_by_gene: dict[str, dict[str, str]] = {}
    claim_to_gene: dict[str, str] = {}
    with INPUTS["task014_claim_registry"].open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["domain_id"] != "DOM_TRANSCRIPTOMIC_DISCOVERY":
                continue
            ensembl_id = row["EnsemblID"]
            if ensembl_id not in valid_ids:
                fail(f"Transcript claim has unknown EnsemblID: {ensembl_id}")
            if ensembl_id in claims_by_gene or row["claim_id"] in claim_to_gene:
                fail(f"Duplicate transcript claim identity at {ensembl_id}")
            claims_by_gene[ensembl_id] = row
            claim_to_gene[row["claim_id"]] = ensembl_id
    if set(claims_by_gene) != valid_ids:
        fail("Transcriptomic claims do not cover the complete Task #012 universe.")

    records_by_gene: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    transcript_record_ids: set[str] = set()
    with INPUTS["task014_record_registry"].open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            role = row["source_record_type"]
            if role not in {"TRANSCRIPT_PRIMARY", "TRANSCRIPT_ROBUSTNESS"}:
                continue
            ensembl_id = claim_to_gene.get(row["claim_id"])
            if ensembl_id is None:
                fail(f"Transcript record has an invalid claim link: {row['record_id']}")
            if role in records_by_gene[ensembl_id]:
                fail(f"Duplicate {role} record at {ensembl_id}")
            if row["record_id"] in transcript_record_ids:
                fail(f"Duplicate transcript record_id: {row['record_id']}")
            records_by_gene[ensembl_id][role] = row
            transcript_record_ids.add(row["record_id"])
    if len(transcript_record_ids) != EXPECTED_TRANSCRIPT_RECORDS:
        fail(
            f"Transcript record count is {len(transcript_record_ids)}; "
            f"expected {EXPECTED_TRANSCRIPT_RECORDS}."
        )
    if any(set(records_by_gene[identifier]) != {"TRANSCRIPT_PRIMARY", "TRANSCRIPT_ROBUSTNESS"} for identifier in valid_ids):
        fail("Every EnsemblID must have exactly both required transcript record roles.")

    dependencies: dict[tuple[str, str], dict[str, str]] = {}
    with INPUTS["task014_dependency_graph"].open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["record_a"] not in transcript_record_ids or row["record_b"] not in transcript_record_ids:
                continue
            key = tuple(sorted((row["record_a"], row["record_b"])))
            if key in dependencies:
                fail(f"Duplicate transcript dependency edge: {key}")
            dependencies[key] = row
    if len(dependencies) != EXPECTED_DEPENDENCIES:
        fail(
            f"Transcript dependency count is {len(dependencies)}; "
            f"expected {EXPECTED_DEPENDENCIES}."
        )

    sources = {row["source_id"]: row for row in read_csv(INPUTS["task014_source_registry"])}
    required_source = sources.get("SRC_PROJECT_DE_ROBUSTNESS")
    if required_source is None or not required_source["version"]:
        fail("Task #014 source registry lacks a versioned DE/robustness source.")
    return claims_by_gene, records_by_gene, dependencies, sources


def expected_raw_reference(ensembl_id: str, fields: list[str]) -> str:
    return (
        "outputs/integrated_registry/integrated_target_registry.csv"
        f"#EnsemblID={ensembl_id}&fields=" + "|".join(fields)
    )


def validate_record(
    ensembl_id: str,
    claim: dict[str, str],
    record: dict[str, str],
    role: str,
    fields: list[str],
    expected_observation: str,
) -> None:
    if record["claim_id"] != claim["claim_id"]:
        fail(f"Claim-record link mismatch at {ensembl_id}/{role}")
    if record["source_id"] != "SRC_PROJECT_DE_ROBUSTNESS":
        fail(f"Unexpected transcript source at {ensembl_id}/{role}")
    if record["source_record_identifier"] != f"TASK012::{ensembl_id}::{role}":
        fail(f"Source-record identifier mismatch at {ensembl_id}/{role}")
    if record["raw_value_reference"] != expected_raw_reference(ensembl_id, fields):
        fail(f"Raw-value reference mismatch at {ensembl_id}/{role}")
    if record["observation_status"] != expected_observation:
        fail(f"Observation status mismatch at {ensembl_id}/{role}")
    if record["missingness_status"] not in MISSINGNESS_VOCABULARY:
        fail(f"Invalid source missingness at {ensembl_id}/{role}")
    if record["missingness_status"] != "OBSERVED":
        fail(f"Frozen transcript record is unexpectedly not OBSERVED at {ensembl_id}/{role}")


def extract_features(
    rows: list[dict[str, str]],
    claims: dict[str, dict[str, str]],
    records: dict[str, dict[str, dict[str, str]]],
    dependencies: dict[tuple[str, str], dict[str, str]],
) -> tuple[list[dict[str, str]], dict[str, dict[str, Any]], Counter[str]]:
    extracted: list[dict[str, str]] = []
    contexts: dict[str, dict[str, Any]] = {}
    summary_counts: Counter[str] = Counter()

    for row in rows:
        ensembl_id = row["EnsemblID"]
        claim = claims[ensembl_id]
        primary = records[ensembl_id]["TRANSCRIPT_PRIMARY"]
        robustness = records[ensembl_id]["TRANSCRIPT_ROBUSTNESS"]
        validate_record(
            ensembl_id, claim, primary, "TRANSCRIPT_PRIMARY", PRIMARY_FIELDS,
            "PRIMARY_ANALYSIS_RESULT_PRESENT",
        )
        validate_record(
            ensembl_id, claim, robustness, "TRANSCRIPT_ROBUSTNESS", ROBUSTNESS_FIELDS,
            "ROBUSTNESS_ANALYSIS_RESULT_PRESENT",
        )

        dep_key = tuple(sorted((primary["record_id"], robustness["record_id"])))
        dependency = dependencies.get(dep_key)
        dependency_complete = bool(
            dependency
            and dependency["relationship"] == "SHARED_DATASET"
            and dependency["dependency_level"] == "DEPENDENT"
            and dependency["review_status"] == "REVIEWED_TASK013"
        )
        if not dependency_complete:
            fail(f"Missing or invalid transcript dependency at {ensembl_id}")

        u0 = parse_bool(row["U0_tested"], f"{ensembl_id}.U0_tested")
        u1 = parse_bool(row["U1_DE"], f"{ensembl_id}.U1_DE")
        u2 = parse_bool(row["U2_effect_supported_DE"], f"{ensembl_id}.U2")
        if not u0:
            fail(f"Frozen Task #012 tested universe contains U0_tested=FALSE at {ensembl_id}")
        logfc0 = parse_float(row["logFC_S0"], f"{ensembl_id}.logFC_S0")
        fdr0 = parse_float(row["FDR_S0"], f"{ensembl_id}.FDR_S0")
        pvalue0 = parse_float(row["P_value_S0"], f"{ensembl_id}.P_value_S0")
        if not 0 <= fdr0 <= 1 or not 0 <= pvalue0 <= 1:
            fail(f"Primary probability field outside [0,1] at {ensembl_id}")
        for field in ("AveExpr_S0", "mean_logCPM_Tumor", "mean_logCPM_Normal"):
            parse_float(row[field], f"{ensembl_id}.{field}")
        sign0 = effect_sign(logfc0)
        if row["sign_S0"] != sign0:
            fail(f"Frozen sign_S0 does not match logFC_S0 at {ensembl_id}")
        if u1 != (fdr0 < 0.05):
            fail(f"Frozen U1 threshold semantics fail at {ensembl_id}")
        if u2 != (u1 and abs(logfc0) >= 0.5):
            fail(f"Frozen U2 threshold semantics fail at {ensembl_id}")

        sensitivity_signs: list[str] = []
        sensitivity_available = 0
        for model in range(1, 7):
            logfc = parse_float(row[f"logFC_S{model}"], f"{ensembl_id}.logFC_S{model}")
            fdr = parse_float(row[f"FDR_S{model}"], f"{ensembl_id}.FDR_S{model}")
            if not 0 <= fdr <= 1:
                fail(f"Sensitivity FDR outside [0,1] at {ensembl_id}/S{model}")
            sensitivity_available += 1
            sensitivity_signs.append(effect_sign(logfc))
        concordant_count = sum(sign == sign0 for sign in sensitivity_signs)
        if parse_int(
            row["sign_concordant_S1_S6_count"],
            f"{ensembl_id}.sign_concordant_S1_S6_count", 0, 6,
        ) != concordant_count:
            fail(f"Frozen sensitivity concordance count mismatch at {ensembl_id}")
        concordant_all = parse_bool(
            row["sign_concordant_all_S1_S6"],
            f"{ensembl_id}.sign_concordant_all_S1_S6",
        )
        if concordant_all != (concordant_count == 6):
            fail(f"Frozen sensitivity all-concordant flag mismatch at {ensembl_id}")
        parse_int(row["n_sensitivity_FDR05"], f"{ensembl_id}.n_sensitivity_FDR05", 0, 6)
        parse_float(row["median_abs_delta_logFC_vs_S0"], f"{ensembl_id}.median_delta")
        parse_float(row["max_abs_delta_logFC_vs_S0"], f"{ensembl_id}.max_delta")
        s6_flip = parse_bool(row["S6_sign_flip_vs_S0"], f"{ensembl_id}.S6_flip")
        if s6_flip != (sensitivity_signs[-1] != sign0):
            fail(f"Frozen S6 sign-flip flag mismatch at {ensembl_id}")
        parse_bool(row["model_dependent_any_top50"], f"{ensembl_id}.model_dependent")
        parse_bool(row["reduced_residual_df_any"], f"{ensembl_id}.reduced_residual_df")
        parse_int(row["max_residual_df_loss"], f"{ensembl_id}.max_residual_df_loss", 0)

        conflict_expected = s6_flip or not concordant_all
        expected_uncertainty = "CONFLICTING_RECORDS" if conflict_expected else "SOURCE_LIMITATION"
        if claim["uncertainty_status"] != expected_uncertainty:
            fail(f"Frozen claim uncertainty mismatch at {ensembl_id}")
        if robustness["uncertainty_status"] != expected_uncertainty:
            fail(f"Frozen robustness uncertainty mismatch at {ensembl_id}")
        if primary["uncertainty_status"] != "SOURCE_LIMITATION":
            fail(f"Frozen primary uncertainty mismatch at {ensembl_id}")

        identity_conflicts = sum([
            claim["EnsemblID"] != ensembl_id,
            primary["source_record_identifier"] != f"TASK012::{ensembl_id}::TRANSCRIPT_PRIMARY",
            robustness["source_record_identifier"] != f"TASK012::{ensembl_id}::TRANSCRIPT_ROBUSTNESS",
            f"#EnsemblID={ensembl_id}&" not in primary["raw_value_reference"],
            f"#EnsemblID={ensembl_id}&" not in robustness["raw_value_reference"],
        ])
        provenance_complete = identity_conflicts == 0 and dependency_complete
        primary_qualifies = primary["missingness_status"] == "OBSERVED"
        robustness_qualifies = (
            robustness["missingness_status"] == "OBSERVED" and sensitivity_available == 6
        )
        qualifying_count = int(primary_qualifies) + int(robustness_qualifies)
        record_count = len(records[ensembl_id])
        assessment_attempted = bool(claim) and record_count > 0
        unknown_coverage = any(
            record["missingness_status"] == "UNKNOWN"
            for record in (primary, robustness)
        )
        retrieval_failure = any(
            "FAIL" in record["observation_status"]
            for record in (primary, robustness)
        )
        query_scope_complete = (
            record_count == 2 and not unknown_coverage and not retrieval_failure
        )
        partial_conditions = sum([
            record_count != 2,
            qualifying_count != 2,
            not provenance_complete,
            not query_scope_complete,
            unknown_coverage,
            retrieval_failure,
        ])
        context_complete = (
            qualifying_count == 2 and provenance_complete and query_scope_complete
        )

        unique_sensitivity_signs = set(sensitivity_signs)
        if sensitivity_available == 0:
            sensitivity_pattern = "NOT_AVAILABLE"
        elif sensitivity_available < 6:
            sensitivity_pattern = "UNKNOWN"
        elif unique_sensitivity_signs == {"UP"}:
            sensitivity_pattern = "TUMOR_HIGHER_ONLY"
        elif unique_sensitivity_signs == {"DOWN"}:
            sensitivity_pattern = "TUMOR_LOWER_ONLY"
        elif unique_sensitivity_signs == {"ZERO"}:
            sensitivity_pattern = "NO_EFFECT_ONLY"
        else:
            sensitivity_pattern = "MIXED_DIRECTION"
        sensitivity_consistency = (
            "CONSISTENT_DIRECTION" if concordant_all else "MIXED_DIRECTION"
        )

        feature_row = {
            "EnsemblID": ensembl_id,
            "transcriptomic_record_available": "OBSERVED",
            "primary_DE_result_available": "OBSERVED",
            "sensitivity_results_available": "OBSERVED",
            "effect_direction_observed": direction_label(sign0),
            "fdr_threshold_version": "TASK008_U1_BH_FDR_LT_0_05_V0_1",
            "fdr_pass_status": "THRESHOLD_MET" if u1 else "THRESHOLD_NOT_MET",
            "effect_threshold_version": "TASK008_ABS_LOGFC_GE_0_5_V0_1",
            "effect_threshold_status": "THRESHOLD_MET" if abs(logfc0) >= 0.5 else "THRESHOLD_NOT_MET",
            "sensitivity_model_count_available": str(sensitivity_available),
            "sensitivity_direction_pattern": sensitivity_pattern,
            "sensitivity_consistency_category": sensitivity_consistency,
            "identity_conflict_count": str(identity_conflicts),
            "provenance_complete": bool_text(provenance_complete),
            "transcript_conflict_count": "1" if conflict_expected else "0",
            "transcript_qualifying_record_count": str(qualifying_count),
            "transcript_observed_context_complete": bool_text(context_complete),
            "transcript_assessment_attempted": bool_text(assessment_attempted),
            "transcript_query_scope_complete": bool_text(query_scope_complete),
            "transcript_record_count": str(record_count),
            "transcript_partial_condition_count": str(partial_conditions),
            "transcript_unknown_coverage": bool_text(unknown_coverage),
            "transcript_retrieval_failure": bool_text(retrieval_failure),
            "extractor_version": EXTRACTOR_VERSION,
        }
        if set(feature_row) != set(FEATURE_COLUMNS):
            fail(f"Internal feature schema mismatch at {ensembl_id}")
        extracted.append(feature_row)
        contexts[ensembl_id] = {
            "claim": claim,
            "records": {
                "TRANSCRIPT_PRIMARY": primary,
                "TRANSCRIPT_ROBUSTNESS": robustness,
            },
            "dependency": dependency,
        }
        summary_counts["u1_count"] += int(u1)
        summary_counts["u2_count"] += int(u2)
        summary_counts[f"direction::{feature_row['effect_direction_observed']}"] += 1
        summary_counts[f"fdr::{feature_row['fdr_pass_status']}"] += 1
        summary_counts[f"effect::{feature_row['effect_threshold_status']}"] += 1
        summary_counts[f"sensitivity::{sensitivity_consistency}"] += 1
        summary_counts[f"transcript_conflict_count::{feature_row['transcript_conflict_count']}"] += 1

    if summary_counts["u1_count"] != EXPECTED_U1:
        fail(f"U1 count changed: {summary_counts['u1_count']} != {EXPECTED_U1}")
    if summary_counts["u2_count"] != EXPECTED_U2:
        fail(f"U2 count changed: {summary_counts['u2_count']} != {EXPECTED_U2}")
    if len(extracted) != EXPECTED_GENES or len({row["EnsemblID"] for row in extracted}) != EXPECTED_GENES:
        fail("Extracted feature table does not retain one unique row per EnsemblID.")
    return extracted, contexts, summary_counts


def validate_feature_values(rows: list[dict[str, str]]) -> None:
    for definition in FEATURE_DEFINITIONS:
        name = definition["feature_name"]
        allowed = definition["allowed_values"]
        dtype = definition["data_type"]
        values = [row[name] for row in rows]
        if dtype == "BOOLEAN" and any(value not in {"TRUE", "FALSE"} for value in values):
            fail(f"Invalid Boolean in {name}")
        elif dtype == "NONNEGATIVE_INTEGER":
            if any(not value.isdigit() for value in values):
                fail(f"Invalid non-negative integer in {name}")
            if ".." in allowed:
                lower, upper = allowed.split("..")
                if upper != "N" and any(not int(lower) <= int(value) <= int(upper) for value in values):
                    fail(f"Value outside {allowed} in {name}")
        elif dtype in {"CONTROLLED_CATEGORY", "CONTROLLED_MISSINGNESS_STATE", "VERSION_IDENTIFIER"}:
            allowed_values = set(allowed.split("|"))
            if any(value not in allowed_values for value in values):
                fail(f"Invalid controlled value in {name}")
        if dtype == "CONTROLLED_MISSINGNESS_STATE" and any(
            value not in MISSINGNESS_VOCABULARY for value in values
        ):
            fail(f"Invalid missingness state in {name}")


def validate_forbidden_headers(headers: Iterable[str]) -> None:
    offenders = []
    for header in headers:
        normalized = header.lower()
        if normalized in FORBIDDEN_HEADER_TOKENS or any(
            normalized.endswith("_" + token) for token in FORBIDDEN_HEADER_TOKENS
        ):
            offenders.append(header)
    if offenders:
        fail(f"Forbidden output fields detected: {sorted(offenders)}")


def dictionary_rows() -> list[dict[str, str]]:
    return [
        {
            "feature_name": definition["feature_name"],
            "feature_category": definition["feature_category"],
            "data_type": definition["data_type"],
            "allowed_values": definition["allowed_values"],
            "source_fields": definition["source_fields"],
            "source_record_roles": definition["source_record_roles"],
            "extraction_rule_id": definition["extraction_rule_id"],
            "extractor_version": EXTRACTOR_VERSION,
            "deterministic_extraction_rule": definition["rule"],
            "missingness_handling": "Preserve OBSERVED/NOT_FOUND/NOT_QUERIED/NOT_APPLICABLE/UNKNOWN; never convert NOT_FOUND to negative evidence or NOT_QUERIED to biological absence.",
            "interpretation_boundary": definition["boundary"],
            "task025_input": definition["task025_input"],
        }
        for definition in FEATURE_DEFINITIONS
    ]


def write_csv(path: Path, fields: list[str], rows: Iterable[dict[str, str]]) -> int:
    count = 0
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
            count += 1
    return count


def provenance_rows(
    features: list[dict[str, str]],
    contexts: dict[str, dict[str, Any]],
) -> Iterable[dict[str, str]]:
    for feature_row in features:
        ensembl_id = feature_row["EnsemblID"]
        context = contexts[ensembl_id]
        claim = context["claim"]
        dependency = context["dependency"]
        for feature_name in FEATURE_NAMES:
            definition = FEATURE_BY_NAME[feature_name]
            feature_id = stable_id(
                "FTR", f"{ensembl_id}|{feature_name}|{EXTRACTOR_VERSION}"
            )
            roles = definition["roles"]
            for role in roles:
                record = context["records"][role]
                yield {
                    "feature_id": feature_id,
                    "EnsemblID": ensembl_id,
                    "feature_name": feature_name,
                    "claim_id": claim["claim_id"],
                    "evidence_record_id": record["record_id"],
                    "source_id": record["source_id"],
                    "artifact_id": ARTIFACT_ID,
                    "dependency_id": (
                        dependency["dependency_id"] if len(roles) > 1
                        else "NOT_APPLICABLE"
                    ),
                    "feature_missingness_status": "OBSERVED",
                    "extraction_rule_id": definition["extraction_rule_id"],
                    "extractor_version": EXTRACTOR_VERSION,
                }


def write_core_artifacts(
    directory: Path,
    features: list[dict[str, str]],
    contexts: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    directory.mkdir(parents=True, exist_ok=True)
    feature_path = directory / "transcriptomic_features.csv"
    dictionary_path = directory / "feature_dictionary.csv"
    provenance_path = directory / "feature_provenance_registry.csv"
    feature_count = write_csv(feature_path, FEATURE_COLUMNS, features)
    dictionary_count = write_csv(dictionary_path, DICTIONARY_COLUMNS, dictionary_rows())
    provenance_count = write_csv(
        provenance_path, PROVENANCE_COLUMNS, provenance_rows(features, contexts)
    )
    return {
        "feature_row_count": feature_count,
        "dictionary_row_count": dictionary_count,
        "provenance_link_count": provenance_count,
        "core_hashes": {
            path.name: sha256(path)
            for path in (feature_path, dictionary_path, provenance_path)
        },
        "core_sizes": {
            path.name: path.stat().st_size
            for path in (feature_path, dictionary_path, provenance_path)
        },
    }


def summary_markdown(
    stats: dict[str, Any],
    counts: Counter[str],
    architecture: dict[str, Any],
) -> str:
    directions = {
        key.split("::", 1)[1]: value
        for key, value in sorted(counts.items()) if key.startswith("direction::")
    }
    consistency = {
        key.split("::", 1)[1]: value
        for key, value in sorted(counts.items()) if key.startswith("sensitivity::")
    }
    effect_counts = {
        key.split("::", 1)[1]: value
        for key, value in sorted(counts.items()) if key.startswith("effect::")
    }
    return f"""# Task #026 transcriptomic feature extraction summary

## Scope

This layer deterministically represents frozen transcriptomic observations and evidence availability. It does not execute Task #025 state rules, materialize target profiles, score or rank genes, select candidates, infer biological importance, or infer therapeutic direction.

## Extracted architecture

- Immutable entities retained: **{stats['feature_row_count']:,}** unique EnsemblIDs in Task #012 order.
- Normalized features per entity: **{len(FEATURE_NAMES)}**.
- Task #025 typed evaluator inputs implemented: **{architecture['task025_feature_count']}**.
- Explicit feature-to-record provenance links: **{stats['provenance_link_count']:,}**.
- Transcriptomic claims: one per EnsemblID.
- Source records: one `TRANSCRIPT_PRIMARY` and one `TRANSCRIPT_ROBUSTNESS` per EnsemblID.
- Dependency treatment: primary and S1-S6 records remain linked as `SHARED_DATASET` / `DEPENDENT`; they are not independent votes.

## Descriptive observations

- Frozen U1 (BH FDR < 0.05): **{counts['u1_count']:,}**.
- Frozen U2 (U1 plus absolute primary logFC at least 0.5): **{counts['u2_count']:,}**.
- Primary direction categories: `{canonical_json(directions)}`.
- Absolute primary logFC threshold categories: `{canonical_json(effect_counts)}`.
- Sensitivity direction consistency categories: `{canonical_json(consistency)}`.
- Frozen Task #014 transcript conflict conditions represented: **{counts['transcript_conflict_count::1']:,}**.

These are structural/statistical descriptions of the frozen analysis. They do not establish causality, importance, efficacy, safety, actionability, or therapeutic direction.

## Validation

- Frozen input SHA256 hashes: **PASS**.
- Task #012 row count, order, unique EnsemblID, U1, and U2 assertions: **PASS**.
- Task #013 evidence-type and dependency semantics: **PASS**.
- Task #014 claim, record, source, raw-reference, missingness, and dependency links: **PASS**.
- Task #021 role/type compatibility: **PASS**.
- Task #025 exact 11-feature typed input contract: **PASS**.
- Every feature has at least one explicit provenance link to a valid claim, evidence record, source, artifact, extraction rule, and extractor version: **PASS**.
- Controlled feature values and missingness vocabulary: **PASS**.
- Forbidden field detection: **PASS**.
- Byte-identical two-pass regeneration: **PASS**.
- Previous frozen artifact hashes unchanged after generation: **PASS**.
- Network, package installation, randomness, wall-clock values, LLM runtime decisions, profile generation, scoring, ranking, candidate selection, and biological interpretation: **NOT USED / NOT GENERATED**.

## Interpretation and review boundaries

`THRESHOLD_NOT_MET` is a frozen statistical observation and is not negative biological evidence. `NOT_FOUND` and `NOT_QUERIED` remain distinct controlled missingness states; neither is converted to biological absence. Record counts are audit metadata only.

The Task #025 state rules remain `AWAITING_INDEPENDENT_SCIENTIFIC_REVIEW`; this extractor does not resolve or release component states. External-source extractors remain unimplemented and require separate source-specific contracts. The explicit provenance registry is expected to be a large derived artifact and should be handled under the Task #018 artifact-governance policy before commit or release.
"""


def write_reports(
    directory: Path,
    core: dict[str, Any],
    counts: Counter[str],
    architecture: dict[str, Any],
    input_manifest: dict[str, dict[str, Any]],
    repository: dict[str, str],
) -> None:
    manifest = {
        "schema_version": "FEATURE_EXTRACTION_MANIFEST_V0.1",
        "task": "026",
        "scope": "TRANSCRIPTOMIC_FEATURE_EXTRACTION_ONLY",
        "extractor_version": EXTRACTOR_VERSION,
        "frozen_task025_base_commit": TASK025_BASE_COMMIT,
        "immutable_key": "EnsemblID",
        "input_artifacts": [input_manifest[key] for key in sorted(input_manifest)],
        "output_artifacts": [
            {
                "relative_path": f"outputs/feature_extraction/{name}",
                "sha256": core["core_hashes"][name],
                "file_size_bytes": core["core_sizes"][name],
                "row_count": {
                    "transcriptomic_features.csv": core["feature_row_count"],
                    "feature_dictionary.csv": core["dictionary_row_count"],
                    "feature_provenance_registry.csv": core["provenance_link_count"],
                }[name],
            }
            for name in (
                "transcriptomic_features.csv", "feature_dictionary.csv",
                "feature_provenance_registry.csv",
            )
        ],
        "extraction_rules": [
            {
                "feature_name": definition["feature_name"],
                "extraction_rule_id": definition["extraction_rule_id"],
                "source_record_roles": list(definition["roles"]),
            }
            for definition in FEATURE_DEFINITIONS
        ],
        "determinism_contract": {
            "randomness": "NOT_USED",
            "network_access": "NOT_USED",
            "package_installation": "NOT_USED",
            "llm_runtime_decisions": "PROHIBITED",
            "wall_clock_values_in_outputs": "NOT_USED",
            "two_pass_byte_identity": "PASS",
        },
        "prohibited_outputs": {
            "profiles": False,
            "scores": False,
            "rankings": False,
            "candidate_selection": False,
            "recommendations": False,
            "biological_conclusions": False,
            "therapeutic_direction": False,
        },
    }
    (directory / "extraction_manifest.json").write_text(
        canonical_json(manifest, pretty=True), encoding="utf-8"
    )
    (directory / "extraction_summary.md").write_text(
        summary_markdown(core, counts, architecture), encoding="utf-8"
    )

    report_hashes = {
        name: sha256(directory / name)
        for name in (
            "transcriptomic_features.csv", "feature_dictionary.csv",
            "feature_provenance_registry.csv", "extraction_manifest.json",
            "extraction_summary.md",
        )
    }
    session_lines = [
        "task=026",
        "purpose=deterministic transcriptomic source-record-to-feature extraction",
        f"extractor_version={EXTRACTOR_VERSION}",
        f"frozen_task025_base_commit={TASK025_BASE_COMMIT}",
        f"git_branch={repository['branch']}",
        f"git_origin={repository['remote']}",
        f"python_implementation={platform.python_implementation()}",
        f"python_version={platform.python_version()}",
        f"platform={platform.platform()}",
        f"script_sha256={sha256(SCRIPT_PATH)}",
        f"feature_row_count={core['feature_row_count']}",
        f"unique_ensembl_id_count={core['feature_row_count']}",
        f"feature_dictionary_count={core['dictionary_row_count']}",
        f"feature_provenance_link_count={core['provenance_link_count']}",
        f"u1_count={counts['u1_count']}",
        f"u2_count={counts['u2_count']}",
        "join_key=EnsemblID_ONLY",
        "gene_symbols_used_as_join_keys=FALSE",
        "network_access=NOT_USED",
        "packages_installed_or_updated=FALSE",
        "randomness_used=FALSE",
        "wall_clock_values_in_outputs=FALSE",
        "llm_runtime_feature_decisions=FALSE",
        "target_profiles_generated=FALSE",
        "scoring_generated=FALSE",
        "ranking_generated=FALSE",
        "candidate_selection_generated=FALSE",
        "therapeutic_direction_inferred=FALSE",
        "biological_conclusions_generated=FALSE",
        "deterministic_two_pass_regeneration=PASS",
    ]
    for key in sorted(input_manifest):
        item = input_manifest[key]
        session_lines.append(
            f"frozen_input_sha256.{item['relative_path']}={item['sha256']}"
        )
    for name in sorted(report_hashes):
        session_lines.append(
            f"output_sha256.outputs/feature_extraction/{name}={report_hashes[name]}"
        )
    (directory / "session_info.txt").write_text(
        "\n".join(session_lines) + "\n", encoding="utf-8"
    )


def validate_provenance_file(
    path: Path,
    features: list[dict[str, str]],
    contexts: dict[str, dict[str, Any]],
) -> int:
    valid_feature_ids = {
        stable_id("FTR", f"{row['EnsemblID']}|{name}|{EXTRACTOR_VERSION}")
        for row in features for name in FEATURE_NAMES
    }
    expected_feature_ids = len(features) * len(FEATURE_NAMES)
    if len(valid_feature_ids) != expected_feature_ids:
        fail("Feature IDs are not unique per EnsemblID/feature pair.")
    seen_feature_ids: set[str] = set()
    link_count = 0
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != PROVENANCE_COLUMNS:
            fail("Provenance registry schema mismatch.")
        for row in reader:
            link_count += 1
            ensembl_id = row["EnsemblID"]
            if row["feature_id"] not in valid_feature_ids:
                fail(f"Invalid feature_id in provenance: {row['feature_id']}")
            context = contexts.get(ensembl_id)
            if context is None:
                fail(f"Unknown EnsemblID in provenance: {ensembl_id}")
            definition = FEATURE_BY_NAME.get(row["feature_name"])
            if definition is None:
                fail(f"Unknown feature in provenance: {row['feature_name']}")
            expected_records = {
                context["records"][role]["record_id"]: context["records"][role]
                for role in definition["roles"]
            }
            record = expected_records.get(row["evidence_record_id"])
            if record is None:
                fail(f"Feature-to-record lineage mismatch for {row['feature_id']}")
            expected_dependency = (
                context["dependency"]["dependency_id"]
                if len(definition["roles"]) > 1 else "NOT_APPLICABLE"
            )
            expected = {
                "claim_id": context["claim"]["claim_id"],
                "source_id": record["source_id"],
                "artifact_id": ARTIFACT_ID,
                "dependency_id": expected_dependency,
                "feature_missingness_status": "OBSERVED",
                "extraction_rule_id": definition["extraction_rule_id"],
                "extractor_version": EXTRACTOR_VERSION,
            }
            for field, value in expected.items():
                if row[field] != value:
                    fail(f"Invalid {field} for provenance feature {row['feature_id']}")
            seen_feature_ids.add(row["feature_id"])
    if seen_feature_ids != valid_feature_ids:
        fail("At least one feature lacks explicit evidence-record provenance.")
    return link_count


def generate_once(
    directory: Path,
    features: list[dict[str, str]],
    contexts: dict[str, dict[str, Any]],
    counts: Counter[str],
    architecture: dict[str, Any],
    input_manifest: dict[str, dict[str, Any]],
    repository: dict[str, str],
) -> dict[str, Any]:
    core = write_core_artifacts(directory, features, contexts)
    expected_links = sum(
        len(definition["roles"]) for definition in FEATURE_DEFINITIONS
    ) * len(features)
    if core["provenance_link_count"] != expected_links:
        fail(
            f"Provenance link count {core['provenance_link_count']} != {expected_links}"
        )
    validated_links = validate_provenance_file(
        directory / "feature_provenance_registry.csv", features, contexts
    )
    if validated_links != expected_links:
        fail("Provenance validation count mismatch.")
    write_reports(directory, core, counts, architecture, input_manifest, repository)
    return core


def compare_directories(first: Path, second: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for name in OUTPUT_NAMES:
        first_hash = sha256(first / name)
        second_hash = sha256(second / name)
        if first_hash != second_hash:
            fail(f"Deterministic regeneration failed for {name}")
        hashes[name] = first_hash
    return hashes


def main() -> None:
    repository = validate_repository()
    input_manifest = validate_input_hashes()
    architecture = validate_architecture()
    integrated = load_integrated()
    identifiers = {row["EnsemblID"] for row in integrated}
    claims, records, dependencies, sources = load_lineage(identifiers)
    if "SRC_PROJECT_DE_ROBUSTNESS" not in sources:
        fail("Versioned transcriptomic source entity is unavailable.")
    features, contexts, counts = extract_features(
        integrated, claims, records, dependencies
    )
    validate_feature_values(features)
    validate_forbidden_headers(
        [*FEATURE_COLUMNS, *DICTIONARY_COLUMNS, *PROVENANCE_COLUMNS]
    )

    with tempfile.TemporaryDirectory(prefix="task026_a_") as temp_a_name, tempfile.TemporaryDirectory(prefix="task026_b_") as temp_b_name:
        temp_a = Path(temp_a_name)
        temp_b = Path(temp_b_name)
        core_a = generate_once(
            temp_a, features, contexts, counts, architecture,
            input_manifest, repository,
        )
        generate_once(
            temp_b, features, contexts, counts, architecture,
            input_manifest, repository,
        )
        output_hashes = compare_directories(temp_a, temp_b)

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        for name in OUTPUT_NAMES:
            shutil.copyfile(temp_a / name, OUTPUT_DIR / name)

    final_links = validate_provenance_file(PROVENANCE_PATH, features, contexts)
    if final_links != core_a["provenance_link_count"]:
        fail("Final provenance registry count changed during copy.")
    if any(sha256(OUTPUT_DIR / name) != output_hashes[name] for name in OUTPUT_NAMES):
        fail("Final artifact hash differs from validated deterministic artifact.")
    validate_input_hashes()
    validate_repository()

    print(f"Wrote {relative(FEATURES_PATH)} ({len(features)} unique EnsemblIDs)")
    print(f"Wrote {relative(DICTIONARY_PATH)} ({len(FEATURE_DEFINITIONS)} features)")
    print(f"Wrote {relative(PROVENANCE_PATH)} ({final_links} explicit lineage links)")
    print(f"Wrote {relative(MANIFEST_PATH)}")
    print(f"Wrote {relative(SUMMARY_PATH)}")
    print(f"Wrote {relative(SESSION_PATH)}")
    print("Frozen hashes, controlled values, provenance, and two-pass byte identity: PASS")
    print("Profiles, scores, rankings, selection, recommendations, and interpretation: NOT GENERATED")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise
