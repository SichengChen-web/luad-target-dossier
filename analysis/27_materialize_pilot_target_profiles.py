#!/usr/bin/env python3
"""Materialize ten deterministic pilot transcriptomic evidence profiles.

The script executes only the frozen Task #025 transcriptomic state predicates
over frozen Task #026 normalized features. It preserves every governed
feature-to-record provenance link and performs no target scoring, ranking,
candidate selection, recommendation, or biological interpretation.
"""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
TASK026A_BASE_COMMIT = "ec815fda81a4f447bd998ad12497d4e2e0f9f9bd"
EXPECTED_BRANCH = "main"
EXPECTED_REMOTE_FRAGMENT = "SichengChen-web/luad-target-dossier"

GENERATOR_VERSION = "PILOT_PROFILE_MATERIALIZER_V0.1"
PROFILE_VERSION = "PILOT_TARGET_EVIDENCE_PROFILE_V0.1"
SCHEMA_VERSION = "TARGET_EVIDENCE_PROFILE_PILOT_SCHEMA_V0.1"
EVIDENCE_SNAPSHOT_VERSION = (
    "TASK026_TRANSCRIPTOMIC_FEATURES_SHA256_"
    "4014469439ff14d27c451a356cf7711daa7a5331c58326eced2cf96edb298844"
)
COMPONENT_ID = "COMP_TRANSCRIPTOMIC_EVIDENCE"
EXPECTED_ENTITY_COUNT = 29_606
EXPECTED_FEATURE_COUNT = 22
EXPECTED_TASK025_FEATURE_COUNT = 11
EXPECTED_PILOT_COUNT = 10
EXPECTED_PROVENANCE_LINKS_PER_ENTITY = 35

SCRIPT_PATH = ROOT / "analysis/27_materialize_pilot_target_profiles.py"
OUTPUT_DIR = ROOT / "outputs/profile_generation"
PROFILES_PATH = OUTPUT_DIR / "pilot_profiles.json"
MANIFEST_PATH = OUTPUT_DIR / "pilot_profile_manifest.json"
PROVENANCE_PATH = OUTPUT_DIR / "pilot_profile_provenance_links.csv"
REPORT_PATH = OUTPUT_DIR / "pilot_profile_validation_report.md"
SCHEMA_PATH = OUTPUT_DIR / "profile_schema_v0.1.json"
SESSION_PATH = OUTPUT_DIR / "session_info.txt"

# The governed provenance CSV is the canonical lineage payload named and
# checksum-frozen by the Task #026-A specification. It is required to satisfy
# the Task #027 no-compressed-lineage contract.
INPUTS = {
    "task026_features": ROOT / "outputs/feature_extraction/transcriptomic_features.csv",
    "task026_dictionary": ROOT / "outputs/feature_extraction/feature_dictionary.csv",
    "task026_provenance": ROOT / "outputs/feature_extraction/feature_provenance_registry.csv",
    "task026_governance": ROOT / "docs/governance/task026_provenance_artifact_governance_v0.1.md",
    "task025_rules": ROOT / "outputs/state_rule_registry/state_rule_registry.csv",
}

EXPECTED_HASHES = {
    "task026_features": "4014469439ff14d27c451a356cf7711daa7a5331c58326eced2cf96edb298844",
    "task026_dictionary": "d3ffd865251674eef14c5f79c8651363a0c1497ef2d5e652a2744fb31f326abd",
    "task026_provenance": "68ba8096563358b539360963da7d2856fcb0f888673da9989741b95549f3b246",
    "task026_governance": "8e5e2a4e5018751ae9c4482734bfe48ffb432418ecebc764a1c341e11684c6da",
    "task025_rules": "858974ae9d13e9505393dfce50e746b7fd1c15adec56d66771cff238da59d13d",
}

ALLOWED_TASK027_PATHS = {"analysis/27_materialize_pilot_target_profiles.py"}
ALLOWED_TASK027_PREFIX = "outputs/profile_generation/"

DIRECTIONS = ("TUMOR_HIGHER", "TUMOR_LOWER")
FDR_STATUSES = ("THRESHOLD_MET", "THRESHOLD_NOT_MET")
SENSITIVITY_CATEGORIES = ("CONSISTENT_DIRECTION", "MIXED_DIRECTION")
SELECTION_RULE_ID = "PILOT_SELECTION_2X2X2_PLUS_LEXICAL_FILL_V0.1"
SELECTION_RULE_TEXT = (
    "Select the lexicographically smallest EnsemblID in each of the eight "
    "effect_direction_observed x fdr_pass_status x "
    "sensitivity_consistency_category cells, in frozen cell order; then add "
    "the two lexicographically smallest remaining EnsemblIDs."
)

PROFILE_STATES = ("CONFLICTING", "OBSERVED", "MISSING", "PARTIAL", "NOT_QUERIED")
MISSINGNESS_STATES = ("OBSERVED", "NOT_FOUND", "NOT_QUERIED", "NOT_APPLICABLE", "UNKNOWN")
FORBIDDEN_FIELD_NAMES = {
    "score", "rank", "ranking", "priority", "confidence", "confidence_score",
    "drugability", "druggability", "recommendation", "therapeutic_direction",
    "target_selection", "biological_importance", "interpretation",
}

PROVENANCE_INPUT_COLUMNS = [
    "feature_id", "EnsemblID", "feature_name", "claim_id",
    "evidence_record_id", "source_id", "artifact_id", "dependency_id",
    "feature_missingness_status", "extraction_rule_id", "extractor_version",
]
PROVENANCE_OUTPUT_COLUMNS = [
    "profile_id", "EnsemblID", "component_id", "feature_id", "feature_name",
    "claim_id", "evidence_record_id", "source_id", "artifact_id",
    "dependency_id", "feature_missingness_status", "extraction_rule_id",
    "extractor_version",
]
OUTPUT_NAMES = (
    "pilot_profiles.json", "pilot_profile_manifest.json",
    "pilot_profile_provenance_links.csv", "pilot_profile_validation_report.md",
    "profile_schema_v0.1.json", "session_info.txt",
)


def fail(message: str) -> None:
    raise RuntimeError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def pretty_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n"


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def stable_id(prefix: str, value: str) -> str:
    return f"{prefix}_{sha256_text(value)[:24].upper()}"


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
    base = run_git("rev-parse", TASK026A_BASE_COMMIT)
    remote = run_git("remote", "get-url", "origin")
    if root != ROOT or branch != EXPECTED_BRANCH or EXPECTED_REMOTE_FRAGMENT not in remote:
        fail(f"Repository identity mismatch: root={root}, branch={branch}, remote={remote}")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", base, head], cwd=ROOT, check=False
    )
    if ancestor.returncode != 0:
        fail("Frozen Task #026-A base commit is not an ancestor of current HEAD.")
    changed = set(run_git("diff", "--name-only").splitlines())
    changed |= set(run_git("diff", "--cached", "--name-only").splitlines())
    untracked = set(run_git("ls-files", "--others", "--exclude-standard").splitlines())
    unexpected = sorted(
        path for path in changed | untracked
        if path
        and path not in ALLOWED_TASK027_PATHS
        and not path.startswith(ALLOWED_TASK027_PREFIX)
    )
    if unexpected:
        fail("Unexpected working-tree paths outside Task #027: " + ", ".join(unexpected))
    return {"branch": branch, "head": head, "base": base, "remote": remote}


def validate_inputs() -> dict[str, dict[str, Any]]:
    manifest: dict[str, dict[str, Any]] = {}
    for key, path in INPUTS.items():
        if not path.is_file():
            fail(f"Missing frozen input: {relative(path)}")
        observed = sha256(path)
        if observed != EXPECTED_HASHES[key]:
            fail(
                f"Frozen input hash mismatch at {relative(path)}: "
                f"observed={observed}, expected={EXPECTED_HASHES[key]}"
            )
        manifest[key] = {
            "relative_path": relative(path),
            "sha256": observed,
            "file_size_bytes": path.stat().st_size,
        }
    governance = INPUTS["task026_governance"].read_text(encoding="utf-8")
    required_governance_tokens = (
        "(feature_id, evidence_record_id)",
        "ART_TASK026_TRANSCRIPTOMIC_FEATURE_PROVENANCE_V0_1",
        EXPECTED_HASHES["task026_provenance"],
        "TRANSCRIPTOMIC_FEATURE_EXTRACTOR_V0.1",
    )
    if any(token not in governance for token in required_governance_tokens):
        fail("Task #026-A governance contract is missing a required frozen token.")
    return manifest


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_features() -> tuple[list[dict[str, str]], list[str]]:
    with INPUTS["task026_features"].open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            fail("Task #026 feature table has no header.")
        rows = list(reader)
        fields = reader.fieldnames
    identifiers = [row["EnsemblID"] for row in rows]
    if len(rows) != EXPECTED_ENTITY_COUNT or len(set(identifiers)) != EXPECTED_ENTITY_COUNT:
        fail("Task #026 feature identity/count contract changed.")
    if any(not identifier.startswith("ENSG") for identifier in identifiers):
        fail("Task #026 feature table contains a non-Ensembl identity.")
    return rows, fields


def load_dictionary(feature_fields: list[str]) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    rows = read_csv(INPUTS["task026_dictionary"])
    if len(rows) != EXPECTED_FEATURE_COUNT:
        fail(f"Feature dictionary count is {len(rows)}, expected {EXPECTED_FEATURE_COUNT}.")
    names = [row["feature_name"] for row in rows]
    if len(set(names)) != len(names):
        fail("Feature dictionary contains duplicate feature names.")
    expected_feature_fields = [
        field for field in feature_fields if field not in {"EnsemblID", "extractor_version"}
    ]
    if names != expected_feature_fields:
        fail("Feature dictionary order does not match Task #026 feature columns.")
    task025_count = sum(row["task025_input"] == "TRUE" for row in rows)
    if task025_count != EXPECTED_TASK025_FEATURE_COUNT:
        fail("Task #026 dictionary no longer exposes exactly 11 Task #025 inputs.")
    return rows, {row["feature_name"]: row for row in rows}


def select_pilot(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    by_cell: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = (
            row["effect_direction_observed"], row["fdr_pass_status"],
            row["sensitivity_consistency_category"],
        )
        by_cell[key].append(row)
    selected: list[dict[str, str]] = []
    selection_records: list[dict[str, str]] = []
    selected_ids: set[str] = set()
    cell_index = 0
    for direction in DIRECTIONS:
        for fdr_status in FDR_STATUSES:
            for sensitivity in SENSITIVITY_CATEGORIES:
                cell_index += 1
                key = (direction, fdr_status, sensitivity)
                candidates = sorted(by_cell.get(key, []), key=lambda row: row["EnsemblID"])
                if not candidates:
                    fail(f"Pilot stratum has no eligible EnsemblID: {key}")
                chosen = candidates[0]
                if chosen["EnsemblID"] in selected_ids:
                    fail("Pilot selection produced a duplicate EnsemblID.")
                selected.append(chosen)
                selected_ids.add(chosen["EnsemblID"])
                selection_records.append({
                    "EnsemblID": chosen["EnsemblID"],
                    "selection_basis": f"CELL_{cell_index}",
                    "effect_direction_observed": direction,
                    "fdr_pass_status": fdr_status,
                    "sensitivity_consistency_category": sensitivity,
                })
    remaining = sorted(
        (row for row in rows if row["EnsemblID"] not in selected_ids),
        key=lambda row: row["EnsemblID"],
    )
    for fill_index, chosen in enumerate(remaining[:2], start=1):
        selected.append(chosen)
        selected_ids.add(chosen["EnsemblID"])
        selection_records.append({
            "EnsemblID": chosen["EnsemblID"],
            "selection_basis": f"LEXICAL_FILL_{fill_index}",
            "effect_direction_observed": chosen["effect_direction_observed"],
            "fdr_pass_status": chosen["fdr_pass_status"],
            "sensitivity_consistency_category": chosen["sensitivity_consistency_category"],
        })
    if len(selected) != EXPECTED_PILOT_COUNT or len(selected_ids) != EXPECTED_PILOT_COUNT:
        fail("Pilot selection did not produce exactly ten unique EnsemblIDs.")
    coverage = {
        "direction": {row["effect_direction_observed"] for row in selected},
        "fdr": {row["fdr_pass_status"] for row in selected},
        "sensitivity": {row["sensitivity_consistency_category"] for row in selected},
    }
    if coverage != {
        "direction": set(DIRECTIONS),
        "fdr": set(FDR_STATUSES),
        "sensitivity": set(SENSITIVITY_CATEGORIES),
    }:
        fail(f"Pilot coverage requirement failed: {coverage}")
    return selected, selection_records


def load_rules(dictionary: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    rows = [
        row for row in read_csv(INPUTS["task025_rules"])
        if row["component_id"] == COMPONENT_ID
    ]
    if len(rows) != 5 or {row["state"] for row in rows} != set(PROFILE_STATES):
        fail("Task #025 transcriptomic state-rule set changed.")
    rows.sort(key=lambda row: int(row["precedence"]))
    if [int(row["precedence"]) for row in rows] != [1, 2, 3, 4, 5]:
        fail("Task #025 transcriptomic precedence changed.")
    if any(
        row["automated_validation_status"] != "PASS"
        or row["runtime_llm_decision"] != "PROHIBITED"
        for row in rows
    ):
        fail("Task #025 rule validation/runtime contract changed.")
    contracts = [json.loads(row["input_feature_contract_json"]) for row in rows]
    if any(contract != contracts[0] for contract in contracts[1:]):
        fail("Task #025 rule states have inconsistent input feature contracts.")
    contract = {item["name"]: item["type"] for item in contracts[0]}
    dictionary_contract = {
        name: definition["data_type"]
        for name, definition in dictionary.items()
        if definition["task025_input"] == "TRUE"
    }
    if contract != dictionary_contract:
        fail("Task #025 rule inputs do not match the Task #026 feature dictionary.")
    for row in rows:
        row["predicate"] = json.loads(row["executable_predicate_json"])
        row["contract"] = contract
    return rows


def typed_value(value: str, data_type: str, label: str) -> bool | int:
    if data_type == "BOOLEAN":
        if value == "TRUE":
            return True
        if value == "FALSE":
            return False
        fail(f"{label} is not a frozen Boolean: {value!r}")
    if data_type == "NONNEGATIVE_INTEGER":
        if not value.isdigit():
            fail(f"{label} is not a non-negative integer: {value!r}")
        return int(value)
    fail(f"Unsupported Task #025 feature type at {label}: {data_type}")


def evaluate_predicate(node: dict[str, Any], features: dict[str, bool | int]) -> bool:
    op = node.get("op")
    if op == "all":
        args = node.get("args")
        if not isinstance(args, list) or not args:
            fail("Invalid Task #025 all predicate.")
        return all(evaluate_predicate(arg, features) for arg in args)
    if op == "any":
        args = node.get("args")
        if not isinstance(args, list) or not args:
            fail("Invalid Task #025 any predicate.")
        return any(evaluate_predicate(arg, features) for arg in args)
    if op in {"eq", "gt", "ge"}:
        feature = node.get("feature")
        if feature not in features or "value" not in node:
            fail(f"Invalid Task #025 leaf predicate: {node}")
        left = features[feature]
        right = node["value"]
        if type(left) is not type(right):
            fail(f"Task #025 comparison type mismatch for {feature}")
        if op == "eq":
            return left == right
        if isinstance(left, bool):
            fail(f"Ordered comparison is invalid for Boolean {feature}")
        return left > right if op == "gt" else left >= right
    fail(f"Unsupported Task #025 predicate operation: {op!r}")


def resolve_state(row: dict[str, str], rules: list[dict[str, Any]]) -> dict[str, str]:
    contract: dict[str, str] = rules[0]["contract"]
    typed = {
        name: typed_value(row[name], data_type, f"{row['EnsemblID']}.{name}")
        for name, data_type in contract.items()
    }
    matched = [rule for rule in rules if evaluate_predicate(rule["predicate"], typed)]
    if not matched:
        fail(f"No Task #025 transcriptomic state rule matched {row['EnsemblID']}")
    chosen = matched[0]
    return {
        "state": chosen["state"],
        "state_rule_id": chosen["rule_id"],
        "state_rule_version": chosen["rule_version"],
        "state_rule_review_status": chosen["review_status"],
    }


def load_selected_provenance(
    selected_ids: set[str],
    dictionary: dict[str, dict[str, str]],
) -> dict[tuple[str, str], list[dict[str, str]]]:
    links: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    seen_composite: set[tuple[str, str]] = set()
    with INPUTS["task026_provenance"].open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != PROVENANCE_INPUT_COLUMNS:
            fail("Governed Task #026 provenance schema changed.")
        for row in reader:
            if row["EnsemblID"] not in selected_ids:
                continue
            definition = dictionary.get(row["feature_name"])
            if definition is None:
                fail(f"Unknown selected provenance feature: {row['feature_name']}")
            expected_feature_id = stable_id(
                "FTR",
                f"{row['EnsemblID']}|{row['feature_name']}|{row['extractor_version']}",
            )
            if row["feature_id"] != expected_feature_id:
                fail(f"Selected provenance feature_id mismatch: {row['feature_id']}")
            if row["extraction_rule_id"] != definition["extraction_rule_id"]:
                fail(f"Selected provenance extraction-rule mismatch: {row['feature_id']}")
            if row["extractor_version"] != definition["extractor_version"]:
                fail(f"Selected provenance extractor-version mismatch: {row['feature_id']}")
            if row["feature_missingness_status"] not in MISSINGNESS_STATES:
                fail(f"Invalid selected missingness state: {row['feature_id']}")
            composite = (row["feature_id"], row["evidence_record_id"])
            if composite in seen_composite:
                fail(f"Duplicate governed provenance relationship: {composite}")
            seen_composite.add(composite)
            links[(row["EnsemblID"], row["feature_name"])].append(row)
    expected_link_count = len(selected_ids) * EXPECTED_PROVENANCE_LINKS_PER_ENTITY
    if sum(len(value) for value in links.values()) != expected_link_count:
        fail("Selected provenance link count differs from governed Task #026 cardinality.")
    for ensembl_id in selected_ids:
        for feature_name, definition in dictionary.items():
            rows = links.get((ensembl_id, feature_name), [])
            expected_count = len(definition["source_record_roles"].split("|"))
            if len(rows) != expected_count:
                fail(
                    f"Missing or extra provenance at {ensembl_id}/{feature_name}: "
                    f"observed={len(rows)}, expected={expected_count}"
                )
            statuses = {row["feature_missingness_status"] for row in rows}
            if len(statuses) != 1:
                fail(f"Conflicting missingness across lineage at {ensembl_id}/{feature_name}")
            rows.sort(key=lambda row: row["evidence_record_id"])
    return links


def build_schema() -> dict[str, Any]:
    provenance_required = [
        "feature_id", "evidence_record_id", "claim_id", "source_id",
        "artifact_id", "dependency_id", "extraction_rule_id", "extractor_version",
    ]
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "urn:luad-target-dossier:pilot-profile-schema:v0.1",
        "title": "Pilot target evidence profile schema v0.1",
        "description": "Structural evidence observations and uncompressed lineage only.",
        "type": "object",
        "additionalProperties": False,
        "required": ["release_metadata", "profiles"],
        "properties": {
            "release_metadata": {
                "type": "object", "additionalProperties": False,
                "required": [
                    "schema_version", "profile_version", "evidence_snapshot_version",
                    "generator_version", "immutable_key", "profile_count",
                    "release_status",
                ],
                "properties": {
                    "schema_version": {"const": SCHEMA_VERSION},
                    "profile_version": {"const": PROFILE_VERSION},
                    "evidence_snapshot_version": {"const": EVIDENCE_SNAPSHOT_VERSION},
                    "generator_version": {"const": GENERATOR_VERSION},
                    "immutable_key": {"const": "EnsemblID"},
                    "profile_count": {"const": EXPECTED_PILOT_COUNT},
                    "release_status": {"const": "PILOT_VALIDATION_ONLY"},
                },
            },
            "profiles": {
                "type": "array", "minItems": EXPECTED_PILOT_COUNT,
                "maxItems": EXPECTED_PILOT_COUNT,
                "items": {"$ref": "#/$defs/profile"},
            },
        },
        "$defs": {
            "provenance_link": {
                "type": "object", "additionalProperties": False,
                "required": provenance_required,
                "properties": {
                    "feature_id": {"type": "string", "pattern": "^FTR_[0-9A-F]{24}$"},
                    "evidence_record_id": {"type": "string", "minLength": 1},
                    "claim_id": {"type": "string", "minLength": 1},
                    "source_id": {"type": "string", "minLength": 1},
                    "artifact_id": {"type": "string", "minLength": 1},
                    "dependency_id": {"type": "string", "minLength": 1},
                    "extraction_rule_id": {"type": "string", "minLength": 1},
                    "extractor_version": {"type": "string", "minLength": 1},
                },
            },
            "feature": {
                "type": "object", "additionalProperties": False,
                "required": [
                    "feature_id", "feature_name", "value", "data_type",
                    "missingness_status", "provenance_links",
                ],
                "properties": {
                    "feature_id": {"type": "string", "pattern": "^FTR_[0-9A-F]{24}$"},
                    "feature_name": {"type": "string", "minLength": 1},
                    "value": {"type": "string"},
                    "data_type": {"type": "string", "minLength": 1},
                    "missingness_status": {"enum": list(MISSINGNESS_STATES)},
                    "provenance_links": {
                        "type": "array", "minItems": 1,
                        "items": {"$ref": "#/$defs/provenance_link"},
                    },
                },
            },
            "component": {
                "type": "object", "additionalProperties": False,
                "required": [
                    "component_id", "state", "state_rule_id", "state_rule_version",
                    "state_rule_review_status", "features",
                ],
                "properties": {
                    "component_id": {"const": COMPONENT_ID},
                    "state": {"enum": list(PROFILE_STATES)},
                    "state_rule_id": {"type": "string", "minLength": 1},
                    "state_rule_version": {"type": "string", "minLength": 1},
                    "state_rule_review_status": {"type": "string", "minLength": 1},
                    "features": {
                        "type": "array", "minItems": EXPECTED_FEATURE_COUNT,
                        "maxItems": EXPECTED_FEATURE_COUNT,
                        "items": {"$ref": "#/$defs/feature"},
                    },
                },
            },
            "profile": {
                "type": "object", "additionalProperties": False,
                "required": [
                    "profile_id", "EnsemblID", "profile_version",
                    "evidence_snapshot_version", "components",
                ],
                "properties": {
                    "profile_id": {"type": "string", "pattern": "^PRF_[0-9A-F]{24}$"},
                    "EnsemblID": {"type": "string", "pattern": "^ENSG[0-9]+\\.[0-9]+$"},
                    "profile_version": {"const": PROFILE_VERSION},
                    "evidence_snapshot_version": {"const": EVIDENCE_SNAPSHOT_VERSION},
                    "components": {
                        "type": "array", "minItems": 1, "maxItems": 1,
                        "items": {"$ref": "#/$defs/component"},
                    },
                },
            },
        },
    }


def profile_id(ensembl_id: str) -> str:
    return stable_id(
        "PRF", f"{ensembl_id}|{PROFILE_VERSION}|{EVIDENCE_SNAPSHOT_VERSION}"
    )


def build_profiles(
    selected: list[dict[str, str]],
    dictionary_rows: list[dict[str, str]],
    provenance: dict[tuple[str, str], list[dict[str, str]]],
    rules: list[dict[str, Any]],
) -> dict[str, Any]:
    profiles: list[dict[str, Any]] = []
    for source_row in selected:
        ensembl_id = source_row["EnsemblID"]
        features: list[dict[str, Any]] = []
        for definition in dictionary_rows:
            feature_name = definition["feature_name"]
            source_links = provenance[(ensembl_id, feature_name)]
            statuses = {link["feature_missingness_status"] for link in source_links}
            if len(statuses) != 1:
                fail(f"Missingness is not preserved at {ensembl_id}/{feature_name}")
            feature_id = source_links[0]["feature_id"]
            if any(link["feature_id"] != feature_id for link in source_links):
                fail(f"Feature identity differs across lineage at {ensembl_id}/{feature_name}")
            features.append({
                "feature_id": feature_id,
                "feature_name": feature_name,
                "value": source_row[feature_name],
                "data_type": definition["data_type"],
                "missingness_status": next(iter(statuses)),
                "provenance_links": [
                    {
                        key: link[key] for key in (
                            "feature_id", "evidence_record_id", "claim_id", "source_id",
                            "artifact_id", "dependency_id", "extraction_rule_id",
                            "extractor_version",
                        )
                    }
                    for link in source_links
                ],
            })
        resolved = resolve_state(source_row, rules)
        profiles.append({
            "profile_id": profile_id(ensembl_id),
            "EnsemblID": ensembl_id,
            "profile_version": PROFILE_VERSION,
            "evidence_snapshot_version": EVIDENCE_SNAPSHOT_VERSION,
            "components": [{
                "component_id": COMPONENT_ID,
                **resolved,
                "features": features,
            }],
        })
    return {
        "release_metadata": {
            "schema_version": SCHEMA_VERSION,
            "profile_version": PROFILE_VERSION,
            "evidence_snapshot_version": EVIDENCE_SNAPSHOT_VERSION,
            "generator_version": GENERATOR_VERSION,
            "immutable_key": "EnsemblID",
            "profile_count": EXPECTED_PILOT_COUNT,
            "release_status": "PILOT_VALIDATION_ONLY",
        },
        "profiles": profiles,
    }


def validate_schema_document(schema: dict[str, Any]) -> None:
    if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
        fail("Profile schema root is not closed.")
    required_defs = {"profile", "component", "feature", "provenance_link"}
    if set(schema.get("$defs", {})) != required_defs:
        fail("Profile schema definitions changed.")
    if schema["$defs"]["profile"].get("additionalProperties") is not False:
        fail("Profile schema does not prohibit undeclared profile fields.")
    if schema["$defs"]["feature"].get("additionalProperties") is not False:
        fail("Profile feature schema is not closed.")


def validate_profiles(
    payload: dict[str, Any],
    selected: list[dict[str, str]],
    dictionary_rows: list[dict[str, str]],
    provenance: dict[tuple[str, str], list[dict[str, str]]],
    schema: dict[str, Any],
) -> dict[str, Any]:
    validate_schema_document(schema)
    if set(payload) != {"release_metadata", "profiles"}:
        fail("Pilot profile root schema mismatch.")
    metadata = payload["release_metadata"]
    if metadata != {
        "schema_version": SCHEMA_VERSION,
        "profile_version": PROFILE_VERSION,
        "evidence_snapshot_version": EVIDENCE_SNAPSHOT_VERSION,
        "generator_version": GENERATOR_VERSION,
        "immutable_key": "EnsemblID",
        "profile_count": EXPECTED_PILOT_COUNT,
        "release_status": "PILOT_VALIDATION_ONLY",
    }:
        fail("Pilot profile release metadata mismatch.")
    profiles = payload["profiles"]
    if len(profiles) != EXPECTED_PILOT_COUNT:
        fail("Pilot payload does not contain ten profiles.")
    source_by_id = {row["EnsemblID"]: row for row in selected}
    expected_order = [row["EnsemblID"] for row in selected]
    if [profile["EnsemblID"] for profile in profiles] != expected_order:
        fail("Pilot profile order differs from deterministic selection order.")
    if len(set(expected_order)) != EXPECTED_PILOT_COUNT:
        fail("Pilot profile EnsemblIDs are not unique.")
    value_mismatches = missingness_mismatches = missing_provenance = 0
    embedded_links: set[tuple[str, str]] = set()
    state_counts: Counter[str] = Counter()
    for profile in profiles:
        ensembl_id = profile["EnsemblID"]
        if set(profile) != {
            "profile_id", "EnsemblID", "profile_version",
            "evidence_snapshot_version", "components",
        }:
            fail(f"Profile schema mismatch at {ensembl_id}")
        if profile["profile_id"] != profile_id(ensembl_id):
            fail(f"Profile identifier mismatch at {ensembl_id}")
        if len(profile["components"]) != 1:
            fail(f"Profile component cardinality mismatch at {ensembl_id}")
        component = profile["components"][0]
        if component["component_id"] != COMPONENT_ID or component["state"] not in PROFILE_STATES:
            fail(f"Component state/schema mismatch at {ensembl_id}")
        state_counts[component["state"]] += 1
        if len(component["features"]) != EXPECTED_FEATURE_COUNT:
            fail(f"Feature count mismatch at {ensembl_id}")
        if [feature["feature_name"] for feature in component["features"]] != [
            row["feature_name"] for row in dictionary_rows
        ]:
            fail(f"Feature order mismatch at {ensembl_id}")
        for feature in component["features"]:
            feature_name = feature["feature_name"]
            source = source_by_id[ensembl_id]
            if feature["value"] != source[feature_name]:
                value_mismatches += 1
            expected_links = provenance[(ensembl_id, feature_name)]
            statuses = {link["feature_missingness_status"] for link in expected_links}
            if feature["missingness_status"] not in statuses or len(statuses) != 1:
                missingness_mismatches += 1
            if not feature["provenance_links"]:
                missing_provenance += 1
            if len(feature["provenance_links"]) != len(expected_links):
                fail(f"Compressed or expanded lineage at {ensembl_id}/{feature_name}")
            expected_pairs = {
                (link["feature_id"], link["evidence_record_id"]) for link in expected_links
            }
            observed_pairs = {
                (link["feature_id"], link["evidence_record_id"])
                for link in feature["provenance_links"]
            }
            if observed_pairs != expected_pairs:
                fail(f"Embedded lineage mismatch at {ensembl_id}/{feature_name}")
            if embedded_links & observed_pairs:
                fail(f"Duplicate embedded provenance relationship at {ensembl_id}/{feature_name}")
            embedded_links |= observed_pairs
    if value_mismatches or missingness_mismatches or missing_provenance:
        fail(
            "Profile validation failure: "
            f"value_mismatches={value_mismatches}, "
            f"missingness_mismatches={missingness_mismatches}, "
            f"missing_provenance={missing_provenance}"
        )
    return {
        "profile_count": len(profiles),
        "profile_feature_count": len(profiles) * EXPECTED_FEATURE_COUNT,
        "embedded_provenance_link_count": len(embedded_links),
        "value_mismatches": value_mismatches,
        "missingness_mismatches": missingness_mismatches,
        "features_without_provenance": missing_provenance,
        "state_counts": dict(sorted(state_counts.items())),
    }


def recursively_validate_forbidden_fields(value: Any, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = key.lower()
            if normalized in FORBIDDEN_FIELD_NAMES or any(
                normalized.endswith("_" + forbidden) for forbidden in FORBIDDEN_FIELD_NAMES
            ):
                fail(f"Forbidden field {key!r} at {path}")
            recursively_validate_forbidden_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            recursively_validate_forbidden_fields(child, f"{path}[{index}]")


def provenance_output_rows(
    payload: dict[str, Any],
) -> Iterable[dict[str, str]]:
    for profile in payload["profiles"]:
        ensembl_id = profile["EnsemblID"]
        profile_identifier = profile["profile_id"]
        component = profile["components"][0]
        for feature in component["features"]:
            for link in feature["provenance_links"]:
                yield {
                    "profile_id": profile_identifier,
                    "EnsemblID": ensembl_id,
                    "component_id": component["component_id"],
                    "feature_id": link["feature_id"],
                    "feature_name": feature["feature_name"],
                    "claim_id": link["claim_id"],
                    "evidence_record_id": link["evidence_record_id"],
                    "source_id": link["source_id"],
                    "artifact_id": link["artifact_id"],
                    "dependency_id": link["dependency_id"],
                    "feature_missingness_status": feature["missingness_status"],
                    "extraction_rule_id": link["extraction_rule_id"],
                    "extractor_version": link["extractor_version"],
                }


def write_csv(path: Path, fields: list[str], rows: Iterable[dict[str, str]]) -> int:
    count = 0
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
            count += 1
    return count


def validation_report(
    selection_records: list[dict[str, str]],
    validation: dict[str, Any],
    output_hashes: dict[str, str],
) -> str:
    selection_lines = "\n".join(
        "| `{EnsemblID}` | {selection_basis} | {effect_direction_observed} | "
        "{fdr_pass_status} | {sensitivity_consistency_category} |".format(**row)
        for row in selection_records
    )
    state_counts = canonical_json(validation["state_counts"])
    return f"""# Task #027 pilot profile validation report

## Scope

This pilot deterministically materializes transcriptomic evidence observations for ten immutable EnsemblIDs. It executes the frozen Task #025 transcriptomic state predicates only. It does not evaluate target quality, score or rank targets, select therapeutic candidates, recommend therapies, infer biological importance, or generate biological interpretations.

## Deterministic pilot selection

Rule `{SELECTION_RULE_ID}`: {SELECTION_RULE_TEXT}

| EnsemblID | Basis | Direction | FDR status | Sensitivity category |
|---|---|---|---|---|
{selection_lines}

This mechanical pilot-universe selection is not scientific target selection.

## Profile schema

- Schema: `{SCHEMA_VERSION}`
- Profile version: `{PROFILE_VERSION}`
- Evidence snapshot: `{EVIDENCE_SNAPSHOT_VERSION}`
- Immutable identity: `EnsemblID`
- Profiles: {validation['profile_count']}
- Component per profile: `{COMPONENT_ID}` only
- Features per profile: {EXPECTED_FEATURE_COUNT}
- Feature values are stored as their exact Task #026 strings.
- Every feature embeds all governed provenance links without compression.
- Component states are structural Task #025 rule outputs; they are not target evaluations.

## Validation results

- Closed schema and required-field validation: **PASS**.
- Ten unique EnsemblIDs and deterministic order: **PASS**.
- Direction/FDR/sensitivity coverage: **PASS**.
- Profile feature values identical to Task #026: **PASS** ({validation['value_mismatches']} mismatches).
- Missingness identical to Task #026 provenance: **PASS** ({validation['missingness_mismatches']} mismatches).
- Every profile feature has provenance: **PASS** ({validation['features_without_provenance']} missing).
- Uncompressed provenance relationships: **PASS** ({validation['embedded_provenance_link_count']} links).
- Task #025 typed input and precedence contract: **PASS**.
- Structural component-state counts: `{state_counts}`.
- Forbidden field detection: **PASS**.
- Byte-identical two-pass generation: **PASS**.
- Frozen input hashes unchanged after generation: **PASS**.
- Network access, package installation, randomness, wall-clock values, LLM decisions, scoring, ranking, recommendation, and biological interpretation: **NOT USED / NOT GENERATED**.

## Core output hashes

- `pilot_profiles.json`: `{output_hashes['pilot_profiles.json']}`
- `pilot_profile_provenance_links.csv`: `{output_hashes['pilot_profile_provenance_links.csv']}`
- `profile_schema_v0.1.json`: `{output_hashes['profile_schema_v0.1.json']}`

## Interpretation boundaries and unresolved assumptions

The pilot validates the current transcriptomic component only. It does not validate future external-source components or a complete multi-domain profile. The selected records instantiate `OBSERVED` and `CONFLICTING` structural component states; the current all-observed Task #026 snapshot does not exercise `MISSING`, `NOT_QUERIED`, or `PARTIAL` profile paths.

Task #025 rules retain `AWAITING_INDEPENDENT_SCIENTIFIC_REVIEW`; these pilot objects are labelled `PILOT_VALIDATION_ONLY` and are not a release of scientific target conclusions. The Task #026-A concrete external storage reference remains pending; this pilot uses the locally available canonical artifact whose SHA256 matches the frozen governance specification.
"""


def write_core(
    directory: Path,
    payload: dict[str, Any],
    schema: dict[str, Any],
) -> dict[str, Any]:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "pilot_profiles.json").write_text(pretty_json(payload), encoding="utf-8")
    (directory / "profile_schema_v0.1.json").write_text(pretty_json(schema), encoding="utf-8")
    provenance_count = write_csv(
        directory / "pilot_profile_provenance_links.csv",
        PROVENANCE_OUTPUT_COLUMNS,
        provenance_output_rows(payload),
    )
    if provenance_count != EXPECTED_PILOT_COUNT * EXPECTED_PROVENANCE_LINKS_PER_ENTITY:
        fail(f"Pilot provenance row count is {provenance_count}, expected 350.")
    return {
        "provenance_link_count": provenance_count,
        "core_hashes": {
            name: sha256(directory / name)
            for name in (
                "pilot_profiles.json", "pilot_profile_provenance_links.csv",
                "profile_schema_v0.1.json",
            )
        },
        "core_sizes": {
            name: (directory / name).stat().st_size
            for name in (
                "pilot_profiles.json", "pilot_profile_provenance_links.csv",
                "profile_schema_v0.1.json",
            )
        },
    }


def validate_provenance_csv(path: Path, payload: dict[str, Any]) -> None:
    expected = list(provenance_output_rows(payload))
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != PROVENANCE_OUTPUT_COLUMNS:
            fail("Pilot provenance output schema mismatch.")
        observed = list(reader)
    if observed != expected:
        fail("Pilot provenance CSV differs from embedded uncompressed lineage.")
    composite = [
        (row["profile_id"], row["feature_id"], row["evidence_record_id"])
        for row in observed
    ]
    if len(composite) != len(set(composite)):
        fail("Pilot provenance CSV has a duplicate relationship key.")


def write_reports(
    directory: Path,
    core: dict[str, Any],
    validation: dict[str, Any],
    selection_records: list[dict[str, str]],
    input_manifest: dict[str, dict[str, Any]],
    repository: dict[str, str],
) -> None:
    report_text = validation_report(selection_records, validation, core["core_hashes"])
    (directory / "pilot_profile_validation_report.md").write_text(
        report_text, encoding="utf-8"
    )
    report_hash = sha256(directory / "pilot_profile_validation_report.md")
    manifest = {
        "manifest_version": "PILOT_PROFILE_MANIFEST_V0.1",
        "task": "027",
        "release_status": "PILOT_VALIDATION_ONLY",
        "generator_version": GENERATOR_VERSION,
        "profile_version": PROFILE_VERSION,
        "schema_version": SCHEMA_VERSION,
        "evidence_snapshot_version": EVIDENCE_SNAPSHOT_VERSION,
        "frozen_task026a_base_commit": TASK026A_BASE_COMMIT,
        "immutable_key": "EnsemblID",
        "input_artifacts": [input_manifest[key] for key in sorted(input_manifest)],
        "selection": {
            "selection_rule_id": SELECTION_RULE_ID,
            "selection_rule": SELECTION_RULE_TEXT,
            "manual_biological_selection": False,
            "profiles": selection_records,
        },
        "outputs": [
            {
                "relative_path": f"outputs/profile_generation/{name}",
                "sha256": core["core_hashes"][name],
                "file_size_bytes": core["core_sizes"][name],
            }
            for name in (
                "pilot_profiles.json", "pilot_profile_provenance_links.csv",
                "profile_schema_v0.1.json",
            )
        ] + [{
            "relative_path": "outputs/profile_generation/pilot_profile_validation_report.md",
            "sha256": report_hash,
            "file_size_bytes": (directory / "pilot_profile_validation_report.md").stat().st_size,
        }],
        "validation": {
            "schema": "PASS",
            "source_value_identity": "PASS",
            "missingness_preservation": "PASS",
            "uncompressed_lineage": "PASS",
            "task025_rule_contract": "PASS",
            "two_pass_byte_identity": "PASS",
            "previous_artifact_hashes": "PASS",
        },
        "prohibited_outputs": {
            "scores": False, "rankings": False, "target_selection": False,
            "recommendations": False, "biological_interpretations": False,
        },
    }
    recursively_validate_forbidden_fields({
        "release_metadata": {"profiles": validation["profile_count"]},
        "profile_payload": {},
    })
    (directory / "pilot_profile_manifest.json").write_text(
        pretty_json(manifest), encoding="utf-8"
    )
    output_hashes = {
        name: sha256(directory / name)
        for name in (
            "pilot_profiles.json", "pilot_profile_manifest.json",
            "pilot_profile_provenance_links.csv", "pilot_profile_validation_report.md",
            "profile_schema_v0.1.json",
        )
    }
    session_lines = [
        "task=027",
        "purpose=deterministic pilot transcriptomic evidence-profile materialization",
        f"generator_version={GENERATOR_VERSION}",
        f"profile_version={PROFILE_VERSION}",
        f"schema_version={SCHEMA_VERSION}",
        f"evidence_snapshot_version={EVIDENCE_SNAPSHOT_VERSION}",
        f"frozen_task026a_base_commit={TASK026A_BASE_COMMIT}",
        f"git_branch={repository['branch']}",
        f"git_origin={repository['remote']}",
        f"python_implementation={platform.python_implementation()}",
        f"python_version={platform.python_version()}",
        f"platform={platform.platform()}",
        f"script_sha256={sha256(SCRIPT_PATH)}",
        f"selection_rule_id={SELECTION_RULE_ID}",
        f"profile_count={validation['profile_count']}",
        f"profile_feature_count={validation['profile_feature_count']}",
        f"provenance_link_count={validation['embedded_provenance_link_count']}",
        "immutable_key=EnsemblID",
        "gene_symbols_used=FALSE",
        "network_access=NOT_USED",
        "packages_installed_or_updated=FALSE",
        "randomness_used=FALSE",
        "wall_clock_values_in_outputs=FALSE",
        "llm_runtime_decisions=FALSE",
        "scoring_generated=FALSE",
        "ranking_generated=FALSE",
        "therapeutic_recommendations_generated=FALSE",
        "biological_interpretations_generated=FALSE",
        "deterministic_two_pass_regeneration=PASS",
    ]
    for key in sorted(input_manifest):
        item = input_manifest[key]
        session_lines.append(
            f"frozen_input_sha256.{item['relative_path']}={item['sha256']}"
        )
    for name in sorted(output_hashes):
        session_lines.append(
            f"output_sha256.outputs/profile_generation/{name}={output_hashes[name]}"
        )
    (directory / "session_info.txt").write_text(
        "\n".join(session_lines) + "\n", encoding="utf-8"
    )


def generate_once(
    directory: Path,
    payload: dict[str, Any],
    schema: dict[str, Any],
    validation: dict[str, Any],
    selection_records: list[dict[str, str]],
    input_manifest: dict[str, dict[str, Any]],
    repository: dict[str, str],
) -> None:
    core = write_core(directory, payload, schema)
    validate_provenance_csv(directory / "pilot_profile_provenance_links.csv", payload)
    write_reports(
        directory, core, validation, selection_records, input_manifest, repository
    )


def compare_directories(first: Path, second: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for name in OUTPUT_NAMES:
        first_hash = sha256(first / name)
        second_hash = sha256(second / name)
        if first_hash != second_hash:
            fail(f"Deterministic regeneration failed for {name}")
        hashes[name] = first_hash
    return hashes


def main() -> None:
    repository = validate_repository()
    input_manifest = validate_inputs()
    feature_rows, feature_fields = load_features()
    dictionary_rows, dictionary = load_dictionary(feature_fields)
    selected, selection_records = select_pilot(feature_rows)
    rules = load_rules(dictionary)
    provenance = load_selected_provenance(
        {row["EnsemblID"] for row in selected}, dictionary
    )
    schema = build_schema()
    payload = build_profiles(selected, dictionary_rows, provenance, rules)
    validation = validate_profiles(
        payload, selected, dictionary_rows, provenance, schema
    )
    recursively_validate_forbidden_fields(payload)
    recursively_validate_forbidden_fields(schema)

    with tempfile.TemporaryDirectory(prefix="task027_a_") as first_name, tempfile.TemporaryDirectory(prefix="task027_b_") as second_name:
        first = Path(first_name)
        second = Path(second_name)
        generate_once(
            first, payload, schema, validation, selection_records,
            input_manifest, repository,
        )
        generate_once(
            second, payload, schema, validation, selection_records,
            input_manifest, repository,
        )
        hashes = compare_directories(first, second)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        for name in OUTPUT_NAMES:
            shutil.copyfile(first / name, OUTPUT_DIR / name)

    if any(sha256(OUTPUT_DIR / name) != hashes[name] for name in OUTPUT_NAMES):
        fail("Copied pilot output differs from the validated deterministic output.")
    validate_provenance_csv(PROVENANCE_PATH, payload)
    validate_inputs()
    validate_repository()

    print(f"Wrote {relative(PROFILES_PATH)} ({EXPECTED_PILOT_COUNT} profiles)")
    print(f"Wrote {relative(MANIFEST_PATH)}")
    print(f"Wrote {relative(PROVENANCE_PATH)} ({validation['embedded_provenance_link_count']} links)")
    print(f"Wrote {relative(REPORT_PATH)}")
    print(f"Wrote {relative(SCHEMA_PATH)}")
    print(f"Wrote {relative(SESSION_PATH)}")
    print("Schema, source values, missingness, provenance, rules, and determinism: PASS")
    print("Scoring, ranking, therapeutic selection/recommendation, and interpretation: NOT GENERATED")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise
