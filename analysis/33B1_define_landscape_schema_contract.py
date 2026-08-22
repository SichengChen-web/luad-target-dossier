#!/usr/bin/env python3
"""Define and validate the Multi-component Evidence Landscape v0.2 schema.

Task #033B-1 is a schema-contract task only. This program writes one JSON
Schema and three small governance/QC artifacts. It does not read or generate
landscape records, retrieve evidence, materialize profiles, or make runtime
scientific decisions.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas/evidence_landscape_schema_v0.2.json"
OUTPUT_DIR = ROOT / "outputs/evidence_landscape_schema_v0.2"
MANIFEST_PATH = OUTPUT_DIR / "schema_manifest.json"
REPORT_PATH = OUTPUT_DIR / "schema_validation_report.md"
SESSION_PATH = OUTPUT_DIR / "session_info.txt"

TASK_ID = "TASK_033B_1"
SCHEMA_VERSION = "EVIDENCE_LANDSCAPE_SCHEMA_V0.2"
LANDSCAPE_VERSION = "MULTI_COMPONENT_EVIDENCE_LANDSCAPE_V0.2"
GENERATOR_VERSION = "LANDSCAPE_SCHEMA_CONTRACT_GENERATOR_V0.1"
SOURCE_PROFILE_SCHEMA_VERSION = "TARGET_EVIDENCE_PROFILE_MULTICOMPONENT_SCHEMA_V0.1"
SOURCE_PROFILE_VERSION = "TARGET_EVIDENCE_PROFILE_MULTICOMPONENT_V0.1"
SOURCE_EVIDENCE_SNAPSHOT_VERSION = (
    "EVIDENCE_SNAPSHOT_32C_CBFD2625F8B0CBB855DB90CBC8E2D605"
)
SOURCE_PROFILE_GENERATOR_VERSION = "MULTICOMPONENT_PROFILE_INTEGRATOR_V0.1"
SOURCE_INTEGRATION_RELEASE_ID = "PROFILE_INTEGRATION_RELEASE_8007AAA939B733EE6619F1FCFB87CAE8"

COMPONENT_STATES = (
    "OBSERVED",
    "PARTIAL",
    "CONFLICTING",
    "MISSING",
    "NOT_QUERIED",
)
FEATURE_MISSINGNESS = (
    "OBSERVED",
    "NOT_FOUND",
    "NOT_QUERIED",
    "NOT_APPLICABLE",
    "UNKNOWN",
)
DEPENDENCY_RELATIONSHIP_TYPES = (
    "SAME_SOURCE",
    "SHARED_DATASET",
    "PARTIAL",
    "UNKNOWN",
    "INDEPENDENT",
    "NOT_APPLICABLE",
)
DEPENDENCY_LEVELS = (
    "DEPENDENT",
    "PARTIALLY_DEPENDENT",
    "UNKNOWN",
    "INDEPENDENT",
    "NOT_APPLICABLE",
)
LIMITATION_SCOPES = (
    "LANDSCAPE",
    "PROFILE",
    "COMPONENT",
    "FEATURE",
    "SOURCE",
    "ARTIFACT",
)

PROHIBITED_FIELDS = frozenset(
    {
        "score",
        "ranking",
        "priority",
        "confidence",
        "overall_state",
        "recommendation",
        "interpretation",
    }
)

# Relevant frozen governance and Task #032C metadata/index artifacts. The
# multi-gigabyte profile payload is intentionally not read: Task #033B-1
# defines a schema and relies on its frozen manifest identity, not payload data.
FROZEN_INPUT_SHA256 = {
    "docs/governance/multi_component_evidence_landscape_specification_v0.2.md": "6d878dc12eaf7b9172f0880345cfc12bd67a209d45af68dbe543e05f192c8e73",
    "docs/governance/evidence_landscape_component_composition_policy_v0.1.md": "1ba8b4bf678906d5f15a50284742d2b81045d7530eb59d2fe28a81ad45eab2b7",
    "docs/governance/evidence_landscape_versioning_policy_v0.1.md": "fd71350c8c00f5abc935a772244232fbcb614dc898c0e44e2763f38121c62677",
    "docs/governance/evidence_landscape_validation_requirements_v0.1.md": "fccbcef5a1b61f8d45184c1f6177ce892a828887ad754c268eab9f1674c1c7ca",
    "docs/governance/target_evidence_profile_governance_v0.1.md": "1b8ab03bb758fd70d8a4bffb27ba1c7f97f83a52c20e75a0c18d9b0bd0941bbd",
    "docs/governance/profile_lifecycle_specification_v0.1.md": "346d46ce22b46513038ed7a62d951f1d3197432246e758bee84e56425137ccca",
    "docs/governance/profile_component_model_v0.1.md": "86ae5b8ce089f97770976b7b9f9b547a918e88c165cb7f983dd450178f8a7355",
    "docs/governance/profile_release_policy_v0.1.md": "f164be0352cd012583560b6ff5ef9850e43c59b49f4b9c4e28e3fe9138c77912",
    "docs/governance/evidence_component_interface_specification_v0.1.md": "b31254b347cbf440e3aade02857fb8149c54ea9a9a2b987197c4b724fefa20e8",
    "docs/governance/component_registration_policy_v0.1.md": "c1736e11695e6bb194665a0cf96115bb526075ca5aa9f9870e8e572f64302668",
    "docs/governance/component_validation_requirements_v0.1.md": "cc71c239972bc8f0b20fff63e4478624e0bcb56bc0febfc52855818ee5171c95",
    "docs/governance/component_dependency_model_v0.1.md": "5b77654a7ea543b2b2a184bba4a280cc4395c575065be6a3674d93a0955cdb06",
    "analysis/32C_integrate_evidence_profiles.py": "5fbfb5f390b94f94494e7f161e435e788d664e6d8388342fc0ad1acff6c0dad3",
    "outputs/evidence_profile_integration_v0.1/profile_manifest.json": "63492499977f7adb086e4ace9a491a72fa617a1fe054d544701826fb9657455d",
    "outputs/evidence_profile_integration_v0.1/profile_index.csv": "376e6d3440dba3ae392410cd2f836a9a700fe66248bf29257794b55015821a28",
    "outputs/evidence_profile_integration_v0.1/validation_report.md": "191ba0d01799d4e3e96bff3ebabc6c75997cbbdeee36217b45f0c45181302699",
}

ALLOWED_TASK_PATHS = {
    "analysis/33B1_define_landscape_schema_contract.py",
    "schemas/evidence_landscape_schema_v0.2.json",
    "outputs/evidence_landscape_schema_v0.2/schema_manifest.json",
    "outputs/evidence_landscape_schema_v0.2/schema_validation_report.md",
    "outputs/evidence_landscape_schema_v0.2/session_info.txt",
    *(
        path
        for path in FROZEN_INPUT_SHA256
        if path.startswith("docs/governance/")
        and path
        in {
            "docs/governance/multi_component_evidence_landscape_specification_v0.2.md",
            "docs/governance/evidence_landscape_component_composition_policy_v0.1.md",
            "docs/governance/evidence_landscape_versioning_policy_v0.1.md",
            "docs/governance/evidence_landscape_validation_requirements_v0.1.md",
        }
    ),
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


def pretty_json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode(
        "utf-8"
    )


def closed_object(properties: dict[str, Any], required: Iterable[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": list(required),
    }


def array_of(item_schema: dict[str, Any], *, min_items: int = 0) -> dict[str, Any]:
    return {
        "type": "array",
        "items": item_schema,
        "minItems": min_items,
        "uniqueItems": True,
    }


def build_schema() -> dict[str, Any]:
    nonempty_string = {"type": "string", "minLength": 1}
    sha256_schema = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
    artifact_id_schema = {"type": "string", "pattern": "^ART_[A-Z0-9_]+$"}

    artifact_reference = closed_object(
        {
            "artifact_id": artifact_id_schema,
            "artifact_sha256": sha256_schema,
            "storage_reference": nonempty_string,
        },
        ("artifact_id", "artifact_sha256"),
    )

    dependency_reference = closed_object(
        {
            "dependency_id": nonempty_string,
            "dependency_reference_status": {
                "type": "string",
                "enum": ["LINKED_GOVERNED_DEPENDENCY", "CONTROLLED_SENTINEL"],
            },
            "relationship_type": {
                "type": "string",
                "enum": list(DEPENDENCY_RELATIONSHIP_TYPES),
            },
            "dependency_level": {"type": "string", "enum": list(DEPENDENCY_LEVELS)},
            "dependency_model_version": nonempty_string,
            "governing_artifact_reference": {"$ref": "#/$defs/artifact_reference"},
            "review_status": nonempty_string,
        },
        (
            "dependency_id",
            "dependency_reference_status",
            "relationship_type",
            "dependency_level",
            "dependency_model_version",
            "governing_artifact_reference",
            "review_status",
        ),
    )
    dependency_reference["allOf"] = [
        {
            "if": {
                "properties": {"relationship_type": {"const": relationship_type}},
                "required": ["relationship_type"],
            },
            "then": {"properties": {"dependency_level": {"const": dependency_level}}},
        }
        for relationship_type, dependency_level in (
            ("SAME_SOURCE", "DEPENDENT"),
            ("SHARED_DATASET", "DEPENDENT"),
            ("PARTIAL", "PARTIALLY_DEPENDENT"),
            ("UNKNOWN", "UNKNOWN"),
            ("INDEPENDENT", "INDEPENDENT"),
            ("NOT_APPLICABLE", "NOT_APPLICABLE"),
        )
    ]

    provenance_reference = closed_object(
        {
            "component_id": {
                "type": "string",
                "enum": ["COMP_TRANSCRIPTOMIC_EVIDENCE", "COMP_DISEASE_ASSOCIATION"],
            },
            "feature_id": {"type": "string", "pattern": "^FTR_[A-Z0-9_]+$"},
            "claim_id": nonempty_string,
            "evidence_record_id": nonempty_string,
            "source_id": nonempty_string,
            "artifact_reference": {"$ref": "#/$defs/artifact_reference"},
            "extraction_rule_id": nonempty_string,
            "extractor_version": nonempty_string,
            "dependency_reference": {"$ref": "#/$defs/dependency_reference"},
        },
        (
            "component_id",
            "feature_id",
            "claim_id",
            "evidence_record_id",
            "source_id",
            "artifact_reference",
            "extraction_rule_id",
            "extractor_version",
            "dependency_reference",
        ),
    )

    feature_reference = closed_object(
        {
            "feature_id": {"type": "string", "pattern": "^FTR_[A-Z0-9_]+$"},
            "feature_name": nonempty_string,
            "missingness_status": {
                "type": "string",
                "enum": list(FEATURE_MISSINGNESS),
            },
            "source_feature_value_sha256": sha256_schema,
            "source_component_record_id": nonempty_string,
            "provenance_references": array_of(
                {"$ref": "#/$defs/provenance_reference"}, min_items=1
            ),
        },
        (
            "feature_id",
            "feature_name",
            "missingness_status",
            "source_component_record_id",
            "provenance_references",
        ),
    )

    transcriptomic_provenance_reference = deepcopy(provenance_reference)
    transcriptomic_provenance_reference["properties"]["component_id"] = {
        "const": "COMP_TRANSCRIPTOMIC_EVIDENCE"
    }
    disease_association_provenance_reference = deepcopy(provenance_reference)
    disease_association_provenance_reference["properties"]["component_id"] = {
        "const": "COMP_DISEASE_ASSOCIATION"
    }

    transcriptomic_feature_reference = deepcopy(feature_reference)
    transcriptomic_feature_reference["properties"]["provenance_references"]["items"] = {
        "$ref": "#/$defs/transcriptomic_provenance_reference"
    }
    disease_association_feature_reference = deepcopy(feature_reference)
    disease_association_feature_reference["properties"]["provenance_references"][
        "items"
    ] = {"$ref": "#/$defs/disease_association_provenance_reference"}

    limitation_reference = closed_object(
        {
            "limitation_id": {
                "type": "string",
                "pattern": "^LIM_[A-Z0-9_]+$",
            },
            "scope": {"type": "string", "enum": list(LIMITATION_SCOPES)},
            "source_version": nonempty_string,
            "registry_artifact_reference": {"$ref": "#/$defs/artifact_reference"},
            "review_status": nonempty_string,
        },
        (
            "limitation_id",
            "scope",
            "source_version",
            "registry_artifact_reference",
            "review_status",
        ),
    )

    source_component_reference = closed_object(
        {
            "source_record_id": nonempty_string,
            "source_record_sha256": sha256_schema,
            "source_record_artifact_id": artifact_id_schema,
            "container_artifact_id": artifact_id_schema,
            "container_artifact_sha256": sha256_schema,
            "partition_id": {"type": "string", "pattern": "^p[0-9a-f]{2}$"},
        },
        (
            "source_record_id",
            "source_record_sha256",
            "source_record_artifact_id",
            "container_artifact_id",
            "container_artifact_sha256",
        ),
    )

    state_rule_reference = closed_object(
        {
            "state_rule_id": nonempty_string,
            "state_rule_version": nonempty_string,
            "state_rule_review_status": nonempty_string,
        },
        ("state_rule_version",),
    )

    transcriptomic_version_axes = closed_object(
        {
            "source_evidence_snapshot_version": {
                "const": "TASK026_TRANSCRIPTOMIC_FEATURES_SHA256_4014469439ff14d27c451a356cf7711daa7a5331c58326eced2cf96edb298844"
            },
            "source_generator_version": {"const": "FULL_PROFILE_MATERIALIZER_V0.1"},
            "source_profile_schema_version": {
                "const": "TARGET_EVIDENCE_PROFILE_FULL_SCHEMA_V0.1"
            },
            "source_profile_version": {
                "const": "FULL_UNIVERSE_TARGET_EVIDENCE_PROFILE_V0.1"
            },
        },
        (
            "source_evidence_snapshot_version",
            "source_generator_version",
            "source_profile_schema_version",
            "source_profile_version",
        ),
    )

    disease_version_axes = closed_object(
        {
            "component_schema_version": {
                "const": "DISEASE_ASSOCIATION_COMPONENT_SCHEMA_V0.1"
            },
            "extractor_version": {
                "const": "DISEASE_ASSOCIATION_FEATURE_EXTRACTOR_V0.1"
            },
            "feature_generator_version": {
                "const": "DISEASE_ASSOCIATION_FEATURE_GENERATOR_V0.1"
            },
            "feature_schema_version": {
                "const": "DISEASE_ASSOCIATION_FEATURE_SCHEMA_V0.1"
            },
            "source_component_generator_version": {
                "const": "DISEASE_ASSOCIATION_COMPONENT_GENERATOR_V0.1"
            },
            "source_snapshot_version": {
                "const": "DA_OT_26_06_MONDO_0005061_SHA256_84949b70be605fea"
            },
        },
        (
            "component_schema_version",
            "extractor_version",
            "feature_generator_version",
            "feature_schema_version",
            "source_component_generator_version",
            "source_snapshot_version",
        ),
    )

    def component_schema(
        component_id: str,
        component_version: str,
        version_axes_ref: str,
        feature_reference_ref: str,
        feature_count: int,
    ) -> dict[str, Any]:
        return closed_object(
            {
                "component_id": {"const": component_id},
                "component_version": {"const": component_version},
                "component_definition_version": {"const": component_version},
                "availability_status": {"const": "PRESENT_IN_SOURCE_PROFILE"},
                "state": {"type": "string", "enum": list(COMPONENT_STATES)},
                "source_component_content_sha256": sha256_schema,
                "source_component_reference": {
                    "$ref": "#/$defs/source_component_reference"
                },
                "source_state_rule_reference": {"$ref": "#/$defs/state_rule_reference"},
                "version_axes": {"$ref": version_axes_ref},
                "feature_references": {
                    "type": "array",
                    "items": {"$ref": feature_reference_ref},
                    "minItems": feature_count,
                    "maxItems": feature_count,
                    "uniqueItems": True,
                },
                "limitation_references": array_of(
                    {"$ref": "#/$defs/limitation_reference"}
                ),
            },
            (
                "component_id",
                "component_version",
                "component_definition_version",
                "availability_status",
                "state",
                "source_component_content_sha256",
                "source_component_reference",
                "source_state_rule_reference",
                "version_axes",
                "feature_references",
                "limitation_references",
            ),
        )

    source_profile_identity = closed_object(
        {
            "source_profile_id": {"type": "string", "pattern": "^PRF_32C_[A-Z0-9]+$"},
            "source_profile_content_sha256": sha256_schema,
            "source_profile_schema_version": {"const": SOURCE_PROFILE_SCHEMA_VERSION},
            "source_profile_version": {"const": SOURCE_PROFILE_VERSION},
            "source_evidence_snapshot_version": {
                "const": SOURCE_EVIDENCE_SNAPSHOT_VERSION
            },
            "source_profile_generator_version": {
                "const": SOURCE_PROFILE_GENERATOR_VERSION
            },
            "source_integration_release_id": {"const": SOURCE_INTEGRATION_RELEASE_ID},
        },
        (
            "source_profile_id",
            "source_profile_content_sha256",
            "source_profile_schema_version",
            "source_profile_version",
            "source_evidence_snapshot_version",
            "source_profile_generator_version",
            "source_integration_release_id",
        ),
    )

    schema = closed_object(
        {
            "landscape_id": {"type": "string", "pattern": "^LND_[A-Z0-9]+$"},
            "EnsemblID": {
                "type": "string",
                "pattern": "^ENSG[0-9]+\\.[0-9]+$",
                "description": "Immutable, versioned Ensembl gene identifier.",
            },
            "universe_ordinal": {"type": "integer", "minimum": 1, "maximum": 29606},
            "landscape_schema_version": {"const": SCHEMA_VERSION},
            "landscape_version": {"const": LANDSCAPE_VERSION},
            "generator_version": {
                "type": "string",
                "pattern": "^MULTI_COMPONENT_EVIDENCE_LANDSCAPE_GENERATOR_V[0-9]+\\.[0-9]+$",
            },
            "source_profile_identity": {"$ref": "#/$defs/source_profile_identity"},
            "components": {
                "type": "array",
                "prefixItems": [
                    {"$ref": "#/$defs/transcriptomic_component_reference"},
                    {"$ref": "#/$defs/disease_association_component_reference"},
                ],
                "items": False,
                "minItems": 2,
                "maxItems": 2,
            },
            "limitation_references": array_of(
                {"$ref": "#/$defs/limitation_reference"}
            ),
        },
        (
            "landscape_id",
            "EnsemblID",
            "universe_ordinal",
            "landscape_schema_version",
            "landscape_version",
            "generator_version",
            "source_profile_identity",
            "components",
            "limitation_references",
        ),
    )
    schema.update(
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "urn:luad-target-dossier:evidence-landscape-schema:v0.2",
            "title": "Multi-component Evidence Landscape schema v0.2",
            "description": (
                "Strict structural contract for a deterministic projection of one frozen "
                "Task #032C multi-component Target Evidence Profile."
            ),
            "$comment": (
                "Schema contract only. It does not authorize or generate landscape payloads."
            ),
            "x-landscape-identity-tuple": [
                "EnsemblID",
                "landscape_schema_version",
                "landscape_version",
                "source_profile_identity.source_profile_id",
                "source_profile_identity.source_evidence_snapshot_version",
            ],
            "x-source-profile-identity-tuple": [
                "EnsemblID",
                "source_profile_identity.source_profile_schema_version",
                "source_profile_identity.source_profile_version",
                "source_profile_identity.source_evidence_snapshot_version",
            ],
            "x-provenance-relationship-key": [
                "component_id",
                "feature_id",
                "evidence_record_id",
            ],
            "$defs": {
                "artifact_reference": artifact_reference,
                "dependency_reference": dependency_reference,
                "provenance_reference": provenance_reference,
                "feature_reference": feature_reference,
                "transcriptomic_provenance_reference": transcriptomic_provenance_reference,
                "disease_association_provenance_reference": disease_association_provenance_reference,
                "transcriptomic_feature_reference": transcriptomic_feature_reference,
                "disease_association_feature_reference": disease_association_feature_reference,
                "limitation_reference": limitation_reference,
                "source_component_reference": source_component_reference,
                "state_rule_reference": state_rule_reference,
                "transcriptomic_version_axes": transcriptomic_version_axes,
                "disease_association_version_axes": disease_version_axes,
                "source_profile_identity": source_profile_identity,
                "transcriptomic_component_reference": component_schema(
                    "COMP_TRANSCRIPTOMIC_EVIDENCE",
                    "COMP_TRANSCRIPTOMIC_EVIDENCE_V0.1",
                    "#/$defs/transcriptomic_version_axes",
                    "#/$defs/transcriptomic_feature_reference",
                    22,
                ),
                "disease_association_component_reference": component_schema(
                    "COMP_DISEASE_ASSOCIATION",
                    "COMP_DISEASE_ASSOCIATION_V0.1",
                    "#/$defs/disease_association_version_axes",
                    "#/$defs/disease_association_feature_reference",
                    19,
                ),
            },
        }
    )
    return schema


def iter_dicts(value: Any, path: str = "$") -> Iterable[tuple[str, dict[str, Any]]]:
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from iter_dicts(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from iter_dicts(child, f"{path}[{index}]")


def validate_frozen_inputs() -> None:
    for relative_path, expected_hash in FROZEN_INPUT_SHA256.items():
        path = ROOT / relative_path
        if not path.is_file():
            fail(f"Frozen input missing: {relative_path}")
        observed_hash = sha256_file(path)
        if observed_hash != expected_hash:
            fail(
                f"Frozen input hash mismatch: {relative_path}; "
                f"expected {expected_hash}, observed {observed_hash}"
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
        if path_text not in ALLOWED_TASK_PATHS:
            unexpected.append(raw_line)
    if unexpected:
        fail("Unexpected working-tree changes:\n" + "\n".join(unexpected))


def validate_no_payload_artifacts() -> None:
    allowed_outputs = {MANIFEST_PATH, REPORT_PATH, SESSION_PATH}
    if OUTPUT_DIR.exists():
        unexpected = sorted(
            path.relative_to(ROOT).as_posix()
            for path in OUTPUT_DIR.rglob("*")
            if path.is_file() and path not in allowed_outputs
        )
        if unexpected:
            fail("Unexpected schema-task payload/output artifacts: " + ", ".join(unexpected))


def validate_governance_documents() -> None:
    governance_expectations = {
        "docs/governance/multi_component_evidence_landscape_specification_v0.2.md": (
            "EVIDENCE_LANDSCAPE_SCHEMA_V0.2",
            "MULTI_COMPONENT_EVIDENCE_LANDSCAPE_V0.2",
            "source_profile_id",
            "source_evidence_snapshot_version",
            "COMP_TRANSCRIPTOMIC_EVIDENCE_V0.1",
            "COMP_DISEASE_ASSOCIATION_V0.1",
        ),
        "docs/governance/evidence_landscape_component_composition_policy_v0.1.md": (
            "PRESENT_IN_SOURCE_PROFILE",
            "(component_id, feature_id, evidence_record_id)",
            "No runtime inference is permitted",
        ),
        "docs/governance/evidence_landscape_versioning_policy_v0.1.md": (
            "EVIDENCE_LANDSCAPE_SCHEMA_V0.2",
            "MULTI_COMPONENT_EVIDENCE_LANDSCAPE_V0.2",
            "Task #033A does not assign a landscape generator version",
        ),
        "docs/governance/evidence_landscape_validation_requirements_v0.1.md": (
            "29,606",
            "59,212",
            "1,213,846",
            "2,517,118",
            "byte-identical",
        ),
    }
    for relative_path, expected_terms in governance_expectations.items():
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        missing = [term for term in expected_terms if term not in text]
        if missing:
            fail(f"Governance terms missing from {relative_path}: {missing}")


def validate_task032c_manifest() -> None:
    path = ROOT / "outputs/evidence_profile_integration_v0.1/profile_manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    expected = {
        "profile_count": 29606,
        "profile_schema_version": SOURCE_PROFILE_SCHEMA_VERSION,
        "profile_version": SOURCE_PROFILE_VERSION,
        "evidence_snapshot_version": SOURCE_EVIDENCE_SNAPSHOT_VERSION,
        "integration_release_id": SOURCE_INTEGRATION_RELEASE_ID,
        "validation_status": "PASS",
    }
    for key, expected_value in expected.items():
        if manifest.get(key) != expected_value:
            fail(f"Task #032C manifest mismatch for {key}")
    observed_components = [
        (item.get("component_id"), item.get("component_version"))
        for item in manifest.get("components", [])
    ]
    expected_components = [
        ("COMP_TRANSCRIPTOMIC_EVIDENCE", "COMP_TRANSCRIPTOMIC_EVIDENCE_V0.1"),
        ("COMP_DISEASE_ASSOCIATION", "COMP_DISEASE_ASSOCIATION_V0.1"),
    ]
    if observed_components != expected_components:
        fail("Task #032C component identity/order mismatch")


def validate_schema_contract(schema: dict[str, Any]) -> dict[str, int]:
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        fail("Schema draft is not JSON Schema 2020-12")
    if schema.get("$id") != "urn:luad-target-dossier:evidence-landscape-schema:v0.2":
        fail("Schema identifier mismatch")
    if schema.get("x-landscape-identity-tuple") != [
        "EnsemblID",
        "landscape_schema_version",
        "landscape_version",
        "source_profile_identity.source_profile_id",
        "source_profile_identity.source_evidence_snapshot_version",
    ]:
        fail("Landscape identity tuple is not represented exactly")

    object_schema_count = 0
    prohibited_declarations: list[str] = []
    open_object_schemas: list[str] = []
    for path, node in iter_dicts(schema):
        properties = node.get("properties")
        if isinstance(properties, dict):
            object_schema_count += 1
            prohibited = PROHIBITED_FIELDS.intersection(properties)
            if prohibited:
                prohibited_declarations.append(f"{path}: {sorted(prohibited)}")
            if node.get("type") == "object" and node.get("additionalProperties") is not False:
                open_object_schemas.append(path)
    if prohibited_declarations:
        fail("Prohibited schema fields declared: " + "; ".join(prohibited_declarations))
    if open_object_schemas:
        fail("Object schemas are not closed: " + "; ".join(open_object_schemas))

    defs = schema.get("$defs", {})
    component_defs = (
        defs.get("transcriptomic_component_reference", {}),
        defs.get("disease_association_component_reference", {}),
    )
    for component_def in component_defs:
        state_values = component_def.get("properties", {}).get("state", {}).get("enum")
        if state_values != list(COMPONENT_STATES):
            fail("Component state vocabulary/order mismatch")
    missingness_values = (
        defs.get("feature_reference", {})
        .get("properties", {})
        .get("missingness_status", {})
        .get("enum")
    )
    if missingness_values != list(FEATURE_MISSINGNESS):
        fail("Feature missingness vocabulary/order mismatch")

    components = schema.get("properties", {}).get("components", {})
    if components.get("minItems") != 2 or components.get("maxItems") != 2:
        fail("Schema does not require exactly two components")
    if components.get("items") is not False or len(components.get("prefixItems", [])) != 2:
        fail("Schema does not freeze the two-component order")

    required_refs = {
        "feature_id",
        "claim_id",
        "evidence_record_id",
        "source_id",
        "artifact_reference",
        "extraction_rule_id",
        "extractor_version",
        "dependency_reference",
    }
    observed_refs = set(defs.get("provenance_reference", {}).get("required", []))
    if not required_refs.issubset(observed_refs):
        fail("Mandatory provenance references are incomplete")

    # Closed objects plus absence of every prohibited property declaration
    # means a conforming Draft 2020-12 validator rejects each named field at
    # the root and at every nested schema-defined object boundary.
    return {
        "closed_object_schema_count": object_schema_count,
        "prohibited_field_count": len(PROHIBITED_FIELDS),
        "component_definition_count": len(component_defs),
        "component_state_count": len(COMPONENT_STATES),
        "feature_missingness_state_count": len(FEATURE_MISSINGNESS),
    }


def build_manifest(schema_bytes: bytes, script_hash: str) -> dict[str, Any]:
    schema_hash = sha256_bytes(schema_bytes)
    return {
        "manifest_artifact_classification": "CLASS_B_REPRODUCIBLE_DERIVED_ARTIFACT",
        "schema_artifact_classification": "CLASS_A_SOURCE_CONTROLLED_SCHEMA_CONTRACT",
        "contract_id": f"SCHEMA_CONTRACT_{schema_hash[:24].upper()}",
        "determinism_contract": (
            "FROZEN_GOVERNANCE_HASHES_PLUS_GENERATOR_VERSION_PRODUCE_IDENTICAL_BYTES"
        ),
        "frozen_inputs": dict(sorted(FROZEN_INPUT_SHA256.items())),
        "generator": {
            "relative_path": "analysis/33B1_define_landscape_schema_contract.py",
            "sha256": script_hash,
            "version": GENERATOR_VERSION,
        },
        "landscape_version": LANDSCAPE_VERSION,
        "network_access": "PROHIBITED_NOT_USED",
        "output_artifact": {
            "relative_path": "schemas/evidence_landscape_schema_v0.2.json",
            "schema_version": SCHEMA_VERSION,
            "sha256": schema_hash,
            "size_bytes": len(schema_bytes),
        },
        "package_installation": "PROHIBITED_NOT_PERFORMED",
        "payload_generation": "PROHIBITED_NONE_GENERATED",
        "runtime_ai_decisions": "PROHIBITED_NONE_USED",
        "source_profile_binding": {
            "component_order": [
                "COMP_TRANSCRIPTOMIC_EVIDENCE",
                "COMP_DISEASE_ASSOCIATION",
            ],
            "evidence_snapshot_version": SOURCE_EVIDENCE_SNAPSHOT_VERSION,
            "profile_schema_version": SOURCE_PROFILE_SCHEMA_VERSION,
            "profile_version": SOURCE_PROFILE_VERSION,
        },
        "task_id": TASK_ID,
        "validation_status": "PASS",
    }


def build_report(schema_bytes: bytes, counts: dict[str, int]) -> bytes:
    schema_hash = sha256_bytes(schema_bytes)
    lines = [
        "# Multi-component Evidence Landscape v0.2 schema validation report",
        "",
        "**Task:** #033B-1  ",
        f"**Schema version:** `{SCHEMA_VERSION}`  ",
        "**Validation status:** PASS",
        "",
        "## Scope",
        "",
        "This report validates the machine-readable schema contract only. No landscape records, profiles, evidence, scores, ranks, priorities, recommendations, or interpretations were generated.",
        "",
        "## Contract validation",
        "",
        "| Check | Result |",
        "|---|---|",
        "| JSON Schema Draft 2020-12 declaration | PASS |",
        "| Task #033A governance hashes and required terminology | PASS |",
        "| Task #032C source-profile identity and component order | PASS |",
        "| Immutable versioned `EnsemblID` required | PASS |",
        "| Landscape identity tuple represented explicitly | PASS |",
        "| Source-profile identity and content hash required | PASS |",
        "| Exactly two ordered component references required | PASS |",
        "| Component versions and five structural states represented | PASS |",
        "| Feature and missingness references represented | PASS |",
        "| Record-level provenance and dependency references required | PASS |",
        "| Limitation references represented | PASS |",
        f"| Closed object schemas | PASS ({counts['closed_object_schema_count']}) |",
        f"| Prohibited fields rejected at closed object boundaries | PASS ({counts['prohibited_field_count']} names) |",
        "| Frozen relevant prior-artifact hashes unchanged | PASS |",
        "| In-memory double generation byte-identical | PASS |",
        "| Network access | PROHIBITED; NOT USED |",
        "| Package installation | PROHIBITED; NOT PERFORMED |",
        "| Runtime AI decisions | PROHIBITED; NONE USED |",
        "| Landscape payload generation | PROHIBITED; NONE GENERATED |",
        "",
        "## Controlled vocabularies",
        "",
        "Component states: `OBSERVED`, `PARTIAL`, `CONFLICTING`, `MISSING`, `NOT_QUERIED`.",
        "",
        "Feature missingness: `OBSERVED`, `NOT_FOUND`, `NOT_QUERIED`, `NOT_APPLICABLE`, `UNKNOWN`.",
        "",
        "## Prohibited fields",
        "",
        "The strict, closed schema does not declare and therefore rejects: `score`, `ranking`, `priority`, `confidence`, `overall_state`, `recommendation`, and `interpretation`.",
        "",
        "## Artifact identity",
        "",
        f"- Schema SHA256: `{schema_hash}`",
        f"- Schema byte size: `{len(schema_bytes)}`",
        f"- Generator version: `{GENERATOR_VERSION}`",
        "",
        "## Boundary",
        "",
        "This PASS establishes schema-contract conformance only. It does not validate or authorize a future landscape payload, release, lifecycle transition, or scientific interpretation.",
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def build_session_info(script_hash: str) -> bytes:
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
        "package_installation=PROHIBITED_NOT_PERFORMED",
        "runtime_ai_decisions=PROHIBITED_NONE_USED",
        "landscape_payload_generation=PROHIBITED_NONE_GENERATED",
        f"frozen_input_count={len(FROZEN_INPUT_SHA256)}",
        "deterministic_timestamp_policy=NO_WALL_CLOCK_FIELDS",
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def build_bundle() -> dict[Path, bytes]:
    schema = build_schema()
    counts = validate_schema_contract(schema)
    schema_bytes = pretty_json(schema)
    script_hash = sha256_file(Path(__file__).resolve())
    manifest_bytes = pretty_json(build_manifest(schema_bytes, script_hash))
    report_bytes = build_report(schema_bytes, counts)
    session_bytes = build_session_info(script_hash)
    return {
        SCHEMA_PATH: schema_bytes,
        MANIFEST_PATH: manifest_bytes,
        REPORT_PATH: report_bytes,
        SESSION_PATH: session_bytes,
    }


def write_bundle(bundle: dict[Path, bytes]) -> None:
    SCHEMA_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path, content in bundle.items():
        path.write_bytes(content)


def main() -> None:
    validate_working_tree_scope()
    validate_no_payload_artifacts()
    validate_frozen_inputs()
    validate_governance_documents()
    validate_task032c_manifest()

    first = build_bundle()
    second = build_bundle()
    if first != second:
        fail("Deterministic regeneration failed: in-memory bundles differ")

    frozen_before = {
        relative_path: sha256_file(ROOT / relative_path)
        for relative_path in FROZEN_INPUT_SHA256
    }
    write_bundle(first)
    validate_no_payload_artifacts()
    frozen_after = {
        relative_path: sha256_file(ROOT / relative_path)
        for relative_path in FROZEN_INPUT_SHA256
    }
    if frozen_before != frozen_after:
        fail("A frozen prior artifact changed during schema generation")

    generated_hashes = {
        path.relative_to(ROOT).as_posix(): sha256_bytes(content)
        for path, content in first.items()
    }
    print("TASK_033B_1_VALIDATION=PASS")
    print(f"schema_version={SCHEMA_VERSION}")
    print(f"schema_sha256={generated_hashes['schemas/evidence_landscape_schema_v0.2.json']}")
    print(f"generated_file_count={len(first)}")
    print("landscape_payloads_generated=0")
    print("network_access=PROHIBITED_NOT_USED")


if __name__ == "__main__":
    main()
