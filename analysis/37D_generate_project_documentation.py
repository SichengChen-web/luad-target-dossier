#!/usr/bin/env python3
"""Generate final GitHub-facing project documentation v1.0.

Task #037D creates documentation and communication metadata only. It does not
create a release package, rerun pipelines, rebuild components, access external
data, modify frozen artifacts, add scientific evidence or biological claims,
score or rank targets, recommend targets, or use runtime AI decisions.
"""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
README_PATH = ROOT / "README.md"
OVERVIEW_PATH = ROOT / "docs/project_overview_v1.0.md"
RELEASE_NOTES_PATH = ROOT / "docs/release_notes_v1.0.md"
OUTPUT_DIR = ROOT / "outputs/final_release_documentation_v1.0"
MANIFEST_PATH = OUTPUT_DIR / "final_release_manifest.json"
VALIDATION_PATH = OUTPUT_DIR / "validation_report.md"
SESSION_PATH = OUTPUT_DIR / "session_info.txt"

TASK_ID = "TASK_037D"
PROJECT_ID = "LUAD_EXPRESSION_DRUGGABLE_TARGET_EVIDENCE_DOSSIER"
PROJECT_NAME = "LUAD Expression → Druggable-Target Evidence Dossier"
DOCUMENTATION_VERSION = "PROJECT_DOCUMENTATION_V1.0"
GENERATOR_VERSION = "PROJECT_DOCUMENTATION_GENERATOR_V1.0"

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
    "docs/reproducibility_report_v0.1.md": "ae7d92d02188548cb8de4d1c337de711e1f5a33d7291168d10f20c436a7af223",
    "outputs/reproducibility_report_v0.1/reproducibility_report_manifest.json": "05850c56575f21e2a46717a6b95357c02f99691d38a87c99edeaa2f2e3c48073",
    "outputs/reproducibility_report_v0.1/validation_report.md": "ebfa6d5f917c6914fef09f0218458ca171d90421673056591ddb4cbcd6fd5c94",
    "outputs/reproducibility_report_v0.1/session_info.txt": "dcd6474a72e33a834aa3670a0017b78264acc6cedbf061e8ae3bbedd3253da60",
}

ALLOWED_WORKTREE_PATHS = {
    "README.md",
    "docs/project_overview_v1.0.md",
    "docs/release_notes_v1.0.md",
    "analysis/37D_generate_project_documentation.py",
    "outputs/final_release_documentation_v1.0/final_release_manifest.json",
    "outputs/final_release_documentation_v1.0/validation_report.md",
    "outputs/final_release_documentation_v1.0/session_info.txt",
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
            fail("Unexpected Task #037D output files: " + ", ".join(unexpected))


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


def load_registry() -> tuple[dict[str, Any], list[dict[str, str]], dict[str, dict[str, str]]]:
    registry_path = ROOT / "outputs/artifact_registry_v0.1/artifact_registry.csv"
    manifest = json.loads(
        (ROOT / "outputs/artifact_registry_v0.1/artifact_registry_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    if manifest.get("validation_status") != "PASS":
        fail("Artifact Registry is not validated")
    if manifest.get("registry_artifact", {}).get("sha256") != sha256_file(registry_path):
        fail("Artifact Registry CSV no longer matches its manifest")
    with registry_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != REGISTRY_COLUMNS:
            fail("Artifact Registry columns changed")
        rows = list(reader)
    if len(rows) != manifest.get("counts", {}).get("records"):
        fail("Artifact Registry count changed")
    by_path = {row["relative_path"]: row for row in rows}
    if len(by_path) != len(rows) or len({row["artifact_id"] for row in rows}) != len(rows):
        fail("Artifact Registry identities or paths are not unique")
    for row in rows:
        if row["storage_class"] == "GIT_MANAGED":
            path = ROOT / row["relative_path"]
            if not path.is_file() or path.is_symlink():
                fail(f"Registered Git artifact is missing or unsafe: {row['relative_path']}")
            if path.stat().st_size != int(row["size_bytes"]) or sha256_file(path) != row["sha256"]:
                fail(f"Registered Git artifact changed: {row['relative_path']}")
    return manifest, rows, by_path


def load_sources(registry_by_path: dict[str, dict[str, str]]) -> dict[str, dict[str, Any]]:
    paths = {
        "release_governance": "outputs/release_governance_v0.1/release_schema_manifest.json",
        "artifact_registry": "outputs/artifact_registry_v0.1/artifact_registry_manifest.json",
        "reproducibility": "outputs/reproducibility_report_v0.1/reproducibility_report_manifest.json",
        "presentation": "outputs/presentation_artifacts_v0.1/presentation_manifest.json",
        "dossier": "outputs/case_dossiers_v0.1/dossier_manifest.json",
    }
    values: dict[str, dict[str, Any]] = {}
    for name, relative_path in paths.items():
        path = ROOT / relative_path
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get("validation_status") != "PASS":
            fail(f"Source manifest is not validated: {name}")
        if name in {"release_governance", "presentation", "dossier"}:
            registry_row = registry_by_path.get(relative_path)
            if registry_row is None or registry_row["sha256"] != sha256_file(path):
                fail(f"Source manifest is absent or changed in registry: {relative_path}")
        values[name] = value

    presentation_sources = values["presentation"].get("source_releases", {})
    if presentation_sources.get("case_dossier_release_id") != values["dossier"].get("release_id"):
        fail("Presentation-to-dossier source identity changed")
    if values["reproducibility"].get("source_registry", {}).get("registry_id") != values[
        "artifact_registry"
    ].get("registry_id"):
        fail("Reproducibility Report source registry identity changed")
    if values["release_governance"].get("schema_version") != "RELEASE_MANIFEST_SCHEMA_V0.1":
        fail("Release governance schema version changed")
    return values


def build_readme(
    registry_manifest: dict[str, Any], sources: dict[str, dict[str, Any]], poster_available: bool
) -> bytes:
    presentation = sources["presentation"]
    text = f"""# {PROJECT_NAME}

## Project identity

This repository develops a reproducible, evidence-grounded framework for organizing evidence relevant to lung adenocarcinoma target research. It begins with governed transcriptomic and disease-association observations and preserves their structure, missingness, provenance, dependencies, limitations, and version history through auditable target evidence dossiers.

The framework is an evidence-representation and hypothesis-organization system. It is not a target-ranking system, a clinical decision tool, or experimental target validation.

## Scientific motivation

Differential expression can identify disease-associated molecular changes, but it does not prove causality, drug efficacy, safety, or therapeutic value. External evidence can also be incomplete, dependent, or absent for reasons unrelated to biology. The project therefore represents evidence and its provenance before any future target-level interpretation.

This separation makes it possible to inspect what was observed, what was not found, what was not queried, which records are dependent, and which limitations remain—without silently converting evidence availability into target quality.

## Framework architecture

```text
Transcriptomic evidence component     Disease association evidence component
                  \\                         /
                   -> Evidence Landscape ->
                      Evidence Summary
                            |
                    Structural Routing
                            |
                Representative Case Dossiers
```

- `COMP_TRANSCRIPTOMIC_EVIDENCE_V0.1` represents governed transcriptomic observations.
- `COMP_DISEASE_ASSOCIATION_V0.1` represents governed disease-association observations.
- The Multi-component Evidence Landscape preserves component states, feature missingness, provenance, dependencies, and limitations for 29,606 immutable EnsemblID entities.
- Evidence Summaries provide deterministic structural projections of landscapes.
- Structural routing applies a transparent, non-ordinal rule catalog and preserves complete rule traces.
- Representative Case Dossiers provide deterministic presentation examples of governed structural patterns; they are not selected as preferred targets.

See the [Project Overview v1.0](docs/project_overview_v1.0.md) and the original [Scientific Specification v0.1](docs/scientific_spec_v0.1.md).

## Reproducibility and artifact governance

The [Artifact Registry v0.1](outputs/artifact_registry_v0.1/artifact_registry.csv) records {registry_manifest['counts']['records']} computational artifacts with immutable identities, versions, SHA256 values, provenance references, dependencies, lifecycle states, and storage references.

- {registry_manifest['counts']['by_storage_class']['GIT_MANAGED']} Git-managed artifacts can be checked directly by file size and SHA256.
- {registry_manifest['counts']['by_storage_class']['EXTERNAL_IMMUTABLE']} large immutable payload sets are represented by source-native IDs, partition-set hashes, sizes, and external-storage references rather than copied into Git.
- The [Reproducibility Report v0.1](docs/reproducibility_report_v0.1.md) separates computational reproducibility from biological, clinical, and therapeutic claims.
- The [Release Package Specification v0.1](docs/governance/release_package_specification_v0.1.md) defines future packaging and lifecycle rules. No release package is created by this documentation task.

## Validation

The governed framework validates:

- deterministic, byte-identical regeneration under frozen inputs and versions;
- artifact size and SHA256 integrity;
- immutable EnsemblID identity and canonical ordering;
- schema and controlled-vocabulary conformance;
- provenance and dependency preservation;
- missingness and limitation preservation;
- recursive rejection of prohibited evaluation fields.

Computational validation demonstrates structural and reproducibility conformance. It does not establish biological truth.

## Limitations

- **Differential expression is not target proof.** Association does not establish causality or therapeutic actionability.
- **Evidence representation is not ranking.** Evidence structure and availability do not establish comparative target quality.
- **Missing evidence is not negative evidence.** `MISSING`, `NOT_FOUND`, and `NOT_QUERIED` retain distinct governed meanings.
- **Routing categories are not target priorities.** They are non-ordinal structural rule outcomes.
- **Computational validation is not biological validation.** Hashes, schemas, and deterministic regeneration do not demonstrate efficacy, safety, or clinical benefit.
- External payload storage remains governed separately from public release distribution.

## Communication materials

Validated communication artifacts are available as:

- [Architecture summary](outputs/presentation_artifacts_v0.1/architecture_summary.md)
- [Evidence-layer summary](outputs/presentation_artifacts_v0.1/evidence_layer_summary.csv)
- [Case-pattern summary](outputs/presentation_artifacts_v0.1/case_pattern_summary.csv)
- [Provenance-flow summary](outputs/presentation_artifacts_v0.1/provenance_flow_summary.md)

Poster materials: {'registered and linked above' if poster_available else 'none are registered in Artifact Registry v0.1; no poster is claimed in this documentation release.'}

## Documentation release

- [Project Overview v1.0](docs/project_overview_v1.0.md)
- [Release Notes v1.0](docs/release_notes_v1.0.md)
- [Reproducibility Report v0.1](docs/reproducibility_report_v0.1.md)
- Presentation release: `{presentation['presentation_release_id']}`

This documentation describes frozen computational artifacts. It introduces no new scientific evidence, ranking, score, recommendation, or biological claim.
"""
    return text.encode("utf-8")


def build_overview(
    registry_manifest: dict[str, Any],
    registry_rows: list[dict[str, str]],
    sources: dict[str, dict[str, Any]],
) -> bytes:
    presentation = sources["presentation"]
    dossier = sources["dossier"]
    reproducibility = sources["reproducibility"]
    release_governance = sources["release_governance"]
    external = sorted(
        (row for row in registry_rows if row["storage_class"] == "EXTERNAL_IMMUTABLE"),
        key=lambda row: row["artifact_id"],
    )
    external_lines = [
        f"| `{row['artifact_id']}` | {int(row['size_bytes']):,} | `{row['sha256']}` |"
        for row in external
    ]
    text = f"""# Project Overview v1.0

**Project:** {PROJECT_NAME}  
**Documentation version:** `{DOCUMENTATION_VERSION}`  
**Status:** Validated project documentation candidate; no release package created

## 1. Purpose and positioning

The project provides a deterministic architecture for representing evidence associated with LUAD expression-derived entities. Its purpose is to preserve evidence identity, availability, missingness, provenance, dependencies, and limitations so that future scientific review can inspect the basis of a dossier without hidden aggregation.

The framework does not itself determine target quality, therapeutic value, clinical utility, or a preferred target. It is infrastructure for evidence organization and hypothesis generation.

## 2. Why representation precedes interpretation

Evidence sources answer different questions and can share underlying datasets. A transcriptomic association, a disease-association record, a tractability observation, and a clinical record are not interchangeable votes. Missing records may reflect query scope or source coverage rather than biology. Representing source identity, dependency, and missingness before interpretation prevents record counts or database presence from becoming implicit scientific conclusions.

The current multi-component release includes transcriptomic and disease-association components only. Future components require separate registration, source contracts, snapshots, feature extraction, validation, and materialization under the governed component interface.

## 3. Architecture

```text
Frozen source observations and snapshots
  -> COMP_TRANSCRIPTOMIC_EVIDENCE_V0.1
  -> COMP_DISEASE_ASSOCIATION_V0.1
  -> Multi-component Evidence Landscape
  -> Evidence Summary
  -> Transparent non-ordinal structural routing
  -> Representative structural case dossiers
  -> Governed communication artifacts
```

The architecture preserves one immutable EnsemblID universe of 29,606 entities. Each representation layer retains its own schema, generator, component, rule-catalog, snapshot, and artifact version axes.

## 4. Governed layers

| Layer | Governed release identity | Purpose boundary |
|---|---|---|
| Evidence Landscape | `{presentation['source_releases']['landscape_release_id']}` | Structural composition of component, feature, provenance, dependency, missingness, and limitation references |
| Evidence Summary | `{presentation['source_releases']['evidence_summary_release_id']}` | Deterministic structural projection of one landscape per entity |
| Structural routing | `{presentation['source_releases']['prioritization_release_id']}` | Fixed-rule, non-ordinal routing with complete trace |
| Case dossiers | `{dossier['release_id']}` | Deterministic representative presentation patterns |
| Communication artifacts | `{presentation['presentation_release_id']}` | Human-readable structural summaries without added evidence |

No layer produces an overall state, evidence-strength measure, target score, rank, or recommendation.

## 5. Artifact governance

Artifact Registry `{registry_manifest['registry_id']}` contains {registry_manifest['counts']['records']} records: {registry_manifest['counts']['by_artifact_scope']['SCIENTIFIC']} scientific-scope, {registry_manifest['counts']['by_artifact_scope']['GOVERNANCE']} governance, and {registry_manifest['counts']['by_artifact_scope']['COMMUNICATION']} communication artifacts.

### Git-managed records

Git-managed artifacts use repository-relative paths and are validated against registered sizes and SHA256 values. These include manifests, indexes, policies, schemas, validation reports, session metadata, generator source, and communication documents.

### External immutable payload references

| Artifact ID | Governed size (bytes) | Partition-set SHA256 |
|---|---:|---|
{chr(10).join(external_lines)}

External rows are metadata references only. Their payloads are not copied into Git by documentation or registry tasks. Durable public distribution remains a separate future action.

## 6. Reproducibility model

The [Reproducibility Report v0.1](reproducibility_report_v0.1.md) documents:

- deterministic generation under frozen inputs;
- metadata and schema validation;
- byte-size and SHA256 integrity checks;
- cross-layer identity reconciliation;
- provenance, dependency, missingness, and limitation preservation;
- explicit boundaries on biological, clinical, and therapeutic claims.

Report `{reproducibility['report_id']}` re-hashed all 38 Git-managed Artifact Registry rows and used the three external payload rows as metadata references only.

## 7. Validation architecture

Validation is layered and fail-closed:

1. schema checks constrain required fields and controlled vocabularies;
2. frozen-hash checks detect input mutation;
3. identity checks preserve the canonical entity universe and release links;
4. lineage checks preserve source, provenance, and dependency references;
5. missingness checks preserve controlled meanings;
6. deterministic regeneration compares generated bytes;
7. prohibited-field checks reject hidden evaluation concepts.

Validation failures are reported rather than repaired by altering frozen artifacts.

## 8. Interpretation boundaries

- DE is not target proof.
- Evidence representation is not ranking.
- Missing evidence is not negative evidence.
- Routing categories are not target priorities.
- Computational validation is not biological validation.
- Representative cases are presentation examples, not preferred targets.
- Release or registry inclusion is not therapeutic endorsement.

## 9. Release and documentation status

Task #037A established `{release_governance['schema_version']}` for a future package. Task #037B created an artifact registry. Task #037C documented computational reproducibility. Task #037D creates the GitHub-facing documentation set only.

No release package, upload, external retrieval, scientific regeneration, target evaluation, or artifact lifecycle promotion occurs in this documentation release.

## 10. Reviewer entry points

- [Repository README](../README.md)
- [Scientific Specification v0.1](scientific_spec_v0.1.md)
- [Reproducibility Report v0.1](reproducibility_report_v0.1.md)
- [Release Package Specification v0.1](governance/release_package_specification_v0.1.md)
- [Artifact Registry Policy v0.1](governance/artifact_registry_policy_v0.1.md)
- [Artifact Registry CSV](../outputs/artifact_registry_v0.1/artifact_registry.csv)
- [Presentation architecture summary](../outputs/presentation_artifacts_v0.1/architecture_summary.md)
- [Release Notes v1.0](release_notes_v1.0.md)
"""
    return text.encode("utf-8")


def build_release_notes(
    registry_manifest: dict[str, Any], sources: dict[str, dict[str, Any]], poster_available: bool
) -> bytes:
    presentation = sources["presentation"]
    dossier = sources["dossier"]
    reproducibility = sources["reproducibility"]
    text = f"""# Release Notes v1.0

**Release:** Project documentation v1.0  
**Release type:** Documentation and communication only  
**Status:** Validated documentation candidate; no computational release package created

## Summary

Version 1.0 provides the final GitHub-facing documentation for the governed LUAD Target Evidence Dossier framework. It explains the scientific motivation, architecture, artifact governance, validation model, reproducibility boundaries, and current limitations without generating or reinterpreting scientific evidence.

## Documentation included

- [README](../README.md)
- [Project Overview v1.0](project_overview_v1.0.md)
- [Reproducibility Report v0.1](reproducibility_report_v0.1.md)
- [Scientific Specification v0.1](scientific_spec_v0.1.md)
- [Release governance](governance/release_package_specification_v0.1.md)
- [Artifact Registry](../outputs/artifact_registry_v0.1/artifact_registry.csv)

## Framework status represented

- 29,606 immutable EnsemblID entities are preserved across the governed multi-component universe.
- Two evidence components are represented independently by version: transcriptomic evidence and disease association.
- Landscape, Evidence Summary, and structural routing layers retain source identities and structural states.
- `{dossier['release_id']}` contains four deterministic representative case-pattern slots.
- `{presentation['presentation_release_id']}` provides four validated communication artifacts.
- `{registry_manifest['registry_id']}` registers {registry_manifest['counts']['records']} computational artifacts, including three external immutable payload references.
- `{reproducibility['report_id']}` documents the computational reproducibility model and its boundaries.

These are structural inventory statements, not biological or therapeutic conclusions.

## Validation disposition

The documentation generator validates:

- deterministic, byte-identical documentation generation;
- required Markdown sections and terminology;
- resolution of all local links;
- frozen upstream SHA256 values;
- Artifact Registry file integrity;
- cross-document release identities;
- absence of scientific artifact generation or modification.

## Communication materials

- [Architecture summary](../outputs/presentation_artifacts_v0.1/architecture_summary.md)
- [Evidence-layer summary](../outputs/presentation_artifacts_v0.1/evidence_layer_summary.csv)
- [Case-pattern summary](../outputs/presentation_artifacts_v0.1/case_pattern_summary.csv)
- [Provenance-flow summary](../outputs/presentation_artifacts_v0.1/provenance_flow_summary.md)

Poster materials: {'registered in the governed registry.' if poster_available else 'not available in Artifact Registry v0.1 and not claimed for this release.'}

## Known limitations

- Differential expression remains a candidate-generation signal, not target proof.
- Evidence representation does not establish a target ranking.
- Missing evidence is not negative evidence.
- Structural routing categories are non-ordinal and are not target priorities.
- Computational validation does not constitute biological validation.
- Registry v0.1 is intentionally bounded to the declared release-framework inputs.
- External immutable payloads require separate durable-storage governance before a public computational package can be released.

## Not included

This documentation release does not include:

- new evidence retrieval or scientific analysis;
- rebuilt components, landscapes, summaries, routing representations, or dossiers;
- target scores, rankings, recommendations, or therapeutic direction;
- biological, clinical, or therapeutic claims;
- a release package, external upload, or artifact lifecycle promotion.

## Version boundary

Documentation v1.0 is versioned separately from component, schema, evidence-snapshot, artifact, registry, and future package versions. Updating documentation must not silently mutate frozen computational artifacts.
"""
    return text.encode("utf-8")


def validate_markdown_bundle(bundle: dict[Path, bytes]) -> int:
    required = {
        README_PATH: [
            "# LUAD Expression → Druggable-Target Evidence Dossier",
            "## Scientific motivation",
            "## Framework architecture",
            "## Reproducibility and artifact governance",
            "## Validation",
            "## Limitations",
            "## Communication materials",
            "Differential expression is not target proof.",
            "Evidence representation is not ranking.",
            "Missing evidence is not negative evidence.",
            "Routing categories are not target priorities.",
            "Computational validation is not biological validation.",
        ],
        OVERVIEW_PATH: [
            "# Project Overview v1.0",
            "## 3. Architecture",
            "## 5. Artifact governance",
            "## 6. Reproducibility model",
            "## 8. Interpretation boundaries",
        ],
        RELEASE_NOTES_PATH: [
            "# Release Notes v1.0",
            "## Framework status represented",
            "## Validation disposition",
            "## Known limitations",
            "## Not included",
        ],
    }
    generated_paths = set(bundle)
    link_count = 0
    for path, data in bundle.items():
        text = data.decode("utf-8")
        if text.count("\n# ") > 0 or not text.startswith("# "):
            fail(f"Markdown document has invalid H1 structure: {path.relative_to(ROOT)}")
        if text.count("```") % 2:
            fail(f"Markdown code fences are unbalanced: {path.relative_to(ROOT)}")
        for term in required[path]:
            if term not in text:
                fail(f"Required documentation term missing from {path.name}: {term}")
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            if target.startswith(("http://", "https://", "#")):
                fail(f"External or unresolved anchor link is outside Task #037D scope: {target}")
            resolved = (path.parent / target.split("#", 1)[0]).resolve()
            if resolved not in generated_paths and not resolved.is_file():
                fail(f"Broken documentation link in {path.name}: {target}")
            link_count += 1
    return link_count


def build_outputs(
    docs: dict[Path, bytes],
    link_count: int,
    registry_manifest: dict[str, Any],
    sources: dict[str, dict[str, Any]],
    frozen_hashes: dict[str, str],
    poster_available: bool,
) -> dict[str, bytes]:
    documentation_artifacts = {
        path.relative_to(ROOT).as_posix(): {
            "sha256": sha256_bytes(data),
            "size_bytes": len(data),
        }
        for path, data in sorted(docs.items(), key=lambda item: item[0].as_posix())
    }
    documentation_id = stable_id(
        "DOCRLS",
        [DOCUMENTATION_VERSION, sorted((path, value["sha256"]) for path, value in documentation_artifacts.items())],
    )
    manifest = {
        "task_id": TASK_ID,
        "project_id": PROJECT_ID,
        "documentation_release_id": documentation_id,
        "documentation_version": DOCUMENTATION_VERSION,
        "manifest_type": "FINAL_PROJECT_DOCUMENTATION_MANIFEST",
        "documentation_status": "VALIDATED_DOCUMENTATION_CANDIDATE",
        "generator": {
            "relative_path": "analysis/37D_generate_project_documentation.py",
            "generator_version": GENERATOR_VERSION,
            "sha256": sha256_file(ROOT / "analysis/37D_generate_project_documentation.py"),
        },
        "documentation_artifacts": documentation_artifacts,
        "source_governance": {
            "release_schema_governance_id": sources["release_governance"]["schema_governance_id"],
            "artifact_registry_id": registry_manifest["registry_id"],
            "reproducibility_report_id": sources["reproducibility"]["report_id"],
            "presentation_release_id": sources["presentation"]["presentation_release_id"],
            "case_dossier_release_id": sources["dossier"]["release_id"],
        },
        "communication_materials": {
            "validated_presentation_artifacts": 4,
            "poster_material_registered": poster_available,
        },
        "frozen_inputs": frozen_hashes,
        "validation": {
            "deterministic_documentation_generation": "BYTE_IDENTICAL",
            "markdown_consistency": "PASS",
            "resolved_local_links": link_count,
            "artifact_registry_integrity": "PASS",
            "frozen_upstream_hashes_unchanged": "PASS",
            "existing_artifacts_modified_except_authorized_readme": False,
            "scientific_artifacts_generated": False,
            "release_package_generated": False,
            "network_access_used": False,
            "runtime_ai_decisions_used": False,
        },
        "validation_status": "PASS",
    }
    validation = f"""# Task #037D Final Documentation Validation

**Validation status:** PASS

## Checks

- PASS — README, Project Overview v1.0, and Release Notes v1.0 generated twice with byte-identical Markdown
- PASS — required identity, motivation, architecture, reproducibility, validation, limitation, and communication sections present
- PASS — {link_count} local Markdown links resolve
- PASS — Artifact Registry `{registry_manifest['registry_id']}` identity, rows, and all Git-managed artifact hashes reconciled
- PASS — release-governance, reproducibility-report, presentation, and case-dossier identities reconciled
- PASS — poster availability checked against Artifact Registry v0.1; registered poster artifact: {str(poster_available).upper()}
- PASS — all {len(FROZEN_INPUT_SHA256)} direct frozen input hashes unchanged before and after generation
- PASS — no existing artifact modified except the explicitly authorized root README
- PASS — no scientific artifact generated or regenerated
- PASS — no network/API access, pipeline rerun, component rebuild, runtime AI decision, score, ranking, recommendation, or biological claim

## Boundary

The output is a validated documentation candidate, not a computational release package. Documentation describes frozen artifacts and does not advance their lifecycle states or scientific interpretation.
""".encode("utf-8")
    session = ("\n".join([
        f"task={TASK_ID}",
        f"project_id={PROJECT_ID}",
        f"documentation_version={DOCUMENTATION_VERSION}",
        f"generator_version={GENERATOR_VERSION}",
        f"python_version={platform.python_version()}",
        f"python_implementation={platform.python_implementation()}",
        "standard_library_only=TRUE",
        "network_access=PROHIBITED_NOT_USED",
        "api_access=PROHIBITED_NOT_USED",
        "pipelines_rerun=FALSE",
        "components_rebuilt=FALSE",
        "scientific_artifacts_generated=FALSE",
        "poster_material_registered=" + str(poster_available).upper(),
        "runtime_ai_llm_decisions=PROHIBITED_NONE_USED",
        "randomness=NOT_USED",
        "wall_clock_governed_values=NOT_USED",
        "release_package_generated=FALSE",
        "deterministic_generation=BYTE_IDENTICAL",
    ]) + "\n").encode("utf-8")
    return {
        "final_release_manifest.json": pretty_json_bytes(manifest),
        "validation_report.md": validation,
        "session_info.txt": session,
    }


def main() -> None:
    validate_working_tree_scope()
    validate_output_scope()
    frozen_before = validate_frozen_inputs()
    registry_manifest, registry_rows, registry_by_path = load_registry()
    sources = load_sources(registry_by_path)
    poster_available = any(
        row["artifact_type"] == "POSTER_MATERIAL" or "poster" in row["relative_path"].lower()
        for row in registry_rows
    )

    first_docs = {
        README_PATH: build_readme(registry_manifest, sources, poster_available),
        OVERVIEW_PATH: build_overview(registry_manifest, registry_rows, sources),
        RELEASE_NOTES_PATH: build_release_notes(registry_manifest, sources, poster_available),
    }
    second_docs = {
        README_PATH: build_readme(registry_manifest, sources, poster_available),
        OVERVIEW_PATH: build_overview(registry_manifest, registry_rows, sources),
        RELEASE_NOTES_PATH: build_release_notes(registry_manifest, sources, poster_available),
    }
    if first_docs != second_docs:
        fail("Two complete project documentation generations are not byte-identical")
    link_count = validate_markdown_bundle(first_docs)
    first_outputs = build_outputs(
        first_docs,
        link_count,
        registry_manifest,
        sources,
        frozen_before,
        poster_available,
    )
    second_outputs = build_outputs(
        second_docs,
        link_count,
        registry_manifest,
        sources,
        frozen_before,
        poster_available,
    )
    if first_outputs != second_outputs:
        fail("Two complete documentation-governance generations are not byte-identical")
    if frozen_before != validate_frozen_inputs():
        fail("Frozen upstream hashes changed during Task #037D generation")

    for path, data in first_docs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, data in sorted(first_outputs.items()):
        (OUTPUT_DIR / name).write_bytes(data)
    if any(path.read_bytes() != data for path, data in first_docs.items()):
        fail("Written project documentation differs from validated bytes")
    if any((OUTPUT_DIR / name).read_bytes() != data for name, data in first_outputs.items()):
        fail("Written documentation metadata differs from validated bytes")
    if frozen_before != validate_frozen_inputs():
        fail("Frozen upstream hashes changed after Task #037D generation")
    validate_working_tree_scope()

    print(f"documentation_version={DOCUMENTATION_VERSION}")
    print(f"documentation_files={len(first_docs)}")
    print(f"resolved_local_links={link_count}")
    print(f"poster_material_registered={str(poster_available).upper()}")
    print("release_package_generated=FALSE")
    print("deterministic_generation=BYTE_IDENTICAL")
    print("validation_status=PASS")


if __name__ == "__main__":
    main()
