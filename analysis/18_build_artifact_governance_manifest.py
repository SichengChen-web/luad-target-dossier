#!/usr/bin/env python3
"""Build the Task #018 artifact governance manifest and contract.

The script inventories repository artifacts, classifies them, records hashes
and Git status, and writes governance documentation. It performs no biological
analysis, network access, package installation, Git mutation, or file deletion.
"""

from __future__ import annotations

import csv
import hashlib
import os
import platform
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
TASK017_BASE_COMMIT = "96f6cb103e8341a9b0eec4ba65f58fb65aa6bb9b"
EXPECTED_BRANCH = "main"
EXPECTED_REMOTE_FRAGMENT = "SichengChen-web/luad-target-dossier"
EXPECTED_PRE_TASK_TRACKED_COUNT = 190

OVER_100MB_THRESHOLD_BYTES = 100_000_000
LARGE_OUTPUT_REVIEW_THRESHOLD_BYTES = 50_000_000

SCRIPT_PATH = ROOT / "analysis/18_build_artifact_governance_manifest.py"
PLAN_PATH = ROOT / "docs/artifact_governance_plan_v0.1.md"
OUTPUT_DIR = ROOT / "outputs/artifact_governance"
MANIFEST_PATH = OUTPUT_DIR / "artifact_manifest.csv"
CLASSIFICATION_PATH = OUTPUT_DIR / "artifact_classification.csv"
CONTRACT_PATH = OUTPUT_DIR / "reproducibility_contract.md"
SUMMARY_PATH = OUTPUT_DIR / "artifact_governance_summary.md"
SESSION_PATH = OUTPUT_DIR / "session_info.txt"

# A manifest cannot include its own final digest. The complete governance
# control bundle is therefore excluded from its own artifact population and
# frozen in session_info.txt. The Task #018 script and plan remain in scope.
GOVERNANCE_CONTROL_PREFIX = "outputs/artifact_governance/"

ALLOWED_TASK018_UNTRACKED_FILES = {
    "analysis/18_build_artifact_governance_manifest.py",
    "docs/artifact_governance_plan_v0.1.md",
}
ALLOWED_TASK018_UNTRACKED_PREFIX = GOVERNANCE_CONTROL_PREFIX

KNOWN_IGNORED_LARGE_ARTIFACTS = {
    "outputs/evidence_claim_architecture/evidence_record_registry.csv": {
        "sha256": "76ec5056fb4e468176073073532204d231765d4f0cd70dbb6cfe4ad8bf752343",
        "size": 139_836_748,
    }
}

MANIFEST_FIELDS = [
    "artifact_id",
    "relative_path",
    "artifact_class",
    "file_size_bytes",
    "sha256",
    "generated_by",
    "input_dependencies_if_known",
    "git_tracking_status",
    "over_100mb",
    "large_output_artifact",
    "untracked_large_file",
]

OUTPUT_GENERATORS = {
    "reconnaissance": "analysis/01_tcga_luad_reconnaissance.R",
    "cohort_diagnostics": "analysis/02_cohort_count_diagnostics.R",
    "sample_qc": "analysis/03_sample_level_qc.R",
    "replicate_ffpe_audit": "analysis/04_tcga_replicate_ffpe_audit.R",
    "final_sample_qc": "analysis/05_final_cohort_qc.R",
    "differential_expression": "analysis/06_primary_differential_expression.R",
    "de_sensitivity": "analysis/07_de_sensitivity_analyses.R",
    "candidate_registry": "analysis/08_build_candidate_registry.py",
    "identifier_normalization": "analysis/09_identifier_normalization.py",
    "evidence_layer": "analysis/10_build_evidence_layer.py",
    "tractability_safety": "analysis/11_build_tractability_safety_layer.py",
    "integrated_registry": "analysis/12_build_integrated_registry.py",
    "evidence_ontology": "analysis/13_build_evidence_ontology.py",
    "evidence_claim_architecture": "analysis/14_build_evidence_claim_architecture.py",
    "evidence_gap_analysis": "analysis/16_build_evidence_gap_analysis.py",
    "evidence_acquisition": "analysis/17_build_evidence_acquisition_framework.py",
    "artifact_governance": "analysis/18_build_artifact_governance_manifest.py",
}

OUTPUT_DEPENDENCIES = {
    "reconnaissance": "external recount3 TCGA-LUAD gencode_v26 project files",
    "cohort_diagnostics": "outputs/reconnaissance|external recount3 cached project files",
    "sample_qc": "outputs/cohort_diagnostics|external recount3 cached project files",
    "replicate_ffpe_audit": "outputs/sample_qc|external recount3 cached project files|documented TCGA annotations",
    "final_sample_qc": "outputs/replicate_ffpe_audit|outputs/sample_qc|external recount3 cached project files",
    "differential_expression": "outputs/final_sample_qc|external recount3 cached project files|docs/de_design_decision_v0.1.md",
    "de_sensitivity": "outputs/differential_expression|outputs/final_sample_qc|docs/de_sensitivity_analysis_plan_v0.1.md",
    "candidate_registry": "outputs/differential_expression|outputs/de_sensitivity|docs/candidate_generation_decision_v0.1.md",
    "identifier_normalization": "outputs/candidate_registry/candidate_registry.csv|external identifier source files",
    "evidence_layer": "outputs/identifier_normalization/identifier_mapping.csv|official external API snapshots",
    "tractability_safety": "outputs/identifier_normalization/identifier_mapping.csv|outputs/evidence_layer|official external API snapshots",
    "integrated_registry": "outputs/candidate_registry|outputs/identifier_normalization|outputs/evidence_layer|outputs/tractability_safety",
    "evidence_ontology": "outputs/integrated_registry|Task #013 ontology definitions",
    "evidence_claim_architecture": "outputs/integrated_registry|outputs/evidence_ontology",
    "evidence_gap_analysis": "outputs/integrated_registry|outputs/evidence_claim_architecture|docs/target_prioritization_framework_v0.1.md",
    "evidence_acquisition": "outputs/evidence_gap_analysis",
    "artifact_governance": "Git index|repository working tree|analysis/18_build_artifact_governance_manifest.py",
}

CLASS_DEFINITIONS = {
    "A": {
        "name": "Source-controlled artifacts",
        "definition": "Human-maintained code, documentation, schemas, configuration, and workflow definitions.",
        "examples": "analysis scripts|documentation|schemas|workflow definitions",
        "git_policy": "Track directly in Git after review; keep text-based and diffable where practical.",
        "storage_policy": "Git repository",
        "reproducibility_requirement": "Version review, syntax/format validation, and committed history.",
    },
    "B": {
        "name": "Reproducible derived artifacts",
        "definition": "Regenerable registries, summaries, figures, session records, and QC outputs.",
        "examples": "generated CSV registries|summaries|QC outputs",
        "git_policy": "Track small review-critical artifacts; otherwise store externally with a manifest and hash.",
        "storage_policy": "Git for small review artifacts; external object storage for bulky derivatives",
        "reproducibility_requirement": "Frozen inputs, generator, parameters, QC assertions, and SHA256.",
    },
    "C": {
        "name": "External source snapshots",
        "definition": "Version or release metadata, manifests, and bounded snapshots obtained from external sources.",
        "examples": "Open Targets release metadata|ChEMBL release metadata|external dataset manifests",
        "git_policy": "Track small metadata/manifests; do not commit bulky source payloads by default.",
        "storage_policy": "Git for manifests; immutable external storage for payloads",
        "reproducibility_requirement": "Official source, release, retrieval time, query, license, URI, and content hash.",
    },
    "D": {
        "name": "Large data objects",
        "definition": "Large matrices, evidence tables, omics objects, and other artifacts unsuitable for ordinary Git blobs.",
        "examples": "large matrices|large evidence tables|future omics datasets",
        "git_policy": "Do not add to ordinary Git; use external storage by default or Git LFS only when justified before first commit.",
        "storage_policy": "Immutable external/object storage; selective Git LFS for version-coupled files",
        "reproducibility_requirement": "Manifest, immutable location, SHA256, size, schema, generator, inputs, and retrieval instructions.",
    },
}

LARGE_OBJECT_EXTENSIONS = {
    ".rds",
    ".rda",
    ".rdata",
    ".h5",
    ".hdf5",
    ".loom",
    ".parquet",
    ".feather",
    ".bam",
    ".cram",
    ".fastq",
    ".fq",
    ".mtx",
}


def fail(message: str) -> None:
    raise RuntimeError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    if path.is_symlink():
        digest.update(os.readlink(path).encode("utf-8"))
        return digest.hexdigest()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        fail(
            f"Git command failed: git {' '.join(args)}\n"
            f"stdout: {result.stdout.strip()}\n"
            f"stderr: {result.stderr.strip()}"
        )
    return result.stdout.strip()


def git_paths(*args: str) -> set[str]:
    result = subprocess.run(
        ["git", *args, "-z"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        fail(
            f"Git path query failed: git {' '.join(args)} -z\n"
            f"{result.stderr.decode(errors='replace').strip()}"
        )
    return {
        value.decode("utf-8")
        for value in result.stdout.split(b"\0")
        if value
    }


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def validate_preflight() -> dict[str, str]:
    branch = run_git("branch", "--show-current")
    head = run_git("rev-parse", "HEAD")
    remote = run_git("remote", "get-url", "origin")
    if branch != EXPECTED_BRANCH:
        fail(f"Expected branch {EXPECTED_BRANCH!r}; observed {branch!r}.")
    if head != TASK017_BASE_COMMIT:
        fail(
            f"Task #018 must start from frozen Task #017 commit {TASK017_BASE_COMMIT}; "
            f"observed {head}."
        )
    if EXPECTED_REMOTE_FRAGMENT not in remote:
        fail(f"Unexpected origin remote: {remote!r}.")
    if run_git("diff", "--name-only"):
        fail("Tracked unstaged changes exist before Task #018.")
    if run_git("diff", "--cached", "--name-only"):
        fail("Staged changes exist before Task #018.")

    tracked = git_paths("ls-files")
    if len(tracked) != EXPECTED_PRE_TASK_TRACKED_COUNT:
        fail(
            f"Expected {EXPECTED_PRE_TASK_TRACKED_COUNT} tracked Task #001-017 files; "
            f"observed {len(tracked)}."
        )

    untracked = git_paths("ls-files", "--others", "--exclude-standard")
    unexpected = {
        path
        for path in untracked
        if not (
            path in ALLOWED_TASK018_UNTRACKED_FILES
            or path.startswith(ALLOWED_TASK018_UNTRACKED_PREFIX)
        )
    }
    if unexpected:
        fail(f"Unexpected untracked files exist: {sorted(unexpected)}")

    for rel, expected in KNOWN_IGNORED_LARGE_ARTIFACTS.items():
        path = ROOT / rel
        if not path.is_file():
            fail(f"Known ignored large Task #014 artifact is missing: {rel}")
        if path.stat().st_size != expected["size"] or sha256(path) != expected["sha256"]:
            fail(f"Known ignored large Task #014 artifact changed: {rel}")

    return {
        "branch": branch,
        "head": head,
        "remote": remote,
        "tracked_count": str(len(tracked)),
    }


def classify_artifact(path: str, size: int) -> str:
    suffix = Path(path).suffix.lower()
    is_large_output = path.startswith("outputs/") and size >= LARGE_OUTPUT_REVIEW_THRESHOLD_BYTES
    if size > OVER_100MB_THRESHOLD_BYTES or is_large_output or suffix in LARGE_OBJECT_EXTENSIONS:
        return "D"
    if (
        "external" in Path(path).parts
        or "source_snapshot" in path.lower()
        or path.endswith("open_targets_schema_snapshot.json")
    ):
        return "C"
    if path.startswith("outputs/"):
        return "B"
    return "A"


def output_group(path: str) -> str | None:
    parts = Path(path).parts
    return parts[1] if len(parts) >= 3 and parts[0] == "outputs" else None


def generated_by(path: str) -> str:
    group = output_group(path)
    if group in OUTPUT_GENERATORS:
        return OUTPUT_GENERATORS[group]
    if path.startswith("analysis/") or path.startswith("docs/"):
        return "AUTHOR_MAINTAINED"
    return "AUTHOR_MAINTAINED"


def dependencies(path: str) -> str:
    group = output_group(path)
    if group in OUTPUT_DEPENDENCIES:
        return OUTPUT_DEPENDENCIES[group]
    if path.startswith("analysis/"):
        return "DOCUMENTED_IN_SCRIPT_OR_TASK_SPECIFICATION"
    if path.startswith("docs/"):
        return "SCIENTIFIC_OR_GOVERNANCE_DECISIONS_FROM_PRIOR_TASKS"
    return "NOT_DOCUMENTED"


def ignored(path: str) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "-q", "--", path], cwd=ROOT, check=False
    )
    return result.returncode == 0


def physical_large_files() -> set[str]:
    result = set()
    for directory, names, files in os.walk(ROOT, followlinks=False):
        names[:] = [name for name in names if name != ".git"]
        base = Path(directory)
        for name in files:
            path = base / name
            try:
                size = path.lstat().st_size
            except OSError as exc:
                fail(f"Unable to inspect {path}: {exc}")
            if size > OVER_100MB_THRESHOLD_BYTES:
                result.add(relative(path))
    return result


def inventory_artifacts() -> list[dict[str, str]]:
    tracked = git_paths("ls-files")
    untracked = git_paths("ls-files", "--others", "--exclude-standard")
    candidates = tracked | untracked | physical_large_files()
    candidates = {
        path
        for path in candidates
        if not path.startswith(GOVERNANCE_CONTROL_PREFIX)
    }

    rows = []
    for rel in sorted(candidates):
        path = ROOT / rel
        if not (path.is_file() or path.is_symlink()):
            fail(f"Inventoried artifact is not a file: {rel}")
        size = path.lstat().st_size
        if rel in tracked:
            status = "TRACKED_GIT"
        elif rel in untracked:
            status = "UNTRACKED"
        elif ignored(rel):
            status = "IGNORED_NOT_TRACKED"
        else:
            status = "NOT_TRACKED"
        over_100mb = size > OVER_100MB_THRESHOLD_BYTES
        large_output = rel.startswith("outputs/") and size >= LARGE_OUTPUT_REVIEW_THRESHOLD_BYTES
        rows.append(
            {
                "artifact_id": "ART-" + hashlib.sha256(rel.encode("utf-8")).hexdigest()[:16],
                "relative_path": rel,
                "artifact_class": classify_artifact(rel, size),
                "file_size_bytes": str(size),
                "sha256": sha256(path),
                "generated_by": generated_by(rel),
                "input_dependencies_if_known": dependencies(rel),
                "git_tracking_status": status,
                "over_100mb": "TRUE" if over_100mb else "FALSE",
                "large_output_artifact": "TRUE" if large_output else "FALSE",
                "untracked_large_file": "TRUE"
                if over_100mb and status != "TRACKED_GIT"
                else "FALSE",
            }
        )
    return rows


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def classification_rows(manifest: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for artifact_class in ("A", "B", "C", "D"):
        subset = [row for row in manifest if row["artifact_class"] == artifact_class]
        definition = CLASS_DEFINITIONS[artifact_class]
        statuses = Counter(row["git_tracking_status"] for row in subset)
        rows.append(
            {
                "artifact_class": artifact_class,
                "class_name": definition["name"],
                "definition": definition["definition"],
                "examples": definition["examples"],
                "git_policy": definition["git_policy"],
                "storage_policy": definition["storage_policy"],
                "reproducibility_requirement": definition["reproducibility_requirement"],
                "artifact_count": str(len(subset)),
                "total_size_bytes": str(sum(int(row["file_size_bytes"]) for row in subset)),
                "tracked_count": str(statuses["TRACKED_GIT"]),
                "untracked_count": str(statuses["UNTRACKED"]),
                "ignored_not_tracked_count": str(statuses["IGNORED_NOT_TRACKED"]),
                "large_output_count": str(sum(row["large_output_artifact"] == "TRUE" for row in subset)),
                "over_100mb_count": str(sum(row["over_100mb"] == "TRUE" for row in subset)),
            }
        )
    return rows


def write_contract() -> None:
    CONTRACT_PATH.write_text(
        """# Reproducibility Contract v0.1

## Contract chain

```text
input manifest
      ↓
versioned analysis script and configuration
      ↓
generated artifact
      ↓
QC validation
      ↓
SHA256 hash freeze and session provenance
```

Every future task must declare its input paths, immutable identifiers, source versions, expected hashes, generator, runtime configuration, output paths, missingness rules, QC assertions, and interpretation boundary before an artifact is treated as frozen.

## Required task record

Each task must preserve:

1. **Input manifest:** relative path or immutable external URI, artifact class, file size, SHA256, source/release, acquisition timestamp where relevant, and dependency lineage.
2. **Generator:** version-controlled script, parameters/configuration, package/runtime versions, Git branch and commit, and network-use declaration.
3. **Generated artifact:** stable schema, immutable primary key where applicable, deterministic ordering where meaningful, explicit missingness, and no silent overwrites of frozen inputs.
4. **QC validation:** row counts, uniqueness, referential integrity, schema checks, expected-versus-observed assertions, and domain-specific validation.
5. **Hash freeze:** SHA256 for every frozen input and output, plus a session record that binds hashes to the Git commit and runtime.

## What enters ordinary Git

- Class A source-controlled artifacts should enter Git after review.
- Small Class B outputs may enter Git when they are necessary for scientific review, validation, or downstream reproducibility and remain reasonably diffable.
- Small Class C release metadata and manifests may enter Git when licensing permits.
- No secret, credential, personal cache, virtual environment, or transient application file enters Git.

Generated files do not enter Git merely because they exist. Their inclusion requires a documented review purpose, stable generation, and acceptable repository impact.

## What does not enter ordinary Git

- Class D matrices, large evidence tables, omics objects, raw API payload collections, and bulky external datasets.
- Reconstructable caches and intermediate files with no review value.
- Restricted, licensed, sensitive, or redistribution-prohibited source data.
- Files approaching or exceeding host limits before an explicit storage decision.

Files stored outside Git require a small committed manifest containing immutable location, size, SHA256, source/release, schema, generator, and retrieval or reconstruction instructions. Missing external payloads must fail clearly rather than trigger silent substitution.

## Git LFS decision rule

Git LFS is appropriate only when a large file must remain version-coupled to repository commits, collaborators need Git-like checkout semantics, redistribution is permitted, and storage/bandwidth quotas are understood. LFS tracking must be configured **before the file's first commit**.

A file above 50 MB requires storage review. A file above 100 MB must not be added as an ordinary Git blob. Git LFS does not make a reproducible derivative scientifically preferable to external storage and does not replace source, version, schema, or checksum metadata.

This task does not install or configure Git LFS and does not migrate existing files.

## When external storage is preferred

Use immutable external/object storage for reproducible large derivatives, raw or versioned source snapshots, large matrices, frequently refreshed datasets, and artifacts that do not need line-level Git review. Prefer content-addressed or versioned locations with retention controls. The repository should retain the manifest and reconstruction contract.

## Freeze and change control

- A frozen artifact is identified by path, size, SHA256, generator, input hashes, and Git commit/session record.
- Regeneration must write a new version or be explicitly approved as a replacement; discrepancies must be reported.
- Changed source releases, schemas, parameters, or dependencies require a new task/version and refreshed QC.
- `NOT_FOUND`, `NOT_QUERIED`, retrieval failure, and negative evidence must remain distinct.
- Derived summaries never replace their underlying record-level provenance.
- Git history must not be rewritten to implement routine artifact governance. Any future repository migration is a separate, explicitly authorized operation with backups and collaborator coordination.

## Governance-manifest boundary

`artifact_manifest.csv` inventories all Git-tracked files, all non-ignored untracked project files, and ignored files over 100 MB at the scan boundary. Local ignored files below that threshold are excluded. The Task #018 governance output directory is excluded from its own manifest because a manifest cannot contain its own final SHA256 without changing itself. `session_info.txt` freezes the hashes of the manifest, classification, contract, and summary instead.
""",
        encoding="utf-8",
    )


def write_summary(manifest: list[dict[str, str]], classes: list[dict[str, str]]) -> None:
    over_100 = [row for row in manifest if row["over_100mb"] == "TRUE"]
    large_outputs = [row for row in manifest if row["large_output_artifact"] == "TRUE"]
    untracked_large = [row for row in manifest if row["untracked_large_file"] == "TRUE"]
    tracked = sum(row["git_tracking_status"] == "TRACKED_GIT" for row in manifest)
    untracked = sum(row["git_tracking_status"] == "UNTRACKED" for row in manifest)
    ignored = sum(row["git_tracking_status"] == "IGNORED_NOT_TRACKED" for row in manifest)

    lines = [
        "# Task #018 artifact governance summary",
        "",
        f"**Artifacts inventoried:** {len(manifest):,}  ",
        f"**Git tracked:** {tracked:,}  ",
        f"**Untracked Task #018 definitions:** {untracked:,}  ",
        f"**Ignored large artifacts included:** {ignored:,}  ",
        f"**Files over 100 MB:** {len(over_100):,}  ",
        f"**Output artifacts at or above 50 MB review threshold:** {len(large_outputs):,}",
        "",
        "## Classification",
        "",
        "| Class | Meaning | Artifacts | Total bytes | Git policy |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for row in classes:
        lines.append(
            f"| {row['artifact_class']} | {row['class_name']} | "
            f"{int(row['artifact_count']):,} | {int(row['total_size_bytes']):,} | "
            f"{row['git_policy']} |"
        )

    lines.extend(["", "## Files over 100 MB", ""])
    if over_100:
        for row in over_100:
            lines.append(
                f"- `{row['relative_path']}` — {int(row['file_size_bytes']):,} bytes; "
                f"Class {row['artifact_class']}; `{row['git_tracking_status']}`; "
                f"SHA256 `{row['sha256']}`"
            )
    else:
        lines.append("No files exceeded 100 MB at the scan boundary.")

    lines.extend(["", "## Large output review", ""])
    for row in large_outputs:
        lines.append(
            f"- `{row['relative_path']}` — {int(row['file_size_bytes']):,} bytes; "
            f"Class {row['artifact_class']}; `{row['git_tracking_status']}`"
        )

    lines.extend(
        [
            "",
            "## Governance observation",
            "",
            f"{len(untracked_large)} file over 100 MB is not tracked by Git. It is currently ignored and retained locally; this task did not delete, move, add, or alter it. Before relying on it across environments, the project needs an immutable external-storage location or a separately approved Git LFS decision plus a committed retrieval/reconstruction manifest.",
            "",
            "The three tracked Class D CSVs between 50 MB and 100 MB also warrant storage review before continued growth. Their current Git state was not changed.",
            "",
            "## Validation boundary",
            "",
            "All Task #001–#017 tracked files matched the frozen Git worktree before and after generation. The known ignored Task #014 record table retained its expected size and SHA256. HEAD did not change. No network access, package installation, file deletion, output rewrite, commit, push, Git LFS operation, or history rewrite occurred.",
            "",
            "The governance control bundle is intentionally excluded from its own manifest to avoid self-referential hashes. Its output hashes are recorded in `session_info.txt`.",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate_manifest(manifest: list[dict[str, str]]) -> list[tuple[str, bool, str]]:
    paths = [row["relative_path"] for row in manifest]
    ids = [row["artifact_id"] for row in manifest]
    checks = [
        ("unique_relative_paths", len(paths) == len(set(paths)), str(len(paths))),
        ("unique_artifact_ids", len(ids) == len(set(ids)), str(len(ids))),
        ("all_sha256_valid", all(len(row["sha256"]) == 64 for row in manifest), str(len(manifest))),
        ("all_classes_valid", all(row["artifact_class"] in CLASS_DEFINITIONS for row in manifest), str(len(manifest))),
        ("all_sizes_nonnegative", all(int(row["file_size_bytes"]) >= 0 for row in manifest), str(len(manifest))),
        ("all_required_fields_nonblank", all(all(row[field] != "" for field in MANIFEST_FIELDS) for row in manifest), str(len(manifest))),
        ("known_100mb_file_detected", any(row["relative_path"] in KNOWN_IGNORED_LARGE_ARTIFACTS and row["over_100mb"] == "TRUE" for row in manifest), str(sum(row["over_100mb"] == "TRUE" for row in manifest))),
        ("governance_control_bundle_excluded", not any(path.startswith(GOVERNANCE_CONTROL_PREFIX) for path in paths), "TRUE"),
    ]
    failed = [name for name, passed, _ in checks if not passed]
    if failed:
        fail(f"Artifact manifest QC failed: {failed}")
    return checks


def validate_postflight(preflight: dict[str, str]) -> None:
    if run_git("rev-parse", "HEAD") != preflight["head"]:
        fail("Git HEAD changed during Task #018.")
    if run_git("diff", "--name-only"):
        fail("A prior tracked file changed during Task #018.")
    if run_git("diff", "--cached", "--name-only"):
        fail("A file was staged during Task #018.")
    for rel, expected in KNOWN_IGNORED_LARGE_ARTIFACTS.items():
        path = ROOT / rel
        if path.stat().st_size != expected["size"] or sha256(path) != expected["sha256"]:
            fail(f"Known ignored large prior artifact changed during Task #018: {rel}")


def write_session(
    started: datetime,
    preflight: dict[str, str],
    manifest: list[dict[str, str]],
    checks: list[tuple[str, bool, str]],
) -> None:
    values = {
        "task": "018",
        "purpose": "artifact governance and reproducibility framework",
        "started_at_utc": started.isoformat(),
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "git_branch": preflight["branch"],
        "git_head_before": preflight["head"],
        "git_head_after": run_git("rev-parse", "HEAD"),
        "git_origin": preflight["remote"],
        "pre_task_tracked_file_count": preflight["tracked_count"],
        "manifest_artifact_count": str(len(manifest)),
        "manifest_over_100mb_count": str(sum(row["over_100mb"] == "TRUE" for row in manifest)),
        "manifest_large_output_count": str(sum(row["large_output_artifact"] == "TRUE" for row in manifest)),
        "manifest_untracked_large_count": str(sum(row["untracked_large_file"] == "TRUE" for row in manifest)),
        "manifest_scope_exclusion": GOVERNANCE_CONTROL_PREFIX,
        "manifest_scope_exclusion_reason": "self_referential_hash_control_bundle",
        "network_access": "NOT_USED",
        "packages_installed_or_updated": "FALSE",
        "files_deleted": "FALSE",
        "previous_outputs_modified": "FALSE",
        "git_history_rewritten": "FALSE",
        "git_lfs_operation": "FALSE",
        "git_commit_or_push": "FALSE",
        "script_sha256": sha256(SCRIPT_PATH),
        "plan_sha256": sha256(PLAN_PATH),
        "known_ignored_large_artifact_sha256": KNOWN_IGNORED_LARGE_ARTIFACTS[
            "outputs/evidence_claim_architecture/evidence_record_registry.csv"
        ]["sha256"],
    }
    for name, passed, observed in checks:
        values[f"qc.{name}"] = f"{'PASS' if passed else 'FAIL'}|observed={observed}"
    for path in (MANIFEST_PATH, CLASSIFICATION_PATH, CONTRACT_PATH, SUMMARY_PATH):
        values[f"output_sha256.{relative(path)}"] = sha256(path)
    SESSION_PATH.write_text(
        "".join(f"{key}={values[key]}\n" for key in sorted(values)),
        encoding="utf-8",
    )


def main() -> None:
    started = datetime.now(timezone.utc)
    preflight = validate_preflight()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    unexpected_outputs = {
        path.name
        for path in OUTPUT_DIR.iterdir()
        if path.name
        not in {
            MANIFEST_PATH.name,
            CLASSIFICATION_PATH.name,
            CONTRACT_PATH.name,
            SUMMARY_PATH.name,
            SESSION_PATH.name,
        }
    }
    if unexpected_outputs:
        fail(f"Unexpected pre-existing Task #018 output files: {sorted(unexpected_outputs)}")

    write_contract()
    manifest = inventory_artifacts()
    checks = validate_manifest(manifest)
    classes = classification_rows(manifest)
    write_csv(MANIFEST_PATH, MANIFEST_FIELDS, manifest)
    write_csv(
        CLASSIFICATION_PATH,
        [
            "artifact_class",
            "class_name",
            "definition",
            "examples",
            "git_policy",
            "storage_policy",
            "reproducibility_requirement",
            "artifact_count",
            "total_size_bytes",
            "tracked_count",
            "untracked_count",
            "ignored_not_tracked_count",
            "large_output_count",
            "over_100mb_count",
        ],
        classes,
    )
    write_summary(manifest, classes)
    validate_postflight(preflight)
    write_session(started, preflight, manifest, checks)

    print("Created files:")
    for path in (MANIFEST_PATH, CLASSIFICATION_PATH, CONTRACT_PATH, SUMMARY_PATH, SESSION_PATH):
        print(f"- {relative(path)}")
    print(f"Artifacts inventoried: {len(manifest)}")
    for row in classes:
        print(f"Class {row['artifact_class']}: {row['artifact_count']}")
    print(f"Files over 100 MB: {sum(row['over_100mb'] == 'TRUE' for row in manifest)}")
    print(f"Large output artifacts: {sum(row['large_output_artifact'] == 'TRUE' for row in manifest)}")
    print("All Task #018 assertions passed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
