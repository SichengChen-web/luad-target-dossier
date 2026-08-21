#!/usr/bin/env python3
"""Build the Task #011 Open Targets tractability and safety evidence layer."""

from __future__ import annotations

import csv
import hashlib
import http.client
import json
import math
import platform
import re
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK010_COMMIT = "072f1e88b08a32077cc44596ad3a6c0235f7d7c5"
EXPECTED_ROWS = 29_606
EXPECTED_U2 = 14_064

PRIMARY_INPUT = Path("outputs/evidence_layer/evidence_registry.csv")
MAPPING_INPUT = Path("outputs/identifier_normalization/identifier_mapping.csv")
CANDIDATE_INPUT = Path("outputs/candidate_registry/candidate_registry.csv")
INPUT_HASHES = {
    PRIMARY_INPUT: "13b6db140c920a60ae3f827ac9df4c4e08916472aa8daafb349acd3a60192405",
    MAPPING_INPUT: "ff50b9cc50006710e681bd0d0f21fa3790becc3cd20a476dbbb6ac5459c1594e",
    CANDIDATE_INPUT: "8055a9d99d058d219399957e62f6a3cccc3dd2217bc028d1d11dd4dc667f90e2",
}

SCRIPT = Path("analysis/11_build_tractability_safety_layer.py")
PLAN = Path("docs/tractability_safety_plan_v0.1.md")
OUTPUT_DIR = Path("outputs/tractability_safety")
REGISTRY = OUTPUT_DIR / "tractability_safety_registry.csv"
TRACTABILITY = OUTPUT_DIR / "tractability_assessments.csv"
SAFETY = OUTPUT_DIR / "safety_liabilities.csv"
QC = OUTPUT_DIR / "tractability_safety_qc.csv"
SUMMARY = OUTPUT_DIR / "tractability_safety_summary.md"
SCHEMA = OUTPUT_DIR / "open_targets_schema_snapshot.json"
SESSION = OUTPUT_DIR / "session_info.txt"

OT_URL = "https://api.platform.opentargets.org/api/v4/graphql"
OT_SOURCE = "OPEN_TARGETS_PLATFORM_GRAPHQL"
USER_AGENT = "luad-target-dossier-task-011/0.1"
BATCH_SIZE = 500

SCHEMA_QUERY = """
query Task011Schema {
  meta { name product apiVersion { x y z suffix } dataVersion { year month iteration } }
  targetType: __type(name: "Target") { name kind fields { name type { kind name ofType { kind name ofType { kind name ofType { kind name } } } } } }
  tractabilityType: __type(name: "Tractability") { name kind fields { name type { kind name ofType { kind name ofType { kind name ofType { kind name } } } } } }
  safetyType: __type(name: "SafetyLiability") { name kind fields { name type { kind name ofType { kind name ofType { kind name ofType { kind name } } } } } }
  safetyEffectsType: __type(name: "SafetyEffects") { name kind fields { name type { kind name ofType { kind name ofType { kind name } } } } }
  safetyBiosampleType: __type(name: "SafetyBiosample") { name kind fields { name type { kind name ofType { kind name ofType { kind name } } } } }
  safetyStudyType: __type(name: "SafetyStudy") { name kind fields { name type { kind name ofType { kind name ofType { kind name } } } } }
}
""".strip()

TARGET_QUERY = """
query Task011TargetEvidence($ids: [String!]!) {
  targets(ensemblIds: $ids) {
    id
    tractability { label modality value }
    safetyLiabilities {
      url
      literature
      effects { direction dosing }
      biosamples { cellFormat cellLabel cellId tissueLabel tissueId }
      event
      eventId
      studies { description type name }
      datasource
    }
  }
}
""".strip()

REQUIRED_SCHEMA = {
    "Target": {
        "id": "String!",
        "tractability": "[Tractability!]!",
        "safetyLiabilities": "[SafetyLiability!]!",
    },
    "Tractability": {"label": "String!", "modality": "String!", "value": "Boolean!"},
    "SafetyLiability": {
        "url": "String",
        "literature": "String",
        "effects": "[SafetyEffects!]",
        "biosamples": "[SafetyBiosample!]",
        "event": "String",
        "eventId": "String",
        "studies": "[SafetyStudy!]",
        "datasource": "String!",
    },
    "SafetyEffects": {"direction": "String!", "dosing": "String"},
    "SafetyBiosample": {
        "cellFormat": "String",
        "cellLabel": "String",
        "cellId": "String",
        "tissueLabel": "String",
        "tissueId": "String",
    },
    "SafetyStudy": {"description": "String", "type": "String", "name": "String"},
}

ALLOWED_UNTRACKED = {str(SCRIPT), str(PLAN)}
ALLOWED_OUTPUT_PREFIX = f"{OUTPUT_DIR}/"
FORBIDDEN_OUTPUT_TERMS = {
    "project_score",
    "safety_score",
    "tractability_score",
    "priority",
    "target_rank",
    "recommendation",
    "therapeutic_direction",
}


def fail(message: str) -> None:
    raise RuntimeError(message)


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(["git", *args], text=True, capture_output=True, check=False)
    if check and result.returncode != 0:
        fail(
            f"Git command failed: git {' '.join(args)}\n"
            f"stdout: {result.stdout.strip()}\nstderr: {result.stderr.strip()}"
        )
    return result.stdout.strip()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def make_tls_context() -> tuple[ssl.SSLContext, str]:
    candidates = [
        ssl.get_default_verify_paths().cafile,
        "/etc/ssl/cert.pem",
        "/etc/ssl/certs/ca-certificates.crt",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return ssl.create_default_context(cafile=candidate), candidate
    return ssl.create_default_context(), "PYTHON_DEFAULT_CA_PATHS"


TLS_CONTEXT, TLS_CA_FILE = make_tls_context()


def validate_repository() -> dict[str, str]:
    root = Path(git("rev-parse", "--show-toplevel")).resolve()
    if root != Path.cwd().resolve():
        fail(f"Run from repository root {root}; observed {Path.cwd().resolve()}")
    branch = git("branch", "--show-current")
    if branch != "main":
        fail(f"Task #011 requires branch main; observed {branch!r}")
    head = git("rev-parse", "HEAD")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", TASK010_COMMIT, head],
        capture_output=True,
        text=True,
        check=False,
    )
    if ancestor.returncode != 0:
        fail(f"Frozen Task #010 commit {TASK010_COMMIT} is not an ancestor of HEAD {head}")
    remote = git("remote", "get-url", "origin")
    if not re.search(r"(?:github\.com[:/])SichengChen-web/luad-target-dossier(?:\.git)?$", remote):
        fail(f"Unexpected origin remote: {remote}")
    if subprocess.run(["git", "diff", "--quiet"], check=False).returncode != 0:
        fail("Unexpected tracked working-tree modifications are present")
    if subprocess.run(["git", "diff", "--cached", "--quiet"], check=False).returncode != 0:
        fail("Unexpected staged modifications are present")
    untracked = git("ls-files", "--others", "--exclude-standard").splitlines()
    unexpected = [
        path
        for path in untracked
        if path not in ALLOWED_UNTRACKED and not path.startswith(ALLOWED_OUTPUT_PREFIX)
    ]
    if unexpected:
        fail("Unexpected untracked files are present: " + ", ".join(unexpected))

    for path, expected_hash in INPUT_HASHES.items():
        if not path.is_file():
            fail(f"Required frozen input is missing: {path}")
        if subprocess.run(
            ["git", "ls-files", "--error-unmatch", str(path)],
            capture_output=True,
            text=True,
            check=False,
        ).returncode != 0:
            fail(f"Required frozen input is not committed: {path}")
        if subprocess.run(
            ["git", "diff", "--quiet", TASK010_COMMIT, "--", str(path)],
            capture_output=True,
            text=True,
            check=False,
        ).returncode != 0:
            fail(f"Required input differs from frozen Task #010 commit: {path}")
        observed = file_sha256(path)
        if observed != expected_hash:
            fail(f"SHA256 mismatch for {path}: {observed} != {expected_hash}")
    return {"root": str(root), "branch": branch, "head": head, "remote": remote}


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            fail(f"CSV has no header: {path}")
        return list(reader.fieldnames), list(reader)


def load_inputs() -> tuple[list[dict[str, str]], list[str]]:
    primary_header, primary = read_csv(PRIMARY_INPUT)
    mapping_header, mapping = read_csv(MAPPING_INPUT)
    candidate_header, candidates = read_csv(CANDIDATE_INPUT)
    primary_required = {
        "EnsemblID", "EnsemblID_base", "Symbol", "gene_type",
        "U2_effect_supported_DE", "OpenTargets_target_ID",
    }
    mapping_required = {
        "EnsemblID", "EnsemblID_base", "Symbol", "gene_type",
        "OpenTargets_target_ID", "OpenTargets_target_ID_status",
    }
    candidate_required = {"EnsemblID", "U2_effect_supported_DE"}
    for label, header, required in (
        ("Task #010 primary input", primary_header, primary_required),
        ("Task #009 mapping input", mapping_header, mapping_required),
        ("Task #008 candidate input", candidate_header, candidate_required),
    ):
        missing = required.difference(header)
        if missing:
            fail(f"{label} lacks required columns: {sorted(missing)}")
    for label, rows in (
        ("Task #010 primary input", primary),
        ("Task #009 mapping input", mapping),
        ("Task #008 candidate input", candidates),
    ):
        if len(rows) != EXPECTED_ROWS:
            fail(f"{label} has {len(rows)} rows; expected {EXPECTED_ROWS}")

    primary_ids = [row["EnsemblID"] for row in primary]
    mapping_ids = [row["EnsemblID"] for row in mapping]
    candidate_ids = [row["EnsemblID"] for row in candidates]
    if len(set(primary_ids)) != EXPECTED_ROWS:
        fail("Task #010 primary input contains duplicate EnsemblID values")
    if primary_ids != mapping_ids or primary_ids != candidate_ids:
        fail("Frozen inputs differ in EnsemblID identity or row order")

    for p_row, m_row, c_row in zip(primary, mapping, candidates, strict=True):
        for field in ("EnsemblID", "EnsemblID_base", "Symbol", "gene_type", "OpenTargets_target_ID"):
            if p_row[field] != m_row[field]:
                fail(f"Primary/mapping mismatch for {field} at {p_row['EnsemblID']}")
        if p_row["U2_effect_supported_DE"] != c_row["U2_effect_supported_DE"]:
            fail(f"Primary/candidate U2 mismatch at {p_row['EnsemblID']}")
        if p_row["U2_effect_supported_DE"] not in {"TRUE", "FALSE"}:
            fail(f"Invalid U2 flag at {p_row['EnsemblID']}")
        ot_id = m_row["OpenTargets_target_ID"]
        if ot_id == "NOT_FOUND":
            if m_row["OpenTargets_target_ID_status"] != "NOT_FOUND":
                fail(f"Inconsistent missing Open Targets mapping at {p_row['EnsemblID']}")
        elif ot_id != m_row["EnsemblID_base"]:
            fail(f"Open Targets ID is not the mapped base Ensembl ID at {p_row['EnsemblID']}")

    u2_count = sum(row["U2_effect_supported_DE"] == "TRUE" for row in primary)
    if u2_count != EXPECTED_U2:
        fail(f"Primary input has {u2_count} U2 genes; expected {EXPECTED_U2}")
    mapped_ids = sorted({row["OpenTargets_target_ID"] for row in mapping if row["OpenTargets_target_ID"] != "NOT_FOUND"})
    return primary, mapped_ids


class ResponseTracker:
    def __init__(self) -> None:
        self.digest = hashlib.sha256()
        self.records: list[dict[str, Any]] = []

    def add(self, label: str, body: bytes) -> None:
        response_hash = hashlib.sha256(body).hexdigest()
        self.digest.update(body)
        self.records.append({"label": label, "bytes": len(body), "sha256": response_hash})

    def metadata(self) -> dict[str, Any]:
        return {
            "request_count": len(self.records),
            "response_bytes": sum(row["bytes"] for row in self.records),
            "sha256_concatenated_responses": self.digest.hexdigest(),
            "response_sha256_by_request_json": json.dumps(self.records, separators=(",", ":"), sort_keys=True),
        }


def request_bytes(payload: dict[str, Any], tracker: ResponseTracker, label: str) -> bytes:
    data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        OT_URL,
        data=data,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    last_error: Exception | None = None
    for attempt in range(1, 6):
        try:
            with urllib.request.urlopen(request, timeout=300, context=TLS_CONTEXT) as response:
                body = response.read()
                if not body:
                    fail(f"Empty Open Targets response for {label}")
                tracker.add(label, body)
                return body
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code not in {429, 500, 502, 503, 504} or attempt == 5:
                break
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            delay = float(retry_after) if retry_after and retry_after.isdigit() else 2 ** attempt
            time.sleep(min(delay, 30))
        except (
            urllib.error.URLError,
            http.client.RemoteDisconnected,
            ConnectionResetError,
            TimeoutError,
        ) as exc:
            last_error = exc
            if attempt == 5:
                break
            time.sleep(min(2 ** attempt, 30))
    fail(f"Open Targets request failed after 5 attempts for {label}: {last_error}")


def graphql(query: str, variables: dict[str, Any], tracker: ResponseTracker, label: str) -> dict[str, Any]:
    body = request_bytes({"query": query, "variables": variables}, tracker, label)
    try:
        result = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Invalid JSON from Open Targets for {label}") from exc
    if not isinstance(result, dict) or result.get("errors"):
        fail(f"Open Targets GraphQL errors for {label}: {result.get('errors') if isinstance(result, dict) else result!r}")
    data = result.get("data")
    if not isinstance(data, dict):
        fail(f"Open Targets response lacks data for {label}")
    return data


def format_api_version(value: Any) -> str:
    if not isinstance(value, dict) or any(value.get(key) is None for key in ("x", "y", "z")):
        fail("Open Targets API version is unavailable")
    return f"{value['x']}.{value['y']}.{value['z']}{value.get('suffix') or ''}"


def format_data_version(value: Any) -> str:
    if not isinstance(value, dict) or value.get("year") is None or value.get("month") is None:
        fail("Open Targets data version is unavailable")
    base = f"{value['year']}.{int(value['month']):02d}"
    iteration = value.get("iteration")
    return base if iteration in (None, 0, "0") else f"{base}.{iteration}"


def format_graphql_type(value: Any) -> str:
    if not isinstance(value, dict) or not isinstance(value.get("kind"), str):
        fail(f"Malformed GraphQL type description: {value!r}")
    kind = value["kind"]
    if kind == "NON_NULL":
        return f"{format_graphql_type(value.get('ofType'))}!"
    if kind == "LIST":
        return f"[{format_graphql_type(value.get('ofType'))}]"
    name = value.get("name")
    if not isinstance(name, str):
        fail(f"Unnamed terminal GraphQL type: {value!r}")
    return name


def inspect_schema(tracker: ResponseTracker) -> tuple[dict[str, Any], dict[str, Any]]:
    data = graphql(SCHEMA_QUERY, {}, tracker, "metadata and focused schema introspection")
    meta = data.get("meta")
    if not isinstance(meta, dict):
        fail("Open Targets metadata is unavailable")
    source = {
        "name": meta.get("name"),
        "product": meta.get("product"),
        "api_version": format_api_version(meta.get("apiVersion")),
        "data_version": format_data_version(meta.get("dataVersion")),
        "url": OT_URL,
    }
    aliases = {
        "Target": "targetType",
        "Tractability": "tractabilityType",
        "SafetyLiability": "safetyType",
        "SafetyEffects": "safetyEffectsType",
        "SafetyBiosample": "safetyBiosampleType",
        "SafetyStudy": "safetyStudyType",
    }
    observed: dict[str, dict[str, str]] = {}
    for type_name, alias in aliases.items():
        type_info = data.get(alias)
        if not isinstance(type_info, dict) or type_info.get("name") != type_name:
            fail(f"Required Open Targets GraphQL type is unavailable: {type_name}")
        fields = type_info.get("fields")
        if not isinstance(fields, list):
            fail(f"GraphQL type {type_name} has no field list")
        all_fields = {
            field.get("name"): format_graphql_type(field.get("type"))
            for field in fields
            if isinstance(field, dict) and isinstance(field.get("name"), str)
        }
        observed[type_name] = {}
        for field_name, expected_type in REQUIRED_SCHEMA[type_name].items():
            actual_type = all_fields.get(field_name)
            if actual_type is None:
                fail(f"Required GraphQL field is unavailable: {type_name}.{field_name}")
            if actual_type != expected_type:
                fail(
                    f"GraphQL field type changed for {type_name}.{field_name}: "
                    f"observed {actual_type}, expected {expected_type}"
                )
            observed[type_name][field_name] = actual_type
    snapshot = {
        "task": "011",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "schema_query_sha256": text_sha256(SCHEMA_QUERY),
        "target_evidence_query_sha256": text_sha256(TARGET_QUERY),
        "types_and_fields_used": observed,
    }
    return source, snapshot


def require_nullable_string(value: Any, label: str) -> None:
    if value is not None and not isinstance(value, str):
        fail(f"{label} is not String/null: {value!r}")


def validate_object_array(value: Any, fields: dict[str, bool], label: str) -> None:
    if value is None:
        return
    if not isinstance(value, list):
        fail(f"{label} is not list/null")
    for index, row in enumerate(value, start=1):
        if not isinstance(row, dict):
            fail(f"{label}[{index}] is not an object")
        for field, required in fields.items():
            item = row.get(field)
            if required and not isinstance(item, str):
                fail(f"{label}[{index}].{field} is not a required String")
            require_nullable_string(item, f"{label}[{index}].{field}")


def validate_tractability(record: Any, target_id: str, index: int) -> dict[str, Any]:
    if not isinstance(record, dict):
        fail(f"Malformed tractability record for {target_id} at index {index}")
    label = record.get("label")
    modality = record.get("modality")
    value = record.get("value")
    if not isinstance(label, str) or not label:
        fail(f"Invalid tractability label for {target_id} at index {index}")
    if not isinstance(modality, str) or not modality:
        fail(f"Invalid tractability modality for {target_id} at index {index}")
    if not isinstance(value, bool):
        fail(f"Invalid tractability Boolean for {target_id} at index {index}")
    return {"label": label, "modality": modality, "value": value}


def validate_safety(record: Any, target_id: str, index: int) -> dict[str, Any]:
    if not isinstance(record, dict):
        fail(f"Malformed safety-liability record for {target_id} at index {index}")
    for field in ("url", "literature", "event", "eventId"):
        require_nullable_string(record.get(field), f"{target_id} safety[{index}].{field}")
    if not isinstance(record.get("datasource"), str) or not record["datasource"]:
        fail(f"Missing safety datasource for {target_id} at index {index}")
    validate_object_array(record.get("effects"), {"direction": True, "dosing": False}, f"{target_id} safety[{index}].effects")
    validate_object_array(
        record.get("biosamples"),
        {"cellFormat": False, "cellLabel": False, "cellId": False, "tissueLabel": False, "tissueId": False},
        f"{target_id} safety[{index}].biosamples",
    )
    validate_object_array(
        record.get("studies"),
        {"description": False, "type": False, "name": False},
        f"{target_id} safety[{index}].studies",
    )
    return record


def retrieve_target_evidence(
    identifiers: list[str], tracker: ResponseTracker
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    submitted = set(identifiers)
    output: dict[str, dict[str, Any]] = {}
    for start in range(0, len(identifiers), BATCH_SIZE):
        batch = identifiers[start : start + BATCH_SIZE]
        data = graphql(
            TARGET_QUERY,
            {"ids": batch},
            tracker,
            f"target tractability/safety batch {start // BATCH_SIZE + 1}",
        )
        targets = data.get("targets")
        if not isinstance(targets, list):
            fail("Open Targets target evidence response lacks a targets list")
        for target in targets:
            if not isinstance(target, dict) or not isinstance(target.get("id"), str):
                fail("Malformed Open Targets target evidence record")
            target_id = target["id"]
            if target_id not in submitted:
                fail(f"Open Targets returned unsubmitted target ID: {target_id}")
            if target_id in output:
                fail(f"Open Targets returned duplicate target ID: {target_id}")
            tractability = target.get("tractability")
            safety = target.get("safetyLiabilities")
            if not isinstance(tractability, list) or not isinstance(safety, list):
                fail(f"Required target evidence arrays are unavailable for {target_id}")
            output[target_id] = {
                "tractability": [
                    validate_tractability(record, target_id, index)
                    for index, record in enumerate(tractability, start=1)
                ],
                "safetyLiabilities": [
                    validate_safety(record, target_id, index)
                    for index, record in enumerate(safety, start=1)
                ],
            }
    return output, {
        "submitted_target_ids": len(identifiers),
        "returned_target_ids": len(output),
        "target_batch_size": BATCH_SIZE,
        "target_batch_count": math.ceil(len(identifiers) / BATCH_SIZE),
    }


def deterministic_json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True, ensure_ascii=False)


def scalar_or_not_available(value: Any) -> str:
    return "NOT_AVAILABLE" if value is None else str(value)


def build_outputs(
    primary: list[dict[str, str]],
    targets: dict[str, dict[str, Any]],
    source_release: str,
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], set[str]]:
    registry_rows: list[dict[str, str]] = []
    tract_rows: list[dict[str, str]] = []
    safety_rows: list[dict[str, str]] = []
    modalities: set[str] = set()

    for source in primary:
        identity = {
            "EnsemblID": source["EnsemblID"],
            "EnsemblID_base": source["EnsemblID_base"],
            "OpenTargets_target_ID": source["OpenTargets_target_ID"],
            "U2_effect_supported_DE": source["U2_effect_supported_DE"],
        }
        ot_id = source["OpenTargets_target_ID"]
        target = None if ot_id == "NOT_FOUND" else targets.get(ot_id)
        if ot_id == "NOT_FOUND":
            tract_status = "TARGET_NOT_MAPPED"
            safety_status = "TARGET_NOT_MAPPED"
            tractability: list[dict[str, Any]] = []
            liabilities: list[dict[str, Any]] = []
        elif target is None:
            tract_status = "API_FIELD_NOT_AVAILABLE_OR_RETRIEVAL_FAILURE"
            safety_status = "API_FIELD_NOT_AVAILABLE_OR_RETRIEVAL_FAILURE"
            tractability = []
            liabilities = []
        else:
            tractability = target["tractability"]
            liabilities = target["safetyLiabilities"]
            tract_status = "TRACTABILITY_RECORD_PRESENT" if tractability else "TARGET_PRESENT_NO_TRACTABILITY_RECORD_RETURNED"
            safety_status = "SAFETY_RECORD_PRESENT" if liabilities else "TARGET_PRESENT_NO_SAFETY_RECORD_RETURNED"

        true_by_modality: Counter[str] = Counter()
        positive_ids: defaultdict[str, list[str]] = defaultdict(list)
        if tractability:
            for index, assessment in enumerate(tractability, start=1):
                modality = assessment["modality"]
                modalities.add(modality)
                if assessment["value"]:
                    true_by_modality[modality] += 1
                    positive_ids[modality].append(assessment["label"])
                tract_rows.append(
                    {
                        **identity,
                        "tractability_retrieval_status": tract_status,
                        "assessment_record_index": str(index),
                        "modality": modality,
                        "assessment_id": assessment["label"],
                        "assessment_value": "TRUE" if assessment["value"] else "FALSE",
                        "source_name": OT_SOURCE,
                        "source_release": source_release,
                    }
                )
        else:
            tract_rows.append(
                {
                    **identity,
                    "tractability_retrieval_status": tract_status,
                    "assessment_record_index": "NOT_AVAILABLE",
                    "modality": "NOT_AVAILABLE",
                    "assessment_id": "NOT_AVAILABLE",
                    "assessment_value": "NOT_AVAILABLE",
                    "source_name": OT_SOURCE,
                    "source_release": source_release,
                }
            )

        if liabilities:
            for index, liability in enumerate(liabilities, start=1):
                safety_rows.append(
                    {
                        **identity,
                        "safety_retrieval_status": safety_status,
                        "safety_record_index": str(index),
                        "event": scalar_or_not_available(liability.get("event")),
                        "event_id": scalar_or_not_available(liability.get("eventId")),
                        "datasource": liability["datasource"],
                        "literature": scalar_or_not_available(liability.get("literature")),
                        "source_url": scalar_or_not_available(liability.get("url")),
                        "effects_json": deterministic_json(liability.get("effects")),
                        "biosamples_json": deterministic_json(liability.get("biosamples")),
                        "studies_json": deterministic_json(liability.get("studies")),
                        "source_record_json": deterministic_json(liability),
                        "source_name": OT_SOURCE,
                        "source_release": source_release,
                    }
                )
        else:
            safety_rows.append(
                {
                    **identity,
                    "safety_retrieval_status": safety_status,
                    "safety_record_index": "NOT_AVAILABLE",
                    "event": "NOT_AVAILABLE",
                    "event_id": "NOT_AVAILABLE",
                    "datasource": "NOT_AVAILABLE",
                    "literature": "NOT_AVAILABLE",
                    "source_url": "NOT_AVAILABLE",
                    "effects_json": "NOT_AVAILABLE",
                    "biosamples_json": "NOT_AVAILABLE",
                    "studies_json": "NOT_AVAILABLE",
                    "source_record_json": "NOT_AVAILABLE",
                    "source_name": OT_SOURCE,
                    "source_release": source_release,
                }
            )

        registry_rows.append(
            {
                "EnsemblID": source["EnsemblID"],
                "EnsemblID_base": source["EnsemblID_base"],
                "Symbol": source["Symbol"],
                "gene_type": source["gene_type"],
                "U2_effect_supported_DE": source["U2_effect_supported_DE"],
                "OpenTargets_target_ID": ot_id,
                "tractability_retrieval_status": tract_status,
                "tractability_record_count": str(len(tractability)),
                "tractability_true_assessment_count": str(sum(true_by_modality.values())),
                "tractability_true_SM_count": str(true_by_modality["SM"]),
                "tractability_true_AB_count": str(true_by_modality["AB"]),
                "tractability_true_PR_count": str(true_by_modality["PR"]),
                "tractability_true_OC_count": str(true_by_modality["OC"]),
                "tractability_true_assessment_ids_by_modality_json": deterministic_json(
                    {key: sorted(value) for key, value in sorted(positive_ids.items())}
                ),
                "safety_retrieval_status": safety_status,
                "safety_liability_record_count": str(len(liabilities)),
                "source_name": OT_SOURCE,
                "source_release": source_release,
            }
        )
    return registry_rows, tract_rows, safety_rows, modalities


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        fail(f"Refusing to write empty CSV: {path}")
    fields = list(rows[0])
    if any(list(row) != fields for row in rows):
        fail(f"Inconsistent output fields for {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def percent(numerator: int, denominator: int) -> str:
    return format(100 * numerator / denominator, ".6f") if denominator else "NOT_AVAILABLE"


def make_qc_rows(
    primary: list[dict[str, str]],
    registry: list[dict[str, str]],
    tract_rows: list[dict[str, str]],
    safety_rows: list[dict[str, str]],
    modalities: set[str],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    def add(category: str, scope: str, metric: str, value: int | str, denominator: int | str = "NOT_APPLICABLE", status: str = "INFO", detail: str = "") -> None:
        numeric_denominator = denominator if isinstance(denominator, int) else None
        numeric_value = value if isinstance(value, int) else None
        rows.append(
            {
                "category": category,
                "scope": scope,
                "metric": metric,
                "value": str(value),
                "denominator": str(denominator),
                "percent": percent(numeric_value, numeric_denominator) if numeric_value is not None and numeric_denominator is not None else "NOT_APPLICABLE",
                "status": status,
                "detail": detail,
            }
        )

    ids = [row["EnsemblID"] for row in registry]
    add("ASSERTION", "ALL_TESTED", "REGISTRY_ROW_COUNT", len(registry), EXPECTED_ROWS, "PASS" if len(registry) == EXPECTED_ROWS else "FAIL")
    add("ASSERTION", "ALL_TESTED", "UNIQUE_ENSEMBL_ID_COUNT", len(set(ids)), EXPECTED_ROWS, "PASS" if len(set(ids)) == EXPECTED_ROWS else "FAIL")
    add("ASSERTION", "ALL_TESTED", "INPUT_ORDER_AND_IDENTITY_PRESERVED", str(ids == [row["EnsemblID"] for row in primary]).upper(), status="PASS" if ids == [row["EnsemblID"] for row in primary] else "FAIL")
    u2_total = sum(row["U2_effect_supported_DE"] == "TRUE" for row in registry)
    add("ASSERTION", "U2_EFFECT_SUPPORTED_DE", "U2_GENE_COUNT", u2_total, EXPECTED_U2, "PASS" if u2_total == EXPECTED_U2 else "FAIL")
    add("ASSERTION", "ALL_TESTED", "SYMBOL_USED_AS_QUERY_KEY", "FALSE", status="PASS")
    add("ASSERTION", "ALL_TESTED", "RANKING_OR_PROJECT_SCORE_GENERATED", "FALSE", status="PASS")
    add("ASSERTION", "ALL_TESTED", "THERAPEUTIC_RECOMMENDATION_GENERATED", "FALSE", status="PASS")

    for scope, selected in (
        ("ALL_TESTED", registry),
        ("U2_EFFECT_SUPPORTED_DE", [row for row in registry if row["U2_effect_supported_DE"] == "TRUE"]),
    ):
        denominator = len(selected)
        selected_ids = {row["EnsemblID"] for row in selected}
        status_counts = Counter(row["tractability_retrieval_status"] for row in selected)
        safety_status_counts = Counter(row["safety_retrieval_status"] for row in selected)
        add("COVERAGE", scope, "OPEN_TARGETS_IDENTIFIER_MAPPED", sum(row["OpenTargets_target_ID"] != "NOT_FOUND" for row in selected), denominator)
        for status, count in sorted(status_counts.items()):
            add("TRACTABILITY", scope, f"TARGET_STATUS_{status}", count, denominator)
        add("TRACTABILITY", scope, "SOURCE_ASSESSMENT_RECORD_COUNT", sum(int(row["tractability_record_count"]) for row in selected))
        add("TRACTABILITY", scope, "SOURCE_TRUE_ASSESSMENT_COUNT", sum(int(row["tractability_true_assessment_count"]) for row in selected))
        for modality in sorted(modalities):
            source_records = [
                row for row in tract_rows
                if row["EnsemblID"] in selected_ids and row["modality"] == modality
            ]
            add("TRACTABILITY", scope, f"ASSESSMENT_RECORD_MODALITY_{modality}", len(source_records))
            for value in ("FALSE", "TRUE"):
                add("TRACTABILITY", scope, f"ASSESSMENT_RECORD_MODALITY_{modality}_VALUE_{value}", sum(row["assessment_value"] == value for row in source_records))
            add("TRACTABILITY", scope, f"TARGET_WITH_TRUE_MODALITY_{modality}", len({row["EnsemblID"] for row in source_records if row["assessment_value"] == "TRUE"}), denominator)
        for status, count in sorted(safety_status_counts.items()):
            add("SAFETY", scope, f"TARGET_STATUS_{status}", count, denominator)
        source_safety = [
            row for row in safety_rows
            if row["EnsemblID"] in selected_ids and row["safety_record_index"] != "NOT_AVAILABLE"
        ]
        add("SAFETY", scope, "SOURCE_LIABILITY_RECORD_COUNT", len(source_safety))
        for datasource, count in sorted(Counter(row["datasource"] for row in source_safety).items()):
            add("SAFETY", scope, f"DATASOURCE_RECORD_COUNT_{datasource}", count)
    return rows


def markdown_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    output = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    output.extend("| " + " | ".join(str(value).replace("|", "\\|") for value in row) + " |" for row in rows)
    return output


def write_summary(
    registry: list[dict[str, str]],
    tract_rows: list[dict[str, str]],
    safety_rows: list[dict[str, str]],
    source: dict[str, Any],
    modalities: set[str],
) -> None:
    lines = [
        "# Task #011 tractability and target-safety evidence summary",
        "",
        f"**Open Targets Platform data release:** {source['data_version']}  ",
        f"**Open Targets API version:** {source['api_version']}  ",
        f"**Genes retained:** {len(registry):,}  ",
        f"**U2 genes retained:** {sum(row['U2_effect_supported_DE'] == 'TRUE' for row in registry):,}",
        "",
        "## Interpretation boundary",
        "",
        "This layer preserves source-native Open Targets tractability assessments and safety-liability records. It does not rank, score, prioritize, recommend, or infer therapeutic direction. A positive tractability assessment is modality-relevant evidence, not proof that a target should be pursued. The number of positive buckets is not a project score.",
        "",
        "**Absence of a curated safety-liability record is absence of retrieved evidence, not evidence of safety.** Presence of a liability is likewise not an automatic reason to reject a target.",
        "",
        "## Tractability retrieval",
        "",
    ]
    tract_summary: list[list[Any]] = []
    for scope, selected in (
        ("All tested genes", registry),
        ("U2 genes", [row for row in registry if row["U2_effect_supported_DE"] == "TRUE"]),
    ):
        tract_summary.append([
            scope,
            len(selected),
            sum(row["OpenTargets_target_ID"] != "NOT_FOUND" for row in selected),
            sum(row["tractability_retrieval_status"] == "TRACTABILITY_RECORD_PRESENT" for row in selected),
            sum(int(row["tractability_record_count"]) for row in selected),
            sum(int(row["tractability_true_assessment_count"]) for row in selected),
        ])
    lines.extend(markdown_table(["Scope", "Genes", "Mapped targets", "Targets with assessment records", "Assessment records", "TRUE assessment records"], tract_summary))
    lines.extend(["", "Source-native modality/assessment-value counts:", ""])
    modality_rows: list[list[Any]] = []
    for modality in sorted(modalities):
        records = [row for row in tract_rows if row["modality"] == modality]
        modality_rows.append([modality, len(records), sum(row["assessment_value"] == "TRUE" for row in records), sum(row["assessment_value"] == "FALSE" for row in records)])
    lines.extend(markdown_table(["Modality", "Records", "TRUE", "FALSE"], modality_rows))

    lines.extend(["", "## Safety-liability retrieval", ""])
    safety_summary: list[list[Any]] = []
    for scope, selected in (
        ("All tested genes", registry),
        ("U2 genes", [row for row in registry if row["U2_effect_supported_DE"] == "TRUE"]),
    ):
        safety_summary.append([
            scope,
            len(selected),
            sum(row["safety_retrieval_status"] == "SAFETY_RECORD_PRESENT" for row in selected),
            sum(row["safety_retrieval_status"] == "TARGET_PRESENT_NO_SAFETY_RECORD_RETURNED" for row in selected),
            sum(int(row["safety_liability_record_count"]) for row in selected),
        ])
    lines.extend(markdown_table(["Scope", "Genes", "Targets with record(s)", "Mapped targets with zero records", "Safety-liability records"], safety_summary))
    source_safety = [row for row in safety_rows if row["safety_record_index"] != "NOT_AVAILABLE"]
    lines.extend(["", "Safety datasource record counts:", ""])
    lines.extend(markdown_table(["Datasource", "Records"], [[key, value] for key, value in sorted(Counter(row["datasource"] for row in source_safety).items())]))

    lines.extend([
        "",
        "## Missingness",
        "",
        "`TARGET_NOT_MAPPED` means Task #009 provided no Open Targets target ID. `TARGET_PRESENT_NO_SAFETY_RECORD_RETURNED` means the mapped target was returned but its current safety-liability array was empty; it does not mean safe or low risk. `SAFETY_RECORD_PRESENT` means at least one source record was returned. `API_FIELD_NOT_AVAILABLE_OR_RETRIEVAL_FAILURE` is reserved for a missing required field or failed/missing target retrieval.",
        "",
        "The long-form tables include explicit placeholder rows for genes without source records. Placeholder rows are not counted as tractability assessments or safety liabilities.",
        "",
        "## Evidence-overlap warning",
        "",
        "Open Targets tractability assessments may incorporate source data such as ChEMBL and clinical precedence. They must not be assumed independent of Task #010 drug/candidate counts or future ChEMBL clinical-development evidence. Task #011 stores the source-native assessment records only.",
        "",
        "## Schema and provenance",
        "",
        "The builder first introspected the deployed GraphQL types and failed unless all required fields and types matched the focused schema. Exact used fields/types, query hashes, release metadata, request/response counts, byte counts, response hashes, timestamps, input hashes, and output hashes are recorded in the schema snapshot and session file. No raw response dump was saved.",
        "",
        "## Non-claims",
        "",
        "No target score, tractability score, safety score, priority, rank, recommendation, therapeutic direction, or biological interpretation was generated.",
    ])
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate_outputs(
    primary: list[dict[str, str]],
    registry: list[dict[str, str]],
    tract_rows: list[dict[str, str]],
    safety_rows: list[dict[str, str]],
    mapped_ids: list[str],
    retrieval_meta: dict[str, Any],
    qc_rows: list[dict[str, str]],
) -> None:
    if len(registry) != EXPECTED_ROWS or len({row["EnsemblID"] for row in registry}) != EXPECTED_ROWS:
        fail("Gene-level registry row/uniqueness assertion failed")
    if [row["EnsemblID"] for row in registry] != [row["EnsemblID"] for row in primary]:
        fail("Gene-level registry did not preserve input EnsemblID order")
    if sum(row["U2_effect_supported_DE"] == "TRUE" for row in registry) != EXPECTED_U2:
        fail("Gene-level registry U2 assertion failed")
    queried_from_mapping = {row["OpenTargets_target_ID"] for row in primary if row["OpenTargets_target_ID"] != "NOT_FOUND"}
    if queried_from_mapping != set(mapped_ids) or retrieval_meta["submitted_target_ids"] != len(mapped_ids):
        fail("Open Targets query identifiers did not come exactly from Task #009 mapping")
    if {row["EnsemblID"] for row in tract_rows} != set(row["EnsemblID"] for row in registry):
        fail("Tractability long table does not represent every gene")
    if {row["EnsemblID"] for row in safety_rows} != set(row["EnsemblID"] for row in registry):
        fail("Safety long table does not represent every gene")
    headers = set(registry[0]) | set(tract_rows[0]) | set(safety_rows[0])
    forbidden = FORBIDDEN_OUTPUT_TERMS.intersection({field.lower() for field in headers})
    if forbidden:
        fail(f"Forbidden ranking/scoring fields were generated: {sorted(forbidden)}")
    if any(row["status"] == "FAIL" for row in qc_rows):
        fail("One or more QC assertions failed")


def flatten_metadata(prefix: str, value: Any) -> list[str]:
    lines: list[str] = []
    if isinstance(value, dict):
        for key in sorted(value):
            lines.extend(flatten_metadata(f"{prefix}.{key}" if prefix else key, value[key]))
    else:
        lines.append(f"{prefix}={value}")
    return lines


def write_session(
    started: datetime,
    repo: dict[str, str],
    source: dict[str, Any],
    tracker: ResponseTracker,
    retrieval_meta: dict[str, Any],
) -> None:
    finished = datetime.now(timezone.utc)
    output_hashes = {
        str(path): file_sha256(path)
        for path in (REGISTRY, TRACTABILITY, SAFETY, QC, SUMMARY, SCHEMA)
    }
    metadata = {
        "Task #011 tractability and target-safety evidence retrieval session": "",
        "started_at_utc": started.isoformat(),
        "finished_at_utc": finished.isoformat(),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "tls_ca_file": TLS_CA_FILE,
        "git_branch": repo["branch"],
        "git_head": repo["head"],
        "frozen_task010_commit": TASK010_COMMIT,
        "git_origin": repo["remote"],
        "network_access": "USED",
        "network_hosts": "api.platform.opentargets.org",
        "packages_installed_or_updated": "FALSE",
        "gene_symbols_used_as_query_keys": "FALSE",
        "raw_api_responses_committed": "FALSE",
        "project_score_generated": "FALSE",
        "ranking_generated": "FALSE",
        "therapeutic_recommendation_generated": "FALSE",
        "open_targets": {
            **source,
            "schema_query_sha256": text_sha256(SCHEMA_QUERY),
            "target_evidence_query_sha256": text_sha256(TARGET_QUERY),
            "retrieval": retrieval_meta,
            "responses": tracker.metadata(),
        },
        "frozen_inputs_sha256": {str(path): INPUT_HASHES[path] for path in INPUT_HASHES},
        "script_sha256": file_sha256(SCRIPT),
        "plan_sha256": file_sha256(PLAN),
        "output_sha256": output_hashes,
    }
    lines = flatten_metadata("", metadata)
    SESSION.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    started = datetime.now(timezone.utc)
    repo = validate_repository()
    primary, mapped_ids = load_inputs()
    tracker = ResponseTracker()
    source, schema_snapshot = inspect_schema(tracker)
    targets, retrieval_meta = retrieve_target_evidence(mapped_ids, tracker)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SCHEMA.write_text(deterministic_json(schema_snapshot) + "\n", encoding="utf-8")
    registry, tract_rows, safety_rows, modalities = build_outputs(primary, targets, source["data_version"])
    qc_rows = make_qc_rows(primary, registry, tract_rows, safety_rows, modalities)
    validate_outputs(primary, registry, tract_rows, safety_rows, mapped_ids, retrieval_meta, qc_rows)
    write_csv(REGISTRY, registry)
    write_csv(TRACTABILITY, tract_rows)
    write_csv(SAFETY, safety_rows)
    write_csv(QC, qc_rows)
    write_summary(registry, tract_rows, safety_rows, source, modalities)
    write_session(started, repo, source, tracker, retrieval_meta)

    print(f"Open Targets data release: {source['data_version']}")
    print(f"Open Targets API version: {source['api_version']}")
    print(f"Mapped targets queried: {len(mapped_ids)}")
    print(f"Mapped targets returned: {len(targets)}")
    print(f"Registry rows: {len(registry)}")
    print(f"Tractability long rows: {len(tract_rows)}")
    print(f"Safety-liability long rows: {len(safety_rows)}")
    print(f"Observed modality codes: {','.join(sorted(modalities))}")
    print("All Task #011 assertions passed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
