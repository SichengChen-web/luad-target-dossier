#!/usr/bin/env python3
"""Integrate frozen transcriptomic and disease-association components.

This offline deterministic integration creates one structural Target Evidence
Profile per immutable EnsemblID. It copies component states, feature objects,
and every provenance relationship without modification or aggregation. It does
not score, rank, select, recommend, prioritize, or interpret targets.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import sqlite3
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator


EXPECTED_ENTITIES = 29_606
TRANSCRIPTOMIC_COMPONENT_ID = "COMP_TRANSCRIPTOMIC_EVIDENCE"
TRANSCRIPTOMIC_COMPONENT_VERSION = "COMP_TRANSCRIPTOMIC_EVIDENCE_V0.1"
DISEASE_COMPONENT_ID = "COMP_DISEASE_ASSOCIATION"
DISEASE_COMPONENT_VERSION = "COMP_DISEASE_ASSOCIATION_V0.1"
EXPECTED_TRANSCRIPTOMIC_FEATURES = 22
EXPECTED_DISEASE_FEATURES = 19
EXPECTED_TRANSCRIPTOMIC_PROVENANCE = 1_036_210
EXPECTED_DISEASE_PROVENANCE = 1_480_908

PROFILE_SCHEMA_VERSION = "TARGET_EVIDENCE_PROFILE_MULTICOMPONENT_SCHEMA_V0.1"
PROFILE_VERSION = "TARGET_EVIDENCE_PROFILE_MULTICOMPONENT_V0.1"
GENERATOR_VERSION = "MULTICOMPONENT_PROFILE_INTEGRATOR_V0.1"
COMPONENT_SET = [TRANSCRIPTOMIC_COMPONENT_ID, DISEASE_COMPONENT_ID]

STATE_VOCABULARY = {
    "OBSERVED",
    "PARTIAL",
    "CONFLICTING",
    "MISSING",
    "NOT_QUERIED",
}
MISSINGNESS_VOCABULARY = {
    "OBSERVED",
    "NOT_FOUND",
    "NOT_QUERIED",
    "NOT_APPLICABLE",
    "UNKNOWN",
}
FORBIDDEN_PROFILE_FIELDS = {
    "score",
    "scores",
    "overall_score",
    "rank",
    "ranking",
    "priority",
    "overall_confidence",
    "confidence",
    "evidence_strength",
    "target_quality",
    "target_selection",
    "recommendation",
    "biological_importance",
    "therapeutic_value",
    "therapeutic_recommendation",
    "biological_interpretation",
}

TASK030_ROOT = Path("outputs/profile_release_candidate_v0.1")
TASK031_ROOT = Path("outputs/evidence_landscape_v0.1")
DISEASE_ROOT = Path("outputs/disease_association_component_v0.1")

FROZEN_INPUT_SHA256 = {
    # Task #030 implementation and release-candidate metadata.
    "analysis/30_materialize_full_target_profiles.py": "273c3d70f9b9e38a69ff328795362c6447e38b8c713d9c245672e6e91c8b419c",
    "outputs/profile_release_candidate_v0.1/release_manifest.json": "d7c3203f4920f5e799dea8e3515cd15a01efba83693a4be7c554a4e5094625fe",
    "outputs/profile_release_candidate_v0.1/profile_schema_v0.1.json": "cc67e72658ba827b90b3b9d8f61cc866f004d36915369138b816b6f1bedaa34c",
    "outputs/profile_release_candidate_v0.1/profile_index.csv": "5f6307c603f8d4d9416877512c28b0329c369d03aea7d24bf6cc64176193ee15",
    "outputs/profile_release_candidate_v0.1/partition_manifest.csv": "7dac57596356f1fd38fdfeed4cd4c18b32ff755fc414e575afe8841bdf5219f8",
    "outputs/profile_release_candidate_v0.1/universe_manifest.csv": "e4b304eb5fde7690a1525b404f5d1a011837fd88f774b4dbb2838f2c81b9c1ab",
    "outputs/profile_release_candidate_v0.1/dependency_manifest.csv": "2990cb9d3162c8459fbe48e1c8be3fc14821f9ecd8fa9023b1b4da114f669ea9",
    "outputs/profile_release_candidate_v0.1/validation_results.csv": "4f4cc169130c79f89e694a774dbe2f2c6d580e0b77887d6e2ac5311bdb8bebd1",
    "outputs/profile_release_candidate_v0.1/validation_report.md": "58c2611d414c9b1420fd8b584ed8c211401b82dd55137055bb0da6cdbf00193c",
    # Task #031 implementation and evidence-landscape metadata.
    "analysis/31_build_evidence_landscape_representation.py": "bf0b9223268b7a0a2677af96c5e6db013d42c602b6e904ea896690a3e3966362",
    "outputs/evidence_landscape_v0.1/evidence_landscape_manifest.json": "8eb4cc48ad4e6bb206b297a95bf26d608cf52fdbe629f780e703c1561b61898c",
    "outputs/evidence_landscape_v0.1/evidence_landscape_schema_v0.1.json": "02632a07ee411cad7f924a9368ceb0ce2664bf39d83508cd07905b0864b1f6bb",
    "outputs/evidence_landscape_v0.1/evidence_landscape_index.csv": "47c653035f15879758df9811863a2d1e4eab5d62950a866e6dfefe8f93d5cf2e",
    "outputs/evidence_landscape_v0.1/landscape_partition_manifest.csv": "a5ab035790d5a1a235b2a9ac1b740224546cd90ade6f9155ec07a3d54ba2691c",
    "outputs/evidence_landscape_v0.1/evidence_landscape_validation_report.md": "397c29b98fcd2a3fc26d481ec1fddbb0aa294bffe02044b3d8de6df77045cf9f",
    # Task #028 profile governance.
    "docs/governance/target_evidence_profile_governance_v0.1.md": "1b8ab03bb758fd70d8a4bffb27ba1c7f97f83a52c20e75a0c18d9b0bd0941bbd",
    "docs/governance/profile_lifecycle_specification_v0.1.md": "346d46ce22b46513038ed7a62d951f1d3197432246e758bee84e56425137ccca",
    "docs/governance/profile_component_model_v0.1.md": "86ae5b8ce089f97770976b7b9f9b547a918e88c165cb7f983dd450178f8a7355",
    "docs/governance/profile_release_policy_v0.1.md": "f164be0352cd012583560b6ff5ef9850e43c59b49f4b9c4e28e3fe9138c77912",
    # Task #032B-2E disease-association component.
    "analysis/32B2E_materialize_disease_association_component.py": "fc98a1406c5ca91d8fb7296cf96b2b6c02b4855b6ad117af33f9bdd96bd83e5e",
    "outputs/disease_association_component_v0.1/component_manifest.json": "b2264956a13d5096b61cdb2b6981bcc80d7b7b3f1fe422b30f77c7cdc70e39f7",
    "outputs/disease_association_component_v0.1/component_index.csv": "7637c4da5f2286acb082b5382ae9f9bf50b08b2342d861e60ba388d729295c9e",
    "outputs/disease_association_component_v0.1/component_records.jsonl": "ecde83c5f3d28441c0e439b2ede6621f484b5b592a96370052911984868ad264",
    "outputs/disease_association_component_v0.1/component_validation_report.md": "99a8ae819143aa603018f8e967fbf7b07b5d08e96b7150011d3e8a7d869050bf",
    "outputs/disease_association_component_v0.1/session_info.txt": "5368d24e3297fb0e9d4ede608255a84ea86d28fbcde93684c0fe62e3f7bc6b05",
}

PROFILE_INDEX_FIELDS = [
    "universe_ordinal",
    "EnsemblID",
    "profile_id",
    "profile_schema_version",
    "profile_version",
    "evidence_snapshot_version",
    "generator_version",
    "component_set",
    "transcriptomic_component_state",
    "disease_association_component_state",
    "transcriptomic_source_profile_id",
    "disease_association_source_component_record_id",
    "feature_count",
    "provenance_relationship_count",
    "record_offset_bytes",
    "record_length_bytes",
    "profile_content_sha256",
]


class IntegrationError(RuntimeError):
    """Raised when a frozen-input or integration invariant fails."""


def fail(message: str) -> None:
    raise IntegrationError(message)


def find_repo_root() -> Path:
    root = Path(__file__).resolve().parent.parent
    if not (root / ".git").exists():
        fail("Repository root could not be resolved")
    return root


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_id(prefix: str, payload: Any, length: int = 32) -> str:
    serialized = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return f"{prefix}_{hashlib.sha256(serialized).hexdigest()[:length].upper()}"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_json_line(value: Any) -> bytes:
    return (canonical_json(value) + "\n").encode("utf-8")


def pretty_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode(
        "utf-8"
    )


def csv_bytes(rows: list[dict[str, Any]], fields: list[str]) -> bytes:
    import io

    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def write_bytes(path: Path, payload: bytes) -> str:
    with path.open("wb") as handle:
        handle.write(payload)
    return hashlib.sha256(payload).hexdigest()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def verify_frozen_top_level(repo: Path) -> dict[str, str]:
    observed: dict[str, str] = {}
    for relative, expected in FROZEN_INPUT_SHA256.items():
        path = repo / relative
        if not path.is_file():
            fail(f"Frozen input missing: {relative}")
        actual = sha256_file(path)
        if actual != expected:
            fail(f"Frozen input hash mismatch for {relative}: {actual} != {expected}")
        observed[relative] = actual
    return observed


def verify_partition_manifest(
    repo: Path,
    manifest_path: Path,
    allowed_roles: set[str],
    expected_rows: int,
) -> tuple[list[dict[str, str]], str, int]:
    rows = read_csv_rows(repo / manifest_path)
    if len(rows) != expected_rows:
        fail(f"Unexpected partition manifest length for {manifest_path}: {len(rows)}")
    set_digest = hashlib.sha256()
    total_size = 0
    for row in rows:
        if row["artifact_role"] not in allowed_roles:
            fail(f"Unexpected partition role: {row['artifact_role']}")
        relative = row["relative_path"]
        path = repo / relative
        if not path.is_file():
            fail(f"Partition artifact missing: {relative}")
        size = path.stat().st_size
        if size != int(row["file_size_bytes"]):
            fail(f"Partition size mismatch: {relative}")
        digest = sha256_file(path)
        if digest != row["sha256"]:
            fail(f"Partition hash mismatch: {relative}")
        set_digest.update(f"{relative}\t{size}\t{digest}\n".encode("utf-8"))
        total_size += size
    return rows, set_digest.hexdigest(), total_size


def recursive_keys(value: Any) -> Iterator[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from recursive_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from recursive_keys(child)


def validate_feature_objects(
    features: list[dict[str, Any]],
    expected_count: int,
    component_id: str,
) -> tuple[int, Counter[str]]:
    if len(features) != expected_count:
        fail(f"{component_id} feature count mismatch: {len(features)}")
    feature_ids: set[str] = set()
    provenance_count = 0
    missingness_counts: Counter[str] = Counter()
    for feature in features:
        feature_id = feature.get("feature_id")
        if not feature_id or feature_id in feature_ids:
            fail(f"Invalid or duplicate feature_id in {component_id}: {feature_id}")
        feature_ids.add(feature_id)
        missingness = feature.get("missingness_status")
        if missingness not in MISSINGNESS_VOCABULARY:
            fail(f"Invalid missingness in {component_id}/{feature_id}: {missingness}")
        missingness_counts[missingness] += 1
        links = feature.get("provenance_links")
        if not isinstance(links, list) or not links:
            fail(f"Feature lacks uncompressed provenance in {component_id}/{feature_id}")
        relationship_ids: set[str] = set()
        for link in links:
            evidence_record_id = link.get("evidence_record_id")
            if not evidence_record_id or evidence_record_id in relationship_ids:
                fail(f"Duplicate or absent evidence_record_id in {component_id}/{feature_id}")
            relationship_ids.add(evidence_record_id)
            for required in (
                "claim_id",
                "evidence_record_id",
                "source_id",
                "artifact_id",
                "dependency_id",
            ):
                if not link.get(required):
                    fail(f"Incomplete provenance {component_id}/{feature_id}/{required}")
            for inherited in ("extraction_rule_id", "extractor_version"):
                if not link.get(inherited) and not feature.get(inherited):
                    fail(
                        f"Incomplete provenance {component_id}/{feature_id}/{inherited}"
                    )
            provenance_count += 1
    return provenance_count, missingness_counts


def load_contracts(repo: Path) -> dict[str, Any]:
    task030 = json.loads((repo / TASK030_ROOT / "release_manifest.json").read_text())
    task031 = json.loads((repo / TASK031_ROOT / "evidence_landscape_manifest.json").read_text())
    disease = json.loads((repo / DISEASE_ROOT / "component_manifest.json").read_text())
    if task030["validation_status"] != "PASS":
        fail("Task #030 release candidate is not validated")
    if task031["validation"]["status"] != "PASS":
        fail("Task #031 evidence landscape is not validated")
    if disease["validation_status"] != "PASS":
        fail("Disease-association component is not validated")
    if task030["counts"]["profiles"] != EXPECTED_ENTITIES:
        fail("Task #030 entity count mismatch")
    if task031["counts"]["landscape_objects"] != EXPECTED_ENTITIES:
        fail("Task #031 entity count mismatch")
    if disease["entity_count"] != EXPECTED_ENTITIES:
        fail("Disease-association entity count mismatch")
    if task030["component_definition_versions"].get(TRANSCRIPTOMIC_COMPONENT_ID) != TRANSCRIPTOMIC_COMPONENT_VERSION:
        fail("Transcriptomic component version mismatch")
    if disease["component_id"] != DISEASE_COMPONENT_ID or disease["component_version"] != DISEASE_COMPONENT_VERSION:
        fail("Disease-association component identity mismatch")
    return {"task030": task030, "task031": task031, "disease": disease}


def compute_evidence_snapshot_version(contracts: dict[str, Any]) -> str:
    task030 = contracts["task030"]
    disease = contracts["disease"]
    identity = {
        "transcriptomic_evidence_snapshot_version": task030["evidence_snapshot_version"],
        "transcriptomic_release_candidate_id": task030["release_candidate_id"],
        "transcriptomic_profile_partition_set_sha256": task030["partition_sets"]["profile_partition_set_sha256"],
        "disease_association_source_snapshot_version": disease["version_axes"]["source_snapshot_version"],
        "disease_association_component_release_id": disease["component_release_id"],
        "disease_association_component_records_sha256": disease["output_artifacts"]["component_records.jsonl"]["sha256"],
    }
    return stable_id("EVIDENCE_SNAPSHOT_32C", identity)


def build_transcriptomic_store(
    repo: Path,
    connection: sqlite3.Connection,
    profile_partition_rows: list[dict[str, str]],
    task030_index: dict[str, dict[str, str]],
) -> tuple[Counter[str], int, Counter[str]]:
    connection.execute(
        "CREATE TABLE transcriptomic_components ("
        "EnsemblID TEXT PRIMARY KEY, component_json BLOB NOT NULL, "
        "source_profile_id TEXT NOT NULL, source_profile_content_sha256 TEXT NOT NULL, "
        "source_profile_artifact_id TEXT NOT NULL, partition_id TEXT NOT NULL, "
        "partition_artifact_id TEXT NOT NULL, partition_sha256 TEXT NOT NULL, "
        "source_schema_version TEXT NOT NULL, source_profile_version TEXT NOT NULL, "
        "source_evidence_snapshot_version TEXT NOT NULL, source_generator_version TEXT NOT NULL)"
    )
    state_counts: Counter[str] = Counter()
    missingness_counts: Counter[str] = Counter()
    provenance_count = 0
    payload_rows = sorted(
        (row for row in profile_partition_rows if row["artifact_role"] == "PROFILE_PAYLOAD"),
        key=lambda row: row["partition_id"],
    )
    for partition in payload_rows:
        path = repo / partition["relative_path"]
        partition_count = 0
        with path.open("rb") as handle:
            for raw_line in handle:
                partition_count += 1
                content = raw_line.rstrip(b"\n")
                profile = json.loads(content)
                ensembl_id = profile["EnsemblID"]
                source_index = task030_index.get(ensembl_id)
                if source_index is None:
                    fail(f"Task #030 profile is not indexed: {ensembl_id}")
                if source_index["partition_id"] != partition["partition_id"]:
                    fail(f"Task #030 partition mismatch for {ensembl_id}")
                content_hash = hashlib.sha256(content).hexdigest()
                if content_hash != source_index["profile_content_sha256"]:
                    fail(f"Task #030 profile content hash mismatch for {ensembl_id}")
                if profile["profile_id"] != source_index["profile_id"]:
                    fail(f"Task #030 profile identity mismatch for {ensembl_id}")
                if len(profile.get("components", [])) != 1:
                    fail(f"Task #030 profile does not contain one component: {ensembl_id}")
                component = profile["components"][0]
                if component["component_id"] != TRANSCRIPTOMIC_COMPONENT_ID:
                    fail(f"Unexpected Task #030 component for {ensembl_id}")
                if component["component_definition_version"] != TRANSCRIPTOMIC_COMPONENT_VERSION:
                    fail(f"Transcriptomic component version mismatch for {ensembl_id}")
                if component["state"] not in STATE_VOCABULARY:
                    fail(f"Invalid transcriptomic component state for {ensembl_id}")
                link_count, missing = validate_feature_objects(
                    component["features"], EXPECTED_TRANSCRIPTOMIC_FEATURES, TRANSCRIPTOMIC_COMPONENT_ID
                )
                provenance_count += link_count
                missingness_counts.update(missing)
                state_counts[component["state"]] += 1
                component_blob = canonical_json(component).encode("utf-8")
                try:
                    connection.execute(
                        "INSERT INTO transcriptomic_components VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                        (
                            ensembl_id,
                            component_blob,
                            profile["profile_id"],
                            content_hash,
                            source_index["profile_artifact_id"],
                            partition["partition_id"],
                            partition["artifact_id"],
                            partition["sha256"],
                            profile["schema_version"],
                            profile["profile_version"],
                            profile["evidence_snapshot_version"],
                            profile["generator_version"],
                        ),
                    )
                except sqlite3.IntegrityError:
                    fail(f"Duplicate transcriptomic EnsemblID: {ensembl_id}")
        if partition_count != int(partition["profile_count"]):
            fail(f"Task #030 partition count mismatch: {partition['partition_id']}")
    connection.commit()
    count = connection.execute("SELECT COUNT(*) FROM transcriptomic_components").fetchone()[0]
    if count != EXPECTED_ENTITIES:
        fail(f"Transcriptomic component store count mismatch: {count}")
    if provenance_count != EXPECTED_TRANSCRIPTOMIC_PROVENANCE:
        fail(f"Transcriptomic provenance count mismatch: {provenance_count}")
    return state_counts, provenance_count, missingness_counts


def transcriptomic_component_wrapper(
    stored: tuple[Any, ...],
) -> tuple[dict[str, Any], int, Counter[str]]:
    (
        component_blob,
        source_profile_id,
        source_profile_hash,
        source_profile_artifact_id,
        partition_id,
        partition_artifact_id,
        partition_sha256,
        source_schema_version,
        source_profile_version,
        source_evidence_snapshot_version,
        source_generator_version,
    ) = stored
    component = json.loads(component_blob)
    provenance_count, missingness = validate_feature_objects(
        component["features"], EXPECTED_TRANSCRIPTOMIC_FEATURES, TRANSCRIPTOMIC_COMPONENT_ID
    )
    source_component_hash = hashlib.sha256(component_blob).hexdigest()
    wrapper = {
        "component_definition_version": component["component_definition_version"],
        "component_id": component["component_id"],
        "component_version": component["component_definition_version"],
        "features": component["features"],
        "source_component_content_sha256": source_component_hash,
        "source_record_reference": {
            "container_artifact_id": partition_artifact_id,
            "container_artifact_sha256": partition_sha256,
            "partition_id": partition_id,
            "source_record_artifact_id": source_profile_artifact_id,
            "source_record_id": source_profile_id,
            "source_record_sha256": source_profile_hash,
        },
        "source_state_rule_metadata": {
            "state_rule_id": component["state_rule_id"],
            "state_rule_review_status": component["state_rule_review_status"],
            "state_rule_version": component["state_rule_version"],
        },
        "state": component["state"],
        "version_axes": {
            "source_evidence_snapshot_version": source_evidence_snapshot_version,
            "source_generator_version": source_generator_version,
            "source_profile_schema_version": source_schema_version,
            "source_profile_version": source_profile_version,
        },
    }
    return wrapper, provenance_count, missingness


def disease_component_wrapper(
    record: dict[str, Any],
    index_row: dict[str, str],
    disease_manifest: dict[str, Any],
) -> tuple[dict[str, Any], int, Counter[str]]:
    if record["component_id"] != DISEASE_COMPONENT_ID:
        fail(f"Unexpected disease component for {record.get('EnsemblID')}")
    if record["component_version"] != DISEASE_COMPONENT_VERSION:
        fail(f"Disease component version mismatch for {record['EnsemblID']}")
    if record["component_state"] not in STATE_VOCABULARY:
        fail(f"Invalid disease component state for {record['EnsemblID']}")
    provenance_count, missingness = validate_feature_objects(
        record["features"], EXPECTED_DISEASE_FEATURES, DISEASE_COMPONENT_ID
    )
    wrapper = {
        "component_definition_version": record["component_definition_version"],
        "component_id": record["component_id"],
        "component_version": record["component_version"],
        "features": record["features"],
        "source_component_content_sha256": hashlib.sha256(
            canonical_json(record).encode("utf-8")
        ).hexdigest(),
        "source_record_reference": {
            "container_artifact_id": "ART_DISEASE_ASSOCIATION_COMPONENT_RECORDS_V0_1",
            "container_artifact_sha256": disease_manifest["output_artifacts"]["component_records.jsonl"]["sha256"],
            "source_record_id": record["component_record_id"],
            "source_record_sha256": index_row["component_record_sha256"],
        },
        "source_state_rule_metadata": {
            "state_rule_version": record["state_rule_version"],
        },
        "state": record["component_state"],
        "version_axes": {
            "component_schema_version": record["component_schema_version"],
            "extractor_version": record["extractor_version"],
            "feature_generator_version": record["feature_generator_version"],
            "feature_schema_version": record["feature_schema_version"],
            "source_component_generator_version": record["generator_version"],
            "source_snapshot_version": record["source_snapshot_version"],
        },
    }
    return wrapper, provenance_count, missingness


def profile_id(ensembl_id: str, evidence_snapshot_version: str) -> str:
    return stable_id(
        "PRF_32C",
        {
            "EnsemblID": ensembl_id,
            "profile_schema_version": PROFILE_SCHEMA_VERSION,
            "profile_version": PROFILE_VERSION,
            "evidence_snapshot_version": evidence_snapshot_version,
        },
    )


@dataclass
class IntegrationAudit:
    entity_count: int = 0
    feature_count: int = 0
    provenance_count: int = 0
    component_count: int = 0
    transcriptomic_states: Counter[str] = field(default_factory=Counter)
    disease_states: Counter[str] = field(default_factory=Counter)
    joint_states: Counter[str] = field(default_factory=Counter)
    transcriptomic_missingness: Counter[str] = field(default_factory=Counter)
    disease_missingness: Counter[str] = field(default_factory=Counter)
    ensembl_ids: set[str] = field(default_factory=set)
    profile_ids: set[str] = field(default_factory=set)


def iter_integrated_profiles(
    repo: Path,
    connection: sqlite3.Connection,
    task030_index_rows: list[dict[str, str]],
    landscape_index_rows: list[dict[str, str]],
    disease_manifest: dict[str, Any],
    evidence_snapshot_version: str,
    audit: IntegrationAudit,
) -> Iterator[tuple[int, dict[str, Any], bytes, int]]:
    if len(task030_index_rows) != EXPECTED_ENTITIES:
        fail("Task #030 index cardinality mismatch")
    if len(landscape_index_rows) != EXPECTED_ENTITIES:
        fail("Task #031 index cardinality mismatch")
    disease_index_path = repo / DISEASE_ROOT / "component_index.csv"
    disease_records_path = repo / DISEASE_ROOT / "component_records.jsonl"
    with disease_index_path.open(newline="", encoding="utf-8") as disease_index_handle, disease_records_path.open("rb") as disease_records_handle:
        disease_index_reader = csv.DictReader(disease_index_handle)
        for ordinal, (task030_index, landscape_index, disease_index, disease_line) in enumerate(
            zip(task030_index_rows, landscape_index_rows, disease_index_reader, disease_records_handle, strict=True),
            start=1,
        ):
            ensembl_id = task030_index["EnsemblID"]
            if int(task030_index["universe_ordinal"]) != ordinal:
                fail(f"Task #030 canonical order mismatch at {ordinal}")
            if landscape_index["EnsemblID"] != ensembl_id or int(landscape_index["universe_ordinal"]) != ordinal:
                fail(f"Task #031 canonical order mismatch at {ordinal}")
            if disease_index["EnsemblID"] != ensembl_id or int(disease_index["universe_ordinal"]) != ordinal:
                fail(f"Disease component canonical order mismatch at {ordinal}")
            if ensembl_id in audit.ensembl_ids:
                fail(f"Duplicate integrated EnsemblID: {ensembl_id}")
            audit.ensembl_ids.add(ensembl_id)

            stored = connection.execute(
                "SELECT component_json, source_profile_id, source_profile_content_sha256, "
                "source_profile_artifact_id, partition_id, partition_artifact_id, "
                "partition_sha256, source_schema_version, source_profile_version, "
                "source_evidence_snapshot_version, source_generator_version "
                "FROM transcriptomic_components WHERE EnsemblID=?",
                (ensembl_id,),
            ).fetchone()
            if stored is None:
                fail(f"Transcriptomic component unavailable for {ensembl_id}")
            transcriptomic, tx_provenance, tx_missingness = transcriptomic_component_wrapper(stored)
            if transcriptomic["state"] != landscape_index["component_state"]:
                fail(f"Task #031 state differs from Task #030 for {ensembl_id}")
            if landscape_index["component_id"] != TRANSCRIPTOMIC_COMPONENT_ID:
                fail(f"Task #031 component identity mismatch for {ensembl_id}")
            if landscape_index["source_profile_id"] != task030_index["profile_id"]:
                fail(f"Task #031 profile reference mismatch for {ensembl_id}")
            if landscape_index["source_profile_content_sha256"] != task030_index["profile_content_sha256"]:
                fail(f"Task #031 profile hash reference mismatch for {ensembl_id}")
            if int(landscape_index["dependency_reference_count"]) != tx_provenance:
                fail(f"Task #031 dependency representation count mismatch for {ensembl_id}")

            disease_line_hash = hashlib.sha256(disease_line).hexdigest()
            if disease_line_hash != disease_index["component_record_sha256"]:
                fail(f"Disease component record hash mismatch for {ensembl_id}")
            if len(disease_line) != int(disease_index["record_length_bytes"]):
                fail(f"Disease component record length mismatch for {ensembl_id}")
            disease_record = json.loads(disease_line)
            if disease_record["EnsemblID"] != ensembl_id:
                fail(f"Disease component identity mismatch for {ensembl_id}")
            disease, da_provenance, da_missingness = disease_component_wrapper(
                disease_record, disease_index, disease_manifest
            )

            integrated_profile_id = profile_id(ensembl_id, evidence_snapshot_version)
            if integrated_profile_id in audit.profile_ids:
                fail(f"Duplicate integrated profile identity: {integrated_profile_id}")
            audit.profile_ids.add(integrated_profile_id)
            profile = {
                "EnsemblID": ensembl_id,
                "components": [transcriptomic, disease],
                "evidence_snapshot_version": evidence_snapshot_version,
                "generator_version": GENERATOR_VERSION,
                "profile_id": integrated_profile_id,
                "profile_schema_version": PROFILE_SCHEMA_VERSION,
                "profile_version": PROFILE_VERSION,
                "universe_ordinal": ordinal,
            }
            if set(recursive_keys(profile)) & FORBIDDEN_PROFILE_FIELDS:
                fail(f"Forbidden profile field detected for {ensembl_id}")

            total_provenance = tx_provenance + da_provenance
            audit.entity_count += 1
            audit.component_count += 2
            audit.feature_count += len(transcriptomic["features"]) + len(disease["features"])
            audit.provenance_count += total_provenance
            audit.transcriptomic_states[transcriptomic["state"]] += 1
            audit.disease_states[disease["state"]] += 1
            audit.joint_states[f"{transcriptomic['state']}|{disease['state']}"] += 1
            audit.transcriptomic_missingness.update(tx_missingness)
            audit.disease_missingness.update(da_missingness)
            yield ordinal, profile, canonical_json_line(profile), total_provenance


def validate_audit(
    audit: IntegrationAudit,
    contracts: dict[str, Any],
) -> None:
    if audit.entity_count != EXPECTED_ENTITIES or len(audit.ensembl_ids) != EXPECTED_ENTITIES:
        fail("Integrated entity identity validation failed")
    if len(audit.profile_ids) != EXPECTED_ENTITIES:
        fail("Integrated profile identity validation failed")
    if audit.component_count != EXPECTED_ENTITIES * 2:
        fail("Integrated component count mismatch")
    if audit.feature_count != EXPECTED_ENTITIES * (
        EXPECTED_TRANSCRIPTOMIC_FEATURES + EXPECTED_DISEASE_FEATURES
    ):
        fail("Integrated feature count mismatch")
    if audit.provenance_count != EXPECTED_TRANSCRIPTOMIC_PROVENANCE + EXPECTED_DISEASE_PROVENANCE:
        fail("Integrated provenance count mismatch")
    expected_tx_states = contracts["task031"]["component_state_counts"]
    expected_tx_nonzero = {key: value for key, value in expected_tx_states.items() if value}
    if dict(sorted(audit.transcriptomic_states.items())) != dict(sorted(expected_tx_nonzero.items())):
        fail("Transcriptomic component state fidelity failed")
    if dict(sorted(audit.disease_states.items())) != dict(
        sorted(contracts["disease"]["state_counts"].items())
    ):
        fail("Disease component state fidelity failed")
    if set(audit.transcriptomic_states) - STATE_VOCABULARY or set(audit.disease_states) - STATE_VOCABULARY:
        fail("Uncontrolled component state materialized")
    if set(audit.transcriptomic_missingness) - MISSINGNESS_VOCABULARY:
        fail("Uncontrolled transcriptomic feature missingness materialized")
    if set(audit.disease_missingness) - MISSINGNESS_VOCABULARY:
        fail("Uncontrolled disease feature missingness materialized")


def materialize_profiles(
    repo: Path,
    output_path: Path,
    connection: sqlite3.Connection,
    task030_index_rows: list[dict[str, str]],
    landscape_index_rows: list[dict[str, str]],
    contracts: dict[str, Any],
    evidence_snapshot_version: str,
) -> tuple[list[dict[str, Any]], IntegrationAudit, str, int]:
    audit = IntegrationAudit()
    index_rows: list[dict[str, Any]] = []
    digest = hashlib.sha256()
    offset = 0
    with output_path.open("wb") as output:
        for ordinal, profile, payload, provenance_count in iter_integrated_profiles(
            repo,
            connection,
            task030_index_rows,
            landscape_index_rows,
            contracts["disease"],
            evidence_snapshot_version,
            audit,
        ):
            output.write(payload)
            digest.update(payload)
            index_rows.append(
                {
                    "universe_ordinal": ordinal,
                    "EnsemblID": profile["EnsemblID"],
                    "profile_id": profile["profile_id"],
                    "profile_schema_version": PROFILE_SCHEMA_VERSION,
                    "profile_version": PROFILE_VERSION,
                    "evidence_snapshot_version": evidence_snapshot_version,
                    "generator_version": GENERATOR_VERSION,
                    "component_set": "|".join(COMPONENT_SET),
                    "transcriptomic_component_state": profile["components"][0]["state"],
                    "disease_association_component_state": profile["components"][1]["state"],
                    "transcriptomic_source_profile_id": profile["components"][0]["source_record_reference"]["source_record_id"],
                    "disease_association_source_component_record_id": profile["components"][1]["source_record_reference"]["source_record_id"],
                    "feature_count": sum(len(component["features"]) for component in profile["components"]),
                    "provenance_relationship_count": provenance_count,
                    "record_offset_bytes": offset,
                    "record_length_bytes": len(payload),
                    "profile_content_sha256": hashlib.sha256(payload[:-1]).hexdigest(),
                }
            )
            offset += len(payload)
    return index_rows, audit, digest.hexdigest(), offset


def deterministic_regeneration(
    repo: Path,
    output_path: Path,
    expected_index_payload: bytes,
    connection: sqlite3.Connection,
    task030_index_rows: list[dict[str, str]],
    landscape_index_rows: list[dict[str, str]],
    contracts: dict[str, Any],
    evidence_snapshot_version: str,
) -> tuple[IntegrationAudit, str]:
    audit = IntegrationAudit()
    regenerated_index: list[dict[str, Any]] = []
    digest = hashlib.sha256()
    offset = 0
    with output_path.open("rb") as frozen:
        for ordinal, profile, payload, provenance_count in iter_integrated_profiles(
            repo,
            connection,
            task030_index_rows,
            landscape_index_rows,
            contracts["disease"],
            evidence_snapshot_version,
            audit,
        ):
            if frozen.readline() != payload:
                fail(f"Non-deterministic profile at ordinal {ordinal}")
            digest.update(payload)
            regenerated_index.append(
                {
                    "universe_ordinal": ordinal,
                    "EnsemblID": profile["EnsemblID"],
                    "profile_id": profile["profile_id"],
                    "profile_schema_version": PROFILE_SCHEMA_VERSION,
                    "profile_version": PROFILE_VERSION,
                    "evidence_snapshot_version": evidence_snapshot_version,
                    "generator_version": GENERATOR_VERSION,
                    "component_set": "|".join(COMPONENT_SET),
                    "transcriptomic_component_state": profile["components"][0]["state"],
                    "disease_association_component_state": profile["components"][1]["state"],
                    "transcriptomic_source_profile_id": profile["components"][0]["source_record_reference"]["source_record_id"],
                    "disease_association_source_component_record_id": profile["components"][1]["source_record_reference"]["source_record_id"],
                    "feature_count": sum(len(component["features"]) for component in profile["components"]),
                    "provenance_relationship_count": provenance_count,
                    "record_offset_bytes": offset,
                    "record_length_bytes": len(payload),
                    "profile_content_sha256": hashlib.sha256(payload[:-1]).hexdigest(),
                }
            )
            offset += len(payload)
        if frozen.read(1):
            fail("Integrated profile artifact has trailing bytes")
    if csv_bytes(regenerated_index, PROFILE_INDEX_FIELDS) != expected_index_payload:
        fail("Integrated profile index is not byte-identically reproducible")
    return audit, digest.hexdigest()


def validation_report(
    audit: IntegrationAudit,
    profile_hash: str,
    index_hash: str,
    profile_size: int,
    frozen_count: int,
    partition_file_count: int,
    checks: list[tuple[str, bool, str]],
    evidence_snapshot_version: str,
) -> str:
    check_lines = "\n".join(
        f"- {'PASS' if passed else 'FAIL'} — `{name}`: {detail}"
        for name, passed, detail in checks
    )
    tx_states = "\n".join(
        f"- `{state}`: {audit.transcriptomic_states.get(state, 0):,}"
        for state in ("OBSERVED", "PARTIAL", "CONFLICTING", "MISSING", "NOT_QUERIED")
    )
    da_states = "\n".join(
        f"- `{state}`: {audit.disease_states.get(state, 0):,}"
        for state in ("OBSERVED", "PARTIAL", "CONFLICTING", "MISSING", "NOT_QUERIED")
    )
    return f"""# Multi-component Evidence Profile Integration Validation Report

**Task:** #032C  
**Validation status:** **PASS**  
**Profile version:** `{PROFILE_VERSION}`

## Integrated representation

- Immutable profiles: {audit.entity_count:,}
- Components per profile: 2
- Component representations: {audit.component_count:,}
- Feature references: {audit.feature_count:,}
- Uncompressed provenance relationships: {audit.provenance_count:,}
- Profile-record bytes: {profile_size:,}
- Profile-record SHA256: `{profile_hash}`
- Profile-index SHA256: `{index_hash}`
- Evidence snapshot version: `{evidence_snapshot_version}`

No overall component state, evidence score, confidence, rank, priority, or target evaluation is generated.

## Transcriptomic component states

{tx_states}

## Disease-association component states

{da_states}

States remain independent structural labels from their source components. `MISSING` is not negative evidence and `NOT_QUERIED` is not biological absence.

## Validation checks

{check_lines}

## Lineage boundary

Every integrated profile retains two independently versioned component objects. Every source feature object and every feature-to-evidence-record provenance relationship is copied without loss. Source component record identifiers, content hashes, containing artifact identifiers, artifact hashes, state-rule metadata, and version axes remain explicit. Counts in the index and report are audit reconciliation fields and do not replace lineage.

## Lifecycle and interpretation boundary

This is a deterministic local multi-component integration candidate. It does not promote a Target Evidence Profile lifecycle state and does not validate any target scientifically. It contains no target scoring, ranking, prioritization, selection, recommendation, biological interpretation, therapeutic inference, or runtime AI/LLM judgement.

## Frozen-input verification

- Top-level frozen artifacts verified: {frozen_count}
- Partition payload files verified: {partition_file_count}
- Network access: none
- Package installation: none
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default="outputs/evidence_profile_integration_v0.1",
        help="Repository-relative output directory below outputs/",
    )
    args = parser.parse_args()

    repo = find_repo_root()
    output_root = (repo / args.output_dir).resolve()
    if (repo / "outputs").resolve() not in output_root.parents:
        fail("Output directory must be below repository outputs/")
    if output_root.exists() and any(output_root.iterdir()):
        fail("Output directory is non-empty; frozen outputs are not overwritten")
    output_root.mkdir(parents=True, exist_ok=True)

    frozen_before = verify_frozen_top_level(repo)
    contracts = load_contracts(repo)
    task030_partitions, task030_partition_set, task030_partition_bytes = verify_partition_manifest(
        repo,
        TASK030_ROOT / "partition_manifest.csv",
        {"PROFILE_PAYLOAD", "PROVENANCE_LINKS"},
        512,
    )
    landscape_partitions, landscape_partition_set, landscape_partition_bytes = verify_partition_manifest(
        repo,
        TASK031_ROOT / "landscape_partition_manifest.csv",
        {"EVIDENCE_LANDSCAPE_PAYLOAD"},
        256,
    )

    task030_index_rows = read_csv_rows(repo / TASK030_ROOT / "profile_index.csv")
    landscape_index_rows = read_csv_rows(repo / TASK031_ROOT / "evidence_landscape_index.csv")
    if len(task030_index_rows) != EXPECTED_ENTITIES or len(landscape_index_rows) != EXPECTED_ENTITIES:
        fail("Canonical source indexes do not contain 29,606 rows")
    if len({row["EnsemblID"] for row in task030_index_rows}) != EXPECTED_ENTITIES:
        fail("Task #030 EnsemblID identity is not unique")
    evidence_snapshot_version = compute_evidence_snapshot_version(contracts)

    with tempfile.TemporaryDirectory(prefix="task032c_component_store_", dir="/private/tmp") as temp_dir:
        connection = sqlite3.connect(str(Path(temp_dir) / "transcriptomic_components.sqlite3"))
        try:
            task030_index = {row["EnsemblID"]: row for row in task030_index_rows}
            tx_source_states, tx_source_provenance, tx_source_missingness = build_transcriptomic_store(
                repo,
                connection,
                task030_partitions,
                task030_index,
            )
            if dict(sorted(tx_source_states.items())) != {
                key: value
                for key, value in sorted(contracts["task031"]["component_state_counts"].items())
                if value
            }:
                fail("Task #030 component states do not match Task #031 manifest")
            if tx_source_provenance != contracts["task030"]["counts"]["provenance_relationships"]:
                fail("Task #030 embedded provenance does not match release manifest")

            records_path = output_root / "profile_records.jsonl"
            index_rows, audit, profile_hash, profile_size = materialize_profiles(
                repo,
                records_path,
                connection,
                task030_index_rows,
                landscape_index_rows,
                contracts,
                evidence_snapshot_version,
            )
            validate_audit(audit, contracts)
            index_payload = csv_bytes(index_rows, PROFILE_INDEX_FIELDS)
            index_hash = write_bytes(output_root / "profile_index.csv", index_payload)

            regenerated_audit, regenerated_hash = deterministic_regeneration(
                repo,
                records_path,
                index_payload,
                connection,
                task030_index_rows,
                landscape_index_rows,
                contracts,
                evidence_snapshot_version,
            )
            validate_audit(regenerated_audit, contracts)
            if regenerated_hash != profile_hash:
                fail("Byte-identical regenerated profile hash mismatch")
        finally:
            connection.close()

    checks = [
        ("frozen_input_hashes", len(frozen_before) == len(FROZEN_INPUT_SHA256), f"{len(frozen_before)} top-level artifacts verified"),
        ("partition_integrity", len(task030_partitions) + len(landscape_partitions) == 768, "768 Task #030/#031 partition files verified by size and SHA256"),
        ("profile_identity", audit.entity_count == EXPECTED_ENTITIES and len(audit.profile_ids) == EXPECTED_ENTITIES, "29606 unique profile identity tuples"),
        ("canonical_order", [row["universe_ordinal"] for row in index_rows] == list(range(1, EXPECTED_ENTITIES + 1)), "Task #030 canonical universe order preserved"),
        ("component_presence", audit.component_count == EXPECTED_ENTITIES * 2, "both registered components present in every profile"),
        ("component_independence", all(row["component_set"] == "|".join(COMPONENT_SET) for row in index_rows), "two separately versioned component objects; no overall state"),
        ("feature_fidelity", audit.feature_count == EXPECTED_ENTITIES * 41, f"{audit.feature_count} exact source feature objects"),
        ("state_fidelity", dict(sorted(audit.transcriptomic_states.items())) == dict(sorted(tx_source_states.items())) and dict(sorted(audit.disease_states.items())) == dict(sorted(contracts["disease"]["state_counts"].items())), "component states unchanged"),
        ("missingness_fidelity", dict(sorted(audit.transcriptomic_missingness.items())) == dict(sorted(tx_source_missingness.items())), "feature missingness unchanged"),
        ("provenance_completeness", audit.provenance_count == EXPECTED_TRANSCRIPTOMIC_PROVENANCE + EXPECTED_DISEASE_PROVENANCE, f"{audit.provenance_count} uncompressed source relationships"),
        ("task031_cross_validation", contracts["task031"]["counts"]["dependency_references"] == EXPECTED_TRANSCRIPTOMIC_PROVENANCE, "transcriptomic states and dependency-reference counts reconciled"),
        ("forbidden_field_detection", not (set(PROFILE_INDEX_FIELDS) & FORBIDDEN_PROFILE_FIELDS), "no score/rank/priority/evaluation field names"),
        ("deterministic_profile_records", regenerated_hash == profile_hash, "full second-pass byte comparison and SHA256 match"),
        ("deterministic_profile_index", True, "byte-identical regenerated index"),
        ("no_network", True, "frozen local artifacts only"),
        ("no_evaluation", True, "no target scoring, ranking, selection, recommendation, or interpretation"),
    ]
    if not all(passed for _, passed, _ in checks):
        fail(f"Validation failed: {[name for name, passed, _ in checks if not passed]}")

    generator_hash = sha256_file(Path(__file__).resolve())
    integration_release_id = stable_id(
        "PROFILE_INTEGRATION_RELEASE",
        {
            "profile_schema_version": PROFILE_SCHEMA_VERSION,
            "profile_version": PROFILE_VERSION,
            "evidence_snapshot_version": evidence_snapshot_version,
            "generator_version": GENERATOR_VERSION,
            "profile_records_sha256": profile_hash,
            "profile_index_sha256": index_hash,
        },
    )
    manifest = {
        "canonical_order": "TASK030_UNIVERSE_ORDINAL",
        "component_count": 2,
        "components": [
            {
                "component_id": TRANSCRIPTOMIC_COMPONENT_ID,
                "component_version": TRANSCRIPTOMIC_COMPONENT_VERSION,
                "feature_count_per_profile": EXPECTED_TRANSCRIPTOMIC_FEATURES,
                "provenance_relationship_count": EXPECTED_TRANSCRIPTOMIC_PROVENANCE,
                "source_evidence_snapshot_version": contracts["task030"]["evidence_snapshot_version"],
                "source_release_candidate_id": contracts["task030"]["release_candidate_id"],
                "state_counts": dict(sorted(audit.transcriptomic_states.items())),
            },
            {
                "component_id": DISEASE_COMPONENT_ID,
                "component_version": DISEASE_COMPONENT_VERSION,
                "feature_count_per_profile": EXPECTED_DISEASE_FEATURES,
                "provenance_relationship_count": EXPECTED_DISEASE_PROVENANCE,
                "source_component_release_id": contracts["disease"]["component_release_id"],
                "source_snapshot_version": contracts["disease"]["version_axes"]["source_snapshot_version"],
                "state_counts": dict(sorted(audit.disease_states.items())),
            },
        ],
        "evidence_snapshot_version": evidence_snapshot_version,
        "frozen_inputs": frozen_before,
        "generator": {"sha256": generator_hash, "version": GENERATOR_VERSION},
        "integration_release_id": integration_release_id,
        "interpretation_boundary": "STRUCTURAL_MULTI_COMPONENT_EVIDENCE_REPRESENTATION_ONLY",
        "joint_component_state_counts": dict(sorted(audit.joint_states.items())),
        "lifecycle_status": "UNASSIGNED_INTEGRATION_CANDIDATE_AWAITING_HUMAN_GOVERNANCE_ACTION",
        "network_access": "PROHIBITED_NOT_USED",
        "output_artifacts": {
            "profile_index.csv": {
                "row_count": len(index_rows),
                "sha256": index_hash,
                "size_bytes": len(index_payload),
            },
            "profile_records.jsonl": {
                "row_count": audit.entity_count,
                "sha256": profile_hash,
                "size_bytes": profile_size,
            },
        },
        "partition_input_sets": {
            "task030_partition_file_count": len(task030_partitions),
            "task030_partition_set_sha256": task030_partition_set,
            "task030_partition_total_bytes": task030_partition_bytes,
            "task031_partition_file_count": len(landscape_partitions),
            "task031_partition_set_sha256": landscape_partition_set,
            "task031_partition_total_bytes": landscape_partition_bytes,
        },
        "profile_count": audit.entity_count,
        "profile_identity_tuple": [
            "EnsemblID",
            "profile_schema_version",
            "profile_version",
            "evidence_snapshot_version",
        ],
        "profile_record_contract": {
            "component_order": COMPONENT_SET,
            "component_state_aggregation": "PROHIBITED_NONE_GENERATED",
            "feature_representation": "EXACT_COMPONENT_SPECIFIC_SOURCE_OBJECT",
            "profile_content_hash_scope": "CANONICAL_JSON_WITHOUT_JSONL_NEWLINE",
            "provenance_representation": "ONE_OBJECT_PER_SOURCE_FEATURE_EVIDENCE_RECORD_RELATIONSHIP",
        },
        "profile_schema_version": PROFILE_SCHEMA_VERSION,
        "profile_version": PROFILE_VERSION,
        "prohibitions": [
            "NO_SCORING",
            "NO_RANKING",
            "NO_PRIORITY",
            "NO_TARGET_SELECTION",
            "NO_RECOMMENDATIONS",
            "NO_BIOLOGICAL_INTERPRETATION",
            "NO_THERAPEUTIC_INFERENCE",
            "NO_LLM_RUNTIME_DECISIONS",
        ],
        "structural_counts": {
            "component_representations": audit.component_count,
            "feature_references": audit.feature_count,
            "provenance_relationships": audit.provenance_count,
        },
        "unresolved_governance": [
            "NO_PROFILE_LIFECYCLE_PROMOTION_RECORDED",
            "EXTERNAL_IMMUTABLE_STORAGE_REFERENCE_PENDING",
            "TRANSCRIPTOMIC_STATE_RULE_INDEPENDENT_REVIEW_PENDING",
            "DISEASE_ASSOCIATION_RECORD_GRANULARITY_UNKNOWN_PRESERVED",
        ],
        "validation_status": "PASS",
    }
    manifest_hash = write_bytes(output_root / "profile_manifest.json", pretty_json_bytes(manifest))
    report = validation_report(
        audit,
        profile_hash,
        index_hash,
        profile_size,
        len(frozen_before),
        len(task030_partitions) + len(landscape_partitions),
        checks,
        evidence_snapshot_version,
    )
    report_hash = write_bytes(output_root / "validation_report.md", report.encode("utf-8"))
    session = "\n".join(
        [
            "Task: #032C Evidence Profile Multi-component Integration",
            f"Integration release ID: {integration_release_id}",
            f"Profile schema version: {PROFILE_SCHEMA_VERSION}",
            f"Profile version: {PROFILE_VERSION}",
            f"Evidence snapshot version: {evidence_snapshot_version}",
            f"Generator version: {GENERATOR_VERSION}",
            f"Generator SHA256: {generator_hash}",
            f"Python: {sys.version.replace(chr(10), ' ')}",
            f"Python executable: {sys.executable}",
            f"Platform: {platform.platform()}",
            "Network access: NONE",
            "Package installation: NONE",
            "Randomness: NONE",
            "Runtime AI/LLM decisions: NONE",
            "Wall-clock values in governed outputs: NONE",
            f"Profile records SHA256: {profile_hash}",
            f"Profile index SHA256: {index_hash}",
            f"Profile manifest SHA256: {manifest_hash}",
            f"Validation report SHA256: {report_hash}",
            "Target evaluation performed: FALSE",
            "Profile lifecycle promotion performed: FALSE",
            "",
        ]
    )
    write_bytes(output_root / "session_info.txt", session.encode("utf-8"))

    frozen_after = verify_frozen_top_level(repo)
    if frozen_after != frozen_before:
        fail("Frozen top-level inputs changed during integration")

    print(f"Profile integration complete: {integration_release_id}")
    print(f"Profiles: {audit.entity_count:,}")
    print(f"Component representations: {audit.component_count:,}")
    print(f"Feature references: {audit.feature_count:,}")
    print(f"Provenance relationships: {audit.provenance_count:,}")
    print("Validation: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except IntegrationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
