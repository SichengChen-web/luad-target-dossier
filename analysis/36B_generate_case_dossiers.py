#!/usr/bin/env python3
"""Materialize deterministic representative structural case dossiers.

Task #036B evaluates the frozen Task #036A case-pattern predicates over every
frozen Task #035B prioritization representation.  It selects one representative
per eligible case category by the governed category-salted SHA256 minimum rule.
It performs no evidence retrieval, scoring, ranking, target optimization,
recommendation, biological interpretation, or runtime AI/LLM decision.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import platform
import subprocess
from collections import OrderedDict
from contextlib import AbstractContextManager
from copy import deepcopy
from pathlib import Path
from typing import Any, BinaryIO


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "outputs/prioritization_v0.1"
SOURCE_MANIFEST = SOURCE_DIR / "prioritization_manifest.json"
SOURCE_INDEX = SOURCE_DIR / "prioritization_index.csv"
SOURCE_PARTITIONS = SOURCE_DIR / "partition_manifest.csv"
SOURCE_EXTERNAL_ROOT = Path(
    "/private/tmp/luad-target-dossier-external-artifacts/prioritization_v0.1"
)
CASE_MODULE_PATH = ROOT / "analysis/36A_define_case_selection_schema.py"
CASE_SCHEMA_PATH = ROOT / "schemas/case_study_selection_schema_v0.1.json"

OUTPUT_DIR = ROOT / "outputs/case_dossiers_v0.1"
MANIFEST_PATH = OUTPUT_DIR / "dossier_manifest.json"
INDEX_PATH = OUTPUT_DIR / "case_selection_index.csv"
DOSSIERS_PATH = OUTPUT_DIR / "case_dossiers.json"
REPORT_PATH = OUTPUT_DIR / "validation_report.md"
SESSION_PATH = OUTPUT_DIR / "session_info.txt"

TASK_ID = "TASK_036B"
GENERATOR_VERSION = "REPRESENTATIVE_CASE_DOSSIER_GENERATOR_V0.1"
DOSSIER_RELEASE_VERSION = "REPRESENTATIVE_CASE_DOSSIER_RELEASE_V0.1"
EXPECTED_OBJECTS = 29_606
EXPECTED_PARTITIONS = 256
SOURCE_SCHEMA_VERSION = "PRIORITIZATION_OUTPUT_SCHEMA_V0.1"
SOURCE_REPRESENTATION_VERSION = "TRANSPARENT_PRIORITIZATION_PROTOTYPE_V0.1"
SOURCE_RULE_CATALOG_VERSION = "PRIORITIZATION_RULE_CATALOG_V0.1"
SOURCE_GENERATOR_VERSION = "TRANSPARENT_PRIORITIZATION_MATERIALIZER_V0.1"
SOURCE_PARTITION_STRATEGY = "ENSEMBL_SHA256_PREFIX_2_V0.1"

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
    "analysis/35B_materialize_prioritization.py": "7a651a3919b0a7c1e1a31bbea12e546039dc9117c053114807883f05491e66f5",
    "outputs/prioritization_v0.1/prioritization_manifest.json": "773eeec6bfa769c932f354bcc5eb552fe4a540a2fe65dd1811720b2e80c4ff80",
    "outputs/prioritization_v0.1/prioritization_index.csv": "8131fa2644dab0efb17c5ae42cb5d297ec3993aa69ba00dda4ec6bdb47c7a69a",
    "outputs/prioritization_v0.1/partition_manifest.csv": "e59a54e4a4857927eab529aab28c82ba8874e7b2cebfa2064527b89c642a5f14",
    "outputs/prioritization_v0.1/validation_report.md": "8fd3664d6ce8ffe9b5c7bfc87793ca0492d23b97be8f4b8ac6abd2f37eead1d0",
    "outputs/prioritization_v0.1/session_info.txt": "9107a208ad059f62b18f915d80879ea9fce9f877f839440fbf7dc145c0724e57",
    "analysis/36A_define_case_selection_schema.py": "eae4d7c5af3509462f8c3317a831db417c586a4c495e24c65f7815bf76eaba0e",
    "docs/governance/case_study_selection_framework_v0.1.md": "c269af2bfe9afd8f33fb1e2f107dc9e563f58ab6648ac66fca2816af2a8fd109",
    "docs/governance/case_study_selection_rule_catalog_v0.1.md": "a81289a329675206db25c5f3b79d8d2c870e95b32e147dc03e7dfc36cb3bf31a",
    "docs/governance/case_study_selection_validation_requirements_v0.1.md": "5ed8a2086135e712218e76d4ce556ae07e37c7ed049f8bf88feefab3a94290f9",
    "schemas/case_study_selection_schema_v0.1.json": "d76da88675e63fb13f9cb59ad1b1e2df5895c22d5862987c4dc6d7818acaeffa",
}

SOURCE_INDEX_COLUMNS = [
    "universe_ordinal", "EnsemblID", "prioritization_representation_id",
    "source_evidence_summary_id", "source_summary_content_sha256",
    "source_evidence_summary_schema_version", "source_evidence_summary_version",
    "transcriptomic_component_version", "transcriptomic_component_state",
    "disease_association_component_version", "disease_association_component_state",
    "category", "assigned_rule_id", "true_rule_count", "rule_trace_step_count",
    "limitation_identifiers", "partition_id", "payload_artifact_id",
    "record_offset_bytes", "record_length_bytes", "representation_content_sha256",
    "prioritization_output_schema_version", "prioritization_representation_version",
    "rule_catalog_version", "generator_version",
]

SOURCE_PARTITION_COLUMNS = [
    "partition_id", "partition_strategy_version", "partition_set_artifact_id",
    "artifact_id", "artifact_class", "artifact_role", "artifact_size", "sha256",
    "generator_version", "storage_reference_placeholder", "storage_status",
    "representation_count", "first_universe_ordinal", "last_universe_ordinal",
    "prioritization_output_schema_version", "prioritization_representation_version",
    "rule_catalog_version", "validation_status",
]

INDEX_COLUMNS = [
    "case_category", "selection_status", "eligible_pool_count", "case_rule_id",
    "predicate_id", "structural_reason_code", "selection_method_id",
    "selection_token_sha256", "case_selection_id", "universe_ordinal", "EnsemblID",
    "source_prioritization_representation_id", "source_prioritization_content_sha256",
    "source_evidence_summary_id", "source_evidence_summary_content_sha256",
    "source_category", "source_assigned_rule_id", "transcriptomic_component_id",
    "transcriptomic_component_version", "transcriptomic_component_state",
    "disease_association_component_id", "disease_association_component_version",
    "disease_association_component_state", "limitation_identifier_count",
]

ALLOWED_WORKTREE_PATHS = {
    "analysis/36B_generate_case_dossiers.py",
    *(f"outputs/case_dossiers_v0.1/{name}" for name in (
        "dossier_manifest.json", "case_selection_index.csv", "case_dossiers.json",
        "validation_report.md", "session_info.txt",
    )),
}


def fail(message: str) -> None:
    raise RuntimeError(message)


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        fail(f"Unable to load frozen module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def pretty_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_id(prefix: str, value: Any, length: int = 32) -> str:
    digest = sha256_bytes(canonical_json(value).encode("utf-8"))
    return f"{prefix}_{digest[:length].upper()}"


def csv_bytes(fieldnames: list[str], rows: list[dict[str, Any]]) -> bytes:
    import io

    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def assert_no_prohibited_fields(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        forbidden = PROHIBITED_FIELDS.intersection(value)
        if forbidden:
            fail(f"Prohibited dossier field(s) at {path}: {sorted(forbidden)}")
        for key, child in value.items():
            assert_no_prohibited_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            assert_no_prohibited_fields(child, f"{path}[{index}]")


def validate_working_tree_scope() -> None:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=ROOT, check=True, capture_output=True, text=True,
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
    allowed = {MANIFEST_PATH, INDEX_PATH, DOSSIERS_PATH, REPORT_PATH, SESSION_PATH}
    if OUTPUT_DIR.exists():
        unexpected = sorted(
            path.relative_to(ROOT).as_posix()
            for path in OUTPUT_DIR.rglob("*")
            if path.is_file() and path not in allowed
        )
        if unexpected:
            fail("Unexpected Task #036B output files: " + ", ".join(unexpected))


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


class LRUReadPool(AbstractContextManager["LRUReadPool"]):
    def __init__(self, paths: dict[str, Path], max_open: int = 32) -> None:
        self.paths = paths
        self.max_open = max_open
        self.handles: OrderedDict[str, BinaryIO] = OrderedDict()

    def reader(self, partition_id: str) -> BinaryIO:
        if partition_id in self.handles:
            handle = self.handles.pop(partition_id)
            self.handles[partition_id] = handle
            return handle
        if len(self.handles) >= self.max_open:
            _, old_handle = self.handles.popitem(last=False)
            old_handle.close()
        handle = self.paths[partition_id].open("rb", buffering=1024 * 1024)
        self.handles[partition_id] = handle
        return handle

    def close(self) -> None:
        while self.handles:
            _, handle = self.handles.popitem(last=False)
            handle.close()

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()


def read_source_metadata() -> tuple[dict[str, Any], list[dict[str, str]], dict[str, dict[str, str]]]:
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("validation_status") != "PASS":
        fail("Frozen Task #035B manifest is not validated")
    if manifest.get("prioritization_output_schema_version") != SOURCE_SCHEMA_VERSION:
        fail("Frozen Task #035B schema version changed")
    if manifest.get("prioritization_representation_version") != SOURCE_REPRESENTATION_VERSION:
        fail("Frozen Task #035B representation version changed")
    if manifest.get("counts", {}).get("representations") != EXPECTED_OBJECTS:
        fail("Frozen Task #035B representation count changed")

    with SOURCE_INDEX.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != SOURCE_INDEX_COLUMNS:
            fail("Frozen Task #035B index columns changed")
        index_rows = list(reader)
    if len(index_rows) != EXPECTED_OBJECTS:
        fail(f"Expected {EXPECTED_OBJECTS} source rows, observed {len(index_rows)}")
    seen: set[str] = set()
    for ordinal, row in enumerate(index_rows, 1):
        if int(row["universe_ordinal"]) != ordinal:
            fail(f"Canonical source order mismatch at ordinal {ordinal}")
        if row["EnsemblID"] in seen:
            fail(f"Duplicate source EnsemblID: {row['EnsemblID']}")
        seen.add(row["EnsemblID"])

    with SOURCE_PARTITIONS.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != SOURCE_PARTITION_COLUMNS:
            fail("Frozen Task #035B partition columns changed")
        partition_rows = list(reader)
    if len(partition_rows) != EXPECTED_PARTITIONS:
        fail("Frozen Task #035B partition count changed")
    partition_map = {row["partition_id"]: row for row in partition_rows}
    if len(partition_map) != EXPECTED_PARTITIONS:
        fail("Duplicate frozen source partition ID")

    set_id = manifest.get("large_payload", {}).get("artifact_id")
    source_root = SOURCE_EXTERNAL_ROOT / str(set_id)
    if not source_root.is_dir() or source_root.is_symlink():
        fail(f"Frozen external Task #035B payload unavailable: {source_root}")
    for partition_id, row in partition_map.items():
        expected = {
            "partition_strategy_version": SOURCE_PARTITION_STRATEGY,
            "partition_set_artifact_id": set_id,
            "generator_version": SOURCE_GENERATOR_VERSION,
            "prioritization_output_schema_version": SOURCE_SCHEMA_VERSION,
            "prioritization_representation_version": SOURCE_REPRESENTATION_VERSION,
            "rule_catalog_version": SOURCE_RULE_CATALOG_VERSION,
            "validation_status": "PASS",
        }
        if any(row.get(key) != value for key, value in expected.items()):
            fail(f"Frozen source partition metadata mismatch: {partition_id}")
        path = source_root / "partitions" / partition_id / "prioritization_records.jsonl"
        if not path.is_file() or path.is_symlink():
            fail(f"Frozen source partition unavailable or unsafe: {path}")
        if path.stat().st_size != int(row["artifact_size"]):
            fail(f"Frozen source partition size mismatch: {partition_id}")
        if sha256_file(path) != row["sha256"]:
            fail(f"Frozen source partition hash mismatch: {partition_id}")
        row["_local_path"] = str(path)
    return manifest, index_rows, partition_map


def read_source_record(
    pool: LRUReadPool, row: dict[str, str], source_rules: Any
) -> tuple[dict[str, Any], str]:
    handle = pool.reader(row["partition_id"])
    offset = int(row["record_offset_bytes"])
    length = int(row["record_length_bytes"])
    handle.seek(offset)
    raw = handle.read(length)
    if len(raw) != length or not raw.endswith(b"\n"):
        fail(f"Source record boundary mismatch at ordinal {row['universe_ordinal']}")
    content_hash = sha256_bytes(raw[:-1])
    if content_hash != row["representation_content_sha256"]:
        fail(f"Source content hash mismatch at ordinal {row['universe_ordinal']}")
    value = json.loads(raw)
    if (
        value.get("EnsemblID") != row["EnsemblID"]
        or value.get("universe_ordinal") != int(row["universe_ordinal"])
        or value.get("prioritization_representation_id")
        != row["prioritization_representation_id"]
        or value.get("source_summary_identity", {}).get("evidence_summary_id")
        != row["source_evidence_summary_id"]
        or value.get("source_summary_identity", {}).get("evidence_summary_content_sha256")
        != row["source_summary_content_sha256"]
    ):
        fail(f"Source identity reconciliation failed at ordinal {row['universe_ordinal']}")
    if (
        value.get("category_assignment", {}).get("category") != row["category"]
        or value.get("category_assignment", {}).get("assigned_rule_id")
        != row["assigned_rule_id"]
        or len(value.get("category_assignment", {}).get("rule_trace", [])) != 4
    ):
        fail(f"Source rule trace reconciliation failed at ordinal {row['universe_ordinal']}")
    source_rules.validate_assignment_semantics(value)
    return value, content_hash


def build_dossier(
    source: dict[str, Any], source_content_hash: str, selected_rule: tuple[Any, ...],
    results: list[bool], case_module: Any,
) -> dict[str, Any]:
    ordinal, rule_id, predicate_id, category, reason_code = selected_rule
    observations = case_module.case_observations(
        source["component_state_snapshot"], source["limitation_identifiers"]
    )
    token_input = [
        case_module.FRAMEWORK_VERSION,
        category,
        source["EnsemblID"],
        source["prioritization_representation_id"],
        source_content_hash,
    ]
    token = sha256_bytes(canonical_json(token_input).encode("utf-8"))
    identity = [
        source["EnsemblID"], case_module.SCHEMA_VERSION,
        case_module.FRAMEWORK_VERSION, category,
        source["prioritization_representation_id"], case_module.RULE_CATALOG_VERSION,
    ]
    dossier = {
        "EnsemblID": source["EnsemblID"],
        "universe_ordinal": source["universe_ordinal"],
        "case_selection_id": stable_id("CASESEL", identity),
        "case_selection_schema_version": case_module.SCHEMA_VERSION,
        "case_selection_framework_version": case_module.FRAMEWORK_VERSION,
        "case_rule_catalog_version": case_module.RULE_CATALOG_VERSION,
        "case_selector_version": GENERATOR_VERSION,
        "source_prioritization_identity": {
            "prioritization_representation_id": source["prioritization_representation_id"],
            "prioritization_output_schema_version": source["prioritization_output_schema_version"],
            "prioritization_representation_version": source["prioritization_representation_version"],
            "prioritization_rule_catalog_version": source["rule_catalog_version"],
            "prioritization_content_sha256": source_content_hash,
            "source_category": source["category_assignment"]["category"],
            "source_assigned_rule_id": source["category_assignment"]["assigned_rule_id"],
            "source_summary_identity": deepcopy(source["source_summary_identity"]),
        },
        "source_prioritization_rule_trace": deepcopy(
            source["category_assignment"]["rule_trace"]
        ),
        "component_state_snapshot": deepcopy(source["component_state_snapshot"]),
        "limitation_identifiers": list(source["limitation_identifiers"]),
        "case_selection": {
            "case_category": category,
            "case_rule_id": rule_id,
            "predicate_trace": [
                {
                    "trace_step_ordinal": item[0],
                    "case_rule_id": item[1],
                    "predicate_id": item[2],
                    "predicate_result": result,
                    "input_observations": deepcopy(observations),
                }
                for item, result in zip(case_module.CASE_RULES, results, strict=True)
            ],
            "structural_reason": {
                "reason_code": reason_code,
                "matched_input_references": deepcopy(observations),
            },
            "selection_method_id": case_module.SELECTION_METHOD_ID,
            "selection_token_sha256": token,
        },
    }
    if not results[ordinal - 1]:
        fail(f"Attempted to materialize ineligible category: {category}")
    return dossier


def reconcile_dossier(
    dossier: dict[str, Any], source: dict[str, Any], source_hash: str,
    case_module: Any, source_rules: Any, schema: dict[str, Any], validator: Any,
) -> None:
    validator.validate_instance(dossier, schema, schema)
    case_module.validate_case_semantics(dossier, source_rules)
    assert_no_prohibited_fields(dossier)
    if dossier["EnsemblID"] != source["EnsemblID"] or dossier["universe_ordinal"] != source["universe_ordinal"]:
        fail("Dossier source identity changed")
    identity = dossier["source_prioritization_identity"]
    if (
        identity["prioritization_representation_id"]
        != source["prioritization_representation_id"]
        or identity["prioritization_content_sha256"] != source_hash
        or identity["source_summary_identity"] != source["source_summary_identity"]
    ):
        fail("Dossier source identity reconciliation failed")
    if dossier["source_prioritization_rule_trace"] != source["category_assignment"]["rule_trace"]:
        fail("Dossier source rule trace changed")
    if dossier["component_state_snapshot"] != source["component_state_snapshot"]:
        fail("Dossier component snapshot changed")
    if dossier["limitation_identifiers"] != source["limitation_identifiers"]:
        fail("Dossier limitations changed")


def generate_pass(
    index_rows: list[dict[str, str]], partition_map: dict[str, dict[str, str]],
    case_module: Any, source_rules: Any, schema: dict[str, Any], validator: Any,
) -> dict[str, Any]:
    counts = {rule[3]: 0 for rule in case_module.CASE_RULES}
    winners: dict[str, dict[str, Any] | None] = {
        rule[3]: None for rule in case_module.CASE_RULES
    }
    paths = {part: Path(row["_local_path"]) for part, row in partition_map.items()}
    with LRUReadPool(paths) as pool:
        for row in index_rows:
            source, source_hash = read_source_record(pool, row, source_rules)
            results = case_module.evaluate_case_rules(
                source["component_state_snapshot"], source["limitation_identifiers"]
            )
            for rule, result in zip(case_module.CASE_RULES, results, strict=True):
                if not result:
                    continue
                category = rule[3]
                counts[category] += 1
                dossier = build_dossier(source, source_hash, rule, results, case_module)
                token = dossier["case_selection"]["selection_token_sha256"]
                current = winners[category]
                if current is None or token < current["case_selection"]["selection_token_sha256"]:
                    reconcile_dossier(
                        dossier, source, source_hash, case_module, source_rules,
                        schema, validator,
                    )
                    winners[category] = dossier

    for category, count in counts.items():
        if (count == 0) != (winners[category] is None):
            fail(f"Filled/unfilled reconciliation failed: {category}")
    release = build_release(counts, winners, case_module)
    assert_no_prohibited_fields(release)
    return {
        "counts": counts,
        "winners": winners,
        "release_bytes": pretty_json_bytes(release),
    }


def build_release(
    counts: dict[str, int], winners: dict[str, dict[str, Any] | None], case_module: Any
) -> dict[str, Any]:
    slots: list[dict[str, Any]] = []
    for rule in case_module.CASE_RULES:
        _, rule_id, predicate_id, category, reason_code = rule
        dossier = winners[category]
        slots.append({
            "case_category": category,
            "selection_status": "FILLED" if dossier is not None else "UNFILLED_NO_ELIGIBLE_RECORD",
            "eligible_pool_count": counts[category],
            "case_rule_id": rule_id,
            "predicate_id": predicate_id,
            "structural_reason_code": reason_code,
            "selection_method_id": case_module.SELECTION_METHOD_ID,
            "dossier": deepcopy(dossier),
        })
    return {
        "dossier_release_version": DOSSIER_RELEASE_VERSION,
        "case_selection_schema_version": case_module.SCHEMA_VERSION,
        "case_selection_framework_version": case_module.FRAMEWORK_VERSION,
        "case_rule_catalog_version": case_module.RULE_CATALOG_VERSION,
        "case_selector_version": GENERATOR_VERSION,
        "source_prioritization_schema_version": SOURCE_SCHEMA_VERSION,
        "source_prioritization_representation_version": SOURCE_REPRESENTATION_VERSION,
        "source_prioritization_rule_catalog_version": SOURCE_RULE_CATALOG_VERSION,
        "source_universe_count": EXPECTED_OBJECTS,
        "case_slots": slots,
    }


def build_index_rows(pass_result: dict[str, Any], case_module: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rule in case_module.CASE_RULES:
        _, rule_id, predicate_id, category, reason_code = rule
        dossier = pass_result["winners"][category]
        if dossier is None:
            rows.append({
                "case_category": category,
                "selection_status": "UNFILLED_NO_ELIGIBLE_RECORD",
                "eligible_pool_count": pass_result["counts"][category],
                "case_rule_id": rule_id, "predicate_id": predicate_id,
                "structural_reason_code": reason_code,
                "selection_method_id": case_module.SELECTION_METHOD_ID,
                **{field: "NOT_APPLICABLE" for field in INDEX_COLUMNS[7:]},
            })
            continue
        source_identity = dossier["source_prioritization_identity"]
        summary_identity = source_identity["source_summary_identity"]
        components = {item["component_id"]: item for item in dossier["component_state_snapshot"]}
        transcriptomic = components["COMP_TRANSCRIPTOMIC_EVIDENCE"]
        disease = components["COMP_DISEASE_ASSOCIATION"]
        limitation_count = len(dossier["limitation_identifiers"]) + sum(
            len(item["limitation_identifiers"]) for item in dossier["component_state_snapshot"]
        )
        rows.append({
            "case_category": category, "selection_status": "FILLED",
            "eligible_pool_count": pass_result["counts"][category],
            "case_rule_id": rule_id, "predicate_id": predicate_id,
            "structural_reason_code": reason_code,
            "selection_method_id": case_module.SELECTION_METHOD_ID,
            "selection_token_sha256": dossier["case_selection"]["selection_token_sha256"],
            "case_selection_id": dossier["case_selection_id"],
            "universe_ordinal": dossier["universe_ordinal"], "EnsemblID": dossier["EnsemblID"],
            "source_prioritization_representation_id": source_identity["prioritization_representation_id"],
            "source_prioritization_content_sha256": source_identity["prioritization_content_sha256"],
            "source_evidence_summary_id": summary_identity["evidence_summary_id"],
            "source_evidence_summary_content_sha256": summary_identity["evidence_summary_content_sha256"],
            "source_category": source_identity["source_category"],
            "source_assigned_rule_id": source_identity["source_assigned_rule_id"],
            "transcriptomic_component_id": transcriptomic["component_id"],
            "transcriptomic_component_version": transcriptomic["component_version"],
            "transcriptomic_component_state": transcriptomic["component_state"],
            "disease_association_component_id": disease["component_id"],
            "disease_association_component_version": disease["component_version"],
            "disease_association_component_state": disease["component_state"],
            "limitation_identifier_count": limitation_count,
        })
    return rows


def build_session(source_manifest: dict[str, Any], case_module: Any) -> bytes:
    lines = [
        f"task={TASK_ID}", f"generator_version={GENERATOR_VERSION}",
        f"python_version={platform.python_version()}", f"python_implementation={platform.python_implementation()}",
        "standard_library_only=TRUE", "network_access=PROHIBITED_NOT_USED",
        "external_knowledge=NOT_USED", "gene_symbols=NOT_USED",
        "runtime_ai_llm_decisions=PROHIBITED_NONE_USED", "randomness=NOT_USED",
        f"source_release_id={source_manifest['release_id']}",
        f"source_payload_artifact_id={source_manifest['large_payload']['artifact_id']}",
        f"source_payload_partition_set_sha256={source_manifest['large_payload']['partition_set_sha256']}",
        f"source_universe_count={EXPECTED_OBJECTS}",
        f"case_selection_schema_version={case_module.SCHEMA_VERSION}",
        f"case_selection_framework_version={case_module.FRAMEWORK_VERSION}",
        f"case_rule_catalog_version={case_module.RULE_CATALOG_VERSION}",
        f"selection_method_id={case_module.SELECTION_METHOD_ID}",
        "complete_source_scans=2", "deterministic_regeneration=BYTE_IDENTICAL",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def build_report(pass_result: dict[str, Any], index_rows: list[dict[str, Any]]) -> bytes:
    selection_lines = [
        f"| {row['case_category']} | {row['selection_status']} | {row['eligible_pool_count']} | {row['EnsemblID']} | {row['universe_ordinal']} |"
        for row in index_rows
    ]
    text = f"""# Task #036B Case Dossier Validation Report

## Scope

This release contains presentation-oriented structural case-pattern dossiers only. It does not identify optimal targets and contains no biological or therapeutic interpretation.

## Selection results

| Case category | Status | Eligible source records | Selected EnsemblID | Universe ordinal |
|---|---:|---:|---|---:|
{chr(10).join(selection_lines)}

All {EXPECTED_OBJECTS:,} frozen Task #035B representations were evaluated independently for every Task #036A category. Category overlap was preserved. No fallback record was substituted for an empty eligible pool.

## Validation

- PASS — source identity and immutable EnsemblID reconciliation
- PASS — complete four-step source rule-trace reconciliation
- PASS — Task #036A category and predicate-trace reconciliation
- PASS — category-salted SHA256 token reproduction and lexicographic minimum selection
- PASS — every filled dossier validates against `CASE_STUDY_SELECTION_SCHEMA_V0.1`
- PASS — component IDs, versions, states, source record IDs, and limitations are unchanged
- PASS — recursive prohibited-field scan
- PASS — two complete {EXPECTED_OBJECTS:,}-record regenerations are byte-identical
- PASS — all frozen Task #035B and Task #036A input hashes unchanged before and after generation

## Interpretation boundary

The selected records are deterministic examples of structural evidence patterns. Selection tokens are routing devices, not measurements. Category membership and selection do not establish biological importance, comparative merit, or therapeutic suitability.
"""
    return text.encode("utf-8")


def build_manifest(
    source_manifest: dict[str, Any], frozen_hashes: dict[str, str],
    pass_result: dict[str, Any], index_rows: list[dict[str, Any]],
    artifact_meta: dict[str, dict[str, Any]], case_module: Any,
) -> bytes:
    filled = sum(row["selection_status"] == "FILLED" for row in index_rows)
    manifest = {
        "task_id": TASK_ID,
        "release_id": stable_id("CASEREL", [
            DOSSIER_RELEASE_VERSION, source_manifest["release_id"],
            case_module.FRAMEWORK_VERSION, case_module.RULE_CATALOG_VERSION,
        ]),
        "dossier_release_version": DOSSIER_RELEASE_VERSION,
        "generator": {
            "relative_path": "analysis/36B_generate_case_dossiers.py",
            "generator_version": GENERATOR_VERSION,
            "sha256": sha256_file(ROOT / "analysis/36B_generate_case_dossiers.py"),
        },
        "source": {
            "prioritization_release_id": source_manifest["release_id"],
            "prioritization_schema_version": SOURCE_SCHEMA_VERSION,
            "prioritization_representation_version": SOURCE_REPRESENTATION_VERSION,
            "prioritization_rule_catalog_version": SOURCE_RULE_CATALOG_VERSION,
            "source_universe_count": EXPECTED_OBJECTS,
            "source_payload_artifact_id": source_manifest["large_payload"]["artifact_id"],
            "source_payload_partition_set_sha256": source_manifest["large_payload"]["partition_set_sha256"],
        },
        "case_contract": {
            "case_selection_schema_version": case_module.SCHEMA_VERSION,
            "case_selection_framework_version": case_module.FRAMEWORK_VERSION,
            "case_rule_catalog_version": case_module.RULE_CATALOG_VERSION,
            "selection_method_id": case_module.SELECTION_METHOD_ID,
            "categories_non_ordinal": [rule[3] for rule in case_module.CASE_RULES],
        },
        "counts": {
            "source_representations_evaluated_per_regeneration": EXPECTED_OBJECTS,
            "complete_regenerations": 2, "case_slots": len(case_module.CASE_RULES),
            "filled_case_slots": filled, "unfilled_case_slots": len(case_module.CASE_RULES) - filled,
            "eligible_pool_counts": pass_result["counts"],
        },
        "selection_results": [
            {
                "case_category": row["case_category"], "selection_status": row["selection_status"],
                "eligible_pool_count": row["eligible_pool_count"], "case_selection_id": row["case_selection_id"],
                "EnsemblID": row["EnsemblID"], "universe_ordinal": row["universe_ordinal"],
                "selection_token_sha256": row["selection_token_sha256"],
            }
            for row in index_rows
        ],
        "git_managed_artifacts": artifact_meta,
        "frozen_inputs": frozen_hashes,
        "validation": {
            "status": "PASS", "source_identity_reconciliation": "PASS",
            "rule_trace_reconciliation": "PASS", "category_reconciliation": "PASS",
            "deterministic_token_reproduction": "PASS", "schema_validation": "PASS",
            "recursive_prohibited_field_scan": "PASS",
            "two_complete_regenerations": "BYTE_IDENTICAL",
            "frozen_input_hashes_before_after": "UNCHANGED",
        },
        "interpretation_boundary": "STRUCTURAL_REPRESENTATIVE_CASE_PATTERNS_ONLY",
        "validation_status": "PASS",
    }
    return pretty_json_bytes(manifest)


def main() -> None:
    validate_working_tree_scope()
    validate_output_scope()
    frozen_before = validate_frozen_inputs()
    case_module = load_module(CASE_MODULE_PATH, "task36a_case_contract")
    source_rules = case_module.load_source_rules()
    validator = source_rules.load_source_validator()
    schema = json.loads(CASE_SCHEMA_PATH.read_text(encoding="utf-8"))
    source_manifest, index_rows, partition_map = read_source_metadata()

    first = generate_pass(index_rows, partition_map, case_module, source_rules, schema, validator)
    second = generate_pass(index_rows, partition_map, case_module, source_rules, schema, validator)
    if first["counts"] != second["counts"] or first["release_bytes"] != second["release_bytes"]:
        fail("Two complete deterministic regenerations are not byte-identical")

    output_rows = build_index_rows(first, case_module)
    index_data = csv_bytes(INDEX_COLUMNS, output_rows)
    dossier_data = first["release_bytes"]
    session_data = build_session(source_manifest, case_module)
    report_data = build_report(first, output_rows)
    if frozen_before != validate_frozen_inputs():
        fail("Frozen input hashes changed during generation")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_bytes(index_data)
    DOSSIERS_PATH.write_bytes(dossier_data)
    REPORT_PATH.write_bytes(report_data)
    SESSION_PATH.write_bytes(session_data)
    artifact_meta = {
        path.name: {"artifact_size": len(data), "sha256": sha256_bytes(data)}
        for path, data in (
            (INDEX_PATH, index_data), (DOSSIERS_PATH, dossier_data),
            (REPORT_PATH, report_data), (SESSION_PATH, session_data),
        )
    }
    manifest_data = build_manifest(
        source_manifest, frozen_before, first, output_rows, artifact_meta, case_module
    )
    MANIFEST_PATH.write_bytes(manifest_data)

    if frozen_before != validate_frozen_inputs():
        fail("Frozen inputs changed after writing Task #036B outputs")
    if INDEX_PATH.read_bytes() != index_data or DOSSIERS_PATH.read_bytes() != dossier_data:
        fail("Written Task #036B artifacts differ from validated bytes")
    validate_working_tree_scope()

    print(f"source_representations_evaluated={EXPECTED_OBJECTS}")
    for row in output_rows:
        print(
            f"{row['case_category']}={row['selection_status']};"
            f"eligible={row['eligible_pool_count']};EnsemblID={row['EnsemblID']}"
        )
    print("complete_regenerations=2")
    print("deterministic_regeneration=BYTE_IDENTICAL")
    print("validation_status=PASS")


if __name__ == "__main__":
    main()
