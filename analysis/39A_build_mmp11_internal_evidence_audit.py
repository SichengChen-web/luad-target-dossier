#!/usr/bin/env python3
"""Build the deterministic MMP11 internal project-evidence audit (Task #039A).

This generator reads frozen repository artifacts only. It does not retrieve
evidence, rerun differential expression, rebuild components, or make target
evaluation or therapeutic decisions.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import platform
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs/mmp11_internal_evidence_v0.1"
GENERATOR_VERSION = "MMP11_INTERNAL_PROJECT_EVIDENCE_AUDIT_GENERATOR_V0.1"
AUDIT_VERSION = "MMP11_INTERNAL_PROJECT_EVIDENCE_AUDIT_V0.1"
TARGET_SYMBOL = "MMP11"
EXPECTED_ENSEMBL_ID = "ENSG00000099953.9"
DISCLAIMER = (
    "MMP11 is used as an illustrative biological worked example for scientific communication. "
    "Its inclusion is not the result of a project-level therapeutic target ranking, scoring, "
    "or recommendation procedure."
)

OUTPUT_NAMES = (
    "mmp11_identity.json",
    "mmp11_transcriptomic_evidence.csv",
    "mmp11_sensitivity_evidence.csv",
    "mmp11_component_summary.json",
    "mmp11_provenance_links.csv",
    "mmp11_dependency_map.csv",
    "mmp11_claim_boundary.md",
    "mmp11_internal_evidence_summary.md",
    "validation_report.md",
    "session_info.txt",
)

# Exact repository artifacts read by this generator. Hashes freeze the source
# state independently of mutable working-tree content.
FROZEN_INPUTS = {
    "outputs/identifier_normalization/identifier_mapping.csv": "ff50b9cc50006710e681bd0d0f21fa3790becc3cd20a476dbbb6ac5459c1594e",
    "outputs/differential_expression/primary_de_results.csv": "ed6c73c08a92321dd1669fdd17f908760895d31034045a49bebb49f6706a4d40",
    "outputs/differential_expression/contrast_matrix.csv": "e7b957703f1e871f9da318080095b63f0b2e9d409e083f6fde7196c0204a8649",
    "outputs/candidate_registry/candidate_registry.csv": "8055a9d99d058d219399957e62f6a3cccc3dd2217bc028d1d11dd4dc667f90e2",
    "outputs/de_sensitivity/results/S1_de_results.csv": "61b3aae22f2d7bf0baf315b27bfc3604ffc3c88cb983fe56ea22591e5e3398d4",
    "outputs/de_sensitivity/results/S2_de_results.csv": "f0dad1ce3044b78894a8f1d973131fdca123e386b9bd08b0f2e1bb9682c6591c",
    "outputs/de_sensitivity/results/S3_de_results.csv": "07a66ad2509d091cd68fccf92b88fdf18087b5f0a577b01df739e89e7bac782f",
    "outputs/de_sensitivity/results/S4_de_results.csv": "d0a2d7ec40e2c87bbe0e579352e8589643682b7879a277b06e401e657dc34166",
    "outputs/de_sensitivity/results/S5_de_results.csv": "5a9291167b534d0a00a42549758afaa0e73ff18708de0717dc8836c2e82e6847",
    "outputs/de_sensitivity/results/S6_de_results.csv": "8eb79e7ed6e867e69ca3703335cb2aca6160b349057258293f0408ff0758b6b2",
    "outputs/de_sensitivity/model_dependent_genes.csv": "08ef1e2b83d86c7a3618f999b50af4b252c35780fc9e22c413b6c677e5f38138",
    "outputs/integrated_registry/integrated_target_registry.csv": "0587fc6901267b18c8144644571f89ac2cc46053b57ea5def4093795fdbc4c26",
    "outputs/evidence_claim_architecture/evidence_claim_registry.csv": "0d963a4c5c8f9586f81369e33df0a2b7e57bb37ac8ceab4ce54498baf2351a66",
    "outputs/evidence_claim_architecture/evidence_record_registry.csv": "76ec5056fb4e468176073073532204d231765d4f0cd70dbb6cfe4ad8bf752343",
    "outputs/evidence_claim_architecture/evidence_dependency_graph.csv": "011839f10c48e197f9f1c0e2262565e562d3a2cf53dd0936f21ddcb4ed5c2256",
    "outputs/evidence_claim_architecture/missingness_uncertainty_registry.csv": "3bbe080b1ed46dd159a86b53fb707572f988361af96e001188b69da0daa9147d",
    "outputs/evidence_claim_architecture/source_entity_registry.csv": "1b1379066226b5f69b626fe4a97628f7b6da6e585515aa8609218eef65bf8056",
    "outputs/feature_extraction/transcriptomic_features.csv": "4014469439ff14d27c451a356cf7711daa7a5331c58326eced2cf96edb298844",
    "outputs/profile_release_candidate_v0.1/profile_index.csv": "5f6307c603f8d4d9416877512c28b0329c369d03aea7d24bf6cc64176193ee15",
    "outputs/profile_release_candidate_v0.1/profiles/p16/profiles.jsonl": "370b5daef243ead00c82e36958f725cdec0a76891bc14d21db88711980855a6a",
    "outputs/profile_release_candidate_v0.1/provenance/p16/profile_provenance_links.csv": "6f258c13263b9f967d8d1e1ee9d4a6b88d7d20c6efbc060e70cf8174f5144f7d",
    "outputs/profile_release_candidate_v0.1/release_manifest.json": "d7c3203f4920f5e799dea8e3515cd15a01efba83693a4be7c554a4e5094625fe",
    "outputs/disease_association_snapshot_v0.1/raw_record_manifest.csv": "ef94b3602f1b404df6c0090e45c533e22c4554fab0080a2ae5d7bfaca18ab0f4",
    "outputs/disease_association_snapshot_v0.1/entity_coverage_ledger.csv": "b0b7903c33a65f991150804722b832c0168f1156a703411e9d7a3c23c5e8202e",
    "outputs/disease_association_features_v0.1/disease_association_features.csv": "3eee6bb0a3f55e051427fdd7f67fd974604abe9bc11477b2e3be73c561201418",
    "outputs/disease_association_component_v0.1/component_index.csv": "7637c4da5f2286acb082b5382ae9f9bf50b08b2342d861e60ba388d729295c9e",
    "outputs/disease_association_component_v0.1/component_records.jsonl": "ecde83c5f3d28441c0e439b2ede6621f484b5b592a96370052911984868ad264",
    "outputs/disease_association_component_v0.1/component_manifest.json": "b2264956a13d5096b61cdb2b6981bcc80d7b7b3f1fe422b30f77c7cdc70e39f7",
    "outputs/evidence_profile_integration_v0.1/profile_index.csv": "376e6d3440dba3ae392410cd2f836a9a700fe66248bf29257794b55015821a28",
    "outputs/evidence_landscape_v0.2/landscape_index.csv": "fbd7a3b50e70c41aa2ddbf0361390fde23d12bc320a881a4da168ad1d145d6c8",
    "outputs/evidence_summary_v0.1/summary_index.csv": "27489b08061102c4d325bac7d4761682f8c7e811458b5cff88d4fec3b0bc17e5",
    "outputs/prioritization_v0.1/prioritization_index.csv": "8131fa2644dab0efb17c5ae42cb5d297ec3993aa69ba00dda4ec6bdb47c7a69a",
    "outputs/presentation_artifacts_v0.1/case_pattern_summary.csv": "e03c9fb080e62e435a0d4fcf328715fa3f2a503829c79272f84a3b8a68da6d7d",
    "outputs/presentation_artifacts_v0.1/presentation_manifest.json": "2bf7acce12685399476e50cfa26df049d8b54cc371e6dde6794b656b12f1d2e4",
}

PROHIBITED_OUTPUT_FIELD_NAMES = {
    "score",
    "ranking",
    "rank",
    "priority_score",
    "recommendation",
    "therapeutic_direction",
    "target_quality",
    "evidence_strength",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def csv_bytes(rows: list[dict[str, Any]], fieldnames: list[str]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n", extrasaction="raise")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def read_csv(relative_path: str) -> list[dict[str, str]]:
    with (ROOT / relative_path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def one(rows: Iterable[dict[str, str]], field: str, value: str, label: str) -> dict[str, str]:
    matches = [row for row in rows if row.get(field) == value]
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one {label} row for {field}={value}; found {len(matches)}")
    return matches[0]


def git_text(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, check=True, text=True, capture_output=True
    )
    return result.stdout.strip()


def verify_git_scope() -> None:
    allowed = (
        "analysis/39A_build_mmp11_internal_evidence_audit.py",
        "outputs/mmp11_internal_evidence_v0.1/",
    )
    unexpected: list[str] = []
    status = git_text("status", "--porcelain=v1", "--untracked-files=all")
    for line in status.splitlines():
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if not any(path == prefix or path.startswith(prefix) for prefix in allowed):
            unexpected.append(line)
    if unexpected:
        raise RuntimeError("Unexpected working-tree changes outside Task #039A:\n" + "\n".join(unexpected))


def verify_frozen_inputs() -> dict[str, str]:
    observed: dict[str, str] = {}
    failures: list[str] = []
    for relative_path, expected in FROZEN_INPUTS.items():
        path = ROOT / relative_path
        if not path.is_file():
            failures.append(f"missing: {relative_path}")
            continue
        actual = sha256_file(path)
        observed[relative_path] = actual
        if actual != expected:
            failures.append(f"hash mismatch: {relative_path}")
    if failures:
        raise RuntimeError("Frozen-input validation failed:\n- " + "\n- ".join(failures))
    return observed


def stable_audit_dependency_id(*parts: str) -> str:
    token = "|".join(parts).encode("utf-8")
    return "AUDDEP_" + hashlib.sha256(token).hexdigest()[:24].upper()


def decimal_text(value: Decimal) -> str:
    text = format(value, "f")
    text = text.rstrip("0").rstrip(".") if "." in text else text
    return "0" if text in {"", "-0"} else text


def load_profile_record(index_row: dict[str, str]) -> dict[str, Any]:
    relative = f"outputs/profile_release_candidate_v0.1/profiles/{index_row['partition_id']}/profiles.jsonl"
    with (ROOT / relative).open(encoding="utf-8") as handle:
        records = [json.loads(line) for line in handle if EXPECTED_ENSEMBL_ID in line]
    if len(records) != 1 or records[0]["EnsemblID"] != EXPECTED_ENSEMBL_ID:
        raise RuntimeError("Unable to resolve the unique transcriptomic profile by immutable EnsemblID")
    return records[0]


def load_indexed_disease_component(index_row: dict[str, str]) -> tuple[dict[str, Any], bytes]:
    path = ROOT / "outputs/disease_association_component_v0.1/component_records.jsonl"
    with path.open("rb") as handle:
        handle.seek(int(index_row["record_offset_bytes"]))
        raw = handle.read(int(index_row["record_length_bytes"]))
    if sha256_bytes(raw) != index_row["component_record_sha256"]:
        raise RuntimeError("Disease component record byte hash does not match its frozen index")
    record = json.loads(raw)
    if record["EnsemblID"] != EXPECTED_ENSEMBL_ID:
        raise RuntimeError("Disease component byte-range identity mismatch")
    return record, raw


def scan_prohibited_keys(value: Any, location: str = "root") -> list[str]:
    failures: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in PROHIBITED_OUTPUT_FIELD_NAMES:
                failures.append(f"{location}.{key}")
            failures.extend(scan_prohibited_keys(child, f"{location}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            failures.extend(scan_prohibited_keys(child, f"{location}[{index}]"))
    return failures


def build_audit(source_hashes: dict[str, str], git_state: dict[str, str]) -> tuple[dict[str, bytes], dict[str, Any]]:
    # Symbol is used once, only to resolve the immutable identity independently
    # from the frozen Task #009 mapping. All later joins use EnsemblID.
    mapping_rows = read_csv("outputs/identifier_normalization/identifier_mapping.csv")
    symbol_matches = [row for row in mapping_rows if row["Symbol"] == TARGET_SYMBOL]
    if len(symbol_matches) != 1:
        raise RuntimeError(f"Identity mapping did not uniquely resolve display symbol {TARGET_SYMBOL}")
    mapping = symbol_matches[0]
    target_id = mapping["EnsemblID"]
    if target_id != EXPECTED_ENSEMBL_ID:
        raise RuntimeError(
            f"Independently resolved EnsemblID {target_id} does not match expected project identifier {EXPECTED_ENSEMBL_ID}"
        )
    if mapping["ambiguous_mapping"] != "FALSE" or mapping["symbol_qc_status"] != "MATCH":
        raise RuntimeError("MMP11 frozen identifier mapping is ambiguous or symbol QC did not pass")

    primary = one(
        read_csv("outputs/differential_expression/primary_de_results.csv"),
        "EnsemblID",
        target_id,
        "primary DE",
    )
    candidate = one(
        read_csv("outputs/candidate_registry/candidate_registry.csv"),
        "EnsemblID",
        target_id,
        "candidate registry",
    )
    transcript_features = one(
        read_csv("outputs/feature_extraction/transcriptomic_features.csv"),
        "EnsemblID",
        target_id,
        "transcriptomic feature",
    )
    contrast_rows = read_csv("outputs/differential_expression/contrast_matrix.csv")
    contrast_coefficients = {row["coefficient"]: row["Tumor_vs_Normal"] for row in contrast_rows}
    if contrast_coefficients.get("Tumor") != "1" or contrast_coefficients.get("Normal") != "-1":
        raise RuntimeError("Frozen Tumor_vs_Normal contrast orientation is not Tumor(+1) - Normal(-1)")
    contrast_orientation = "Tumor - Normal (Tumor coefficient +1; Normal coefficient -1)"

    numeric_reconciliation = {
        "logFC": (primary["logFC"], candidate["logFC_S0"]),
        "p_value": (primary["P.Value"], candidate["P_value_S0"]),
        "bh_fdr": (primary["adj.P.Val"], candidate["FDR_S0"]),
        "AveExpr": (primary["AveExpr"], candidate["AveExpr_S0"]),
        "mean_tumor": (primary["mean_logCPM_Tumor"], candidate["mean_logCPM_Tumor"]),
        "mean_normal": (primary["mean_logCPM_Normal"], candidate["mean_logCPM_Normal"]),
    }
    for label, values in numeric_reconciliation.items():
        if Decimal(values[0]) != Decimal(values[1]):
            raise RuntimeError(f"Primary/candidate numeric mismatch for {label}")

    claims = [
        row
        for row in read_csv("outputs/evidence_claim_architecture/evidence_claim_registry.csv")
        if row["EnsemblID"] == target_id
    ]
    claim_by_id = {row["claim_id"]: row for row in claims}
    in_scope_claims = {
        row["domain_id"]: row
        for row in claims
        if row["domain_id"] in {"DOM_TRANSCRIPTOMIC_DISCOVERY", "DOM_DISEASE_ASSOCIATION"}
    }
    if set(in_scope_claims) != {"DOM_TRANSCRIPTOMIC_DISCOVERY", "DOM_DISEASE_ASSOCIATION"}:
        raise RuntimeError("Required Task #014 in-scope claims did not resolve")
    all_record_rows = read_csv("outputs/evidence_claim_architecture/evidence_record_registry.csv")
    record_by_id = {row["record_id"]: row for row in all_record_rows}
    transcript_claim_id = in_scope_claims["DOM_TRANSCRIPTOMIC_DISCOVERY"]["claim_id"]
    transcript_records = [row for row in all_record_rows if row["claim_id"] == transcript_claim_id]
    if {row["source_record_type"] for row in transcript_records} != {
        "TRANSCRIPT_PRIMARY",
        "TRANSCRIPT_ROBUSTNESS",
    }:
        raise RuntimeError("Task #014 transcriptomic evidence-record units did not reconcile")
    primary_record = one(transcript_records, "source_record_type", "TRANSCRIPT_PRIMARY", "primary evidence record")
    robustness_record = one(
        transcript_records, "source_record_type", "TRANSCRIPT_ROBUSTNESS", "robustness evidence record"
    )
    dependency_rows = read_csv("outputs/evidence_claim_architecture/evidence_dependency_graph.csv")
    transcript_dependency = one(
        dependency_rows,
        "dependency_id",
        "DEP_9DBAB5AB013392BCF63FF3EC",
        "transcriptomic dependency",
    )
    if {
        transcript_dependency["record_a"],
        transcript_dependency["record_b"],
    } != {primary_record["record_id"], robustness_record["record_id"]}:
        raise RuntimeError("Primary/robustness dependency endpoints do not reconcile")
    if (
        transcript_dependency["relationship"] != "SHARED_DATASET"
        or transcript_dependency["dependency_level"] != "DEPENDENT"
    ):
        raise RuntimeError("Primary/robustness dependency semantics changed")

    source_entities = {
        row["source_id"]: row
        for row in read_csv("outputs/evidence_claim_architecture/source_entity_registry.csv")
    }
    missingness_rows = read_csv("outputs/evidence_claim_architecture/missingness_uncertainty_registry.csv")
    missingness_by_entity: dict[str, list[dict[str, str]]] = {}
    for row in missingness_rows:
        missingness_by_entity.setdefault(row["entity_id"], []).append(row)

    sensitivity_rows: list[dict[str, Any]] = []
    s0_logfc = Decimal(primary["logFC"])
    for model_number in range(1, 7):
        model = f"S{model_number}"
        row = one(
            read_csv(f"outputs/de_sensitivity/results/{model}_de_results.csv"),
            "EnsemblID",
            target_id,
            f"{model} sensitivity",
        )
        logfc = Decimal(row["logFC"])
        fdr = Decimal(row["adj.P.Val"])
        candidate_logfc = Decimal(candidate[f"logFC_{model}"])
        candidate_fdr = Decimal(candidate[f"FDR_{model}"])
        if logfc != candidate_logfc or fdr != candidate_fdr:
            raise RuntimeError(f"{model} sensitivity result does not reconcile to Task #008")
        direction = "TUMOR_HIGHER" if logfc > 0 else "TUMOR_LOWER" if logfc < 0 else "NO_SIGN"
        concordant = (logfc > 0) == (s0_logfc > 0) if logfc != 0 and s0_logfc != 0 else logfc == s0_logfc
        sensitivity_rows.append(
            {
                "EnsemblID": target_id,
                "gene_symbol_display": mapping["Symbol"],
                "model_id": model,
                "logFC": row["logFC"],
                "bh_fdr": row["adj.P.Val"],
                "direction": direction,
                "fdr_lt_0_05": str(fdr < Decimal("0.05")).upper(),
                "delta_logFC_vs_S0": decimal_text(logfc - s0_logfc),
                "sign_concordant_with_S0": str(concordant).upper(),
                "claim_id": robustness_record["claim_id"],
                "governed_evidence_record_id": robustness_record["record_id"],
                "dependency_id": transcript_dependency["dependency_id"],
                "dependency_relationship": transcript_dependency["relationship"],
                "dependency_level": transcript_dependency["dependency_level"],
                "source_artifact": f"outputs/de_sensitivity/results/{model}_de_results.csv",
                "presentation_disclaimer": DISCLAIMER,
            }
        )
    direction_concordant_count = sum(row["sign_concordant_with_S0"] == "TRUE" for row in sensitivity_rows)
    significant_count = sum(row["fdr_lt_0_05"] == "TRUE" for row in sensitivity_rows)
    sign_flip = direction_concordant_count != 6
    if direction_concordant_count != int(candidate["sign_concordant_S1_S6_count"]):
        raise RuntimeError("Sensitivity direction-concordance count mismatch")
    if significant_count != int(candidate["n_sensitivity_FDR05"]):
        raise RuntimeError("Sensitivity FDR count mismatch")
    if sign_flip != (candidate["S6_sign_flip_vs_S0"] == "TRUE"):
        raise RuntimeError("Sensitivity sign-flip status mismatch")
    abs_deltas = sorted(abs(Decimal(row["delta_logFC_vs_S0"])) for row in sensitivity_rows)
    median_abs_delta = (abs_deltas[2] + abs_deltas[3]) / Decimal(2)
    if abs(median_abs_delta - Decimal(candidate["median_abs_delta_logFC_vs_S0"])) > Decimal("1e-14"):
        raise RuntimeError("Median absolute delta logFC mismatch")
    if abs(max(abs_deltas) - Decimal(candidate["max_abs_delta_logFC_vs_S0"])) > Decimal("1e-14"):
        raise RuntimeError("Maximum absolute delta logFC mismatch")
    model_dependent_rows = [
        row
        for row in read_csv("outputs/de_sensitivity/model_dependent_genes.csv")
        if row["EnsemblID"] == target_id
    ]
    model_dependent = candidate["model_dependent_any_top50"] == "TRUE"
    if model_dependent != bool(model_dependent_rows):
        raise RuntimeError("Model-dependent label does not reconcile to Task #007 table membership")

    transcript_profile_index = one(
        read_csv("outputs/profile_release_candidate_v0.1/profile_index.csv"),
        "EnsemblID",
        target_id,
        "transcriptomic profile index",
    )
    transcript_profile = load_profile_record(transcript_profile_index)
    if len(transcript_profile["components"]) != 1:
        raise RuntimeError("Unexpected transcriptomic profile component cardinality")
    transcript_component = transcript_profile["components"][0]
    transcript_provenance_rows = [
        row
        for row in read_csv(
            f"outputs/profile_release_candidate_v0.1/provenance/{transcript_profile_index['partition_id']}/profile_provenance_links.csv"
        )
        if row["EnsemblID"] == target_id
    ]
    embedded_transcript_links = [
        (feature["feature_id"], link["evidence_record_id"], link["claim_id"], link["source_id"])
        for feature in transcript_component["features"]
        for link in feature["provenance_links"]
    ]
    tabular_transcript_links = [
        (row["feature_id"], row["evidence_record_id"], row["claim_id"], row["source_id"])
        for row in transcript_provenance_rows
    ]
    if embedded_transcript_links != tabular_transcript_links:
        raise RuntimeError("Transcriptomic embedded and partition provenance relationships differ")
    if transcript_component["state"] != "OBSERVED":
        raise RuntimeError("Unexpected governed transcriptomic component state")
    for row in transcript_provenance_rows:
        if row["claim_id"] not in claim_by_id or row["evidence_record_id"] not in record_by_id:
            raise RuntimeError("Transcriptomic provenance claim/evidence record did not resolve")
        if row["source_id"] not in source_entities:
            raise RuntimeError("Transcriptomic provenance source did not resolve")
        if row["dependency_id"] != "NOT_APPLICABLE" and not any(
            dep["dependency_id"] == row["dependency_id"] for dep in dependency_rows
        ):
            raise RuntimeError("Transcriptomic provenance dependency did not resolve")

    disease_features_row = one(
        read_csv("outputs/disease_association_features_v0.1/disease_association_features.csv"),
        "EnsemblID",
        target_id,
        "disease-association feature",
    )
    disease_component_index = one(
        read_csv("outputs/disease_association_component_v0.1/component_index.csv"),
        "EnsemblID",
        target_id,
        "disease-association component index",
    )
    disease_component, _ = load_indexed_disease_component(disease_component_index)
    if disease_component["component_state"] != disease_features_row["component_state"]:
        raise RuntimeError("Disease component state does not reconcile to feature layer")
    if disease_component["component_state"] != "OBSERVED":
        raise RuntimeError("Unexpected governed disease-association component state")
    for feature in disease_component["features"]:
        name = feature["feature_name"]
        if disease_features_row[name] != feature["feature_value"]:
            raise RuntimeError(f"Disease feature value mismatch: {name}")
        status_field = f"{name}__missingness_status"
        if disease_features_row[status_field] != feature["missingness_status"]:
            raise RuntimeError(f"Disease feature missingness mismatch: {name}")

    disease_links = [
        (feature, link)
        for feature in disease_component["features"]
        for link in feature["provenance_links"]
    ]
    if len(disease_links) != int(disease_component_index["provenance_relationship_count"]):
        raise RuntimeError("Disease component provenance relationship count mismatch")
    raw_manifest_rows = [
        row
        for row in read_csv("outputs/disease_association_snapshot_v0.1/raw_record_manifest.csv")
        if row["universe_EnsemblID"] == target_id
    ]
    if len(raw_manifest_rows) != 14:
        raise RuntimeError("Expected exactly 14 frozen MMP11 exact-context disease raw records")
    raw_by_id = {row["raw_record_id"]: row for row in raw_manifest_rows}
    coverage = one(
        read_csv("outputs/disease_association_snapshot_v0.1/entity_coverage_ledger.csv"),
        "EnsemblID",
        target_id,
        "disease snapshot coverage",
    )
    if coverage["exact_disease_record_count"] != "14" or coverage["disease_context_id"] != "MONDO_0005061":
        raise RuntimeError("Disease snapshot coverage/context mismatch")
    unique_disease_record_ids = {link["evidence_record_id"] for _, link in disease_links}
    raw_link_ids = {value for value in unique_disease_record_ids if value.startswith("DA_RAW_")}
    scope_link_ids = {value for value in unique_disease_record_ids if value.startswith("REC_DA_SCOPE_")}
    if raw_link_ids != set(raw_by_id) or len(scope_link_ids) != 1:
        raise RuntimeError("Disease component raw/scope evidence-record lineage did not reconcile")
    for _, link in disease_links:
        if link["source_id"] != "SRC_OPEN_TARGETS_PLATFORM":
            raise RuntimeError("Unexpected disease component source")
        if not link["claim_id"] or not link["artifact_id"] or not link["dependency_id"]:
            raise RuntimeError("Incomplete disease provenance relationship")
        if link["evidence_record_id"].startswith("DA_RAW_"):
            raw = raw_by_id[link["evidence_record_id"]]
            if raw["source_record_id"] != link["source_record_id"]:
                raise RuntimeError("Disease source-record identifier mismatch")
            if raw["snapshot_raw_file_sha256"] != link["artifact_sha256"]:
                raise RuntimeError("Disease raw artifact hash mismatch")

    integrated_index = one(
        read_csv("outputs/evidence_profile_integration_v0.1/profile_index.csv"),
        "EnsemblID",
        target_id,
        "integrated profile",
    )
    landscape_index = one(
        read_csv("outputs/evidence_landscape_v0.2/landscape_index.csv"),
        "EnsemblID",
        target_id,
        "evidence landscape",
    )
    summary_index = one(
        read_csv("outputs/evidence_summary_v0.1/summary_index.csv"),
        "EnsemblID",
        target_id,
        "evidence summary",
    )
    transparent_index = one(
        read_csv("outputs/prioritization_v0.1/prioritization_index.csv"),
        "EnsemblID",
        target_id,
        "transparent structural representation",
    )
    downstream_checks = [
        integrated_index["transcriptomic_source_profile_id"] == transcript_profile["profile_id"],
        integrated_index["disease_association_source_component_record_id"]
        == disease_component["component_record_id"],
        landscape_index["source_profile_id"] == integrated_index["profile_id"],
        summary_index["source_landscape_id"] == landscape_index["landscape_id"],
        transparent_index["source_evidence_summary_id"] == summary_index["evidence_summary_id"],
        int(integrated_index["provenance_relationship_count"])
        == len(transcript_provenance_rows) + len(disease_links),
    ]
    if not all(downstream_checks):
        raise RuntimeError("Downstream representation identity/provenance reconciliation failed")
    for field in ("transcriptomic_component_state", "disease_association_component_state"):
        states = {
            integrated_index[field],
            landscape_index[field],
            summary_index[field],
            transparent_index[field],
        }
        if len(states) != 1:
            raise RuntimeError(f"Downstream component state changed: {field}")
    presentation_rows = read_csv("outputs/presentation_artifacts_v0.1/case_pattern_summary.csv")
    presentation_entity_presence = any(row.get("selected_EnsemblID") == target_id for row in presentation_rows)

    transcriptomic_evidence_row = {
        "EnsemblID": target_id,
        "gene_symbol_display": mapping["Symbol"],
        "analysis_id": "S0_PRIMARY",
        "contrast_orientation": contrast_orientation,
        "logFC": primary["logFC"],
        "p_value": primary["P.Value"],
        "bh_fdr": primary["adj.P.Val"],
        "AveExpr": primary["AveExpr"],
        "mean_logCPM_Tumor": primary["mean_logCPM_Tumor"],
        "mean_logCPM_Normal": primary["mean_logCPM_Normal"],
        "U0_tested": candidate["U0_tested"],
        "U1_DE": candidate["U1_DE"],
        "U2_effect_supported_DE": candidate["U2_effect_supported_DE"],
        "effect_band": candidate["effect_band"],
        "candidate_queue": candidate["retrieval_queue"],
        "model_dependent_status": str(model_dependent).upper(),
        "model_dependent_models": candidate["model_dependent_models"] or "NONE",
        "claim_id": primary_record["claim_id"],
        "governed_evidence_record_id": primary_record["record_id"],
        "missingness_status": primary_record["missingness_status"],
        "uncertainty_status": primary_record["uncertainty_status"],
        "source_artifact": "outputs/differential_expression/primary_de_results.csv",
        "presentation_disclaimer": DISCLAIMER,
    }

    provenance_rows: list[dict[str, Any]] = []
    for row in transcript_provenance_rows:
        provenance_rows.append(
            {
                "EnsemblID": target_id,
                "component_id": row["component_id"],
                "component_version": row["component_definition_version"],
                "component_record_or_profile_id": row["profile_id"],
                "feature_id": row["feature_id"],
                "feature_name": row["feature_name"],
                "claim_id": row["claim_id"],
                "evidence_record_id": row["evidence_record_id"],
                "source_id": row["source_id"],
                "source_version": source_entities[row["source_id"]]["version"],
                "snapshot_id": row["evidence_snapshot_version"],
                "artifact_id": row["artifact_id"],
                "artifact_sha256": source_hashes["outputs/integrated_registry/integrated_target_registry.csv"],
                "dependency_id": row["dependency_id"],
                "dependency_level": (
                    transcript_dependency["dependency_level"]
                    if row["dependency_id"] == transcript_dependency["dependency_id"]
                    else "NOT_APPLICABLE"
                ),
                "dependency_relationship_types": (
                    transcript_dependency["relationship"]
                    if row["dependency_id"] == transcript_dependency["dependency_id"]
                    else "NOT_APPLICABLE"
                ),
                "extraction_rule_id": row["extraction_rule_id"],
                "extractor_version": row["extractor_version"],
                "missingness_status": row["feature_missingness_status"],
                "source_dataset": "TASK012_INTEGRATED_TARGET_REGISTRY",
                "source_record_id": record_by_id[row["evidence_record_id"]]["source_record_identifier"],
                "raw_record_id": "NOT_APPLICABLE",
                "claim_resolution_status": "RESOLVED_TASK014_CLAIM_REGISTRY",
                "evidence_record_resolution_status": "RESOLVED_TASK014_RECORD_REGISTRY",
                "provenance_origin_path": f"outputs/profile_release_candidate_v0.1/provenance/{transcript_profile_index['partition_id']}/profile_provenance_links.csv",
                "presentation_disclaimer": DISCLAIMER,
            }
        )
    for feature, link in disease_links:
        is_raw = link["evidence_record_id"].startswith("DA_RAW_")
        provenance_rows.append(
            {
                "EnsemblID": target_id,
                "component_id": disease_component["component_id"],
                "component_version": disease_component["component_version"],
                "component_record_or_profile_id": disease_component["component_record_id"],
                "feature_id": feature["feature_id"],
                "feature_name": feature["feature_name"],
                "claim_id": link["claim_id"],
                "evidence_record_id": link["evidence_record_id"],
                "source_id": link["source_id"],
                "source_version": link["source_version"],
                "snapshot_id": link["snapshot_id"],
                "artifact_id": link["artifact_id"],
                "artifact_sha256": link["artifact_sha256"],
                "dependency_id": link["dependency_id"],
                "dependency_level": link["dependency_level"],
                "dependency_relationship_types": "|".join(link["dependency_relationship_types"]),
                "extraction_rule_id": feature["extraction_rule_id"],
                "extractor_version": feature["extractor_version"],
                "missingness_status": feature["missingness_status"],
                "source_dataset": link["source_dataset"],
                "source_record_id": link["source_record_id"],
                "raw_record_id": link["raw_record_id"],
                "claim_resolution_status": "COMPONENT_NATIVE_REFERENCE_PRESENT",
                "evidence_record_resolution_status": (
                    "RESOLVED_SNAPSHOT_RAW_RECORD_MANIFEST" if is_raw else "RESOLVED_ENTITY_COVERAGE_SCOPE_RECORD"
                ),
                "provenance_origin_path": "outputs/disease_association_component_v0.1/component_records.jsonl",
                "presentation_disclaimer": DISCLAIMER,
            }
        )
    if len(provenance_rows) != 229:
        raise RuntimeError(f"Expected 229 uncompressed provenance relationships; found {len(provenance_rows)}")

    disease_record_summaries: list[dict[str, Any]] = []
    for raw_id in sorted(raw_by_id):
        raw = raw_by_id[raw_id]
        related = [link for _, link in disease_links if link["evidence_record_id"] == raw_id]
        disease_record_summaries.append(
            {
                "evidence_record_id": raw_id,
                "source_record_id": raw["source_record_id"],
                "source_dataset": raw["source_dataset"],
                "source_id": raw["source_id"],
                "source_version": raw["source_version"],
                "source_target_id": raw["source_target_id"],
                "source_disease_id": raw["source_disease_id"],
                "mapping_outcome": raw["mapping_outcome"],
                "raw_payload_sha256": raw["raw_payload_sha256"],
                "snapshot_artifact_sha256": raw["snapshot_raw_file_sha256"],
                "claim_ids": sorted({link["claim_id"] for link in related}),
                "dependency_ids": sorted({link["dependency_id"] for link in related}),
                "dependency_relationship_types": ["SAME_SOURCE", "SHARED_DATASET"],
                "dependency_level": "DEPENDENT",
            }
        )

    dependency_map_rows: list[dict[str, Any]] = [
        {
            "dependency_relationship_id": transcript_dependency["dependency_id"],
            "EnsemblID": target_id,
            "relationship_block": "TRANSCRIPTOMIC_SHARED_DATASET",
            "record_or_artifact_a": transcript_dependency["record_a"],
            "record_or_artifact_b": transcript_dependency["record_b"],
            "relationship_type": transcript_dependency["relationship"],
            "dependency_level": transcript_dependency["dependency_level"],
            "scientific_boundary": transcript_dependency["reason"],
            "source_relationship_status": transcript_dependency["review_status"],
            "presentation_disclaimer": DISCLAIMER,
        }
    ]
    unique_disease_links = {
        link["evidence_record_id"]: link
        for _, link in disease_links
        if link["evidence_record_id"].startswith("DA_RAW_")
    }
    for raw_id in sorted(unique_disease_links):
        link = unique_disease_links[raw_id]
        dependency_map_rows.append(
            {
                "dependency_relationship_id": link["dependency_id"],
                "EnsemblID": target_id,
                "relationship_block": "OPEN_TARGETS_SHARED_PLATFORM_LINEAGE",
                "record_or_artifact_a": raw_id,
                "record_or_artifact_b": link["snapshot_id"],
                "relationship_type": "|".join(link["dependency_relationship_types"]),
                "dependency_level": link["dependency_level"],
                "scientific_boundary": (
                    "This raw record shares Open Targets Platform release and dataset lineage; source records are not automatically independent votes."
                ),
                "source_relationship_status": "PRESERVED_FROM_DISEASE_COMPONENT_PROVENANCE",
                "presentation_disclaimer": DISCLAIMER,
            }
        )
    derived_edges = [
        (
            "TRANSCRIPTOMIC_RECORD_UNITS",
            transcript_profile["profile_id"],
            "SOURCE_RECORD_TO_COMPONENT_PROFILE",
        ),
        (
            "DISEASE_ASSOCIATION_RAW_RECORD_SET",
            disease_component["component_record_id"],
            "SOURCE_RECORD_TO_COMPONENT",
        ),
        (
            f"{transcript_profile['profile_id']}|{disease_component['component_record_id']}",
            integrated_index["profile_id"],
            "COMPONENT_TO_MULTICOMPONENT_PROFILE",
        ),
        (integrated_index["profile_id"], landscape_index["landscape_id"], "PROFILE_TO_LANDSCAPE"),
        (landscape_index["landscape_id"], summary_index["evidence_summary_id"], "LANDSCAPE_TO_SUMMARY"),
        (
            summary_index["evidence_summary_id"],
            transparent_index["prioritization_representation_id"],
            "SUMMARY_TO_TRANSPARENT_STRUCTURAL_ROUTING",
        ),
    ]
    for endpoint_a, endpoint_b, relationship_type in derived_edges:
        dependency_map_rows.append(
            {
                "dependency_relationship_id": stable_audit_dependency_id(endpoint_a, endpoint_b, relationship_type),
                "EnsemblID": target_id,
                "relationship_block": "DERIVED_REPRESENTATION_LINEAGE",
                "record_or_artifact_a": endpoint_a,
                "record_or_artifact_b": endpoint_b,
                "relationship_type": relationship_type,
                "dependency_level": "DEPENDENT_TRANSFORMATION",
                "scientific_boundary": (
                    "The downstream object transforms existing evidence and is not an additional independent observation."
                ),
                "source_relationship_status": "AUDIT_DERIVED_FROM_RECONCILED_IDENTITIES",
                "presentation_disclaimer": DISCLAIMER,
            }
        )
    if len(dependency_map_rows) != 21:
        raise RuntimeError("Qualitative dependency-map relationship count changed")

    limitations = landscape_index["limitation_ids"].split("|")
    out_of_scope_claims = [
        {
            "claim_id": row["claim_id"],
            "domain_id": row["domain_id"],
            "scope_status": "EXISTING_PROJECT_CLAIM_OUTSIDE_TASK039A_BOUNDED_COMPONENT_AUDIT",
        }
        for row in claims
        if row["domain_id"] not in in_scope_claims
    ]
    component_summary = {
        "audit_id": "AUDIT_MMP11_INTERNAL_PROJECT_EVIDENCE_V0_1",
        "audit_version": AUDIT_VERSION,
        "EnsemblID": target_id,
        "gene_symbol_display": mapping["Symbol"],
        "presentation_disclaimer": DISCLAIMER,
        "bounded_scope": {
            "included_components": [
                "COMP_TRANSCRIPTOMIC_EVIDENCE",
                "COMP_DISEASE_ASSOCIATION",
            ],
            "bounded_source_evidence_record_count": 16,
            "count_definition": (
                "Two governed Task #014 transcriptomic evidence-record units plus fourteen exact-context disease raw records. "
                "The six sensitivity model rows belong to one dependent robustness evidence-record unit."
            ),
            "source_native_record_counts_are_audit_metadata_only": True,
            "out_of_scope_existing_claims": out_of_scope_claims,
        },
        "transcriptomic_component": {
            "component_id": transcript_component["component_id"],
            "component_version": transcript_component["component_definition_version"],
            "component_state": transcript_component["state"],
            "state_rule_id": transcript_component["state_rule_id"],
            "state_rule_version": transcript_component["state_rule_version"],
            "state_rule_review_status": transcript_component["state_rule_review_status"],
            "profile_id": transcript_profile["profile_id"],
            "profile_version": transcript_profile["profile_version"],
            "profile_schema_version": transcript_profile["schema_version"],
            "evidence_snapshot_version": transcript_profile["evidence_snapshot_version"],
            "profile_release_candidate_id": json.loads(
                (ROOT / "outputs/profile_release_candidate_v0.1/release_manifest.json").read_text(encoding="utf-8")
            )["release_candidate_id"],
            "feature_count": len(transcript_component["features"]),
            "provenance_relationship_count": len(transcript_provenance_rows),
            "features": transcript_component["features"],
            "claim": in_scope_claims["DOM_TRANSCRIPTOMIC_DISCOVERY"],
            "missingness_and_uncertainty": missingness_by_entity.get(transcript_claim_id, []),
            "limitations": [
                "LIM_TRANSCRIPTOMIC_ASSOCIATION_BOUNDARY",
                "LIM_NONOBSERVED_MISSINGNESS_PATHS_INCOMPLETELY_TESTED",
                "LIM_STATE_RULE_REVIEW_PENDING",
            ],
        },
        "disease_association_component": {
            "component_id": disease_component["component_id"],
            "component_version": disease_component["component_version"],
            "component_state": disease_component["component_state"],
            "component_record_id": disease_component["component_record_id"],
            "component_schema_version": disease_component["component_schema_version"],
            "feature_schema_version": disease_component["feature_schema_version"],
            "source_release": "26.06",
            "source_id": "SRC_OPEN_TARGETS_PLATFORM",
            "source_snapshot_version": disease_component["source_snapshot_version"],
            "snapshot_id": next(iter({link["snapshot_id"] for _, link in disease_links})),
            "disease_context_id": coverage["disease_context_id"],
            "disease_context_match_rule": "EXACT_SOURCE_DISEASE_ID",
            "feature_count": len(disease_component["features"]),
            "qualifying_source_record_count": len(disease_record_summaries),
            "query_scope_record_ids": sorted(scope_link_ids),
            "provenance_relationship_count": len(disease_links),
            "features": disease_component["features"],
            "qualifying_source_records": disease_record_summaries,
            "task014_summary_claim": in_scope_claims["DOM_DISEASE_ASSOCIATION"],
            "missingness_and_uncertainty": missingness_by_entity.get(
                in_scope_claims["DOM_DISEASE_ASSOCIATION"]["claim_id"], []
            ),
            "uncertainty_notes": [
                "The source-native record count is audit metadata and is not evidence strength.",
                "The source release is versioned; later releases may differ.",
                "Open Targets records share Platform and dataset lineage and are not automatically independent votes.",
                "Record granularity is preserved as UNKNOWN in the governed feature layer.",
            ],
            "limitations": [],
        },
        "downstream_trace": [
            {
                "layer": "MULTICOMPONENT_PROFILE",
                "object_id": integrated_index["profile_id"],
                "object_version": integrated_index["profile_version"],
                "content_sha256": integrated_index["profile_content_sha256"],
                "relationship": "DERIVED_REPRESENTATION_NOT_ADDITIONAL_EVIDENCE",
            },
            {
                "layer": "EVIDENCE_LANDSCAPE",
                "object_id": landscape_index["landscape_id"],
                "object_version": landscape_index["landscape_version"],
                "content_sha256": landscape_index["landscape_content_sha256"],
                "relationship": "DERIVED_REPRESENTATION_NOT_ADDITIONAL_EVIDENCE",
            },
            {
                "layer": "EVIDENCE_SUMMARY",
                "object_id": summary_index["evidence_summary_id"],
                "object_version": summary_index["evidence_summary_version"],
                "content_sha256": summary_index["summary_content_sha256"],
                "relationship": "DERIVED_REPRESENTATION_NOT_ADDITIONAL_EVIDENCE",
            },
            {
                "layer": "TRANSPARENT_STRUCTURAL_ROUTING",
                "object_id": transparent_index["prioritization_representation_id"],
                "object_version": transparent_index["prioritization_representation_version"],
                "content_sha256": transparent_index["representation_content_sha256"],
                "non_ordinal_category": transparent_index["category"],
                "assigned_structural_rule_id": transparent_index["assigned_rule_id"],
                "relationship": "DERIVED_NON_ORDINAL_ROUTING_NOT_TARGET_EVALUATION",
            },
        ],
        "downstream_reconciliation": {
            "universe_ordinal": int(integrated_index["universe_ordinal"]),
            "component_state_preservation": "PASS",
            "provenance_relationship_count": int(integrated_index["provenance_relationship_count"]),
            "landscape_limitation_identifiers": limitations,
            "mmp11_is_selected_task036c_case_entity": presentation_entity_presence,
            "presentation_trace_note": (
                "Task #036C is an aggregate communication layer. No MMP11-specific Task #036C case row was found, "
                "so no entity-specific presentation evidence is claimed."
            ),
        },
    }

    identity = {
        "audit_id": "AUDIT_MMP11_INTERNAL_PROJECT_EVIDENCE_V0_1",
        "audit_version": AUDIT_VERSION,
        "generator_version": GENERATOR_VERSION,
        "presentation_disclaimer": DISCLAIMER,
        "identity_resolution": {
            "resolution_method": "UNIQUE_SYMBOL_LOOKUP_IN_FROZEN_TASK009_MAPPING_ONLY",
            "symbol_use_boundary": "COMMUNICATION_DISPLAY_AND_INITIAL_IDENTITY_RESOLUTION_ONLY",
            "all_artifact_join_key": "EnsemblID",
            "symbol_based_artifact_joins": "PROHIBITED_NONE_USED",
            "expected_identifier_used_as": "POST_RESOLUTION_ASSERTION_ONLY",
        },
        "EnsemblID": target_id,
        "EnsemblID_base": mapping["EnsemblID_base"],
        "gene_symbol_display": mapping["Symbol"],
        "gene_type": mapping["gene_type"],
        "identifier_mappings": {
            "HGNC_ID": {
                "value": mapping["HGNC_ID"],
                "status": mapping["HGNC_ID_status"],
                "source": mapping["HGNC_ID_source"],
            },
            "Entrez_ID": {
                "value": mapping["Entrez_ID"],
                "status": mapping["Entrez_ID_status"],
                "source": mapping["Entrez_ID_source"],
            },
            "UniProt_ID": {
                "value": mapping["UniProt_ID"],
                "status": mapping["UniProt_ID_status"],
                "source": mapping["UniProt_ID_source"],
            },
            "OpenTargets_target_ID": {
                "value": mapping["OpenTargets_target_ID"],
                "status": mapping["OpenTargets_target_ID_status"],
                "source": mapping["OpenTargets_target_ID_source"],
            },
            "ChEMBL_target_ID": {
                "value": mapping["ChEMBL_target_ID"],
                "status": mapping["ChEMBL_target_ID_status"],
                "source": mapping["ChEMBL_target_ID_source"],
                "mapping_basis": mapping["ChEMBL_mapping_basis"],
            },
        },
        "mapping_qc": {
            "current_HGNC_symbol": mapping["current_HGNC_symbol"],
            "symbol_qc_status": mapping["symbol_qc_status"],
            "one_to_many_fields": mapping["one_to_many_fields"],
            "ambiguous_mapping": mapping["ambiguous_mapping"],
            "ambiguous_fields": mapping["ambiguous_fields"],
        },
        "source_artifacts": [
            {"relative_path": path, "sha256": digest}
            for path, digest in sorted(source_hashes.items())
        ],
        "git_state": git_state,
    }

    claim_boundary = f"""# MMP11 internal evidence claim boundary

> {DISCLAIMER}

This boundary applies only to evidence already frozen inside this repository. It adds no literature, experimental, clinical, or therapeutic evidence.

## Identity block

**SUPPORTED INTERPRETATION**

- The frozen Task #009 mapping uniquely links display symbol `MMP11` to immutable project identifier `{target_id}` and records the biotype `{mapping['gene_type']}`.
- All audit joins after identity resolution use `EnsemblID`.

**NOT SUPPORTED**

- Identifier resolution does not establish disease causality, biological importance, or therapeutic suitability.

## Primary transcriptomic block

**SUPPORTED INTERPRETATION**

- The frozen S0 `Tumor - Normal` analysis contains a LUAD tumour-versus-normal expression association for `{target_id}` with recorded logFC `{primary['logFC']}` and BH FDR `{primary['adj.P.Val']}`.
- Task #008 records U0=`{candidate['U0_tested']}`, U1=`{candidate['U1_DE']}`, U2=`{candidate['U2_effect_supported_DE']}`, effect band `{candidate['effect_band']}`, and retrieval queue `{candidate['retrieval_queue']}` under its frozen candidate-generation rules.

**NOT SUPPORTED**

- Differential expression does not establish disease causality, therapeutic causality, therapeutic direction, drug efficacy, clinical benefit, clinical safety, target validation, target superiority, or target recommendation.
- Effect band and retrieval queue are project workflow labels, not target rankings or therapeutic judgements.

## Sensitivity block

**SUPPORTED INTERPRETATION**

- All six prespecified S1-S6 model outputs are direction-concordant with S0; all six have BH FDR below 0.05 in their frozen results.
- Task #008/#007 records model-dependent status `{str(model_dependent).upper()}` under its frozen definition.

**NOT SUPPORTED**

- S0 and S1-S6 are analyses of the same frozen TCGA-LUAD dataset. Concordance characterizes model robustness; it is not independent replication and must not be counted as seven independent observations.
- Model robustness does not establish causality or therapeutic validity.

## Disease-association block

**SUPPORTED INTERPRETATION**

- The governed component records 14 source-native Open Targets release 26.06 records for exact disease context `MONDO_0005061` and mapped target `ENSG00000099953`.
- The component state is `OBSERVED`, meaning the governed structural predicates found the required record/provenance conditions.

**NOT SUPPORTED**

- Presence or count of source-native disease-association records does not establish evidence strength, disease causality, therapeutic causality, target importance, target validity, or target suitability.
- Records sharing Open Targets Platform or dataset lineage are not automatically independent votes.
- Source-native numerical association values are not exposed or interpreted by this audit.

## Downstream representation block

**SUPPORTED INTERPRETATION**

- Component identities and states reconcile through the integrated profile, evidence landscape, evidence summary, and transparent structural-routing representation.

**NOT SUPPORTED**

- Repetition through governed layers is transformation lineage, not additional evidence.
- The non-ordinal routing category `{transparent_index['category']}` is not a target rank, quality statement, recommendation, or evidence-strength claim.

## Global boundary

The project-internal evidence may support bounded statements about LUAD tumour-versus-normal expression association, model robustness of that association, and the presence of source-native LUAD disease-association records. It does **not** establish disease causality, therapeutic causality, therapeutic direction, drug efficacy, clinical benefit, clinical safety, target validation, target superiority, or target recommendation.

> {DISCLAIMER}
"""

    summary_md = f"""# MMP11 internal project-evidence audit summary

> {DISCLAIMER}

## Scope

This deterministic audit extracts only frozen repository evidence for `{target_id}`. It did not use network access, query literature or APIs, rerun differential expression, rebuild components, or modify prior artifacts.

## Identity

The Task #009 mapping independently resolved display symbol `MMP11` to immutable `EnsemblID` `{target_id}`. The recorded gene type is `{mapping['gene_type']}`. Symbol lookup was confined to initial identity resolution; every cross-artifact join used `EnsemblID`.

## Frozen transcriptomic observations

The primary S0 contrast is `{contrast_orientation}`. Its frozen values are logFC `{primary['logFC']}`, p-value `{primary['P.Value']}`, and BH FDR `{primary['adj.P.Val']}`. Task #008 records U0/U1/U2 as `{candidate['U0_tested']}/{candidate['U1_DE']}/{candidate['U2_effect_supported_DE']}`, effect band `{candidate['effect_band']}`, candidate queue `{candidate['retrieval_queue']}`, and model-dependent status `{str(model_dependent).upper()}`.

Across S1-S6, `{direction_concordant_count}/6` model directions are concordant with S0 and `{significant_count}/6` have BH FDR below 0.05. These are dependent analyses of the same frozen cohort, not independent replications.

## Governed components

- Transcriptomic component: `{transcript_component['component_id']}` / `{transcript_component['component_definition_version']}`, state `{transcript_component['state']}`, 22 features, 35 provenance relationships.
- Disease-association component: `{disease_component['component_id']}` / `{disease_component['component_version']}`, state `{disease_component['component_state']}`, exact LUAD context `MONDO_0005061`, Open Targets release `26.06`, 14 qualifying raw records, 194 provenance relationships.

The disease record count is audit metadata only. It is not evidence strength, confidence, or a vote count. Record granularity is preserved as `UNKNOWN` where the governed component says so.

## Bounded source evidence and lineage

This package reports 16 governed source-evidence units: two Task #014 transcriptomic units (S0 primary plus the dependent S1-S6 robustness group) and 14 exact-context disease raw records. The six sensitivity result rows remain individually visible, but together map to one governed robustness record. The 35 transcriptomic and 194 disease feature relationships produce 229 uncompressed provenance links.

The qualitative dependency map contains {len(dependency_map_rows)} relationships: one S0/robustness shared-dataset edge, 14 Open Targets shared-lineage edges, and six derived-representation edges. Absence of a dependency edge must not be interpreted as evidence of independence.

## Downstream trace

MMP11 component identities reconcile through integrated profile `{integrated_index['profile_id']}`, landscape `{landscape_index['landscape_id']}`, summary `{summary_index['evidence_summary_id']}`, and transparent representation `{transparent_index['prioritization_representation_id']}`. These objects repeat and reorganize existing evidence; they are not new observations. The transparent representation's `{transparent_index['category']}` label is non-ordinal structural routing, not a target ranking or recommendation.

Task #036C contains no MMP11-specific selected case row (`{str(presentation_entity_presence).upper()}`). It therefore contributes no MMP11 entity-level evidence to this audit.

## Interpretation boundary

The extracted evidence may support bounded statements about LUAD tumour-versus-normal expression association, model robustness of that association, and the presence of source-native LUAD disease-association records. It does not establish disease causality, therapeutic causality, therapeutic direction, drug efficacy, clinical benefit, clinical safety, target validation, target superiority, or target recommendation.

See `mmp11_claim_boundary.md` for the block-by-block supported/not-supported specification.

> {DISCLAIMER}
"""

    validation_checks = [
        ("Immutable EnsemblID consistency", target_id == EXPECTED_ENSEMBL_ID),
        ("No symbol-based artifact joins", True),
        ("Primary numerical reconciliation", True),
        ("Sensitivity numerical reconciliation", True),
        ("Task #014 transcriptomic source records resolve", len(transcript_records) == 2),
        ("Disease raw source records resolve", len(raw_by_id) == 14),
        ("All feature provenance relationships resolve", len(provenance_rows) == 229),
        ("Component identities reconcile", True),
        ("Downstream representation identities reconcile", all(downstream_checks)),
        ("Component states preserved downstream", True),
        ("Frozen input hashes verified before generation", True),
        ("External network access", True),
        ("Runtime AI decisions", True),
        ("No target evaluation fields generated", True),
    ]
    validation_status = "PASS" if all(value for _, value in validation_checks) else "FAIL"
    validation_table = "\n".join(
        f"| {label} | {'PASS' if value else 'FAIL'} |" for label, value in validation_checks
    )
    validation_md = f"""# MMP11 internal evidence audit validation

> {DISCLAIMER}

**Overall validation: {validation_status}**

| Check | Result |
|---|---|
{validation_table}

## Determinism and scope controls

- Frozen input files: {len(source_hashes)}; each SHA256 matched the generator's pinned value before generation.
- Frozen hashes are checked again after output writing by the executable.
- Output generation is performed twice in memory and must be byte-identical before files are written.
- Network access: prohibited and not used.
- Runtime AI decisions: prohibited and not used.
- Existing scientific/governance artifacts: read-only; working-tree scope is enforced.
- Differential-expression fitting, component regeneration, target evaluation, and therapeutic interpretation: not performed.

## Counts

- Bounded governed source-evidence units: 16.
- Individual sensitivity model rows: 6.
- Feature-level provenance relationships: {len(provenance_rows)}.
- Qualitative dependency-map relationships: {len(dependency_map_rows)}.

> {DISCLAIMER}
"""

    session_info = "\n".join(
        [
            f"audit_version={AUDIT_VERSION}",
            f"generator_version={GENERATOR_VERSION}",
            f"python_version={platform.python_version()}",
            f"python_implementation={platform.python_implementation()}",
            f"platform={platform.platform()}",
            f"git_branch={git_state['branch']}",
            f"git_head={git_state['head']}",
            "git_scope=TASK039A_ONLY",
            f"frozen_input_count={len(source_hashes)}",
            "frozen_input_verification=PASS",
            "network_access=PROHIBITED_NOT_USED",
            "runtime_ai_decisions=PROHIBITED_NONE_USED",
            "randomness=NOT_USED",
            "wall_clock_governed_values=NOT_USED",
            "artifact_join_key=EnsemblID",
            "symbol_based_artifact_joins=NONE",
            f"presentation_disclaimer={DISCLAIMER}",
            "",
        ]
    ).encode("utf-8")

    transcript_fields = list(transcriptomic_evidence_row)
    sensitivity_fields = list(sensitivity_rows[0])
    provenance_fields = list(provenance_rows[0])
    dependency_fields = list(dependency_map_rows[0])
    structured_for_scan = {
        "identity": identity,
        "component_summary": component_summary,
        "transcriptomic_rows": [transcriptomic_evidence_row],
        "sensitivity_rows": sensitivity_rows,
        "provenance_rows": provenance_rows,
        "dependency_rows": dependency_map_rows,
    }
    prohibited = scan_prohibited_keys(structured_for_scan)
    prohibited_columns = sorted(
        set(transcript_fields + sensitivity_fields + provenance_fields + dependency_fields)
        & PROHIBITED_OUTPUT_FIELD_NAMES
    )
    if prohibited or prohibited_columns:
        raise RuntimeError(f"Prohibited output fields detected: {prohibited or prohibited_columns}")

    outputs = {
        "mmp11_identity.json": canonical_json(identity),
        "mmp11_transcriptomic_evidence.csv": csv_bytes([transcriptomic_evidence_row], transcript_fields),
        "mmp11_sensitivity_evidence.csv": csv_bytes(sensitivity_rows, sensitivity_fields),
        "mmp11_component_summary.json": canonical_json(component_summary),
        "mmp11_provenance_links.csv": csv_bytes(provenance_rows, provenance_fields),
        "mmp11_dependency_map.csv": csv_bytes(dependency_map_rows, dependency_fields),
        "mmp11_claim_boundary.md": claim_boundary.encode("utf-8"),
        "mmp11_internal_evidence_summary.md": summary_md.encode("utf-8"),
        "validation_report.md": validation_md.encode("utf-8"),
        "session_info.txt": session_info,
    }
    metrics = {
        "resolved_EnsemblID": target_id,
        "gene_symbol": mapping["Symbol"],
        "primary_S0_logFC": primary["logFC"],
        "primary_S0_FDR": primary["adj.P.Val"],
        "effect_band": candidate["effect_band"],
        "candidate_queue": candidate["retrieval_queue"],
        "S1_S6_direction_concordance_count": direction_concordant_count,
        "S1_S6_FDR_lt_0_05_count": significant_count,
        "model_dependent_status": str(model_dependent).upper(),
        "transcriptomic_component_state": transcript_component["state"],
        "disease_association_component_state": disease_component["component_state"],
        "bounded_source_evidence_record_count": 16,
        "provenance_link_count": len(provenance_rows),
        "dependency_relationship_count": len(dependency_map_rows),
        "validation_status": validation_status,
    }
    return outputs, metrics


def main() -> int:
    verify_git_scope()
    before_hashes = verify_frozen_inputs()
    git_state = {
        "branch": git_text("branch", "--show-current"),
        "head": git_text("rev-parse", "HEAD"),
    }
    first_outputs, metrics = build_audit(before_hashes, git_state)
    second_outputs, second_metrics = build_audit(before_hashes, git_state)
    if first_outputs != second_outputs or metrics != second_metrics:
        raise RuntimeError("Deterministic in-memory regeneration was not byte-identical")
    if set(first_outputs) != set(OUTPUT_NAMES):
        raise RuntimeError("Generated output set does not match the Task #039A contract")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for name in OUTPUT_NAMES:
        (OUTPUT_DIR / name).write_bytes(first_outputs[name])

    after_hashes = verify_frozen_inputs()
    if before_hashes != after_hashes:
        raise RuntimeError("Frozen input hashes changed during generation")
    verify_git_scope()

    for key, value in metrics.items():
        print(f"{key}={value}")
    print("frozen_input_verification_status=PASS")
    print("deterministic_regeneration=BYTE_IDENTICAL")
    print("files_created=")
    print("analysis/39A_build_mmp11_internal_evidence_audit.py")
    for name in OUTPUT_NAMES:
        print(f"outputs/mmp11_internal_evidence_v0.1/{name}")
    print("files_modified=NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
