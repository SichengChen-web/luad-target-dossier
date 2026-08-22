#!/usr/bin/env python3
"""Build normalized structural disease-association features from Task 032B-2C.

The extractor is offline and deterministic. It represents source-record
availability, structure, provenance, dependency, missingness, and governed
component states only. It does not expose source-native association metrics as
normalized values and does not score, rank, select, recommend, interpret, or
materialize target profiles.

Required runtime: Python with pyarrow. No package installation or network
access is performed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import platform
import re
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "pyarrow is required but is unavailable in this Python runtime. "
        "No installation is authorized. On the reviewed system run: "
        "/opt/anaconda3/bin/python "
        "analysis/32B2D_build_disease_association_feature_extractor.py"
    ) from exc


EXTRACTOR_VERSION = "DISEASE_ASSOCIATION_FEATURE_EXTRACTOR_V0.1"
GENERATOR_VERSION = "DISEASE_ASSOCIATION_FEATURE_GENERATOR_V0.1"
FEATURE_SCHEMA_VERSION = "DISEASE_ASSOCIATION_FEATURE_SCHEMA_V0.1"
STATE_RULE_VERSION = "DA_COMPONENT_STATE_RULES_V0.1"
COMPONENT_ID = "COMP_DISEASE_ASSOCIATION"
COMPONENT_VERSION = "COMP_DISEASE_ASSOCIATION_V0.1"
SOURCE_ID = "SRC_OPEN_TARGETS_PLATFORM"
SOURCE_VERSION = "26.06"
DISEASE_CONTEXT_ID = "MONDO_0005061"
UNIVERSE_ID = "UNIV_TASK030_ENSEMBL_29606_V0_1"
EXPECTED_ENTITIES = 29_606
SNAPSHOT_ROOT_RELATIVE = Path("outputs/disease_association_snapshot_v0.1")

MISSINGNESS_VOCABULARY = {
    "OBSERVED",
    "NOT_FOUND",
    "NOT_QUERIED",
    "NOT_APPLICABLE",
    "UNKNOWN",
}
STATE_VOCABULARY = {
    "OBSERVED",
    "PARTIAL",
    "CONFLICTING",
    "MISSING",
    "NOT_QUERIED",
}
STATE_PRECEDENCE = [
    "CONFLICTING",
    "OBSERVED",
    "MISSING",
    "PARTIAL",
    "NOT_QUERIED",
]
MAPPING_STATUS_VOCABULARY = {
    "RESOLVED",
    "NOT_REQUIRED",
    "UNRESOLVED",
    "CONFLICTING",
    "UNKNOWN",
}
DEPENDENCY_RELATIONSHIP_VOCABULARY = {
    "SAME_SOURCE",
    "SHARED_DATASET",
    "PARTIAL",
    "UNKNOWN",
    "INDEPENDENT",
    "NOT_APPLICABLE",
}
DEPENDENCY_LEVEL_VOCABULARY = {
    "DEPENDENT",
    "PARTIALLY_DEPENDENT",
    "UNKNOWN",
    "INDEPENDENT",
    "NOT_APPLICABLE",
}
FORBIDDEN_FIELD_NAMES = {
    "score",
    "evidence_score",
    "confidence_score",
    "confidence_metric",
    "target_quality",
    "importance",
    "rank",
    "ranking",
    "priority",
    "recommendation",
    "therapeutic_direction",
    "therapeutic_interpretation",
    "target_selection",
}

SNAPSHOT_SHA256 = {
    "analysis/32B2C_retrieve_disease_association_snapshot.py": "436c1135c5ecb133e461ca14dc07ebe6414ed87c220d7992f6e09cc8117e78bc",
    "outputs/disease_association_snapshot_v0.1/snapshot_manifest.json": "1bd2df46ad11528f3bbf4da8eb7c68a581277b92461586b942f660f9be00ae75",
    "outputs/disease_association_snapshot_v0.1/release_manifest.json": "b38a53665b7e17d65ce2f830063812094cd18a6c1a3861b3892b056ce259cf47",
    "outputs/disease_association_snapshot_v0.1/file_inventory.csv": "e425a6d9223686e27b4dbd69a83eb50d2e7352eb9b6eba14a11b8b471b5ed8e9",
    "outputs/disease_association_snapshot_v0.1/raw_record_manifest.csv": "ef94b3602f1b404df6c0090e45c533e22c4554fab0080a2ae5d7bfaca18ab0f4",
    "outputs/disease_association_snapshot_v0.1/entity_coverage_ledger.csv": "b0b7903c33a65f991150804722b832c0168f1156a703411e9d7a3c23c5e8202e",
    "outputs/disease_association_snapshot_v0.1/snapshot_qc_report.md": "078234cc85b02563737fdbdbc1f4078bff9bba7057db88a54e662b10c1d5e4b3",
    "outputs/disease_association_snapshot_v0.1/session_info.txt": "92738f23f34ca42718d3eb9ba0b869d5cd86323c1505f19ee5339da4d9682e03",
}

GOVERNANCE_SHA256 = {
    "docs/governance/evidence_component_interface_specification_v0.1.md": "b31254b347cbf440e3aade02857fb8149c54ea9a9a2b987197c4b724fefa20e8",
    "docs/governance/component_registration_policy_v0.1.md": "c1736e11695e6bb194665a0cf96115bb526075ca5aa9f9870e8e572f64302668",
    "docs/governance/component_validation_requirements_v0.1.md": "cc71c239972bc8f0b20fff63e4478624e0bcb56bc0febfc52855818ee5171c95",
    "docs/governance/component_dependency_model_v0.1.md": "5b77654a7ea543b2b2a184bba4a280cc4395c575065be6a3674d93a0955cdb06",
    "docs/governance/disease_association_component_registration_v0.1.md": "3f625be0234d234be9df555002cb48a1bf9afffc9b8b2e1ce9b51220df01c50a",
    "docs/governance/disease_association_component_scope_v0.1.md": "f153a296ba14fee53d142e836a0b07efddaf1793965cea04ce9ab46024a9faee",
    "docs/governance/disease_association_component_feature_contract_v0.1.md": "c4ead626b6e6f1616a0dc8e396d7a52495bb21523acd96567a98c50f3c6d9139",
    "docs/governance/disease_association_component_validation_plan_v0.1.md": "d96ad308cf2e795be2fcd8b3950491371709cc0a075386bcd8cdc1b9b1da4508",
    "docs/governance/disease_association_source_selection_record_v0.1.md": "45cb84646742945552d5741b85bdbec5e709584d1aaea68555720764146f8de8",
    "docs/governance/disease_context_registration_v0.1.md": "6df7b8c9cd0452d377a58b7d7819aa35a23ec620728000cc97b7fc3aad3f2460",
    "docs/governance/disease_association_materialization_authorization_v0.1.md": "f9c99bb420705e70fb1295ea6a3e400f285e5229a30cd4ea19ce1e93816ed8a5",
}

FROZEN_INPUT_SHA256 = {**GOVERNANCE_SHA256, **SNAPSHOT_SHA256}


class ExtractionError(RuntimeError):
    """Deterministic extraction or validation failure."""


def feature_definition(
    definition_id: str,
    name: str,
    category: str,
    data_type: str,
    allowed_values: str,
    state_input: bool,
    source_roles: str,
    rule_id: str,
    rule: str,
    missingness_rule: str,
    provenance_mode: str,
    empty_set_rule: str = "NOT_APPLICABLE_NON_SET_FEATURE",
) -> dict[str, str]:
    return {
        "feature_definition_id": definition_id,
        "feature_name": name,
        "feature_category": category,
        "data_type": data_type,
        "allowed_values": allowed_values,
        "state_input": "TRUE" if state_input else "FALSE",
        "source_roles": source_roles,
        "extraction_rule_id": rule_id,
        "extractor_version": EXTRACTOR_VERSION,
        "deterministic_extraction_rule": rule,
        "feature_missingness_rule": missingness_rule,
        "provenance_mode": provenance_mode,
        "empty_set_rule": empty_set_rule,
        "interpretation_boundary": (
            "Structural availability/audit representation only; not association "
            "strength, biological importance, target quality, or therapeutic meaning."
        ),
    }


FEATURE_DEFINITIONS = [
    feature_definition(
        "DAF_ASSESSMENT_ATTEMPTED_V0_1",
        "disease_association_assessment_attempted",
        "EVIDENCE_AVAILABILITY",
        "BOOLEAN",
        "TRUE|FALSE",
        True,
        "ROLE_QUERY_SCOPE_RECORD",
        "DAR_ASSESSMENT_ATTEMPTED_V0_1",
        "Copy the validated assessment_attempted Boolean from the entity coverage ledger.",
        "OBSERVED when the query-scope ledger row is valid; otherwise UNKNOWN.",
        "SCOPE_ONLY",
    ),
    feature_definition(
        "DAF_QUERY_SCOPE_COMPLETE_V0_1",
        "disease_association_query_scope_complete",
        "EVIDENCE_AVAILABILITY",
        "BOOLEAN",
        "TRUE|FALSE",
        True,
        "ROLE_QUERY_SCOPE_RECORD",
        "DAR_QUERY_SCOPE_COMPLETE_V0_1",
        "TRUE only when the frozen snapshot and per-entity coverage ledger both declare complete retrieval scope.",
        "OBSERVED when completion is resolved; otherwise UNKNOWN.",
        "SCOPE_ONLY",
    ),
    feature_definition(
        "DAF_RECORD_AVAILABILITY_V0_1",
        "disease_association_record_availability",
        "EVIDENCE_AVAILABILITY",
        "CONTROLLED_STRING",
        "RECORDS_PRESENT|NO_RECORDS_RETURNED|NOT_QUERIED|UNKNOWN",
        True,
        "ROLE_QUERY_SCOPE_RECORD|ROLE_DISEASE_ASSOCIATION_RECORD",
        "DAR_RECORD_AVAILABILITY_V0_1",
        "RECORDS_PRESENT when at least one reconciled in-scope record exists; NO_RECORDS_RETURNED after a complete attempted query with zero records; otherwise preserve NOT_QUERIED or UNKNOWN.",
        "The availability result itself is OBSERVED when resolved; UNKNOWN otherwise.",
        "SCOPE_AND_RECORDS",
    ),
    feature_definition(
        "DAF_RECORD_COUNT_V0_1",
        "disease_association_record_count",
        "STRUCTURAL_RECORD",
        "NON_NEGATIVE_INTEGER_AUDIT_METADATA",
        "INTEGER_GE_0",
        True,
        "ROLE_QUERY_SCOPE_RECORD|ROLE_DISEASE_ASSOCIATION_RECORD",
        "DAR_RECORD_COUNT_V0_1",
        "Count distinct (source_dataset, source_record_id) identities after exact-duplicate reconciliation; never treat the count as support or confidence.",
        "OBSERVED for a complete attempted query, including zero; otherwise UNKNOWN or NOT_QUERIED.",
        "SCOPE_AND_RECORDS",
    ),
    feature_definition(
        "DAF_RECORD_ROLE_SET_V0_1",
        "disease_association_record_role_set",
        "STRUCTURAL_RECORD",
        "CANONICAL_JSON_STRING_ARRAY",
        "ROLE_DISEASE_ASSOCIATION_RECORD",
        False,
        "ROLE_DISEASE_ASSOCIATION_RECORD",
        "DAR_RECORD_ROLE_SET_V0_1",
        "Emit the canonically sorted registered roles represented by returned raw association records.",
        "OBSERVED with records; NOT_FOUND after a completed zero-record query.",
        "RECORDS_OR_SCOPE",
        "Serialize [] with NOT_FOUND when no association record was returned.",
    ),
    feature_definition(
        "DAF_RECORD_GRANULARITY_SET_V0_1",
        "disease_association_record_granularity_set",
        "STRUCTURAL_RECORD",
        "CANONICAL_JSON_STRING_ARRAY",
        "SOURCE_ATOMIC|SOURCE_AGGREGATE|MIXED|UNKNOWN",
        False,
        "ROLE_DISEASE_ASSOCIATION_RECORD",
        "DAR_RECORD_GRANULARITY_SET_V0_1",
        "Emit [\"UNKNOWN\"] because the frozen Open Targets snapshot does not expose a reviewed record-level granularity field; do not infer atomicity from row count.",
        "UNKNOWN with records until source-specific granularity is governed; NOT_FOUND with zero records.",
        "RECORDS_OR_SCOPE",
        "Serialize [] with NOT_FOUND when no association record was returned.",
    ),
    feature_definition(
        "DAF_SOURCE_EVIDENCE_TYPE_SET_V0_1",
        "disease_association_source_evidence_type_id_set",
        "STRUCTURAL_RECORD",
        "CANONICAL_JSON_STRING_ARRAY",
        "SOURCE_NATIVE_DATATYPE_ID_STRINGS",
        False,
        "ROLE_DISEASE_ASSOCIATION_RECORD",
        "DAR_SOURCE_EVIDENCE_TYPE_SET_V0_1",
        "Extract source-native datatypeId strings from every contributing raw record and serialize the unique values in lexical order.",
        "OBSERVED when every record supplies datatypeId; UNKNOWN if any is unresolved; NOT_FOUND with zero records.",
        "RECORDS_OR_SCOPE",
        "Serialize [] with NOT_FOUND when no association record was returned.",
    ),
    feature_definition(
        "DAF_SOURCE_DISEASE_ID_SET_V0_1",
        "disease_association_source_disease_id_set",
        "STRUCTURAL_RECORD",
        "CANONICAL_JSON_STRING_ARRAY",
        "SOURCE_NATIVE_DISEASE_ID_STRINGS",
        False,
        "ROLE_DISEASE_ASSOCIATION_RECORD|ROLE_DISEASE_CONTEXT_MAPPING",
        "DAR_SOURCE_DISEASE_ID_SET_V0_1",
        "Serialize unique source_disease_id values from all contributing raw records in lexical order.",
        "OBSERVED with records; NOT_FOUND with zero records; UNKNOWN if a record identity is unresolved.",
        "RECORDS_OR_SCOPE",
        "Serialize [] with NOT_FOUND when no association record was returned.",
    ),
    feature_definition(
        "DAF_SOURCE_TARGET_ID_SET_V0_1",
        "disease_association_source_target_id_set",
        "STRUCTURAL_RECORD",
        "CANONICAL_JSON_STRING_ARRAY",
        "SOURCE_NATIVE_TARGET_ID_STRINGS",
        False,
        "ROLE_DISEASE_ASSOCIATION_RECORD|ROLE_TARGET_IDENTITY_MAPPING",
        "DAR_SOURCE_TARGET_ID_SET_V0_1",
        "Serialize unique source_target_id values from all contributing raw records in lexical order.",
        "OBSERVED with records; NOT_FOUND with zero records; UNKNOWN if a record identity is unresolved.",
        "RECORDS_OR_SCOPE",
        "Serialize [] with NOT_FOUND when no association record was returned.",
    ),
    feature_definition(
        "DAF_DISEASE_MAPPING_STATUS_V0_1",
        "disease_context_mapping_status",
        "MAPPING_STRUCTURE",
        "CONTROLLED_STRING",
        "RESOLVED|NOT_REQUIRED|UNRESOLVED|CONFLICTING|UNKNOWN",
        True,
        "ROLE_DISEASE_CONTEXT_MAPPING",
        "DAR_DISEASE_MAPPING_STATUS_V0_1",
        "RESOLVED only when every retained record and the frozen disease entity use exact MONDO_0005061 under the exact-only context rule.",
        "OBSERVED when mapping status is deterministically resolved, including a controlled unresolved/conflicting status.",
        "SCOPE_ONLY",
    ),
    feature_definition(
        "DAF_TARGET_MAPPING_STATUS_V0_1",
        "target_identity_mapping_status",
        "MAPPING_STRUCTURE",
        "CONTROLLED_STRING",
        "RESOLVED|NOT_REQUIRED|UNRESOLVED|CONFLICTING|UNKNOWN",
        True,
        "ROLE_TARGET_IDENTITY_MAPPING",
        "DAR_TARGET_MAPPING_STATUS_V0_1",
        "Translate frozen target outcomes: MAPPED to RESOLVED; NOT_FOUND or AMBIGUOUS to UNRESOLVED; preserve CONFLICTING and UNKNOWN.",
        "OBSERVED because the mapping outcome itself is explicit; it is not silently repaired.",
        "SCOPE_ONLY",
    ),
    feature_definition(
        "DAF_PROVENANCE_COMPLETE_V0_1",
        "disease_association_provenance_complete",
        "PROVENANCE",
        "BOOLEAN",
        "TRUE|FALSE",
        True,
        "ROLE_QUERY_SCOPE_RECORD|ROLE_DISEASE_ASSOCIATION_RECORD|ROLE_DISEASE_CONTEXT_MAPPING|ROLE_TARGET_IDENTITY_MAPPING",
        "DAR_PROVENANCE_COMPLETE_V0_1",
        "TRUE only when query scope, mappings, every record identity, source artifact, artifact hash, and raw payload hash resolve.",
        "OBSERVED when the completeness check executes; UNKNOWN if required lineage cannot be tested.",
        "SCOPE_AND_RECORDS",
    ),
    feature_definition(
        "DAF_DEPENDENCY_COMPLETE_V0_1",
        "disease_association_dependency_complete",
        "DEPENDENCY_STRUCTURE",
        "BOOLEAN",
        "TRUE|FALSE",
        True,
        "ROLE_DEPENDENCY_ASSERTION",
        "DAR_DEPENDENCY_COMPLETE_V0_1",
        "TRUE only when every record has a deterministic SAME_SOURCE/SHARED_DATASET relationship or an explicit NOT_APPLICABLE sentinel.",
        "OBSERVED when dependency classification executes; UNKNOWN if a record remains unclassified.",
        "RECORDS_OR_SCOPE",
    ),
    feature_definition(
        "DAF_DEPENDENCY_STATUS_SET_V0_1",
        "disease_association_dependency_status_set",
        "DEPENDENCY_STRUCTURE",
        "CANONICAL_JSON_STRING_ARRAY",
        "SAME_SOURCE|SHARED_DATASET|PARTIAL|UNKNOWN|INDEPENDENT|NOT_APPLICABLE",
        False,
        "ROLE_DEPENDENCY_ASSERTION",
        "DAR_DEPENDENCY_STATUS_SET_V0_1",
        "Emit NOT_APPLICABLE for fewer than two records; otherwise SAME_SOURCE and, when at least two records share source_dataset, SHARED_DATASET. Never infer independence.",
        "OBSERVED when all relationships are classified; UNKNOWN otherwise.",
        "RECORDS_OR_SCOPE",
        "Serialize [\"NOT_APPLICABLE\"] when fewer than two records make pairwise dependency inapplicable.",
    ),
    feature_definition(
        "DAF_CONFLICT_COUNT_V0_1",
        "disease_association_structural_conflict_count",
        "STRUCTURAL_CONFLICT_AUDIT",
        "NON_NEGATIVE_INTEGER_AUDIT_METADATA",
        "INTEGER_GE_0",
        True,
        "ROLE_QUERY_SCOPE_RECORD|ROLE_DISEASE_ASSOCIATION_RECORD|ROLE_DISEASE_CONTEXT_MAPPING|ROLE_TARGET_IDENTITY_MAPPING",
        "DAR_CONFLICT_COUNT_V0_1",
        "Count only incompatible payloads sharing one (source_dataset, source_record_id), conflicting target mappings, or conflicting disease mapping; never encode biological disagreement.",
        "OBSERVED when reconciliation completes; UNKNOWN otherwise.",
        "SCOPE_AND_RECORDS",
    ),
    feature_definition(
        "DAF_PARTIAL_CONDITION_COUNT_V0_1",
        "disease_association_partial_condition_count",
        "STRUCTURAL_COMPLETENESS_AUDIT",
        "NON_NEGATIVE_INTEGER_AUDIT_METADATA",
        "INTEGER_GE_0",
        True,
        "ROLE_QUERY_SCOPE_RECORD|ROLE_DISEASE_ASSOCIATION_RECORD|ROLE_DISEASE_CONTEXT_MAPPING|ROLE_TARGET_IDENTITY_MAPPING|ROLE_DEPENDENCY_ASSERTION",
        "DAR_PARTIAL_CONDITION_COUNT_V0_1",
        "Count registered incomplete query, mapping, provenance, dependency, retrieval, or coverage conditions; do not count missing records after a complete resolved query.",
        "OBSERVED when completeness reconciliation executes; UNKNOWN otherwise.",
        "SCOPE_AND_RECORDS",
    ),
    feature_definition(
        "DAF_RETRIEVAL_FAILURE_V0_1",
        "disease_association_retrieval_failure",
        "EVIDENCE_AVAILABILITY",
        "BOOLEAN",
        "TRUE|FALSE",
        True,
        "ROLE_QUERY_SCOPE_RECORD",
        "DAR_RETRIEVAL_FAILURE_V0_1",
        "FALSE only when the frozen snapshot is COMPLETE and the entity coverage row records an attempted complete source operation.",
        "OBSERVED when retrieval status resolves; UNKNOWN otherwise.",
        "SCOPE_ONLY",
    ),
    feature_definition(
        "DAF_UNKNOWN_COVERAGE_V0_1",
        "disease_association_unknown_coverage",
        "EVIDENCE_AVAILABILITY",
        "BOOLEAN",
        "TRUE|FALSE",
        True,
        "ROLE_QUERY_SCOPE_RECORD",
        "DAR_UNKNOWN_COVERAGE_V0_1",
        "TRUE when required per-entity or snapshot coverage cannot be resolved; otherwise FALSE after complete reconciliation.",
        "OBSERVED when coverage status resolves; UNKNOWN otherwise.",
        "SCOPE_ONLY",
    ),
    feature_definition(
        "DAF_RECORDS_MISSINGNESS_V0_1",
        "disease_association_records_missingness_status",
        "MISSINGNESS",
        "CONTROLLED_STRING",
        "OBSERVED|NOT_FOUND|NOT_QUERIED|NOT_APPLICABLE|UNKNOWN",
        True,
        "ROLE_QUERY_SCOPE_RECORD|ROLE_DISEASE_ASSOCIATION_RECORD",
        "DAR_RECORDS_MISSINGNESS_V0_1",
        "OBSERVED with qualifying records; NOT_FOUND after a complete resolved zero-record query; NOT_QUERIED when unattempted; otherwise UNKNOWN.",
        "The missingness-status feature itself is OBSERVED when its controlled value is deterministically assigned.",
        "SCOPE_AND_RECORDS",
    ),
]

FEATURE_DICTIONARY_FIELDS = list(FEATURE_DEFINITIONS[0])
FEATURE_NAMES = [item["feature_name"] for item in FEATURE_DEFINITIONS]
MISSINGNESS_COLUMNS = [f"{name}__missingness_status" for name in FEATURE_NAMES]
FEATURE_OUTPUT_FIELDS = [
    "EnsemblID",
    "component_state",
    *FEATURE_NAMES,
    *MISSINGNESS_COLUMNS,
    "component_id",
    "component_version",
    "feature_schema_version",
    "source_snapshot_version",
    "state_rule_version",
    "extractor_version",
]
PROVENANCE_FIELDS = [
    "feature_id",
    "EnsemblID",
    "feature_definition_id",
    "feature_name",
    "feature_value_sha256",
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
    "feature_missingness_status",
    "extraction_rule_id",
    "extractor_version",
]


def find_repo_root() -> Path:
    script = Path(__file__).resolve()
    for candidate in [script.parent, *script.parents]:
        if (candidate / ".git").exists() and (candidate / "analysis").exists():
            return candidate
    raise ExtractionError("Could not resolve repository root")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    )


def pretty_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def stable_id(prefix: str, payload: Any, length: int = 24) -> str:
    digest = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    return f"{prefix}_{digest[:length].upper()}"


def bool_string(value: bool) -> str:
    return "TRUE" if value else "FALSE"


def parse_bool(value: str, field: str) -> bool:
    if value == "TRUE":
        return True
    if value == "FALSE":
        return False
    raise ExtractionError(f"Invalid Boolean {field}={value!r}")


def csv_bytes(rows: Iterable[dict[str, Any]], fields: Sequence[str]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=list(fields), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fields})
    return output.getvalue().encode("utf-8")


def write_bytes(path: Path, payload: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    if path.read_bytes() != payload:
        raise ExtractionError(f"Write verification failed: {path}")
    return hashlib.sha256(payload).hexdigest()


def verify_frozen_inputs(repo: Path) -> dict[str, str]:
    observed: dict[str, str] = {}
    for relative, expected in FROZEN_INPUT_SHA256.items():
        path = repo / relative
        if not path.is_file():
            raise ExtractionError(f"Frozen input missing: {relative}")
        actual = sha256_file(path)
        if actual != expected:
            raise ExtractionError(
                f"Frozen input hash mismatch: {relative}: {actual} != {expected}"
            )
        observed[relative] = actual
    return observed


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate_snapshot_raw_files(
    repo: Path,
    snapshot_root: Path,
    file_inventory: list[dict[str, str]],
) -> dict[str, dict[str, str]]:
    raw_inventory: dict[str, dict[str, str]] = {}
    for row in file_inventory:
        if row["artifact_role"] != "SNAPSHOT_RAW_FILE":
            continue
        relative = row["relative_path_or_reference"]
        path = snapshot_root / relative
        if not path.is_file():
            raise ExtractionError(f"Raw snapshot artifact missing: {relative}")
        if path.stat().st_size != int(row["file_size_bytes"]):
            raise ExtractionError(f"Raw snapshot size mismatch: {relative}")
        if sha256_file(path) != row["sha256"]:
            raise ExtractionError(f"Raw snapshot SHA256 mismatch: {relative}")
        if relative in raw_inventory:
            raise ExtractionError(f"Duplicate raw artifact inventory path: {relative}")
        raw_inventory[relative] = row
    if not raw_inventory:
        raise ExtractionError("No retained raw snapshot files found")
    return raw_inventory


def enrich_raw_records_from_parquet(
    snapshot_root: Path,
    raw_records: list[dict[str, str]],
    raw_inventory: dict[str, dict[str, str]],
) -> None:
    by_file: dict[str, dict[tuple[int, int], dict[str, str]]] = defaultdict(dict)
    for row in raw_records:
        relative = row["snapshot_raw_file"]
        position = (int(row["snapshot_row_group"]), int(row["snapshot_row_index"]))
        if position in by_file[relative]:
            raise ExtractionError(f"Duplicate raw snapshot position: {relative} {position}")
        by_file[relative][position] = row
    evidence_inventory_paths = {
        path for path in raw_inventory if path.startswith("raw/evidence/")
    }
    if set(by_file) != evidence_inventory_paths:
        raise ExtractionError("Raw record manifest and evidence Parquet inventory differ")

    for relative in sorted(by_file):
        path = snapshot_root / relative
        parquet_file = pq.ParquetFile(path)
        if "id" not in parquet_file.schema_arrow.names or "datatypeId" not in parquet_file.schema_arrow.names:
            raise ExtractionError(f"Required structural fields absent: {relative}")
        visited: set[tuple[int, int]] = set()
        for row_group in range(parquet_file.num_row_groups):
            table = parquet_file.read_row_group(row_group, columns=["id", "datatypeId"])
            for row_index, record in enumerate(table.to_pylist()):
                position = (row_group, row_index)
                manifest_row = by_file[relative].get(position)
                if manifest_row is None:
                    raise ExtractionError(
                        f"Parquet row missing raw-record manifest lineage: {relative} {position}"
                    )
                if str(record["id"]) != manifest_row["source_record_id"]:
                    raise ExtractionError(f"Source record identity mismatch: {relative} {position}")
                datatype_id = record.get("datatypeId")
                manifest_row["datatypeId"] = "" if datatype_id is None else str(datatype_id)
                visited.add(position)
        if visited != set(by_file[relative]):
            raise ExtractionError(f"Raw record positions unresolved: {relative}")


def target_mapping_status(outcome: str) -> str:
    mapping = {
        "MAPPED": "RESOLVED",
        "NOT_FOUND": "UNRESOLVED",
        "AMBIGUOUS": "UNRESOLVED",
        "CONFLICTING": "CONFLICTING",
        "UNKNOWN": "UNKNOWN",
    }
    if outcome not in mapping:
        raise ExtractionError(f"Unknown frozen target mapping outcome: {outcome}")
    return mapping[outcome]


def reconcile_records(records: list[dict[str, str]]) -> tuple[list[dict[str, str]], int]:
    identities: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for record in records:
        identities[(record["source_dataset"], record["source_record_id"])].append(record)
    reconciled: list[dict[str, str]] = []
    conflict_count = 0
    for identity in sorted(identities):
        members = sorted(identities[identity], key=lambda row: row["raw_record_id"])
        payloads = {row["raw_payload_sha256"] for row in members}
        if len(payloads) > 1:
            conflict_count += 1
        reconciled.append(members[0])
    return reconciled, conflict_count


def dependency_context(records: list[dict[str, str]]) -> tuple[list[str], dict[str, tuple[list[str], str, str]]]:
    dataset_counts = Counter(record["source_dataset"] for record in records)
    per_record: dict[str, tuple[list[str], str, str]] = {}
    if len(records) < 2:
        statuses = ["NOT_APPLICABLE"]
        for record in records:
            relationships = ["NOT_APPLICABLE"]
            level = "NOT_APPLICABLE"
            dependency_id = stable_id(
                "DEP_DA",
                {
                    "raw_record_id": record["raw_record_id"],
                    "relationships": relationships,
                    "level": level,
                },
            )
            per_record[record["raw_record_id"]] = (
                relationships,
                level,
                dependency_id,
            )
        return statuses, per_record

    status_set = {"SAME_SOURCE"}
    if any(count > 1 for count in dataset_counts.values()):
        status_set.add("SHARED_DATASET")
    for record in records:
        relationships = ["SAME_SOURCE"]
        if dataset_counts[record["source_dataset"]] > 1:
            relationships.append("SHARED_DATASET")
        relationships = sorted(relationships)
        dependency_id = stable_id(
            "DEP_DA",
            {
                "EnsemblID": record["universe_EnsemblID"],
                "raw_record_id": record["raw_record_id"],
                "relationships": relationships,
                "level": "DEPENDENT",
            },
        )
        per_record[record["raw_record_id"]] = (
            relationships,
            "DEPENDENT",
            dependency_id,
        )
    return sorted(status_set), per_record


def evaluate_component_state(values: dict[str, Any]) -> tuple[str, dict[str, bool]]:
    disease_mapping_ok = values["disease_context_mapping_status"] in {
        "RESOLVED",
        "NOT_REQUIRED",
    }
    target_mapping_ok = values["target_identity_mapping_status"] in {
        "RESOLVED",
        "NOT_REQUIRED",
    }
    mapping_conflict = (
        values["disease_context_mapping_status"] == "CONFLICTING"
        or values["target_identity_mapping_status"] == "CONFLICTING"
    )
    predicates = {
        "CONFLICTING": values["disease_association_structural_conflict_count"] > 0
        or mapping_conflict,
        "OBSERVED": all(
            [
                values["disease_association_assessment_attempted"],
                values["disease_association_query_scope_complete"],
                values["disease_association_record_availability"] == "RECORDS_PRESENT",
                values["disease_association_record_count"] > 0,
                values["disease_association_records_missingness_status"] == "OBSERVED",
                disease_mapping_ok,
                target_mapping_ok,
                values["disease_association_provenance_complete"],
                values["disease_association_dependency_complete"],
                values["disease_association_partial_condition_count"] == 0,
                not values["disease_association_retrieval_failure"],
                not values["disease_association_unknown_coverage"],
            ]
        ),
        "MISSING": all(
            [
                values["disease_association_assessment_attempted"],
                values["disease_association_query_scope_complete"],
                values["disease_association_record_availability"]
                == "NO_RECORDS_RETURNED",
                values["disease_association_record_count"] == 0,
                values["disease_association_records_missingness_status"] == "NOT_FOUND",
                disease_mapping_ok,
                target_mapping_ok,
                values["disease_association_provenance_complete"],
                not values["disease_association_retrieval_failure"],
                not values["disease_association_unknown_coverage"],
            ]
        ),
        "PARTIAL": values["disease_association_assessment_attempted"]
        and any(
            [
                not values["disease_association_query_scope_complete"],
                values["disease_association_retrieval_failure"],
                values["disease_association_unknown_coverage"],
                values["disease_association_partial_condition_count"] > 0,
                values["target_identity_mapping_status"] in {"UNRESOLVED", "UNKNOWN"},
                values["disease_context_mapping_status"] in {"UNRESOLVED", "UNKNOWN"},
                not values["disease_association_provenance_complete"],
                not values["disease_association_dependency_complete"],
            ]
        ),
        "NOT_QUERIED": all(
            [
                not values["disease_association_assessment_attempted"],
                values["disease_association_record_availability"] == "NOT_QUERIED",
                values["disease_association_record_count"] == 0,
                values["disease_association_records_missingness_status"]
                == "NOT_QUERIED",
            ]
        ),
    }
    matches = [state for state in STATE_PRECEDENCE if predicates[state]]
    if not matches:
        raise ExtractionError(f"No component-state predicate matched: {values}")
    return matches[0], predicates


def state_fixtures() -> list[dict[str, Any]]:
    base = {
        "disease_association_assessment_attempted": True,
        "disease_association_query_scope_complete": True,
        "disease_association_record_availability": "RECORDS_PRESENT",
        "disease_association_record_count": 1,
        "disease_context_mapping_status": "RESOLVED",
        "target_identity_mapping_status": "RESOLVED",
        "disease_association_provenance_complete": True,
        "disease_association_dependency_complete": True,
        "disease_association_structural_conflict_count": 0,
        "disease_association_partial_condition_count": 0,
        "disease_association_retrieval_failure": False,
        "disease_association_unknown_coverage": False,
        "disease_association_records_missingness_status": "OBSERVED",
    }
    fixtures: list[tuple[str, str, dict[str, Any]]] = []
    fixtures.append(("FIX_OBSERVED", "OBSERVED", dict(base)))
    missing = dict(base)
    missing.update(
        disease_association_record_availability="NO_RECORDS_RETURNED",
        disease_association_record_count=0,
        disease_association_records_missingness_status="NOT_FOUND",
    )
    fixtures.append(("FIX_MISSING", "MISSING", missing))
    partial = dict(missing)
    partial.update(
        target_identity_mapping_status="UNRESOLVED",
        disease_association_partial_condition_count=1,
    )
    fixtures.append(("FIX_PARTIAL", "PARTIAL", partial))
    not_queried = dict(missing)
    not_queried.update(
        disease_association_assessment_attempted=False,
        disease_association_query_scope_complete=False,
        disease_association_record_availability="NOT_QUERIED",
        disease_association_records_missingness_status="NOT_QUERIED",
        disease_context_mapping_status="UNKNOWN",
        target_identity_mapping_status="UNKNOWN",
        disease_association_provenance_complete=False,
        disease_association_dependency_complete=False,
    )
    fixtures.append(("FIX_NOT_QUERIED", "NOT_QUERIED", not_queried))
    conflicting = dict(base)
    conflicting["disease_association_structural_conflict_count"] = 1
    fixtures.append(("FIX_CONFLICTING", "CONFLICTING", conflicting))
    conflict_over_partial = dict(partial)
    conflict_over_partial["disease_association_structural_conflict_count"] = 1
    fixtures.append(
        ("FIX_CONFLICT_PRECEDENCE_OVER_PARTIAL", "CONFLICTING", conflict_over_partial)
    )
    results = []
    for fixture_id, expected, values in fixtures:
        observed, predicates = evaluate_component_state(values)
        results.append(
            {
                "fixture_id": fixture_id,
                "expected_state": expected,
                "observed_state": observed,
                "passed": observed == expected,
                "matching_predicates": [
                    state for state in STATE_PRECEDENCE if predicates[state]
                ],
            }
        )
    return results


def build_entity_context(
    coverage: dict[str, str],
    records: list[dict[str, str]],
    snapshot_complete: bool,
    artifact_by_path: dict[str, dict[str, str]],
) -> dict[str, Any]:
    reconciled, duplicate_conflicts = reconcile_records(records)
    expected_count = int(coverage["exact_disease_record_count"])
    if expected_count != len(records):
        raise ExtractionError(
            f"Coverage/raw-record count mismatch for {coverage['EnsemblID']}: "
            f"{expected_count} != {len(records)}"
        )
    assessment_attempted = parse_bool(
        coverage["assessment_attempted"], "assessment_attempted"
    )
    scope_complete = (
        snapshot_complete
        and parse_bool(coverage["source_release_complete"], "source_release_complete")
    )
    retrieval_failure = assessment_attempted and not scope_complete
    unknown_coverage = not assessment_attempted or not scope_complete
    target_status = target_mapping_status(coverage["target_mapping_outcome"])
    disease_status = "RESOLVED"

    record_provenance_complete = True
    for record in records:
        required = [
            "raw_record_id",
            "source_record_id",
            "source_file_sha256",
            "snapshot_raw_file",
            "snapshot_raw_file_sha256",
            "raw_payload_sha256",
            "datatypeId",
        ]
        if any(not record.get(field, "") for field in required):
            record_provenance_complete = False
        inventory = artifact_by_path.get(record["snapshot_raw_file"])
        if inventory is None or inventory["sha256"] != record["snapshot_raw_file_sha256"]:
            record_provenance_complete = False
    query_provenance_complete = coverage["provenance_complete"] == "TRUE"
    provenance_complete = query_provenance_complete and record_provenance_complete

    dependency_statuses, record_dependencies = dependency_context(records)
    dependency_complete = len(record_dependencies) == len(records)
    record_count = len(reconciled)
    if not assessment_attempted:
        availability = "NOT_QUERIED"
        collection_missingness = "NOT_QUERIED"
    elif not scope_complete:
        availability = "UNKNOWN"
        collection_missingness = "UNKNOWN"
    elif record_count > 0:
        availability = "RECORDS_PRESENT"
        collection_missingness = "OBSERVED"
    else:
        availability = "NO_RECORDS_RETURNED"
        collection_missingness = "NOT_FOUND"

    mapping_conflict_count = int(target_status == "CONFLICTING") + int(
        disease_status == "CONFLICTING"
    )
    conflict_count = duplicate_conflicts + mapping_conflict_count
    partial_conditions = 0
    partial_conditions += int(not scope_complete)
    partial_conditions += int(target_status in {"UNRESOLVED", "UNKNOWN"})
    partial_conditions += int(disease_status in {"UNRESOLVED", "UNKNOWN"})
    partial_conditions += int(not provenance_complete)
    partial_conditions += int(not dependency_complete)
    partial_conditions += int(retrieval_failure)
    partial_conditions += int(unknown_coverage)

    evidence_types = sorted(
        {record["datatypeId"] for record in records if record.get("datatypeId")}
    )
    evidence_type_unknown = any(not record.get("datatypeId") for record in records)
    source_disease_ids = sorted({record["source_disease_id"] for record in records})
    source_target_ids = sorted({record["source_target_id"] for record in records})

    values: dict[str, Any] = {
        "disease_association_assessment_attempted": assessment_attempted,
        "disease_association_query_scope_complete": scope_complete,
        "disease_association_record_availability": availability,
        "disease_association_record_count": record_count,
        "disease_association_record_role_set": (
            ["ROLE_DISEASE_ASSOCIATION_RECORD"] if records else []
        ),
        "disease_association_record_granularity_set": ["UNKNOWN"] if records else [],
        "disease_association_source_evidence_type_id_set": evidence_types,
        "disease_association_source_disease_id_set": source_disease_ids,
        "disease_association_source_target_id_set": source_target_ids,
        "disease_context_mapping_status": disease_status,
        "target_identity_mapping_status": target_status,
        "disease_association_provenance_complete": provenance_complete,
        "disease_association_dependency_complete": dependency_complete,
        "disease_association_dependency_status_set": dependency_statuses,
        "disease_association_structural_conflict_count": conflict_count,
        "disease_association_partial_condition_count": partial_conditions,
        "disease_association_retrieval_failure": retrieval_failure,
        "disease_association_unknown_coverage": unknown_coverage,
        "disease_association_records_missingness_status": collection_missingness,
    }
    missingness: dict[str, str] = {name: "OBSERVED" for name in FEATURE_NAMES}
    record_set_features = {
        "disease_association_record_role_set",
        "disease_association_record_granularity_set",
        "disease_association_source_evidence_type_id_set",
        "disease_association_source_disease_id_set",
        "disease_association_source_target_id_set",
    }
    if not records:
        for name in record_set_features:
            missingness[name] = collection_missingness
    else:
        missingness["disease_association_record_granularity_set"] = "UNKNOWN"
        if evidence_type_unknown:
            missingness["disease_association_source_evidence_type_id_set"] = "UNKNOWN"
    state, predicates = evaluate_component_state(values)
    return {
        "EnsemblID": coverage["EnsemblID"],
        "coverage": coverage,
        "records": records,
        "reconciled_records": reconciled,
        "record_dependencies": record_dependencies,
        "values": values,
        "missingness": missingness,
        "component_state": state,
        "state_predicates": predicates,
    }


def serialize_feature_value(value: Any) -> str:
    if isinstance(value, bool):
        return bool_string(value)
    if isinstance(value, list):
        return canonical_json(value)
    return str(value)


def feature_instance_id(
    ensembl_id: str, definition_id: str, source_snapshot_version: str
) -> str:
    return stable_id(
        "FTR_DA",
        {
            "EnsemblID": ensembl_id,
            "feature_definition_id": definition_id,
            "source_snapshot_version": source_snapshot_version,
        },
    )


def feature_claim_id(feature_id: str, value_sha256: str) -> str:
    return stable_id(
        "CLM_DA",
        {"feature_id": feature_id, "feature_value_sha256": value_sha256},
    )


def scope_evidence_record_id(ensembl_id: str, snapshot_id: str) -> str:
    return stable_id(
        "REC_DA_SCOPE",
        {"EnsemblID": ensembl_id, "snapshot_id": snapshot_id},
    )


def scope_dependency_id(ensembl_id: str) -> str:
    return stable_id(
        "DEP_DA_SCOPE",
        {"EnsemblID": ensembl_id, "relationship": "NOT_APPLICABLE"},
    )


def make_feature_rows(
    contexts: list[dict[str, Any]], source_snapshot_version: str
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for context in contexts:
        output: dict[str, str] = {
            "EnsemblID": context["EnsemblID"],
            "component_state": context["component_state"],
        }
        for definition in FEATURE_DEFINITIONS:
            name = definition["feature_name"]
            output[name] = serialize_feature_value(context["values"][name])
            output[f"{name}__missingness_status"] = context["missingness"][name]
        output.update(
            component_id=COMPONENT_ID,
            component_version=COMPONENT_VERSION,
            feature_schema_version=FEATURE_SCHEMA_VERSION,
            source_snapshot_version=source_snapshot_version,
            state_rule_version=STATE_RULE_VERSION,
            extractor_version=EXTRACTOR_VERSION,
        )
        rows.append(output)
    return rows


def provenance_rows(
    contexts: list[dict[str, Any]],
    source_snapshot_version: str,
    snapshot_id: str,
    coverage_artifact_id: str,
    coverage_artifact_sha256: str,
    artifact_by_path: dict[str, dict[str, str]],
) -> Iterator[dict[str, str]]:
    for context in contexts:
        ensembl_id = context["EnsemblID"]
        records = context["records"]
        for definition in FEATURE_DEFINITIONS:
            name = definition["feature_name"]
            value = serialize_feature_value(context["values"][name])
            value_sha256 = hashlib.sha256(value.encode("utf-8")).hexdigest()
            feature_id = feature_instance_id(
                ensembl_id,
                definition["feature_definition_id"],
                source_snapshot_version,
            )
            claim_id = feature_claim_id(feature_id, value_sha256)
            mode = definition["provenance_mode"]
            include_scope = mode in {"SCOPE_ONLY", "SCOPE_AND_RECORDS"} or (
                mode == "RECORDS_OR_SCOPE" and not records
            )
            include_records = mode in {"SCOPE_AND_RECORDS", "RECORDS_OR_SCOPE"} and bool(
                records
            )
            if include_scope:
                yield {
                    "feature_id": feature_id,
                    "EnsemblID": ensembl_id,
                    "feature_definition_id": definition["feature_definition_id"],
                    "feature_name": name,
                    "feature_value_sha256": value_sha256,
                    "claim_id": claim_id,
                    "evidence_record_id": scope_evidence_record_id(
                        ensembl_id, snapshot_id
                    ),
                    "raw_record_id": "NOT_APPLICABLE_QUERY_SCOPE_RECORD",
                    "source_record_id": f"QUERY_SCOPE::{ensembl_id}",
                    "source_id": SOURCE_ID,
                    "source_version": SOURCE_VERSION,
                    "snapshot_id": snapshot_id,
                    "source_snapshot_version": source_snapshot_version,
                    "artifact_id": coverage_artifact_id,
                    "artifact_sha256": coverage_artifact_sha256,
                    "source_dataset": "entity_coverage_ledger",
                    "source_role": "ROLE_QUERY_SCOPE_RECORD",
                    "dependency_id": scope_dependency_id(ensembl_id),
                    "dependency_relationship_types": canonical_json(
                        ["NOT_APPLICABLE"]
                    ),
                    "dependency_level": "NOT_APPLICABLE",
                    "feature_missingness_status": context["missingness"][name],
                    "extraction_rule_id": definition["extraction_rule_id"],
                    "extractor_version": EXTRACTOR_VERSION,
                }
            if include_records:
                for record in records:
                    artifact = artifact_by_path[record["snapshot_raw_file"]]
                    relationships, dependency_level, dependency_id = context[
                        "record_dependencies"
                    ][record["raw_record_id"]]
                    yield {
                        "feature_id": feature_id,
                        "EnsemblID": ensembl_id,
                        "feature_definition_id": definition["feature_definition_id"],
                        "feature_name": name,
                        "feature_value_sha256": value_sha256,
                        "claim_id": claim_id,
                        "evidence_record_id": record["raw_record_id"],
                        "raw_record_id": record["raw_record_id"],
                        "source_record_id": record["source_record_id"],
                        "source_id": record["source_id"],
                        "source_version": record["source_version"],
                        "snapshot_id": snapshot_id,
                        "source_snapshot_version": source_snapshot_version,
                        "artifact_id": artifact["inventory_id"],
                        "artifact_sha256": artifact["sha256"],
                        "source_dataset": record["source_dataset"],
                        "source_role": "ROLE_DISEASE_ASSOCIATION_RECORD",
                        "dependency_id": dependency_id,
                        "dependency_relationship_types": canonical_json(relationships),
                        "dependency_level": dependency_level,
                        "feature_missingness_status": context["missingness"][name],
                        "extraction_rule_id": definition["extraction_rule_id"],
                        "extractor_version": EXTRACTOR_VERSION,
                    }


def write_provenance(
    path: Path,
    row_iterator: Iterable[dict[str, str]],
) -> tuple[str, int]:
    path.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    row_count = 0
    with path.open("w", newline="", encoding="utf-8") as handle:
        class HashingWriter:
            def write(self, text: str) -> int:
                digest.update(text.encode("utf-8"))
                return handle.write(text)

        writer = csv.DictWriter(
            HashingWriter(), fieldnames=PROVENANCE_FIELDS, lineterminator="\n"
        )
        writer.writeheader()
        for row in row_iterator:
            writer.writerow({field: row.get(field, "") for field in PROVENANCE_FIELDS})
            row_count += 1
    if sha256_file(path) != digest.hexdigest():
        raise ExtractionError("Streaming provenance hash mismatch")
    return digest.hexdigest(), row_count


def validate_provenance_file(
    path: Path,
    contexts: list[dict[str, Any]],
    source_snapshot_version: str,
) -> tuple[int, int]:
    raw_ids = {
        record["raw_record_id"]
        for context in contexts
        for record in context["records"]
    }
    expected_feature_instances = len(contexts) * len(FEATURE_DEFINITIONS)
    observed_feature_instances = 0
    current_feature = None
    current_evidence_ids: set[str] = set()
    row_count = 0
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != PROVENANCE_FIELDS:
            raise ExtractionError("Provenance header mismatch")
        for row in reader:
            row_count += 1
            if row["feature_id"] != current_feature:
                if current_feature is not None and not current_evidence_ids:
                    raise ExtractionError(f"Feature without provenance: {current_feature}")
                current_feature = row["feature_id"]
                current_evidence_ids = set()
                observed_feature_instances += 1
            if row["evidence_record_id"] in current_evidence_ids:
                raise ExtractionError(
                    "Duplicate (feature_id, evidence_record_id) relationship"
                )
            current_evidence_ids.add(row["evidence_record_id"])
            if row["raw_record_id"] != "NOT_APPLICABLE_QUERY_SCOPE_RECORD":
                if row["raw_record_id"] not in raw_ids:
                    raise ExtractionError("Broken raw-record lineage")
                if row["evidence_record_id"] != row["raw_record_id"]:
                    raise ExtractionError("Raw/evidence record identity mismatch")
            if row["feature_missingness_status"] not in MISSINGNESS_VOCABULARY:
                raise ExtractionError("Invalid provenance missingness")
            relationships = json.loads(row["dependency_relationship_types"])
            if not set(relationships).issubset(DEPENDENCY_RELATIONSHIP_VOCABULARY):
                raise ExtractionError("Invalid dependency relationship")
            if row["dependency_level"] not in DEPENDENCY_LEVEL_VOCABULARY:
                raise ExtractionError("Invalid dependency level")
            if row["source_snapshot_version"] != source_snapshot_version:
                raise ExtractionError("Provenance source snapshot mismatch")
    if observed_feature_instances != expected_feature_instances:
        raise ExtractionError(
            f"Provenance feature coverage mismatch: {observed_feature_instances} "
            f"!= {expected_feature_instances}"
        )
    return row_count, observed_feature_instances


def validation_report(
    source_snapshot_version: str,
    feature_sha256: str,
    dictionary_sha256: str,
    provenance_sha256: str,
    feature_rows: list[dict[str, str]],
    provenance_rows_count: int,
    fixtures: list[dict[str, Any]],
    checks: Sequence[tuple[str, bool, str]],
) -> str:
    status = "PASS" if all(passed for _, passed, _ in checks) else "FAIL"
    states = Counter(row["component_state"] for row in feature_rows)
    missingness = Counter(
        row[column] for row in feature_rows for column in MISSINGNESS_COLUMNS
    )
    check_lines = "\n".join(
        f"- {'PASS' if passed else 'FAIL'} — `{name}`: {detail}"
        for name, passed, detail in checks
    )
    fixture_lines = "\n".join(
        f"- {'PASS' if item['passed'] else 'FAIL'} — `{item['fixture_id']}`: "
        f"expected `{item['expected_state']}`, observed `{item['observed_state']}`"
        for item in fixtures
    )
    state_lines = "\n".join(
        f"- `{state}`: {states.get(state, 0):,}" for state in STATE_PRECEDENCE
    )
    missingness_lines = "\n".join(
        f"- `{value}`: {missingness.get(value, 0):,}"
        for value in ["OBSERVED", "NOT_FOUND", "NOT_QUERIED", "NOT_APPLICABLE", "UNKNOWN"]
    )
    return f"""# Disease Association Feature Extraction Validation Report

**Task:** #032B-2D  
**Component:** `{COMPONENT_ID}`  
**Source snapshot:** `{source_snapshot_version}`  
**Validation status:** **{status}**

## Generated layer

- Immutable entities: {len(feature_rows):,}
- Registered structural feature definitions: {len(FEATURE_DEFINITIONS)}
- Feature instances: {len(feature_rows) * len(FEATURE_DEFINITIONS):,}
- Uncompressed feature-to-record provenance relationships: {provenance_rows_count:,}
- Feature table SHA256: `{feature_sha256}`
- Feature dictionary SHA256: `{dictionary_sha256}`
- Provenance registry SHA256: `{provenance_sha256}`

Source-native association metrics remain only in the frozen raw Parquet records. They are not normalized feature values or state inputs.

## Actual structural component states

{state_lines}

These states are non-ordinal structural labels. `MISSING` means a complete resolved query returned no qualifying record; it is not negative evidence. `PARTIAL` identifies unresolved infrastructure conditions and is not a judgement about a target.

## Feature-level missingness observations

{missingness_lines}

The `UNKNOWN` feature-missingness observations arise from the deliberately unresolved source-native record-granularity classification. This feature is not a state input.

## Executable state fixtures

{fixture_lines}

## Validation checks

{check_lines}

## Dependency boundary

Every association record retains its own provenance relationship. Entities with multiple records are labelled `SAME_SOURCE`; records sharing one Open Targets source dataset additionally retain `SHARED_DATASET`. A single record or zero records use `NOT_APPLICABLE`. No record is labelled independent.

## Interpretation boundary

This layer describes evidence availability, record structure, mapping, provenance, dependency, missingness, and structural state only. It does not establish disease causality, biological importance, evidence strength, target quality, therapeutic value, ranking, recommendation, or target selection. No profile was generated.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default="outputs/disease_association_features_v0.1",
        help="Repository-relative output directory",
    )
    args = parser.parse_args()

    repo = find_repo_root()
    output_root = (repo / args.output_dir).resolve()
    if (repo / "outputs").resolve() not in output_root.parents:
        raise ExtractionError("Output must be below repository outputs/")
    if output_root.exists() and any(output_root.iterdir()):
        raise ExtractionError("Output directory is non-empty; frozen outputs are not overwritten")
    output_root.mkdir(parents=True, exist_ok=True)

    frozen_before = verify_frozen_inputs(repo)
    snapshot_root = repo / SNAPSHOT_ROOT_RELATIVE
    snapshot_manifest = json.loads((snapshot_root / "snapshot_manifest.json").read_text())
    if snapshot_manifest["completeness_status"] != "COMPLETE":
        raise ExtractionError("Source snapshot is not COMPLETE")
    source_snapshot_version = snapshot_manifest["source_snapshot_version"]
    snapshot_id = snapshot_manifest["snapshot_id"]
    if snapshot_manifest["identity_payload"]["source_version"] != SOURCE_VERSION:
        raise ExtractionError("Source version mismatch")
    if snapshot_manifest["identity_payload"]["disease_context_id"] != DISEASE_CONTEXT_ID:
        raise ExtractionError("Disease context mismatch")
    if snapshot_manifest["identity_payload"]["universe_id"] != UNIVERSE_ID:
        raise ExtractionError("Universe mismatch")

    coverage_rows = read_csv(snapshot_root / "entity_coverage_ledger.csv")
    raw_records = read_csv(snapshot_root / "raw_record_manifest.csv")
    file_inventory = read_csv(snapshot_root / "file_inventory.csv")
    if len(coverage_rows) != EXPECTED_ENTITIES:
        raise ExtractionError(f"Coverage row count mismatch: {len(coverage_rows)}")
    if [int(row["universe_ordinal"]) for row in coverage_rows] != list(
        range(1, EXPECTED_ENTITIES + 1)
    ):
        raise ExtractionError("Coverage canonical order mismatch")
    if len({row["EnsemblID"] for row in coverage_rows}) != EXPECTED_ENTITIES:
        raise ExtractionError("Coverage EnsemblID uniqueness failure")
    if len({row["raw_record_id"] for row in raw_records}) != len(raw_records):
        raise ExtractionError("Raw record identity is not unique")

    artifact_by_path = validate_snapshot_raw_files(
        repo, snapshot_root, file_inventory
    )
    enrich_raw_records_from_parquet(snapshot_root, raw_records, artifact_by_path)
    records_by_entity: dict[str, list[dict[str, str]]] = defaultdict(list)
    for record in raw_records:
        if record["source_disease_id"] != DISEASE_CONTEXT_ID:
            raise ExtractionError("Non-exact disease record entered extractor")
        records_by_entity[record["universe_EnsemblID"]].append(record)
    for records in records_by_entity.values():
        records.sort(
            key=lambda row: (
                row["source_dataset"],
                row["source_file_path"],
                int(row["source_row_group"]),
                int(row["source_row_index"]),
            )
        )

    contexts = [
        build_entity_context(
            coverage,
            records_by_entity.get(coverage["EnsemblID"], []),
            snapshot_complete=True,
            artifact_by_path=artifact_by_path,
        )
        for coverage in coverage_rows
    ]
    feature_rows = make_feature_rows(contexts, source_snapshot_version)
    feature_payload = csv_bytes(feature_rows, FEATURE_OUTPUT_FIELDS)
    feature_sha256 = write_bytes(
        output_root / "disease_association_features.csv", feature_payload
    )
    dictionary_payload = csv_bytes(
        FEATURE_DEFINITIONS, FEATURE_DICTIONARY_FIELDS
    )
    dictionary_sha256 = write_bytes(
        output_root / "feature_dictionary.csv", dictionary_payload
    )

    coverage_artifact_sha256 = SNAPSHOT_SHA256[
        "outputs/disease_association_snapshot_v0.1/entity_coverage_ledger.csv"
    ]
    coverage_artifact_id = stable_id(
        "ART_DA_COVERAGE",
        {
            "path": "entity_coverage_ledger.csv",
            "sha256": coverage_artifact_sha256,
        },
    )
    provenance_path = output_root / "feature_provenance_registry.csv"
    provenance_sha256, provenance_count = write_provenance(
        provenance_path,
        provenance_rows(
            contexts,
            source_snapshot_version,
            snapshot_id,
            coverage_artifact_id,
            coverage_artifact_sha256,
            artifact_by_path,
        ),
    )
    provenance_validated_count, provenance_feature_instances = (
        validate_provenance_file(
            provenance_path,
            contexts,
            source_snapshot_version,
        )
    )
    if provenance_validated_count != provenance_count:
        raise ExtractionError("Provenance validation row-count mismatch")

    with tempfile.TemporaryDirectory(prefix="task032b2d_determinism_") as folder:
        duplicate_path = Path(folder) / "feature_provenance_registry.csv"
        duplicate_sha256, duplicate_count = write_provenance(
            duplicate_path,
            provenance_rows(
                contexts,
                source_snapshot_version,
                snapshot_id,
                coverage_artifact_id,
                coverage_artifact_sha256,
                artifact_by_path,
            ),
        )
        provenance_deterministic = (
            duplicate_sha256 == provenance_sha256
            and duplicate_count == provenance_count
            and duplicate_path.read_bytes() == provenance_path.read_bytes()
        )

    fixtures = state_fixtures()
    state_counts = Counter(row["component_state"] for row in feature_rows)
    feature_missingness_values = {
        row[column] for row in feature_rows for column in MISSINGNESS_COLUMNS
    }
    feature_headers_safe = not (
        set(FEATURE_OUTPUT_FIELDS)
        | set(FEATURE_DICTIONARY_FIELDS)
        | set(PROVENANCE_FIELDS)
    ) & FORBIDDEN_FIELD_NAMES
    all_feature_ids = {
        definition["feature_definition_id"] for definition in FEATURE_DEFINITIONS
    }
    expected_feature_ids = {
        "DAF_ASSESSMENT_ATTEMPTED_V0_1",
        "DAF_QUERY_SCOPE_COMPLETE_V0_1",
        "DAF_RECORD_AVAILABILITY_V0_1",
        "DAF_RECORD_COUNT_V0_1",
        "DAF_RECORD_ROLE_SET_V0_1",
        "DAF_RECORD_GRANULARITY_SET_V0_1",
        "DAF_SOURCE_EVIDENCE_TYPE_SET_V0_1",
        "DAF_SOURCE_DISEASE_ID_SET_V0_1",
        "DAF_SOURCE_TARGET_ID_SET_V0_1",
        "DAF_DISEASE_MAPPING_STATUS_V0_1",
        "DAF_TARGET_MAPPING_STATUS_V0_1",
        "DAF_PROVENANCE_COMPLETE_V0_1",
        "DAF_DEPENDENCY_COMPLETE_V0_1",
        "DAF_DEPENDENCY_STATUS_SET_V0_1",
        "DAF_CONFLICT_COUNT_V0_1",
        "DAF_PARTIAL_CONDITION_COUNT_V0_1",
        "DAF_RETRIEVAL_FAILURE_V0_1",
        "DAF_UNKNOWN_COVERAGE_V0_1",
        "DAF_RECORDS_MISSINGNESS_V0_1",
    }
    checks: list[tuple[str, bool, str]] = [
        ("frozen_input_hashes", True, f"{len(frozen_before)} inputs verified"),
        ("entity_identity", len(feature_rows) == EXPECTED_ENTITIES, f"{len(feature_rows)} ordered EnsemblID rows"),
        ("registered_feature_definitions", all_feature_ids == expected_feature_ids and len(FEATURE_DEFINITIONS) == 19, "19 exact Task032B-1 definitions"),
        ("raw_record_lineage", len(raw_records) == 75_165, f"{len(raw_records)} immutable raw records resolved"),
        ("feature_provenance_completeness", provenance_feature_instances == EXPECTED_ENTITIES * 19, f"{provenance_feature_instances} feature instances have lineage"),
        ("uncompressed_provenance", provenance_count > len(raw_records), f"{provenance_count} separate feature-to-record links"),
        ("missingness_vocabulary", feature_missingness_values <= MISSINGNESS_VOCABULARY, canonical_json(sorted(feature_missingness_values))),
        ("component_state_vocabulary", set(state_counts) <= STATE_VOCABULARY, canonical_json(dict(sorted(state_counts.items())))),
        ("state_fixture_coverage", all(item["passed"] for item in fixtures) and {item["expected_state"] for item in fixtures} == STATE_VOCABULARY, f"{len(fixtures)} fixtures including precedence"),
        ("dependency_preservation", all(context["values"]["disease_association_dependency_complete"] for context in contexts), "every raw record has dependent or NOT_APPLICABLE classification"),
        ("forbidden_field_detection", feature_headers_safe, "no prohibited output field names"),
        ("source_native_metric_exclusion", all("score" not in definition["feature_name"].lower() and "confidence" not in definition["feature_name"].lower() for definition in FEATURE_DEFINITIONS), "no source metric exposed as normalized feature"),
        ("deterministic_feature_table", feature_payload == csv_bytes(feature_rows, FEATURE_OUTPUT_FIELDS), "byte-identical regeneration"),
        ("deterministic_feature_dictionary", dictionary_payload == csv_bytes(FEATURE_DEFINITIONS, FEATURE_DICTIONARY_FIELDS), "byte-identical regeneration"),
        ("deterministic_provenance", provenance_deterministic, "byte-identical independent regeneration"),
        ("no_network", True, "extractor contains no network client or live source call"),
        ("no_profiles", True, "no profile artifact generated"),
        ("no_evaluation", True, "no scoring, ranking, recommendation, or biological interpretation"),
    ]
    if not all(passed for _, passed, _ in checks):
        failed = [name for name, passed, _ in checks if not passed]
        raise ExtractionError(f"Validation failed: {failed}")

    input_identity = {
        "component_id": COMPONENT_ID,
        "component_version": COMPONENT_VERSION,
        "disease_context_id": DISEASE_CONTEXT_ID,
        "extractor_sha256": sha256_file(Path(__file__).resolve()),
        "extractor_version": EXTRACTOR_VERSION,
        "feature_dictionary_sha256": dictionary_sha256,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "feature_table_sha256": feature_sha256,
        "frozen_input_sha256": frozen_before,
        "generator_version": GENERATOR_VERSION,
        "provenance_registry_sha256": provenance_sha256,
        "source_snapshot_version": source_snapshot_version,
        "state_rule_version": STATE_RULE_VERSION,
        "universe_id": UNIVERSE_ID,
    }
    component_release_id = stable_id("DA_FEATURE_RELEASE", input_identity, length=32)
    component_manifest = {
        "component_id": COMPONENT_ID,
        "component_release_id": component_release_id,
        "component_version": COMPONENT_VERSION,
        "entity_count": len(feature_rows),
        "extractor": {
            "sha256": sha256_file(Path(__file__).resolve()),
            "version": EXTRACTOR_VERSION,
        },
        "feature_definition_count": len(FEATURE_DEFINITIONS),
        "feature_instance_count": len(feature_rows) * len(FEATURE_DEFINITIONS),
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "frozen_inputs": frozen_before,
        "generator_version": GENERATOR_VERSION,
        "interpretation_boundary": "STRUCTURAL_EVIDENCE_REPRESENTATION_ONLY",
        "missingness_vocabulary": [
            "OBSERVED",
            "NOT_FOUND",
            "NOT_QUERIED",
            "NOT_APPLICABLE",
            "UNKNOWN",
        ],
        "network_access": "PROHIBITED_NOT_USED",
        "output_artifacts": {
            "disease_association_features.csv": {
                "row_count": len(feature_rows),
                "sha256": feature_sha256,
            },
            "feature_dictionary.csv": {
                "row_count": len(FEATURE_DEFINITIONS),
                "sha256": dictionary_sha256,
            },
            "feature_provenance_registry.csv": {
                "row_count": provenance_count,
                "sha256": provenance_sha256,
            },
        },
        "prohibited_outputs": [
            "SOURCE_NATIVE_ASSOCIATION_METRICS_AS_NORMALIZED_VALUES",
            "TARGET_EVALUATION",
            "TARGET_PROFILE",
            "THERAPEUTIC_INTERPRETATION",
        ],
        "source_id": SOURCE_ID,
        "source_snapshot_id": snapshot_id,
        "source_snapshot_manifest_sha256": SNAPSHOT_SHA256[
            "outputs/disease_association_snapshot_v0.1/snapshot_manifest.json"
        ],
        "source_snapshot_version": source_snapshot_version,
        "state_counts": dict(sorted(state_counts.items())),
        "state_precedence": STATE_PRECEDENCE,
        "state_rule_version": STATE_RULE_VERSION,
        "state_vocabulary": STATE_PRECEDENCE,
        "validation_status": "PASS",
    }
    manifest_sha256 = write_bytes(
        output_root / "component_manifest.json",
        pretty_json_bytes(component_manifest),
    )
    report = validation_report(
        source_snapshot_version,
        feature_sha256,
        dictionary_sha256,
        provenance_sha256,
        feature_rows,
        provenance_count,
        fixtures,
        checks,
    )
    report_sha256 = write_bytes(
        output_root / "validation_report.md", report.encode("utf-8")
    )
    session = "\n".join(
        [
            "Task: #032B-2D Disease Association Feature Extractor",
            f"Extractor version: {EXTRACTOR_VERSION}",
            f"Extractor SHA256: {sha256_file(Path(__file__).resolve())}",
            f"Generator version: {GENERATOR_VERSION}",
            f"Feature schema version: {FEATURE_SCHEMA_VERSION}",
            f"State rule version: {STATE_RULE_VERSION}",
            f"Python: {sys.version.replace(chr(10), ' ')}",
            f"Python executable: {sys.executable}",
            f"pyarrow: {pa.__version__}",
            f"Platform: {platform.platform()}",
            "Network access: NONE",
            "Package installation: NONE",
            "Randomness: NONE",
            "Runtime AI/LLM decisions: NONE",
            "Wall-clock values in outputs: NONE",
            f"Source snapshot version: {source_snapshot_version}",
            f"Feature table SHA256: {feature_sha256}",
            f"Feature dictionary SHA256: {dictionary_sha256}",
            f"Provenance registry SHA256: {provenance_sha256}",
            f"Component manifest SHA256: {manifest_sha256}",
            f"Validation report SHA256: {report_sha256}",
            "Normalized source-native association metrics: NONE",
            "Profiles generated: FALSE",
            "Target evaluation performed: FALSE",
            "",
        ]
    )
    write_bytes(output_root / "session_info.txt", session.encode("utf-8"))

    frozen_after = verify_frozen_inputs(repo)
    if frozen_after != frozen_before:
        raise ExtractionError("Frozen inputs changed during extraction")

    print(f"Feature extraction complete: {component_release_id}")
    print(f"Entities: {len(feature_rows):,}")
    print(f"Feature definitions: {len(FEATURE_DEFINITIONS)}")
    print(f"Provenance relationships: {provenance_count:,}")
    print(f"Component states: {dict(sorted(state_counts.items()))}")
    print("Validation: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ExtractionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
