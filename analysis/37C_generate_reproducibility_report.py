#!/usr/bin/env python3
"""Generate the governed Reproducibility Report v0.1.

Task #037C reads frozen manifests, validation reports, and the artifact registry
only. It does not create a release package, rerun science, rebuild components,
regenerate scientific representations, access a network/API, retrieve data,
interpret biology, score or rank targets, recommend targets, or use runtime AI.
"""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "docs/reproducibility_report_v0.1.md"
OUTPUT_DIR = ROOT / "outputs/reproducibility_report_v0.1"
MANIFEST_PATH = OUTPUT_DIR / "reproducibility_report_manifest.json"
VALIDATION_PATH = OUTPUT_DIR / "validation_report.md"
SESSION_PATH = OUTPUT_DIR / "session_info.txt"

TASK_ID = "TASK_037C"
PROJECT_ID = "LUAD_EXPRESSION_DRUGGABLE_TARGET_EVIDENCE_DOSSIER"
PROJECT_NAME = "LUAD Expression → Druggable-Target Evidence Dossier"
REPORT_VERSION = "REPRODUCIBILITY_REPORT_V0.1"
GENERATOR_VERSION = "REPRODUCIBILITY_REPORT_GENERATOR_V0.1"

REGISTRY_COLUMNS = [
    "artifact_id",
    "relative_path",
    "artifact_type",
    "artifact_scope",
    "artifact_version",
    "generating_task",
    "lifecycle_state",
    "validation_status",
    "sha256",
    "size_bytes",
    "storage_class",
    "storage_reference",
    "provenance_reference",
    "dependency_reference",
]

FROZEN_INPUT_SHA256 = {
    "docs/governance/release_package_specification_v0.1.md": "39125ef1d550597ae9bb7af97b1fc81e7eee7d37cc8e54149276db8c2f3fe0ad",
    "docs/governance/release_scope_policy_v0.1.md": "ce47a9c5b3b111d8230c38e92e3012e6e4e8f81adcd47318e49ebcb3326959a3",
    "docs/governance/release_validation_requirements_v0.1.md": "104013b5ff9eeedd55b78a2f015b0f220a3ac1f5cc1bb2d464f8b16df158a1f1",
    "docs/governance/artifact_registry_policy_v0.1.md": "a7051623e88b219af476c4c775fca540163198a85cb5cfbaf40e7948333d7ae7",
    "schemas/artifact_registry_schema_v0.1.json": "62108eb4b3d27f881370898f019511145b55d85e8b6e4b36a99e2b3178c9f0ae",
    "outputs/artifact_registry_v0.1/artifact_registry.csv": "06b0e6ff4ddbc751136edeeb0e60799d81328692968b2f43a25d2dc021750e57",
    "outputs/artifact_registry_v0.1/artifact_registry_manifest.json": "d7bbca889f78bbef55ecae59881a6b9ec34147762e6cd26b17810304dcedde2c",
    "outputs/artifact_registry_v0.1/validation_report.md": "afa4d470045e6349285cea63f44abe37b10e4b1bfe9c8c951c12e7cedf78930a",
    "outputs/artifact_registry_v0.1/session_info.txt": "c070e113c66ba827990bc5eb03308fe29d83b60ad2d5da9615fe13265ad4a641",
}

LAYER_MANIFEST_PATHS = {
    "landscape": "outputs/evidence_landscape_v0.2/landscape_manifest.json",
    "summary": "outputs/evidence_summary_v0.1/summary_manifest.json",
    "routing": "outputs/prioritization_v0.1/prioritization_manifest.json",
    "dossier": "outputs/case_dossiers_v0.1/dossier_manifest.json",
    "presentation": "outputs/presentation_artifacts_v0.1/presentation_manifest.json",
    "release_governance": "outputs/release_governance_v0.1/release_schema_manifest.json",
}

ALLOWED_WORKTREE_PATHS = {
    "analysis/37C_generate_reproducibility_report.py",
    "docs/reproducibility_report_v0.1.md",
    "outputs/reproducibility_report_v0.1/reproducibility_report_manifest.json",
    "outputs/reproducibility_report_v0.1/validation_report.md",
    "outputs/reproducibility_report_v0.1/session_info.txt",
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
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("utf-8")


def stable_id(prefix: str, value: Any, length: int = 32) -> str:
    digest = sha256_bytes(canonical_json(value).encode("utf-8"))
    return f"{prefix}_{digest[:length].upper()}"


def validate_working_tree_scope() -> None:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    unexpected: list[str] = []
    for line in result.stdout.splitlines():
        if not line:
            continue
        path_text = line[3:]
        if " -> " in path_text:
            path_text = path_text.split(" -> ", 1)[1]
        if path_text not in ALLOWED_WORKTREE_PATHS:
            unexpected.append(line)
    if unexpected:
        fail("Unexpected working-tree changes:\n" + "\n".join(unexpected))


def validate_output_scope() -> None:
    allowed = {MANIFEST_PATH, VALIDATION_PATH, SESSION_PATH}
    if OUTPUT_DIR.exists():
        unexpected = sorted(
            path.relative_to(ROOT).as_posix()
            for path in OUTPUT_DIR.rglob("*")
            if path.is_file() and path not in allowed
        )
        if unexpected:
            fail("Unexpected Task #037C output files: " + ", ".join(unexpected))


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


def load_and_validate_registry() -> tuple[
    dict[str, Any], list[dict[str, str]], dict[str, dict[str, str]], dict[str, int]
]:
    manifest_path = ROOT / "outputs/artifact_registry_v0.1/artifact_registry_manifest.json"
    registry_path = ROOT / "outputs/artifact_registry_v0.1/artifact_registry.csv"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("validation_status") != "PASS":
        fail("Frozen Artifact Registry is not validated")
    if manifest.get("registry_version") != "ARTIFACT_REGISTRY_V0.1":
        fail("Frozen Artifact Registry version changed")
    registry_meta = manifest.get("registry_artifact", {})
    if (
        registry_meta.get("sha256") != sha256_file(registry_path)
        or registry_meta.get("size_bytes") != registry_path.stat().st_size
    ):
        fail("Artifact Registry manifest does not match registry CSV bytes")

    with registry_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != REGISTRY_COLUMNS:
            fail("Artifact Registry columns changed")
        rows = list(reader)
    if len(rows) != manifest.get("counts", {}).get("records"):
        fail("Artifact Registry row count changed")
    ids = [row["artifact_id"] for row in rows]
    paths = [row["relative_path"] for row in rows]
    if len(ids) != len(set(ids)) or len(paths) != len(set(paths)):
        fail("Artifact Registry identifiers or paths are not unique")

    by_path = {row["relative_path"]: row for row in rows}
    git_rows = 0
    external_rows = 0
    for row in rows:
        if row["storage_class"] == "GIT_MANAGED":
            git_rows += 1
            path = ROOT / row["relative_path"]
            if not path.is_file() or path.is_symlink():
                fail(f"Registered Git artifact is missing or unsafe: {row['relative_path']}")
            if path.stat().st_size != int(row["size_bytes"]) or sha256_file(path) != row["sha256"]:
                fail(f"Registered Git artifact bytes changed: {row['relative_path']}")
        elif row["storage_class"] == "EXTERNAL_IMMUTABLE":
            external_rows += 1
            if not row["relative_path"].startswith("EXTERNAL::"):
                fail("External Artifact Registry row lacks logical locator")
        else:
            fail(f"Uncontrolled storage class: {row['storage_class']}")
    expected_storage = manifest.get("counts", {}).get("by_storage_class", {})
    if git_rows != expected_storage.get("GIT_MANAGED") or external_rows != expected_storage.get(
        "EXTERNAL_IMMUTABLE"
    ):
        fail("Artifact Registry storage counts changed")
    return manifest, rows, by_path, {"git_rows": git_rows, "external_rows": external_rows}


def load_and_reconcile_manifests(
    registry_by_path: dict[str, dict[str, str]]
) -> dict[str, dict[str, Any]]:
    manifests: dict[str, dict[str, Any]] = {}
    for name, relative_path in LAYER_MANIFEST_PATHS.items():
        row = registry_by_path.get(relative_path)
        if row is None:
            fail(f"Required layer manifest is absent from Artifact Registry: {relative_path}")
        path = ROOT / relative_path
        if row["sha256"] != sha256_file(path):
            fail(f"Layer manifest differs from Artifact Registry: {relative_path}")
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get("validation_status") != "PASS":
            fail(f"Layer manifest is not validated: {name}")
        manifests[name] = value

    landscape = manifests["landscape"]
    summary = manifests["summary"]
    routing = manifests["routing"]
    dossier = manifests["dossier"]
    presentation = manifests["presentation"]
    if not (
        landscape.get("counts", {}).get("landscapes")
        == summary.get("counts", {}).get("summaries")
        == routing.get("counts", {}).get("representations")
        == presentation.get("counts", {}).get("canonical_entities")
        == 29_606
    ):
        fail("Canonical entity counts do not reconcile across layers")
    if landscape.get("component_versions") != summary.get("component_versions"):
        fail("Component versions changed between landscape and Evidence Summary")
    if landscape.get("component_versions") != routing.get("component_versions"):
        fail("Component versions changed between landscape and routing representation")
    if summary.get("source_landscape", {}).get("manifest_sha256") != sha256_file(
        ROOT / LAYER_MANIFEST_PATHS["landscape"]
    ):
        fail("Landscape-to-summary provenance changed")
    if dossier.get("source", {}).get("prioritization_release_id") != routing.get("release_id"):
        fail("Routing-to-dossier provenance changed")
    if presentation.get("source_releases") != {
        "landscape_release_id": landscape.get("release_id"),
        "evidence_summary_release_id": summary.get("release_id"),
        "prioritization_release_id": routing.get("release_id"),
        "case_dossier_release_id": dossier.get("release_id"),
    }:
        fail("Presentation source-release provenance changed")
    if manifests["release_governance"].get("schema_version") != "RELEASE_MANIFEST_SCHEMA_V0.1":
        fail("Release governance schema version changed")
    return manifests


def external_payload_table(rows: list[dict[str, str]]) -> tuple[list[str], int]:
    external = sorted(
        (row for row in rows if row["storage_class"] == "EXTERNAL_IMMUTABLE"),
        key=lambda row: row["artifact_id"],
    )
    lines = [
        f"| `{row['artifact_id']}` | {int(row['size_bytes']):,} | `{row['sha256']}` | `{row['storage_reference']}` |"
        for row in external
    ]
    return lines, sum(int(row["size_bytes"]) for row in external)


def build_report(
    registry_manifest: dict[str, Any],
    registry_rows: list[dict[str, str]],
    manifests: dict[str, dict[str, Any]],
) -> bytes:
    landscape = manifests["landscape"]
    summary = manifests["summary"]
    routing = manifests["routing"]
    dossier = manifests["dossier"]
    presentation = manifests["presentation"]
    release_governance = manifests["release_governance"]
    external_lines, external_total = external_payload_table(registry_rows)
    registry_counts = registry_manifest["counts"]
    text = f"""# Reproducibility Report v0.1

**Project:** {PROJECT_NAME}  
**Report version:** `{REPORT_VERSION}`  
**Release context:** Pre-release reproducibility and governance record; no release package generated  
**Artifact registry:** `{registry_manifest['registry_id']}` (`{registry_manifest['registry_version']}`)

## 1. Project identity and purpose

This project represents evidence structure and provenance. Its computational framework organizes frozen evidence observations, missingness states, dependencies, limitations, deterministic structural routing, and presentation-oriented case patterns.

It does not establish:

- biological validation;
- therapeutic value;
- clinical utility;
- target recommendation.

The release context is governed by [Release Package Specification v0.1](governance/release_package_specification_v0.1.md), [Release Scope Policy v0.1](governance/release_scope_policy_v0.1.md), and [Release Validation Requirements v0.1](governance/release_validation_requirements_v0.1.md). Task #037C documents reproducibility only; it does not create, freeze, or release a package.

## 2. Computational lifecycle

```text
Input data
  -> Evidence components
  -> Evidence landscape
  -> Evidence summary
  -> Structural routing
  -> Case dossiers
  -> Communication artifacts
```

### 2.1 Input data

Earlier governed tasks froze the source observations that feed the profile architecture: transcriptomic features derived from the governed LUAD expression workflow and a pinned disease-association evidence snapshot. Task #037C does not reopen, retrieve, normalize, or reinterpret those source records.

The multi-component source profile records evidence snapshot `{landscape['source_profile']['evidence_snapshot_version']}` and integration release `{landscape['source_profile']['integration_release_id']}`.

### 2.2 Evidence components

Each of the 29,606 immutable EnsemblID entities has two separately represented component slots:

- `{landscape['component_versions']['COMP_TRANSCRIPTOMIC_EVIDENCE']}`;
- `{landscape['component_versions']['COMP_DISEASE_ASSOCIATION']}`.

Component states describe structural evidence conditions. They are not combined into a global assessment.

### 2.3 Evidence landscape

Release `{landscape['release_id']}` contains 29,606 structural landscapes and preserves {landscape['counts']['provenance_references']:,} provenance relationships plus {landscape['counts']['dependency_relationships']:,} dependency relationships. The landscape represents feature availability, missingness, provenance, dependencies, and limitations without target evaluation.

### 2.4 Evidence Summary

Release `{summary['release_id']}` contains {summary['counts']['summaries']:,} summaries. It preserves the two component versions, {summary['counts']['feature_missingness_references']:,} feature-missingness references, and {summary['counts']['dependency_relationships']:,} dependency relationships from the landscape projection.

### 2.5 Structural routing

Release `{routing['release_id']}` contains {routing['counts']['representations']:,} transparent routing representations and {routing['counts']['rule_trace_steps']:,} fixed-order rule-trace steps. Routing categories are non-ordinal structural categories. They are not priorities.

### 2.6 Case dossiers

Release `{dossier['release_id']}` contains {dossier['counts']['filled_case_slots']} filled representative structural case slots. Each was selected from a complete eligible pool by the frozen category-salted SHA256 minimum rule. Selection is a reproducible presentation mechanism, not target selection.

### 2.7 Communication artifacts

Release `{presentation['presentation_release_id']}` contains governed architecture, evidence-layer, case-pattern, and provenance-flow summaries. These artifacts communicate existing representations without adding literature, biological claims, or therapeutic conclusions.

## 3. Artifact governance

The [Artifact Registry v0.1](../outputs/artifact_registry_v0.1/artifact_registry.csv) contains {registry_counts['records']} records:

- {registry_counts['by_artifact_scope']['SCIENTIFIC']} scientific-scope computational artifacts;
- {registry_counts['by_artifact_scope']['GOVERNANCE']} governance artifacts;
- {registry_counts['by_artifact_scope']['COMMUNICATION']} communication artifacts;
- {registry_counts['by_storage_class']['GIT_MANAGED']} Git-managed file records;
- {registry_counts['by_storage_class']['EXTERNAL_IMMUTABLE']} external immutable payload references.

The registry is governed by [Artifact Registry Policy v0.1](governance/artifact_registry_policy_v0.1.md). Each row preserves an immutable artifact ID, path or logical external locator, artifact and schema versions, generating task, lifecycle state, validation disposition, SHA256, byte size, storage reference, provenance reference, and dependency reference.

All registered artifacts are currently recorded as `VALIDATED`; none is promoted by this report to `FROZEN` or `RELEASED`.

### 3.1 Git-managed artifacts

Git-managed records point to repository-relative files. Reproducibility validation recalculates each file's size and SHA256 and compares them with the frozen registry. Source code, schemas, policies, manifests, indexes, validation reports, session metadata, and small communication artifacts can therefore be audited without opening large external payloads.

### 3.2 External immutable payload references

| Artifact ID | Governed size (bytes) | Partition-set SHA256 | Storage reference |
|---|---:|---|---|
{chr(10).join(external_lines)}

The three references describe {external_total:,} governed bytes in total. Task #037C neither reads nor copies those payload bytes. Their storage references identify content-addressed local staging or pending durable registration; this report does not claim public release availability.

### 3.3 Versioning, identity, and provenance

- Artifact IDs identify immutable registry entries; source-native external IDs remain unchanged.
- Component, schema, representation, evidence-snapshot, registry, report, and future release versions remain separate axes.
- SHA256 verifies byte identity, not scientific correctness.
- Provenance references record upstream release or contract identity.
- Dependency references preserve computational lineage and must not be interpreted as independent evidence votes.

The future release-manifest contract is `{release_governance['schema_version']}`. Its presence defines package structure but does not create a package.

## 4. Reproducibility model

### 4.1 Reproducible computational properties

| Property | Governed claim |
|---|---|
| Deterministic generation | Identical frozen inputs, generator versions, and rules produce byte-identical governed outputs where each task's validation report states this result. |
| Metadata validation | Identities, versions, dimensions, controlled vocabularies, lifecycle states, and source-release links are checked deterministically. |
| Schema validation | Closed schemas constrain required fields and reject undeclared or prohibited structural fields. |
| Artifact integrity | Registered Git-managed bytes are checked by size and SHA256; external payloads are checked through frozen metadata identities and partition-set hashes. |
| Provenance preservation | Layer-to-layer identities, content hashes, dependency relationships, missingness, and limitation references remain traceable. |

### 4.2 Not claimed

This project does not claim:

- biological reproducibility;
- clinical reproducibility;
- therapeutic prediction;
- experimental target validation;
- efficacy, safety, or clinical benefit.

Computational regeneration can demonstrate that governed software transforms the same frozen inputs into the same bytes. It cannot demonstrate that a molecular observation is causal or therapeutically useful.

## 5. Validation framework

### 5.1 Frozen hashes

Every governed task checks frozen input hashes before and after generation. The Artifact Registry independently records and validates 38 Git-managed file artifacts and three external payload references. Task #037C re-hashes every Git-managed registry row before generating this report.

### 5.2 Deterministic regeneration

The landscape, Evidence Summary, structural routing, case dossier, and presentation tasks each record two complete byte-identical generations. Task #037C similarly generates this report and its governance metadata twice and compares the bytes.

### 5.3 Dependency preservation

The landscape records ordered dependency relationships without collapsing dependent records. Evidence Summaries preserve those relationships, routing preserves component-state snapshots and source-summary identities, and case dossiers preserve routing identities, rule traces, limitations, and deterministic selection tokens. The Artifact Registry requires all registered dependency references to resolve and its dependency graph to remain acyclic.

### 5.4 Schema validation

Layer-specific schemas preserve identity, component state, missingness, provenance, dependency, limitation, and version contracts. Task #037A defines the future release-manifest schema; Task #037B defines the registry schema. Schema conformance is structural validation only.

### 5.5 Prohibited-field checks

Previous generators recursively reject fields that would introduce scores, rankings, priorities, confidence metrics, recommendations, target-quality assertions, or evidence-strength assertions. Task #037C preserves those boundaries and adds none of those values.

## 6. Reproducibility boundaries and limitations

1. **Differential expression is candidate generation, not target proof.** Expression association does not establish disease causality or therapeutic actionability.
2. **Evidence representation is not ranking.** Structural component states and evidence availability do not establish comparative target quality.
3. **Missing evidence is not negative evidence.** `MISSING`, `NOT_QUERIED`, `NOT_FOUND`, and related controlled states must retain their governed meanings.
4. **Routing categories are not priorities.** The transparent categories are non-ordinal rule outcomes and must not be read as a preferred order.
5. **Artifact validation is not biological validation.** Hash, schema, lineage, and deterministic-regeneration checks establish computational integrity only.
6. **External storage is not yet a public release.** The registry contains metadata references to immutable payload sets, but durable distribution remains a future release action.
7. **The registry is intentionally bounded.** Registry v0.1 covers the declared release-framework inputs and does not claim exhaustive coverage of every historical repository artifact.
8. **No wet-lab replication is performed here.** Experimental validation remains outside this computational framework.

## 7. Reproduction contract

A future reproducibility exercise should:

1. verify the registry, policy, schema, generator, and frozen release identities;
2. verify every Git-managed byte size and SHA256;
3. resolve external immutable payloads by source-native ID and partition-set SHA256 without rewriting identifiers;
4. use the recorded generator, schema, component, rule-catalog, and snapshot versions;
5. regenerate only the authorized layer under its frozen contract;
6. compare every generated byte, index identity, dependency reference, and validation disposition;
7. report mismatches rather than changing frozen inputs or manufacturing agreement.

This report documents that contract. It does not execute it for the scientific layers.

## 8. Report provenance and status

This report is generated deterministically by `analysis/37C_generate_reproducibility_report.py` from frozen manifests and Artifact Registry v0.1. Its own SHA256 and generator identity are recorded in `outputs/reproducibility_report_v0.1/reproducibility_report_manifest.json`.

Status: validated governance documentation candidate. No release package was created, and no artifact lifecycle state was advanced.
"""
    return text.encode("utf-8")


def validate_markdown(report_bytes: bytes) -> int:
    text = report_bytes.decode("utf-8")
    required_headings = [
        "# Reproducibility Report v0.1",
        "## 1. Project identity and purpose",
        "## 2. Computational lifecycle",
        "## 3. Artifact governance",
        "## 4. Reproducibility model",
        "## 5. Validation framework",
        "## 6. Reproducibility boundaries and limitations",
        "## 7. Reproduction contract",
        "## 8. Report provenance and status",
    ]
    for heading in required_headings:
        if text.count(heading) != 1:
            fail(f"Required report heading missing or duplicated: {heading}")
    required_statements = [
        "This project represents evidence structure and provenance.",
        "biological validation",
        "therapeutic value",
        "clinical utility",
        "target recommendation",
        "Differential expression is candidate generation, not target proof.",
        "Evidence representation is not ranking.",
        "Missing evidence is not negative evidence.",
        "Routing categories are not priorities.",
        "Artifact validation is not biological validation.",
        "No release package was created",
    ]
    for statement in required_statements:
        if statement not in text:
            fail(f"Required reproducibility statement missing: {statement}")
    if text.count("```") % 2:
        fail("Unbalanced Markdown code fences")
    link_count = 0
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
        if target.startswith(("http://", "https://", "#")):
            fail("Network or unresolved anchor link is outside Task #037C scope")
        resolved = (REPORT_PATH.parent / target.split("#", 1)[0]).resolve()
        if not resolved.is_file():
            fail(f"Broken reproducibility report link: {target}")
        link_count += 1
    return link_count


def build_outputs(
    report_bytes: bytes,
    report_links: int,
    registry_manifest: dict[str, Any],
    registry_counts: dict[str, int],
    manifests: dict[str, dict[str, Any]],
    frozen_hashes: dict[str, str],
) -> dict[str, bytes]:
    report_hash = sha256_bytes(report_bytes)
    report_id = stable_id(
        "REPROREPORT",
        [REPORT_VERSION, registry_manifest["registry_id"], report_hash],
    )
    manifest = {
        "task_id": TASK_ID,
        "project_id": PROJECT_ID,
        "report_id": report_id,
        "report_version": REPORT_VERSION,
        "report_status": "VALIDATED_GOVERNANCE_DOCUMENTATION_CANDIDATE",
        "generator": {
            "relative_path": "analysis/37C_generate_reproducibility_report.py",
            "generator_version": GENERATOR_VERSION,
            "sha256": sha256_file(ROOT / "analysis/37C_generate_reproducibility_report.py"),
        },
        "report_artifact": {
            "relative_path": "docs/reproducibility_report_v0.1.md",
            "sha256": report_hash,
            "size_bytes": len(report_bytes),
        },
        "source_registry": {
            "registry_id": registry_manifest["registry_id"],
            "registry_version": registry_manifest["registry_version"],
            "registry_sha256": FROZEN_INPUT_SHA256[
                "outputs/artifact_registry_v0.1/artifact_registry.csv"
            ],
            "registered_records": registry_manifest["counts"]["records"],
            "git_managed_rows_rehashed": registry_counts["git_rows"],
            "external_payload_metadata_rows": registry_counts["external_rows"],
        },
        "source_releases": {
            "landscape_release_id": manifests["landscape"]["release_id"],
            "evidence_summary_release_id": manifests["summary"]["release_id"],
            "structural_routing_release_id": manifests["routing"]["release_id"],
            "case_dossier_release_id": manifests["dossier"]["release_id"],
            "presentation_release_id": manifests["presentation"]["presentation_release_id"],
            "release_schema_governance_id": manifests["release_governance"][
                "schema_governance_id"
            ],
        },
        "frozen_inputs": frozen_hashes,
        "validation": {
            "deterministic_report_generation": "BYTE_IDENTICAL",
            "markdown_consistency": "PASS",
            "resolved_local_markdown_links": report_links,
            "registered_git_artifact_hashes": "PASS",
            "frozen_upstream_hashes_unchanged": "PASS",
            "existing_artifacts_modified": False,
            "scientific_artifacts_generated": False,
            "scientific_workflows_rerun": False,
            "external_payload_bytes_read": False,
            "release_package_generated": False,
            "runtime_ai_decisions_used": False,
        },
        "validation_status": "PASS",
    }
    validation = f"""# Task #037C Reproducibility Report Validation

**Validation status:** PASS

## Checks

- PASS — report generated twice with byte-identical Markdown
- PASS — required project identity, lifecycle, governance, reproducibility, validation, and limitation sections present exactly once
- PASS — required interpretation boundaries present
- PASS — {report_links} local Markdown links resolve
- PASS — Artifact Registry identity, CSV hash, row count, identifiers, paths, and storage counts reconciled
- PASS — all {registry_counts['git_rows']} registered Git-managed artifacts independently re-hashed by size and SHA256
- PASS — all {registry_counts['external_rows']} external payload rows used as metadata references only; external bytes not read or copied
- PASS — layer identities, 29,606-entity counts, component versions, and cross-layer provenance reconciled
- PASS — all {len(FROZEN_INPUT_SHA256)} direct frozen input hashes unchanged before and after generation
- PASS — no existing artifact modified and no scientific artifact generated
- PASS — no network/API access, scientific workflow rerun, component rebuild, runtime AI decision, scoring, ranking, recommendation, or biological interpretation

## Boundary

The report documents computational reproducibility and its limits. It does not create a release package or establish biological, clinical, or therapeutic reproducibility.
""".encode("utf-8")
    session = ("\n".join([
        f"task={TASK_ID}",
        f"project_id={PROJECT_ID}",
        f"report_version={REPORT_VERSION}",
        f"generator_version={GENERATOR_VERSION}",
        f"python_version={platform.python_version()}",
        f"python_implementation={platform.python_implementation()}",
        "standard_library_only=TRUE",
        "network_access=PROHIBITED_NOT_USED",
        "api_access=PROHIBITED_NOT_USED",
        "external_data_retrieval=FALSE",
        "scientific_workflows_rerun=FALSE",
        "components_rebuilt=FALSE",
        "scientific_artifacts_generated=FALSE",
        "external_payload_bytes_read=FALSE",
        "runtime_ai_llm_decisions=PROHIBITED_NONE_USED",
        "randomness=NOT_USED",
        "wall_clock_governed_values=NOT_USED",
        "release_package_generated=FALSE",
        "deterministic_generation=BYTE_IDENTICAL",
    ]) + "\n").encode("utf-8")
    return {
        "reproducibility_report_manifest.json": pretty_json_bytes(manifest),
        "validation_report.md": validation,
        "session_info.txt": session,
    }


def main() -> None:
    validate_working_tree_scope()
    validate_output_scope()
    frozen_before = validate_frozen_inputs()
    registry_manifest, registry_rows, registry_by_path, registry_counts = (
        load_and_validate_registry()
    )
    manifests = load_and_reconcile_manifests(registry_by_path)

    first_report = build_report(registry_manifest, registry_rows, manifests)
    second_report = build_report(registry_manifest, registry_rows, manifests)
    if first_report != second_report:
        fail("Two complete reproducibility report generations are not byte-identical")
    report_links = validate_markdown(first_report)
    first_outputs = build_outputs(
        first_report,
        report_links,
        registry_manifest,
        registry_counts,
        manifests,
        frozen_before,
    )
    second_outputs = build_outputs(
        second_report,
        report_links,
        registry_manifest,
        registry_counts,
        manifests,
        frozen_before,
    )
    if first_outputs != second_outputs:
        fail("Two complete reproducibility governance generations are not byte-identical")
    if frozen_before != validate_frozen_inputs():
        fail("Direct frozen input hashes changed during Task #037C generation")

    REPORT_PATH.write_bytes(first_report)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, data in sorted(first_outputs.items()):
        (OUTPUT_DIR / name).write_bytes(data)
    if REPORT_PATH.read_bytes() != first_report:
        fail("Written reproducibility report differs from validated bytes")
    if any((OUTPUT_DIR / name).read_bytes() != data for name, data in first_outputs.items()):
        fail("Written reproducibility governance output differs from validated bytes")
    if frozen_before != validate_frozen_inputs():
        fail("Direct frozen input hashes changed after Task #037C generation")
    validate_working_tree_scope()

    print(f"report_version={REPORT_VERSION}")
    print(f"registry_records={len(registry_rows)}")
    print(f"git_managed_artifacts_rehashed={registry_counts['git_rows']}")
    print("release_package_generated=FALSE")
    print("deterministic_generation=BYTE_IDENTICAL")
    print("validation_status=PASS")


if __name__ == "__main__":
    main()
