#!/usr/bin/env python3
"""Define and validate Transparent Prioritization Prototype schema v0.1.

Task #035A creates governance and a categorical trace schema only. It does not
materialize target assignments, score or rank targets, select or recommend
targets, retrieve evidence, modify Evidence Summaries, interpret biology, or
use runtime AI/LLM decisions.
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
SCHEMA_PATH = ROOT / "schemas/prioritization_output_schema_v0.1.json"
SOURCE_VALIDATOR_PATH = ROOT / "analysis/34A_define_evidence_summary_schema.py"

TASK_ID = "TASK_035A"
SCHEMA_VERSION = "PRIORITIZATION_OUTPUT_SCHEMA_V0.1"
REPRESENTATION_VERSION = "TRANSPARENT_PRIORITIZATION_PROTOTYPE_V0.1"
RULE_CATALOG_VERSION = "PRIORITIZATION_RULE_CATALOG_V0.1"
GENERATOR_VERSION = "TRANSPARENT_PRIORITIZATION_SCHEMA_GENERATOR_V0.1"
SCHEMA_ID = "urn:luad-target-dossier:prioritization-output-schema:v0.1"
SOURCE_SUMMARY_SCHEMA_VERSION = "EVIDENCE_SUMMARY_SCHEMA_V0.1"
SOURCE_SUMMARY_VERSION = "EVIDENCE_AGGREGATION_REPRESENTATION_V0.1"

COMPONENT_STATES = ["OBSERVED", "PARTIAL", "CONFLICTING", "MISSING", "NOT_QUERIED"]
CATEGORIES = ["CATEGORY_A", "CATEGORY_B", "CATEGORY_C", "CATEGORY_UNASSIGNED"]
RULES = [
    (
        1,
        "PRULE_035A_001_PARTIAL_OR_CONFLICTING",
        "PPRED_ANY_PARTIAL_OR_CONFLICTING_V0.1",
        "CATEGORY_C",
    ),
    (
        2,
        "PRULE_035A_002_ALL_OBSERVED",
        "PPRED_ALL_COMPONENTS_OBSERVED_V0.1",
        "CATEGORY_A",
    ),
    (
        3,
        "PRULE_035A_003_MIXED_OBSERVED_UNAVAILABLE",
        "PPRED_MIXED_OBSERVED_AND_UNAVAILABLE_V0.1",
        "CATEGORY_B",
    ),
    (
        4,
        "PRULE_035A_004_ALL_UNAVAILABLE",
        "PPRED_ALL_COMPONENTS_UNAVAILABLE_V0.1",
        "CATEGORY_UNASSIGNED",
    ),
]
PROHIBITED_FIELDS = {
    "score",
    "ranking",
    "rank",
    "priority_score",
    "confidence",
    "probability",
    "success_prediction",
    "recommendation",
    "target_quality",
    "evidence_strength",
}

FROZEN_INPUT_SHA256 = {
    "analysis/34A_define_evidence_summary_schema.py": "0f401e377f40d1355b4bdba2ad197b5c405d906e02a2822c948addfefca5dec0",
    "docs/governance/evidence_aggregation_representation_specification_v0.1.md": "47bb0621b23090db5bb5f90f8a9c87ec56785e31957089c02573f1e1def40274",
    "docs/governance/evidence_summary_component_policy_v0.1.md": "c6e81a704060021baa951e25b78d1a2b355a656f824b27d6656e8af568049ee1",
    "docs/governance/evidence_summary_dependency_policy_v0.1.md": "efb423fc6ef1c918accdf70b6f38e10fd6c79e5c2455aca5ed0fb539d682d974",
    "docs/governance/evidence_summary_validation_requirements_v0.1.md": "e51e34743943cfc168572856fa5b1bf991261f899ced6b56057a9245f7f09c02",
    "schemas/evidence_summary_schema_v0.1.json": "0942733644e1333247293ca83f2eb14c13640939edf3727ea74d19d33990b366",
    "analysis/34B_materialize_evidence_summary.py": "2b24b79c46100b919243e8978d7c29a96ec2f20428f2153c29c0573f6af47685",
    "outputs/evidence_summary_v0.1/summary_manifest.json": "02b9a893569bd01257cb0108121f61a78041e90ffd769ac7a1d163d24051e19f",
    "outputs/evidence_summary_v0.1/summary_index.csv": "27489b08061102c4d325bac7d4761682f8c7e811458b5cff88d4fec3b0bc17e5",
    "outputs/evidence_summary_v0.1/partition_manifest.csv": "fd9bd76ea5f940a0165a6a082538a810fc64cbcd8b0fe4ecda9f0aae14795202",
    "outputs/evidence_summary_v0.1/validation_report.md": "257662af9adf87ce7f913e2024b6e43db2685cc84a117f9424830b6308c034e8",
    "outputs/evidence_summary_v0.1/session_info.txt": "bd04e5a858f2c70e746954d2e99bdfd44e3d64f818261d31c393f20bed9bda44",
}

NEW_DOCUMENTS = {
    "docs/governance/prioritization_framework_specification_v0.1.md",
    "docs/governance/prioritization_rule_catalog_v0.1.md",
    "docs/governance/prioritization_validation_requirements_v0.1.md",
}
ALLOWED_WORKTREE_PATHS = {
    *NEW_DOCUMENTS,
    "analysis/35A_define_prioritization_schema.py",
    "schemas/prioritization_output_schema_v0.1.json",
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


def load_source_validator() -> Any:
    spec = importlib.util.spec_from_file_location("task34a_validator", SOURCE_VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        fail("Unable to load frozen Task #034A schema validator")
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


def build_schema() -> dict[str, Any]:
    sha256_schema = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
    rule_ids = [item[1] for item in RULES]
    predicate_ids = [item[2] for item in RULES]

    input_observation = closed_object(
        {
            "json_pointer": {
                "type": "string",
                "pattern": "^/component_state_snapshot/[0-9]+/component_state$",
            },
            "observed_value": {"type": "string", "enum": COMPONENT_STATES},
        },
        ["json_pointer", "observed_value"],
    )

    trace_step = closed_object(
        {
            "trace_step_ordinal": {"type": "integer", "minimum": 1, "maximum": 4},
            "rule_id": {"type": "string", "enum": rule_ids},
            "predicate_id": {"type": "string", "enum": predicate_ids},
            "predicate_result": {"type": "boolean"},
            "input_observations": {
                "type": "array",
                "minItems": 1,
                "items": {"$ref": "#/$defs/inputObservation"},
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
            {
                "if": {
                    "properties": {"trace_step_ordinal": {"const": ordinal}},
                    "required": ["trace_step_ordinal"],
                },
                "then": {
                    "properties": {
                        "rule_id": {"const": rule_id},
                        "predicate_id": {"const": predicate_id},
                    }
                },
            }
            for ordinal, rule_id, predicate_id, _ in RULES
        ],
    )

    category_assignment = closed_object(
        {
            "category": {"type": "string", "enum": CATEGORIES},
            "assigned_rule_id": {"type": "string", "enum": rule_ids},
            "rule_trace": {
                "type": "array",
                "minItems": 4,
                "maxItems": 4,
                "items": {"$ref": "#/$defs/ruleTraceStep"},
            },
        },
        ["category", "assigned_rule_id", "rule_trace"],
        allOf=[
            {
                "if": {
                    "properties": {"assigned_rule_id": {"const": rule_id}},
                    "required": ["assigned_rule_id"],
                },
                "then": {"properties": {"category": {"const": category}}},
            }
            for _, rule_id, _, category in RULES
        ],
    )

    component_state_snapshot = closed_object(
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

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": SCHEMA_ID,
        "title": "Transparent Prioritization Prototype output schema v0.1",
        "description": (
            "Closed categorical rule-trace representation derived from one frozen "
            "Evidence Summary; categories are explicitly non-ordinal."
        ),
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "EnsemblID": {"type": "string", "pattern": "^ENSG[0-9]+\\.[0-9]+$"},
            "universe_ordinal": {"type": "integer", "minimum": 1},
            "prioritization_representation_id": {
                "type": "string",
                "pattern": "^PRZ_[A-F0-9]{32}$",
            },
            "prioritization_output_schema_version": {
                "type": "string",
                "const": SCHEMA_VERSION,
            },
            "prioritization_representation_version": {
                "type": "string",
                "const": REPRESENTATION_VERSION,
            },
            "rule_catalog_version": {"type": "string", "const": RULE_CATALOG_VERSION},
            "prioritization_generator_version": {"type": "string", "minLength": 1},
            "source_summary_identity": {"$ref": "#/$defs/sourceSummaryIdentity"},
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
            "category_assignment": {"$ref": "#/$defs/categoryAssignment"},
        },
        "required": [
            "EnsemblID",
            "universe_ordinal",
            "prioritization_representation_id",
            "prioritization_output_schema_version",
            "prioritization_representation_version",
            "rule_catalog_version",
            "prioritization_generator_version",
            "source_summary_identity",
            "component_state_snapshot",
            "limitation_identifiers",
            "category_assignment",
        ],
        "$defs": {
            "categoryAssignment": category_assignment,
            "componentStateSnapshot": component_state_snapshot,
            "inputObservation": input_observation,
            "ruleTraceStep": trace_step,
            "sourceSummaryIdentity": source_summary_identity,
        },
        "$comment": (
            "The schema prohibits numeric scoring, target ordering, confidence or "
            "probability estimation, success prediction, recommendation, target "
            "quality, and evidence strength."
        ),
    }


def evaluate_rules(states: list[str]) -> list[bool]:
    if not states or any(state not in COMPONENT_STATES for state in states):
        fail("Rule evaluator received an empty or uncontrolled component-state snapshot")
    partial_or_conflicting = any(state in {"PARTIAL", "CONFLICTING"} for state in states)
    all_observed = all(state == "OBSERVED" for state in states)
    mixed = (
        not partial_or_conflicting
        and any(state == "OBSERVED" for state in states)
        and any(state in {"MISSING", "NOT_QUERIED"} for state in states)
    )
    all_unavailable = all(state in {"MISSING", "NOT_QUERIED"} for state in states)
    return [partial_or_conflicting, all_observed, mixed, all_unavailable]


def synthetic_assignment(states: list[str]) -> dict[str, Any]:
    results = evaluate_rules(states)
    true_indices = [index for index, result in enumerate(results) if result]
    if len(true_indices) != 1:
        fail("Synthetic rule fixture did not resolve exactly one category")
    true_index = true_indices[0]
    assigned_rule = RULES[true_index]
    observations = [
        {
            "json_pointer": f"/component_state_snapshot/{index}/component_state",
            "observed_value": state,
        }
        for index, state in enumerate(states)
    ]
    components = [
        {
            "component_id": f"COMP_SYNTHETIC_{index + 1}",
            "component_version": f"COMP_SYNTHETIC_{index + 1}_V0.1",
            "component_state": state,
            "source_component_record_id": f"CMPREC_SYNTHETIC_{index + 1}",
            "limitation_identifiers": [],
        }
        for index, state in enumerate(states)
    ]
    return {
        "EnsemblID": "ENSG00000000000.1",
        "universe_ordinal": 1,
        "prioritization_representation_id": "PRZ_0123456789ABCDEF0123456789ABCDEF",
        "prioritization_output_schema_version": SCHEMA_VERSION,
        "prioritization_representation_version": REPRESENTATION_VERSION,
        "rule_catalog_version": RULE_CATALOG_VERSION,
        "prioritization_generator_version": "SYNTHETIC_BOUNDARY_FIXTURE_V0.1",
        "source_summary_identity": {
            "evidence_summary_id": "SUM_0123456789ABCDEF0123456789ABCDEF",
            "evidence_summary_schema_version": SOURCE_SUMMARY_SCHEMA_VERSION,
            "evidence_summary_version": SOURCE_SUMMARY_VERSION,
            "evidence_summary_content_sha256": "a" * 64,
            "source_landscape_id": "LND_SYNTHETIC_FIXTURE",
            "source_evidence_snapshot_version": "EVIDENCE_SNAPSHOT_SYNTHETIC_FIXTURE",
        },
        "component_state_snapshot": components,
        "limitation_identifiers": ["LIM_SYNTHETIC_FIXTURE"],
        "category_assignment": {
            "category": assigned_rule[3],
            "assigned_rule_id": assigned_rule[1],
            "rule_trace": [
                {
                    "trace_step_ordinal": ordinal,
                    "rule_id": rule_id,
                    "predicate_id": predicate_id,
                    "predicate_result": result,
                    "input_observations": deepcopy(observations),
                }
                for (ordinal, rule_id, predicate_id, _), result in zip(
                    RULES, results, strict=True
                )
            ],
        },
    }


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


def validate_assignment_semantics(value: dict[str, Any]) -> None:
    components = value["component_state_snapshot"]
    if not components:
        fail("Component-state snapshot is empty")
    component_ids = [item["component_id"] for item in components]
    if len(component_ids) != len(set(component_ids)):
        fail("Component-state snapshot contains duplicate component IDs")
    states = [item["component_state"] for item in components]
    expected_results = evaluate_rules(states)
    trace = value["category_assignment"]["rule_trace"]
    if len(trace) != len(RULES):
        fail("Rule trace is incomplete")
    expected_observations = [
        {
            "json_pointer": f"/component_state_snapshot/{index}/component_state",
            "observed_value": state,
        }
        for index, state in enumerate(states)
    ]
    for step, expected_rule, expected_result in zip(
        trace, RULES, expected_results, strict=True
    ):
        ordinal, rule_id, predicate_id, _ = expected_rule
        if (
            step["trace_step_ordinal"] != ordinal
            or step["rule_id"] != rule_id
            or step["predicate_id"] != predicate_id
            or step["predicate_result"] is not expected_result
            or step["input_observations"] != expected_observations
        ):
            fail("Rule trace does not reproduce the frozen catalog")
    true_rules = [rule for rule, result in zip(RULES, expected_results, strict=True) if result]
    if len(true_rules) != 1:
        fail("Rule catalog did not produce exactly one true predicate")
    assigned = value["category_assignment"]
    if assigned["assigned_rule_id"] != true_rules[0][1] or assigned["category"] != true_rules[0][3]:
        fail("Assigned category does not match the single true rule")


def expect_schema_rejected(
    instance: dict[str, Any], schema: dict[str, Any], validator: Any, label: str
) -> None:
    try:
        validator.validate_instance(instance, schema, schema)
    except RuntimeError:
        return
    fail(f"Invalid schema boundary fixture was accepted: {label}")


def expect_semantics_rejected(instance: dict[str, Any], label: str) -> None:
    try:
        validate_assignment_semantics(instance)
    except RuntimeError:
        return
    fail(f"Invalid semantic boundary fixture was accepted: {label}")


def validate_fixtures(schema: dict[str, Any], validator: Any) -> int:
    patterns = {
        "CATEGORY_A": ["OBSERVED", "OBSERVED"],
        "CATEGORY_B": ["OBSERVED", "MISSING"],
        "CATEGORY_C": ["PARTIAL", "OBSERVED"],
        "CATEGORY_UNASSIGNED": ["MISSING", "NOT_QUERIED"],
    }
    fixtures: list[dict[str, Any]] = []
    tests = 0
    for category, states in patterns.items():
        fixture = synthetic_assignment(states)
        if fixture["category_assignment"]["category"] != category:
            fail(f"Category fixture mapping changed: {category}")
        validator.validate_instance(fixture, schema, schema)
        validate_assignment_semantics(fixture)
        assert_no_prohibited_fields(fixture)
        fixtures.append(fixture)
        tests += 1

    conflict_fixture = synthetic_assignment(["CONFLICTING", "MISSING"])
    validator.validate_instance(conflict_fixture, schema, schema)
    validate_assignment_semantics(conflict_fixture)
    tests += 1

    for field in sorted(PROHIBITED_FIELDS):
        candidate = deepcopy(fixtures[0])
        candidate[field] = "PROHIBITED"
        expect_schema_rejected(candidate, schema, validator, f"root prohibited field {field}")
        candidate = deepcopy(fixtures[0])
        candidate["category_assignment"][field] = "PROHIBITED"
        expect_schema_rejected(candidate, schema, validator, f"nested prohibited field {field}")
        tests += 2

    candidate = deepcopy(fixtures[0])
    candidate["category_assignment"]["category"] = "CATEGORY_B"
    expect_schema_rejected(candidate, schema, validator, "wrong category/rule mapping")
    tests += 1
    candidate = deepcopy(fixtures[0])
    candidate["category_assignment"]["rule_trace"] = candidate[
        "category_assignment"
    ]["rule_trace"][:3]
    expect_schema_rejected(candidate, schema, validator, "incomplete trace")
    tests += 1
    candidate = deepcopy(fixtures[0])
    candidate["category_assignment"]["rule_trace"][0], candidate[
        "category_assignment"
    ]["rule_trace"][1] = (
        candidate["category_assignment"]["rule_trace"][1],
        candidate["category_assignment"]["rule_trace"][0],
    )
    expect_semantics_rejected(candidate, "reordered trace")
    tests += 1
    candidate = deepcopy(fixtures[0])
    for step in candidate["category_assignment"]["rule_trace"]:
        step["predicate_result"] = False
    expect_semantics_rejected(candidate, "zero true predicates")
    tests += 1
    candidate = deepcopy(fixtures[0])
    candidate["category_assignment"]["rule_trace"][0]["predicate_result"] = True
    expect_semantics_rejected(candidate, "multiple asserted predicates")
    tests += 1
    candidate = deepcopy(fixtures[0])
    candidate["component_state_snapshot"][0]["component_state"] = "STRONG"
    expect_schema_rejected(candidate, schema, validator, "uncontrolled component state")
    tests += 1
    return tests


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


def validate_markdown_links() -> int:
    pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    checked = 0
    for relative_path in sorted(NEW_DOCUMENTS):
        path = ROOT / relative_path
        if not path.is_file():
            fail(f"Task #035A governance document missing: {relative_path}")
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
        REPRESENTATION_VERSION,
        RULE_CATALOG_VERSION,
        SOURCE_SUMMARY_SCHEMA_VERSION,
        SOURCE_SUMMARY_VERSION,
        *CATEGORIES,
        *(item[1] for item in RULES),
        "component_state",
        "limitation_identifiers",
        "rule trace",
        "non-ordinal",
    }
    missing = sorted(token for token in required if token not in combined)
    if missing:
        fail(f"Task #035A governance terminology is incomplete: {missing}")


def main() -> None:
    validate_working_tree_scope()
    frozen_before = validate_frozen_inputs()
    validate_document_terminology()

    schema_first = build_schema()
    schema_second = build_schema()
    bytes_first = pretty_json_bytes(schema_first)
    bytes_second = pretty_json_bytes(schema_second)
    if bytes_first != bytes_second:
        fail("Prioritization schema regeneration is not byte-identical")
    if schema_first.get("$id") != SCHEMA_ID:
        fail("Prioritization schema identity mismatch")
    validator = load_source_validator()
    closed_objects = validator.assert_closed_objects(schema_first)
    assert_no_prohibited_schema_fields(schema_first)
    fixture_tests = validate_fixtures(schema_first, validator)

    SCHEMA_PATH.parent.mkdir(parents=True, exist_ok=True)
    if SCHEMA_PATH.exists() and SCHEMA_PATH.read_bytes() != bytes_first:
        fail("Existing Task #035A schema differs from deterministic regeneration")
    SCHEMA_PATH.write_bytes(bytes_first)
    if SCHEMA_PATH.read_bytes() != bytes_second:
        fail("Written prioritization schema differs from independent regeneration")
    markdown_links = validate_markdown_links()

    if frozen_before != validate_frozen_inputs():
        fail("A frozen previous artifact changed during Task #035A")
    validate_working_tree_scope()

    print("TASK_035A_VALIDATION=PASS")
    print(f"schema_version={SCHEMA_VERSION}")
    print(f"representation_version={REPRESENTATION_VERSION}")
    print(f"rule_catalog_version={RULE_CATALOG_VERSION}")
    print(f"schema_sha256={sha256_bytes(bytes_first)}")
    print(f"schema_size_bytes={len(bytes_first)}")
    print(f"controlled_categories={len(CATEGORIES)}")
    print(f"controlled_rules={len(RULES)}")
    print(f"closed_object_schemas={closed_objects}")
    print(f"boundary_fixture_tests={fixture_tests}")
    print(f"resolved_markdown_links={markdown_links}")
    print("frozen_previous_artifacts=UNCHANGED")
    print("prioritization_outputs_generated=0")
    print("target_selection=NOT_PERFORMED")
    print("network_access=PROHIBITED_NOT_USED")
    print("runtime_ai_decisions=PROHIBITED_NONE_USED")


if __name__ == "__main__":
    main()

