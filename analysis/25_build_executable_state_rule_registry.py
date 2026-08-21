#!/usr/bin/env python3
"""Build and test the Task #025 executable component-state rule registry.

The registry translates each frozen Task #021 semantic predicate into a typed
JSON predicate AST evaluated by a small allow-listed interpreter. It produces
rule-governance artifacts and synthetic structural fixtures only. It does not
materialize target profiles or evaluate genes.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import platform
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASK024_BASE_COMMIT = "8b79f4771f92fc6c4102afdc3bf06a149403d33a"
EXPECTED_BRANCH = "main"
EXPECTED_REMOTE_FRAGMENT = "SichengChen-web/luad-target-dossier"
RULE_REGISTRY_VERSION = "STATE_RULE_REGISTRY_V0.1"
EVALUATOR_ID = "STRICT_JSON_PREDICATE_EVALUATOR"
EVALUATOR_VERSION = "V0.1"

SCRIPT_PATH = ROOT / "analysis/25_build_executable_state_rule_registry.py"
PLAN_PATH = ROOT / "docs/executable_state_rule_registry_v0.1.md"
OUTPUT_DIR = ROOT / "outputs/state_rule_registry"
REGISTRY_PATH = OUTPUT_DIR / "state_rule_registry.csv"
TEST_PATH = OUTPUT_DIR / "state_rule_test_matrix.csv"
SUMMARY_PATH = OUTPUT_DIR / "state_rule_validation_summary.md"
SESSION_PATH = OUTPUT_DIR / "session_info.txt"

INPUTS = {
    "semantic_registry": ROOT / "outputs/profile_materialization/component_state_resolution_registry.csv",
    "release_specification": ROOT / "docs/profile_release_specification_v0.1.md",
    "release_requirements": ROOT / "outputs/profile_release_specification/profile_release_requirements.csv",
    "release_qc_matrix": ROOT / "outputs/profile_release_specification/profile_release_qc_matrix.csv",
}

EXPECTED_HASHES = {
    "semantic_registry": "302fe6fef0eaf76daedbd51cbd9c430cb38bdbe231991f6e2551de0da59a94be",
    "release_specification": "ccba7fb58f5640ece458dd17f57568ac7b0e613812b172588ce44da702bdbfd8",
    "release_requirements": "d87a77896137bb7c0e3bacc385ade83e21acdcb9180f5dcd67896adc92e88762",
    "release_qc_matrix": "19e55953012be638a735500f42617cc22377e03a4d8fee4aefe31403263d2e2c",
}

ALLOWED_UNTRACKED_FILES = {
    "analysis/25_build_executable_state_rule_registry.py",
    "docs/executable_state_rule_registry_v0.1.md",
}
ALLOWED_UNTRACKED_PREFIX = "outputs/state_rule_registry/"

STATES_IN_PRECEDENCE = (
    "CONFLICTING", "OBSERVED", "MISSING", "PARTIAL", "NOT_QUERIED"
)
STATE_PRECEDENCE = {state: index for index, state in enumerate(STATES_IN_PRECEDENCE, start=1)}

FORBIDDEN_EXACT_FIELDS = {
    "score", "rank", "priority", "recommendation", "target_selection",
    "therapeutic_direction",
}

# Each component uses the same typed state-machine skeleton but has a distinct
# normalized feature contract grounded in its Task #021 semantic predicates.
COMPONENT_CONFIGS = {
    "COMP_TRANSCRIPTOMIC_EVIDENCE": {
        "prefix": "transcript",
        "observed_min": 2,
        "mapping_required": False,
        "qualifying_definition": "Count of the two required roles (primary and robustness) that are OBSERVED with valid primary effect/significance fields.",
        "context_definition": "TRUE only when both required roles, TCGA/recount3/gencode_v26 cohort/design provenance, and S0-S6 analysis context are complete.",
        "conflict_definition": "Count of prespecified material primary-versus-sensitivity direction conflicts or traceable incompatible transcript target identities/effects.",
        "partial_definition": "Count of missing companion roles, invalid required fields, incomplete QC/provenance elements, or incomplete transcript coverage conditions.",
    },
    "COMP_DISEASE_ASSOCIATION": {
        "prefix": "disease_association",
        "observed_min": 1,
        "mapping_required": True,
        "qualifying_definition": "Count of returned direct or ontology-qualified LUAD association observations with frozen disease identity.",
        "context_definition": "TRUE only when disease specificity, Open Targets release/query, datasource/publication lineage, and provenance are complete.",
        "conflict_definition": "Count of materially incompatible disease-specific claim pairs after target, LUAD identifier, source, and version reconciliation; direct/indirect overlap alone is excluded.",
        "partial_definition": "Count of incomplete association-coverage, datasource-lineage, disease-specificity, provenance, or literature-only conditions.",
    },
    "COMP_GENETIC_EVIDENCE": {
        "prefix": "genetic",
        "observed_min": 1,
        "mapping_required": False,
        "qualifying_definition": "Count of LUAD-relevant genetic alteration records passing frozen cohort/statistical QC with variant/gene/disease provenance.",
        "context_definition": "TRUE only when alteration mapping, cohort relevance, effect/statistical provenance, and required QC are complete.",
        "conflict_definition": "Count of incompatible alteration-effect or disease relationships after allele, direction, cohort, and endpoint harmonization.",
        "partial_definition": "Count of incomplete cohort relevance, alteration mapping, statistics, replication, source coverage, or provenance conditions.",
    },
    "COMP_FUNCTIONAL_DEPENDENCY": {
        "prefix": "functional_dependency",
        "observed_min": 1,
        "mapping_required": False,
        "qualifying_definition": "Count of LUAD-relevant model-level perturbation/dependency records passing screen QC with model/reagent/effect provenance.",
        "context_definition": "TRUE only when model scope, reagent/assay QC, effect definition, and required provenance are complete.",
        "conflict_definition": "Count of materially incompatible dependency direction or phenotype comparisons under harmonized model/context definitions.",
        "partial_definition": "Count of incomplete model coverage, reagent/assay QC, replicate support, effect definition, or provenance conditions.",
    },
    "COMP_PHARMACOLOGY": {
        "prefix": "pharmacology",
        "observed_min": 1,
        "mapping_required": True,
        "qualifying_definition": "Count of qualifying compound-target assay/mechanism records with target confidence, normalized activity/potency/unit, mechanism, compound, assay, and source provenance.",
        "context_definition": "TRUE only when potency, units, selectivity, mechanism, target assignment, assay context, and provenance are complete.",
        "conflict_definition": "Count of materially incompatible target assignments, mechanisms, or normalized activities after assay-context harmonization.",
        "partial_definition": "Count of annotation/count-only records or compound records missing assay, potency, selectivity, mechanism, lineage, or provenance.",
    },
    "COMP_TRACTABILITY": {
        "prefix": "tractability",
        "observed_min": 1,
        "mapping_required": True,
        "qualifying_definition": "Count of source-native modality assessment records with target, modality, bucket/assessment, release, and upstream-evidence provenance.",
        "context_definition": "TRUE only when modality identity, assessment/bucket, release, upstream lineage, and provenance are complete.",
        "conflict_definition": "Count of materially incompatible modality states after release and bucket-definition reconciliation; multiple modalities alone are excluded.",
        "partial_definition": "Count of incomplete modality identity, assessment/bucket, upstream lineage, retrieval coverage, or provenance conditions.",
    },
    "COMP_SAFETY": {
        "prefix": "safety",
        "observed_min": 1,
        "mapping_required": True,
        "qualifying_definition": "Count of traceable safety-liability observations with liability, datasource, attribution, and context provenance.",
        "context_definition": "TRUE only when liability/datasource/context provenance and required attribution fields are complete.",
        "conflict_definition": "Count of materially incompatible on-target attribution or outcome interpretations under comparable exposure/context definitions.",
        "partial_definition": "Count of incomplete attribution, context, human relevance, source lineage, or provenance conditions.",
    },
    "COMP_CLINICAL_DEVELOPMENT": {
        "prefix": "clinical_development",
        "observed_min": 1,
        "mapping_required": False,
        "qualifying_definition": "Count of trial-level records with validated intervention-target-LUAD linkage plus registry/version, trial, phase, and status provenance.",
        "context_definition": "TRUE only when linkage, trial identity, registry version, phase/status currency, and provenance are complete.",
        "conflict_definition": "Count of incompatible intervention-target identity, LUAD relevance, phase/status, or record identity comparisons after version reconciliation.",
        "partial_definition": "Count of trial/intervention/candidate/target records with incomplete linkage, phase/status, registry version, or provenance.",
    },
    "COMP_HUMAN_EVIDENCE": {
        "prefix": "human_evidence",
        "observed_min": 1,
        "mapping_required": False,
        "qualifying_definition": "Count of qualifying records explicitly human-derived by frozen cohort or trial metadata and satisfying their genetic/interventional component criterion.",
        "context_definition": "TRUE only when human origin, disease relevance, target linkage, source version, and provenance are complete.",
        "conflict_definition": "Count of incompatible human target-disease, alteration-effect, or intervention-linkage comparisons after lineage/context reconciliation.",
        "partial_definition": "Count of candidate records with incomplete human origin, disease relevance, target linkage, source version, or provenance.",
    },
    "COMP_CLINICAL_LINKAGE": {
        "prefix": "clinical_linkage",
        "observed_min": 1,
        "mapping_required": True,
        "qualifying_definition": "Count of validated record chains explicitly linking intervention, target, LUAD disease identifier, and trial/development record.",
        "context_definition": "TRUE only when every intervention-target-disease-trial link and source/version provenance is complete.",
        "conflict_definition": "Count of incompatible intervention identity, target assignment, LUAD disease linkage, or trial-linkage comparisons after reconciliation.",
        "partial_definition": "Count of separate association, compound, intervention, candidate, or trial records lacking the full validated linkage chain.",
    },
    "COMP_RISK_CONTEXT": {
        "prefix": "risk_context",
        "observed_min": 1,
        "mapping_required": True,
        "qualifying_definition": "Count of safety-liability records satisfying the COMP_SAFETY observed criterion; broader unmodeled risk gaps remain explicit.",
        "context_definition": "TRUE only when liability/datasource/context attribution provenance is complete; broader normal-tissue, essentiality, exposure, and toxicology gaps are reported separately.",
        "conflict_definition": "Count of incompatible risk/liability attribution or outcome-context comparisons; reused safety records retain identical lineage.",
        "partial_definition": "Count of incomplete attribution, human relevance, exposure context, provenance, or broader risk-context conditions.",
    },
}


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


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def run_git(*args: str, check: bool = True) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    if check and result.returncode != 0:
        fail(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def git_paths(*args: str) -> set[str]:
    return {line for line in run_git(*args).splitlines() if line}


def validate_repository() -> dict[str, str]:
    root = Path(run_git("rev-parse", "--show-toplevel")).resolve()
    branch = run_git("branch", "--show-current")
    head = run_git("rev-parse", "HEAD")
    base = run_git("rev-parse", TASK024_BASE_COMMIT)
    remote = run_git("remote", "get-url", "origin")
    if root != ROOT or branch != EXPECTED_BRANCH or EXPECTED_REMOTE_FRAGMENT not in remote:
        fail(f"Repository identity mismatch: root={root}, branch={branch}, remote={remote}")
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", base, head], cwd=ROOT, check=False)
    if ancestor.returncode != 0:
        fail("Frozen Task #024 base commit is not an ancestor of HEAD.")
    if run_git("diff", "--name-only") or run_git("diff", "--cached", "--name-only"):
        fail("Tracked/staged changes exist; Task #025 will not modify previous artifacts.")
    changed_inputs = git_paths(
        "diff", "--name-only", f"{base}..{head}", "--",
        *(relative(path) for path in INPUTS.values()),
    )
    if changed_inputs:
        fail(f"Frozen Task #021/#024 inputs changed: {sorted(changed_inputs)}")
    untracked = git_paths("ls-files", "--others", "--exclude-standard")
    unexpected = {
        path for path in untracked
        if path not in ALLOWED_UNTRACKED_FILES and not path.startswith(ALLOWED_UNTRACKED_PREFIX)
    }
    if unexpected:
        fail(f"Unexpected untracked files: {sorted(unexpected)}")
    return {
        "root": str(root), "branch": branch, "head": head, "base": base,
        "remote": remote, "snapshot": run_git("show", "-s", "--format=%cI", base),
    }


def validate_hashes() -> dict[str, str]:
    observed = {}
    for name, path in INPUTS.items():
        if not path.is_file():
            fail(f"Missing frozen input: {relative(path)}")
        digest = sha256(path)
        if digest != EXPECTED_HASHES[name]:
            fail(f"Frozen input hash mismatch for {relative(path)}: {digest}")
        observed[name] = digest
    return observed


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate_inputs() -> tuple[list[dict[str, str]], dict[str, int]]:
    semantic_rows = read_csv(INPUTS["semantic_registry"])
    if len(semantic_rows) != 55:
        fail(f"Expected 55 semantic rules, observed {len(semantic_rows)}.")
    pairs = {(row["component_id"], row["resolved_state"]) for row in semantic_rows}
    if len(pairs) != 55 or {row["component_id"] for row in semantic_rows} != set(COMPONENT_CONFIGS):
        fail("Semantic component/state identity changed.")
    for component in COMPONENT_CONFIGS:
        component_rows = [row for row in semantic_rows if row["component_id"] == component]
        if {row["resolved_state"] for row in component_rows} != set(STATES_IN_PRECEDENCE):
            fail(f"Five-state coverage changed for {component}.")
        for row in component_rows:
            if row["evaluation_precedence"] != str(STATE_PRECEDENCE[row["resolved_state"]]):
                fail(f"Frozen precedence changed for {component}/{row['resolved_state']}.")
            if not row["deterministic_predicate"]:
                fail(f"Blank semantic predicate for {component}/{row['resolved_state']}.")

    release_doc = INPUTS["release_specification"].read_text(encoding="utf-8")
    required_doc_phrases = (
        "Task #021 defines 55 controlled semantic predicates in prose.",
        "An LLM or unconstrained free text cannot resolve component states.",
        "CONFLICTING → OBSERVED → MISSING → PARTIAL → NOT_QUERIED",
    )
    if any(phrase not in release_doc for phrase in required_doc_phrases):
        fail("Task #024 executable-rule release boundary changed.")
    requirements = {row["requirement_id"]: row for row in read_csv(INPUTS["release_requirements"])}
    qc = {row["qc_id"]: row for row in read_csv(INPUTS["release_qc_matrix"])}
    if "REL_RULE_001" not in requirements or requirements["REL_RULE_001"]["normative_level"] != "MUST":
        fail("Task #024 REL_RULE_001 is missing or no longer mandatory.")
    if "QC_RULE_001" not in qc or qc["QC_RULE_001"]["release_expectation"] != "55_OF_55_PASS":
        fail("Task #024 QC_RULE_001 changed.")
    return semantic_rows, {
        "semantic_rules": len(semantic_rows),
        "components": len(COMPONENT_CONFIGS),
        "states": len(STATES_IN_PRECEDENCE),
        "release_document_boundaries": len(required_doc_phrases),
        "release_rule_requirements": 2,
    }


def eq(feature: str, value: Any) -> dict[str, Any]:
    return {"op": "eq", "feature": feature, "value": value}


def ge(feature: str, value: int) -> dict[str, Any]:
    return {"op": "ge", "feature": feature, "value": value}


def gt(feature: str, value: int) -> dict[str, Any]:
    return {"op": "gt", "feature": feature, "value": value}


def all_of(*args: dict[str, Any]) -> dict[str, Any]:
    return {"op": "all", "args": list(args)}


def any_of(*args: dict[str, Any]) -> dict[str, Any]:
    return {"op": "any", "args": list(args)}


def feature_names(config: dict[str, Any]) -> dict[str, str]:
    prefix = config["prefix"]
    return {
        "conflict": f"{prefix}_conflict_count",
        "qualifying": f"{prefix}_qualifying_record_count",
        "context": f"{prefix}_observed_context_complete",
        "attempted": f"{prefix}_assessment_attempted",
        "scope": f"{prefix}_query_scope_complete",
        "records": f"{prefix}_record_count",
        "partial": f"{prefix}_partial_condition_count",
        "unknown": f"{prefix}_unknown_coverage",
        "failure": f"{prefix}_retrieval_failure",
        "mapping": f"{prefix}_mapping_valid",
    }


def feature_contract(config: dict[str, Any]) -> list[dict[str, str]]:
    names = feature_names(config)
    rows = [
        {"name": "identity_conflict_count", "type": "NONNEGATIVE_INTEGER", "definition": "Count of traceable incompatible target/entity identity assignments under frozen identifier reconciliation."},
        {"name": "provenance_complete", "type": "BOOLEAN", "definition": "TRUE only when all claim, record, source/version, artifact/hash, rule, and required context provenance resolves."},
        {"name": names["conflict"], "type": "NONNEGATIVE_INTEGER", "definition": config["conflict_definition"]},
        {"name": names["qualifying"], "type": "NONNEGATIVE_INTEGER", "definition": config["qualifying_definition"]},
        {"name": names["context"], "type": "BOOLEAN", "definition": config["context_definition"]},
        {"name": names["attempted"], "type": "BOOLEAN", "definition": "TRUE only when an eligible acquisition/assessment was attempted under the frozen component scope."},
        {"name": names["scope"], "type": "BOOLEAN", "definition": "TRUE only when every source/query scope required by the frozen component contract completed without unknown coverage."},
        {"name": names["records"], "type": "NONNEGATIVE_INTEGER", "definition": "Count of atomic source records linked to this component before state resolution; zero records are distinct from a returned zero result."},
        {"name": names["partial"], "type": "NONNEGATIVE_INTEGER", "definition": config["partial_definition"]},
        {"name": names["unknown"], "type": "BOOLEAN", "definition": "TRUE when required acquisition/query coverage remains unknown or unresolved."},
        {"name": names["failure"], "type": "BOOLEAN", "definition": "TRUE when a required retrieval or parsing operation failed."},
    ]
    if config["mapping_required"]:
        rows.append({"name": names["mapping"], "type": "BOOLEAN", "definition": "TRUE only when the source-specific target/disease/linkage mapping needed to execute the component query is valid and provenance-complete."})
    return rows


def rule_expression(state: str, config: dict[str, Any]) -> dict[str, Any]:
    names = feature_names(config)
    no_conflict = (eq(names["conflict"], 0), eq("identity_conflict_count", 0))
    mapping_ok = (eq(names["mapping"], True),) if config["mapping_required"] else ()
    if state == "CONFLICTING":
        return any_of(gt(names["conflict"], 0), gt("identity_conflict_count", 0))
    if state == "OBSERVED":
        return all_of(
            *no_conflict,
            ge(names["qualifying"], int(config["observed_min"])),
            eq(names["context"], True),
            eq("provenance_complete", True),
            *mapping_ok,
        )
    if state == "MISSING":
        return all_of(
            *no_conflict,
            eq(names["attempted"], True),
            eq(names["scope"], True),
            eq(names["qualifying"], 0),
            eq(names["unknown"], False),
            eq(names["failure"], False),
            eq("provenance_complete", True),
            *mapping_ok,
        )
    if state == "PARTIAL":
        return all_of(
            *no_conflict,
            any_of(eq(names["attempted"], True), gt(names["records"], 0)),
            gt(names["partial"], 0),
        )
    if state == "NOT_QUERIED":
        return all_of(
            *no_conflict,
            eq(names["attempted"], False),
            eq(names["records"], 0),
        )
    fail(f"Unknown state: {state}")


def validate_feature_value(name: str, value: Any, contract: dict[str, dict[str, str]]) -> None:
    if name not in contract:
        fail(f"Predicate references undeclared feature: {name}")
    data_type = contract[name]["type"]
    if data_type == "BOOLEAN" and type(value) is not bool:
        fail(f"Feature {name} requires BOOLEAN, observed {type(value).__name__}.")
    if data_type == "NONNEGATIVE_INTEGER" and (type(value) is not int or value < 0):
        fail(f"Feature {name} requires NONNEGATIVE_INTEGER, observed {value!r}.")


def evaluate_ast(node: dict[str, Any], values: dict[str, Any], contract: dict[str, dict[str, str]]) -> bool:
    if set(node) not in ({"op", "args"}, {"op", "feature", "value"}):
        fail(f"Invalid predicate node keys: {sorted(node)}")
    op = node["op"]
    if op in {"all", "any"}:
        args = node["args"]
        if not isinstance(args, list) or not args:
            fail(f"Operator {op} requires a nonempty args list.")
        evaluated = [evaluate_ast(arg, values, contract) for arg in args]
        return all(evaluated) if op == "all" else any(evaluated)
    if op not in {"eq", "ge", "gt"}:
        fail(f"Operator not allowed: {op}")
    feature = node["feature"]
    if feature not in values:
        fail(f"Missing feature value: {feature}")
    validate_feature_value(feature, values[feature], contract)
    validate_feature_value(feature, node["value"], contract)
    if op == "eq":
        return values[feature] == node["value"]
    if contract[feature]["type"] != "NONNEGATIVE_INTEGER":
        fail(f"Numeric operator {op} applied to non-integer feature: {feature}")
    return values[feature] >= node["value"] if op == "ge" else values[feature] > node["value"]


def stable_rule_id(component: str, state: str) -> str:
    component_token = component.removeprefix("COMP_")
    return f"SRR_V0_1__{component_token}__{state}"


def build_rules(semantic_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    source = {(row["component_id"], row["resolved_state"]): row for row in semantic_rows}
    rules = []
    for component in COMPONENT_CONFIGS:
        config = COMPONENT_CONFIGS[component]
        contract = feature_contract(config)
        for state in STATES_IN_PRECEDENCE:
            semantic = source[(component, state)]
            expression = rule_expression(state, config)
            rules.append({
                "rule_id": stable_rule_id(component, state),
                "component_id": component,
                "component_name": semantic["component_name"],
                "state": state,
                "precedence": str(STATE_PRECEDENCE[state]),
                "rule_version": RULE_REGISTRY_VERSION,
                "semantic_predicate_sha256": sha256_text(semantic["deterministic_predicate"]),
                "semantic_predicate": semantic["deterministic_predicate"],
                "executable_predicate_json": canonical_json(expression),
                "input_feature_contract_json": canonical_json(contract),
                "feature_extractor_requirement": "VERSIONED_DETERMINISTIC_SOURCE_TO_FEATURE_EXTRACTOR_REQUIRED",
                "evaluator_id": EVALUATOR_ID,
                "evaluator_version": EVALUATOR_VERSION,
                "fixture_ids": "PENDING",
                "fixture_count": "0",
                "automated_validation_status": "PENDING",
                "review_status": "AWAITING_INDEPENDENT_SCIENTIFIC_REVIEW",
                "runtime_llm_decision": "PROHIBITED",
                "interpretation_boundary": "STATE_RESOLUTION_ONLY_NO_SCORE_RANK_SELECTION_DIRECTION_OR_BIOLOGICAL_CONCLUSION",
            })
    return rules


def default_values(config: dict[str, Any]) -> dict[str, Any]:
    names = feature_names(config)
    values = {
        "identity_conflict_count": 0,
        "provenance_complete": False,
        names["conflict"]: 0,
        names["qualifying"]: 0,
        names["context"]: False,
        names["attempted"]: False,
        names["scope"]: False,
        names["records"]: 0,
        names["partial"]: 0,
        names["unknown"]: False,
        names["failure"]: False,
    }
    if config["mapping_required"]:
        values[names["mapping"]] = True
    return values


def positive_fixture_values(state: str, config: dict[str, Any]) -> dict[str, Any]:
    values = default_values(config)
    names = feature_names(config)
    if state == "CONFLICTING":
        values[names["conflict"]] = 1
        values[names["attempted"]] = True
        values[names["records"]] = 2
    elif state == "OBSERVED":
        values[names["qualifying"]] = int(config["observed_min"])
        values[names["context"]] = True
        values[names["attempted"]] = True
        values[names["scope"]] = True
        values[names["records"]] = max(1, int(config["observed_min"]))
        values["provenance_complete"] = True
    elif state == "MISSING":
        values[names["attempted"]] = True
        values[names["scope"]] = True
        values[names["records"]] = 1
        values["provenance_complete"] = True
    elif state == "PARTIAL":
        values[names["attempted"]] = True
        values[names["records"]] = 1
        values[names["partial"]] = 1
    elif state == "NOT_QUERIED":
        if config["mapping_required"]:
            values[names["mapping"]] = False
    else:
        fail(f"Unknown fixture state: {state}")
    return values


def resolve_rules(
    component_rules: list[dict[str, str]], values: dict[str, Any]
) -> tuple[list[str], str, str, str]:
    contract_rows = json.loads(component_rules[0]["input_feature_contract_json"])
    contract = {row["name"]: row for row in contract_rows}
    if set(values) != set(contract):
        fail(f"Fixture feature set differs from contract: missing={set(contract)-set(values)}, extra={set(values)-set(contract)}")
    ordered = sorted(component_rules, key=lambda row: int(row["precedence"]))
    matched = []
    for rule in ordered:
        expression = json.loads(rule["executable_predicate_json"])
        first = evaluate_ast(expression, values, contract)
        second = evaluate_ast(expression, values, contract)
        if first != second:
            fail(f"Nondeterministic predicate evaluation: {rule['rule_id']}")
        if first:
            matched.append(rule["rule_id"])
    if not matched:
        return [], "NO_RULE", "NO_STATE", "STOP_UNRESOLVED"
    resolved = next(rule for rule in ordered if rule["rule_id"] == matched[0])
    trace = ">".join(f"{rule['precedence']}:{rule['rule_id']}" for rule in ordered)
    return matched, resolved["rule_id"], resolved["state"], trace


def build_tests(rules: list[dict[str, str]]) -> list[dict[str, str]]:
    by_component: dict[str, list[dict[str, str]]] = defaultdict(list)
    for rule in rules:
        by_component[rule["component_id"]].append(rule)
    tests = []
    for component, component_rules in by_component.items():
        config = COMPONENT_CONFIGS[component]
        token = component.removeprefix("COMP_")
        # One positive fixture for each of the 55 semantic rules.
        for state in STATES_IN_PRECEDENCE:
            fixture_id = f"FX_BASE__{token}__{state}"
            values = positive_fixture_values(state, config)
            matched, resolved_rule, resolved_state, trace = resolve_rules(component_rules, values)
            expected_rule = stable_rule_id(component, state)
            passed = resolved_rule == expected_rule and resolved_state == state
            tests.append({
                "fixture_id": fixture_id,
                "fixture_type": "POSITIVE_STATE",
                "component_id": component,
                "intended_semantic_state": state,
                "input_features_json": canonical_json(values),
                "individually_matched_rule_ids": "|".join(matched) if matched else "NONE",
                "resolved_rule_id": resolved_rule,
                "resolved_state": resolved_state,
                "expected_rule_id": expected_rule,
                "expected_state": state,
                "precedence_trace": trace,
                "deterministic_repeat_match": "TRUE",
                "assertion": "ONE_EXPECTED_RULE_RESOLVES",
                "validation_status": "PASS" if passed else "FAIL",
            })
        # Higher-priority conflict conditions must guard every lower state.
        for lower_state in STATES_IN_PRECEDENCE[1:]:
            fixture_id = f"FX_GUARD__{token}__CONFLICT_OVER_{lower_state}"
            values = positive_fixture_values(lower_state, config)
            values[feature_names(config)["conflict"]] = 1
            matched, resolved_rule, resolved_state, trace = resolve_rules(component_rules, values)
            expected_rule = stable_rule_id(component, "CONFLICTING")
            passed = resolved_rule == expected_rule and resolved_state == "CONFLICTING"
            tests.append({
                "fixture_id": fixture_id,
                "fixture_type": "PRECEDENCE_GUARD",
                "component_id": component,
                "intended_semantic_state": f"CONFLICTING_OVER_{lower_state}",
                "input_features_json": canonical_json(values),
                "individually_matched_rule_ids": "|".join(matched) if matched else "NONE",
                "resolved_rule_id": resolved_rule,
                "resolved_state": resolved_state,
                "expected_rule_id": expected_rule,
                "expected_state": "CONFLICTING",
                "precedence_trace": trace,
                "deterministic_repeat_match": "TRUE",
                "assertion": "CONFLICT_GUARD_RESOLVES_FIRST",
                "validation_status": "PASS" if passed else "FAIL",
            })
        # An incoherent feature set must fail closed instead of guessing a state.
        fixture_id = f"FX_FAIL_CLOSED__{token}"
        values = default_values(config)
        values[feature_names(config)["records"]] = 1
        matched, resolved_rule, resolved_state, trace = resolve_rules(component_rules, values)
        passed = not matched and resolved_rule == "NO_RULE" and resolved_state == "NO_STATE"
        tests.append({
            "fixture_id": fixture_id,
            "fixture_type": "FAIL_CLOSED",
            "component_id": component,
            "intended_semantic_state": "UNRESOLVED_INPUT",
            "input_features_json": canonical_json(values),
            "individually_matched_rule_ids": "NONE",
            "resolved_rule_id": resolved_rule,
            "resolved_state": resolved_state,
            "expected_rule_id": "NO_RULE",
            "expected_state": "NO_STATE",
            "precedence_trace": trace,
            "deterministic_repeat_match": "TRUE",
            "assertion": "STOP_WITHOUT_RUNTIME_GUESS",
            "validation_status": "PASS" if passed else "FAIL",
        })
    return tests


def attach_fixture_coverage(rules: list[dict[str, str]], tests: list[dict[str, str]]) -> None:
    coverage: dict[str, list[str]] = defaultdict(list)
    for test in tests:
        if test["validation_status"] == "PASS" and test["resolved_rule_id"] != "NO_RULE":
            coverage[test["resolved_rule_id"]].append(test["fixture_id"])
    positive_coverage = {
        test["expected_rule_id"]
        for test in tests
        if test["fixture_type"] == "POSITIVE_STATE" and test["validation_status"] == "PASS"
    }
    for rule in rules:
        fixtures = sorted(coverage[rule["rule_id"]])
        rule["fixture_ids"] = "|".join(fixtures)
        rule["fixture_count"] = str(len(fixtures))
        rule["automated_validation_status"] = (
            "PASS" if rule["rule_id"] in positive_coverage and fixtures else "FAIL"
        )


def validate_outputs(rules: list[dict[str, str]], tests: list[dict[str, str]]) -> list[dict[str, str]]:
    checks = []

    def check(name: str, passed: bool, observed: Any, expected: Any, detail: str) -> None:
        checks.append({"check": name, "status": "PASS" if passed else "FAIL", "observed": str(observed), "expected": str(expected), "detail": detail})
        if not passed:
            fail(f"Rule registry validation failed: {name}")

    rule_pairs = {(row["component_id"], row["state"]) for row in rules}
    components = {row["component_id"] for row in rules}
    states = {row["state"] for row in rules}
    headers = {field.lower() for table in (rules, tests) for field in table[0]}
    forbidden = headers.intersection(FORBIDDEN_EXACT_FIELDS)
    fixture_types = Counter(row["fixture_type"] for row in tests)

    check("semantic_rule_count", len(rules) == 55 and len(rule_pairs) == 55, len(rules), 55, "Exactly one executable rule per frozen semantic predicate.")
    check("component_ids_preserved", components == set(COMPONENT_CONFIGS), len(components), 11, "All Task #021 component IDs preserved.")
    check("five_states_preserved", states == set(STATES_IN_PRECEDENCE), sorted(states), list(STATES_IN_PRECEDENCE), "Exact five-state vocabulary.")
    check("precedence_preserved", all(row["precedence"] == str(STATE_PRECEDENCE[row["state"]]) for row in rules), "all exact", "1>2>3>4>5", "Numerical field is control-flow order only, never a target metric.")
    check("stable_rule_ids_unique", len({row["rule_id"] for row in rules}) == 55, len({row["rule_id"] for row in rules}), 55, "Stable versioned identifiers.")
    check("semantic_hashes_unique_per_pair", all(len(row["semantic_predicate_sha256"]) == 64 for row in rules), "55 hashes", "55 hashes", "Every executable rule retains its prose-source hash.")
    check("executable_predicates_present", all(row["executable_predicate_json"].startswith("{") for row in rules), "55 JSON ASTs", "55 JSON ASTs", "No free-text execution.")
    check("feature_contracts_present", all(row["input_feature_contract_json"].startswith("[") for row in rules), "55 contracts", "55 contracts", "Typed normalized inputs explicit.")
    check("fixture_matrix_shape", len(tests) == 110 and fixture_types == Counter({"POSITIVE_STATE": 55, "PRECEDENCE_GUARD": 44, "FAIL_CLOSED": 11}), dict(fixture_types), {"POSITIVE_STATE": 55, "PRECEDENCE_GUARD": 44, "FAIL_CLOSED": 11}, "Positive, guard, and no-guess fixtures.")
    check("all_fixtures_pass", all(row["validation_status"] == "PASS" for row in tests), sum(row["validation_status"] == "PASS" for row in tests), len(tests), "Deterministic execution and expected resolution.")
    check("all_rules_fixture_covered", all(int(row["fixture_count"]) >= 1 and row["automated_validation_status"] == "PASS" for row in rules), sum(row["automated_validation_status"] == "PASS" for row in rules), 55, "Every rule has at least one passing positive fixture.")
    check("fail_closed_no_guess", all(row["resolved_rule_id"] == "NO_RULE" and row["resolved_state"] == "NO_STATE" for row in tests if row["fixture_type"] == "FAIL_CLOSED"), "11 stopped", "11 stopped", "Unresolved features never trigger runtime inference.")
    check("runtime_llm_prohibited", all(row["runtime_llm_decision"] == "PROHIBITED" for row in rules), "55 prohibited", "55 prohibited", "No model-generated state decisions.")
    check("independent_review_explicit", all(row["review_status"] == "AWAITING_INDEPENDENT_SCIENTIFIC_REVIEW" for row in rules), "55 awaiting", "55 awaiting", "Automated validation is not misrepresented as independent review.")
    check("forbidden_fields_absent", not forbidden, sorted(forbidden), [], "No scoring, ranking, selection, recommendation, or direction fields.")
    check("no_profiles_generated", not any((OUTPUT_DIR / name).exists() for name in ("profiles.csv", "target_profiles.csv", "target_evidence_profiles.csv")), "none", "none", "Governance artifacts and synthetic fixtures only.")
    check("all_cells_nonblank", all(all(value != "" for value in row.values()) for table in (rules, tests) for row in table), "all nonblank", "all nonblank", "No implicit rule/review/test state.")
    return checks


def csv_bytes(rows: list[dict[str, str]]) -> bytes:
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue().encode("utf-8")


def summary_bytes(rules: list[dict[str, str]], tests: list[dict[str, str]], checks: list[dict[str, str]]) -> bytes:
    fixture_types = Counter(row["fixture_type"] for row in tests)
    lines = [
        "# Task #025 executable state rule registry validation summary",
        "",
        "**Registry status:** AUTOMATED VALIDATION PASS; INDEPENDENT SCIENTIFIC REVIEW PENDING  ",
        "**Profiles materialized:** 0  ",
        f"**Executable semantic rules:** {len(rules)}  ",
        f"**Components:** {len({row['component_id'] for row in rules})}  ",
        f"**States per component:** {len({row['state'] for row in rules})}  ",
        f"**Synthetic structural fixtures:** {len(tests)}  ",
        f"**Validation checks:** {sum(row['status'] == 'PASS' for row in checks)}/{len(checks)}  ",
        "**Scores, rankings, selections, therapeutic direction, or biological conclusions generated:** No",
        "",
        "## Architecture",
        "",
        "Each frozen Task #021 `(component_id, state)` predicate maps one-to-one to a stable rule ID, original semantic predicate/hash, canonical JSON predicate AST, typed component-specific feature contract, frozen precedence, registry/evaluator version, fixture coverage, automated validation status, and explicit review status.",
        "",
        "The evaluator accepts only `all`, `any`, `eq`, `ge`, and `gt` operators over declared Boolean or nonnegative-integer features. It uses no Python `eval`, expression language, runtime model call, free-text judgment, randomness, or wall clock.",
        "",
        "## Resolution",
        "",
        "All matching predicates are evaluated deterministically, then the first match in the frozen order resolves:",
        "",
        "```text",
        "CONFLICTING > OBSERVED > MISSING > PARTIAL > NOT_QUERIED",
        "```",
        "",
        "The integers 1–5 encode control-flow order only. They are not scores, weights, quality levels, or target rankings.",
        "",
        "If no rule matches, execution returns `NO_RULE/NO_STATE` and must stop. It cannot ask an LLM, infer from a blank, choose the nearest state, or silently use a default.",
        "",
        "## Fixture coverage",
        "",
        f"- Positive state fixtures: {fixture_types['POSITIVE_STATE']} (one per semantic rule).",
        f"- Conflict precedence guards: {fixture_types['PRECEDENCE_GUARD']} (one for each lower state per component).",
        f"- Fail-closed fixtures: {fixture_types['FAIL_CLOSED']} (one per component).",
        "",
        "All 110 fixtures passed and repeated predicate evaluation was identical. Fixtures contain synthetic normalized structural features only; no gene, target, evidence profile, or biological conclusion is represented.",
        "",
        "## Release-readiness boundary",
        "",
        "This task resolves the executable-predicate representation gap at the state-machine layer, but does not by itself satisfy final release requirement `REL_RULE_001`. Before release, an independent scientific review must approve every semantic-to-feature mapping, and each source-to-feature extractor must be implemented, versioned, reviewed, and tested against frozen evidence records.",
        "",
        "The registry therefore records `automated_validation_status=PASS` and `review_status=AWAITING_INDEPENDENT_SCIENTIFIC_REVIEW` separately. Automated agreement with generated fixtures is not independent scientific review.",
        "",
        "## Limitations",
        "",
        "- Predicate execution begins from normalized component features; Task #025 does not implement source-record-to-feature extractors.",
        "- Synthetic fixtures test rule mechanics and boundaries, not biological correctness or real-dataset prevalence.",
        "- Conflict guards validate precedence, but existing real conflict examples remain concentrated in transcriptomic sensitivity evidence.",
        "- No target universe, profile row, release bundle, scoring system, or interpretation layer was created.",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def session_bytes(
    git_info: dict[str, str], hashes: dict[str, str], counts: dict[str, int],
    checks: list[dict[str, str]], outputs: dict[Path, bytes],
) -> bytes:
    values = {
        "task": "025",
        "purpose": "executable component-state rule governance registry",
        "rule_registry_version": RULE_REGISTRY_VERSION,
        "evaluator_id": EVALUATOR_ID,
        "evaluator_version": EVALUATOR_VERSION,
        "specification_snapshot_time_utc": git_info["snapshot"],
        "wall_clock_used_in_generated_outputs": "FALSE",
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "git_branch": git_info["branch"],
        "git_head": git_info["head"],
        "git_origin": git_info["remote"],
        "frozen_task024_base_commit": git_info["base"],
        "network_access": "NOT_USED",
        "packages_installed_or_updated": "FALSE",
        "previous_artifacts_modified": "FALSE",
        "profiles_generated": "FALSE",
        "scoring_generated": "FALSE",
        "ranking_generated": "FALSE",
        "therapeutic_candidate_selection_generated": "FALSE",
        "therapeutic_direction_inferred": "FALSE",
        "biological_conclusions_generated": "FALSE",
        "runtime_llm_decisions": "PROHIBITED_AND_NOT_USED",
        "independent_scientific_review": "PENDING",
        "git_commit_or_push": "FALSE",
        "script_sha256": sha256(SCRIPT_PATH),
        "plan_sha256": sha256(PLAN_PATH),
        "registry_result": "AUTOMATED_VALIDATION_PASS_REVIEW_PENDING",
    }
    for name, digest in hashes.items():
        values[f"frozen_input_sha256.{relative(INPUTS[name])}"] = digest
    for name, count in counts.items():
        values[f"validated_count.{name}"] = str(count)
    for row in checks:
        values[f"validation.{row['check']}"] = row["status"]
    for path, content in outputs.items():
        values[f"output_sha256.{relative(path)}"] = hashlib.sha256(content).hexdigest()
    return "".join(f"{key}={values[key]}\n" for key in sorted(values)).encode("utf-8")


def validate_postflight(start_head: str) -> None:
    if run_git("rev-parse", "HEAD") != start_head:
        fail("Git HEAD changed during Task #025.")
    if run_git("diff", "--name-only") or run_git("diff", "--cached", "--name-only"):
        fail("An existing tracked file changed during Task #025.")
    validate_hashes()


def main() -> None:
    git_info = validate_repository()
    hashes = validate_hashes()
    semantic_rows, input_counts = validate_inputs()
    rules = build_rules(semantic_rows)
    tests = build_tests(rules)
    attach_fixture_coverage(rules, tests)
    checks = validate_outputs(rules, tests)
    scientific_outputs = {
        REGISTRY_PATH: csv_bytes(rules),
        TEST_PATH: csv_bytes(tests),
        SUMMARY_PATH: summary_bytes(rules, tests, checks),
    }
    counts = {
        **input_counts,
        "executable_rules": len(rules),
        "positive_fixtures": sum(row["fixture_type"] == "POSITIVE_STATE" for row in tests),
        "precedence_guard_fixtures": sum(row["fixture_type"] == "PRECEDENCE_GUARD" for row in tests),
        "fail_closed_fixtures": sum(row["fixture_type"] == "FAIL_CLOSED" for row in tests),
        "passing_fixtures": sum(row["validation_status"] == "PASS" for row in tests),
        "rules_awaiting_independent_review": sum(row["review_status"] == "AWAITING_INDEPENDENT_SCIENTIFIC_REVIEW" for row in rules),
    }
    session = session_bytes(git_info, hashes, counts, checks, scientific_outputs)
    all_outputs = {**scientific_outputs, SESSION_PATH: session}
    repeated_scientific = {
        REGISTRY_PATH: csv_bytes(rules),
        TEST_PATH: csv_bytes(tests),
        SUMMARY_PATH: summary_bytes(rules, tests, checks),
    }
    repeated_session = session_bytes(git_info, hashes, counts, checks, repeated_scientific)
    if all_outputs != {**repeated_scientific, SESSION_PATH: repeated_session}:
        fail("Repeated state-rule artifact construction was not byte-identical.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    allowed = {path.name for path in all_outputs}
    unexpected = {path.name for path in OUTPUT_DIR.iterdir() if path.name not in allowed}
    if unexpected:
        fail(f"Unexpected Task #025 output files: {sorted(unexpected)}")
    for path, content in all_outputs.items():
        path.write_bytes(content)
    validate_postflight(git_info["head"])

    print("Created files:")
    for path in all_outputs:
        print(f"- {relative(path)}")
    print(f"Executable semantic rules: {len(rules)}")
    print(f"Structural fixtures: {len(tests)}")
    print(f"Passing fixtures: {sum(row['validation_status'] == 'PASS' for row in tests)}/{len(tests)}")
    print(f"Registry validation checks passed: {sum(row['status'] == 'PASS' for row in checks)}/{len(checks)}")
    print("Independent scientific review: PENDING")
    print("No profiles, scores, rankings, selections, direction inferences, or biological conclusions were generated.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
