#!/usr/bin/env python3
"""Define and validate Case Study Selection schema v0.1.

Task #036A creates governance and a machine-readable case-pattern contract
only. It does not select project cases, rank or optimize targets, retrieve
evidence, modify prioritization outputs, interpret biology, or use runtime
AI/LLM decisions.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
from copy import deepcopy
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas/case_study_selection_schema_v0.1.json"
SOURCE_RULE_MODULE_PATH = ROOT / "analysis/35A_define_prioritization_schema.py"

TASK_ID = "TASK_036A"
SCHEMA_VERSION = "CASE_STUDY_SELECTION_SCHEMA_V0.1"
FRAMEWORK_VERSION = "CASE_STUDY_SELECTION_FRAMEWORK_V0.1"
RULE_CATALOG_VERSION = "CASE_STUDY_SELECTION_RULE_CATALOG_V0.1"
GENERATOR_VERSION = "CASE_STUDY_SELECTION_SCHEMA_GENERATOR_V0.1"
SELECTION_METHOD_ID = "CASE_SELECTION_SHA256_MINIMUM_V0.1"
SCHEMA_ID = "urn:luad-target-dossier:case-study-selection-schema:v0.1"
SOURCE_PRIORITIZATION_SCHEMA_VERSION = "PRIORITIZATION_OUTPUT_SCHEMA_V0.1"
SOURCE_PRIORITIZATION_VERSION = "TRANSPARENT_PRIORITIZATION_PROTOTYPE_V0.1"
SOURCE_PRIORITIZATION_RULE_CATALOG = "PRIORITIZATION_RULE_CATALOG_V0.1"
SOURCE_SUMMARY_SCHEMA_VERSION = "EVIDENCE_SUMMARY_SCHEMA_V0.1"
SOURCE_SUMMARY_VERSION = "EVIDENCE_AGGREGATION_REPRESENTATION_V0.1"

COMPONENT_STATES = ["OBSERVED", "PARTIAL", "CONFLICTING", "MISSING", "NOT_QUERIED"]
SOURCE_CATEGORIES = ["CATEGORY_A", "CATEGORY_B", "CATEGORY_C", "CATEGORY_UNASSIGNED"]
CASE_RULES = [
    (
        1,
        "CSRULE_036A_001_COMPLETE_PATTERN",
        "CSPRED_ALL_COMPONENTS_OBSERVED_V0.1",
        "CASE_COMPLETE_PATTERN",
        "STRUCTURAL_ALL_COMPONENTS_OBSERVED",
    ),
    (
        2,
        "CSRULE_036A_002_PARTIAL_PATTERN",
        "CSPRED_PARTIAL_OR_MIXED_AVAILABILITY_V0.1",
        "CASE_PARTIAL_PATTERN",
        "STRUCTURAL_PARTIAL_OR_MIXED_AVAILABILITY",
    ),
    (
        3,
        "CSRULE_036A_003_CONFLICT_PATTERN",
        "CSPRED_ANY_COMPONENT_CONFLICTING_V0.1",
        "CASE_CONFLICT_PATTERN",
        "STRUCTURAL_COMPONENT_CONFLICT_PRESENT",
    ),
    (
        4,
        "CSRULE_036A_004_LIMITATION_PATTERN",
        "CSPRED_ANY_LIMITATION_IDENTIFIER_V0.1",
        "CASE_LIMITATION_PATTERN",
        "STRUCTURAL_LIMITATION_IDENTIFIER_PRESENT",
    ),
]
PROHIBITED_FIELDS = {
    "best_target",
    "top_target",
    "rank",
    "ranking",
    "score",
    "priority_score",
    "recommendation",
    "target_quality",
    "evidence_strength",
}

FROZEN_INPUT_SHA256 = {
    "analysis/35A_define_prioritization_schema.py": "de23378886ebfc2cdb264bd96d680ce4d24d043588ccdb13d71f5530acdb6d07",
    "docs/governance/prioritization_framework_specification_v0.1.md": "104afeda3b4ecb824369d7f1f655213dbdc36679c1fd97c3b95e00ad63163f5a",
    "docs/governance/prioritization_rule_catalog_v0.1.md": "7794d79debd01c0a2e00f6d6109f78048089b8a1a747f77372e1e589e0dfadb1",
    "docs/governance/prioritization_validation_requirements_v0.1.md": "bf26ca1882685caf1da4cb45ccda0726049087c4782deab925524a8f0d321c47",
    "schemas/prioritization_output_schema_v0.1.json": "c79dcb1478e71239d158855ebf6b0f3b58cad84286fe1da3806bb22e77e74d72",
    "analysis/35B_materialize_prioritization.py": "7a651a3919b0a7c1e1a31bbea12e546039dc9117c053114807883f05491e66f5",
    "outputs/prioritization_v0.1/prioritization_manifest.json": "773eeec6bfa769c932f354bcc5eb552fe4a540a2fe65dd1811720b2e80c4ff80",
    "outputs/prioritization_v0.1/prioritization_index.csv": "8131fa2644dab0efb17c5ae42cb5d297ec3993aa69ba00dda4ec6bdb47c7a69a",
    "outputs/prioritization_v0.1/partition_manifest.csv": "e59a54e4a4857927eab529aab28c82ba8874e7b2cebfa2064527b89c642a5f14",
    "outputs/prioritization_v0.1/validation_report.md": "8fd3664d6ce8ffe9b5c7bfc87793ca0492d23b97be8f4b8ac6abd2f37eead1d0",
    "outputs/prioritization_v0.1/session_info.txt": "9107a208ad059f62b18f915d80879ea9fce9f877f839440fbf7dc145c0724e57",
}

NEW_DOCUMENTS = {
    "docs/governance/case_study_selection_framework_v0.1.md",
    "docs/governance/case_study_selection_rule_catalog_v0.1.md",
    "docs/governance/case_study_selection_validation_requirements_v0.1.md",
}
ALLOWED_WORKTREE_PATHS = {
    *NEW_DOCUMENTS,
    "analysis/36A_define_case_selection_schema.py",
    "schemas/case_study_selection_schema_v0.1.json",
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


def stable_id(prefix: str, value: Any, length: int = 32) -> str:
    return f"{prefix}_{sha256_bytes(canonical_json(value).encode('utf-8'))[:length].upper()}"


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


def load_source_rules() -> Any:
    spec = importlib.util.spec_from_file_location("task35a_rules", SOURCE_RULE_MODULE_PATH)
    if spec is None or spec.loader is None:
        fail("Unable to load frozen Task #035A rule/schema module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def conditional_mapping(
    trigger_field: str,
    trigger_value: str,
    mapped_values: dict[str, str],
) -> dict[str, Any]:
    return {
        "if": {
            "properties": {trigger_field: {"const": trigger_value}},
            "required": [trigger_field],
        },
        "then": {
            "properties": {
                field: {"const": value} for field, value in mapped_values.items()
            }
        },
    }


def build_schema() -> dict[str, Any]:
    sha256_schema = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
    source_rule_ids = [item[1] for item in load_source_rules().RULES]
    source_predicate_ids = [item[2] for item in load_source_rules().RULES]
    case_rule_ids = [item[1] for item in CASE_RULES]
    case_predicate_ids = [item[2] for item in CASE_RULES]
    case_categories = [item[3] for item in CASE_RULES]
    reason_codes = [item[4] for item in CASE_RULES]

    source_input_observation = closed_object(
        {
            "json_pointer": {
                "type": "string",
                "pattern": "^/component_state_snapshot/[0-9]+/component_state$",
            },
            "observed_value": {"type": "string", "enum": COMPONENT_STATES},
        },
        ["json_pointer", "observed_value"],
    )
    source_trace_step = closed_object(
        {
            "trace_step_ordinal": {"type": "integer", "minimum": 1, "maximum": 4},
            "rule_id": {"type": "string", "enum": source_rule_ids},
            "predicate_id": {"type": "string", "enum": source_predicate_ids},
            "predicate_result": {"type": "boolean"},
            "input_observations": {
                "type": "array",
                "minItems": 1,
                "items": {"$ref": "#/$defs/sourceInputObservation"},
            },
        },
        [
            "trace_step_ordinal",
            "rule_id",
            "predicate_id",
            "predicate_result",
            "input_observations",
        ],
        allOf=[
            conditional_mapping(
                "trace_step_ordinal",
                ordinal,
                {"rule_id": rule_id, "predicate_id": predicate_id},
            )
            for ordinal, rule_id, predicate_id, _ in load_source_rules().RULES
        ],
    )
    component_snapshot = closed_object(
        {
            "component_id": {"type": "string", "pattern": "^COMP_[A-Z0-9_]+$"},
            "component_version": {
                "type": "string",
                "pattern": "^COMP_[A-Z0-9_]+_V[0-9]+\\.[0-9]+$",
            },
            "component_state": {"type": "string", "enum": COMPONENT_STATES},
            "source_component_record_id": {"type": "string", "minLength": 1},
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
            "limitation_identifiers",
        ],
    )
    source_summary_identity = closed_object(
        {
            "evidence_summary_id": {
                "type": "string",
                "pattern": "^SUM_[A-F0-9]{32}$",
            },
            "evidence_summary_schema_version": {
                "type": "string",
                "const": SOURCE_SUMMARY_SCHEMA_VERSION,
            },
            "evidence_summary_version": {
                "type": "string",
                "const": SOURCE_SUMMARY_VERSION,
            },
            "evidence_summary_content_sha256": deepcopy(sha256_schema),
            "source_landscape_id": {"type": "string", "minLength": 1},
            "source_evidence_snapshot_version": {"type": "string", "minLength": 1},
        },
        [
            "evidence_summary_id",
            "evidence_summary_schema_version",
            "evidence_summary_version",
            "evidence_summary_content_sha256",
            "source_landscape_id",
            "source_evidence_snapshot_version",
        ],
    )
    source_prioritization_identity = closed_object(
        {
            "prioritization_representation_id": {
                "type": "string",
                "pattern": "^PRZ_[A-F0-9]{32}$",
            },
            "prioritization_output_schema_version": {
                "type": "string",
                "const": SOURCE_PRIORITIZATION_SCHEMA_VERSION,
            },
            "prioritization_representation_version": {
                "type": "string",
                "const": SOURCE_PRIORITIZATION_VERSION,
            },
            "prioritization_rule_catalog_version": {
                "type": "string",
                "const": SOURCE_PRIORITIZATION_RULE_CATALOG,
            },
            "prioritization_content_sha256": deepcopy(sha256_schema),
            "source_category": {"type": "string", "enum": SOURCE_CATEGORIES},
            "source_assigned_rule_id": {"type": "string", "enum": source_rule_ids},
            "source_summary_identity": {"$ref": "#/$defs/sourceSummaryIdentity"},
        },
        [
            "prioritization_representation_id",
            "prioritization_output_schema_version",
            "prioritization_representation_version",
            "prioritization_rule_catalog_version",
            "prioritization_content_sha256",
            "source_category",
            "source_assigned_rule_id",
            "source_summary_identity",
        ],
    )
    case_input_observation = closed_object(
        {
            "json_pointer": {"type": "string", "minLength": 1},
            "observed_values": {
                "type": "array",
                "items": {"type": "string", "minLength": 1},
            },
        },
        ["json_pointer", "observed_values"],
    )
    case_trace_step = closed_object(
        {
            "trace_step_ordinal": {"type": "integer", "minimum": 1, "maximum": 4},
            "case_rule_id": {"type": "string", "enum": case_rule_ids},
            "predicate_id": {"type": "string", "enum": case_predicate_ids},
            "predicate_result": {"type": "boolean"},
            "input_observations": {
                "type": "array",
                "minItems": 1,
                "items": {"$ref": "#/$defs/caseInputObservation"},
            },
        },
        [
            "trace_step_ordinal",
            "case_rule_id",
            "predicate_id",
            "predicate_result",
            "input_observations",
        ],
        allOf=[
            conditional_mapping(
                "trace_step_ordinal",
                ordinal,
                {"case_rule_id": rule_id, "predicate_id": predicate_id},
            )
            for ordinal, rule_id, predicate_id, _, _ in CASE_RULES
        ],
    )
    structural_reason = closed_object(
        {
            "reason_code": {"type": "string", "enum": reason_codes},
            "matched_input_references": {
                "type": "array",
                "minItems": 1,
                "items": {"$ref": "#/$defs/caseInputObservation"},
            },
        },
        ["reason_code", "matched_input_references"],
    )
    case_selection = closed_object(
        {
            "case_category": {"type": "string", "enum": case_categories},
            "case_rule_id": {"type": "string", "enum": case_rule_ids},
            "predicate_trace": {
                "type": "array",
                "minItems": 4,
                "maxItems": 4,
                "items": {"$ref": "#/$defs/caseTraceStep"},
            },
            "structural_reason": {"$ref": "#/$defs/structuralReason"},
            "selection_method_id": {
                "type": "string",
                "const": SELECTION_METHOD_ID,
            },
            "selection_token_sha256": deepcopy(sha256_schema),
        },
        [
            "case_category",
            "case_rule_id",
            "predicate_trace",
            "structural_reason",
            "selection_method_id",
            "selection_token_sha256",
        ],
        allOf=[
            {
                "if": {
                    "properties": {"case_rule_id": {"const": rule_id}},
                    "required": ["case_rule_id"],
                },
                "then": {
                    "properties": {
                        "case_category": {"const": category},
                        "structural_reason": {
                            "properties": {
                                "reason_code": {"const": reason_code}
                            }
                        },
                    }
                },
            }
            for _, rule_id, _, category, reason_code in CASE_RULES
        ],
    )

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": SCHEMA_ID,
        "title": "Case Study Selection schema v0.1",
        "description": (
            "Closed non-ordinal structural contract for deterministic selection "
            "of representative presentation case patterns."
        ),
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "EnsemblID": {"type": "string", "pattern": "^ENSG[0-9]+\\.[0-9]+$"},
            "universe_ordinal": {"type": "integer", "minimum": 1},
            "case_selection_id": {
                "type": "string",
                "pattern": "^CASESEL_[A-F0-9]{32}$",
            },
            "case_selection_schema_version": {
                "type": "string",
                "const": SCHEMA_VERSION,
            },
            "case_selection_framework_version": {
                "type": "string",
                "const": FRAMEWORK_VERSION,
            },
            "case_rule_catalog_version": {
                "type": "string",
                "const": RULE_CATALOG_VERSION,
            },
            "case_selector_version": {"type": "string", "minLength": 1},
            "source_prioritization_identity": {
                "$ref": "#/$defs/sourcePrioritizationIdentity"
            },
            "source_prioritization_rule_trace": {
                "type": "array",
                "minItems": 4,
                "maxItems": 4,
                "items": {"$ref": "#/$defs/sourceTraceStep"},
            },
            "component_state_snapshot": {
                "type": "array",
                "minItems": 1,
                "items": {"$ref": "#/$defs/componentStateSnapshot"},
            },
            "limitation_identifiers": {
                "type": "array",
                "uniqueItems": True,
                "items": {"type": "string", "pattern": "^LIM_[A-Z0-9_]+$"},
            },
            "case_selection": {"$ref": "#/$defs/caseSelection"},
        },
        "required": [
            "EnsemblID",
            "universe_ordinal",
            "case_selection_id",
            "case_selection_schema_version",
            "case_selection_framework_version",
            "case_rule_catalog_version",
            "case_selector_version",
            "source_prioritization_identity",
            "source_prioritization_rule_trace",
            "component_state_snapshot",
            "limitation_identifiers",
            "case_selection",
        ],
        "$defs": {
            "caseInputObservation": case_input_observation,
            "caseSelection": case_selection,
            "caseTraceStep": case_trace_step,
            "componentStateSnapshot": component_snapshot,
            "sourceInputObservation": source_input_observation,
            "sourcePrioritizationIdentity": source_prioritization_identity,
            "sourceSummaryIdentity": source_summary_identity,
            "sourceTraceStep": source_trace_step,
            "structuralReason": structural_reason,
        },
        "$comment": (
            "The contract prohibits target optimization, ordering, scoring, "
            "recommendation, target-quality or evidence-strength claims."
        ),
    }


def evaluate_case_rules(
    components: list[dict[str, Any]], root_limitations: list[str]
) -> list[bool]:
    if not components:
        fail("Case rule evaluator received an empty component snapshot")
    states = [item["component_state"] for item in components]
    if any(state not in COMPONENT_STATES for state in states):
        fail("Case rule evaluator received an uncontrolled component state")
    complete = all(state == "OBSERVED" for state in states)
    partial = (
        not any(state == "CONFLICTING" for state in states)
        and (
            any(state == "PARTIAL" for state in states)
            or (
                any(state == "OBSERVED" for state in states)
                and any(state in {"MISSING", "NOT_QUERIED"} for state in states)
            )
        )
    )
    conflict = any(state == "CONFLICTING" for state in states)
    limitation = bool(root_limitations) or any(
        item["limitation_identifiers"] for item in components
    )
    return [complete, partial, conflict, limitation]


def case_observations(
    components: list[dict[str, Any]], root_limitations: list[str]
) -> list[dict[str, Any]]:
    observations = [
        {
            "json_pointer": f"/component_state_snapshot/{index}/component_state",
            "observed_values": [item["component_state"]],
        }
        for index, item in enumerate(components)
    ]
    observations.append(
        {
            "json_pointer": "/limitation_identifiers",
            "observed_values": list(root_limitations),
        }
    )
    observations.extend(
        {
            "json_pointer": (
                f"/component_state_snapshot/{index}/limitation_identifiers"
            ),
            "observed_values": list(item["limitation_identifiers"]),
        }
        for index, item in enumerate(components)
    )
    return observations


def synthetic_case(
    states: list[str],
    root_limitations: list[str],
    component_limitations: list[list[str]],
    selected_category: str,
    source_rules: Any,
) -> dict[str, Any]:
    source = source_rules.synthetic_assignment(states)
    components = deepcopy(source["component_state_snapshot"])
    for component, limitations in zip(components, component_limitations, strict=True):
        component["limitation_identifiers"] = list(limitations)
    results = evaluate_case_rules(components, root_limitations)
    selected_indices = [
        index for index, rule in enumerate(CASE_RULES) if rule[3] == selected_category
    ]
    if len(selected_indices) != 1 or not results[selected_indices[0]]:
        fail(f"Synthetic fixture is not eligible for {selected_category}")
    selected = CASE_RULES[selected_indices[0]]
    observations = case_observations(components, root_limitations)
    source_hash = "b" * 64
    token_input = [
        FRAMEWORK_VERSION,
        selected_category,
        source["EnsemblID"],
        source["prioritization_representation_id"],
        source_hash,
    ]
    token = sha256_bytes(canonical_json(token_input).encode("utf-8"))
    identity = [
        source["EnsemblID"],
        SCHEMA_VERSION,
        FRAMEWORK_VERSION,
        selected_category,
        source["prioritization_representation_id"],
        RULE_CATALOG_VERSION,
    ]
    return {
        "EnsemblID": source["EnsemblID"],
        "universe_ordinal": source["universe_ordinal"],
        "case_selection_id": stable_id("CASESEL", identity),
        "case_selection_schema_version": SCHEMA_VERSION,
        "case_selection_framework_version": FRAMEWORK_VERSION,
        "case_rule_catalog_version": RULE_CATALOG_VERSION,
        "case_selector_version": "SYNTHETIC_CASE_SELECTOR_V0.1",
        "source_prioritization_identity": {
            "prioritization_representation_id": source[
                "prioritization_representation_id"
            ],
            "prioritization_output_schema_version": source[
                "prioritization_output_schema_version"
            ],
            "prioritization_representation_version": source[
                "prioritization_representation_version"
            ],
            "prioritization_rule_catalog_version": source[
                "rule_catalog_version"
            ],
            "prioritization_content_sha256": source_hash,
            "source_category": source["category_assignment"]["category"],
            "source_assigned_rule_id": source["category_assignment"][
                "assigned_rule_id"
            ],
            "source_summary_identity": deepcopy(source["source_summary_identity"]),
        },
        "source_prioritization_rule_trace": deepcopy(
            source["category_assignment"]["rule_trace"]
        ),
        "component_state_snapshot": components,
        "limitation_identifiers": list(root_limitations),
        "case_selection": {
            "case_category": selected[3],
            "case_rule_id": selected[1],
            "predicate_trace": [
                {
                    "trace_step_ordinal": ordinal,
                    "case_rule_id": rule_id,
                    "predicate_id": predicate_id,
                    "predicate_result": result,
                    "input_observations": deepcopy(observations),
                }
                for (ordinal, rule_id, predicate_id, _, _), result in zip(
                    CASE_RULES, results, strict=True
                )
            ],
            "structural_reason": {
                "reason_code": selected[4],
                "matched_input_references": deepcopy(observations),
            },
            "selection_method_id": SELECTION_METHOD_ID,
            "selection_token_sha256": token,
        },
    }


def validate_case_semantics(value: dict[str, Any], source_rules: Any) -> None:
    source_proxy = {
        "component_state_snapshot": value["component_state_snapshot"],
        "category_assignment": {
            "category": value["source_prioritization_identity"]["source_category"],
            "assigned_rule_id": value["source_prioritization_identity"][
                "source_assigned_rule_id"
            ],
            "rule_trace": value["source_prioritization_rule_trace"],
        },
    }
    source_rules.validate_assignment_semantics(source_proxy)
    components = value["component_state_snapshot"]
    limitations = value["limitation_identifiers"]
    expected_results = evaluate_case_rules(components, limitations)
    expected_observations = case_observations(components, limitations)
    trace = value["case_selection"]["predicate_trace"]
    if len(trace) != len(CASE_RULES):
        fail("Case predicate trace is incomplete")
    for step, rule, result in zip(trace, CASE_RULES, expected_results, strict=True):
        ordinal, rule_id, predicate_id, _, _ = rule
        if (
            step["trace_step_ordinal"] != ordinal
            or step["case_rule_id"] != rule_id
            or step["predicate_id"] != predicate_id
            or step["predicate_result"] is not result
            or step["input_observations"] != expected_observations
        ):
            fail("Case predicate trace does not reproduce the frozen catalog")
    selection = value["case_selection"]
    selected_rules = [rule for rule in CASE_RULES if rule[1] == selection["case_rule_id"]]
    if len(selected_rules) != 1:
        fail("Selected case rule is uncontrolled")
    selected = selected_rules[0]
    if not expected_results[selected[0] - 1]:
        fail("Selected case rule predicate is false")
    if (
        selection["case_category"] != selected[3]
        or selection["structural_reason"]["reason_code"] != selected[4]
        or selection["structural_reason"]["matched_input_references"]
        != expected_observations
    ):
        fail("Case category or structural reason does not match selected rule")
    source_identity = value["source_prioritization_identity"]
    token_input = [
        FRAMEWORK_VERSION,
        selection["case_category"],
        value["EnsemblID"],
        source_identity["prioritization_representation_id"],
        source_identity["prioritization_content_sha256"],
    ]
    expected_token = sha256_bytes(canonical_json(token_input).encode("utf-8"))
    if selection["selection_token_sha256"] != expected_token:
        fail("Deterministic case-selection token changed")


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


def expect_schema_rejected(
    instance: dict[str, Any], schema: dict[str, Any], validator: Any, label: str
) -> None:
    try:
        validator.validate_instance(instance, schema, schema)
    except RuntimeError:
        return
    fail(f"Invalid schema fixture was accepted: {label}")


def expect_semantics_rejected(
    instance: dict[str, Any], source_rules: Any, label: str
) -> None:
    try:
        validate_case_semantics(instance, source_rules)
    except RuntimeError:
        return
    fail(f"Invalid semantic fixture was accepted: {label}")


def validate_fixtures(schema: dict[str, Any], validator: Any, source_rules: Any) -> int:
    fixtures = [
        synthetic_case(
            ["OBSERVED", "OBSERVED"], [], [[], []], "CASE_COMPLETE_PATTERN", source_rules
        ),
        synthetic_case(
            ["OBSERVED", "PARTIAL"], [], [[], []], "CASE_PARTIAL_PATTERN", source_rules
        ),
        synthetic_case(
            ["OBSERVED", "MISSING"], [], [[], []], "CASE_PARTIAL_PATTERN", source_rules
        ),
        synthetic_case(
            ["OBSERVED", "CONFLICTING"], [], [[], []], "CASE_CONFLICT_PATTERN", source_rules
        ),
        synthetic_case(
            ["OBSERVED", "OBSERVED"],
            ["LIM_SYNTHETIC_ROOT"],
            [[], []],
            "CASE_LIMITATION_PATTERN",
            source_rules,
        ),
    ]
    tests = 0
    for fixture in fixtures:
        validator.validate_instance(fixture, schema, schema)
        validate_case_semantics(fixture, source_rules)
        assert_no_prohibited_fields(fixture)
        tests += 1

    overlap_results = evaluate_case_rules(
        fixtures[-1]["component_state_snapshot"], fixtures[-1]["limitation_identifiers"]
    )
    if overlap_results != [True, False, False, True]:
        fail("Complete/limitation overlap fixture changed")
    tests += 1

    for field in sorted(PROHIBITED_FIELDS):
        candidate = deepcopy(fixtures[0])
        candidate[field] = "PROHIBITED"
        expect_schema_rejected(candidate, schema, validator, f"root prohibited field {field}")
        candidate = deepcopy(fixtures[0])
        candidate["case_selection"][field] = "PROHIBITED"
        expect_schema_rejected(candidate, schema, validator, f"nested prohibited field {field}")
        tests += 2

    candidate = deepcopy(fixtures[0])
    candidate["case_selection"]["case_rule_id"] = CASE_RULES[1][1]
    expect_schema_rejected(candidate, schema, validator, "wrong rule/category mapping")
    tests += 1
    candidate = deepcopy(fixtures[0])
    candidate["case_selection"]["predicate_trace"] = candidate["case_selection"][
        "predicate_trace"
    ][:3]
    expect_schema_rejected(candidate, schema, validator, "incomplete predicate trace")
    tests += 1
    candidate = deepcopy(fixtures[0])
    candidate["case_selection"]["predicate_trace"][0], candidate["case_selection"][
        "predicate_trace"
    ][1] = (
        candidate["case_selection"]["predicate_trace"][1],
        candidate["case_selection"]["predicate_trace"][0],
    )
    expect_semantics_rejected(candidate, source_rules, "reordered predicate trace")
    tests += 1
    candidate = deepcopy(fixtures[0])
    candidate["source_prioritization_rule_trace"][0]["predicate_result"] = True
    expect_semantics_rejected(candidate, source_rules, "changed source rule trace")
    tests += 1
    candidate = deepcopy(fixtures[0])
    candidate["case_selection"]["selection_token_sha256"] = "0" * 64
    expect_semantics_rejected(candidate, source_rules, "changed deterministic token")
    tests += 1
    return tests


def validate_markdown_links() -> int:
    pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    checked = 0
    for relative_path in sorted(NEW_DOCUMENTS):
        path = ROOT / relative_path
        if not path.is_file():
            fail(f"Task #036A governance document missing: {relative_path}")
        for target in pattern.findall(path.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "#")):
                continue
            resolved = (path.parent / target.split("#", 1)[0]).resolve()
            if not resolved.exists():
                fail(f"Broken Markdown link in {relative_path}: {target}")
            checked += 1
    return checked


def validate_document_terminology() -> None:
    combined = "\n".join(
        (ROOT / relative_path).read_text(encoding="utf-8")
        for relative_path in sorted(NEW_DOCUMENTS)
    )
    required = {
        SCHEMA_VERSION,
        FRAMEWORK_VERSION,
        RULE_CATALOG_VERSION,
        SOURCE_PRIORITIZATION_SCHEMA_VERSION,
        SOURCE_PRIORITIZATION_VERSION,
        *(item[1] for item in CASE_RULES),
        *(item[3] for item in CASE_RULES),
        "source prioritization",
        "source Evidence Summary",
        "predicate trace",
        "structural_reason",
        "non-ordinal",
    }
    missing = sorted(token for token in required if token not in combined)
    if missing:
        fail(f"Task #036A governance terminology is incomplete: {missing}")


def main() -> None:
    validate_working_tree_scope()
    frozen_before = validate_frozen_inputs()
    validate_document_terminology()
    source_rules = load_source_rules()
    validator = source_rules.load_source_validator()

    schema_first = build_schema()
    schema_second = build_schema()
    bytes_first = pretty_json_bytes(schema_first)
    bytes_second = pretty_json_bytes(schema_second)
    if bytes_first != bytes_second:
        fail("Case-selection schema regeneration is not byte-identical")
    if schema_first.get("$id") != SCHEMA_ID:
        fail("Case-selection schema identity mismatch")
    closed_objects = validator.assert_closed_objects(schema_first)
    assert_no_prohibited_schema_fields(schema_first)
    fixture_tests = validate_fixtures(schema_first, validator, source_rules)

    SCHEMA_PATH.parent.mkdir(parents=True, exist_ok=True)
    if SCHEMA_PATH.exists() and SCHEMA_PATH.read_bytes() != bytes_first:
        fail("Existing Task #036A schema differs from deterministic regeneration")
    SCHEMA_PATH.write_bytes(bytes_first)
    if SCHEMA_PATH.read_bytes() != bytes_second:
        fail("Written case-selection schema differs from independent regeneration")
    markdown_links = validate_markdown_links()

    if frozen_before != validate_frozen_inputs():
        fail("A frozen previous artifact changed during Task #036A")
    validate_working_tree_scope()

    print("TASK_036A_VALIDATION=PASS")
    print(f"schema_version={SCHEMA_VERSION}")
    print(f"framework_version={FRAMEWORK_VERSION}")
    print(f"rule_catalog_version={RULE_CATALOG_VERSION}")
    print(f"schema_sha256={sha256_bytes(bytes_first)}")
    print(f"schema_size_bytes={len(bytes_first)}")
    print(f"controlled_case_categories={len(CASE_RULES)}")
    print(f"controlled_case_rules={len(CASE_RULES)}")
    print(f"closed_object_schemas={closed_objects}")
    print(f"boundary_fixture_tests={fixture_tests}")
    print(f"resolved_markdown_links={markdown_links}")
    print("frozen_previous_artifacts=UNCHANGED")
    print("case_selections_generated=0")
    print("target_ranking=NOT_PERFORMED")
    print("network_access=PROHIBITED_NOT_USED")
    print("runtime_ai_decisions=PROHIBITED_NONE_USED")


if __name__ == "__main__":
    main()
