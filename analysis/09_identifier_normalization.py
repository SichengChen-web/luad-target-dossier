#!/usr/bin/env python3
"""Build the Task #009 auditable identifier-normalization snapshot."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import platform
import re
import ssl
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK008_COMMIT = "c420cbe07715a15000dbf2d4c7d9f2dc3fb7c662"
EXPECTED_INPUT_SHA256 = "8055a9d99d058d219399957e62f6a3cccc3dd2217bc028d1d11dd4dc667f90e2"
EXPECTED_ROWS = 29_606
EXPECTED_U2 = 14_064

INPUT = Path("outputs/candidate_registry/candidate_registry.csv")
OUTPUT_DIR = Path("outputs/identifier_normalization")
MAPPING = OUTPUT_DIR / "identifier_mapping.csv"
QC = OUTPUT_DIR / "mapping_qc.csv"
SUMMARY = OUTPUT_DIR / "mapping_summary.md"
SESSION = OUTPUT_DIR / "session_info.txt"

HGNC_URL = (
    "https://storage.googleapis.com/public-download-files/hgnc/tsv/tsv/"
    "hgnc_complete_set.txt"
)
OT_URL = "https://api.platform.opentargets.org/api/v4/graphql"
CHEMBL_COMPONENT_URL = "https://www.ebi.ac.uk/chembl/api/data/target_component.json"
CHEMBL_STATUS_URL = "https://www.ebi.ac.uk/chembl/api/data/status.json"

HGNC_SOURCE = "HGNC_COMPLETE_SET_EXACT_ENSEMBL"
OT_SOURCE = "OPEN_TARGETS_PLATFORM_GRAPHQL_EXACT_ENSEMBL"
CHEMBL_SOURCE = "CHEMBL_TARGET_COMPONENT_API_VIA_HGNC_UNIPROT"
DELIMITER = "|"

ALLOWED_UNTRACKED = {
    "analysis/09_identifier_normalization.py",
    "docs/identifier_normalization_plan_v0.1.md",
}
ALLOWED_OUTPUT_PREFIX = "outputs/identifier_normalization/"
USER_AGENT = "luad-target-dossier-task-009/0.1"


def make_tls_context() -> tuple[ssl.SSLContext, str]:
    """Use an existing verified CA bundle without installing a package."""
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


def bytes_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_repository() -> dict[str, str]:
    root = Path(git("rev-parse", "--show-toplevel")).resolve()
    if root != Path.cwd().resolve():
        fail(f"Run from repository root {root}; observed {Path.cwd().resolve()}")

    branch = git("branch", "--show-current")
    if branch != "main":
        fail(f"Task #009 requires branch main; observed {branch!r}")
    head = git("rev-parse", "HEAD")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", TASK008_COMMIT, head],
        text=True,
        capture_output=True,
        check=False,
    )
    if ancestor.returncode != 0:
        fail(f"Frozen Task #008 commit {TASK008_COMMIT} is not an ancestor of {head}")

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

    if not INPUT.is_file():
        fail(f"Frozen Task #008 registry is missing: {INPUT}")
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(INPUT)],
        text=True,
        capture_output=True,
        check=False,
    )
    if tracked.returncode != 0:
        fail(f"Frozen input is not committed: {INPUT}")
    unchanged = subprocess.run(
        ["git", "diff", "--quiet", TASK008_COMMIT, "--", str(INPUT)],
        text=True,
        capture_output=True,
        check=False,
    )
    if unchanged.returncode != 0:
        fail(f"Frozen input differs from Task #008 commit: {INPUT}")
    observed_hash = file_sha256(INPUT)
    if observed_hash != EXPECTED_INPUT_SHA256:
        fail(
            f"Frozen input SHA256 mismatch: observed {observed_hash}, "
            f"expected {EXPECTED_INPUT_SHA256}"
        )
    return {"root": str(root), "branch": branch, "head": head, "remote": remote}


def read_registry() -> tuple[list[dict[str, str]], list[str]]:
    with INPUT.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            fail(f"CSV has no header: {INPUT}")
        header = list(reader.fieldnames)
        rows = list(reader)

    required = {"EnsemblID", "EnsemblID_base", "Symbol", "gene_type", "U2_effect_supported_DE"}
    missing = required.difference(header)
    if missing:
        fail(f"Frozen registry lacks required columns: {sorted(missing)}")
    if len(rows) != EXPECTED_ROWS:
        fail(f"Registry has {len(rows)} rows; expected {EXPECTED_ROWS}")
    identifiers = [row["EnsemblID"] for row in rows]
    if len(set(identifiers)) != EXPECTED_ROWS:
        fail("Registry EnsemblID values are not unique")
    if any(not row[field] for row in rows for field in ("EnsemblID", "EnsemblID_base", "gene_type")):
        fail("Required registry identity field is empty")
    if any(not re.fullmatch(r"ENSG\d+", row["EnsemblID_base"]) for row in rows):
        fail("At least one EnsemblID_base is malformed")
    if len({row["EnsemblID_base"] for row in rows}) != EXPECTED_ROWS:
        fail("Registry EnsemblID_base values are not unique")
    u2 = sum(row["U2_effect_supported_DE"] == "TRUE" for row in rows)
    if u2 != EXPECTED_U2:
        fail(f"Registry contains {u2} U2 genes; expected {EXPECTED_U2}")
    return rows, header


def request_bytes(
    url: str,
    *,
    payload: dict[str, Any] | None = None,
    timeout: int = 180,
    attempts: int = 4,
) -> tuple[bytes, dict[str, str]]:
    data = None
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json, text/plain"}
    if payload is not None:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method="POST" if data else "GET")
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(
                request, timeout=timeout, context=TLS_CONTEXT
            ) as response:
                body = response.read()
                response_headers = {key.lower(): value for key, value in response.headers.items()}
                if not body:
                    fail(f"Empty response from {url}")
                return body, response_headers
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            last_error = exc
            if attempt == attempts:
                break
            time.sleep(2 ** (attempt - 1))
    fail(f"Network request failed after {attempts} attempts: {url}: {last_error}")


def parse_json_response(body: bytes, source: str) -> dict[str, Any]:
    try:
        result = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Invalid JSON from {source}") from exc
    if not isinstance(result, dict):
        fail(f"Unexpected JSON root from {source}")
    return result


def split_multi(value: str | None) -> list[str]:
    if value is None:
        return []
    return sorted({item.strip() for item in value.split("|") if item.strip()})


def retrieve_hgnc() -> tuple[dict[str, list[dict[str, str]]], dict[str, Any]]:
    body, headers = request_bytes(HGNC_URL)
    try:
        text = body.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise RuntimeError("HGNC complete set is not valid UTF-8") from exc
    reader = csv.DictReader(io.StringIO(text), delimiter="\t")
    if reader.fieldnames is None:
        fail("HGNC complete set has no header")
    required = {"hgnc_id", "symbol", "entrez_id", "ensembl_gene_id", "uniprot_ids"}
    missing = required.difference(reader.fieldnames)
    if missing:
        fail(f"HGNC complete set lacks required columns: {sorted(missing)}")

    by_ensembl: dict[str, list[dict[str, str]]] = defaultdict(list)
    source_rows = 0
    for row in reader:
        source_rows += 1
        for ensembl_id in split_multi(row.get("ensembl_gene_id")):
            if re.fullmatch(r"ENSG\d+", ensembl_id):
                by_ensembl[ensembl_id].append(row)

    metadata = {
        "url": HGNC_URL,
        "last_modified": headers.get("last-modified", "NOT_PROVIDED"),
        "etag": headers.get("etag", "NOT_PROVIDED"),
        "bytes": len(body),
        "sha256": bytes_sha256(body),
        "source_rows": source_rows,
        "ensembl_keys": len(by_ensembl),
        "request_count": 1,
    }
    return by_ensembl, metadata


def retrieve_open_targets(ensembl_ids: list[str]) -> tuple[set[str], dict[str, Any]]:
    meta_query = (
        "query{meta{name product apiVersion{x y z suffix} "
        "dataVersion{year month iteration}}}"
    )
    meta_body, _ = request_bytes(OT_URL, payload={"query": meta_query})
    meta_json = parse_json_response(meta_body, "Open Targets metadata query")
    if meta_json.get("errors"):
        fail(f"Open Targets metadata query failed: {meta_json['errors']}")
    try:
        source_meta = meta_json["data"]["meta"]
    except (KeyError, TypeError) as exc:
        raise RuntimeError("Open Targets metadata response lacks data.meta") from exc

    target_query = "query($ids:[String!]!){targets(ensemblIds:$ids){id}}"
    found: set[str] = set()
    submitted = set(ensembl_ids)
    digest = hashlib.sha256()
    digest.update(meta_body)
    response_bytes = len(meta_body)
    batch_size = 500
    request_count = 1
    for start in range(0, len(ensembl_ids), batch_size):
        batch = ensembl_ids[start : start + batch_size]
        body, _ = request_bytes(
            OT_URL, payload={"query": target_query, "variables": {"ids": batch}}
        )
        request_count += 1
        response_bytes += len(body)
        digest.update(body)
        result = parse_json_response(body, "Open Targets target query")
        if result.get("errors"):
            fail(f"Open Targets target batch failed at index {start}: {result['errors']}")
        targets = result.get("data", {}).get("targets")
        if not isinstance(targets, list):
            fail(f"Open Targets target response is malformed at index {start}")
        for target in targets:
            if not isinstance(target, dict) or not isinstance(target.get("id"), str):
                fail("Open Targets returned a target without a string id")
            target_id = target["id"]
            if target_id not in submitted:
                fail(f"Open Targets returned an identifier that was not submitted: {target_id}")
            found.add(target_id)

    metadata = {
        "url": OT_URL,
        "name": source_meta.get("name", "NOT_PROVIDED"),
        "product": source_meta.get("product", "NOT_PROVIDED"),
        "api_version": format_ot_api_version(source_meta.get("apiVersion")),
        "data_version": format_ot_data_version(source_meta.get("dataVersion")),
        "bytes": response_bytes,
        "sha256_concatenated_responses": digest.hexdigest(),
        "request_count": request_count,
        "submitted_ids": len(ensembl_ids),
        "returned_ids": len(found),
        "batch_size": batch_size,
    }
    return found, metadata


def format_ot_api_version(value: Any) -> str:
    if not isinstance(value, dict):
        return "NOT_PROVIDED"
    required = ("x", "y", "z")
    if any(value.get(key) is None for key in required):
        return "NOT_PROVIDED"
    suffix = value.get("suffix") or ""
    return f"{value['x']}.{value['y']}.{value['z']}{suffix}"


def format_ot_data_version(value: Any) -> str:
    if not isinstance(value, dict):
        return "NOT_PROVIDED"
    if value.get("year") is None or value.get("month") is None:
        return "NOT_PROVIDED"
    iteration = value.get("iteration")
    base = f"{value['year']}.{int(value['month']):02d}"
    return base if iteration in (None, 0, "0") else f"{base}.{iteration}"


def retrieve_chembl() -> tuple[dict[str, set[str]], dict[str, Any]]:
    status_body, _ = request_bytes(CHEMBL_STATUS_URL)
    status = parse_json_response(status_body, "ChEMBL status endpoint")
    if status.get("status") != "UP":
        fail(f"ChEMBL status endpoint did not report UP: {status}")

    params = urllib.parse.urlencode(
        {
            "tax_id": "9606",
            "limit": "1000",
            "only": "accession,targets,component_id",
        }
    )
    next_url: str | None = f"{CHEMBL_COMPONENT_URL}?{params}"
    accession_to_targets: dict[str, set[str]] = defaultdict(set)
    digest = hashlib.sha256()
    digest.update(status_body)
    response_bytes = len(status_body)
    request_count = 1
    page_count = 0
    component_count = 0
    component_ids: set[int] = set()

    while next_url is not None:
        body, _ = request_bytes(next_url)
        request_count += 1
        page_count += 1
        response_bytes += len(body)
        digest.update(body)
        result = parse_json_response(body, "ChEMBL target-component endpoint")
        components = result.get("target_components")
        page_meta = result.get("page_meta")
        if not isinstance(components, list) or not isinstance(page_meta, dict):
            fail("Malformed ChEMBL target-component response")
        for component in components:
            if not isinstance(component, dict):
                fail("Malformed ChEMBL target-component record")
            component_id = component.get("component_id")
            if not isinstance(component_id, int):
                fail("ChEMBL target component lacks an integer component_id")
            if component_id in component_ids:
                fail(f"Duplicate ChEMBL component_id across pages: {component_id}")
            component_ids.add(component_id)
            component_count += 1
            accession = component.get("accession")
            targets = component.get("targets")
            if accession is None:
                continue
            if not isinstance(accession, str) or not accession:
                fail(f"Invalid ChEMBL accession for component {component_id}")
            if not isinstance(targets, list):
                fail(f"Invalid ChEMBL targets list for component {component_id}")
            for target in targets:
                if not isinstance(target, dict):
                    fail(f"Invalid ChEMBL target for component {component_id}")
                target_id = target.get("target_chembl_id")
                if not isinstance(target_id, str) or not re.fullmatch(r"CHEMBL\d+", target_id):
                    fail(f"Invalid ChEMBL target identifier for component {component_id}")
                accession_to_targets[accession].add(target_id)
        next_value = page_meta.get("next")
        if next_value is None:
            next_url = None
        elif isinstance(next_value, str):
            next_url = urllib.parse.urljoin("https://www.ebi.ac.uk", next_value)
        else:
            fail("Invalid ChEMBL next-page value")

    expected_components = page_meta.get("total_count")
    if expected_components is not None and component_count != int(expected_components):
        fail(
            f"ChEMBL component count mismatch: received {component_count}, "
            f"expected {expected_components}"
        )
    metadata = {
        "component_url": CHEMBL_COMPONENT_URL,
        "status_url": CHEMBL_STATUS_URL,
        "database_version": status.get("chembl_db_version", "NOT_PROVIDED"),
        "release_date": status.get("chembl_release_date", "NOT_PROVIDED"),
        "bytes": response_bytes,
        "sha256_concatenated_responses": digest.hexdigest(),
        "request_count": request_count,
        "page_count": page_count,
        "human_component_count": component_count,
        "accessions_with_targets": len(accession_to_targets),
    }
    return accession_to_targets, metadata


def values_from_hgnc(records: list[dict[str, str]], field: str) -> list[str]:
    values: set[str] = set()
    for record in records:
        values.update(split_multi(record.get(field)))
    return sorted(values)


def mapping_value(values: list[str]) -> str:
    return DELIMITER.join(values) if values else "NOT_FOUND"


def mapping_status(values: list[str], ambiguous_upstream: bool = False) -> str:
    if not values:
        return "NOT_FOUND"
    if ambiguous_upstream:
        return "AMBIGUOUS"
    return "UNIQUE" if len(values) == 1 else "ONE_TO_MANY"


def build_mapping(
    registry: list[dict[str, str]],
    hgnc_by_ensembl: dict[str, list[dict[str, str]]],
    ot_ids: set[str],
    chembl_by_uniprot: dict[str, set[str]],
) -> tuple[list[str], list[dict[str, str]]]:
    output: list[dict[str, str]] = []
    for source_row in registry:
        ensembl_base = source_row["EnsemblID_base"]
        hgnc_records = hgnc_by_ensembl.get(ensembl_base, [])
        upstream_ambiguous = len(hgnc_records) > 1
        hgnc_ids = values_from_hgnc(hgnc_records, "hgnc_id")
        entrez_ids = values_from_hgnc(hgnc_records, "entrez_id")
        uniprot_ids = values_from_hgnc(hgnc_records, "uniprot_ids")
        hgnc_symbols = values_from_hgnc(hgnc_records, "symbol")
        open_targets_ids = [ensembl_base] if ensembl_base in ot_ids else []

        chembl_targets: set[str] = set()
        matched_accessions: list[str] = []
        for accession in uniprot_ids:
            targets = chembl_by_uniprot.get(accession, set())
            if targets:
                matched_accessions.append(accession)
                chembl_targets.update(targets)
        chembl_ids = sorted(chembl_targets)

        values_by_field = {
            "HGNC_ID": hgnc_ids,
            "Entrez_ID": entrez_ids,
            "UniProt_ID": uniprot_ids,
            "OpenTargets_target_ID": open_targets_ids,
            "ChEMBL_target_ID": chembl_ids,
        }
        statuses = {
            "HGNC_ID": mapping_status(hgnc_ids, upstream_ambiguous),
            "Entrez_ID": mapping_status(entrez_ids, upstream_ambiguous),
            "UniProt_ID": mapping_status(uniprot_ids, upstream_ambiguous),
            "OpenTargets_target_ID": mapping_status(open_targets_ids),
            "ChEMBL_target_ID": mapping_status(chembl_ids, upstream_ambiguous),
        }
        one_to_many_fields = sorted(
            field for field, status in statuses.items() if status == "ONE_TO_MANY"
        )
        ambiguous_fields = sorted(
            field for field, status in statuses.items() if status == "AMBIGUOUS"
        )

        if not hgnc_records:
            symbol_qc = "NOT_ASSESSED_NO_HGNC_MAPPING"
        elif upstream_ambiguous:
            symbol_qc = "NOT_ASSESSED_AMBIGUOUS_HGNC_MAPPING"
        elif source_row["Symbol"] in hgnc_symbols:
            symbol_qc = "MATCH"
        else:
            symbol_qc = "MISMATCH_CURRENT_HGNC"

        notes: list[str] = []
        if upstream_ambiguous:
            notes.append(f"exact Ensembl ID matched {len(hgnc_records)} HGNC records")
        if symbol_qc == "MISMATCH_CURRENT_HGNC":
            notes.append("registry symbol differs from current HGNC symbol; symbol was not used for mapping")
        if one_to_many_fields:
            notes.append("one-to-many fields retained without choosing a preferred identifier")

        row = {
            "EnsemblID": source_row["EnsemblID"],
            "EnsemblID_base": ensembl_base,
            "Symbol": source_row["Symbol"],
            "gene_type": source_row["gene_type"],
            "HGNC_ID": mapping_value(hgnc_ids),
            "HGNC_ID_status": statuses["HGNC_ID"],
            "HGNC_ID_source": HGNC_SOURCE,
            "Entrez_ID": mapping_value(entrez_ids),
            "Entrez_ID_status": statuses["Entrez_ID"],
            "Entrez_ID_source": HGNC_SOURCE,
            "UniProt_ID": mapping_value(uniprot_ids),
            "UniProt_ID_status": statuses["UniProt_ID"],
            "UniProt_ID_source": HGNC_SOURCE,
            "OpenTargets_target_ID": mapping_value(open_targets_ids),
            "OpenTargets_target_ID_status": statuses["OpenTargets_target_ID"],
            "OpenTargets_target_ID_source": OT_SOURCE,
            "ChEMBL_target_ID": mapping_value(chembl_ids),
            "ChEMBL_target_ID_status": statuses["ChEMBL_target_ID"],
            "ChEMBL_target_ID_source": CHEMBL_SOURCE,
            "ChEMBL_mapping_basis": "EXACT_HGNC_UNIPROT_TO_CHEMBL_COMPONENT_ACCESSION",
            "ChEMBL_matched_UniProt_ID": mapping_value(sorted(matched_accessions)),
            "current_HGNC_symbol": mapping_value(hgnc_symbols),
            "symbol_qc_status": symbol_qc,
            "one_to_many_fields": DELIMITER.join(one_to_many_fields) if one_to_many_fields else "NONE",
            "ambiguous_mapping": "TRUE" if ambiguous_fields else "FALSE",
            "ambiguous_fields": DELIMITER.join(ambiguous_fields) if ambiguous_fields else "NONE",
            "mapping_note": "; ".join(notes),
        }
        output.append(row)

    return list(output[0]), output


def validate_mapping(
    registry: list[dict[str, str]], fieldnames: list[str], mapping: list[dict[str, str]]
) -> None:
    if len(mapping) != len(registry) or len(mapping) != EXPECTED_ROWS:
        fail("Identifier mapping did not preserve every registry row")
    input_ids = [row["EnsemblID"] for row in registry]
    output_ids = [row["EnsemblID"] for row in mapping]
    if output_ids != input_ids:
        fail("Identifier mapping changed EnsemblID values or input row order")
    if len(set(output_ids)) != EXPECTED_ROWS:
        fail("Identifier mapping contains duplicate EnsemblID values")

    external_fields = (
        "HGNC_ID",
        "Entrez_ID",
        "UniProt_ID",
        "OpenTargets_target_ID",
        "ChEMBL_target_ID",
    )
    allowed_statuses = {"UNIQUE", "ONE_TO_MANY", "AMBIGUOUS", "NOT_FOUND"}
    for row in mapping:
        for field in external_fields:
            value = row[field]
            status = row[f"{field}_status"]
            source = row[f"{field}_source"]
            if not value or not status or not source:
                fail(f"Empty value/status/source for {field} at {row['EnsemblID']}")
            if status not in allowed_statuses:
                fail(f"Invalid mapping status {status!r} for {field}")
            if status == "NOT_FOUND" and value != "NOT_FOUND":
                fail(f"Non-explicit missing mapping for {field} at {row['EnsemblID']}")
            if status != "NOT_FOUND" and value == "NOT_FOUND":
                fail(f"Mapped status lacks value for {field} at {row['EnsemblID']}")
            value_count = 0 if value == "NOT_FOUND" else len(value.split(DELIMITER))
            if status == "UNIQUE" and value_count != 1:
                fail(f"UNIQUE status has {value_count} values for {field}")
            if status == "ONE_TO_MANY" and value_count < 2:
                fail(f"ONE_TO_MANY status has fewer than two values for {field}")

    forbidden = [
        field
        for field in fieldnames
        if any(token in field.lower() for token in ("score", "rank", "priority", "therapeutic"))
    ]
    if forbidden:
        fail(f"Forbidden score/rank/priority/therapeutic fields were emitted: {forbidden}")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def make_qc(
    registry: list[dict[str, str]], mapping: list[dict[str, str]]
) -> list[dict[str, Any]]:
    external_fields = (
        "HGNC_ID",
        "Entrez_ID",
        "UniProt_ID",
        "OpenTargets_target_ID",
        "ChEMBL_target_ID",
    )
    scopes = {
        "ALL_TESTED": list(range(len(mapping))),
        "U2_EFFECT_SUPPORTED_DE": [
            index
            for index, row in enumerate(registry)
            if row["U2_effect_supported_DE"] == "TRUE"
        ],
    }
    result: list[dict[str, Any]] = []
    for scope, indices in scopes.items():
        denominator = len(indices)
        for field in external_fields:
            statuses = Counter(mapping[index][f"{field}_status"] for index in indices)
            mapped = denominator - statuses["NOT_FOUND"]
            metrics = [
                ("MAPPED", mapped),
                ("NOT_FOUND", statuses["NOT_FOUND"]),
                ("UNIQUE", statuses["UNIQUE"]),
                ("ONE_TO_MANY", statuses["ONE_TO_MANY"]),
                ("AMBIGUOUS", statuses["AMBIGUOUS"]),
            ]
            for metric, count in metrics:
                result.append(
                    {
                        "scope": scope,
                        "identifier": field,
                        "metric": metric,
                        "count": count,
                        "denominator": denominator,
                        "percent": f"{100 * count / denominator:.6f}",
                    }
                )

        row_metrics = {
            "ANY_AMBIGUOUS_MAPPING": sum(
                mapping[index]["ambiguous_mapping"] == "TRUE" for index in indices
            ),
            "ANY_ONE_TO_MANY_MAPPING": sum(
                mapping[index]["one_to_many_fields"] != "NONE" for index in indices
            ),
            "SYMBOL_MATCH_CURRENT_HGNC": sum(
                mapping[index]["symbol_qc_status"] == "MATCH" for index in indices
            ),
            "SYMBOL_MISMATCH_CURRENT_HGNC": sum(
                mapping[index]["symbol_qc_status"] == "MISMATCH_CURRENT_HGNC"
                for index in indices
            ),
        }
        for metric, count in row_metrics.items():
            result.append(
                {
                    "scope": scope,
                    "identifier": "ROW_LEVEL_QC",
                    "metric": metric,
                    "count": count,
                    "denominator": denominator,
                    "percent": f"{100 * count / denominator:.6f}",
                }
            )
    return result


def qc_lookup(qc_rows: list[dict[str, Any]], scope: str, identifier: str, metric: str) -> int:
    matches = [
        row
        for row in qc_rows
        if row["scope"] == scope and row["identifier"] == identifier and row["metric"] == metric
    ]
    if len(matches) != 1:
        fail(f"QC lookup is not unique for {scope}/{identifier}/{metric}")
    return int(matches[0]["count"])


def percent(count: int, denominator: int) -> str:
    return f"{100 * count / denominator:.2f}%"


def write_summary(qc_rows: list[dict[str, Any]], source_meta: dict[str, dict[str, Any]]) -> None:
    identifiers = (
        "HGNC_ID",
        "Entrez_ID",
        "UniProt_ID",
        "OpenTargets_target_ID",
        "ChEMBL_target_ID",
    )
    labels = {
        "HGNC_ID": "HGNC",
        "Entrez_ID": "Entrez",
        "UniProt_ID": "UniProt",
        "OpenTargets_target_ID": "Open Targets",
        "ChEMBL_target_ID": "ChEMBL target",
    }
    coverage_lines: list[str] = []
    for field in identifiers:
        all_mapped = qc_lookup(qc_rows, "ALL_TESTED", field, "MAPPED")
        u2_mapped = qc_lookup(qc_rows, "U2_EFFECT_SUPPORTED_DE", field, "MAPPED")
        all_otm = qc_lookup(qc_rows, "ALL_TESTED", field, "ONE_TO_MANY")
        all_ambiguous = qc_lookup(qc_rows, "ALL_TESTED", field, "AMBIGUOUS")
        coverage_lines.append(
            f"| {labels[field]} | {all_mapped:,} ({percent(all_mapped, EXPECTED_ROWS)}) | "
            f"{u2_mapped:,} ({percent(u2_mapped, EXPECTED_U2)}) | {all_otm:,} | "
            f"{all_ambiguous:,} |"
        )

    ambiguous_rows = qc_lookup(
        qc_rows, "ALL_TESTED", "ROW_LEVEL_QC", "ANY_AMBIGUOUS_MAPPING"
    )
    one_to_many_rows = qc_lookup(
        qc_rows, "ALL_TESTED", "ROW_LEVEL_QC", "ANY_ONE_TO_MANY_MAPPING"
    )
    symbol_mismatches = qc_lookup(
        qc_rows, "ALL_TESTED", "ROW_LEVEL_QC", "SYMBOL_MISMATCH_CURRENT_HGNC"
    )
    text = f"""# Identifier Mapping Summary

**Task:** #009  
**Input genes retained:** {EXPECTED_ROWS:,} / {EXPECTED_ROWS:,}  
**U2 evidence candidates retained:** {EXPECTED_U2:,} / {EXPECTED_U2:,}  
**Primary key:** immutable versioned `EnsemblID`

## Mapping coverage

| Identifier | All tested genes | U2 genes | One-to-many, all genes | Ambiguous, all genes |
|---|---:|---:|---:|---:|
{chr(10).join(coverage_lines)}

`NOT_FOUND` is an explicit mapping result and does not mean that a gene lacks
biological relevance. Multiple identifiers are retained with `|`; the script
does not choose a preferred identifier.

## Quality-control observations

- Duplicate output `EnsemblID` values: **0**
- Missing registry rows: **0**
- Rows with at least one ambiguous mapping: **{ambiguous_rows:,}**
- Rows with at least one one-to-many mapping: **{one_to_many_rows:,}**
- Registry symbols differing from the current uniquely matched HGNC symbol:
  **{symbol_mismatches:,}**

Symbol differences are warnings only. Symbols were never mapping keys and no
symbol-based rescue was attempted.

## Source snapshot

- HGNC complete set: last modified `{source_meta['hgnc']['last_modified']}`;
  SHA256 `{source_meta['hgnc']['sha256']}`.
- Open Targets Platform: data `{source_meta['open_targets']['data_version']}`;
  API `{source_meta['open_targets']['api_version']}`.
- ChEMBL: `{source_meta['chembl']['database_version']}`, released
  `{source_meta['chembl']['release_date']}`.

Network access was used only for these official identifier resources. No
package was installed or updated. Raw responses were processed in memory; URL,
request-count, byte-count, version, and response-hash provenance are recorded
in `session_info.txt`.

## Warnings and interpretation limits

- These are current external mappings applied to the older GENCODE v26 gene
  universe, so retired or changed records are expected.
- A ChEMBL one-to-many mapping can reflect single-protein, complex, family, or
  other target records. Task #009 does not select among them.
- The ChEMBL route requires an exact HGNC-supplied UniProt accession; genes
  without that bridge remain `NOT_FOUND` rather than being guessed by symbol.
- Source databases evolve. This output and its recorded versions constitute a
  snapshot and must not be silently refreshed in later analyses.

## Explicit non-claims

No target score, ranking, drug prioritization, therapeutic direction, or
biological interpretation was generated. Identifier coverage is not evidence
of target quality or actionability.
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
    finished_at = datetime.now(timezone.utc).isoformat()
    lines = [
        "Task #009 identifier-normalization session",
        f"started_at_utc={started_at}",
        f"finished_at_utc={finished_at}",
        f"python_version={platform.python_version()}",
        f"python_implementation={platform.python_implementation()}",
        f"platform={platform.platform()}",
        f"tls_ca_file={TLS_CA_FILE}",
        f"git_branch={repo['branch']}",
        f"git_head={repo['head']}",
        f"frozen_task008_commit={TASK008_COMMIT}",
        f"git_origin={repo['remote']}",
        f"input_path={INPUT}",
        f"input_sha256={file_sha256(INPUT)}",
        "network_access=USED",
        "network_purpose=official identifier mapping only",
        "packages_installed_or_updated=FALSE",
        "gene_symbols_used_as_mapping_keys=FALSE",
        "raw_responses_committed=FALSE",
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
            f"{file_sha256(MAPPING)}  {MAPPING}",
            f"{file_sha256(QC)}  {QC}",
            f"{file_sha256(SUMMARY)}  {SUMMARY}",
        ]
    )
    SESSION.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    started_at = datetime.now(timezone.utc).isoformat()
    repo = validate_repository()
    registry, _ = read_registry()
    ensembl_ids = [row["EnsemblID_base"] for row in registry]

    print("Retrieving official HGNC complete-set mapping...", flush=True)
    hgnc_by_ensembl, hgnc_meta = retrieve_hgnc()
    print("Validating Ensembl IDs against Open Targets...", flush=True)
    ot_ids, ot_meta = retrieve_open_targets(ensembl_ids)
    print("Retrieving human ChEMBL target-component mapping...", flush=True)
    chembl_by_uniprot, chembl_meta = retrieve_chembl()

    fieldnames, mapping_rows = build_mapping(
        registry, hgnc_by_ensembl, ot_ids, chembl_by_uniprot
    )
    validate_mapping(registry, fieldnames, mapping_rows)
    qc_rows = make_qc(registry, mapping_rows)
    source_meta = {
        "hgnc": hgnc_meta,
        "open_targets": ot_meta,
        "chembl": chembl_meta,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(MAPPING, fieldnames, mapping_rows)
    write_csv(
        QC,
        ["scope", "identifier", "metric", "count", "denominator", "percent"],
        qc_rows,
    )
    write_summary(qc_rows, source_meta)
    write_session(repo, source_meta, started_at)

    print(f"Wrote {MAPPING} ({len(mapping_rows)} rows)")
    print(f"Wrote {QC} ({len(qc_rows)} QC rows)")
    print(f"Ambiguous rows: {sum(row['ambiguous_mapping'] == 'TRUE' for row in mapping_rows)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
