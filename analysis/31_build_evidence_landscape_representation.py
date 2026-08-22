#!/usr/bin/env python3
"""Build the governed Task #031 evidence-landscape representation.

This deterministic projection preserves component availability, structural
state, feature missingness, record-level dependency references, and governed
limitations from the frozen Task #030 profile universe. It does not evaluate,
score, rank, prioritize, select, recommend, or biologically interpret targets.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
FROZEN_TASK030_BASE_COMMIT = "018198214987a6a47ab6ac08e800247ed149ac64"
EXPECTED_BRANCH = "main"
EXPECTED_REMOTE_FRAGMENT = "SichengChen-web/luad-target-dossier"

EXPECTED_PROFILES = 29_606
EXPECTED_FEATURES_PER_PROFILE = 22
EXPECTED_FEATURE_REPRESENTATIONS = 651_332
EXPECTED_DEPENDENCY_REFERENCES = 1_036_210
EXPECTED_PARTITIONS = 256

SOURCE_SCHEMA_VERSION = "TARGET_EVIDENCE_PROFILE_FULL_SCHEMA_V0.1"
SOURCE_PROFILE_VERSION = "FULL_UNIVERSE_TARGET_EVIDENCE_PROFILE_V0.1"
SOURCE_EVIDENCE_SNAPSHOT_VERSION = (
    "TASK026_TRANSCRIPTOMIC_FEATURES_SHA256_"
    "4014469439ff14d27c451a356cf7711daa7a5331c58326eced2cf96edb298844"
)
SOURCE_RELEASE_CANDIDATE_ID = "PRC_5A13C5055A54AF794EDD0898"
SOURCE_PARTITION_STRATEGY_VERSION = "ENSEMBL_SHA256_PREFIX_2_V0.1"
SOURCE_COMPONENT_ID = "COMP_TRANSCRIPTOMIC_EVIDENCE"
SOURCE_COMPONENT_DEFINITION_VERSION = "COMP_TRANSCRIPTOMIC_EVIDENCE_V0.1"
SOURCE_STATE_RULE_VERSION = "STATE_RULE_REGISTRY_V0.1"

LANDSCAPE_SCHEMA_VERSION = "EVIDENCE_LANDSCAPE_SCHEMA_V0.1"
LANDSCAPE_VERSION = "EVIDENCE_LANDSCAPE_REPRESENTATION_V0.1"
GENERATOR_VERSION = "EVIDENCE_LANDSCAPE_REPRESENTATION_GENERATOR_V0.1"
MANIFEST_VERSION = "EVIDENCE_LANDSCAPE_MANIFEST_V0.1"
AVAILABILITY_STATUS = "PRESENT_IN_SOURCE_PROFILE"

COMPONENT_STATES = (
    "CONFLICTING",
    "OBSERVED",
    "MISSING",
    "PARTIAL",
    "NOT_QUERIED",
)
FEATURE_MISSINGNESS_STATES = (
    "OBSERVED",
    "NOT_FOUND",
    "NOT_QUERIED",
    "NOT_APPLICABLE",
    "UNKNOWN",
)
PARTITION_IDS = tuple(f"p{value:02x}" for value in range(EXPECTED_PARTITIONS))

SCRIPT_PATH = ROOT / "analysis/31_build_evidence_landscape_representation.py"
OUTPUT_DIR = ROOT / "outputs/evidence_landscape_v0.1"
LANDSCAPE_DIR = OUTPUT_DIR / "landscapes"
SOURCE_DIR = ROOT / "outputs/profile_release_candidate_v0.1"

INPUTS = {
    "task025_state_rules": ROOT / "outputs/state_rule_registry/state_rule_registry.csv",
    "task028_profile_governance": ROOT / "docs/governance/target_evidence_profile_governance_v0.1.md",
    "task028_component_model": ROOT / "docs/governance/profile_component_model_v0.1.md",
    "task028_lifecycle": ROOT / "docs/governance/profile_lifecycle_specification_v0.1.md",
    "task028_release_policy": ROOT / "docs/governance/profile_release_policy_v0.1.md",
    "task030_release_manifest": SOURCE_DIR / "release_manifest.json",
    "task030_profile_schema": SOURCE_DIR / "profile_schema_v0.1.json",
    "task030_profile_index": SOURCE_DIR / "profile_index.csv",
    "task030_dependency_manifest": SOURCE_DIR / "dependency_manifest.csv",
    "task030_partition_manifest": SOURCE_DIR / "partition_manifest.csv",
    "task030_universe_manifest": SOURCE_DIR / "universe_manifest.csv",
    "task030_validation_results": SOURCE_DIR / "validation_results.csv",
    "task030_validation_report": SOURCE_DIR / "validation_report.md",
}

EXPECTED_HASHES = {
    "task025_state_rules": "858974ae9d13e9505393dfce50e746b7fd1c15adec56d66771cff238da59d13d",
    "task028_profile_governance": "1b8ab03bb758fd70d8a4bffb27ba1c7f97f83a52c20e75a0c18d9b0bd0941bbd",
    "task028_component_model": "86ae5b8ce089f97770976b7b9f9b547a918e88c165cb7f983dd450178f8a7355",
    "task028_lifecycle": "346d46ce22b46513038ed7a62d951f1d3197432246e758bee84e56425137ccca",
    "task028_release_policy": "f164be0352cd012583560b6ff5ef9850e43c59b49f4b9c4e28e3fe9138c77912",
    "task030_release_manifest": "d7c3203f4920f5e799dea8e3515cd15a01efba83693a4be7c554a4e5094625fe",
    "task030_profile_schema": "cc67e72658ba827b90b3b9d8f61cc866f004d36915369138b816b6f1bedaa34c",
    "task030_profile_index": "5f6307c603f8d4d9416877512c28b0329c369d03aea7d24bf6cc64176193ee15",
    "task030_dependency_manifest": "2990cb9d3162c8459fbe48e1c8be3fc14821f9ecd8fa9023b1b4da114f669ea9",
    "task030_partition_manifest": "7dac57596356f1fd38fdfeed4cd4c18b32ff755fc414e575afe8841bdf5219f8",
    "task030_universe_manifest": "e4b304eb5fde7690a1525b404f5d1a011837fd88f774b4dbb2838f2c81b9c1ab",
    "task030_validation_results": "4f4cc169130c79f89e694a774dbe2f2c6d580e0b77887d6e2ac5311bdb8bebd1",
    "task030_validation_report": "58c2611d414c9b1420fd8b584ed8c211401b82dd55137055bb0da6cdbf00193c",
}

LIMITATION_REGISTRY = (
    {
        "limitation_id": "LIM_ONLY_TRANSCRIPTOMIC_COMPONENT",
        "scope": "PROFILE",
        "statement": "Only COMP_TRANSCRIPTOMIC_EVIDENCE is materialized in the frozen source profile universe.",
    },
    {
        "limitation_id": "LIM_TRANSCRIPTOMIC_ASSOCIATION_BOUNDARY",
        "scope": "COMPONENT",
        "statement": "The component represents tumour-versus-normal transcriptomic association and analysis structure only; it does not establish causality or therapeutic meaning.",
    },
    {
        "limitation_id": "LIM_NONOBSERVED_MISSINGNESS_PATHS_INCOMPLETELY_TESTED",
        "scope": "COMPONENT",
        "statement": "The frozen Task #030 features are OBSERVED; non-observed feature-missingness paths remain incompletely exercised by the materialized universe.",
    },
    {
        "limitation_id": "LIM_STATE_RULE_REVIEW_PENDING",
        "scope": "COMPONENT",
        "statement": "Task #025 structural state rules retain AWAITING_INDEPENDENT_SCIENTIFIC_REVIEW status.",
    },
    {
        "limitation_id": "LIM_PROFILE_LIFECYCLE_UNASSIGNED",
        "scope": "PROFILE",
        "statement": "Task #030 is a validated local release candidate without a human-governed lifecycle promotion.",
    },
    {
        "limitation_id": "LIM_EXTERNAL_STORAGE_PENDING",
        "scope": "PROFILE",
        "statement": "Governed external immutable storage references for the Task #030 large artifacts remain pending.",
    },
    {
        "limitation_id": "LIM_HUMAN_TRACEABILITY_AUDIT_PENDING",
        "scope": "PROFILE",
        "statement": "The deterministic Task #030 audit sample has not yet received its future human traceability audit.",
    },
)
COMPONENT_LIMITATION_IDS = tuple(
    item["limitation_id"] for item in LIMITATION_REGISTRY if item["scope"] == "COMPONENT"
)
PROFILE_LIMITATION_IDS = tuple(item["limitation_id"] for item in LIMITATION_REGISTRY)

ALLOWED_TASK031_PATHS = {"analysis/31_build_evidence_landscape_representation.py"}
ALLOWED_TASK031_PREFIX = "outputs/evidence_landscape_v0.1/"

TOP_LEVEL_OUTPUT_NAMES = {
    "evidence_landscape_schema_v0.1.json",
    "evidence_landscape_manifest.json",
    "evidence_landscape_validation_report.md",
    "evidence_landscape_index.csv",
    "landscape_partition_manifest.csv",
}

INDEX_COLUMNS = [
    "EnsemblID",
    "universe_ordinal",
    "landscape_id",
    "source_profile_id",
    "source_profile_content_sha256",
    "partition_id",
    "landscape_artifact_id",
    "landscape_content_sha256",
    "component_id",
    "component_availability_status",
    "component_state",
    "feature_missingness_states_present",
    "dependency_reference_count",
    "linked_dependency_reference_count",
    "not_applicable_dependency_reference_count",
    "limitation_ids",
    "landscape_schema_version",
    "landscape_version",
    "generator_version",
]

PARTITION_COLUMNS = [
    "partition_id",
    "artifact_role",
    "relative_path",
    "artifact_id",
    "landscape_count",
    "feature_missingness_representation_count",
    "dependency_reference_count",
    "file_size_bytes",
    "sha256",
    "landscape_schema_version",
    "landscape_version",
    "generator_version",
    "source_partition_strategy_version",
    "validation_status",
]

FORBIDDEN_FIELD_NAMES = {
    "score",
    "scores",
    "rank",
    "ranking",
    "rankings",
    "priority",
    "priorities",
    "confidence",
    "confidence_metric",
    "confidence_score",
    "evidence_strength",
    "target_quality",
    "target_selection",
    "recommendation",
    "recommendations",
    "therapeutic_recommendation",
    "therapeutic_direction",
    "biological_interpretation",
    "biological_importance",
}


def fail(message: str) -> None:
    raise RuntimeError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def pretty_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n"


def stable_id(prefix: str, value: str) -> str:
    return f"{prefix}_{sha256_text(value)[:24].upper()}"


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: list[str], rows: Iterable[dict[str, Any]]) -> int:
    count = 0
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in fields})
            count += 1
    return count


def run_git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, text=True, capture_output=True, check=False
    )
    if check and result.returncode != 0:
        fail(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def validate_repository() -> dict[str, str]:
    root = Path(run_git("rev-parse", "--show-toplevel")).resolve()
    branch = run_git("branch", "--show-current")
    head = run_git("rev-parse", "HEAD")
    remote = run_git("remote", "get-url", "origin")
    if root != ROOT:
        fail(f"Repository root mismatch: {root}")
    if branch != EXPECTED_BRANCH:
        fail(f"Branch mismatch: {branch}")
    if EXPECTED_REMOTE_FRAGMENT not in remote:
        fail(f"Remote mismatch: {remote}")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", FROZEN_TASK030_BASE_COMMIT, head],
        cwd=ROOT,
        check=False,
    )
    if ancestor.returncode != 0:
        fail("Frozen Task #030 base commit is not an ancestor of current HEAD.")

    paths = set(run_git("diff", "--name-only").splitlines())
    paths |= set(run_git("diff", "--cached", "--name-only").splitlines())
    paths |= set(run_git("ls-files", "--others", "--exclude-standard").splitlines())
    unexpected = sorted(
        path
        for path in paths
        if path
        and path not in ALLOWED_TASK031_PATHS
        and not path.startswith(ALLOWED_TASK031_PREFIX)
    )
    if unexpected:
        fail("Unexpected working-tree paths outside Task #031: " + ", ".join(unexpected))
    return {"branch": branch, "head": head, "remote": remote}


def validate_output_layout() -> None:
    if not OUTPUT_DIR.exists():
        return
    unexpected: list[str] = []
    for path in OUTPUT_DIR.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(OUTPUT_DIR).as_posix()
        if rel in TOP_LEVEL_OUTPUT_NAMES:
            continue
        if re.fullmatch(r"landscapes/p[0-9a-f]{2}/evidence_landscapes\.jsonl", rel):
            continue
        unexpected.append(rel)
    if unexpected:
        fail("Unexpected existing Task #031 output files: " + ", ".join(sorted(unexpected)))


def validate_frozen_inputs() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for key, path in INPUTS.items():
        if not path.is_file():
            fail(f"Missing frozen input: {relative(path)}")
        observed = sha256(path)
        if observed != EXPECTED_HASHES[key]:
            fail(
                f"Frozen input hash mismatch for {relative(path)}: "
                f"observed={observed}, expected={EXPECTED_HASHES[key]}"
            )
        result[key] = {
            "relative_path": relative(path),
            "file_size_bytes": path.stat().st_size,
            "sha256": observed,
        }

    governance = INPUTS["task028_profile_governance"].read_text(encoding="utf-8")
    component_model = INPUTS["task028_component_model"].read_text(encoding="utf-8")
    required_tokens = (
        (governance, "Profile completeness is not target quality."),
        (governance, "(feature_id, evidence_record_id)"),
        (component_model, SOURCE_COMPONENT_ID),
        (component_model, "`SHARED_DATASET` with dependency level `DEPENDENT`"),
        (component_model, "AWAITING_INDEPENDENT_SCIENTIFIC_REVIEW"),
    )
    if any(token not in text for text, token in required_tokens):
        fail("A required Task #028 governance token is absent.")
    return result


def load_source_release() -> tuple[
    dict[str, Any],
    dict[str, dict[str, str]],
    dict[str, dict[str, str]],
    list[dict[str, str]],
    dict[str, dict[str, dict[str, str]]],
]:
    release = json.loads(INPUTS["task030_release_manifest"].read_text(encoding="utf-8"))
    expected_release_fields = {
        "release_candidate_id": SOURCE_RELEASE_CANDIDATE_ID,
        "release_candidate_status": "VALIDATED_LOCAL_CANDIDATE",
        "validation_status": "PASS",
        "schema_version": SOURCE_SCHEMA_VERSION,
        "profile_version": SOURCE_PROFILE_VERSION,
        "evidence_snapshot_version": SOURCE_EVIDENCE_SNAPSHOT_VERSION,
        "partition_strategy_version": SOURCE_PARTITION_STRATEGY_VERSION,
        "state_rule_version": SOURCE_STATE_RULE_VERSION,
    }
    for field, expected in expected_release_fields.items():
        if release.get(field) != expected:
            fail(f"Task #030 release field {field} changed.")
    if release.get("counts", {}).get("profiles") != EXPECTED_PROFILES:
        fail("Task #030 profile count changed.")
    if release.get("counts", {}).get("profile_features") != EXPECTED_FEATURE_REPRESENTATIONS:
        fail("Task #030 feature count changed.")
    if release.get("counts", {}).get("provenance_relationships") != EXPECTED_DEPENDENCY_REFERENCES:
        fail("Task #030 provenance count changed.")
    if release.get("human_governance_promotion_recorded") is not False:
        fail("Task #030 lifecycle status unexpectedly changed.")

    source_schema = json.loads(INPUTS["task030_profile_schema"].read_text(encoding="utf-8"))
    if source_schema.get("properties", {}).get("schema_version", {}).get("const") != SOURCE_SCHEMA_VERSION:
        fail("Task #030 source schema identity changed.")

    universe_rows = read_csv(INPUTS["task030_universe_manifest"])
    index_rows = read_csv(INPUTS["task030_profile_index"])
    dependency_rows = read_csv(INPUTS["task030_dependency_manifest"])
    if not all(len(rows) == EXPECTED_PROFILES for rows in (universe_rows, index_rows, dependency_rows)):
        fail("Task #030 universe/index/dependency cardinality changed.")
    universe_ids = [row["EnsemblID"] for row in universe_rows]
    index_ids = [row["EnsemblID"] for row in index_rows]
    dependency_ids = [row["EnsemblID"] for row in dependency_rows]
    if universe_ids != index_ids or universe_ids != dependency_ids:
        fail("Task #030 canonical order differs across manifests.")
    if len(set(universe_ids)) != EXPECTED_PROFILES:
        fail("Task #030 immutable identities are not unique.")
    for ordinal, (universe, index, dependency) in enumerate(
        zip(universe_rows, index_rows, dependency_rows, strict=True), start=1
    ):
        expected_ordinal = str(ordinal)
        if any(
            row["universe_ordinal"] != expected_ordinal
            for row in (universe, index, dependency)
        ):
            fail(f"Task #030 ordinal mismatch at {ordinal}.")
        if universe["partition_id"] != index["partition_id"] or universe["partition_id"] != dependency["partition_id"]:
            fail(f"Task #030 partition mismatch for {universe['EnsemblID']}.")
        if dependency["provenance_relationship_count"] != "35":
            fail(f"Task #030 dependency count changed for {universe['EnsemblID']}.")

    index_by_id = {row["EnsemblID"]: row for row in index_rows}
    dependency_by_id = {row["EnsemblID"]: row for row in dependency_rows}

    partition_rows = read_csv(INPUTS["task030_partition_manifest"])
    if len(partition_rows) != EXPECTED_PARTITIONS * 2:
        fail("Task #030 partition manifest cardinality changed.")
    partitions: dict[str, dict[str, dict[str, str]]] = {
        part: {} for part in PARTITION_IDS
    }
    for row in partition_rows:
        part = row["partition_id"]
        role = row["artifact_role"]
        if part not in partitions or role not in {"PROFILE_PAYLOAD", "PROVENANCE_LINKS"}:
            fail(f"Unexpected Task #030 partition row: {part}/{role}")
        if role in partitions[part]:
            fail(f"Duplicate Task #030 partition role: {part}/{role}")
        path = ROOT / row["relative_path"]
        if not path.is_file():
            fail(f"Missing Task #030 partition payload: {relative(path)}")
        if path.stat().st_size != int(row["file_size_bytes"]) or sha256(path) != row["sha256"]:
            fail(f"Task #030 partition payload mismatch: {relative(path)}")
        partitions[part][role] = row
    if any(set(roles) != {"PROFILE_PAYLOAD", "PROVENANCE_LINKS"} for roles in partitions.values()):
        fail("Task #030 partition role coverage is incomplete.")

    validation_rows = read_csv(INPUTS["task030_validation_results"])
    if not validation_rows or any(row["status"] != "PASS" for row in validation_rows):
        fail("Task #030 frozen validation is not entirely PASS.")
    return release, index_by_id, dependency_by_id, universe_rows, partitions


def load_state_rules() -> dict[str, dict[str, str]]:
    rows = [
        row
        for row in read_csv(INPUTS["task025_state_rules"])
        if row["component_id"] == SOURCE_COMPONENT_ID
    ]
    rows.sort(key=lambda row: int(row["precedence"]))
    if len(rows) != 5 or tuple(row["state"] for row in rows) != COMPONENT_STATES:
        fail("Task #025 transcriptomic state vocabulary/precedence changed.")
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        if row["rule_version"] != SOURCE_STATE_RULE_VERSION:
            fail("Task #025 state rule version changed.")
        if row["automated_validation_status"] != "PASS":
            fail("Task #025 automated validation is not PASS.")
        if row["runtime_llm_decision"] != "PROHIBITED":
            fail("Task #025 runtime LLM prohibition changed.")
        result[row["rule_id"]] = row
    return result


def build_schema() -> dict[str, Any]:
    dependency_reference = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "feature_id",
            "evidence_record_id",
            "dependency_id",
            "dependency_reference_status",
            "relationship_type",
            "dependency_level",
        ],
        "properties": {
            "feature_id": {"type": "string", "pattern": "^FTR_[0-9A-F]{24}$"},
            "evidence_record_id": {"type": "string"},
            "dependency_id": {"type": "string"},
            "dependency_reference_status": {
                "enum": ["LINKED_GOVERNED_DEPENDENCY", "NOT_APPLICABLE"]
            },
            "relationship_type": {"enum": ["SHARED_DATASET", "NOT_APPLICABLE"]},
            "dependency_level": {"enum": ["DEPENDENT", "NOT_APPLICABLE"]},
        },
    }
    feature_landscape = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "feature_id",
            "feature_name",
            "missingness_status",
            "dependency_references",
        ],
        "properties": {
            "feature_id": {"type": "string", "pattern": "^FTR_[0-9A-F]{24}$"},
            "feature_name": {"type": "string"},
            "missingness_status": {"enum": list(FEATURE_MISSINGNESS_STATES)},
            "dependency_references": {
                "type": "array",
                "minItems": 1,
                "items": {"$ref": "#/$defs/dependency_reference"},
            },
        },
    }
    component_landscape = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "component_id",
            "component_definition_version",
            "availability_status",
            "state",
            "state_rule_id",
            "state_rule_version",
            "state_rule_review_status",
            "feature_landscapes",
            "limitation_ids",
        ],
        "properties": {
            "component_id": {"const": SOURCE_COMPONENT_ID},
            "component_definition_version": {"const": SOURCE_COMPONENT_DEFINITION_VERSION},
            "availability_status": {"const": AVAILABILITY_STATUS},
            "state": {"enum": list(COMPONENT_STATES)},
            "state_rule_id": {"type": "string"},
            "state_rule_version": {"const": SOURCE_STATE_RULE_VERSION},
            "state_rule_review_status": {"type": "string"},
            "feature_landscapes": {
                "type": "array",
                "minItems": EXPECTED_FEATURES_PER_PROFILE,
                "maxItems": EXPECTED_FEATURES_PER_PROFILE,
                "items": {"$ref": "#/$defs/feature_landscape"},
            },
            "limitation_ids": {
                "type": "array",
                "items": {"type": "string", "pattern": "^LIM_[A-Z0-9_]+$"},
            },
        },
    }
    source_reference = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "release_candidate_id",
            "profile_id",
            "profile_content_sha256",
            "profile_artifact_id",
            "profile_version",
            "profile_schema_version",
            "evidence_snapshot_version",
            "partition_strategy_version",
            "partition_id",
        ],
        "properties": {
            "release_candidate_id": {"const": SOURCE_RELEASE_CANDIDATE_ID},
            "profile_id": {"type": "string", "pattern": "^PRF_[0-9A-F]{24}$"},
            "profile_content_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "profile_artifact_id": {"type": "string", "pattern": "^ART_[0-9A-F]{24}$"},
            "profile_version": {"const": SOURCE_PROFILE_VERSION},
            "profile_schema_version": {"const": SOURCE_SCHEMA_VERSION},
            "evidence_snapshot_version": {"const": SOURCE_EVIDENCE_SNAPSHOT_VERSION},
            "partition_strategy_version": {"const": SOURCE_PARTITION_STRATEGY_VERSION},
            "partition_id": {"type": "string", "pattern": "^p[0-9a-f]{2}$"},
        },
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "urn:luad-target-dossier:evidence-landscape:v0.1",
        "title": "Evidence Landscape representation schema v0.1",
        "description": "A deterministic non-evaluative projection of one governed Target Evidence Profile.",
        "type": "object",
        "additionalProperties": False,
        "$defs": {
            "source_profile_reference": source_reference,
            "component_landscape": component_landscape,
            "feature_landscape": feature_landscape,
            "dependency_reference": dependency_reference,
        },
        "required": [
            "landscape_id",
            "EnsemblID",
            "universe_ordinal",
            "landscape_schema_version",
            "landscape_version",
            "generator_version",
            "source_profile_reference",
            "components",
            "profile_limitation_ids",
        ],
        "properties": {
            "landscape_id": {"type": "string", "pattern": "^LND_[0-9A-F]{24}$"},
            "EnsemblID": {"type": "string", "pattern": "^ENSG[0-9]+\\.[0-9]+$"},
            "universe_ordinal": {"type": "integer", "minimum": 1, "maximum": EXPECTED_PROFILES},
            "landscape_schema_version": {"const": LANDSCAPE_SCHEMA_VERSION},
            "landscape_version": {"const": LANDSCAPE_VERSION},
            "generator_version": {"const": GENERATOR_VERSION},
            "source_profile_reference": {"$ref": "#/$defs/source_profile_reference"},
            "components": {
                "type": "array",
                "minItems": 1,
                "maxItems": 1,
                "items": {"$ref": "#/$defs/component_landscape"},
            },
            "profile_limitation_ids": {
                "type": "array",
                "minItems": len(PROFILE_LIMITATION_IDS),
                "maxItems": len(PROFILE_LIMITATION_IDS),
                "items": {"type": "string", "pattern": "^LIM_[A-Z0-9_]+$"},
            },
        },
    }


def recursively_validate_forbidden_fields(value: Any, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = key.lower()
            if normalized in FORBIDDEN_FIELD_NAMES or any(
                normalized.endswith("_" + item) for item in FORBIDDEN_FIELD_NAMES
            ):
                fail(f"Forbidden evaluative field at {path}.{key}")
            recursively_validate_forbidden_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            recursively_validate_forbidden_fields(child, f"{path}[{index}]")


def dependency_semantics(dependency_id: str) -> tuple[str, str, str]:
    if dependency_id == "NOT_APPLICABLE":
        return "NOT_APPLICABLE", "NOT_APPLICABLE", "NOT_APPLICABLE"
    if re.fullmatch(r"DEP_[0-9A-F]{24}", dependency_id):
        return "LINKED_GOVERNED_DEPENDENCY", "SHARED_DATASET", "DEPENDENT"
    fail(f"Unrecognized frozen dependency identifier: {dependency_id}")


def validate_source_profile(
    profile: dict[str, Any],
    index_row: dict[str, str],
    dependency_row: dict[str, str],
    rules: dict[str, dict[str, str]],
) -> None:
    identifier = profile.get("EnsemblID")
    if identifier != index_row["EnsemblID"] or identifier != dependency_row["EnsemblID"]:
        fail(f"Source profile identity mismatch: {identifier}")
    if profile.get("profile_id") != index_row["profile_id"]:
        fail(f"Source profile ID mismatch: {identifier}")
    if profile.get("universe_ordinal") != int(index_row["universe_ordinal"]):
        fail(f"Source profile ordinal mismatch: {identifier}")
    if profile.get("schema_version") != SOURCE_SCHEMA_VERSION:
        fail(f"Source schema mismatch: {identifier}")
    if profile.get("profile_version") != SOURCE_PROFILE_VERSION:
        fail(f"Source profile version mismatch: {identifier}")
    if profile.get("evidence_snapshot_version") != SOURCE_EVIDENCE_SNAPSHOT_VERSION:
        fail(f"Source evidence snapshot mismatch: {identifier}")
    observed_hash = sha256_text(canonical_json(profile))
    if observed_hash != index_row["profile_content_sha256"]:
        fail(f"Source profile content hash mismatch: {identifier}")
    components = profile.get("components")
    if not isinstance(components, list) or len(components) != 1:
        fail(f"Unexpected component cardinality: {identifier}")
    component = components[0]
    if component.get("component_id") != SOURCE_COMPONENT_ID:
        fail(f"Unexpected component identity: {identifier}")
    if component.get("component_definition_version") != SOURCE_COMPONENT_DEFINITION_VERSION:
        fail(f"Unexpected component version: {identifier}")
    if component.get("state") not in COMPONENT_STATES:
        fail(f"Unexpected component state: {identifier}")
    rule = rules.get(component.get("state_rule_id"))
    if rule is None or rule["state"] != component["state"]:
        fail(f"Task #025 rule/state mismatch: {identifier}")
    if component.get("state_rule_version") != rule["rule_version"]:
        fail(f"Task #025 rule version mismatch: {identifier}")
    if component.get("state_rule_review_status") != rule["review_status"]:
        fail(f"Task #025 review status mismatch: {identifier}")
    features = component.get("features")
    if not isinstance(features, list) or len(features) != EXPECTED_FEATURES_PER_PROFILE:
        fail(f"Source feature cardinality mismatch: {identifier}")


def source_relationship_rows(profile: dict[str, Any]) -> list[tuple[str, ...]]:
    result: list[tuple[str, ...]] = []
    seen_keys: set[tuple[str, str]] = set()
    for feature in profile["components"][0]["features"]:
        missingness = feature.get("missingness_status")
        if missingness not in FEATURE_MISSINGNESS_STATES:
            fail(f"Invalid source missingness for {profile['EnsemblID']}")
        links = feature.get("provenance_links")
        if not isinstance(links, list) or not links:
            fail(f"Missing source lineage for {profile['EnsemblID']}.{feature.get('feature_name')}")
        for link in links:
            if link.get("feature_id") != feature.get("feature_id"):
                fail(f"Feature/link identity mismatch for {profile['EnsemblID']}")
            key = (link["feature_id"], link["evidence_record_id"])
            if key in seen_keys:
                fail(f"Duplicate governed provenance key for {profile['EnsemblID']}: {key}")
            seen_keys.add(key)
            dependency_semantics(link["dependency_id"])
            result.append(
                (
                    link["feature_id"],
                    link["evidence_record_id"],
                    link["claim_id"],
                    link["source_id"],
                    link["artifact_id"],
                    link["dependency_id"],
                    missingness,
                    link["extraction_rule_id"],
                    link["extractor_version"],
                )
            )
    return sorted(result)


def csv_relationship_rows(rows: list[dict[str, str]]) -> list[tuple[str, ...]]:
    return sorted(
        (
            row["feature_id"],
            row["evidence_record_id"],
            row["claim_id"],
            row["source_id"],
            row["artifact_id"],
            row["dependency_id"],
            row["feature_missingness_status"],
            row["extraction_rule_id"],
            row["extractor_version"],
        )
        for row in rows
    )


def build_landscape(
    profile: dict[str, Any],
    index_row: dict[str, str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    identifier = profile["EnsemblID"]
    component = profile["components"][0]
    feature_landscapes: list[dict[str, Any]] = []
    missingness_counts: Counter[str] = Counter()
    dependency_status_counts: Counter[str] = Counter()
    linked_dependency_ids: set[str] = set()

    for feature in component["features"]:
        missingness = feature["missingness_status"]
        missingness_counts[missingness] += 1
        dependency_references: list[dict[str, str]] = []
        for link in feature["provenance_links"]:
            status, relationship_type, dependency_level = dependency_semantics(
                link["dependency_id"]
            )
            dependency_status_counts[status] += 1
            if status == "LINKED_GOVERNED_DEPENDENCY":
                linked_dependency_ids.add(link["dependency_id"])
            dependency_references.append(
                {
                    "feature_id": feature["feature_id"],
                    "evidence_record_id": link["evidence_record_id"],
                    "dependency_id": link["dependency_id"],
                    "dependency_reference_status": status,
                    "relationship_type": relationship_type,
                    "dependency_level": dependency_level,
                }
            )
        feature_landscapes.append(
            {
                "feature_id": feature["feature_id"],
                "feature_name": feature["feature_name"],
                "missingness_status": missingness,
                "dependency_references": dependency_references,
            }
        )

    landscape_id = stable_id(
        "LND",
        f"{profile['profile_id']}|{LANDSCAPE_VERSION}|{GENERATOR_VERSION}",
    )
    landscape = {
        "landscape_id": landscape_id,
        "EnsemblID": identifier,
        "universe_ordinal": profile["universe_ordinal"],
        "landscape_schema_version": LANDSCAPE_SCHEMA_VERSION,
        "landscape_version": LANDSCAPE_VERSION,
        "generator_version": GENERATOR_VERSION,
        "source_profile_reference": {
            "release_candidate_id": SOURCE_RELEASE_CANDIDATE_ID,
            "profile_id": profile["profile_id"],
            "profile_content_sha256": index_row["profile_content_sha256"],
            "profile_artifact_id": index_row["profile_artifact_id"],
            "profile_version": profile["profile_version"],
            "profile_schema_version": profile["schema_version"],
            "evidence_snapshot_version": profile["evidence_snapshot_version"],
            "partition_strategy_version": profile["partition_strategy_version"],
            "partition_id": index_row["partition_id"],
        },
        "components": [
            {
                "component_id": component["component_id"],
                "component_definition_version": component["component_definition_version"],
                "availability_status": AVAILABILITY_STATUS,
                "state": component["state"],
                "state_rule_id": component["state_rule_id"],
                "state_rule_version": component["state_rule_version"],
                "state_rule_review_status": component["state_rule_review_status"],
                "feature_landscapes": feature_landscapes,
                "limitation_ids": list(COMPONENT_LIMITATION_IDS),
            }
        ],
        "profile_limitation_ids": list(PROFILE_LIMITATION_IDS),
    }
    metadata = {
        "EnsemblID": identifier,
        "universe_ordinal": profile["universe_ordinal"],
        "landscape_id": landscape_id,
        "source_profile_id": profile["profile_id"],
        "source_profile_content_sha256": index_row["profile_content_sha256"],
        "partition_id": index_row["partition_id"],
        "component_state": component["state"],
        "missingness_counts": dict(missingness_counts),
        "dependency_status_counts": dict(dependency_status_counts),
        "linked_dependency_ids": sorted(linked_dependency_ids),
        "landscape_content_sha256": sha256_text(canonical_json(landscape)),
    }
    return landscape, metadata


def validate_landscape_object(landscape: dict[str, Any]) -> None:
    expected_top = {
        "landscape_id",
        "EnsemblID",
        "universe_ordinal",
        "landscape_schema_version",
        "landscape_version",
        "generator_version",
        "source_profile_reference",
        "components",
        "profile_limitation_ids",
    }
    if set(landscape) != expected_top:
        fail(f"Landscape top-level schema mismatch for {landscape.get('EnsemblID')}")
    if not re.fullmatch(r"LND_[0-9A-F]{24}", landscape["landscape_id"]):
        fail("Invalid landscape ID.")
    if not re.fullmatch(r"ENSG[0-9]+\.[0-9]+", landscape["EnsemblID"]):
        fail("Invalid immutable EnsemblID.")
    if landscape["landscape_schema_version"] != LANDSCAPE_SCHEMA_VERSION:
        fail("Landscape schema version mismatch.")
    if landscape["landscape_version"] != LANDSCAPE_VERSION:
        fail("Landscape version mismatch.")
    if landscape["generator_version"] != GENERATOR_VERSION:
        fail("Landscape generator version mismatch.")
    source = landscape["source_profile_reference"]
    expected_source = {
        "release_candidate_id",
        "profile_id",
        "profile_content_sha256",
        "profile_artifact_id",
        "profile_version",
        "profile_schema_version",
        "evidence_snapshot_version",
        "partition_strategy_version",
        "partition_id",
    }
    if set(source) != expected_source:
        fail("Source-profile reference schema mismatch.")
    if len(landscape["components"]) != 1:
        fail("Landscape component cardinality mismatch.")
    component = landscape["components"][0]
    expected_component = {
        "component_id",
        "component_definition_version",
        "availability_status",
        "state",
        "state_rule_id",
        "state_rule_version",
        "state_rule_review_status",
        "feature_landscapes",
        "limitation_ids",
    }
    if set(component) != expected_component:
        fail("Landscape component schema mismatch.")
    if component["component_id"] != SOURCE_COMPONENT_ID:
        fail("Landscape component identity mismatch.")
    if component["availability_status"] != AVAILABILITY_STATUS:
        fail("Landscape component availability mismatch.")
    if component["state"] not in COMPONENT_STATES:
        fail("Landscape component state vocabulary mismatch.")
    if len(component["feature_landscapes"]) != EXPECTED_FEATURES_PER_PROFILE:
        fail("Landscape feature cardinality mismatch.")
    for feature in component["feature_landscapes"]:
        if set(feature) != {
            "feature_id",
            "feature_name",
            "missingness_status",
            "dependency_references",
        }:
            fail("Landscape feature schema mismatch.")
        if feature["missingness_status"] not in FEATURE_MISSINGNESS_STATES:
            fail("Landscape missingness vocabulary mismatch.")
        if not feature["dependency_references"]:
            fail("Landscape feature has no dependency references.")
        for reference in feature["dependency_references"]:
            if set(reference) != {
                "feature_id",
                "evidence_record_id",
                "dependency_id",
                "dependency_reference_status",
                "relationship_type",
                "dependency_level",
            }:
                fail("Landscape dependency-reference schema mismatch.")
            expected = dependency_semantics(reference["dependency_id"])
            observed = (
                reference["dependency_reference_status"],
                reference["relationship_type"],
                reference["dependency_level"],
            )
            if observed != expected or reference["feature_id"] != feature["feature_id"]:
                fail("Landscape dependency semantics mismatch.")
    if tuple(component["limitation_ids"]) != COMPONENT_LIMITATION_IDS:
        fail("Landscape component limitations changed.")
    if tuple(landscape["profile_limitation_ids"]) != PROFILE_LIMITATION_IDS:
        fail("Landscape profile limitations changed.")
    recursively_validate_forbidden_fields(landscape)


def read_provenance_partition(path: Path) -> dict[str, list[dict[str, str]]]:
    by_identifier: dict[str, list[dict[str, str]]] = defaultdict(list)
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            by_identifier[row["EnsemblID"]].append(row)
    return dict(by_identifier)


def generate_partition(
    part: str,
    source_profile_path: Path,
    source_provenance_path: Path,
    output_path: Path,
    index_by_id: dict[str, dict[str, str]],
    dependency_by_id: dict[str, dict[str, str]],
    rules: dict[str, dict[str, str]],
) -> dict[str, Any]:
    provenance_by_id = read_provenance_partition(source_provenance_path)
    metadata: list[dict[str, Any]] = []
    state_counts: Counter[str] = Counter()
    missingness_counts: Counter[str] = Counter()
    dependency_status_counts: Counter[str] = Counter()
    linked_dependency_ids: set[str] = set()
    landscape_count = feature_count = dependency_count = 0

    with source_profile_path.open(encoding="utf-8") as source, output_path.open(
        "w", encoding="utf-8", newline=""
    ) as target:
        for line in source:
            profile = json.loads(line)
            identifier = profile["EnsemblID"]
            if identifier not in index_by_id or identifier not in dependency_by_id:
                fail(f"Source manifest lookup failed for {identifier}")
            index_row = index_by_id[identifier]
            dependency_row = dependency_by_id[identifier]
            if index_row["partition_id"] != part:
                fail(f"Source profile is in the wrong partition: {identifier}")
            validate_source_profile(profile, index_row, dependency_row, rules)
            embedded = source_relationship_rows(profile)
            tabular = csv_relationship_rows(provenance_by_id.pop(identifier, []))
            if embedded != tabular:
                fail(f"Task #030 embedded/tabular dependency lineage differs: {identifier}")

            landscape, item = build_landscape(profile, index_row)
            validate_landscape_object(landscape)
            landscape_text = canonical_json(landscape)
            if sha256_text(landscape_text) != item["landscape_content_sha256"]:
                fail(f"Landscape content hash mismatch: {identifier}")
            target.write(landscape_text + "\n")
            metadata.append(item)
            landscape_count += 1
            feature_count += len(landscape["components"][0]["feature_landscapes"])
            dependency_count += len(embedded)
            state_counts[item["component_state"]] += 1
            missingness_counts.update(item["missingness_counts"])
            dependency_status_counts.update(item["dependency_status_counts"])
            linked_dependency_ids.update(item["linked_dependency_ids"])

    if provenance_by_id:
        fail(f"Unmatched Task #030 provenance rows in {part}: {len(provenance_by_id)}")
    if landscape_count == 0:
        fail(f"Empty Task #031 partition: {part}")
    return {
        "partition_id": part,
        "output_path": output_path,
        "sha256": sha256(output_path),
        "file_size_bytes": output_path.stat().st_size,
        "landscape_count": landscape_count,
        "feature_count": feature_count,
        "dependency_count": dependency_count,
        "state_counts": dict(state_counts),
        "missingness_counts": dict(missingness_counts),
        "dependency_status_counts": dict(dependency_status_counts),
        "linked_dependency_ids": sorted(linked_dependency_ids),
        "metadata": metadata,
    }


def compare_partition_passes(first: dict[str, Any], second: dict[str, Any]) -> None:
    keys = (
        "partition_id",
        "sha256",
        "file_size_bytes",
        "landscape_count",
        "feature_count",
        "dependency_count",
        "state_counts",
        "missingness_counts",
        "dependency_status_counts",
        "linked_dependency_ids",
        "metadata",
    )
    if any(first[key] != second[key] for key in keys):
        fail(f"Partition regeneration differs: {first['partition_id']}")


def landscape_artifact_id(part: str) -> str:
    return stable_id(
        "ART", f"{LANDSCAPE_VERSION}|{GENERATOR_VERSION}|{part}|LANDSCAPE_PAYLOAD"
    )


def build_index_rows(metadata: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in sorted(metadata, key=lambda value: value["universe_ordinal"]):
        part = item["partition_id"]
        missingness_present = "|".join(sorted(item["missingness_counts"]))
        rows.append(
            {
                "EnsemblID": item["EnsemblID"],
                "universe_ordinal": str(item["universe_ordinal"]),
                "landscape_id": item["landscape_id"],
                "source_profile_id": item["source_profile_id"],
                "source_profile_content_sha256": item["source_profile_content_sha256"],
                "partition_id": part,
                "landscape_artifact_id": landscape_artifact_id(part),
                "landscape_content_sha256": item["landscape_content_sha256"],
                "component_id": SOURCE_COMPONENT_ID,
                "component_availability_status": AVAILABILITY_STATUS,
                "component_state": item["component_state"],
                "feature_missingness_states_present": missingness_present,
                "dependency_reference_count": str(sum(item["dependency_status_counts"].values())),
                "linked_dependency_reference_count": str(
                    item["dependency_status_counts"].get("LINKED_GOVERNED_DEPENDENCY", 0)
                ),
                "not_applicable_dependency_reference_count": str(
                    item["dependency_status_counts"].get("NOT_APPLICABLE", 0)
                ),
                "limitation_ids": "|".join(PROFILE_LIMITATION_IDS),
                "landscape_schema_version": LANDSCAPE_SCHEMA_VERSION,
                "landscape_version": LANDSCAPE_VERSION,
                "generator_version": GENERATOR_VERSION,
            }
        )
    return rows


def build_partition_rows(results: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for result in results:
        part = result["partition_id"]
        output_path = LANDSCAPE_DIR / part / "evidence_landscapes.jsonl"
        rows.append(
            {
                "partition_id": part,
                "artifact_role": "EVIDENCE_LANDSCAPE_PAYLOAD",
                "relative_path": relative(output_path),
                "artifact_id": landscape_artifact_id(part),
                "landscape_count": str(result["landscape_count"]),
                "feature_missingness_representation_count": str(result["feature_count"]),
                "dependency_reference_count": str(result["dependency_count"]),
                "file_size_bytes": str(result["file_size_bytes"]),
                "sha256": result["sha256"],
                "landscape_schema_version": LANDSCAPE_SCHEMA_VERSION,
                "landscape_version": LANDSCAPE_VERSION,
                "generator_version": GENERATOR_VERSION,
                "source_partition_strategy_version": SOURCE_PARTITION_STRATEGY_VERSION,
                "validation_status": "PASS",
            }
        )
    return rows


def combined_partition_hash(rows: list[dict[str, str]]) -> str:
    payload = [
        {
            "partition_id": row["partition_id"],
            "relative_path": row["relative_path"],
            "file_size_bytes": row["file_size_bytes"],
            "sha256": row["sha256"],
        }
        for row in rows
    ]
    return sha256_text(canonical_json(payload))


def build_validation_report(
    state_counts: Counter[str],
    missingness_counts: Counter[str],
    dependency_status_counts: Counter[str],
    linked_dependency_count: int,
    partition_set_hash: str,
    partition_bytes: int,
) -> str:
    state_text = canonical_json({state: state_counts.get(state, 0) for state in COMPONENT_STATES})
    missingness_text = canonical_json(
        {state: missingness_counts.get(state, 0) for state in FEATURE_MISSINGNESS_STATES}
    )
    dependency_text = canonical_json(dict(sorted(dependency_status_counts.items())))
    return f"""# Task #031 evidence landscape validation report

## Scope

This layer is a deterministic structural projection of the frozen Task #030 Target Evidence Profiles. It represents component availability, the exact non-ordinal Task #025 component state, feature-level missingness, record-level dependency references, and governed limitations. It does not evaluate targets or interpret evidence biologically.

## Architecture

- Immutable entity key: `EnsemblID`
- Source release: `{SOURCE_RELEASE_CANDIDATE_ID}`
- Landscape schema: `{LANDSCAPE_SCHEMA_VERSION}`
- Landscape version: `{LANDSCAPE_VERSION}`
- Generator: `{GENERATOR_VERSION}`
- Component represented: `{SOURCE_COMPONENT_ID}`
- Availability status: `{AVAILABILITY_STATUS}`
- Source partitioning retained: `{SOURCE_PARTITION_STRATEGY_VERSION}`

Each feature representation retains its exact source `missingness_status` and one dependency reference for every frozen Task #030 provenance relationship. `DEP_*` identifiers retain the Task #028 `SHARED_DATASET / DEPENDENT` semantics. The `NOT_APPLICABLE` sentinel remains explicitly non-linked.

## Structural audit counts

Counts below are reconciliation metadata only. They are not evidence strength, target quality, or confidence measures.

- Landscape objects: **{EXPECTED_PROFILES:,}**
- Component representations: **{EXPECTED_PROFILES:,}**
- Feature-missingness representations: **{EXPECTED_FEATURE_REPRESENTATIONS:,}**
- Dependency references: **{EXPECTED_DEPENDENCY_REFERENCES:,}**
- Unique linked governed dependency identifiers: **{linked_dependency_count:,}**
- Component-state distribution: `{state_text}`
- Feature-missingness distribution: `{missingness_text}`
- Dependency-reference status distribution: `{dependency_text}`
- Landscape partitions: **{EXPECTED_PARTITIONS}**
- Landscape payload bytes: **{partition_bytes:,}**
- Landscape partition-set SHA256: `{partition_set_hash}`

## Validation results

- Frozen Task #025, #028, and #030 input hashes: **PASS**.
- Source universe identity, cardinality, and canonical order: **PASS**.
- Source profile content hashes and version axes: **PASS**.
- Component availability represented separately from component state: **PASS**.
- All five state values retained in the schema and source states preserved exactly: **PASS**.
- All five feature-missingness values retained in the schema and source missingness preserved exactly: **PASS**.
- Embedded and tabular Task #030 dependency lineage reconciled exactly: **PASS**.
- All record-level `(feature_id, evidence_record_id, dependency_id)` references preserved: **PASS**.
- Governed dependency semantics and `NOT_APPLICABLE` boundary preserved: **PASS**.
- Source limitations represented through stable limitation identifiers: **PASS**.
- No evaluative or interpretation fields: **PASS**.
- Every one of 256 partitions regenerated byte-identically: **PASS**.
- Metadata regenerated byte-identically: **PASS**.
- Network access, package installation, randomness, wall-clock values, and runtime LLM decisions: **NOT USED**.

## Limitations

- Only the transcriptomic component exists in the frozen source universe.
- The materialized source universe exercises `OBSERVED` and `CONFLICTING`; the other component-state values remain schema-valid but absent from this snapshot.
- All source feature missingness values are `OBSERVED`; non-observed missingness values remain schema-valid but absent from this snapshot.
- Task #025 rules await independent scientific review.
- Task #030 lifecycle promotion, external immutable storage, and future human traceability audit remain unresolved governance actions.

This report validates representation fidelity only. It does not validate any target scientifically.
"""


def write_metadata_once(
    directory: Path,
    frozen_inputs: dict[str, dict[str, Any]],
    source_release: dict[str, Any],
    index_rows: list[dict[str, str]],
    partition_rows: list[dict[str, str]],
    state_counts: Counter[str],
    missingness_counts: Counter[str],
    dependency_status_counts: Counter[str],
    linked_dependency_count: int,
) -> dict[str, str]:
    directory.mkdir(parents=True, exist_ok=True)
    schema_path = directory / "evidence_landscape_schema_v0.1.json"
    index_path = directory / "evidence_landscape_index.csv"
    partition_path = directory / "landscape_partition_manifest.csv"
    manifest_path = directory / "evidence_landscape_manifest.json"
    report_path = directory / "evidence_landscape_validation_report.md"

    schema = build_schema()
    recursively_validate_forbidden_fields(schema)
    schema_path.write_text(pretty_json(schema), encoding="utf-8")
    if write_csv(index_path, INDEX_COLUMNS, index_rows) != EXPECTED_PROFILES:
        fail("Landscape index cardinality mismatch.")
    if write_csv(partition_path, PARTITION_COLUMNS, partition_rows) != EXPECTED_PARTITIONS:
        fail("Landscape partition manifest cardinality mismatch.")

    partition_set_hash = combined_partition_hash(partition_rows)
    partition_bytes = sum(int(row["file_size_bytes"]) for row in partition_rows)
    output_metadata = [
        {
            "relative_path": relative(OUTPUT_DIR / path.name),
            "file_size_bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in (schema_path, index_path, partition_path)
    ]
    manifest = {
        "manifest_version": MANIFEST_VERSION,
        "landscape_schema_version": LANDSCAPE_SCHEMA_VERSION,
        "landscape_version": LANDSCAPE_VERSION,
        "generator_version": GENERATOR_VERSION,
        "generator_script": {
            "relative_path": relative(SCRIPT_PATH),
            "sha256": sha256(SCRIPT_PATH),
        },
        "immutable_key": "EnsemblID",
        "canonical_order": "TASK030_UNIVERSE_ORDINAL",
        "source_release": {
            "release_candidate_id": SOURCE_RELEASE_CANDIDATE_ID,
            "schema_version": SOURCE_SCHEMA_VERSION,
            "profile_version": SOURCE_PROFILE_VERSION,
            "evidence_snapshot_version": SOURCE_EVIDENCE_SNAPSHOT_VERSION,
            "partition_strategy_version": SOURCE_PARTITION_STRATEGY_VERSION,
            "lifecycle_status": source_release["lifecycle_status"],
        },
        "frozen_inputs": list(frozen_inputs.values()),
        "counts": {
            "landscape_objects": EXPECTED_PROFILES,
            "component_representations": EXPECTED_PROFILES,
            "feature_missingness_representations": EXPECTED_FEATURE_REPRESENTATIONS,
            "dependency_references": EXPECTED_DEPENDENCY_REFERENCES,
            "unique_linked_dependency_identifiers": linked_dependency_count,
            "landscape_partitions": EXPECTED_PARTITIONS,
        },
        "component_availability": {
            SOURCE_COMPONENT_ID: {AVAILABILITY_STATUS: EXPECTED_PROFILES}
        },
        "component_state_counts": {
            state: state_counts.get(state, 0) for state in COMPONENT_STATES
        },
        "feature_missingness_counts": {
            state: missingness_counts.get(state, 0) for state in FEATURE_MISSINGNESS_STATES
        },
        "dependency_reference_status_counts": dict(sorted(dependency_status_counts.items())),
        "limitation_registry": list(LIMITATION_REGISTRY),
        "payload": {
            "partition_count": EXPECTED_PARTITIONS,
            "total_bytes": partition_bytes,
            "partition_set_sha256": partition_set_hash,
            "partition_manifest": relative(OUTPUT_DIR / partition_path.name),
        },
        "metadata_artifacts": output_metadata,
        "validation": {
            "status": "PASS",
            "state_preservation": "PASS",
            "missingness_preservation": "PASS",
            "dependency_preservation": "PASS",
            "forbidden_field_validation": "PASS",
            "partition_byte_identical_regeneration": "PASS",
            "metadata_byte_identical_regeneration": "PASS",
        },
        "prohibitions": [
            "NO_SCORES",
            "NO_RANKINGS",
            "NO_PRIORITIES",
            "NO_CONFIDENCE_METRICS",
            "NO_EVIDENCE_STRENGTH",
            "NO_TARGET_QUALITY",
            "NO_THERAPEUTIC_RECOMMENDATIONS",
            "NO_BIOLOGICAL_INTERPRETATION",
            "NO_LLM_RUNTIME_DECISIONS",
        ],
        "network_access": "PROHIBITED_NOT_USED",
        "package_installation": "PROHIBITED_NOT_USED",
    }
    recursively_validate_forbidden_fields(
        {
            "landscape_schema": schema,
            "landscape_payload_field_contract": {
                key: True for key in schema["properties"]
            },
        }
    )
    manifest_path.write_text(pretty_json(manifest), encoding="utf-8")
    report_path.write_text(
        build_validation_report(
            state_counts,
            missingness_counts,
            dependency_status_counts,
            linked_dependency_count,
            partition_set_hash,
            partition_bytes,
        ),
        encoding="utf-8",
    )
    return {
        path.name: sha256(path)
        for path in (schema_path, index_path, partition_path, manifest_path, report_path)
    }


def compare_metadata(first: Path, second: Path) -> None:
    for name in TOP_LEVEL_OUTPUT_NAMES:
        a = first / name
        b = second / name
        if not a.is_file() or not b.is_file() or a.read_bytes() != b.read_bytes():
            fail(f"Metadata regeneration differs: {name}")


def main() -> None:
    repository = validate_repository()
    validate_output_layout()
    frozen_inputs = validate_frozen_inputs()
    source_release, index_by_id, dependency_by_id, universe_rows, source_partitions = load_source_release()
    rules = load_state_rules()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LANDSCAPE_DIR.mkdir(parents=True, exist_ok=True)
    all_metadata: list[dict[str, Any]] = []
    partition_results: list[dict[str, Any]] = []
    state_counts: Counter[str] = Counter()
    missingness_counts: Counter[str] = Counter()
    dependency_status_counts: Counter[str] = Counter()
    linked_dependency_ids: set[str] = set()

    with tempfile.TemporaryDirectory(prefix="task031_landscape_") as temp_name:
        temp = Path(temp_name)
        pass_a = temp / "pass_a"
        pass_b = temp / "pass_b"
        pass_a.mkdir()
        pass_b.mkdir()

        for part in PARTITION_IDS:
            profile_row = source_partitions[part]["PROFILE_PAYLOAD"]
            provenance_row = source_partitions[part]["PROVENANCE_LINKS"]
            source_profile_path = ROOT / profile_row["relative_path"]
            source_provenance_path = ROOT / provenance_row["relative_path"]
            a_path = pass_a / f"{part}.jsonl"
            b_path = pass_b / f"{part}.jsonl"
            first = generate_partition(
                part,
                source_profile_path,
                source_provenance_path,
                a_path,
                index_by_id,
                dependency_by_id,
                rules,
            )
            second = generate_partition(
                part,
                source_profile_path,
                source_provenance_path,
                b_path,
                index_by_id,
                dependency_by_id,
                rules,
            )
            compare_partition_passes(first, second)
            destination = LANDSCAPE_DIR / part / "evidence_landscapes.jsonl"
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(a_path, destination)
            if sha256(destination) != first["sha256"] or destination.stat().st_size != first["file_size_bytes"]:
                fail(f"Copied landscape payload differs: {part}")
            result = dict(first)
            result["output_path"] = destination
            partition_results.append(result)
            all_metadata.extend(first["metadata"])
            state_counts.update(first["state_counts"])
            missingness_counts.update(first["missingness_counts"])
            dependency_status_counts.update(first["dependency_status_counts"])
            linked_dependency_ids.update(first["linked_dependency_ids"])

        if len(all_metadata) != EXPECTED_PROFILES:
            fail(f"Landscape object count {len(all_metadata)} != {EXPECTED_PROFILES}")
        if sum(state_counts.values()) != EXPECTED_PROFILES:
            fail("Landscape state count does not reconcile.")
        if sum(missingness_counts.values()) != EXPECTED_FEATURE_REPRESENTATIONS:
            fail("Landscape missingness count does not reconcile.")
        if sum(dependency_status_counts.values()) != EXPECTED_DEPENDENCY_REFERENCES:
            fail("Landscape dependency count does not reconcile.")
        if len({item["EnsemblID"] for item in all_metadata}) != EXPECTED_PROFILES:
            fail("Landscape immutable identities are not unique.")
        ordered_metadata = sorted(all_metadata, key=lambda item: item["universe_ordinal"])
        if [item["EnsemblID"] for item in ordered_metadata] != [row["EnsemblID"] for row in universe_rows]:
            fail("Landscape universe order differs from Task #030.")

        index_rows = build_index_rows(ordered_metadata)
        partition_rows = build_partition_rows(partition_results)
        meta_a = temp / "metadata_a"
        meta_b = temp / "metadata_b"
        write_metadata_once(
            meta_a,
            frozen_inputs,
            source_release,
            index_rows,
            partition_rows,
            state_counts,
            missingness_counts,
            dependency_status_counts,
            len(linked_dependency_ids),
        )
        write_metadata_once(
            meta_b,
            frozen_inputs,
            source_release,
            index_rows,
            partition_rows,
            state_counts,
            missingness_counts,
            dependency_status_counts,
            len(linked_dependency_ids),
        )
        compare_metadata(meta_a, meta_b)
        for name in TOP_LEVEL_OUTPUT_NAMES:
            shutil.copyfile(meta_a / name, OUTPUT_DIR / name)

    # Final audits after all repository writes.
    validate_frozen_inputs()
    _, final_index, final_dependencies, final_universe, final_partitions = load_source_release()
    if final_index.keys() != index_by_id.keys() or final_dependencies.keys() != dependency_by_id.keys():
        fail("Frozen Task #030 identities changed during generation.")
    if [row["EnsemblID"] for row in final_universe] != [row["EnsemblID"] for row in universe_rows]:
        fail("Frozen Task #030 canonical order changed during generation.")
    if final_partitions.keys() != source_partitions.keys():
        fail("Frozen Task #030 partition identities changed during generation.")
    validate_repository()
    validate_output_layout()

    partition_rows = read_csv(OUTPUT_DIR / "landscape_partition_manifest.csv")
    partition_set_hash = combined_partition_hash(partition_rows)
    partition_bytes = sum(int(row["file_size_bytes"]) for row in partition_rows)
    print(f"Evidence landscapes: {EXPECTED_PROFILES}")
    print(f"Feature missingness representations: {EXPECTED_FEATURE_REPRESENTATIONS}")
    print(f"Dependency references: {EXPECTED_DEPENDENCY_REFERENCES}")
    print(f"Component states: {canonical_json({state: state_counts.get(state, 0) for state in COMPONENT_STATES})}")
    print(f"Feature missingness: {canonical_json({state: missingness_counts.get(state, 0) for state in FEATURE_MISSINGNESS_STATES})}")
    print(f"Landscape partitions: {EXPECTED_PARTITIONS} ({partition_bytes} bytes)")
    print(f"Landscape partition-set SHA256: {partition_set_hash}")
    print("State, missingness, dependency, limitation, schema, and deterministic validation: PASS")
    print("Scores, rankings, priorities, confidence metrics, evidence strength, target quality, recommendations, biological interpretation, and LLM runtime decisions: NOT GENERATED")
    print(f"Repository: {repository['branch']} {repository['head']}")


if __name__ == "__main__":
    main()
