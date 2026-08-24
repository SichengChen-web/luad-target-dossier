#!/usr/bin/env python3
"""Build Artifact Registry v0.1 from frozen release-framework metadata.

This registry-only task inventories immutable computational artifacts. It does
not create a release package, read or copy external payload bytes, rerun an
analysis, rebuild a component, retrieve evidence, access a network/API,
interpret biology, score or rank targets, recommend targets, or use runtime AI.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import platform
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "docs/governance/artifact_registry_policy_v0.1.md"
SCHEMA_PATH = ROOT / "schemas/artifact_registry_schema_v0.1.json"
OUTPUT_DIR = ROOT / "outputs/artifact_registry_v0.1"
REGISTRY_PATH = OUTPUT_DIR / "artifact_registry.csv"
MANIFEST_PATH = OUTPUT_DIR / "artifact_registry_manifest.json"
REPORT_PATH = OUTPUT_DIR / "validation_report.md"
SESSION_PATH = OUTPUT_DIR / "session_info.txt"

TASK_ID = "TASK_037B"
REGISTRY_VERSION = "ARTIFACT_REGISTRY_V0.1"
POLICY_VERSION = "ARTIFACT_REGISTRY_POLICY_V0.1"
SCHEMA_VERSION = "ARTIFACT_REGISTRY_SCHEMA_V0.1"
GENERATOR_VERSION = "ARTIFACT_REGISTRY_GENERATOR_V0.1"
SCHEMA_ID = "urn:luad-target-dossier:artifact-registry-schema:v0.1"
EXPECTED_EXTERNAL_PAYLOADS = 3

REGISTRY_COLUMNS = [
    "artifact_id",
    "relative_path",
    "artifact_type",
    "artifact_scope",
    "artifact_version",
    "generating_task",
    "lifecycle_state",
    "validation_status",
    "sha256",
    "size_bytes",
    "storage_class",
    "storage_reference",
    "provenance_reference",
    "dependency_reference",
]

ARTIFACT_TYPES = [
    "MANIFEST",
    "INDEX",
    "PARTITION_MANIFEST",
    "REPRESENTATION_PAYLOAD",
    "EXTERNAL_PAYLOAD",
    "VALIDATION_REPORT",
    "SESSION_METADATA",
    "PRESENTATION_ARTIFACT",
    "POLICY",
    "SCHEMA",
    "GENERATOR_SOURCE",
]
ARTIFACT_SCOPES = ["SCIENTIFIC", "GOVERNANCE", "COMMUNICATION"]
LIFECYCLE_STATES = ["PROPOSED", "VALIDATED", "FROZEN", "RELEASED"]
VALIDATION_STATES = ["NOT_RUN", "PASS", "FAIL"]
STORAGE_CLASSES = ["GIT_MANAGED", "EXTERNAL_IMMUTABLE"]

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
    "analysis/37A_define_release_manifest_schema.py": "7796c454ef30185fb886cea52f02e1e0fce669868d91515d116619431b4cbf20",
    "docs/governance/release_package_specification_v0.1.md": "39125ef1d550597ae9bb7af97b1fc81e7eee7d37cc8e54149276db8c2f3fe0ad",
    "docs/governance/release_scope_policy_v0.1.md": "ce47a9c5b3b111d8230c38e92e3012e6e4e8f81adcd47318e49ebcb3326959a3",
    "docs/governance/release_validation_requirements_v0.1.md": "104013b5ff9eeedd55b78a2f015b0f220a3ac1f5cc1bb2d464f8b16df158a1f1",
    "schemas/release_manifest_schema_v0.1.json": "3b2bcb87e37d9cb83b2d1f5dceb0e2d503683a0be9c517dd899f3686d9b8b93b",
    "outputs/release_governance_v0.1/release_schema_manifest.json": "6176fb134bd452f14b29ef7a0b6fe0a52366f3492d17bc9f97b32b6d0323c960",
    "outputs/release_governance_v0.1/validation_report.md": "26d8f481fabe05f62d816ecdee15f5dba29edb0b12b52fc7b993e26cc3c67427",
    "outputs/release_governance_v0.1/session_info.txt": "e460abc9d993493277c71db200cb2e1fd82242c404843663aa018d261b264e20",
}

ALLOWED_WORKTREE_PATHS = {
    "analysis/37B_build_artifact_registry.py",
    "docs/governance/artifact_registry_policy_v0.1.md",
    "schemas/artifact_registry_schema_v0.1.json",
    "outputs/artifact_registry_v0.1/artifact_registry.csv",
    "outputs/artifact_registry_v0.1/artifact_registry_manifest.json",
    "outputs/artifact_registry_v0.1/validation_report.md",
    "outputs/artifact_registry_v0.1/session_info.txt",
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


def csv_bytes(rows: list[dict[str, Any]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=REGISTRY_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def closed_object(properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": required,
    }


def build_schema() -> dict[str, Any]:
    sha_schema = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
    artifact_id = {"type": "string", "pattern": "^ART(?:REG)?_[A-Z0-9_]+$"}
    record = closed_object(
        {
            "artifact_id": artifact_id,
            "relative_path": {"type": "string", "minLength": 1},
            "artifact_type": {"type": "string", "enum": ARTIFACT_TYPES},
            "artifact_scope": {"type": "string", "enum": ARTIFACT_SCOPES},
            "artifact_version": {"type": "string", "minLength": 1},
            "generating_task": {"type": "string", "pattern": "^TASK_[A-Z0-9_]+$"},
            "lifecycle_state": {"type": "string", "enum": LIFECYCLE_STATES},
            "validation_status": {"type": "string", "enum": VALIDATION_STATES},
            "sha256": sha_schema,
            "size_bytes": {"type": "integer", "minimum": 0},
            "storage_class": {"type": "string", "enum": STORAGE_CLASSES},
            "storage_reference": {"type": "string", "minLength": 1},
            "provenance_reference": {"type": "string", "minLength": 1},
            "dependency_reference": {"type": "string", "minLength": 1},
        },
        REGISTRY_COLUMNS,
    )
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": SCHEMA_ID,
        "title": "LUAD Target Evidence Dossier Artifact Registry Schema v0.1",
        "description": "Closed metadata-only schema for a governed computational artifact inventory.",
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "registry_id": {"type": "string", "pattern": "^ARTREGISTRY_[A-F0-9]{32}$"},
            "registry_version": {"type": "string", "const": REGISTRY_VERSION},
            "registry_schema_version": {"type": "string", "const": SCHEMA_VERSION},
            "record_count": {"type": "integer", "minimum": 1},
            "records": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/artifactRecord"}},
            "registry_boundaries": closed_object(
                {
                    "release_package_generated": {"type": "boolean", "const": False},
                    "external_payloads_copied": {"type": "boolean", "const": False},
                    "scientific_interpretation_added": {"type": "boolean", "const": False},
                    "runtime_ai_decisions_used": {"type": "boolean", "const": False},
                },
                [
                    "release_package_generated",
                    "external_payloads_copied",
                    "scientific_interpretation_added",
                    "runtime_ai_decisions_used",
                ],
            ),
        },
        "required": [
            "registry_id",
            "registry_version",
            "registry_schema_version",
            "record_count",
            "records",
            "registry_boundaries",
        ],
        "$defs": {"artifactRecord": record},
        "$comment": "Registry inclusion records computational identity only and is not scientific evaluation.",
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
    for line in result.stdout.splitlines():
        if not line:
            continue
        path_text = line[3:]
        if " -> " in path_text:
            path_text = path_text.split(" -> ", 1)[1]
        if path_text not in ALLOWED_WORKTREE_PATHS:
            unexpected.append(line)
    if unexpected:
        fail("Unexpected working-tree changes:\n" + "\n".join(unexpected))


def validate_output_scope() -> None:
    allowed = {REGISTRY_PATH, MANIFEST_PATH, REPORT_PATH, SESSION_PATH}
    if OUTPUT_DIR.exists():
        unexpected = sorted(
            path.relative_to(ROOT).as_posix()
            for path in OUTPUT_DIR.rglob("*")
            if path.is_file() and path not in allowed
        )
        if unexpected:
            fail("Unexpected Task #037B output files: " + ", ".join(unexpected))


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


def validate_policy() -> str:
    if not POLICY_PATH.is_file():
        fail("Artifact Registry Policy is missing")
    text = POLICY_PATH.read_text(encoding="utf-8")
    required = [
        POLICY_VERSION,
        "registry inclusion != biological validation",
        "registry inclusion != evidence strength",
        "registry inclusion != target importance",
        "registry inclusion != therapeutic recommendation",
        "Task #037B must not open, copy, move, upload, or rewrite external payload bytes",
    ]
    for term in required:
        if term not in text:
            fail(f"Artifact Registry Policy terminology missing: {term}")
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
        if target.startswith(("http://", "https://", "#")):
            continue
        if not (POLICY_PATH.parent / target.split("#", 1)[0]).resolve().is_file():
            fail(f"Broken Artifact Registry Policy link: {target}")
    return sha256_file(POLICY_PATH)


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
        target: Any = root
        for token in schema["$ref"][2:].split("/"):
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
        missing = [key for key in schema.get("required", []) if key not in instance]
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
        if "items" in schema:
            for index, child in enumerate(instance):
                validate_instance(child, schema["items"], root, f"{path}[{index}]")


def load_manifests() -> dict[str, dict[str, Any]]:
    paths = {
        "landscape": ROOT / "outputs/evidence_landscape_v0.2/landscape_manifest.json",
        "summary": ROOT / "outputs/evidence_summary_v0.1/summary_manifest.json",
        "prioritization": ROOT / "outputs/prioritization_v0.1/prioritization_manifest.json",
        "dossier": ROOT / "outputs/case_dossiers_v0.1/dossier_manifest.json",
        "presentation": ROOT / "outputs/presentation_artifacts_v0.1/presentation_manifest.json",
        "release_governance": ROOT / "outputs/release_governance_v0.1/release_schema_manifest.json",
    }
    values = {name: json.loads(path.read_text(encoding="utf-8")) for name, path in paths.items()}
    for name, value in values.items():
        if value.get("validation_status") != "PASS":
            fail(f"Frozen source manifest is not validated: {name}")
    if values["landscape"].get("counts", {}).get("landscapes") != 29_606:
        fail("Landscape entity count changed")
    if values["summary"].get("counts", {}).get("summaries") != 29_606:
        fail("Evidence Summary entity count changed")
    if values["prioritization"].get("counts", {}).get("representations") != 29_606:
        fail("Routing representation entity count changed")
    if values["dossier"].get("counts", {}).get("case_slots") != 4:
        fail("Case dossier slot count changed")
    if values["presentation"].get("counts", {}).get("canonical_entities") != 29_606:
        fail("Presentation entity count changed")
    if values["release_governance"].get("schema_version") != "RELEASE_MANIFEST_SCHEMA_V0.1":
        fail("Task #037A release schema version changed")
    return values


def make_file_spec(
    relative_path: str,
    artifact_type: str,
    scope: str,
    version: str,
    task: str,
    provenance: str,
    dependencies: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "relative_path": relative_path,
        "artifact_type": artifact_type,
        "artifact_scope": scope,
        "artifact_version": version,
        "generating_task": task,
        "provenance_reference": provenance,
        "dependency_paths": dependencies or [],
    }


def build_file_specs(manifests: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    landscape_manifest = "outputs/evidence_landscape_v0.2/landscape_manifest.json"
    summary_manifest = "outputs/evidence_summary_v0.1/summary_manifest.json"
    prioritization_manifest = "outputs/prioritization_v0.1/prioritization_manifest.json"
    dossier_manifest = "outputs/case_dossiers_v0.1/dossier_manifest.json"
    presentation_manifest = "outputs/presentation_artifacts_v0.1/presentation_manifest.json"
    task37a_schema = "schemas/release_manifest_schema_v0.1.json"
    specs: list[dict[str, Any]] = []

    def add_layer(
        base: str,
        files: list[tuple[str, str, str]],
        version: str,
        task: str,
        release_id: str,
        manifest_path: str,
        manifest_dependencies: list[str],
    ) -> None:
        for filename, artifact_type, scope in files:
            path = f"{base}/{filename}"
            dependencies = manifest_dependencies if path == manifest_path else [manifest_path]
            specs.append(
                make_file_spec(
                    path,
                    artifact_type,
                    scope,
                    version,
                    task,
                    f"SOURCE_RELEASE::{release_id}",
                    dependencies,
                )
            )

    add_layer(
        "outputs/evidence_landscape_v0.2",
        [
            ("landscape_manifest.json", "MANIFEST", "SCIENTIFIC"),
            ("landscape_index.csv", "INDEX", "SCIENTIFIC"),
            ("partition_manifest.csv", "PARTITION_MANIFEST", "SCIENTIFIC"),
            ("validation_report.md", "VALIDATION_REPORT", "GOVERNANCE"),
            ("session_info.txt", "SESSION_METADATA", "GOVERNANCE"),
        ],
        manifests["landscape"]["landscape_version"],
        "TASK_033B_2",
        manifests["landscape"]["release_id"],
        landscape_manifest,
        [],
    )
    add_layer(
        "outputs/evidence_summary_v0.1",
        [
            ("summary_manifest.json", "MANIFEST", "SCIENTIFIC"),
            ("summary_index.csv", "INDEX", "SCIENTIFIC"),
            ("partition_manifest.csv", "PARTITION_MANIFEST", "SCIENTIFIC"),
            ("validation_report.md", "VALIDATION_REPORT", "GOVERNANCE"),
            ("session_info.txt", "SESSION_METADATA", "GOVERNANCE"),
        ],
        manifests["summary"]["evidence_summary_version"],
        "TASK_034B",
        manifests["summary"]["release_id"],
        summary_manifest,
        [landscape_manifest],
    )
    add_layer(
        "outputs/prioritization_v0.1",
        [
            ("prioritization_manifest.json", "MANIFEST", "SCIENTIFIC"),
            ("prioritization_index.csv", "INDEX", "SCIENTIFIC"),
            ("partition_manifest.csv", "PARTITION_MANIFEST", "SCIENTIFIC"),
            ("validation_report.md", "VALIDATION_REPORT", "GOVERNANCE"),
            ("session_info.txt", "SESSION_METADATA", "GOVERNANCE"),
        ],
        manifests["prioritization"]["prioritization_representation_version"],
        "TASK_035B",
        manifests["prioritization"]["release_id"],
        prioritization_manifest,
        [summary_manifest],
    )
    add_layer(
        "outputs/case_dossiers_v0.1",
        [
            ("dossier_manifest.json", "MANIFEST", "SCIENTIFIC"),
            ("case_selection_index.csv", "INDEX", "SCIENTIFIC"),
            ("case_dossiers.json", "REPRESENTATION_PAYLOAD", "SCIENTIFIC"),
            ("validation_report.md", "VALIDATION_REPORT", "GOVERNANCE"),
            ("session_info.txt", "SESSION_METADATA", "GOVERNANCE"),
        ],
        manifests["dossier"]["dossier_release_version"],
        "TASK_036B",
        manifests["dossier"]["release_id"],
        dossier_manifest,
        [prioritization_manifest],
    )
    add_layer(
        "outputs/presentation_artifacts_v0.1",
        [
            ("presentation_manifest.json", "MANIFEST", "GOVERNANCE"),
            ("architecture_summary.md", "PRESENTATION_ARTIFACT", "COMMUNICATION"),
            ("evidence_layer_summary.csv", "PRESENTATION_ARTIFACT", "COMMUNICATION"),
            ("case_pattern_summary.csv", "PRESENTATION_ARTIFACT", "COMMUNICATION"),
            ("provenance_flow_summary.md", "PRESENTATION_ARTIFACT", "COMMUNICATION"),
            ("validation_report.md", "VALIDATION_REPORT", "GOVERNANCE"),
            ("session_info.txt", "SESSION_METADATA", "GOVERNANCE"),
        ],
        manifests["presentation"]["presentation_version"],
        "TASK_036C",
        manifests["presentation"]["presentation_release_id"],
        presentation_manifest,
        [landscape_manifest, summary_manifest, prioritization_manifest, dossier_manifest],
    )

    release_inputs = [
        landscape_manifest,
        summary_manifest,
        prioritization_manifest,
        dossier_manifest,
        presentation_manifest,
    ]
    task37a_specs = [
        ("docs/governance/release_package_specification_v0.1.md", "POLICY", "RELEASE_PACKAGE_SPECIFICATION_V0.1", release_inputs),
        ("docs/governance/release_scope_policy_v0.1.md", "POLICY", "RELEASE_SCOPE_POLICY_V0.1", release_inputs),
        ("docs/governance/release_validation_requirements_v0.1.md", "POLICY", "RELEASE_VALIDATION_REQUIREMENTS_V0.1", release_inputs),
        ("analysis/37A_define_release_manifest_schema.py", "GENERATOR_SOURCE", "RELEASE_MANIFEST_SCHEMA_GENERATOR_V0.1", release_inputs),
        (task37a_schema, "SCHEMA", "RELEASE_MANIFEST_SCHEMA_V0.1", release_inputs),
        ("outputs/release_governance_v0.1/release_schema_manifest.json", "MANIFEST", "RELEASE_SCHEMA_GOVERNANCE_V0.1", [task37a_schema]),
        ("outputs/release_governance_v0.1/validation_report.md", "VALIDATION_REPORT", "RELEASE_SCHEMA_GOVERNANCE_V0.1", ["outputs/release_governance_v0.1/release_schema_manifest.json"]),
        ("outputs/release_governance_v0.1/session_info.txt", "SESSION_METADATA", "RELEASE_SCHEMA_GOVERNANCE_V0.1", ["outputs/release_governance_v0.1/release_schema_manifest.json"]),
    ]
    for path, artifact_type, version, dependencies in task37a_specs:
        specs.append(
            make_file_spec(
                path,
                artifact_type,
                "GOVERNANCE",
                version,
                "TASK_037A",
                f"SCHEMA_GOVERNANCE::{manifests['release_governance']['schema_governance_id']}",
                dependencies,
            )
        )

    task37b_specs = [
        ("docs/governance/artifact_registry_policy_v0.1.md", "POLICY", POLICY_VERSION),
        ("schemas/artifact_registry_schema_v0.1.json", "SCHEMA", SCHEMA_VERSION),
        ("analysis/37B_build_artifact_registry.py", "GENERATOR_SOURCE", GENERATOR_VERSION),
    ]
    for path, artifact_type, version in task37b_specs:
        specs.append(
            make_file_spec(
                path,
                artifact_type,
                "GOVERNANCE",
                version,
                TASK_ID,
                f"REGISTRY_CONTRACT::{POLICY_VERSION}",
                [task37a_schema],
            )
        )
    return specs


def derive_landscape_storage_reference() -> str:
    path = ROOT / "outputs/evidence_landscape_v0.2/partition_manifest.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or "external_storage_reference" not in rows[0]:
        fail("Landscape partition manifest lacks storage references")
    prefixes = {
        row["external_storage_reference"].split("/partitions/", 1)[0] + "/"
        for row in rows
        if "/partitions/" in row["external_storage_reference"]
    }
    if len(prefixes) != 1:
        fail("Landscape external partition references do not share one immutable set prefix")
    return next(iter(prefixes))


def external_specs(manifests: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    landscape = manifests["landscape"]
    summary = manifests["summary"]
    prioritization = manifests["prioritization"]
    return [
        {
            "artifact_id": landscape["partition_set"]["partition_set_artifact_id"],
            "relative_path": f"EXTERNAL::{landscape['partition_set']['partition_set_artifact_id']}",
            "artifact_type": "EXTERNAL_PAYLOAD",
            "artifact_scope": "SCIENTIFIC",
            "artifact_version": landscape["landscape_version"],
            "generating_task": "TASK_033B_2",
            "sha256": landscape["partition_set"]["partition_set_sha256"],
            "size_bytes": landscape["partition_set"]["total_bytes"],
            "storage_class": "EXTERNAL_IMMUTABLE",
            "storage_reference": derive_landscape_storage_reference(),
            "provenance_reference": f"SOURCE_RELEASE::{landscape['release_id']}",
            "dependency_paths": [
                "outputs/evidence_landscape_v0.2/landscape_manifest.json",
                "outputs/evidence_landscape_v0.2/partition_manifest.csv",
            ],
        },
        {
            "artifact_id": summary["large_payload"]["artifact_id"],
            "relative_path": f"EXTERNAL::{summary['large_payload']['artifact_id']}",
            "artifact_type": "EXTERNAL_PAYLOAD",
            "artifact_scope": "SCIENTIFIC",
            "artifact_version": summary["evidence_summary_version"],
            "generating_task": "TASK_034B",
            "sha256": summary["large_payload"]["partition_set_sha256"],
            "size_bytes": summary["large_payload"]["artifact_size"],
            "storage_class": "EXTERNAL_IMMUTABLE",
            "storage_reference": summary["large_payload"]["storage_reference_placeholder"],
            "provenance_reference": f"SOURCE_RELEASE::{summary['release_id']}",
            "dependency_paths": [
                "outputs/evidence_summary_v0.1/summary_manifest.json",
                "outputs/evidence_summary_v0.1/partition_manifest.csv",
            ],
        },
        {
            "artifact_id": prioritization["large_payload"]["artifact_id"],
            "relative_path": f"EXTERNAL::{prioritization['large_payload']['artifact_id']}",
            "artifact_type": "EXTERNAL_PAYLOAD",
            "artifact_scope": "SCIENTIFIC",
            "artifact_version": prioritization["prioritization_representation_version"],
            "generating_task": "TASK_035B",
            "sha256": prioritization["large_payload"]["partition_set_sha256"],
            "size_bytes": prioritization["large_payload"]["artifact_size"],
            "storage_class": "EXTERNAL_IMMUTABLE",
            "storage_reference": prioritization["large_payload"]["storage_reference_placeholder"],
            "provenance_reference": f"SOURCE_RELEASE::{prioritization['release_id']}",
            "dependency_paths": [
                "outputs/prioritization_v0.1/prioritization_manifest.json",
                "outputs/prioritization_v0.1/partition_manifest.csv",
            ],
        },
    ]


def build_records(manifests: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    file_specs = build_file_specs(manifests)
    file_rows: list[dict[str, Any]] = []
    path_to_id: dict[str, str] = {}
    for spec in file_specs:
        relative_path = spec["relative_path"]
        path = ROOT / relative_path
        if not path.is_file() or path.is_symlink():
            fail(f"Registry file artifact missing or unsafe: {relative_path}")
        digest = sha256_file(path)
        artifact_id = stable_id("ARTREG", [relative_path, digest])
        if relative_path in path_to_id:
            fail(f"Duplicate file spec path: {relative_path}")
        path_to_id[relative_path] = artifact_id
        file_rows.append(
            {
                "artifact_id": artifact_id,
                "relative_path": relative_path,
                "artifact_type": spec["artifact_type"],
                "artifact_scope": spec["artifact_scope"],
                "artifact_version": spec["artifact_version"],
                "generating_task": spec["generating_task"],
                "lifecycle_state": "VALIDATED",
                "validation_status": "PASS",
                "sha256": digest,
                "size_bytes": path.stat().st_size,
                "storage_class": "GIT_MANAGED",
                "storage_reference": relative_path,
                "provenance_reference": spec["provenance_reference"],
                "dependency_paths": spec["dependency_paths"],
            }
        )
    rows: list[dict[str, Any]] = []
    for row in file_rows:
        dependencies = row.pop("dependency_paths")
        row["dependency_reference"] = (
            "|".join(path_to_id[path] for path in dependencies)
            if dependencies
            else "NOT_APPLICABLE"
        )
        rows.append(row)
    for spec in external_specs(manifests):
        dependencies = spec.pop("dependency_paths")
        spec["dependency_reference"] = "|".join(path_to_id[path] for path in dependencies)
        spec["lifecycle_state"] = "VALIDATED"
        spec["validation_status"] = "PASS"
        rows.append(spec)
    rows.sort(key=lambda row: (row["artifact_scope"], row["artifact_type"], row["relative_path"]))
    return rows


def validate_records(records: list[dict[str, Any]], schema: dict[str, Any]) -> dict[str, Counter[str]]:
    envelope = {
        "registry_id": stable_id(
            "ARTREGISTRY",
            [REGISTRY_VERSION, [(row["artifact_id"], row["sha256"]) for row in records]],
        ),
        "registry_version": REGISTRY_VERSION,
        "registry_schema_version": SCHEMA_VERSION,
        "record_count": len(records),
        "records": records,
        "registry_boundaries": {
            "release_package_generated": False,
            "external_payloads_copied": False,
            "scientific_interpretation_added": False,
            "runtime_ai_decisions_used": False,
        },
    }
    validate_instance(envelope, schema, schema)
    assert_no_prohibited_fields(envelope)
    if envelope["record_count"] != len(records):
        fail("Registry record count mismatch")
    ids = [row["artifact_id"] for row in records]
    paths = [row["relative_path"] for row in records]
    if len(ids) != len(set(ids)):
        fail("Duplicate artifact identifiers")
    if len(paths) != len(set(paths)):
        fail("Duplicate registry paths")
    known = set(ids)
    graph: dict[str, set[str]] = {}
    for row in records:
        dependencies = (
            []
            if row["dependency_reference"] == "NOT_APPLICABLE"
            else row["dependency_reference"].split("|")
        )
        if row["artifact_id"] in dependencies:
            fail(f"Self dependency: {row['artifact_id']}")
        unknown = set(dependencies) - known
        if unknown:
            fail(f"Unknown dependency reference(s): {sorted(unknown)}")
        graph[row["artifact_id"]] = set(dependencies)
        if row["storage_class"] == "GIT_MANAGED":
            path = ROOT / row["relative_path"]
            if row["storage_reference"] != row["relative_path"]:
                fail("Git-managed storage reference differs from relative path")
            if path.stat().st_size != row["size_bytes"] or sha256_file(path) != row["sha256"]:
                fail(f"Git-managed registry record does not match bytes: {row['relative_path']}")
        else:
            if not row["relative_path"].startswith("EXTERNAL::"):
                fail("External payload lacks logical registry path")
            if row["artifact_type"] != "EXTERNAL_PAYLOAD":
                fail("External storage record is not an EXTERNAL_PAYLOAD")
            if (OUTPUT_DIR / row["artifact_id"]).exists():
                fail("External payload bytes were copied into registry output")

    temporary: set[str] = set()
    permanent: set[str] = set()

    def visit(node: str) -> None:
        if node in permanent:
            return
        if node in temporary:
            fail(f"Registry dependency cycle detected at {node}")
        temporary.add(node)
        for dependency in graph[node]:
            visit(dependency)
        temporary.remove(node)
        permanent.add(node)

    for artifact_id in sorted(graph):
        visit(artifact_id)
    external = [row for row in records if row["storage_class"] == "EXTERNAL_IMMUTABLE"]
    if len(external) != EXPECTED_EXTERNAL_PAYLOADS:
        fail(f"Expected {EXPECTED_EXTERNAL_PAYLOADS} external payload references, observed {len(external)}")
    return {
        "artifact_type": Counter(row["artifact_type"] for row in records),
        "artifact_scope": Counter(row["artifact_scope"] for row in records),
        "storage_class": Counter(row["storage_class"] for row in records),
        "lifecycle_state": Counter(row["lifecycle_state"] for row in records),
        "validation_status": Counter(row["validation_status"] for row in records),
    }


def validate_prohibited_field_rejection(schema: dict[str, Any], records: list[dict[str, Any]]) -> int:
    tests = 0
    base = {
        "registry_id": "ARTREGISTRY_" + "A" * 32,
        "registry_version": REGISTRY_VERSION,
        "registry_schema_version": SCHEMA_VERSION,
        "record_count": 1,
        "records": [dict(records[0])],
        "registry_boundaries": {
            "release_package_generated": False,
            "external_payloads_copied": False,
            "scientific_interpretation_added": False,
            "runtime_ai_decisions_used": False,
        },
    }
    for field in sorted(PROHIBITED_FIELDS):
        for location in ("root", "record"):
            candidate = json.loads(json.dumps(base))
            if location == "root":
                candidate[field] = "PROHIBITED"
            else:
                candidate["records"][0][field] = "PROHIBITED"
            try:
                validate_instance(candidate, schema, schema)
                assert_no_prohibited_fields(candidate)
            except RuntimeError:
                tests += 1
                continue
            fail(f"Prohibited field fixture accepted: {location}/{field}")
    return tests


def build_outputs(
    records: list[dict[str, Any]],
    counters: dict[str, Counter[str]],
    registry_bytes: bytes,
    schema_bytes: bytes,
    policy_hash: str,
    frozen_hashes: dict[str, str],
    prohibited_tests: int,
) -> dict[str, bytes]:
    registry_id = stable_id(
        "ARTREGISTRY",
        [REGISTRY_VERSION, [(row["artifact_id"], row["sha256"]) for row in records]],
    )
    external = [row for row in records if row["storage_class"] == "EXTERNAL_IMMUTABLE"]
    manifest = {
        "task_id": TASK_ID,
        "registry_id": registry_id,
        "registry_version": REGISTRY_VERSION,
        "registry_schema_version": SCHEMA_VERSION,
        "policy_version": POLICY_VERSION,
        "generator": {
            "relative_path": "analysis/37B_build_artifact_registry.py",
            "generator_version": GENERATOR_VERSION,
            "sha256": sha256_file(ROOT / "analysis/37B_build_artifact_registry.py"),
        },
        "registry_artifact": {
            "relative_path": "outputs/artifact_registry_v0.1/artifact_registry.csv",
            "sha256": sha256_bytes(registry_bytes),
            "size_bytes": len(registry_bytes),
        },
        "schema": {
            "relative_path": "schemas/artifact_registry_schema_v0.1.json",
            "sha256": sha256_bytes(schema_bytes),
        },
        "policy": {
            "relative_path": "docs/governance/artifact_registry_policy_v0.1.md",
            "sha256": policy_hash,
        },
        "counts": {
            "records": len(records),
            "by_artifact_type": dict(sorted(counters["artifact_type"].items())),
            "by_artifact_scope": dict(sorted(counters["artifact_scope"].items())),
            "by_storage_class": dict(sorted(counters["storage_class"].items())),
            "by_lifecycle_state": dict(sorted(counters["lifecycle_state"].items())),
            "by_validation_status": dict(sorted(counters["validation_status"].items())),
        },
        "external_payload_references": [
            {
                "artifact_id": row["artifact_id"],
                "artifact_version": row["artifact_version"],
                "sha256": row["sha256"],
                "size_bytes": row["size_bytes"],
                "storage_reference": row["storage_reference"],
                "dependency_reference": row["dependency_reference"],
            }
            for row in external
        ],
        "frozen_inputs": frozen_hashes,
        "validation": {
            "deterministic_regeneration": "BYTE_IDENTICAL",
            "unique_artifact_identifiers": "PASS",
            "unique_paths": "PASS",
            "dependency_references_resolved": "PASS",
            "dependency_graph_acyclic": "PASS",
            "frozen_upstream_hashes_unchanged": "PASS",
            "existing_artifacts_modified": False,
            "external_payloads_metadata_only": "PASS",
            "prohibited_field_tests": prohibited_tests,
            "scientific_interpretation_fields": "NONE",
            "release_package_generated": False,
        },
        "validation_status": "PASS",
    }
    report = f"""# Task #037B Artifact Registry Validation Report

**Validation status:** PASS

## Registry scope

- Registry records: **{len(records)}**
- Scientific-scope artifacts: **{counters['artifact_scope'].get('SCIENTIFIC', 0)}**
- Governance-scope artifacts: **{counters['artifact_scope'].get('GOVERNANCE', 0)}**
- Communication-scope artifacts: **{counters['artifact_scope'].get('COMMUNICATION', 0)}**
- Git-managed artifact records: **{counters['storage_class'].get('GIT_MANAGED', 0)}**
- External immutable payload references: **{counters['storage_class'].get('EXTERNAL_IMMUTABLE', 0)}**

## Validation

- PASS — deterministic schema and registry generation
- PASS — unique artifact identifiers and unique logical/relative paths
- PASS — every Git-managed row matches file size and SHA256
- PASS — every dependency resolves to a registered artifact; dependency graph is acyclic
- PASS — three source-native external payload IDs, sizes, partition-set hashes, and storage references reconciled from frozen manifests
- PASS — no external payload bytes opened, copied, uploaded, or written
- PASS — {prohibited_tests} prohibited-field fixtures rejected
- PASS — all {len(FROZEN_INPUT_SHA256)} frozen upstream artifact hashes unchanged before and after generation
- PASS — no existing artifact modified
- PASS — no network/API access, scientific rerun, component rebuild, biological interpretation, or runtime AI decision

## Boundary

This registry describes computational artifacts only. Registry inclusion does not establish biological validation, evidence strength, target importance, or therapeutic recommendation. No release package was created.
""".encode("utf-8")
    session = ("\n".join([
        f"task={TASK_ID}",
        f"registry_version={REGISTRY_VERSION}",
        f"registry_schema_version={SCHEMA_VERSION}",
        f"policy_version={POLICY_VERSION}",
        f"generator_version={GENERATOR_VERSION}",
        f"python_version={platform.python_version()}",
        f"python_implementation={platform.python_implementation()}",
        "standard_library_only=TRUE",
        "network_access=PROHIBITED_NOT_USED",
        "api_access=PROHIBITED_NOT_USED",
        "scientific_analyses_rerun=FALSE",
        "components_rebuilt=FALSE",
        "external_payload_bytes_read=FALSE",
        "external_payload_bytes_copied=FALSE",
        "external_uploads=FALSE",
        "runtime_ai_llm_decisions=PROHIBITED_NONE_USED",
        "randomness=NOT_USED",
        "wall_clock_governed_values=NOT_USED",
        "release_package_generated=FALSE",
        "deterministic_regeneration=BYTE_IDENTICAL",
    ]) + "\n").encode("utf-8")
    return {
        "artifact_registry_manifest.json": pretty_json_bytes(manifest),
        "validation_report.md": report,
        "session_info.txt": session,
    }


def main() -> None:
    validate_working_tree_scope()
    validate_output_scope()
    frozen_before = validate_frozen_inputs()
    manifests = load_manifests()

    first_schema = pretty_json_bytes(build_schema())
    second_schema = pretty_json_bytes(build_schema())
    if first_schema != second_schema:
        fail("Artifact registry schema generation is not deterministic")
    SCHEMA_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCHEMA_PATH.write_bytes(first_schema)
    policy_hash = validate_policy()

    schema = json.loads(first_schema)
    first_records = build_records(manifests)
    first_counters = validate_records(first_records, schema)
    prohibited_tests = validate_prohibited_field_rejection(schema, first_records)
    first_registry = csv_bytes(first_records)
    second_records = build_records(manifests)
    second_counters = validate_records(second_records, schema)
    second_registry = csv_bytes(second_records)
    if first_records != second_records or first_counters != second_counters or first_registry != second_registry:
        fail("Two complete artifact registry generations are not byte-identical")
    first_outputs = build_outputs(
        first_records,
        first_counters,
        first_registry,
        first_schema,
        policy_hash,
        frozen_before,
        prohibited_tests,
    )
    second_outputs = build_outputs(
        second_records,
        second_counters,
        second_registry,
        second_schema,
        policy_hash,
        frozen_before,
        prohibited_tests,
    )
    if first_outputs != second_outputs:
        fail("Two complete artifact registry metadata generations are not byte-identical")
    if frozen_before != validate_frozen_inputs():
        fail("Frozen upstream hashes changed during Task #037B generation")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_bytes(first_registry)
    for name, data in sorted(first_outputs.items()):
        (OUTPUT_DIR / name).write_bytes(data)
    if REGISTRY_PATH.read_bytes() != first_registry or SCHEMA_PATH.read_bytes() != first_schema:
        fail("Written registry/schema differs from validated bytes")
    if any((OUTPUT_DIR / name).read_bytes() != data for name, data in first_outputs.items()):
        fail("Written registry metadata differs from validated bytes")
    if frozen_before != validate_frozen_inputs():
        fail("Frozen upstream hashes changed after Task #037B generation")
    validate_working_tree_scope()

    print(f"registry_records={len(first_records)}")
    print(f"external_payload_references={first_counters['storage_class'].get('EXTERNAL_IMMUTABLE', 0)}")
    print("release_package_generated=FALSE")
    print("deterministic_regeneration=BYTE_IDENTICAL")
    print("validation_status=PASS")


if __name__ == "__main__":
    main()
