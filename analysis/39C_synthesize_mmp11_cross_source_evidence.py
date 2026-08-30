#!/usr/bin/env python3
"""Build the frozen Task #039C MMP11 cross-source evidence synthesis.

This script performs local, deterministic structural synthesis only. It does
not retrieve evidence, rerun analyses, score or rank targets, or issue a
therapeutic recommendation.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import platform
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASK_A = ROOT / "outputs" / "mmp11_internal_evidence_v0.1"
TASK_B = ROOT / "outputs" / "mmp11_external_evidence_v0.1"
OUT = ROOT / "outputs" / "mmp11_cross_source_synthesis_v0.1"
ENSEMBL_ID = "ENSG00000099953.9"
SYMBOL = "MMP11"
GENERATOR_VERSION = "MMP11_CROSS_SOURCE_SYNTHESIS_GENERATOR_V0.1"
SYNTHESIS_VERSION = "MMP11_CROSS_SOURCE_SYNTHESIS_V0.1"
TASK_A_BASE_COMMIT = "dc5dc17"
TASK_B_BASE_COMMIT = "5f67014"
DISCLAIMER = (
    "MMP11 is an illustrative LUAD worked example. This synthesis organizes "
    "frozen evidence and dependencies; it is not a target score, ranking, "
    "therapeutic validation, clinical-efficacy claim, or recommendation."
)

TASK_A_HASHES = {
    "mmp11_identity.json": "caeb90f8ecef320a02db10ce9a396dcc77f17fc126e6c3f5b788349bfa2e8ae3",
    "mmp11_transcriptomic_evidence.csv": "30104ce14fa7211883e69c337f354e64560ae916fed67ade62a0b385a63bd57a",
    "mmp11_sensitivity_evidence.csv": "a4032761eb37207637bcc1c50397314353187b736d9a575886ba281fcbe0f0c9",
    "mmp11_component_summary.json": "85d3bb3e4e73613bc2362f722b305d09f8577f0eaf28aa84e0aab729a2d60ee5",
    "mmp11_provenance_links.csv": "8b51cb282caa55504dd3b0b16c8cfecef5ec5be400042eb1de3605b86b0f18a3",
    "mmp11_dependency_map.csv": "76306760de5c6c37321ab5e30b5c8f9e361ef0b3be42826920fd4f045a4d577d",
    "mmp11_claim_boundary.md": "8da1472467dd90d10a28a85fdc7c3b2b0f1482c38f75ffc44cd86860719353ea",
    "mmp11_internal_evidence_summary.md": "886ac61d2cb2de5d47a761c3a5c9068441a58660afdb1a029b91a684122e5c20",
    "validation_report.md": "ad8986ddd3431b77f7b8bf00462ebff9cdbc98ad2d98acd0ad4d5ebaa80c2cc1",
}

TASK_B_HASHES = {
    "search_strategy.json": "d875e32517deeaa8584a70448da5f578fde297990cf594b3c30a19b69654cc04",
    "publication_registry.csv": "fddb058699173a666d1563e9effaa5e291202914af3928615e3a3c78f35206c0",
    "external_evidence_registry.csv": "bd2c56a2c90f132be88630d2c5d2d7515f99e024366956eaa8c5f440c6e56a1d",
    "experimental_model_registry.csv": "7c64500b6eb3add7e2c9a33f5fa2c263670454e5d9413dcc8d3b473132d89d6e",
    "dataset_registry.csv": "5ee06213fdc7590eee2d9c41df84abf0145b2f443de66ccf23a27a88b330f86c",
    "external_provenance_links.csv": "dc57d328c8b78e67e0122a526b4f0729751c91733fc363ea0f538df3aafe9bf9",
    "external_dependency_map.csv": "e1838f91a3dc45706421035e868f671b5259910b0721a795c799e0c2f0c2af99",
    "evidence_exclusion_log.csv": "06478cf480004f2cc30e8075590826f3557efc71fff0b75973c555c0d7157c96",
    "external_claim_boundary.md": "51ef7fe9a0295a0cac22daa9a1572a900f222f0684b665f900e2da4a0a38dfe2",
    "mmp11_external_evidence_summary.md": "958df078cee0785f5e39f26de1cc2b51b6284ab6ba2ebb1ba6ad964d29a76929",
    "validation_report.md": "163b48eff30572b918f5e783fb16f2fd234c603d6d3f6517826903851609e29d",
    "session_info.txt": "b11a028dce7b1aaaada39435d751c1b5d20dad9dd7b7b9c089b6e62d6e14e103",
}

STRUCTURAL_OUTPUT_HASHES = {
    "evidence_family_registry.csv": "543f9955935cf3c0a0549f3d262373d7ef3011ebf285a344cf05dc93e735a2a2",
    "cross_source_dependency_map.csv": "1b3d3832b0b5beb81f853c43a74f8af9a82947702fd562663543275ee8f02f62",
    "claim_registry.csv": "dad160774617d7dcb8e76d696cb5723f35b4634e43fa6f3aef9843691f289b7b",
    "claim_evidence_matrix.csv": "78520330731d261cbfb6513845dd702bf9d9e6e6a2bdbb4448c0717cced208c0",
    "claim_dependency_audit.csv": "e41ec912b3893ea0cd3554dd0fac74ca77d19ac3211fe942ff6578e91f96b1c4",
    "modality_summary.csv": "693306bfb01cc70a4da712d96f90997c78a2006917fbe3875e37ffa7f137d282",
    "translational_boundary.json": "c64257dfa723ff2fea0674efae30966a7318b13dd671669372be67d49de598ab",
    "presentation_claim_candidates.json": "998dedf501465914385fe1316868c88c8e2ca6b0668c3e4bc06bd3e699e4cb1f",
}

ALLOWED_RELATIONSHIPS = {
    "SHARED_DATASET", "SHARED_PUBLICATION", "SHARED_EXPERIMENT",
    "SHARED_MODEL_SYSTEM", "SHARED_REAGENT", "DERIVED_REPRESENTATION",
    "DERIVED_REANALYSIS", "SAME_COHORT", "PARTIAL_COHORT_OVERLAP",
    "POSSIBLE_DEPENDENCY", "UNKNOWN", "NO_DEPENDENCY_IDENTIFIED",
    "SAME_SOURCE",
}
ALLOWED_CLAIM_RELATIONSHIPS = {
    "DIRECT_SUPPORT", "CONTEXTUAL_SUPPORT", "NULL_IN_CONTEXT",
    "LIMITS_GENERALIZATION", "INSUFFICIENTLY_SPECIFIC",
    "DEPENDENT_CORROBORATION", "NOT_APPLICABLE",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def stable_id(prefix: str, *parts: object) -> str:
    value = "||".join(str(x) for x in parts)
    return f"{prefix}_{hashlib.sha256(value.encode()).hexdigest()[:20].upper()}"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    fields = fields or (list(rows[0]) if rows else [])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def unique_ordered(values: list[str]) -> list[str]:
    return list(dict.fromkeys(x for x in values if x and x not in {"NONE", "NOT_APPLICABLE"}))


def safe_token(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", value.upper()).strip("_")


def git_is_ancestor(commit: str) -> bool:
    return subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=ROOT,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0


def tracked_worktree_is_clean() -> bool:
    """Allow new Task #039C files while rejecting changes to tracked artifacts."""
    unstaged = subprocess.run(
        ["git", "diff", "--quiet"], cwd=ROOT,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0
    staged = subprocess.run(
        ["git", "diff", "--cached", "--quiet"], cwd=ROOT,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0
    return unstaged and staged


def has_no_network_client_imports() -> bool:
    """Fail closed on executable imports of common Python network clients."""
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    prohibited = {"requests", "urllib", "httpx", "aiohttp"}
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".", 1)[0])
    return prohibited.isdisjoint(imported)


def input_hashes() -> dict[str, dict[str, str]]:
    return {
        "task039a": {name: sha256(TASK_A / name) for name in TASK_A_HASHES},
        "task039b": {name: sha256(TASK_B / name) for name in TASK_B_HASHES},
    }


def assign_external_family(row: dict[str, str]) -> tuple[str, str, str, str]:
    """Assign exactly one primary lineage family without implying independence."""
    eid = row["external_evidence_id"]
    dataset = row["dataset_or_cohort"]
    domain = row["evidence_domain"]

    if "TCGA-LUAD" in dataset:
        return (
            "FAM_EXTERNAL_TCGA_REANALYSIS", "EXTERNAL_TCGA_REANALYSIS",
            "Published TCGA-LUAD reanalysis lineage",
            "Shares TCGA-LUAD biological dataset lineage with Task #039A and is not independent transcriptomic replication.",
        )
    special = {
        "EXT_31024988_01": ("FAM_GEO_JOINT_2019", "GEO_TRANSCRIPTOMIC_LINEAGE", "2019 joint GEO analysis", "One published evidence unit jointly derived from GSE7670, GSE10072, GSE68465, and GSE43458; not four published findings."),
        "EXT_40386736_01": ("FAM_GEO_MULTI_2025", "GEO_TRANSCRIPTOMIC_LINEAGE", "2025 mixed-histology GEO reanalysis", "One analysis spanning GSE33479, GSE18842, and GSE32863; histology specificity differs by accession."),
        "EXT_40826767_01": ("FAM_GEO_COPD_NSCLC_REUSE", "GEO_TRANSCRIPTOMIC_LINEAGE", "COPD/NSCLC GEO derived reanalysis", "Reuses GSE10072 and GSE18842 from other published analyses."),
        "EXT_34671675_01": ("FAM_GEO_GSE19804", "GEO_TRANSCRIPTOMIC_LINEAGE", "GSE19804 paired lung-tissue lineage", "Potentially distinct dataset lineage, but LUAD histology is incompletely resolved."),
        "EXT_23659968_01": ("FAM_GEO_GSE43458_PRIMARY", "GEO_TRANSCRIPTOMIC_LINEAGE", "GSE43458 primary publication lineage", "Shares GSE43458 with the 2019 joint GEO analysis and Task #039A Expression Atlas lineage."),
        "EXT_15653641_01": ("FAM_ARRAY_E_MEXP_231", "GEO_TRANSCRIPTOMIC_LINEAGE", "E-MEXP-231 array lineage", "Shares source-dataset lineage with Task #039A Expression Atlas evidence."),
        "EXT_25141350_01": ("FAM_GEO_GSE43767", "GEO_TRANSCRIPTOMIC_LINEAGE", "GSE43767 developmental/LUAD lineage", "Shares source-dataset lineage with Task #039A and mixes developmental and tumour contexts."),
        "EXT_39672019_01": ("FAM_SINGLE_CELL_LUAD_2025", "EXTERNAL_TRANSCRIPTOMIC_CONTEXT", "LUAD single-cell myofibroblast observation", "Accession unresolved; marker status is not a causal result."),
        "EXT_40552583_01": ("FAM_PANCANCER_SINGLE_CELL_LUAD", "EXTERNAL_TRANSCRIPTOMIC_CONTEXT", "Pan-cancer single-cell LUAD-resolved observation", "Primary paper context is bladder cancer; LUAD observation is contextual."),
        "EXT_31024988_05": ("FAM_CELL_PERTURBATION_310_A549_PC9", "CELL_FUNCTIONAL_PERTURBATION", "2019 LUAD-cell depletion lineage", "Shares publication, A549/PC9 models, and some experimental lineage with other readouts."),
        "EXT_31024988_06": ("FAM_CELL_PERTURBATION_310_A549_PC9", "MECHANISTIC", "2019 LUAD-cell depletion lineage", "AKT readout shares the A549 depletion experiment and does not establish a complete mechanism."),
        "EXT_31024988_07": ("FAM_CELL_PERTURBATION_310_PC9_RESCUE", "CELL_FUNCTIONAL_PERTURBATION", "2019 PC9 depletion/rescue lineage", "Rescue is within the same publication and model system, not an external replication."),
        "EXT_31024988_08": ("FAM_CELL_PERTURBATION_310_A549_PC9", "CELL_FUNCTIONAL_PERTURBATION", "2019 LUAD-cell depletion lineage", "Migration/invasion readouts share cell and experiment lineage with depletion studies."),
        "EXT_31024988_09": ("FAM_ANTIBODY_INTERVENTION_310", "ANTIBODY_INTERVENTION", "2019 anti-MMP11 intervention lineage", "Shares publication and antibody reagent with migration and xenograft experiments."),
        "EXT_31024988_10": ("FAM_ANTIBODY_INTERVENTION_310", "ANTIBODY_INTERVENTION", "2019 anti-MMP11 intervention lineage", "Shares publication and antibody reagent with growth and xenograft experiments."),
        "EXT_31024988_11": ("FAM_XENOGRAFT_DEPLETION_310", "XENOGRAFT_DEPLETION", "2019 genetic-depletion xenograft lineage", "Preclinical A549 immunodeficient-mouse model; not clinical efficacy."),
        "EXT_31024988_12": ("FAM_ANTIBODY_INTERVENTION_310", "ANTIBODY_INTERVENTION", "2019 anti-MMP11 intervention lineage", "One evidence unit is both an intervention-domain record and an in-vivo experiment; it must not be duplicated."),
    }
    if eid in special:
        return special[eid]

    if dataset.startswith("COHORT_") or dataset.startswith("LUAD_") or dataset.startswith("KM_") or dataset.startswith("DATASET_"):
        if domain == "B_PROTEIN_TISSUE":
            family_type = "HUMAN_SERUM" if "SERUM" in dataset or "serum" in row["model_system"].lower() else "HUMAN_TISSUE_PROTEIN"
        elif domain == "C_CLINICAL_ASSOCIATION":
            family_type = "CLINICAL_ASSOCIATION"
        elif domain == "E_MECHANISTIC":
            family_type = "MECHANISTIC"
        elif domain == "A_TRANSCRIPTOMIC_EXPRESSION":
            family_type = "EXTERNAL_TRANSCRIPTOMIC_CONTEXT"
        else:
            family_type = "OBSERVATIONAL_COHORT"
        return (
            f"FAM_{safe_token(dataset)}", family_type,
            f"{dataset} lineage", "Observations share the named cohort/dataset; absence of another edge does not prove independence.",
        )
    if dataset.startswith("MODEL_"):
        family_type = {
            "D_FUNCTIONAL_PERTURBATION": "CELL_FUNCTIONAL_PERTURBATION",
            "E_MECHANISTIC": "MECHANISTIC",
            "F_IN_VIVO": "XENOGRAFT_DEPLETION",
            "G_INTERVENTION": "ANTIBODY_INTERVENTION",
        }.get(domain, "EXPERIMENTAL_MODEL")
        return (
            f"FAM_{safe_token(dataset)}", family_type,
            f"{dataset} model lineage", "Model-system observations are bounded to the source experiment and publication.",
        )
    if "|" in dataset or dataset.startswith("GSE") or dataset.startswith("E-"):
        return (
            f"FAM_DATASET_{safe_token(dataset)}", "GEO_TRANSCRIPTOMIC_LINEAGE",
            f"{dataset} transcriptomic lineage", "Dataset reuse must be assessed at accession level and is not an automatic independent replication.",
        )
    raise AssertionError(f"No governed family assignment for {eid}: {dataset}")


def build_families(
    transcript: list[dict[str, str]], sensitivity: list[dict[str, str]],
    external: list[dict[str, str]], ext_prov: list[dict[str, str]],
) -> tuple[list[dict[str, str]], dict[str, str]]:
    external_family: dict[str, str] = {}
    groups: dict[str, dict[str, Any]] = {}
    prov_by_eid = {x["external_evidence_id"]: x["external_provenance_link_id"] for x in ext_prov}

    for row in external:
        fid, family_type, name, boundary = assign_external_family(row)
        external_family[row["external_evidence_id"]] = fid
        group = groups.setdefault(fid, {
            "family_id": fid, "family_name": name, "family_type": family_type,
            "members": [], "datasets": [], "publications": [], "models": [],
            "domains": [], "statuses": [], "provenance": [], "boundary": boundary,
        })
        group["members"].append(row["external_evidence_id"])
        group["datasets"].extend(row["dataset_or_cohort"].split("|"))
        group["publications"].append(row["publication_id"])
        group["models"].append(row["model_system"])
        group["domains"].append(row["evidence_domain"])
        group["statuses"].append(row["evidence_status"])
        group["provenance"].append(prov_by_eid[row["external_evidence_id"]])

    rows: list[dict[str, str]] = [{
        "evidence_family_id": "FAM_PROJECT_TCGA_EXPRESSION",
        "EnsemblID": ENSEMBL_ID,
        "family_name": "Project TCGA-LUAD expression and prespecified sensitivity lineage",
        "family_type": "PROJECT_TCGA_EXPRESSION",
        "source_tasks": "TASK039A",
        "member_evidence_ids": "|".join(unique_ordered([transcript[0]["governed_evidence_record_id"], sensitivity[0]["governed_evidence_record_id"]])),
        "member_source_rows": "S0_PRIMARY|" + "|".join(x["model_id"] for x in sensitivity),
        "governed_evidence_record_count": "2",
        "source_row_count": str(1 + len(sensitivity)),
        "evidence_domains": "PROJECT_TRANSCRIPTOMICS",
        "evidence_statuses": "OBSERVED",
        "dataset_lineages": "TCGA-LUAD",
        "publication_lineages": "NOT_APPLICABLE",
        "model_lineages": "S0_PRIMARY|S1|S2|S3|S4|S5|S6",
        "dependency_boundary": "S1-S6 test robustness of the same TCGA-LUAD biological dataset and are not independent replication; downstream representations are derived, not new evidence.",
        "family_status": "LINEAGE_GROUP_DEFINED",
        "provenance_references": "outputs/mmp11_internal_evidence_v0.1/mmp11_transcriptomic_evidence.csv|outputs/mmp11_internal_evidence_v0.1/mmp11_sensitivity_evidence.csv|outputs/mmp11_internal_evidence_v0.1/mmp11_provenance_links.csv",
    }]
    for group in groups.values():
        rows.append({
            "evidence_family_id": group["family_id"], "EnsemblID": ENSEMBL_ID,
            "family_name": group["family_name"], "family_type": group["family_type"],
            "source_tasks": "TASK039B", "member_evidence_ids": "|".join(group["members"]),
            "member_source_rows": "|".join(group["members"]),
            "governed_evidence_record_count": str(len(group["members"])),
            "source_row_count": str(len(group["members"])),
            "evidence_domains": "|".join(unique_ordered(group["domains"])),
            "evidence_statuses": "|".join(unique_ordered(group["statuses"])),
            "dataset_lineages": "|".join(unique_ordered(group["datasets"])),
            "publication_lineages": "|".join(unique_ordered(group["publications"])),
            "model_lineages": "|".join(unique_ordered(group["models"])),
            "dependency_boundary": group["boundary"], "family_status": "LINEAGE_GROUP_DEFINED",
            "provenance_references": "|".join(unique_ordered(group["provenance"])),
        })
    rows.append({
        "evidence_family_id": "FAM_CLINICAL_DEVELOPMENT_CHECK", "EnsemblID": ENSEMBL_ID,
        "family_name": "Bounded frozen ClinicalTrials.gov lexical check", "family_type": "CLINICAL_DEVELOPMENT_CHECK",
        "source_tasks": "TASK039B", "member_evidence_ids": "SEARCH_CLINICALTRIALS_MMP11",
        "member_source_rows": "SEARCH_CLINICALTRIALS_MMP11", "governed_evidence_record_count": "0",
        "source_row_count": "1", "evidence_domains": "H_CLINICAL_DEVELOPMENT",
        "evidence_statuses": "NO_RELEVANT_RECORD_IDENTIFIED_IN_BOUNDED_SEARCH",
        "dataset_lineages": "NOT_APPLICABLE", "publication_lineages": "NOT_APPLICABLE",
        "model_lineages": "NOT_APPLICABLE",
        "dependency_boundary": "Five lexical hits were excluded as unrelated; bounded search absence is not proof that no study exists globally.",
        "family_status": "SEARCH_LINEAGE_GROUP_DEFINED",
        "provenance_references": "outputs/mmp11_external_evidence_v0.1/search_strategy.json|outputs/mmp11_external_evidence_v0.1/evidence_exclusion_log.csv",
    })
    return rows, external_family


def normalized_internal_relationship_types(source: dict[str, str]) -> list[str]:
    """Expand a Task #039A source record into atomic qualitative types."""
    transformation_types = {
        "SOURCE_RECORD_TO_COMPONENT_PROFILE", "SOURCE_RECORD_TO_COMPONENT",
        "COMPONENT_TO_MULTICOMPONENT_PROFILE", "PROFILE_TO_LANDSCAPE",
        "LANDSCAPE_TO_SUMMARY", "SUMMARY_TO_TRANSPARENT_STRUCTURAL_ROUTING",
    }
    return unique_ordered([
        "DERIVED_REPRESENTATION" if token in transformation_types else token
        for token in source["relationship_type"].split("|")
    ])


def normalize_dependencies(
    internal_deps: list[dict[str, str]], external_deps: list[dict[str, str]],
    external: list[dict[str, str]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    def add(dep_id: str, source_task: str, source_id: str, a: str, b: str,
            rel: str, level: str, scope: str, rationale: str, provenance: str) -> None:
        rows.append({
            "cross_source_dependency_id": dep_id, "EnsemblID": ENSEMBL_ID,
            "source_task": source_task, "source_relationship_id": source_id,
            "entity_a": a, "entity_b": b, "relationship_type": rel,
            "dependency_level": level, "lineage_scope": scope,
            "rationale": rationale,
            "independence_boundary": "A missing edge or NO_DEPENDENCY_IDENTIFIED does not prove statistical independence.",
            "provenance_reference": provenance,
        })

    for source in internal_deps:
        normalized = normalized_internal_relationship_types(source)
        for index, rel in enumerate(normalized, 1):
            add(
                source["dependency_relationship_id"] if len(normalized) == 1 else f"{source['dependency_relationship_id']}::{index}",
                "TASK039A", source["dependency_relationship_id"], source["record_or_artifact_a"],
                source["record_or_artifact_b"], rel, source["dependency_level"],
                source["relationship_block"], source["scientific_boundary"],
                "outputs/mmp11_internal_evidence_v0.1/mmp11_dependency_map.csv",
            )
    for source in external_deps:
        add(
            source["dependency_id"], "TASK039B", source["dependency_id"],
            source["source_evidence_id"], source["related_entity_id"],
            source["relationship_type"], source["dependency_level"], "EXTERNAL_EVIDENCE_LINEAGE",
            source["rationale"], "outputs/mmp11_external_evidence_v0.1/external_dependency_map.csv",
        )

    primary_id = "REC_1FDB3CAEC78761B6CDAC13A2"
    tcga_units = [x["external_evidence_id"] for x in external if "TCGA-LUAD" in x["dataset_or_cohort"]]
    for eid in tcga_units:
        add(stable_id("XDEP", primary_id, eid, "SHARED_DATASET"), "TASK039C", "SYNTHESIZED_CROSS_TASK",
            primary_id, eid, "SHARED_DATASET", "DEPENDENT_DATASET_LINEAGE", "CROSS_TASK_TCGA",
            "Project S0/S1-S6 and the published observation share TCGA-LUAD biological dataset lineage.",
            "Task039A transcriptomic records + Task039B dataset/dependency registries")

    for a, b in [("EXT_31024988_09", "EXT_31024988_10"), ("EXT_31024988_09", "EXT_31024988_12")]:
        add(stable_id("XDEP", a, b, "SHARED_REAGENT"), "TASK039C", "SYNTHESIZED_CROSS_TASK",
            a, b, "SHARED_REAGENT", "DEPENDENT_REAGENT_LINEAGE", "ANTIBODY_INTERVENTION",
            "Anti-MMP11 experiments share a reagent and publication while retaining experiment-specific distinctions.",
            "Task039B external evidence and dependency registries")

    overlap_pmids = ["31024988", "36756152", "35422093", "39904499", "40552583"]
    for pmid in overlap_pmids:
        alias, pub = f"TASK039A_OPEN_TARGETS_LITERATURE::PMID_{pmid}", f"PUB_PMID_{pmid}"
        add(stable_id("XDEP", alias, pub, "DERIVED_REPRESENTATION"), "TASK039C", "SYNTHESIZED_CROSS_TASK",
            alias, pub, "DERIVED_REPRESENTATION", "DEPENDENT_SOURCE_REPRESENTATION", "OPEN_TARGETS_PUBLICATION_OVERLAP",
            "The Open Targets literature representation and direct PubMed publication resolve to the same publication identifier.",
            "Task039A component summary + Task039B publication/dependency registries")

    overlap_datasets = ["GSE10072", "GSE18842", "GSE43458", "GSE43767", "E-MEXP-231"]
    for dataset in overlap_datasets:
        alias = f"TASK039A_OT_OR_EXPRESSION_ATLAS::{dataset}"
        add(stable_id("XDEP", alias, dataset, "SHARED_DATASET"), "TASK039C", "SYNTHESIZED_CROSS_TASK",
            alias, dataset, "SHARED_DATASET", "DEPENDENT_SOURCE_LINEAGE", "EXPRESSION_ATLAS_DATASET_OVERLAP",
            "The Task #039A source representation and Task #039B observation resolve to the same dataset accession.",
            "Task039A component summary + Task039B dataset/dependency registries")
    return rows


def claim_definitions() -> list[dict[str, str]]:
    claims = [
        ("MMP11_CLAIM_01", "MMP11 shows higher expression in LUAD tumour than normal tissue in the project TCGA-LUAD analysis.", "PROJECT_EXPRESSION", "BOUNDED_SUPPORTED", "The frozen S0 contrast reports logFC +5.18003235678542 and BH FDR 1.79025769607393e-37.", "Expression association does not establish disease causality or therapeutic actionability.", "State the Tumor-minus-Normal contrast and project-dataset boundary.", "Cell-type attribution and causal relevance remain unresolved."),
        ("MMP11_CLAIM_02", "The direction of the project-derived MMP11 tumour-normal association is concordant across all six prespecified sensitivity models.", "MODEL_ROBUSTNESS", "BOUNDED_SUPPORTED", "S1-S6 retain TUMOR_HIGHER direction and BH FDR below 0.05.", "Sensitivity models are not independent biological replications.", "State that all models use the same TCGA-LUAD biological dataset.", "Robust model direction cannot resolve dataset-specific bias or causality."),
        ("MMP11_CLAIM_03", "MMP11 tumour-associated expression observations exist in additional external transcriptomic datasets and analyses.", "EXTERNAL_TRANSCRIPTOMICS", "BOUNDED_SUPPORTED_WITH_DEPENDENCIES", "Eligible external transcriptomic observations include TCGA, GEO, array, and single-cell contexts.", "External TCGA reanalysis is not independent of the project dataset; histology and accession specificity vary.", "Separate same-dataset TCGA corroboration from potentially distinct accession-resolved GEO observations.", "Dataset reuse, mixed histology, and unresolved accessions limit replication claims."),
        ("MMP11_CLAIM_04", "MMP11 protein or tissue-associated observations have been reported in LUAD patient samples.", "HUMAN_TISSUE_PROTEIN", "BOUNDED_SUPPORTED_WITH_CONTEXT", "Eligible IHC, tissue-protein, serum, and stromal observations are retained by cohort.", "Protein or serum observation is not diagnostic validation or therapeutic causality.", "Identify cohort, assay, histology specificity, and tissue-versus-serum context.", "Small cohorts, mixed histology, localization, and diagnostic specificity remain limitations."),
        ("MMP11_CLAIM_05", "Experimental perturbation involving MMP11 altered growth-related and/or migration-invasion phenotypes in reported lung cancer cell models.", "CELL_FUNCTIONAL_PERTURBATION", "BOUNDED_SUPPORTED_WITH_CONTEXT", "Direct LUAD CRISPR/depletion/rescue observations and an insufficiently resolved lung-cancer axis study are represented separately.", "Cell-model perturbation does not establish patient efficacy or safety.", "Distinguish direct LUAD models from insufficiently histology-resolved rescue evidence.", "Off-target effects, model specificity, and cross-publication replication remain unresolved."),
        ("MMP11_CLAIM_06", "Preclinical xenograft experiments reported reduced tumour growth after MMP11 depletion or anti-MMP11 intervention.", "IN_VIVO_PRECLINICAL", "BOUNDED_SUPPORTED_PRECLINICAL", "One genetic-depletion xenograft and one antibody xenograft observation are retained.", "Xenograft response is not clinical efficacy or human safety.", "State that the antibody xenograft is one record classified under intervention but also in vivo.", "Both experiments arise from one publication and A549 xenograft context."),
        ("MMP11_CLAIM_07", "Clinical and prognostic associations involving MMP11 are context-dependent and include null findings.", "CLINICAL_ASSOCIATION", "BOUNDED_MIXED", "All seven null records, contextual results, and insufficiently LUAD-specific clinical associations are preserved.", "These records cannot be collapsed into a binary favourable/unfavourable vote.", "Report null findings and histology/cohort limitations alongside associations.", "Retrospective cohorts, computational predictions, mixed histology, and endpoint heterogeneity remain."),
        ("MMP11_CLAIM_08", "No relevant registered MMP11 clinical-development study was identified within the bounded frozen Task #039B ClinicalTrials.gov check.", "CLINICAL_DEVELOPMENT", "BOUNDED_SEARCH_RESULT", "Five lexical hits were screened and excluded as unrelated.", "Bounded search absence is not proof that no study exists globally.", "State the frozen query scope and lexical false-positive exclusions.", "Registry indexing, terminology, and future record changes limit the search conclusion."),
        ("MMP11_CLAIM_09", "Mechanistic and pathway observations involving MMP11 exist, but they remain model- and context-dependent.", "MECHANISTIC", "BOUNDED_CONTEXTUAL", "Regulatory, stromal, immune, signalling, and computational-network observations are represented.", "Association, downstream readout, or inferred network position is not a complete causal mechanism.", "Name the exact model, perturbation, and whether MMP11 itself was directly changed.", "Many records use downstream readouts, mixed NSCLC models, or unresolved dataset lineage."),
        ("MMP11_CLAIM_10", "Anti-MMP11 antibody experiments reported effects in bounded in-vitro and xenograft models.", "PRECLINICAL_INTERVENTION", "BOUNDED_SUPPORTED_PRECLINICAL", "Three antibody evidence units cover growth, migration, and xenograft readouts.", "Preclinical antibody effects do not establish clinical efficacy, safety, specificity, or validated intervention status.", "Retain shared publication, reagent, and model dependencies.", "Independent reagent validation, exposure, safety, and replication are unresolved."),
    ]
    fields = ["claim_id", "claim_statement", "claim_scope", "claim_status", "supported_interpretation", "not_supported", "required_qualifier", "major_remaining_uncertainty"]
    return [dict(zip(fields, row)) for row in claims]


def build_claim_matrix(
    claims: list[dict[str, str]], transcript: list[dict[str, str]], sensitivity: list[dict[str, str]],
    external: list[dict[str, str]], external_family: dict[str, str],
    ext_prov: list[dict[str, str]], ext_deps: list[dict[str, str]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    prov_by_eid = {x["external_evidence_id"]: x["external_provenance_link_id"] for x in ext_prov}
    deps_by_eid: dict[str, list[str]] = defaultdict(list)
    for dep in ext_deps:
        deps_by_eid[dep["source_evidence_id"]].append(dep["relationship_type"])

    def add(claim: str, evidence_id: str, selector: str, task: str, family: str,
            domain: str, status: str, relation: str, dataset: str, publication: str,
            model: str, dependency: str, provenance: str, limitation: str) -> None:
        rows.append({
            "claim_id": claim, "evidence_id": evidence_id,
            "source_record_selector": selector, "evidence_source_task": task,
            "evidence_family_id": family, "evidence_domain": domain,
            "evidence_status": status, "relationship_to_claim": relation,
            "dataset_lineage": dataset, "publication_lineage": publication,
            "model_lineage": model, "dependency_status": dependency,
            "provenance_reference": provenance, "major_limitation": limitation,
        })

    primary = transcript[0]
    add("MMP11_CLAIM_01", primary["governed_evidence_record_id"], primary["analysis_id"], "TASK039A",
        "FAM_PROJECT_TCGA_EXPRESSION", "PROJECT_TRANSCRIPTOMICS", "OBSERVED", "DIRECT_SUPPORT",
        "TCGA-LUAD", "NOT_APPLICABLE", "S0_PRIMARY", "PRIMARY_PROJECT_OBSERVATION",
        f"outputs/mmp11_internal_evidence_v0.1/mmp11_transcriptomic_evidence.csv#analysis_id={primary['analysis_id']}",
        "Bulk-tissue association does not establish causality or cell-type origin.")
    for sens in sensitivity:
        add("MMP11_CLAIM_02", sens["governed_evidence_record_id"], sens["model_id"], "TASK039A",
            "FAM_PROJECT_TCGA_EXPRESSION", "PROJECT_TRANSCRIPTOMICS", "OBSERVED", "DIRECT_SUPPORT",
            "TCGA-LUAD", "NOT_APPLICABLE", sens["model_id"], "SAME_DATASET_ROBUSTNESS|SHARED_DATASET",
            f"outputs/mmp11_internal_evidence_v0.1/mmp11_sensitivity_evidence.csv#model_id={sens['model_id']}",
            "Prespecified model variant on the same biological dataset; not independent replication.")

    claim_for_domain = {
        "A_TRANSCRIPTOMIC_EXPRESSION": "MMP11_CLAIM_03",
        "B_PROTEIN_TISSUE": "MMP11_CLAIM_04",
        "D_FUNCTIONAL_PERTURBATION": "MMP11_CLAIM_05",
        "C_CLINICAL_ASSOCIATION": "MMP11_CLAIM_07",
        "E_MECHANISTIC": "MMP11_CLAIM_09",
        "F_IN_VIVO": "MMP11_CLAIM_06",
        "G_INTERVENTION": "MMP11_CLAIM_10",
    }
    for ev in external:
        claim = claim_for_domain[ev["evidence_domain"]]
        if ev["evidence_status"] == "OBSERVED_NULL":
            relation = "NULL_IN_CONTEXT"
        elif ev["evidence_status"] == "CONTEXT_DEPENDENT":
            relation = "CONTEXTUAL_SUPPORT"
        elif ev["evidence_status"] == "INSUFFICIENTLY_SPECIFIC":
            relation = "INSUFFICIENTLY_SPECIFIC"
        elif "TCGA-LUAD" in ev["dataset_or_cohort"] and claim == "MMP11_CLAIM_03":
            relation = "DEPENDENT_CORROBORATION"
        else:
            relation = "DIRECT_SUPPORT"
        dep_types = unique_ordered(deps_by_eid[ev["external_evidence_id"]])
        add(claim, ev["external_evidence_id"], ev["external_evidence_id"], "TASK039B",
            external_family[ev["external_evidence_id"]], ev["evidence_domain"], ev["evidence_status"], relation,
            ev["dataset_or_cohort"], ev["publication_id"], ev["model_system"], "|".join(dep_types),
            prov_by_eid[ev["external_evidence_id"]], ev["major_limitation"])

    # The antibody xenograft is referenced by the in-vivo claim without creating
    # a second evidence record or second family membership.
    antibody_xeno = next(x for x in external if x["external_evidence_id"] == "EXT_31024988_12")
    add("MMP11_CLAIM_06", antibody_xeno["external_evidence_id"], antibody_xeno["external_evidence_id"], "TASK039B",
        external_family[antibody_xeno["external_evidence_id"]], antibody_xeno["evidence_domain"],
        antibody_xeno["evidence_status"], "DIRECT_SUPPORT", antibody_xeno["dataset_or_cohort"],
        antibody_xeno["publication_id"], antibody_xeno["model_system"],
        "SHARED_PUBLICATION|SHARED_REAGENT|SHARED_MODEL_SYSTEM",
        prov_by_eid[antibody_xeno["external_evidence_id"]],
        "Same single evidence unit is intervention-domain and in-vivo; audit references must not be summed as two observations.")

    add("MMP11_CLAIM_08", "SEARCH_CLINICALTRIALS_MMP11", "SEARCH_CLINICALTRIALS_MMP11", "TASK039B_SEARCH_STRATEGY",
        "FAM_CLINICAL_DEVELOPMENT_CHECK", "H_CLINICAL_DEVELOPMENT",
        "NO_RELEVANT_RECORD_IDENTIFIED_IN_BOUNDED_SEARCH", "DIRECT_SUPPORT", "NOT_APPLICABLE",
        "NOT_APPLICABLE", "NOT_APPLICABLE", "BOUNDED_SEARCH_RESULT",
        "outputs/mmp11_external_evidence_v0.1/search_strategy.json#SEARCH_CLINICALTRIALS_MMP11",
        "Search absence is bounded and external registries are mutable.")
    return rows


def claim_dependency_audit(
    claims: list[dict[str, str]], matrix: list[dict[str, str]],
) -> list[dict[str, str]]:
    claim_by_id = {x["claim_id"]: x for x in claims}
    rows = []
    for claim_id in claim_by_id:
        links = [x for x in matrix if x["claim_id"] == claim_id]
        dataset_counts = Counter(x["dataset_lineage"] for x in links if x["dataset_lineage"] != "NOT_APPLICABLE")
        pub_counts = Counter(x["publication_lineage"] for x in links if x["publication_lineage"] != "NOT_APPLICABLE")
        model_counts = Counter(x["model_lineage"] for x in links if x["model_lineage"] != "NOT_APPLICABLE")
        rows.append({
            "claim_id": claim_id,
            "total_linked_evidence_rows": str(len(links)),
            "unique_linked_evidence_ids": str(len({x["evidence_id"] for x in links})),
            "number_of_evidence_families": str(len({x["evidence_family_id"] for x in links})),
            "number_sharing_dataset_lineage": str(sum(v for v in dataset_counts.values() if v > 1)),
            "number_sharing_publication_lineage": str(sum(v for v in pub_counts.values() if v > 1)),
            "number_sharing_experimental_model": str(sum(v for v in model_counts.values() if v > 1)),
            "number_with_unresolved_dependency": str(sum("UNKNOWN" in x["dependency_status"] for x in links)),
            "null_evidence_present": str(any(x["evidence_status"] == "OBSERVED_NULL" for x in links)).upper(),
            "context_dependent_evidence_present": str(any(x["evidence_status"] == "CONTEXT_DEPENDENT" for x in links)).upper(),
            "insufficiently_specific_evidence_present": str(any(x["evidence_status"] == "INSUFFICIENTLY_SPECIFIC" for x in links)).upper(),
            "major_remaining_uncertainty": claim_by_id[claim_id]["major_remaining_uncertainty"],
            "count_semantics": "Audit metadata only; counts are not evidence strength or confidence.",
        })
    return rows


def modality_summary(matrix: list[dict[str, str]]) -> list[dict[str, str]]:
    specs = [
        ("PROJECT_TRANSCRIPTOMICS", ["MMP11_CLAIM_01", "MMP11_CLAIM_02"], "S0 plus six same-dataset sensitivity rows", "S0 and S1-S6 share TCGA-LUAD.", "No null model-direction record; robustness is same-dataset.", "Bulk expression association does not establish causality."),
        ("EXTERNAL_TRANSCRIPTOMICS", ["MMP11_CLAIM_03"], "External transcriptomic records", "Published TCGA shares project lineage; GEO accessions may be reused across papers.", "Context-dependent and insufficiently specific transcriptomic records remain visible.", "Accession, histology, and cohort provenance vary."),
        ("PROTEIN_TISSUE", ["MMP11_CLAIM_04"], "IHC, tissue protein, serum, and stromal observations", "Patient observations are grouped by cohort/publication.", "Context and insufficient-histology records remain visible.", "Observation is not diagnostic validation or therapeutic causality."),
        ("CLINICAL_ASSOCIATION", ["MMP11_CLAIM_07"], "Clinical, subgroup, survival, and prognosis records", "Some analyses share TCGA or the same clinical cohort.", "All seven Task #039B null records are retained.", "Endpoints and histology specificity are heterogeneous."),
        ("FUNCTIONAL_PERTURBATION", ["MMP11_CLAIM_05"], "Cell depletion, rescue, and phenotype records", "Several readouts share publication, model, and experiment lineage.", "One lung-cancer axis record is insufficiently LUAD-specific.", "Cell effects are not patient efficacy."),
        ("MECHANISTIC", ["MMP11_CLAIM_09"], "Signalling, regulatory, stromal, immune, and network records", "Many records are downstream or derived reanalyses.", "Context-dependent and unresolved-provenance records predominate.", "No complete causal mechanism is established."),
        ("IN_VIVO", ["MMP11_CLAIM_06"], "One depletion xenograft plus one antibody xenograft", "Both are from PMID 31024988; antibody xenograft is one record shared with intervention modality.", "No clinical outcome evidence.", "Immunodeficient subcutaneous models do not establish human efficacy or safety."),
        ("INTERVENTION", ["MMP11_CLAIM_10"], "Three preclinical antibody records", "Shared publication, reagent, and A549/PC9 model lineage.", "No clinical-development observation.", "Specificity, exposure, replication, and safety remain unresolved."),
        ("CLINICAL_DEVELOPMENT", ["MMP11_CLAIM_08"], "Bounded registry check; zero relevant records", "Five lexical false positives are separately excluded.", "No relevant record within the frozen query; absence is not global proof.", "External registry coverage and future updates remain mutable."),
    ]
    rows = []
    for modality, claim_ids, presence, dep, nulls, limitation in specs:
        links = [x for x in matrix if x["claim_id"] in claim_ids]
        unique_evidence = {x["evidence_id"] for x in links if x["evidence_id"] != "SEARCH_CLINICALTRIALS_MMP11"}
        if modality == "IN_VIVO":
            count = 2
        elif modality == "CLINICAL_DEVELOPMENT":
            count = 0
        else:
            count = len(unique_evidence) if modality != "PROJECT_TRANSCRIPTOMICS" else 7
        rows.append({
            "modality_id": modality, "observations_present": presence,
            "observation_count": str(count),
            "relevant_evidence_families": "|".join(unique_ordered([x["evidence_family_id"] for x in links])),
            "dependency_considerations": dep, "null_or_context_findings": nulls,
            "major_limitation": limitation,
            "count_semantics": "Descriptive audit count only; not a favourable/unfavourable value.",
        })
    return rows


def translational_boundary() -> dict[str, Any]:
    levels = [
        ("LEVEL_1_EXPRESSION_ASSOCIATION", "SUPPORTED_WITHIN_PROJECT_DATASET", "MMP11 has a strong tumour-normal expression association in the project TCGA-LUAD analysis.", "Expression association does not establish causality.", ["MMP11_CLAIM_01"]),
        ("LEVEL_2_MODEL_ROBUSTNESS", "SUPPORTED_WITHIN_SAME_DATASET", "The expression direction is concordant across six prespecified model variants.", "Same-dataset robustness is not independent replication.", ["MMP11_CLAIM_02"]),
        ("LEVEL_3_EXTERNAL_OBSERVATION", "SUPPORTED_WITH_DEPENDENCY_BOUNDARIES", "Additional transcriptomic and tissue observations exist in external datasets and cohorts.", "Published TCGA shares project lineage; external observations do not establish causality.", ["MMP11_CLAIM_03", "MMP11_CLAIM_04"]),
        ("LEVEL_4_PRECLINICAL_FUNCTIONAL_RELEVANCE", "SUPPORTED_IN_BOUNDED_MODELS", "Cell perturbation and xenograft experiments report phenotypic effects.", "Preclinical model effects do not establish patient efficacy or safety.", ["MMP11_CLAIM_05", "MMP11_CLAIM_06", "MMP11_CLAIM_09"]),
        ("LEVEL_5_PRECLINICAL_INTERVENTION", "SUPPORTED_IN_BOUNDED_MODELS", "An anti-MMP11 antibody produced effects in bounded preclinical models.", "The observations share publication/reagent lineage and do not validate a clinical intervention.", ["MMP11_CLAIM_10"]),
        ("LEVEL_6_CLINICAL_VALIDATION", "NOT_ESTABLISHED_BY_CURRENT_EVIDENCE", "No clinical validation is established by the frozen evidence package.", "A bounded registry search cannot prove global absence.", ["MMP11_CLAIM_07", "MMP11_CLAIM_08"]),
        ("LEVEL_7_THERAPEUTIC_RECOMMENDATION", "OUTSIDE_PROJECT_SCOPE_AND_NOT_SUPPORTED", "No therapeutic recommendation is generated.", "Target selection, benefit, and safety require evidence beyond this synthesis.", []),
    ]
    return {
        "synthesis_version": SYNTHESIS_VERSION,
        "EnsemblID": ENSEMBL_ID,
        "display_symbol": SYMBOL,
        "boundary_semantics": "Descriptive interpretation boundaries only; levels are not an ordinal target-quality scale.",
        "levels": [
            {"level_id": a, "status": b, "maximum_supported_interpretation": c, "boundary": d, "claim_references": e}
            for a, b, c, d, e in levels
        ],
        "disclaimer": DISCLAIMER,
    }


def presentation_candidates() -> dict[str, Any]:
    candidates = [
        {
            "candidate_id": "PRESENTATION_CLAIM_01", "claim_ids": ["MMP11_CLAIM_01", "MMP11_CLAIM_02"],
            "short_statement": "Project analysis: MMP11 was strongly upregulated in LUAD tumour versus normal tissue (logFC +5.18; BH FDR 1.79e-37), with concordant direction across all six prespecified sensitivity models.",
            "supporting_evidence_families": ["FAM_PROJECT_TCGA_EXPRESSION"],
            "required_qualifier": "These sensitivity models use the same TCGA-LUAD dataset and are not independent replication.",
            "prohibited_stronger_wording": "Do not describe robustness models as six independent validations or claim that expression proves causality.",
            "provenance_references": ["REC_1FDB3CAEC78761B6CDAC13A2", "REC_0EECFF585907F97C3C1A314E"],
        },
        {
            "candidate_id": "PRESENTATION_CLAIM_02", "claim_ids": ["MMP11_CLAIM_03", "MMP11_CLAIM_04"],
            "short_statement": "External evidence: published GEO, tissue, and serum observations extend the represented evidence across additional datasets and biospecimen modalities.",
            "supporting_evidence_families": ["FAM_EXTERNAL_TCGA_REANALYSIS", "FAM_GEO_JOINT_2019", "FAM_GEO_GSE43458_PRIMARY", "FAM_COHORT_2019_LUAD_18", "FAM_COHORT_2019_SERUM"],
            "required_qualifier": "Some transcriptomic analyses reuse TCGA or GEO accessions, and cohort/histology specificity varies.",
            "prohibited_stronger_wording": "Do not call all external records independent replication or diagnostic validation.",
            "provenance_references": ["EXT_31024988_01", "EXT_31024988_02", "EXT_31024988_03", "EXT_31024988_04"],
        },
        {
            "candidate_id": "PRESENTATION_CLAIM_03", "claim_ids": ["MMP11_CLAIM_05", "MMP11_CLAIM_06", "MMP11_CLAIM_10"],
            "short_statement": "Functional context: MMP11 depletion was associated with reduced proliferation, migration-invasion, and xenograft growth in reported LUAD models, while anti-MMP11 antibody experiments showed preclinical effects.",
            "supporting_evidence_families": ["FAM_CELL_PERTURBATION_310_A549_PC9", "FAM_CELL_PERTURBATION_310_PC9_RESCUE", "FAM_XENOGRAFT_DEPLETION_310", "FAM_ANTIBODY_INTERVENTION_310"],
            "required_qualifier": "These are preclinical observations, substantially within one publication, and do not establish clinical efficacy or safety.",
            "prohibited_stronger_wording": "Do not describe MMP11 as clinically validated, safe, effective, or recommended for therapy.",
            "provenance_references": ["EXT_31024988_05", "EXT_31024988_07", "EXT_31024988_08", "EXT_31024988_11", "EXT_31024988_12"],
        },
        {
            "candidate_id": "PRESENTATION_CLAIM_04", "claim_ids": ["MMP11_CLAIM_07", "MMP11_CLAIM_08", "MMP11_CLAIM_09"],
            "short_statement": "Boundary: clinical associations are context-dependent and include null findings; no relevant MMP11 clinical-development record was identified in the bounded frozen registry check.",
            "supporting_evidence_families": ["FAM_EXTERNAL_TCGA_REANALYSIS", "FAM_CLINICAL_DEVELOPMENT_CHECK"],
            "required_qualifier": "Null results are context-specific, and bounded search absence is not proof that no study exists globally.",
            "prohibited_stronger_wording": "Do not infer clinical failure, global absence, efficacy, safety, or a therapeutic recommendation.",
            "provenance_references": ["SEARCH_CLINICALTRIALS_MMP11", "EXT_36756152_02", "EXT_36756152_06", "EXT_36756152_07"],
        },
    ]
    return {
        "synthesis_version": SYNTHESIS_VERSION,
        "purpose": "Scientifically bounded candidate statements for a later communication task; not final slide copy.",
        "candidates": candidates,
        "disclaimer": DISCLAIMER,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    before = input_hashes()
    checks: list[tuple[str, bool, str]] = [
        ("task039a_hashes", before["task039a"] == TASK_A_HASHES, "All reviewed Task #039A inputs match pinned SHA256 values."),
        ("task039b_hashes", before["task039b"] == TASK_B_HASHES, "All reviewed Task #039B inputs match pinned SHA256 values."),
        ("task039a_base_ancestor", git_is_ancestor(TASK_A_BASE_COMMIT), "Task #039A base commit is an ancestor of current HEAD."),
        ("task039b_base_ancestor", git_is_ancestor(TASK_B_BASE_COMMIT), "Task #039B base commit is an ancestor of current HEAD."),
    ]

    identity = json.loads((TASK_A / "mmp11_identity.json").read_text())
    transcript = read_csv(TASK_A / "mmp11_transcriptomic_evidence.csv")
    sensitivity = read_csv(TASK_A / "mmp11_sensitivity_evidence.csv")
    internal_prov = read_csv(TASK_A / "mmp11_provenance_links.csv")
    internal_deps = read_csv(TASK_A / "mmp11_dependency_map.csv")
    search = json.loads((TASK_B / "search_strategy.json").read_text())
    publications = read_csv(TASK_B / "publication_registry.csv")
    external = read_csv(TASK_B / "external_evidence_registry.csv")
    models = read_csv(TASK_B / "experimental_model_registry.csv")
    datasets = read_csv(TASK_B / "dataset_registry.csv")
    ext_prov = read_csv(TASK_B / "external_provenance_links.csv")
    ext_deps = read_csv(TASK_B / "external_dependency_map.csv")

    families, external_family = build_families(transcript, sensitivity, external, ext_prov)
    cross_deps = normalize_dependencies(internal_deps, ext_deps, external)
    claims = claim_definitions()
    matrix = build_claim_matrix(claims, transcript, sensitivity, external, external_family, ext_prov, ext_deps)
    claim_audit = claim_dependency_audit(claims, matrix)
    modalities = modality_summary(matrix)
    translation = translational_boundary()
    candidates = presentation_candidates()

    task_a_source_ids = [x["dependency_relationship_id"] for x in internal_deps]
    task_a_atomic_counts = [len(normalized_internal_relationship_types(x)) for x in internal_deps]
    task_a_normalized_edges = [x for x in cross_deps if x["source_task"] == "TASK039A"]
    task_b_normalized_edges = [x for x in cross_deps if x["source_task"] == "TASK039B"]
    task_c_synthesized_edges = [x for x in cross_deps if x["source_task"] == "TASK039C"]
    task_b_source_ids = {x["dependency_id"] for x in ext_deps}
    task_b_retained_ids = {x["source_relationship_id"] for x in task_b_normalized_edges}
    dependency_counts = {
        "task039a_source_dependency_records": len(task_a_source_ids),
        "task039a_normalized_dependency_edges": len(task_a_normalized_edges),
        "task039a_single_relationship_records": task_a_atomic_counts.count(1),
        "task039a_multi_relationship_records": task_a_atomic_counts.count(2),
        "task039b_dependency_edges": len(task_b_normalized_edges),
        "task039c_new_cross_task_edges": len(task_c_synthesized_edges),
        "combined_normalized_dependency_edges": len(cross_deps),
    }
    dependency_count_semantics_valid = all([
        len(task_a_source_ids) == len(set(task_a_source_ids)) == 21,
        set(task_a_atomic_counts) == {1, 2},
        dependency_counts["task039a_single_relationship_records"] == 7,
        dependency_counts["task039a_multi_relationship_records"] == 14,
        dependency_counts["task039a_normalized_dependency_edges"] == sum(task_a_atomic_counts) == 35,
        len(ext_deps) == len(task_b_source_ids) == 197,
        task_b_source_ids == task_b_retained_ids,
        dependency_counts["task039b_dependency_edges"] == 197,
        dependency_counts["task039c_new_cross_task_edges"] == 19,
        dependency_counts["combined_normalized_dependency_edges"] == 35 + 197 + 19 == 251,
    ])

    families_again, external_family_again = build_families(transcript, sensitivity, external, ext_prov)
    deterministic_bundle = [families, external_family, cross_deps, claims, matrix, claim_audit, modalities, translation, candidates]
    deterministic_bundle_again = [
        families_again,
        external_family_again,
        normalize_dependencies(internal_deps, ext_deps, external),
        claim_definitions(),
        build_claim_matrix(claims, transcript, sensitivity, external, external_family, ext_prov, ext_deps),
        claim_dependency_audit(claims, matrix),
        modality_summary(matrix),
        translational_boundary(),
        presentation_candidates(),
    ]

    internal_ids = {x["governed_evidence_record_id"] for x in transcript + sensitivity}
    external_ids = {x["external_evidence_id"] for x in external}
    search_ids = {x["search_id"] for x in search["searches"]}
    resolvable_evidence = internal_ids | external_ids | search_ids
    family_members = [m for f in families for m in f["member_evidence_ids"].split("|")]

    frozen_endpoint_ids = set()
    for dep in internal_deps:
        frozen_endpoint_ids.update([dep["record_or_artifact_a"], dep["record_or_artifact_b"]])
    for dep in ext_deps:
        frozen_endpoint_ids.update([dep["source_evidence_id"], dep["related_entity_id"]])
    frozen_endpoint_ids.update(internal_ids | external_ids | search_ids)
    frozen_endpoint_ids.update(x["publication_id"] for x in publications)
    frozen_endpoint_ids.update(x["dataset_id"] for x in datasets)
    frozen_endpoint_ids.update(x["model_id"] for x in models)

    null_ids = {x["external_evidence_id"] for x in external if x["evidence_status"] == "OBSERVED_NULL"}
    context_ids = {x["external_evidence_id"] for x in external if x["evidence_status"] == "CONTEXT_DEPENDENT"}
    insufficient_links = [x for x in matrix if x["evidence_status"] == "INSUFFICIENTLY_SPECIFIC"]
    tcga_ext = {x["external_evidence_id"] for x in external if "TCGA-LUAD" in x["dataset_or_cohort"]}
    geo_reuse_ids = {x["external_evidence_id"] for x in external if any(g in x["dataset_or_cohort"] for g in ["GSE10072", "GSE18842", "GSE43458"])}
    pmid_2019 = {x["external_evidence_id"] for x in external if x["publication_id"] == "PUB_PMID_31024988"}
    antibody_xeno_links = [x for x in matrix if x["evidence_id"] == "EXT_31024988_12"]

    checks.extend([
        ("target_identity", ENSEMBL_ID in json.dumps(identity) and all(x["EnsemblID"] == ENSEMBL_ID for x in transcript + sensitivity + external), "Immutable EnsemblID reconciles across both tasks."),
        ("source_counts_frozen", len(transcript) == 1 and len(sensitivity) == 6 and len(publications) == 37 and len(external) == 56 and len(ext_prov) == 56 and len(ext_deps) == 197, "Frozen source row counts reconcile."),
        ("family_members_resolve", all(x in resolvable_evidence for x in family_members), "All evidence-family members resolve to frozen record or search identifiers."),
        ("external_family_partition", set(external_family) == external_ids and len(external_family) == 56, "Each external evidence unit has exactly one primary evidence family."),
        ("claim_evidence_resolves", all(x["evidence_id"] in resolvable_evidence for x in matrix), "Every claim-evidence reference resolves."),
        ("claim_relationship_vocabulary", all(x["relationship_to_claim"] in ALLOWED_CLAIM_RELATIONSHIPS for x in matrix), "All claim relationships use controlled non-numeric terms."),
        ("dependency_vocabulary", all(x["relationship_type"] in ALLOWED_RELATIONSHIPS for x in cross_deps), "All normalized dependency relationships use qualitative controlled terms."),
        ("cross_dependency_endpoints_resolve", all(x["entity_a"] in frozen_endpoint_ids and x["entity_b"] in frozen_endpoint_ids for x in cross_deps), "Every dependency endpoint resolves to a frozen or explicitly synthesized lineage entity."),
        ("tcga_overlap_retained", len(tcga_ext) == 7 and all(any(d["entity_a"] == "REC_1FDB3CAEC78761B6CDAC13A2" and d["entity_b"] == eid and d["relationship_type"] == "SHARED_DATASET" for d in cross_deps) for eid in tcga_ext), "All seven external TCGA units retain explicit shared project lineage."),
        ("geo_reuse_retained", all(any(d["entity_a"] == eid and d["relationship_type"] == "SHARED_DATASET" for d in cross_deps) for eid in geo_reuse_ids), "GEO reuse is retained at accession level."),
        ("pmid_31024988_structure", len(pmid_2019) == 12 and all(external_family[x] for x in pmid_2019) and all(any(d["entity_a"] == x and d["relationship_type"] == "SHARED_PUBLICATION" for d in cross_deps) for x in pmid_2019), "All 12 PMID 31024988 units retain publication-level dependency and experiment-specific families."),
        ("all_null_units_represented", len(null_ids) == 7 and null_ids.issubset({x["evidence_id"] for x in matrix if x["claim_id"] == "MMP11_CLAIM_07"}), "All seven external null evidence units remain represented in the clinical-association claim."),
        ("context_units_visible", len(context_ids) == 19 and context_ids.issubset({x["evidence_id"] for x in matrix}), "All context-dependent evidence units remain visible."),
        ("insufficient_not_promoted", len(insufficient_links) == 13 and all(x["relationship_to_claim"] == "INSUFFICIENTLY_SPECIFIC" for x in insufficient_links), "Insufficiently specific evidence is never promoted to direct LUAD support."),
        ("antibody_xenograft_not_duplicated", len(antibody_xeno_links) == 2 and len({x["evidence_id"] for x in antibody_xeno_links}) == 1 and sum("EXT_31024988_12" in f["member_evidence_ids"].split("|") for f in families) == 1, "The antibody xenograft is one evidence record and one family member, referenced by two descriptive claims without double counting."),
        ("in_vivo_count_semantics", next(x for x in modalities if x["modality_id"] == "IN_VIVO")["observation_count"] == "2" and sum(x["evidence_domain"] == "F_IN_VIVO" for x in external) == 1, "F_IN_VIVO remains one domain record while total in-vivo experimental units remain two."),
        ("dependency_count_semantics", dependency_count_semantics_valid, "21 Task #039A source records normalize to 35 atomic edges; Task #039B contributes 197 frozen edges and Task #039C synthesizes 19 cross-task edges, for 251 graph rows."),
        ("clinical_efficacy_boundary", next(x for x in translation["levels"] if x["level_id"] == "LEVEL_6_CLINICAL_VALIDATION")["status"] == "NOT_ESTABLISHED_BY_CURRENT_EVIDENCE", "The synthesis explicitly records that clinical validation is not established."),
        ("therapeutic_validation_boundary", next(x for x in translation["levels"] if x["level_id"] == "LEVEL_7_THERAPEUTIC_RECOMMENDATION")["status"] == "OUTSIDE_PROJECT_SCOPE_AND_NOT_SUPPORTED", "Therapeutic recommendation remains outside scope and unsupported."),
        ("deterministic_object_construction", deterministic_bundle == deterministic_bundle_again, "Two independent in-memory synthesis constructions are identical."),
        ("no_network_runtime", has_no_network_client_imports(), "Generator contains no network client import and used frozen local inputs only."),
        ("tracked_existing_artifacts_unchanged", tracked_worktree_is_clean(), "No tracked project artifact is staged or modified; only new Task #039C paths may be present."),
    ])

    forbidden = {"score", "ranking", "rank", "priority_score", "confidence_score", "recommendation"}
    generated_keys = set()
    for collection in [families, cross_deps, claims, matrix, claim_audit, modalities]:
        for row in collection:
            generated_keys.update(row)
    for obj in [translation, candidates]:
        def walk(value: Any) -> None:
            if isinstance(value, dict):
                generated_keys.update(value)
                for child in value.values(): walk(child)
            elif isinstance(value, list):
                for child in value: walk(child)
        walk(obj)
    checks.append(("forbidden_fields_absent", not forbidden.intersection(generated_keys), "No score, rank, confidence-score, or recommendation field is generated."))

    after = input_hashes()
    checks.append(("frozen_inputs_unchanged", before == after, "All Task #039A and #039B inputs are byte-unchanged."))
    all_pass = all(ok for _, ok, _ in checks)
    if not all_pass:
        raise AssertionError("Validation failed before output publication: " + ", ".join(name for name, ok, _ in checks if not ok))

    write_csv(OUT / "evidence_family_registry.csv", families)
    write_csv(OUT / "cross_source_dependency_map.csv", cross_deps)
    write_csv(OUT / "claim_registry.csv", claims)
    write_csv(OUT / "claim_evidence_matrix.csv", matrix)
    write_csv(OUT / "claim_dependency_audit.csv", claim_audit)
    write_csv(OUT / "modality_summary.csv", modalities)
    (OUT / "translational_boundary.json").write_text(json.dumps(translation, indent=2, sort_keys=True) + "\n")
    (OUT / "presentation_claim_candidates.json").write_text(json.dumps(candidates, indent=2, sort_keys=True) + "\n")

    dataset_ids = {x["dataset_id"] for x in datasets}
    represented_dataset_lineages = unique_ordered([
        token for ev in external for token in ev["dataset_or_cohort"].split("|") if token in dataset_ids
    ])
    unresolved_dependencies = sum(x["relationship_type"] == "UNKNOWN" for x in cross_deps)
    same_dataset_robustness = 6
    synthesis = f"""# MMP11 cross-source evidence synthesis v0.1

{DISCLAIMER}

## Scope

This synthesis references frozen Task #039A and Task #039B evidence without replacing any evidence identifier. It links one S0 source row, six sensitivity-model rows represented by two governed internal records, and all **{len(external)}** bounded external evidence units. Counts below are audit metadata, not evidence strength.

## What the evidence package can support

- **Project expression association:** S0 reports MMP11 higher in LUAD tumour than normal tissue (Tumor minus Normal logFC **+5.18003235678542**; BH FDR **1.79025769607393e-37**).
- **Same-dataset robustness:** all **{same_dataset_robustness}** prespecified sensitivity models retain the tumour-higher direction. They use the same TCGA-LUAD biological dataset and are not independent replication.
- **External observation:** external transcriptomic and patient tissue/protein observations exist. Published TCGA analyses share project dataset lineage; accession-resolved GEO observations provide other dataset contexts, with reuse and histology limitations retained.
- **Preclinical functional context:** reported LUAD cell perturbation, xenograft depletion, and anti-MMP11 antibody experiments contain bounded phenotypic observations.
- **Clinical boundary:** clinical/prognostic records include all **{len(null_ids)}** null observations and context-dependent findings. The bounded registry check found no relevant MMP11 clinical-development record among five lexical false positives.

## Dependency-aware interpretation

The synthesis defines **{len(families)}** evidence families and **{len(cross_deps)}** qualitative dependency relationships. It distinguishes:

1. **Same-dataset robustness:** S0 versus S1-S6.
2. **Same-dataset reanalysis:** project TCGA-LUAD versus published TCGA analyses.
3. **Distinct dataset observation:** provenance-resolved non-TCGA cohorts, subject to accession reuse and overlap checks.
4. **Distinct evidence modality:** transcriptomics, protein/tissue, clinical association, cell perturbation, mechanistic, in-vivo, intervention, and clinical-development-check contexts.
5. **Same-publication multi-modality:** PMID 31024988 contributes transcriptomic, tissue, cell, xenograft, and antibody observations, but these retain shared publication, model, experiment, and reagent lineages.

`NO_DEPENDENCY_IDENTIFIED` and missing graph edges never establish statistical independence. The number of GEO accessions is not the number of independent transcriptomic replications, and the number of evidence units is not the number of independent sources.

## Dependency count semantics

- The frozen Task #039A dependency map contains **{dependency_counts['task039a_source_dependency_records']} source relationship records**.
- **{dependency_counts['task039a_multi_relationship_records']}** of those records carry two qualitative relationship types; **{dependency_counts['task039a_single_relationship_records']}** carry one.
- Task #039C represents each qualitative relationship type as an atomic graph row. The 21 Task #039A source records therefore become **{dependency_counts['task039a_normalized_dependency_edges']} normalized atomic edges**.
- Task #039B contributes **{dependency_counts['task039b_dependency_edges']} frozen dependency edges**.
- Task #039C adds **{dependency_counts['task039c_new_cross_task_edges']} newly synthesized cross-task relationships**.
- The combined normalized dependency graph contains **{dependency_counts['combined_normalized_dependency_edges']} rows**: 35 + 197 + 19 = 251.

**251 graph rows != 251 independent evidence sources.** Normalization expands representation granularity only; it does not add scientific observations or evidence strength.

## Important count semantics

- Frozen `F_IN_VIVO` domain evidence units: **1**.
- Total in-vivo experimental units: **2**, because `EXT_31024988_12` is classified under intervention while also being a xenograft experiment.
- `EXT_31024988_12` remains one evidence record and one family member; its relevance to two claims is not two observations.
- Distinct governed dataset/cohort lineages represented: **{len(represented_dataset_lineages)}**.
- Unresolved dependency relationships retained: **{unresolved_dependencies}**.

## What cannot be said

- Expression or prognostic association does not prove disease causality.
- Model robustness and published TCGA reanalysis are not independent biological replication.
- Protein or serum observations do not establish diagnostic validity.
- Cell perturbation and xenograft effects do not establish patient efficacy or safety.
- Preclinical antibody observations do not establish a validated therapeutic intervention.
- The bounded clinical-development search does not prove global absence.
- This synthesis does not rank MMP11, calculate a target or confidence score, or recommend therapy.

## Maximum bounded conclusion

MMP11 provides an illustrative LUAD worked example in which a strong, model-robust project-derived transcriptomic association can be connected to external observations across transcriptomic, tissue, functional, and preclinical experimental modalities. However, shared TCGA lineage, within-publication dependencies, context-dependent clinical associations, and the absence of clinical validation prevent these observations from being interpreted as proof of therapeutic efficacy or as a validated target recommendation.

This conclusion was emitted only after all claim, identity, provenance, dependency, count-semantic, and frozen-input checks passed.
"""
    (OUT / "mmp11_cross_source_synthesis.md").write_text(synthesis)

    validation_report = f"""# Task #039C validation report

{DISCLAIMER}

Overall validation: **PASS**

| Check | Result | Detail |
|---|---|---|
""" + "\n".join(f"| `{name}` | **{'PASS' if ok else 'FAIL'}** | {detail} |" for name, ok, detail in checks) + "\n"
    (OUT / "validation_report.md").write_text(validation_report)

    branch = subprocess.run(["git", "branch", "--show-current"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    session = "\n".join([
        f"synthesis_version={SYNTHESIS_VERSION}",
        f"generator_version={GENERATOR_VERSION}",
        f"python_version={platform.python_version()}",
        f"platform={platform.platform()}",
        "network_access=NONE",
        f"git_branch={branch}",
        f"task039a_base_commit={TASK_A_BASE_COMMIT}",
        f"task039b_base_commit={TASK_B_BASE_COMMIT}",
        f"task039a_source_dependency_records={dependency_counts['task039a_source_dependency_records']}",
        f"task039a_normalized_dependency_edges={dependency_counts['task039a_normalized_dependency_edges']}",
        f"task039a_single_relationship_records={dependency_counts['task039a_single_relationship_records']}",
        f"task039a_multi_relationship_records={dependency_counts['task039a_multi_relationship_records']}",
        f"task039b_dependency_edges={dependency_counts['task039b_dependency_edges']}",
        f"task039c_new_cross_task_edges={dependency_counts['task039c_new_cross_task_edges']}",
        f"combined_normalized_dependency_edges={dependency_counts['combined_normalized_dependency_edges']}",
        "runtime_head_policy=BASE_COMMITS_MUST_BE_ANCESTORS;CURRENT_HEAD_NOT_EMBEDDED_FOR_POST_COMMIT_DETERMINISM",
        "working_tree_state=REPORTED_AT_COMPLETION_NOT_EMBEDDED",
        "task039a_input_hashes=" + json.dumps(TASK_A_HASHES, sort_keys=True),
        "task039b_input_hashes=" + json.dumps(TASK_B_HASHES, sort_keys=True),
        f"disclaimer={DISCLAIMER}", "",
    ])
    (OUT / "session_info.txt").write_text(session)

    structural_output_hashes = {
        name: sha256(OUT / name) for name in STRUCTURAL_OUTPUT_HASHES
    }
    scientific_artifact_hashes_unchanged = structural_output_hashes == STRUCTURAL_OUTPUT_HASHES
    if not scientific_artifact_hashes_unchanged:
        changed = [
            name for name in STRUCTURAL_OUTPUT_HASHES
            if structural_output_hashes.get(name) != STRUCTURAL_OUTPUT_HASHES[name]
        ]
        raise AssertionError("Task #039C scientific/structural artifact changed: " + ", ".join(changed))

    final_hashes = input_hashes()
    if final_hashes != before:
        raise AssertionError("Frozen input changed while outputs were written")

    metrics = {
        "target_identity": ENSEMBL_ID,
        "internal_evidence_units_referenced": 1 + len(sensitivity),
        "internal_governed_evidence_records_referenced": len(internal_ids),
        "external_evidence_units_referenced": len({x["evidence_id"] for x in matrix if x["evidence_id"] in external_ids}),
        "evidence_families_created": len(families),
        "claims_created": len(claims),
        "claim_evidence_links": len(matrix),
        "task039a_source_dependency_records": dependency_counts["task039a_source_dependency_records"],
        "task039a_normalized_atomic_dependency_edges": dependency_counts["task039a_normalized_dependency_edges"],
        "task039b_frozen_dependency_edges": dependency_counts["task039b_dependency_edges"],
        "task039c_newly_synthesized_cross_task_edges": dependency_counts["task039c_new_cross_task_edges"],
        "combined_normalized_dependency_graph_rows": dependency_counts["combined_normalized_dependency_edges"],
        "scientific_artifact_hashes_unchanged": "YES" if scientific_artifact_hashes_unchanged else "NO",
        "named_validation_checks": len(checks),
        "distinct_dataset_lineages_represented": len(represented_dataset_lineages),
        "evidence_modalities_represented": len(modalities),
        "null_evidence_units_retained": len(null_ids),
        "context_dependent_units_retained": len(context_ids),
        "unresolved_dependency_count": unresolved_dependencies,
        "tcga_shared_lineage_count": len(tcga_ext),
        "presentation_claim_candidates_generated": len(candidates["candidates"]),
        "frozen_input_verification_status": "PASS",
        "validation": "PASS",
    }
    print(json.dumps(metrics, indent=2, sort_keys=True))
    print("files_modified:")
    for path in [
        Path("analysis/39C_synthesize_mmp11_cross_source_evidence.py"),
        Path("outputs/mmp11_cross_source_synthesis_v0.1/mmp11_cross_source_synthesis.md"),
        Path("outputs/mmp11_cross_source_synthesis_v0.1/validation_report.md"),
        Path("outputs/mmp11_cross_source_synthesis_v0.1/session_info.txt"),
    ]:
        print(f"- {path}")


if __name__ == "__main__":
    main()
