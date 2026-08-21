#!/usr/bin/env python3
"""Build the Task #010 source-native external evidence layer."""

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
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK009_COMMIT = "436436715af43a0dc69a6a51acf82b435f65cf6c"
INPUT_SHA256 = "ff50b9cc50006710e681bd0d0f21fa3790becc3cd20a476dbbb6ac5459c1594e"
U2_REFERENCE_SHA256 = "8055a9d99d058d219399957e62f6a3cccc3dd2217bc028d1d11dd4dc667f90e2"
EXPECTED_ROWS = 29_606
EXPECTED_U2 = 14_064

INPUT = Path("outputs/identifier_normalization/identifier_mapping.csv")
U2_REFERENCE = Path("outputs/candidate_registry/candidate_registry.csv")
PLAN = Path("docs/evidence_layer_plan_v0.1.md")
OUTPUT_DIR = Path("outputs/evidence_layer")
REGISTRY = OUTPUT_DIR / "evidence_registry.csv"
QC = OUTPUT_DIR / "evidence_qc.csv"
SUMMARY = OUTPUT_DIR / "evidence_summary.md"
SESSION = OUTPUT_DIR / "session_info.txt"

OT_URL = "https://api.platform.opentargets.org/api/v4/graphql"
CHEMBL_TARGET_URL = "https://www.ebi.ac.uk/chembl/api/data/target.json"
CHEMBL_STATUS_URL = "https://www.ebi.ac.uk/chembl/api/data/status.json"
LUAD_ID = "MONDO_0005061"
LUAD_NAME = "lung adenocarcinoma"
OT_SOURCE = "OPEN_TARGETS_PLATFORM_GRAPHQL"
CHEMBL_SOURCE = "CHEMBL_TARGET_API"
USER_AGENT = "luad-target-dossier-task-010/0.1"

OT_META_QUERY = (
    "query($diseaseId:String!){meta{name product apiVersion{x y z suffix} "
    "dataVersion{year month iteration}} disease(efoId:$diseaseId){id name}}"
)
OT_TARGET_QUERY = (
    "query($ids:[String!]!){targets(ensemblIds:$ids){id approvedName "
    "approvedSymbol biotype literatureOcurrences{count filteredCount} "
    "drugAndClinicalCandidates{count}}}"
)
OT_ASSOCIATION_QUERY = (
    "query($diseaseId:String!,$indirect:Boolean!,$pageIndex:Int!,$pageSize:Int!){"
    "disease(efoId:$diseaseId){id name associatedTargets(enableIndirect:$indirect,"
    "orderByScore:\"score\",page:{index:$pageIndex,size:$pageSize}){count "
    "rows{score target{id} "
    "datasourceScores{id score} datatypeScores{id score}}}}}"
)

ALLOWED_UNTRACKED = {
    "analysis/10_build_evidence_layer.py",
    "docs/evidence_layer_plan_v0.1.md",
}
ALLOWED_OUTPUT_PREFIX = "outputs/evidence_layer/"


def fail(message: str) -> None:
    raise RuntimeError(message)


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args], text=True, capture_output=True, check=False
    )
    if check and result.returncode != 0:
        fail(
            f"Git command failed: git {' '.join(args)}\n"
            f"stdout: {result.stdout.strip()}\n"
            f"stderr: {result.stderr.strip()}"
        )
    return result.stdout.strip()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
        fail(f"Task #010 requires branch main; observed {branch!r}")
    head = git("rev-parse", "HEAD")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", TASK009_COMMIT, head],
        capture_output=True,
        text=True,
        check=False,
    )
    if ancestor.returncode != 0:
        fail(f"Frozen Task #009 commit {TASK009_COMMIT} is not an ancestor of HEAD {head}")
    remote = git("remote", "get-url", "origin")
    if not re.search(
        r"(?:github\.com[:/])SichengChen-web/luad-target-dossier(?:\.git)?$", remote
    ):
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

    for path, expected_hash in (
        (INPUT, INPUT_SHA256),
        (U2_REFERENCE, U2_REFERENCE_SHA256),
    ):
        if not path.is_file():
            fail(f"Required frozen file is missing: {path}")
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", str(path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if tracked.returncode != 0:
            fail(f"Required frozen file is not committed: {path}")
        unchanged = subprocess.run(
            ["git", "diff", "--quiet", TASK009_COMMIT, "--", str(path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if unchanged.returncode != 0:
            fail(f"Required file differs from frozen Task #009 commit: {path}")
        observed_hash = file_sha256(path)
        if observed_hash != expected_hash:
            fail(f"SHA256 mismatch for {path}: {observed_hash} != {expected_hash}")
    return {"root": str(root), "branch": branch, "head": head, "remote": remote}


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            fail(f"CSV has no header: {path}")
        return list(reader.fieldnames), list(reader)


def load_inputs() -> tuple[list[dict[str, str]], set[str]]:
    header, mapping = read_csv(INPUT)
    required = {
        "EnsemblID",
        "EnsemblID_base",
        "Symbol",
        "gene_type",
        "OpenTargets_target_ID",
        "OpenTargets_target_ID_status",
        "ChEMBL_target_ID",
        "ChEMBL_target_ID_status",
    }
    missing = required.difference(header)
    if missing:
        fail(f"Task #009 input lacks required columns: {sorted(missing)}")
    if len(mapping) != EXPECTED_ROWS:
        fail(f"Task #009 input has {len(mapping)} rows; expected {EXPECTED_ROWS}")
    mapping_ids = [row["EnsemblID"] for row in mapping]
    if len(set(mapping_ids)) != EXPECTED_ROWS:
        fail("Task #009 input contains duplicate EnsemblID values")

    ref_header, reference = read_csv(U2_REFERENCE)
    if "EnsemblID" not in ref_header or "U2_effect_supported_DE" not in ref_header:
        fail("U2 reference lacks EnsemblID or U2_effect_supported_DE")
    if len(reference) != EXPECTED_ROWS:
        fail(f"U2 reference has {len(reference)} rows; expected {EXPECTED_ROWS}")
    reference_ids = [row["EnsemblID"] for row in reference]
    if reference_ids != mapping_ids:
        fail("Task #009 input and U2 reference identifiers/order differ")
    u2_ids = {
        row["EnsemblID"]
        for row in reference
        if row["U2_effect_supported_DE"] == "TRUE"
    }
    invalid_flags = {
        row["U2_effect_supported_DE"]
        for row in reference
        if row["U2_effect_supported_DE"] not in {"TRUE", "FALSE"}
    }
    if invalid_flags:
        fail(f"Invalid U2 reference flags: {sorted(invalid_flags)}")
    if len(u2_ids) != EXPECTED_U2:
        fail(f"U2 reference contains {len(u2_ids)} genes; expected {EXPECTED_U2}")
    return mapping, u2_ids


class ResponseTracker:
    def __init__(self, source: str) -> None:
        self.source = source
        self.digest = hashlib.sha256()
        self.request_count = 0
        self.byte_count = 0

    def add(self, body: bytes) -> None:
        self.digest.update(body)
        self.request_count += 1
        self.byte_count += len(body)

    def metadata(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "request_count": self.request_count,
            "response_bytes": self.byte_count,
            "sha256_concatenated_responses": self.digest.hexdigest(),
        }


def request_bytes(
    url: str,
    tracker: ResponseTracker,
    *,
    payload: dict[str, Any] | None = None,
    timeout: int = 300,
    attempts: int = 5,
) -> bytes:
    data = None
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(
        url, data=data, headers=headers, method="POST" if data else "GET"
    )
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(
                request, timeout=timeout, context=TLS_CONTEXT
            ) as response:
                body = response.read()
                if not body:
                    fail(f"Empty response from {url}")
                tracker.add(body)
                return body
        except urllib.error.HTTPError as exc:
            last_error = exc
            retryable = exc.code in {429, 500, 502, 503, 504}
            if not retryable or attempt == attempts:
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
            if attempt == attempts:
                break
            time.sleep(min(2 ** attempt, 30))
    fail(f"Network request failed after {attempts} attempts: {url}: {last_error}")


def parse_json(body: bytes, source: str) -> dict[str, Any]:
    try:
        value = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Invalid JSON from {source}") from exc
    if not isinstance(value, dict):
        fail(f"Unexpected JSON root from {source}")
    return value


def graphql(
    query: str,
    variables: dict[str, Any],
    tracker: ResponseTracker,
    label: str,
) -> dict[str, Any]:
    body = request_bytes(
        OT_URL, tracker, payload={"query": query, "variables": variables}
    )
    result = parse_json(body, label)
    if result.get("errors"):
        fail(f"Open Targets GraphQL errors for {label}: {result['errors']}")
    data = result.get("data")
    if not isinstance(data, dict):
        fail(f"Open Targets response lacks data object for {label}")
    return data


def format_ot_api_version(value: Any) -> str:
    if not isinstance(value, dict) or any(value.get(k) is None for k in ("x", "y", "z")):
        return "NOT_PROVIDED"
    return f"{value['x']}.{value['y']}.{value['z']}{value.get('suffix') or ''}"


def format_ot_data_version(value: Any) -> str:
    if not isinstance(value, dict) or value.get("year") is None or value.get("month") is None:
        return "NOT_PROVIDED"
    base = f"{value['year']}.{int(value['month']):02d}"
    iteration = value.get("iteration")
    return base if iteration in (None, 0, "0") else f"{base}.{iteration}"


def validate_nonnegative_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        fail(f"{label} is not a non-negative integer: {value!r}")
    return value


def validate_score(value: Any, label: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        fail(f"{label} is not numeric: {value!r}")
    result = float(value)
    if not math.isfinite(result) or not 0 <= result <= 1:
        fail(f"{label} is outside [0,1]: {result}")
    return result


def retrieve_ot_metadata(tracker: ResponseTracker) -> dict[str, Any]:
    data = graphql(
        OT_META_QUERY,
        {"diseaseId": LUAD_ID},
        tracker,
        "metadata and LUAD identity",
    )
    meta = data.get("meta")
    disease = data.get("disease")
    if not isinstance(meta, dict) or not isinstance(disease, dict):
        fail("Open Targets metadata/LUAD response is incomplete")
    if disease.get("id") != LUAD_ID or disease.get("name") != LUAD_NAME:
        fail(f"Pinned LUAD identity did not validate: {disease}")
    return {
        "url": OT_URL,
        "name": meta.get("name", "NOT_PROVIDED"),
        "product": meta.get("product", "NOT_PROVIDED"),
        "api_version": format_ot_api_version(meta.get("apiVersion")),
        "data_version": format_ot_data_version(meta.get("dataVersion")),
        "luad_id": disease["id"],
        "luad_name": disease["name"],
    }


def retrieve_ot_targets(
    identifiers: list[str], tracker: ResponseTracker
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    batch_size = 500
    submitted = set(identifiers)
    output: dict[str, dict[str, Any]] = {}
    for start in range(0, len(identifiers), batch_size):
        batch = identifiers[start : start + batch_size]
        data = graphql(
            OT_TARGET_QUERY,
            {"ids": batch},
            tracker,
            f"target annotation batch {start // batch_size + 1}",
        )
        targets = data.get("targets")
        if not isinstance(targets, list):
            fail("Open Targets target batch lacks targets list")
        for target in targets:
            if not isinstance(target, dict) or not isinstance(target.get("id"), str):
                fail("Malformed Open Targets target annotation")
            target_id = target["id"]
            if target_id not in submitted:
                fail(f"Open Targets returned unsubmitted target ID: {target_id}")
            if target_id in output:
                fail(f"Open Targets returned duplicate target ID: {target_id}")
            literature = target.get("literatureOcurrences")
            candidates = target.get("drugAndClinicalCandidates")
            if not isinstance(literature, dict) or not isinstance(candidates, dict):
                fail(f"Open Targets count annotations are missing for {target_id}")
            output[target_id] = {
                "id": target_id,
                "approvedName": target.get("approvedName"),
                "approvedSymbol": target.get("approvedSymbol"),
                "biotype": target.get("biotype"),
                "literature_count": validate_nonnegative_int(
                    literature.get("count"), f"literature count for {target_id}"
                ),
                "literature_filtered_count": validate_nonnegative_int(
                    literature.get("filteredCount"),
                    f"filtered literature count for {target_id}",
                ),
                "drug_candidate_count": validate_nonnegative_int(
                    candidates.get("count"), f"drug/candidate count for {target_id}"
                ),
            }
    return output, {
        "submitted_target_ids": len(identifiers),
        "returned_target_ids": len(output),
        "target_batch_size": batch_size,
        "target_batch_count": math.ceil(len(identifiers) / batch_size),
    }


def normalize_score_rows(value: Any, label: str) -> str:
    if not isinstance(value, list):
        fail(f"{label} is not a list")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in value:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str):
            fail(f"Malformed {label} row")
        row_id = row["id"]
        if row_id in seen:
            fail(f"Duplicate {label} ID: {row_id}")
        seen.add(row_id)
        normalized.append(
            {"id": row_id, "score": validate_score(row.get("score"), f"{label}/{row_id}")}
        )
    normalized.sort(key=lambda row: row["id"])
    return json.dumps(normalized, separators=(",", ":"), sort_keys=True)


def retrieve_ot_associations(
    indirect: bool, tracker: ResponseTracker
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    # The API permits at most 3,000 rows. Score ties can still create unstable
    # page boundaries, so bounded alternate-size traversals are unioned until
    # the reported number of unique target associations is recovered.
    page_sizes = (3000, 2999, 2500)
    expected_count: int | None = None
    output: dict[str, dict[str, Any]] = {}
    traversal_audit: list[dict[str, int]] = []
    total_page_count = 0
    for page_size in page_sizes:
        traversal: dict[str, dict[str, Any]] = {}
        raw_row_count = 0
        duplicate_row_count = 0
        page_index = 0
        while expected_count is None or raw_row_count < expected_count:
            data = graphql(
                OT_ASSOCIATION_QUERY,
                {
                    "diseaseId": LUAD_ID,
                    "indirect": indirect,
                    "pageIndex": page_index,
                    "pageSize": page_size,
                },
                tracker,
                (
                    f"LUAD {'indirect' if indirect else 'direct'} association "
                    f"size {page_size} page {page_index}"
                ),
            )
            total_page_count += 1
            disease = data.get("disease")
            if not isinstance(disease, dict):
                fail("Open Targets LUAD association response lacks disease")
            if disease.get("id") != LUAD_ID or disease.get("name") != LUAD_NAME:
                fail("Open Targets LUAD association response changed disease identity")
            associations = disease.get("associatedTargets")
            if not isinstance(associations, dict):
                fail("Open Targets LUAD response lacks associatedTargets")
            count = validate_nonnegative_int(
                associations.get("count"), "LUAD association total count"
            )
            if expected_count is None:
                expected_count = count
            elif count != expected_count:
                fail("Open Targets LUAD association count changed during pagination")
            rows = associations.get("rows")
            if not isinstance(rows, list):
                fail("Open Targets LUAD association page lacks rows")
            raw_row_count += len(rows)
            for row in rows:
                if not isinstance(row, dict) or not isinstance(row.get("target"), dict):
                    fail("Malformed Open Targets LUAD association row")
                target_id = row["target"].get("id")
                if not isinstance(target_id, str):
                    fail("Open Targets LUAD association row lacks target ID")
                normalized = {
                    "score": validate_score(
                        row.get("score"), f"LUAD association/{target_id}"
                    ),
                    "datasource_scores_json": normalize_score_rows(
                        row.get("datasourceScores"), f"datasource scores/{target_id}"
                    ),
                    "datatype_scores_json": normalize_score_rows(
                        row.get("datatypeScores"), f"datatype scores/{target_id}"
                    ),
                }
                if target_id in traversal:
                    duplicate_row_count += 1
                    if traversal[target_id] != normalized:
                        fail(f"Conflicting duplicate LUAD association: {target_id}")
                else:
                    traversal[target_id] = normalized
                if target_id in output and output[target_id] != normalized:
                    fail(f"LUAD association changed across traversals: {target_id}")
                output[target_id] = normalized
            page_index += 1
            if not rows and raw_row_count < expected_count:
                fail("Open Targets LUAD pagination ended before expected row count")
            if page_index > math.ceil(expected_count / page_size) + 1:
                fail("Open Targets LUAD pagination exceeded expected page count")
        if raw_row_count != expected_count:
            fail(
                f"LUAD traversal size {page_size} returned {raw_row_count} raw rows, "
                f"expected {expected_count}"
            )
        traversal_audit.append(
            {
                "page_size": page_size,
                "page_count": page_index,
                "raw_row_count": raw_row_count,
                "unique_row_count": len(traversal),
                "duplicate_row_count": duplicate_row_count,
                "union_unique_count": len(output),
            }
        )
        if len(output) == expected_count:
            break
    if len(output) != expected_count:
        fail(
            f"Bounded LUAD pagination recovery returned {len(output)} unique "
            f"associations of {expected_count}"
        )
    return output, {
        "enable_indirect": indirect,
        "association_count_all_platform_targets": expected_count,
        "page_sizes_attempted": "|".join(str(row["page_size"]) for row in traversal_audit),
        "traversal_count": len(traversal_audit),
        "total_page_count": total_page_count,
        "duplicate_rows_observed": sum(
            row["duplicate_row_count"] for row in traversal_audit
        ),
        "traversal_audit_json": json.dumps(
            traversal_audit, separators=(",", ":"), sort_keys=True
        ),
    }


def retrieve_chembl(
    required_ids: set[str], tracker: ResponseTracker
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    status_body = request_bytes(CHEMBL_STATUS_URL, tracker)
    status = parse_json(status_body, "ChEMBL status")
    if status.get("status") != "UP":
        fail(f"ChEMBL did not report UP: {status}")

    params = urllib.parse.urlencode(
        {
            # Smaller pages avoid intermittent TLS truncation observed from
            # the target endpoint at 1,000 records.
            "limit": "500",
            "only": (
                "target_chembl_id,pref_name,target_type,organism,tax_id,"
                "species_group_flag"
            ),
        }
    )
    next_url: str | None = f"{CHEMBL_TARGET_URL}?{params}"
    all_ids: set[str] = set()
    required_records: dict[str, dict[str, Any]] = {}
    expected_count: int | None = None
    page_count = 0
    while next_url is not None:
        body = request_bytes(next_url, tracker)
        result = parse_json(body, "ChEMBL target page")
        page_meta = result.get("page_meta")
        targets = result.get("targets")
        if not isinstance(page_meta, dict) or not isinstance(targets, list):
            fail("Malformed ChEMBL target page")
        count = validate_nonnegative_int(page_meta.get("total_count"), "ChEMBL target count")
        if expected_count is None:
            expected_count = count
        elif count != expected_count:
            fail("ChEMBL target count changed during pagination")
        for target in targets:
            if not isinstance(target, dict):
                fail("Malformed ChEMBL target record")
            target_id = target.get("target_chembl_id")
            if not isinstance(target_id, str) or not re.fullmatch(r"CHEMBL\d+", target_id):
                fail("Invalid ChEMBL target identifier")
            if target_id in all_ids:
                fail(f"Duplicate ChEMBL target identifier: {target_id}")
            all_ids.add(target_id)
            if target_id in required_ids:
                required_records[target_id] = {
                    "target_chembl_id": target_id,
                    "pref_name": target.get("pref_name"),
                    "target_type": target.get("target_type"),
                    "organism": target.get("organism"),
                    "tax_id": target.get("tax_id"),
                    "species_group_flag": target.get("species_group_flag"),
                }
        page_count += 1
        next_value = page_meta.get("next")
        if next_value is None:
            next_url = None
        elif isinstance(next_value, str):
            next_url = urllib.parse.urljoin("https://www.ebi.ac.uk", next_value)
        else:
            fail("Invalid ChEMBL next-page value")
    if expected_count is None or len(all_ids) != expected_count:
        fail(f"ChEMBL pagination returned {len(all_ids)} of {expected_count}")
    return required_records, {
        "target_url": CHEMBL_TARGET_URL,
        "status_url": CHEMBL_STATUS_URL,
        "database_version": status.get("chembl_db_version", "NOT_PROVIDED"),
        "release_date": status.get("chembl_release_date", "NOT_PROVIDED"),
        "target_count": expected_count,
        "page_count": page_count,
        "required_target_ids": len(required_ids),
        "required_target_ids_found": len(required_records),
    }


def split_identifier(value: str) -> list[str]:
    if value == "NOT_FOUND":
        return []
    values = value.split("|")
    if any(not item for item in values) or len(values) != len(set(values)):
        fail(f"Malformed delimited identifier value: {value!r}")
    return values


def scalar_or_not_available(value: Any) -> str:
    return "NOT_AVAILABLE" if value is None else str(value)


def build_registry(
    mapping: list[dict[str, str]],
    u2_ids: set[str],
    ot_targets: dict[str, dict[str, Any]],
    direct_associations: dict[str, dict[str, Any]],
    indirect_associations: dict[str, dict[str, Any]],
    chembl_records: dict[str, dict[str, Any]],
) -> tuple[list[str], list[dict[str, str]]]:
    output: list[dict[str, str]] = []
    for source in mapping:
        ot_id = source["OpenTargets_target_ID"]
        chembl_ids = split_identifier(source["ChEMBL_target_ID"])
        ot_target = None if ot_id == "NOT_FOUND" else ot_targets.get(ot_id)
        direct = None if ot_id == "NOT_FOUND" else direct_associations.get(ot_id)
        indirect = None if ot_id == "NOT_FOUND" else indirect_associations.get(ot_id)

        if ot_id == "NOT_FOUND":
            ot_status = "NOT_MAPPED"
        elif ot_target is None:
            ot_status = "NOT_FOUND_IN_API"
        else:
            ot_status = "PRESENT"

        if ot_status != "PRESENT":
            ot_approved_name = "NOT_AVAILABLE"
            ot_approved_symbol = "NOT_AVAILABLE"
            ot_biotype = "NOT_AVAILABLE"
            literature_count = "NOT_AVAILABLE"
            literature_filtered_count = "NOT_AVAILABLE"
            drug_candidate_count = "NOT_AVAILABLE"
        else:
            ot_approved_name = scalar_or_not_available(ot_target["approvedName"])
            ot_approved_symbol = scalar_or_not_available(ot_target["approvedSymbol"])
            ot_biotype = scalar_or_not_available(ot_target["biotype"])
            literature_count = str(ot_target["literature_count"])
            literature_filtered_count = str(ot_target["literature_filtered_count"])
            drug_candidate_count = str(ot_target["drug_candidate_count"])

        if ot_status != "PRESENT":
            direct_status = ot_status
            indirect_status = ot_status
            direct_count = "NOT_AVAILABLE"
            indirect_count = "NOT_AVAILABLE"
            direct_score = "NOT_AVAILABLE"
            indirect_score = "NOT_AVAILABLE"
            datasource_scores = "NOT_AVAILABLE"
            datatype_scores = "NOT_AVAILABLE"
        else:
            direct_status = "PRESENT" if direct else "NO_ASSOCIATION_RETURNED"
            indirect_status = "PRESENT" if indirect else "NO_ASSOCIATION_RETURNED"
            direct_count = "1" if direct else "0"
            indirect_count = "1" if indirect else "0"
            direct_score = format(direct["score"], ".17g") if direct else "NOT_FOUND"
            indirect_score = format(indirect["score"], ".17g") if indirect else "NOT_FOUND"
            datasource_scores = (
                direct["datasource_scores_json"] if direct else "NOT_FOUND"
            )
            datatype_scores = direct["datatype_scores_json"] if direct else "NOT_FOUND"

        found_chembl = [target_id for target_id in chembl_ids if target_id in chembl_records]
        if not chembl_ids:
            chembl_status = "NOT_MAPPED"
            chembl_count = "NOT_AVAILABLE"
            chembl_json = "NOT_AVAILABLE"
        elif not found_chembl:
            chembl_status = "NOT_FOUND_IN_API"
            chembl_count = "0"
            chembl_json = "NOT_FOUND"
        else:
            chembl_status = "PRESENT" if len(found_chembl) == len(chembl_ids) else "PARTIAL"
            chembl_count = str(len(found_chembl))
            annotations = [chembl_records[target_id] for target_id in sorted(found_chembl)]
            chembl_json = json.dumps(annotations, separators=(",", ":"), sort_keys=True)

        row = {
            "EnsemblID": source["EnsemblID"],
            "EnsemblID_base": source["EnsemblID_base"],
            "Symbol": source["Symbol"],
            "gene_type": source["gene_type"],
            "U2_effect_supported_DE": "TRUE" if source["EnsemblID"] in u2_ids else "FALSE",
            "OpenTargets_target_ID": ot_id,
            "ChEMBL_target_ID": source["ChEMBL_target_ID"],
            "ot_target_retrieval_status": ot_status,
            "ot_target_approved_name": ot_approved_name,
            "ot_target_approved_symbol": ot_approved_symbol,
            "ot_target_biotype": ot_biotype,
            "ot_literature_occurrence_count": literature_count,
            "ot_literature_filtered_count": literature_filtered_count,
            "ot_drug_clinical_candidate_record_count": drug_candidate_count,
            "ot_target_annotation_source": OT_SOURCE,
            "ot_luad_disease_id": LUAD_ID,
            "ot_luad_disease_name": LUAD_NAME,
            "ot_luad_direct_association_status": direct_status,
            "ot_luad_direct_association_count": direct_count,
            "ot_luad_direct_association_score_native": direct_score,
            "ot_luad_direct_datasource_scores_native_json": datasource_scores,
            "ot_luad_direct_datatype_scores_native_json": datatype_scores,
            "ot_luad_indirect_association_status": indirect_status,
            "ot_luad_indirect_association_count": indirect_count,
            "ot_luad_indirect_association_score_native": indirect_score,
            "ot_luad_association_source": OT_SOURCE,
            "chembl_target_retrieval_status": chembl_status,
            "chembl_target_record_count": chembl_count,
            "chembl_target_annotations_json": chembl_json,
            "chembl_target_annotation_source": CHEMBL_SOURCE,
        }
        output.append(row)
    return list(output[0]), output


def validate_registry(
    mapping: list[dict[str, str]], fieldnames: list[str], rows: list[dict[str, str]]
) -> None:
    if len(rows) != EXPECTED_ROWS or len(rows) != len(mapping):
        fail("Evidence registry did not preserve all 29,606 genes")
    input_ids = [row["EnsemblID"] for row in mapping]
    output_ids = [row["EnsemblID"] for row in rows]
    if output_ids != input_ids or len(set(output_ids)) != EXPECTED_ROWS:
        fail("Evidence registry changed EnsemblID order or uniqueness")
    for source, output in zip(mapping, rows):
        for field in (
            "EnsemblID",
            "EnsemblID_base",
            "Symbol",
            "gene_type",
            "OpenTargets_target_ID",
            "ChEMBL_target_ID",
        ):
            if source[field] != output[field]:
                fail(f"Evidence registry changed {field} for {source['EnsemblID']}")
    if sum(row["U2_effect_supported_DE"] == "TRUE" for row in rows) != EXPECTED_U2:
        fail("Evidence registry did not preserve the 14,064-gene U2 subset")
    if any(row["U2_effect_supported_DE"] not in {"TRUE", "FALSE"} for row in rows):
        fail("Evidence registry contains invalid U2 flags")

    source_fields = (
        "ot_target_annotation_source",
        "ot_luad_association_source",
        "chembl_target_annotation_source",
    )
    if any(not row[field] for row in rows for field in source_fields):
        fail("At least one evidence source field is empty")
    forbidden_tokens = ("rank", "priority", "recommendation", "therapeutic_direction")
    forbidden = [
        field for field in fieldnames if any(token in field.lower() for token in forbidden_tokens)
    ]
    if forbidden:
        fail(f"Forbidden ranking/prioritization/therapeutic fields emitted: {forbidden}")
    score_fields = [field for field in fieldnames if "score" in field.lower()]
    if any("native" not in field.lower() for field in score_fields):
        fail(f"Non-source-native score field emitted: {score_fields}")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def make_qc(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    scopes = {
        "ALL_TESTED": list(range(len(rows))),
        "U2_EFFECT_SUPPORTED_DE": [
            index for index, row in enumerate(rows) if row["U2_effect_supported_DE"] == "TRUE"
        ],
    }
    metrics = (
        ("REGISTRY", "ROWS_PRESERVED", lambda row: True),
        ("OPEN_TARGETS", "IDENTIFIER_MAPPED", lambda row: row["OpenTargets_target_ID"] != "NOT_FOUND"),
        ("OPEN_TARGETS", "TARGET_PRESENT", lambda row: row["ot_target_retrieval_status"] == "PRESENT"),
        ("OPEN_TARGETS", "TARGET_NOT_FOUND_IN_API", lambda row: row["ot_target_retrieval_status"] == "NOT_FOUND_IN_API"),
        ("OPEN_TARGETS", "LUAD_DIRECT_ASSOCIATION_PRESENT", lambda row: row["ot_luad_direct_association_status"] == "PRESENT"),
        ("OPEN_TARGETS", "LUAD_INDIRECT_ASSOCIATION_PRESENT", lambda row: row["ot_luad_indirect_association_status"] == "PRESENT"),
        ("OPEN_TARGETS", "LITERATURE_COUNT_NONZERO", lambda row: row["ot_literature_occurrence_count"].isdigit() and int(row["ot_literature_occurrence_count"]) > 0),
        ("OPEN_TARGETS", "DRUG_CANDIDATE_RECORD_COUNT_NONZERO", lambda row: row["ot_drug_clinical_candidate_record_count"].isdigit() and int(row["ot_drug_clinical_candidate_record_count"]) > 0),
        ("CHEMBL", "IDENTIFIER_MAPPED", lambda row: row["ChEMBL_target_ID"] != "NOT_FOUND"),
        ("CHEMBL", "TARGET_PRESENT", lambda row: row["chembl_target_retrieval_status"] == "PRESENT"),
        ("CHEMBL", "TARGET_PARTIAL", lambda row: row["chembl_target_retrieval_status"] == "PARTIAL"),
        ("CHEMBL", "TARGET_NOT_FOUND_IN_API", lambda row: row["chembl_target_retrieval_status"] == "NOT_FOUND_IN_API"),
    )
    output: list[dict[str, Any]] = []
    for scope, indices in scopes.items():
        denominator = len(indices)
        for source, metric, predicate in metrics:
            count = sum(predicate(rows[index]) for index in indices)
            output.append(
                {
                    "scope": scope,
                    "source": source,
                    "metric": metric,
                    "count": count,
                    "denominator": denominator,
                    "percent": f"{100 * count / denominator:.6f}",
                }
            )
    return output


def qc_count(qc_rows: list[dict[str, Any]], scope: str, source: str, metric: str) -> int:
    matches = [
        row
        for row in qc_rows
        if row["scope"] == scope and row["source"] == source and row["metric"] == metric
    ]
    if len(matches) != 1:
        fail(f"QC metric is not unique: {scope}/{source}/{metric}")
    return int(matches[0]["count"])


def pct(count: int, denominator: int) -> str:
    return f"{100 * count / denominator:.2f}%"


def write_summary(
    qc_rows: list[dict[str, Any]], source_meta: dict[str, dict[str, Any]]
) -> None:
    all_ot = qc_count(qc_rows, "ALL_TESTED", "OPEN_TARGETS", "TARGET_PRESENT")
    u2_ot = qc_count(qc_rows, "U2_EFFECT_SUPPORTED_DE", "OPEN_TARGETS", "TARGET_PRESENT")
    all_direct = qc_count(
        qc_rows, "ALL_TESTED", "OPEN_TARGETS", "LUAD_DIRECT_ASSOCIATION_PRESENT"
    )
    u2_direct = qc_count(
        qc_rows,
        "U2_EFFECT_SUPPORTED_DE",
        "OPEN_TARGETS",
        "LUAD_DIRECT_ASSOCIATION_PRESENT",
    )
    all_indirect = qc_count(
        qc_rows, "ALL_TESTED", "OPEN_TARGETS", "LUAD_INDIRECT_ASSOCIATION_PRESENT"
    )
    u2_indirect = qc_count(
        qc_rows,
        "U2_EFFECT_SUPPORTED_DE",
        "OPEN_TARGETS",
        "LUAD_INDIRECT_ASSOCIATION_PRESENT",
    )
    all_lit = qc_count(
        qc_rows, "ALL_TESTED", "OPEN_TARGETS", "LITERATURE_COUNT_NONZERO"
    )
    u2_lit = qc_count(
        qc_rows,
        "U2_EFFECT_SUPPORTED_DE",
        "OPEN_TARGETS",
        "LITERATURE_COUNT_NONZERO",
    )
    all_drug = qc_count(
        qc_rows, "ALL_TESTED", "OPEN_TARGETS", "DRUG_CANDIDATE_RECORD_COUNT_NONZERO"
    )
    u2_drug = qc_count(
        qc_rows,
        "U2_EFFECT_SUPPORTED_DE",
        "OPEN_TARGETS",
        "DRUG_CANDIDATE_RECORD_COUNT_NONZERO",
    )
    all_chembl = qc_count(qc_rows, "ALL_TESTED", "CHEMBL", "TARGET_PRESENT")
    u2_chembl = qc_count(
        qc_rows, "U2_EFFECT_SUPPORTED_DE", "CHEMBL", "TARGET_PRESENT"
    )
    chembl_partial = qc_count(qc_rows, "ALL_TESTED", "CHEMBL", "TARGET_PARTIAL")
    chembl_missing = qc_count(
        qc_rows, "ALL_TESTED", "CHEMBL", "TARGET_NOT_FOUND_IN_API"
    )
    ot_missing = qc_count(
        qc_rows, "ALL_TESTED", "OPEN_TARGETS", "TARGET_NOT_FOUND_IN_API"
    )

    text = f"""# Evidence Layer Summary

**Task:** #010  
**Genes retained:** {EXPECTED_ROWS:,} / {EXPECTED_ROWS:,}  
**U2 genes retained:** {EXPECTED_U2:,} / {EXPECTED_U2:,}  
**Immutable key:** versioned `EnsemblID`

## Retrieval coverage

| Evidence field | All tested genes | U2 genes |
|---|---:|---:|
| Open Targets target record | {all_ot:,} ({pct(all_ot, EXPECTED_ROWS)}) | {u2_ot:,} ({pct(u2_ot, EXPECTED_U2)}) |
| Direct LUAD association | {all_direct:,} ({pct(all_direct, EXPECTED_ROWS)}) | {u2_direct:,} ({pct(u2_direct, EXPECTED_U2)}) |
| Ontology-expanded LUAD association | {all_indirect:,} ({pct(all_indirect, EXPECTED_ROWS)}) | {u2_indirect:,} ({pct(u2_indirect, EXPECTED_U2)}) |
| Nonzero Open Targets bibliography count | {all_lit:,} ({pct(all_lit, EXPECTED_ROWS)}) | {u2_lit:,} ({pct(u2_lit, EXPECTED_U2)}) |
| Nonzero Open Targets drug/candidate record count | {all_drug:,} ({pct(all_drug, EXPECTED_ROWS)}) | {u2_drug:,} ({pct(u2_drug, EXPECTED_U2)}) |
| ChEMBL target annotation | {all_chembl:,} ({pct(all_chembl, EXPECTED_ROWS)}) | {u2_chembl:,} ({pct(u2_chembl, EXPECTED_U2)}) |

Counts describe retrieved records only. They are not target scores, ranks, or
statements of biological importance.

## Disease query

- Disease ID: `{LUAD_ID}`
- Disease label: `{LUAD_NAME}`
- Direct Platform association universe: **{source_meta['open_targets']['direct_associations']['association_count_all_platform_targets']:,}** targets
- Ontology-expanded association universe: **{source_meta['open_targets']['indirect_associations']['association_count_all_platform_targets']:,}** targets

Direct and ontology-expanded evidence are retained separately. All association
scores and datasource/datatype values are unmodified Open Targets source-native
fields, not project-generated scores.

## Source snapshot

- Open Targets data `{source_meta['open_targets']['metadata']['data_version']}`;
  API `{source_meta['open_targets']['metadata']['api_version']}`.
- ChEMBL `{source_meta['chembl']['database_version']}`, released
  `{source_meta['chembl']['release_date']}`.
- Open Targets mapped IDs absent from the current API: **{ot_missing:,}**
- ChEMBL rows with partial one-to-many retrieval: **{chembl_partial:,}**
- ChEMBL mapped rows absent from the current API: **{chembl_missing:,}**

Network access was limited to official Open Targets and ChEMBL APIs. No package
was installed or updated. Response hashes and request provenance are recorded
in `session_info.txt`.

## Interpretation limits

- Bibliography values are count fields only; no publication content was
  retrieved.
- Literature volume does not establish causality or target quality.
- A ChEMBL target record indicates database availability, not compound quality,
  potency, druggability, or therapeutic suitability.
- A source-native association score is not a confidence probability and was not
  used to rank genes.
- Zero means the queried API returned a count of zero. `NOT_AVAILABLE` means the
  source could not be queried because the required identifier was unavailable.

## Explicit non-claims

Task #010 generated no target rank, project score, gene or drug prioritization,
therapeutic direction, biological interpretation, or treatment recommendation.
"""
    SUMMARY.write_text(text, encoding="utf-8")


def flatten(prefix: str, value: Any, output: list[str]) -> None:
    if isinstance(value, dict):
        for key in sorted(value):
            flatten(f"{prefix}.{key}" if prefix else key, value[key], output)
    else:
        output.append(f"{prefix}={value}")


def write_session(
    repo: dict[str, str], source_meta: dict[str, dict[str, Any]], started_at: str
) -> None:
    lines = [
        "Task #010 evidence-layer retrieval session",
        f"started_at_utc={started_at}",
        f"finished_at_utc={datetime.now(timezone.utc).isoformat()}",
        f"python_version={platform.python_version()}",
        f"python_implementation={platform.python_implementation()}",
        f"platform={platform.platform()}",
        f"tls_ca_file={TLS_CA_FILE}",
        f"git_branch={repo['branch']}",
        f"git_head={repo['head']}",
        f"frozen_task009_commit={TASK009_COMMIT}",
        f"git_origin={repo['remote']}",
        f"input_path={INPUT}",
        f"input_sha256={file_sha256(INPUT)}",
        f"u2_reference_path={U2_REFERENCE}",
        f"u2_reference_sha256={file_sha256(U2_REFERENCE)}",
        f"script_sha256={file_sha256(Path(__file__))}",
        f"plan_sha256={file_sha256(PLAN)}",
        "network_access=USED",
        "network_hosts=api.platform.opentargets.org|www.ebi.ac.uk",
        "packages_installed_or_updated=FALSE",
        "gene_symbols_used_as_query_keys=FALSE",
        "raw_api_responses_committed=FALSE",
        "project_score_generated=FALSE",
        "ranking_generated=FALSE",
        "therapeutic_recommendation_generated=FALSE",
        "",
        "GraphQL query SHA256:",
        f"meta_query={hashlib.sha256(OT_META_QUERY.encode()).hexdigest()}",
        f"target_query={hashlib.sha256(OT_TARGET_QUERY.encode()).hexdigest()}",
        f"association_query={hashlib.sha256(OT_ASSOCIATION_QUERY.encode()).hexdigest()}",
        "",
        "Source provenance:",
    ]
    flattened: list[str] = []
    flatten("source", source_meta, flattened)
    lines.extend(flattened)
    lines.extend(
        [
            "",
            "Output SHA256:",
            f"{file_sha256(REGISTRY)}  {REGISTRY}",
            f"{file_sha256(QC)}  {QC}",
            f"{file_sha256(SUMMARY)}  {SUMMARY}",
        ]
    )
    SESSION.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    started_at = datetime.now(timezone.utc).isoformat()
    repo = validate_repository()
    mapping, u2_ids = load_inputs()
    ot_identifiers = [
        row["OpenTargets_target_ID"]
        for row in mapping
        if row["OpenTargets_target_ID"] != "NOT_FOUND"
    ]
    if len(ot_identifiers) != len(set(ot_identifiers)):
        fail("Task #009 Open Targets identifiers are not unique")
    chembl_required: set[str] = set()
    for row in mapping:
        chembl_required.update(split_identifier(row["ChEMBL_target_ID"]))

    ot_tracker = ResponseTracker("Open Targets Platform GraphQL API")
    print("Retrieving Open Targets metadata and validating LUAD identity...", flush=True)
    ot_metadata = retrieve_ot_metadata(ot_tracker)
    print("Retrieving Open Targets target annotations and literature counts...", flush=True)
    ot_targets, ot_target_meta = retrieve_ot_targets(ot_identifiers, ot_tracker)
    print("Retrieving direct LUAD target associations...", flush=True)
    direct, direct_meta = retrieve_ot_associations(False, ot_tracker)
    print("Retrieving ontology-expanded LUAD target associations...", flush=True)
    indirect, indirect_meta = retrieve_ot_associations(True, ot_tracker)

    chembl_tracker = ResponseTracker("ChEMBL data web service")
    print("Retrieving ChEMBL target annotations...", flush=True)
    chembl_records, chembl_meta = retrieve_chembl(chembl_required, chembl_tracker)

    fieldnames, evidence_rows = build_registry(
        mapping, u2_ids, ot_targets, direct, indirect, chembl_records
    )
    validate_registry(mapping, fieldnames, evidence_rows)
    qc_rows = make_qc(evidence_rows)
    source_meta = {
        "open_targets": {
            "metadata": ot_metadata,
            "target_retrieval": ot_target_meta,
            "direct_associations": direct_meta,
            "indirect_associations": indirect_meta,
            "response_tracking": ot_tracker.metadata(),
        },
        "chembl": {**chembl_meta, "response_tracking": chembl_tracker.metadata()},
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(REGISTRY, fieldnames, evidence_rows)
    write_csv(
        QC,
        ["scope", "source", "metric", "count", "denominator", "percent"],
        qc_rows,
    )
    write_summary(qc_rows, source_meta)
    write_session(repo, source_meta, started_at)
    print(f"Wrote {REGISTRY} ({len(evidence_rows)} rows)")
    print(f"Wrote {QC} ({len(qc_rows)} QC rows)")
    print(f"Preserved U2 genes: {sum(row['U2_effect_supported_DE'] == 'TRUE' for row in evidence_rows)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
