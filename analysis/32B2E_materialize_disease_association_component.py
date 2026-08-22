#!/usr/bin/env python3
"""Materialize the governed disease-association evidence component.

This offline deterministic materializer copies the validated Task #032B-2D
feature values, structural states, missingness, and every feature-to-record
provenance relationship into one component record per immutable EnsemblID.
It does not retrieve evidence, generate profiles, evaluate targets, score,
rank, prioritize, recommend, or interpret biology.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator


COMPONENT_ID = "COMP_DISEASE_ASSOCIATION"
COMPONENT_VERSION = "COMP_DISEASE_ASSOCIATION_V0.1"
COMPONENT_SCHEMA_VERSION = "DISEASE_ASSOCIATION_COMPONENT_SCHEMA_V0.1"
COMPONENT_GENERATOR_VERSION = "DISEASE_ASSOCIATION_COMPONENT_GENERATOR_V0.1"
EXPECTED_ENTITY_COUNT = 29_606
EXPECTED_FEATURE_COUNT = 19
EXPECTED_FEATURE_INSTANCE_COUNT = EXPECTED_ENTITY_COUNT * EXPECTED_FEATURE_COUNT
EXPECTED_PROVENANCE_COUNT = 1_480_908
EXPECTED_RAW_RECORD_COUNT = 75_165

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
DEPENDENCY_RELATIONSHIP_TYPES = {
    "SAME_SOURCE",
    "SHARED_DATASET",
    "PARTIAL",
    "UNKNOWN",
    "INDEPENDENT",
    "NOT_APPLICABLE",
}
DEPENDENCY_LEVELS = {
    "DEPENDENT",
    "PARTIALLY_DEPENDENT",
    "UNKNOWN",
    "INDEPENDENT",
    "NOT_APPLICABLE",
}
FORBIDDEN_RECORD_FIELDS = {
    "score",
    "scores",
    "rank",
    "ranking",
    "priority",
    "confidence",
    "quality",
    "importance",
    "recommendation",
    "target_recommendation",
    "target_priority",
    "biological_interpretation",
    "therapeutic_interpretation",
}

FROZEN_INPUT_SHA256 = {
    # Task #032A — evidence component governance.
    "docs/governance/evidence_component_interface_specification_v0.1.md": "b31254b347cbf440e3aade02857fb8149c54ea9a9a2b987197c4b724fefa20e8",
    "docs/governance/component_registration_policy_v0.1.md": "c1736e11695e6bb194665a0cf96115bb526075ca5aa9f9870e8e572f64302668",
    "docs/governance/component_validation_requirements_v0.1.md": "cc71c239972bc8f0b20fff63e4478624e0bcb56bc0febfc52855818ee5171c95",
    "docs/governance/component_dependency_model_v0.1.md": "5b77654a7ea543b2b2a184bba4a280cc4395c575065be6a3674d93a0955cdb06",
    # Task #032B-2C — immutable raw snapshot and retrieval implementation.
    "analysis/32B2C_retrieve_disease_association_snapshot.py": "436c1135c5ecb133e461ca14dc07ebe6414ed87c220d7992f6e09cc8117e78bc",
    "outputs/disease_association_snapshot_v0.1/snapshot_manifest.json": "1bd2df46ad11528f3bbf4da8eb7c68a581277b92461586b942f660f9be00ae75",
    "outputs/disease_association_snapshot_v0.1/release_manifest.json": "b38a53665b7e17d65ce2f830063812094cd18a6c1a3861b3892b056ce259cf47",
    "outputs/disease_association_snapshot_v0.1/file_inventory.csv": "e425a6d9223686e27b4dbd69a83eb50d2e7352eb9b6eba14a11b8b471b5ed8e9",
    "outputs/disease_association_snapshot_v0.1/raw_record_manifest.csv": "ef94b3602f1b404df6c0090e45c533e22c4554fab0080a2ae5d7bfaca18ab0f4",
    "outputs/disease_association_snapshot_v0.1/entity_coverage_ledger.csv": "b0b7903c33a65f991150804722b832c0168f1156a703411e9d7a3c23c5e8202e",
    "outputs/disease_association_snapshot_v0.1/snapshot_qc_report.md": "078234cc85b02563737fdbdbc1f4078bff9bba7057db88a54e662b10c1d5e4b3",
    "outputs/disease_association_snapshot_v0.1/session_info.txt": "92738f23f34ca42718d3eb9ba0b869d5cd86323c1505f19ee5339da4d9682e03",
    # Task #032B-2D — validated normalized features.
    "analysis/32B2D_build_disease_association_feature_extractor.py": "ac7326e54aa02739f3ddbe4490dd8890e587b7ceab2782e128bd4cae0afdda7b",
    "outputs/disease_association_features_v0.1/component_manifest.json": "5034bd52cf8fdefd6f8232f291298b882e0b27cb9ec5f3844f9707772dc1f526",
    "outputs/disease_association_features_v0.1/disease_association_features.csv": "3eee6bb0a3f55e051427fdd7f67fd974604abe9bc11477b2e3be73c561201418",
    "outputs/disease_association_features_v0.1/feature_dictionary.csv": "690f5d23fd6de3a949d77b60e19fad6655fec83441afcb31d1c2dfd46532be32",
    "outputs/disease_association_features_v0.1/feature_provenance_registry.csv": "d3f16e0a621e0b129c3d42e7bc01cb2042d1cef05374c19b1e23643043545480",
    "outputs/disease_association_features_v0.1/validation_report.md": "91ecadb7c09febc271cd7e7c75b6b53ce7b212776f9c32e4a745f65da1df2f6e",
    "outputs/disease_association_features_v0.1/session_info.txt": "c4661de6a31f799fae0787cf1886d0e1277ae1a3942af416c889c8bbdb06b4d6",
    # Task #028 — profile governance and version/lifecycle boundaries.
    "docs/governance/target_evidence_profile_governance_v0.1.md": "1b8ab03bb758fd70d8a4bffb27ba1c7f97f83a52c20e75a0c18d9b0bd0941bbd",
    "docs/governance/profile_lifecycle_specification_v0.1.md": "346d46ce22b46513038ed7a62d951f1d3197432246e758bee84e56425137ccca",
    "docs/governance/profile_component_model_v0.1.md": "86ae5b8ce089f97770976b7b9f9b547a918e88c165cb7f983dd450178f8a7355",
    "docs/governance/profile_release_policy_v0.1.md": "f164be0352cd012583560b6ff5ef9850e43c59b49f4b9c4e28e3fe9138c77912",
}

SNAPSHOT_ROOT = Path("outputs/disease_association_snapshot_v0.1")
FEATURE_ROOT = Path("outputs/disease_association_features_v0.1")

FEATURES_PATH = FEATURE_ROOT / "disease_association_features.csv"
DICTIONARY_PATH = FEATURE_ROOT / "feature_dictionary.csv"
PROVENANCE_PATH = FEATURE_ROOT / "feature_provenance_registry.csv"
FEATURE_MANIFEST_PATH = FEATURE_ROOT / "component_manifest.json"
SNAPSHOT_MANIFEST_PATH = SNAPSHOT_ROOT / "snapshot_manifest.json"
RAW_RECORD_MANIFEST_PATH = SNAPSHOT_ROOT / "raw_record_manifest.csv"
FILE_INVENTORY_PATH = SNAPSHOT_ROOT / "file_inventory.csv"

INDEX_FIELDS = [
    "universe_ordinal",
    "EnsemblID",
    "component_record_id",
    "component_id",
    "component_version",
    "component_state",
    "component_schema_version",
    "source_snapshot_version",
    "feature_schema_version",
    "state_rule_version",
    "generator_version",
    "feature_count",
    "provenance_relationship_count",
    "record_offset_bytes",
    "record_length_bytes",
    "component_record_sha256",
]

LINK_FIELDS = [
    "claim_id",
    "evidence_record_id",
    "raw_record_id",
    "source_record_id",
    "source_id",
    "source_version",
    "snapshot_id",
    "source_snapshot_version",
    "artifact_id",
    "artifact_sha256",
    "source_dataset",
    "source_role",
    "dependency_id",
    "dependency_relationship_types",
    "dependency_level",
]


class MaterializationError(RuntimeError):
    """Raised when a frozen-input or materialization invariant fails."""


def fail(message: str) -> None:
    raise MaterializationError(message)


def find_repo_root() -> Path:
    candidate = Path(__file__).resolve().parent.parent
    if not (candidate / ".git").exists():
        fail("Repository root could not be resolved from the materializer path")
    return candidate


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def pretty_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode(
        "utf-8"
    )


def stable_id(prefix: str, payload: Any, length: int = 32) -> str:
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
            "utf-8"
        )
    ).hexdigest()[:length].upper()
    return f"{prefix}_{digest}"


def csv_bytes(rows: list[dict[str, Any]], fields: list[str]) -> bytes:
    import io

    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def write_bytes(path: Path, payload: bytes) -> str:
    with path.open("wb") as handle:
        handle.write(payload)
    return hashlib.sha256(payload).hexdigest()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def verify_frozen_inputs(repo: Path) -> dict[str, str]:
    actual: dict[str, str] = {}
    for relative_path, expected in FROZEN_INPUT_SHA256.items():
        path = repo / relative_path
        if not path.is_file():
            fail(f"Frozen input is missing: {relative_path}")
        observed = sha256_file(path)
        if observed != expected:
            fail(
                f"Frozen input hash mismatch for {relative_path}: "
                f"expected {expected}, observed {observed}"
            )
        actual[relative_path] = observed
    return actual


def validate_local_snapshot_artifacts(repo: Path) -> tuple[set[str], dict[str, str]]:
    rows = read_csv_rows(repo / FILE_INVENTORY_PATH)
    if len(rows) != 350:
        fail(f"Unexpected Task #032B-2C file inventory length: {len(rows)}")
    allowed_artifact_hashes: set[str] = set()
    local_verified: dict[str, str] = {}
    for row in rows:
        artifact_hash = row["sha256"]
        allowed_artifact_hashes.add(artifact_hash)
        relative = row["relative_path_or_reference"]
        candidate = repo / SNAPSHOT_ROOT / relative
        if candidate.is_file():
            size = candidate.stat().st_size
            if size != int(row["file_size_bytes"]):
                fail(f"Snapshot artifact size mismatch: {relative}")
            observed = sha256_file(candidate)
            if observed != artifact_hash:
                fail(f"Snapshot artifact hash mismatch: {relative}")
            local_verified[relative] = observed
    coverage_hash = FROZEN_INPUT_SHA256[
        "outputs/disease_association_snapshot_v0.1/entity_coverage_ledger.csv"
    ]
    allowed_artifact_hashes.add(coverage_hash)
    return allowed_artifact_hashes, local_verified


def load_raw_records(repo: Path) -> dict[str, dict[str, str]]:
    rows = read_csv_rows(repo / RAW_RECORD_MANIFEST_PATH)
    if len(rows) != EXPECTED_RAW_RECORD_COUNT:
        fail(f"Unexpected raw-record count: {len(rows)}")
    by_id: dict[str, dict[str, str]] = {}
    for row in rows:
        raw_id = row["raw_record_id"]
        if raw_id in by_id:
            fail(f"Duplicate raw_record_id: {raw_id}")
        if row["source_disease_id"] != "MONDO_0005061":
            fail(f"Out-of-scope disease record: {raw_id}")
        by_id[raw_id] = row
    return by_id


def load_contracts(repo: Path) -> tuple[list[dict[str, str]], dict[str, Any], dict[str, Any]]:
    dictionary = read_csv_rows(repo / DICTIONARY_PATH)
    if len(dictionary) != EXPECTED_FEATURE_COUNT:
        fail(f"Feature dictionary must contain exactly {EXPECTED_FEATURE_COUNT} rows")
    feature_names = [row["feature_name"] for row in dictionary]
    definition_ids = [row["feature_definition_id"] for row in dictionary]
    if len(set(feature_names)) != EXPECTED_FEATURE_COUNT:
        fail("Feature names are not unique")
    if len(set(definition_ids)) != EXPECTED_FEATURE_COUNT:
        fail("Feature definition IDs are not unique")

    feature_manifest = json.loads((repo / FEATURE_MANIFEST_PATH).read_text(encoding="utf-8"))
    snapshot_manifest = json.loads((repo / SNAPSHOT_MANIFEST_PATH).read_text(encoding="utf-8"))
    if feature_manifest["validation_status"] != "PASS":
        fail("Task #032B-2D feature layer is not validated")
    if snapshot_manifest["completeness_status"] != "COMPLETE":
        fail("Task #032B-2C raw snapshot is not complete")
    if feature_manifest["component_id"] != COMPONENT_ID:
        fail("Feature component_id mismatch")
    if feature_manifest["component_version"] != COMPONENT_VERSION:
        fail("Feature component_version mismatch")
    if feature_manifest["entity_count"] != EXPECTED_ENTITY_COUNT:
        fail("Feature entity count mismatch")
    if feature_manifest["feature_definition_count"] != EXPECTED_FEATURE_COUNT:
        fail("Feature definition count mismatch")
    if feature_manifest["feature_instance_count"] != EXPECTED_FEATURE_INSTANCE_COUNT:
        fail("Feature instance count mismatch")
    if (
        feature_manifest["output_artifacts"]["feature_provenance_registry.csv"]["row_count"]
        != EXPECTED_PROVENANCE_COUNT
    ):
        fail("Feature provenance count mismatch")
    if (
        snapshot_manifest["identity_payload"]["component_id"] != COMPONENT_ID
        or snapshot_manifest["identity_payload"]["component_version"] != COMPONENT_VERSION
    ):
        fail("Snapshot component identity mismatch")
    if (
        feature_manifest["source_snapshot_version"]
        != snapshot_manifest["source_snapshot_version"]
    ):
        fail("Feature and raw source-snapshot versions differ")
    return dictionary, feature_manifest, snapshot_manifest


def load_feature_headers(repo: Path, dictionary: list[dict[str, str]]) -> list[str]:
    with (repo / FEATURES_PATH).open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        headers = next(reader)
    for definition in dictionary:
        name = definition["feature_name"]
        if name not in headers or f"{name}__missingness_status" not in headers:
            fail(f"Feature table is missing governed fields for {name}")
    if set(headers) & FORBIDDEN_RECORD_FIELDS:
        fail("Forbidden field detected in normalized feature input")
    return headers


@dataclass
class Audit:
    entity_count: int = 0
    feature_instance_count: int = 0
    provenance_relationship_count: int = 0
    raw_record_link_count: int = 0
    scope_record_link_count: int = 0
    state_counts: Counter[str] = field(default_factory=Counter)
    missingness_counts: Counter[str] = field(default_factory=Counter)
    dependency_level_counts: Counter[str] = field(default_factory=Counter)
    dependency_relationship_type_counts: Counter[str] = field(default_factory=Counter)
    seen_feature_ids: set[str] = field(default_factory=set)


class ProvenanceGroups:
    """Stream Task #032B-2D provenance in canonical entity order."""

    def __init__(self, path: Path):
        self._handle = path.open(newline="", encoding="utf-8")
        self._reader = csv.DictReader(self._handle)
        required = {
            "feature_id",
            "EnsemblID",
            "feature_definition_id",
            "feature_name",
            "feature_value_sha256",
            "claim_id",
            "evidence_record_id",
            "raw_record_id",
            "source_id",
            "snapshot_id",
            "artifact_id",
            "artifact_sha256",
            "dependency_id",
            "dependency_relationship_types",
            "dependency_level",
            "feature_missingness_status",
            "extraction_rule_id",
            "extractor_version",
        }
        if not required <= set(self._reader.fieldnames or []):
            fail("Task #032B-2D provenance schema is incomplete")
        if set(self._reader.fieldnames or []) & FORBIDDEN_RECORD_FIELDS:
            fail("Forbidden field detected in provenance input")
        self._current = next(self._reader, None)

    def consume_entity(self, expected_ensembl_id: str) -> dict[str, list[dict[str, str]]]:
        if self._current is None:
            fail(f"Provenance ended before {expected_ensembl_id}")
        if self._current["EnsemblID"] != expected_ensembl_id:
            fail(
                f"Provenance order mismatch: expected {expected_ensembl_id}, "
                f"observed {self._current['EnsemblID']}"
            )
        groups: dict[str, list[dict[str, str]]] = defaultdict(list)
        while self._current is not None and self._current["EnsemblID"] == expected_ensembl_id:
            groups[self._current["feature_definition_id"]].append(self._current)
            self._current = next(self._reader, None)
        return dict(groups)

    def assert_exhausted(self) -> None:
        if self._current is not None:
            fail(f"Unconsumed provenance remains at {self._current['EnsemblID']}")

    def close(self) -> None:
        self._handle.close()


def validate_dependency(types: list[str], level: str) -> None:
    if not types or not set(types) <= DEPENDENCY_RELATIONSHIP_TYPES:
        fail(f"Invalid dependency relationship types: {types}")
    if level not in DEPENDENCY_LEVELS:
        fail(f"Invalid dependency level: {level}")
    if "NOT_APPLICABLE" in types and (types != ["NOT_APPLICABLE"] or level != "NOT_APPLICABLE"):
        fail("NOT_APPLICABLE dependency was altered or combined")
    if set(types) & {"SAME_SOURCE", "SHARED_DATASET"} and level != "DEPENDENT":
        fail("Same-source/shared-dataset record is not DEPENDENT")
    if "PARTIAL" in types and level != "PARTIALLY_DEPENDENT":
        fail("PARTIAL relationship has incompatible level")
    if "UNKNOWN" in types and level != "UNKNOWN":
        fail("UNKNOWN relationship has incompatible level")
    if "INDEPENDENT" in types and level != "INDEPENDENT":
        fail("INDEPENDENT relationship has incompatible level")


def component_record_id(ensembl_id: str, versions: dict[str, str]) -> str:
    return stable_id(
        "CMPREC_DA",
        {
            "EnsemblID": ensembl_id,
            "component_id": COMPONENT_ID,
            "component_version": COMPONENT_VERSION,
            "source_snapshot_version": versions["source_snapshot_version"],
        },
    )


def build_record(
    feature_row: dict[str, str],
    dictionary: list[dict[str, str]],
    provenance_groups: dict[str, list[dict[str, str]]],
    raw_records: dict[str, dict[str, str]],
    allowed_artifact_hashes: set[str],
    versions: dict[str, str],
    audit: Audit,
) -> dict[str, Any]:
    ensembl_id = feature_row["EnsemblID"]
    state = feature_row["component_state"]
    if state not in STATE_VOCABULARY:
        fail(f"Invalid component state for {ensembl_id}: {state}")
    if feature_row["component_id"] != COMPONENT_ID:
        fail(f"Feature component identity mismatch for {ensembl_id}")
    if feature_row["component_version"] != COMPONENT_VERSION:
        fail(f"Feature component version mismatch for {ensembl_id}")
    for axis in (
        "source_snapshot_version",
        "feature_schema_version",
        "state_rule_version",
        "extractor_version",
    ):
        if feature_row[axis] != versions[axis]:
            fail(f"Feature {axis} mismatch for {ensembl_id}")

    expected_definition_ids = [row["feature_definition_id"] for row in dictionary]
    if set(provenance_groups) != set(expected_definition_ids):
        fail(f"Provenance feature set mismatch for {ensembl_id}")

    features: list[dict[str, Any]] = []
    for definition in dictionary:
        definition_id = definition["feature_definition_id"]
        feature_name = definition["feature_name"]
        source_value = feature_row[feature_name]
        missingness = feature_row[f"{feature_name}__missingness_status"]
        if missingness not in MISSINGNESS_VOCABULARY:
            fail(f"Invalid feature missingness for {ensembl_id}/{feature_name}: {missingness}")
        provenance_rows = provenance_groups[definition_id]
        if not provenance_rows:
            fail(f"Feature lacks provenance for {ensembl_id}/{feature_name}")
        feature_ids = {row["feature_id"] for row in provenance_rows}
        if len(feature_ids) != 1:
            fail(f"Feature identity conflict for {ensembl_id}/{feature_name}")
        feature_id = next(iter(feature_ids))
        if feature_id in audit.seen_feature_ids:
            fail(f"Duplicate feature instance identity: {feature_id}")
        audit.seen_feature_ids.add(feature_id)
        expected_value_hash = hashlib.sha256(source_value.encode("utf-8")).hexdigest()
        if {row["feature_value_sha256"] for row in provenance_rows} != {expected_value_hash}:
            fail(f"Feature value hash mismatch for {ensembl_id}/{feature_name}")
        if {row["feature_name"] for row in provenance_rows} != {feature_name}:
            fail(f"Feature name mismatch in provenance for {ensembl_id}/{feature_name}")
        if {row["feature_missingness_status"] for row in provenance_rows} != {missingness}:
            fail(f"Missingness mismatch in provenance for {ensembl_id}/{feature_name}")
        if {row["extraction_rule_id"] for row in provenance_rows} != {
            definition["extraction_rule_id"]
        }:
            fail(f"Extraction rule mismatch for {ensembl_id}/{feature_name}")
        if {row["extractor_version"] for row in provenance_rows} != {
            definition["extractor_version"]
        }:
            fail(f"Extractor version mismatch for {ensembl_id}/{feature_name}")

        evidence_record_ids: set[str] = set()
        links: list[dict[str, Any]] = []
        for row in provenance_rows:
            evidence_record_id = row["evidence_record_id"]
            if evidence_record_id in evidence_record_ids:
                fail(
                    f"Duplicate provenance relationship for {feature_id}/{evidence_record_id}"
                )
            evidence_record_ids.add(evidence_record_id)
            if row["artifact_sha256"] not in allowed_artifact_hashes:
                fail(f"Unresolved snapshot artifact hash for {evidence_record_id}")
            raw_id = row["raw_record_id"]
            if raw_id == "NOT_APPLICABLE_QUERY_SCOPE_RECORD":
                audit.scope_record_link_count += 1
                if row["source_dataset"] != "entity_coverage_ledger":
                    fail(f"Invalid query-scope provenance dataset for {evidence_record_id}")
            else:
                audit.raw_record_link_count += 1
                raw = raw_records.get(raw_id)
                if raw is None:
                    fail(f"Unresolved raw record: {raw_id}")
                checks = {
                    "source_record_id": raw["source_record_id"],
                    "source_id": raw["source_id"],
                    "source_version": raw["source_version"],
                    "source_dataset": raw["source_dataset"],
                    "artifact_sha256": raw["snapshot_raw_file_sha256"],
                }
                for field_name, expected in checks.items():
                    if row[field_name] != expected:
                        fail(f"Raw lineage mismatch for {raw_id}/{field_name}")
            try:
                dependency_types = json.loads(row["dependency_relationship_types"])
            except json.JSONDecodeError as exc:
                fail(f"Invalid dependency JSON for {evidence_record_id}: {exc}")
            if not isinstance(dependency_types, list) or not all(
                isinstance(item, str) for item in dependency_types
            ):
                fail(f"Dependency types are not a string list for {evidence_record_id}")
            if json.dumps(dependency_types, separators=(",", ":")) != row[
                "dependency_relationship_types"
            ]:
                fail(f"Dependency relationship ordering is not canonical for {evidence_record_id}")
            validate_dependency(dependency_types, row["dependency_level"])
            audit.dependency_level_counts[row["dependency_level"]] += 1
            audit.dependency_relationship_type_counts.update(dependency_types)
            if any(not row[field_name] for field_name in LINK_FIELDS if field_name != "dependency_relationship_types"):
                fail(f"Incomplete provenance relationship: {feature_id}/{evidence_record_id}")
            link = {field_name: row[field_name] for field_name in LINK_FIELDS}
            link["dependency_relationship_types"] = dependency_types
            links.append(link)

        features.append(
            {
                "extraction_rule_id": definition["extraction_rule_id"],
                "extractor_version": definition["extractor_version"],
                "feature_definition_id": definition_id,
                "feature_id": feature_id,
                "feature_name": feature_name,
                "feature_value": source_value,
                "feature_value_sha256": expected_value_hash,
                "missingness_status": missingness,
                "provenance_links": links,
            }
        )
        audit.feature_instance_count += 1
        audit.provenance_relationship_count += len(links)
        audit.missingness_counts[missingness] += 1

    audit.entity_count += 1
    audit.state_counts[state] += 1
    record = {
        "EnsemblID": ensembl_id,
        "component_definition_version": COMPONENT_VERSION,
        "component_id": COMPONENT_ID,
        "component_record_id": component_record_id(ensembl_id, versions),
        "component_schema_version": COMPONENT_SCHEMA_VERSION,
        "component_state": state,
        "component_version": COMPONENT_VERSION,
        "extractor_version": versions["extractor_version"],
        "feature_generator_version": versions["feature_generator_version"],
        "feature_schema_version": versions["feature_schema_version"],
        "features": features,
        "generator_version": COMPONENT_GENERATOR_VERSION,
        "source_snapshot_version": versions["source_snapshot_version"],
        "state_rule_version": versions["state_rule_version"],
    }
    if set(record) & FORBIDDEN_RECORD_FIELDS:
        fail(f"Forbidden component field for {ensembl_id}")
    return record


def iter_component_records(
    repo: Path,
    dictionary: list[dict[str, str]],
    raw_records: dict[str, dict[str, str]],
    allowed_artifact_hashes: set[str],
    versions: dict[str, str],
    audit: Audit,
) -> Iterator[tuple[int, dict[str, Any], bytes]]:
    provenance = ProvenanceGroups(repo / PROVENANCE_PATH)
    try:
        with (repo / FEATURES_PATH).open(newline="", encoding="utf-8") as feature_handle:
            reader = csv.DictReader(feature_handle)
            ordinal = 0
            for ordinal, feature_row in enumerate(reader, start=1):
                ensembl_id = feature_row["EnsemblID"]
                groups = provenance.consume_entity(ensembl_id)
                record = build_record(
                    feature_row,
                    dictionary,
                    groups,
                    raw_records,
                    allowed_artifact_hashes,
                    versions,
                    audit,
                )
                yield ordinal, record, canonical_json_bytes(record)
            if ordinal != EXPECTED_ENTITY_COUNT:
                fail(f"Feature row count mismatch: {ordinal}")
        provenance.assert_exhausted()
    finally:
        provenance.close()


def materialize_records(
    repo: Path,
    output_path: Path,
    dictionary: list[dict[str, str]],
    raw_records: dict[str, dict[str, str]],
    allowed_artifact_hashes: set[str],
    versions: dict[str, str],
) -> tuple[list[dict[str, Any]], Audit, str, int]:
    audit = Audit()
    index_rows: list[dict[str, Any]] = []
    output_hash = hashlib.sha256()
    offset = 0
    with output_path.open("wb") as output:
        for ordinal, record, payload in iter_component_records(
            repo, dictionary, raw_records, allowed_artifact_hashes, versions, audit
        ):
            output.write(payload)
            output_hash.update(payload)
            record_hash = hashlib.sha256(payload).hexdigest()
            provenance_count = sum(len(feature["provenance_links"]) for feature in record["features"])
            index_rows.append(
                {
                    "universe_ordinal": ordinal,
                    "EnsemblID": record["EnsemblID"],
                    "component_record_id": record["component_record_id"],
                    "component_id": COMPONENT_ID,
                    "component_version": COMPONENT_VERSION,
                    "component_state": record["component_state"],
                    "component_schema_version": COMPONENT_SCHEMA_VERSION,
                    "source_snapshot_version": versions["source_snapshot_version"],
                    "feature_schema_version": versions["feature_schema_version"],
                    "state_rule_version": versions["state_rule_version"],
                    "generator_version": COMPONENT_GENERATOR_VERSION,
                    "feature_count": len(record["features"]),
                    "provenance_relationship_count": provenance_count,
                    "record_offset_bytes": offset,
                    "record_length_bytes": len(payload),
                    "component_record_sha256": record_hash,
                }
            )
            offset += len(payload)
    return index_rows, audit, output_hash.hexdigest(), offset


def validate_audit(audit: Audit, expected_states: dict[str, int]) -> None:
    if audit.entity_count != EXPECTED_ENTITY_COUNT:
        fail(f"Materialized entity count mismatch: {audit.entity_count}")
    if audit.feature_instance_count != EXPECTED_FEATURE_INSTANCE_COUNT:
        fail(f"Feature instance count mismatch: {audit.feature_instance_count}")
    if audit.provenance_relationship_count != EXPECTED_PROVENANCE_COUNT:
        fail(f"Provenance count mismatch: {audit.provenance_relationship_count}")
    if len(audit.seen_feature_ids) != EXPECTED_FEATURE_INSTANCE_COUNT:
        fail("Feature instance IDs are not unique")
    if audit.raw_record_link_count + audit.scope_record_link_count != EXPECTED_PROVENANCE_COUNT:
        fail("Raw and query-scope provenance links do not reconcile")
    if set(audit.state_counts) - STATE_VOCABULARY:
        fail("Uncontrolled component state materialized")
    if dict(sorted(audit.state_counts.items())) != dict(sorted(expected_states.items())):
        fail("Component states differ from Task #032B-2D")
    if set(audit.missingness_counts) - MISSINGNESS_VOCABULARY:
        fail("Uncontrolled feature missingness materialized")
    if "INDEPENDENT" in audit.dependency_level_counts:
        fail("Disease-association records were unexpectedly labelled INDEPENDENT")


def verify_byte_identical_regeneration(
    repo: Path,
    output_path: Path,
    expected_index_payload: bytes,
    dictionary: list[dict[str, str]],
    raw_records: dict[str, dict[str, str]],
    allowed_artifact_hashes: set[str],
    versions: dict[str, str],
) -> tuple[Audit, str]:
    audit = Audit()
    regenerated_index: list[dict[str, Any]] = []
    offset = 0
    digest = hashlib.sha256()
    with output_path.open("rb") as frozen:
        for ordinal, record, regenerated in iter_component_records(
            repo, dictionary, raw_records, allowed_artifact_hashes, versions, audit
        ):
            observed = frozen.readline()
            if observed != regenerated:
                fail(f"Non-deterministic component record at ordinal {ordinal}")
            digest.update(regenerated)
            regenerated_index.append(
                {
                    "universe_ordinal": ordinal,
                    "EnsemblID": record["EnsemblID"],
                    "component_record_id": record["component_record_id"],
                    "component_id": COMPONENT_ID,
                    "component_version": COMPONENT_VERSION,
                    "component_state": record["component_state"],
                    "component_schema_version": COMPONENT_SCHEMA_VERSION,
                    "source_snapshot_version": versions["source_snapshot_version"],
                    "feature_schema_version": versions["feature_schema_version"],
                    "state_rule_version": versions["state_rule_version"],
                    "generator_version": COMPONENT_GENERATOR_VERSION,
                    "feature_count": len(record["features"]),
                    "provenance_relationship_count": sum(
                        len(feature["provenance_links"]) for feature in record["features"]
                    ),
                    "record_offset_bytes": offset,
                    "record_length_bytes": len(regenerated),
                    "component_record_sha256": hashlib.sha256(regenerated).hexdigest(),
                }
            )
            offset += len(regenerated)
        if frozen.read(1) != b"":
            fail("Component record artifact contains trailing bytes")
    if csv_bytes(regenerated_index, INDEX_FIELDS) != expected_index_payload:
        fail("Component index is not byte-identically reproducible")
    return audit, digest.hexdigest()


def validation_report(
    frozen_count: int,
    local_snapshot_count: int,
    audit: Audit,
    records_hash: str,
    index_hash: str,
    records_size: int,
    checks: list[tuple[str, bool, str]],
    versions: dict[str, str],
) -> str:
    state_lines = "\n".join(
        f"- `{state}`: {audit.state_counts.get(state, 0):,}"
        for state in ("OBSERVED", "PARTIAL", "CONFLICTING", "MISSING", "NOT_QUERIED")
    )
    missing_lines = "\n".join(
        f"- `{state}`: {audit.missingness_counts.get(state, 0):,}"
        for state in ("OBSERVED", "NOT_FOUND", "NOT_QUERIED", "NOT_APPLICABLE", "UNKNOWN")
    )
    check_lines = "\n".join(
        f"- {'PASS' if passed else 'FAIL'} — `{name}`: {detail}"
        for name, passed, detail in checks
    )
    return f"""# Disease Association Component Validation Report

**Task:** #032B-2E  
**Component:** `{COMPONENT_ID}`  
**Component version:** `{COMPONENT_VERSION}`  
**Validation status:** **PASS**

## Materialized component

- Immutable component instances: {audit.entity_count:,}
- Features per instance: {EXPECTED_FEATURE_COUNT}
- Total feature instances: {audit.feature_instance_count:,}
- Uncompressed provenance relationships: {audit.provenance_relationship_count:,}
- Direct raw-record relationships: {audit.raw_record_link_count:,}
- Query-scope relationships: {audit.scope_record_link_count:,}
- Component-record bytes: {records_size:,}
- Component-record SHA256: `{records_hash}`
- Component-index SHA256: `{index_hash}`

## Independent version axes

- Component version: `{COMPONENT_VERSION}`
- Component schema version: `{COMPONENT_SCHEMA_VERSION}`
- Source snapshot version: `{versions['source_snapshot_version']}`
- Feature schema version: `{versions['feature_schema_version']}`
- Feature generator version: `{versions['feature_generator_version']}`
- State-rule version: `{versions['state_rule_version']}`
- Extractor version: `{versions['extractor_version']}`
- Component generator version: `{COMPONENT_GENERATOR_VERSION}`

## Structural component states

{state_lines}

These are structural evidence conditions only. They are non-ordinal and do not represent disease relevance, target quality, importance, confidence, priority, or therapeutic value.

## Feature missingness

{missing_lines}

`NOT_FOUND` remains a completed-query structural outcome and is not negative evidence. Feature missingness is not substituted by component state.

## Validation checks

{check_lines}

## Provenance and dependency boundary

Every Task #032B-2D `(feature_id, evidence_record_id)` relationship is embedded separately below its feature. Each relationship retains its raw-record, source, snapshot-artifact, extraction-rule, and dependency identifiers. Same-source and shared-dataset relationships remain dependent; `NOT_APPLICABLE` is not rewritten as independence. Counts in this report and index are audit reconciliation fields and do not replace lineage.

## Authorization and lifecycle boundary

The explicit Task #032B-2E instruction is the scoped execution authority for this component materialization. The earlier Task #032B-2B retrieval-only authorization remains unchanged as a historical governance record. This component artifact does not create or promote a Target Evidence Profile lifecycle state.

## Interpretation boundary

This component materializes validated structural observations only. It generates no target profile, score, rank, priority, recommendation, disease-relevance interpretation, therapeutic interpretation, or biological conclusion. No network, live source, randomness, or runtime AI/LLM decision was used.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default="outputs/disease_association_component_v0.1",
        help="Repository-relative output directory below outputs/",
    )
    args = parser.parse_args()

    repo = find_repo_root()
    output_root = (repo / args.output_dir).resolve()
    if (repo / "outputs").resolve() not in output_root.parents:
        fail("Output directory must be below repository outputs/")
    if output_root.exists() and any(output_root.iterdir()):
        fail("Output directory is non-empty; frozen component outputs are not overwritten")
    output_root.mkdir(parents=True, exist_ok=True)

    frozen_before = verify_frozen_inputs(repo)
    dictionary, feature_manifest, snapshot_manifest = load_contracts(repo)
    load_feature_headers(repo, dictionary)
    allowed_artifact_hashes, local_snapshot_artifacts = validate_local_snapshot_artifacts(repo)
    raw_records = load_raw_records(repo)

    versions = {
        "source_snapshot_version": feature_manifest["source_snapshot_version"],
        "feature_schema_version": feature_manifest["feature_schema_version"],
        "feature_generator_version": feature_manifest["generator_version"],
        "state_rule_version": feature_manifest["state_rule_version"],
        "extractor_version": feature_manifest["extractor"]["version"],
    }
    if versions["source_snapshot_version"] != snapshot_manifest["source_snapshot_version"]:
        fail("Source snapshot version mismatch")

    records_path = output_root / "component_records.jsonl"
    index_rows, audit, records_hash, records_size = materialize_records(
        repo,
        records_path,
        dictionary,
        raw_records,
        allowed_artifact_hashes,
        versions,
    )
    expected_states = feature_manifest["state_counts"]
    validate_audit(audit, expected_states)

    index_payload = csv_bytes(index_rows, INDEX_FIELDS)
    index_hash = write_bytes(output_root / "component_index.csv", index_payload)
    regenerated_audit, regenerated_records_hash = verify_byte_identical_regeneration(
        repo,
        records_path,
        index_payload,
        dictionary,
        raw_records,
        allowed_artifact_hashes,
        versions,
    )
    validate_audit(regenerated_audit, expected_states)
    if regenerated_records_hash != records_hash:
        fail("Regenerated component-record hash mismatch")

    checks = [
        ("frozen_input_hashes", len(frozen_before) == len(FROZEN_INPUT_SHA256), f"{len(frozen_before)} frozen files verified"),
        ("raw_snapshot_local_artifacts", bool(local_snapshot_artifacts), f"{len(local_snapshot_artifacts)} local snapshot artifacts verified by size and SHA256"),
        ("entity_identity", audit.entity_count == EXPECTED_ENTITY_COUNT, f"{audit.entity_count} ordered immutable EnsemblID records"),
        ("component_identity", all(row["component_id"] == COMPONENT_ID and row["component_version"] == COMPONENT_VERSION for row in index_rows), "all index identities exact"),
        ("feature_fidelity", audit.feature_instance_count == EXPECTED_FEATURE_INSTANCE_COUNT, f"{audit.feature_instance_count} exact source feature instances"),
        ("state_fidelity", dict(sorted(audit.state_counts.items())) == dict(sorted(expected_states.items())), json.dumps(dict(sorted(audit.state_counts.items())), separators=(",", ":"))),
        ("provenance_completeness", audit.provenance_relationship_count == EXPECTED_PROVENANCE_COUNT, f"{audit.provenance_relationship_count} uncompressed relationships"),
        ("raw_record_lineage", audit.raw_record_link_count > 0 and len(raw_records) == EXPECTED_RAW_RECORD_COUNT, f"{audit.raw_record_link_count} direct links resolve against {len(raw_records)} raw records"),
        ("dependency_preservation", "INDEPENDENT" not in audit.dependency_level_counts, json.dumps(dict(sorted(audit.dependency_level_counts.items())), separators=(",", ":"))),
        ("missingness_preservation", set(audit.missingness_counts) <= MISSINGNESS_VOCABULARY, json.dumps(dict(sorted(audit.missingness_counts.items())), separators=(",", ":"))),
        ("forbidden_field_detection", not (set(INDEX_FIELDS) & FORBIDDEN_RECORD_FIELDS), "no prohibited component/index field names"),
        ("deterministic_component_records", regenerated_records_hash == records_hash, "full second-pass byte comparison and SHA256 match"),
        ("deterministic_component_index", True, "byte-identical regenerated index"),
        ("no_network", True, "offline frozen artifacts only"),
        ("no_profiles", True, "no target profile artifact generated"),
        ("no_evaluation", True, "no scoring, ranking, priority, recommendation, or interpretation"),
    ]
    if not all(passed for _, passed, _ in checks):
        fail(f"Validation checks failed: {[name for name, passed, _ in checks if not passed]}")

    script_hash = sha256_file(Path(__file__).resolve())
    component_release_id = stable_id(
        "DA_COMPONENT_RELEASE",
        {
            "component_id": COMPONENT_ID,
            "component_version": COMPONENT_VERSION,
            "component_schema_version": COMPONENT_SCHEMA_VERSION,
            "source_snapshot_version": versions["source_snapshot_version"],
            "feature_schema_version": versions["feature_schema_version"],
            "generator_version": COMPONENT_GENERATOR_VERSION,
            "component_records_sha256": records_hash,
            "component_index_sha256": index_hash,
        },
    )
    component_manifest = {
        "authorization": {
            "authority": "EXPLICIT_TASK_032B_2E_USER_INSTRUCTION",
            "historical_task032b2b_record_status": "APPROVED_FOR_SNAPSHOT_RETRIEVAL",
            "scope": "COMPONENT_MATERIALIZATION_ONLY",
        },
        "component_id": COMPONENT_ID,
        "component_record_contract": {
            "entity_key": "EnsemblID",
            "feature_fidelity": "EXACT_TASK032B2D_STRING_VALUE_AND_MISSINGNESS",
            "feature_order": [row["feature_definition_id"] for row in dictionary],
            "provenance_cardinality": "ONE_OBJECT_PER_FEATURE_EVIDENCE_RECORD_RELATIONSHIP",
        },
        "component_release_id": component_release_id,
        "component_schema_version": COMPONENT_SCHEMA_VERSION,
        "component_version": COMPONENT_VERSION,
        "entity_count": audit.entity_count,
        "feature_count_per_entity": EXPECTED_FEATURE_COUNT,
        "feature_instance_count": audit.feature_instance_count,
        "frozen_inputs": frozen_before,
        "generator": {
            "sha256": script_hash,
            "version": COMPONENT_GENERATOR_VERSION,
        },
        "interpretation_boundary": "STRUCTURAL_EVIDENCE_REPRESENTATION_ONLY",
        "materialization_status": "MATERIALIZED_VALIDATION_CANDIDATE",
        "network_access": "PROHIBITED_NOT_USED",
        "output_artifacts": {
            "component_index.csv": {
                "row_count": len(index_rows),
                "size_bytes": len(index_payload),
                "sha256": index_hash,
            },
            "component_records.jsonl": {
                "row_count": audit.entity_count,
                "size_bytes": records_size,
                "sha256": records_hash,
            },
        },
        "provenance_relationship_count": audit.provenance_relationship_count,
        "source_snapshot_id": snapshot_manifest["snapshot_id"],
        "state_counts": dict(sorted(audit.state_counts.items())),
        "validation_status": "PASS",
        "version_axes": {
            "component_schema_version": COMPONENT_SCHEMA_VERSION,
            "component_version": COMPONENT_VERSION,
            "extractor_version": versions["extractor_version"],
            "feature_generator_version": versions["feature_generator_version"],
            "feature_schema_version": versions["feature_schema_version"],
            "generator_version": COMPONENT_GENERATOR_VERSION,
            "source_snapshot_version": versions["source_snapshot_version"],
            "state_rule_version": versions["state_rule_version"],
        },
    }
    manifest_hash = write_bytes(
        output_root / "component_manifest.json", pretty_json_bytes(component_manifest)
    )
    report = validation_report(
        len(frozen_before),
        len(local_snapshot_artifacts),
        audit,
        records_hash,
        index_hash,
        records_size,
        checks,
        versions,
    )
    report_hash = write_bytes(
        output_root / "component_validation_report.md", report.encode("utf-8")
    )
    session = "\n".join(
        [
            "Task: #032B-2E Disease Association Component Materialization",
            f"Component release ID: {component_release_id}",
            f"Component ID: {COMPONENT_ID}",
            f"Component version: {COMPONENT_VERSION}",
            f"Component schema version: {COMPONENT_SCHEMA_VERSION}",
            f"Component generator version: {COMPONENT_GENERATOR_VERSION}",
            f"Component generator SHA256: {script_hash}",
            f"Source snapshot version: {versions['source_snapshot_version']}",
            f"Feature schema version: {versions['feature_schema_version']}",
            f"Feature generator version: {versions['feature_generator_version']}",
            f"State rule version: {versions['state_rule_version']}",
            f"Extractor version: {versions['extractor_version']}",
            f"Python: {sys.version.replace(chr(10), ' ')}",
            f"Python executable: {sys.executable}",
            f"Platform: {platform.platform()}",
            "Network access: NONE",
            "Package installation: NONE",
            "Randomness: NONE",
            "Runtime AI/LLM decisions: NONE",
            "Live source access: NONE",
            "Wall-clock values in governed outputs: NONE",
            f"Component records SHA256: {records_hash}",
            f"Component index SHA256: {index_hash}",
            f"Component manifest SHA256: {manifest_hash}",
            f"Validation report SHA256: {report_hash}",
            "Profiles generated: FALSE",
            "Target evaluation performed: FALSE",
            "",
        ]
    )
    write_bytes(output_root / "session_info.txt", session.encode("utf-8"))

    frozen_after = verify_frozen_inputs(repo)
    if frozen_after != frozen_before:
        fail("Frozen inputs changed during component materialization")

    print(f"Component materialization complete: {component_release_id}")
    print(f"Entities: {audit.entity_count:,}")
    print(f"Feature instances: {audit.feature_instance_count:,}")
    print(f"Provenance relationships: {audit.provenance_relationship_count:,}")
    print(f"Component states: {dict(sorted(audit.state_counts.items()))}")
    print("Validation: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except MaterializationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
