#!/usr/bin/env python3
"""Build the Task #022 target-universe governance framework.

This standard-library builder validates the frozen Task #008–#021 inputs and
defines a future target_manifest.csv schema plus deterministic membership-rule
templates. It does not materialize a target universe, profile a gene, or create
any score, ordering, selection, recommendation, or therapeutic interpretation.
"""

from __future__ import annotations

import csv
import hashlib
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
TASK021_BASE_COMMIT = "25cc91b"
EXPECTED_BRANCH = "main"
EXPECTED_REMOTE_FRAGMENT = "SichengChen-web/luad-target-dossier"

SCRIPT_PATH = ROOT / "analysis/22_build_target_universe_governance.py"
PLAN_PATH = ROOT / "docs/target_universe_governance_framework_v0.1.md"
OUTPUT_DIR = ROOT / "outputs/target_universe_governance"
SCHEMA_PATH = OUTPUT_DIR / "target_universe_schema.csv"
RULES_PATH = OUTPUT_DIR / "target_universe_membership_rules.csv"
SUMMARY_PATH = OUTPUT_DIR / "target_universe_summary.md"
SESSION_PATH = OUTPUT_DIR / "session_info.txt"

INPUTS = {
    "integrated_registry": ROOT / "outputs/integrated_registry/integrated_target_registry.csv",
    "candidate_registry": ROOT / "outputs/candidate_registry/candidate_registry.csv",
    "profile_schema": ROOT / "outputs/evidence_profiles/profile_schema.csv",
    "profile_builder_contract": ROOT / "outputs/profile_materialization/profile_builder_contract.md",
}

EXPECTED_HASHES = {
    "integrated_registry": "0587fc6901267b18c8144644571f89ac2cc46053b57ea5def4093795fdbc4c26",
    "candidate_registry": "8055a9d99d058d219399957e62f6a3cccc3dd2217bc028d1d11dd4dc667f90e2",
    "profile_schema": "71fce3919f8c9f7b782faee40aeadce9010825410ca640d5453523b0424275ed",
    "profile_builder_contract": "3b9ae40e670349be387e351426bf5418e7ede8de2ff780e19e63050d2e7bf29b",
}

ALLOWED_UNTRACKED_FILES = {
    "analysis/22_build_target_universe_governance.py",
    "docs/target_universe_governance_framework_v0.1.md",
}
ALLOWED_UNTRACKED_PREFIX = "outputs/target_universe_governance/"

MEMBERSHIP_STATES = ("INCLUDED", "EXCLUDED", "NOT_ASSESSED", "FUTURE_SCOPE")
FORBIDDEN_EXACT_FIELDS = {
    "score",
    "rank",
    "priority",
    "recommendation",
    "target_selection",
    "therapeutic_direction",
}

SCHEMA_DEFINITIONS = [
    (1, "EnsemblID", "STRING", "TRUE", "NONEMPTY_VERSIONED_ENSEMBL_GENE_ID", "Frozen source registry", "Only immutable entity and join key.", "Unique within one target_universe_id and target_universe_version manifest; exact source value preserved.", "No symbol, base ID, or external identifier may replace it."),
    (2, "target_universe_id", "STRING", "TRUE", "VERSIONED_CONTROLLED_UNIVERSE_ID", "Frozen universe definition", "Stable identifier for the universe definition family.", "One value per manifest snapshot.", "An identifier labels scope; it does not imply scientific merit."),
    (3, "target_universe_version", "STRING", "TRUE", "CONTENT_DERIVED_VERSION", "Definition, source hashes, rule hash, and generator hash", "Immutable version of one universe snapshot.", "Must change if the definition, source artifacts, membership rules, or generator changes.", "Versions record evolution and are not ordered by target quality."),
    (4, "target_order", "INTEGER", "TRUE", "UNIQUE_POSITIVE_INTEGER", "Frozen source order", "Deterministic row order passed to Task #021 for included entities.", "Unique and contiguous within one manifest; never derived from evidence strength.", "Row order is serialization metadata, not an ordering of scientific value."),
    (5, "membership_state", "CATEGORY", "TRUE", "INCLUDED|EXCLUDED|NOT_ASSESSED|FUTURE_SCOPE", "Deterministic membership rule", "Entity state relative to this exact universe scope.", "Exactly one controlled state per EnsemblID.", "EXCLUDED means outside scope, not biologically unfavorable."),
    (6, "membership_rule_id", "STRING", "TRUE", "CONTROLLED_NONEMPTY_RULE_ID", "Versioned rule registry", "Exact deterministic rule that resolved membership.", "Must resolve in the frozen rule set for this universe version.", "A rule establishes membership only and cannot encode therapeutic judgment."),
    (7, "membership_source", "STRING", "TRUE", "NONEMPTY_ARTIFACT_AND_FIELD_REFERENCE", "Frozen source artifact", "Machine-readable source path and field or governed event used by the rule.", "No free-text or symbol-based fallback source.", "Source presence is not evidence quality."),
    (8, "membership_reason", "STRING", "TRUE", "CONTROLLED_REASON_TEMPLATE_OUTPUT", "Versioned membership rule", "Neutral explanation of why the membership condition resolved.", "Generated from a fixed template using governed values.", "Reasons cannot assert importance, low value, druggability, or clinical relevance."),
    (9, "source_artifact_id", "PIPE_DELIMITED_ID_LIST", "TRUE", "TASK018_STYLE_ARTIFACT_IDS", "Frozen membership-source manifest", "Governed artifacts that support the membership decision.", "Unique, lexically sorted IDs; NONE forbidden for a resolved decision.", "Artifact identity is provenance, not biological support."),
    (10, "source_artifact_sha256", "PIPE_DELIMITED_SHA256_LIST", "TRUE", "64_CHARACTER_SHA256_VALUES", "Frozen membership-source manifest", "Content hashes aligned to source_artifact_id.", "Every source artifact ID has exactly one verified hash.", "A hash proves content identity, not scientific validity."),
    (11, "membership_timestamp", "DATETIME", "TRUE", "FROZEN_ISO8601_UTC", "Frozen universe run configuration", "Timestamp of the governed membership snapshot.", "Copied from configuration; never read from wall clock during row generation.", "Recency does not imply improved evidence or relevance."),
    (12, "inclusion_timestamp", "DATETIME_OR_SENTINEL", "TRUE", "FROZEN_ISO8601_UTC|NOT_APPLICABLE", "Membership state and frozen configuration", "Snapshot time for INCLUDED rows; explicit sentinel otherwise.", "Equals membership_timestamp only for INCLUDED; NOT_APPLICABLE for all other states.", "This field records entry into scope, not discovery or biological timing."),
    (13, "exclusion_reason", "STRING", "TRUE", "CONTROLLED_REASON|NOT_APPLICABLE", "Versioned membership rule", "Neutral scope reason for EXCLUDED rows; explicit sentinel otherwise.", "Required for EXCLUDED and NOT_APPLICABLE for other states.", "Exclusion never means biologically bad or uninteresting."),
    (14, "annotation_status", "CATEGORY", "TRUE", "PRESENT|PARTIAL|MISSING|NOT_APPLICABLE", "Exact annotation-copy validation", "Availability state for permitted display annotations.", "Cannot affect membership unless a future universe definition explicitly governs that annotation as a scope variable.", "Annotation absence cannot trigger manual identifier inference."),
    (15, "Symbol", "STRING", "TRUE", "SOURCE_VALUE|NOT_FOUND", "Exact copy from frozen source", "Optional human-readable display annotation.", "Never joined, repaired, or used as a fallback identifier.", "Symbols may change and are not entity identity."),
    (16, "gene_type", "STRING", "TRUE", "SOURCE_VALUE|NOT_FOUND", "Exact copy from frozen source", "Optional source-provided gene-type annotation.", "Copied without recoding; any future scope use must be explicit and versioned.", "Gene type alone does not imply druggability or relevance."),
    (17, "generated_by", "STRING", "TRUE", "VERSIONED_GENERATOR_PATH_AND_SHA256", "Frozen universe run configuration", "Generator identity used for this manifest.", "Exact path and script hash are required.", "Generator identity does not validate scientific meaning."),
]

RULE_DEFINITIONS = [
    # Universe A: all tested genes.
    ("TU_A_INCLUDED", "ALL_TESTED_GENES", "All tested genes", "1", "INCLUDED", "EnsemblID exists uniquely in both frozen Task #008 and Task #012 registries; values and order match; declared all-tested field equals TRUE.", "outputs/candidate_registry/candidate_registry.csv:EnsemblID,U0_tested plus outputs/integrated_registry/integrated_target_registry.csv:EnsemblID,U0_tested", "Present in the frozen tested-gene registry under the declared all-tested rule.", "A resolved FALSE value may support EXCLUDED only if the universe definition explicitly declares the field as its boundary.", "Exact Symbol and gene_type may be copied after EnsemblID validation; they never affect the join."),
    ("TU_A_EXCLUDED", "ALL_TESTED_GENES", "All tested genes", "2", "EXCLUDED", "Entity is present in the governed source ledger but the explicitly declared all-tested field equals FALSE.", "Versioned all-tested source artifact and declared Boolean field", "Outside this version's declared all-tested scope.", "This is a scope statement and does not assert lack of biological interest.", "Annotations remain display-only."),
    ("TU_A_NOT_ASSESSED", "ALL_TESTED_GENES", "All tested genes", "3", "NOT_ASSESSED", "Entity is in the governed ledger but the declared all-tested value is missing, invalid, or cannot be evaluated without manual inference.", "Versioned all-tested source artifact and validation record", "All-tested membership could not be resolved from the frozen source.", "A data-integrity failure must remain unresolved or stop release; it cannot be coerced to EXCLUDED.", "No annotation repair is permitted."),
    # Universe B: a deliberately parameterized DE layer.
    ("TU_B_INCLUDED", "DE_SUPPORTED_GENES", "DE-supported genes", "1", "INCLUDED", "The universe definition names one exact frozen Boolean DE membership field and that field equals TRUE for the immutable EnsemblID.", "outputs/candidate_registry/candidate_registry.csv:DECLARED_DE_LAYER_FIELD", "Meets the exact frozen DE-layer membership definition named by this universe version.", "The framework does not choose between U1_DE and U2_effect_supported_DE; that choice requires an explicit versioned scientific definition.", "Symbol and gene_type are copied only after EnsemblID membership resolution."),
    ("TU_B_EXCLUDED", "DE_SUPPORTED_GENES", "DE-supported genes", "2", "EXCLUDED", "The exact declared DE membership field equals FALSE.", "outputs/candidate_registry/candidate_registry.csv:DECLARED_DE_LAYER_FIELD", "Outside the declared DE-supported universe scope.", "FALSE is not evidence that the gene is biologically unimportant or unsuitable for therapy.", "Annotations do not alter the state."),
    ("TU_B_NOT_ASSESSED", "DE_SUPPORTED_GENES", "DE-supported genes", "3", "NOT_ASSESSED", "The declared DE membership field is absent, invalid, or not frozen in the version definition.", "Versioned universe configuration and candidate registry validation", "DE-supported membership was not resolvable under the frozen definition.", "A missing definition is not interpreted as FALSE and blocks an executable universe release.", "No symbol-based recovery is allowed."),
    # Universe C: entities with a released profile, without judging its content.
    ("TU_C_INCLUDED", "EVIDENCE_PROFILED_ENTITIES", "Evidence-profiled entities", "1", "INCLUDED", "A released Task #021-compatible profile exists for the immutable EnsemblID and passes all profile cardinality, provenance, input-hash, and output-hash checks.", "Governed profile artifact plus profile QC and frozen Task #021 contract", "A validated evidence profile artifact exists for this entity.", "INCLUDED describes successful materialization only; profile completeness and component states do not determine membership.", "Profile and universe annotations must resolve to the same exact EnsemblID."),
    ("TU_C_EXCLUDED", "EVIDENCE_PROFILED_ENTITIES", "Evidence-profiled entities", "2", "EXCLUDED", "A versioned profile run scope explicitly excludes the entity under a neutral, prespecified operational boundary.", "Frozen profile-run target manifest and rule ID", "Outside this version's declared profile-materialization scope.", "Lack of evidence, a MISSING component, or an unfavorable interpretation can never cause this state.", "Annotations remain unchanged."),
    ("TU_C_NOT_ASSESSED", "EVIDENCE_PROFILED_ENTITIES", "Evidence-profiled entities", "3", "NOT_ASSESSED", "No released, QC-passing profile exists for the entity in this universe version.", "Governed profile release manifest and QC artifact", "No validated profile was materialized for this entity in the frozen scope.", "Not profiled is not no evidence, negative evidence, or low value.", "No profile membership may be inferred from Symbol."),
    # Universe D: definition intentionally deferred.
    ("TU_D_FUTURE_SCOPE", "FUTURE_THERAPEUTIC_DEVELOPMENT_UNIVERSE", "Future therapeutic development universe", "1", "FUTURE_SCOPE", "No scientifically approved, versioned membership definition exists in Task #022.", "Future governed universe definition not supplied", "Membership criteria are intentionally deferred to a future version.", "No current tractability, drug, clinical, safety, profile, or DE field may be used as an implicit filter.", "Annotations cannot substitute for the missing definition."),
    # Cross-universe evolution rule.
    ("TU_VERSION_EVOLUTION", "ALL_UNIVERSES", "All universe definitions", "1", "FUTURE_SCOPE", "A proposed entity or definition belongs to a later scope not represented by the frozen version.", "New governed source artifact and new universe configuration", "Recorded for consideration in a future target-universe version.", "The existing universe is immutable; evolution creates a new version and never overwrites old membership.", "New annotations require source provenance and cannot alter historical rows."),
]


def fail(message: str) -> None:
    raise RuntimeError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def run_git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, text=True, capture_output=True, check=False
    )
    if check and result.returncode != 0:
        fail(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def git_paths(*args: str) -> set[str]:
    output = run_git(*args)
    return {line for line in output.splitlines() if line}


def validate_repository() -> dict[str, str]:
    root = Path(run_git("rev-parse", "--show-toplevel")).resolve()
    if root != ROOT:
        fail(f"Unexpected repository root: {root}")
    branch = run_git("branch", "--show-current")
    head = run_git("rev-parse", "HEAD")
    remote = run_git("remote", "get-url", "origin")
    if branch != EXPECTED_BRANCH:
        fail(f"Expected branch {EXPECTED_BRANCH!r}, observed {branch!r}.")
    if EXPECTED_REMOTE_FRAGMENT not in remote:
        fail(f"Unexpected origin remote: {remote}")
    base = run_git("rev-parse", TASK021_BASE_COMMIT)
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", base, head], cwd=ROOT, check=False
    )
    if result.returncode != 0:
        fail("Frozen Task #021 base commit is not an ancestor of current HEAD.")
    if run_git("diff", "--name-only") or run_git("diff", "--cached", "--name-only"):
        fail("Tracked or staged working-tree changes exist; Task #022 will not modify existing files.")
    changed_inputs = git_paths("diff", "--name-only", f"{base}..{head}", "--", *(relative(path) for path in INPUTS.values()))
    if changed_inputs:
        fail(f"Frozen inputs changed after Task #021 base commit: {sorted(changed_inputs)}")
    untracked = git_paths("ls-files", "--others", "--exclude-standard")
    unexpected = {
        path
        for path in untracked
        if path not in ALLOWED_UNTRACKED_FILES and not path.startswith(ALLOWED_UNTRACKED_PREFIX)
    }
    if unexpected:
        fail(f"Unexpected untracked files: {sorted(unexpected)}")
    return {"root": str(root), "branch": branch, "head": head, "base": base, "remote": remote}


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


def registry_snapshot(path: Path) -> tuple[list[str], list[dict[str, str]], list[str]]:
    required = {
        "EnsemblID",
        "EnsemblID_base",
        "Symbol",
        "gene_type",
        "U0_tested",
        "U1_DE",
        "U2_effect_supported_DE",
    }
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames or []
        missing = required.difference(header)
        if missing:
            fail(f"Missing registry fields in {relative(path)}: {sorted(missing)}")
        rows = [
            {field: row[field] for field in required}
            for row in reader
        ]
    return header, rows, [row["EnsemblID"] for row in rows]


def validate_inputs() -> dict[str, int]:
    _, integrated, integrated_order = registry_snapshot(INPUTS["integrated_registry"])
    _, candidate, candidate_order = registry_snapshot(INPUTS["candidate_registry"])
    expected_rows = 29_606
    if len(integrated) != expected_rows or len(candidate) != expected_rows:
        fail(f"Expected {expected_rows} rows in both registries.")
    if len(set(integrated_order)) != expected_rows or len(set(candidate_order)) != expected_rows:
        fail("EnsemblID is not unique in a frozen registry.")
    if integrated_order != candidate_order:
        fail("Integrated and candidate EnsemblID order differs.")
    for index, (left, right) in enumerate(zip(integrated, candidate), start=2):
        if left != right:
            fail(f"Identity, annotation, or universe-layer mismatch at CSV row {index}.")
        if not left["EnsemblID"] or left["EnsemblID"] == left["EnsemblID_base"]:
            fail(f"Versioned EnsemblID was not preserved at CSV row {index}.")
        if left["U0_tested"] not in {"TRUE", "FALSE"} or left["U1_DE"] not in {"TRUE", "FALSE"} or left["U2_effect_supported_DE"] not in {"TRUE", "FALSE"}:
            fail(f"Invalid frozen Boolean universe field at CSV row {index}.")
    counts = {
        "integrated_registry_rows": len(integrated),
        "candidate_registry_rows": len(candidate),
        "unique_ensembl_ids": len(set(integrated_order)),
        "u0_tested_true": sum(row["U0_tested"] == "TRUE" for row in integrated),
        "u1_de_true": sum(row["U1_DE"] == "TRUE" for row in integrated),
        "u2_effect_supported_de_true": sum(row["U2_effect_supported_DE"] == "TRUE" for row in integrated),
    }
    if counts != {
        "integrated_registry_rows": 29_606,
        "candidate_registry_rows": 29_606,
        "unique_ensembl_ids": 29_606,
        "u0_tested_true": 29_606,
        "u1_de_true": 21_232,
        "u2_effect_supported_de_true": 14_064,
    }:
        fail(f"Frozen registry counts differ from expectations: {counts}")

    with INPUTS["profile_schema"].open(newline="", encoding="utf-8") as handle:
        profile_rows = list(csv.DictReader(handle))
    if len(profile_rows) != 28 or [row["field_name"] for row in profile_rows].count("EnsemblID") != 1:
        fail("Task #020 profile schema identity/cardinality validation failed.")
    ensembl_profile = next(row for row in profile_rows if row["field_name"] == "EnsemblID")
    if ensembl_profile["allowed_values"] != "IMMUTABLE_ENSEMBL_GENE_ID":
        fail("Task #020 no longer identifies EnsemblID as immutable.")

    contract = INPUTS["profile_builder_contract"].read_text(encoding="utf-8")
    required_contract_text = (
        "immutable target-universe manifest with unique EnsemblIDs and explicit target order",
        "No gene symbol may replace EnsemblID or be used as a fallback join",
        "Task #021 supplies no target manifest and creates no target profiles",
    )
    for phrase in required_contract_text:
        if phrase not in contract:
            fail(f"Task #021 contract boundary missing: {phrase}")
    counts["profile_schema_fields"] = len(profile_rows)
    counts["task021_contract_required_boundaries"] = len(required_contract_text)
    return counts


def schema_rows() -> list[dict[str, str]]:
    fields = [
        "field_order",
        "field_name",
        "data_type",
        "required",
        "allowed_values",
        "source_or_derivation",
        "definition",
        "validation_rule",
        "interpretation_boundary",
    ]
    return [dict(zip(fields, map(str, row))) for row in SCHEMA_DEFINITIONS]


def membership_rule_rows() -> list[dict[str, str]]:
    fields = [
        "membership_rule_id",
        "target_universe_id",
        "target_universe_name",
        "rule_order",
        "resolved_membership_state",
        "deterministic_condition",
        "membership_source",
        "membership_reason_template",
        "unresolved_or_exclusion_boundary",
        "annotation_handling",
        "versioning_rule",
    ]
    versioning = "Create a new target_universe_version if the universe definition, source artifact hashes, membership rules, or generator hash changes; never overwrite prior membership."
    return [dict(zip(fields, (*map(str, row), versioning))) for row in RULE_DEFINITIONS]


def validate_outputs(schema: list[dict[str, str]], rules: list[dict[str, str]]) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []

    def check(name: str, passed: bool, observed: object, expected: object, detail: str) -> None:
        checks.append({"check": name, "status": "PASS" if passed else "FAIL", "observed": str(observed), "expected": str(expected), "detail": detail})
        if not passed:
            fail(f"Output validation failed: {name}")

    required_fields = {
        "EnsemblID", "target_universe_id", "membership_state", "membership_source",
        "membership_reason", "source_artifact_id", "source_artifact_sha256",
        "inclusion_timestamp", "exclusion_reason", "annotation_status",
    }
    schema_names = [row["field_name"] for row in schema]
    headers = set(schema[0]) | set(rules[0]) | set(schema_names)
    forbidden = {value.lower() for value in headers}.intersection(FORBIDDEN_EXACT_FIELDS)
    rule_states = {row["resolved_membership_state"] for row in rules}
    rule_universes = {row["target_universe_id"] for row in rules}

    check("schema_required_fields", required_fields.issubset(schema_names), len(required_fields.intersection(schema_names)), len(required_fields), "All user-required target_manifest fields are defined.")
    check("schema_fields_unique", len(schema_names) == len(set(schema_names)), len(set(schema_names)), len(schema_names), "No duplicate manifest fields.")
    check("immutable_join_key", schema_names.count("EnsemblID") == 1 and "EnsemblID_base" not in schema_names, "EnsemblID only", "EnsemblID only", "EnsemblID is the only entity/join key; Symbol is display-only.")
    check("membership_states_exact", rule_states == set(MEMBERSHIP_STATES), sorted(rule_states), list(MEMBERSHIP_STATES), "All and only the controlled states are represented.")
    check("four_universe_concepts", {"ALL_TESTED_GENES", "DE_SUPPORTED_GENES", "EVIDENCE_PROFILED_ENTITIES", "FUTURE_THERAPEUTIC_DEVELOPMENT_UNIVERSE"}.issubset(rule_universes), len(rule_universes), ">=4", "Universe A–D concepts are represented without membership materialization.")
    check("membership_rule_ids_unique", len({row["membership_rule_id"] for row in rules}) == len(rules), len({row["membership_rule_id"] for row in rules}), len(rules), "Stable rule IDs.")
    check("future_de_definition_explicit", any("does not choose between U1_DE and U2_effect_supported_DE" in row["unresolved_or_exclusion_boundary"] for row in rules), "deferred", "deferred", "No unrequested DE-layer decision is made.")
    check("future_development_scope_deferred", any(row["membership_rule_id"] == "TU_D_FUTURE_SCOPE" and row["resolved_membership_state"] == "FUTURE_SCOPE" for row in rules), "FUTURE_SCOPE", "FUTURE_SCOPE", "No implicit druggability or clinical filter.")
    check("versioning_defined", all("never overwrite" in row["versioning_rule"] for row in rules), "all rules", "all rules", "Universe evolution creates a new immutable version.")
    check("forbidden_fields_absent", not forbidden, sorted(forbidden), [], "No forbidden assessment fields in generated schemas.")
    check("all_cells_nonblank", all(all(value != "" for value in row.values()) for table in (schema, rules) for row in table), "all nonblank", "all nonblank", "Rules and provenance requirements are explicit.")
    check("no_target_manifest_generated", not (OUTPUT_DIR / "target_manifest.csv").exists(), "absent", "absent", "Task #022 defines a schema but does not populate memberships.")
    return checks


def write_csv(path: Path, fields: list[str], rows: Iterable[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_summary(schema: list[dict[str, str]], rules: list[dict[str, str]], checks: list[dict[str, str]], counts: dict[str, int]) -> None:
    lines = [
        "# Task #022 target universe governance summary",
        "",
        "**Target manifests populated:** 0  ",
        "**Target profiles populated:** 0  ",
        f"**Future target_manifest schema fields:** {len(schema)}  ",
        f"**Membership-rule templates:** {len(rules)}  ",
        f"**Frozen registry identities validated:** {counts['unique_ensembl_ids']:,}  ",
        f"**Validation checks passed:** {sum(row['status'] == 'PASS' for row in checks)}/{len(checks)}  ",
        "**Scores, rankings, selections, recommendations, or therapeutic interpretations generated:** No",
        "",
        "## Scientific formulation",
        "",
        "The governing question is well formed when interpreted as entity and scope definition: which immutable gene entities are members of a named, versioned universe, under which frozen rule and provenance? It is not a question about which genes are better targets.",
        "",
        "A target entity is the exact versioned Ensembl gene record carried by `EnsemblID`. `Symbol` and `gene_type` are permitted display annotations only. A future manifest covers one universe ID and version so EnsemblID remains unique within that snapshot.",
        "",
        "## Universe concepts",
        "",
        "| Universe | Membership meaning | Boundary |",
        "| --- | --- | --- |",
        "| All tested genes | Membership in an explicitly frozen tested-gene analysis scope | No inference about biological interest |",
        "| DE-supported genes | Membership in one explicitly named frozen DE layer | Task #022 does not choose U1_DE versus U2_effect_supported_DE |",
        "| Evidence-profiled entities | Existence of a released, QC-passing Task #021-compatible profile | Profile state or completeness is not target quality |",
        "| Future therapeutic development universe | Definition intentionally deferred | No current drug, tractability, safety, clinical, or DE field is an implicit filter |",
        "",
        "## Membership states",
        "",
        "- `INCLUDED`: the exact versioned rule evaluates true.",
        "- `EXCLUDED`: the entity is outside this universe's defined scope; this is not a biological judgment.",
        "- `NOT_ASSESSED`: available frozen information cannot resolve membership without inference or repair.",
        "- `FUTURE_SCOPE`: the entity or universe definition is intentionally reserved for a later version.",
        "",
        "Every future decision records its source, rule ID, artifact ID and SHA256, frozen membership timestamp, and neutral reason. Manual edits without provenance and symbol-based joins are prohibited.",
        "",
        "## Version and release contract",
        "",
        "A future `target_universe_version` must be content-derived from the canonical universe definition, ordered source artifact IDs and hashes, canonical membership rules, and generator script hash. Changing any element creates a new version; prior manifests are immutable.",
        "",
        "The future manifest must preserve source order through `target_order`. Task #021 may materialize profiles only from `INCLUDED` rows after the manifest itself is registered externally with an artifact ID and SHA256. The manifest must not contain its own hash because that would create a circular identity; its hash belongs in the materialization run manifest.",
        "",
        "## Frozen input validation",
        "",
        f"The Task #008 candidate and Task #012 integrated registries each contain {counts['candidate_registry_rows']:,} unique, identically ordered EnsemblIDs. Their U0/U1/U2 counts remain {counts['u0_tested_true']:,}, {counts['u1_de_true']:,}, and {counts['u2_effect_supported_de_true']:,}. These counts validate identity only and do not instantiate a universe in Task #022.",
        "",
        "Task #020 still defines EnsemblID as immutable, and the frozen Task #021 contract still requires a unique ordered target universe manifest while prohibiting symbol fallback. All four frozen input hashes matched before and after generation.",
        "",
        "## Deliberately unresolved",
        "",
        "- whether a DE-supported universe should use U1_DE, U2_effect_supported_DE, or a future versioned definition;",
        "- which entities should enter any future therapeutic-development universe;",
        "- when an evidence-profile materialization campaign should begin; and",
        "- any scientific interpretation of membership, evidence state, or exclusion.",
    ]
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate_postflight(start_head: str) -> None:
    if run_git("rev-parse", "HEAD") != start_head:
        fail("Git HEAD changed during Task #022.")
    if run_git("diff", "--name-only") or run_git("diff", "--cached", "--name-only"):
        fail("An existing tracked file changed during Task #022.")
    validate_hashes()


def write_session(started: datetime, git_info: dict[str, str], hashes: dict[str, str], counts: dict[str, int], checks: list[dict[str, str]]) -> None:
    values = {
        "task": "022",
        "purpose": "target universe governance framework",
        "started_at_utc": started.isoformat(),
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "git_branch": git_info["branch"],
        "git_head_before": git_info["head"],
        "git_head_after": run_git("rev-parse", "HEAD"),
        "git_origin": git_info["remote"],
        "frozen_task021_base_commit": git_info["base"],
        "network_access": "NOT_USED",
        "packages_installed_or_updated": "FALSE",
        "existing_files_modified": "FALSE",
        "target_manifest_generated": "FALSE",
        "target_profiles_generated": "FALSE",
        "scoring_generated": "FALSE",
        "ranking_generated": "FALSE",
        "candidate_selection_generated": "FALSE",
        "target_recommendations_generated": "FALSE",
        "therapeutic_interpretation_generated": "FALSE",
        "git_commit_or_push": "FALSE",
        "script_sha256": sha256(SCRIPT_PATH),
        "plan_sha256": sha256(PLAN_PATH),
    }
    for name, value in counts.items():
        values[f"input_validation.{name}"] = str(value)
    for name, digest in hashes.items():
        values[f"frozen_input_sha256.{relative(INPUTS[name])}"] = digest
    for row in checks:
        values[f"output_validation.{row['check']}"] = row["status"]
    for path in (SCHEMA_PATH, RULES_PATH, SUMMARY_PATH):
        values[f"output_sha256.{relative(path)}"] = sha256(path)
    SESSION_PATH.write_text("".join(f"{key}={values[key]}\n" for key in sorted(values)), encoding="utf-8")


def main() -> None:
    started = datetime.now(timezone.utc)
    git_info = validate_repository()
    hashes = validate_hashes()
    counts = validate_inputs()
    schema = schema_rows()
    rules = membership_rule_rows()
    checks = validate_outputs(schema, rules)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    allowed = {SCHEMA_PATH.name, RULES_PATH.name, SUMMARY_PATH.name, SESSION_PATH.name}
    unexpected = {path.name for path in OUTPUT_DIR.iterdir() if path.name not in allowed}
    if unexpected:
        fail(f"Unexpected Task #022 output files: {sorted(unexpected)}")

    write_csv(SCHEMA_PATH, list(schema[0]), schema)
    write_csv(RULES_PATH, list(rules[0]), rules)
    write_summary(schema, rules, checks, counts)
    validate_postflight(git_info["head"])
    write_session(started, git_info, hashes, counts, checks)

    print("Created files:")
    for path in (SCHEMA_PATH, RULES_PATH, SUMMARY_PATH, SESSION_PATH):
        print(f"- {relative(path)}")
    print(f"Future manifest schema fields: {len(schema)}")
    print(f"Membership-rule templates: {len(rules)}")
    print(f"Validated immutable EnsemblIDs: {counts['unique_ensembl_ids']}")
    print(f"Validation checks passed: {sum(row['status'] == 'PASS' for row in checks)}/{len(checks)}")
    print("No target manifest, profile, score, ranking, selection, or recommendation was generated.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
