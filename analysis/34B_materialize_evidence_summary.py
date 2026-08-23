#!/usr/bin/env python3
"""Materialize governed Evidence Summary v0.1 structural projections.

The only evidence-bearing input is the frozen Task #033B-2 Multi-component
Evidence Landscape. This program performs no retrieval, component rebuild,
target evaluation, scoring, ranking, prioritization, recommendation,
biological interpretation, or runtime AI/LLM decision.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import platform
import re
import shutil
import subprocess
import tempfile
from collections import Counter, OrderedDict
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any, BinaryIO


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "outputs/evidence_landscape_v0.2"
SOURCE_MANIFEST = SOURCE_DIR / "landscape_manifest.json"
SOURCE_INDEX = SOURCE_DIR / "landscape_index.csv"
SOURCE_PARTITIONS = SOURCE_DIR / "partition_manifest.csv"
SOURCE_EXTERNAL_ROOT = Path(
    "/private/tmp/luad-target-dossier-external-artifacts/evidence_landscape_v0.2"
)
SCHEMA_PATH = ROOT / "schemas/evidence_summary_schema_v0.1.json"
SCHEMA_GENERATOR_PATH = ROOT / "analysis/34A_define_evidence_summary_schema.py"

OUTPUT_DIR = ROOT / "outputs/evidence_summary_v0.1"
EXTERNAL_ROOT = Path(
    "/private/tmp/luad-target-dossier-external-artifacts/evidence_summary_v0.1"
)
MANIFEST_PATH = OUTPUT_DIR / "summary_manifest.json"
INDEX_PATH = OUTPUT_DIR / "summary_index.csv"
PARTITION_MANIFEST_PATH = OUTPUT_DIR / "partition_manifest.csv"
REPORT_PATH = OUTPUT_DIR / "validation_report.md"
SESSION_PATH = OUTPUT_DIR / "session_info.txt"

TASK_ID = "TASK_034B"
GENERATOR_VERSION = "EVIDENCE_SUMMARY_MATERIALIZER_V0.1"
SUMMARY_SCHEMA_VERSION = "EVIDENCE_SUMMARY_SCHEMA_V0.1"
SUMMARY_VERSION = "EVIDENCE_AGGREGATION_REPRESENTATION_V0.1"
SOURCE_SCHEMA_VERSION = "EVIDENCE_LANDSCAPE_SCHEMA_V0.2.1"
SOURCE_LANDSCAPE_VERSION = "MULTI_COMPONENT_EVIDENCE_LANDSCAPE_V0.2"
SOURCE_GENERATOR_VERSION = "MULTI_COMPONENT_EVIDENCE_LANDSCAPE_GENERATOR_V0.1"
PARTITION_STRATEGY_VERSION = "ENSEMBL_SHA256_PREFIX_2_V0.1"
EXPECTED_SUMMARIES = 29_606
EXPECTED_COMPONENTS = 59_212
EXPECTED_FEATURE_MISSINGNESS = 1_213_846
EXPECTED_DEPENDENCY_SUMMARIES = 2_517_118
EXPECTED_DEPENDENCY_RELATIONSHIPS = 3_430_043
EXPECTED_MULTI_DEPENDENCY_SUMMARIES = 912_925
EXPECTED_PARTITIONS = 256
GIT_PROHIBITED_THRESHOLD = 100_000_000

COMPONENT_ORDER = (
    ("COMP_TRANSCRIPTOMIC_EVIDENCE", "COMP_TRANSCRIPTOMIC_EVIDENCE_V0.1"),
    ("COMP_DISEASE_ASSOCIATION", "COMP_DISEASE_ASSOCIATION_V0.1"),
)
PROHIBITED_FIELDS = {
    "score",
    "ranking",
    "priority",
    "confidence",
    "overall_state",
    "recommendation",
    "target_quality",
    "evidence_strength",
}

FROZEN_INPUT_SHA256 = {
    "analysis/33B2_generate_evidence_landscape.py": "46d53c1fa4883de87a41b63556209ec5dc104ea3fdb32eabc6be38f359084800",
    "outputs/evidence_landscape_v0.2/landscape_manifest.json": "2c3853becd3895b0aaffb12be95205d910d1507dc1f2f8f36f7f150f651dba29",
    "outputs/evidence_landscape_v0.2/landscape_index.csv": "fbd7a3b50e70c41aa2ddbf0361390fde23d12bc320a881a4da168ad1d145d6c8",
    "outputs/evidence_landscape_v0.2/partition_manifest.csv": "2ccc38a384fe816d50b2c5d8f4c528a49727189434fe4be41e70355ff146cf8d",
    "outputs/evidence_landscape_v0.2/validation_report.md": "d5933862fe468ef4561188716abaee2de1cda16e06bcb1d39c1793f66cc29a8a",
    "outputs/evidence_landscape_v0.2/session_info.txt": "bb928646c3c7c3aba85f9faa127b4eb93b50455fa24165aa6b1a048bf1c658de",
    "analysis/34A_define_evidence_summary_schema.py": "0f401e377f40d1355b4bdba2ad197b5c405d906e02a2822c948addfefca5dec0",
    "docs/governance/evidence_aggregation_representation_specification_v0.1.md": "47bb0621b23090db5bb5f90f8a9c87ec56785e31957089c02573f1e1def40274",
    "docs/governance/evidence_summary_component_policy_v0.1.md": "c6e81a704060021baa951e25b78d1a2b355a656f824b27d6656e8af568049ee1",
    "docs/governance/evidence_summary_dependency_policy_v0.1.md": "efb423fc6ef1c918accdf70b6f38e10fd6c79e5c2455aca5ed0fb539d682d974",
    "docs/governance/evidence_summary_validation_requirements_v0.1.md": "e51e34743943cfc168572856fa5b1bf991261f899ced6b56057a9245f7f09c02",
    "schemas/evidence_summary_schema_v0.1.json": "0942733644e1333247293ca83f2eb14c13640939edf3727ea74d19d33990b366",
}

SOURCE_INDEX_COLUMNS = [
    "universe_ordinal",
    "EnsemblID",
    "landscape_id",
    "source_profile_id",
    "source_profile_content_sha256",
    "source_profile_schema_version",
    "source_profile_version",
    "source_evidence_snapshot_version",
    "transcriptomic_component_version",
    "transcriptomic_component_state",
    "disease_association_component_version",
    "disease_association_component_state",
    "component_count",
    "feature_reference_count",
    "provenance_reference_count",
    "dependency_relationship_count",
    "multi_dependency_reference_count",
    "limitation_ids",
    "partition_id",
    "payload_artifact_id",
    "record_offset_bytes",
    "record_length_bytes",
    "landscape_content_sha256",
    "landscape_schema_version",
    "landscape_version",
    "generator_version",
]
SOURCE_PARTITION_COLUMNS = [
    "partition_id",
    "partition_strategy_version",
    "partition_set_artifact_id",
    "payload_artifact_id",
    "artifact_class",
    "artifact_role",
    "immutable_identifier",
    "external_storage_reference",
    "storage_status",
    "landscape_count",
    "first_universe_ordinal",
    "last_universe_ordinal",
    "file_size_bytes",
    "sha256",
    "landscape_schema_version",
    "landscape_version",
    "generator_version",
    "validation_status",
]
INDEX_COLUMNS = [
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
    "summary_count",
    "first_universe_ordinal",
    "last_universe_ordinal",
    "evidence_summary_schema_version",
    "evidence_summary_version",
    "validation_status",
]

ALLOWED_WORKTREE_PATHS = {
    "analysis/34B_materialize_evidence_summary.py",
    *(f"outputs/evidence_summary_v0.1/{name}" for name in (
        "summary_manifest.json",
        "summary_index.csv",
        "partition_manifest.csv",
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
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode(
        "utf-8"
    )


def stable_id(prefix: str, value: Any, length: int = 32) -> str:
    return f"{prefix}_{sha256_bytes(canonical_json(value).encode('utf-8'))[:length].upper()}"


def partition_id(ensembl_id: str) -> str:
    return "p" + hashlib.sha256(ensembl_id.encode("utf-8")).hexdigest()[:2]


def read_csv_bytes(rows: list[dict[str, Any]], fields: list[str]) -> bytes:
    import io

    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fields})
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
    allowed = {MANIFEST_PATH, INDEX_PATH, PARTITION_MANIFEST_PATH, REPORT_PATH, SESSION_PATH}
    if OUTPUT_DIR.exists():
        unexpected = sorted(
            path.relative_to(ROOT).as_posix()
            for path in OUTPUT_DIR.rglob("*")
            if path.is_file() and path not in allowed
        )
        if unexpected:
            fail("Unexpected repository summary payload/output files: " + ", ".join(unexpected))


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


def load_schema_module() -> Any:
    spec = importlib.util.spec_from_file_location("task34a_schema", SCHEMA_GENERATOR_PATH)
    if spec is None or spec.loader is None:
        fail("Unable to load frozen Task #034A schema validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_source_metadata() -> tuple[
    dict[str, Any], list[dict[str, str]], dict[str, dict[str, str]]
]:
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    expected_manifest = {
        "validation_status": "PASS",
        "landscape_schema_version": SOURCE_SCHEMA_VERSION,
        "landscape_version": SOURCE_LANDSCAPE_VERSION,
    }
    for key, expected in expected_manifest.items():
        if manifest.get(key) != expected:
            fail(f"Frozen Task #033B-2 manifest mismatch: {key}")
    counts = manifest.get("counts", {})
    expected_counts = {
        "landscapes": EXPECTED_SUMMARIES,
        "components": EXPECTED_COMPONENTS,
        "feature_references": EXPECTED_FEATURE_MISSINGNESS,
        "provenance_references": EXPECTED_DEPENDENCY_SUMMARIES,
        "dependency_relationships": EXPECTED_DEPENDENCY_RELATIONSHIPS,
        "multi_dependency_references": EXPECTED_MULTI_DEPENDENCY_SUMMARIES,
        "partitions": EXPECTED_PARTITIONS,
    }
    if any(counts.get(key) != value for key, value in expected_counts.items()):
        fail("Frozen Task #033B-2 manifest reconciliation counts changed")
    if manifest.get("component_versions") != dict(COMPONENT_ORDER):
        fail("Frozen Task #033B-2 component versions changed")

    with SOURCE_INDEX.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != SOURCE_INDEX_COLUMNS:
            fail("Frozen landscape index columns changed")
        index_rows = list(reader)
    if len(index_rows) != EXPECTED_SUMMARIES:
        fail(f"Expected {EXPECTED_SUMMARIES} landscape rows, observed {len(index_rows)}")
    seen_entities: set[str] = set()
    for ordinal, row in enumerate(index_rows, 1):
        if int(row["universe_ordinal"]) != ordinal:
            fail(f"Landscape canonical order mismatch at ordinal {ordinal}")
        if row["EnsemblID"] in seen_entities:
            fail(f"Duplicate frozen landscape EnsemblID: {row['EnsemblID']}")
        if partition_id(row["EnsemblID"]) != row["partition_id"]:
            fail(f"Frozen landscape partition mismatch at ordinal {ordinal}")
        seen_entities.add(row["EnsemblID"])

    with SOURCE_PARTITIONS.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != SOURCE_PARTITION_COLUMNS:
            fail("Frozen landscape partition-manifest columns changed")
        partition_rows = list(reader)
    if len(partition_rows) != EXPECTED_PARTITIONS:
        fail("Frozen landscape partition count changed")
    partition_map = {row["partition_id"]: row for row in partition_rows}
    if len(partition_map) != EXPECTED_PARTITIONS:
        fail("Duplicate frozen landscape partition identity")
    partition_set_id = manifest.get("partition_set", {}).get("partition_set_artifact_id")
    expected_source_root = SOURCE_EXTERNAL_ROOT / str(partition_set_id)
    if not expected_source_root.is_dir() or expected_source_root.is_symlink():
        fail(f"Frozen external landscape payload is unavailable: {expected_source_root}")
    for part, row in partition_map.items():
        expected = {
            "partition_strategy_version": PARTITION_STRATEGY_VERSION,
            "partition_set_artifact_id": partition_set_id,
            "landscape_schema_version": SOURCE_SCHEMA_VERSION,
            "landscape_version": SOURCE_LANDSCAPE_VERSION,
            "generator_version": SOURCE_GENERATOR_VERSION,
            "validation_status": "PASS",
        }
        if any(row.get(key) != value for key, value in expected.items()):
            fail(f"Frozen landscape partition metadata mismatch: {part}")
        path = expected_source_root / "partitions" / part / "landscape_records.jsonl"
        if not path.is_file() or path.is_symlink():
            fail(f"Frozen landscape partition is unavailable or unsafe: {path}")
        if path.stat().st_size != int(row["file_size_bytes"]):
            fail(f"Frozen landscape partition size mismatch: {part}")
        row["_local_path"] = str(path)
    return manifest, index_rows, partition_map


def assert_no_prohibited_fields(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        forbidden = PROHIBITED_FIELDS.intersection(value)
        if forbidden:
            fail(f"Prohibited summary field(s) at {path}: {sorted(forbidden)}")
        for key, child in value.items():
            assert_no_prohibited_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            assert_no_prohibited_fields(child, f"{path}[{index}]")


def project_dependency(
    component_id: str,
    component_version: str,
    feature_id: str,
    provenance: dict[str, Any],
) -> dict[str, Any]:
    dependency = provenance.get("dependency_reference", {})
    relationships = dependency.get("dependency_relationships")
    artifact = provenance.get("artifact_reference", {})
    if not isinstance(relationships, list) or not relationships:
        fail("Source landscape dependency relationships are absent")
    projected_relationships = [
        {
            "relationship_type": relationship["relationship_type"],
            "dependency_level": relationship["dependency_level"],
        }
        for relationship in relationships
    ]
    return {
        "component_id": component_id,
        "component_version": component_version,
        "feature_id": feature_id,
        "evidence_record_id": provenance["evidence_record_id"],
        "source_id": provenance["source_id"],
        "dependency_id": dependency["dependency_id"],
        "dependency_relationships": projected_relationships,
        "artifact_reference": {
            "artifact_id": artifact["artifact_id"],
            "artifact_namespace": artifact["artifact_namespace"],
            "artifact_sha256": artifact["artifact_sha256"],
        },
    }


def project_component(source: dict[str, Any]) -> dict[str, Any]:
    component_id = source["component_id"]
    component_version = source["component_version"]
    source_record_id = source["source_component_reference"]["source_record_id"]
    feature_missingness: list[dict[str, Any]] = []
    dependency_summaries: list[dict[str, Any]] = []
    for feature in source["feature_references"]:
        feature_summary = {
            "feature_id": feature["feature_id"],
            "missingness_status": feature["missingness_status"],
            "source_component_record_id": feature["source_component_record_id"],
        }
        if "source_feature_value_sha256" in feature:
            feature_summary["source_feature_value_sha256"] = feature[
                "source_feature_value_sha256"
            ]
        feature_missingness.append(feature_summary)
        dependency_summaries.extend(
            project_dependency(component_id, component_version, feature["feature_id"], item)
            for item in feature["provenance_references"]
        )
    return {
        "component_id": component_id,
        "component_version": component_version,
        "component_state": source["state"],
        "source_component_record_id": source_record_id,
        "source_component_content_sha256": source["source_component_content_sha256"],
        "feature_missingness": feature_missingness,
        "dependency_summaries": dependency_summaries,
        "limitation_identifiers": [
            item["limitation_id"] for item in source["limitation_references"]
        ],
    }


def project_summary(landscape: dict[str, Any], source_content_hash: str) -> dict[str, Any]:
    identity = [
        landscape["EnsemblID"],
        SUMMARY_SCHEMA_VERSION,
        SUMMARY_VERSION,
        landscape["landscape_id"],
        landscape["landscape_schema_version"],
        landscape["landscape_version"],
    ]
    source_profile = landscape["source_profile_identity"]
    return {
        "EnsemblID": landscape["EnsemblID"],
        "universe_ordinal": landscape["universe_ordinal"],
        "evidence_summary_id": stable_id("SUM", identity),
        "evidence_summary_schema_version": SUMMARY_SCHEMA_VERSION,
        "evidence_summary_version": SUMMARY_VERSION,
        "summary_generator_version": GENERATOR_VERSION,
        "source_landscape_identity": {
            "landscape_id": landscape["landscape_id"],
            "landscape_schema_version": landscape["landscape_schema_version"],
            "landscape_version": landscape["landscape_version"],
            "source_profile_id": source_profile["source_profile_id"],
            "source_evidence_snapshot_version": source_profile[
                "source_evidence_snapshot_version"
            ],
            "source_landscape_generator_version": landscape["generator_version"],
            "landscape_content_sha256": source_content_hash,
        },
        "component_summaries": [project_component(item) for item in landscape["components"]],
        "limitation_identifiers": [
            item["limitation_id"] for item in landscape["limitation_references"]
        ],
    }


def reconcile_summary(landscape: dict[str, Any], summary: dict[str, Any]) -> dict[str, int]:
    if (
        summary["EnsemblID"] != landscape["EnsemblID"]
        or summary["universe_ordinal"] != landscape["universe_ordinal"]
        or summary["source_landscape_identity"]["landscape_id"]
        != landscape["landscape_id"]
    ):
        fail("Landscape-to-summary identity reconciliation failed")
    source_components = landscape["components"]
    projected_components = summary["component_summaries"]
    if len(source_components) != 2 or len(projected_components) != 2:
        fail("Summary component cardinality changed")
    feature_count = 0
    dependency_count = 0
    relationship_count = 0
    multi_count = 0
    for source_component, projected_component, expected in zip(
        source_components, projected_components, COMPONENT_ORDER, strict=True
    ):
        if (
            source_component["component_id"],
            source_component["component_version"],
        ) != expected:
            fail("Source component order or version changed")
        direct_fields = {
            "component_id": source_component["component_id"],
            "component_version": source_component["component_version"],
            "component_state": source_component["state"],
            "source_component_record_id": source_component["source_component_reference"][
                "source_record_id"
            ],
            "source_component_content_sha256": source_component[
                "source_component_content_sha256"
            ],
        }
        if any(projected_component[key] != value for key, value in direct_fields.items()):
            fail("Component identity, version, state, or lineage changed")
        expected_limitations = [
            item["limitation_id"] for item in source_component["limitation_references"]
        ]
        if projected_component["limitation_identifiers"] != expected_limitations:
            fail("Component limitation identifiers changed")
        source_features = source_component["feature_references"]
        projected_features = projected_component["feature_missingness"]
        if len(source_features) != len(projected_features):
            fail("Feature missingness cardinality changed")
        expected_dependencies: list[dict[str, Any]] = []
        for source_feature, projected_feature in zip(
            source_features, projected_features, strict=True
        ):
            expected_feature = {
                "feature_id": source_feature["feature_id"],
                "missingness_status": source_feature["missingness_status"],
                "source_component_record_id": source_feature["source_component_record_id"],
            }
            if "source_feature_value_sha256" in source_feature:
                expected_feature["source_feature_value_sha256"] = source_feature[
                    "source_feature_value_sha256"
                ]
            if projected_feature != expected_feature:
                fail("Feature identity, missingness, or value hash changed")
            feature_count += 1
            expected_dependencies.extend(
                project_dependency(
                    source_component["component_id"],
                    source_component["component_version"],
                    source_feature["feature_id"],
                    provenance,
                )
                for provenance in source_feature["provenance_references"]
            )
        if projected_component["dependency_summaries"] != expected_dependencies:
            fail("Dependency order, identity, relationships, or artifact lineage changed")
        seen_relationship_keys: set[tuple[str, str, str]] = set()
        for dependency in projected_component["dependency_summaries"]:
            key = (
                dependency["component_id"],
                dependency["feature_id"],
                dependency["evidence_record_id"],
            )
            if key in seen_relationship_keys:
                fail(f"Duplicate summary dependency relationship key: {key}")
            seen_relationship_keys.add(key)
            count = len(dependency["dependency_relationships"])
            dependency_count += 1
            relationship_count += count
            if count > 1:
                multi_count += 1
    expected_root_limitations = [
        item["limitation_id"] for item in landscape["limitation_references"]
    ]
    if summary["limitation_identifiers"] != expected_root_limitations:
        fail("Summary limitation identifiers changed")
    return {
        "features": feature_count,
        "dependencies": dependency_count,
        "relationships": relationship_count,
        "multi_dependencies": multi_count,
    }


class LRUReadPool(AbstractContextManager["LRUReadPool"]):
    def __init__(self, paths: dict[str, Path], max_open: int = 32) -> None:
        self.paths = paths
        self.max_open = max_open
        self.handles: OrderedDict[str, BinaryIO] = OrderedDict()

    def reader(self, part: str) -> BinaryIO:
        if part in self.handles:
            handle = self.handles.pop(part)
            self.handles[part] = handle
            return handle
        if len(self.handles) >= self.max_open:
            _, handle = self.handles.popitem(last=False)
            handle.close()
        handle = self.paths[part].open("rb", buffering=1024 * 1024)
        self.handles[part] = handle
        return handle

    def close(self) -> None:
        while self.handles:
            _, handle = self.handles.popitem(last=False)
            handle.close()

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()


class LRUWritePool(AbstractContextManager["LRUWritePool"]):
    def __init__(self, directory: Path, max_open: int = 32) -> None:
        self.directory = directory
        self.max_open = max_open
        self.handles: OrderedDict[str, BinaryIO] = OrderedDict()

    def writer(self, part: str) -> BinaryIO:
        if part in self.handles:
            handle = self.handles.pop(part)
            self.handles[part] = handle
            return handle
        if len(self.handles) >= self.max_open:
            _, handle = self.handles.popitem(last=False)
            handle.close()
        handle = (self.directory / f"{part}.jsonl").open(
            "ab", buffering=1024 * 1024
        )
        self.handles[part] = handle
        return handle

    def close(self) -> None:
        while self.handles:
            _, handle = self.handles.popitem(last=False)
            handle.close()

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()


def generate_pass(
    destination: Path,
    source_index: list[dict[str, str]],
    source_partitions: dict[str, dict[str, str]],
    schema: dict[str, Any],
    schema_module: Any,
    pass_name: str,
) -> dict[str, Any]:
    destination.mkdir(parents=True, exist_ok=False)
    output_stats: dict[str, dict[str, Any]] = {
        f"p{number:02x}": {
            "sha256": hashlib.sha256(),
            "size": 0,
            "count": 0,
            "first_ordinal": None,
            "last_ordinal": None,
        }
        for number in range(EXPECTED_PARTITIONS)
    }
    source_stats: dict[str, dict[str, Any]] = {
        part: {
            "sha256": hashlib.sha256(),
            "size": 0,
            "count": 0,
            "next_offset": 0,
        }
        for part in source_partitions
    }
    source_paths = {
        part: Path(row["_local_path"]) for part, row in source_partitions.items()
    }
    index_rows: list[dict[str, Any]] = []
    component_state_counts: Counter[tuple[str, str]] = Counter()
    missingness_counts: Counter[tuple[str, str]] = Counter()
    totals = {
        "summaries": 0,
        "components": 0,
        "features": 0,
        "dependencies": 0,
        "relationships": 0,
        "multi_dependencies": 0,
    }

    with LRUReadPool(source_paths) as readers, LRUWritePool(destination) as writers:
        for ordinal, source_row in enumerate(source_index, 1):
            part = source_row["partition_id"]
            source_stat = source_stats[part]
            offset = int(source_row["record_offset_bytes"])
            length = int(source_row["record_length_bytes"])
            if offset != source_stat["next_offset"]:
                fail(f"Source partition ordering/offset mismatch at ordinal {ordinal}")
            source_handle = readers.reader(part)
            source_handle.seek(offset)
            raw_line = source_handle.read(length)
            if len(raw_line) != length or not raw_line.endswith(b"\n"):
                fail(f"Incomplete source landscape record at ordinal {ordinal}")
            source_stat["sha256"].update(raw_line)
            source_stat["size"] += length
            source_stat["count"] += 1
            source_stat["next_offset"] += length
            content = raw_line[:-1]
            content_hash = sha256_bytes(content)
            if content_hash != source_row["landscape_content_sha256"]:
                fail(f"Source landscape content hash mismatch at ordinal {ordinal}")
            landscape = json.loads(content)
            if (
                landscape.get("EnsemblID") != source_row["EnsemblID"]
                or landscape.get("universe_ordinal") != ordinal
                or landscape.get("landscape_id") != source_row["landscape_id"]
            ):
                fail(f"Source landscape identity mismatch at ordinal {ordinal}")

            summary = project_summary(landscape, content_hash)
            assert_no_prohibited_fields(summary)
            schema_module.validate_instance(summary, schema, schema)
            schema_module.validate_artifact_namespace(summary)
            reconciliation = reconcile_summary(landscape, summary)

            encoded_content = canonical_json(summary).encode("utf-8")
            encoded_line = encoded_content + b"\n"
            output_stat = output_stats[part]
            output_offset = output_stat["size"]
            writers.writer(part).write(encoded_line)
            output_stat["sha256"].update(encoded_line)
            output_stat["size"] += len(encoded_line)
            output_stat["count"] += 1
            output_stat["first_ordinal"] = output_stat["first_ordinal"] or ordinal
            output_stat["last_ordinal"] = ordinal

            totals["summaries"] += 1
            totals["components"] += len(summary["component_summaries"])
            totals["features"] += reconciliation["features"]
            totals["dependencies"] += reconciliation["dependencies"]
            totals["relationships"] += reconciliation["relationships"]
            totals["multi_dependencies"] += reconciliation["multi_dependencies"]
            for component in summary["component_summaries"]:
                component_state_counts[
                    (component["component_id"], component["component_state"])
                ] += 1
                for feature in component["feature_missingness"]:
                    missingness_counts[
                        (component["component_id"], feature["missingness_status"])
                    ] += 1

            all_limitations = list(summary["limitation_identifiers"])
            for component in summary["component_summaries"]:
                all_limitations.extend(component["limitation_identifiers"])
            if "|".join(all_limitations) != source_row["limitation_ids"]:
                fail(f"Landscape-to-summary limitation reconciliation failed at {ordinal}")
            index_rows.append(
                {
                    "universe_ordinal": ordinal,
                    "EnsemblID": summary["EnsemblID"],
                    "evidence_summary_id": summary["evidence_summary_id"],
                    "source_landscape_id": landscape["landscape_id"],
                    "source_landscape_content_sha256": content_hash,
                    "source_landscape_schema_version": landscape[
                        "landscape_schema_version"
                    ],
                    "source_landscape_version": landscape["landscape_version"],
                    "transcriptomic_component_version": COMPONENT_ORDER[0][1],
                    "transcriptomic_component_state": summary["component_summaries"][0][
                        "component_state"
                    ],
                    "disease_association_component_version": COMPONENT_ORDER[1][1],
                    "disease_association_component_state": summary[
                        "component_summaries"
                    ][1]["component_state"],
                    "component_count": 2,
                    "feature_missingness_count": reconciliation["features"],
                    "dependency_summary_count": reconciliation["dependencies"],
                    "dependency_relationship_count": reconciliation["relationships"],
                    "multi_dependency_summary_count": reconciliation[
                        "multi_dependencies"
                    ],
                    "limitation_identifiers": "|".join(all_limitations),
                    "partition_id": part,
                    "record_offset_bytes": output_offset,
                    "record_length_bytes": len(encoded_line),
                    "summary_content_sha256": sha256_bytes(encoded_content),
                    "evidence_summary_schema_version": SUMMARY_SCHEMA_VERSION,
                    "evidence_summary_version": SUMMARY_VERSION,
                    "generator_version": GENERATOR_VERSION,
                }
            )
            if ordinal % 5000 == 0 or ordinal == EXPECTED_SUMMARIES:
                print(f"{pass_name}: materialized {ordinal}/{EXPECTED_SUMMARIES}", flush=True)

    expected_totals = {
        "summaries": EXPECTED_SUMMARIES,
        "components": EXPECTED_COMPONENTS,
        "features": EXPECTED_FEATURE_MISSINGNESS,
        "dependencies": EXPECTED_DEPENDENCY_SUMMARIES,
        "relationships": EXPECTED_DEPENDENCY_RELATIONSHIPS,
        "multi_dependencies": EXPECTED_MULTI_DEPENDENCY_SUMMARIES,
    }
    if totals != expected_totals:
        fail(f"Full-universe summary reconciliation failed during {pass_name}: {totals}")
    for part, source_stat in source_stats.items():
        expected = source_partitions[part]
        if (
            source_stat["size"] != int(expected["file_size_bytes"])
            or source_stat["count"] != int(expected["landscape_count"])
            or source_stat["sha256"].hexdigest() != expected["sha256"]
        ):
            fail(f"Frozen source partition integrity failed during {pass_name}: {part}")
    if any(stat["count"] == 0 for stat in output_stats.values()):
        fail(f"One or more deterministic summary partitions are empty during {pass_name}")

    normalized_output = {
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
        "partitions": normalized_output,
        "index_rows": index_rows,
        "totals": totals,
        "component_state_counts": dict(component_state_counts),
        "missingness_counts": dict(missingness_counts),
    }


def compare_passes(first: dict[str, Any], second: dict[str, Any]) -> None:
    for key in (
        "partitions",
        "index_rows",
        "totals",
        "component_state_counts",
        "missingness_counts",
    ):
        if first[key] != second[key]:
            fail(f"Independent summary regeneration mismatch: {key}")


def partition_set_hash(partitions: dict[str, dict[str, Any]]) -> str:
    identity = [
        {
            "partition_id": part,
            "sha256": partitions[part]["sha256"],
            "artifact_size": partitions[part]["size"],
            "summary_count": partitions[part]["count"],
        }
        for part in sorted(partitions)
    ]
    return sha256_bytes(canonical_json(identity).encode("utf-8"))


def external_final_path(set_artifact_id: str) -> Path:
    return EXTERNAL_ROOT / set_artifact_id


def validate_external_artifact(
    root: Path, partitions: dict[str, dict[str, Any]]
) -> None:
    if not root.is_dir() or root.is_symlink():
        fail(f"External summary partition set is unavailable or unsafe: {root}")
    for part, expected in partitions.items():
        path = root / "partitions" / part / "summary_records.jsonl"
        if not path.is_file() or path.is_symlink():
            fail(f"External summary partition is unavailable or unsafe: {path}")
        if path.stat().st_size != expected["size"] or sha256_file(path) != expected["sha256"]:
            fail(f"External summary partition integrity mismatch: {part}")


def promote_external_payload(
    pass_directory: Path,
    partitions: dict[str, dict[str, Any]],
    set_artifact_id: str,
) -> Path:
    final = external_final_path(set_artifact_id)
    if final.exists():
        validate_external_artifact(final, partitions)
        return final
    final.parent.mkdir(parents=True, exist_ok=True)
    stage = final.parent / f".{set_artifact_id}.staging"
    if stage.exists():
        fail(f"Unexpected pre-existing external staging directory: {stage}")
    (stage / "partitions").mkdir(parents=True)
    for part in sorted(partitions):
        destination = stage / "partitions" / part
        destination.mkdir()
        (pass_directory / f"{part}.jsonl").replace(
            destination / "summary_records.jsonl"
        )
    stage.replace(final)
    validate_external_artifact(final, partitions)
    return final


def build_partition_rows(
    partitions: dict[str, dict[str, Any]], set_artifact_id: str
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for part in sorted(partitions):
        stats = partitions[part]
        artifact_id = f"ART_SUMV01_{stats['sha256'][:24].upper()}"
        rows.append(
            {
                "partition_id": part,
                "partition_strategy_version": PARTITION_STRATEGY_VERSION,
                "partition_set_artifact_id": set_artifact_id,
                "artifact_id": artifact_id,
                "artifact_class": "CLASS_D_LARGE_DATA_OBJECT",
                "artifact_role": "EVIDENCE_SUMMARY_JSONL_PAYLOAD",
                "artifact_size": stats["size"],
                "sha256": stats["sha256"],
                "generator_version": GENERATOR_VERSION,
                "storage_reference_placeholder": (
                    "external+sha256://PENDING/luad-target-dossier/evidence-summary-v0.1/"
                    f"{set_artifact_id}/partitions/{part}/summary_records.jsonl"
                ),
                "storage_status": "LOCAL_CONTENT_ADDRESSED_STAGING_PENDING_DURABLE_REGISTRATION",
                "summary_count": stats["count"],
                "first_universe_ordinal": stats["first_ordinal"],
                "last_universe_ordinal": stats["last_ordinal"],
                "evidence_summary_schema_version": SUMMARY_SCHEMA_VERSION,
                "evidence_summary_version": SUMMARY_VERSION,
                "validation_status": "PASS",
            }
        )
    return rows


def finalize_index_rows(
    rows: list[dict[str, Any]], partition_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    artifact_by_partition = {
        row["partition_id"]: row["artifact_id"] for row in partition_rows
    }
    seen_entities: set[str] = set()
    seen_summaries: set[str] = set()
    finalized: list[dict[str, Any]] = []
    for ordinal, row in enumerate(rows, 1):
        if row["universe_ordinal"] != ordinal:
            fail("Summary canonical order changed")
        if row["EnsemblID"] in seen_entities or row["evidence_summary_id"] in seen_summaries:
            fail("Duplicate summary entity or summary identity")
        seen_entities.add(row["EnsemblID"])
        seen_summaries.add(row["evidence_summary_id"])
        item = dict(row)
        item["payload_artifact_id"] = artifact_by_partition[item["partition_id"]]
        finalized.append(item)
    return finalized


def counter_to_nested(counter: dict[tuple[str, str], int]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for (component_id, value), count in sorted(counter.items()):
        result.setdefault(component_id, {})[value] = count
    return result


def build_manifest(
    script_hash: str,
    schema_hash: str,
    index_bytes: bytes,
    partition_bytes: bytes,
    result: dict[str, Any],
    partition_rows: list[dict[str, Any]],
    set_hash: str,
    set_artifact_id: str,
) -> dict[str, Any]:
    total_size = sum(int(row["artifact_size"]) for row in partition_rows)
    release_id = stable_id(
        "SUMREL",
        [
            FROZEN_INPUT_SHA256[
                "outputs/evidence_landscape_v0.2/landscape_manifest.json"
            ],
            schema_hash,
            set_hash,
            GENERATOR_VERSION,
        ],
    )
    return {
        "release_id": release_id,
        "release_status": "VALIDATED_LOCAL_STRUCTURAL_CANDIDATE",
        "evidence_summary_schema_version": SUMMARY_SCHEMA_VERSION,
        "evidence_summary_version": SUMMARY_VERSION,
        "generator": {
            "relative_path": "analysis/34B_materialize_evidence_summary.py",
            "generator_version": GENERATOR_VERSION,
            "sha256": script_hash,
        },
        "immutable_key": "EnsemblID",
        "summary_identity_tuple": [
            "EnsemblID",
            "evidence_summary_schema_version",
            "evidence_summary_version",
            "source_landscape_id",
            "source_landscape_schema_version",
            "source_landscape_version",
        ],
        "source_landscape": {
            "landscape_schema_version": SOURCE_SCHEMA_VERSION,
            "landscape_version": SOURCE_LANDSCAPE_VERSION,
            "generator_version": SOURCE_GENERATOR_VERSION,
            "manifest_sha256": FROZEN_INPUT_SHA256[
                "outputs/evidence_landscape_v0.2/landscape_manifest.json"
            ],
            "index_sha256": FROZEN_INPUT_SHA256[
                "outputs/evidence_landscape_v0.2/landscape_index.csv"
            ],
            "partition_manifest_sha256": FROZEN_INPUT_SHA256[
                "outputs/evidence_landscape_v0.2/partition_manifest.csv"
            ],
        },
        "schema": {
            "relative_path": "schemas/evidence_summary_schema_v0.1.json",
            "sha256": schema_hash,
        },
        "component_order": [item[0] for item in COMPONENT_ORDER],
        "component_versions": dict(COMPONENT_ORDER),
        "counts": {
            "summaries": result["totals"]["summaries"],
            "components": result["totals"]["components"],
            "feature_missingness_references": result["totals"]["features"],
            "dependency_summaries": result["totals"]["dependencies"],
            "dependency_relationships": result["totals"]["relationships"],
            "multi_dependency_summaries": result["totals"]["multi_dependencies"],
            "partitions": len(partition_rows),
        },
        "component_state_counts": counter_to_nested(result["component_state_counts"]),
        "feature_missingness_counts": counter_to_nested(result["missingness_counts"]),
        "large_payload": {
            "artifact_id": set_artifact_id,
            "artifact_size": total_size,
            "partition_set_sha256": set_hash,
            "generator_version": GENERATOR_VERSION,
            "storage_reference_placeholder": (
                "external+sha256://PENDING/luad-target-dossier/evidence-summary-v0.1/"
                f"{set_artifact_id}/"
            ),
            "artifact_class": "CLASS_D_LARGE_DATA_OBJECT",
            "partition_count": len(partition_rows),
            "storage_status": "LOCAL_CONTENT_ADDRESSED_STAGING_PENDING_DURABLE_REGISTRATION",
            "ordinary_git_tracking": "PROHIBITED",
        },
        "git_managed_artifacts": {
            "summary_index.csv": {
                "artifact_size": len(index_bytes),
                "sha256": sha256_bytes(index_bytes),
                "row_count": EXPECTED_SUMMARIES,
            },
            "partition_manifest.csv": {
                "artifact_size": len(partition_bytes),
                "sha256": sha256_bytes(partition_bytes),
                "row_count": EXPECTED_PARTITIONS,
            },
        },
        "frozen_inputs": dict(sorted(FROZEN_INPUT_SHA256.items())),
        "determinism": {
            "independent_complete_regenerations": 2,
            "summary_partition_bytes": "BYTE_IDENTICAL_BY_SIZE_AND_SHA256",
            "summary_index_rows": "IDENTICAL",
            "network_access": "PROHIBITED_NOT_USED",
            "api_access": "PROHIBITED_NOT_USED",
            "runtime_ai_decisions": "PROHIBITED_NONE_USED",
            "randomness": "NOT_USED",
            "wall_clock_governed_values": "NOT_USED",
        },
        "prohibitions": [
            "NO_EVIDENCE_RETRIEVAL",
            "NO_COMPONENT_REBUILD",
            "NO_TARGET_EVALUATION",
            "NO_SCORING",
            "NO_RANKING",
            "NO_PRIORITIZATION",
            "NO_RECOMMENDATION",
            "NO_BIOLOGICAL_INTERPRETATION",
            "NO_RUNTIME_AI_DECISIONS",
        ],
        "validation_status": "PASS",
    }


def build_report(manifest: dict[str, Any]) -> bytes:
    counts = manifest["counts"]
    payload = manifest["large_payload"]
    lines = [
        "# Evidence Summary v0.1 validation report",
        "",
        "**Task:** #034B  ",
        "**Validation status:** PASS  ",
        f"**Schema:** `{SUMMARY_SCHEMA_VERSION}`  ",
        f"**Representation:** `{SUMMARY_VERSION}`",
        "",
        "## Structural materialization",
        "",
        f"- Evidence Summary objects: **{counts['summaries']:,}**",
        f"- Component summaries: **{counts['components']:,}**",
        f"- Feature-missingness references: **{counts['feature_missingness_references']:,}**",
        f"- Dependency summaries: **{counts['dependency_summaries']:,}**",
        f"- Ordered dependency relationships: **{counts['dependency_relationships']:,}**",
        f"- Multi-relationship dependency summaries: **{counts['multi_dependency_summaries']:,}**",
        "",
        "Every summary was projected from exactly one frozen Task #033B-2 landscape. No component or evidence record was rebuilt.",
        "",
        "## Validation results",
        "",
        "| Validation | Result |",
        "|---|---|",
        "| Exactly 29,606 summaries in canonical EnsemblID order | PASS |",
        "| One summary per source landscape | PASS |",
        "| Summary identity tuple and source-landscape content hash | PASS |",
        "| Exactly two ordered components and exact component versions | PASS |",
        "| Component states preserved | PASS |",
        "| All feature missingness values preserved | PASS |",
        "| Dependency identities and ordered relationship arrays preserved | PASS |",
        "| `SAME_SOURCE` and `SHARED_DATASET` retained separately | PASS |",
        "| Source-native artifact IDs, namespaces, and SHA256 hashes preserved | PASS |",
        "| Summary and component limitation identifiers preserved | PASS |",
        "| Evidence Summary schema validation for every object | PASS |",
        "| Recursive prohibited-field scan for every object | PASS |",
        "| Every frozen source partition size and SHA256 reconciled twice | PASS |",
        "| Two independent complete regenerations | PASS — byte-identical partitions and metadata |",
        "| Frozen repository input hashes unchanged | PASS |",
        "| Network/API access | PROHIBITED; NOT USED |",
        "| Runtime AI/LLM decisions | PROHIBITED; NONE USED |",
        "",
        "## Large artifact governance",
        "",
        f"- Partition-set artifact ID: `{payload['artifact_id']}`",
        f"- Aggregate payload size: **{payload['artifact_size']:,} bytes**",
        f"- Partition-set SHA256: `{payload['partition_set_sha256']}`",
        f"- Storage reference placeholder: `{payload['storage_reference_placeholder']}`",
        "- The immutable JSONL partitions are held in content-addressed local staging outside the repository.",
        "- Durable external storage registration remains pending; no payload file is present in ordinary Git.",
        "",
        "## Interpretation boundary",
        "",
        "This release candidate establishes structural representation, lineage, and deterministic reproducibility only. It contains no target evaluation, score, rank, priority, confidence measure, overall state, recommendation, target-quality field, evidence-strength field, biological interpretation, or therapeutic conclusion.",
        "",
    ]
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
                "randomness=NOT_USED",
                "wall_clock_governed_values=NOT_USED",
                "independent_complete_regenerations=2",
                "deterministic_regeneration=PASS",
                f"external_partition_set_artifact_id={set_artifact_id}",
                "external_storage_mode=CONTENT_ADDRESSED_LOCAL_STAGING_OUTSIDE_REPOSITORY",
                "durable_external_storage_registration=PENDING_SEPARATE_GOVERNANCE_ACTION",
                "",
            ]
        )
    ).encode("utf-8")


def write_metadata_bundle(bundle: dict[Path, bytes]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path, content in bundle.items():
        path.write_bytes(content)


def main() -> None:
    validate_working_tree_scope()
    validate_output_scope()
    frozen_before = validate_frozen_inputs()
    source_manifest, source_index, source_partitions = read_source_metadata()
    del source_manifest
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    schema_module = load_schema_module()
    if (
        schema.get("$id") != schema_module.SCHEMA_ID
        or schema_module.SCHEMA_VERSION != SUMMARY_SCHEMA_VERSION
        or schema_module.SUMMARY_VERSION != SUMMARY_VERSION
    ):
        fail("Frozen Task #034A schema identity mismatch")

    EXTERNAL_ROOT.mkdir(parents=True, exist_ok=True)
    if EXTERNAL_ROOT.is_symlink() or not EXTERNAL_ROOT.is_dir():
        fail(f"Unsafe summary external root: {EXTERNAL_ROOT}")
    work_root = Path(tempfile.mkdtemp(prefix=".task034b-", dir=EXTERNAL_ROOT))
    script_hash = sha256_file(Path(__file__).resolve())
    try:
        pass_a_dir = work_root / "pass_a"
        pass_b_dir = work_root / "pass_b"
        first = generate_pass(
            pass_a_dir, source_index, source_partitions, schema, schema_module, "PASS_A"
        )
        second = generate_pass(
            pass_b_dir, source_index, source_partitions, schema, schema_module, "PASS_B"
        )
        compare_passes(first, second)

        set_hash = partition_set_hash(first["partitions"])
        set_artifact_id = f"ART_SUMV01_SET_{set_hash[:24].upper()}"
        external_final = promote_external_payload(
            pass_a_dir, first["partitions"], set_artifact_id
        )
        partition_rows = build_partition_rows(first["partitions"], set_artifact_id)
        finalized_index = finalize_index_rows(first["index_rows"], partition_rows)
        index_bytes = read_csv_bytes(finalized_index, INDEX_COLUMNS)
        partition_bytes = read_csv_bytes(partition_rows, PARTITION_COLUMNS)
        total_payload_size = sum(item["size"] for item in first["partitions"].values())
        if total_payload_size <= GIT_PROHIBITED_THRESHOLD:
            fail("Summary payload did not cross the governed externalization threshold")
        if len(index_bytes) > GIT_PROHIBITED_THRESHOLD:
            fail("Required Git-managed summary index exceeds 100 MB")
        if len(partition_bytes) > GIT_PROHIBITED_THRESHOLD:
            fail("Required Git-managed summary partition manifest exceeds 100 MB")

        schema_hash = FROZEN_INPUT_SHA256["schemas/evidence_summary_schema_v0.1.json"]
        manifest = build_manifest(
            script_hash,
            schema_hash,
            index_bytes,
            partition_bytes,
            first,
            partition_rows,
            set_hash,
            set_artifact_id,
        )
        bundle = {
            MANIFEST_PATH: pretty_json_bytes(manifest),
            INDEX_PATH: index_bytes,
            PARTITION_MANIFEST_PATH: partition_bytes,
            REPORT_PATH: build_report(manifest),
            SESSION_PATH: build_session_info(script_hash, set_artifact_id),
        }
        second_index_bytes = read_csv_bytes(
            finalize_index_rows(second["index_rows"], partition_rows), INDEX_COLUMNS
        )
        second_manifest = build_manifest(
            script_hash,
            schema_hash,
            second_index_bytes,
            partition_bytes,
            second,
            partition_rows,
            set_hash,
            set_artifact_id,
        )
        second_bundle = {
            MANIFEST_PATH: pretty_json_bytes(second_manifest),
            INDEX_PATH: second_index_bytes,
            PARTITION_MANIFEST_PATH: read_csv_bytes(partition_rows, PARTITION_COLUMNS),
            REPORT_PATH: build_report(second_manifest),
            SESSION_PATH: build_session_info(script_hash, set_artifact_id),
        }
        if bundle != second_bundle:
            fail("Git-managed summary metadata regeneration is not byte-identical")
        write_metadata_bundle(bundle)
        validate_output_scope()
        if frozen_before != validate_frozen_inputs():
            fail("A frozen input changed during Task #034B")
        validate_external_artifact(external_final, first["partitions"])
        validate_working_tree_scope()

        print("TASK_034B_VALIDATION=PASS")
        print(f"summaries={first['totals']['summaries']}")
        print(f"components={first['totals']['components']}")
        print(f"feature_missingness_references={first['totals']['features']}")
        print(f"dependency_summaries={first['totals']['dependencies']}")
        print(f"dependency_relationships={first['totals']['relationships']}")
        print(f"multi_dependency_summaries={first['totals']['multi_dependencies']}")
        print(f"external_payload_size={total_payload_size}")
        print(f"external_partition_set={set_artifact_id}")
        print(f"external_local_staging_path={external_final}")
        print("independent_regenerations=2_BYTE_IDENTICAL")
        print("network_access=PROHIBITED_NOT_USED")
    finally:
        if work_root.exists():
            shutil.rmtree(work_root)


if __name__ == "__main__":
    main()

