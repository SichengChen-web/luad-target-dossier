#!/usr/bin/env python3
"""Generate Multi-component Evidence Landscape v0.2.

This Task #033B-2 generator projects frozen Task #032C Target Evidence
Profiles into a structural landscape representation. It performs no evidence
retrieval, component reconstruction, target evaluation, scoring, ranking,
prioritization, recommendation, biological interpretation, or runtime AI/LLM
decision.

Large landscape JSONL partitions are written to a content-addressed external
local staging area outside the repository. Only small manifests, the index,
QC, and session metadata are written under outputs/evidence_landscape_v0.2/.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import tempfile
from collections import Counter, OrderedDict
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any, BinaryIO, Iterable


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "outputs/evidence_profile_integration_v0.1"
SOURCE_RECORDS = SOURCE_DIR / "profile_records.jsonl"
SOURCE_INDEX = SOURCE_DIR / "profile_index.csv"
SOURCE_MANIFEST = SOURCE_DIR / "profile_manifest.json"
SCHEMA_PATH = ROOT / "schemas/evidence_landscape_schema_v0.2.json"
OUTPUT_DIR = ROOT / "outputs/evidence_landscape_v0.2"
EXTERNAL_ROOT = Path(
    "/private/tmp/luad-target-dossier-external-artifacts/evidence_landscape_v0.2"
)

MANIFEST_PATH = OUTPUT_DIR / "landscape_manifest.json"
INDEX_PATH = OUTPUT_DIR / "landscape_index.csv"
PARTITION_MANIFEST_PATH = OUTPUT_DIR / "partition_manifest.csv"
REPORT_PATH = OUTPUT_DIR / "validation_report.md"
SESSION_PATH = OUTPUT_DIR / "session_info.txt"

TASK_ID = "TASK_033B_2"
GENERATOR_VERSION = "MULTI_COMPONENT_EVIDENCE_LANDSCAPE_GENERATOR_V0.1"
SCHEMA_VERSION = "EVIDENCE_LANDSCAPE_SCHEMA_V0.2"
LANDSCAPE_VERSION = "MULTI_COMPONENT_EVIDENCE_LANDSCAPE_V0.2"
PARTITION_STRATEGY_VERSION = "ENSEMBL_SHA256_PREFIX_2_V0.1"
EXPECTED_LANDSCAPES = 29606
EXPECTED_COMPONENTS = 59212
EXPECTED_FEATURES = 1213846
EXPECTED_PROVENANCE = 2517118
EXPECTED_PARTITIONS = 256
GIT_REVIEW_THRESHOLD = 50_000_000
GIT_PROHIBITED_THRESHOLD = 100_000_000

SOURCE_PROFILE_SCHEMA_VERSION = "TARGET_EVIDENCE_PROFILE_MULTICOMPONENT_SCHEMA_V0.1"
SOURCE_PROFILE_VERSION = "TARGET_EVIDENCE_PROFILE_MULTICOMPONENT_V0.1"
SOURCE_EVIDENCE_SNAPSHOT_VERSION = (
    "EVIDENCE_SNAPSHOT_32C_CBFD2625F8B0CBB855DB90CBC8E2D605"
)
SOURCE_PROFILE_GENERATOR_VERSION = "MULTICOMPONENT_PROFILE_INTEGRATOR_V0.1"
SOURCE_INTEGRATION_RELEASE_ID = "PROFILE_INTEGRATION_RELEASE_8007AAA939B733EE6619F1FCFB87CAE8"

COMPONENT_ORDER = (
    ("COMP_TRANSCRIPTOMIC_EVIDENCE", "COMP_TRANSCRIPTOMIC_EVIDENCE_V0.1", 22),
    ("COMP_DISEASE_ASSOCIATION", "COMP_DISEASE_ASSOCIATION_V0.1", 19),
)
COMPONENT_STATES = {"OBSERVED", "PARTIAL", "CONFLICTING", "MISSING", "NOT_QUERIED"}
MISSINGNESS_STATES = {
    "OBSERVED",
    "NOT_FOUND",
    "NOT_QUERIED",
    "NOT_APPLICABLE",
    "UNKNOWN",
}
PROHIBITED_FIELDS = {
    "score",
    "ranking",
    "priority",
    "confidence",
    "overall_state",
    "recommendation",
    "interpretation",
}

FROZEN_INPUT_SHA256 = {
    "analysis/33B1_define_landscape_schema_contract.py": "089723f2a4d1c9e85d151cedbcda1f2e68953d04f1c98325680c9d75db3c3a42",
    "schemas/evidence_landscape_schema_v0.2.json": "a52109fb90fda2493d99f20f51dacbf987a394678c90ee9e5d6c58a7afbc62ba",
    "outputs/evidence_landscape_schema_v0.2/schema_manifest.json": "7cd1c5b15aaa745ff4602ed54171ca39c4d72f54407476661103367373f6b6a8",
    "outputs/evidence_profile_integration_v0.1/profile_manifest.json": "63492499977f7adb086e4ace9a491a72fa617a1fe054d544701826fb9657455d",
    "outputs/evidence_profile_integration_v0.1/profile_index.csv": "376e6d3440dba3ae392410cd2f836a9a700fe66248bf29257794b55015821a28",
    "outputs/evidence_profile_integration_v0.1/validation_report.md": "191ba0d01799d4e3e96bff3ebabc6c75997cbbdeee36217b45f0c45181302699",
    "outputs/evidence_profile_integration_v0.1/profile_records.jsonl": "8fab364cbe1318f49dd8b29501dd1439d1ae2a38161e090942801399bec7e156",
    "docs/governance/multi_component_evidence_landscape_specification_v0.2.md": "6d878dc12eaf7b9172f0880345cfc12bd67a209d45af68dbe543e05f192c8e73",
    "docs/governance/evidence_landscape_component_composition_policy_v0.1.md": "1ba8b4bf678906d5f15a50284742d2b81045d7530eb59d2fe28a81ad45eab2b7",
    "docs/governance/evidence_landscape_versioning_policy_v0.1.md": "fd71350c8c00f5abc935a772244232fbcb614dc898c0e44e2763f38121c62677",
    "docs/governance/evidence_landscape_validation_requirements_v0.1.md": "fccbcef5a1b61f8d45184c1f6177ce892a828887ad754c268eab9f1674c1c7ca",
    # These three manifests are transitive, frozen provenance resolvers already
    # referenced by the Task #032C lineage. They supply no biological evidence.
    "outputs/feature_extraction/extraction_manifest.json": "7d62eaf07d38f64e35e395a3f33367b66f7803ab6710e1fccd507eb11840e944",
    "outputs/evidence_landscape_v0.1/evidence_landscape_manifest.json": "8eb4cc48ad4e6bb206b297a95bf26d608cf52fdbe629f780e703c1561b61898c",
    "outputs/disease_association_component_v0.1/component_manifest.json": "b2264956a13d5096b61cdb2b6981bcc80d7b7b3f1fe422b30f77c7cdc70e39f7",
    "docs/governance/component_dependency_model_v0.1.md": "5b77654a7ea543b2b2a184bba4a280cc4395c575065be6a3674d93a0955cdb06",
}

EXPECTED_SOURCE_RECORD_SIZE = 2_151_412_821
EXPECTED_INDEX_COLUMNS = [
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

INDEX_COLUMNS = [
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

PARTITION_COLUMNS = [
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

TASK033A_PATHS = {
    path
    for path in FROZEN_INPUT_SHA256
    if path.startswith("docs/governance/") and "evidence_landscape" in path
}
ALLOWED_WORKTREE_PATHS = {
    "analysis/33B2_generate_evidence_landscape.py",
    *TASK033A_PATHS,
    *(f"outputs/evidence_landscape_v0.2/{name}" for name in (
        "landscape_manifest.json",
        "landscape_index.csv",
        "partition_manifest.csv",
        "validation_report.md",
        "session_info.txt",
    )),
}

TRANSCRIPTOMIC_LIMITATION_IDS = (
    "LIM_TRANSCRIPTOMIC_ASSOCIATION_BOUNDARY",
    "LIM_NONOBSERVED_MISSINGNESS_PATHS_INCOMPLETELY_TESTED",
    "LIM_STATE_RULE_REVIEW_PENDING",
)
PROFILE_LIMITATION_IDS = (
    "LIM_PROFILE_LIFECYCLE_UNASSIGNED",
    "LIM_EXTERNAL_STORAGE_PENDING",
    "LIM_HUMAN_TRACEABILITY_AUDIT_PENDING",
)
HISTORICAL_EXCLUDED_LIMITATION_ID = "LIM_ONLY_TRANSCRIPTOMIC_COMPONENT"


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
    digest = sha256_bytes(canonical_json(value).encode("utf-8"))
    return f"{prefix}_{digest[:length].upper()}"


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


def read_source_index() -> list[dict[str, str]]:
    with SOURCE_INDEX.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != EXPECTED_INDEX_COLUMNS:
            fail("Task #032C profile index columns changed")
        rows = list(reader)
    if len(rows) != EXPECTED_LANDSCAPES:
        fail(f"Expected {EXPECTED_LANDSCAPES} Task #032C index rows, observed {len(rows)}")
    seen: set[str] = set()
    for ordinal, row in enumerate(rows, 1):
        if int(row["universe_ordinal"]) != ordinal:
            fail(f"Task #032C canonical ordinal mismatch at row {ordinal}")
        identifier = row["EnsemblID"]
        if not re.fullmatch(r"ENSG[0-9]+\.[0-9]+", identifier):
            fail(f"Invalid immutable EnsemblID at row {ordinal}: {identifier}")
        if identifier in seen:
            fail(f"Duplicate Task #032C EnsemblID: {identifier}")
        seen.add(identifier)
    return rows


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
            fail("Unexpected repository payload/output files: " + ", ".join(unexpected))


def validate_external_root() -> None:
    EXTERNAL_ROOT.parent.mkdir(parents=True, exist_ok=True)
    if EXTERNAL_ROOT.exists() and (EXTERNAL_ROOT.is_symlink() or not EXTERNAL_ROOT.is_dir()):
        fail(f"Unsafe external artifact root: {EXTERNAL_ROOT}")
    EXTERNAL_ROOT.mkdir(parents=True, exist_ok=True)
    resolved_root = EXTERNAL_ROOT.resolve()
    resolved_parent = EXTERNAL_ROOT.parent.resolve()
    if resolved_root.parent != resolved_parent:
        fail("External artifact root escaped its expected parent")


def validate_frozen_inputs(*, include_source_payload: bool) -> dict[str, str]:
    observed: dict[str, str] = {}
    for relative_path, expected_hash in FROZEN_INPUT_SHA256.items():
        path = ROOT / relative_path
        if not path.is_file():
            fail(f"Frozen input missing: {relative_path}")
        if relative_path.endswith("profile_records.jsonl") and not include_source_payload:
            if path.stat().st_size != EXPECTED_SOURCE_RECORD_SIZE:
                fail("Task #032C profile payload byte size changed")
            continue
        actual_hash = sha256_file(path)
        if actual_hash != expected_hash:
            fail(
                f"Frozen input hash mismatch: {relative_path}; "
                f"expected {expected_hash}, observed {actual_hash}"
            )
        observed[relative_path] = actual_hash
    return observed


def validate_governance_and_manifests() -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    schema_manifest = json.loads(
        (ROOT / "outputs/evidence_landscape_schema_v0.2/schema_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    if schema_manifest.get("validation_status") != "PASS":
        fail("Task #033B-1 schema contract is not validated")
    schema_artifact = schema_manifest.get("output_artifact", {})
    if (
        schema_artifact.get("schema_version") != SCHEMA_VERSION
        or schema_artifact.get("sha256") != FROZEN_INPUT_SHA256["schemas/evidence_landscape_schema_v0.2.json"]
    ):
        fail("Task #033B-1 schema identity mismatch")

    source_manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    expected_source = {
        "profile_count": EXPECTED_LANDSCAPES,
        "profile_schema_version": SOURCE_PROFILE_SCHEMA_VERSION,
        "profile_version": SOURCE_PROFILE_VERSION,
        "evidence_snapshot_version": SOURCE_EVIDENCE_SNAPSHOT_VERSION,
        "integration_release_id": SOURCE_INTEGRATION_RELEASE_ID,
        "validation_status": "PASS",
    }
    for key, expected in expected_source.items():
        if source_manifest.get(key) != expected:
            fail(f"Task #032C manifest mismatch: {key}")
    source_components = [
        (entry.get("component_id"), entry.get("component_version"))
        for entry in source_manifest.get("components", [])
    ]
    if source_components != [(item[0], item[1]) for item in COMPONENT_ORDER]:
        fail("Task #032C component identity/order changed")
    profile_payload = source_manifest.get("output_artifacts", {}).get("profile_records.jsonl", {})
    if (
        profile_payload.get("row_count") != EXPECTED_LANDSCAPES
        or profile_payload.get("size_bytes") != EXPECTED_SOURCE_RECORD_SIZE
        or profile_payload.get("sha256")
        != FROZEN_INPUT_SHA256["outputs/evidence_profile_integration_v0.1/profile_records.jsonl"]
    ):
        fail("Task #032C profile payload manifest mismatch")

    extraction_manifest = json.loads(
        (ROOT / "outputs/feature_extraction/extraction_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    artifact_hashes = {
        item["artifact_id"]: item["sha256"]
        for item in extraction_manifest.get("input_artifacts", [])
    }
    required_artifact = "ART_TASK012_INTEGRATED_TARGET_REGISTRY"
    expected_artifact_hash = "0587fc6901267b18c8144644571f89ac2cc46053b57ea5def4093795fdbc4c26"
    if artifact_hashes.get(required_artifact) != expected_artifact_hash:
        fail("Frozen transcriptomic provenance artifact hash cannot be resolved")

    task031_manifest = json.loads(
        (ROOT / "outputs/evidence_landscape_v0.1/evidence_landscape_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    limitations = {
        item["limitation_id"]: {
            "scope": item["scope"],
            "statement": item["statement"],
        }
        for item in task031_manifest.get("limitation_registry", [])
    }
    required_limitations = {
        *TRANSCRIPTOMIC_LIMITATION_IDS,
        *PROFILE_LIMITATION_IDS,
        HISTORICAL_EXCLUDED_LIMITATION_ID,
    }
    if not required_limitations.issubset(limitations):
        fail("Frozen limitation registry is incomplete")
    if limitations[HISTORICAL_EXCLUDED_LIMITATION_ID]["scope"] != "PROFILE":
        fail("Historical single-component limitation identity changed")

    return artifact_hashes, limitations


def resolve_json_pointer(root_schema: dict[str, Any], reference: str) -> dict[str, Any]:
    if not reference.startswith("#/"):
        fail(f"Unsupported non-local schema reference: {reference}")
    node: Any = root_schema
    for part in reference[2:].split("/"):
        key = part.replace("~1", "/").replace("~0", "~")
        node = node[key]
    if not isinstance(node, dict):
        fail(f"Schema reference does not resolve to an object: {reference}")
    return node


def schema_type_matches(instance: Any, expected_type: str) -> bool:
    return {
        "object": isinstance(instance, dict),
        "array": isinstance(instance, list),
        "string": isinstance(instance, str),
        "integer": isinstance(instance, int) and not isinstance(instance, bool),
        "number": isinstance(instance, (int, float)) and not isinstance(instance, bool),
        "boolean": isinstance(instance, bool),
        "null": instance is None,
    }.get(expected_type, False)


def validate_schema_instance(
    instance: Any,
    schema: dict[str, Any] | bool,
    root_schema: dict[str, Any],
    path: str = "$",
) -> None:
    if schema is False:
        fail(f"Schema rejects value at {path}")
    if schema is True:
        return
    if "$ref" in schema:
        validate_schema_instance(instance, resolve_json_pointer(root_schema, schema["$ref"]), root_schema, path)
        return
    if "const" in schema and instance != schema["const"]:
        fail(f"Schema const mismatch at {path}")
    if "enum" in schema and instance not in schema["enum"]:
        fail(f"Schema enum mismatch at {path}: {instance!r}")
    expected_type = schema.get("type")
    if expected_type and not schema_type_matches(instance, expected_type):
        fail(f"Schema type mismatch at {path}: expected {expected_type}")

    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            fail(f"Schema minLength mismatch at {path}")
        pattern = schema.get("pattern")
        if pattern and re.search(pattern, instance) is None:
            fail(f"Schema pattern mismatch at {path}: {instance!r}")
    if isinstance(instance, int) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            fail(f"Schema minimum mismatch at {path}")
        if "maximum" in schema and instance > schema["maximum"]:
            fail(f"Schema maximum mismatch at {path}")

    if isinstance(instance, dict):
        required = schema.get("required", [])
        missing = [key for key in required if key not in instance]
        if missing:
            fail(f"Schema required fields missing at {path}: {missing}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extras = set(instance) - set(properties)
            if extras:
                fail(f"Schema additional fields at {path}: {sorted(extras)}")
        for key, child_schema in properties.items():
            if key in instance:
                validate_schema_instance(instance[key], child_schema, root_schema, f"{path}.{key}")

    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            fail(f"Schema minItems mismatch at {path}")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            fail(f"Schema maxItems mismatch at {path}")
        if schema.get("uniqueItems"):
            canonical = [canonical_json(item) for item in instance]
            if len(canonical) != len(set(canonical)):
                fail(f"Schema uniqueItems mismatch at {path}")
        prefix = schema.get("prefixItems", [])
        for index, child_schema in enumerate(prefix):
            if index < len(instance):
                validate_schema_instance(instance[index], child_schema, root_schema, f"{path}[{index}]")
        if "items" in schema:
            item_schema = schema["items"]
            for index in range(len(prefix), len(instance)):
                validate_schema_instance(instance[index], item_schema, root_schema, f"{path}[{index}]")

    for child_schema in schema.get("allOf", []):
        validate_schema_instance(instance, child_schema, root_schema, path)
    if "if" in schema:
        condition_passes = True
        try:
            validate_schema_instance(instance, schema["if"], root_schema, path)
        except RuntimeError:
            condition_passes = False
        branch = schema.get("then") if condition_passes else schema.get("else")
        if branch is not None:
            validate_schema_instance(instance, branch, root_schema, path)


def assert_no_prohibited_fields(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        forbidden = PROHIBITED_FIELDS.intersection(value)
        if forbidden:
            fail(f"Prohibited field(s) at {path}: {sorted(forbidden)}")
        for key, child in value.items():
            assert_no_prohibited_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            assert_no_prohibited_fields(child, f"{path}[{index}]")


def limitation_reference(limitation_id: str, scope: str) -> dict[str, Any]:
    return {
        "limitation_id": limitation_id,
        "scope": scope,
        "source_version": "EVIDENCE_LANDSCAPE_REPRESENTATION_V0.1",
        "registry_artifact_reference": {
            "artifact_id": "ART_TASK031_EVIDENCE_LANDSCAPE_MANIFEST",
            "artifact_sha256": FROZEN_INPUT_SHA256[
                "outputs/evidence_landscape_v0.1/evidence_landscape_manifest.json"
            ],
        },
        "review_status": "PRESERVED_APPLICABLE_UNRESOLVED",
    }


def dependency_reference(component_id: str, link: dict[str, Any]) -> dict[str, Any]:
    dependency_id = str(link.get("dependency_id", ""))
    if not dependency_id:
        fail("Source provenance relationship lacks dependency_id")

    if component_id == "COMP_TRANSCRIPTOMIC_EVIDENCE":
        if dependency_id == "NOT_APPLICABLE":
            relationship_type = "NOT_APPLICABLE"
            dependency_level = "NOT_APPLICABLE"
            reference_status = "CONTROLLED_SENTINEL"
        elif dependency_id.startswith("DEP_"):
            relationship_type = "SHARED_DATASET"
            dependency_level = "DEPENDENT"
            reference_status = "LINKED_GOVERNED_DEPENDENCY"
        else:
            fail(f"Unsupported transcriptomic dependency identifier: {dependency_id}")
        governing_artifact = {
            "artifact_id": "ART_TASK031_EVIDENCE_LANDSCAPE_MANIFEST",
            "artifact_sha256": FROZEN_INPUT_SHA256[
                "outputs/evidence_landscape_v0.1/evidence_landscape_manifest.json"
            ],
        }
        review_status = "PRESERVED_FROM_TASK031_GOVERNED_REFERENCE"
    elif component_id == "COMP_DISEASE_ASSOCIATION":
        relationship_types = link.get("dependency_relationship_types")
        if not isinstance(relationship_types, list) or len(relationship_types) != 1:
            fail(
                "Disease-association dependency relationship must have exactly one frozen type"
            )
        relationship_type = str(relationship_types[0])
        dependency_level = str(link.get("dependency_level", ""))
        reference_status = (
            "CONTROLLED_SENTINEL"
            if relationship_type == "NOT_APPLICABLE"
            else "LINKED_GOVERNED_DEPENDENCY"
        )
        governing_artifact = {
            "artifact_id": "ART_DISEASE_ASSOCIATION_COMPONENT_MANIFEST",
            "artifact_sha256": FROZEN_INPUT_SHA256[
                "outputs/disease_association_component_v0.1/component_manifest.json"
            ],
        }
        review_status = "PRESERVED_FROM_TASK032C_SOURCE_PROVENANCE"
    else:
        fail(f"Unknown component dependency namespace: {component_id}")

    return {
        "dependency_id": dependency_id,
        "dependency_reference_status": reference_status,
        "relationship_type": relationship_type,
        "dependency_level": dependency_level,
        "dependency_model_version": "COMPONENT_DEPENDENCY_MODEL_V0.1",
        "governing_artifact_reference": governing_artifact,
        "review_status": review_status,
    }


def provenance_reference(
    component_id: str,
    feature: dict[str, Any],
    link: dict[str, Any],
    artifact_hashes: dict[str, str],
) -> dict[str, Any]:
    artifact_id = str(link.get("artifact_id", ""))
    artifact_hash = link.get("artifact_sha256") or artifact_hashes.get(artifact_id)
    if not artifact_id or not isinstance(artifact_hash, str) or not re.fullmatch(
        r"[0-9a-f]{64}", artifact_hash
    ):
        fail(f"Unresolved provenance artifact reference: {artifact_id!r}")

    extraction_rule_id = link.get("extraction_rule_id") or feature.get("extraction_rule_id")
    extractor_version = link.get("extractor_version") or feature.get("extractor_version")
    # Task #032C transcriptomic links repeat feature_id, whereas its
    # disease-association links inherit feature_id from the containing frozen
    # feature object. Both encodings identify the same source relationship.
    link_feature_id = link.get("feature_id") or feature.get("feature_id")
    required_text = {
        "feature_id": link_feature_id,
        "claim_id": link.get("claim_id"),
        "evidence_record_id": link.get("evidence_record_id"),
        "source_id": link.get("source_id"),
        "extraction_rule_id": extraction_rule_id,
        "extractor_version": extractor_version,
    }
    missing = [key for key, value in required_text.items() if not isinstance(value, str) or not value]
    if missing:
        fail(f"Incomplete source provenance relationship: {missing}")
    if required_text["feature_id"] != feature.get("feature_id"):
        fail("Source provenance feature_id does not match containing feature")

    return {
        "component_id": component_id,
        "feature_id": required_text["feature_id"],
        "claim_id": required_text["claim_id"],
        "evidence_record_id": required_text["evidence_record_id"],
        "source_id": required_text["source_id"],
        "artifact_reference": {
            "artifact_id": artifact_id,
            "artifact_sha256": artifact_hash,
        },
        "extraction_rule_id": required_text["extraction_rule_id"],
        "extractor_version": required_text["extractor_version"],
        "dependency_reference": dependency_reference(component_id, link),
    }


def project_feature(
    component_id: str,
    source_record_id: str,
    feature: dict[str, Any],
    artifact_hashes: dict[str, str],
) -> dict[str, Any]:
    feature_id = feature.get("feature_id")
    feature_name = feature.get("feature_name")
    missingness = feature.get("missingness_status")
    links = feature.get("provenance_links")
    if not isinstance(feature_id, str) or not isinstance(feature_name, str):
        fail("Source feature identity is incomplete")
    if missingness not in MISSINGNESS_STATES:
        fail(f"Uncontrolled source feature missingness: {missingness!r}")
    if not isinstance(links, list) or not links:
        fail(f"Source feature lacks provenance relationships: {feature_id}")

    projected = {
        "feature_id": feature_id,
        "feature_name": feature_name,
        "missingness_status": missingness,
        "source_component_record_id": source_record_id,
        "provenance_references": [
            provenance_reference(component_id, feature, link, artifact_hashes) for link in links
        ],
    }
    source_value_hash = feature.get("feature_value_sha256")
    if source_value_hash is not None:
        projected["source_feature_value_sha256"] = source_value_hash
    return projected


def project_component(
    source_component: dict[str, Any],
    artifact_hashes: dict[str, str],
) -> dict[str, Any]:
    component_id = source_component.get("component_id")
    expected_by_id = {item[0]: item for item in COMPONENT_ORDER}
    if component_id not in expected_by_id:
        fail(f"Unexpected source component: {component_id!r}")
    _, expected_version, expected_features = expected_by_id[component_id]
    if (
        source_component.get("component_version") != expected_version
        or source_component.get("component_definition_version") != expected_version
    ):
        fail(f"Source component version mismatch: {component_id}")
    state = source_component.get("state")
    if state not in COMPONENT_STATES:
        fail(f"Uncontrolled source component state: {state!r}")
    features = source_component.get("features")
    if not isinstance(features, list) or len(features) != expected_features:
        fail(f"Source feature cardinality mismatch: {component_id}")

    source_reference = dict(source_component.get("source_record_reference", {}))
    if "source_record_artifact_id" not in source_reference:
        # Disease-association records are stored directly in their declared
        # container artifact. This explicit alias satisfies the common schema
        # without changing the source record identity or content hash.
        source_reference["source_record_artifact_id"] = source_reference.get(
            "container_artifact_id"
        )
    allowed_source_reference = {
        key: source_reference[key]
        for key in (
            "source_record_id",
            "source_record_sha256",
            "source_record_artifact_id",
            "container_artifact_id",
            "container_artifact_sha256",
            "partition_id",
        )
        if key in source_reference
    }
    source_record_id = allowed_source_reference.get("source_record_id")
    if not isinstance(source_record_id, str) or not source_record_id:
        fail(f"Source component record identity missing: {component_id}")

    projected_features = [
        project_feature(component_id, source_record_id, feature, artifact_hashes)
        for feature in features
    ]
    limitation_references = (
        [limitation_reference(item, "COMPONENT") for item in TRANSCRIPTOMIC_LIMITATION_IDS]
        if component_id == "COMP_TRANSCRIPTOMIC_EVIDENCE"
        else []
    )
    return {
        "component_id": component_id,
        "component_version": expected_version,
        "component_definition_version": expected_version,
        "availability_status": "PRESENT_IN_SOURCE_PROFILE",
        "state": state,
        "source_component_content_sha256": source_component[
            "source_component_content_sha256"
        ],
        "source_component_reference": allowed_source_reference,
        "source_state_rule_reference": dict(source_component["source_state_rule_metadata"]),
        "version_axes": dict(source_component["version_axes"]),
        "feature_references": projected_features,
        "limitation_references": limitation_references,
    }


def project_landscape(
    profile: dict[str, Any],
    artifact_hashes: dict[str, str],
) -> dict[str, Any]:
    ensembl_id = profile.get("EnsemblID")
    profile_id = profile.get("profile_id")
    identity_tuple = [
        ensembl_id,
        SCHEMA_VERSION,
        LANDSCAPE_VERSION,
        profile_id,
        profile.get("evidence_snapshot_version"),
    ]
    source_components = profile.get("components")
    if not isinstance(source_components, list) or len(source_components) != 2:
        fail(f"Source profile component cardinality mismatch: {ensembl_id}")
    observed_order = [item.get("component_id") for item in source_components]
    if observed_order != [item[0] for item in COMPONENT_ORDER]:
        fail(f"Source profile component order mismatch: {ensembl_id}")

    return {
        "landscape_id": stable_id("LND", identity_tuple),
        "EnsemblID": ensembl_id,
        "universe_ordinal": profile.get("universe_ordinal"),
        "landscape_schema_version": SCHEMA_VERSION,
        "landscape_version": LANDSCAPE_VERSION,
        "generator_version": GENERATOR_VERSION,
        "source_profile_identity": {
            "source_profile_id": profile_id,
            "source_profile_content_sha256": profile["_source_profile_content_sha256"],
            "source_profile_schema_version": profile.get("profile_schema_version"),
            "source_profile_version": profile.get("profile_version"),
            "source_evidence_snapshot_version": profile.get("evidence_snapshot_version"),
            "source_profile_generator_version": profile.get("generator_version"),
            "source_integration_release_id": SOURCE_INTEGRATION_RELEASE_ID,
        },
        "components": [
            project_component(component, artifact_hashes) for component in source_components
        ],
        "limitation_references": [
            limitation_reference(item, "PROFILE") for item in PROFILE_LIMITATION_IDS
        ],
    }


class LRUFilePool(AbstractContextManager["LRUFilePool"]):
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
        path = self.directory / f"{part}.jsonl"
        handle = path.open("ab", buffering=1024 * 1024)
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
    schema: dict[str, Any],
    artifact_hashes: dict[str, str],
    pass_name: str,
) -> dict[str, Any]:
    destination.mkdir(parents=True, exist_ok=False)
    partitions: dict[str, dict[str, Any]] = {
        f"p{index:02x}": {
            "sha256": hashlib.sha256(),
            "size": 0,
            "count": 0,
            "first_ordinal": None,
            "last_ordinal": None,
        }
        for index in range(EXPECTED_PARTITIONS)
    }
    index_rows: list[dict[str, Any]] = []
    state_counts: Counter[tuple[str, str]] = Counter()
    missingness_counts: Counter[tuple[str, str]] = Counter()
    source_digest = hashlib.sha256()
    total_features = 0
    total_provenance = 0
    total_components = 0
    source_offset = 0

    with SOURCE_RECORDS.open("rb") as source_handle, LRUFilePool(destination) as pool:
        for ordinal, raw_line in enumerate(source_handle, 1):
            if ordinal > EXPECTED_LANDSCAPES:
                fail("Task #032C profile payload contains excess records")
            source_digest.update(raw_line)
            source_row = source_index[ordinal - 1]
            if int(source_row["record_offset_bytes"]) != source_offset:
                fail(f"Task #032C source offset mismatch at ordinal {ordinal}")
            if int(source_row["record_length_bytes"]) != len(raw_line):
                fail(f"Task #032C source record length mismatch at ordinal {ordinal}")
            source_offset += len(raw_line)
            source_content = raw_line[:-1] if raw_line.endswith(b"\n") else raw_line
            source_content_hash = sha256_bytes(source_content)
            if source_content_hash != source_row["profile_content_sha256"]:
                fail(f"Task #032C source profile hash mismatch at ordinal {ordinal}")
            profile = json.loads(source_content)
            if (
                profile.get("universe_ordinal") != ordinal
                or profile.get("EnsemblID") != source_row["EnsemblID"]
                or profile.get("profile_id") != source_row["profile_id"]
            ):
                fail(f"Task #032C source profile identity mismatch at ordinal {ordinal}")
            profile["_source_profile_content_sha256"] = source_content_hash

            landscape = project_landscape(profile, artifact_hashes)
            assert_no_prohibited_fields(landscape)
            validate_schema_instance(landscape, schema, schema)
            encoded_content = canonical_json(landscape).encode("utf-8")
            encoded_line = encoded_content + b"\n"
            part = partition_id(profile["EnsemblID"])
            stats = partitions[part]
            record_offset = stats["size"]
            pool.writer(part).write(encoded_line)
            stats["sha256"].update(encoded_line)
            stats["size"] += len(encoded_line)
            stats["count"] += 1
            stats["first_ordinal"] = stats["first_ordinal"] or ordinal
            stats["last_ordinal"] = ordinal

            feature_count = 0
            provenance_count = 0
            for component in landscape["components"]:
                total_components += 1
                state_counts[(component["component_id"], component["state"])] += 1
                for feature in component["feature_references"]:
                    feature_count += 1
                    total_features += 1
                    missingness_counts[
                        (component["component_id"], feature["missingness_status"])
                    ] += 1
                    relationships = len(feature["provenance_references"])
                    provenance_count += relationships
                    total_provenance += relationships

            limitation_ids = [
                item["limitation_id"] for item in landscape["limitation_references"]
            ]
            for component in landscape["components"]:
                limitation_ids.extend(
                    item["limitation_id"] for item in component["limitation_references"]
                )
            index_rows.append(
                {
                    "universe_ordinal": ordinal,
                    "EnsemblID": landscape["EnsemblID"],
                    "landscape_id": landscape["landscape_id"],
                    "source_profile_id": landscape["source_profile_identity"][
                        "source_profile_id"
                    ],
                    "source_profile_content_sha256": source_content_hash,
                    "source_profile_schema_version": SOURCE_PROFILE_SCHEMA_VERSION,
                    "source_profile_version": SOURCE_PROFILE_VERSION,
                    "source_evidence_snapshot_version": SOURCE_EVIDENCE_SNAPSHOT_VERSION,
                    "transcriptomic_component_version": COMPONENT_ORDER[0][1],
                    "transcriptomic_component_state": landscape["components"][0]["state"],
                    "disease_association_component_version": COMPONENT_ORDER[1][1],
                    "disease_association_component_state": landscape["components"][1]["state"],
                    "component_count": 2,
                    "feature_reference_count": feature_count,
                    "provenance_reference_count": provenance_count,
                    "limitation_ids": "|".join(limitation_ids),
                    "partition_id": part,
                    "record_offset_bytes": record_offset,
                    "record_length_bytes": len(encoded_line),
                    "landscape_content_sha256": sha256_bytes(encoded_content),
                    "landscape_schema_version": SCHEMA_VERSION,
                    "landscape_version": LANDSCAPE_VERSION,
                    "generator_version": GENERATOR_VERSION,
                }
            )
            if ordinal % 5000 == 0 or ordinal == EXPECTED_LANDSCAPES:
                print(f"{pass_name}: projected {ordinal}/{EXPECTED_LANDSCAPES}", flush=True)

    if len(index_rows) != EXPECTED_LANDSCAPES:
        fail(f"Expected {EXPECTED_LANDSCAPES} source profiles, observed {len(index_rows)}")
    source_hash = source_digest.hexdigest()
    if source_hash != FROZEN_INPUT_SHA256[
        "outputs/evidence_profile_integration_v0.1/profile_records.jsonl"
    ]:
        fail(f"Task #032C source payload hash mismatch during {pass_name}")
    if source_offset != EXPECTED_SOURCE_RECORD_SIZE:
        fail(f"Task #032C source payload size mismatch during {pass_name}")
    if total_components != EXPECTED_COMPONENTS:
        fail(f"Component reconciliation failed during {pass_name}: {total_components}")
    if total_features != EXPECTED_FEATURES:
        fail(f"Feature reconciliation failed during {pass_name}: {total_features}")
    if total_provenance != EXPECTED_PROVENANCE:
        fail(f"Provenance reconciliation failed during {pass_name}: {total_provenance}")
    if any(stats["count"] == 0 for stats in partitions.values()):
        fail(f"One or more deterministic partitions are empty during {pass_name}")

    normalized_partitions = {
        part: {
            "sha256": stats["sha256"].hexdigest(),
            "size": stats["size"],
            "count": stats["count"],
            "first_ordinal": stats["first_ordinal"],
            "last_ordinal": stats["last_ordinal"],
        }
        for part, stats in partitions.items()
    }
    return {
        "partitions": normalized_partitions,
        "index_rows": index_rows,
        "state_counts": dict(state_counts),
        "missingness_counts": dict(missingness_counts),
        "source_hash": source_hash,
        "totals": {
            "landscapes": len(index_rows),
            "components": total_components,
            "features": total_features,
            "provenance": total_provenance,
        },
    }


def compare_passes(first: dict[str, Any], second: dict[str, Any]) -> None:
    for key in ("partitions", "index_rows", "state_counts", "missingness_counts", "source_hash", "totals"):
        if first[key] != second[key]:
            fail(f"Independent regeneration mismatch: {key}")


def partition_set_hash(partitions: dict[str, dict[str, Any]]) -> str:
    identity = [
        {
            "partition_id": part,
            "sha256": partitions[part]["sha256"],
            "size_bytes": partitions[part]["size"],
            "landscape_count": partitions[part]["count"],
        }
        for part in sorted(partitions)
    ]
    return sha256_bytes(canonical_json(identity).encode("utf-8"))


def validate_existing_external_artifact(
    final_root: Path, partitions: dict[str, dict[str, Any]]
) -> None:
    if final_root.is_symlink() or not final_root.is_dir():
        fail(f"Unsafe or invalid existing external artifact: {final_root}")
    expected_files = {f"partitions/{part}/landscape_records.jsonl" for part in partitions}
    observed_files = {
        path.relative_to(final_root).as_posix()
        for path in final_root.rglob("*")
        if path.is_file()
    }
    if observed_files != expected_files:
        fail("Existing external artifact file inventory mismatch")
    for part, stats in partitions.items():
        path = final_root / "partitions" / part / "landscape_records.jsonl"
        if path.is_symlink() or path.stat().st_size != stats["size"]:
            fail(f"Existing external partition size mismatch: {part}")
        if sha256_file(path) != stats["sha256"]:
            fail(f"Existing external partition hash mismatch: {part}")


def promote_external_payload(
    pass_a: Path,
    partitions: dict[str, dict[str, Any]],
    set_artifact_id: str,
) -> Path:
    final_root = EXTERNAL_ROOT / set_artifact_id
    if final_root.exists():
        validate_existing_external_artifact(final_root, partitions)
        return final_root

    organized = pass_a.parent / "organized"
    organized.mkdir()
    partition_root = organized / "partitions"
    partition_root.mkdir()
    for part in sorted(partitions):
        destination = partition_root / part
        destination.mkdir()
        source = pass_a / f"{part}.jsonl"
        source.rename(destination / "landscape_records.jsonl")
    organized.rename(final_root)
    validate_existing_external_artifact(final_root, partitions)
    return final_root


def build_partition_rows(
    partitions: dict[str, dict[str, Any]], set_artifact_id: str
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for part in sorted(partitions):
        stats = partitions[part]
        payload_artifact_id = f"ART_LNDV02_{stats['sha256'][:24].upper()}"
        rows.append(
            {
                "partition_id": part,
                "partition_strategy_version": PARTITION_STRATEGY_VERSION,
                "partition_set_artifact_id": set_artifact_id,
                "payload_artifact_id": payload_artifact_id,
                "artifact_class": "CLASS_D_LARGE_DATA_OBJECT",
                "artifact_role": "LANDSCAPE_JSONL_PAYLOAD",
                "immutable_identifier": f"urn:sha256:{stats['sha256']}",
                "external_storage_reference": (
                    "external+sha256://luad-target-dossier/evidence-landscape-v0.2/"
                    f"{set_artifact_id}/partitions/{part}/landscape_records.jsonl"
                ),
                "storage_status": "LOCAL_CONTENT_ADDRESSED_EXTERNAL_STAGING",
                "landscape_count": stats["count"],
                "first_universe_ordinal": stats["first_ordinal"],
                "last_universe_ordinal": stats["last_ordinal"],
                "file_size_bytes": stats["size"],
                "sha256": stats["sha256"],
                "landscape_schema_version": SCHEMA_VERSION,
                "landscape_version": LANDSCAPE_VERSION,
                "generator_version": GENERATOR_VERSION,
                "validation_status": "PASS",
            }
        )
    return rows


def finalize_index_rows(
    base_rows: list[dict[str, Any]], partition_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    artifact_by_partition = {
        row["partition_id"]: row["payload_artifact_id"] for row in partition_rows
    }
    finalized: list[dict[str, Any]] = []
    seen_landscapes: set[str] = set()
    seen_entities: set[str] = set()
    for ordinal, row in enumerate(base_rows, 1):
        if row["universe_ordinal"] != ordinal:
            fail("Landscape index canonical order changed")
        if row["landscape_id"] in seen_landscapes or row["EnsemblID"] in seen_entities:
            fail("Duplicate landscape or immutable EnsemblID in index")
        seen_landscapes.add(row["landscape_id"])
        seen_entities.add(row["EnsemblID"])
        item = dict(row)
        item["payload_artifact_id"] = artifact_by_partition[row["partition_id"]]
        finalized.append(item)
    return finalized


def counter_to_nested(counter: dict[tuple[str, str], int]) -> dict[str, dict[str, int]]:
    nested: dict[str, dict[str, int]] = {}
    for (component_id, value), count in sorted(counter.items()):
        nested.setdefault(component_id, {})[value] = count
    return nested


def build_manifest(
    script_hash: str,
    index_bytes: bytes,
    partition_bytes: bytes,
    result: dict[str, Any],
    partition_rows: list[dict[str, Any]],
    set_hash: str,
    set_artifact_id: str,
) -> dict[str, Any]:
    total_payload_bytes = sum(row["file_size_bytes"] for row in partition_rows)
    release_id = stable_id(
        "LNDREL",
        [
            FROZEN_INPUT_SHA256[
                "outputs/evidence_profile_integration_v0.1/profile_records.jsonl"
            ],
            FROZEN_INPUT_SHA256["schemas/evidence_landscape_schema_v0.2.json"],
            set_hash,
            GENERATOR_VERSION,
        ],
    )
    return {
        "release_id": release_id,
        "release_status": "VALIDATED_LOCAL_STRUCTURAL_CANDIDATE",
        "lifecycle_status": "UNASSIGNED_AWAITING_HUMAN_GOVERNANCE_ACTION",
        "landscape_schema_version": SCHEMA_VERSION,
        "landscape_version": LANDSCAPE_VERSION,
        "generator": {
            "version": GENERATOR_VERSION,
            "relative_path": "analysis/33B2_generate_evidence_landscape.py",
            "sha256": script_hash,
        },
        "immutable_key": "EnsemblID",
        "landscape_identity_tuple": [
            "EnsemblID",
            "landscape_schema_version",
            "landscape_version",
            "source_profile_id",
            "source_evidence_snapshot_version",
        ],
        "source_profile": {
            "profile_schema_version": SOURCE_PROFILE_SCHEMA_VERSION,
            "profile_version": SOURCE_PROFILE_VERSION,
            "evidence_snapshot_version": SOURCE_EVIDENCE_SNAPSHOT_VERSION,
            "integration_release_id": SOURCE_INTEGRATION_RELEASE_ID,
            "profile_payload_sha256": result["source_hash"],
        },
        "component_order": [item[0] for item in COMPONENT_ORDER],
        "component_versions": {item[0]: item[1] for item in COMPONENT_ORDER},
        "counts": {
            "landscapes": result["totals"]["landscapes"],
            "components": result["totals"]["components"],
            "feature_references": result["totals"]["features"],
            "provenance_references": result["totals"]["provenance"],
            "partitions": len(partition_rows),
        },
        "component_state_counts": counter_to_nested(result["state_counts"]),
        "feature_missingness_counts": counter_to_nested(result["missingness_counts"]),
        "limitation_identifiers": {
            "profile": list(PROFILE_LIMITATION_IDS),
            "components": {
                "COMP_TRANSCRIPTOMIC_EVIDENCE": list(TRANSCRIPTOMIC_LIMITATION_IDS),
                "COMP_DISEASE_ASSOCIATION": [],
            },
            "historical_not_propagated": [HISTORICAL_EXCLUDED_LIMITATION_ID],
            "new_identifiers_created": 0,
        },
        "partition_set": {
            "partition_strategy_version": PARTITION_STRATEGY_VERSION,
            "partition_set_artifact_id": set_artifact_id,
            "partition_set_sha256": set_hash,
            "partition_count": len(partition_rows),
            "total_bytes": total_payload_bytes,
            "artifact_class": "CLASS_D_LARGE_DATA_OBJECT",
            "storage_mode": "EXTERNAL_CONTENT_ADDRESSED",
            "storage_status": "LOCAL_STAGING_REQUIRES_DURABLE_EXTERNAL_COPY",
            "ordinary_git_tracking": "PROHIBITED",
        },
        "git_managed_artifacts": {
            "landscape_index.csv": {
                "artifact_class": "CLASS_B_REPRODUCIBLE_DERIVED_ARTIFACT",
                "size_bytes": len(index_bytes),
                "sha256": sha256_bytes(index_bytes),
                "row_count": EXPECTED_LANDSCAPES,
            },
            "partition_manifest.csv": {
                "artifact_class": "CLASS_B_REPRODUCIBLE_DERIVED_ARTIFACT",
                "size_bytes": len(partition_bytes),
                "sha256": sha256_bytes(partition_bytes),
                "row_count": EXPECTED_PARTITIONS,
            },
        },
        "frozen_inputs": dict(sorted(FROZEN_INPUT_SHA256.items())),
        "determinism": {
            "independent_full_regenerations": 2,
            "partition_bytes": "BYTE_IDENTICAL_BY_SIZE_AND_SHA256",
            "index_rows": "IDENTICAL",
            "network_access": "PROHIBITED_NOT_USED",
            "runtime_ai_decisions": "PROHIBITED_NONE_USED",
            "randomness": "NOT_USED",
            "wall_clock_governed_values": "NOT_USED",
        },
        "prohibitions": [
            "NO_EXTERNAL_EVIDENCE_RETRIEVAL",
            "NO_COMPONENT_REBUILD",
            "NO_SCORING",
            "NO_RANKING",
            "NO_PRIORITY",
            "NO_CANDIDATE_SELECTION",
            "NO_RECOMMENDATIONS",
            "NO_BIOLOGICAL_INTERPRETATION",
            "NO_LLM_RUNTIME_DECISIONS",
        ],
        "validation_status": "PASS",
    }


def build_report(
    manifest: dict[str, Any], index_bytes: bytes, partition_bytes: bytes
) -> bytes:
    counts = manifest["counts"]
    partition = manifest["partition_set"]
    state_counts = manifest["component_state_counts"]
    missingness_counts = manifest["feature_missingness_counts"]
    lines = [
        "# Multi-component Evidence Landscape v0.2 validation report",
        "",
        "**Task:** #033B-2  ",
        "**Validation status:** PASS  ",
        f"**Landscape version:** `{LANDSCAPE_VERSION}`",
        "",
        "## Structural projection",
        "",
        f"- Landscapes: **{counts['landscapes']:,}**",
        f"- Component references: **{counts['components']:,}**",
        f"- Feature references: **{counts['feature_references']:,}**",
        f"- Record-level provenance/dependency references: **{counts['provenance_references']:,}**",
        f"- External JSONL partitions: **{counts['partitions']:,}**",
        "",
        "Each landscape is a structural projection of exactly one frozen Task #032C profile. No component was rebuilt from raw evidence.",
        "",
        "## Validation results",
        "",
        "| Validation | Result |",
        "|---|---|",
        "| Exact Task #032C EnsemblID universe and canonical order | PASS |",
        "| 29,606 unique landscape and source-profile identities | PASS |",
        "| Exactly two ordered components per landscape | PASS |",
        "| Component versions and states preserved | PASS |",
        "| Feature identity and missingness preserved | PASS |",
        "| All 2,517,118 provenance relationships preserved separately | PASS |",
        "| Dependency identifiers and governed classifications preserved | PASS |",
        "| Applicable registered limitation IDs preserved | PASS |",
        f"| Historical `{HISTORICAL_EXCLUDED_LIMITATION_ID}` excluded | PASS |",
        "| Task #033B-1 schema validation for every landscape | PASS |",
        "| Prohibited-field recursive scan for every landscape | PASS |",
        "| Two independent complete regenerations | PASS — identical partition sizes and SHA256 hashes |",
        "| Frozen input hashes unchanged | PASS |",
        "| Network or API access | PROHIBITED; NOT USED |",
        "| Runtime AI/LLM decisions | PROHIBITED; NONE USED |",
        "",
        "## Component states",
        "",
    ]
    for component_id in (item[0] for item in COMPONENT_ORDER):
        lines.append(f"### `{component_id}`")
        lines.append("")
        for state in ("OBSERVED", "PARTIAL", "CONFLICTING", "MISSING", "NOT_QUERIED"):
            lines.append(f"- `{state}`: {state_counts.get(component_id, {}).get(state, 0):,}")
        lines.append("")
    lines.extend(
        [
            "## Feature missingness",
            "",
        ]
    )
    for component_id in (item[0] for item in COMPONENT_ORDER):
        lines.append(f"### `{component_id}`")
        lines.append("")
        for status in ("OBSERVED", "NOT_FOUND", "NOT_QUERIED", "NOT_APPLICABLE", "UNKNOWN"):
            lines.append(
                f"- `{status}`: {missingness_counts.get(component_id, {}).get(status, 0):,}"
            )
        lines.append("")
    lines.extend(
        [
            "## Artifact governance",
            "",
            f"- External payload size: **{partition['total_bytes']:,} bytes**",
            f"- Partition-set artifact: `{partition['partition_set_artifact_id']}`",
            f"- Partition-set SHA256: `{partition['partition_set_sha256']}`",
            "- Payload class: `CLASS_D_LARGE_DATA_OBJECT`",
            "- Ordinary Git tracking: prohibited; JSONL partitions are held in content-addressed external local staging.",
            "- Durable external storage registration remains a separate governance action.",
            f"- Git-managed index size: {len(index_bytes):,} bytes; SHA256 `{sha256_bytes(index_bytes)}`",
            f"- Git-managed partition manifest size: {len(partition_bytes):,} bytes; SHA256 `{sha256_bytes(partition_bytes)}`",
            "",
            "## Provenance-resolution boundary",
            "",
            "The generator copied feature-to-record relationships from Task #032C. Small frozen lineage manifests were used only to resolve artifact hashes, governed dependency classifications, and applicable stable limitation identifiers already referenced by that lineage. No raw evidence source or API was accessed.",
            "",
            "Task #032C does not register a disease-association limitation identifier. None was invented; the component limitation-reference array therefore remains empty.",
            "",
            "## Interpretation boundary",
            "",
            "This validation establishes structural, lineage, and reproducibility conformance only. The landscape contains no target evaluation, score, rank, priority, selection, recommendation, biological interpretation, therapeutic conclusion, or overall component state.",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


def build_session_info(script_hash: str, set_artifact_id: str) -> bytes:
    lines = [
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
        "independent_full_regenerations=2",
        "deterministic_regeneration=PASS",
        f"external_partition_set_artifact_id={set_artifact_id}",
        "external_storage_mode=CONTENT_ADDRESSED_LOCAL_STAGING_OUTSIDE_REPOSITORY",
        "durable_external_storage_registration=PENDING_SEPARATE_GOVERNANCE_ACTION",
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def write_metadata_bundle(bundle: dict[Path, bytes]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path, content in bundle.items():
        path.write_bytes(content)


def main() -> None:
    validate_working_tree_scope()
    validate_output_scope()
    validate_external_root()
    validate_frozen_inputs(include_source_payload=False)
    artifact_hashes, limitation_registry = validate_governance_and_manifests()
    del limitation_registry  # Presence and identity were validated; no statements enter payloads.
    source_index = read_source_index()
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    if schema.get("$id") != "urn:luad-target-dossier:evidence-landscape-schema:v0.2":
        fail("Unexpected Task #033B-1 schema identifier")

    script_hash = sha256_file(Path(__file__).resolve())
    frozen_before = validate_frozen_inputs(include_source_payload=False)

    work_root = Path(tempfile.mkdtemp(prefix=".task033b2-", dir=EXTERNAL_ROOT))
    try:
        pass_a_dir = work_root / "pass_a"
        pass_b_dir = work_root / "pass_b"
        first = generate_pass(pass_a_dir, source_index, schema, artifact_hashes, "PASS_A")
        second = generate_pass(pass_b_dir, source_index, schema, artifact_hashes, "PASS_B")
        compare_passes(first, second)

        set_hash = partition_set_hash(first["partitions"])
        set_artifact_id = f"ART_LNDV02_SET_{set_hash[:24].upper()}"
        external_final = promote_external_payload(
            pass_a_dir, first["partitions"], set_artifact_id
        )

        partition_rows = build_partition_rows(first["partitions"], set_artifact_id)
        finalized_index = finalize_index_rows(first["index_rows"], partition_rows)
        index_bytes = read_csv_bytes(finalized_index, INDEX_COLUMNS)
        partition_bytes = read_csv_bytes(partition_rows, PARTITION_COLUMNS)
        if len(index_bytes) > GIT_PROHIBITED_THRESHOLD:
            fail("Required Git-managed landscape index exceeds 100 MB")
        if len(partition_bytes) > GIT_PROHIBITED_THRESHOLD:
            fail("Required Git-managed partition manifest exceeds 100 MB")

        manifest = build_manifest(
            script_hash,
            index_bytes,
            partition_bytes,
            first,
            partition_rows,
            set_hash,
            set_artifact_id,
        )
        manifest_bytes = pretty_json_bytes(manifest)
        report_bytes = build_report(manifest, index_bytes, partition_bytes)
        session_bytes = build_session_info(script_hash, set_artifact_id)
        bundle = {
            MANIFEST_PATH: manifest_bytes,
            INDEX_PATH: index_bytes,
            PARTITION_MANIFEST_PATH: partition_bytes,
            REPORT_PATH: report_bytes,
            SESSION_PATH: session_bytes,
        }
        # Metadata regeneration is performed twice in memory and compared.
        second_bundle = {
            MANIFEST_PATH: pretty_json_bytes(
                build_manifest(
                    script_hash,
                    index_bytes,
                    partition_bytes,
                    second,
                    partition_rows,
                    set_hash,
                    set_artifact_id,
                )
            ),
            INDEX_PATH: read_csv_bytes(
                finalize_index_rows(second["index_rows"], partition_rows), INDEX_COLUMNS
            ),
            PARTITION_MANIFEST_PATH: read_csv_bytes(partition_rows, PARTITION_COLUMNS),
            REPORT_PATH: build_report(manifest, index_bytes, partition_bytes),
            SESSION_PATH: build_session_info(script_hash, set_artifact_id),
        }
        if bundle != second_bundle:
            fail("Git-managed metadata regeneration is not byte-identical")
        write_metadata_bundle(bundle)
        validate_output_scope()

        frozen_after = validate_frozen_inputs(include_source_payload=False)
        if frozen_before != frozen_after:
            fail("A frozen input changed during landscape generation")
        # Both complete generation passes independently verified the large
        # source payload hash, avoiding a third multi-gigabyte read.
        expected_source_hash = FROZEN_INPUT_SHA256[
            "outputs/evidence_profile_integration_v0.1/profile_records.jsonl"
        ]
        if first["source_hash"] != expected_source_hash or second["source_hash"] != expected_source_hash:
            fail("Frozen source profile payload changed during generation")
        validate_existing_external_artifact(external_final, first["partitions"])

        total_payload_bytes = sum(
            stats["size"] for stats in first["partitions"].values()
        )
        if total_payload_bytes <= GIT_PROHIBITED_THRESHOLD:
            fail("Expected landscape payload to require externalization, but it did not exceed 100 MB")
        print("TASK_033B_2_VALIDATION=PASS")
        print(f"landscapes={first['totals']['landscapes']}")
        print(f"components={first['totals']['components']}")
        print(f"features={first['totals']['features']}")
        print(f"provenance_references={first['totals']['provenance']}")
        print(f"external_payload_bytes={total_payload_bytes}")
        print(f"external_partition_set={set_artifact_id}")
        print(f"external_local_staging_path={external_final}")
        print("independent_regenerations=2_BYTE_IDENTICAL")
        print("network_access=PROHIBITED_NOT_USED")
    finally:
        # tempfile work directories contain only this run's independently
        # generated pass artifacts. A promoted content-addressed artifact is
        # moved outside work_root before this scoped cleanup.
        if work_root.exists():
            shutil.rmtree(work_root)


if __name__ == "__main__":
    main()
