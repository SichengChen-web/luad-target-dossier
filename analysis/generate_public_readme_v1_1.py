#!/usr/bin/env python3
"""Generate the forward-only public README documentation patch v1.1.

This maintenance generator preserves the validated Task #037D v1.0 and Task
#038A releases. It creates no scientific task, evidence, component, score,
ordering, recommendation, or biological interpretation.
"""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
README_PATH = ROOT / "README.md"
RELEASE_NOTES_PATH = ROOT / "docs/release_notes_v1.1.md"
OUTPUT_DIR = ROOT / "outputs/final_release_documentation_v1.1"
MANIFEST_PATH = OUTPUT_DIR / "final_release_manifest.json"
VALIDATION_PATH = OUTPUT_DIR / "validation_report.md"
SESSION_PATH = OUTPUT_DIR / "session_info.txt"

PROJECT_ID = "LUAD_EXPRESSION_DRUGGABLE_TARGET_EVIDENCE_DOSSIER"
DOCUMENTATION_VERSION = "PROJECT_DOCUMENTATION_V1.1"
GENERATOR_VERSION = "PUBLIC_README_DOCUMENTATION_GENERATOR_V1.1"
PATCH_TYPE = "FORWARD_ONLY_DOCUMENTATION_MAINTENANCE"
HISTORICAL_BASE_COMMIT = "daffadf9feb0fc572b83306b433abfc8360e0e8b"
HISTORICAL_README_SHA256 = "5bd5bdaf54ee7f12e6c169db8049bb3b9c77b0b02bb186d5ff418e5d7a60af77"

FIGURE_PATHS = (
    "figures/complete_evidence_pattern.svg",
    "figures/partial_evidence_pattern.svg",
    "figures/conflict_evidence_pattern.svg",
    "figures/limitation_evidence_pattern.svg",
)

FROZEN_INPUTS = {
    "outputs/final_release_documentation_v1.0/final_release_manifest.json": "87e706362b41156c5b3054f96c40b45a6a9744c59f900815dc83df18bd2f63b5",
    "docs/project_overview_v1.0.md": "a35819c02c6f02a253973eb38bc30a12e5da0915ce234d7ece4ce1b15ba3946c",
    "docs/reproducibility_report_v0.1.md": "ae7d92d02188548cb8de4d1c337de711e1f5a33d7291168d10f20c436a7af223",
    "docs/release_notes_v1.0.md": "66ec903597964f5f5fde325b9d20cc074d7489e7279ee9494687bc53552eca41",
    "outputs/artifact_registry_v0.1/artifact_registry.csv": "06b0e6ff4ddbc751136edeeb0e60799d81328692968b2f43a25d2dc021750e57",
    "outputs/artifact_registry_v0.1/artifact_registry_manifest.json": "d7bbca889f78bbef55ecae59881a6b9ec34147762e6cd26b17810304dcedde2c",
    "outputs/case_study_communication_v0.1/case_study_manifest.json": "587a5bfb379dacc08d0dbb71c78906b6ce5a458ca5356482cfc146f4a1f04b26",
    "docs/case_study_communication_specification_v0.1.md": "d9ccd5714eace86107f1c8659dc1ce144e208aa87eaf3658eace34bdba5047fd",
    "outputs/evidence_profile_integration_v0.1/profile_manifest.json": "63492499977f7adb086e4ace9a491a72fa617a1fe054d544701826fb9657455d",
    "outputs/prioritization_v0.1/prioritization_manifest.json": "773eeec6bfa769c932f354bcc5eb552fe4a540a2fe65dd1811720b2e80c4ff80",
    "outputs/final_sample_qc/final_sample_qc_summary.md": "a5c18361788c8bf73135323fbd364d4700235b4b51b9ee146d54b75d61480de6",
    "outputs/presentation_artifacts_v0.1/presentation_manifest.json": "2bf7acce12685399476e50cfa26df049d8b54cc371e6dde6794b656b12f1d2e4",
    "figures/complete_evidence_pattern.svg": "c5386e2f3e9f73c05466ba82847edb85f54fa8c20d274ad5d4a97f40f77ad596",
    "figures/partial_evidence_pattern.svg": "3affb1153bc8eaa6f1c9880868bf0fb11e1ce3cf76f43b1b4adac2ae86a7f4ea",
    "figures/conflict_evidence_pattern.svg": "eb50c62bc4b83a06eef30c0b9b7947599a1f24fe5dcc585ad4ac6cc14d54420f",
    "figures/limitation_evidence_pattern.svg": "cad980b53b038e28986175fd90bb21262f40d6c1f3664f4e070fa94c39abea29",
}

ALLOWED_WORKTREE_PATHS = {
    "README.md",
    "analysis/generate_public_readme_v1_1.py",
    "docs/release_notes_v1.1.md",
    "outputs/final_release_documentation_v1.1/final_release_manifest.json",
    "outputs/final_release_documentation_v1.1/validation_report.md",
    "outputs/final_release_documentation_v1.1/session_info.txt",
}

PROHIBITED_PUBLIC_PHRASES = (
    "top target",
    "target ranking",
    "target recommendation",
    "therapeutic recommendation",
    "deterministic scoring",
    "strongest combined evidence",
)
MANDATED_NEGATED_BOUNDARY = "Complete ≠ best target"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def stable_id(prefix: str, value: Any) -> str:
    compact = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return prefix + "_" + sha256_bytes(compact.encode("utf-8"))[:32].upper()


def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    )
    return result.stdout


def validate_worktree_scope() -> None:
    unexpected: list[str] = []
    for line in run_git("status", "--porcelain=v1", "--untracked-files=all").splitlines():
        path_text = line[3:]
        if " -> " in path_text:
            path_text = path_text.split(" -> ", 1)[1]
        if path_text not in ALLOWED_WORKTREE_PATHS:
            unexpected.append(line)
    if unexpected:
        raise RuntimeError("Unexpected working-tree changes:\n" + "\n".join(unexpected))


def validate_historical_boundary() -> dict[str, Any]:
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", HISTORICAL_BASE_COMMIT, "HEAD"],
        cwd=ROOT,
    )
    if ancestor.returncode != 0:
        raise RuntimeError("Historical Task #038A base commit is not an ancestor of HEAD")
    historical_readme = run_git("show", f"{HISTORICAL_BASE_COMMIT}:README.md").encode("utf-8")
    if sha256_bytes(historical_readme) != HISTORICAL_README_SHA256:
        raise RuntimeError("Historical README cannot be reconstructed at the frozen base commit")
    old_manifest = json.loads(
        (ROOT / "outputs/final_release_documentation_v1.0/final_release_manifest.json").read_text()
    )
    if old_manifest["documentation_artifacts"]["README.md"]["sha256"] != HISTORICAL_README_SHA256:
        raise RuntimeError("Task #037D v1.0 does not freeze the expected historical README")
    case_manifest = json.loads(
        (ROOT / "outputs/case_study_communication_v0.1/case_study_manifest.json").read_text()
    )
    if case_manifest["frozen_inputs"]["README.md"] != HISTORICAL_README_SHA256:
        raise RuntimeError("Task #038A does not record the expected historical README input")
    return {"old_manifest": old_manifest, "case_manifest": case_manifest}


def validate_frozen_inputs() -> None:
    failures: list[str] = []
    for relative_path, expected in FROZEN_INPUTS.items():
        path = ROOT / relative_path
        if not path.is_file():
            failures.append(f"missing: {relative_path}")
        elif sha256_file(path) != expected:
            failures.append(f"hash mismatch: {relative_path}")
    if failures:
        raise RuntimeError("Frozen input validation failed:\n- " + "\n- ".join(failures))


def load_sources() -> dict[str, Any]:
    sources = {
        "registry": json.loads(
            (ROOT / "outputs/artifact_registry_v0.1/artifact_registry_manifest.json").read_text()
        ),
        "profile": json.loads(
            (ROOT / "outputs/evidence_profile_integration_v0.1/profile_manifest.json").read_text()
        ),
        "routing": json.loads(
            (ROOT / "outputs/prioritization_v0.1/prioritization_manifest.json").read_text()
        ),
        "case": json.loads(
            (ROOT / "outputs/case_study_communication_v0.1/case_study_manifest.json").read_text()
        ),
        "presentation": json.loads(
            (ROOT / "outputs/presentation_artifacts_v0.1/presentation_manifest.json").read_text()
        ),
    }
    for name, value in sources.items():
        if value.get("validation_status") != "PASS":
            raise RuntimeError(f"Frozen source is not validated: {name}")

    counts = sources["registry"]["counts"]
    if counts["records"] != 41 or counts["by_storage_class"] != {
        "EXTERNAL_IMMUTABLE": 3,
        "GIT_MANAGED": 38,
    }:
        raise RuntimeError("Artifact Registry scale changed")
    if sources["profile"]["profile_count"] != 29606 or sources["profile"]["component_count"] != 2:
        raise RuntimeError("Profile universe scale changed")
    expected_states = {
        "COMP_TRANSCRIPTOMIC_EVIDENCE": {"CONFLICTING": 3435, "OBSERVED": 26171},
        "COMP_DISEASE_ASSOCIATION": {"MISSING": 20500, "OBSERVED": 8393, "PARTIAL": 713},
    }
    observed_states = {
        component["component_id"]: component["state_counts"]
        for component in sources["profile"]["components"]
    }
    if observed_states != expected_states:
        raise RuntimeError("Component state counts changed")
    joint = sources["profile"]["joint_component_state_counts"]
    pattern_counts = {
        "both_observed": joint["OBSERVED|OBSERVED"],
        "partial_or_mixed": joint["OBSERVED|MISSING"] + joint["OBSERVED|PARTIAL"],
        "component_conflict": sum(value for key, value in joint.items() if key.startswith("CONFLICTING|")),
    }
    if pattern_counts != {
        "both_observed": 7690,
        "partial_or_mixed": 18481,
        "component_conflict": 3435,
    }:
        raise RuntimeError("Joint structural pattern counts changed")
    final_summary = (ROOT / "outputs/final_sample_qc/final_sample_qc_summary.md").read_text()
    if "The frozen cohort has 574 biological observations" not in final_summary:
        raise RuntimeError("Final transcriptomic cohort count changed")
    if sources["case"]["counts"]["structural_figures"] != 4:
        raise RuntimeError("Case-study figure count changed")
    for relative_path in FIGURE_PATHS:
        ET.parse(ROOT / relative_path)
        recorded = sources["case"]["artifacts"][relative_path]
        path = ROOT / relative_path
        if recorded["sha256"] != sha256_file(path) or recorded["size_bytes"] != path.stat().st_size:
            raise RuntimeError(f"Case-study figure no longer matches manifest: {relative_path}")
    return {**sources, "pattern_counts": pattern_counts}


def build_readme(sources: dict[str, Any]) -> bytes:
    registry_counts = sources["registry"]["counts"]
    text = f"""# LUAD Target Evidence Dossier

**A provenance-aware framework for representing heterogeneous LUAD target evidence without converting evidence availability into target quality.**

## Why this project?

Differential expression can reveal tumour-associated molecular changes, but it is not proof that a gene is a therapeutic target. Evidence from different databases may share upstream sources, while absent records may mean `MISSING`, `NOT_FOUND`, or `NOT_QUERIED` rather than biological absence. Compressing these distinctions too early can hide conflict, double-count dependent records, or create misleading certainty. This project therefore organizes evidence before any target-level decision is attempted.

> **How can heterogeneous target evidence be integrated while preserving provenance, missingness, dependency, conflict, and interpretation boundaries?**

## What I built

```text
Transcriptomic evidence
        +
Disease-association evidence
        ↓
Multi-component Evidence Landscape
        ↓
Evidence Summary
        ↓
Non-ordinal Structural Routing
        ↓
Representative Evidence-Pattern Dossiers
```

The framework converts frozen observations into traceable structural representations. This organization does not create new biological evidence or determine which target should be pursued.

## Project at a glance

| Governed layer | Frozen structural result |
|---|---:|
| Entity universe | **{sources['profile']['profile_count']:,}** immutable EnsemblID entities |
| Implemented evidence components | **{sources['profile']['component_count']}** |
| Final transcriptomic cohort | **574** biological observations |
| Transcriptomic component states | **26,171 `OBSERVED`** · **3,435 `CONFLICTING`** |
| Disease-association component states | **8,393 `OBSERVED`** · **713 `PARTIAL`** · **20,500 `MISSING`** |
| Joint structural patterns | **7,690** both components observed · **18,481** partial/mixed availability · **3,435** component conflict |
| Artifact Registry v0.1 | **{registry_counts['records']}** records · **{registry_counts['by_storage_class']['GIT_MANAGED']}** Git-managed · **{registry_counts['by_storage_class']['EXTERNAL_IMMUTABLE']}** external immutable references |

These counts describe representation states and artifact scale. They are not measures of evidence strength, target quality, or therapeutic value.

## Representative evidence patterns

The four examples below are deterministic structural representatives selected by the governed Task #036A/#036B process. They contain immutable EnsemblID identities only—no gene-symbol annotation or biological narrative.

<table>
  <tr>
    <td width="50%" valign="top">
      <strong>Complete pattern</strong><br>
      <sub>Complete ≠ best target</sub><br><br>
      <img src="figures/complete_evidence_pattern.svg" alt="Complete structural evidence pattern">
    </td>
    <td width="50%" valign="top">
      <strong>Partial pattern</strong><br>
      <sub>Partial ≠ negative evidence</sub><br><br>
      <img src="figures/partial_evidence_pattern.svg" alt="Partial structural evidence pattern">
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <strong>Conflict pattern</strong><br>
      <sub>Conflict ≠ failure</sub><br><br>
      <img src="figures/conflict_evidence_pattern.svg" alt="Conflicting structural evidence pattern">
    </td>
    <td width="50%" valign="top">
      <strong>Limitation pattern</strong><br>
      <sub>Limitation ≠ rejection</sub><br><br>
      <img src="figures/limitation_evidence_pattern.svg" alt="Structural limitation pattern">
    </td>
  </tr>
</table>

The figures expose component states, state-derived feature availability, provenance references, missingness, and preserved limitations; dependency detail remains governed upstream and is referenced rather than reconstructed here. See the [case-study communication specification](docs/case_study_communication_specification_v0.1.md) for the exact communication contract.

## What the framework preserves

- immutable EnsemblID identity;
- component and feature states;
- evidence-record provenance;
- source, snapshot, schema, and generator versions;
- dependency relationships and independence boundaries;
- explicit missingness semantics;
- limitation identifiers;
- deterministic rule traces.

## Reproducibility

The computational lifecycle is governed through versioned artifacts, frozen inputs, SHA256 integrity checks, deterministic regeneration, and explicit references to externally stored immutable payloads.

- [Reproducibility Report v0.1](docs/reproducibility_report_v0.1.md) defines what is computationally reproducible and what is not claimed.
- [Artifact Registry v0.1](outputs/artifact_registry_v0.1/artifact_registry.csv) records artifact identity, version, provenance, dependencies, storage class, size, and SHA256.
- Git-managed artifacts are validated directly; three large payload sets remain represented by immutable metadata references rather than copied into Git.
- Validation fails closed when frozen identity, lineage, state, schema, or artifact integrity changes unexpectedly.

## Interpretation boundaries

- **DE is not target proof.** Association does not establish causality or actionability.
- **Evidence representation is not ranking.** Structural availability does not establish comparative target quality.
- **Missing evidence is not negative evidence.** Missing, not-found, and not-queried states retain different meanings.
- **Routing categories are not priorities.** They are non-ordinal structural outcomes.
- **Computational validation is not biological validation.** Reproducible bytes and valid schemas do not demonstrate efficacy, safety, or clinical benefit.

This repository is not a clinical decision tool or a system for selecting or recommending targets.

## Documentation and communication

- [Project Overview v1.0](docs/project_overview_v1.0.md)
- [Reproducibility Report v0.1](docs/reproducibility_report_v0.1.md)
- [Release Notes v1.1](docs/release_notes_v1.1.md)
- [Scientific Specification v0.1](docs/scientific_spec_v0.1.md)
- [Case-study Communication Specification v0.1](docs/case_study_communication_specification_v0.1.md)
- [Architecture summary](outputs/presentation_artifacts_v0.1/architecture_summary.md)
- [Evidence-layer summary](outputs/presentation_artifacts_v0.1/evidence_layer_summary.csv)
- [Case-pattern summary](outputs/presentation_artifacts_v0.1/case_pattern_summary.csv)
- [Provenance-flow summary](outputs/presentation_artifacts_v0.1/provenance_flow_summary.md)

Documentation v1.1 is a forward-only public-facing maintenance release. The validated v1.0 documentation and Task #038A communication manifests remain unchanged historical records.
"""
    return text.encode("utf-8")


def build_release_notes(old_manifest: dict[str, Any], release_id: str) -> bytes:
    text = f"""# Release Notes v1.1

**Release:** Public README documentation v1.1
**Release ID:** `{release_id}`
**Release type:** Forward-only documentation maintenance
**Scientific artifact changes:** None

## Summary

Documentation v1.1 redesigns the GitHub landing page for rapid scientific review. It foregrounds the project question, architecture, frozen scale, representative evidence patterns, reproducibility model, and interpretation boundaries.

## Public-facing changes

- shortened the project title and added a one-sentence positioning statement;
- moved scientific motivation and the core integration question to the first screen;
- added a compact architecture and frozen project-scale table;
- embedded the four validated Task #038A structural SVGs in a two-by-two layout;
- made preservation guarantees, reproducibility controls, and interpretation boundaries easier to scan;
- retained links to detailed governance, reproducibility, communication, and presentation artifacts.

## Forward-only governance

Task #037D release `{old_manifest['documentation_release_id']}` freezes the historical README SHA256 `{HISTORICAL_README_SHA256}`. Task #038A also records that historical README as an input. Those manifests and all previously validated artifacts remain byte-unchanged.

The root README is intentionally superseded at the repository path by `PROJECT_DOCUMENTATION_V1.1`. Its historical bytes remain reconstructable from Git commit `{HISTORICAL_BASE_COMMIT}`. This release has a new manifest and identity; it does not rewrite the v1.0 manifest or imply that its old README hash matches the current path.

Artifact Registry v0.1 remains a frozen historical registry with 41 records. The v1.1 documentation artifacts are governed by their own manifest and are not silently inserted into that registry.

## Scientific boundary

This maintenance release does not rerun a workflow, rebuild a component, retrieve evidence, change an entity or state, add a biological narrative, or create an evaluative result. All displayed counts are reconciled to frozen upstream artifacts.

## Related documentation

- [Current README](../README.md)
- [Historical Release Notes v1.0](release_notes_v1.0.md)
- [Project Overview v1.0](project_overview_v1.0.md)
- [Reproducibility Report v0.1](reproducibility_report_v0.1.md)
- [Case-study Communication Specification v0.1](case_study_communication_specification_v0.1.md)
"""
    return text.encode("utf-8")


def validate_public_language(readme: bytes, release_notes: bytes) -> None:
    readme_text = readme.decode("utf-8")
    notes_text = release_notes.decode("utf-8")
    combined = (readme_text + "\n" + notes_text).lower()
    for phrase in PROHIBITED_PUBLIC_PHRASES:
        if phrase in combined:
            raise RuntimeError(f"Prohibited public wording detected: {phrase}")
    if readme_text.count(MANDATED_NEGATED_BOUNDARY) != 1:
        raise RuntimeError("The mandated complete-pattern non-claim must appear exactly once")
    if "best target" in notes_text.lower():
        raise RuntimeError("The complete-pattern non-claim may appear only in the README figure caption")
    required_boundaries = (
        "Partial ≠ negative evidence",
        "Conflict ≠ failure",
        "Limitation ≠ rejection",
        "DE is not target proof",
        "Evidence representation is not ranking",
        "Missing evidence is not negative evidence",
        "Routing categories are not priorities",
        "Computational validation is not biological validation",
    )
    for value in required_boundaries:
        if value not in readme_text:
            raise RuntimeError(f"Required interpretation boundary missing: {value}")


def validate_links(readme: bytes, release_notes: bytes, generated: set[Path]) -> int:
    total = 0
    for source_path, payload in ((README_PATH, readme), (RELEASE_NOTES_PATH, release_notes)):
        text = payload.decode("utf-8")
        targets = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
        targets += re.findall(r"<(?:img|a)\b[^>]*(?:src|href)=\"([^\"]+)\"", text)
        for target in targets:
            if target.startswith(("http://", "https://", "#")):
                raise RuntimeError(f"Unexpected external link: {target}")
            resolved = (source_path.parent / target).resolve()
            if not resolved.exists() and resolved not in generated:
                raise RuntimeError(f"Unresolved local link in {source_path.name}: {target}")
            total += 1
    return total


def build_session_info() -> bytes:
    lines = [
        "activity=PUBLIC_README_DOCUMENTATION_MAINTENANCE",
        f"project_id={PROJECT_ID}",
        f"documentation_version={DOCUMENTATION_VERSION}",
        f"generator_version={GENERATOR_VERSION}",
        f"historical_base_commit={HISTORICAL_BASE_COMMIT}",
        f"python_version={platform.python_version()}",
        f"python_implementation={platform.python_implementation()}",
        "standard_library_only=TRUE",
        "network_api_access=PROHIBITED_NOT_USED",
        "scientific_workflow_rerun=FALSE",
        "component_rebuild=FALSE",
        "evidence_regeneration=FALSE",
        "external_payload_bytes_copied=FALSE",
        "runtime_ai_decisions=PROHIBITED_NONE_USED",
        "biological_interpretation_added=FALSE",
        "evaluative_outputs_generated=FALSE",
        "randomness=NOT_USED",
        "wall_clock_governed_values=NOT_USED",
        "deterministic_generation=BYTE_IDENTICAL",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def artifact_entry(payload: bytes) -> dict[str, Any]:
    return {"size_bytes": len(payload), "sha256": sha256_bytes(payload)}


def build_validation_report(release_id: str, link_count: int) -> bytes:
    text = f"""# Public README Documentation v1.1 Validation

**Release ID:** `{release_id}`
**Validation status:** PASS

## Governance

- PASS — forward-only version bump applied because v1.0 and Task #038A freeze the historical README hash
- PASS — historical README reconstructed from Git commit `{HISTORICAL_BASE_COMMIT}`
- PASS — Task #037D v1.0, Task #038A, and all {len(FROZEN_INPUTS)} direct frozen inputs remained byte-unchanged
- PASS — Artifact Registry v0.1 preserved as a 41-record historical registry

## Content and rendering

- PASS — required scientific story, architecture, scale, reproducibility, and interpretation boundaries present
- PASS — all displayed counts reconciled to frozen cohort, profile, routing, and registry artifacts
- PASS — four case identities and SVG hashes reconciled to Task #038A
- PASS — four SVG files parse and are referenced in a GitHub-compatible two-by-two HTML layout
- PASS — {link_count} local Markdown/HTML links resolve
- PASS — prohibited public wording scan passed; the required complete-pattern phrase appears once as an explicit negated non-claim
- PASS — two complete documentation generations are byte-identical

## Public-release safety boundary

- PASS — no scientific workflow rerun, component rebuild, evidence regeneration, network/API retrieval, evaluative result, or biological interpretation
- PASS — no external payload bytes copied into Git; generated documentation files are below 100 MB

Repository-wide credential-pattern scanning and final Git checks are reported separately at handoff because they inspect the completed working tree rather than generate documentation bytes.
"""
    return text.encode("utf-8")


def build_all() -> tuple[dict[Path, bytes], str]:
    validate_frozen_inputs()
    historical = validate_historical_boundary()
    sources = load_sources()
    release_seed = {
        "documentation_version": DOCUMENTATION_VERSION,
        "supersedes": historical["old_manifest"]["documentation_release_id"],
        "case_communication_release": sources["case"]["communication_release_id"],
        "historical_base_commit": HISTORICAL_BASE_COMMIT,
    }
    release_id = stable_id("DOCRLS", release_seed)
    readme = build_readme(sources)
    notes = build_release_notes(historical["old_manifest"], release_id)
    validate_public_language(readme, notes)
    generated = {README_PATH, RELEASE_NOTES_PATH}
    link_count = validate_links(readme, notes, generated)
    session = build_session_info()
    validation = build_validation_report(release_id, link_count)

    manifest = {
        "manifest_type": "FORWARD_ONLY_DOCUMENTATION_PATCH_MANIFEST",
        "project_id": PROJECT_ID,
        "patch_type": PATCH_TYPE,
        "documentation_release_id": release_id,
        "documentation_version": DOCUMENTATION_VERSION,
        "documentation_status": "VALIDATED_PUBLIC_DOCUMENTATION_CANDIDATE",
        "supersedes": {
            "documentation_release_id": historical["old_manifest"]["documentation_release_id"],
            "documentation_version": historical["old_manifest"]["documentation_version"],
            "manifest_path": "outputs/final_release_documentation_v1.0/final_release_manifest.json",
            "manifest_sha256": FROZEN_INPUTS[
                "outputs/final_release_documentation_v1.0/final_release_manifest.json"
            ],
            "historical_readme_sha256": HISTORICAL_README_SHA256,
            "historical_readme_git_commit": HISTORICAL_BASE_COMMIT,
        },
        "source_releases": {
            "case_study_communication_release_id": sources["case"]["communication_release_id"],
            "profile_integration_release_id": sources["profile"]["integration_release_id"],
            "structural_routing_release_id": sources["routing"]["release_id"],
            "artifact_registry_id": sources["registry"]["registry_id"],
        },
        "documentation_artifacts": {
            "README.md": artifact_entry(readme),
            "docs/release_notes_v1.1.md": artifact_entry(notes),
            "outputs/final_release_documentation_v1.1/validation_report.md": artifact_entry(
                validation
            ),
            "outputs/final_release_documentation_v1.1/session_info.txt": artifact_entry(session),
        },
        "generator": {
            "relative_path": "analysis/generate_public_readme_v1_1.py",
            "generator_version": GENERATOR_VERSION,
            "sha256": sha256_file(Path(__file__).resolve()),
        },
        "frozen_inputs": dict(sorted(FROZEN_INPUTS.items())),
        "validation": {
            "forward_only_versioning": "PASS",
            "historical_release_preserved": "PASS",
            "frozen_input_hashes_unchanged": "PASS",
            "frozen_count_reconciliation": "PASS",
            "svg_reference_validation": "PASS",
            "markdown_html_links_resolved": link_count,
            "public_wording_validation": "PASS",
            "deterministic_generation": "BYTE_IDENTICAL",
            "scientific_artifacts_modified": False,
            "external_payload_bytes_copied": False,
            "network_api_access_used": False,
            "runtime_ai_decisions_used": False,
        },
        "validation_status": "PASS",
    }
    payloads = {
        README_PATH: readme,
        RELEASE_NOTES_PATH: notes,
        VALIDATION_PATH: validation,
        SESSION_PATH: session,
        MANIFEST_PATH: canonical_json(manifest),
    }
    return payloads, release_id


def write_payloads(payloads: dict[Path, bytes]) -> None:
    expected = {README_PATH, RELEASE_NOTES_PATH, MANIFEST_PATH, VALIDATION_PATH, SESSION_PATH}
    if set(payloads) != expected:
        raise RuntimeError("Documentation output path contract changed")
    for path, payload in payloads.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)


def main() -> None:
    validate_worktree_scope()
    first, release_id = build_all()
    second, second_release_id = build_all()
    if release_id != second_release_id or first != second:
        raise RuntimeError("Two complete documentation generations were not byte-identical")
    write_payloads(first)
    validate_frozen_inputs()
    validate_worktree_scope()
    for path, payload in first.items():
        if path.read_bytes() != payload:
            raise RuntimeError(f"Written documentation differs from generated bytes: {path}")
        if path.stat().st_size > 100_000_000:
            raise RuntimeError(f"Generated documentation exceeds 100 MB: {path}")
    print(f"documentation_release_id={release_id}")
    print(f"documentation_version={DOCUMENTATION_VERSION}")
    print("forward_only_version_bump=TRUE")
    print("historical_release_preserved=PASS")
    print("deterministic_generation=BYTE_IDENTICAL")
    print("validation_status=PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
