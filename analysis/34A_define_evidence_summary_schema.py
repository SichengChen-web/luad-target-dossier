#!/usr/bin/env python3
"""Define and validate Evidence Summary schema v0.1.

Task #034A creates governance and a machine-readable representation contract
only. It does not read landscape payloads, generate target summaries, retrieve
evidence, evaluate targets, or use runtime AI/LLM decisions.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from copy import deepcopy
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas/evidence_summary_schema_v0.1.json"

TASK_ID = "TASK_034A"
SCHEMA_VERSION = "EVIDENCE_SUMMARY_SCHEMA_V0.1"
SUMMARY_VERSION = "EVIDENCE_AGGREGATION_REPRESENTATION_V0.1"
GENERATOR_VERSION = "EVIDENCE_SUMMARY_SCHEMA_GENERATOR_V0.1"
SCHEMA_ID = "urn:luad-target-dossier:evidence-summary-schema:v0.1"
SOURCE_LANDSCAPE_SCHEMA_VERSION = "EVIDENCE_LANDSCAPE_SCHEMA_V0.2.1"
SOURCE_LANDSCAPE_VERSION = "MULTI_COMPONENT_EVIDENCE_LANDSCAPE_V0.2"

COMPONENT_STATES = ["OBSERVED", "PARTIAL", "CONFLICTING", "MISSING", "NOT_QUERIED"]
MISSINGNESS_STATES = [
    "OBSERVED",
    "NOT_FOUND",
    "NOT_QUERIED",
    "NOT_APPLICABLE",
    "UNKNOWN",
]
RELATIONSHIP_LEVEL_COMPATIBILITY = {
    "SAME_SOURCE": "DEPENDENT",
    "SHARED_DATASET": "DEPENDENT",
    "PARTIAL": "PARTIALLY_DEPENDENT",
    "UNKNOWN": "UNKNOWN",
    "INDEPENDENT": "INDEPENDENT",
    "NOT_APPLICABLE": "NOT_APPLICABLE",
}
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
    "docs/governance/target_evidence_profile_governance_v0.1.md": "1b8ab03bb758fd70d8a4bffb27ba1c7f97f83a52c20e75a0c18d9b0bd0941bbd",
    "docs/governance/multi_component_evidence_landscape_specification_v0.2.md": "6d878dc12eaf7b9172f0880345cfc12bd67a209d45af68dbe543e05f192c8e73",
    "docs/governance/evidence_landscape_component_composition_policy_v0.1.md": "1ba8b4bf678906d5f15a50284742d2b81045d7530eb59d2fe28a81ad45eab2b7",
    "docs/governance/evidence_landscape_versioning_policy_v0.1.md": "fd71350c8c00f5abc935a772244232fbcb614dc898c0e44e2763f38121c62677",
    "docs/governance/evidence_landscape_validation_requirements_v0.1.md": "fccbcef5a1b61f8d45184c1f6177ce892a828887ad754c268eab9f1674c1c7ca",
    "analysis/33B1_1_patch_landscape_schema_contract.py": "bbe05e9de94fea125bdef6342dc959740029cfe10df16fa95c480fb147ac1e16",
    "schemas/evidence_landscape_schema_v0.2.1.json": "fc3d512c56ec44f03a351108bde640cd5d153d0df62ada66638482cfbd04b32a",
    "outputs/evidence_landscape_schema_v0.2.1/schema_manifest.json": "50a7403c75a8a9a78c6eb7f9699e484b17e51f4a724ee2c45c896e35e18ca552",
    "outputs/evidence_landscape_schema_v0.2.1/validation_report.md": "b39cd9c85ea619e74a48ba06be9e3d15e157d8715f39585ac7671640a446cfac",
    "analysis/33B2_generate_evidence_landscape.py": "46d53c1fa4883de87a41b63556209ec5dc104ea3fdb32eabc6be38f359084800",
    "outputs/evidence_landscape_v0.2/landscape_manifest.json": "2c3853becd3895b0aaffb12be95205d910d1507dc1f2f8f36f7f150f651dba29",
    "outputs/evidence_landscape_v0.2/landscape_index.csv": "fbd7a3b50e70c41aa2ddbf0361390fde23d12bc320a881a4da168ad1d145d6c8",
    "outputs/evidence_landscape_v0.2/partition_manifest.csv": "2ccc38a384fe816d50b2c5d8f4c528a49727189434fe4be41e70355ff146cf8d",
    "outputs/evidence_landscape_v0.2/validation_report.md": "d5933862fe468ef4561188716abaee2de1cda16e06bcb1d39c1793f66cc29a8a",
    "outputs/evidence_landscape_v0.2/session_info.txt": "bb928646c3c7c3aba85f9faa127b4eb93b50455fa24165aa6b1a048bf1c658de",
}

NEW_DOCUMENTS = {
    "docs/governance/evidence_aggregation_representation_specification_v0.1.md",
    "docs/governance/evidence_summary_component_policy_v0.1.md",
    "docs/governance/evidence_summary_dependency_policy_v0.1.md",
    "docs/governance/evidence_summary_validation_requirements_v0.1.md",
}
ALLOWED_WORKTREE_PATHS = {
    *{
        path
        for path in FROZEN_INPUT_SHA256
        if path.startswith("docs/governance/")
        and "evidence_landscape" in path
    },
    *NEW_DOCUMENTS,
    "analysis/34A_define_evidence_summary_schema.py",
    "schemas/evidence_summary_schema_v0.1.json",
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


def closed_object(
    properties: dict[str, Any], required: list[str], **extra: Any
) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": required,
        **extra,
    }


def build_schema() -> dict[str, Any]:
    sha256_schema = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
    nonempty = {"type": "string", "minLength": 1}
    component_state = {"type": "string", "enum": COMPONENT_STATES}
    missingness_state = {"type": "string", "enum": MISSINGNESS_STATES}

    dependency_relationship = closed_object(
        {
            "relationship_type": {
                "type": "string",
                "enum": list(RELATIONSHIP_LEVEL_COMPATIBILITY),
            },
            "dependency_level": {
                "type": "string",
                "enum": sorted(set(RELATIONSHIP_LEVEL_COMPATIBILITY.values())),
            },
        },
        ["relationship_type", "dependency_level"],
        allOf=[
            {
                "if": {
                    "properties": {"relationship_type": {"const": relationship_type}},
                    "required": ["relationship_type"],
                },
                "then": {
                    "properties": {"dependency_level": {"const": dependency_level}}
                },
            }
            for relationship_type, dependency_level in RELATIONSHIP_LEVEL_COMPATIBILITY.items()
        ],
    )

    artifact_reference = closed_object(
        {
            "artifact_id": {
                "type": "string",
                "minLength": 1,
                "description": "Source-native artifact identifier preserved without rewriting.",
            },
            "artifact_namespace": {
                "type": "string",
                "pattern": "^[A-Z][A-Z0-9]*$",
                "description": "Source-native namespace stored separately from artifact_id.",
            },
            "artifact_sha256": deepcopy(sha256_schema),
            "immutable_storage_reference": {"type": "string", "minLength": 1},
        },
        ["artifact_id", "artifact_namespace", "artifact_sha256"],
    )

    feature_missingness = closed_object(
        {
            "feature_id": {"type": "string", "minLength": 1},
            "missingness_status": deepcopy(missingness_state),
            "source_component_record_id": {"type": "string", "minLength": 1},
            "source_feature_value_sha256": deepcopy(sha256_schema),
        },
        ["feature_id", "missingness_status", "source_component_record_id"],
    )

    dependency_summary = closed_object(
        {
            "component_id": {"type": "string", "pattern": "^COMP_[A-Z0-9_]+$"},
            "component_version": {
                "type": "string",
                "pattern": "^COMP_[A-Z0-9_]+_V[0-9]+\\.[0-9]+$",
            },
            "feature_id": {"type": "string", "minLength": 1},
            "evidence_record_id": {"type": "string", "minLength": 1},
            "source_id": {"type": "string", "minLength": 1},
            "dependency_id": {"type": "string", "minLength": 1},
            "dependency_relationships": {
                "type": "array",
                "minItems": 1,
                "items": {"$ref": "#/$defs/dependencyRelationship"},
            },
            "artifact_reference": {"$ref": "#/$defs/artifactReference"},
        },
        [
            "component_id",
            "component_version",
            "feature_id",
            "evidence_record_id",
            "source_id",
            "dependency_id",
            "dependency_relationships",
            "artifact_reference",
        ],
    )

    component_summary = closed_object(
        {
            "component_id": {"type": "string", "pattern": "^COMP_[A-Z0-9_]+$"},
            "component_version": {
                "type": "string",
                "pattern": "^COMP_[A-Z0-9_]+_V[0-9]+\\.[0-9]+$",
            },
            "component_state": deepcopy(component_state),
            "source_component_record_id": {"type": "string", "minLength": 1},
            "source_component_content_sha256": deepcopy(sha256_schema),
            "feature_missingness": {
                "type": "array",
                "minItems": 1,
                "items": {"$ref": "#/$defs/featureMissingness"},
            },
            "dependency_summaries": {
                "type": "array",
                "items": {"$ref": "#/$defs/dependencySummary"},
            },
            "limitation_identifiers": {
                "type": "array",
                "uniqueItems": True,
                "items": {"type": "string", "pattern": "^LIM_[A-Z0-9_]+$"},
            },
        },
        [
            "component_id",
            "component_version",
            "component_state",
            "source_component_record_id",
            "source_component_content_sha256",
            "feature_missingness",
            "dependency_summaries",
            "limitation_identifiers",
        ],
    )

    source_landscape_identity = closed_object(
        {
            "landscape_id": {"type": "string", "minLength": 1},
            "landscape_schema_version": {
                "type": "string",
                "const": SOURCE_LANDSCAPE_SCHEMA_VERSION,
            },
            "landscape_version": {
                "type": "string",
                "const": SOURCE_LANDSCAPE_VERSION,
            },
            "source_profile_id": {"type": "string", "minLength": 1},
            "source_evidence_snapshot_version": {"type": "string", "minLength": 1},
            "source_landscape_generator_version": {"type": "string", "minLength": 1},
            "landscape_content_sha256": deepcopy(sha256_schema),
        },
        [
            "landscape_id",
            "landscape_schema_version",
            "landscape_version",
            "source_profile_id",
            "source_evidence_snapshot_version",
            "source_landscape_generator_version",
            "landscape_content_sha256",
        ],
    )

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": SCHEMA_ID,
        "title": "Evidence Aggregation Representation schema v0.1",
        "description": (
            "Closed structural contract for a non-evaluative Evidence Summary "
            "projected from one governed Multi-component Evidence Landscape."
        ),
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "EnsemblID": {"type": "string", "pattern": "^ENSG[0-9]+\\.[0-9]+$"},
            "universe_ordinal": {"type": "integer", "minimum": 1},
            "evidence_summary_id": {
                "type": "string",
                "pattern": "^SUM_[A-F0-9]{32}$",
            },
            "evidence_summary_schema_version": {
                "type": "string",
                "const": SCHEMA_VERSION,
            },
            "evidence_summary_version": {
                "type": "string",
                "const": SUMMARY_VERSION,
            },
            "summary_generator_version": {"type": "string", "minLength": 1},
            "source_landscape_identity": {"$ref": "#/$defs/sourceLandscapeIdentity"},
            "component_summaries": {
                "type": "array",
                "minItems": 1,
                "items": {"$ref": "#/$defs/componentSummary"},
            },
            "limitation_identifiers": {
                "type": "array",
                "uniqueItems": True,
                "items": {"type": "string", "pattern": "^LIM_[A-Z0-9_]+$"},
            },
        },
        "required": [
            "EnsemblID",
            "universe_ordinal",
            "evidence_summary_id",
            "evidence_summary_schema_version",
            "evidence_summary_version",
            "summary_generator_version",
            "source_landscape_identity",
            "component_summaries",
            "limitation_identifiers",
        ],
        "$defs": {
            "artifactReference": artifact_reference,
            "componentSummary": component_summary,
            "dependencyRelationship": dependency_relationship,
            "dependencySummary": dependency_summary,
            "featureMissingness": feature_missingness,
            "sourceLandscapeIdentity": source_landscape_identity,
        },
        "$comment": (
            "The contract prohibits evaluation, scoring, ranking, prioritization, "
            "confidence, overall state, recommendation, target quality, and evidence strength."
        ),
    }


def resolve_json_pointer(root_schema: dict[str, Any], reference: str) -> dict[str, Any]:
    if not reference.startswith("#/"):
        fail(f"Unsupported non-local schema reference: {reference}")
    node: Any = root_schema
    for part in reference[2:].split("/"):
        node = node[part.replace("~1", "/").replace("~0", "~")]
    if not isinstance(node, dict):
        fail(f"Schema reference does not resolve to an object: {reference}")
    return node


def type_matches(instance: Any, expected: str) -> bool:
    return {
        "object": isinstance(instance, dict),
        "array": isinstance(instance, list),
        "string": isinstance(instance, str),
        "integer": isinstance(instance, int) and not isinstance(instance, bool),
        "number": isinstance(instance, (int, float)) and not isinstance(instance, bool),
        "boolean": isinstance(instance, bool),
        "null": instance is None,
    }.get(expected, False)


def validate_instance(
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
        validate_instance(instance, resolve_json_pointer(root_schema, schema["$ref"]), root_schema, path)
        return
    if "const" in schema and instance != schema["const"]:
        fail(f"Schema const mismatch at {path}")
    if "enum" in schema and instance not in schema["enum"]:
        fail(f"Schema enum mismatch at {path}: {instance!r}")
    if "type" in schema and not type_matches(instance, schema["type"]):
        fail(f"Schema type mismatch at {path}: expected {schema['type']}")

    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            fail(f"Schema minLength mismatch at {path}")
        if "pattern" in schema and re.fullmatch(schema["pattern"], instance) is None:
            fail(f"Schema pattern mismatch at {path}: {instance!r}")
    if isinstance(instance, int) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            fail(f"Schema minimum mismatch at {path}")

    if isinstance(instance, dict):
        properties = schema.get("properties", {})
        missing = [key for key in schema.get("required", []) if key not in instance]
        if missing:
            fail(f"Schema required fields missing at {path}: {missing}")
        if schema.get("additionalProperties") is False:
            extras = set(instance) - set(properties)
            if extras:
                fail(f"Schema additional fields at {path}: {sorted(extras)}")
        for key, child_schema in properties.items():
            if key in instance:
                validate_instance(instance[key], child_schema, root_schema, f"{path}.{key}")

    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            fail(f"Schema minItems mismatch at {path}")
        if schema.get("uniqueItems"):
            encoded = [canonical_json(item) for item in instance]
            if len(encoded) != len(set(encoded)):
                fail(f"Schema uniqueItems mismatch at {path}")
        if "items" in schema:
            for index, child in enumerate(instance):
                validate_instance(child, schema["items"], root_schema, f"{path}[{index}]")

    for condition in schema.get("allOf", []):
        validate_instance(instance, condition, root_schema, path)
    if "if" in schema:
        condition_passes = True
        try:
            validate_instance(instance, schema["if"], root_schema, path)
        except RuntimeError:
            condition_passes = False
        branch = schema.get("then") if condition_passes else schema.get("else")
        if branch is not None:
            validate_instance(instance, branch, root_schema, path)


def assert_closed_objects(value: Any, path: str = "$", count: list[int] | None = None) -> int:
    counter = count if count is not None else [0]
    if isinstance(value, dict):
        if value.get("type") == "object":
            counter[0] += 1
            if value.get("additionalProperties") is not False:
                fail(f"Open object schema at {path}")
        for key, child in value.items():
            assert_closed_objects(child, f"{path}.{key}", counter)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            assert_closed_objects(child, f"{path}[{index}]", counter)
    return counter[0]


def assert_no_prohibited_schema_fields(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        properties = value.get("properties")
        if isinstance(properties, dict):
            forbidden = PROHIBITED_FIELDS.intersection(properties)
            if forbidden:
                fail(f"Prohibited schema field(s) at {path}: {sorted(forbidden)}")
        for key, child in value.items():
            assert_no_prohibited_schema_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            assert_no_prohibited_schema_fields(child, f"{path}[{index}]")


def validate_artifact_namespace(instance: dict[str, Any]) -> None:
    for component in instance["component_summaries"]:
        for dependency in component["dependency_summaries"]:
            artifact = dependency["artifact_reference"]
            expected_namespace = artifact["artifact_id"].split("_", 1)[0]
            if artifact["artifact_namespace"] != expected_namespace:
                fail("Artifact namespace does not match preserved source-native identifier")


def valid_fixture() -> dict[str, Any]:
    digest = "a" * 64
    component_id = "COMP_DISEASE_ASSOCIATION"
    component_version = "COMP_DISEASE_ASSOCIATION_V0.1"
    return {
        "EnsemblID": "ENSG00000108576.9",
        "universe_ordinal": 2,
        "evidence_summary_id": "SUM_0123456789ABCDEF0123456789ABCDEF",
        "evidence_summary_schema_version": SCHEMA_VERSION,
        "evidence_summary_version": SUMMARY_VERSION,
        "summary_generator_version": "EVIDENCE_SUMMARY_MATERIALIZER_V0.1",
        "source_landscape_identity": {
            "landscape_id": "LND_EXAMPLE",
            "landscape_schema_version": SOURCE_LANDSCAPE_SCHEMA_VERSION,
            "landscape_version": SOURCE_LANDSCAPE_VERSION,
            "source_profile_id": "PROFILE_EXAMPLE",
            "source_evidence_snapshot_version": "EVIDENCE_SNAPSHOT_EXAMPLE",
            "source_landscape_generator_version": "MULTI_COMPONENT_EVIDENCE_LANDSCAPE_GENERATOR_V0.1",
            "landscape_content_sha256": digest,
        },
        "component_summaries": [
            {
                "component_id": component_id,
                "component_version": component_version,
                "component_state": "OBSERVED",
                "source_component_record_id": "CMPREC_EXAMPLE",
                "source_component_content_sha256": digest,
                "feature_missingness": [
                    {
                        "feature_id": "FEAT_EXAMPLE",
                        "missingness_status": "OBSERVED",
                        "source_component_record_id": "CMPREC_EXAMPLE",
                        "source_feature_value_sha256": digest,
                    }
                ],
                "dependency_summaries": [
                    {
                        "component_id": component_id,
                        "component_version": component_version,
                        "feature_id": "FEAT_EXAMPLE",
                        "evidence_record_id": "EVID_EXAMPLE",
                        "source_id": "SRC_OPEN_TARGETS_PLATFORM",
                        "dependency_id": "DEP_EXAMPLE",
                        "dependency_relationships": [
                            {
                                "relationship_type": "SAME_SOURCE",
                                "dependency_level": "DEPENDENT",
                            },
                            {
                                "relationship_type": "SHARED_DATASET",
                                "dependency_level": "DEPENDENT",
                            },
                        ],
                        "artifact_reference": {
                            "artifact_id": "INV_EXAMPLE",
                            "artifact_namespace": "INV",
                            "artifact_sha256": digest,
                        },
                    }
                ],
                "limitation_identifiers": [],
            }
        ],
        "limitation_identifiers": ["LIM_PROFILE_LIFECYCLE_UNASSIGNED"],
    }


def expect_rejected(instance: dict[str, Any], schema: dict[str, Any], label: str) -> None:
    try:
        validate_instance(instance, schema, schema)
    except RuntimeError:
        return
    fail(f"Invalid boundary fixture was accepted: {label}")


def validate_fixtures(schema: dict[str, Any]) -> int:
    fixture = valid_fixture()
    validate_instance(fixture, schema, schema)
    validate_artifact_namespace(fixture)
    fixture_bytes = canonical_json(fixture).encode("utf-8")
    if b'"SAME_SOURCE"' not in fixture_bytes or b'"SHARED_DATASET"' not in fixture_bytes:
        fail("Multi-relationship fixture lost an ordered dependency relationship")

    tests = 1
    for state in COMPONENT_STATES:
        candidate = deepcopy(fixture)
        candidate["component_summaries"][0]["component_state"] = state
        validate_instance(candidate, schema, schema)
        tests += 1
    for missingness in MISSINGNESS_STATES:
        candidate = deepcopy(fixture)
        candidate["component_summaries"][0]["feature_missingness"][0][
            "missingness_status"
        ] = missingness
        validate_instance(candidate, schema, schema)
        tests += 1

    for field in sorted(PROHIBITED_FIELDS):
        candidate = deepcopy(fixture)
        candidate[field] = "PROHIBITED"
        expect_rejected(candidate, schema, f"root prohibited field {field}")
        candidate = deepcopy(fixture)
        candidate["component_summaries"][0][field] = "PROHIBITED"
        expect_rejected(candidate, schema, f"nested prohibited field {field}")
        tests += 2

    candidate = deepcopy(fixture)
    candidate["component_summaries"][0]["component_state"] = "STRONG"
    expect_rejected(candidate, schema, "uncontrolled component state")
    tests += 1
    candidate = deepcopy(fixture)
    candidate["component_summaries"][0]["feature_missingness"][0][
        "missingness_status"
    ] = "NEGATIVE"
    expect_rejected(candidate, schema, "uncontrolled missingness")
    tests += 1
    candidate = deepcopy(fixture)
    candidate["component_summaries"][0]["dependency_summaries"][0][
        "dependency_relationships"
    ][0]["dependency_level"] = "INDEPENDENT"
    expect_rejected(candidate, schema, "incompatible dependency type and level")
    tests += 1
    candidate = deepcopy(fixture)
    candidate["component_summaries"][0]["dependency_summaries"][0][
        "artifact_reference"
    ]["artifact_namespace"] = "ART"
    try:
        validate_artifact_namespace(candidate)
    except RuntimeError:
        tests += 1
    else:
        fail("Artifact identifier rewriting boundary fixture was accepted")
    return tests


def validate_markdown_links() -> int:
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    checked = 0
    for relative_path in sorted(NEW_DOCUMENTS):
        path = ROOT / relative_path
        if not path.is_file():
            fail(f"Task #034A governance document missing: {relative_path}")
        text = path.read_text(encoding="utf-8")
        for target in link_pattern.findall(text):
            if target.startswith(("http://", "https://", "#")):
                continue
            clean_target = target.split("#", 1)[0]
            resolved = (path.parent / clean_target).resolve()
            if not resolved.exists():
                fail(f"Broken Markdown link in {relative_path}: {target}")
            checked += 1
    return checked


def validate_document_terminology() -> None:
    combined = "\n".join(
        (ROOT / relative_path).read_text(encoding="utf-8")
        for relative_path in sorted(NEW_DOCUMENTS)
    )
    required_tokens = {
        SCHEMA_VERSION,
        SUMMARY_VERSION,
        SOURCE_LANDSCAPE_SCHEMA_VERSION,
        SOURCE_LANDSCAPE_VERSION,
        "component_id",
        "component_version",
        "component_state",
        "feature missingness",
        "dependency_relationships",
        "artifact_namespace",
        "limitation_id",
    }
    missing = sorted(token for token in required_tokens if token not in combined)
    if missing:
        fail(f"Governance terminology is incomplete: {missing}")


def main() -> None:
    validate_working_tree_scope()
    frozen_before = validate_frozen_inputs()
    validate_document_terminology()

    schema_first = build_schema()
    schema_second = build_schema()
    bytes_first = pretty_json_bytes(schema_first)
    bytes_second = pretty_json_bytes(schema_second)
    if bytes_first != bytes_second:
        fail("Schema regeneration is not byte-identical")
    if schema_first.get("$id") != SCHEMA_ID:
        fail("Schema identity mismatch")
    closed_objects = assert_closed_objects(schema_first)
    assert_no_prohibited_schema_fields(schema_first)
    fixture_tests = validate_fixtures(schema_first)

    SCHEMA_PATH.parent.mkdir(parents=True, exist_ok=True)
    if SCHEMA_PATH.exists() and SCHEMA_PATH.read_bytes() != bytes_first:
        fail("Existing Task #034A schema differs from deterministic regeneration")
    SCHEMA_PATH.write_bytes(bytes_first)
    if SCHEMA_PATH.read_bytes() != bytes_second:
        fail("Written schema does not match independent regeneration")
    markdown_links = validate_markdown_links()

    frozen_after = validate_frozen_inputs()
    if frozen_before != frozen_after:
        fail("A frozen previous artifact changed during Task #034A")
    validate_working_tree_scope()

    print("TASK_034A_VALIDATION=PASS")
    print(f"schema_version={SCHEMA_VERSION}")
    print(f"summary_version={SUMMARY_VERSION}")
    print(f"schema_sha256={sha256_bytes(bytes_first)}")
    print(f"schema_size_bytes={len(bytes_first)}")
    print(f"closed_object_schemas={closed_objects}")
    print(f"boundary_fixture_tests={fixture_tests}")
    print(f"resolved_markdown_links={markdown_links}")
    print("frozen_previous_artifacts=UNCHANGED")
    print("summary_payloads_generated=0")
    print("network_access=PROHIBITED_NOT_USED")
    print("runtime_ai_decisions=PROHIBITED_NONE_USED")


if __name__ == "__main__":
    main()
