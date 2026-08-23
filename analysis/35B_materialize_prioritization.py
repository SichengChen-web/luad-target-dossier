#!/usr/bin/env python3
"""Materialize Transparent Prioritization Prototype v0.1 representations.

The program evaluates only the four frozen Task #035A structural predicates
against component states copied from frozen Task #034B Evidence Summaries. It
performs no evidence retrieval, scoring, ranking, target selection,
recommendation, biological interpretation, or runtime AI/LLM decision.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import platform
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "outputs/evidence_summary_v0.1"
SOURCE_MANIFEST = SOURCE_DIR / "summary_manifest.json"
SOURCE_INDEX = SOURCE_DIR / "summary_index.csv"
SOURCE_PARTITIONS = SOURCE_DIR / "partition_manifest.csv"
SOURCE_EXTERNAL_ROOT = Path(
    "/private/tmp/luad-target-dossier-external-artifacts/evidence_summary_v0.1"
)
SOURCE_UTILITY_PATH = ROOT / "analysis/34B_materialize_evidence_summary.py"
RULE_MODULE_PATH = ROOT / "analysis/35A_define_prioritization_schema.py"
SCHEMA_PATH = ROOT / "schemas/prioritization_output_schema_v0.1.json"

OUTPUT_DIR = ROOT / "outputs/prioritization_v0.1"
EXTERNAL_ROOT = Path(
    "/private/tmp/luad-target-dossier-external-artifacts/prioritization_v0.1"
)
MANIFEST_PATH = OUTPUT_DIR / "prioritization_manifest.json"
INDEX_PATH = OUTPUT_DIR / "prioritization_index.csv"
PARTITION_MANIFEST_PATH = OUTPUT_DIR / "partition_manifest.csv"
REPORT_PATH = OUTPUT_DIR / "validation_report.md"
SESSION_PATH = OUTPUT_DIR / "session_info.txt"

TASK_ID = "TASK_035B"
GENERATOR_VERSION = "TRANSPARENT_PRIORITIZATION_MATERIALIZER_V0.1"
SCHEMA_VERSION = "PRIORITIZATION_OUTPUT_SCHEMA_V0.1"
REPRESENTATION_VERSION = "TRANSPARENT_PRIORITIZATION_PROTOTYPE_V0.1"
RULE_CATALOG_VERSION = "PRIORITIZATION_RULE_CATALOG_V0.1"
SOURCE_SCHEMA_VERSION = "EVIDENCE_SUMMARY_SCHEMA_V0.1"
SOURCE_SUMMARY_VERSION = "EVIDENCE_AGGREGATION_REPRESENTATION_V0.1"
SOURCE_GENERATOR_VERSION = "EVIDENCE_SUMMARY_MATERIALIZER_V0.1"
PARTITION_STRATEGY_VERSION = "ENSEMBL_SHA256_PREFIX_2_V0.1"
EXPECTED_OBJECTS = 29_606
EXPECTED_COMPONENTS = 59_212
EXPECTED_PARTITIONS = 256
EXPECTED_TRACE_STEPS = EXPECTED_OBJECTS * 4
GIT_PROHIBITED_THRESHOLD = 100_000_000

COMPONENT_ORDER = (
    ("COMP_TRANSCRIPTOMIC_EVIDENCE", "COMP_TRANSCRIPTOMIC_EVIDENCE_V0.1"),
    ("COMP_DISEASE_ASSOCIATION", "COMP_DISEASE_ASSOCIATION_V0.1"),
)
ALLOWED_CATEGORIES = {
    "CATEGORY_A",
    "CATEGORY_B",
    "CATEGORY_C",
    "CATEGORY_UNASSIGNED",
}
RULE_IDS = (
    "PRULE_035A_001_PARTIAL_OR_CONFLICTING",
    "PRULE_035A_002_ALL_OBSERVED",
    "PRULE_035A_003_MIXED_OBSERVED_UNAVAILABLE",
    "PRULE_035A_004_ALL_UNAVAILABLE",
)
PROHIBITED_FIELDS = {
    "score",
    "ranking",
    "rank",
    "priority_score",
    "confidence",
    "probability",
    "success_prediction",
    "recommendation",
    "target_quality",
    "evidence_strength",
}

FROZEN_INPUT_SHA256 = {
    "analysis/34B_materialize_evidence_summary.py": "2b24b79c46100b919243e8978d7c29a96ec2f20428f2153c29c0573f6af47685",
    "outputs/evidence_summary_v0.1/summary_manifest.json": "02b9a893569bd01257cb0108121f61a78041e90ffd769ac7a1d163d24051e19f",
    "outputs/evidence_summary_v0.1/summary_index.csv": "27489b08061102c4d325bac7d4761682f8c7e811458b5cff88d4fec3b0bc17e5",
    "outputs/evidence_summary_v0.1/partition_manifest.csv": "fd9bd76ea5f940a0165a6a082538a810fc64cbcd8b0fe4ecda9f0aae14795202",
    "outputs/evidence_summary_v0.1/validation_report.md": "257662af9adf87ce7f913e2024b6e43db2685cc84a117f9424830b6308c034e8",
    "outputs/evidence_summary_v0.1/session_info.txt": "bd04e5a858f2c70e746954d2e99bdfd44e3d64f818261d31c393f20bed9bda44",
    "analysis/35A_define_prioritization_schema.py": "de23378886ebfc2cdb264bd96d680ce4d24d043588ccdb13d71f5530acdb6d07",
    "docs/governance/prioritization_framework_specification_v0.1.md": "104afeda3b4ecb824369d7f1f655213dbdc36679c1fd97c3b95e00ad63163f5a",
    "docs/governance/prioritization_rule_catalog_v0.1.md": "7794d79debd01c0a2e00f6d6109f78048089b8a1a747f77372e1e589e0dfadb1",
    "docs/governance/prioritization_validation_requirements_v0.1.md": "bf26ca1882685caf1da4cb45ccda0726049087c4782deab925524a8f0d321c47",
    "schemas/prioritization_output_schema_v0.1.json": "c79dcb1478e71239d158855ebf6b0f3b58cad84286fe1da3806bb22e77e74d72",
}

SOURCE_INDEX_COLUMNS = [
    "universe_ordinal",
    "EnsemblID",
    "evidence_summary_id",
    "source_landscape_id",
    "source_landscape_content_sha256",
    "source_landscape_schema_version",
    "source_landscape_version",
    "transcriptomic_component_version",
    "transcriptomic_component_state",
    "disease_association_component_version",
    "disease_association_component_state",
    "component_count",
    "feature_missingness_count",
    "dependency_summary_count",
    "dependency_relationship_count",
    "multi_dependency_summary_count",
    "limitation_identifiers",
    "partition_id",
    "payload_artifact_id",
    "record_offset_bytes",
    "record_length_bytes",
    "summary_content_sha256",
    "evidence_summary_schema_version",
    "evidence_summary_version",
    "generator_version",
]
SOURCE_PARTITION_COLUMNS = [
    "partition_id",
    "partition_strategy_version",
    "partition_set_artifact_id",
    "artifact_id",
    "artifact_class",
    "artifact_role",
    "artifact_size",
    "sha256",
    "generator_version",
    "storage_reference_placeholder",
    "storage_status",
    "summary_count",
    "first_universe_ordinal",
    "last_universe_ordinal",
    "evidence_summary_schema_version",
    "evidence_summary_version",
    "validation_status",
]
INDEX_COLUMNS = [
    "universe_ordinal",
    "EnsemblID",
    "prioritization_representation_id",
    "source_evidence_summary_id",
    "source_summary_content_sha256",
    "source_evidence_summary_schema_version",
    "source_evidence_summary_version",
    "transcriptomic_component_version",
    "transcriptomic_component_state",
    "disease_association_component_version",
    "disease_association_component_state",
    "category",
    "assigned_rule_id",
    "true_rule_count",
    "rule_trace_step_count",
    "limitation_identifiers",
    "partition_id",
    "payload_artifact_id",
    "record_offset_bytes",
    "record_length_bytes",
    "representation_content_sha256",
    "prioritization_output_schema_version",
    "prioritization_representation_version",
    "rule_catalog_version",
    "generator_version",
]
PARTITION_COLUMNS = [
    "partition_id",
    "partition_strategy_version",
    "partition_set_artifact_id",
    "artifact_id",
    "artifact_class",
    "artifact_role",
    "artifact_size",
    "sha256",
    "generator_version",
    "storage_reference_placeholder",
    "storage_status",
    "representation_count",
    "first_universe_ordinal",
    "last_universe_ordinal",
    "prioritization_output_schema_version",
    "prioritization_representation_version",
    "rule_catalog_version",
    "validation_status",
]

ALLOWED_WORKTREE_PATHS = {
    "analysis/35B_materialize_prioritization.py",
    *(f"outputs/prioritization_v0.1/{name}" for name in (
        "prioritization_manifest.json",
        "prioritization_index.csv",
        "partition_manifest.csv",
        "validation_report.md",
        "session_info.txt",
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
    allowed = {MANIFEST_PATH, INDEX_PATH, PARTITION_MANIFEST_PATH, REPORT_PATH, SESSION_PATH}
    if OUTPUT_DIR.exists():
        unexpected = sorted(
            path.relative_to(ROOT).as_posix()
            for path in OUTPUT_DIR.rglob("*")
            if path.is_file() and path not in allowed
        )
        if unexpected:
            fail("Unexpected repository prioritization payload/output files: " + ", ".join(unexpected))


def validate_frozen_inputs(utility: Any) -> dict[str, str]:
    observed: dict[str, str] = {}
    for relative_path, expected_hash in FROZEN_INPUT_SHA256.items():
        path = ROOT / relative_path
        if not path.is_file():
            fail(f"Frozen input missing: {relative_path}")
        actual_hash = utility.sha256_file(path)
        if actual_hash != expected_hash:
            fail(
                f"Frozen input hash mismatch: {relative_path}; "
                f"expected {expected_hash}, observed {actual_hash}"
            )
        observed[relative_path] = actual_hash
    return observed


def read_source_metadata(utility: Any) -> tuple[
    dict[str, Any], list[dict[str, str]], dict[str, dict[str, str]]
]:
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    expected_manifest = {
        "validation_status": "PASS",
        "evidence_summary_schema_version": SOURCE_SCHEMA_VERSION,
        "evidence_summary_version": SOURCE_SUMMARY_VERSION,
    }
    for key, expected in expected_manifest.items():
        if manifest.get(key) != expected:
            fail(f"Frozen Task #034B manifest mismatch: {key}")
    counts = manifest.get("counts", {})
    if (
        counts.get("summaries") != EXPECTED_OBJECTS
        or counts.get("components") != EXPECTED_COMPONENTS
        or counts.get("partitions") != EXPECTED_PARTITIONS
    ):
        fail("Frozen Task #034B reconciliation counts changed")
    if manifest.get("component_versions") != dict(COMPONENT_ORDER):
        fail("Frozen Task #034B component versions changed")

    with SOURCE_INDEX.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != SOURCE_INDEX_COLUMNS:
            fail("Frozen Evidence Summary index columns changed")
        index_rows = list(reader)
    if len(index_rows) != EXPECTED_OBJECTS:
        fail(f"Expected {EXPECTED_OBJECTS} source summaries, observed {len(index_rows)}")
    seen: set[str] = set()
    for ordinal, row in enumerate(index_rows, 1):
        if int(row["universe_ordinal"]) != ordinal:
            fail(f"Source summary canonical order mismatch at ordinal {ordinal}")
        if row["EnsemblID"] in seen:
            fail(f"Duplicate source-summary EnsemblID: {row['EnsemblID']}")
        if utility.partition_id(row["EnsemblID"]) != row["partition_id"]:
            fail(f"Source summary partition mismatch at ordinal {ordinal}")
        seen.add(row["EnsemblID"])

    with SOURCE_PARTITIONS.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != SOURCE_PARTITION_COLUMNS:
            fail("Frozen Evidence Summary partition columns changed")
        partition_rows = list(reader)
    if len(partition_rows) != EXPECTED_PARTITIONS:
        fail("Frozen Evidence Summary partition count changed")
    partition_map = {row["partition_id"]: row for row in partition_rows}
    if len(partition_map) != EXPECTED_PARTITIONS:
        fail("Duplicate source-summary partition ID")
    set_id = manifest.get("large_payload", {}).get("artifact_id")
    source_root = SOURCE_EXTERNAL_ROOT / str(set_id)
    if not source_root.is_dir() or source_root.is_symlink():
        fail(f"Frozen external Evidence Summary payload is unavailable: {source_root}")
    for part, row in partition_map.items():
        expected = {
            "partition_strategy_version": PARTITION_STRATEGY_VERSION,
            "partition_set_artifact_id": set_id,
            "generator_version": SOURCE_GENERATOR_VERSION,
            "evidence_summary_schema_version": SOURCE_SCHEMA_VERSION,
            "evidence_summary_version": SOURCE_SUMMARY_VERSION,
            "validation_status": "PASS",
        }
        if any(row.get(key) != value for key, value in expected.items()):
            fail(f"Frozen source-summary partition metadata mismatch: {part}")
        path = source_root / "partitions" / part / "summary_records.jsonl"
        if not path.is_file() or path.is_symlink():
            fail(f"Frozen source-summary partition unavailable or unsafe: {path}")
        if path.stat().st_size != int(row["artifact_size"]):
            fail(f"Frozen source-summary partition size mismatch: {part}")
        row["_local_path"] = str(path)
    return manifest, index_rows, partition_map


def project_representation(summary: dict[str, Any], content_hash: str, rules: Any, utility: Any) -> dict[str, Any]:
    component_snapshot = [
        {
            "component_id": item["component_id"],
            "component_version": item["component_version"],
            "component_state": item["component_state"],
            "source_component_record_id": item["source_component_record_id"],
            "limitation_identifiers": list(item["limitation_identifiers"]),
        }
        for item in summary["component_summaries"]
    ]
    states = [item["component_state"] for item in component_snapshot]
    results = rules.evaluate_rules(states)
    true_indices = [index for index, result in enumerate(results) if result]
    if len(true_indices) != 1:
        fail("Frozen rule catalog did not resolve exactly one category")
    assigned = rules.RULES[true_indices[0]]
    observations = [
        {
            "json_pointer": f"/component_state_snapshot/{index}/component_state",
            "observed_value": state,
        }
        for index, state in enumerate(states)
    ]
    identity = [
        summary["EnsemblID"],
        SCHEMA_VERSION,
        REPRESENTATION_VERSION,
        summary["evidence_summary_id"],
        RULE_CATALOG_VERSION,
    ]
    source_landscape = summary["source_landscape_identity"]
    return {
        "EnsemblID": summary["EnsemblID"],
        "universe_ordinal": summary["universe_ordinal"],
        "prioritization_representation_id": utility.stable_id("PRZ", identity),
        "prioritization_output_schema_version": SCHEMA_VERSION,
        "prioritization_representation_version": REPRESENTATION_VERSION,
        "rule_catalog_version": RULE_CATALOG_VERSION,
        "prioritization_generator_version": GENERATOR_VERSION,
        "source_summary_identity": {
            "evidence_summary_id": summary["evidence_summary_id"],
            "evidence_summary_schema_version": summary[
                "evidence_summary_schema_version"
            ],
            "evidence_summary_version": summary["evidence_summary_version"],
            "evidence_summary_content_sha256": content_hash,
            "source_landscape_id": source_landscape["landscape_id"],
            "source_evidence_snapshot_version": source_landscape[
                "source_evidence_snapshot_version"
            ],
        },
        "component_state_snapshot": component_snapshot,
        "limitation_identifiers": list(summary["limitation_identifiers"]),
        "category_assignment": {
            "category": assigned[3],
            "assigned_rule_id": assigned[1],
            "rule_trace": [
                {
                    "trace_step_ordinal": ordinal,
                    "rule_id": rule_id,
                    "predicate_id": predicate_id,
                    "predicate_result": result,
                    "input_observations": [dict(item) for item in observations],
                }
                for (ordinal, rule_id, predicate_id, _), result in zip(
                    rules.RULES, results, strict=True
                )
            ],
        },
    }


def reconcile_representation(summary: dict[str, Any], value: dict[str, Any], rules: Any) -> None:
    if (
        value["EnsemblID"] != summary["EnsemblID"]
        or value["universe_ordinal"] != summary["universe_ordinal"]
        or value["source_summary_identity"]["evidence_summary_id"]
        != summary["evidence_summary_id"]
    ):
        fail("Evidence Summary-to-prioritization identity mismatch")
    expected_components = [
        {
            "component_id": item["component_id"],
            "component_version": item["component_version"],
            "component_state": item["component_state"],
            "source_component_record_id": item["source_component_record_id"],
            "limitation_identifiers": item["limitation_identifiers"],
        }
        for item in summary["component_summaries"]
    ]
    if value["component_state_snapshot"] != expected_components:
        fail("Component IDs, versions, states, records, or limitations changed")
    if value["limitation_identifiers"] != summary["limitation_identifiers"]:
        fail("Summary limitation identifiers changed")
    rules.validate_assignment_semantics(value)
    true_count = sum(
        step["predicate_result"] for step in value["category_assignment"]["rule_trace"]
    )
    if true_count != 1 or value["category_assignment"]["category"] not in ALLOWED_CATEGORIES:
        fail("Category or true-rule reconciliation failed")


def generate_pass(
    destination: Path,
    source_index: list[dict[str, str]],
    source_partitions: dict[str, dict[str, str]],
    schema: dict[str, Any],
    rules: Any,
    schema_validator: Any,
    utility: Any,
    pass_name: str,
) -> dict[str, Any]:
    destination.mkdir(parents=True, exist_ok=False)
    output_stats = {
        f"p{number:02x}": {
            "sha256": hashlib.sha256(),
            "size": 0,
            "count": 0,
            "first_ordinal": None,
            "last_ordinal": None,
        }
        for number in range(EXPECTED_PARTITIONS)
    }
    source_stats = {
        part: {"sha256": hashlib.sha256(), "size": 0, "count": 0, "next_offset": 0}
        for part in source_partitions
    }
    source_paths = {part: Path(row["_local_path"]) for part, row in source_partitions.items()}
    index_rows: list[dict[str, Any]] = []
    category_counts: Counter[str] = Counter()
    true_rule_counts: Counter[str] = Counter()
    state_counts: Counter[tuple[str, str]] = Counter()
    total_components = 0
    total_trace_steps = 0

    with utility.LRUReadPool(source_paths) as readers, utility.LRUWritePool(destination) as writers:
        for ordinal, source_row in enumerate(source_index, 1):
            part = source_row["partition_id"]
            stat = source_stats[part]
            offset = int(source_row["record_offset_bytes"])
            length = int(source_row["record_length_bytes"])
            if offset != stat["next_offset"]:
                fail(f"Source summary offset/order mismatch at ordinal {ordinal}")
            handle = readers.reader(part)
            handle.seek(offset)
            raw_line = handle.read(length)
            if len(raw_line) != length or not raw_line.endswith(b"\n"):
                fail(f"Incomplete source summary at ordinal {ordinal}")
            stat["sha256"].update(raw_line)
            stat["size"] += length
            stat["count"] += 1
            stat["next_offset"] += length
            content = raw_line[:-1]
            content_hash = utility.sha256_bytes(content)
            if content_hash != source_row["summary_content_sha256"]:
                fail(f"Source Evidence Summary hash mismatch at ordinal {ordinal}")
            summary = json.loads(content)
            if (
                summary.get("EnsemblID") != source_row["EnsemblID"]
                or summary.get("universe_ordinal") != ordinal
                or summary.get("evidence_summary_id") != source_row["evidence_summary_id"]
            ):
                fail(f"Source Evidence Summary identity mismatch at ordinal {ordinal}")

            value = project_representation(summary, content_hash, rules, utility)
            rules.assert_no_prohibited_fields(value)
            schema_validator.validate_instance(value, schema, schema)
            reconcile_representation(summary, value, rules)
            encoded_content = utility.canonical_json(value).encode("utf-8")
            encoded_line = encoded_content + b"\n"
            output = output_stats[part]
            output_offset = output["size"]
            writers.writer(part).write(encoded_line)
            output["sha256"].update(encoded_line)
            output["size"] += len(encoded_line)
            output["count"] += 1
            output["first_ordinal"] = output["first_ordinal"] or ordinal
            output["last_ordinal"] = ordinal

            components = value["component_state_snapshot"]
            assignment = value["category_assignment"]
            true_count = sum(step["predicate_result"] for step in assignment["rule_trace"])
            total_components += len(components)
            total_trace_steps += len(assignment["rule_trace"])
            category_counts[assignment["category"]] += 1
            true_rule_counts[assignment["assigned_rule_id"]] += 1
            for component in components:
                state_counts[(component["component_id"], component["component_state"])] += 1
            all_limitations = list(value["limitation_identifiers"])
            for component in components:
                all_limitations.extend(component["limitation_identifiers"])
            if "|".join(all_limitations) != source_row["limitation_identifiers"]:
                fail(f"Limitation reconciliation mismatch at ordinal {ordinal}")

            index_rows.append(
                {
                    "universe_ordinal": ordinal,
                    "EnsemblID": value["EnsemblID"],
                    "prioritization_representation_id": value[
                        "prioritization_representation_id"
                    ],
                    "source_evidence_summary_id": summary["evidence_summary_id"],
                    "source_summary_content_sha256": content_hash,
                    "source_evidence_summary_schema_version": summary[
                        "evidence_summary_schema_version"
                    ],
                    "source_evidence_summary_version": summary[
                        "evidence_summary_version"
                    ],
                    "transcriptomic_component_version": COMPONENT_ORDER[0][1],
                    "transcriptomic_component_state": components[0]["component_state"],
                    "disease_association_component_version": COMPONENT_ORDER[1][1],
                    "disease_association_component_state": components[1]["component_state"],
                    "category": assignment["category"],
                    "assigned_rule_id": assignment["assigned_rule_id"],
                    "true_rule_count": true_count,
                    "rule_trace_step_count": len(assignment["rule_trace"]),
                    "limitation_identifiers": "|".join(all_limitations),
                    "partition_id": part,
                    "record_offset_bytes": output_offset,
                    "record_length_bytes": len(encoded_line),
                    "representation_content_sha256": utility.sha256_bytes(encoded_content),
                    "prioritization_output_schema_version": SCHEMA_VERSION,
                    "prioritization_representation_version": REPRESENTATION_VERSION,
                    "rule_catalog_version": RULE_CATALOG_VERSION,
                    "generator_version": GENERATOR_VERSION,
                }
            )
            if ordinal % 5000 == 0 or ordinal == EXPECTED_OBJECTS:
                print(f"{pass_name}: materialized {ordinal}/{EXPECTED_OBJECTS}", flush=True)

    if len(index_rows) != EXPECTED_OBJECTS or total_components != EXPECTED_COMPONENTS:
        fail(f"Identity/component reconciliation failed during {pass_name}")
    if total_trace_steps != EXPECTED_TRACE_STEPS:
        fail(f"Rule-trace reconciliation failed during {pass_name}")
    if sum(category_counts.values()) != EXPECTED_OBJECTS or sum(true_rule_counts.values()) != EXPECTED_OBJECTS:
        fail(f"Category/assigned-rule reconciliation failed during {pass_name}")
    for part, stat in source_stats.items():
        expected = source_partitions[part]
        if (
            stat["size"] != int(expected["artifact_size"])
            or stat["count"] != int(expected["summary_count"])
            or stat["sha256"].hexdigest() != expected["sha256"]
        ):
            fail(f"Frozen source-summary partition integrity failed during {pass_name}: {part}")
    if any(stat["count"] == 0 for stat in output_stats.values()):
        fail(f"One or more output partitions are empty during {pass_name}")
    normalized = {
        part: {
            "sha256": stat["sha256"].hexdigest(),
            "size": stat["size"],
            "count": stat["count"],
            "first_ordinal": stat["first_ordinal"],
            "last_ordinal": stat["last_ordinal"],
        }
        for part, stat in output_stats.items()
    }
    return {
        "partitions": normalized,
        "index_rows": index_rows,
        "category_counts": dict(category_counts),
        "true_rule_counts": dict(true_rule_counts),
        "state_counts": dict(state_counts),
        "totals": {
            "representations": len(index_rows),
            "components": total_components,
            "trace_steps": total_trace_steps,
        },
    }


def compare_passes(first: dict[str, Any], second: dict[str, Any]) -> None:
    for key in ("partitions", "index_rows", "category_counts", "true_rule_counts", "state_counts", "totals"):
        if first[key] != second[key]:
            fail(f"Independent prioritization regeneration mismatch: {key}")


def partition_set_hash(partitions: dict[str, dict[str, Any]], utility: Any) -> str:
    identity = [
        {
            "partition_id": part,
            "sha256": partitions[part]["sha256"],
            "artifact_size": partitions[part]["size"],
            "representation_count": partitions[part]["count"],
        }
        for part in sorted(partitions)
    ]
    return utility.sha256_bytes(utility.canonical_json(identity).encode("utf-8"))


def validate_external_artifact(root: Path, partitions: dict[str, dict[str, Any]], utility: Any) -> None:
    if not root.is_dir() or root.is_symlink():
        fail(f"External prioritization partition set unavailable or unsafe: {root}")
    for part, expected in partitions.items():
        path = root / "partitions" / part / "prioritization_records.jsonl"
        if not path.is_file() or path.is_symlink():
            fail(f"External prioritization partition unavailable or unsafe: {path}")
        if path.stat().st_size != expected["size"] or utility.sha256_file(path) != expected["sha256"]:
            fail(f"External prioritization partition integrity mismatch: {part}")


def promote_external_payload(
    pass_directory: Path,
    partitions: dict[str, dict[str, Any]],
    set_artifact_id: str,
    utility: Any,
) -> Path:
    final = EXTERNAL_ROOT / set_artifact_id
    if final.exists():
        validate_external_artifact(final, partitions, utility)
        return final
    stage = EXTERNAL_ROOT / f".{set_artifact_id}.staging"
    if stage.exists():
        fail(f"Unexpected pre-existing prioritization staging directory: {stage}")
    (stage / "partitions").mkdir(parents=True)
    for part in sorted(partitions):
        destination = stage / "partitions" / part
        destination.mkdir()
        (pass_directory / f"{part}.jsonl").replace(
            destination / "prioritization_records.jsonl"
        )
    stage.replace(final)
    validate_external_artifact(final, partitions, utility)
    return final


def build_partition_rows(
    partitions: dict[str, dict[str, Any]], set_artifact_id: str
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for part in sorted(partitions):
        stat = partitions[part]
        artifact_id = f"ART_PRZV01_{stat['sha256'][:24].upper()}"
        rows.append(
            {
                "partition_id": part,
                "partition_strategy_version": PARTITION_STRATEGY_VERSION,
                "partition_set_artifact_id": set_artifact_id,
                "artifact_id": artifact_id,
                "artifact_class": "CLASS_D_LARGE_DATA_OBJECT",
                "artifact_role": "TRANSPARENT_PRIORITIZATION_JSONL_PAYLOAD",
                "artifact_size": stat["size"],
                "sha256": stat["sha256"],
                "generator_version": GENERATOR_VERSION,
                "storage_reference_placeholder": (
                    "external+sha256://PENDING/luad-target-dossier/prioritization-v0.1/"
                    f"{set_artifact_id}/partitions/{part}/prioritization_records.jsonl"
                ),
                "storage_status": "LOCAL_CONTENT_ADDRESSED_STAGING_PENDING_DURABLE_REGISTRATION",
                "representation_count": stat["count"],
                "first_universe_ordinal": stat["first_ordinal"],
                "last_universe_ordinal": stat["last_ordinal"],
                "prioritization_output_schema_version": SCHEMA_VERSION,
                "prioritization_representation_version": REPRESENTATION_VERSION,
                "rule_catalog_version": RULE_CATALOG_VERSION,
                "validation_status": "PASS",
            }
        )
    return rows


def finalize_index_rows(
    rows: list[dict[str, Any]], partition_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    artifact_by_part = {row["partition_id"]: row["artifact_id"] for row in partition_rows}
    seen_entities: set[str] = set()
    seen_representations: set[str] = set()
    result: list[dict[str, Any]] = []
    for ordinal, row in enumerate(rows, 1):
        if row["universe_ordinal"] != ordinal:
            fail("Prioritization canonical order changed")
        if row["EnsemblID"] in seen_entities or row["prioritization_representation_id"] in seen_representations:
            fail("Duplicate prioritization identity")
        seen_entities.add(row["EnsemblID"])
        seen_representations.add(row["prioritization_representation_id"])
        item = dict(row)
        item["payload_artifact_id"] = artifact_by_part[item["partition_id"]]
        result.append(item)
    return result


def counter_to_nested(counter: dict[tuple[str, str], int]) -> dict[str, dict[str, int]]:
    nested: dict[str, dict[str, int]] = {}
    for (component_id, state), count in sorted(counter.items()):
        nested.setdefault(component_id, {})[state] = count
    return nested


def build_manifest(
    script_hash: str,
    index_bytes: bytes,
    partition_bytes: bytes,
    result: dict[str, Any],
    partition_rows: list[dict[str, Any]],
    set_hash: str,
    set_artifact_id: str,
    utility: Any,
) -> dict[str, Any]:
    total_size = sum(int(row["artifact_size"]) for row in partition_rows)
    release_id = utility.stable_id(
        "PRZREL",
        [
            FROZEN_INPUT_SHA256["outputs/evidence_summary_v0.1/summary_manifest.json"],
            FROZEN_INPUT_SHA256["schemas/prioritization_output_schema_v0.1.json"],
            FROZEN_INPUT_SHA256["docs/governance/prioritization_rule_catalog_v0.1.md"],
            set_hash,
            GENERATOR_VERSION,
        ],
    )
    tracking = "PROHIBITED" if total_size > GIT_PROHIBITED_THRESHOLD else "EXTERNALIZED_BY_ARTIFACT_DESIGN"
    return {
        "release_id": release_id,
        "release_status": "VALIDATED_LOCAL_STRUCTURAL_ROUTING_CANDIDATE",
        "prioritization_output_schema_version": SCHEMA_VERSION,
        "prioritization_representation_version": REPRESENTATION_VERSION,
        "rule_catalog_version": RULE_CATALOG_VERSION,
        "generator": {
            "relative_path": "analysis/35B_materialize_prioritization.py",
            "generator_version": GENERATOR_VERSION,
            "sha256": script_hash,
        },
        "immutable_key": "EnsemblID",
        "representation_identity_tuple": [
            "EnsemblID",
            "prioritization_output_schema_version",
            "prioritization_representation_version",
            "source_evidence_summary_id",
            "rule_catalog_version",
        ],
        "source_evidence_summary": {
            "evidence_summary_schema_version": SOURCE_SCHEMA_VERSION,
            "evidence_summary_version": SOURCE_SUMMARY_VERSION,
            "manifest_sha256": FROZEN_INPUT_SHA256[
                "outputs/evidence_summary_v0.1/summary_manifest.json"
            ],
            "index_sha256": FROZEN_INPUT_SHA256[
                "outputs/evidence_summary_v0.1/summary_index.csv"
            ],
            "partition_manifest_sha256": FROZEN_INPUT_SHA256[
                "outputs/evidence_summary_v0.1/partition_manifest.csv"
            ],
        },
        "rule_catalog": {
            "version": RULE_CATALOG_VERSION,
            "relative_path": "docs/governance/prioritization_rule_catalog_v0.1.md",
            "sha256": FROZEN_INPUT_SHA256[
                "docs/governance/prioritization_rule_catalog_v0.1.md"
            ],
            "fixed_trace_order": [1, 2, 3, 4],
        },
        "component_order": [item[0] for item in COMPONENT_ORDER],
        "component_versions": dict(COMPONENT_ORDER),
        "counts": {
            "representations": result["totals"]["representations"],
            "component_state_snapshots": result["totals"]["components"],
            "rule_trace_steps": result["totals"]["trace_steps"],
            "partitions": len(partition_rows),
        },
        "category_counts_non_ordinal_reconciliation_only": {
            category: result["category_counts"].get(category, 0)
            for category in (
                "CATEGORY_A",
                "CATEGORY_B",
                "CATEGORY_C",
                "CATEGORY_UNASSIGNED",
            )
        },
        "assigned_rule_counts_reconciliation_only": {
            rule_id: result["true_rule_counts"].get(rule_id, 0)
            for rule_id in RULE_IDS
        },
        "component_state_counts_reconciliation_only": counter_to_nested(
            result["state_counts"]
        ),
        "large_payload": {
            "artifact_id": set_artifact_id,
            "artifact_size": total_size,
            "partition_set_sha256": set_hash,
            "generator_version": GENERATOR_VERSION,
            "storage_reference_placeholder": (
                "external+sha256://PENDING/luad-target-dossier/prioritization-v0.1/"
                f"{set_artifact_id}/"
            ),
            "artifact_class": "CLASS_D_LARGE_DATA_OBJECT",
            "partition_count": len(partition_rows),
            "storage_status": "LOCAL_CONTENT_ADDRESSED_STAGING_PENDING_DURABLE_REGISTRATION",
            "ordinary_git_tracking": tracking,
        },
        "git_managed_artifacts": {
            "prioritization_index.csv": {
                "artifact_size": len(index_bytes),
                "sha256": utility.sha256_bytes(index_bytes),
                "row_count": EXPECTED_OBJECTS,
            },
            "partition_manifest.csv": {
                "artifact_size": len(partition_bytes),
                "sha256": utility.sha256_bytes(partition_bytes),
                "row_count": EXPECTED_PARTITIONS,
            },
        },
        "frozen_inputs": dict(sorted(FROZEN_INPUT_SHA256.items())),
        "determinism": {
            "independent_complete_regenerations": 2,
            "partition_bytes": "BYTE_IDENTICAL_BY_SIZE_AND_SHA256",
            "index_rows": "IDENTICAL",
            "network_access": "PROHIBITED_NOT_USED",
            "api_access": "PROHIBITED_NOT_USED",
            "runtime_ai_decisions": "PROHIBITED_NONE_USED",
            "gene_symbols": "NOT_USED",
            "external_knowledge": "NOT_USED",
            "randomness": "NOT_USED",
        },
        "non_ordinality": {
            "category_order": "NONE",
            "numeric_encoding": "PROHIBITED_NONE_PRESENT",
            "target_sorting": "PROHIBITED_NOT_PERFORMED",
            "target_selection": "PROHIBITED_NOT_PERFORMED",
        },
        "validation_status": "PASS",
    }


def build_report(manifest: dict[str, Any]) -> bytes:
    counts = manifest["counts"]
    categories = manifest["category_counts_non_ordinal_reconciliation_only"]
    payload = manifest["large_payload"]
    lines = [
        "# Transparent Prioritization Prototype v0.1 validation report",
        "",
        "**Task:** #035B  ",
        "**Validation status:** PASS  ",
        f"**Schema:** `{SCHEMA_VERSION}`  ",
        f"**Rule catalog:** `{RULE_CATALOG_VERSION}`",
        "",
        "## Structural materialization",
        "",
        f"- Representations: **{counts['representations']:,}**",
        f"- Preserved component-state snapshots: **{counts['component_state_snapshots']:,}**",
        f"- Rule-trace steps: **{counts['rule_trace_steps']:,}**",
        "- Every representation contains four rule evaluations in fixed order and exactly one true result.",
        "",
        "## Non-ordinal category reconciliation",
        "",
    ]
    for category in ("CATEGORY_A", "CATEGORY_B", "CATEGORY_C", "CATEGORY_UNASSIGNED"):
        lines.append(f"- `{category}`: {categories.get(category, 0):,}")
    lines.extend(
        [
            "",
            "These counts are structural reconciliation metadata. Categories have no order, weight, desirability, or scientific meaning beyond their frozen predicates.",
            "",
            "## Validation results",
            "",
            "| Validation | Result |",
            "|---|---|",
            "| Exactly 29,606 representations in canonical EnsemblID order | PASS |",
            "| One representation per frozen Evidence Summary | PASS |",
            "| Source summary identity and content SHA256 preserved | PASS |",
            "| Component IDs, versions, states, records, and limitations preserved | PASS |",
            "| All four rules evaluated in fixed order 1–4 | PASS |",
            "| Predicate IDs and boolean results reproduced | PASS |",
            "| Exactly one true rule and correct category for every object | PASS |",
            "| Recursive prohibited-field scan | PASS |",
            "| Schema validation for every object | PASS |",
            "| Every frozen source partition size and SHA256 reconciled twice | PASS |",
            "| Two independent complete regenerations | PASS — byte-identical |",
            "| Frozen repository input hashes unchanged | PASS |",
            "| Gene symbols or external knowledge | NOT USED |",
            "| Network/API access | PROHIBITED; NOT USED |",
            "| Runtime AI/LLM decisions | PROHIBITED; NONE USED |",
            "",
            "## Payload governance",
            "",
            f"- Artifact ID: `{payload['artifact_id']}`",
            f"- Payload size: **{payload['artifact_size']:,} bytes**",
            f"- Partition-set SHA256: `{payload['partition_set_sha256']}`",
            f"- Storage reference placeholder: `{payload['storage_reference_placeholder']}`",
            f"- Ordinary Git tracking: `{payload['ordinary_git_tracking']}`",
            "- The immutable JSONL partitions are held in content-addressed local staging outside the repository; durable registration remains pending.",
            "",
            "## Interpretation boundary",
            "",
            "This artifact is a deterministic structural routing representation. It is not a ranking, score, target selection, recommendation, biological interpretation, confidence estimate, probability estimate, or prediction of drug success.",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


def build_session_info(script_hash: str, set_artifact_id: str) -> bytes:
    return (
        "\n".join(
            [
                f"task_id={TASK_ID}",
                f"generator_version={GENERATOR_VERSION}",
                f"generator_sha256={script_hash}",
                f"python_implementation={platform.python_implementation()}",
                f"python_version={platform.python_version()}",
                f"platform_system={platform.system()}",
                f"platform_machine={platform.machine()}",
                "dependencies=PYTHON_STANDARD_LIBRARY_ONLY",
                "network_access=PROHIBITED_NOT_USED",
                "api_access=PROHIBITED_NOT_USED",
                "package_installation=PROHIBITED_NOT_PERFORMED",
                "runtime_ai_decisions=PROHIBITED_NONE_USED",
                "gene_symbols=NOT_USED",
                "external_knowledge=NOT_USED",
                "randomness=NOT_USED",
                "independent_complete_regenerations=2",
                "deterministic_regeneration=PASS",
                f"external_partition_set_artifact_id={set_artifact_id}",
                "external_storage_mode=CONTENT_ADDRESSED_LOCAL_STAGING_OUTSIDE_REPOSITORY",
                "durable_external_storage_registration=PENDING_SEPARATE_GOVERNANCE_ACTION",
                "",
            ]
        )
    ).encode("utf-8")


def write_bundle(bundle: dict[Path, bytes]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path, content in bundle.items():
        path.write_bytes(content)


def main() -> None:
    validate_working_tree_scope()
    validate_output_scope()
    utility = load_module(SOURCE_UTILITY_PATH, "task34b_utility")
    rules = load_module(RULE_MODULE_PATH, "task35a_rules")
    schema_validator = rules.load_source_validator()
    frozen_before = validate_frozen_inputs(utility)
    source_manifest, source_index, source_partitions = read_source_metadata(utility)
    del source_manifest
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    if (
        schema.get("$id") != rules.SCHEMA_ID
        or rules.SCHEMA_VERSION != SCHEMA_VERSION
        or rules.REPRESENTATION_VERSION != REPRESENTATION_VERSION
        or rules.RULE_CATALOG_VERSION != RULE_CATALOG_VERSION
    ):
        fail("Frozen Task #035A schema/rule identity mismatch")

    EXTERNAL_ROOT.mkdir(parents=True, exist_ok=True)
    if EXTERNAL_ROOT.is_symlink() or not EXTERNAL_ROOT.is_dir():
        fail(f"Unsafe prioritization external root: {EXTERNAL_ROOT}")
    work_root = Path(tempfile.mkdtemp(prefix=".task035b-", dir=EXTERNAL_ROOT))
    script_hash = utility.sha256_file(Path(__file__).resolve())
    try:
        pass_a = generate_pass(
            work_root / "pass_a",
            source_index,
            source_partitions,
            schema,
            rules,
            schema_validator,
            utility,
            "PASS_A",
        )
        pass_b = generate_pass(
            work_root / "pass_b",
            source_index,
            source_partitions,
            schema,
            rules,
            schema_validator,
            utility,
            "PASS_B",
        )
        compare_passes(pass_a, pass_b)
        set_hash = partition_set_hash(pass_a["partitions"], utility)
        set_artifact_id = f"ART_PRZV01_SET_{set_hash[:24].upper()}"
        external_final = promote_external_payload(
            work_root / "pass_a", pass_a["partitions"], set_artifact_id, utility
        )
        partition_rows = build_partition_rows(pass_a["partitions"], set_artifact_id)
        finalized_index = finalize_index_rows(pass_a["index_rows"], partition_rows)
        index_bytes = utility.read_csv_bytes(finalized_index, INDEX_COLUMNS)
        partition_bytes = utility.read_csv_bytes(partition_rows, PARTITION_COLUMNS)
        if len(index_bytes) > GIT_PROHIBITED_THRESHOLD or len(partition_bytes) > GIT_PROHIBITED_THRESHOLD:
            fail("Required Git-managed prioritization metadata exceeds 100 MB")

        manifest = build_manifest(
            script_hash,
            index_bytes,
            partition_bytes,
            pass_a,
            partition_rows,
            set_hash,
            set_artifact_id,
            utility,
        )
        bundle = {
            MANIFEST_PATH: utility.pretty_json_bytes(manifest),
            INDEX_PATH: index_bytes,
            PARTITION_MANIFEST_PATH: partition_bytes,
            REPORT_PATH: build_report(manifest),
            SESSION_PATH: build_session_info(script_hash, set_artifact_id),
        }
        second_index_bytes = utility.read_csv_bytes(
            finalize_index_rows(pass_b["index_rows"], partition_rows), INDEX_COLUMNS
        )
        second_manifest = build_manifest(
            script_hash,
            second_index_bytes,
            partition_bytes,
            pass_b,
            partition_rows,
            set_hash,
            set_artifact_id,
            utility,
        )
        second_bundle = {
            MANIFEST_PATH: utility.pretty_json_bytes(second_manifest),
            INDEX_PATH: second_index_bytes,
            PARTITION_MANIFEST_PATH: utility.read_csv_bytes(partition_rows, PARTITION_COLUMNS),
            REPORT_PATH: build_report(second_manifest),
            SESSION_PATH: build_session_info(script_hash, set_artifact_id),
        }
        if bundle != second_bundle:
            fail("Git-managed prioritization metadata regeneration is not byte-identical")
        write_bundle(bundle)
        validate_output_scope()
        if frozen_before != validate_frozen_inputs(utility):
            fail("A frozen input changed during Task #035B")
        validate_external_artifact(external_final, pass_a["partitions"], utility)
        validate_working_tree_scope()

        total_size = manifest["large_payload"]["artifact_size"]
        print("TASK_035B_VALIDATION=PASS")
        print(f"representations={pass_a['totals']['representations']}")
        print(f"component_state_snapshots={pass_a['totals']['components']}")
        print(f"rule_trace_steps={pass_a['totals']['trace_steps']}")
        for category in sorted(ALLOWED_CATEGORIES):
            print(f"{category}={pass_a['category_counts'].get(category, 0)}")
        print(f"external_payload_size={total_size}")
        print(f"external_partition_set={set_artifact_id}")
        print(f"external_local_staging_path={external_final}")
        print("independent_regenerations=2_BYTE_IDENTICAL")
        print("target_selection=NOT_PERFORMED")
        print("network_access=PROHIBITED_NOT_USED")
    finally:
        if work_root.exists():
            shutil.rmtree(work_root)


if __name__ == "__main__":
    main()
