#!/usr/bin/env python3
"""Generate deterministic, interpretation-safe case-study communication artifacts.

Task #038A is a structural communication projection only. It reads frozen
Task #036A/#036B/#036C/#037D artifacts and does not retrieve evidence, rebuild
case dossiers, use gene symbols, or make target-level scientific judgements.
"""

from __future__ import annotations

import csv
import hashlib
import html
import io
import json
import platform
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GENERATOR_VERSION = "CASE_STUDY_COMMUNICATION_GENERATOR_V0.1"
COMMUNICATION_VERSION = "CASE_STUDY_COMMUNICATION_V0.1"
PROJECT_ID = "LUAD_EXPRESSION_DRUGGABLE_TARGET_EVIDENCE_DOSSIER"
TASK_ID = "TASK_038A"

DOC_PATH = ROOT / "docs/case_study_communication_specification_v0.1.md"
OUTPUT_DIR = ROOT / "outputs/case_study_communication_v0.1"
FIGURE_DIR = ROOT / "figures"

CASE_ORDER = (
    "CASE_COMPLETE_PATTERN",
    "CASE_PARTIAL_PATTERN",
    "CASE_CONFLICT_PATTERN",
    "CASE_LIMITATION_PATTERN",
)

CASE_PRESENTATION = {
    "CASE_COMPLETE_PATTERN": {
        "label": "Complete evidence pattern",
        "boundary": "Complete evidence ≠ best target",
        "accent": "#2F6B5F",
        "figure": "complete_evidence_pattern.svg",
    },
    "CASE_PARTIAL_PATTERN": {
        "label": "Partial evidence pattern",
        "boundary": "Partial evidence ≠ negative evidence",
        "accent": "#A86115",
        "figure": "partial_evidence_pattern.svg",
    },
    "CASE_CONFLICT_PATTERN": {
        "label": "Conflict evidence pattern",
        "boundary": "Conflict ≠ failure",
        "accent": "#8A3D6D",
        "figure": "conflict_evidence_pattern.svg",
    },
    "CASE_LIMITATION_PATTERN": {
        "label": "Limitation evidence pattern",
        "boundary": "Limitation ≠ rejection",
        "accent": "#5B5F97",
        "figure": "limitation_evidence_pattern.svg",
    },
}

FEATURE_AVAILABILITY_BY_STATE = {
    "OBSERVED": "OBSERVATION_STRUCTURE_AVAILABLE",
    "PARTIAL": "PARTIAL_OBSERVATION_STRUCTURE_AVAILABLE",
    "CONFLICTING": "CONFLICTING_OBSERVATION_STRUCTURE_AVAILABLE",
    "MISSING": "SOURCE_COMPONENT_STATE_MISSING",
    "NOT_QUERIED": "SOURCE_COMPONENT_STATE_NOT_QUERIED",
}

PROHIBITED_FIELD_NAMES = {
    "best_target",
    "top_target",
    "rank",
    "ranking",
    "score",
    "priority_score",
    "recommendation",
    "target_quality",
    "evidence_strength",
}

# Directly frozen Task #036A/#036B/#036C/#037D inputs.
FROZEN_INPUTS = {
    "analysis/36A_define_case_selection_schema.py": "eae4d7c5af3509462f8c3317a831db417c586a4c495e24c65f7815bf76eaba0e",
    "docs/governance/case_study_selection_framework_v0.1.md": "c269af2bfe9afd8f33fb1e2f107dc9e563f58ab6648ac66fca2816af2a8fd109",
    "docs/governance/case_study_selection_rule_catalog_v0.1.md": "a81289a329675206db25c5f3b79d8d2c870e95b32e147dc03e7dfc36cb3bf31a",
    "docs/governance/case_study_selection_validation_requirements_v0.1.md": "5ed8a2086135e712218e76d4ce556ae07e37c7ed049f8bf88feefab3a94290f9",
    "schemas/case_study_selection_schema_v0.1.json": "d76da88675e63fb13f9cb59ad1b1e2df5895c22d5862987c4dc6d7818acaeffa",
    "analysis/36B_generate_case_dossiers.py": "5b8d0c30f2f660faa069db4eb48716f03ca1e1681fe33e02f5f81ca95450e6f6",
    "outputs/case_dossiers_v0.1/case_dossiers.json": "d861e2500797ae9351f70e474c8a8acafa51d30481357aa450d1d77314bd27b8",
    "outputs/case_dossiers_v0.1/case_selection_index.csv": "f11892cc59d1fc3b042e79b4859e293677d9befbe975dd9d6635e0033011bc52",
    "outputs/case_dossiers_v0.1/dossier_manifest.json": "9039d3523bf52841239dce9ab880a98a3e2dcd5dfff3a87cece10c986067678b",
    "outputs/case_dossiers_v0.1/validation_report.md": "8ca6bc43b72fd653924b75eb9c5429e90cc82477908a1d17877bd7f5776fbbc3",
    "outputs/case_dossiers_v0.1/session_info.txt": "0cae68b33106ff97512e39ade11059701dfa8dfc847eb5db47bd7b04c3e0572f",
    "analysis/36C_generate_presentation_artifacts.py": "5eaa4df64a10515c99dbb97fcdb08da265ce0d60e90fb73846d5f881f9f8171e",
    "outputs/presentation_artifacts_v0.1/architecture_summary.md": "e1f99162ccd69701d8f446ff56210142e56e11d3ada164a8b785aaff9ac535fc",
    "outputs/presentation_artifacts_v0.1/case_pattern_summary.csv": "e03c9fb080e62e435a0d4fcf328715fa3f2a503829c79272f84a3b8a68da6d7d",
    "outputs/presentation_artifacts_v0.1/evidence_layer_summary.csv": "0b30b5454c3d963b22b17c2ea35e776d2fa38ef805f5fe8c54bbf7599677abda",
    "outputs/presentation_artifacts_v0.1/presentation_manifest.json": "2bf7acce12685399476e50cfa26df049d8b54cc371e6dde6794b656b12f1d2e4",
    "outputs/presentation_artifacts_v0.1/provenance_flow_summary.md": "57885dccc7f07922a9cfec9f6d48c385dfb49e0bc745003d9fc9efabd9365f56",
    "outputs/presentation_artifacts_v0.1/validation_report.md": "2237c292ab827f4396b3db4220321d1d5c626120104ce1f03cccfdbc2eb21f22",
    "outputs/presentation_artifacts_v0.1/session_info.txt": "d6b6a2270a466d487db96572ca274be350042849e360d0870916ebd90bef6738",
    "README.md": "5bd5bdaf54ee7f12e6c169db8049bb3b9c77b0b02bb186d5ff418e5d7a60af77",
    "analysis/37D_generate_project_documentation.py": "530b9c0508159ac2899eefd02c0e597037a94298dafabf3bb891e7f4a3a5bcc3",
    "docs/project_overview_v1.0.md": "a35819c02c6f02a253973eb38bc30a12e5da0915ce234d7ece4ce1b15ba3946c",
    "docs/release_notes_v1.0.md": "66ec903597964f5f5fde325b9d20cc074d7489e7279ee9494687bc53552eca41",
    "outputs/final_release_documentation_v1.0/final_release_manifest.json": "87e706362b41156c5b3054f96c40b45a6a9744c59f900815dc83df18bd2f63b5",
    "outputs/final_release_documentation_v1.0/validation_report.md": "10f376bf245761d0af784989840afc9fb09eea44719994018a20406e45171e9f",
    "outputs/final_release_documentation_v1.0/session_info.txt": "647cf623bcf66a5a48f9decf7fc4d2cd75189b6c7b6177951f698f7fd3b047a4",
}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def verify_frozen_inputs() -> None:
    failures: list[str] = []
    for relative_path, expected_hash in FROZEN_INPUTS.items():
        path = ROOT / relative_path
        if not path.is_file():
            failures.append(f"missing frozen input: {relative_path}")
        elif sha256_file(path) != expected_hash:
            failures.append(f"frozen input hash mismatch: {relative_path}")
    if failures:
        raise RuntimeError("Frozen-input validation failed:\n- " + "\n- ".join(failures))


def load_json(relative_path: str) -> Any:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def load_csv(relative_path: str) -> list[dict[str, str]]:
    with (ROOT / relative_path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def flatten_limitations(dossier: dict[str, Any]) -> list[str]:
    ordered: list[str] = []
    for value in dossier["limitation_identifiers"]:
        if value not in ordered:
            ordered.append(value)
    for component in dossier["component_state_snapshot"]:
        for value in component["limitation_identifiers"]:
            if value not in ordered:
                ordered.append(value)
    return ordered


def normalize_cases(
    dossier_payload: dict[str, Any],
    dossier_index: list[dict[str, str]],
    presentation_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    slots = dossier_payload["case_slots"]
    by_category = {slot["case_category"]: slot for slot in slots}
    index_by_category = {row["case_category"]: row for row in dossier_index}
    presentation_by_category = {row["case_category"]: row for row in presentation_rows}
    if tuple(by_category) != CASE_ORDER:
        raise RuntimeError("Case dossier category order does not match the frozen Task #036A order")
    if set(index_by_category) != set(CASE_ORDER) or set(presentation_by_category) != set(CASE_ORDER):
        raise RuntimeError("Task #036B/#036C case-category coverage mismatch")

    records: list[dict[str, Any]] = []
    for category in CASE_ORDER:
        slot = by_category[category]
        if slot["selection_status"] != "FILLED" or not isinstance(slot.get("dossier"), dict):
            raise RuntimeError(f"Communication v0.1 requires the frozen filled case slot: {category}")
        dossier = slot["dossier"]
        index_row = index_by_category[category]
        presentation_row = presentation_by_category[category]
        source_priority = dossier["source_prioritization_identity"]
        source_summary = source_priority["source_summary_identity"]
        components = {item["component_id"]: item for item in dossier["component_state_snapshot"]}
        expected_components = {"COMP_TRANSCRIPTOMIC_EVIDENCE", "COMP_DISEASE_ASSOCIATION"}
        if set(components) != expected_components:
            raise RuntimeError(f"Unexpected component set for {category}")

        # Reconcile the two Task #036B representations and Task #036C projection.
        checks = {
            "EnsemblID": dossier["EnsemblID"],
            "case_selection_id": dossier["case_selection_id"],
            "case_rule_id": slot["case_rule_id"],
            "source_prioritization_representation_id": source_priority["prioritization_representation_id"],
            "source_evidence_summary_id": source_summary["evidence_summary_id"],
        }
        for field, expected in checks.items():
            index_field = field if field in index_row else "selected_EnsemblID"
            if index_row[index_field] != expected:
                raise RuntimeError(f"Task #036B index reconciliation failed for {category}: {field}")
        if presentation_row["selected_EnsemblID"] != dossier["EnsemblID"]:
            raise RuntimeError(f"Task #036C identity reconciliation failed for {category}")

        component_records = [components[name] for name in (
            "COMP_TRANSCRIPTOMIC_EVIDENCE",
            "COMP_DISEASE_ASSOCIATION",
        )]
        for component in component_records:
            if component["component_state"] not in FEATURE_AVAILABILITY_BY_STATE:
                raise RuntimeError(f"Unsupported governed state in {category}")

        records.append(
            {
                "case_category": category,
                "case_pattern_label": CASE_PRESENTATION[category]["label"],
                "communication_boundary": CASE_PRESENTATION[category]["boundary"],
                "EnsemblID": dossier["EnsemblID"],
                "universe_ordinal": int(dossier["universe_ordinal"]),
                "case_selection_id": dossier["case_selection_id"],
                "case_rule_id": slot["case_rule_id"],
                "structural_reason_code": slot["structural_reason_code"],
                "selection_method_id": slot["selection_method_id"],
                "selection_token_sha256": dossier["case_selection"]["selection_token_sha256"],
                "source_prioritization_representation_id": source_priority["prioritization_representation_id"],
                "source_prioritization_content_sha256": source_priority["prioritization_content_sha256"],
                "source_evidence_summary_id": source_summary["evidence_summary_id"],
                "source_evidence_summary_content_sha256": source_summary["evidence_summary_content_sha256"],
                "components": component_records,
                "feature_availability": {
                    component["component_id"]: FEATURE_AVAILABILITY_BY_STATE[component["component_state"]]
                    for component in component_records
                },
                "provenance_references": [
                    *(component["source_component_record_id"] for component in component_records),
                    source_summary["evidence_summary_id"],
                    source_priority["prioritization_representation_id"],
                    dossier["case_selection_id"],
                ],
                "dependency_representation": "SOURCE_EVIDENCE_SUMMARY_REFERENCE_ONLY",
                "limitations": flatten_limitations(dossier),
                "figure_path": f"figures/{CASE_PRESENTATION[category]['figure']}",
            }
        )
    return records


def build_specification() -> bytes:
    text = """# Case Study Communication Specification v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Task:** #038A  
**Version:** `CASE_STUDY_COMMUNICATION_V0.1`  
**Status:** Structural scientific communication layer

## 1. Purpose

This specification governs the deterministic transformation of the four frozen Task #036B representative case dossiers into human-readable tables and figures for presentations, posters, and project documentation. The communication artifacts expose evidence structure; they do not add evidence or interpret target biology.

The selected EnsemblID identities remain deterministic structural representatives. They are not preferred, optimal, validated, or recommended targets.

## 2. Frozen source relationship

```text
Task #036A case-pattern governance
                ↓
Task #036B deterministic representative dossier
                ↓
Task #036C structural communication context
                ↓
Task #038A case-study communication view
```

Task #038A may copy or structurally label only fields already present in the frozen dossiers. It must not rebuild selection, access earlier payloads to enrich a case, retrieve evidence, add gene symbols, or introduce biological narratives.

## 3. Communication cases

Exactly four governed slots are communicated in frozen Task #036A order:

1. `CASE_COMPLETE_PATTERN`;
2. `CASE_PARTIAL_PATTERN`;
3. `CASE_CONFLICT_PATTERN`;
4. `CASE_LIMITATION_PATTERN`.

Every artifact must communicate these interpretation boundaries verbatim:

- **Complete evidence ≠ best target**
- **Partial evidence ≠ negative evidence**
- **Conflict ≠ failure**
- **Limitation ≠ rejection**

The cases remain non-ordinal. Their category-salted SHA256 tokens are deterministic sampling devices and must not be used for cross-case ordering.

## 4. Required communication fields

Each case row and figure preserves:

- immutable `EnsemblID` and canonical universe ordinal;
- case category, case-selection ID, case rule, structural reason code, and deterministic selection method;
- component IDs, versions, states, and source component-record IDs;
- a bounded feature-availability label derived only from each frozen component state;
- source Evidence Summary and prioritization representation identities;
- all summary-level and component-level limitation identifiers.

## 5. Feature-availability boundary

Task #036B dossiers expose component states but do not expose record-level feature inventories. Therefore v0.1 uses this fixed structural communication map only:

| Frozen component state | Communication label |
|---|---|
| `OBSERVED` | `OBSERVATION_STRUCTURE_AVAILABLE` |
| `PARTIAL` | `PARTIAL_OBSERVATION_STRUCTURE_AVAILABLE` |
| `CONFLICTING` | `CONFLICTING_OBSERVATION_STRUCTURE_AVAILABLE` |
| `MISSING` | `SOURCE_COMPONENT_STATE_MISSING` |
| `NOT_QUERIED` | `SOURCE_COMPONENT_STATE_NOT_QUERIED` |

These labels do not reconstruct features, measure evidence quantity, or convert missingness into negative evidence.

## 6. Provenance and dependency communication

The communication lineage is:

```text
source component-record references
                ↓
source Evidence Summary identity
                ↓
source prioritization representation identity
                ↓
frozen case-selection identity
```

Task #036B dossiers do not expose dependency-edge inventories. Figures must state `SOURCE_EVIDENCE_SUMMARY_REFERENCE_ONLY` and point to the frozen Evidence Summary identity. No dependency edge may be invented, flattened, counted as an independent vote, or inferred from component state.

## 7. Figure contract

Each communication-ready SVG must:

- display one exact EnsemblID structural representative;
- show both component identities, versions, states, and feature-availability labels;
- show provenance references and preserved limitations;
- disclose the dependency-detail boundary;
- use controlled state labels without desirability ordering;
- include an accessible SVG title and description;
- contain no external font, script, network resource, or mutable reference.

The four deterministic figures are:

- [Complete evidence pattern](../figures/complete_evidence_pattern.svg)
- [Partial evidence pattern](../figures/partial_evidence_pattern.svg)
- [Conflict evidence pattern](../figures/conflict_evidence_pattern.svg)
- [Limitation evidence pattern](../figures/limitation_evidence_pattern.svg)

## 8. Prohibitions

The communication layer must not retrieve evidence, access APIs, regenerate upstream artifacts, add gene symbols, create biological narratives, recommend targets, or introduce target scores, ranks, priorities, confidence estimates, evidence-strength measures, or runtime AI/LLM decisions.

Visual emphasis and color distinguish pattern types only; they must not encode quality, desirability, or priority.

## 9. Validation

Generation must validate:

- exact Task #036A/#036B/#036C/#037D frozen hashes;
- reconciliation of dossier, index, and presentation identities;
- exact component-state, provenance-reference, and limitation fidelity;
- the fixed feature-availability mapping;
- explicit dependency-detail boundaries;
- well-formed, self-contained SVG output;
- recursive prohibited-field absence from structured outputs;
- resolution of local Markdown links;
- two byte-identical complete generations;
- no network access or runtime AI decisions.

Structural and computational validation does not constitute biological validation.

## 10. Related artifacts

- [Case Study Selection Framework v0.1](governance/case_study_selection_framework_v0.1.md)
- [Case Study Selection Rule Catalog v0.1](governance/case_study_selection_rule_catalog_v0.1.md)
- [Task #036B case dossiers](../outputs/case_dossiers_v0.1/case_dossiers.json)
- [Task #036C presentation artifacts](../outputs/presentation_artifacts_v0.1/presentation_manifest.json)
- [Project Overview v1.0](project_overview_v1.0.md)
"""
    return text.encode("utf-8")


def build_summary_csv(records: list[dict[str, Any]]) -> bytes:
    fieldnames = [
        "case_category",
        "case_pattern_label",
        "EnsemblID",
        "universe_ordinal",
        "case_selection_id",
        "case_rule_id",
        "structural_reason_code",
        "selection_method_id",
        "selection_token_sha256",
        "transcriptomic_component_id",
        "transcriptomic_component_version",
        "transcriptomic_component_state",
        "transcriptomic_feature_availability",
        "transcriptomic_source_component_record_id",
        "disease_association_component_id",
        "disease_association_component_version",
        "disease_association_component_state",
        "disease_association_feature_availability",
        "disease_association_source_component_record_id",
        "source_evidence_summary_id",
        "source_prioritization_representation_id",
        "provenance_references",
        "dependency_representation",
        "limitation_identifiers",
        "communication_boundary",
        "figure_path",
    ]
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for record in records:
        components = {item["component_id"]: item for item in record["components"]}
        transcriptomic = components["COMP_TRANSCRIPTOMIC_EVIDENCE"]
        disease = components["COMP_DISEASE_ASSOCIATION"]
        writer.writerow(
            {
                "case_category": record["case_category"],
                "case_pattern_label": record["case_pattern_label"],
                "EnsemblID": record["EnsemblID"],
                "universe_ordinal": record["universe_ordinal"],
                "case_selection_id": record["case_selection_id"],
                "case_rule_id": record["case_rule_id"],
                "structural_reason_code": record["structural_reason_code"],
                "selection_method_id": record["selection_method_id"],
                "selection_token_sha256": record["selection_token_sha256"],
                "transcriptomic_component_id": transcriptomic["component_id"],
                "transcriptomic_component_version": transcriptomic["component_version"],
                "transcriptomic_component_state": transcriptomic["component_state"],
                "transcriptomic_feature_availability": record["feature_availability"][transcriptomic["component_id"]],
                "transcriptomic_source_component_record_id": transcriptomic["source_component_record_id"],
                "disease_association_component_id": disease["component_id"],
                "disease_association_component_version": disease["component_version"],
                "disease_association_component_state": disease["component_state"],
                "disease_association_feature_availability": record["feature_availability"][disease["component_id"]],
                "disease_association_source_component_record_id": disease["source_component_record_id"],
                "source_evidence_summary_id": record["source_evidence_summary_id"],
                "source_prioritization_representation_id": record["source_prioritization_representation_id"],
                "provenance_references": "|".join(record["provenance_references"]),
                "dependency_representation": record["dependency_representation"],
                "limitation_identifiers": "|".join(record["limitations"]),
                "communication_boundary": record["communication_boundary"],
                "figure_path": record["figure_path"],
            }
        )
    return handle.getvalue().encode("utf-8")


def xml_text(value: Any) -> str:
    return html.escape(str(value), quote=True)


def state_colors(state: str) -> tuple[str, str]:
    return {
        "OBSERVED": ("#DCEFE9", "#244E45"),
        "PARTIAL": ("#F6E8CE", "#71450D"),
        "CONFLICTING": ("#F2DCE8", "#6D2F56"),
        "MISSING": ("#E8EBEF", "#4D5662"),
        "NOT_QUERIED": ("#E6E3F0", "#504A6B"),
    }[state]


def wrap_identifiers(values: list[str], max_chars: int = 105) -> list[str]:
    lines: list[str] = []
    current = ""
    for value in values:
        candidate = value if not current else f"{current}  •  {value}"
        if current and len(candidate) > max_chars:
            lines.append(current)
            current = value
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def build_svg(record: dict[str, Any]) -> bytes:
    presentation = CASE_PRESENTATION[record["case_category"]]
    components = record["components"]
    limitation_lines = wrap_identifiers(record["limitations"])
    component_blocks: list[str] = []
    for x, component in zip((60, 710), components, strict=True):
        fill, text_color = state_colors(component["component_state"])
        availability = record["feature_availability"][component["component_id"]]
        short_name = (
            "Transcriptomic evidence"
            if component["component_id"] == "COMP_TRANSCRIPTOMIC_EVIDENCE"
            else "Disease association"
        )
        component_blocks.append(
            f"""
  <g>
    <rect x="{x}" y="180" width="630" height="170" rx="18" fill="#FFFFFF" stroke="#CBD3DC" stroke-width="2"/>
    <text x="{x + 28}" y="218" class="component-title">{xml_text(short_name)}</text>
    <text x="{x + 28}" y="247" class="mono muted">{xml_text(component['component_version'])}</text>
    <rect x="{x + 28}" y="268" width="170" height="42" rx="21" fill="{fill}"/>
    <text x="{x + 113}" y="295" text-anchor="middle" class="state" fill="{text_color}">{xml_text(component['component_state'])}</text>
    <text x="{x + 220}" y="285" class="label">FEATURE AVAILABILITY</text>
    <text x="{x + 220}" y="307" class="mono small">{xml_text(availability)}</text>
    <text x="{x + 28}" y="334" class="mono tiny">record: {xml_text(component['source_component_record_id'])}</text>
  </g>"""
        )

    limitation_tspans = "\n".join(
        f'    <tspan x="82" dy="{0 if index == 0 else 22}">{xml_text(line)}</tspan>'
        for index, line in enumerate(limitation_lines)
    )
    description = (
        f"Structural representative {record['EnsemblID']} for {record['case_category']}; "
        "shows component states, state-derived feature availability, provenance references, "
        "dependency disclosure, and preserved limitations without biological interpretation."
    )
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="900" viewBox="0 0 1400 900" role="img" aria-labelledby="title desc">
  <title id="title">{xml_text(presentation['label'])}: {xml_text(record['EnsemblID'])}</title>
  <desc id="desc">{xml_text(description)}</desc>
  <style>
    text {{ font-family: Arial, Helvetica, sans-serif; fill: #172333; }}
    .eyebrow {{ font-size: 15px; font-weight: 700; letter-spacing: 1.5px; }}
    .title {{ font-size: 34px; font-weight: 700; }}
    .entity {{ font-size: 18px; font-weight: 600; }}
    .boundary {{ font-size: 20px; font-weight: 700; fill: #FFFFFF; }}
    .component-title {{ font-size: 23px; font-weight: 700; }}
    .state {{ font-size: 17px; font-weight: 700; }}
    .label {{ font-size: 12px; font-weight: 700; letter-spacing: 0.8px; fill: #5D6875; }}
    .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 14px; }}
    .small {{ font-size: 12px; }}
    .tiny {{ font-size: 11px; fill: #5D6875; }}
    .muted {{ fill: #5D6875; }}
    .section-title {{ font-size: 16px; font-weight: 700; }}
    .body {{ font-size: 14px; }}
    .limitation {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 12px; fill: #394656; }}
  </style>
  <rect width="1400" height="900" fill="#F5F7FA"/>
  <rect x="0" y="0" width="18" height="900" fill="{presentation['accent']}"/>
  <text x="60" y="55" class="eyebrow" fill="{presentation['accent']}">STRUCTURAL CASE COMMUNICATION · TASK #038A</text>
  <text x="60" y="100" class="title">{xml_text(presentation['label'])}</text>
  <text x="60" y="132" class="entity">Entity: {xml_text(record['EnsemblID'])} · canonical ordinal {record['universe_ordinal']}</text>
  <rect x="980" y="48" width="360" height="74" rx="14" fill="{presentation['accent']}"/>
  <text x="1160" y="92" text-anchor="middle" class="boundary">{xml_text(presentation['boundary'])}</text>
  {''.join(component_blocks)}
  <rect x="60" y="375" width="1280" height="126" rx="18" fill="#FFFFFF" stroke="#CBD3DC" stroke-width="2"/>
  <text x="82" y="408" class="section-title">PROVENANCE FLOW</text>
  <text x="82" y="437" class="mono small">component records → {xml_text(record['source_evidence_summary_id'])}</text>
  <text x="82" y="461" class="mono small">→ {xml_text(record['source_prioritization_representation_id'])}</text>
  <text x="82" y="485" class="mono small">→ {xml_text(record['case_selection_id'])}</text>
  <text x="980" y="408" class="label">STRUCTURAL REASON</text>
  <text x="980" y="434" class="mono small">{xml_text(record['structural_reason_code'])}</text>
  <text x="980" y="468" class="label">DETERMINISTIC SELECTION</text>
  <text x="980" y="491" class="mono tiny">{xml_text(record['selection_method_id'])}</text>
  <rect x="60" y="525" width="1280" height="92" rx="18" fill="#EEF2F6" stroke="#CBD3DC" stroke-width="2"/>
  <text x="82" y="557" class="section-title">DEPENDENCY TRANSPARENCY</text>
  <text x="82" y="584" class="mono small">{xml_text(record['dependency_representation'])}</text>
  <text x="690" y="584" class="body">Dependency edges are not exposed by the frozen dossier; no independence claim is added.</text>
  <rect x="60" y="641" width="1280" height="150" rx="18" fill="#FFFFFF" stroke="#CBD3DC" stroke-width="2"/>
  <text x="82" y="674" class="section-title">PRESERVED LIMITATION IDENTIFIERS</text>
  <text x="82" y="704" class="limitation">
{limitation_tspans}
  </text>
  <line x1="60" y1="822" x2="1340" y2="822" stroke="#CBD3DC"/>
  <text x="60" y="852" class="body">State labels describe evidence structure only. Missingness is preserved; dependent records are not independent votes.</text>
  <text x="60" y="878" class="mono tiny">{xml_text(record['case_rule_id'])} · {xml_text(record['case_category'])}</text>
</svg>
"""
    return svg.encode("utf-8")


def scan_prohibited_keys(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in PROHIBITED_FIELD_NAMES:
                raise RuntimeError(f"Prohibited structured field at {path}.{key}")
            scan_prohibited_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_prohibited_keys(child, f"{path}[{index}]")


def validate_svg(payload: bytes, record: dict[str, Any]) -> None:
    root = ET.fromstring(payload)
    if root.tag != "{http://www.w3.org/2000/svg}svg":
        raise RuntimeError("Figure is not an SVG root")
    text = payload.decode("utf-8")
    required = [
        record["EnsemblID"],
        record["communication_boundary"],
        record["source_evidence_summary_id"],
        record["source_prioritization_representation_id"],
        record["dependency_representation"],
        *record["limitations"],
    ]
    for value in required:
        if value not in text:
            raise RuntimeError(f"Figure omitted required structural value: {value}")
    if re.search(r"<(script|image|foreignObject)\b", text, flags=re.IGNORECASE):
        raise RuntimeError("Figure contains a prohibited external/runtime-capable SVG element")
    if re.search(r"(?:href|src)\s*=", text, flags=re.IGNORECASE):
        raise RuntimeError("Figure contains an external reference")


def validate_markdown_links(payload: bytes, generated_paths: set[Path]) -> int:
    text = payload.decode("utf-8")
    targets = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
    resolved = 0
    for target in targets:
        if target.startswith(("http://", "https://", "#")):
            raise RuntimeError(f"Unexpected non-local link in communication specification: {target}")
        path = (DOC_PATH.parent / target).resolve()
        if not path.exists() and path not in generated_paths:
            raise RuntimeError(f"Unresolved Markdown link: {target}")
        resolved += 1
    return resolved


def artifact_entry(payload: bytes) -> dict[str, Any]:
    return {"size_bytes": len(payload), "sha256": sha256_bytes(payload)}


def build_session_info() -> bytes:
    lines = [
        f"task={TASK_ID}",
        f"project_id={PROJECT_ID}",
        f"communication_version={COMMUNICATION_VERSION}",
        f"generator_version={GENERATOR_VERSION}",
        f"python_version={platform.python_version()}",
        f"python_implementation={platform.python_implementation()}",
        "standard_library_only=TRUE",
        "network_access=PROHIBITED_NOT_USED",
        "api_access=PROHIBITED_NOT_USED",
        "external_evidence_retrieval=FALSE",
        "case_dossiers_rebuilt=FALSE",
        "gene_symbols_added=FALSE",
        "runtime_ai_llm_decisions=PROHIBITED_NONE_USED",
        "randomness=NOT_USED",
        "wall_clock_governed_values=NOT_USED",
        "biological_interpretation=FALSE",
        "scoring_ranking_recommendation=FALSE",
        "deterministic_generation=BYTE_IDENTICAL",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def build_validation_report(release_id: str, link_count: int) -> bytes:
    text = f"""# Task #038A Case Study Communication Validation

**Communication release:** `{release_id}`  
**Validation status:** PASS

## Checks

- PASS — four frozen Task #036B case identities preserved in Task #036A category order
- PASS — dossier JSON, selection index, and Task #036C case summary reconciled
- PASS — component identities, versions, states, and source component-record references preserved
- PASS — feature-availability labels derived only through the frozen five-state communication map
- PASS — source Evidence Summary, prioritization representation, and case-selection provenance retained
- PASS — all summary-level and component-level limitation identifiers preserved
- PASS — dependency detail disclosed as retained upstream; no dependency edge or independence claim invented
- PASS — four self-contained SVG figures parse as XML and contain required structural fields
- PASS — {link_count} local Markdown links resolve
- PASS — recursive prohibited structured-field scan passed
- PASS — all {len(FROZEN_INPUTS)} Task #036A/#036B/#036C/#037D frozen input hashes unchanged before and after generation
- PASS — two complete generations are byte-identical
- PASS — no network/API access, evidence retrieval, dossier rebuild, gene symbol, biological narrative, runtime AI decision, score, ranking, or recommendation

## Interpretation boundaries

- Complete evidence ≠ best target
- Partial evidence ≠ negative evidence
- Conflict ≠ failure
- Limitation ≠ rejection

The outputs communicate governed evidence structure only. Computational conformance does not establish biological validity or therapeutic value.
"""
    return text.encode("utf-8")


def build_all() -> tuple[dict[Path, bytes], list[dict[str, Any]], str]:
    dossier_payload = load_json("outputs/case_dossiers_v0.1/case_dossiers.json")
    dossier_manifest = load_json("outputs/case_dossiers_v0.1/dossier_manifest.json")
    presentation_manifest = load_json("outputs/presentation_artifacts_v0.1/presentation_manifest.json")
    documentation_manifest = load_json("outputs/final_release_documentation_v1.0/final_release_manifest.json")
    dossier_index = load_csv("outputs/case_dossiers_v0.1/case_selection_index.csv")
    presentation_rows = load_csv("outputs/presentation_artifacts_v0.1/case_pattern_summary.csv")

    if dossier_manifest["validation_status"] != "PASS":
        raise RuntimeError("Frozen Task #036B dossier release is not validated")
    if presentation_manifest["validation_status"] != "PASS":
        raise RuntimeError("Frozen Task #036C presentation release is not validated")
    if documentation_manifest["validation_status"] != "PASS":
        raise RuntimeError("Frozen Task #037D documentation release is not validated")
    if presentation_manifest["source_releases"]["case_dossier_release_id"] != dossier_manifest["release_id"]:
        raise RuntimeError("Task #036B/#036C release identity mismatch")
    if documentation_manifest["source_governance"]["case_dossier_release_id"] != dossier_manifest["release_id"]:
        raise RuntimeError("Task #036B/#037D release identity mismatch")
    if documentation_manifest["source_governance"]["presentation_release_id"] != presentation_manifest["presentation_release_id"]:
        raise RuntimeError("Task #036C/#037D release identity mismatch")

    records = normalize_cases(dossier_payload, dossier_index, presentation_rows)
    release_seed = {
        "communication_version": COMMUNICATION_VERSION,
        "dossier_release_id": dossier_manifest["release_id"],
        "presentation_release_id": presentation_manifest["presentation_release_id"],
        "documentation_release_id": documentation_manifest["documentation_release_id"],
        "case_selection_ids": [record["case_selection_id"] for record in records],
    }
    release_id = "CASECOM_" + sha256_bytes(canonical_json(release_seed))[:32].upper()

    payloads: dict[Path, bytes] = {
        DOC_PATH: build_specification(),
        OUTPUT_DIR / "case_study_summary.csv": build_summary_csv(records),
        OUTPUT_DIR / "session_info.txt": build_session_info(),
    }
    for record in records:
        figure_path = ROOT / record["figure_path"]
        figure_payload = build_svg(record)
        validate_svg(figure_payload, record)
        payloads[figure_path] = figure_payload

    generated_paths = set(payloads)
    link_count = validate_markdown_links(payloads[DOC_PATH], generated_paths)
    validation_payload = build_validation_report(release_id, link_count)
    payloads[OUTPUT_DIR / "validation_report.md"] = validation_payload

    scan_prohibited_keys(records)
    with io.StringIO(payloads[OUTPUT_DIR / "case_study_summary.csv"].decode("utf-8")) as handle:
        csv_fields = csv.DictReader(handle).fieldnames or []
    prohibited_csv_fields = set(field.lower() for field in csv_fields) & PROHIBITED_FIELD_NAMES
    if prohibited_csv_fields:
        raise RuntimeError(f"Prohibited CSV field(s): {sorted(prohibited_csv_fields)}")

    generator_hash = sha256_file(Path(__file__).resolve())
    artifacts = {
        str(path.relative_to(ROOT)): artifact_entry(payload)
        for path, payload in sorted(payloads.items(), key=lambda item: str(item[0]))
    }
    manifest = {
        "manifest_type": "CASE_STUDY_COMMUNICATION_MANIFEST",
        "project_id": PROJECT_ID,
        "task_id": TASK_ID,
        "communication_release_id": release_id,
        "communication_version": COMMUNICATION_VERSION,
        "scope_boundary": "STRUCTURAL_COMMUNICATION_ONLY",
        "source_releases": {
            "case_dossier_release_id": dossier_manifest["release_id"],
            "presentation_release_id": presentation_manifest["presentation_release_id"],
            "documentation_release_id": documentation_manifest["documentation_release_id"],
        },
        "generator": {
            "relative_path": str(Path(__file__).resolve().relative_to(ROOT)),
            "generator_version": GENERATOR_VERSION,
            "sha256": generator_hash,
        },
        "counts": {
            "case_patterns": len(records),
            "case_summary_rows": len(records),
            "structural_figures": len(records),
            "preserved_entities": len({record["EnsemblID"] for record in records}),
        },
        "case_identities": [
            {
                "case_category": record["case_category"],
                "EnsemblID": record["EnsemblID"],
                "case_selection_id": record["case_selection_id"],
                "figure_path": record["figure_path"],
            }
            for record in records
        ],
        "artifacts": artifacts,
        "frozen_inputs": dict(sorted(FROZEN_INPUTS.items())),
        "validation": {
            "case_identity_reconciliation": "PASS",
            "component_state_fidelity": "PASS",
            "feature_availability_mapping": "PASS",
            "provenance_reference_preservation": "PASS",
            "limitation_preservation": "PASS",
            "dependency_disclosure": "PASS",
            "svg_validation": "PASS",
            "markdown_consistency": "PASS",
            "resolved_local_links": link_count,
            "prohibited_field_scan": "PASS",
            "frozen_input_hashes_unchanged": "PASS",
            "deterministic_generation": "BYTE_IDENTICAL",
            "network_access_used": False,
            "runtime_ai_decisions_used": False,
            "biological_interpretation_added": False,
        },
        "validation_status": "PASS",
    }
    payloads[OUTPUT_DIR / "case_study_manifest.json"] = canonical_json(manifest)
    return payloads, records, release_id


def write_payloads(payloads: dict[Path, bytes]) -> None:
    allowed = {
        DOC_PATH,
        OUTPUT_DIR / "case_study_manifest.json",
        OUTPUT_DIR / "case_study_summary.csv",
        OUTPUT_DIR / "validation_report.md",
        OUTPUT_DIR / "session_info.txt",
        *(FIGURE_DIR / CASE_PRESENTATION[category]["figure"] for category in CASE_ORDER),
    }
    if set(payloads) != allowed:
        unexpected = sorted(str(path.relative_to(ROOT)) for path in set(payloads) ^ allowed)
        raise RuntimeError(f"Generated path contract mismatch: {unexpected}")
    for path, payload in payloads.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)


def main() -> None:
    verify_frozen_inputs()
    first, records, release_id = build_all()
    second, _, second_release_id = build_all()
    if release_id != second_release_id or first != second:
        raise RuntimeError("Two complete in-memory generations were not byte-identical")
    write_payloads(first)
    verify_frozen_inputs()
    for path, expected in first.items():
        if path.read_bytes() != expected:
            raise RuntimeError(f"Written artifact byte mismatch: {path.relative_to(ROOT)}")

    print(f"communication_release_id={release_id}")
    print(f"case_patterns={len(records)}")
    print(f"structural_figures={len(records)}")
    print("deterministic_generation=BYTE_IDENTICAL")
    print("frozen_inputs_unchanged=PASS")
    print("network_access_used=FALSE")
    print("runtime_ai_decisions_used=FALSE")
    print("validation_status=PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # Fail closed with one clear diagnostic.
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
