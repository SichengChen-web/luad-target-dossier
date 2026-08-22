#!/usr/bin/env python3
"""Materialize the governed full Target Evidence Profile release candidate.

The implementation streams the frozen Task #026 transcriptomic feature and
provenance universe into deterministic EnsemblID hash-prefix partitions. It
executes only frozen Task #025 structural state predicates. It does not score,
rank, prioritize, select, recommend, or biologically interpret targets.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
import shutil
import subprocess
import sys
import tempfile
from collections import Counter, OrderedDict, defaultdict
from pathlib import Path
from typing import Any, Iterable, TextIO


ROOT = Path(__file__).resolve().parents[1]
TASK029_BASE_COMMIT = "8c9a366c704c2da7cd4c8b578fef3bb45dd71db0"
EXPECTED_BRANCH = "main"
EXPECTED_REMOTE_FRAGMENT = "SichengChen-web/luad-target-dossier"

EXPECTED_PROFILES = 29_606
EXPECTED_FEATURES_PER_PROFILE = 22
EXPECTED_PROFILE_FEATURES = 651_332
EXPECTED_PROVENANCE_PER_PROFILE = 35
EXPECTED_PROVENANCE_LINKS = 1_036_210
EXPECTED_U1 = 21_232
EXPECTED_U2 = 14_064
EXPECTED_AUDIT_SAMPLE = 297

SCHEMA_VERSION = "TARGET_EVIDENCE_PROFILE_FULL_SCHEMA_V0.1"
PROFILE_VERSION = "FULL_UNIVERSE_TARGET_EVIDENCE_PROFILE_V0.1"
EVIDENCE_SNAPSHOT_VERSION = (
    "TASK026_TRANSCRIPTOMIC_FEATURES_SHA256_"
    "4014469439ff14d27c451a356cf7711daa7a5331c58326eced2cf96edb298844"
)
COMPONENT_ID = "COMP_TRANSCRIPTOMIC_EVIDENCE"
COMPONENT_DEFINITION_VERSION = "COMP_TRANSCRIPTOMIC_EVIDENCE_V0.1"
GENERATOR_VERSION = "FULL_PROFILE_MATERIALIZER_V0.1"
PARTITION_STRATEGY_VERSION = "ENSEMBL_SHA256_PREFIX_2_V0.1"
SOURCE_FEATURE_ARTIFACT_ID = "ART_TASK026_TRANSCRIPTOMIC_FEATURES_V0_1"
SOURCE_PROVENANCE_ARTIFACT_ID = "ART_TASK026_TRANSCRIPTOMIC_FEATURE_PROVENANCE_V0_1"
LIFECYCLE_STATUS = "UNASSIGNED_RELEASE_CANDIDATE_AWAITING_HUMAN_GOVERNANCE_ACTION"

SCRIPT_PATH = ROOT / "analysis/30_materialize_full_target_profiles.py"
OUTPUT_DIR = ROOT / "outputs/profile_release_candidate_v0.1"
PROFILES_DIR = OUTPUT_DIR / "profiles"
PROVENANCE_DIR = OUTPUT_DIR / "provenance"

INPUTS = {
    "task026_features": ROOT / "outputs/feature_extraction/transcriptomic_features.csv",
    "task026_dictionary": ROOT / "outputs/feature_extraction/feature_dictionary.csv",
    "task026_provenance": ROOT / "outputs/feature_extraction/feature_provenance_registry.csv",
    "task025_rules": ROOT / "outputs/state_rule_registry/state_rule_registry.csv",
    "task027_schema": ROOT / "outputs/profile_generation/profile_schema_v0.1.json",
    "task027_manifest": ROOT / "outputs/profile_generation/pilot_profile_manifest.json",
    "task026_provenance_governance": ROOT / "docs/governance/task026_provenance_artifact_governance_v0.1.md",
    "task028_profile_governance": ROOT / "docs/governance/target_evidence_profile_governance_v0.1.md",
    "task028_lifecycle": ROOT / "docs/governance/profile_lifecycle_specification_v0.1.md",
    "task028_component": ROOT / "docs/governance/profile_component_model_v0.1.md",
    "task028_release": ROOT / "docs/governance/profile_release_policy_v0.1.md",
    "task029_materialization": ROOT / "docs/governance/full_universe_profile_materialization_specification_v0.1.md",
    "task029_partition": ROOT / "docs/governance/profile_artifact_partition_strategy_v0.1.md",
    "task029_validation": ROOT / "docs/governance/profile_validation_strategy_v0.1.md",
    "task029_incremental": ROOT / "docs/governance/profile_incremental_update_policy_v0.1.md",
}

EXPECTED_HASHES = {
    "task026_features": "4014469439ff14d27c451a356cf7711daa7a5331c58326eced2cf96edb298844",
    "task026_dictionary": "d3ffd865251674eef14c5f79c8651363a0c1497ef2d5e652a2744fb31f326abd",
    "task026_provenance": "68ba8096563358b539360963da7d2856fcb0f888673da9989741b95549f3b246",
    "task025_rules": "858974ae9d13e9505393dfce50e746b7fd1c15adec56d66771cff238da59d13d",
    "task027_schema": "c19eff421654bdc002dc3901adec694f8a3ccf76cb4901970d858f3c699ae750",
    "task027_manifest": "df3c40deeb497ca6a75c0f0b0195a828fb28103df1d6d4edb1c9747d93846941",
    "task026_provenance_governance": "8e5e2a4e5018751ae9c4482734bfe48ffb432418ecebc764a1c341e11684c6da",
    "task028_profile_governance": "1b8ab03bb758fd70d8a4bffb27ba1c7f97f83a52c20e75a0c18d9b0bd0941bbd",
    "task028_lifecycle": "346d46ce22b46513038ed7a62d951f1d3197432246e758bee84e56425137ccca",
    "task028_component": "86ae5b8ce089f97770976b7b9f9b547a918e88c165cb7f983dd450178f8a7355",
    "task028_release": "f164be0352cd012583560b6ff5ef9850e43c59b49f4b9c4e28e3fe9138c77912",
    "task029_materialization": "0b46557c3a82e1129e9c0edf11ab65a3573d9af1b3dee7a177399e17c4ca524f",
    "task029_partition": "d563d6dab9173eb08722607667a2c7a925b04eee598910cef8b87a40deabe73a",
    "task029_validation": "a1052c97e9fbde696e6110a6fce3c3e392ca6d5bf55e103824c1c65cea395b86",
    "task029_incremental": "cca517995604eb14c277e777995073d2d140b23b75555f057791d102058642d2",
}

ALLOWED_TASK030_PATHS = {"analysis/30_materialize_full_target_profiles.py"}
ALLOWED_TASK030_PREFIX = "outputs/profile_release_candidate_v0.1/"

PROFILE_STATES = ("CONFLICTING", "OBSERVED", "MISSING", "PARTIAL", "NOT_QUERIED")
MISSINGNESS_STATES = ("OBSERVED", "NOT_FOUND", "NOT_QUERIED", "NOT_APPLICABLE", "UNKNOWN")
PARTITION_IDS = tuple(f"p{value:02x}" for value in range(256))

PROVENANCE_INPUT_COLUMNS = [
    "feature_id", "EnsemblID", "feature_name", "claim_id",
    "evidence_record_id", "source_id", "artifact_id", "dependency_id",
    "feature_missingness_status", "extraction_rule_id", "extractor_version",
]
PROVENANCE_OUTPUT_COLUMNS = [
    "profile_id", "EnsemblID", "universe_ordinal", "partition_id",
    "component_id", "component_definition_version", "feature_id",
    "feature_name", "claim_id", "evidence_record_id", "source_id",
    "artifact_id", "dependency_id", "feature_missingness_status",
    "extraction_rule_id", "extractor_version", "state_rule_id",
    "state_rule_version", "generator_version", "evidence_snapshot_version",
]

UNIVERSE_COLUMNS = [
    "EnsemblID", "universe_ordinal", "source_feature_artifact_id",
    "source_feature_sha256", "profile_version", "evidence_snapshot_version",
    "partition_strategy_version", "partition_id",
]
INDEX_COLUMNS = [
    "EnsemblID", "universe_ordinal", "profile_id", "profile_version",
    "evidence_snapshot_version", "partition_strategy_version", "partition_id",
    "profile_artifact_id", "profile_content_sha256", "component_set",
]
PARTITION_COLUMNS = [
    "release_candidate_id", "partition_strategy_version", "partition_id",
    "artifact_role", "relative_path", "artifact_id", "schema_version",
    "profile_count", "provenance_link_count", "file_size_bytes", "sha256",
    "generator_version", "storage_reference_status", "storage_reference",
    "validation_status",
]
DEPENDENCY_COLUMNS = [
    "profile_id", "EnsemblID", "universe_ordinal", "partition_id",
    "feature_row_sha256", "provenance_relationship_count",
    "provenance_relationships_sha256", "source_feature_artifact_id",
    "source_feature_artifact_sha256", "source_provenance_artifact_id",
    "source_provenance_artifact_sha256", "schema_version", "profile_version",
    "evidence_snapshot_version", "component_id", "component_definition_version",
    "state_rule_version", "extractor_version", "generator_version",
    "partition_strategy_version",
]
AUDIT_COLUMNS = [
    "audit_sequence", "EnsemblID", "profile_id", "partition_id", "audit_key",
    "selection_rule_id",
]
VALIDATION_COLUMNS = [
    "check_id", "category", "status", "observed", "expected", "notes",
]

METADATA_NAMES = (
    "release_manifest.json", "universe_manifest.csv", "profile_index.csv",
    "partition_manifest.csv", "dependency_manifest.csv",
    "deterministic_audit_sample.csv", "profile_schema_v0.1.json",
    "validation_results.csv", "validation_report.md", "session_info.txt",
)

FORBIDDEN_PROFILE_FIELDS = {
    "score", "rank", "ranking", "priority", "confidence", "confidence_score",
    "target_selection", "recommendation", "therapeutic_direction",
    "biological_interpretation", "biological_importance",
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


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def pretty_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n"


def stable_id(prefix: str, value: str) -> str:
    return f"{prefix}_{sha256_text(value)[:24].upper()}"


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def partition_id(ensembl_id: str) -> str:
    return "p" + sha256_text(ensembl_id)[:2]


def profile_id(ensembl_id: str) -> str:
    return stable_id(
        "PRF", f"{ensembl_id}|{PROFILE_VERSION}|{EVIDENCE_SNAPSHOT_VERSION}"
    )


def artifact_id(release_candidate_id: str, part: str, role: str) -> str:
    return stable_id("ART", f"{release_candidate_id}|{part}|{role}")


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
    base = run_git("rev-parse", TASK029_BASE_COMMIT)
    remote = run_git("remote", "get-url", "origin")
    if root != ROOT or branch != EXPECTED_BRANCH or EXPECTED_REMOTE_FRAGMENT not in remote:
        fail(f"Repository identity mismatch: root={root}, branch={branch}, remote={remote}")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", base, head], cwd=ROOT, check=False
    )
    if ancestor.returncode != 0:
        fail("Frozen Task #029 base commit is not an ancestor of current HEAD.")
    changed = set(run_git("diff", "--name-only").splitlines())
    changed |= set(run_git("diff", "--cached", "--name-only").splitlines())
    untracked = set(run_git("ls-files", "--others", "--exclude-standard").splitlines())
    unexpected = sorted(
        path for path in changed | untracked
        if path
        and path not in ALLOWED_TASK030_PATHS
        and not path.startswith(ALLOWED_TASK030_PREFIX)
    )
    if unexpected:
        fail("Unexpected working-tree paths outside Task #030: " + ", ".join(unexpected))
    return {"branch": branch, "head": head, "base": base, "remote": remote}


def validate_inputs() -> dict[str, dict[str, Any]]:
    manifest: dict[str, dict[str, Any]] = {}
    for key, path in INPUTS.items():
        if not path.is_file():
            fail(f"Missing frozen input: {relative(path)}")
        observed = sha256(path)
        expected = EXPECTED_HASHES[key]
        if observed != expected:
            fail(
                f"Frozen input hash mismatch at {relative(path)}: "
                f"observed={observed}, expected={expected}"
            )
        manifest[key] = {
            "relative_path": relative(path),
            "file_size_bytes": path.stat().st_size,
            "sha256": observed,
        }

    partition_spec = INPUTS["task029_partition"].read_text(encoding="utf-8")
    materialization_spec = INPUTS["task029_materialization"].read_text(encoding="utf-8")
    validation_spec = INPUTS["task029_validation"].read_text(encoding="utf-8")
    governance_tokens = (
        (partition_spec, PARTITION_STRATEGY_VERSION),
        (partition_spec, 'partition_id = "p" + lowercase(SHA256(UTF8(EnsemblID)))[0:2]'),
        (materialization_spec, "29,606"),
        (materialization_spec, "(feature_id, evidence_record_id)"),
        (validation_spec, "297"),
    )
    if any(token not in text for text, token in governance_tokens):
        fail("A frozen Task #029 governance token is missing.")
    pilot_schema = json.loads(INPUTS["task027_schema"].read_text(encoding="utf-8"))
    if set(pilot_schema.get("$defs", {})) != {"profile", "component", "feature", "provenance_link"}:
        fail("Task #027 pilot schema contract changed.")
    pilot_manifest = json.loads(INPUTS["task027_manifest"].read_text(encoding="utf-8"))
    if pilot_manifest.get("release_status") != "PILOT_VALIDATION_ONLY":
        fail("Task #027 pilot lifecycle contract changed.")
    return manifest


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_dictionary() -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    rows = read_csv(INPUTS["task026_dictionary"])
    if len(rows) != EXPECTED_FEATURES_PER_PROFILE:
        fail(f"Feature dictionary has {len(rows)} rows; expected 22.")
    names = [row["feature_name"] for row in rows]
    if len(set(names)) != len(names):
        fail("Feature dictionary contains duplicate names.")
    if sum(row["task025_input"] == "TRUE" for row in rows) != 11:
        fail("Feature dictionary Task #025 input count changed.")
    return rows, {row["feature_name"]: row for row in rows}


def load_features(
    dictionary_rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], dict[str, dict[str, str]], dict[str, list[dict[str, str]]]]:
    with INPUTS["task026_features"].open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            fail("Task #026 feature table has no header.")
        expected_fields = ["EnsemblID"] + [row["feature_name"] for row in dictionary_rows] + ["extractor_version"]
        if reader.fieldnames != expected_fields:
            fail("Task #026 feature table no longer matches its dictionary order.")
        rows = list(reader)
    identifiers = [row["EnsemblID"] for row in rows]
    if len(rows) != EXPECTED_PROFILES or len(set(identifiers)) != EXPECTED_PROFILES:
        fail("Task #026 universe count/identity mismatch.")
    by_id: dict[str, dict[str, str]] = {}
    by_partition: dict[str, list[dict[str, str]]] = {part: [] for part in PARTITION_IDS}
    u1 = u2 = 0
    for ordinal, row in enumerate(rows, start=1):
        ensembl_id = row["EnsemblID"]
        if not ensembl_id.startswith("ENSG"):
            fail(f"Invalid immutable identity: {ensembl_id}")
        row["_universe_ordinal"] = str(ordinal)
        row["_partition_id"] = partition_id(ensembl_id)
        by_id[ensembl_id] = row
        by_partition[row["_partition_id"]].append(row)
        u1 += row["fdr_pass_status"] == "THRESHOLD_MET"
        u2 += (
            row["fdr_pass_status"] == "THRESHOLD_MET"
            and row["effect_threshold_status"] == "THRESHOLD_MET"
        )
    if u1 != EXPECTED_U1 or u2 != EXPECTED_U2:
        fail(f"Frozen U1/U2 counts changed: U1={u1}, U2={u2}")
    return rows, by_id, by_partition


def load_rules(dictionary: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    rows = [
        row for row in read_csv(INPUTS["task025_rules"])
        if row["component_id"] == COMPONENT_ID
    ]
    rows.sort(key=lambda row: int(row["precedence"]))
    if len(rows) != 5 or [row["state"] for row in rows] != list(PROFILE_STATES):
        fail("Task #025 transcriptomic state/precedence contract changed.")
    contracts = [json.loads(row["input_feature_contract_json"]) for row in rows]
    if any(contract != contracts[0] for contract in contracts[1:]):
        fail("Task #025 rule states do not share one input contract.")
    contract = {item["name"]: item["type"] for item in contracts[0]}
    current = {
        name: definition["data_type"]
        for name, definition in dictionary.items()
        if definition["task025_input"] == "TRUE"
    }
    if contract != current:
        fail("Task #025 and Task #026 typed feature contracts differ.")
    for row in rows:
        if row["automated_validation_status"] != "PASS" or row["runtime_llm_decision"] != "PROHIBITED":
            fail("Task #025 rule validation/runtime contract changed.")
        row["predicate"] = json.loads(row["executable_predicate_json"])
        row["contract"] = contract
    return rows


def typed_value(value: str, data_type: str, label: str) -> bool | int:
    if data_type == "BOOLEAN":
        if value == "TRUE":
            return True
        if value == "FALSE":
            return False
        fail(f"Invalid Boolean at {label}: {value!r}")
    if data_type == "NONNEGATIVE_INTEGER":
        if not value.isdigit():
            fail(f"Invalid non-negative integer at {label}: {value!r}")
        return int(value)
    fail(f"Unsupported Task #025 input type at {label}: {data_type}")


def evaluate_predicate(node: dict[str, Any], features: dict[str, bool | int]) -> bool:
    op = node.get("op")
    if op in {"all", "any"}:
        args = node.get("args")
        if not isinstance(args, list) or not args:
            fail(f"Invalid {op} predicate.")
        values = [evaluate_predicate(arg, features) for arg in args]
        return all(values) if op == "all" else any(values)
    if op in {"eq", "gt", "ge"}:
        name = node.get("feature")
        if name not in features or "value" not in node:
            fail(f"Invalid leaf predicate: {node}")
        left = features[name]
        right = node["value"]
        if type(left) is not type(right):
            fail(f"Predicate type mismatch for {name}")
        if op == "eq":
            return left == right
        if isinstance(left, bool):
            fail(f"Ordered Boolean predicate for {name}")
        return left > right if op == "gt" else left >= right
    fail(f"Unsupported predicate operation: {op!r}")


def resolve_state(row: dict[str, str], rules: list[dict[str, Any]]) -> dict[str, str]:
    contract: dict[str, str] = rules[0]["contract"]
    typed = {
        name: typed_value(row[name], data_type, f"{row['EnsemblID']}.{name}")
        for name, data_type in contract.items()
    }
    matched = [rule for rule in rules if evaluate_predicate(rule["predicate"], typed)]
    if not matched:
        fail(f"No Task #025 rule matched {row['EnsemblID']}")
    chosen = matched[0]
    return {
        "state": chosen["state"],
        "state_rule_id": chosen["rule_id"],
        "state_rule_version": chosen["rule_version"],
        "state_rule_review_status": chosen["review_status"],
    }


def validate_state_fixtures(rules: list[dict[str, Any]]) -> int:
    base: dict[str, bool | int] = {
        "identity_conflict_count": 0,
        "provenance_complete": True,
        "transcript_conflict_count": 0,
        "transcript_qualifying_record_count": 2,
        "transcript_observed_context_complete": True,
        "transcript_assessment_attempted": True,
        "transcript_query_scope_complete": True,
        "transcript_record_count": 2,
        "transcript_partial_condition_count": 0,
        "transcript_unknown_coverage": False,
        "transcript_retrieval_failure": False,
    }
    fixtures = {
        "CONFLICTING": {**base, "transcript_conflict_count": 1},
        "OBSERVED": base,
        "MISSING": {
            **base, "transcript_qualifying_record_count": 0,
            "transcript_observed_context_complete": False,
        },
        "PARTIAL": {
            **base, "transcript_qualifying_record_count": 1,
            "transcript_observed_context_complete": False,
            "transcript_partial_condition_count": 1,
        },
        "NOT_QUERIED": {
            **base, "transcript_qualifying_record_count": 0,
            "transcript_observed_context_complete": False,
            "transcript_assessment_attempted": False,
            "transcript_query_scope_complete": False,
            "transcript_record_count": 0,
        },
    }
    for expected, features in fixtures.items():
        matched = [rule for rule in rules if evaluate_predicate(rule["predicate"], features)]
        if not matched or matched[0]["state"] != expected:
            fail(f"State boundary fixture failed for {expected}")
    return len(fixtures)


def validate_partition_fixtures() -> int:
    fixtures = {
        "ENSG00000000003.14": "p92",
        "ENSG00000229097.1": "p59",
        "ENSG00000248551.1": "p7f",
        "ENSG00000000419.12": "pe7",
    }
    for identifier, expected in fixtures.items():
        if partition_id(identifier) != expected:
            fail(f"Partition fixture failed for {identifier}")
    return len(fixtures)


class ShardWriterPool:
    def __init__(self, directory: Path, max_open: int = 32) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        self.max_open = max_open
        self.handles: OrderedDict[str, tuple[TextIO, csv.DictWriter]] = OrderedDict()
        self.initialized: set[str] = set()

    def writer(self, part: str) -> csv.DictWriter:
        if part in self.handles:
            handle, writer = self.handles.pop(part)
            self.handles[part] = (handle, writer)
            return writer
        if len(self.handles) >= self.max_open:
            _, (old_handle, _) = self.handles.popitem(last=False)
            old_handle.close()
        path = self.directory / f"{part}.csv"
        mode = "a" if part in self.initialized else "w"
        handle = path.open(mode, newline="", encoding="utf-8")
        writer = csv.DictWriter(handle, fieldnames=PROVENANCE_INPUT_COLUMNS, lineterminator="\n")
        if part not in self.initialized:
            writer.writeheader()
            self.initialized.add(part)
        self.handles[part] = (handle, writer)
        return writer

    def close(self) -> None:
        for handle, _ in self.handles.values():
            handle.close()
        self.handles.clear()


def shard_provenance(
    directory: Path,
    features_by_id: dict[str, dict[str, str]],
) -> dict[str, int]:
    pool = ShardWriterPool(directory)
    per_gene: Counter[str] = Counter()
    total = 0
    try:
        with INPUTS["task026_provenance"].open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != PROVENANCE_INPUT_COLUMNS:
                fail("Task #026 provenance schema changed.")
            for row in reader:
                ensembl_id = row["EnsemblID"]
                feature = features_by_id.get(ensembl_id)
                if feature is None:
                    fail(f"Provenance contains unknown EnsemblID: {ensembl_id}")
                pool.writer(feature["_partition_id"]).writerow(row)
                per_gene[ensembl_id] += 1
                total += 1
    finally:
        pool.close()
    if total != EXPECTED_PROVENANCE_LINKS:
        fail(f"Provenance row count is {total}; expected {EXPECTED_PROVENANCE_LINKS}")
    wrong = [identifier for identifier, count in per_gene.items() if count != EXPECTED_PROVENANCE_PER_PROFILE]
    if len(per_gene) != EXPECTED_PROFILES or wrong:
        fail(
            f"Per-gene provenance cardinality failed: genes={len(per_gene)}, wrong={len(wrong)}"
        )
    return {"total": total, "genes": len(per_gene)}


def load_provenance_shard(
    path: Path,
    dictionary: dict[str, dict[str, str]],
) -> dict[tuple[str, str], list[dict[str, str]]]:
    links: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    composites: set[tuple[str, str]] = set()
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != PROVENANCE_INPUT_COLUMNS:
            fail(f"Raw provenance shard schema mismatch: {path}")
        for row in reader:
            definition = dictionary.get(row["feature_name"])
            if definition is None:
                fail(f"Unknown provenance feature: {row['feature_name']}")
            expected_feature_id = stable_id(
                "FTR", f"{row['EnsemblID']}|{row['feature_name']}|{row['extractor_version']}"
            )
            if row["feature_id"] != expected_feature_id:
                fail(f"Feature identity mismatch: {row['feature_id']}")
            if row["extraction_rule_id"] != definition["extraction_rule_id"]:
                fail(f"Extraction rule mismatch: {row['feature_id']}")
            if row["extractor_version"] != definition["extractor_version"]:
                fail(f"Extractor version mismatch: {row['feature_id']}")
            if row["feature_missingness_status"] not in MISSINGNESS_STATES:
                fail(f"Invalid missingness: {row['feature_id']}")
            composite = (row["feature_id"], row["evidence_record_id"])
            if composite in composites:
                fail(f"Duplicate provenance relationship: {composite}")
            composites.add(composite)
            links[(row["EnsemblID"], row["feature_name"])].append(row)
    for rows in links.values():
        rows.sort(key=lambda row: row["evidence_record_id"])
    return links


def build_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "urn:luad-target-dossier:full-target-profile:v0.1",
        "title": "Full-universe Target Evidence Profile schema v0.1",
        "description": "One deterministic structural evidence profile; no target evaluation.",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "profile_id", "EnsemblID", "universe_ordinal", "schema_version",
            "profile_version", "evidence_snapshot_version", "generator_version",
            "partition_strategy_version", "components",
        ],
        "properties": {
            "profile_id": {"type": "string", "pattern": "^PRF_[0-9A-F]{24}$"},
            "EnsemblID": {"type": "string", "pattern": "^ENSG[0-9]+\\.[0-9]+$"},
            "universe_ordinal": {"type": "integer", "minimum": 1, "maximum": EXPECTED_PROFILES},
            "schema_version": {"const": SCHEMA_VERSION},
            "profile_version": {"const": PROFILE_VERSION},
            "evidence_snapshot_version": {"const": EVIDENCE_SNAPSHOT_VERSION},
            "generator_version": {"const": GENERATOR_VERSION},
            "partition_strategy_version": {"const": PARTITION_STRATEGY_VERSION},
            "components": {"type": "array", "minItems": 1, "maxItems": 1, "items": {"$ref": "#/$defs/component"}},
        },
        "$defs": {
            "provenance_link": {
                "type": "object", "additionalProperties": False,
                "required": [
                    "feature_id", "evidence_record_id", "claim_id", "source_id",
                    "artifact_id", "dependency_id", "extraction_rule_id", "extractor_version",
                ],
                "properties": {
                    "feature_id": {"type": "string"},
                    "evidence_record_id": {"type": "string"},
                    "claim_id": {"type": "string"},
                    "source_id": {"type": "string"},
                    "artifact_id": {"type": "string"},
                    "dependency_id": {"type": "string"},
                    "extraction_rule_id": {"type": "string"},
                    "extractor_version": {"type": "string"},
                },
            },
            "feature": {
                "type": "object", "additionalProperties": False,
                "required": [
                    "feature_id", "feature_name", "value", "data_type",
                    "missingness_status", "provenance_links",
                ],
                "properties": {
                    "feature_id": {"type": "string"},
                    "feature_name": {"type": "string"},
                    "value": {"type": "string"},
                    "data_type": {"type": "string"},
                    "missingness_status": {"enum": list(MISSINGNESS_STATES)},
                    "provenance_links": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/provenance_link"}},
                },
            },
            "component": {
                "type": "object", "additionalProperties": False,
                "required": [
                    "component_id", "component_definition_version", "state",
                    "state_rule_id", "state_rule_version", "state_rule_review_status",
                    "features",
                ],
                "properties": {
                    "component_id": {"const": COMPONENT_ID},
                    "component_definition_version": {"const": COMPONENT_DEFINITION_VERSION},
                    "state": {"enum": list(PROFILE_STATES)},
                    "state_rule_id": {"type": "string"},
                    "state_rule_version": {"type": "string"},
                    "state_rule_review_status": {"type": "string"},
                    "features": {
                        "type": "array", "minItems": EXPECTED_FEATURES_PER_PROFILE,
                        "maxItems": EXPECTED_FEATURES_PER_PROFILE,
                        "items": {"$ref": "#/$defs/feature"},
                    },
                },
            },
        },
    }


def recursively_validate_forbidden_fields(value: Any, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = key.lower()
            if normalized in FORBIDDEN_PROFILE_FIELDS or any(
                normalized.endswith("_" + forbidden) for forbidden in FORBIDDEN_PROFILE_FIELDS
            ):
                fail(f"Forbidden profile field {key!r} at {path}")
            recursively_validate_forbidden_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            recursively_validate_forbidden_fields(child, f"{path}[{index}]")


def build_profile(
    row: dict[str, str],
    dictionary_rows: list[dict[str, str]],
    links: dict[tuple[str, str], list[dict[str, str]]],
    rules: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, str]], dict[str, str], dict[str, str]]:
    ensembl_id = row["EnsemblID"]
    ordinal = int(row["_universe_ordinal"])
    part = row["_partition_id"]
    identifier = profile_id(ensembl_id)
    feature_objects: list[dict[str, Any]] = []
    all_output_links: list[dict[str, str]] = []
    relationship_digest_items: list[dict[str, str]] = []

    for definition in dictionary_rows:
        name = definition["feature_name"]
        source_links = links.get((ensembl_id, name), [])
        expected_count = len(definition["source_record_roles"].split("|"))
        if len(source_links) != expected_count:
            fail(
                f"Provenance cardinality mismatch at {ensembl_id}/{name}: "
                f"observed={len(source_links)}, expected={expected_count}"
            )
        feature_ids = {link["feature_id"] for link in source_links}
        statuses = {link["feature_missingness_status"] for link in source_links}
        if len(feature_ids) != 1 or len(statuses) != 1:
            fail(f"Feature identity/missingness disagreement at {ensembl_id}/{name}")
        if expected_count > 1:
            dependency_ids = {link["dependency_id"] for link in source_links}
            if len(dependency_ids) != 1 or "NOT_APPLICABLE" in dependency_ids:
                fail(f"Dependent multi-record lineage is incomplete at {ensembl_id}/{name}")
        elif source_links[0]["dependency_id"] != "NOT_APPLICABLE":
            fail(f"Single-record dependency marker changed at {ensembl_id}/{name}")

        embedded: list[dict[str, str]] = []
        for link in source_links:
            item = {
                key: link[key] for key in (
                    "feature_id", "evidence_record_id", "claim_id", "source_id",
                    "artifact_id", "dependency_id", "extraction_rule_id", "extractor_version",
                )
            }
            embedded.append(item)
            relationship_digest_items.append(item)
        feature_objects.append({
            "feature_id": source_links[0]["feature_id"],
            "feature_name": name,
            "value": row[name],
            "data_type": definition["data_type"],
            "missingness_status": source_links[0]["feature_missingness_status"],
            "provenance_links": embedded,
        })

    resolved = resolve_state(row, rules)
    component = {
        "component_id": COMPONENT_ID,
        "component_definition_version": COMPONENT_DEFINITION_VERSION,
        **resolved,
        "features": feature_objects,
    }
    profile = {
        "profile_id": identifier,
        "EnsemblID": ensembl_id,
        "universe_ordinal": ordinal,
        "schema_version": SCHEMA_VERSION,
        "profile_version": PROFILE_VERSION,
        "evidence_snapshot_version": EVIDENCE_SNAPSHOT_VERSION,
        "generator_version": GENERATOR_VERSION,
        "partition_strategy_version": PARTITION_STRATEGY_VERSION,
        "components": [component],
    }
    recursively_validate_forbidden_fields(profile)

    for feature in feature_objects:
        for link in feature["provenance_links"]:
            all_output_links.append({
                "profile_id": identifier,
                "EnsemblID": ensembl_id,
                "universe_ordinal": str(ordinal),
                "partition_id": part,
                "component_id": COMPONENT_ID,
                "component_definition_version": COMPONENT_DEFINITION_VERSION,
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
                "state_rule_id": resolved["state_rule_id"],
                "state_rule_version": resolved["state_rule_version"],
                "generator_version": GENERATOR_VERSION,
                "evidence_snapshot_version": EVIDENCE_SNAPSHOT_VERSION,
            })

    profile_text = canonical_json(profile)
    feature_values = {definition["feature_name"]: row[definition["feature_name"]] for definition in dictionary_rows}
    profile_meta = {
        "EnsemblID": ensembl_id,
        "universe_ordinal": str(ordinal),
        "profile_id": identifier,
        "partition_id": part,
        "profile_content_sha256": sha256_text(profile_text),
        "state": resolved["state"],
    }
    dependency_meta = {
        "profile_id": identifier,
        "EnsemblID": ensembl_id,
        "universe_ordinal": str(ordinal),
        "partition_id": part,
        "feature_row_sha256": sha256_text(canonical_json(feature_values)),
        "provenance_relationship_count": str(len(relationship_digest_items)),
        "provenance_relationships_sha256": sha256_text(canonical_json(relationship_digest_items)),
        "source_feature_artifact_id": SOURCE_FEATURE_ARTIFACT_ID,
        "source_feature_artifact_sha256": EXPECTED_HASHES["task026_features"],
        "source_provenance_artifact_id": SOURCE_PROVENANCE_ARTIFACT_ID,
        "source_provenance_artifact_sha256": EXPECTED_HASHES["task026_provenance"],
        "schema_version": SCHEMA_VERSION,
        "profile_version": PROFILE_VERSION,
        "evidence_snapshot_version": EVIDENCE_SNAPSHOT_VERSION,
        "component_id": COMPONENT_ID,
        "component_definition_version": COMPONENT_DEFINITION_VERSION,
        "state_rule_version": resolved["state_rule_version"],
        "extractor_version": row["extractor_version"],
        "generator_version": GENERATOR_VERSION,
        "partition_strategy_version": PARTITION_STRATEGY_VERSION,
    }
    return profile, all_output_links, profile_meta, dependency_meta


def validate_profile_against_source(
    profile: dict[str, Any],
    source: dict[str, str],
    dictionary_rows: list[dict[str, str]],
) -> None:
    expected_keys = {
        "profile_id", "EnsemblID", "universe_ordinal", "schema_version",
        "profile_version", "evidence_snapshot_version", "generator_version",
        "partition_strategy_version", "components",
    }
    if set(profile) != expected_keys:
        fail(f"Profile schema mismatch at {source['EnsemblID']}")
    if profile["profile_id"] != profile_id(source["EnsemblID"]):
        fail(f"Profile identity mismatch at {source['EnsemblID']}")
    if profile["universe_ordinal"] != int(source["_universe_ordinal"]):
        fail(f"Profile ordinal mismatch at {source['EnsemblID']}")
    if len(profile["components"]) != 1:
        fail(f"Component cardinality mismatch at {source['EnsemblID']}")
    component = profile["components"][0]
    if component["component_id"] != COMPONENT_ID or len(component["features"]) != EXPECTED_FEATURES_PER_PROFILE:
        fail(f"Component schema mismatch at {source['EnsemblID']}")
    expected_names = [row["feature_name"] for row in dictionary_rows]
    observed_names = [feature["feature_name"] for feature in component["features"]]
    if observed_names != expected_names:
        fail(f"Feature order mismatch at {source['EnsemblID']}")
    for feature in component["features"]:
        if feature["value"] != source[feature["feature_name"]]:
            fail(f"Feature value mismatch at {source['EnsemblID']}/{feature['feature_name']}")
        if feature["missingness_status"] not in MISSINGNESS_STATES or not feature["provenance_links"]:
            fail(f"Feature missingness/provenance failure at {source['EnsemblID']}/{feature['feature_name']}")


def write_csv(path: Path, fields: list[str], rows: Iterable[dict[str, str]]) -> int:
    count = 0
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
            count += 1
    return count


def generate_partition(
    directory: Path,
    part: str,
    feature_rows: list[dict[str, str]],
    provenance: dict[tuple[str, str], list[dict[str, str]]],
    dictionary_rows: list[dict[str, str]],
    rules: list[dict[str, Any]],
) -> dict[str, Any]:
    directory.mkdir(parents=True, exist_ok=True)
    profile_path = directory / "profiles.jsonl"
    provenance_path = directory / "profile_provenance_links.csv"
    profile_meta: list[dict[str, str]] = []
    dependency_meta: list[dict[str, str]] = []
    state_counts: Counter[str] = Counter()
    provenance_count = 0
    seen_relationships: set[tuple[str, str]] = set()

    with profile_path.open("w", encoding="utf-8", newline="") as profile_handle, provenance_path.open(
        "w", encoding="utf-8", newline=""
    ) as provenance_handle:
        writer = csv.DictWriter(
            provenance_handle, fieldnames=PROVENANCE_OUTPUT_COLUMNS, lineterminator="\n"
        )
        writer.writeheader()
        for row in feature_rows:
            profile, output_links, meta, dependency = build_profile(
                row, dictionary_rows, provenance, rules
            )
            validate_profile_against_source(profile, row, dictionary_rows)
            profile_handle.write(canonical_json(profile) + "\n")
            for link in output_links:
                composite = (link["feature_id"], link["evidence_record_id"])
                if composite in seen_relationships:
                    fail(f"Duplicate partition relationship at {part}: {composite}")
                seen_relationships.add(composite)
                writer.writerow(link)
                provenance_count += 1
            profile_meta.append(meta)
            dependency_meta.append(dependency)
            state_counts[meta["state"]] += 1

    expected_links = len(feature_rows) * EXPECTED_PROVENANCE_PER_PROFILE
    if provenance_count != expected_links:
        fail(f"Partition {part} provenance count {provenance_count} != {expected_links}")
    return {
        "profile_path": profile_path,
        "provenance_path": provenance_path,
        "profile_count": len(feature_rows),
        "provenance_count": provenance_count,
        "profile_sha256": sha256(profile_path),
        "provenance_sha256": sha256(provenance_path),
        "profile_size": profile_path.stat().st_size,
        "provenance_size": provenance_path.stat().st_size,
        "profile_meta": profile_meta,
        "dependency_meta": dependency_meta,
        "state_counts": dict(sorted(state_counts.items())),
    }


def compare_partition_passes(first: dict[str, Any], second: dict[str, Any], part: str) -> None:
    comparable = (
        "profile_count", "provenance_count", "profile_sha256", "provenance_sha256",
        "profile_size", "provenance_size", "profile_meta", "dependency_meta",
        "state_counts",
    )
    for key in comparable:
        if first[key] != second[key]:
            fail(f"Deterministic partition mismatch at {part}/{key}")


def final_partition_audit(
    profile_path: Path,
    provenance_path: Path,
    feature_rows: list[dict[str, str]],
    provenance: dict[tuple[str, str], list[dict[str, str]]],
    dictionary_rows: list[dict[str, str]],
    rules: list[dict[str, Any]],
) -> tuple[int, int]:
    expected_profile_lines: list[str] = []
    expected_provenance: list[dict[str, str]] = []
    for row in feature_rows:
        profile, links, _, _ = build_profile(row, dictionary_rows, provenance, rules)
        expected_profile_lines.append(canonical_json(profile))
        expected_provenance.extend(links)
    with profile_path.open(encoding="utf-8") as handle:
        observed_lines = [line.rstrip("\n") for line in handle]
    if observed_lines != expected_profile_lines:
        fail(f"Final profile payload differs from exhaustive expected output: {profile_path}")
    for line, source in zip(observed_lines, feature_rows, strict=True):
        validate_profile_against_source(json.loads(line), source, dictionary_rows)
    with provenance_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != PROVENANCE_OUTPUT_COLUMNS:
            fail(f"Final provenance schema mismatch: {provenance_path}")
        observed_provenance = list(reader)
    if observed_provenance != expected_provenance:
        fail(f"Final provenance differs from embedded/source lineage: {provenance_path}")
    return len(observed_lines), len(observed_provenance)


def partition_manifest_rows(
    release_candidate_id: str,
    partition_results: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for part in PARTITION_IDS:
        result = partition_results[part]
        for role in ("PROFILE_PAYLOAD", "PROVENANCE_LINKS"):
            is_profile = role == "PROFILE_PAYLOAD"
            path = (
                Path("outputs/profile_release_candidate_v0.1/profiles") / part / "profiles.jsonl"
                if is_profile else
                Path("outputs/profile_release_candidate_v0.1/provenance") / part / "profile_provenance_links.csv"
            )
            rows.append({
                "release_candidate_id": release_candidate_id,
                "partition_strategy_version": PARTITION_STRATEGY_VERSION,
                "partition_id": part,
                "artifact_role": role,
                "relative_path": path.as_posix(),
                "artifact_id": artifact_id(release_candidate_id, part, role),
                "schema_version": SCHEMA_VERSION if is_profile else "PROFILE_PROVENANCE_LINK_SCHEMA_V0.1",
                "profile_count": str(result["profile_count"]),
                "provenance_link_count": str(result["provenance_count"] if not is_profile else 0),
                "file_size_bytes": str(result["profile_size"] if is_profile else result["provenance_size"]),
                "sha256": result["profile_sha256"] if is_profile else result["provenance_sha256"],
                "generator_version": GENERATOR_VERSION,
                "storage_reference_status": "PENDING_EXTERNALIZATION",
                "storage_reference": "LOCAL_RELEASE_CANDIDATE_ONLY::" + path.as_posix(),
                "validation_status": "PASS",
            })
    return rows


def build_universe_rows(feature_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "EnsemblID": row["EnsemblID"],
            "universe_ordinal": row["_universe_ordinal"],
            "source_feature_artifact_id": SOURCE_FEATURE_ARTIFACT_ID,
            "source_feature_sha256": EXPECTED_HASHES["task026_features"],
            "profile_version": PROFILE_VERSION,
            "evidence_snapshot_version": EVIDENCE_SNAPSHOT_VERSION,
            "partition_strategy_version": PARTITION_STRATEGY_VERSION,
            "partition_id": row["_partition_id"],
        }
        for row in feature_rows
    ]


def build_index_rows(
    profile_meta: list[dict[str, str]],
    release_candidate_id: str,
) -> list[dict[str, str]]:
    rows = sorted(profile_meta, key=lambda row: int(row["universe_ordinal"]))
    return [
        {
            "EnsemblID": row["EnsemblID"],
            "universe_ordinal": row["universe_ordinal"],
            "profile_id": row["profile_id"],
            "profile_version": PROFILE_VERSION,
            "evidence_snapshot_version": EVIDENCE_SNAPSHOT_VERSION,
            "partition_strategy_version": PARTITION_STRATEGY_VERSION,
            "partition_id": row["partition_id"],
            "profile_artifact_id": artifact_id(
                release_candidate_id, row["partition_id"], "PROFILE_PAYLOAD"
            ),
            "profile_content_sha256": row["profile_content_sha256"],
            "component_set": COMPONENT_ID,
        }
        for row in rows
    ]


def build_audit_sample(
    index_rows: list[dict[str, str]],
    release_candidate_id: str,
) -> list[dict[str, str]]:
    sample_size = math.ceil(0.01 * len(index_rows))
    if sample_size != EXPECTED_AUDIT_SAMPLE:
        fail(f"Audit sample size {sample_size} != {EXPECTED_AUDIT_SAMPLE}")
    keyed = sorted(
        (
            sha256_text(f"{release_candidate_id}|{row['EnsemblID']}"), row
        )
        for row in index_rows
    )[:sample_size]
    return [
        {
            "audit_sequence": str(index),
            "EnsemblID": row["EnsemblID"],
            "profile_id": row["profile_id"],
            "partition_id": row["partition_id"],
            "audit_key": key,
            "selection_rule_id": "SHA256_RELEASE_ID_ENSEMBL_LOWEST_1_PERCENT_V0.1",
        }
        for index, (key, row) in enumerate(keyed, start=1)
    ]


def combined_partition_hash(
    partition_results: dict[str, dict[str, Any]], role: str
) -> str:
    key = "profile_sha256" if role == "PROFILE_PAYLOAD" else "provenance_sha256"
    return sha256_text(canonical_json([
        {"partition_id": part, "sha256": partition_results[part][key]}
        for part in PARTITION_IDS
    ]))


def validation_rows(
    state_counts: Counter[str],
    populated_partitions: int,
    state_fixture_count: int,
    partition_fixture_count: int,
) -> list[dict[str, str]]:
    checks = [
        ("VAL_UNIVERSE_COUNT", "UNIVERSE", EXPECTED_PROFILES, EXPECTED_PROFILES, "Complete Task #026 universe retained."),
        ("VAL_UNIQUE_IDENTITY", "IDENTITY", EXPECTED_PROFILES, EXPECTED_PROFILES, "Unique immutable EnsemblID profiles."),
        ("VAL_PROFILE_FEATURE_COUNT", "FEATURE_FIDELITY", EXPECTED_PROFILE_FEATURES, EXPECTED_PROFILE_FEATURES, "Every exact Task #026 feature represented."),
        ("VAL_PROVENANCE_COUNT", "PROVENANCE", EXPECTED_PROVENANCE_LINKS, EXPECTED_PROVENANCE_LINKS, "Complete uncompressed lineage."),
        ("VAL_IDENTITY_MISMATCH", "IDENTITY", 0, 0, "No profile/source identity mismatch."),
        ("VAL_FEATURE_MISMATCH", "FEATURE_FIDELITY", 0, 0, "No source/profile value mismatch."),
        ("VAL_PROVENANCE_MISMATCH", "PROVENANCE", 0, 0, "No embedded/tabular/source lineage mismatch."),
        ("VAL_DEPENDENCY_CONFLICT", "DEPENDENCY", 0, 0, "Governed multi-record dependency identifiers preserved."),
        ("VAL_STATE_MISMATCH", "STATE_REPRODUCTION", 0, 0, "Frozen Task #025 state outputs reproduced."),
        ("VAL_PARTITION_COUNT", "PARTITION", populated_partitions, 256, "All deterministic prefix partitions populated."),
        ("VAL_PARTITION_DETERMINISM", "DETERMINISM", 256, 256, "Every partition generated twice byte-identically."),
        ("VAL_STATE_FIXTURES", "BOUNDARY_FIXTURES", state_fixture_count, 5, "All five structural state boundaries pass."),
        ("VAL_PARTITION_FIXTURES", "BOUNDARY_FIXTURES", partition_fixture_count, 4, "Frozen partition fixtures pass."),
        ("VAL_AUDIT_SAMPLE", "SAMPLING", EXPECTED_AUDIT_SAMPLE, EXPECTED_AUDIT_SAMPLE, "Deterministic 1% audit sample manifest."),
        ("VAL_FORBIDDEN_FIELDS", "INTERPRETATION_BOUNDARY", 0, 0, "No evaluative fields in profiles."),
    ]
    rows = [
        {
            "check_id": check_id,
            "category": category,
            "status": "PASS" if observed == expected else "FAIL",
            "observed": str(observed),
            "expected": str(expected),
            "notes": notes,
        }
        for check_id, category, observed, expected, notes in checks
    ]
    rows.append({
        "check_id": "VAL_STATE_COUNTS",
        "category": "STATE_REPRODUCTION",
        "status": "PASS",
        "observed": canonical_json(dict(sorted(state_counts.items()))),
        "expected": "COUNTS_DERIVED_FROM_FROZEN_RULES",
        "notes": "Structural state counts are audit metadata, not evaluation.",
    })
    if any(row["status"] != "PASS" for row in rows):
        fail("One or more full-universe validation checks failed.")
    return rows


def validation_report_text(
    release_candidate_id: str,
    state_counts: Counter[str],
    profile_bytes: int,
    provenance_bytes: int,
    profile_set_hash: str,
    provenance_set_hash: str,
) -> str:
    return f"""# Task #030 full profile release-candidate validation report

## Scope

This release candidate materializes structural evidence profiles for the complete frozen Task #026 EnsemblID universe. It does not score, rank, prioritize, select, recommend, or biologically interpret targets.

## Release-candidate identity

- Release candidate: `{release_candidate_id}`
- Profiles: **{EXPECTED_PROFILES:,}**
- Canonical order: exact Task #026 feature-row order
- Profile version: `{PROFILE_VERSION}`
- Schema version: `{SCHEMA_VERSION}`
- Evidence snapshot: `{EVIDENCE_SNAPSHOT_VERSION}`
- Component: `{COMPONENT_ID}`
- Generator: `{GENERATOR_VERSION}`
- Partition strategy: `{PARTITION_STRATEGY_VERSION}`
- Lifecycle: `{LIFECYCLE_STATUS}`

## Materialization summary

- Profile feature values: **{EXPECTED_PROFILE_FEATURES:,}**
- Record-level provenance relationships: **{EXPECTED_PROVENANCE_LINKS:,}**
- Profile partitions: **256**
- Provenance partitions: **256**
- Structural state counts: `{canonical_json(dict(sorted(state_counts.items())))}`
- Profile partition bytes: **{profile_bytes:,}**
- Provenance partition bytes: **{provenance_bytes:,}**
- Profile partition-set SHA256: `{profile_set_hash}`
- Provenance partition-set SHA256: `{provenance_set_hash}`

## Validation

- Universe identity, cardinality, and canonical order: **PASS**.
- Full profile schema and version axes: **PASS**.
- All feature values identical to Task #026: **PASS**.
- Complete embedded and tabular provenance equivalence: **PASS**.
- Composite provenance-key uniqueness: **PASS**.
- Governed dependency identifiers: **PASS**.
- Task #025 state reproduction and precedence: **PASS**.
- All 256 partition assignments and global reconciliation: **PASS**.
- Per-partition two-pass byte-identical generation: **PASS**.
- Five state-boundary and four partition fixtures: **PASS**.
- Deterministic 297-profile audit-sample manifest: **PASS**.
- Frozen input hashes unchanged after generation: **PASS**.
- Runtime AI/LLM decisions, mutable retrieval, scoring, ranking, selection, recommendation, and biological interpretation: **NOT USED / NOT GENERATED**.

## Governance limits

This is a local release candidate, not a lifecycle promotion. External immutable storage references are pending, the Task #025 rules remain awaiting independent scientific review, and deterministic sampling identifies records for a future human traceability audit but does not itself complete that audit. Full-universe materialization validates infrastructure conformance only; it does not validate any target scientifically.
"""


def write_metadata_once(
    directory: Path,
    release_candidate_id: str,
    input_manifest: dict[str, dict[str, Any]],
    repository: dict[str, str],
    schema: dict[str, Any],
    universe_rows: list[dict[str, str]],
    index_rows: list[dict[str, str]],
    partition_rows: list[dict[str, str]],
    dependency_rows: list[dict[str, str]],
    audit_rows: list[dict[str, str]],
    checks: list[dict[str, str]],
    report_text: str,
    partition_results: dict[str, dict[str, Any]],
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "profile_schema_v0.1.json").write_text(pretty_json(schema), encoding="utf-8")
    write_csv(directory / "universe_manifest.csv", UNIVERSE_COLUMNS, universe_rows)
    write_csv(directory / "profile_index.csv", INDEX_COLUMNS, index_rows)
    write_csv(directory / "partition_manifest.csv", PARTITION_COLUMNS, partition_rows)
    write_csv(directory / "dependency_manifest.csv", DEPENDENCY_COLUMNS, dependency_rows)
    write_csv(directory / "deterministic_audit_sample.csv", AUDIT_COLUMNS, audit_rows)
    write_csv(directory / "validation_results.csv", VALIDATION_COLUMNS, checks)
    (directory / "validation_report.md").write_text(report_text, encoding="utf-8")

    governed_names = (
        "profile_schema_v0.1.json", "universe_manifest.csv", "profile_index.csv",
        "partition_manifest.csv", "dependency_manifest.csv",
        "deterministic_audit_sample.csv", "validation_results.csv",
        "validation_report.md",
    )
    metadata_artifacts = [
        {
            "relative_path": f"outputs/profile_release_candidate_v0.1/{name}",
            "file_size_bytes": (directory / name).stat().st_size,
            "sha256": sha256(directory / name),
        }
        for name in governed_names
    ]
    profile_bytes = sum(result["profile_size"] for result in partition_results.values())
    provenance_bytes = sum(result["provenance_size"] for result in partition_results.values())
    manifest = {
        "manifest_version": "FULL_PROFILE_RELEASE_CANDIDATE_MANIFEST_V0.1",
        "release_candidate_id": release_candidate_id,
        "release_candidate_status": "VALIDATED_LOCAL_CANDIDATE",
        "lifecycle_status": LIFECYCLE_STATUS,
        "human_governance_promotion_recorded": False,
        "schema_version": SCHEMA_VERSION,
        "profile_version": PROFILE_VERSION,
        "evidence_snapshot_version": EVIDENCE_SNAPSHOT_VERSION,
        "component_definition_versions": {COMPONENT_ID: COMPONENT_DEFINITION_VERSION},
        "state_rule_version": "STATE_RULE_REGISTRY_V0.1",
        "extractor_version": "TRANSCRIPTOMIC_FEATURE_EXTRACTOR_V0.1",
        "generator_version": GENERATOR_VERSION,
        "partition_strategy_version": PARTITION_STRATEGY_VERSION,
        "immutable_key": "EnsemblID",
        "canonical_order": "TASK026_TRANSCRIPTOMIC_FEATURE_ROW_ORDER",
        "counts": {
            "profiles": EXPECTED_PROFILES,
            "profile_features": EXPECTED_PROFILE_FEATURES,
            "provenance_relationships": EXPECTED_PROVENANCE_LINKS,
            "profile_partitions": 256,
            "provenance_partitions": 256,
            "deterministic_audit_sample": EXPECTED_AUDIT_SAMPLE,
        },
        "partition_sets": {
            "profile_partition_set_sha256": combined_partition_hash(partition_results, "PROFILE_PAYLOAD"),
            "profile_partition_total_bytes": profile_bytes,
            "provenance_partition_set_sha256": combined_partition_hash(partition_results, "PROVENANCE_LINKS"),
            "provenance_partition_total_bytes": provenance_bytes,
            "external_storage_status": "PENDING_EXTERNALIZATION",
        },
        "input_artifacts": [input_manifest[key] for key in sorted(input_manifest)],
        "metadata_artifacts": metadata_artifacts,
        "validation_status": "PASS",
        "governance_limitations": [
            "No lifecycle promotion is assigned by materialization.",
            "External immutable storage references remain pending.",
            "Task #025 state rules retain awaiting independent scientific review status.",
            "The deterministic audit sample awaits human traceability review.",
        ],
        "prohibitions": [
            "NO_SCORING", "NO_RANKING", "NO_PRIORITY", "NO_TARGET_SELECTION",
            "NO_RECOMMENDATIONS", "NO_BIOLOGICAL_INTERPRETATION",
            "NO_THERAPEUTIC_CONCLUSIONS", "NO_LLM_RUNTIME_DECISIONS",
        ],
    }
    (directory / "release_manifest.json").write_text(pretty_json(manifest), encoding="utf-8")
    session_lines = [
        "task=030",
        "purpose=full-universe deterministic structural evidence-profile materialization",
        f"release_candidate_id={release_candidate_id}",
        f"lifecycle_status={LIFECYCLE_STATUS}",
        f"schema_version={SCHEMA_VERSION}",
        f"profile_version={PROFILE_VERSION}",
        f"evidence_snapshot_version={EVIDENCE_SNAPSHOT_VERSION}",
        f"component_definition_version={COMPONENT_DEFINITION_VERSION}",
        f"generator_version={GENERATOR_VERSION}",
        f"partition_strategy_version={PARTITION_STRATEGY_VERSION}",
        f"frozen_task029_base_commit={TASK029_BASE_COMMIT}",
        f"git_branch={repository['branch']}",
        f"git_origin={repository['remote']}",
        f"python_implementation={platform.python_implementation()}",
        f"python_version={platform.python_version()}",
        f"platform={platform.platform()}",
        f"script_sha256={sha256(SCRIPT_PATH)}",
        f"profile_count={EXPECTED_PROFILES}",
        f"profile_feature_count={EXPECTED_PROFILE_FEATURES}",
        f"provenance_relationship_count={EXPECTED_PROVENANCE_LINKS}",
        "partition_count=256",
        f"audit_sample_count={EXPECTED_AUDIT_SAMPLE}",
        "immutable_key=EnsemblID",
        "gene_symbols_used_as_keys=FALSE",
        "network_access=NOT_USED",
        "packages_installed_or_updated=FALSE",
        "randomness_used=FALSE",
        "wall_clock_values_in_outputs=FALSE",
        "llm_runtime_decisions=FALSE",
        "scoring_generated=FALSE",
        "ranking_generated=FALSE",
        "target_selection_generated=FALSE",
        "recommendations_generated=FALSE",
        "biological_interpretations_generated=FALSE",
        "per_partition_two_pass_determinism=PASS",
        "complete_automated_validation=PASS",
        "external_storage_status=PENDING_EXTERNALIZATION",
    ]
    for key in sorted(input_manifest):
        item = input_manifest[key]
        session_lines.append(
            f"frozen_input_sha256.{item['relative_path']}={item['sha256']}"
        )
    for name in (*governed_names, "release_manifest.json"):
        session_lines.append(
            f"output_sha256.outputs/profile_release_candidate_v0.1/{name}={sha256(directory / name)}"
        )
    (directory / "session_info.txt").write_text(
        "\n".join(session_lines) + "\n", encoding="utf-8"
    )


def compare_metadata(first: Path, second: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for name in METADATA_NAMES:
        first_hash = sha256(first / name)
        second_hash = sha256(second / name)
        if first_hash != second_hash:
            fail(f"Deterministic metadata mismatch: {name}")
        hashes[name] = first_hash
    return hashes


def main() -> None:
    repository = validate_repository()
    input_manifest = validate_inputs()
    dictionary_rows, dictionary = load_dictionary()
    feature_rows, features_by_id, features_by_partition = load_features(dictionary_rows)
    rules = load_rules(dictionary)
    state_fixture_count = validate_state_fixtures(rules)
    partition_fixture_count = validate_partition_fixtures()
    schema = build_schema()
    recursively_validate_forbidden_fields(schema)
    release_candidate_id = stable_id(
        "PRC",
        canonical_json({
            "profile_version": PROFILE_VERSION,
            "schema_version": SCHEMA_VERSION,
            "evidence_snapshot_version": EVIDENCE_SNAPSHOT_VERSION,
            "generator_version": GENERATOR_VERSION,
            "partition_strategy_version": PARTITION_STRATEGY_VERSION,
            "input_hashes": EXPECTED_HASHES,
        }),
    )

    if OUTPUT_DIR.exists():
        existing = {
            path.relative_to(OUTPUT_DIR).as_posix()
            for path in OUTPUT_DIR.rglob("*") if path.is_file()
        }
        allowed_existing = set(METADATA_NAMES)
        allowed_existing |= {
            f"profiles/{part}/profiles.jsonl" for part in PARTITION_IDS
        }
        allowed_existing |= {
            f"provenance/{part}/profile_provenance_links.csv" for part in PARTITION_IDS
        }
        unexpected = sorted(existing - allowed_existing)
        if unexpected:
            fail("Unexpected existing Task #030 files: " + ", ".join(unexpected))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    PROVENANCE_DIR.mkdir(parents=True, exist_ok=True)

    partition_results: dict[str, dict[str, Any]] = {}
    all_profile_meta: list[dict[str, str]] = []
    all_dependency_meta: list[dict[str, str]] = []
    state_counts: Counter[str] = Counter()
    exhaustive_profiles = exhaustive_provenance = 0

    with tempfile.TemporaryDirectory(prefix="task030_") as temp_name:
        temp_root = Path(temp_name)
        raw_shards = temp_root / "raw_provenance"
        shard_provenance(raw_shards, features_by_id)

        for part in PARTITION_IDS:
            rows = features_by_partition[part]
            if not rows:
                fail(f"Frozen full universe unexpectedly has empty partition {part}")
            provenance = load_provenance_shard(raw_shards / f"{part}.csv", dictionary)
            first = generate_partition(
                temp_root / "pass_a" / part, part, rows, provenance,
                dictionary_rows, rules,
            )
            second = generate_partition(
                temp_root / "pass_b" / part, part, rows, provenance,
                dictionary_rows, rules,
            )
            compare_partition_passes(first, second, part)

            final_profile_dir = PROFILES_DIR / part
            final_provenance_dir = PROVENANCE_DIR / part
            final_profile_dir.mkdir(parents=True, exist_ok=True)
            final_provenance_dir.mkdir(parents=True, exist_ok=True)
            final_profile_path = final_profile_dir / "profiles.jsonl"
            final_provenance_path = final_provenance_dir / "profile_provenance_links.csv"
            shutil.copyfile(first["profile_path"], final_profile_path)
            shutil.copyfile(first["provenance_path"], final_provenance_path)
            if sha256(final_profile_path) != first["profile_sha256"] or sha256(final_provenance_path) != first["provenance_sha256"]:
                fail(f"Copied partition hash mismatch at {part}")

            audited_profiles, audited_provenance = final_partition_audit(
                final_profile_path, final_provenance_path, rows, provenance,
                dictionary_rows, rules,
            )
            exhaustive_profiles += audited_profiles
            exhaustive_provenance += audited_provenance
            result = {
                key: first[key] for key in (
                    "profile_count", "provenance_count", "profile_sha256",
                    "provenance_sha256", "profile_size", "provenance_size",
                    "profile_meta", "dependency_meta", "state_counts",
                )
            }
            partition_results[part] = result
            all_profile_meta.extend(result["profile_meta"])
            all_dependency_meta.extend(result["dependency_meta"])
            state_counts.update(result["state_counts"])

        if exhaustive_profiles != EXPECTED_PROFILES or exhaustive_provenance != EXPECTED_PROVENANCE_LINKS:
            fail(
                f"Exhaustive final audit counts failed: profiles={exhaustive_profiles}, "
                f"provenance={exhaustive_provenance}"
            )
        if sum(state_counts.values()) != EXPECTED_PROFILES:
            fail("Structural state counts do not reconcile to the universe.")

        universe_rows = build_universe_rows(feature_rows)
        index_rows = build_index_rows(all_profile_meta, release_candidate_id)
        dependency_rows = sorted(
            all_dependency_meta, key=lambda row: int(row["universe_ordinal"])
        )
        if [row["EnsemblID"] for row in universe_rows] != [row["EnsemblID"] for row in index_rows]:
            fail("Universe and profile-index identity/order differ.")
        if len(dependency_rows) != EXPECTED_PROFILES:
            fail("Dependency manifest profile count mismatch.")
        partition_rows = partition_manifest_rows(release_candidate_id, partition_results)
        audit_rows = build_audit_sample(index_rows, release_candidate_id)
        populated_partitions = sum(bool(features_by_partition[part]) for part in PARTITION_IDS)
        checks = validation_rows(
            state_counts, populated_partitions, state_fixture_count,
            partition_fixture_count,
        )
        profile_bytes = sum(result["profile_size"] for result in partition_results.values())
        provenance_bytes = sum(result["provenance_size"] for result in partition_results.values())
        profile_set_hash = combined_partition_hash(partition_results, "PROFILE_PAYLOAD")
        provenance_set_hash = combined_partition_hash(partition_results, "PROVENANCE_LINKS")
        report_text = validation_report_text(
            release_candidate_id, state_counts, profile_bytes, provenance_bytes,
            profile_set_hash, provenance_set_hash,
        )

        metadata_a = temp_root / "metadata_a"
        metadata_b = temp_root / "metadata_b"
        write_metadata_once(
            metadata_a, release_candidate_id, input_manifest, repository, schema,
            universe_rows, index_rows, partition_rows, dependency_rows, audit_rows,
            checks, report_text, partition_results,
        )
        write_metadata_once(
            metadata_b, release_candidate_id, input_manifest, repository, schema,
            universe_rows, index_rows, partition_rows, dependency_rows, audit_rows,
            checks, report_text, partition_results,
        )
        metadata_hashes = compare_metadata(metadata_a, metadata_b)
        for name in METADATA_NAMES:
            shutil.copyfile(metadata_a / name, OUTPUT_DIR / name)
            if sha256(OUTPUT_DIR / name) != metadata_hashes[name]:
                fail(f"Copied metadata hash mismatch: {name}")

    expected_files = set(METADATA_NAMES)
    expected_files |= {f"profiles/{part}/profiles.jsonl" for part in PARTITION_IDS}
    expected_files |= {
        f"provenance/{part}/profile_provenance_links.csv" for part in PARTITION_IDS
    }
    observed_files = {
        path.relative_to(OUTPUT_DIR).as_posix()
        for path in OUTPUT_DIR.rglob("*") if path.is_file()
    }
    if observed_files != expected_files:
        fail(
            f"Final release-candidate file inventory mismatch: "
            f"missing={sorted(expected_files-observed_files)}, "
            f"extra={sorted(observed_files-expected_files)}"
        )
    validate_inputs()
    validate_repository()

    profile_bytes = sum(result["profile_size"] for result in partition_results.values())
    provenance_bytes = sum(result["provenance_size"] for result in partition_results.values())
    print(f"Release candidate: {release_candidate_id}")
    print(f"Profiles: {EXPECTED_PROFILES}; features: {EXPECTED_PROFILE_FEATURES}; provenance links: {EXPECTED_PROVENANCE_LINKS}")
    print(f"Structural states: {canonical_json(dict(sorted(state_counts.items())))}")
    print(f"Profile partitions: 256 ({profile_bytes} bytes)")
    print(f"Provenance partitions: 256 ({provenance_bytes} bytes)")
    print(f"Profile partition-set SHA256: {combined_partition_hash(partition_results, 'PROFILE_PAYLOAD')}")
    print(f"Provenance partition-set SHA256: {combined_partition_hash(partition_results, 'PROVENANCE_LINKS')}")
    print("Universe, schema, feature, provenance, dependency, state, partition, and deterministic validation: PASS")
    print(f"Lifecycle: {LIFECYCLE_STATUS}; external storage: PENDING_EXTERNALIZATION")
    print("Scoring, ranking, selection, recommendation, interpretation, and LLM runtime decisions: NOT GENERATED")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise
