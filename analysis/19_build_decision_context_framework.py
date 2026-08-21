#!/usr/bin/env python3
"""Build the Task #019 qualitative decision-context framework.

The builder maps the frozen evidence ontology to three scientific decision
contexts and records evidence-type interpretation boundaries. It does not
evaluate genes, aggregate evidence, score, rank, select, or recommend targets.
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
TASK018_BASE_COMMIT = "029817068bfb79888864359f462f52358c166e85"
EXPECTED_BRANCH = "main"
EXPECTED_REMOTE_FRAGMENT = "SichengChen-web/luad-target-dossier"

SCRIPT_PATH = ROOT / "analysis/19_build_decision_context_framework.py"
PLAN_PATH = ROOT / "docs/decision_context_framework_v0.1.md"
OUTPUT_DIR = ROOT / "outputs/decision_context"
CONTEXT_PATH = OUTPUT_DIR / "decision_context_registry.csv"
MATRIX_PATH = OUTPUT_DIR / "evidence_context_matrix.csv"
BOUNDARY_PATH = OUTPUT_DIR / "interpretation_boundary_registry.csv"
SUMMARY_PATH = OUTPUT_DIR / "decision_framework_summary.md"
SESSION_PATH = OUTPUT_DIR / "session_info.txt"

INPUTS = {
    "governance_plan": ROOT / "docs/artifact_governance_plan_v0.1.md",
    "artifact_manifest": ROOT / "outputs/artifact_governance/artifact_manifest.csv",
    "artifact_classification": ROOT
    / "outputs/artifact_governance/artifact_classification.csv",
    "reproducibility_contract": ROOT
    / "outputs/artifact_governance/reproducibility_contract.md",
    "artifact_governance_summary": ROOT
    / "outputs/artifact_governance/artifact_governance_summary.md",
    "artifact_governance_session": ROOT / "outputs/artifact_governance/session_info.txt",
    "domain_registry": ROOT / "outputs/evidence_ontology/evidence_domain_registry.csv",
    "independence_map": ROOT / "outputs/evidence_ontology/evidence_independence_map.csv",
    "source_lineage": ROOT / "outputs/evidence_ontology/evidence_source_lineage.csv",
    "claim_registry": ROOT
    / "outputs/evidence_claim_architecture/evidence_claim_registry.csv",
    "dependency_graph": ROOT
    / "outputs/evidence_claim_architecture/evidence_dependency_graph.csv",
    "source_entity_registry": ROOT
    / "outputs/evidence_claim_architecture/source_entity_registry.csv",
}

EXPECTED_HASHES = {
    "governance_plan": "92557a1e2002c841d9acd41b0bd58177a92b18105bc555b57ecd8df1ef841c7a",
    "artifact_manifest": "f8cb7150b2a6e51f74f04ba2a542348c973359aaab172d903385073f21a62b24",
    "artifact_classification": "c53b52bff0357ef5d69bf85a007ce7c214ecf4f3e7f2b4ff6b47fcd6e2b75c12",
    "reproducibility_contract": "e4bcfeca738a78ae7047d0fdbd0f5f285044c1f9585565f70cc0d61744e52f79",
    "artifact_governance_summary": "9287140c9671a7c8e3d56d43d6b2a4868b1deb36eca3c83ac14ac467d3d3d4a6",
    "artifact_governance_session": "ee2761523fec18ff4782c5edfaf67a547dce283d3f8db0e2c134c35afe7dc312",
    "domain_registry": "ee62ce66f2ca4726c9365da347198251b9bd77d2dead87b8409221505f2d03b8",
    "independence_map": "d99bbaa8fe5e6229774ac2bf73d84de8fbd367e585d692eb1273ecc7b5c53945",
    "source_lineage": "e9496e8bbf953fdffdbaed7e09936a8493230fc74939597537f8960fabf19f2c",
    "claim_registry": "0d963a4c5c8f9586f81369e33df0a2b7e57bb37ac8ceab4ce54498baf2351a66",
    "dependency_graph": "011839f10c48e197f9f1c0e2262565e562d3a2cf53dd0936f21ddcb4ed5c2256",
    "source_entity_registry": "1b1379066226b5f69b626fe4a97628f7b6da6e585515aa8609218eef65bf8056",
}

ALLOWED_UNTRACKED_FILES = {
    "analysis/19_build_decision_context_framework.py",
    "docs/decision_context_framework_v0.1.md",
}
ALLOWED_UNTRACKED_PREFIX = "outputs/decision_context/"

SUPPORT_LEVELS = {"REQUIRED", "RELEVANT", "OPTIONAL", "NOT_APPLICABLE"}
FORBIDDEN_EXACT_COLUMNS = {
    "score",
    "rank",
    "priority",
    "target_selection",
    "recommendation",
    "therapeutic_direction",
}

DOMAIN_ORDER = [
    "DOM_TRANSCRIPTOMIC_DISCOVERY",
    "DOM_DISEASE_ASSOCIATION",
    "DOM_GENETIC_EVIDENCE",
    "DOM_FUNCTIONAL_DEPENDENCY",
    "DOM_PHARMACOLOGY",
    "DOM_TRACTABILITY",
    "DOM_CLINICAL_DEVELOPMENT",
    "DOM_SAFETY",
]

CURRENT_CLAIM_DOMAINS = {
    "DOM_TRANSCRIPTOMIC_DISCOVERY",
    "DOM_DISEASE_ASSOCIATION",
    "DOM_PHARMACOLOGY",
    "DOM_TRACTABILITY",
    "DOM_SAFETY",
}

FUTURE_EVIDENCE_TYPES = {
    "EV_GENETIC_CANCER",
    "EV_FUNCTIONAL_CRISPR_DEPENDENCY",
    "EV_CHEMBL_COMPOUND_TARGET",
    "EV_CLINICAL_TRIAL_DEVELOPMENT",
}

CONTEXTS = [
    {
        "id": "CTX_BIOLOGICAL_DISCOVERY",
        "name": "Biological Discovery",
        "question": "Is this gene worth further biological investigation?",
        "required": {
            "DOM_TRANSCRIPTOMIC_DISCOVERY",
            "DOM_DISEASE_ASSOCIATION",
        },
        "relevant": {
            "DOM_GENETIC_EVIDENCE",
            "DOM_FUNCTIONAL_DEPENDENCY",
        },
        "optional": {"DOM_PHARMACOLOGY", "DOM_TRACTABILITY"},
        "not_applicable": {"DOM_CLINICAL_DEVELOPMENT", "DOM_SAFETY"},
        "interpretation": (
            "This context can justify additional biological investigation when LUAD-linked "
            "molecular observations are traceable and coherent. It cannot establish causality, "
            "drug efficacy, safety, clinical benefit, or a therapeutic mechanism."
        ),
        "generation_boundary": (
            "The framework classifies evidence roles only. Expression, association, genetic, "
            "and perturbational observations must be generated and QC-validated in separate tasks."
        ),
        "status_rule": (
            "A context interpretation remains UNRESOLVED when a required domain is missing, "
            "not queried, provenance-incomplete, or materially conflicting; absence is not negative evidence."
        ),
    },
    {
        "id": "CTX_THERAPEUTIC_DEVELOPMENT",
        "name": "Therapeutic Development",
        "question": "Does this target have evidence relevant to drug development feasibility?",
        "required": {"DOM_PHARMACOLOGY", "DOM_TRACTABILITY", "DOM_SAFETY"},
        "relevant": {
            "DOM_TRANSCRIPTOMIC_DISCOVERY",
            "DOM_DISEASE_ASSOCIATION",
            "DOM_GENETIC_EVIDENCE",
            "DOM_FUNCTIONAL_DEPENDENCY",
        },
        "optional": {"DOM_CLINICAL_DEVELOPMENT"},
        "not_applicable": set(),
        "interpretation": (
            "This context describes whether source-grounded pharmacology, modality feasibility, "
            "and risk information are available for development planning. It cannot establish "
            "biological causality, therapeutic efficacy, acceptable dose, or clinical success."
        ),
        "generation_boundary": (
            "Target annotations, tractability assessments, compounds, assays, and safety records "
            "remain source evidence; this framework does not create or upgrade them."
        ),
        "status_rule": (
            "Feasibility remains UNRESOLVED if any required domain lacks adequate evidence or "
            "provenance. A missing safety record is not evidence of safety."
        ),
    },
    {
        "id": "CTX_TRANSLATIONAL",
        "name": "Translational Context",
        "question": "Is there evidence supporting potential clinical relevance?",
        "required": {
            "DOM_DISEASE_ASSOCIATION",
            "DOM_PHARMACOLOGY",
            "DOM_CLINICAL_DEVELOPMENT",
            "DOM_SAFETY",
        },
        "relevant": {
            "DOM_TRANSCRIPTOMIC_DISCOVERY",
            "DOM_GENETIC_EVIDENCE",
            "DOM_FUNCTIONAL_DEPENDENCY",
            "DOM_TRACTABILITY",
        },
        "optional": set(),
        "not_applicable": set(),
        "interpretation": (
            "This context describes traceable disease relevance, intervention linkage, human "
            "development evidence, and risk context. It cannot establish efficacy, approval, "
            "patient benefit, clinical utility, or a favorable benefit-risk balance."
        ),
        "generation_boundary": (
            "Trial, intervention, disease, target-linkage, and safety evidence must be retrieved "
            "at record level in dedicated tasks; platform counts are not substituted for clinical records."
        ),
        "status_rule": (
            "Potential clinical relevance remains UNRESOLVED when required trial-level or linkage "
            "evidence is absent, stale, conflicting, or not independently traceable."
        ),
    },
]

MATRIX_NOTES = {
    "CTX_BIOLOGICAL_DISCOVERY": {
        "DOM_TRANSCRIPTOMIC_DISCOVERY": "Required project-entry evidence for a reproducible LUAD tumour-associated expression alteration; it remains associative.",
        "DOM_DISEASE_ASSOCIATION": "Required external disease-context evidence; source-native association does not establish causality.",
        "DOM_GENETIC_EVIDENCE": "Relevant to causal plausibility and mechanism, but absence does not preclude initial biological follow-up.",
        "DOM_FUNCTIONAL_DEPENDENCY": "Relevant because controlled perturbation can test disease-model function; model context limits generalization.",
        "DOM_PHARMACOLOGY": "Optional experimental-tool context; target annotation or compound evidence does not determine biological importance.",
        "DOM_TRACTABILITY": "Optional modality context; feasibility does not establish that the biology warrants investigation.",
        "DOM_CLINICAL_DEVELOPMENT": "Not applicable to the direct biological-discovery question; maturity is retained for other contexts.",
        "DOM_SAFETY": "Not applicable as support for biological discovery; risk evidence remains essential in development contexts.",
    },
    "CTX_THERAPEUTIC_DEVELOPMENT": {
        "DOM_TRANSCRIPTOMIC_DISCOVERY": "Relevant disease-context evidence, but differential expression does not demonstrate a modlatable dependency.",
        "DOM_DISEASE_ASSOCIATION": "Relevant to disease rationale; association alone does not establish feasibility or efficacy.",
        "DOM_GENETIC_EVIDENCE": "Relevant to causal plausibility and target validity; it does not establish modality feasibility.",
        "DOM_FUNCTIONAL_DEPENDENCY": "Relevant to whether perturbation changes disease-model function; it does not establish safe human modulation.",
        "DOM_PHARMACOLOGY": "Required to characterize actual target annotations, compound interaction, potency, selectivity, and mechanism at appropriate resolution.",
        "DOM_TRACTABILITY": "Required to establish source-grounded feasibility for at least one explicitly defined therapeutic modality.",
        "DOM_CLINICAL_DEVELOPMENT": "Optional precedent for feasibility; absence of trials does not prove that development is infeasible.",
        "DOM_SAFETY": "Required to characterize known liabilities and missing risk evidence; no returned record is not evidence of safety.",
    },
    "CTX_TRANSLATIONAL": {
        "DOM_TRANSCRIPTOMIC_DISCOVERY": "Relevant to patient-tumour molecular context, but bulk tumour association does not establish clinical utility.",
        "DOM_DISEASE_ASSOCIATION": "Required to establish traceable LUAD relevance for the translational hypothesis.",
        "DOM_GENETIC_EVIDENCE": "Relevant to patient subgroup, causal, or biomarker hypotheses; it does not establish treatment benefit.",
        "DOM_FUNCTIONAL_DEPENDENCY": "Relevant to mechanism and context of response; preclinical models do not establish patient efficacy.",
        "DOM_PHARMACOLOGY": "Required to link an intervention or modality to the target with interpretable mechanism and exposure context.",
        "DOM_TRACTABILITY": "Relevant to whether a clinically usable modality is plausible; source assessments are not clinical validation.",
        "DOM_CLINICAL_DEVELOPMENT": "Required at trial/intervention/disease resolution to support a claim of human investigation or development maturity.",
        "DOM_SAFETY": "Required for translational risk context; liability records do not alone determine a benefit-risk balance.",
    },
}

# Each entry states the maximum bounded interpretation of one ontology evidence
# type. Additional evidence names evidence classes, not target recommendations.
BOUNDARIES = {
    "EV_TCGA_DE_EFFECT": {
        "supports": "Direction and magnitude of a tumour-versus-normal RNA-expression association in the frozen TCGA-LUAD cohort.",
        "not": "Biological causality, cancer-cell dependency, therapeutic mechanism, drug efficacy, or intervention direction.",
        "additional": "Independent LUAD expression replication plus genetic or controlled perturbational evidence for causal interpretation.",
        "provenance": "Cohort definition|gene annotation|count processing|design and contrast|effect estimate|analysis commit",
        "dependency": "Shares the TCGA cohort and primary model with significance statistics; S1-S6 are related reanalyses, not independent replication.",
    },
    "EV_TCGA_DE_SIGNIFICANCE": {
        "supports": "Statistical evidence against the fitted model's null contrast after its stated multiple-testing procedure.",
        "not": "Biological importance, effect magnitude, causality, replication, druggability, or clinical relevance.",
        "additional": "Effect magnitude, model diagnostics, independent replication, and mechanistic evidence.",
        "provenance": "Cohort and design|contrast|test procedure|multiple-testing method|tested gene universe|analysis commit",
        "dependency": "Derived from the same samples and model as the effect estimate; significance and effect are complementary fields, not separate votes.",
    },
    "EV_TCGA_DE_ROBUSTNESS": {
        "supports": "Sensitivity of the TCGA-LUAD expression result to prespecified related model specifications.",
        "not": "Independent biological replication, absence of bias, causality, efficacy, or clinical robustness.",
        "additional": "Independent-cohort replication and orthogonal biological validation.",
        "provenance": "Shared frozen cohort|S0-S6 model definitions|contrast consistency|residual degrees of freedom|analysis commits",
        "dependency": "All robustness models reuse the same frozen expression cohort and cannot be counted as independent datasets.",
    },
    "EV_OT_LUAD_DIRECT_ASSOCIATION": {
        "supports": "A source-native Open Targets association view directly linked to the LUAD disease identifier.",
        "not": "Causality, record independence, intervention efficacy, direction of action, or clinical validity.",
        "additional": "Datasource-level association records with upstream lineage plus independent genetic or functional evidence.",
        "provenance": "Open Targets release/API|target ID|LUAD disease ID|query|datasource records|retrieval timestamp",
        "dependency": "May reuse literature, genetics, clinical, or ChEMBL-derived records and overlaps the indirect association view.",
    },
    "EV_OT_LUAD_INDIRECT_ASSOCIATION": {
        "supports": "An ontology-expanded Open Targets association view involving LUAD-related descendant disease records.",
        "not": "A direct LUAD association, an independent validation of the direct view, causality, or therapeutic relevance.",
        "additional": "Direct disease-specific records and review of descendant disease relevance and upstream record overlap.",
        "provenance": "Open Targets release/API|target ID|disease ontology path|descendant IDs|source records|retrieval timestamp",
        "dependency": "Derived from the same platform framework as the direct view and contains overlapping disease evidence.",
    },
    "EV_OT_LITERATURE_COUNT": {
        "supports": "The number of literature occurrences returned by the defined Open Targets bibliography query.",
        "not": "Evidence quality, causal support, novelty, independent replication, or therapeutic value.",
        "additional": "Publication-level records with study design, claim relevance, duplication, and source-lineage review.",
        "provenance": "Platform release/API|query scope|filter definition|publication identifiers|retrieval timestamp",
        "dependency": "Literature occurrences may overlap association records and may contain multiple reports of the same underlying observation.",
    },
    "EV_GENETIC_CANCER": {
        "supports": "A future source-grounded relationship between inherited or tumour-acquired genetic alteration and LUAD biology.",
        "not": "Pharmacological tractability, therapeutic direction, efficacy, or equivalence between genetic loss and drug modulation.",
        "additional": "Variant-level QC, independent cohorts, functional perturbation, mechanism, and pharmacological validation.",
        "provenance": "Source release|cohort|alteration and gene identifiers|disease definition|statistical model|sample overlap",
        "dependency": "Future genetic evidence may share TCGA samples or may already contribute to Open Targets association evidence.",
    },
    "EV_FUNCTIONAL_CRISPR_DEPENDENCY": {
        "supports": "A future context-specific effect of gene perturbation on cancer-model fitness or function.",
        "not": "Patient benefit, universal tumour dependency, safe therapeutic window, drug efficacy, or clinical relevance.",
        "additional": "Independent screens, LUAD model coverage, rescue/orthogonal perturbation, in-vivo context, and normal-cell comparison.",
        "provenance": "Screen release|model and lineage|guide reagents|QC metrics|effect definition|replicate structure",
        "dependency": "Models, guides, or upstream screens can be reused across resources; lineage independence requires record-level review.",
    },
    "EV_CHEMBL_TARGET_ANNOTATION": {
        "supports": "The presence and annotation of a target entity in the frozen ChEMBL release.",
        "not": "Compound binding, potency, selectivity, mechanism, LUAD relevance, tractability, or clinical actionability.",
        "additional": "Assay- and compound-level activity records with target confidence, potency, mechanism, and selectivity context.",
        "provenance": "ChEMBL release|target ID|mapping basis|target type|annotation record|retrieval timestamp",
        "dependency": "Open Targets drug and tractability records may reuse ChEMBL target or compound information.",
    },
    "EV_OT_DRUG_CANDIDATE_COUNT": {
        "supports": "The source-native count of Open Targets drug or clinical-candidate records linked to the target query.",
        "not": "Compound quality, unique mechanisms, target validity, disease-specific efficacy, approval, or independent support.",
        "additional": "Record-level compounds, mechanisms, indications, phases, statuses, target linkage, and upstream-source deduplication.",
        "provenance": "Open Targets release/API|target ID|record identifiers|count definition|query|retrieval timestamp",
        "dependency": "Records may overlap ChEMBL and Open Targets tractability or clinical-precedence evidence.",
    },
    "EV_CHEMBL_COMPOUND_TARGET": {
        "supports": "A future source-grounded compound-target assay or mechanism observation at defined target confidence and activity context.",
        "not": "In-vivo efficacy, selectivity across biology, LUAD relevance, clinical benefit, or safety.",
        "additional": "Potency normalization, assay quality, selectivity panels, mechanism, target engagement, disease models, and exposure evidence.",
        "provenance": "ChEMBL release|compound/target/assay IDs|target confidence|activity type/value/unit|mechanism record",
        "dependency": "Compound records can be upstream of Open Targets drug and small-molecule tractability evidence.",
    },
    "EV_OT_TRACTABILITY_SM": {
        "supports": "A source-native Open Targets assessment of small-molecule tractability for the target.",
        "not": "Biological causality, compound efficacy, selectivity, disease relevance, safety, or development success.",
        "additional": "Bucket-level provenance, structural/ligand evidence, selective compounds, target engagement, and disease-model validation.",
        "provenance": "Open Targets release/API|target ID|modality|assessment and bucket identifiers|upstream evidence",
        "dependency": "Shares the Open Targets tractability framework and may reuse ChEMBL or clinical-precedence records.",
    },
    "EV_OT_TRACTABILITY_AB": {
        "supports": "A source-native Open Targets assessment of antibody tractability for the target.",
        "not": "Target accessibility in the relevant tumour, antibody efficacy, selectivity, safety, or clinical success.",
        "additional": "Cell-surface/accessibility evidence, target localization, antibody specificity, functional studies, and exposure context.",
        "provenance": "Open Targets release/API|target ID|antibody modality|assessment/bucket identifiers|upstream evidence",
        "dependency": "Shares the Open Targets framework and can overlap platform drug/candidate clinical precedent.",
    },
    "EV_OT_TRACTABILITY_PR": {
        "supports": "A source-native Open Targets assessment of PROTAC or targeted-protein-degradation tractability.",
        "not": "Degrader efficacy, ternary-complex formation, suitable tissue exposure, biological validity, safety, or clinical success.",
        "additional": "Ligand and E3 compatibility, degradation assays, selectivity, target resynthesis, disease-model response, and exposure evidence.",
        "provenance": "Open Targets release/API|target ID|degrader modality|assessment/bucket identifiers|upstream evidence",
        "dependency": "Shares source framework and may reuse ligandability or development-precedence records represented elsewhere.",
    },
    "EV_OT_TRACTABILITY_OC": {
        "supports": "A source-native Open Targets assessment for another clinically precedented modality category.",
        "not": "Feasibility of a specific unnamed modality, biological causality, efficacy, safety, or clinical success.",
        "additional": "Explicit modality identity, mechanism, target-access evidence, product-level precedent, and disease-context validation.",
        "provenance": "Open Targets release/API|target ID|explicit modality category|assessment/bucket identifiers|upstream evidence",
        "dependency": "Other-clinical-modality assessments may encode clinical precedent also represented in drug or trial records.",
    },
    "EV_CLINICAL_TRIAL_DEVELOPMENT": {
        "supports": "A future trial-level record that target modulation or a linked intervention entered human investigation in a defined disease context.",
        "not": "Efficacy, target validity, approval, successful completion, patient benefit, or a favorable benefit-risk balance.",
        "additional": "Verified intervention-target linkage, trial status/phase, disease relevance, results, endpoints, exposure, and safety outcomes.",
        "provenance": "Registry and version|trial ID|intervention ID|target-linkage basis|disease ID|phase/status|retrieval timestamp",
        "dependency": "Trial records may overlap Open Targets candidate counts and tractability clinical-precedence assessments.",
    },
    "EV_OT_SAFETY_LIABILITY": {
        "supports": "A curated Open Targets safety-liability observation with its reported context and source lineage.",
        "not": "Causal on-target toxicity, incidence, dose relationship, complete risk, target rejection, or safety when records are absent.",
        "additional": "Record-level on/off-target attribution, exposure, normal-tissue expression, essentiality, toxicology, clinical outcomes, and replication.",
        "provenance": "Open Targets release/API|target ID|liability and datasource IDs|study/publication|context|retrieval timestamp",
        "dependency": "Multiple liability records may share a datasource, study, publication, event, compound, or mechanism.",
    },
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
        fail(result.stderr.decode(errors="replace").strip())
    return {item.decode("utf-8") for item in result.stdout.split(b"\0") if item}


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            fail(f"Missing CSV header: {relative(path)}")
        return list(reader.fieldnames), list(reader)


def read_key_values(path: Path) -> dict[str, str]:
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value
    return values


def validate_repository() -> dict[str, str]:
    branch = run_git("branch", "--show-current")
    head = run_git("rev-parse", "HEAD")
    remote = run_git("remote", "get-url", "origin")
    if branch != EXPECTED_BRANCH:
        fail(f"Expected branch {EXPECTED_BRANCH!r}; observed {branch!r}.")
    if EXPECTED_REMOTE_FRAGMENT not in remote:
        fail(f"Unexpected origin remote: {remote!r}.")
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", TASK018_BASE_COMMIT, "HEAD"],
        cwd=ROOT,
        check=False,
    ).returncode != 0:
        fail(f"Frozen Task #018 commit is not an ancestor of HEAD {head}.")
    if run_git("diff", "--name-only") or run_git("diff", "--cached", "--name-only"):
        fail("Unexpected tracked or staged working-tree changes exist.")

    untracked = git_paths("ls-files", "--others", "--exclude-standard")
    unexpected = {
        path
        for path in untracked
        if not (path in ALLOWED_UNTRACKED_FILES or path.startswith(ALLOWED_UNTRACKED_PREFIX))
    }
    if unexpected:
        fail(f"Unexpected untracked paths exist: {sorted(unexpected)}")

    for path in INPUTS.values():
        rel = relative(path)
        if not path.is_file():
            fail(f"Frozen input is missing: {rel}")
        if not run_git("ls-files", "--error-unmatch", rel, check=False):
            fail(f"Frozen input is not committed: {rel}")
        if run_git("diff", "--name-only", TASK018_BASE_COMMIT, "HEAD", "--", rel):
            fail(f"Frozen input changed after Task #018: {rel}")

    return {"branch": branch, "head": head, "remote": remote}


def validate_frozen_hashes() -> dict[str, str]:
    observed = {}
    for name, path in INPUTS.items():
        actual = sha256(path)
        if actual != EXPECTED_HASHES[name]:
            fail(
                f"Hash mismatch for {relative(path)}: expected {EXPECTED_HASHES[name]}, "
                f"observed {actual}."
            )
        observed[name] = actual
    return observed


def validate_task018_governance() -> tuple[int, int]:
    _, manifest = read_csv(INPUTS["artifact_manifest"])
    if len(manifest) != 193:
        fail(f"Expected 193 Task #018 manifest rows; observed {len(manifest)}.")
    if len({row["relative_path"] for row in manifest}) != len(manifest):
        fail("Task #018 manifest paths are not unique.")
    for row in manifest:
        path = ROOT / row["relative_path"]
        if not (path.is_file() or path.is_symlink()):
            fail(f"Task #018 governed artifact is missing: {row['relative_path']}")
        if path.lstat().st_size != int(row["file_size_bytes"]):
            fail(f"Task #018 governed artifact size changed: {row['relative_path']}")
        if sha256(path) != row["sha256"]:
            fail(f"Task #018 governed artifact hash changed: {row['relative_path']}")

    session = read_key_values(INPUTS["artifact_governance_session"])
    controls = {
        "outputs/artifact_governance/artifact_manifest.csv": INPUTS["artifact_manifest"],
        "outputs/artifact_governance/artifact_classification.csv": INPUTS["artifact_classification"],
        "outputs/artifact_governance/reproducibility_contract.md": INPUTS["reproducibility_contract"],
        "outputs/artifact_governance/artifact_governance_summary.md": INPUTS["artifact_governance_summary"],
    }
    for rel, path in controls.items():
        key = f"output_sha256.{rel}"
        if session.get(key) != sha256(path):
            fail(f"Task #018 session hash does not reconcile for {rel}.")
    return len(manifest), sum(row["artifact_class"] == "D" for row in manifest)


def validate_ontology_and_claims() -> tuple[
    dict[str, dict[str, str]], set[str], dict[str, int]
]:
    _, domain_rows = read_csv(INPUTS["domain_registry"])
    domains = {row["domain_id"]: row for row in domain_rows}
    if list(domains) != DOMAIN_ORDER or len(domains) != 8:
        fail("Evidence ontology domains or order differ from the frozen eight-domain vocabulary.")
    evidence_types = []
    for row in domain_rows:
        evidence_types.extend(row["evidence_type"].split("|"))
    if len(evidence_types) != 17 or len(set(evidence_types)) != 17:
        fail("Expected 17 unique ontology evidence types.")
    if set(BOUNDARIES) != set(evidence_types):
        fail("Interpretation boundaries do not cover exactly the ontology evidence types.")

    _, independence = read_csv(INPUTS["independence_map"])
    if len(independence) != 31:
        fail(f"Expected 31 ontology independence relationships; observed {len(independence)}.")
    for row in independence:
        pair = row["evidence_pair"].split(" vs ")
        if len(pair) != 2 or not set(pair).issubset(evidence_types):
            fail(f"Invalid ontology evidence pair: {row['evidence_pair']}")

    _, source_lineage = read_csv(INPUTS["source_lineage"])
    if len(source_lineage) != 6 or len({row["source_id"] for row in source_lineage}) != 6:
        fail("Expected six unique ontology source-lineage entities.")

    _, claims = read_csv(INPUTS["claim_registry"])
    claim_types = {row["claim_type"] for row in claims}
    claim_domains = {row["domain_id"] for row in claims}
    if len(claims) != 148_030:
        fail(f"Expected 148,030 claim rows; observed {len(claims)}.")
    if claim_domains != CURRENT_CLAIM_DOMAINS or len(claim_types) != 5:
        fail("Current claim-domain/type coverage differs from Task #014.")

    _, dependencies = read_csv(INPUTS["dependency_graph"])
    if len(dependencies) != 77_202:
        fail(f"Expected 77,202 claim dependency edges; observed {len(dependencies)}.")
    _, sources = read_csv(INPUTS["source_entity_registry"])
    if len(sources) != 6 or len({row["source_id"] for row in sources}) != 6:
        fail("Expected six claim-architecture source entities.")

    return domains, set(evidence_types), {
        "domain_count": len(domains),
        "evidence_type_count": len(evidence_types),
        "independence_relationship_count": len(independence),
        "source_lineage_count": len(source_lineage),
        "claim_count": len(claims),
        "claim_type_count": len(claim_types),
        "claim_dependency_count": len(dependencies),
        "claim_source_count": len(sources),
    }


def joined_domains(values: set[str]) -> str:
    return "|".join(domain for domain in DOMAIN_ORDER if domain in values) or "NONE"


def build_context_registry() -> list[dict[str, str]]:
    rows = []
    for context in CONTEXTS:
        rows.append(
            {
                "decision_context_id": context["id"],
                "decision_context": context["name"],
                "scientific_question": context["question"],
                "required_evidence_domains": joined_domains(context["required"]),
                "relevant_evidence_domains": joined_domains(context["relevant"]),
                "optional_evidence_domains": joined_domains(context["optional"]),
                "not_applicable_evidence_domains": joined_domains(context["not_applicable"]),
                "interpretation_limits": context["interpretation"],
                "evidence_generation_boundary": context["generation_boundary"],
                "missing_required_evidence_rule": context["status_rule"],
                "provenance_requirement": "Evidence record → source entity → source release/query → dependency lineage → frozen artifact hash.",
            }
        )
    return rows


def build_context_matrix(domains: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for context in CONTEXTS:
        partitions = {
            "REQUIRED": context["required"],
            "RELEVANT": context["relevant"],
            "OPTIONAL": context["optional"],
            "NOT_APPLICABLE": context["not_applicable"],
        }
        for domain_id in DOMAIN_ORDER:
            levels = [level for level, values in partitions.items() if domain_id in values]
            if len(levels) != 1:
                fail(f"Domain {domain_id} does not have exactly one support level in {context['id']}.")
            rows.append(
                {
                    "evidence_domain": domain_id,
                    "decision_context": context["name"],
                    "support_level": levels[0],
                    "interpretation_note": MATRIX_NOTES[context["id"]][domain_id],
                }
            )
    return rows


def build_boundary_registry(domains: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for domain_id in DOMAIN_ORDER:
        for evidence_type in domains[domain_id]["evidence_type"].split("|"):
            boundary = BOUNDARIES[evidence_type]
            rows.append(
                {
                    "evidence_type": evidence_type,
                    "evidence_domain": domain_id,
                    "claim_architecture_state": (
                        "FUTURE_COMPATIBLE_NOT_QUERIED"
                        if evidence_type in FUTURE_EVIDENCE_TYPES
                        else "CURRENT_BOUNDED_CLAIM_ARCHITECTURE"
                    ),
                    "what_it_supports": boundary["supports"],
                    "what_it_does_not_support": boundary["not"],
                    "additional_evidence_required": boundary["additional"],
                    "provenance_requirement": boundary["provenance"],
                    "dependency_warning": boundary["dependency"],
                }
            )
    return rows


def validate_outputs(
    contexts: list[dict[str, str]],
    matrix: list[dict[str, str]],
    boundaries: list[dict[str, str]],
    evidence_types: set[str],
) -> list[dict[str, str]]:
    checks = []

    def check(name: str, passed: bool, observed: object, expected: object, detail: str) -> None:
        checks.append(
            {
                "check": name,
                "status": "PASS" if passed else "FAIL",
                "observed": str(observed),
                "expected": str(expected),
                "detail": detail,
            }
        )
        if not passed:
            fail(f"Output validation failed: {name}")

    matrix_keys = {(row["evidence_domain"], row["decision_context"]) for row in matrix}
    boundary_types = {row["evidence_type"] for row in boundaries}
    check("three_contexts", len(contexts) == 3, len(contexts), 3, "Exactly the prespecified decision contexts.")
    check("context_ids_unique", len({row["decision_context_id"] for row in contexts}) == 3, len({row["decision_context_id"] for row in contexts}), 3, "Stable context identifiers.")
    check("matrix_complete", len(matrix) == 24 and len(matrix_keys) == 24, len(matrix_keys), 24, "Eight ontology domains by three contexts.")
    check("support_vocabulary", {row["support_level"] for row in matrix}.issubset(SUPPORT_LEVELS), sorted({row["support_level"] for row in matrix}), sorted(SUPPORT_LEVELS), "Qualitative support roles only.")
    check("boundary_complete", len(boundaries) == 17 and boundary_types == evidence_types, len(boundary_types), 17, "One boundary per ontology evidence type.")
    check("future_types_explicit", sum(row["claim_architecture_state"] == "FUTURE_COMPATIBLE_NOT_QUERIED" for row in boundaries) == 4, sum(row["claim_architecture_state"] == "FUTURE_COMPATIBLE_NOT_QUERIED" for row in boundaries), 4, "No future-compatible type is presented as observed.")
    check("nonblank_cells", all(all(value != "" for value in row.values()) for table in (contexts, matrix, boundaries) for row in table), "all nonblank", "all nonblank", "Interpretation and provenance are explicit.")
    fields = set().union(*(row.keys() for table in (contexts, matrix, boundaries) for row in table))
    forbidden = fields.intersection(FORBIDDEN_EXACT_COLUMNS)
    check("forbidden_fields_absent", not forbidden, sorted(forbidden), [], "No target-assessment fields.")
    return checks


def write_csv(path: Path, fields: list[str], rows: Iterable[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_summary(
    contexts: list[dict[str, str]],
    matrix: list[dict[str, str]],
    boundaries: list[dict[str, str]],
    checks: list[dict[str, str]],
) -> None:
    level_counts = defaultdict(Counter)
    for row in matrix:
        level_counts[row["decision_context"]][row["support_level"]] += 1
    lines = [
        "# Task #019 decision-context framework summary",
        "",
        f"**Decision contexts:** {len(contexts)}  ",
        f"**Evidence-context relationships:** {len(matrix)}  ",
        f"**Evidence-type interpretation boundaries:** {len(boundaries)}  ",
        f"**Validation checks passed:** {sum(row['status'] == 'PASS' for row in checks)}/{len(checks)}  ",
        "**Gene or target evaluation performed:** No",
        "",
        "## Contexts",
        "",
    ]
    for context in contexts:
        lines.extend(
            [
                f"### {context['decision_context']}",
                "",
                f"**Question:** {context['scientific_question']}",
                "",
                f"**Required domains:** `{context['required_evidence_domains']}`",
                "",
                context["interpretation_limits"],
                "",
            ]
        )
    lines.extend(
        [
            "## Support-role counts",
            "",
            "| Context | Required | Relevant | Optional | Not applicable |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for context in contexts:
        counts = level_counts[context["decision_context"]]
        lines.append(
            f"| {context['decision_context']} | {counts['REQUIRED']} | {counts['RELEVANT']} | "
            f"{counts['OPTIONAL']} | {counts['NOT_APPLICABLE']} |"
        )
    lines.extend(
        [
            "",
            "## Central interpretation rules",
            "",
            "- `REQUIRED` means the domain must be adequately characterized before the stated context can be interpreted as supported. It is not a numerical weight.",
            "- Missing required evidence leaves the context unresolved; it does not count against the gene and is not negative evidence.",
            "- `RELEVANT` qualifies or challenges the interpretation but cannot substitute automatically for a required domain.",
            "- `OPTIONAL` can add context but is neither necessary nor sufficient for the context question.",
            "- `NOT_APPLICABLE` means the domain does not directly support that specific question; its evidence remains available for other contexts.",
            "- Evidence counts and multiple fields from shared sources are not independent votes.",
            "- Every interpretation must retain record, source, release/query, dependency lineage, and frozen artifact hash.",
            "",
            "## Evidence generation versus decision interpretation",
            "",
            "This framework defines which evidence can inform each question and the maximum conclusion allowed from each evidence type. It does not retrieve, generate, transform, or aggregate scientific evidence. Four ontology types—cancer genetics, CRISPR dependency, compound-target evidence, and trial-level development—remain future-compatible and `NOT_QUERIED` in the current architecture.",
            "",
            "## Explicit non-claims",
            "",
            "No gene was assessed. No evidence was converted into a score, ordering, candidate selection, target recommendation, intervention mechanism, or therapeutic direction. The framework does not establish causality, efficacy, safety, clinical benefit, or a benefit-risk balance.",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate_postflight(start_head: str) -> None:
    if run_git("rev-parse", "HEAD") != start_head:
        fail("Git HEAD changed during Task #019.")
    if run_git("diff", "--name-only") or run_git("diff", "--cached", "--name-only"):
        fail("An existing tracked file changed during Task #019.")
    validate_frozen_hashes()
    validate_task018_governance()


def write_session(
    started: datetime,
    git_info: dict[str, str],
    frozen_hashes: dict[str, str],
    input_counts: dict[str, int],
    checks: list[dict[str, str]],
) -> None:
    values = {
        "task": "019",
        "purpose": "qualitative decision context calibration framework",
        "started_at_utc": started.isoformat(),
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "git_branch": git_info["branch"],
        "git_head_before": git_info["head"],
        "git_head_after": run_git("rev-parse", "HEAD"),
        "git_origin": git_info["remote"],
        "frozen_task018_base_commit": TASK018_BASE_COMMIT,
        "decision_context_count": "3",
        "evidence_context_matrix_row_count": "24",
        "interpretation_boundary_count": "17",
        "network_access": "NOT_USED",
        "packages_installed_or_updated": "FALSE",
        "existing_files_modified": "FALSE",
        "scoring_generated": "FALSE",
        "ranking_generated": "FALSE",
        "candidate_selection_generated": "FALSE",
        "target_recommendations_generated": "FALSE",
        "therapeutic_direction_generated": "FALSE",
        "git_commit_or_push": "FALSE",
        "script_sha256": sha256(SCRIPT_PATH),
        "plan_sha256": sha256(PLAN_PATH),
    }
    for name, value in input_counts.items():
        values[f"input_validation.{name}"] = str(value)
    for name, digest in frozen_hashes.items():
        values[f"frozen_input_sha256.{relative(INPUTS[name])}"] = digest
    for row in checks:
        values[f"output_validation.{row['check']}"] = row["status"]
    for path in (CONTEXT_PATH, MATRIX_PATH, BOUNDARY_PATH, SUMMARY_PATH):
        values[f"output_sha256.{relative(path)}"] = sha256(path)
    SESSION_PATH.write_text(
        "".join(f"{key}={values[key]}\n" for key in sorted(values)),
        encoding="utf-8",
    )


def main() -> None:
    started = datetime.now(timezone.utc)
    git_info = validate_repository()
    frozen_hashes = validate_frozen_hashes()
    artifact_count, class_d_count = validate_task018_governance()
    domains, evidence_types, counts = validate_ontology_and_claims()
    counts["task018_artifact_count"] = artifact_count
    counts["task018_class_d_count"] = class_d_count

    contexts = build_context_registry()
    matrix = build_context_matrix(domains)
    boundaries = build_boundary_registry(domains)
    checks = validate_outputs(contexts, matrix, boundaries, evidence_types)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    allowed = {
        CONTEXT_PATH.name,
        MATRIX_PATH.name,
        BOUNDARY_PATH.name,
        SUMMARY_PATH.name,
        SESSION_PATH.name,
    }
    unexpected = {path.name for path in OUTPUT_DIR.iterdir() if path.name not in allowed}
    if unexpected:
        fail(f"Unexpected Task #019 output files: {sorted(unexpected)}")

    write_csv(CONTEXT_PATH, list(contexts[0]), contexts)
    write_csv(MATRIX_PATH, ["evidence_domain", "decision_context", "support_level", "interpretation_note"], matrix)
    write_csv(BOUNDARY_PATH, list(boundaries[0]), boundaries)
    write_summary(contexts, matrix, boundaries, checks)
    validate_postflight(git_info["head"])
    write_session(started, git_info, frozen_hashes, counts, checks)

    print("Created files:")
    for path in (CONTEXT_PATH, MATRIX_PATH, BOUNDARY_PATH, SUMMARY_PATH, SESSION_PATH):
        print(f"- {relative(path)}")
    print(f"Decision contexts: {len(contexts)}")
    print(f"Evidence-context relationships: {len(matrix)}")
    print(f"Interpretation boundaries: {len(boundaries)}")
    print(f"Validation checks passed: {sum(row['status'] == 'PASS' for row in checks)}/{len(checks)}")
    print("No gene or target evaluation was performed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
