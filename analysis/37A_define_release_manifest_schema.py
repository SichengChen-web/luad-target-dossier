#!/usr/bin/env python3
"""Define and validate Release Manifest Schema v0.1.

Task #037A is governance-only. It creates a deterministic schema contract and
schema-governance reports; it does not create a release package, rerun any
scientific pipeline, modify frozen artifacts, interpret biology, rank or score
targets, recommend targets, access a network/API, or use runtime AI decisions.
"""

from __future__ import annotations

import hashlib
import json
import platform
import re
import subprocess
from copy import deepcopy
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas/release_manifest_schema_v0.1.json"
OUTPUT_DIR = ROOT / "outputs/release_governance_v0.1"
SCHEMA_MANIFEST_PATH = OUTPUT_DIR / "release_schema_manifest.json"
REPORT_PATH = OUTPUT_DIR / "validation_report.md"
SESSION_PATH = OUTPUT_DIR / "session_info.txt"

TASK_ID = "TASK_037A"
PROJECT_ID = "LUAD_EXPRESSION_DRUGGABLE_TARGET_EVIDENCE_DOSSIER"
SCHEMA_VERSION = "RELEASE_MANIFEST_SCHEMA_V0.1"
SPECIFICATION_VERSION = "RELEASE_PACKAGE_SPECIFICATION_V0.1"
SCOPE_POLICY_VERSION = "RELEASE_SCOPE_POLICY_V0.1"
VALIDATION_REQUIREMENTS_VERSION = "RELEASE_VALIDATION_REQUIREMENTS_V0.1"
GENERATOR_VERSION = "RELEASE_MANIFEST_SCHEMA_GENERATOR_V0.1"
SCHEMA_ID = "urn:luad-target-dossier:release-manifest-schema:v0.1"

DOC_PATHS = [
    ROOT / "docs/governance/release_package_specification_v0.1.md",
    ROOT / "docs/governance/release_scope_policy_v0.1.md",
    ROOT / "docs/governance/release_validation_requirements_v0.1.md",
]

PROHIBITED_FIELDS = {
    "score",
    "rank",
    "ranking",
    "priority_score",
    "confidence",
    "probability",
    "recommendation",
    "target_quality",
    "evidence_strength",
    "biological_claim",
    "therapeutic_direction",
}

LIFECYCLE_STATES = ["PROPOSED", "VALIDATED", "FROZEN", "RELEASED"]
RELEASE_TYPES = ["INTERNAL_RESEARCH_ARTIFACT", "REPRODUCIBLE_RESEARCH_ARTIFACT"]
ARTIFACT_SCOPES = ["SCIENTIFIC", "GOVERNANCE", "COMMUNICATION"]
ARTIFACT_TYPES = [
    "EVIDENCE_COMPONENT",
    "EVIDENCE_LANDSCAPE",
    "EVIDENCE_SUMMARY",
    "TRANSPARENT_PRIORITIZATION_REPRESENTATION",
    "REPRESENTATIVE_CASE_DOSSIER",
    "SCHEMA",
    "VALIDATION_REPORT",
    "POLICY",
    "MANIFEST",
    "INDEX",
    "GENERATOR_SOURCE",
    "SESSION_METADATA",
    "PRESENTATION_ARTIFACT",
    "FIGURE",
    "POSTER_MATERIAL",
    "EXTERNAL_PAYLOAD",
]
VALIDATION_STATES = ["NOT_RUN", "PASS", "FAIL"]
PROVENANCE_RELATIONSHIPS = ["DERIVED_FROM", "VALIDATES", "GOVERNS", "COMMUNICATES"]
STORAGE_CLASSES = ["GIT_MANAGED", "EXTERNAL_IMMUTABLE"]
STORAGE_AVAILABILITY = [
    "AVAILABLE",
    "PENDING_DURABLE_REGISTRATION",
    "UNAVAILABLE",
]

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
    "outputs/case_dossiers_v0.1/dossier_manifest.json": "9039d3523bf52841239dce9ab880a98a3e2dcd5dfff3a87cece10c986067678b",
    "outputs/case_dossiers_v0.1/case_selection_index.csv": "f11892cc59d1fc3b042e79b4859e293677d9befbe975dd9d6635e0033011bc52",
    "outputs/case_dossiers_v0.1/case_dossiers.json": "d861e2500797ae9351f70e474c8a8acafa51d30481357aa450d1d77314bd27b8",
    "outputs/case_dossiers_v0.1/validation_report.md": "8ca6bc43b72fd653924b75eb9c5429e90cc82477908a1d17877bd7f5776fbbc3",
    "outputs/case_dossiers_v0.1/session_info.txt": "0cae68b33106ff97512e39ade11059701dfa8dfc847eb5db47bd7b04c3e0572f",
    "outputs/presentation_artifacts_v0.1/presentation_manifest.json": "2bf7acce12685399476e50cfa26df049d8b54cc371e6dde6794b656b12f1d2e4",
    "outputs/presentation_artifacts_v0.1/architecture_summary.md": "e1f99162ccd69701d8f446ff56210142e56e11d3ada164a8b785aaff9ac535fc",
    "outputs/presentation_artifacts_v0.1/evidence_layer_summary.csv": "0b30b5454c3d963b22b17c2ea35e776d2fa38ef805f5fe8c54bbf7599677abda",
    "outputs/presentation_artifacts_v0.1/case_pattern_summary.csv": "e03c9fb080e62e435a0d4fcf328715fa3f2a503829c79272f84a3b8a68da6d7d",
    "outputs/presentation_artifacts_v0.1/provenance_flow_summary.md": "57885dccc7f07922a9cfec9f6d48c385dfb49e0bc745003d9fc9efabd9365f56",
    "outputs/presentation_artifacts_v0.1/validation_report.md": "2237c292ab827f4396b3db4220321d1d5c626120104ce1f03cccfdbc2eb21f22",
    "outputs/presentation_artifacts_v0.1/session_info.txt": "d6b6a2270a466d487db96572ca274be350042849e360d0870916ebd90bef6738",
}

ALLOWED_WORKTREE_PATHS = {
    "analysis/37A_define_release_manifest_schema.py",
    "schemas/release_manifest_schema_v0.1.json",
    "docs/governance/release_package_specification_v0.1.md",
    "docs/governance/release_scope_policy_v0.1.md",
    "docs/governance/release_validation_requirements_v0.1.md",
    "outputs/release_governance_v0.1/release_schema_manifest.json",
    "outputs/release_governance_v0.1/validation_report.md",
    "outputs/release_governance_v0.1/session_info.txt",
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


def closed_object(properties: dict[str, Any], required: list[str], **extra: Any) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": required,
        **extra,
    }


def build_schema() -> dict[str, Any]:
    sha256_schema = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
    artifact_id_schema = {"type": "string", "pattern": "^[A-Z][A-Z0-9_]{2,127}$"}
    identifier_array = {
        "type": "array",
        "uniqueItems": True,
        "items": deepcopy(artifact_id_schema),
    }
    provenance_reference = closed_object(
        {
            "upstream_artifact_id": deepcopy(artifact_id_schema),
            "upstream_artifact_sha256": deepcopy(sha256_schema),
            "relationship_type": {"type": "string", "enum": PROVENANCE_RELATIONSHIPS},
        },
        ["upstream_artifact_id", "upstream_artifact_sha256", "relationship_type"],
    )
    storage_reference = closed_object(
        {
            "storage_class": {"type": "string", "enum": STORAGE_CLASSES},
            "storage_uri": {"type": "string", "minLength": 1},
            "availability_status": {"type": "string", "enum": STORAGE_AVAILABILITY},
            "retrieval_required_for_release": {"type": "boolean"},
        },
        [
            "storage_class",
            "storage_uri",
            "availability_status",
            "retrieval_required_for_release",
        ],
    )
    artifact = closed_object(
        {
            "artifact_id": deepcopy(artifact_id_schema),
            "relative_path": {
                "type": "string",
                "pattern": "^(?!/)(?!.*(?:^|/)\\.\\.(?:/|$))[^\\r\\n]+$",
            },
            "artifact_version": {"type": "string", "minLength": 1},
            "artifact_type": {"type": "string", "enum": ARTIFACT_TYPES},
            "artifact_scope": {"type": "string", "enum": ARTIFACT_SCOPES},
            "generating_task": {"type": "string", "pattern": "^TASK_[A-Z0-9_]+$"},
            "lifecycle_state": {"type": "string", "enum": LIFECYCLE_STATES},
            "validation_status": {"type": "string", "enum": VALIDATION_STATES},
            "sha256": deepcopy(sha256_schema),
            "size_bytes": {"type": "integer", "minimum": 0},
            "provenance_reference": provenance_reference,
            "storage_reference": storage_reference,
        },
        [
            "artifact_id",
            "relative_path",
            "artifact_version",
            "artifact_type",
            "artifact_scope",
            "generating_task",
            "lifecycle_state",
            "validation_status",
            "sha256",
            "size_bytes",
            "provenance_reference",
            "storage_reference",
        ],
    )
    component_versions = closed_object(
        {
            "COMP_TRANSCRIPTOMIC_EVIDENCE": {"type": "string", "minLength": 1},
            "COMP_DISEASE_ASSOCIATION": {"type": "string", "minLength": 1},
        },
        ["COMP_TRANSCRIPTOMIC_EVIDENCE", "COMP_DISEASE_ASSOCIATION"],
    )
    artifact_version_names = [
        "evidence_landscape_schema_version",
        "evidence_landscape_version",
        "evidence_summary_schema_version",
        "evidence_summary_version",
        "transparent_prioritization_schema_version",
        "transparent_prioritization_representation_version",
        "transparent_prioritization_rule_catalog_version",
        "representative_case_dossier_release_version",
        "representative_case_selection_schema_version",
        "representative_case_selection_framework_version",
        "representative_case_rule_catalog_version",
        "presentation_artifact_version",
        "release_manifest_schema_version",
    ]
    artifact_versions = closed_object(
        {name: {"type": "string", "minLength": 1} for name in artifact_version_names},
        artifact_version_names,
    )
    release_scope = closed_object(
        {
            "scientific_artifact_ids": deepcopy(identifier_array),
            "governance_artifact_ids": deepcopy(identifier_array),
            "communication_artifact_ids": deepcopy(identifier_array),
            "explicit_exclusions": {
                "type": "array",
                "items": closed_object(
                    {
                        "artifact_or_class": {"type": "string", "minLength": 1},
                        "exclusion_reason_code": {
                            "type": "string",
                            "pattern": "^[A-Z][A-Z0-9_]+$",
                        },
                    },
                    ["artifact_or_class", "exclusion_reason_code"],
                ),
            },
        },
        [
            "scientific_artifact_ids",
            "governance_artifact_ids",
            "communication_artifact_ids",
            "explicit_exclusions",
        ],
    )
    validation_summary = closed_object(
        {
            name: {"type": "string", "enum": VALIDATION_STATES}
            for name in [
                "schema_validation",
                "artifact_integrity",
                "provenance_reconciliation",
                "storage_reconciliation",
                "deterministic_regeneration",
                "prohibited_field_scan",
                "frozen_input_hashes",
                "overall_validation_status",
            ]
        },
        [
            "schema_validation",
            "artifact_integrity",
            "provenance_reconciliation",
            "storage_reconciliation",
            "deterministic_regeneration",
            "prohibited_field_scan",
            "frozen_input_hashes",
            "overall_validation_status",
        ],
    )
    release_boundaries = closed_object(
        {
            "new_scientific_evidence_generated": {"type": "boolean", "const": False},
            "biological_validation_claimed": {"type": "boolean", "const": False},
            "target_recommendation_claimed": {"type": "boolean", "const": False},
            "runtime_ai_decisions_used": {"type": "boolean", "const": False},
        },
        [
            "new_scientific_evidence_generated",
            "biological_validation_claimed",
            "target_recommendation_claimed",
            "runtime_ai_decisions_used",
        ],
    )
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": SCHEMA_ID,
        "title": "LUAD Target Evidence Dossier Release Manifest Schema v0.1",
        "description": "Closed artifact-governance contract for a future reproducible research release.",
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "release_id": {"type": "string", "pattern": "^REL_[A-F0-9]{32}$"},
            "release_version": {
                "type": "string",
                "pattern": "^v[0-9]+\\.[0-9]+(?:\\.[0-9]+)?$",
            },
            "release_type": {"type": "string", "enum": RELEASE_TYPES},
            "lifecycle_state": {"type": "string", "enum": LIFECYCLE_STATES},
            "project_id": {"type": "string", "const": PROJECT_ID},
            "release_manifest_schema_version": {"type": "string", "const": SCHEMA_VERSION},
            "component_versions": component_versions,
            "artifact_versions": artifact_versions,
            "release_scope": release_scope,
            "artifacts": {"type": "array", "minItems": 1, "items": artifact},
            "artifact_count": {"type": "integer", "minimum": 1},
            "validation_summary": validation_summary,
            "release_boundaries": release_boundaries,
        },
        "required": [
            "release_id",
            "release_version",
            "release_type",
            "lifecycle_state",
            "project_id",
            "release_manifest_schema_version",
            "component_versions",
            "artifact_versions",
            "release_scope",
            "artifacts",
            "artifact_count",
            "validation_summary",
            "release_boundaries",
        ],
        "$defs": {
            "artifactRecord": artifact,
            "provenanceReference": provenance_reference,
            "storageReference": storage_reference,
        },
        "$comment": (
            "This schema governs packaging only. Closed objects prohibit hidden target-level "
            "evaluation, scoring, ordering, recommendation, and biological claims."
        ),
    }


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
    allowed = {SCHEMA_MANIFEST_PATH, REPORT_PATH, SESSION_PATH}
    if OUTPUT_DIR.exists():
        unexpected = sorted(
            path.relative_to(ROOT).as_posix()
            for path in OUTPUT_DIR.rglob("*")
            if path.is_file() and path not in allowed
        )
        if unexpected:
            fail("Unexpected Task #037A output files: " + ", ".join(unexpected))


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


def load_upstream_manifests() -> dict[str, dict[str, Any]]:
    paths = {
        "landscape": ROOT / "outputs/evidence_landscape_v0.2/landscape_manifest.json",
        "summary": ROOT / "outputs/evidence_summary_v0.1/summary_manifest.json",
        "prioritization": ROOT / "outputs/prioritization_v0.1/prioritization_manifest.json",
        "dossier": ROOT / "outputs/case_dossiers_v0.1/dossier_manifest.json",
        "presentation": ROOT / "outputs/presentation_artifacts_v0.1/presentation_manifest.json",
    }
    values = {name: json.loads(path.read_text(encoding="utf-8")) for name, path in paths.items()}
    for name, value in values.items():
        if value.get("validation_status") != "PASS":
            fail(f"Frozen upstream manifest is not validated: {name}")
    if values["landscape"].get("counts", {}).get("landscapes") != 29_606:
        fail("Frozen landscape entity count changed")
    if values["summary"].get("counts", {}).get("summaries") != 29_606:
        fail("Frozen Evidence Summary entity count changed")
    if values["prioritization"].get("counts", {}).get("representations") != 29_606:
        fail("Frozen routing representation entity count changed")
    if values["dossier"].get("counts", {}).get("case_slots") != 4:
        fail("Frozen case dossier slot count changed")
    if values["presentation"].get("counts", {}).get("canonical_entities") != 29_606:
        fail("Frozen presentation artifact entity count changed")
    if values["summary"].get("source_landscape", {}).get("manifest_sha256") != FROZEN_INPUT_SHA256[
        "outputs/evidence_landscape_v0.2/landscape_manifest.json"
    ]:
        fail("Upstream landscape-to-summary terminology/provenance changed")
    if values["dossier"].get("source", {}).get("prioritization_release_id") != values[
        "prioritization"
    ].get("release_id"):
        fail("Upstream routing-to-dossier release identity changed")
    presentation_sources = values["presentation"].get("source_releases", {})
    expected_sources = {
        "landscape_release_id": values["landscape"].get("release_id"),
        "evidence_summary_release_id": values["summary"].get("release_id"),
        "prioritization_release_id": values["prioritization"].get("release_id"),
        "case_dossier_release_id": values["dossier"].get("release_id"),
    }
    if presentation_sources != expected_sources:
        fail("Frozen presentation source release identities changed")
    return values


def validate_documentation() -> dict[str, str]:
    required_terms = {
        DOC_PATHS[0]: [
            SPECIFICATION_VERSION,
            "PROPOSED -> VALIDATED -> FROZEN -> RELEASED",
            "release artifact != biological validation",
            "release artifact != target recommendation",
            "No release disposition is authorized by Task #037A",
        ],
        DOC_PATHS[1]: [
            SCOPE_POLICY_VERSION,
            "Scientific artifact scope",
            "Governance artifact scope",
            "Communication artifact scope",
            "Task #037A creates none",
        ],
        DOC_PATHS[2]: [
            VALIDATION_REQUIREMENTS_VERSION,
            "Lifecycle gates",
            "Prohibited-field validation",
            "Frozen-input protection",
            "not biological validation or target recommendation",
        ],
    }
    hashes: dict[str, str] = {}
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for path, terms in required_terms.items():
        if not path.is_file():
            fail(f"Required governance document missing: {path.relative_to(ROOT)}")
        text = path.read_text(encoding="utf-8")
        for term in terms:
            if term not in text:
                fail(f"Governance terminology missing from {path.name}: {term}")
        for target in link_pattern.findall(text):
            if target.startswith(("http://", "https://", "#")):
                continue
            resolved = (path.parent / target.split("#", 1)[0]).resolve()
            if not resolved.is_file():
                fail(f"Broken governance Markdown link in {path.name}: {target}")
        hashes[path.relative_to(ROOT).as_posix()] = sha256_file(path)
    return hashes


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


def assert_closed_schema(schema: Any, path: str = "$") -> None:
    if isinstance(schema, dict):
        if schema.get("type") == "object" and schema.get("additionalProperties") is not False:
            fail(f"Schema object is not closed at {path}")
        properties = schema.get("properties")
        if isinstance(properties, dict):
            forbidden = PROHIBITED_FIELDS.intersection(properties)
            if forbidden:
                fail(f"Prohibited schema properties at {path}: {sorted(forbidden)}")
        for key, child in schema.items():
            assert_closed_schema(child, f"{path}.{key}")
    elif isinstance(schema, list):
        for index, child in enumerate(schema):
            assert_closed_schema(child, f"{path}[{index}]")


def validate_type(value: Any, expected: str, path: str) -> None:
    checks = {
        "string": lambda item: isinstance(item, str),
        "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
        "boolean": lambda item: isinstance(item, bool),
        "array": lambda item: isinstance(item, list),
        "object": lambda item: isinstance(item, dict),
    }
    if expected in checks and not checks[expected](value):
        fail(f"Schema type mismatch at {path}: expected {expected}")


def validate_instance(instance: Any, schema: dict[str, Any], root: dict[str, Any], path: str = "$") -> None:
    if "$ref" in schema:
        pointer = schema["$ref"]
        if not pointer.startswith("#/"):
            fail(f"Unsupported schema reference: {pointer}")
        target: Any = root
        for token in pointer[2:].split("/"):
            target = target[token.replace("~1", "/").replace("~0", "~")]
        validate_instance(instance, target, root, path)
        return
    if "type" in schema:
        validate_type(instance, schema["type"], path)
    if "const" in schema and instance != schema["const"]:
        fail(f"Schema const mismatch at {path}")
    if "enum" in schema and instance not in schema["enum"]:
        fail(f"Schema enum mismatch at {path}")
    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            fail(f"Schema string too short at {path}")
        if "pattern" in schema and re.fullmatch(schema["pattern"], instance) is None:
            fail(f"Schema pattern mismatch at {path}")
    if isinstance(instance, int) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            fail(f"Schema minimum mismatch at {path}")
    if isinstance(instance, dict):
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        missing = [key for key in required if key not in instance]
        if missing:
            fail(f"Schema required field(s) missing at {path}: {missing}")
        if schema.get("additionalProperties") is False:
            unknown = set(instance) - set(properties)
            if unknown:
                fail(f"Schema unknown field(s) at {path}: {sorted(unknown)}")
        for key, child in instance.items():
            if key in properties:
                validate_instance(child, properties[key], root, f"{path}.{key}")
    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            fail(f"Schema array too short at {path}")
        if schema.get("uniqueItems") and len({canonical_json(item) for item in instance}) != len(instance):
            fail(f"Schema array items are not unique at {path}")
        if "items" in schema:
            for index, child in enumerate(instance):
                validate_instance(child, schema["items"], root, f"{path}[{index}]")


def validate_release_semantics(value: dict[str, Any]) -> None:
    assert_no_prohibited_fields(value)
    artifacts = value["artifacts"]
    if value["artifact_count"] != len(artifacts):
        fail("Release artifact_count does not match artifacts array")
    artifact_ids = [item["artifact_id"] for item in artifacts]
    relative_paths = [item["relative_path"] for item in artifacts]
    if len(set(artifact_ids)) != len(artifact_ids):
        fail("Duplicate release artifact_id")
    if len(set(relative_paths)) != len(relative_paths):
        fail("Duplicate release relative_path")
    scope = value["release_scope"]
    scoped = (
        scope["scientific_artifact_ids"]
        + scope["governance_artifact_ids"]
        + scope["communication_artifact_ids"]
    )
    if len(scoped) != len(set(scoped)) or set(scoped) != set(artifact_ids):
        fail("Release scope does not partition all artifact IDs exactly once")
    expected_scope = {
        "SCIENTIFIC": set(scope["scientific_artifact_ids"]),
        "GOVERNANCE": set(scope["governance_artifact_ids"]),
        "COMMUNICATION": set(scope["communication_artifact_ids"]),
    }
    for artifact in artifacts:
        if artifact["artifact_id"] not in expected_scope[artifact["artifact_scope"]]:
            fail("Artifact scope classification mismatch")
    boundaries = value["release_boundaries"]
    if any(boundaries.values()):
        fail("Release boundary flag must remain false")
    lifecycle = value["lifecycle_state"]
    if lifecycle in {"FROZEN", "RELEASED"}:
        if value["validation_summary"]["overall_validation_status"] != "PASS":
            fail("Frozen/released manifest lacks PASS validation")
        if any(item["validation_status"] != "PASS" for item in artifacts):
            fail("Frozen/released manifest contains non-PASS artifact")
    if lifecycle == "RELEASED":
        if any(item["lifecycle_state"] != "RELEASED" for item in artifacts):
            fail("Released manifest contains non-released artifact")
        if any(
            item["storage_reference"]["availability_status"] != "AVAILABLE"
            for item in artifacts
        ):
            fail("Released manifest contains unavailable storage")


def build_valid_fixture() -> dict[str, Any]:
    artifacts = []
    fixture_specs = [
        ("ART_FIX_SCIENTIFIC", "SCIENTIFIC", "EVIDENCE_LANDSCAPE", "artifacts/landscape.json"),
        ("ART_FIX_GOVERNANCE", "GOVERNANCE", "SCHEMA", "schemas/release.json"),
        ("ART_FIX_COMMUNICATION", "COMMUNICATION", "PRESENTATION_ARTIFACT", "communication/summary.md"),
    ]
    for index, (artifact_id, scope, artifact_type, relative_path) in enumerate(fixture_specs, 1):
        artifacts.append(
            {
                "artifact_id": artifact_id,
                "relative_path": relative_path,
                "artifact_version": "V0.1",
                "artifact_type": artifact_type,
                "artifact_scope": scope,
                "generating_task": "TASK_037A_FIXTURE",
                "lifecycle_state": "PROPOSED",
                "validation_status": "PASS",
                "sha256": f"{index:064x}",
                "size_bytes": index,
                "provenance_reference": {
                    "upstream_artifact_id": "ART_FIX_UPSTREAM",
                    "upstream_artifact_sha256": "a" * 64,
                    "relationship_type": "DERIVED_FROM",
                },
                "storage_reference": {
                    "storage_class": "GIT_MANAGED",
                    "storage_uri": relative_path,
                    "availability_status": "AVAILABLE",
                    "retrieval_required_for_release": False,
                },
            }
        )
    artifact_versions = {
        name: "V0.1"
        for name in build_schema()["properties"]["artifact_versions"]["required"]
    }
    artifact_versions["release_manifest_schema_version"] = SCHEMA_VERSION
    return {
        "release_id": "REL_" + "A" * 32,
        "release_version": "v0.1.0",
        "release_type": "INTERNAL_RESEARCH_ARTIFACT",
        "lifecycle_state": "PROPOSED",
        "project_id": PROJECT_ID,
        "release_manifest_schema_version": SCHEMA_VERSION,
        "component_versions": {
            "COMP_TRANSCRIPTOMIC_EVIDENCE": "COMP_TRANSCRIPTOMIC_EVIDENCE_V0.1",
            "COMP_DISEASE_ASSOCIATION": "COMP_DISEASE_ASSOCIATION_V0.1",
        },
        "artifact_versions": artifact_versions,
        "release_scope": {
            "scientific_artifact_ids": ["ART_FIX_SCIENTIFIC"],
            "governance_artifact_ids": ["ART_FIX_GOVERNANCE"],
            "communication_artifact_ids": ["ART_FIX_COMMUNICATION"],
            "explicit_exclusions": [],
        },
        "artifacts": artifacts,
        "artifact_count": len(artifacts),
        "validation_summary": {
            "schema_validation": "PASS",
            "artifact_integrity": "PASS",
            "provenance_reconciliation": "PASS",
            "storage_reconciliation": "PASS",
            "deterministic_regeneration": "PASS",
            "prohibited_field_scan": "PASS",
            "frozen_input_hashes": "PASS",
            "overall_validation_status": "PASS",
        },
        "release_boundaries": {
            "new_scientific_evidence_generated": False,
            "biological_validation_claimed": False,
            "target_recommendation_claimed": False,
            "runtime_ai_decisions_used": False,
        },
    }


def expect_rejected(value: dict[str, Any], schema: dict[str, Any], label: str) -> None:
    try:
        validate_instance(value, schema, schema)
        validate_release_semantics(value)
    except RuntimeError:
        return
    fail(f"Invalid release fixture was accepted: {label}")


def validate_fixtures(schema: dict[str, Any]) -> int:
    fixture = build_valid_fixture()
    validate_instance(fixture, schema, schema)
    validate_release_semantics(fixture)
    tests = 1
    for field in sorted(PROHIBITED_FIELDS):
        candidate = deepcopy(fixture)
        candidate[field] = "PROHIBITED"
        expect_rejected(candidate, schema, f"root prohibited field {field}")
        candidate = deepcopy(fixture)
        candidate["artifacts"][0][field] = "PROHIBITED"
        expect_rejected(candidate, schema, f"artifact prohibited field {field}")
        tests += 2
    candidate = deepcopy(fixture)
    candidate["artifact_count"] += 1
    expect_rejected(candidate, schema, "artifact count mismatch")
    tests += 1
    candidate = deepcopy(fixture)
    candidate["release_scope"]["scientific_artifact_ids"].append("ART_FIX_GOVERNANCE")
    expect_rejected(candidate, schema, "scope overlap")
    tests += 1
    candidate = deepcopy(fixture)
    candidate["release_boundaries"]["biological_validation_claimed"] = True
    expect_rejected(candidate, schema, "biological validation boundary")
    tests += 1
    candidate = deepcopy(fixture)
    candidate["lifecycle_state"] = "RELEASED"
    for artifact in candidate["artifacts"]:
        artifact["lifecycle_state"] = "RELEASED"
    candidate["artifacts"][0]["storage_reference"]["availability_status"] = (
        "PENDING_DURABLE_REGISTRATION"
    )
    expect_rejected(candidate, schema, "released package with pending storage")
    tests += 1
    return tests


def build_outputs(
    schema_bytes: bytes,
    document_hashes: dict[str, str],
    frozen_hashes: dict[str, str],
    manifests: dict[str, dict[str, Any]],
    fixture_tests: int,
) -> dict[str, bytes]:
    landscape = manifests["landscape"]
    summary = manifests["summary"]
    prioritization = manifests["prioritization"]
    dossier = manifests["dossier"]
    presentation = manifests["presentation"]
    schema_hash = sha256_bytes(schema_bytes)
    manifest = {
        "task_id": TASK_ID,
        "schema_governance_id": stable_id(
            "RELSCHEMA",
            [SCHEMA_VERSION, SPECIFICATION_VERSION, SCOPE_POLICY_VERSION, VALIDATION_REQUIREMENTS_VERSION],
        ),
        "schema_version": SCHEMA_VERSION,
        "specification_version": SPECIFICATION_VERSION,
        "scope_policy_version": SCOPE_POLICY_VERSION,
        "validation_requirements_version": VALIDATION_REQUIREMENTS_VERSION,
        "generator": {
            "relative_path": "analysis/37A_define_release_manifest_schema.py",
            "generator_version": GENERATOR_VERSION,
            "sha256": sha256_file(ROOT / "analysis/37A_define_release_manifest_schema.py"),
        },
        "schema": {
            "relative_path": "schemas/release_manifest_schema_v0.1.json",
            "sha256": schema_hash,
        },
        "governance_documents": document_hashes,
        "frozen_source_releases": {
            "landscape": {
                "release_id": landscape["release_id"],
                "schema_version": landscape["landscape_schema_version"],
                "artifact_version": landscape["landscape_version"],
            },
            "evidence_summary": {
                "release_id": summary["release_id"],
                "schema_version": summary["evidence_summary_schema_version"],
                "artifact_version": summary["evidence_summary_version"],
            },
            "transparent_prioritization": {
                "release_id": prioritization["release_id"],
                "schema_version": prioritization["prioritization_output_schema_version"],
                "artifact_version": prioritization["prioritization_representation_version"],
                "rule_catalog_version": prioritization["rule_catalog"]["version"],
            },
            "representative_case_dossiers": {
                "release_id": dossier["release_id"],
                "artifact_version": dossier["dossier_release_version"],
            },
            "presentation_artifacts": {
                "release_id": presentation["presentation_release_id"],
                "artifact_version": presentation["presentation_version"],
            },
        },
        "frozen_inputs": frozen_hashes,
        "validation": {
            "schema_deterministic_generation": "PASS",
            "schema_objects_closed": "PASS",
            "valid_fixture": "PASS",
            "invalid_fixture_tests": fixture_tests - 1,
            "prohibited_field_rejection": "PASS",
            "terminology_compatibility": "PASS",
            "markdown_link_resolution": "PASS",
            "frozen_artifact_hashes_unchanged": "PASS",
            "scientific_artifacts_modified": False,
            "release_package_generated": False,
        },
        "validation_status": "PASS",
    }
    report = f"""# Task #037A Release Governance Validation Report

**Validation status:** PASS

## Generated contract

- Schema: `{SCHEMA_VERSION}`
- Package specification: `{SPECIFICATION_VERSION}`
- Scope policy: `{SCOPE_POLICY_VERSION}`
- Validation requirements: `{VALIDATION_REQUIREMENTS_VERSION}`

## Validation results

- PASS — schema generated twice with byte-identical output
- PASS — every schema object is closed to undeclared fields
- PASS — one valid synthetic governance fixture accepted
- PASS — {fixture_tests - 1} invalid synthetic fixtures rejected
- PASS — all {len(PROHIBITED_FIELDS)} prohibited exact field names rejected at root and artifact-record levels
- PASS — lifecycle, artifact-count, scope-partition, release-boundary, and released-storage invariants tested
- PASS — terminology reconciled with Tasks #033B, #034B, #035B, #036B, and #036C
- PASS — all local Markdown links resolve
- PASS — all {len(FROZEN_INPUT_SHA256)} frozen input hashes unchanged before and after generation
- PASS — no previous scientific, governance, or communication artifact modified
- PASS — no network/API access, analysis rerun, component rebuild, or runtime AI decision

## Boundary

Task #037A generated a schema and governance records only. It did not create, freeze, or release a concrete package. Schema conformance establishes packaging structure; it does not establish biological validation or target recommendation.
""".encode("utf-8")
    session = ("\n".join([
        f"task={TASK_ID}",
        f"generator_version={GENERATOR_VERSION}",
        f"schema_version={SCHEMA_VERSION}",
        f"specification_version={SPECIFICATION_VERSION}",
        f"scope_policy_version={SCOPE_POLICY_VERSION}",
        f"validation_requirements_version={VALIDATION_REQUIREMENTS_VERSION}",
        f"python_version={platform.python_version()}",
        f"python_implementation={platform.python_implementation()}",
        "standard_library_only=TRUE",
        "network_access=PROHIBITED_NOT_USED",
        "api_access=PROHIBITED_NOT_USED",
        "analysis_pipelines_rerun=FALSE",
        "components_rebuilt=FALSE",
        "runtime_ai_llm_decisions=PROHIBITED_NONE_USED",
        "randomness=NOT_USED",
        "wall_clock_governed_values=NOT_USED",
        "release_package_generated=FALSE",
        "deterministic_schema_generation=BYTE_IDENTICAL",
    ]) + "\n").encode("utf-8")
    return {
        "release_schema_manifest.json": pretty_json_bytes(manifest),
        "validation_report.md": report,
        "session_info.txt": session,
    }


def main() -> None:
    validate_working_tree_scope()
    validate_output_scope()
    frozen_before = validate_frozen_inputs()
    manifests = load_upstream_manifests()

    first_schema = pretty_json_bytes(build_schema())
    second_schema = pretty_json_bytes(build_schema())
    if first_schema != second_schema:
        fail("Release manifest schema generation is not deterministic")
    SCHEMA_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCHEMA_PATH.write_bytes(first_schema)

    document_hashes = validate_documentation()
    schema = json.loads(first_schema)
    assert_closed_schema(schema)
    fixture_tests = validate_fixtures(schema)
    first_outputs = build_outputs(
        first_schema, document_hashes, frozen_before, manifests, fixture_tests
    )
    second_outputs = build_outputs(
        first_schema, document_hashes, frozen_before, manifests, fixture_tests
    )
    if first_outputs != second_outputs:
        fail("Release governance output generation is not deterministic")
    if frozen_before != validate_frozen_inputs():
        fail("Frozen input hashes changed during Task #037A generation")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, data in sorted(first_outputs.items()):
        (OUTPUT_DIR / name).write_bytes(data)
    if SCHEMA_PATH.read_bytes() != first_schema:
        fail("Written release schema differs from validated schema bytes")
    if any((OUTPUT_DIR / name).read_bytes() != data for name, data in first_outputs.items()):
        fail("Written release governance output differs from validated bytes")
    if frozen_before != validate_frozen_inputs():
        fail("Frozen input hashes changed after Task #037A generation")
    validate_working_tree_scope()

    print(f"schema_version={SCHEMA_VERSION}")
    print(f"fixture_tests={fixture_tests}")
    print("release_package_generated=FALSE")
    print("deterministic_generation=BYTE_IDENTICAL")
    print("validation_status=PASS")


if __name__ == "__main__":
    main()
