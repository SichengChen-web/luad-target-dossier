#!/usr/bin/env python3
"""Create the forward-only Evidence Landscape schema v0.2.1 patch.

The patch is limited to lossless dependency-relationship cardinality and
source-native artifact identifier namespaces. It creates no landscape records,
profiles, evidence, evaluation fields, or runtime scientific decisions.
"""

from __future__ import annotations

import hashlib
import json
import platform
import re
import subprocess
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
BASE_SCHEMA_PATH = ROOT / "schemas/evidence_landscape_schema_v0.2.json"
SCHEMA_PATH = ROOT / "schemas/evidence_landscape_schema_v0.2.1.json"
SOURCE_PROFILE_PATH = ROOT / "outputs/evidence_profile_integration_v0.1/profile_records.jsonl"
OUTPUT_DIR = ROOT / "outputs/evidence_landscape_schema_v0.2.1"
MANIFEST_PATH = OUTPUT_DIR / "schema_manifest.json"
REPORT_PATH = OUTPUT_DIR / "validation_report.md"
SESSION_PATH = OUTPUT_DIR / "session_info.txt"

TASK_ID = "TASK_033B_1_1"
BASE_SCHEMA_VERSION = "EVIDENCE_LANDSCAPE_SCHEMA_V0.2"
SCHEMA_VERSION = "EVIDENCE_LANDSCAPE_SCHEMA_V0.2.1"
LANDSCAPE_VERSION = "MULTI_COMPONENT_EVIDENCE_LANDSCAPE_V0.2"
GENERATOR_VERSION = "LANDSCAPE_SCHEMA_COMPATIBILITY_PATCH_GENERATOR_V0.2.1"
BASE_SCHEMA_ID = "urn:luad-target-dossier:evidence-landscape-schema:v0.2"
SCHEMA_ID = "urn:luad-target-dossier:evidence-landscape-schema:v0.2.1"

PROHIBITED_FIELDS = {
    "score",
    "ranking",
    "priority",
    "confidence",
    "overall_state",
    "recommendation",
    "interpretation",
}
RELATIONSHIP_LEVEL_COMPATIBILITY = {
    "SAME_SOURCE": "DEPENDENT",
    "SHARED_DATASET": "DEPENDENT",
    "PARTIAL": "PARTIALLY_DEPENDENT",
    "UNKNOWN": "UNKNOWN",
    "INDEPENDENT": "INDEPENDENT",
    "NOT_APPLICABLE": "NOT_APPLICABLE",
}

FROZEN_INPUT_SHA256 = {
    "analysis/33B1_define_landscape_schema_contract.py": "089723f2a4d1c9e85d151cedbcda1f2e68953d04f1c98325680c9d75db3c3a42",
    "schemas/evidence_landscape_schema_v0.2.json": "a52109fb90fda2493d99f20f51dacbf987a394678c90ee9e5d6c58a7afbc62ba",
    "outputs/evidence_landscape_schema_v0.2/schema_manifest.json": "7cd1c5b15aaa745ff4602ed54171ca39c4d72f54407476661103367373f6b6a8",
    "outputs/evidence_landscape_schema_v0.2/schema_validation_report.md": "057c231591615bfc22a9134c6c41afb1d66294079e6fd908f369406cdaff05cf",
    "outputs/evidence_landscape_schema_v0.2/session_info.txt": "67bab5de22e759687cc4eaa9af55bfc2ab0a450b5da403ddd4e9f9ff284a0f63",
    "analysis/33B2_generate_evidence_landscape.py": "31c49ef0170d13734569e9601562712c83fd998c9ccd08c3e5a92e96fca42fd7",
    "docs/governance/multi_component_evidence_landscape_specification_v0.2.md": "6d878dc12eaf7b9172f0880345cfc12bd67a209d45af68dbe543e05f192c8e73",
    "docs/governance/evidence_landscape_component_composition_policy_v0.1.md": "1ba8b4bf678906d5f15a50284742d2b81045d7530eb59d2fe28a81ad45eab2b7",
    "docs/governance/evidence_landscape_versioning_policy_v0.1.md": "fd71350c8c00f5abc935a772244232fbcb614dc898c0e44e2763f38121c62677",
    "docs/governance/evidence_landscape_validation_requirements_v0.1.md": "fccbcef5a1b61f8d45184c1f6177ce892a828887ad754c268eab9f1674c1c7ca",
    "outputs/evidence_profile_integration_v0.1/profile_manifest.json": "63492499977f7adb086e4ace9a491a72fa617a1fe054d544701826fb9657455d",
    "outputs/evidence_profile_integration_v0.1/profile_index.csv": "376e6d3440dba3ae392410cd2f836a9a700fe66248bf29257794b55015821a28",
    "outputs/evidence_profile_integration_v0.1/validation_report.md": "191ba0d01799d4e3e96bff3ebabc6c75997cbbdeee36217b45f0c45181302699",
}
EXPECTED_SOURCE_PROFILE_SIZE = 2_151_412_821
EXPECTED_SOURCE_PROFILE_SHA256 = "8fab364cbe1318f49dd8b29501dd1439d1ae2a38161e090942801399bec7e156"

TASK033A_PATHS = {
    path
    for path in FROZEN_INPUT_SHA256
    if path.startswith("docs/governance/") and "evidence_landscape" in path
}
ALLOWED_WORKTREE_PATHS = {
    "analysis/33B2_generate_evidence_landscape.py",
    "analysis/33B1_1_patch_landscape_schema_contract.py",
    "schemas/evidence_landscape_schema_v0.2.1.json",
    *TASK033A_PATHS,
    *(f"outputs/evidence_landscape_schema_v0.2.1/{name}" for name in (
        "schema_manifest.json",
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


def pretty_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode(
        "utf-8"
    )


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


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
    allowed = {MANIFEST_PATH, REPORT_PATH, SESSION_PATH}
    if OUTPUT_DIR.exists():
        unexpected = sorted(
            path.relative_to(ROOT).as_posix()
            for path in OUTPUT_DIR.rglob("*")
            if path.is_file() and path not in allowed
        )
        if unexpected:
            fail("Unexpected schema-patch output or payload files: " + ", ".join(unexpected))


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
    if not SOURCE_PROFILE_PATH.is_file() or SOURCE_PROFILE_PATH.stat().st_size != EXPECTED_SOURCE_PROFILE_SIZE:
        fail("Frozen Task #032C profile payload size changed")
    profile_manifest = json.loads(
        (ROOT / "outputs/evidence_profile_integration_v0.1/profile_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    profile_artifact = profile_manifest.get("output_artifacts", {}).get(
        "profile_records.jsonl", {}
    )
    if (
        profile_artifact.get("size_bytes") != EXPECTED_SOURCE_PROFILE_SIZE
        or profile_artifact.get("sha256") != EXPECTED_SOURCE_PROFILE_SHA256
        or profile_artifact.get("row_count") != 29606
    ):
        fail("Frozen Task #032C profile payload manifest changed")
    return observed


def relationship_object_schema(
    relationship_type_schema: dict[str, Any], dependency_level_schema: dict[str, Any]
) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "relationship_type": deepcopy(relationship_type_schema),
            "dependency_level": deepcopy(dependency_level_schema),
        },
        "required": ["relationship_type", "dependency_level"],
        "allOf": [
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
    }


def patch_artifact_reference(definition: dict[str, Any]) -> None:
    properties = definition["properties"]
    properties["artifact_id"] = {
        "type": "string",
        "minLength": 1,
        "description": "Source-native artifact identifier preserved byte-for-byte.",
    }
    properties["artifact_namespace"] = {
        "type": "string",
        "minLength": 1,
        "description": "Source-native identifier namespace; it does not replace artifact_id.",
    }
    required = definition["required"]
    if "artifact_namespace" not in required:
        required.insert(required.index("artifact_id") + 1, "artifact_namespace")


def patch_source_component_reference(definition: dict[str, Any]) -> None:
    properties = definition["properties"]
    for field in ("source_record_artifact_id", "container_artifact_id"):
        properties[field] = {
            "type": "string",
            "minLength": 1,
            "description": "Source-native artifact identifier preserved byte-for-byte.",
        }
        namespace_field = field.removesuffix("_id") + "_namespace"
        properties[namespace_field] = {
            "type": "string",
            "minLength": 1,
            "description": "Source-native namespace for the paired artifact identifier.",
        }
        required = definition["required"]
        if namespace_field not in required:
            required.insert(required.index(field) + 1, namespace_field)


def build_schema() -> dict[str, Any]:
    base = json.loads(BASE_SCHEMA_PATH.read_text(encoding="utf-8"))
    if base.get("$id") != BASE_SCHEMA_ID:
        fail("Unexpected frozen v0.2 schema identifier")
    if (
        base.get("properties", {})
        .get("landscape_schema_version", {})
        .get("const")
        != BASE_SCHEMA_VERSION
    ):
        fail("Unexpected frozen v0.2 schema-version constant")

    patched = deepcopy(base)
    patched["$id"] = SCHEMA_ID
    patched["title"] = "Multi-component Evidence Landscape schema v0.2.1"
    patched["$comment"] = (
        "Forward-only compatibility patch for ordered dependency relationships and "
        "source-native artifact namespaces. No landscape payload is authorized or generated."
    )
    patched["properties"]["landscape_schema_version"]["const"] = SCHEMA_VERSION
    patched["x-forward-compatible-from"] = BASE_SCHEMA_VERSION
    patched["x-compatibility-patch-scope"] = [
        "DEPENDENCY_RELATIONSHIP_CARDINALITY",
        "ARTIFACT_IDENTIFIER_NAMESPACE",
    ]

    definitions = patched["$defs"]
    patch_artifact_reference(definitions["artifact_reference"])
    patch_source_component_reference(definitions["source_component_reference"])

    dependency = definitions["dependency_reference"]
    relationship_type_schema = dependency["properties"].pop("relationship_type")
    dependency_level_schema = dependency["properties"].pop("dependency_level")
    dependency.pop("allOf")
    dependency["required"].remove("relationship_type")
    dependency["required"].remove("dependency_level")
    dependency["properties"]["dependency_relationships"] = {
        "type": "array",
        "items": {"$ref": "#/$defs/dependency_relationship"},
        "minItems": 1,
        "uniqueItems": True,
        "description": (
            "Lossless ordered relationship classifications for one evidence relationship."
        ),
    }
    insert_at = dependency["required"].index("dependency_reference_status") + 1
    dependency["required"].insert(insert_at, "dependency_relationships")
    definitions["dependency_relationship"] = relationship_object_schema(
        relationship_type_schema, dependency_level_schema
    )
    return patched


def validate_patch_scope(base: dict[str, Any], patched: dict[str, Any]) -> None:
    if patched["properties"]["landscape_version"] != base["properties"]["landscape_version"]:
        fail("Landscape semantic version changed outside patch scope")
    if patched["x-landscape-identity-tuple"] != base["x-landscape-identity-tuple"]:
        fail("Landscape identity tuple changed outside patch scope")
    if patched["x-provenance-relationship-key"] != base["x-provenance-relationship-key"]:
        fail("Provenance relationship key changed outside patch scope")
    if patched["x-source-profile-identity-tuple"] != base["x-source-profile-identity-tuple"]:
        fail("Source-profile identity tuple changed outside patch scope")

    allowed_changed_definitions = {
        "artifact_reference",
        "source_component_reference",
        "dependency_reference",
    }
    for name, base_definition in base["$defs"].items():
        if name not in allowed_changed_definitions and patched["$defs"].get(name) != base_definition:
            fail(f"Schema definition changed outside compatibility scope: {name}")
    if set(patched["$defs"]) - set(base["$defs"]) != {"dependency_relationship"}:
        fail("Unexpected new schema definitions")

    base_properties = deepcopy(base["properties"])
    patched_properties = deepcopy(patched["properties"])
    base_properties.pop("landscape_schema_version")
    patched_properties.pop("landscape_schema_version")
    if patched_properties != base_properties:
        fail("Top-level landscape fields changed outside schema-version axis")


def resolve_json_pointer(root_schema: dict[str, Any], reference: str) -> dict[str, Any]:
    if not reference.startswith("#/"):
        fail(f"Unsupported non-local schema reference: {reference}")
    node: Any = root_schema
    for part in reference[2:].split("/"):
        node = node[part.replace("~1", "/").replace("~0", "~")]
    if not isinstance(node, dict):
        fail(f"Schema reference is not an object: {reference}")
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
        validate_schema_instance(
            instance, resolve_json_pointer(root_schema, schema["$ref"]), root_schema, path
        )
        return
    if "const" in schema and instance != schema["const"]:
        fail(f"Schema const mismatch at {path}")
    if "enum" in schema and instance not in schema["enum"]:
        fail(f"Schema enum mismatch at {path}: {instance!r}")
    expected_type = schema.get("type")
    if expected_type and not schema_type_matches(instance, expected_type):
        fail(f"Schema type mismatch at {path}: expected {expected_type}")
    if isinstance(instance, str) and len(instance) < schema.get("minLength", 0):
        fail(f"Schema minLength mismatch at {path}")
    if isinstance(instance, str) and schema.get("pattern"):
        if re.search(schema["pattern"], instance) is None:
            fail(f"Schema pattern mismatch at {path}")
    if isinstance(instance, dict):
        missing = [key for key in schema.get("required", []) if key not in instance]
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
            serialized = [canonical_json(item) for item in instance]
            if len(serialized) != len(set(serialized)):
                fail(f"Schema uniqueItems mismatch at {path}")
        prefix_items = schema.get("prefixItems", [])
        for index, child_schema in enumerate(prefix_items):
            if index < len(instance):
                validate_schema_instance(
                    instance[index], child_schema, root_schema, f"{path}[{index}]"
                )
        if "items" in schema:
            for index in range(len(prefix_items), len(instance)):
                validate_schema_instance(
                    instance[index], schema["items"], root_schema, f"{path}[{index}]"
                )
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


def artifact_namespace(artifact_id: str) -> str:
    if not artifact_id or "_" not in artifact_id:
        fail(f"Cannot preserve source-native artifact namespace: {artifact_id!r}")
    return artifact_id.split("_", 1)[0]


def load_task032c_compatibility_examples() -> dict[str, Any]:
    with SOURCE_PROFILE_PATH.open("rb") as handle:
        first_raw = handle.readline()
        second_raw = handle.readline()
    first = json.loads(first_raw)
    second = json.loads(second_raw)
    if first.get("universe_ordinal") != 1 or second.get("universe_ordinal") != 2:
        fail("Task #032C compatibility fixture ordinals changed")
    if second.get("EnsemblID") != "ENSG00000108576.9":
        fail("Task #032C multi-relationship fixture identity changed")

    multi_link: dict[str, Any] | None = None
    single_link: dict[str, Any] | None = None
    for profile in (first, second):
        for component in profile["components"]:
            for feature in component["features"]:
                for link in feature["provenance_links"]:
                    relationships = link.get("dependency_relationship_types")
                    if isinstance(relationships, list) and len(relationships) > 1:
                        multi_link = link
                    if link.get("dependency_id") == "NOT_APPLICABLE":
                        single_link = link
    if multi_link is None or single_link is None:
        fail("Task #032C dependency compatibility fixtures are unavailable")
    if multi_link.get("dependency_relationship_types") != [
        "SAME_SOURCE",
        "SHARED_DATASET",
    ]:
        fail("Task #032C ordered multi-relationship fixture changed")
    if not str(multi_link.get("artifact_id", "")).startswith("INV_"):
        fail("Task #032C source-native INV artifact fixture changed")
    return {
        "first_profile": first,
        "second_profile": second,
        "single_link": single_link,
        "multi_link": multi_link,
    }


def dependency_fixture(link: dict[str, Any]) -> dict[str, Any]:
    relationship_types = link.get("dependency_relationship_types")
    if not isinstance(relationship_types, list):
        relationship_types = [
            "NOT_APPLICABLE" if link.get("dependency_id") == "NOT_APPLICABLE" else "UNKNOWN"
        ]
    dependency_level = str(link.get("dependency_level") or "NOT_APPLICABLE")
    return {
        "dependency_id": str(link["dependency_id"]),
        "dependency_reference_status": (
            "CONTROLLED_SENTINEL"
            if link["dependency_id"] == "NOT_APPLICABLE"
            else "LINKED_GOVERNED_DEPENDENCY"
        ),
        "dependency_relationships": [
            {
                "relationship_type": relationship_type,
                "dependency_level": dependency_level,
            }
            for relationship_type in relationship_types
        ],
        "dependency_model_version": "COMPONENT_DEPENDENCY_MODEL_V0.1",
        "governing_artifact_reference": {
            "artifact_id": str(link["artifact_id"]),
            "artifact_namespace": artifact_namespace(str(link["artifact_id"])),
            "artifact_sha256": str(link.get("artifact_sha256") or "0" * 64),
        },
        "review_status": "COMPATIBILITY_FIXTURE_ONLY",
    }


def validate_task032c_examples(schema: dict[str, Any]) -> dict[str, Any]:
    fixtures = load_task032c_compatibility_examples()
    multi_link = fixtures["multi_link"]
    single_link = fixtures["single_link"]
    multi_dependency = dependency_fixture(multi_link)
    single_dependency = dependency_fixture(single_link)
    validate_schema_instance(
        multi_dependency, schema["$defs"]["dependency_reference"], schema
    )
    validate_schema_instance(
        single_dependency, schema["$defs"]["dependency_reference"], schema
    )

    source_types = multi_link["dependency_relationship_types"]
    represented_types = [
        item["relationship_type"] for item in multi_dependency["dependency_relationships"]
    ]
    if represented_types != source_types:
        fail("Dependency relationship order or cardinality was not preserved")
    if len(represented_types) != len(source_types):
        fail("Dependency relationships were compressed")

    source_artifact_id = str(multi_link["artifact_id"])
    artifact_fixture = {
        "artifact_id": source_artifact_id,
        "artifact_namespace": artifact_namespace(source_artifact_id),
        "artifact_sha256": multi_link["artifact_sha256"],
    }
    validate_schema_instance(artifact_fixture, schema["$defs"]["artifact_reference"], schema)
    if artifact_fixture["artifact_id"] != source_artifact_id:
        fail("Source-native artifact identifier was rewritten")
    if artifact_fixture["artifact_namespace"] != "INV":
        fail("Source-native INV namespace was not preserved")

    art_example = "ART_TASK012_INTEGRATED_TARGET_REGISTRY"
    validate_schema_instance(
        {
            "artifact_id": art_example,
            "artifact_namespace": artifact_namespace(art_example),
            "artifact_sha256": "0" * 64,
        },
        schema["$defs"]["artifact_reference"],
        schema,
    )
    return {
        "fixture_ensembl_id": fixtures["second_profile"]["EnsemblID"],
        "multi_relationship_count": len(source_types),
        "multi_relationship_order": list(source_types),
        "source_native_artifact_id": source_artifact_id,
        "source_native_artifact_namespace": "INV",
        "single_relationship_count": len(single_dependency["dependency_relationships"]),
        "identifier_rewriting": "NONE",
        "provenance_compression": "NONE",
    }


def iter_dicts(value: Any, path: str = "$") -> Iterable[tuple[str, dict[str, Any]]]:
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from iter_dicts(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from iter_dicts(child, f"{path}[{index}]")


def validate_schema_safety(schema: dict[str, Any]) -> dict[str, int]:
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        fail("Schema draft changed")
    if schema.get("$id") != SCHEMA_ID:
        fail("Patched schema identifier mismatch")
    if schema["properties"]["landscape_schema_version"].get("const") != SCHEMA_VERSION:
        fail("Patched schema-version constant mismatch")
    object_count = 0
    for path, node in iter_dicts(schema):
        properties = node.get("properties")
        if isinstance(properties, dict):
            object_count += 1
            forbidden = PROHIBITED_FIELDS.intersection(properties)
            if forbidden:
                fail(f"Prohibited fields declared at {path}: {sorted(forbidden)}")
            if node.get("type") == "object" and node.get("additionalProperties") is not False:
                fail(f"Open object schema at {path}")
    dependency = schema["$defs"]["dependency_reference"]
    if "relationship_type" in dependency["properties"] or "dependency_level" in dependency["properties"]:
        fail("Scalar dependency relationship fields remain in v0.2.1")
    relationship_array = dependency["properties"].get("dependency_relationships", {})
    if (
        relationship_array.get("type") != "array"
        or relationship_array.get("minItems") != 1
        or relationship_array.get("uniqueItems") is not True
    ):
        fail("Lossless ordered dependency relationship array is not enforced")
    artifact = schema["$defs"]["artifact_reference"]
    if "artifact_namespace" not in artifact["required"]:
        fail("Artifact namespace is not mandatory")
    if "pattern" in artifact["properties"]["artifact_id"]:
        fail("Artifact identifier still has a single-prefix restriction")
    return {
        "closed_object_schema_count": object_count,
        "prohibited_field_count": len(PROHIBITED_FIELDS),
        "relationship_type_count": len(RELATIONSHIP_LEVEL_COMPATIBILITY),
    }


def build_manifest(
    schema_bytes: bytes,
    script_hash: str,
    fixture_results: dict[str, Any],
) -> dict[str, Any]:
    schema_hash = sha256_bytes(schema_bytes)
    return {
        "task_id": TASK_ID,
        "patch_id": f"SCHEMA_PATCH_{schema_hash[:24].upper()}",
        "patch_type": "FORWARD_ONLY_COMPATIBILITY_REVISION",
        "base_schema": {
            "version": BASE_SCHEMA_VERSION,
            "relative_path": "schemas/evidence_landscape_schema_v0.2.json",
            "sha256": FROZEN_INPUT_SHA256["schemas/evidence_landscape_schema_v0.2.json"],
            "modification_status": "UNCHANGED",
        },
        "new_schema": {
            "version": SCHEMA_VERSION,
            "relative_path": "schemas/evidence_landscape_schema_v0.2.1.json",
            "sha256": schema_hash,
            "size_bytes": len(schema_bytes),
        },
        "landscape_version": LANDSCAPE_VERSION,
        "generator": {
            "version": GENERATOR_VERSION,
            "relative_path": "analysis/33B1_1_patch_landscape_schema_contract.py",
            "sha256": script_hash,
        },
        "patch_scope": {
            "dependency_relationship_cardinality": (
                "LOSSLESS_ORDERED_ARRAY_ONE_OR_MORE_RELATIONSHIP_OBJECTS"
            ),
            "artifact_identifier": "SOURCE_NATIVE_ID_PLUS_EXPLICIT_NAMESPACE",
            "component_semantics_changed": False,
            "landscape_semantics_changed": False,
            "provenance_compression": "PROHIBITED_NONE_PERFORMED",
            "identifier_rewriting": "PROHIBITED_NONE_PERFORMED",
        },
        "task032c_compatibility_fixtures": fixture_results,
        "frozen_inputs": dict(sorted(FROZEN_INPUT_SHA256.items())),
        "source_profile_payload": {
            "relative_path": "outputs/evidence_profile_integration_v0.1/profile_records.jsonl",
            "size_bytes": EXPECTED_SOURCE_PROFILE_SIZE,
            "sha256": EXPECTED_SOURCE_PROFILE_SHA256,
            "access_scope": "TWO_STRUCTURAL_COMPATIBILITY_RECORDS_READ_ONLY",
        },
        "network_access": "PROHIBITED_NOT_USED",
        "package_installation": "PROHIBITED_NOT_PERFORMED",
        "landscape_payload_generation": "PROHIBITED_NONE_GENERATED",
        "profile_generation": "PROHIBITED_NONE_GENERATED",
        "runtime_ai_decisions": "PROHIBITED_NONE_USED",
        "validation_status": "PASS",
    }


def build_report(
    schema_bytes: bytes,
    fixture_results: dict[str, Any],
    safety_results: dict[str, int],
) -> bytes:
    lines = [
        "# Evidence Landscape schema v0.2.1 compatibility validation",
        "",
        "**Task:** #033B-1.1  ",
        "**Validation status:** PASS  ",
        f"**New schema:** `{SCHEMA_VERSION}`",
        "",
        "## Forward-only patch",
        "",
        f"The frozen `{BASE_SCHEMA_VERSION}` contract remains unchanged. `{SCHEMA_VERSION}` changes only dependency-relationship cardinality and source-native artifact identifier representation. The landscape semantic version remains `{LANDSCAPE_VERSION}`.",
        "",
        "This is semantic backward compatibility with Task #033A governance, not byte-level acceptance of an old serialized landscape. A v0.2.1 landscape must use the new explicit structures.",
        "",
        "## Compatibility changes",
        "",
        "1. A dependency reference now contains the required ordered `dependency_relationships` array. Each entry retains one `relationship_type` and its compatible `dependency_level`. No relationship is selected, collapsed, counted as a substitute, or reordered.",
        "2. Every artifact reference now retains the original `artifact_id` plus an explicit `artifact_namespace`. No prefix is required and no source identifier is rewritten.",
        "3. Source-component artifact identifiers receive matching namespace fields without changing their original identifiers.",
        "",
        "## Frozen Task #032C fixtures",
        "",
        f"- EnsemblID: `{fixture_results['fixture_ensembl_id']}`",
        f"- Ordered dependency relationships: `{fixture_results['multi_relationship_order']}`",
        f"- Relationship count before/after representation: `{fixture_results['multi_relationship_count']}` / `{fixture_results['multi_relationship_count']}`",
        f"- Source-native artifact ID retained: `{fixture_results['source_native_artifact_id']}`",
        f"- Artifact namespace: `{fixture_results['source_native_artifact_namespace']}`",
        "- Single-relationship representation remains an array of one object: PASS",
        "- Provenance compression: NONE",
        "- Identifier rewriting: NONE",
        "",
        "## Validation results",
        "",
        "| Check | Result |",
        "|---|---|",
        "| Task #033A identity, state, missingness, provenance, dependency, and limitation semantics unchanged | PASS |",
        "| Dependency arrays are ordered, non-empty, and unique | PASS |",
        "| Relationship type/level compatibility retained | PASS |",
        "| Multi-relationship Task #032C example represented losslessly | PASS |",
        "| `ART` and `INV` source-native namespaces represented without identifier rewriting | PASS |",
        "| Provenance relationship key unchanged | PASS |",
        "| Component and landscape semantic versions unchanged | PASS |",
        f"| Closed object schemas | PASS ({safety_results['closed_object_schema_count']}) |",
        f"| Prohibited fields absent/rejected | PASS ({safety_results['prohibited_field_count']} names) |",
        "| Two in-memory regenerations byte-identical | PASS |",
        "| Previous frozen artifact hashes unchanged | PASS |",
        "| Landscape/profile payload generation | PROHIBITED; NONE GENERATED |",
        "| Network/API access | PROHIBITED; NOT USED |",
        "| Runtime AI/LLM decisions | PROHIBITED; NONE USED |",
        "",
        "## Artifact identity",
        "",
        f"- Schema SHA256: `{sha256_bytes(schema_bytes)}`",
        f"- Schema size: `{len(schema_bytes)}` bytes",
        f"- Generator version: `{GENERATOR_VERSION}`",
        "",
        "## Boundary",
        "",
        "This PASS validates a serialization compatibility contract only. It does not generate or authorize landscape records, profiles, evidence retrieval, scoring, ranking, prioritization, recommendation, or biological interpretation.",
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def build_session_info(script_hash: str) -> bytes:
    lines = [
        f"task_id={TASK_ID}",
        f"generator_version={GENERATOR_VERSION}",
        f"generator_sha256={script_hash}",
        f"base_schema_version={BASE_SCHEMA_VERSION}",
        f"new_schema_version={SCHEMA_VERSION}",
        f"python_implementation={platform.python_implementation()}",
        f"python_version={platform.python_version()}",
        f"platform_system={platform.system()}",
        f"platform_machine={platform.machine()}",
        "dependencies=PYTHON_STANDARD_LIBRARY_ONLY",
        "network_access=PROHIBITED_NOT_USED",
        "api_access=PROHIBITED_NOT_USED",
        "package_installation=PROHIBITED_NOT_PERFORMED",
        "landscape_payload_generation=PROHIBITED_NONE_GENERATED",
        "profile_generation=PROHIBITED_NONE_GENERATED",
        "runtime_ai_decisions=PROHIBITED_NONE_USED",
        "randomness=NOT_USED",
        "wall_clock_governed_values=NOT_USED",
        "deterministic_regeneration=PASS",
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def build_bundle() -> dict[Path, bytes]:
    base = json.loads(BASE_SCHEMA_PATH.read_text(encoding="utf-8"))
    patched = build_schema()
    validate_patch_scope(base, patched)
    fixture_results = validate_task032c_examples(patched)
    safety_results = validate_schema_safety(patched)
    schema_bytes = pretty_json_bytes(patched)
    script_hash = sha256_file(Path(__file__).resolve())
    return {
        SCHEMA_PATH: schema_bytes,
        MANIFEST_PATH: pretty_json_bytes(
            build_manifest(schema_bytes, script_hash, fixture_results)
        ),
        REPORT_PATH: build_report(schema_bytes, fixture_results, safety_results),
        SESSION_PATH: build_session_info(script_hash),
    }


def write_bundle(bundle: dict[Path, bytes]) -> None:
    SCHEMA_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path, content in bundle.items():
        path.write_bytes(content)


def main() -> None:
    validate_working_tree_scope()
    validate_output_scope()
    frozen_before = validate_frozen_inputs()
    first = build_bundle()
    second = build_bundle()
    if first != second:
        fail("Deterministic schema-patch regeneration failed")
    write_bundle(first)
    validate_output_scope()
    frozen_after = validate_frozen_inputs()
    if frozen_before != frozen_after:
        fail("A previous frozen artifact changed during schema patch generation")
    print("TASK_033B_1_1_VALIDATION=PASS")
    print(f"schema_version={SCHEMA_VERSION}")
    print(f"schema_sha256={sha256_bytes(first[SCHEMA_PATH])}")
    print("dependency_relationship_cardinality=LOSSLESS_ORDERED_ARRAY")
    print("artifact_identifier_policy=SOURCE_NATIVE_ID_PLUS_NAMESPACE")
    print("landscape_payloads_generated=0")
    print("network_access=PROHIBITED_NOT_USED")


if __name__ == "__main__":
    main()
