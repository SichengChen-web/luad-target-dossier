#!/usr/bin/env python3
"""Retrieve the governed Open Targets 26.06 LUAD disease-association snapshot.

This program performs source retrieval and snapshot validation only.  It does
not normalize evidence, create component states, materialize profiles, score,
rank, or interpret targets.

The source byte stream is the official Open Targets 26.06 AWS mirror declared
by that release's Croissant metadata.  Every source Parquet part is downloaded
in full to a temporary cache, checked against the release-published SHA1, and
hashed with SHA256.  Exact source-native rows satisfying both frozen boundaries
(`diseaseId == MONDO_0005061` and target in the Task 030 universe) are retained
without field transformation in one snapshot Parquet file per source part.

Required runtime: Python with pyarrow (validated with /opt/anaconda3/bin/python,
pyarrow 16.1.0).  No package installation is performed by this script.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import math
import os
import platform
import re
import shutil
import ssl
import subprocess
import sys
import tempfile
import threading
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable, Sequence

try:
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.parquet as pq
except ImportError as exc:  # pragma: no cover - explicit environment guard
    raise SystemExit(
        "pyarrow is required but is not installed in this Python runtime. "
        "No installation is authorized. On the reviewed system run: "
        "/opt/anaconda3/bin/python analysis/32B2C_retrieve_disease_association_snapshot.py"
    ) from exc


SCRIPT_VERSION = "TASK032B2C_RETRIEVER_V0.1"
SNAPSHOT_SCHEMA_VERSION = "DISEASE_ASSOCIATION_RAW_SNAPSHOT_SCHEMA_V0.1"
SOURCE_ID = "SRC_OPEN_TARGETS_PLATFORM"
SOURCE_VERSION = "26.06"
ACCESS_MODE = "OFFICIAL_RELEASE_PINNED_PARQUET_DATA_DOWNLOADS"
DISEASE_CONTEXT_ID = "MONDO_0005061"
DISEASE_CONTEXT_LABEL = "lung adenocarcinoma"
UNIVERSE_ID = "UNIV_TASK030_ENSEMBL_29606_V0_1"
UNIVERSE_EXPECTED_ROWS = 29_606
UNIVERSE_SHA256 = "e4b304eb5fde7690a1525b404f5d1a011837fd88f774b4dbb2838f2c81b9c1ab"
COMPONENT_ID = "COMP_DISEASE_ASSOCIATION"
COMPONENT_VERSION = "COMP_DISEASE_ASSOCIATION_V0.1"
QUERY_SCOPE_VERSION = "DA_QUERY_SCOPE_V0.1"
MAPPING_RULE_VERSION = "DA_OT_ENSEMBL_BASE_MAPPING_V0.1"
DISEASE_MAPPING_RULE_VERSION = "DA_LUAD_CONTEXT_MAPPING_V0.1"
AUTHORIZATION_ID = "AUTH_DA_OT_26_06_SNAPSHOT_V0_1"
AUTHORIZATION_STATUS = "APPROVED_FOR_SNAPSHOT_RETRIEVAL"

AWS_BUCKET_HTTP = "https://open-targets-public-data-releases.s3.amazonaws.com"
AWS_RELEASE_PREFIX = f"platform/{SOURCE_VERSION}"
AWS_RELEASE_ROOT = f"{AWS_BUCKET_HTTP}/{AWS_RELEASE_PREFIX}"
FTP_RELEASE_ROOT = (
    f"https://ftp.ebi.ac.uk/pub/databases/opentargets/platform/{SOURCE_VERSION}"
)
LICENSE_URL = "https://platform-docs.opentargets.org/licence"
ALLOWED_NETWORK_HOSTS = {
    "open-targets-public-data-releases.s3.amazonaws.com",
    "ftp.ebi.ac.uk",
    "platform-docs.opentargets.org",
}
USER_AGENT = "luad-target-dossier-task032b2c/0.1"
CONTROLLED_MAPPING_OUTCOMES = {
    "MAPPED",
    "NOT_FOUND",
    "AMBIGUOUS",
    "CONFLICTING",
    "UNKNOWN",
}
FORBIDDEN_OUTPUT_FIELDS = {
    "score",
    "ranking",
    "rank",
    "priority",
    "recommendation",
    "therapeutic_direction",
    "target_selection",
    "confidence_metric",
    "target_quality",
}

# Frozen Task 032A, 032B-1, 032B-2A, and 032B-2B governance inputs.
FROZEN_INPUT_SHA256 = {
    "docs/governance/evidence_component_interface_specification_v0.1.md": "b31254b347cbf440e3aade02857fb8149c54ea9a9a2b987197c4b724fefa20e8",
    "docs/governance/component_registration_policy_v0.1.md": "c1736e11695e6bb194665a0cf96115bb526075ca5aa9f9870e8e572f64302668",
    "docs/governance/component_validation_requirements_v0.1.md": "cc71c239972bc8f0b20fff63e4478624e0bcb56bc0febfc52855818ee5171c95",
    "docs/governance/component_dependency_model_v0.1.md": "5b77654a7ea543b2b2a184bba4a280cc4395c575065be6a3674d93a0955cdb06",
    "docs/governance/disease_association_component_registration_v0.1.md": "3f625be0234d234be9df555002cb48a1bf9afffc9b8b2e1ce9b51220df01c50a",
    "docs/governance/disease_association_component_scope_v0.1.md": "f153a296ba14fee53d142e836a0b07efddaf1793965cea04ce9ab46024a9faee",
    "docs/governance/disease_association_component_feature_contract_v0.1.md": "c4ead626b6e6f1616a0dc8e396d7a52495bb21523acd96567a98c50f3c6d9139",
    "docs/governance/disease_association_component_validation_plan_v0.1.md": "d96ad308cf2e795be2fcd8b3950491371709cc0a075386bcd8cdc1b9b1da4508",
    "docs/governance/disease_association_source_contract_v0.1.md": "48abb3e333acf764f1a4235442697fe8f401951451dfebdd33ca2c1f3d3a7914",
    "docs/governance/disease_context_definition_policy_v0.1.md": "20338c37a8c38f5bfe69402a5c507deba065d8d690bbd8b3364fa623c2e25e5a",
    "docs/governance/disease_association_snapshot_policy_v0.1.md": "f4d2643c34efea119702414bad27098dc59772a41b1a1e65b9caa816130e9f96",
    "docs/governance/disease_association_query_scope_policy_v0.1.md": "b285d986a58e16a30790285bf3a8621df2382c6d27e58f19613e0b58143dd1c6",
    "docs/governance/disease_association_source_selection_record_v0.1.md": "45cb84646742945552d5741b85bdbec5e709584d1aaea68555720764146f8de8",
    "docs/governance/disease_context_registration_v0.1.md": "6df7b8c9cd0452d377a58b7d7819aa35a23ec620728000cc97b7fc3aad3f2460",
    "docs/governance/disease_association_materialization_authorization_v0.1.md": "f9c99bb420705e70fb1295ea6a3e400f285e5229a30cd4ea19ce1e93816ed8a5",
    "outputs/profile_release_candidate_v0.1/universe_manifest.csv": UNIVERSE_SHA256,
}

FILE_INVENTORY_FIELDS = [
    "inventory_id",
    "artifact_role",
    "logical_dataset",
    "source_dataset",
    "relative_path_or_reference",
    "official_url",
    "file_size_bytes",
    "sha256",
    "official_sha1",
    "official_etag",
    "last_modified",
    "content_type",
    "parquet_row_count",
    "parquet_row_group_count",
    "schema_field_count",
    "schema_sha256",
    "retrieval_attempt_count",
    "retry_count",
    "http_status_summary",
    "integrity_status",
]

RAW_RECORD_FIELDS = [
    "raw_record_id",
    "source_record_id",
    "source_id",
    "source_version",
    "source_dataset",
    "source_target_id",
    "source_disease_id",
    "universe_EnsemblID",
    "source_file_path",
    "source_file_sha256",
    "source_row_group",
    "source_row_index",
    "snapshot_raw_file",
    "snapshot_raw_file_sha256",
    "snapshot_row_group",
    "snapshot_row_index",
    "raw_payload_sha256",
    "mapping_outcome",
]

COVERAGE_FIELDS = [
    "EnsemblID",
    "EnsemblID_base",
    "universe_ordinal",
    "universe_id",
    "target_mapping_outcome",
    "target_record_count",
    "exact_disease_record_count",
    "assessment_attempted",
    "source_release_complete",
    "mapping_rule_version",
    "disease_context_id",
    "query_scope_version",
    "provenance_complete",
]


class SnapshotError(RuntimeError):
    """Clear, governed snapshot failure."""


@dataclass(frozen=True)
class RemoteObject:
    key: str
    size: int
    etag: str
    last_modified: str

    @property
    def url(self) -> str:
        return f"{AWS_BUCKET_HTTP}/{urllib.parse.quote(self.key, safe='/')}"

    @property
    def release_relative_path(self) -> str:
        prefix = f"{AWS_RELEASE_PREFIX}/"
        if not self.key.startswith(prefix):
            raise SnapshotError(f"Object is outside frozen release: {self.key}")
        return self.key[len(prefix) :]


def find_repo_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / ".git").exists() and (candidate / "analysis").exists():
            return candidate
    raise SnapshotError("Could not resolve repository root from script path")


def file_hash(path: Path, algorithm: str = "sha256") -> str:
    h = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
            default=json_default,
        ).encode("utf-8")
    )


def pretty_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
            default=json_default,
        )
        + "\n"
    ).encode("utf-8")


def json_default(value: Any) -> Any:
    if isinstance(value, (dt.date, dt.datetime, dt.time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, bytes):
        return {"__bytes_hex__": value.hex()}
    if hasattr(value, "as_py"):
        return value.as_py()
    raise TypeError(f"Unsupported JSON value type: {type(value).__name__}")


def deterministic_csv_bytes(rows: Sequence[dict[str, Any]], fields: Sequence[str]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(fields), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fields})
    return stream.getvalue().encode("utf-8")


def write_bytes_checked(path: Path, payload: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    reread = path.read_bytes()
    if reread != payload:
        raise SnapshotError(f"Byte verification failed after writing {path}")
    return hashlib.sha256(payload).hexdigest()


def assert_network_url(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_NETWORK_HOSTS:
        raise SnapshotError(f"Network host is not authorized: {url}")
    if SOURCE_VERSION not in url and parsed.hostname != "platform-docs.opentargets.org":
        raise SnapshotError(f"Non-release-pinned source URL is prohibited: {url}")


def urlopen(request: urllib.request.Request, timeout: int = 180):
    assert_network_url(request.full_url)
    return urllib.request.urlopen(
        request,
        timeout=timeout,
        context=ssl.create_default_context(),
    )


def fetch_bytes(url: str, timeout: int = 180) -> tuple[bytes, dict[str, str]]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"},
    )
    with urlopen(request, timeout=timeout) as response:
        payload = response.read()
        headers = {key.lower(): value for key, value in response.headers.items()}
        headers["_http_status"] = str(getattr(response, "status", "UNKNOWN"))
    return payload, headers


def fetch_s3_inventory(
    prefix: str,
) -> tuple[list[RemoteObject], bytes, dict[str, str]]:
    query = urllib.parse.urlencode(
        {"list-type": "2", "prefix": prefix, "max-keys": "1000"}
    )
    url = f"{AWS_BUCKET_HTTP}/?{query}"
    payload, headers = fetch_bytes(url)
    root = ET.fromstring(payload)
    namespace = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
    truncated = root.findtext("s3:IsTruncated", namespaces=namespace)
    if truncated != "false":
        raise SnapshotError(f"S3 inventory unexpectedly truncated for prefix {prefix}")
    objects: list[RemoteObject] = []
    for node in root.findall("s3:Contents", namespace):
        key = node.findtext("s3:Key", namespaces=namespace)
        size = node.findtext("s3:Size", namespaces=namespace)
        etag = node.findtext("s3:ETag", namespaces=namespace)
        modified = node.findtext("s3:LastModified", namespaces=namespace)
        if None in (key, size, etag, modified):
            raise SnapshotError(f"Incomplete S3 inventory entry under {prefix}")
        objects.append(
            RemoteObject(
                key=key,
                size=int(size),
                etag=etag.strip('"'),
                last_modified=modified,
            )
        )
    return sorted(objects, key=lambda item: item.key), payload, headers


def download_parallel(
    url: str,
    size: int,
    destination: Path,
    range_workers: int,
    retries: int = 4,
) -> dict[str, int]:
    """Download exact bytes with disjoint HTTPS range requests and atomic publish."""
    assert_network_url(url)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".downloading")
    if temporary.exists():
        temporary.unlink()
    if size == 0:
        temporary.write_bytes(b"")
        temporary.replace(destination)
        return {"retrieval_attempt_count": 0, "retry_count": 0}

    workers = max(1, min(range_workers, math.ceil(size / (1024 * 1024))))
    chunk_size = math.ceil(size / workers)
    descriptor = os.open(temporary, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o644)
    os.ftruncate(descriptor, size)
    statistics = {"retrieval_attempt_count": 0, "retry_count": 0}
    statistics_lock = threading.Lock()

    def retrieve(index: int) -> int:
        start = index * chunk_size
        end = min(size - 1, ((index + 1) * chunk_size) - 1)
        expected = end - start + 1
        last_error: Exception | None = None
        for attempt in range(1, retries + 1):
            with statistics_lock:
                statistics["retrieval_attempt_count"] += 1
                if attempt > 1:
                    statistics["retry_count"] += 1
            try:
                request = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": USER_AGENT,
                        "Accept-Encoding": "identity",
                        "Range": f"bytes={start}-{end}",
                    },
                )
                with urlopen(request, timeout=240) as response:
                    payload = response.read()
                    status = getattr(response, "status", None)
                    content_range = response.headers.get("Content-Range", "")
                if status != 206:
                    raise SnapshotError(
                        f"Range request returned HTTP {status} for {url}"
                    )
                if content_range != f"bytes {start}-{end}/{size}":
                    raise SnapshotError(
                        f"Content-Range mismatch for {url}: {content_range}"
                    )
                if len(payload) != expected:
                    raise SnapshotError(
                        f"Range length mismatch for {url}: {len(payload)} != {expected}"
                    )
                os.pwrite(descriptor, payload, start)
                return expected
            except Exception as exc:  # deterministic retry of transport only
                last_error = exc
                if attempt == retries:
                    break
        raise SnapshotError(f"Failed range {start}-{end} for {url}: {last_error}")

    try:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            received = sum(pool.map(retrieve, range(workers)))
        if received != size:
            raise SnapshotError(f"Downloaded size mismatch for {url}: {received} != {size}")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    if temporary.stat().st_size != size:
        raise SnapshotError(f"Temporary file size mismatch for {url}")
    temporary.replace(destination)
    return statistics


def parse_integrity_index(payload: bytes) -> dict[str, str]:
    result: dict[str, str] = {}
    pattern = re.compile(rb"^([0-9a-f]{40})  \./(.+)$")
    for number, line in enumerate(payload.splitlines(), start=1):
        match = pattern.match(line)
        if not match:
            raise SnapshotError(f"Malformed integrity-index line {number}")
        digest = match.group(1).decode("ascii")
        relative_path = match.group(2).decode("utf-8")
        if relative_path in result:
            raise SnapshotError(f"Duplicate integrity path: {relative_path}")
        result[relative_path] = digest
    return result


def normalize_schema(schema: pa.Schema) -> str:
    return schema.to_string(show_field_metadata=True, show_schema_metadata=True)


def schema_digest(schema: pa.Schema) -> str:
    return hashlib.sha256(normalize_schema(schema).encode("utf-8")).hexdigest()


def parquet_write_options() -> dict[str, Any]:
    return {
        "version": "2.6",
        "compression": "snappy",
        "use_dictionary": True,
        "write_statistics": True,
        "data_page_version": "1.0",
    }


def source_record_payload_hash(record: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(record)).hexdigest()


def raw_record_identity(
    dataset: str,
    source_record_id: str,
    source_file: str,
    row_group: int,
    row_index: int,
) -> str:
    payload = {
        "source_dataset": dataset,
        "source_file": source_file,
        "source_record_id": source_record_id,
        "source_row_group": row_group,
        "source_row_index": row_index,
    }
    return "DA_RAW_" + hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def write_filtered_parquet(
    parquet_file: pq.ParquetFile,
    output_path: Path,
    predicate_kind: str,
    universe_values: pa.Array,
) -> tuple[int, list[dict[str, Any]], dict[str, list[str]], int]:
    """Write source-native selected rows, retaining source order and row groups."""
    required = {"id"}
    if predicate_kind == "disease":
        required |= {"name"}
    elif predicate_kind == "target":
        pass
    elif predicate_kind == "evidence":
        required |= {"targetId", "diseaseId"}
    else:
        raise SnapshotError(f"Unknown predicate kind: {predicate_kind}")
    missing = required - set(parquet_file.schema_arrow.names)
    if missing:
        raise SnapshotError(f"Required Parquet fields absent: {sorted(missing)}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    writer: pq.ParquetWriter | None = None
    selected_rows = 0
    selected_metadata: list[dict[str, Any]] = []
    target_payloads: dict[str, list[str]] = defaultdict(list)
    exact_disease_rows_outside_universe = 0
    snapshot_row_group = 0
    try:
        for source_row_group in range(parquet_file.num_row_groups):
            table = parquet_file.read_row_group(source_row_group)
            if predicate_kind == "disease":
                mask = pc.equal(table["id"], DISEASE_CONTEXT_ID)
            elif predicate_kind == "target":
                mask = pc.is_in(table["id"], value_set=universe_values)
            else:
                exact_mask = pc.equal(table["diseaseId"], DISEASE_CONTEXT_ID)
                universe_mask = pc.is_in(table["targetId"], value_set=universe_values)
                exact_count = int(pc.sum(pc.cast(exact_mask, pa.int64())).as_py() or 0)
                combined = pc.and_(exact_mask, universe_mask)
                combined_count = int(pc.sum(pc.cast(combined, pa.int64())).as_py() or 0)
                exact_disease_rows_outside_universe += exact_count - combined_count
                mask = combined
            positions = pc.indices_nonzero(mask).to_pylist()
            if not positions:
                continue
            filtered = table.filter(mask)
            if writer is None:
                writer = pq.ParquetWriter(
                    output_path,
                    filtered.schema,
                    **parquet_write_options(),
                )
            writer.write_table(filtered)
            records = filtered.to_pylist()
            for snapshot_row_index, (source_row_index, record) in enumerate(
                zip(positions, records, strict=True)
            ):
                source_record_id = str(record["id"])
                if not source_record_id or source_record_id == "None":
                    raise SnapshotError("Source record id is null")
                record_meta = {
                    "source_record_id": source_record_id,
                    "source_target_id": str(
                        record.get("targetId", record.get("id", ""))
                    ),
                    "source_disease_id": str(
                        record.get("diseaseId", record.get("id", ""))
                    ),
                    "source_row_group": source_row_group,
                    "source_row_index": int(source_row_index),
                    "snapshot_row_group": snapshot_row_group,
                    "snapshot_row_index": snapshot_row_index,
                    "raw_payload_sha256": source_record_payload_hash(record),
                }
                selected_metadata.append(record_meta)
                if predicate_kind == "target":
                    target_payloads[source_record_id].append(
                        record_meta["raw_payload_sha256"]
                    )
            selected_rows += filtered.num_rows
            snapshot_row_group += 1
    finally:
        if writer is not None:
            writer.close()
    if selected_rows == 0:
        if output_path.exists():
            output_path.unlink()
    elif not output_path.exists():
        raise SnapshotError(f"Filtered Parquet output was not created: {output_path}")
    return (
        selected_rows,
        selected_metadata,
        dict(target_payloads),
        exact_disease_rows_outside_universe,
    )


def validate_parquet_regeneration(path: Path) -> bool:
    source = pq.ParquetFile(path)
    with tempfile.TemporaryDirectory(prefix="task032b2c_determinism_") as folder:
        duplicate = Path(folder) / path.name
        writer: pq.ParquetWriter | None = None
        try:
            for row_group in range(source.num_row_groups):
                table = source.read_row_group(row_group)
                if writer is None:
                    writer = pq.ParquetWriter(
                        duplicate,
                        table.schema,
                        **parquet_write_options(),
                    )
                writer.write_table(table)
        finally:
            if writer is not None:
                writer.close()
        return file_hash(path) == file_hash(duplicate)


def inventory_id(role: str, relative_path: str) -> str:
    digest = hashlib.sha256(
        canonical_json_bytes({"artifact_role": role, "path": relative_path})
    ).hexdigest()
    return "INV_" + digest


def verify_frozen_inputs(repo: Path) -> dict[str, str]:
    observed: dict[str, str] = {}
    for relative, expected in FROZEN_INPUT_SHA256.items():
        path = repo / relative
        if not path.is_file():
            raise SnapshotError(f"Frozen input missing: {relative}")
        actual = file_hash(path)
        if actual != expected:
            raise SnapshotError(
                f"Frozen input changed: {relative}: {actual} != {expected}"
            )
        observed[relative] = actual
    return observed


def load_universe(repo: Path) -> list[dict[str, Any]]:
    path = repo / "outputs/profile_release_candidate_v0.1/universe_manifest.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != UNIVERSE_EXPECTED_ROWS:
        raise SnapshotError(f"Universe row count mismatch: {len(rows)}")
    expected_ordinals = list(range(1, UNIVERSE_EXPECTED_ROWS + 1))
    observed_ordinals = [int(row["universe_ordinal"]) for row in rows]
    if observed_ordinals != expected_ordinals:
        raise SnapshotError("Task 030 canonical universe order is not contiguous")
    ids = [row["EnsemblID"] for row in rows]
    if len(set(ids)) != UNIVERSE_EXPECTED_ROWS:
        raise SnapshotError("Task 030 EnsemblID values are not unique")
    bases = [identifier.split(".", 1)[0] for identifier in ids]
    if len(set(bases)) != UNIVERSE_EXPECTED_ROWS:
        raise SnapshotError("Version-stripped Ensembl IDs are ambiguous in Task 030")
    for row, base in zip(rows, bases, strict=True):
        if not re.fullmatch(r"ENSG[0-9]{11}", base):
            raise SnapshotError(f"Invalid Ensembl base identifier: {base}")
        row["EnsemblID_base"] = base
    return rows


def parse_croissant(payload: bytes) -> tuple[dict[str, Any], list[str]]:
    metadata = json.loads(payload)
    if metadata.get("version") != SOURCE_VERSION:
        raise SnapshotError(
            f"Croissant release mismatch: {metadata.get('version')} != {SOURCE_VERSION}"
        )
    if metadata.get("datePublished") != "2026-06-23":
        raise SnapshotError(
            f"Unexpected 26.06 release date: {metadata.get('datePublished')}"
        )
    if metadata.get("license") != "https://creativecommons.org/publicdomain/zero/1.0/":
        raise SnapshotError(f"Unexpected Platform license: {metadata.get('license')}")
    record_sets = metadata.get("recordSet", [])
    names = sorted(record.get("name", "") for record in record_sets)
    if "disease" not in names or "target" not in names:
        raise SnapshotError("Croissant metadata lacks disease or target record set")
    evidence_names = sorted(name for name in names if name.startswith("evidence_"))
    if not evidence_names:
        raise SnapshotError("Croissant metadata contains no evidence datasets")
    distributions = {
        item.get("@id"): item.get("contentUrl")
        for item in metadata.get("distribution", [])
    }
    expected_s3 = f"s3://open-targets-public-data-releases/platform/{SOURCE_VERSION}/output/"
    if distributions.get("aws-location") != expected_s3:
        raise SnapshotError("Croissant AWS release location differs from frozen mirror")
    return metadata, evidence_names


def process_parquet_object(
    remote: RemoteObject,
    logical_dataset: str,
    source_dataset: str,
    predicate_kind: str,
    output_root: Path,
    cache_root: Path,
    integrity_index: dict[str, str],
    universe_values: pa.Array,
    range_workers: int,
) -> dict[str, Any]:
    relative = remote.release_relative_path
    expected_sha1 = integrity_index.get(relative)
    if expected_sha1 is None:
        raise SnapshotError(f"Release integrity index lacks {relative}")
    cache_name = hashlib.sha256(relative.encode("utf-8")).hexdigest() + ".parquet"
    cached = cache_root / cache_name
    download_statistics = download_parallel(
        remote.url, remote.size, cached, range_workers=range_workers
    )
    if cached.stat().st_size != remote.size:
        raise SnapshotError(f"Source size mismatch: {relative}")
    observed_sha1 = file_hash(cached, "sha1")
    if observed_sha1 != expected_sha1:
        raise SnapshotError(
            f"Official SHA1 mismatch for {relative}: {observed_sha1} != {expected_sha1}"
        )
    observed_sha256 = file_hash(cached, "sha256")
    parquet_file = pq.ParquetFile(cached)
    raw_relative = Path("raw") / predicate_kind / source_dataset / Path(relative).name
    raw_path = output_root / raw_relative
    selected_rows, selected_metadata, target_payloads, outside_universe = (
        write_filtered_parquet(
            parquet_file,
            raw_path,
            predicate_kind=predicate_kind,
            universe_values=universe_values,
        )
    )
    source_inventory = {
        "inventory_id": inventory_id("REMOTE_SOURCE_FILE", relative),
        "artifact_role": "REMOTE_SOURCE_FILE",
        "logical_dataset": logical_dataset,
        "source_dataset": source_dataset,
        "relative_path_or_reference": relative,
        "official_url": remote.url,
        "file_size_bytes": remote.size,
        "sha256": observed_sha256,
        "official_sha1": expected_sha1,
        "official_etag": remote.etag,
        "last_modified": remote.last_modified,
        "content_type": "application/vnd.apache.parquet",
        "parquet_row_count": parquet_file.metadata.num_rows,
        "parquet_row_group_count": parquet_file.num_row_groups,
        "schema_field_count": len(parquet_file.schema_arrow.names),
        "schema_sha256": schema_digest(parquet_file.schema_arrow),
        "retrieval_attempt_count": download_statistics["retrieval_attempt_count"],
        "retry_count": download_statistics["retry_count"],
        "http_status_summary": "206_PARTIAL_CONTENT",
        "integrity_status": "VERIFIED_SHA1_AND_SHA256",
    }
    raw_inventory = None
    raw_sha256 = ""
    if selected_rows:
        raw_sha256 = file_hash(raw_path)
        raw_pf = pq.ParquetFile(raw_path)
        if raw_pf.metadata.num_rows != selected_rows:
            raise SnapshotError(f"Raw snapshot row count mismatch: {raw_relative}")
        raw_inventory = {
            "inventory_id": inventory_id("SNAPSHOT_RAW_FILE", raw_relative.as_posix()),
            "artifact_role": "SNAPSHOT_RAW_FILE",
            "logical_dataset": logical_dataset,
            "source_dataset": source_dataset,
            "relative_path_or_reference": raw_relative.as_posix(),
            "official_url": "NOT_APPLICABLE_PROJECT_SNAPSHOT_ARTIFACT",
            "file_size_bytes": raw_path.stat().st_size,
            "sha256": raw_sha256,
            "official_sha1": "NOT_APPLICABLE_PROJECT_SNAPSHOT_ARTIFACT",
            "official_etag": "NOT_APPLICABLE_PROJECT_SNAPSHOT_ARTIFACT",
            "last_modified": "NOT_USED_FOR_IDENTITY",
            "content_type": "application/vnd.apache.parquet",
            "parquet_row_count": selected_rows,
            "parquet_row_group_count": raw_pf.num_row_groups,
            "schema_field_count": len(raw_pf.schema_arrow.names),
            "schema_sha256": schema_digest(raw_pf.schema_arrow),
            "retrieval_attempt_count": "NOT_APPLICABLE_LOCAL_PACKAGING",
            "retry_count": "NOT_APPLICABLE_LOCAL_PACKAGING",
            "http_status_summary": "NOT_APPLICABLE_LOCAL_PACKAGING",
            "integrity_status": "VERIFIED_SHA256",
        }
        if raw_inventory["schema_sha256"] != source_inventory["schema_sha256"]:
            raise SnapshotError(f"Schema changed while filtering {relative}")
    try:
        cached.unlink()
    except FileNotFoundError:
        pass
    return {
        "remote": remote,
        "source_inventory": source_inventory,
        "raw_inventory": raw_inventory,
        "selected_rows": selected_rows,
        "selected_metadata": selected_metadata,
        "target_payloads": target_payloads,
        "outside_universe": outside_universe,
        "raw_relative": raw_relative.as_posix() if selected_rows else "",
        "raw_sha256": raw_sha256,
    }


def make_control_inventory(
    path: Path,
    output_root: Path,
    role: str,
    official_url: str,
    headers: dict[str, str],
    logical_dataset: str = "release_control",
) -> dict[str, Any]:
    relative = path.relative_to(output_root).as_posix()
    return {
        "inventory_id": inventory_id(role, relative),
        "artifact_role": role,
        "logical_dataset": logical_dataset,
        "source_dataset": "release_control",
        "relative_path_or_reference": relative,
        "official_url": official_url,
        "file_size_bytes": path.stat().st_size,
        "sha256": file_hash(path),
        "official_sha1": "NOT_PUBLISHED_FOR_THIS_CONTROL_ARTIFACT",
        "official_etag": headers.get("etag", "NOT_RECORDED"),
        "last_modified": headers.get("last-modified", "NOT_RECORDED"),
        "content_type": headers.get("content-type", "application/octet-stream"),
        "parquet_row_count": "NOT_APPLICABLE",
        "parquet_row_group_count": "NOT_APPLICABLE",
        "schema_field_count": "NOT_APPLICABLE",
        "schema_sha256": "NOT_APPLICABLE",
        "retrieval_attempt_count": 1,
        "retry_count": 0,
        "http_status_summary": headers.get("_http_status", "UNKNOWN"),
        "integrity_status": "VERIFIED_SHA256",
    }


def output_has_forbidden_fields(fields: Iterable[str]) -> list[str]:
    return sorted(set(fields) & FORBIDDEN_OUTPUT_FIELDS)


def build_summary(
    snapshot_version: str,
    release_date: str,
    evidence_dataset_count: int,
    source_parquet_count: int,
    source_bytes: int,
    raw_parquet_count: int,
    raw_bytes: int,
    raw_record_count: int,
    mapping_counts: Counter[str],
    outside_universe_count: int,
    qc_checks: Sequence[tuple[str, bool, str]],
) -> str:
    status = "PASS" if all(passed for _, passed, _ in qc_checks) else "FAIL"
    mapping_lines = "\n".join(
        f"- `{state}`: {mapping_counts.get(state, 0):,}"
        for state in sorted(CONTROLLED_MAPPING_OUTCOMES)
    )
    check_lines = "\n".join(
        f"- {'PASS' if passed else 'FAIL'} — `{name}`: {detail}"
        for name, passed, detail in qc_checks
    )
    return f"""# Disease Association Snapshot QC Report

**Task:** #032B-2C  
**Snapshot version:** `{snapshot_version}`  
**Validation status:** **{status}**

## Frozen scope

- Source: `{SOURCE_ID}`
- Release: `{SOURCE_VERSION}` (published `{release_date}`)
- Access: `{ACCESS_MODE}`
- Disease context: exact `{DISEASE_CONTEXT_ID}` (`{DISEASE_CONTEXT_LABEL}`)
- Entity universe: `{UNIVERSE_ID}` ({UNIVERSE_EXPECTED_ROWS:,} immutable EnsemblID entries)
- Logical evidence dataset: {evidence_dataset_count} source-native `evidence_*` record sets declared by the release metadata

## Snapshot contents

- Fully downloaded and integrity-checked source Parquet parts: {source_parquet_count:,}
- Source Parquet bytes checked: {source_bytes:,}
- Exact-scope raw Parquet parts retained: {raw_parquet_count:,}
- Exact-scope raw Parquet bytes retained: {raw_bytes:,}
- Exact LUAD/universe source-native evidence records retained: {raw_record_count:,}
- Exact LUAD evidence rows outside the frozen universe: {outside_universe_count:,} (excluded by the registered universe boundary and counted only for scope reconciliation)

Raw records were selected without merging, aggregation, score transformation, or biological interpretation. Source-native score fields, when present, remain unchanged inside the raw Parquet payloads and are not exposed as normalized features.

## Target mapping outcomes

{mapping_lines}

`NOT_FOUND` means no exact Open Targets target `id` matched the version-stripped Ensembl identifier. It is not negative biological evidence. No symbol-based or free-text mapping was used.

## Validation checks

{check_lines}

## Interpretation boundary

This snapshot records available source-native observations and explicit retrieval/mapping outcomes only. It does not create normalized features, component states, profiles, scores, rankings, priorities, recommendations, disease-causality claims, or therapeutic interpretations.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default="outputs/disease_association_snapshot_v0.1",
        help="Repository-relative output directory",
    )
    parser.add_argument(
        "--cache-dir",
        default="/private/tmp/luad_task032b2c_cache",
        help="Temporary full-source download cache (not a snapshot artifact)",
    )
    parser.add_argument("--file-workers", type=int, default=2)
    parser.add_argument("--range-workers", type=int, default=8)
    args = parser.parse_args()

    repo = find_repo_root()
    output_root = (repo / args.output_dir).resolve()
    expected_parent = (repo / "outputs").resolve()
    if expected_parent not in output_root.parents:
        raise SnapshotError("Output directory must be below repository outputs/")
    cache_root = Path(args.cache_dir).resolve()
    if cache_root != Path("/private/tmp/luad_task032b2c_cache"):
        raise SnapshotError(
            "v0.1 cache path is pinned to /private/tmp/luad_task032b2c_cache"
        )
    if args.file_workers < 1 or args.range_workers < 1:
        raise SnapshotError("Worker counts must be positive")
    final_marker = output_root / "snapshot_manifest.json"
    if final_marker.exists():
        raise SnapshotError(
            "A completed snapshot already exists. Immutable artifacts are not overwritten."
        )
    output_root.mkdir(parents=True, exist_ok=True)
    cache_root.mkdir(parents=True, exist_ok=True)
    retrieval_started_at_utc = dt.datetime.now(dt.timezone.utc).isoformat()

    frozen_before = verify_frozen_inputs(repo)
    universe_rows = load_universe(repo)
    universe_bases = [row["EnsemblID_base"] for row in universe_rows]
    base_to_versioned = {
        row["EnsemblID_base"]: row["EnsemblID"] for row in universe_rows
    }
    universe_values = pa.array(sorted(universe_bases), type=pa.string())

    raw_release = output_root / "raw/release"
    raw_release.mkdir(parents=True, exist_ok=True)
    inventory_rows: list[dict[str, Any]] = []

    # Freeze release metadata and official license documentation.
    control_specs = [
        ("croissant.json", f"{AWS_RELEASE_ROOT}/croissant.json"),
        ("release_data_integrity", f"{AWS_RELEASE_ROOT}/release_data_integrity"),
        ("release_data_integrity.sha1", f"{AWS_RELEASE_ROOT}/release_data_integrity.sha1"),
        ("open_targets_license.html", LICENSE_URL),
    ]
    control_headers: dict[str, dict[str, str]] = {}
    for name, url in control_specs:
        payload, headers = fetch_bytes(url, timeout=300)
        destination = raw_release / name
        write_bytes_checked(destination, payload)
        control_headers[name] = headers
        inventory_rows.append(
            make_control_inventory(
                destination,
                output_root,
                "LICENSE_ARTIFACT" if name == "open_targets_license.html" else "RELEASE_CONTROL_ARTIFACT",
                url,
                headers,
            )
        )

    integrity_payload = (raw_release / "release_data_integrity").read_bytes()
    integrity_sha1_text = (
        raw_release / "release_data_integrity.sha1"
    ).read_text(encoding="utf-8").strip()
    match = re.fullmatch(r"([0-9a-f]{40})  release_data_integrity", integrity_sha1_text)
    if not match:
        raise SnapshotError("Malformed release_data_integrity.sha1")
    if hashlib.sha1(integrity_payload).hexdigest() != match.group(1):
        raise SnapshotError("Official release integrity index SHA1 validation failed")
    integrity_index = parse_integrity_index(integrity_payload)

    croissant_payload = (raw_release / "croissant.json").read_bytes()
    croissant, evidence_datasets = parse_croissant(croissant_payload)

    prefixes = {
        "disease": f"{AWS_RELEASE_PREFIX}/output/disease/",
        "target": f"{AWS_RELEASE_PREFIX}/output/target/",
        "evidence": f"{AWS_RELEASE_PREFIX}/output/evidence_",
    }
    remote_objects: list[RemoteObject] = []
    for logical, prefix in prefixes.items():
        objects, inventory_payload, inventory_headers = fetch_s3_inventory(prefix)
        if not objects:
            raise SnapshotError(f"Official object inventory empty for {logical}")
        inventory_name = f"s3_object_inventory_{logical}.xml"
        destination = raw_release / inventory_name
        write_bytes_checked(destination, inventory_payload)
        inventory_rows.append(
            make_control_inventory(
                destination,
                output_root,
                "RELEASE_OBJECT_INVENTORY",
                f"{AWS_BUCKET_HTTP}/?list-type=2&prefix={urllib.parse.quote(prefix, safe='')}&max-keys=1000",
                inventory_headers,
                logical_dataset=logical,
            )
        )
        remote_objects.extend(objects)

    parquet_objects = [obj for obj in remote_objects if obj.key.endswith(".parquet")]
    marker_objects = [obj for obj in remote_objects if obj.key.endswith("/_SUCCESS")]
    unexpected = [
        obj.key
        for obj in remote_objects
        if not (obj.key.endswith(".parquet") or obj.key.endswith("/_SUCCESS"))
    ]
    if unexpected:
        raise SnapshotError(f"Unexpected release objects: {unexpected[:5]}")
    observed_evidence_datasets = sorted(
        {obj.key.split("/")[3] for obj in parquet_objects if "/evidence_" in obj.key}
    )
    if observed_evidence_datasets != evidence_datasets:
        raise SnapshotError(
            "Croissant evidence record sets differ from official object inventory"
        )

    # Integrity-record zero-byte completion markers without network download.
    for marker in marker_objects:
        relative = marker.release_relative_path
        expected_sha1 = integrity_index.get(relative)
        if marker.size != 0 or expected_sha1 != hashlib.sha1(b"").hexdigest():
            raise SnapshotError(f"Invalid completion marker: {relative}")
        dataset = marker.key.split("/")[3]
        logical = "evidence" if dataset.startswith("evidence_") else dataset
        inventory_rows.append(
            {
                "inventory_id": inventory_id("REMOTE_SUCCESS_MARKER", relative),
                "artifact_role": "REMOTE_SUCCESS_MARKER",
                "logical_dataset": logical,
                "source_dataset": dataset,
                "relative_path_or_reference": relative,
                "official_url": marker.url,
                "file_size_bytes": 0,
                "sha256": hashlib.sha256(b"").hexdigest(),
                "official_sha1": expected_sha1,
                "official_etag": marker.etag,
                "last_modified": marker.last_modified,
                "content_type": "application/octet-stream",
                "parquet_row_count": "NOT_APPLICABLE",
                "parquet_row_group_count": "NOT_APPLICABLE",
                "schema_field_count": "NOT_APPLICABLE",
                "schema_sha256": "NOT_APPLICABLE",
                "retrieval_attempt_count": 0,
                "retry_count": 0,
                "http_status_summary": "DISCOVERED_IN_VERIFIED_S3_LIST_RESPONSE",
                "integrity_status": "VERIFIED_ZERO_BYTE_MARKER",
            }
        )

    def classify(remote: RemoteObject) -> tuple[str, str, str]:
        dataset = remote.key.split("/")[3]
        if dataset == "disease":
            return "disease", dataset, "disease"
        if dataset == "target":
            return "target", dataset, "target"
        if dataset.startswith("evidence_"):
            return "evidence", dataset, "evidence"
        raise SnapshotError(f"Unauthorized source dataset: {dataset}")

    processing_results: list[dict[str, Any]] = []
    print(
        f"Retrieving {len(parquet_objects)} Parquet parts "
        f"({sum(obj.size for obj in parquet_objects):,} bytes) from official release {SOURCE_VERSION}",
        flush=True,
    )
    with ThreadPoolExecutor(max_workers=args.file_workers) as pool:
        futures = {}
        for remote in parquet_objects:
            logical, source_dataset, predicate = classify(remote)
            future = pool.submit(
                process_parquet_object,
                remote,
                logical,
                source_dataset,
                predicate,
                output_root,
                cache_root,
                integrity_index,
                universe_values,
                args.range_workers,
            )
            futures[future] = remote
        completed = 0
        for future in as_completed(futures):
            remote = futures[future]
            result = future.result()
            processing_results.append(result)
            completed += 1
            print(
                f"[{completed}/{len(parquet_objects)}] {remote.release_relative_path}: "
                f"{result['selected_rows']} selected rows",
                flush=True,
            )

    processing_results.sort(key=lambda item: item["remote"].key)
    retrieval_completed_at_utc = dt.datetime.now(dt.timezone.utc).isoformat()
    target_payloads: dict[str, list[str]] = defaultdict(list)
    evidence_counts: Counter[str] = Counter()
    raw_record_rows: list[dict[str, Any]] = []
    disease_records: list[dict[str, Any]] = []
    outside_universe_count = 0

    # First resolve the complete target entity table. Evidence mapping outcomes
    # must not depend on source-file completion or lexical processing order.
    for result in processing_results:
        remote = result["remote"]
        dataset = remote.key.split("/")[3]
        if dataset == "target":
            for target_id, payloads in result["target_payloads"].items():
                target_payloads[target_id].extend(payloads)

    for result in processing_results:
        inventory_rows.append(result["source_inventory"])
        if result["raw_inventory"] is not None:
            inventory_rows.append(result["raw_inventory"])
        outside_universe_count += result["outside_universe"]
        remote = result["remote"]
        dataset = remote.key.split("/")[3]
        if dataset == "disease":
            disease_records.extend(result["selected_metadata"])
        if dataset.startswith("evidence_"):
            for metadata in result["selected_metadata"]:
                target_id = metadata["source_target_id"]
                evidence_counts[target_id] += 1
                source_record_id = metadata["source_record_id"]
                raw_record_rows.append(
                    {
                        "raw_record_id": raw_record_identity(
                            dataset,
                            source_record_id,
                            remote.release_relative_path,
                            metadata["source_row_group"],
                            metadata["source_row_index"],
                        ),
                        "source_record_id": source_record_id,
                        "source_id": SOURCE_ID,
                        "source_version": SOURCE_VERSION,
                        "source_dataset": dataset,
                        "source_target_id": target_id,
                        "source_disease_id": metadata["source_disease_id"],
                        "universe_EnsemblID": base_to_versioned[target_id],
                        "source_file_path": remote.release_relative_path,
                        "source_file_sha256": result["source_inventory"]["sha256"],
                        "source_row_group": metadata["source_row_group"],
                        "source_row_index": metadata["source_row_index"],
                        "snapshot_raw_file": result["raw_relative"],
                        "snapshot_raw_file_sha256": result["raw_sha256"],
                        "snapshot_row_group": metadata["snapshot_row_group"],
                        "snapshot_row_index": metadata["snapshot_row_index"],
                        "raw_payload_sha256": metadata["raw_payload_sha256"],
                        "mapping_outcome": "PENDING_TARGET_LEDGER_RESOLUTION",
                    }
                )

    if len(disease_records) != 1:
        raise SnapshotError(
            f"Exact disease identity expected one row, observed {len(disease_records)}"
        )
    # Confirm name from retained source-native disease row.
    disease_raw_files = [
        output_root / row["relative_path_or_reference"]
        for row in inventory_rows
        if row["artifact_role"] == "SNAPSHOT_RAW_FILE"
        and row["source_dataset"] == "disease"
    ]
    disease_table = pq.read_table(disease_raw_files)
    if disease_table.num_rows != 1:
        raise SnapshotError("Retained disease artifact does not contain exactly one row")
    disease_name = disease_table["name"][0].as_py()
    if str(disease_name).lower() != DISEASE_CONTEXT_LABEL:
        raise SnapshotError(
            f"Disease label mismatch: {disease_name!r} != {DISEASE_CONTEXT_LABEL!r}"
        )

    coverage_rows: list[dict[str, Any]] = []
    mapping_counts: Counter[str] = Counter()
    target_outcomes: dict[str, str] = {}
    for row in universe_rows:
        base = row["EnsemblID_base"]
        payloads = target_payloads.get(base, [])
        if not payloads:
            outcome = "NOT_FOUND"
        elif len(payloads) == 1:
            outcome = "MAPPED"
        elif len(set(payloads)) == 1:
            outcome = "AMBIGUOUS"
        else:
            outcome = "CONFLICTING"
        target_outcomes[base] = outcome
        mapping_counts[outcome] += 1
        coverage_rows.append(
            {
                "EnsemblID": row["EnsemblID"],
                "EnsemblID_base": base,
                "universe_ordinal": row["universe_ordinal"],
                "universe_id": UNIVERSE_ID,
                "target_mapping_outcome": outcome,
                "target_record_count": len(payloads),
                "exact_disease_record_count": evidence_counts.get(base, 0),
                "assessment_attempted": "TRUE",
                "source_release_complete": "TRUE",
                "mapping_rule_version": MAPPING_RULE_VERSION,
                "disease_context_id": DISEASE_CONTEXT_ID,
                "query_scope_version": QUERY_SCOPE_VERSION,
                "provenance_complete": "TRUE",
            }
        )

    for row in raw_record_rows:
        row["mapping_outcome"] = target_outcomes[row["source_target_id"]]

    raw_record_rows.sort(
        key=lambda row: (
            row["source_dataset"],
            row["source_file_path"],
            int(row["source_row_group"]),
            int(row["source_row_index"]),
        )
    )
    if len({row["raw_record_id"] for row in raw_record_rows}) != len(raw_record_rows):
        raise SnapshotError("Raw record identity collision")
    if any(row["source_disease_id"] != DISEASE_CONTEXT_ID for row in raw_record_rows):
        raise SnapshotError("Non-exact disease record entered raw record manifest")
    if any(row["universe_EnsemblID"] not in {x["EnsemblID"] for x in universe_rows} for row in raw_record_rows):
        raise SnapshotError("Record outside frozen universe entered raw manifest")

    inventory_rows.sort(
        key=lambda row: (
            row["artifact_role"],
            row["logical_dataset"],
            row["source_dataset"],
            row["relative_path_or_reference"],
        )
    )
    if len({row["inventory_id"] for row in inventory_rows}) != len(inventory_rows):
        raise SnapshotError("File inventory identity collision")
    if output_has_forbidden_fields(FILE_INVENTORY_FIELDS + RAW_RECORD_FIELDS + COVERAGE_FIELDS):
        raise SnapshotError("Forbidden field exists in governed output schema")
    if not set(mapping_counts).issubset(CONTROLLED_MAPPING_OUTCOMES):
        raise SnapshotError("Uncontrolled target mapping outcome")

    release_manifest = {
        "access_mode": ACCESS_MODE,
        "authorized_logical_datasets": ["disease", "evidence", "target"],
        "croissant_artifact": "raw/release/croissant.json",
        "croissant_sha256": file_hash(raw_release / "croissant.json"),
        "disease_context_id": DISEASE_CONTEXT_ID,
        "evidence_source_datasets": evidence_datasets,
        "integrity_artifact": "raw/release/release_data_integrity",
        "integrity_artifact_sha1": file_hash(
            raw_release / "release_data_integrity", "sha1"
        ),
        "integrity_artifact_sha256": file_hash(raw_release / "release_data_integrity"),
        "license": "CC0-1.0",
        "license_artifact": "raw/release/open_targets_license.html",
        "license_artifact_sha256": file_hash(
            raw_release / "open_targets_license.html"
        ),
        "license_reference": LICENSE_URL,
        "license_storage_review": "APPROVED_BY_TASK032B2B_FOR_RAW_SNAPSHOT_RETRIEVAL",
        "license_redistribution_status": "CC0_1_0_PLATFORM_DATA_WITH_UPSTREAM_ATTRIBUTION_BOUNDARIES_RETAINED",
        "release_documentation_identity": "OPEN_TARGETS_26.06_CROISSANT_METADATA",
        "release_documentation_sha256": file_hash(raw_release / "croissant.json"),
        "release_date": croissant["datePublished"],
        "source_disease_identifier_namespace": "Open Targets disease ontology graph with MONDO identifiers",
        "source_evidence_type_vocabulary_version": "OPEN_TARGETS_26.06_EVIDENCE_DATASET_NAMES",
        "source_name": "Open Targets Platform",
        "source_record_semantics_version": "OPEN_TARGETS_26.06_CROISSANT_RECORD_SETS",
        "source_release_id": "OPEN_TARGETS_PLATFORM_26.06",
        "source_target_identifier_namespace": "Ensembl gene ID",
        "release_mirrors": {
            "aws": f"s3://open-targets-public-data-releases/platform/{SOURCE_VERSION}/output/",
            "ftp": f"{FTP_RELEASE_ROOT}/output/",
            "gcp": f"gs://open-targets-data-releases/{SOURCE_VERSION}/output/",
        },
        "source_authority": "Open Targets consortium",
        "source_id": SOURCE_ID,
        "source_version": SOURCE_VERSION,
    }
    release_manifest_path = output_root / "release_manifest.json"
    release_manifest_sha = write_bytes_checked(
        release_manifest_path, pretty_json_bytes(release_manifest)
    )

    file_inventory_payload = deterministic_csv_bytes(
        inventory_rows, FILE_INVENTORY_FIELDS
    )
    file_inventory_sha = write_bytes_checked(
        output_root / "file_inventory.csv", file_inventory_payload
    )
    raw_record_payload = deterministic_csv_bytes(raw_record_rows, RAW_RECORD_FIELDS)
    raw_record_manifest_sha = write_bytes_checked(
        output_root / "raw_record_manifest.csv", raw_record_payload
    )
    coverage_payload = deterministic_csv_bytes(coverage_rows, COVERAGE_FIELDS)
    coverage_sha = write_bytes_checked(
        output_root / "entity_coverage_ledger.csv", coverage_payload
    )

    # Determinism and raw-file fidelity checks.
    raw_snapshot_paths = sorted(
        output_root / row["relative_path_or_reference"]
        for row in inventory_rows
        if row["artifact_role"] == "SNAPSHOT_RAW_FILE"
    )
    deterministic_parquet = all(
        validate_parquet_regeneration(path) for path in raw_snapshot_paths
    )
    source_parquet_rows = [
        row for row in inventory_rows if row["artifact_role"] == "REMOTE_SOURCE_FILE"
    ]
    source_schema_by_dataset: dict[str, set[str]] = defaultdict(set)
    for row in source_parquet_rows:
        source_schema_by_dataset[row["source_dataset"]].add(row["schema_sha256"])
    schema_consistent = all(len(values) == 1 for values in source_schema_by_dataset.values())
    provenance_complete = all(
        row["source_record_id"]
        and row["source_file_sha256"]
        and row["snapshot_raw_file_sha256"]
        and row["raw_payload_sha256"]
        for row in raw_record_rows
    )

    qc_checks: list[tuple[str, bool, str]] = [
        ("frozen_input_hashes", True, f"{len(frozen_before)} frozen inputs verified"),
        ("source_release_identity", croissant["version"] == SOURCE_VERSION, SOURCE_VERSION),
        ("official_integrity_index", True, "published SHA1 and every selected source part verified"),
        ("schema_capture", schema_consistent, f"{len(source_schema_by_dataset)} source schemas captured"),
        ("disease_exact_match", len(disease_records) == 1, f"1 exact {DISEASE_CONTEXT_ID} disease row"),
        ("entity_coverage", len(coverage_rows) == UNIVERSE_EXPECTED_ROWS, f"{len(coverage_rows)} ledger rows"),
        ("identifier_mapping", sum(mapping_counts.values()) == UNIVERSE_EXPECTED_ROWS, json.dumps(mapping_counts, sort_keys=True)),
        ("record_provenance", provenance_complete, f"{len(raw_record_rows)} evidence records checked"),
        ("raw_record_identity", len({row['raw_record_id'] for row in raw_record_rows}) == len(raw_record_rows), "no duplicate raw_record_id"),
        ("deterministic_csv_regeneration", file_inventory_payload == deterministic_csv_bytes(inventory_rows, FILE_INVENTORY_FIELDS) and raw_record_payload == deterministic_csv_bytes(raw_record_rows, RAW_RECORD_FIELDS) and coverage_payload == deterministic_csv_bytes(coverage_rows, COVERAGE_FIELDS), "byte-identical in-memory regeneration"),
        ("deterministic_parquet_regeneration", deterministic_parquet, f"{len(raw_snapshot_paths)} raw Parquet files regenerated byte-identically"),
        ("no_normalized_features", True, "no normalized feature artifact created"),
        ("no_component_or_profiles", True, "no component or profile artifact created"),
        ("no_ranking_or_interpretation", True, "no ranking, score, recommendation, or interpretation output"),
    ]
    if not all(passed for _, passed, _ in qc_checks):
        failed = [name for name, passed, _ in qc_checks if not passed]
        raise SnapshotError(f"Snapshot QC failed: {failed}")

    identity_payload = {
        "access_mode": ACCESS_MODE,
        "authorization_id": AUTHORIZATION_ID,
        "component_id": COMPONENT_ID,
        "component_version": COMPONENT_VERSION,
        "coverage_ledger_sha256": coverage_sha,
        "disease_context_id": DISEASE_CONTEXT_ID,
        "disease_mapping_rule_version": DISEASE_MAPPING_RULE_VERSION,
        "file_inventory_sha256": file_inventory_sha,
        "frozen_input_sha256": frozen_before,
        "license_artifact_sha256": release_manifest["license_artifact_sha256"],
        "mapping_rule_version": MAPPING_RULE_VERSION,
        "query_scope_version": QUERY_SCOPE_VERSION,
        "raw_record_manifest_sha256": raw_record_manifest_sha,
        "release_manifest_sha256": release_manifest_sha,
        "retrieval_implementation_sha256": file_hash(Path(__file__).resolve()),
        "retrieval_implementation_version": SCRIPT_VERSION,
        "snapshot_schema_version": SNAPSHOT_SCHEMA_VERSION,
        "source_id": SOURCE_ID,
        "source_version": SOURCE_VERSION,
        "universe_id": UNIVERSE_ID,
        "universe_sha256": UNIVERSE_SHA256,
    }
    identity_sha = hashlib.sha256(canonical_json_bytes(identity_payload)).hexdigest()
    snapshot_version = f"DA_OT_26_06_MONDO_0005061_SHA256_{identity_sha[:16]}"
    snapshot_manifest = {
        "authorization_status_at_retrieval": AUTHORIZATION_STATUS,
        "completeness_status": "COMPLETE",
        "determinism": {
            "manifest_identity_sha256": identity_sha,
            "randomness": "PROHIBITED_NOT_USED",
            "runtime_ai": "PROHIBITED_NOT_USED",
            "wall_clock_in_identity": "PROHIBITED_NOT_USED",
        },
        "identity_payload": identity_payload,
        "output_artifacts": {
            "entity_coverage_ledger": {
                "path": "entity_coverage_ledger.csv",
                "sha256": coverage_sha,
            },
            "file_inventory": {
                "path": "file_inventory.csv",
                "sha256": file_inventory_sha,
            },
            "raw_record_manifest": {
                "path": "raw_record_manifest.csv",
                "sha256": raw_record_manifest_sha,
            },
            "release_manifest": {
                "path": "release_manifest.json",
                "sha256": release_manifest_sha,
            },
        },
        "retrieval_provenance": {
            "batching_rule": "ONE_OFFICIAL_PARQUET_PART_PER_RETRIEVAL_UNIT",
            "bulk_artifact_identity": f"{SOURCE_ID}_{SOURCE_VERSION}_OFFICIAL_RELEASE",
            "canonical_selection_rule": "retain source-native rows where diseaseId == MONDO_0005061 and targetId is in the version-stripped Task030 EnsemblID universe; retain the exact disease entity row and exact target entity rows",
            "failed_source_parts": 0,
            "filters": {
                "disease": "id == MONDO_0005061",
                "evidence": "diseaseId == MONDO_0005061 AND targetId IN UNIV_TASK030_ENSEMBL_29606_V0_1",
                "target": "id IN UNIV_TASK030_ENSEMBL_29606_V0_1",
            },
            "http_status_summary": {
                "control_and_inventory_requests": "200_OK",
                "source_byte_range_requests": "206_PARTIAL_CONTENT",
            },
            "network_hosts_contacted": [
                "open-targets-public-data-releases.s3.amazonaws.com",
                "platform-docs.opentargets.org",
            ],
            "omitted_authorized_source_parts": 0,
            "ordering_rule": "source dataset, source file path, source row group, source row index",
            "pagination": "NOT_APPLICABLE_BULK_RELEASE_ARTIFACTS",
            "raw_packaging": "LOSSLESS_LOGICAL_PARQUET_REPACKAGING_PER_SOURCE_PART_WITH_ALL_SOURCE_NATIVE_FIELDS_AND_SOURCE_ORDER_PRESERVED",
            "requested_fields": "ALL_SOURCE_NATIVE_FIELDS",
            "retrieval_completed_at_utc": retrieval_completed_at_utc,
            "retrieval_implementation_sha256": file_hash(Path(__file__).resolve()),
            "retrieval_implementation_version": SCRIPT_VERSION,
            "retrieval_started_at_utc": retrieval_started_at_utc,
            "retry_rule": "maximum four attempts per disjoint HTTPS byte range; every attempt and retry recorded in file_inventory.csv",
            "unresolved_source_parts": 0,
        },
        "snapshot_id": "SNAP_DA_OT_26_06_LUAD_EXACT_UNIV_TASK030_V0_1",
        "source_snapshot_version": snapshot_version,
    }
    snapshot_manifest_payload = pretty_json_bytes(snapshot_manifest)
    snapshot_manifest_sha = write_bytes_checked(
        output_root / "snapshot_manifest.json", snapshot_manifest_payload
    )
    if snapshot_manifest_payload != pretty_json_bytes(snapshot_manifest):
        raise SnapshotError("Snapshot manifest regeneration is not deterministic")

    summary = build_summary(
        snapshot_version=snapshot_version,
        release_date=croissant["datePublished"],
        evidence_dataset_count=len(evidence_datasets),
        source_parquet_count=len(source_parquet_rows),
        source_bytes=sum(int(row["file_size_bytes"]) for row in source_parquet_rows),
        raw_parquet_count=len(raw_snapshot_paths),
        raw_bytes=sum(path.stat().st_size for path in raw_snapshot_paths),
        raw_record_count=len(raw_record_rows),
        mapping_counts=mapping_counts,
        outside_universe_count=outside_universe_count,
        qc_checks=qc_checks,
    )
    summary_sha = write_bytes_checked(
        output_root / "snapshot_qc_report.md", summary.encode("utf-8")
    )

    session_lines = [
        "Task: #032B-2C Disease Association Snapshot Retrieval",
        f"Script version: {SCRIPT_VERSION}",
        f"Script SHA256: {file_hash(Path(__file__).resolve())}",
        f"Run completed (provenance only; excluded from snapshot identity): {dt.datetime.now(dt.timezone.utc).isoformat()}",
        f"Command: {' '.join(sys.argv)}",
        f"Python: {sys.version.replace(chr(10), ' ')}",
        f"Python executable: {sys.executable}",
        f"pyarrow: {pa.__version__}",
        f"Platform: {platform.platform()}",
        f"Source: {SOURCE_ID}",
        f"Source version: {SOURCE_VERSION}",
        f"Access mode: {ACCESS_MODE}",
        f"Network hosts contacted: {', '.join(sorted(ALLOWED_NETWORK_HOSTS))}",
        "Live API used: FALSE",
        "Package installation: NONE",
        f"Source snapshot version: {snapshot_version}",
        f"Snapshot manifest SHA256: {snapshot_manifest_sha}",
        f"Release manifest SHA256: {release_manifest_sha}",
        f"File inventory SHA256: {file_inventory_sha}",
        f"Raw record manifest SHA256: {raw_record_manifest_sha}",
        f"Coverage ledger SHA256: {coverage_sha}",
        f"QC report SHA256: {summary_sha}",
        "Normalized features generated: FALSE",
        "Evidence component generated: FALSE",
        "Profiles generated: FALSE",
        "Scoring/ranking/interpretation performed: FALSE",
    ]
    write_bytes_checked(
        output_root / "session_info.txt", ("\n".join(session_lines) + "\n").encode("utf-8")
    )

    frozen_after = verify_frozen_inputs(repo)
    if frozen_after != frozen_before:
        raise SnapshotError("Frozen input hashes changed during retrieval")

    print(f"Snapshot complete: {snapshot_version}")
    print(f"Evidence records: {len(raw_record_rows):,}")
    print(f"Coverage rows: {len(coverage_rows):,}")
    print(f"Snapshot manifest SHA256: {snapshot_manifest_sha}")
    print("QC: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SnapshotError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
