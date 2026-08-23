#!/usr/bin/env python3
"""Generate deterministic presentation artifacts from frozen governed outputs.

Task #036C communicates the existing evidence architecture, structural layer
counts, provenance flow, and representative case-pattern identities. It does
not retrieve or generate evidence, evaluate targets, add gene symbols, produce
scores or rankings, recommend targets, interpret biology, or use runtime AI.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import platform
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs/presentation_artifacts_v0.1"
MANIFEST_PATH = OUTPUT_DIR / "presentation_manifest.json"
ARCHITECTURE_PATH = OUTPUT_DIR / "architecture_summary.md"
EVIDENCE_LAYER_PATH = OUTPUT_DIR / "evidence_layer_summary.csv"
CASE_PATTERN_PATH = OUTPUT_DIR / "case_pattern_summary.csv"
PROVENANCE_FLOW_PATH = OUTPUT_DIR / "provenance_flow_summary.md"
VALIDATION_PATH = OUTPUT_DIR / "validation_report.md"
SESSION_PATH = OUTPUT_DIR / "session_info.txt"

LANDSCAPE_DIR = ROOT / "outputs/evidence_landscape_v0.2"
SUMMARY_DIR = ROOT / "outputs/evidence_summary_v0.1"
PRIORITIZATION_DIR = ROOT / "outputs/prioritization_v0.1"
DOSSIER_DIR = ROOT / "outputs/case_dossiers_v0.1"

TASK_ID = "TASK_036C"
GENERATOR_VERSION = "SCIENTIFIC_PRESENTATION_ARTIFACT_GENERATOR_V0.1"
PRESENTATION_VERSION = "SCIENTIFIC_PRESENTATION_ARTIFACTS_V0.1"
EXPECTED_ENTITIES = 29_606
EXPECTED_COMPONENTS_PER_ENTITY = 2
EXPECTED_CASE_SLOTS = 4

PROHIBITED_FIELDS = {
    "best_target",
    "top_target",
    "rank",
    "ranking",
    "score",
    "priority_score",
    "recommendation",
    "target_quality",
    "evidence_strength",
    "clinical_value",
    "drug_candidate",
}

FROZEN_INPUT_SHA256 = {
    "outputs/evidence_landscape_v0.2/landscape_manifest.json": "2c3853becd3895b0aaffb12be95205d910d1507dc1f2f8f36f7f150f651dba29",
    "outputs/evidence_landscape_v0.2/landscape_index.csv": "fbd7a3b50e70c41aa2ddbf0361390fde23d12bc320a881a4da168ad1d145d6c8",
    "outputs/evidence_landscape_v0.2/partition_manifest.csv": "2ccc38a384fe816d50b2c5d8f4c528a49727189434fe4be41e70355ff146cf8d",
    "outputs/evidence_landscape_v0.2/validation_report.md": "d5933862fe468ef4561188716abaee2de1cda16e06bcb1d39c1793f66cc29a8a",
    "outputs/evidence_landscape_v0.2/session_info.txt": "bb928646c3c7c3aba85f9faa127b4eb93b50455fa24165aa6b1a048bf1c658de",
    "outputs/evidence_summary_v0.1/summary_manifest.json": "02b9a893569bd01257cb0108121f61a78041e90ffd769ac7a1d163d24051e19f",
    "outputs/evidence_summary_v0.1/summary_index.csv": "27489b08061102c4d325bac7d4761682f8c7e811458b5cff88d4fec3b0bc17e5",
    "outputs/evidence_summary_v0.1/partition_manifest.csv": "fd9bd76ea5f940a0165a6a082538a810fc64cbcd8b0fe4ecda9f0aae14795202",
    "outputs/evidence_summary_v0.1/validation_report.md": "257662af9adf87ce7f913e2024b6e43db2685cc84a117f9424830b6308c034e8",
    "outputs/evidence_summary_v0.1/session_info.txt": "bd04e5a858f2c70e746954d2e99bdfd44e3d64f818261d31c393f20bed9bda44",
    "outputs/prioritization_v0.1/prioritization_manifest.json": "773eeec6bfa769c932f354bcc5eb552fe4a540a2fe65dd1811720b2e80c4ff80",
    "outputs/prioritization_v0.1/prioritization_index.csv": "8131fa2644dab0efb17c5ae42cb5d297ec3993aa69ba00dda4ec6bdb47c7a69a",
    "outputs/prioritization_v0.1/partition_manifest.csv": "e59a54e4a4857927eab529aab28c82ba8874e7b2cebfa2064527b89c642a5f14",
    "outputs/prioritization_v0.1/validation_report.md": "8fd3664d6ce8ffe9b5c7bfc87793ca0492d23b97be8f4b8ac6abd2f37eead1d0",
    "outputs/prioritization_v0.1/session_info.txt": "9107a208ad059f62b18f915d80879ea9fce9f877f839440fbf7dc145c0724e57",
    "analysis/36B_generate_case_dossiers.py": "5b8d0c30f2f660faa069db4eb48716f03ca1e1681fe33e02f5f81ca95450e6f6",
    "outputs/case_dossiers_v0.1/dossier_manifest.json": "9039d3523bf52841239dce9ab880a98a3e2dcd5dfff3a87cece10c986067678b",
    "outputs/case_dossiers_v0.1/case_selection_index.csv": "f11892cc59d1fc3b042e79b4859e293677d9befbe975dd9d6635e0033011bc52",
    "outputs/case_dossiers_v0.1/case_dossiers.json": "d861e2500797ae9351f70e474c8a8acafa51d30481357aa450d1d77314bd27b8",
    "outputs/case_dossiers_v0.1/validation_report.md": "8ca6bc43b72fd653924b75eb9c5429e90cc82477908a1d17877bd7f5776fbbc3",
    "outputs/case_dossiers_v0.1/session_info.txt": "0cae68b33106ff97512e39ade11059701dfa8dfc847eb5db47bd7b04c3e0572f",
}

INDEX_SPECS = {
    "landscape": {
        "path": LANDSCAPE_DIR / "landscape_index.csv",
        "id_field": "landscape_id",
        "content_hash_field": "landscape_content_sha256",
    },
    "summary": {
        "path": SUMMARY_DIR / "summary_index.csv",
        "id_field": "evidence_summary_id",
        "content_hash_field": "summary_content_sha256",
    },
    "prioritization": {
        "path": PRIORITIZATION_DIR / "prioritization_index.csv",
        "id_field": "prioritization_representation_id",
        "content_hash_field": "representation_content_sha256",
    },
}

EVIDENCE_LAYER_COLUMNS = [
    "layer_ordinal",
    "layer_id",
    "artifact_identity",
    "version",
    "entity_count",
    "purpose_code",
    "provenance_reference",
    "provenance_sha256",
]

CASE_PATTERN_COLUMNS = [
    "case_category",
    "selection_status",
    "eligible_pool_count",
    "selected_EnsemblID",
    "canonical_universe_ordinal",
    "case_selection_id",
    "case_rule_id",
    "predicate_id",
    "structural_reason_code",
    "selection_method_id",
    "selection_token_sha256",
    "source_prioritization_representation_id",
    "source_evidence_summary_id",
]

ALLOWED_WORKTREE_PATHS = {
    "analysis/36C_generate_presentation_artifacts.py",
    *(f"outputs/presentation_artifacts_v0.1/{name}" for name in (
        "presentation_manifest.json",
        "architecture_summary.md",
        "evidence_layer_summary.csv",
        "case_pattern_summary.csv",
        "provenance_flow_summary.md",
        "validation_report.md",
        "session_info.txt",
    )),
}


def fail(message: str) -> None:
    raise RuntimeError(message)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def pretty_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("utf-8")


def stable_id(prefix: str, value: Any, length: int = 32) -> str:
    digest = sha256_bytes(canonical_json(value).encode("utf-8"))
    return f"{prefix}_{digest[:length].upper()}"


def csv_bytes(fieldnames: list[str], rows: list[dict[str, Any]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def validate_working_tree_scope() -> None:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    unexpected: list[str] = []
    for raw_line in result.stdout.splitlines():
        if not raw_line:
            continue
        path_text = raw_line[3:]
        if " -> " in path_text:
            path_text = path_text.split(" -> ", 1)[1]
        if path_text not in ALLOWED_WORKTREE_PATHS:
            unexpected.append(raw_line)
    if unexpected:
        fail("Unexpected working-tree changes:\n" + "\n".join(unexpected))


def validate_output_scope() -> None:
    allowed = {
        MANIFEST_PATH,
        ARCHITECTURE_PATH,
        EVIDENCE_LAYER_PATH,
        CASE_PATTERN_PATH,
        PROVENANCE_FLOW_PATH,
        VALIDATION_PATH,
        SESSION_PATH,
    }
    if OUTPUT_DIR.exists():
        unexpected = sorted(
            path.relative_to(ROOT).as_posix()
            for path in OUTPUT_DIR.rglob("*")
            if path.is_file() and path not in allowed
        )
        if unexpected:
            fail("Unexpected Task #036C output files: " + ", ".join(unexpected))


def validate_frozen_inputs() -> dict[str, str]:
    observed: dict[str, str] = {}
    for relative_path, expected_hash in FROZEN_INPUT_SHA256.items():
        path = ROOT / relative_path
        if not path.is_file():
            fail(f"Frozen input missing: {relative_path}")
        actual_hash = sha256_file(path)
        if actual_hash != expected_hash:
            fail(
                f"Frozen input hash mismatch: {relative_path}; "
                f"expected {expected_hash}, observed {actual_hash}"
            )
        observed[relative_path] = actual_hash
    return observed


def assert_no_prohibited_fields(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        forbidden = PROHIBITED_FIELDS.intersection(value)
        if forbidden:
            fail(f"Prohibited structured field(s) at {path}: {sorted(forbidden)}")
        for key, child in value.items():
            assert_no_prohibited_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            assert_no_prohibited_fields(child, f"{path}[{index}]")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        fail(f"Expected JSON object: {path}")
    return value


def load_and_validate_manifests() -> dict[str, dict[str, Any]]:
    manifests = {
        "landscape": load_json(LANDSCAPE_DIR / "landscape_manifest.json"),
        "summary": load_json(SUMMARY_DIR / "summary_manifest.json"),
        "prioritization": load_json(PRIORITIZATION_DIR / "prioritization_manifest.json"),
        "dossier": load_json(DOSSIER_DIR / "dossier_manifest.json"),
    }
    for name, manifest in manifests.items():
        if manifest.get("validation_status") != "PASS":
            fail(f"Frozen {name} manifest is not validated")

    landscape = manifests["landscape"]
    summary = manifests["summary"]
    prioritization = manifests["prioritization"]
    dossier = manifests["dossier"]
    if landscape.get("counts", {}).get("landscapes") != EXPECTED_ENTITIES:
        fail("Landscape entity count changed")
    if summary.get("counts", {}).get("summaries") != EXPECTED_ENTITIES:
        fail("Evidence Summary entity count changed")
    if prioritization.get("counts", {}).get("representations") != EXPECTED_ENTITIES:
        fail("Prioritization representation count changed")
    if dossier.get("counts", {}).get("case_slots") != EXPECTED_CASE_SLOTS:
        fail("Case dossier slot count changed")
    if landscape.get("component_order") != [
        "COMP_TRANSCRIPTOMIC_EVIDENCE",
        "COMP_DISEASE_ASSOCIATION",
    ]:
        fail("Frozen landscape component order changed")
    if landscape.get("component_versions") != summary.get("component_versions"):
        fail("Component versions changed between landscape and summary")
    if summary.get("source_landscape", {}).get("manifest_sha256") != FROZEN_INPUT_SHA256[
        "outputs/evidence_landscape_v0.2/landscape_manifest.json"
    ]:
        fail("Evidence Summary no longer references the frozen landscape manifest")
    if dossier.get("source", {}).get("prioritization_release_id") != prioritization.get("release_id"):
        fail("Case dossier source release does not match prioritization release")
    return manifests


def load_case_records() -> tuple[list[dict[str, str]], dict[str, Any]]:
    with (DOSSIER_DIR / "case_selection_index.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != EXPECTED_CASE_SLOTS:
        fail(f"Expected {EXPECTED_CASE_SLOTS} case index rows, observed {len(rows)}")
    release = load_json(DOSSIER_DIR / "case_dossiers.json")
    slots = release.get("case_slots")
    if not isinstance(slots, list) or len(slots) != EXPECTED_CASE_SLOTS:
        fail("Case dossier release slot structure changed")
    if [row["case_category"] for row in rows] != [slot.get("case_category") for slot in slots]:
        fail("Case index and dossier category order differ")
    for row, slot in zip(rows, slots, strict=True):
        if row["selection_status"] != slot.get("selection_status"):
            fail(f"Case selection status mismatch: {row['case_category']}")
        dossier = slot.get("dossier")
        if row["selection_status"] == "FILLED":
            if not isinstance(dossier, dict):
                fail(f"Filled case has no dossier: {row['case_category']}")
            if (
                dossier.get("EnsemblID") != row["EnsemblID"]
                or str(dossier.get("universe_ordinal")) != row["universe_ordinal"]
                or dossier.get("case_selection_id") != row["case_selection_id"]
                or dossier.get("case_selection", {}).get("case_category") != row["case_category"]
                or dossier.get("case_selection", {}).get("case_rule_id") != row["case_rule_id"]
                or dossier.get("case_selection", {}).get("structural_reason", {}).get("reason_code")
                != row["structural_reason_code"]
                or dossier.get("case_selection", {}).get("selection_method_id")
                != row["selection_method_id"]
                or dossier.get("case_selection", {}).get("selection_token_sha256")
                != row["selection_token_sha256"]
            ):
                fail(f"Case dossier/index identity mismatch: {row['case_category']}")
        elif dossier is not None:
            fail(f"Unfilled case unexpectedly contains a dossier: {row['case_category']}")
    assert_no_prohibited_fields(release)
    return rows, release


def selected_index_records(
    case_rows: list[dict[str, str]],
) -> dict[str, dict[str, dict[str, str]]]:
    selected_ids = {row["EnsemblID"] for row in case_rows if row["selection_status"] == "FILLED"}
    results: dict[str, dict[str, dict[str, str]]] = {}
    expected_order: list[str] | None = None
    for layer_name, spec in INDEX_SPECS.items():
        found: dict[str, dict[str, str]] = {}
        order: list[str] = []
        seen: set[str] = set()
        with spec["path"].open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            required = {
                "universe_ordinal", "EnsemblID", spec["id_field"], spec["content_hash_field"],
                "transcriptomic_component_version", "transcriptomic_component_state",
                "disease_association_component_version", "disease_association_component_state",
            }
            if reader.fieldnames is None or not required.issubset(reader.fieldnames):
                fail(f"Frozen {layer_name} index lacks required structural columns")
            for ordinal, row in enumerate(reader, 1):
                if int(row["universe_ordinal"]) != ordinal:
                    fail(f"{layer_name} canonical ordering changed at ordinal {ordinal}")
                entity_id = row["EnsemblID"]
                if entity_id in seen:
                    fail(f"Duplicate {layer_name} EnsemblID: {entity_id}")
                seen.add(entity_id)
                order.append(entity_id)
                if entity_id in selected_ids:
                    found[entity_id] = row
        if len(order) != EXPECTED_ENTITIES:
            fail(f"Expected {EXPECTED_ENTITIES} {layer_name} rows, observed {len(order)}")
        if expected_order is None:
            expected_order = order
        elif order != expected_order:
            fail(f"Canonical universe order changed at {layer_name}")
        if set(found) != selected_ids:
            fail(f"Not all selected dossier entities were found in {layer_name}")
        results[layer_name] = found
    return results


def reconcile_case_lineage(
    case_rows: list[dict[str, str]], selected: dict[str, dict[str, dict[str, str]]]
) -> None:
    for case in case_rows:
        if case["selection_status"] != "FILLED":
            continue
        entity_id = case["EnsemblID"]
        landscape = selected["landscape"][entity_id]
        summary = selected["summary"][entity_id]
        prioritization = selected["prioritization"][entity_id]
        if not (
            case["universe_ordinal"]
            == landscape["universe_ordinal"]
            == summary["universe_ordinal"]
            == prioritization["universe_ordinal"]
        ):
            fail(f"Universe ordinal lineage mismatch: {entity_id}")
        if summary["source_landscape_id"] != landscape["landscape_id"]:
            fail(f"Landscape-to-summary identity mismatch: {entity_id}")
        if summary["source_landscape_content_sha256"] != landscape["landscape_content_sha256"]:
            fail(f"Landscape-to-summary content hash mismatch: {entity_id}")
        if prioritization["source_evidence_summary_id"] != summary["evidence_summary_id"]:
            fail(f"Summary-to-prioritization identity mismatch: {entity_id}")
        if prioritization["source_summary_content_sha256"] != summary["summary_content_sha256"]:
            fail(f"Summary-to-prioritization content hash mismatch: {entity_id}")
        if case["source_prioritization_representation_id"] != prioritization["prioritization_representation_id"]:
            fail(f"Prioritization-to-dossier identity mismatch: {entity_id}")
        if case["source_prioritization_content_sha256"] != prioritization["representation_content_sha256"]:
            fail(f"Prioritization-to-dossier content hash mismatch: {entity_id}")
        if case["source_evidence_summary_id"] != summary["evidence_summary_id"]:
            fail(f"Dossier-to-summary identity mismatch: {entity_id}")
        for prefix in ("transcriptomic", "disease_association"):
            version_field = f"{prefix}_component_version"
            state_field = f"{prefix}_component_state"
            if not (
                case[version_field]
                == landscape[version_field]
                == summary[version_field]
                == prioritization[version_field]
            ):
                fail(f"Component version lineage mismatch: {entity_id}/{prefix}")
            if not (
                case[state_field]
                == landscape[state_field]
                == summary[state_field]
                == prioritization[state_field]
            ):
                fail(f"Component state lineage mismatch: {entity_id}/{prefix}")


def build_evidence_layer_rows(manifests: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    landscape = manifests["landscape"]
    summary = manifests["summary"]
    prioritization = manifests["prioritization"]
    dossier = manifests["dossier"]
    component_versions = landscape["component_versions"]
    source_profile = landscape["source_profile"]
    rows = [
        {
            "layer_ordinal": 1,
            "layer_id": "LAYER_COMPONENT_TRANSCRIPTOMIC",
            "artifact_identity": "COMP_TRANSCRIPTOMIC_EVIDENCE",
            "version": component_versions["COMP_TRANSCRIPTOMIC_EVIDENCE"],
            "entity_count": EXPECTED_ENTITIES,
            "purpose_code": "STRUCTURAL_TRANSCRIPTOMIC_OBSERVATION_COMPONENT",
            "provenance_reference": "outputs/feature_extraction/extraction_manifest.json",
            "provenance_sha256": landscape["frozen_inputs"]["outputs/feature_extraction/extraction_manifest.json"],
        },
        {
            "layer_ordinal": 2,
            "layer_id": "LAYER_COMPONENT_DISEASE_ASSOCIATION",
            "artifact_identity": "COMP_DISEASE_ASSOCIATION",
            "version": component_versions["COMP_DISEASE_ASSOCIATION"],
            "entity_count": EXPECTED_ENTITIES,
            "purpose_code": "STRUCTURAL_DISEASE_ASSOCIATION_OBSERVATION_COMPONENT",
            "provenance_reference": "outputs/disease_association_component_v0.1/component_manifest.json",
            "provenance_sha256": landscape["frozen_inputs"]["outputs/disease_association_component_v0.1/component_manifest.json"],
        },
        {
            "layer_ordinal": 3,
            "layer_id": "LAYER_MULTI_COMPONENT_LANDSCAPE",
            "artifact_identity": landscape["release_id"],
            "version": f"{landscape['landscape_schema_version']}|{landscape['landscape_version']}",
            "entity_count": landscape["counts"]["landscapes"],
            "purpose_code": "STRUCTURAL_COMPONENT_COMPOSITION_AND_LINEAGE_PROJECTION",
            "provenance_reference": source_profile["integration_release_id"],
            "provenance_sha256": source_profile["profile_payload_sha256"],
        },
        {
            "layer_ordinal": 4,
            "layer_id": "LAYER_EVIDENCE_SUMMARY",
            "artifact_identity": summary["release_id"],
            "version": f"{summary['evidence_summary_schema_version']}|{summary['evidence_summary_version']}",
            "entity_count": summary["counts"]["summaries"],
            "purpose_code": "STRUCTURAL_EVIDENCE_SUMMARY_PROJECTION",
            "provenance_reference": landscape["release_id"],
            "provenance_sha256": FROZEN_INPUT_SHA256["outputs/evidence_landscape_v0.2/landscape_manifest.json"],
        },
        {
            "layer_ordinal": 5,
            "layer_id": "LAYER_TRANSPARENT_ROUTING_REPRESENTATION",
            "artifact_identity": prioritization["release_id"],
            "version": f"{prioritization['prioritization_output_schema_version']}|{prioritization['prioritization_representation_version']}",
            "entity_count": prioritization["counts"]["representations"],
            "purpose_code": "DETERMINISTIC_NON_ORDINAL_STRUCTURAL_ROUTING",
            "provenance_reference": summary["release_id"],
            "provenance_sha256": FROZEN_INPUT_SHA256["outputs/evidence_summary_v0.1/summary_manifest.json"],
        },
        {
            "layer_ordinal": 6,
            "layer_id": "LAYER_REPRESENTATIVE_CASE_DOSSIER",
            "artifact_identity": dossier["release_id"],
            "version": dossier["dossier_release_version"],
            "entity_count": dossier["counts"]["filled_case_slots"],
            "purpose_code": "PRESENTATION_CASE_PATTERN_MATERIALIZATION",
            "provenance_reference": prioritization["release_id"],
            "provenance_sha256": FROZEN_INPUT_SHA256["outputs/prioritization_v0.1/prioritization_manifest.json"],
        },
    ]
    return rows


def build_case_pattern_rows(case_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    return [
        {
            "case_category": row["case_category"],
            "selection_status": row["selection_status"],
            "eligible_pool_count": row["eligible_pool_count"],
            "selected_EnsemblID": row["EnsemblID"],
            "canonical_universe_ordinal": row["universe_ordinal"],
            "case_selection_id": row["case_selection_id"],
            "case_rule_id": row["case_rule_id"],
            "predicate_id": row["predicate_id"],
            "structural_reason_code": row["structural_reason_code"],
            "selection_method_id": row["selection_method_id"],
            "selection_token_sha256": row["selection_token_sha256"],
            "source_prioritization_representation_id": row["source_prioritization_representation_id"],
            "source_evidence_summary_id": row["source_evidence_summary_id"],
        }
        for row in case_rows
    ]


def build_architecture_summary(manifests: dict[str, dict[str, Any]]) -> bytes:
    landscape = manifests["landscape"]
    summary = manifests["summary"]
    prioritization = manifests["prioritization"]
    dossier = manifests["dossier"]
    transcript_states = landscape["component_state_counts"]["COMP_TRANSCRIPTOMIC_EVIDENCE"]
    disease_states = landscape["component_state_counts"]["COMP_DISEASE_ASSOCIATION"]
    text = f"""# Governed Evidence Architecture Summary v0.1

## Communication scope

This document describes frozen structural representations. It adds no evidence and makes no target-level biological or therapeutic claim. All identities below are immutable governed identifiers; gene symbols are not used.

## Evidence components

The {EXPECTED_ENTITIES:,}-entity universe contains exactly two distinct component slots per entity:

| Component | Version | Recorded structural states |
|---|---|---|
| `COMP_TRANSCRIPTOMIC_EVIDENCE` | `{landscape['component_versions']['COMP_TRANSCRIPTOMIC_EVIDENCE']}` | `OBSERVED={transcript_states.get('OBSERVED', 0)}`; `CONFLICTING={transcript_states.get('CONFLICTING', 0)}` |
| `COMP_DISEASE_ASSOCIATION` | `{landscape['component_versions']['COMP_DISEASE_ASSOCIATION']}` | `OBSERVED={disease_states.get('OBSERVED', 0)}`; `PARTIAL={disease_states.get('PARTIAL', 0)}`; `MISSING={disease_states.get('MISSING', 0)}` |

Component states are structural conditions. They are preserved separately and are not combined into a global state.

## Representation layers

1. **Multi-component evidence landscape** — `{landscape['release_id']}` composes component, feature, provenance, dependency, missingness, and limitation references for {landscape['counts']['landscapes']:,} immutable EnsemblID entities.
2. **Evidence Summary** — `{summary['release_id']}` projects each landscape into one governed structural summary while retaining component states, missingness, dependency relationships, and limitations.
3. **Transparent routing representation** — `{prioritization['release_id']}` applies the frozen non-ordinal rule catalog to each of {prioritization['counts']['representations']:,} summaries and preserves a complete rule trace.
4. **Representative case dossiers** — `{dossier['release_id']}` contains {dossier['counts']['filled_case_slots']} filled structural presentation slots selected from complete eligible pools by category-salted SHA256 minimum tokens.

## Interpretation boundary

The architecture organizes evidence records and structural states for traceable communication. Layer counts, states, categories, and selected cases are not comparative measurements and do not establish target importance, efficacy, safety, clinical value, or therapeutic suitability.
"""
    return text.encode("utf-8")


def build_provenance_flow(manifests: dict[str, dict[str, Any]]) -> bytes:
    landscape = manifests["landscape"]
    summary = manifests["summary"]
    prioritization = manifests["prioritization"]
    dossier = manifests["dossier"]
    snapshot = landscape["source_profile"]["evidence_snapshot_version"]
    text = f"""# Provenance Flow Summary v0.1

## Required provenance backbone

```text
GOVERNED_SOURCE_RECORDS
  -> {snapshot}
  -> COMP_TRANSCRIPTOMIC_EVIDENCE_V0.1 + COMP_DISEASE_ASSOCIATION_V0.1
  -> {landscape['release_id']}
  -> {summary['release_id']}
  -> {dossier['release_id']}
```

This is the required `source -> snapshot -> component -> landscape -> summary -> dossier` communication path. `GOVERNED_SOURCE_RECORDS` is a structural origin label, not a new source artifact.

## Expanded governed routing path

```text
source record references
  -> frozen evidence snapshot
  -> separately represented evidence component records
  -> multi-component landscape
  -> evidence summary
  -> {prioritization['release_id']}
  -> representative case dossier
```

The transparent routing representation mediates the summary-to-dossier link. It preserves source summary identity, component states, limitations, fixed-order rule traces, and the assigned non-ordinal category. The dossier then preserves the source representation identity and deterministic selection token.

## Lineage preservation

- Landscape records retain feature, provenance, dependency, missingness, and limitation references.
- Evidence Summaries retain landscape identity and content hash references.
- Transparent routing representations retain Evidence Summary identity and content hash references.
- Case dossiers retain routing representation identity, Evidence Summary identity, component versions and states, limitations, rule traces, and selection tokens.
- This presentation layer cites those governed identities and hashes without copying or altering underlying evidence payloads.

## Boundary

The arrows record derivation and traceability only. They do not represent evidence strength, causal direction, biological importance, or therapeutic conclusions.
"""
    return text.encode("utf-8")


def build_validation_report(
    manifests: dict[str, dict[str, Any]], case_rows: list[dict[str, str]]
) -> bytes:
    filled = sum(row["selection_status"] == "FILLED" for row in case_rows)
    text = f"""# Task #036C Presentation Artifact Validation Report

**Validation status:** PASS

## Reconciliation

- PASS — all {len(FROZEN_INPUT_SHA256)} frozen input artifact hashes matched before and after generation
- PASS — landscape, summary, and routing indexes each contain {EXPECTED_ENTITIES:,} unique EnsemblID entities in identical canonical order
- PASS — two component versions and states reconcile across all selected case lineage paths
- PASS — all {filled} filled case dossiers reconcile to source routing representations, Evidence Summaries, and landscapes by identity and content hash
- PASS — case categories, structural reason codes, selection method IDs, and SHA256 tokens match Task #036B exactly
- PASS — all seven required Task #036C artifacts are present
- PASS — structured presentation objects contain no prohibited fields
- PASS — two complete in-memory generations are byte-identical
- PASS — written artifacts are byte-identical to the validated generated bytes

## Execution boundaries

- Network and API access: prohibited and not used
- Evidence retrieval or generation: not performed
- Literature or external knowledge: not used
- Gene symbols: not used
- Runtime AI/LLM decisions: prohibited and not used
- Target evaluation, ranking, scoring, recommendation, or biological/therapeutic interpretation: not performed

## Source releases

- Landscape: `{manifests['landscape']['release_id']}`
- Evidence Summary: `{manifests['summary']['release_id']}`
- Transparent routing representation: `{manifests['prioritization']['release_id']}`
- Representative case dossier: `{manifests['dossier']['release_id']}`
"""
    return text.encode("utf-8")


def build_session(manifests: dict[str, dict[str, Any]]) -> bytes:
    lines = [
        f"task={TASK_ID}",
        f"generator_version={GENERATOR_VERSION}",
        f"presentation_version={PRESENTATION_VERSION}",
        f"python_version={platform.python_version()}",
        f"python_implementation={platform.python_implementation()}",
        "standard_library_only=TRUE",
        "network_access=PROHIBITED_NOT_USED",
        "api_access=PROHIBITED_NOT_USED",
        "external_evidence_retrieval=NOT_PERFORMED",
        "literature_information=NOT_USED",
        "gene_symbols=NOT_USED",
        "runtime_ai_llm_decisions=PROHIBITED_NONE_USED",
        "randomness=NOT_USED",
        "wall_clock_governed_values=NOT_USED",
        "complete_in_memory_generations=2",
        "deterministic_regeneration=BYTE_IDENTICAL",
        f"landscape_release_id={manifests['landscape']['release_id']}",
        f"summary_release_id={manifests['summary']['release_id']}",
        f"prioritization_release_id={manifests['prioritization']['release_id']}",
        f"dossier_release_id={manifests['dossier']['release_id']}",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def build_artifact_bytes(
    manifests: dict[str, dict[str, Any]], case_rows: list[dict[str, str]],
    frozen_hashes: dict[str, str],
) -> dict[str, bytes]:
    evidence_rows = build_evidence_layer_rows(manifests)
    case_pattern_rows = build_case_pattern_rows(case_rows)
    assert_no_prohibited_fields(evidence_rows)
    assert_no_prohibited_fields(case_pattern_rows)
    artifacts = {
        "architecture_summary.md": build_architecture_summary(manifests),
        "evidence_layer_summary.csv": csv_bytes(EVIDENCE_LAYER_COLUMNS, evidence_rows),
        "case_pattern_summary.csv": csv_bytes(CASE_PATTERN_COLUMNS, case_pattern_rows),
        "provenance_flow_summary.md": build_provenance_flow(manifests),
        "validation_report.md": build_validation_report(manifests, case_rows),
        "session_info.txt": build_session(manifests),
    }
    artifact_inventory = {
        name: {"artifact_size": len(data), "sha256": sha256_bytes(data)}
        for name, data in sorted(artifacts.items())
    }
    manifest = {
        "task_id": TASK_ID,
        "presentation_release_id": stable_id(
            "PRESREL",
            [
                PRESENTATION_VERSION,
                manifests["landscape"]["release_id"],
                manifests["summary"]["release_id"],
                manifests["prioritization"]["release_id"],
                manifests["dossier"]["release_id"],
            ],
        ),
        "presentation_version": PRESENTATION_VERSION,
        "generator": {
            "relative_path": "analysis/36C_generate_presentation_artifacts.py",
            "generator_version": GENERATOR_VERSION,
            "sha256": sha256_file(ROOT / "analysis/36C_generate_presentation_artifacts.py"),
        },
        "source_releases": {
            "landscape_release_id": manifests["landscape"]["release_id"],
            "evidence_summary_release_id": manifests["summary"]["release_id"],
            "prioritization_release_id": manifests["prioritization"]["release_id"],
            "case_dossier_release_id": manifests["dossier"]["release_id"],
        },
        "counts": {
            "canonical_entities": EXPECTED_ENTITIES,
            "evidence_components": EXPECTED_COMPONENTS_PER_ENTITY,
            "evidence_layer_rows": len(evidence_rows),
            "case_pattern_rows": len(case_pattern_rows),
            "filled_case_patterns": sum(row["selection_status"] == "FILLED" for row in case_rows),
        },
        "artifacts": artifact_inventory,
        "frozen_inputs": frozen_hashes,
        "determinism": {
            "complete_in_memory_generations": 2,
            "byte_identical_second_generation": "PASS",
            "network_access": "PROHIBITED_NOT_USED",
            "runtime_ai_decisions": "PROHIBITED_NONE_USED",
            "randomness": "NOT_USED",
            "wall_clock_governed_values": "NOT_USED",
        },
        "validation": {
            "frozen_input_hashes_unchanged": "PASS",
            "case_dossier_identity_reconciliation": "PASS",
            "artifact_completeness": "PASS",
            "prohibited_field_scan": "PASS",
            "deterministic_regeneration": "BYTE_IDENTICAL",
        },
        "scope_boundary": "STRUCTURAL_SCIENTIFIC_COMMUNICATION_ONLY",
        "validation_status": "PASS",
    }
    assert_no_prohibited_fields(manifest)
    artifacts["presentation_manifest.json"] = pretty_json_bytes(manifest)
    return artifacts


def main() -> None:
    validate_working_tree_scope()
    validate_output_scope()
    frozen_before = validate_frozen_inputs()
    manifests = load_and_validate_manifests()
    case_rows, _ = load_case_records()
    selected = selected_index_records(case_rows)
    reconcile_case_lineage(case_rows, selected)

    first = build_artifact_bytes(manifests, case_rows, frozen_before)
    second = build_artifact_bytes(manifests, case_rows, frozen_before)
    if first != second:
        fail("Two complete presentation artifact generations are not byte-identical")
    expected_names = {
        "presentation_manifest.json",
        "architecture_summary.md",
        "evidence_layer_summary.csv",
        "case_pattern_summary.csv",
        "provenance_flow_summary.md",
        "validation_report.md",
        "session_info.txt",
    }
    if set(first) != expected_names:
        fail("Generated presentation artifact set is incomplete")
    if frozen_before != validate_frozen_inputs():
        fail("Frozen input hashes changed during generation")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for name in sorted(first):
        (OUTPUT_DIR / name).write_bytes(first[name])
    if any((OUTPUT_DIR / name).read_bytes() != data for name, data in first.items()):
        fail("Written presentation artifacts differ from validated generated bytes")
    if frozen_before != validate_frozen_inputs():
        fail("Frozen input hashes changed after writing Task #036C outputs")
    validate_working_tree_scope()

    print(f"presentation_artifacts={len(first)}")
    print(f"canonical_entities={EXPECTED_ENTITIES}")
    print(f"case_patterns={len(case_rows)}")
    print("deterministic_regeneration=BYTE_IDENTICAL")
    print("validation_status=PASS")


if __name__ == "__main__":
    main()
