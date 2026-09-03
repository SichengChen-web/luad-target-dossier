#!/usr/bin/env python3
"""Generate the frozen Task #039D MMP11 communication artifacts locally."""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import platform
import struct
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "outputs" / "mmp11_cross_source_synthesis_v0.1"
OUT = ROOT / "outputs" / "mmp11_worked_example_communication_v0.1"
SOURCE_BASE_COMMIT = "7c19a91"
TARGET_ID = "ENSG00000099953.9"
DISPLAY_SYMBOL = "MMP11"
SOURCE_SYNTHESIS_VERSION = "MMP11_CROSS_SOURCE_SYNTHESIS_V0.1"
GENERATOR_VERSION = "MMP11_WORKED_EXAMPLE_COMMUNICATION_GENERATOR_V0.1"
COMMUNICATION_VERSION = "MMP11_WORKED_EXAMPLE_COMMUNICATION_V0.1"
FIGURE_WIDTH = 1600
FIGURE_HEIGHT = 900
CHROME_RENDERER = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")

SOURCE_HASHES = {
    "evidence_family_registry.csv": "543f9955935cf3c0a0549f3d262373d7ef3011ebf285a344cf05dc93e735a2a2",
    "cross_source_dependency_map.csv": "1b3d3832b0b5beb81f853c43a74f8af9a82947702fd562663543275ee8f02f62",
    "claim_registry.csv": "dad160774617d7dcb8e76d696cb5723f35b4634e43fa6f3aef9843691f289b7b",
    "claim_evidence_matrix.csv": "78520330731d261cbfb6513845dd702bf9d9e6e6a2bdbb4448c0717cced208c0",
    "claim_dependency_audit.csv": "e41ec912b3893ea0cd3554dd0fac74ca77d19ac3211fe942ff6578e91f96b1c4",
    "modality_summary.csv": "693306bfb01cc70a4da712d96f90997c78a2006917fbe3875e37ffa7f137d282",
    "translational_boundary.json": "c64257dfa723ff2fea0674efae30966a7318b13dd671669372be67d49de598ab",
    "presentation_claim_candidates.json": "998dedf501465914385fe1316868c88c8e2ca6b0668c3e4bc06bd3e699e4cb1f",
    "mmp11_cross_source_synthesis.md": "97201a1d1376fd80fdbbc147d77ee31308242d9d0e8bc0193f690150fb1bb07c",
    "validation_report.md": "4a5d1ddee5a2953b132eac0d692159633dbeb4d4683717ab00832beda3499edc",
    "session_info.txt": "bacef8ff47486dc4a754f8c724cd4b3fcab0392fa9f95b0cf4a9509afcbecd6a",
}

DISPLAYED_FAMILIES = {
    "external_datasets": ["FAM_GEO_JOINT_2019", "FAM_GEO_GSE43458_PRIMARY", "FAM_COHORT_2019_LUAD_18"],
    "functional_models": ["FAM_CELL_PERTURBATION_310_A549_PC9", "FAM_CELL_PERTURBATION_310_PC9_RESCUE"],
    "preclinical_in_vivo": ["FAM_XENOGRAFT_DEPLETION_310"],
    "intervention": ["FAM_ANTIBODY_INTERVENTION_310"],
}

BOTTOM_LINE = (
    "MMP11 illustrates how a strong project-derived association can be linked "
    "to external transcriptomic and preclinical evidence while preserving "
    "shared-source dependencies and translational limits."
)
BOUNDARY_LINE = "Illustrative candidate — not a validated therapeutic target."
SLIDE_CLAIM_IDS = [
    "MMP11_CLAIM_01", "MMP11_CLAIM_02", "MMP11_CLAIM_03",
    "MMP11_CLAIM_04", "MMP11_CLAIM_05", "MMP11_CLAIM_06",
    "MMP11_CLAIM_10",
]


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def source_hashes() -> dict[str, str]:
    return {name: sha256(SOURCE / name) for name in SOURCE_HASHES}


def git_is_ancestor(commit: str) -> bool:
    return subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=ROOT,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0


def tracked_worktree_is_clean() -> bool:
    return all(
        subprocess.run(
            command, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        ).returncode == 0
        for command in (["git", "diff", "--quiet"], ["git", "diff", "--cached", "--quiet"])
    )


def has_no_network_client_imports() -> bool:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    prohibited = {"requests", "urllib", "httpx", "aiohttp"}
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".", 1)[0])
    return prohibited.isdisjoint(imported)


def slide_content() -> dict[str, Any]:
    return {
        "communication_version": COMMUNICATION_VERSION,
        "slide_title": "Worked example: MMP11",
        "slide_subtitle": "From an auditable evidence dossier to a biological hypothesis",
        "project_panel": {
            "panel_label": "PROJECT EVIDENCE",
            "target": DISPLAY_SYMBOL,
            "EnsemblID": TARGET_ID,
            "contrast": "LUAD tumour vs normal",
            "logFC": "+5.18",
            "BH_FDR": "1.79 × 10^-37",
            "sensitivity": "6/6 direction-concordant",
            "qualifier": "Same TCGA-LUAD dataset; robustness, not independent replication.",
        },
        "external_panel": {
            "panel_label": "EXTERNAL MODALITIES",
            "items": [
                {"label": "External datasets", "detail": "GEO / patient tissue", "family_ids": DISPLAYED_FAMILIES["external_datasets"]},
                {"label": "Functional models", "detail": "cell perturbation", "family_ids": DISPLAYED_FAMILIES["functional_models"]},
                {"label": "Preclinical in vivo", "detail": "xenograft", "family_ids": DISPLAYED_FAMILIES["preclinical_in_vivo"]},
                {"label": "Intervention", "detail": "anti-MMP11 antibody", "family_ids": DISPLAYED_FAMILIES["intervention"]},
            ],
            "qualifier": "Some transcriptomic analyses reuse TCGA or GEO datasets.",
        },
        "dependency_panel": {
            "panel_label": "DEPENDENCY CHECK",
            "relationships": [
                "Published TCGA evidence → shared dataset lineage",
                "Functional / xenograft / antibody observations → some share publication, model, experiment, or reagent lineage",
            ],
            "translational_boundary": "Preclinical evidence ≠ clinical validation",
        },
        "bottom_line": BOTTOM_LINE,
        "boundary_line": BOUNDARY_LINE,
        "optional_footer": "Evidence structure and provenance—not target evaluation",
        "source_claim_ids": SLIDE_CLAIM_IDS,
        "required_qualifiers": [
            "The six sensitivity models use the same TCGA-LUAD dataset and are not independent replication.",
            "Some transcriptomic analyses reuse TCGA or GEO datasets.",
            "Functional, xenograft, and antibody observations are preclinical and substantially share publication and experimental lineage.",
            "Clinical associations are context-dependent and include null findings.",
        ],
    }


def speaker_notes() -> str:
    return """# MMP11 worked-example speaker notes

## 30-second version

For a concrete example, this is MMP11. In our TCGA-LUAD analysis, it showed a strong tumour-versus-normal signal: logFC plus 5.18, with the same direction across all six sensitivity models. External records add GEO and patient-sample observations, cell perturbation, xenograft, and antibody experiments. The dependency check shows shared TCGA and experimental lineages. MMP11 is therefore an illustrative, traceable biological hypothesis—not a validated therapeutic target.

## 45-second version

For a concrete example, this is MMP11. In our TCGA-LUAD analysis, it showed a strong tumour-versus-normal signal, with a logFC of plus 5.18 and the same direction across all six prespecified sensitivity models. Those models use the same TCGA dataset, so they show robustness rather than independent replication. Connecting the result to external evidence adds GEO and patient-sample observations, cell perturbation, xenograft, and a preclinical antibody study. The provenance layer also reveals shared TCGA, publication, model, experiment, and reagent lineages. Clinical associations remain context-dependent and include null findings. The point is a traceable biological hypothesis with explicit translational limits—not a validated therapeutic target.

## Source notes

- Project signal and robustness: `MMP11_CLAIM_01`, `MMP11_CLAIM_02`
- External transcriptomic and tissue observations: `MMP11_CLAIM_03`, `MMP11_CLAIM_04`
- Functional, xenograft, and intervention observations: `MMP11_CLAIM_05`, `MMP11_CLAIM_06`, `MMP11_CLAIM_10`
- Clinical and mechanistic boundaries: `MMP11_CLAIM_07`, `MMP11_CLAIM_08`, `MMP11_CLAIM_09`
"""


def presenter_detail() -> str:
    return """# MMP11 presenter detail

These details support presenter preparation and should not appear as headline slide metrics.

## Audit metadata

- 56 external evidence units
- 43 evidence families
- 251 normalized dependency graph rows
- 34 dataset/cohort lineages
- 7 null findings
- 19 context-dependent findings
- 5 unresolved dependencies

**These are audit metadata, not evidence-strength metrics.** Evidence-unit, family, dataset, and graph-row counts do not represent independent replication, target quality, confidence, or therapeutic value.

## Count and dependency boundaries

- The 251 graph rows consist of 35 normalized Task #039A atomic edges, 197 frozen Task #039B edges, and 19 synthesized cross-task edges.
- The six sensitivity models reuse the same TCGA-LUAD biological dataset.
- Published TCGA observations share dataset lineage with the project analysis.
- Several functional, xenograft, and antibody observations share publication, model, experiment, or reagent lineage.
- The antibody xenograft is one evidence unit represented in both in-vivo and intervention contexts; it is not two independent observations.

## Translational boundary

The frozen synthesis supports a project expression association, same-dataset model robustness, external observations, and bounded preclinical functional/intervention observations. Clinical validation is not established, and therapeutic recommendation is outside project scope.
"""


def svg_figure() -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{FIGURE_WIDTH}" height="{FIGURE_HEIGHT}" viewBox="0 0 {FIGURE_WIDTH} {FIGURE_HEIGHT}" role="img" aria-labelledby="title desc" fill="#17253D">
  <title id="title">Worked example: MMP11</title>
  <desc id="desc">Project expression evidence connected to external modalities, dependency checks, and a preclinical-to-clinical interpretation boundary.</desc>
  <rect width="1600" height="900" fill="#F7F9FC"/>
  <style>
    text {{ font-family: Arial, Helvetica, sans-serif; }}
    .eyebrow {{ font-size: 16px; font-weight: 700; letter-spacing: 2px; fill: #54708F; }}
    .paneltitle {{ font-size: 18px; font-weight: 700; letter-spacing: 1.4px; fill: #3D5A78; }}
    .label {{ font-size: 20px; font-weight: 700; }}
    .detail {{ font-size: 17px; fill: #52657A; }}
    .small {{ font-size: 15px; fill: #52657A; }}
  </style>

  <text class="eyebrow" x="64" y="54">AUDITABLE LUAD WORKED EXAMPLE</text>
  <text x="64" y="106" font-size="38" font-weight="700">MMP11 · from signal to bounded hypothesis</text>
  <text x="64" y="139" font-size="20" fill="#5E7083">A provenance-aware view of evidence—not a target ranking</text>

  <!-- Project panel -->
  <rect x="64" y="186" width="430" height="476" rx="24" fill="#FFFFFF" stroke="#C9D7E6" stroke-width="2"/>
  <rect x="64" y="186" width="430" height="8" rx="4" fill="#4169A1"/>
  <text class="paneltitle" x="94" y="232">01  PROJECT EVIDENCE</text>
  <text x="94" y="296" font-size="50" font-weight="700">MMP11</text>
  <text x="94" y="327" font-size="17" fill="#61758A">ENSG00000099953.9</text>
  <text x="94" y="373" font-size="19" font-weight="700">LUAD tumour vs normal</text>

  <rect x="94" y="401" width="176" height="104" rx="16" fill="#EAF1FA"/>
  <text x="112" y="448" font-size="36" font-weight="700" fill="#294E82">+5.18</text>
  <text class="small" x="112" y="480">logFC</text>
  <rect x="286" y="401" width="178" height="104" rx="16" fill="#EAF1FA"/>
  <text x="304" y="447" font-size="28" font-weight="700" fill="#294E82">1.79 × 10⁻³⁷</text>
  <text class="small" x="304" y="480">BH FDR</text>

  <rect x="94" y="521" width="370" height="62" rx="16" fill="#DCE9F8"/>
  <text x="116" y="561" font-size="25" font-weight="700" fill="#294E82">6 / 6 direction-concordant</text>
  <text class="small" x="94" y="614">Same TCGA-LUAD dataset</text>
  <text class="small" x="94" y="638">Robustness, not independent replication</text>

  <!-- Connector -->
  <line x1="510" y1="424" x2="548" y2="424" stroke="#8EA5BC" stroke-width="4"/>
  <path d="M548 424 L534 414 L534 434 Z" fill="#8EA5BC"/>

  <!-- External modalities panel -->
  <rect x="562" y="186" width="472" height="476" rx="24" fill="#FFFFFF" stroke="#C9D7E6" stroke-width="2"/>
  <rect x="562" y="186" width="472" height="8" rx="4" fill="#5A7F83"/>
  <text class="paneltitle" x="592" y="232">02  EXTERNAL MODALITIES</text>

  <rect x="592" y="260" width="196" height="132" rx="18" fill="#EDF4F3"/>
  <circle cx="626" cy="296" r="18" fill="none" stroke="#4D777B" stroke-width="3"/>
  <path d="M615 296h22M626 285v22" stroke="#4D777B" stroke-width="3"/>
  <text class="label" x="612" y="340">External datasets</text>
  <text class="detail" x="612" y="367">GEO / patient tissue</text>

  <rect x="808" y="260" width="196" height="132" rx="18" fill="#EDF4F3"/>
  <circle cx="842" cy="296" r="17" fill="none" stroke="#4D777B" stroke-width="3"/>
  <path d="M832 304c7-18 13-18 21 0M833 289h18" fill="none" stroke="#4D777B" stroke-width="3"/>
  <text class="label" x="828" y="340">Functional models</text>
  <text class="detail" x="828" y="367">cell perturbation</text>

  <rect x="592" y="410" width="196" height="132" rx="18" fill="#EDF4F3"/>
  <path d="M614 453c12-18 28-18 40 0M619 453v17h30v-17" fill="none" stroke="#4D777B" stroke-width="3"/>
  <text class="label" x="612" y="490">Preclinical in vivo</text>
  <text class="detail" x="612" y="517">xenograft</text>

  <rect x="808" y="410" width="196" height="132" rx="18" fill="#EDF4F3"/>
  <path d="M828 454h40M848 434v40M833 439l30 30M863 439l-30 30" stroke="#4D777B" stroke-width="3"/>
  <text class="label" x="828" y="490">Intervention</text>
  <text class="detail" x="828" y="517">anti-MMP11 antibody</text>

  <rect x="592" y="566" width="412" height="62" rx="15" fill="#F1F4F7"/>
  <text class="small" x="612" y="593">Some transcriptomic analyses reuse</text>
  <text class="small" x="612" y="615">TCGA or GEO datasets.</text>

  <!-- Connector -->
  <line x1="1050" y1="424" x2="1088" y2="424" stroke="#8EA5BC" stroke-width="4"/>
  <path d="M1088 424 L1074 414 L1074 434 Z" fill="#8EA5BC"/>

  <!-- Dependency panel -->
  <rect x="1102" y="186" width="434" height="476" rx="24" fill="#FFFFFF" stroke="#C9D7E6" stroke-width="2"/>
  <rect x="1102" y="186" width="434" height="8" rx="4" fill="#806F9B"/>
  <text class="paneltitle" x="1132" y="232">03  DEPENDENCY CHECK</text>

  <rect x="1132" y="262" width="374" height="92" rx="16" fill="#F3F0F7"/>
  <text x="1152" y="296" font-size="18" font-weight="700">Published TCGA evidence</text>
  <text x="1152" y="326" font-size="17" fill="#665779">→ shared dataset lineage</text>

  <rect x="1132" y="370" width="374" height="126" rx="16" fill="#F3F0F7"/>
  <text x="1152" y="404" font-size="18" font-weight="700">Functional · xenograft · antibody</text>
  <text x="1152" y="434" font-size="17" fill="#665779">→ some shared publication / model</text>
  <text x="1152" y="462" font-size="17" fill="#665779">   experiment / reagent lineage</text>

  <rect x="1132" y="520" width="374" height="108" rx="18" fill="#272F46"/>
  <text x="1154" y="559" font-size="17" font-weight="700" fill="#D9E3F0">TRANSLATIONAL BOUNDARY</text>
  <text x="1154" y="594" font-size="24" font-weight="700" fill="#FFFFFF">Preclinical evidence ≠</text>
  <text x="1154" y="619" font-size="24" font-weight="700" fill="#FFFFFF">clinical validation</text>

  <!-- Bottom line -->
  <rect x="64" y="704" width="1472" height="132" rx="22" fill="#17253D"/>
  <text x="92" y="748" font-size="19" font-weight="700" fill="#AFC6DF">BOTTOM LINE</text>
  <text x="92" y="783" font-size="22" font-weight="700" fill="#FFFFFF">MMP11 links a strong project association to external transcriptomic and preclinical evidence</text>
  <text x="92" y="812" font-size="22" font-weight="700" fill="#FFFFFF">while keeping shared-source dependencies and translational limits visible.</text>
  <text x="1166" y="785" font-size="16" font-weight="700" fill="#E3D6AF">ILLUSTRATIVE CANDIDATE</text>
  <text x="1166" y="812" font-size="16" fill="#FFFFFF">not a validated therapeutic target</text>
  <text x="64" y="872" font-size="14" fill="#71849A">Original project graphic · source: {SOURCE_SYNTHESIS_VERSION}</text>
</svg>
'''


def png_dimensions(payload: bytes) -> tuple[int, int]:
    if (
        payload[:8] != b"\x89PNG\r\n\x1a\n"
        or payload[12:16] != b"IHDR"
        or payload[-8:-4] != b"IEND"
    ):
        raise AssertionError("Rasterized figure is not a valid PNG")
    return struct.unpack(">II", payload[16:24])


def render_png(svg_payload: str, destination: Path) -> bytes:
    if not CHROME_RENDERER.is_file():
        raise RuntimeError("The frozen generator requires the locally installed Chrome headless renderer")
    svg_path = destination.with_suffix(".source.svg")
    svg_path.write_text(svg_payload, encoding="utf-8")
    profile_path = destination.parent / f"chrome_profile_{destination.stem}"
    command = [
        str(CHROME_RENDERER), "--headless=new", "--disable-gpu", "--no-first-run",
        "--disable-background-networking", "--disable-component-update", "--disable-sync",
        "--disable-default-apps", "--disable-extensions", "--metrics-recording-only",
        "--host-resolver-rules=MAP * 0.0.0.0, EXCLUDE localhost",
        f"--user-data-dir={profile_path}",
        f"--window-size={FIGURE_WIDTH},{FIGURE_HEIGHT}",
        "--force-device-scale-factor=1", "--hide-scrollbars",
        f"--screenshot={destination}", svg_path.as_uri(),
    ]
    process = subprocess.Popen(
        command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    previous_size = -1
    stable_intervals = 0
    for _ in range(200):
        if destination.exists():
            current_size = destination.stat().st_size
            stable_intervals = stable_intervals + 1 if current_size == previous_size and current_size > 24 else 0
            previous_size = current_size
            if stable_intervals >= 3:
                break
        if process.poll() is not None and not destination.exists():
            raise RuntimeError(f"Chrome SVG rasterization exited with status {process.returncode}")
        time.sleep(0.1)
    else:
        raise RuntimeError("Chrome SVG rasterization did not produce a stable PNG within 20 seconds")
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    svg_path.unlink()
    return destination.read_bytes()


def note_word_count(notes: str, heading: str, next_heading: str) -> int:
    section = notes.split(heading, 1)[1].split(next_heading, 1)[0]
    return len(section.split())


def build_manifest(
    content: dict[str, Any], artifact_hashes: dict[str, str], note_counts: dict[str, int],
) -> dict[str, Any]:
    candidates = json.loads((SOURCE / "presentation_claim_candidates.json").read_text())
    communication_claim_ids = [
        claim_id for candidate in candidates["candidates"] for claim_id in candidate["claim_ids"]
    ]
    return {
        "communication_id": "COMM_MMP11_WORKED_EXAMPLE_V0.1",
        "communication_version": COMMUNICATION_VERSION,
        "target_identity": {"EnsemblID": TARGET_ID, "display_symbol": DISPLAY_SYMBOL},
        "source_synthesis_version": candidates["synthesis_version"],
        "source_base_commit": SOURCE_BASE_COMMIT,
        "source_claim_ids": communication_claim_ids,
        "slide_source_claim_ids": content["source_claim_ids"],
        "exact_project_values_used": {
            "contrast": "LUAD tumour vs normal",
            "logFC_display": "+5.18",
            "BH_FDR_display": "1.79 × 10^-37",
            "sensitivity_display": "6/6 direction-concordant",
        },
        "evidence_families_referenced": DISPLAYED_FAMILIES,
        "required_qualifiers": content["required_qualifiers"],
        "prohibited_wording": [
            "proven target", "validated target", "best target", "top target",
            "promising therapeutic target", "clinically actionable", "clinically validated",
            "independent lines of evidence",
        ],
        "figure_files": [
            "outputs/mmp11_worked_example_communication_v0.1/figure_mmp11_worked_example.svg",
            "outputs/mmp11_worked_example_communication_v0.1/figure_mmp11_worked_example.png",
        ],
        "figure_dimensions_pixels": {"width": FIGURE_WIDTH, "height": FIGURE_HEIGHT},
        "speaker_note_source_references": communication_claim_ids,
        "speaker_note_word_counts": note_counts,
        "generation_timestamp_policy": "OMITTED_FOR_DETERMINISM",
        "generator_version": GENERATOR_VERSION,
        "artifact_sha256": artifact_hashes,
        "source_artifact_sha256": SOURCE_HASHES,
        "communication_boundary": BOUNDARY_LINE,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    before = source_hashes()
    families = read_csv(SOURCE / "evidence_family_registry.csv")
    claims = read_csv(SOURCE / "claim_registry.csv")
    candidates = json.loads((SOURCE / "presentation_claim_candidates.json").read_text())
    translation = json.loads((SOURCE / "translational_boundary.json").read_text())

    content = slide_content()
    notes = speaker_notes()
    detail = presenter_detail()
    svg = svg_figure()
    note_counts = {
        "30_second_version": note_word_count(notes, "## 30-second version", "## 45-second version"),
        "45_second_version": note_word_count(notes, "## 45-second version", "## Source notes"),
    }

    # Build all deterministic source artifacts twice before publication.
    content_again = slide_content()
    notes_again = speaker_notes()
    detail_again = presenter_detail()
    svg_again = svg_figure()
    text_deterministic = (content, notes, detail, svg) == (content_again, notes_again, detail_again, svg_again)

    with tempfile.TemporaryDirectory(prefix="task039d_") as temporary:
        temp = Path(temporary)
        png_one = render_png(svg, temp / "figure_one.png")
        png_two = render_png(svg_again, temp / "figure_two.png")
    png_deterministic = png_one == png_two
    width, height = png_dimensions(png_one)

    family_ids = {x["evidence_family_id"] for x in families}
    claim_ids = {x["claim_id"] for x in claims}
    candidate_claim_ids = {
        claim_id for candidate in candidates["candidates"] for claim_id in candidate["claim_ids"]
    }
    displayed_family_ids = {item for values in DISPLAYED_FAMILIES.values() for item in values}
    slide_serialized = canonical_json(content)
    visible_payload = (slide_serialized + svg).lower()
    communication_payload = (slide_serialized + notes + svg).lower()
    audit_headline_tokens = ["56 evidence units", "43 evidence families", "251 dependency"]
    positive_prohibited_phrases = [
        "mmp11 is a proven target", "mmp11 is a validated target",
        "mmp11 is a promising therapeutic target", "mmp11 is clinically actionable",
        "independent lines of evidence",
    ]

    checks: list[tuple[str, bool, str]] = [
        ("task039c_frozen_hashes", before == SOURCE_HASHES, "All 11 frozen Task #039C artifacts match pinned SHA256 values."),
        ("source_base_commit", git_is_ancestor(SOURCE_BASE_COMMIT), "The frozen Task #039C base commit is an ancestor of current HEAD."),
        ("target_identity", content["project_panel"]["EnsemblID"] == TARGET_ID and translation["EnsemblID"] == TARGET_ID, "MMP11 immutable identity resolves to the frozen synthesis."),
        ("project_logfc_fidelity", content["project_panel"]["logFC"] == "+5.18" and "+5.18" in candidates["candidates"][0]["short_statement"], "Displayed logFC derives from PRESENTATION_CLAIM_01."),
        ("project_fdr_fidelity", content["project_panel"]["BH_FDR"] == "1.79 × 10^-37" and "1.79e-37" in candidates["candidates"][0]["short_statement"], "Displayed BH FDR derives from PRESENTATION_CLAIM_01."),
        ("sensitivity_fidelity", content["project_panel"]["sensitivity"] == "6/6 direction-concordant" and "all six" in candidates["candidates"][0]["short_statement"], "Displayed 6/6 result derives from PRESENTATION_CLAIM_01."),
        ("external_modalities_resolve", displayed_family_ids.issubset(family_ids), "Every visible external modality resolves to frozen evidence-family identifiers."),
        ("slide_claims_resolve", set(content["source_claim_ids"]).issubset(claim_ids & candidate_claim_ids), "All slide and note claims resolve to validated Task #039C presentation candidates."),
        ("tcga_dependency_qualifier", "shared dataset lineage" in visible_payload and "not independent replication" in visible_payload, "Shared TCGA lineage and same-dataset robustness qualifiers remain visible."),
        ("experimental_dependency_qualifier", all(token in visible_payload for token in ["publication", "model", "experiment", "reagent"]), "Shared publication/model/experiment/reagent lineage is visible."),
        ("preclinical_boundary", "preclinical evidence ≠ clinical validation" in visible_payload, "The preclinical-to-clinical boundary is prominent."),
        ("clinical_validation_not_claimed", not any(phrase in communication_payload for phrase in positive_prohibited_phrases), "No affirmative clinical-validation, recommendation, or unsupported-independence claim is present."),
        ("audit_counts_not_strength_headlines", not any(token in visible_payload for token in audit_headline_tokens) and "audit metadata, not evidence-strength metrics" in detail.lower(), "Audit counts are confined to presenter detail and explicitly bounded."),
        ("no_score_rank_recommendation_fields", not {"score", "rank", "ranking", "recommendation"}.intersection(content), "No score, rank, or recommendation field is generated."),
        ("original_project_graphic", "<image" not in svg.lower() and "original project graphic" in svg.lower(), "Figure uses only generator-defined vector primitives; no publication figure is copied."),
        ("figure_dimensions", (width, height) == (FIGURE_WIDTH, FIGURE_HEIGHT), "SVG and PNG are 1600 × 900 pixels (16:9)."),
        ("deterministic_regeneration", text_deterministic and png_deterministic, "Two independent text/vector constructions and PNG rasterizations are byte-identical."),
        ("no_network_runtime", has_no_network_client_imports(), "Generator imports no network client and uses frozen local inputs only."),
        ("tracked_upstream_unchanged", tracked_worktree_is_clean(), "No tracked Task #039A/#039B/#039C artifact is modified or staged."),
    ]
    if not all(ok for _, ok, _ in checks):
        raise AssertionError("Pre-publication validation failed: " + ", ".join(name for name, ok, _ in checks if not ok))

    slide_bytes = slide_serialized.encode("utf-8")
    notes_bytes = notes.encode("utf-8")
    detail_bytes = detail.encode("utf-8")
    svg_bytes = svg.encode("utf-8")
    artifact_hashes = {
        "slide_content.json": sha256_bytes(slide_bytes),
        "speaker_notes.md": sha256_bytes(notes_bytes),
        "presenter_detail.md": sha256_bytes(detail_bytes),
        "figure_mmp11_worked_example.svg": sha256_bytes(svg_bytes),
        "figure_mmp11_worked_example.png": sha256_bytes(png_one),
    }
    manifest = build_manifest(content, artifact_hashes, note_counts)

    validation_report = """# Task #039D validation report

Overall validation: **PASS**

MMP11 is an illustrative worked example. These communication artifacts preserve the frozen synthesis and do not constitute target ranking, therapeutic validation, clinical-efficacy evidence, safety evidence, or a recommendation.

| Check | Result | Detail |
|---|---|---|
""" + "\n".join(
        f"| `{name}` | **{'PASS' if ok else 'FAIL'}** | {detail} |" for name, ok, detail in checks
    ) + "\n"

    branch = subprocess.run(
        ["git", "branch", "--show-current"], cwd=ROOT, check=True,
        text=True, capture_output=True,
    ).stdout.strip()
    renderer_version = subprocess.run(
        [str(CHROME_RENDERER), "--version"], check=True,
        text=True, capture_output=True,
    ).stdout.strip().replace("\n", "; ")
    session = "\n".join([
        f"communication_version={COMMUNICATION_VERSION}",
        f"generator_version={GENERATOR_VERSION}",
        f"source_synthesis_version={SOURCE_SYNTHESIS_VERSION}",
        f"source_base_commit={SOURCE_BASE_COMMIT}",
        f"python_version={platform.python_version()}",
        f"platform={platform.platform()}",
        f"svg_renderer={renderer_version}",
        f"figure_dimensions={FIGURE_WIDTH}x{FIGURE_HEIGHT}",
        f"git_branch={branch}",
        "network_access=NONE",
        "generation_timestamp_policy=OMITTED_FOR_DETERMINISM",
        "runtime_head_policy=SOURCE_BASE_COMMIT_MUST_BE_ANCESTOR;CURRENT_HEAD_NOT_EMBEDDED",
        "working_tree_state=REPORTED_AT_COMPLETION_NOT_EMBEDDED",
        "source_artifact_hashes=" + json.dumps(SOURCE_HASHES, sort_keys=True),
        "", 
    ])

    outputs = {
        "communication_manifest.json": canonical_json(manifest).encode("utf-8"),
        "slide_content.json": slide_bytes,
        "speaker_notes.md": notes_bytes,
        "presenter_detail.md": detail_bytes,
        "figure_mmp11_worked_example.svg": svg_bytes,
        "figure_mmp11_worked_example.png": png_one,
        "validation_report.md": validation_report.encode("utf-8"),
        "session_info.txt": session.encode("utf-8"),
    }
    for name, payload in outputs.items():
        (OUT / name).write_bytes(payload)

    if source_hashes() != before:
        raise AssertionError("Frozen Task #039C source changed during generation")

    metrics = {
        "target": f"{DISPLAY_SYMBOL} ({TARGET_ID})",
        "source_task039c_synthesis_version": SOURCE_SYNTHESIS_VERSION,
        "slide_claims_used": content["source_claim_ids"],
        "evidence_modalities_displayed": ["external datasets", "functional models", "preclinical in vivo", "intervention"],
        "dependency_qualifiers_displayed": ["shared TCGA dataset lineage", "shared publication/model/experiment/reagent lineage"],
        "project_numerical_values_displayed": {"logFC": "+5.18", "BH_FDR": "1.79 × 10^-37", "sensitivity": "6/6"},
        "final_bottom_line_statement": BOTTOM_LINE,
        "30_second_note_word_count": note_counts["30_second_version"],
        "45_second_note_word_count": note_counts["45_second_version"],
        "figure_dimensions": f"{FIGURE_WIDTH}x{FIGURE_HEIGHT}",
        "validation": "PASS",
    }
    print(canonical_json(metrics), end="")
    print("files_created:")
    print("- analysis/39D_generate_mmp11_worked_example_communication.py")
    for name in outputs:
        print(f"- outputs/mmp11_worked_example_communication_v0.1/{name}")
    print("files_modified: none")


if __name__ == "__main__":
    main()
