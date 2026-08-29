#!/usr/bin/env python3
"""Acquire and normalize external MMP11/LUAD evidence for Task #039B.

The network step freezes official source payloads.  All registries and reports
are deterministic transformations of those frozen payloads plus the reviewed,
explicit evidence-unit catalogue below.  No score, rank, recommendation, or
therapeutic-direction inference is produced.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "mmp11_external_evidence_v0.1"
RAW = OUT / "raw_retrieval"
INTERNAL = ROOT / "outputs" / "mmp11_internal_evidence_v0.1"
ENSEMBL_ID = "ENSG00000099953.9"
SYMBOL = "MMP11"
GENERATOR_VERSION = "MMP11_EXTERNAL_EVIDENCE_ACQUISITION_GENERATOR_V0.1.1"
REGISTRY_VERSION = "MMP11_EXTERNAL_EVIDENCE_REGISTRY_V0.1"
DOCUMENTATION_PATCH_VERSION = "TASK039B_1_SEARCH_COVERAGE_PATCH_V0.1"
DISCLAIMER = (
    "MMP11 is being used as an illustrative biological worked example. "
    "External evidence is organized to demonstrate provenance-aware evidence "
    "synthesis and does not constitute a project-level therapeutic target "
    "ranking, validation, or recommendation."
)

FROZEN_INPUTS = [
    "mmp11_identity.json",
    "mmp11_component_summary.json",
    "mmp11_dependency_map.csv",
    "mmp11_claim_boundary.md",
    "mmp11_internal_evidence_summary.md",
    "validation_report.md",
]
EXPECTED_TASK039A_HASHES = {
    "mmp11_identity.json": "caeb90f8ecef320a02db10ce9a396dcc77f17fc126e6c3f5b788349bfa2e8ae3",
    "mmp11_component_summary.json": "85d3bb3e4e73613bc2362f722b305d09f8577f0eaf28aa84e0aab729a2d60ee5",
    "mmp11_dependency_map.csv": "76306760de5c6c37321ab5e30b5c8f9e361ef0b3be42826920fd4f045a4d577d",
    "mmp11_claim_boundary.md": "8da1472467dd90d10a28a85fdc7c3b2b0f1482c38f75ffc44cd86860719353ea",
    "mmp11_internal_evidence_summary.md": "886ac61d2cb2de5d47a761c3a5c9068441a58660afdb1a029b91a684122e5c20",
    "validation_report.md": "ad8986ddd3431b77f7b8bf00462ebff9cdbc98ad2d98acd0ad4d5ebaa80c2cc1",
}
EXPECTED_TASK039B_BIOLOGICAL_HASHES = {
    "publication_registry.csv": "fddb058699173a666d1563e9effaa5e291202914af3928615e3a3c78f35206c0",
    "external_evidence_registry.csv": "bd2c56a2c90f132be88630d2c5d2d7515f99e024366956eaa8c5f440c6e56a1d",
    "experimental_model_registry.csv": "7c64500b6eb3add7e2c9a33f5fa2c263670454e5d9413dcc8d3b473132d89d6e",
    "dataset_registry.csv": "5ee06213fdc7590eee2d9c41df84abf0145b2f443de66ccf23a27a88b330f86c",
    "external_provenance_links.csv": "dc57d328c8b78e67e0122a526b4f0729751c91733fc363ea0f538df3aafe9bf9",
    "external_dependency_map.csv": "e1838f91a3dc45706421035e868f671b5259910b0721a795c799e0c2f0c2af99",
    "evidence_exclusion_log.csv": "06478cf480004f2cc30e8075590826f3557efc71fff0b75973c555c0d7157c96",
}
SEARCH_ROLES = {
    "PRIMARY_SCREENING_FRAME",
    "SUPPLEMENTARY_DISCOVERY",
    "OVERLAP_ORIENTATION",
    "CLINICAL_DEVELOPMENT_CHECK",
}

BROAD_QUERY = (
    '(MMP11[Title/Abstract] OR "matrix metalloproteinase 11"[Title/Abstract] '
    'OR stromelysin-3[Title/Abstract]) AND ("lung adenocarcinoma"[Title/Abstract] '
    'OR LUAD[Title/Abstract] OR NSCLC[Title/Abstract] OR "lung cancer"[Title/Abstract])'
)
FUNCTION_QUERY = (
    f"{BROAD_QUERY} AND (expression[Title/Abstract] OR prognosis[Title/Abstract] "
    "OR survival[Title/Abstract] OR perturbation[Title/Abstract] OR "
    "knockdown[Title/Abstract] OR knockout[Title/Abstract] OR CRISPR[Title/Abstract] "
    "OR siRNA[Title/Abstract] OR shRNA[Title/Abstract] OR proliferation[Title/Abstract] "
    "OR migration[Title/Abstract] OR invasion[Title/Abstract] OR xenograft[Title/Abstract] "
    "OR metastasis[Title/Abstract] OR antibody[Title/Abstract] OR inhibitor[Title/Abstract] "
    "OR therapeutic[Title/Abstract] OR mechanism[Title/Abstract])"
)
EUROPE_PMC_QUERY = (
    '(MMP11 OR "matrix metalloproteinase 11" OR "stromelysin-3") AND '
    '("lung adenocarcinoma" OR LUAD OR NSCLC OR "lung cancer")'
)
CLINICAL_TRIALS_QUERY = "MMP11 OR \"matrix metalloproteinase 11\" OR stromelysin-3"

# Four identifiers were discovered through the frozen Task #039A Open Targets
# literature records and three through its Expression Atlas records.  They are
# screened explicitly rather than silently treated as new independent evidence.
OT_ORIENTATION_PMIDS = [
    "33836753", "37543577", "39239548", "40977645",
    "23659968", "15653641", "25141350",
]

GEO_ACCESSIONS = [
    "GSE7670", "GSE10072", "GSE68465", "GSE43458", "GSE33479",
    "GSE18842", "GSE32863", "GSE19804", "GSE31210", "GSE76925",
    "GSE43767",
]

PMCIDS = [
    "PMC6477516", "PMC9900007", "PMC12082244", "PMC8523254",
    "PMC9010460", "PMC5928655", "PMC2556648", "PMC11967273",
    "PMC12407355", "PMC12366952", "PMC12972608",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def stable_id(prefix: str, *parts: object) -> str:
    key = "||".join(str(x) for x in parts)
    return f"{prefix}_{hashlib.sha256(key.encode()).hexdigest()[:20].upper()}"


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["curl", "-fsSL", "--retry", "3", "--connect-timeout", "30",
         "--max-time", "180", "-A", "luad-target-dossier-task039b/0.1",
         "-o", str(destination), url],
        check=True,
    )
    time.sleep(0.35)


def retrieve_payloads() -> None:
    """Retrieve official mutable-source payloads once; never overwrite silently."""
    RAW.mkdir(parents=True, exist_ok=True)
    manifest_path = RAW / "retrieval_manifest.json"
    if manifest_path.exists():
        print("Frozen raw retrieval payloads already exist; retrieval skipped.")
        return

    retrieval_time = now_utc()
    sources: list[dict[str, object]] = []

    def fetch(name: str, url: str, source: str, query: str = "") -> Path:
        path = RAW / name
        download(url, path)
        sources.append({
            "payload_path": str(path.relative_to(ROOT)),
            "source": source,
            "query": query,
            "retrieval_timestamp_utc": retrieval_time,
            "url": url,
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
        })
        return path

    ncbi = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    broad_url = f"{ncbi}/esearch.fcgi?" + urllib.parse.urlencode({
        "db": "pubmed", "term": BROAD_QUERY, "retmode": "json", "retmax": "1000",
    })
    broad_path = fetch("pubmed_esearch_broad.json", broad_url, "PubMed", BROAD_QUERY)
    broad = json.loads(broad_path.read_text())
    broad_ids = broad["esearchresult"]["idlist"]

    function_url = f"{ncbi}/esearch.fcgi?" + urllib.parse.urlencode({
        "db": "pubmed", "term": FUNCTION_QUERY, "retmode": "json", "retmax": "1000",
    })
    fetch("pubmed_esearch_functional.json", function_url, "PubMed", FUNCTION_QUERY)

    all_pmids = list(dict.fromkeys(broad_ids + OT_ORIENTATION_PMIDS))
    efetch_url = f"{ncbi}/efetch.fcgi?" + urllib.parse.urlencode({
        "db": "pubmed", "id": ",".join(all_pmids), "retmode": "xml",
    })
    fetch("pubmed_screened_records.xml", efetch_url, "PubMed", "PMID set from broad search plus Task #039A overlap audit")

    epmc_url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode({
        "query": EUROPE_PMC_QUERY, "format": "json", "pageSize": "1000", "resultType": "core",
    })
    fetch("europe_pmc_search.json", epmc_url, "Europe PMC", EUROPE_PMC_QUERY)

    ct_url = "https://clinicaltrials.gov/api/v2/studies?" + urllib.parse.urlencode({
        "query.term": CLINICAL_TRIALS_QUERY, "pageSize": "100",
    })
    fetch("clinicaltrials_search.json", ct_url, "ClinicalTrials.gov", CLINICAL_TRIALS_QUERY)

    for accession in GEO_ACCESSIONS:
        url = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?" + urllib.parse.urlencode({
            "acc": accession, "targ": "self", "form": "text", "view": "brief",
        })
        fetch(f"geo_{accession}_brief.soft", url, "NCBI GEO", accession)

    for pmcid in PMCIDS:
        url = f"https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_json/{pmcid}/unicode"
        try:
            fetch(f"pmc_{pmcid}_bioc.json", url, "PubMed Central", pmcid)
        except Exception as exc:  # retained as an explicit retrieval issue
            sources.append({
                "payload_path": "NOT_RETAINED",
                "source": "PubMed Central",
                "query": pmcid,
                "retrieval_timestamp_utc": retrieval_time,
                "url": url,
                "size_bytes": 0,
                "sha256": "NOT_AVAILABLE",
                "retrieval_error": f"{type(exc).__name__}: {exc}",
            })

    manifest = {
        "retrieval_id": stable_id("RETR", retrieval_time, *all_pmids),
        "retrieval_timestamp_utc": retrieval_time,
        "mutable_network_retrieval": True,
        "future_byte_identity_claimed": False,
        "payloads": sources,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def parse_pubmed() -> dict[str, dict[str, str]]:
    root = ET.parse(RAW / "pubmed_screened_records.xml").getroot()
    records: dict[str, dict[str, str]] = {}
    for node in root.findall(".//PubmedArticle"):
        citation = node.find("MedlineCitation")
        article = citation.find("Article") if citation is not None else None
        pmid = citation.findtext("PMID", "") if citation is not None else ""
        if not pmid or article is None:
            continue
        title_node = article.find("ArticleTitle")
        title = "".join(title_node.itertext()).strip() if title_node is not None else ""
        authors = []
        for author in article.findall(".//AuthorList/Author"):
            collective = author.findtext("CollectiveName")
            if collective:
                authors.append(collective)
            else:
                name = " ".join(x for x in [author.findtext("ForeName", ""), author.findtext("LastName", "")] if x)
                if name:
                    authors.append(name)
        journal = article.findtext("Journal/Title", "")
        year = article.findtext("Journal/JournalIssue/PubDate/Year", "")
        if not year:
            medline_date = article.findtext("Journal/JournalIssue/PubDate/MedlineDate", "")
            match = re.search(r"(?:19|20)\d{2}", medline_date or "")
            year = match.group(0) if match else "UNKNOWN"
        types = [x.text or "" for x in article.findall("PublicationTypeList/PublicationType")]
        ids = {x.attrib.get("IdType", ""): (x.text or "") for x in node.findall("PubmedData/ArticleIdList/ArticleId")}
        records[pmid] = {
            "PMID": pmid,
            "PMCID": ids.get("pmc", "NOT_AVAILABLE"),
            "DOI": ids.get("doi", "NOT_AVAILABLE"),
            "title": title,
            "authors": "; ".join(authors),
            "year": year,
            "journal": journal,
            "article_type": "; ".join(types) if types else "NOT_REPORTED",
        }
    return records


# Reviewed screening decisions.  Evidence inclusion means only that a bounded
# observation can be represented; it is not a judgement of quality or relevance.
SCREENING = {
    "41804162": ("CONTEXT_DEPENDENT", "LUAD A549 experimental model; multi-target compound exposure"),
    "41654000": ("CONTEXT_DEPENDENT", "Non-tumour lung tissue from NSCLC/interstitial-pneumonia context"),
    "40826767": ("INCLUDED_PRIMARY_EVIDENCE", "LUAD-resolved GEO reanalysis; dataset reuse retained"),
    "40552583": ("CONTEXT_DEPENDENT", "Bladder-primary study with a LUAD-resolved pan-cancer analysis"),
    "40386736": ("INCLUDED_PRIMARY_EVIDENCE", "NSCLC cohorts include adenocarcinoma-resolved tissue results"),
    "39904499": ("CONTEXT_DEPENDENT", "ALK-rearranged NSCLC model; histology not established as LUAD"),
    "39672019": ("INCLUDED_PRIMARY_EVIDENCE", "LUAD single-cell analysis with explicit null prognostic result for MMP11"),
    "37602450": ("CONTEXT_DEPENDENT", "Lung-cancer perturbation study; histology/model identity incompletely reported"),
    "37287543": ("EXCLUDED", "Breast-cancer primary study; no LUAD-resolved biological result"),
    "36756152": ("INCLUDED_PRIMARY_EVIDENCE", "LUAD TCGA and clinical cohorts; supportive and null results"),
    "35422093": ("CONTEXT_DEPENDENT", "USP15-focused NSCLC study with four-sample LUAD microarray observation"),
    "34671675": ("CONTEXT_DEPENDENT", "Nonsmoking female lung-cancer GEO cohort; histology incompletely resolved"),
    "31570432": ("INCLUDED_PRIMARY_EVIDENCE", "Lung-cancer germline association null study; histology not separated"),
    "31024988": ("INCLUDED_PRIMARY_EVIDENCE", "Direct LUAD expression, perturbation, xenograft, and antibody study"),
    "30825234": ("CONTEXT_DEPENDENT", "NSCLC osimertinib-resistance study; MMP11 is correlational"),
    "29796998": ("INCLUDED_PRIMARY_EVIDENCE", "Patient-derived LUAD mesenchymal-stromal model"),
    "29568911": ("CONTEXT_DEPENDENT", "A549 plus non-LUAD/unclear model mechanistic study"),
    "19949890": ("CONTEXT_DEPENDENT", "Computational LUAD network reconstruction; MMP11 not perturbed"),
    "18793406": ("CONTEXT_DEPENDENT", "Mixed NSCLC stage comparison; LUAD result not separated"),
    "17310584": ("CONTEXT_DEPENDENT", "Mixed stage-I NSCLC prognosis; near-significant MMP11 result"),
    "15536641": ("CONTEXT_DEPENDENT", "Lung-cancer cell-line betaTrCP study; MMP11 is downstream readout"),
    "15509588": ("CONTEXT_DEPENDENT", "NSCLC–fibroblast co-culture; histology not resolved"),
    "15036884": ("INCLUDED_PRIMARY_EVIDENCE", "Adenocarcinoma and squamous tissue groups explicitly represented"),
    "14647437": ("CONTEXT_DEPENDENT", "Mixed stage-IB lung cancer recurrence study; explicit MMP11 non-validation"),
    "10741738": ("CONTEXT_DEPENDENT", "Mixed NSCLC cohort; adenocarcinoma-specific result unavailable"),
    "10561218": ("EXCLUDED", "Small-cell lung cancer study; outside NSCLC/LUAD scope"),
    "9417124": ("CONTEXT_DEPENDENT", "NSCLC–fibroblast co-culture; histology not resolved"),
    "9137088": ("CONTEXT_DEPENDENT", "Mixed lung carcinomas; 23 adenocarcinomas but MMP11 result not stratified"),
    "8683934": ("EXCLUDED", "Bronchial preinvasive/squamous-lesion context without LUAD result"),
    "7664289": ("CONTEXT_DEPENDENT", "Mixed NSCLC tissue series including adenocarcinoma"),
    "33836753": ("EXCLUDED", "Non-LUAD primary study that cites the 2019 LUAD publication"),
    "37543577": ("EXCLUDED", "Contextual/review record without independently traceable LUAD experiment"),
    "39239548": ("EXCLUDED", "Colorectal-cancer primary context; citation overlap only"),
    "40977645": ("EXCLUDED", "Non-LUAD primary context; citation overlap only"),
    "23659968": ("INCLUDED_PRIMARY_EVIDENCE", "Primary source linked to LUAD GEO accession GSE43458"),
    "15653641": ("INCLUDED_PRIMARY_EVIDENCE", "Primary LUAD expression source linked to E-MEXP-231"),
    "25141350": ("INCLUDED_PRIMARY_EVIDENCE", "Primary LUAD source linked to GSE43767"),
}


def pub_id(pmid: str) -> str:
    return f"PUB_PMID_{pmid}"


def evidence_catalogue() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    def add(pmid: str, domain: str, etype: str, modality: str, question: str,
            model: str, dataset: str, intervention: str, comparator: str,
            outcome: str, direction: str, qualitative: str, quantitative: str,
            statistical: str, location: str, status: str, limitation: str,
            disease: str = "lung adenocarcinoma", histology: str = "LUAD_SPECIFIC") -> None:
        ordinal = sum(1 for x in rows if x["publication_id"] == pub_id(pmid)) + 1
        eid = f"EXT_{pmid}_{ordinal:02d}"
        rows.append({
            "external_evidence_id": eid, "publication_id": pub_id(pmid),
            "EnsemblID": ENSEMBL_ID, "displayed_gene_symbol": SYMBOL,
            "disease_context": disease, "histology_specificity": histology,
            "evidence_domain": domain, "evidence_type": etype,
            "experimental_modality": modality, "biological_question": question,
            "model_system": model, "dataset_or_cohort": dataset,
            "intervention_or_perturbation": intervention, "comparator": comparator,
            "outcome": outcome, "direction_of_observation": direction,
            "qualitative_result": qualitative, "quantitative_result": quantitative,
            "statistical_result": statistical, "source_location": location,
            "evidence_status": status, "major_limitation": limitation,
            "provenance_completeness_status": "COMPLETE_PRIMARY_SOURCE_TRACE",
        })

    # PMID 31024988: separate scientific questions, while dependency remains explicit.
    add("31024988", "A_TRANSCRIPTOMIC_EXPRESSION", "MULTI_GEO_REANALYSIS", "microarray reanalysis",
        "Is MMP11 transcript abundance altered in LUAD?", "Human tumour transcriptomes",
        "GSE7670|GSE10072|GSE68465|GSE43458", "NONE", "Normal lung",
        "MMP11 expression", "TUMOUR_HIGHER", "MMP11 was the highest-upregulated MMP in the joint analysis.",
        "Four GEO cohorts; source-native fold estimates shown in Figure 1", "Reported as significant in source",
        "Figure 1; Results: MMP11 Is Significantly Upregulated", "OBSERVED_SUPPORTIVE",
        "Joint reanalysis combines heterogeneous GEO cohorts; not four independent evidence votes.")
    add("31024988", "A_TRANSCRIPTOMIC_EXPRESSION", "TCGA_REANALYSIS", "RNA-seq reanalysis",
        "Does TCGA-LUAD reproduce tumour-associated expression?", "Human tumour transcriptomes", "TCGA-LUAD",
        "NONE", "Adjacent normal", "MMP11 expression", "TUMOUR_HIGHER", "TCGA analysis showed higher tumour expression.",
        "Approximately five-fold higher", "Source reports significance", "Figure 2A", "OBSERVED_SUPPORTIVE",
        "Shares TCGA-LUAD biological data lineage with Task #039A; not independent replication.")
    add("31024988", "B_PROTEIN_TISSUE", "PATIENT_IHC", "immunohistochemistry",
        "Where is MMP11 protein observed in LUAD tissue?", "18 human LUAD biopsies", "COHORT_2019_LUAD_18",
        "NONE", "Adjacent tissue", "MMP11 staining", "TUMOUR_HIGHER",
        "Strong staining was described in transformed cancer cells with little or no staining in adjacent stroma.",
        "n=18", "Descriptive/source figure", "Figure 2B", "OBSERVED_SUPPORTIVE",
        "Small cohort; staining assessment and selection details limit generalization.")
    add("31024988", "B_PROTEIN_TISSUE", "SERUM_ELISA", "ELISA",
        "Is circulating MMP11 higher in patients with LUAD?", "Human serum", "COHORT_2019_SERUM",
        "NONE", "Healthy donors", "Serum MMP11", "HIGHER_IN_LUAD", "Serum MMP11 was higher in the LUAD group.",
        "18 LUAD; 11 healthy", "p<0.01", "Figure 2C", "OBSERVED_SUPPORTIVE",
        "Small cross-sectional cohort; diagnostic specificity was not established.")
    add("31024988", "D_FUNCTIONAL_PERTURBATION", "CRISPR_PROLIFERATION", "CRISPR/Cas9 knockout",
        "Does MMP11 depletion alter LUAD-cell proliferation?", "A549 LUAD cells", "MODEL_A549_CRISPR",
        "Two MMP11 guide RNAs", "Scrambled/control cells", "Proliferation, Ki67, colony formation", "DECREASED_AFTER_DEPLETION",
        "MMP11 depletion reduced proliferation-related readouts.", "Proliferation >60% lower; colonies nearly 60% lower",
        "Source significance markers", "Figure 2D-F", "OBSERVED_SUPPORTIVE",
        "Single cell line for this evidence unit; CRISPR off-target and clonal effects require consideration.")
    add("31024988", "E_MECHANISTIC", "SIGNALLING_READOUT", "immunoblot after CRISPR",
        "Does MMP11 depletion alter AKT phosphorylation?", "A549 LUAD cells", "MODEL_A549_CRISPR",
        "MMP11 CRISPR", "Control cells", "phospho-AKT", "DECREASED_AFTER_DEPLETION",
        "Phosphorylated AKT was reduced after depletion.", "No source-normalized effect size extracted", "Source figure",
        "Figure 2G", "CONTEXT_DEPENDENT", "Downstream readout does not establish a complete causal pathway.")
    add("31024988", "D_FUNCTIONAL_PERTURBATION", "CRISPR_RESCUE", "CRISPR plus transient rescue",
        "Can MMP11 re-expression partially restore proliferation phenotypes?", "PC9 LUAD cells", "MODEL_PC9_RESCUE",
        "MMP11 depletion then transient MMP11 expression", "Depletion and control conditions", "Proliferation, Ki67, colonies",
        "PARTIALLY_RESTORED", "Depletion-associated reductions were reported as partially rescued.",
        "Source figure; no single aggregate effect", "Source significance markers", "Figure 3", "OBSERVED_SUPPORTIVE",
        "Transient rescue and source-text wording inconsistencies require cautious interpretation.")
    add("31024988", "D_FUNCTIONAL_PERTURBATION", "MIGRATION_INVASION", "wound healing and transwell",
        "Does MMP11 depletion alter migration/invasion?", "A549 and PC9 LUAD cells", "MODEL_LUAD_MIGRATION",
        "MMP11 CRISPR with rescue conditions", "Control cells", "Migration and invasion", "DECREASED_AFTER_DEPLETION",
        "Migration/invasion readouts decreased; rescue was partial.", "A549 invasion approximately 60% lower; n=3-5 by assay",
        "Source significance markers", "Figure 5", "OBSERVED_SUPPORTIVE",
        "Assays share cell systems and publication; migration assays are not metastasis outcomes.")
    add("31024988", "G_INTERVENTION", "ANTIBODY_IN_VITRO", "antibody exposure",
        "Does an anti-MMP11 antibody alter LUAD-cell growth?", "A549 and PC9 LUAD cells", "MODEL_ANTIBODY_IN_VITRO",
        "Anti-MMP11 antibody 1-10 microgram/mL", "0 microgram/mL", "Cell growth", "DECREASED_WITH_ANTIBODY",
        "Growth inhibition was reported from 1 microgram/mL.", "n=4; followed to 96 h", "Source significance markers",
        "Figure 4", "OBSERVED_SUPPORTIVE", "Reagent specificity and translational pharmacology were not independently established.")
    add("31024988", "G_INTERVENTION", "ANTIBODY_MIGRATION", "antibody exposure plus wound healing",
        "Does an anti-MMP11 antibody alter migration?", "A549 and PC9 LUAD cells", "MODEL_ANTIBODY_MIGRATION",
        "Anti-MMP11 antibody 0.5-1 microgram/mL", "0 microgram/mL", "Migration", "DECREASED_WITH_ANTIBODY",
        "Migration decreased with antibody exposure.", "n=5", "Source significance markers", "Figure 6",
        "OBSERVED_SUPPORTIVE", "Same antibody and cell systems as other paper experiments; not an independent replication.")
    add("31024988", "F_IN_VIVO", "GENETIC_XENOGRAFT", "subcutaneous xenograft",
        "Does MMP11 depletion alter xenograft growth?", "A549 xenograft in female BALB/c nude mice", "MODEL_A549_XENOGRAFT_KO",
        "MMP11-depleted A549 cells", "Control A549 cells", "Tumour volume", "DECREASED_AFTER_DEPLETION",
        "Control tumours were reported approximately four times larger at day 30.", "n=8 per stated experiment", "p<0.001",
        "Figure 7A", "OBSERVED_SUPPORTIVE", "Subcutaneous immunodeficient-mouse model does not establish patient efficacy.")
    add("31024988", "G_INTERVENTION", "ANTIBODY_XENOGRAFT", "preclinical antibody intervention",
        "Does anti-MMP11 antibody exposure alter xenograft growth?", "A549 xenograft in female BALB/c nude mice", "MODEL_A549_XENOGRAFT_AB",
        "1 mg/kg IV every four days, four administrations", "Control treatment", "Tumour volume", "DECREASED_WITH_ANTIBODY",
        "Antibody treatment reduced tumour growth.", ">60% reduction reported; n=8", "p<0.001", "Figure 7B",
        "OBSERVED_SUPPORTIVE", "Preclinical model only; efficacy, specificity, exposure, and safety require further study.")

    # PMID 36756152: explicitly retain null and subgroup findings.
    add("36756152", "A_TRANSCRIPTOMIC_EXPRESSION", "TCGA_REANALYSIS", "RNA-seq reanalysis",
        "Is MMP11 higher in LUAD and EGFR-mutant LUAD?", "TCGA-LUAD", "TCGA-LUAD",
        "NONE", "Normal lung and EGFR-wild-type LUAD", "MMP11 expression", "TUMOUR_HIGHER_AND_EGFR_MUTANT_HIGHER",
        "MMP11 was higher in tumour and modestly higher in EGFR-mutant cases.", "512 cases with known EGFR status; 59 normals",
        "Tumour vs normal p<0.001; mutant vs wild type p<0.05", "Results/Figure 1", "OBSERVED_SUPPORTIVE",
        "Shares TCGA-LUAD lineage with Task #039A and the 2019 TCGA reanalysis.")
    add("36756152", "C_CLINICAL_ASSOCIATION", "EGFR_SUBTYPE_COMPARISON", "TCGA subgroup analysis",
        "Does MMP11 differ across EGFR mutation subtypes?", "TCGA-LUAD EGFR-mutant subset", "TCGA-LUAD",
        "NONE", "Exon 19 deletion, L858R, uncommon, compound subtypes", "MMP11 expression", "NO_OVERALL_SUBTYPE_DIFFERENCE",
        "No overall difference among EGFR-mutant subtypes was reported.", "19 exon19del; 18 L858R; 18 uncommon; 11 compound",
        "overall p>0.05", "Results/Figure 1F", "OBSERVED_NULL",
        "Small subtype groups and shared TCGA cohort.")
    add("36756152", "B_PROTEIN_TISSUE", "CLINICAL_IHC", "immunohistochemistry",
        "Is MMP11 protein higher in EGFR-mutant LUAD?", "Resected human LUAD", "COHORT_2023_LUAD_37",
        "NONE", "EGFR-wild-type LUAD", "MMP11 IHC", "HIGHER_IN_EGFR_MUTANT",
        "Higher MMP11 IHC was reported in EGFR-mutant cases.", "20 mutant mean 5.45; 17 wild type mean 2.353", "p<0.001",
        "Results/Figure 2", "OBSERVED_SUPPORTIVE", "Single-centre small retrospective cohort.")
    add("36756152", "E_MECHANISTIC", "IMMUNE_CORRELATION", "computational immune deconvolution",
        "Is MMP11 associated with activated CD8 and NK-cell estimates?", "TCGA-LUAD", "TCGA-LUAD",
        "NONE", "Lower-MMP11 cases", "Estimated activated immune-cell abundance", "LOWER_WITH_HIGH_MMP11",
        "High-MMP11 cases had lower estimated activated CD8 and NK-cell abundance.", "No causal effect size extracted", "Source significance tests",
        "Results/Figure 4", "CONTEXT_DEPENDENT", "Computational estimates from shared bulk TCGA data do not establish mechanism.")
    add("36756152", "B_PROTEIN_TISSUE", "IMMUNE_IHC", "patient-tissue immunostaining",
        "Are CD8/NK observations reproduced in tissue?", "Resected human LUAD", "COHORT_2023_LUAD_37",
        "NONE", "MMP11-negative regions/cases", "CD8 and NK-cell staining", "LOWER_IN_MMP11_POSITIVE_CONTEXT",
        "Tumour parenchyma with MMP11 positivity showed lower CD8/NK staining.", "Cohort n=37", "Source tests",
        "Results/Figure 5", "CONTEXT_DEPENDENT", "Spatial association in the same clinical cohort is not causal.")
    add("36756152", "C_CLINICAL_ASSOCIATION", "CYTOTOXIC_T_CELL_ASSOCIATION", "computational association",
        "Is MMP11 correlated with cytotoxic T-cell level?", "LUAD computational cohort", "TCGA-LUAD",
        "NONE", "Continuous MMP11 expression", "Cytotoxic T-cell level", "NO_ASSOCIATION",
        "No statistically significant correlation was reported.", "NOT_REPORTED_AS_EFFECT_SIZE", "p=0.192",
        "Results/immune analysis", "OBSERVED_NULL", "Computational estimate; shared TCGA dataset.")
    add("36756152", "C_CLINICAL_ASSOCIATION", "ICB_BENEFIT_PREDICTION", "TIDE/Kaplan-Meier analysis",
        "Is MMP11 associated with clinical benefit of immune-checkpoint blockade?", "LUAD computational prediction", "TCGA-LUAD",
        "NONE", "MMP11-high vs low", "Predicted/annotated ICB benefit", "NO_ASSOCIATION",
        "No significant association with clinical benefit was reported.", "NOT_REPORTED_AS_EFFECT_SIZE", "p=0.598",
        "Results/Figure 6", "OBSERVED_NULL", "TIDE is a computational predictor, not a prospective treatment cohort.")
    add("36756152", "C_CLINICAL_ASSOCIATION", "TIDE_PREDICTION", "computational prediction",
        "Is MMP11 associated with TIDE score?", "TCGA-LUAD", "TCGA-LUAD", "NONE", "MMP11-low",
        "TIDE score", "HIGHER_TIDE_WITH_HIGH_MMP11", "Higher TIDE scores were reported in the high-MMP11 group.",
        "No clinical efficacy effect size", "Source test", "Results/Figure 6", "CONTEXT_DEPENDENT",
        "Predicted response metric must not be represented as observed clinical efficacy.")

    # Additional patient, cohort, null, contextual, and reanalysis evidence.
    add("40386736", "A_TRANSCRIPTOMIC_EXPRESSION", "MULTI_GEO_REANALYSIS", "microarray reanalysis",
        "Is MMP11 transcript abundance higher in lung-cancer datasets?", "Human lung tumour transcriptomes",
        "GSE33479|GSE18842|GSE32863", "NONE", "Non-tumour controls", "MMP11 expression", "TUMOUR_HIGHER",
        "MMP11 was elevated in all three reanalysed datasets.", "AUCs 0.933, 0.984, 0.991", "all p<0.001",
        "Results/Figure 1", "INSUFFICIENTLY_SPECIFIC", "Only GSE32863 is LUAD-specific; other datasets include squamous or mixed histology.",
        disease="NSCLC with LUAD subset", histology="PARTIALLY_LUAD_SPECIFIC")
    add("40386736", "B_PROTEIN_TISSUE", "TISSUE_LYSATE_ASSAY", "protein assay",
        "Is tissue MMP11 higher in adenocarcinoma than adjacent normal?", "Human lung adenocarcinoma tissue", "COHORT_2025_TISSUE_20",
        "NONE", "Adjacent normal", "Tissue MMP11", "TUMOUR_HIGHER",
        "Adenocarcinoma tissue had higher MMP11 than adjacent normal.", "39.50±3.31 vs 6.85±1.37", "p<0.001",
        "Results/tissue analysis", "OBSERVED_SUPPORTIVE", "Small tissue cohort; assay localization not resolved.")
    add("40386736", "B_PROTEIN_TISSUE", "SERUM_ASSAY", "serum protein assay",
        "Is serum MMP11 higher in NSCLC than controls?", "Human serum", "COHORT_2025_SERUM_400", "NONE", "Healthy controls",
        "Serum MMP11", "HIGHER_IN_NSCLC", "Serum MMP11 was higher in NSCLC.",
        "200 NSCLC vs 200 controls; medians 40.55 vs 16.01 ng/mL", "p<0.001", "Results/Figure 3",
        "INSUFFICIENTLY_SPECIFIC", "Primary comparison combines adenocarcinoma and squamous cases.",
        disease="NSCLC", histology="NOT_LUAD_SEPARATED_FOR_PRIMARY_COMPARISON")
    add("40386736", "C_CLINICAL_ASSOCIATION", "HISTOLOGY_COMPARISON", "serum biomarker comparison",
        "Does serum MMP11 distinguish adenocarcinoma from squamous NSCLC?", "Human serum", "COHORT_2025_SERUM_400", "NONE",
        "Squamous NSCLC", "Serum MMP11", "LOWER_IN_ADENOCARCINOMA_THAN_SQUAMOUS",
        "Serum MMP11 was lower in adenocarcinoma than squamous cases.", "Histology AUC 0.6634", "p<0.001",
        "Results/Figure 4", "CONTEXT_DEPENDENT", "Cross-sectional assay does not establish disease mechanism.")
    add("39672019", "A_TRANSCRIPTOMIC_EXPRESSION", "SINGLE_CELL_MARKER", "single-cell reanalysis",
        "Is MMP11 observed among variable myofibroblast genes in LUAD?", "Human LUAD single-cell data", "LUAD_SC_DATASET_2025",
        "NONE", "Other fibroblast states", "Marker-gene status", "OBSERVED_AS_MYOFIBROBLAST_MARKER",
        "MMP11 was one of three high-variance myofibroblast genes.", "No source-normalized effect extracted", "FindAllMarkers result",
        "Results", "CONTEXT_DEPENDENT", "Marker assignment is cell-state association, not target causality.")
    add("39672019", "C_CLINICAL_ASSOCIATION", "PROGNOSTIC_ANALYSIS", "survival association",
        "Was MMP11 associated with LUAD prognosis in the tested signature genes?", "Human LUAD cohort", "LUAD_SURVIVAL_2025",
        "NONE", "Expression strata", "Survival association", "NO_ASSOCIATION_REPORTED",
        "Among CTHRC1, POSTN and MMP11, only POSTN correlated with prognosis.", "NOT_REPORTED", "MMP11 not significant",
        "Abstract/Results", "OBSERVED_NULL", "Source focuses mechanistically on POSTN, not MMP11.")
    add("40552583", "A_TRANSCRIPTOMIC_EXPRESSION", "PAN_CANCER_SINGLE_CELL_REANALYSIS", "single-cell reanalysis",
        "Is an MMP11-positive myofibroblast state reported in a LUAD-resolved pan-cancer analysis?",
        "Human pan-cancer single-cell datasets with LUAD-resolved analysis", "LUAD_PANCANCER_SC_2025",
        "NONE", "Source-defined stromal states", "MMP11-positive myofibroblast state",
        "OBSERVED_IN_LUAD_RESOLVED_REANALYSIS",
        "The bladder-primary publication reported an MMP11-positive myofibroblast state in its LUAD-resolved pan-cancer analysis.",
        "No Task #039B-normalized effect size", "Source-defined analysis", "LUAD-resolved pan-cancer results",
        "CONTEXT_DEPENDENT",
        "The publication's primary experimental context is bladder cancer; no MMP11 perturbation was performed in LUAD.")
    add("34671675", "A_TRANSCRIPTOMIC_EXPRESSION", "GEO_REANALYSIS", "microarray reanalysis",
        "Is MMP11 among upregulated genes in a paired lung-cancer cohort?", "Nonsmoking female lung tumours", "GSE19804", "NONE",
        "Paired normal lung", "MMP11 expression", "TUMOUR_HIGHER", "MMP11 was included among 39 upregulated genes.",
        "60 tumour and 60 paired normal samples", "Study-defined differential expression", "Results/network module",
        "INSUFFICIENTLY_SPECIFIC", "Publication does not fully resolve LUAD histology for every sample.",
        disease="lung cancer", histology="HISTOLOGY_INCOMPLETELY_REPORTED")
    add("34671675", "C_CLINICAL_ASSOCIATION", "SURVIVAL_REANALYSIS", "Kaplan-Meier web-tool analysis",
        "Is high MMP11 associated with survival in the queried lung cohort?", "Lung-cancer survival cohort", "KM_PLOTTER_2021",
        "NONE", "Low MMP11", "Overall survival", "WORSE_WITH_HIGH_MMP11", "High MMP11 was associated with lower survival.",
        "n=168; HR=4.93", "Source figure", "Figure 6e", "INSUFFICIENTLY_SPECIFIC",
        "Underlying cohort composition and accession are not fully traceable in the paper.",
        disease="lung cancer", histology="UNRESOLVED")
    add("35422093", "E_MECHANISTIC", "SMALL_COHORT_MICROARRAY", "expression profiling",
        "Which genes are altered in LUAD with low USP15?", "Four primary LUAD samples", "COHORT_2022_LUAD_4",
        "Low-USP15 context", "Comparator context in study", "MMP11 transcript", "HIGHER_IN_LOW_USP15_CONTEXT",
        "MMP11 was among significantly upregulated genes.", "n=4", "Study-defined significance", "Results/supplementary microarray",
        "CONTEXT_DEPENDENT", "Very small cohort; MMP11 was not directly perturbed.")
    add("29568911", "E_MECHANISTIC", "REGULATORY_AXIS", "miRNA/KLF4 perturbation",
        "Does miR-25/KLF4 perturbation alter MMP11 readout?", "A549 and Calu-1 cells", "MODEL_MIR25_A549_CALU1",
        "miR-25 inhibition/overexpression and KLF4 manipulation", "Matched controls", "MMP11 expression and invasion",
        "MMP11_TRACKED_INVASIVE_PHENOTYPE", "MMP11 decreased with miR-25 inhibition and increased in the reciprocal context.",
        "No independent MMP11-mediated effect isolated", "Source tests", "Results/Figures", "CONTEXT_DEPENDENT",
        "MMP11 was a downstream readout and was not itself perturbed; Calu-1 is not LUAD.")
    add("29796998", "B_PROTEIN_TISSUE", "PATIENT_DERIVED_STROMAL_MODEL", "cell isolation and co-culture",
        "Do LUAD tumour-derived MSCs display an MMP11-positive CAF-like phenotype?", "MSCs from one LUAD patient plus A549 co-culture",
        "COHORT_2018_ONE_PATIENT", "Tumour-derived vs healthy-tissue MSCs", "Healthy-tissue MSCs", "CAF-marker expression",
        "MMP11_HIGHER_IN_TUMOUR_DERIVED_MSCS", "MMP11 was among CAF-related markers higher in tumour-derived MSCs.",
        "One patient", "Reported significant marker difference", "Results/Abstract", "CONTEXT_DEPENDENT",
        "Single-patient stromal model; MMP11-specific functional contribution was not tested.")
    add("31570432", "C_CLINICAL_ASSOCIATION", "GERMLINE_CASE_CONTROL", "genotyping",
        "Are four MMP11 promoter variants associated with lung-cancer susceptibility?", "Taiwanese lung-cancer cases and controls",
        "COHORT_2019_GENOTYPE_1074", "NONE", "Healthy controls", "Lung-cancer risk", "NO_ASSOCIATION",
        "No association was found for rs738791, rs2267029, rs738792, or rs28382575.", "358 cases; 716 controls",
        "rs738791 trend p=0.5638; other tests null", "Abstract/Results", "OBSERVED_NULL",
        "Histology-specific LUAD estimates were not reported.", disease="lung cancer", histology="NOT_LUAD_SEPARATED")
    add("30825234", "E_MECHANISTIC", "CORRELATIONAL_TISSUE_ANALYSIS", "expression correlation",
        "Is SPOCK1 expression correlated with MMP11 in NSCLC tissue?", "Human NSCLC tissue", "COHORT_SPOCK1_NSCLC",
        "SPOCK1 context", "Normal tissue", "MMP11 correlation", "POSITIVE_CORRELATION",
        "SPOCK1 overexpression was positively correlated with MMP11 and TGF-beta1.", "NOT_REPORTED", "Source reports correlation",
        "Abstract/Results", "CONTEXT_DEPENDENT", "MMP11 was not perturbed and LUAD histology was not separated.",
        disease="NSCLC", histology="NOT_LUAD_SEPARATED")
    add("37602450", "D_FUNCTIONAL_PERTURBATION", "AXIS_RESCUE", "lncRNA knockdown and MMP11 overexpression rescue",
        "Can MMP11 overexpression offset effects of linc00511 silencing?", "Lung-cancer cells", "MODEL_LINC00511_UNRESOLVED",
        "linc00511 knockdown; miR-16-5p inhibition or MMP11 overexpression", "Matched controls", "Malignant phenotypes",
        "PARTIAL_OR_REPORTED_RESCUE", "MMP11 overexpression was reported to offset suppressive effects of linc00511 silencing.",
        "NOT_REPORTED_IN_ABSTRACT", "Source tests", "Abstract/Results", "INSUFFICIENTLY_SPECIFIC",
        "Cell-line identity and LUAD histology are not explicit enough in accessible source text.",
        disease="lung cancer", histology="UNRESOLVED")
    add("39904499", "E_MECHANISTIC", "SINGLE_CELL_TREATMENT_CONTEXT", "single-cell RNA-seq",
        "Does alectinib treatment alter Mmp11 in stromal cells?", "ALK-rearranged NSCLC/host stromal models", "MODEL_ALK_ALECTINIB",
        "Alectinib", "Pretreatment/control", "CAF Mmp11 expression", "INCREASED_DURING_TREATMENT",
        "CAFs substantially upregulated Mmp11 during alectinib treatment.", "NOT_REPORTED_AS_EFFECT_SIZE", "Source analysis",
        "Abstract/Results", "CONTEXT_DEPENDENT", "MMP11 was not perturbed; histology and species/source-cell distinctions limit LUAD inference.",
        disease="ALK-rearranged NSCLC", histology="NOT_LUAD_ESTABLISHED")
    add("40826767", "A_TRANSCRIPTOMIC_EXPRESSION", "DERIVED_GEO_REANALYSIS", "integrative bioinformatics",
        "Is MMP11 among shared COPD/LUAD/LUSC expression features?", "Human GEO transcriptomes", "GSE76925|GSE18842|GSE10072",
        "NONE", "Disease-specific controls", "Shared DEG/hub status", "OBSERVED_AS_SHARED_DEG",
        "MMP11 was identified among 15 shared DEGs and as a network hub.", "No source-native effect extracted", "Study-defined thresholds",
        "Abstract/Results", "CONTEXT_DEPENDENT", "Reuses GSE10072 and GSE18842; network hub status is not causal evidence.")
    add("41804162", "E_MECHANISTIC", "COMPOUND_EXPOSURE_READOUT", "RT-qPCR after multi-target compound exposure",
        "Does cirsimarin exposure alter MMP11 transcript in A549 cells?", "A549 LUAD cells in 2D culture", "MODEL_CIRSIMARIN_A549",
        "Cirsimarin 1-80 micromolar", "Vehicle/control", "MMP11 transcript and migration", "MMP11_DECREASED_WITH_EXPOSURE",
        "Cirsimarin reduced migration and multiple genes including MMP11.", "MMP11 0.04-fold; migration inhibited",
        "Source tests", "Abstract/Results", "CONTEXT_DEPENDENT",
        "Multi-target, partly cytotoxic exposure; no MMP11 mediation or direct binding test.")
    add("41654000", "E_MECHANISTIC", "DRUG_EXPOSURE_NON_TUMOUR_TISSUE", "RNA-seq",
        "Does nintedanib exposure alter MMP11 in non-tumour lung?", "Non-tumour lung from NSCLC patients with interstitial pneumonia",
        "COHORT_NINTEDANIB_NON_TUMOUR", "Preoperative nintedanib", "Untreated fibrotic/non-IP tissue", "MMP11 transcript",
        "INCREASED_AFTER_NINTEDANIB", "MMP11 was upregulated in non-tumour lung after nintedanib.", "7 treated non-tumour samples stated",
        "Study-defined differential expression", "Abstract/Results", "INSUFFICIENTLY_SPECIFIC",
        "Non-tumour fibrotic/inflammatory tissue context; not evidence of LUAD-tumour response.",
        disease="NSCLC with interstitial pneumonia", histology="NON_TUMOUR_CONTEXT")

    # Historical tissue/co-culture evidence, retaining limited histology resolution and null results.
    add("10741738", "A_TRANSCRIPTOMIC_EXPRESSION", "TUMOUR_NORMAL_TISSUE", "Northern blot",
        "Is MMP11 higher in resected NSCLC than matched normal lung?", "Human NSCLC tissue", "COHORT_2000_NSCLC_119",
        "NONE", "Adjacent normal", "MMP11 RNA", "TUMOUR_HIGHER", "MMP11 was increased in tumour tissue.",
        "Average tumour:normal ratio 83.5; 30 matched pairs within 119 cases", "Reported significant", "Abstract/Results",
        "INSUFFICIENTLY_SPECIFIC", "Mixed NSCLC histologies; LUAD-specific estimate unavailable.",
        disease="NSCLC", histology="NOT_LUAD_SEPARATED")
    add("10741738", "C_CLINICAL_ASSOCIATION", "LYMPH_NODE_ASSOCIATION", "clinicopathological association",
        "Is MMP11 tumour:normal ratio associated with lymph-node involvement?", "Human NSCLC tissue", "COHORT_2000_NSCLC_119",
        "NONE", "Node-negative disease", "Lymph-node involvement", "POSITIVE_ASSOCIATION", "Higher ratio was linked to nodal involvement.",
        "NOT_REPORTED", "p<0.05", "Abstract/Results", "INSUFFICIENTLY_SPECIFIC",
        "Mixed histology and observational association.", disease="NSCLC", histology="NOT_LUAD_SEPARATED")
    add("9137088", "B_PROTEIN_TISSUE", "IN_SITU_AND_IHC", "in situ hybridization and IHC",
        "Where is MMP11 expressed in lung carcinomas?", "89 human lung carcinomas", "COHORT_1997_LUNG_89",
        "NONE", "Histologic groups", "Stromal/epithelial MMP11", "PREDOMINANTLY_STROMAL",
        "MMP11 was more often stromal; 23 adenocarcinomas were included.", "89 total; 23 adenocarcinoma", "Descriptive",
        "Abstract/Results", "INSUFFICIENTLY_SPECIFIC", "Key MMP11 associations were not stratified for adenocarcinoma.",
        disease="lung carcinoma", histology="ADENOCARCINOMA_INCLUDED_NOT_SEPARATED")
    add("9137088", "C_CLINICAL_ASSOCIATION", "TUMOUR_SIZE_NODE_ASSOCIATION", "clinicopathological association",
        "Is stromal MMP11 associated with tumour size or nodal involvement?", "Non-NE NSCLC", "COHORT_1997_LUNG_89",
        "NONE", "Clinical strata", "Tumour size and lymph-node involvement", "POSITIVE_ASSOCIATION",
        "Stromal MMP11 was linked to tumour size and nodal involvement.", "NOT_REPORTED", "p=0.03 and p=0.02",
        "Abstract/Results", "INSUFFICIENTLY_SPECIFIC", "Non-NE aggregate, not LUAD-specific.",
        disease="NSCLC", histology="NOT_LUAD_SEPARATED")
    add("7664289", "A_TRANSCRIPTOMIC_EXPRESSION", "TISSUE_EXPRESSION", "RNA/protein tissue analysis",
        "Is MMP11 more abundant in NSCLC than adjacent normal lung?", "Stage I-III NSCLC tissue", "COHORT_1995_NSCLC",
        "NONE", "Adjacent normal", "MMP11 transcript/protein", "TUMOUR_HIGHER", "Transcript and protein were more abundant in NSCLC.",
        "Cohort includes squamous and adenocarcinoma", "Reported significant", "Abstract/Results", "INSUFFICIENTLY_SPECIFIC",
        "Histology-specific estimates unavailable.", disease="NSCLC", histology="ADENOCARCINOMA_INCLUDED_NOT_SEPARATED")
    add("7664289", "B_PROTEIN_TISSUE", "CELLULAR_LOCALIZATION", "tissue localization",
        "Which compartment contains MMP11 in NSCLC?", "Human NSCLC tissue", "COHORT_1995_NSCLC", "NONE", "Tumour compartments",
        "MMP11 localization", "PREDOMINANTLY_STROMAL", "MMP11 was primarily localized to stromal elements.",
        "NOT_REPORTED", "Descriptive", "Abstract/Results", "INSUFFICIENTLY_SPECIFIC",
        "Mixed histology and historical assay context.", disease="NSCLC", histology="NOT_LUAD_SEPARATED")
    add("17310584", "C_CLINICAL_ASSOCIATION", "SURVIVAL_ASSOCIATION", "stromal IHC survival analysis",
        "Is stromal MMP11 associated with cancer-related survival in stage-I NSCLC?", "80 resected stage-I NSCLC cases",
        "COHORT_2007_NSCLC_80", "NONE", "Expression strata", "Cancer-related survival", "NO_STATISTICALLY_SIGNIFICANT_ASSOCIATION",
        "The source described a near-significant relation, not a significant result.", "n=80", "Near-significant; exact p not in abstract",
        "Abstract", "OBSERVED_NULL", "Mixed histology; treating near-significance as supportive would be misleading.",
        disease="NSCLC", histology="NOT_LUAD_SEPARATED")
    add("14647437", "C_CLINICAL_ASSOCIATION", "RECURRENCE_EXPRESSION", "microarray plus validation",
        "Is MMP11 consistently higher in recurrent stage-IB lung cancer?", "20 stage-IB lung cancers", "COHORT_2004_STAGEIB_20",
        "NONE", "Non-recurrent cases", "MMP11 expression", "NOT_VALIDATED_AS_GROUP_DIFFERENCE",
        "MMP11 was up in one recurrent case; only MMP10 and MMP12 validated as significant group findings.", "10 recurrent; 10 non-recurrent",
        "No MMP11 group significance reported", "Abstract/Results", "OBSERVED_NULL",
        "Small mixed-histology cohort; MMP11 was not a validated recurrence marker.",
        disease="lung cancer", histology="NOT_LUAD_SEPARATED")
    add("15036884", "A_TRANSCRIPTOMIC_EXPRESSION", "HISTOLOGY_RESOLVED_TISSUE", "expression profiling",
        "Is MMP11 upregulated in lung adenocarcinoma tissue?", "Human adenocarcinoma and squamous tissue", "COHORT_2004_ADC_SCC_26",
        "NONE", "Normal lung", "MMP11 expression", "TUMOUR_HIGHER", "MMP11 was reported among genes upregulated in both histologies.",
        "13 adenocarcinoma; 13 squamous", "Study-defined differential expression", "Results", "OBSERVED_SUPPORTIVE",
        "Small cohort and historical profiling platform.")
    add("18793406", "C_CLINICAL_ASSOCIATION", "STAGE_COMPARISON", "qPCR validation",
        "Is MMP11 higher in stage II than stage I NSCLC?", "Stage I/II NSCLC", "COHORT_2008_NSCLC_64",
        "NONE", "Stage I", "MMP11 expression", "HIGHER_IN_STAGE_II", "MMP11 was reported higher in stage II.",
        "3.68-fold", "Source validation table", "Table 2/Results", "INSUFFICIENTLY_SPECIFIC",
        "Mixed 33 squamous, 23 adenocarcinoma, and 8 other cases; no LUAD-stratified result.",
        disease="NSCLC", histology="NOT_LUAD_SEPARATED")
    add("9417124", "E_MECHANISTIC", "TUMOUR_STROMA_COCULTURE", "co-culture",
        "Can NSCLC cells induce MMP11 secretion by pulmonary fibroblasts?", "NSCLC–normal pulmonary fibroblast co-culture",
        "MODEL_1998_COCULTURE", "Tumour/stroma co-culture", "Fibroblasts alone", "MMP11 secretion/processing",
        "INDUCED_IN_FIBROBLASTS", "Co-culture induced fibroblast MMP11 secretion; processing context was assessed.",
        "NOT_REPORTED", "Source tests", "Abstract/Results", "CONTEXT_DEPENDENT",
        "Histology unresolved; model does not isolate LUAD-specific signalling.", disease="NSCLC", histology="UNRESOLVED")
    add("15509588", "E_MECHANISTIC", "SIGNALLING_IN_COCULTURE", "co-culture plus kinase perturbation",
        "Which PKC pathways mediate tumour-cell induction of fibroblast MMP11?", "NSCLC–pulmonary fibroblast co-culture",
        "MODEL_2005_COCULTURE", "PKC-alpha/epsilon modulation", "Matched controls", "Fibroblast MMP11 induction",
        "PKC_DEPENDENT_INDUCTION", "PKC-alpha and PKC-epsilon were required for MMP11 induction.", "NOT_REPORTED", "Source tests",
        "Abstract/Results", "CONTEXT_DEPENDENT", "Histology unresolved; stromal induction model is not direct tumour-cell dependency.",
        disease="NSCLC", histology="UNRESOLVED")
    add("15536641", "E_MECHANISTIC", "DOWNSTREAM_READOUT", "betaTrCP restoration",
        "Does betaTrCP restoration alter active MMP11 and motility?", "Lung-cancer cell lines", "MODEL_BTRCP_LUNG",
        "betaTrCP restoration", "Control", "Active MMP11 and motility", "DECREASED_WITH_BTRCP_RESTORATION",
        "Active MMP11 and motility decreased after betaTrCP restoration.", "NOT_REPORTED", "Source tests", "Results",
        "CONTEXT_DEPENDENT", "MMP11 was downstream and not directly perturbed; LUAD identity unresolved.",
        disease="lung cancer", histology="UNRESOLVED")
    add("19949890", "E_MECHANISTIC", "COMPUTATIONAL_NETWORK", "integrative biocomputation",
        "How is MMP11 placed in a computed SPP1 upstream network?", "LUAD vs adjacent-normal expression", "DATASET_2010_UNRESOLVED",
        "NONE", "Adjacent normal network", "Network-edge assignment", "CONTEXT_SPECIFIC_NETWORK_CHANGE",
        "MMP11 appeared in different inferred modules/edge directions between contexts.", "No direct perturbation", "Algorithmic result",
        "Abstract/Results", "CONTEXT_DEPENDENT", "Underlying dataset and inferred edges require source-specific reconstruction; no causal perturbation.")

    # Primary GEO sources encountered through the frozen Open Targets/Expression Atlas lineage.
    add("23659968", "A_TRANSCRIPTOMIC_EXPRESSION", "PRIMARY_GEO_COHORT", "microarray",
        "Is MMP11 expression observed in smoking-stratified LUAD vs normal comparisons?", "Human LUAD/normal tissue", "GSE43458",
        "NONE", "Normal lung", "MMP11 expression record availability", "TUMOUR_ASSOCIATED_RECORD_AVAILABLE",
        "The primary dataset supports LUAD-versus-normal contrasts used by downstream reanalyses.", "40 never-smoker LUAD; 40 smoker LUAD; 30 normal",
        "Not re-estimated in Task #039B", "GEO GSE43458 and linked publication", "OBSERVED_SUPPORTIVE",
        "Task #039B preserves the source record but does not recompute expression statistics.")
    add("15653641", "A_TRANSCRIPTOMIC_EXPRESSION", "PRIMARY_ARRAY_COHORT", "microarray",
        "Is a primary LUAD-versus-normal transcriptomic dataset available?", "Human LUAD/normal tissue", "E-MEXP-231",
        "NONE", "Normal lung", "MMP11 expression record availability", "TUMOUR_ASSOCIATED_RECORD_AVAILABLE",
        "A LUAD-versus-normal source record is present in the frozen Open Targets/Expression Atlas lineage.", "Cohort details retained by source",
        "Not re-estimated in Task #039B", "Publication and Expression Atlas accession", "OBSERVED_SUPPORTIVE",
        "Array accession is not GEO; raw values were not retrieved in this task.")
    add("25141350", "A_TRANSCRIPTOMIC_EXPRESSION", "PRIMARY_GEO_COHORT", "microarray",
        "Is a LUAD development-related transcriptomic cohort available?", "Human lung/LUAD developmental context", "GSE43767",
        "NONE", "Source-defined controls", "MMP11 expression record availability", "TUMOUR_ASSOCIATED_RECORD_AVAILABLE",
        "A LUAD-versus-normal source record is present in the frozen Open Targets/Expression Atlas lineage.", "113 GEO samples",
        "Not re-estimated in Task #039B", "GEO GSE43767 and linked publication", "CONTEXT_DEPENDENT",
        "Developmental and tumour contexts are mixed; Task #039B does not recompute contrasts.")
    return rows


def dataset_catalogue() -> list[dict[str, str]]:
    data = [
        ("TCGA-LUAD", "TCGA-LUAD", "GDC/recount3", "LUAD", "tumour and normal transcriptomes", "Source-dependent; Task #039A cohort 574 observations", "31024988|36756152", "TRUE", "FALSE", "NOT_APPLICABLE", "SHARED_DATASET with Task #039A primary transcriptomic evidence", "SHARED_DATASET"),
        ("GSE7670", "GSE7670", "NCBI GEO", "LUAD", "tumour and normal lung", "66 GEO records", "31024988", "FALSE", "TRUE", "GSE7670", "External GEO cohort; distinct from Task #039A TCGA data", "NO_DEPENDENCY_IDENTIFIED"),
        ("GSE10072", "GSE10072", "NCBI GEO", "LUAD", "tumour and normal lung", "107 GEO records; source design notes larger selected set/duplicates", "31024988|40826767", "FALSE", "TRUE", "GSE10072", "External GEO cohort reused across publications", "SHARED_DATASET"),
        ("GSE68465", "GSE68465", "NCBI GEO", "LUAD", "tumour transcriptomes", "462 records; source describes 442 LUAD", "31024988", "FALSE", "TRUE", "GSE68465", "External GEO cohort", "NO_DEPENDENCY_IDENTIFIED"),
        ("GSE43458", "GSE43458", "NCBI GEO", "LUAD", "smoking-stratified tumour and normal", "110 records: 40 never-smoker LUAD, 40 smoker LUAD, 30 normal", "31024988|23659968", "FALSE", "TRUE", "GSE43458", "External GEO cohort also represented in Task #039A Open Targets/Expression Atlas lineage", "SHARED_DATASET"),
        ("GSE33479", "GSE33479", "NCBI GEO", "squamous/bronchial", "bronchial biopsies", "122 records", "40386736", "FALSE", "TRUE", "GSE33479", "Not a LUAD replication", "NO_DEPENDENCY_IDENTIFIED"),
        ("GSE18842", "GSE18842", "NCBI GEO", "mixed lung cancer", "tumour and control", "91 records; 46 tumour, 45 control", "40386736|40826767", "FALSE", "TRUE", "GSE18842", "External GEO cohort reused across publications", "SHARED_DATASET"),
        ("GSE32863", "GSE32863", "NCBI GEO", "LUAD", "paired tumour and adjacent normal", "116 records; 58 pairs", "40386736", "FALSE", "TRUE", "GSE32863", "Potentially distinct LUAD dataset lineage", "NO_DEPENDENCY_IDENTIFIED"),
        ("GSE19804", "GSE19804", "NCBI GEO", "lung cancer; histology incompletely resolved", "paired tumour and normal", "120 records; 60 pairs", "34671675", "FALSE", "TRUE", "GSE19804", "External GEO dataset; LUAD specificity unresolved", "NO_DEPENDENCY_IDENTIFIED"),
        ("GSE76925", "GSE76925", "NCBI GEO", "COPD", "lung tissue", "151 records", "40826767", "FALSE", "TRUE", "GSE76925", "Non-cancer comparator dataset in derived reanalysis", "NO_DEPENDENCY_IDENTIFIED"),
        ("GSE43767", "GSE43767", "NCBI GEO", "LUAD/developmental lung", "human lung samples", "113 records", "25141350", "FALSE", "TRUE", "GSE43767", "Also represented in Task #039A Open Targets/Expression Atlas lineage", "SHARED_DATASET"),
        ("E-MEXP-231", "E-MEXP-231", "ArrayExpress/Expression Atlas", "LUAD", "tumour and normal", "Source-defined", "15653641", "FALSE", "FALSE", "NOT_APPLICABLE", "Already represented in Task #039A Open Targets/Expression Atlas lineage", "SHARED_DATASET"),
        ("E-TABM-15", "E-TABM-15", "ArrayExpress/Expression Atlas", "LUAD", "tumour and normal", "Source-defined", "NO_PMID", "FALSE", "FALSE", "NOT_APPLICABLE", "Task #039A Open Targets/Expression Atlas lineage; no new evidence unit created", "SHARED_DATASET"),
        ("COHORT_2019_LUAD_18", "NOT_APPLICABLE", "Primary publication", "LUAD", "patient biopsy", "18", "31024988", "FALSE", "FALSE", "NOT_APPLICABLE", "External patient cohort", "NO_DEPENDENCY_IDENTIFIED"),
        ("COHORT_2019_SERUM", "NOT_APPLICABLE", "Primary publication", "LUAD", "serum", "18 LUAD; 11 healthy", "31024988", "FALSE", "FALSE", "NOT_APPLICABLE", "External patient cohort", "SAME_COHORT"),
        ("COHORT_2023_LUAD_37", "NOT_APPLICABLE", "Primary publication", "LUAD", "resected tissue", "37", "36756152", "FALSE", "FALSE", "NOT_APPLICABLE", "External patient cohort", "NO_DEPENDENCY_IDENTIFIED"),
        ("COHORT_2025_TISSUE_20", "NOT_APPLICABLE", "Primary publication", "adenocarcinoma and squamous", "tissue lysates", "20", "40386736", "FALSE", "FALSE", "NOT_APPLICABLE", "External patient cohort", "NO_DEPENDENCY_IDENTIFIED"),
        ("COHORT_2025_SERUM_400", "NOT_APPLICABLE", "Primary publication", "NSCLC", "serum", "200 NSCLC; 200 controls", "40386736", "FALSE", "FALSE", "NOT_APPLICABLE", "External patient cohort", "NO_DEPENDENCY_IDENTIFIED"),
        ("COHORT_2022_LUAD_4", "NOT_APPLICABLE", "Primary publication", "LUAD", "primary tissue microarray", "4", "35422093", "FALSE", "FALSE", "NOT_APPLICABLE", "External small patient cohort", "NO_DEPENDENCY_IDENTIFIED"),
        ("COHORT_2018_ONE_PATIENT", "NOT_APPLICABLE", "Primary publication", "LUAD", "patient-derived stromal cells", "1 patient", "29796998", "FALSE", "FALSE", "NOT_APPLICABLE", "External patient-derived model", "NO_DEPENDENCY_IDENTIFIED"),
        ("COHORT_2019_GENOTYPE_1074", "NOT_APPLICABLE", "Primary publication", "lung cancer", "germline case-control", "358 cases; 716 controls", "31570432", "FALSE", "FALSE", "NOT_APPLICABLE", "External genetic cohort; histology not separated", "NO_DEPENDENCY_IDENTIFIED"),
        ("COHORT_2000_NSCLC_119", "NOT_APPLICABLE", "Primary publication", "NSCLC", "resected tissue", "119; 30 matched", "10741738", "FALSE", "FALSE", "NOT_APPLICABLE", "External historical cohort", "NO_DEPENDENCY_IDENTIFIED"),
        ("COHORT_1997_LUNG_89", "NOT_APPLICABLE", "Primary publication", "mixed lung carcinoma", "resected tissue", "89; 23 adenocarcinoma", "9137088", "FALSE", "FALSE", "NOT_APPLICABLE", "External historical cohort", "NO_DEPENDENCY_IDENTIFIED"),
        ("COHORT_1995_NSCLC", "NOT_APPLICABLE", "Primary publication", "NSCLC", "resected tissue", "Source-defined panel", "7664289", "FALSE", "FALSE", "NOT_APPLICABLE", "External historical cohort", "NO_DEPENDENCY_IDENTIFIED"),
        ("COHORT_2007_NSCLC_80", "NOT_APPLICABLE", "Primary publication", "stage-I NSCLC", "resected tissue", "80", "17310584", "FALSE", "FALSE", "NOT_APPLICABLE", "External historical cohort", "NO_DEPENDENCY_IDENTIFIED"),
        ("COHORT_2004_STAGEIB_20", "NOT_APPLICABLE", "Primary publication", "stage-IB lung cancer", "resected tissue", "10 recurrent; 10 non-recurrent", "14647437", "FALSE", "FALSE", "NOT_APPLICABLE", "External historical cohort", "NO_DEPENDENCY_IDENTIFIED"),
        ("COHORT_2004_ADC_SCC_26", "NOT_APPLICABLE", "Primary publication", "adenocarcinoma and squamous", "resected tissue", "13 plus 13", "15036884", "FALSE", "FALSE", "NOT_APPLICABLE", "External historical cohort", "NO_DEPENDENCY_IDENTIFIED"),
        ("COHORT_2008_NSCLC_64", "NOT_APPLICABLE", "Primary publication", "stage-I/II NSCLC", "resected tissue", "64", "18793406", "FALSE", "FALSE", "NOT_APPLICABLE", "External historical cohort", "NO_DEPENDENCY_IDENTIFIED"),
        ("KM_PLOTTER_2021", "NOT_REPORTED", "KM Plotter via publication", "lung cancer", "survival reanalysis", "168", "34671675", "FALSE", "FALSE", "NOT_APPLICABLE", "Underlying accession unresolved", "UNKNOWN"),
        ("LUAD_SC_DATASET_2025", "NOT_REPORTED", "Primary publication", "LUAD", "single-cell dataset", "Source-defined", "39672019", "FALSE", "FALSE", "NOT_APPLICABLE", "Accession unresolved in abstract-level audit", "UNKNOWN"),
        ("LUAD_SURVIVAL_2025", "NOT_REPORTED", "Primary publication", "LUAD", "survival cohort", "Source-defined", "39672019", "FALSE", "FALSE", "NOT_APPLICABLE", "Accession unresolved in abstract-level audit", "UNKNOWN"),
        ("LUAD_PANCANCER_SC_2025", "NOT_REPORTED", "Primary publication", "pan-cancer with LUAD-resolved subset", "single-cell dataset", "Source-defined", "40552583", "FALSE", "FALSE", "NOT_APPLICABLE", "Publication overlaps a Task #039A Open Targets literature record", "UNKNOWN"),
        ("COHORT_SPOCK1_NSCLC", "NOT_APPLICABLE", "Primary publication", "NSCLC", "clinical tissue", "Source-defined", "30825234", "FALSE", "FALSE", "NOT_APPLICABLE", "External clinical cohort; LUAD histology unresolved", "UNKNOWN"),
        ("COHORT_NINTEDANIB_NON_TUMOUR", "NOT_APPLICABLE", "Primary publication", "NSCLC with interstitial pneumonia", "non-tumour and fibrotic lung", "7 treated non-tumour; additional source-defined groups", "41654000", "FALSE", "FALSE", "NOT_APPLICABLE", "Non-tumour treatment context; not Task #039A tumour transcriptomics", "NO_DEPENDENCY_IDENTIFIED"),
        ("DATASET_2010_UNRESOLVED", "NOT_REPORTED", "Primary publication", "LUAD", "computational expression network", "Source-defined", "19949890", "FALSE", "FALSE", "NOT_APPLICABLE", "Underlying accession unresolved", "UNKNOWN"),
    ]
    fields = ["dataset_id", "accession", "source_repository", "disease_histology", "sample_type", "cohort_size", "publication_linkage", "uses_tcga", "uses_geo", "geo_accession", "relation_to_task039a", "dependency_assessment"]
    return [dict(zip(fields, row)) for row in data]


def model_catalogue() -> list[dict[str, str]]:
    models = [
        ("MODEL_A549_CRISPR", "31024988", "CELL_LINE", "A549", "human", "LUAD", "MMP11 CRISPR/Cas9", "scrambled/control", "proliferation; Ki67; colony; pAKT", "PMC6477516 Figures 2D-G"),
        ("MODEL_PC9_RESCUE", "31024988", "CELL_LINE_RESCUE", "PC9", "human", "LUAD", "MMP11 CRISPR plus transient rescue", "control/depletion", "proliferation; Ki67; colony", "PMC6477516 Figure 3"),
        ("MODEL_LUAD_MIGRATION", "31024988", "CELL_LINE", "A549; PC9", "human", "LUAD", "MMP11 CRISPR/rescue", "control", "wound healing; transwell", "PMC6477516 Figure 5"),
        ("MODEL_ANTIBODY_IN_VITRO", "31024988", "CELL_LINE_INTERVENTION", "A549; PC9", "human", "LUAD", "anti-MMP11 antibody", "0 microgram/mL", "growth", "PMC6477516 Figure 4"),
        ("MODEL_ANTIBODY_MIGRATION", "31024988", "CELL_LINE_INTERVENTION", "A549; PC9", "human", "LUAD", "anti-MMP11 antibody", "0 microgram/mL", "migration", "PMC6477516 Figure 6"),
        ("MODEL_A549_XENOGRAFT_KO", "31024988", "ANIMAL_XENOGRAFT", "A549 in female BALB/c nude mice", "human cells/mouse host", "LUAD xenograft", "MMP11-depleted cells", "control cells", "tumour volume", "PMC6477516 Figure 7A"),
        ("MODEL_A549_XENOGRAFT_AB", "31024988", "ANIMAL_XENOGRAFT_INTERVENTION", "A549 in female BALB/c nude mice", "human cells/mouse host", "LUAD xenograft", "anti-MMP11 antibody IV", "control treatment", "tumour volume", "PMC6477516 Figure 7B"),
        ("MODEL_MIR25_A549_CALU1", "29568911", "CELL_LINE", "A549; Calu-1", "human", "LUAD plus non-LUAD/unclear", "miR-25/KLF4 perturbation", "matched controls", "MMP11; invasion", "PMC5928655"),
        ("MODEL_LINC00511_UNRESOLVED", "37602450", "CELL_LINE", "Not explicit in abstract", "human presumed", "lung cancer unresolved", "linc00511 knockdown; MMP11 rescue", "matched controls", "malignant phenotypes", "PMID 37602450"),
        ("MODEL_ALK_ALECTINIB", "39904499", "CELL_LINE_ANIMAL_SINGLE_CELL", "H3122; NIH3T3; mouse host stromal cells", "human/mouse", "ALK-rearranged NSCLC", "alectinib/GAS6/AXL context", "matched controls", "resistance and stromal Mmp11", "PMID 39904499"),
        ("MODEL_CIRSIMARIN_A549", "41804162", "CELL_LINE", "A549 2D/3D; MRC-5 comparator", "human", "LUAD", "cirsimarin", "vehicle", "viability; migration; RT-qPCR", "PMID 41804162"),
        ("MODEL_1998_COCULTURE", "9417124", "COCULTURE", "NSCLC cells plus normal pulmonary fibroblasts", "human", "NSCLC unresolved", "co-culture", "fibroblasts alone", "MMP11 secretion/processing", "PMID 9417124"),
        ("MODEL_2005_COCULTURE", "15509588", "COCULTURE", "NSCLC cells plus normal pulmonary fibroblasts", "human", "NSCLC unresolved", "PKC pathway perturbation", "matched controls", "MMP11 induction", "PMID 15509588"),
        ("MODEL_BTRCP_LUNG", "15536641", "CELL_LINE", "Lung-cancer cell lines", "human", "lung cancer unresolved", "betaTrCP restoration", "control", "active MMP11; motility", "PMID 15536641"),
        ("MODEL_PATIENT_IHC_2019", "31024988", "PATIENT_TISSUE", "18 LUAD biopsies", "human", "LUAD", "none", "adjacent tissue", "IHC", "PMC6477516 Figure 2B"),
        ("MODEL_PATIENT_SERUM_2019", "31024988", "PATIENT_BIOSPECIMEN", "18 LUAD; 11 healthy", "human", "LUAD", "none", "healthy serum", "ELISA", "PMC6477516 Figure 2C"),
        ("MODEL_PATIENT_IHC_2023", "36756152", "PATIENT_TISSUE", "37 LUAD cases", "human", "LUAD", "none", "EGFR wild type", "MMP11/CD8/NK IHC", "PMC9900007"),
        ("MODEL_PATIENT_TISSUE_2025", "40386736", "PATIENT_TISSUE", "20 adenocarcinoma/squamous tissue sets", "human", "NSCLC", "none", "adjacent normal", "protein assay", "PMC12082244"),
        ("MODEL_PATIENT_SERUM_2025", "40386736", "PATIENT_BIOSPECIMEN", "200 NSCLC; 200 controls", "human", "NSCLC", "none", "healthy serum", "protein assay", "PMC12082244"),
        ("MODEL_PATIENT_MSC_2018", "29796998", "PATIENT_DERIVED_CELLS", "MSCs from one LUAD patient; A549 co-culture", "human", "LUAD", "co-culture", "healthy-tissue MSC", "CAF markers/IL6", "PMID 29796998"),
        ("MODEL_TCGA_COMPUTATIONAL", "31024988|36756152", "COMPUTATIONAL_REANALYSIS", "TCGA-LUAD", "human", "LUAD", "none", "normal/subgroups", "expression/immune estimates", "Primary publications; shared with Task #039A"),
        ("MODEL_GEO_COMPUTATIONAL", "31024988|40386736|40826767", "COMPUTATIONAL_REANALYSIS", "GEO cohorts", "human", "mixed/LUAD", "none", "source controls", "expression/network", "Primary publications and GEO"),
        ("MODEL_PANCANCER_MCAF_2025", "40552583", "COMPUTATIONAL_REANALYSIS", "Pan-cancer single-cell datasets", "human", "LUAD-resolved subset", "none", "source-defined stromal states", "MMP11-positive myofibroblast state", "PMID 40552583; Task #039A literature overlap"),
    ]
    fields = ["model_id", "publication_id", "model_class", "cell_line_animal_patient_cohort", "species", "histology", "intervention", "control", "assay", "provenance"]
    rows = [dict(zip(fields, row)) for row in models]
    for row in rows:
        row["publication_id"] = "|".join(pub_id(x) for x in row["publication_id"].split("|"))
    return rows


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def publication_registry(metadata: dict[str, dict[str, str]], broad_ids: list[str]) -> list[dict[str, str]]:
    rows = []
    for pmid in list(dict.fromkeys(broad_ids + OT_ORIENTATION_PMIDS)):
        if pmid not in SCREENING:
            raise AssertionError(f"Missing reviewed screening decision for PMID {pmid}")
        status, reason = SCREENING[pmid]
        meta = metadata.get(pmid)
        if not meta:
            raise AssertionError(f"PubMed metadata missing for PMID {pmid}")
        included = status != "EXCLUDED"
        rows.append({
            "publication_id": pub_id(pmid), "PMID": pmid, "PMCID": meta["PMCID"], "DOI": meta["DOI"],
            "title": meta["title"], "authors": meta["authors"], "year": meta["year"], "journal": meta["journal"],
            "article_type": meta["article_type"],
            "LUAD_specificity": status if included else "OUTSIDE_INCLUDED_PRIMARY_SCOPE",
            "inclusion_status": "INCLUDED" if included else "EXCLUDED",
            "exclusion_reason": "NOT_APPLICABLE" if included else reason,
            "full_text_availability": "OPEN_ACCESS_PMC" if meta["PMCID"] in PMCIDS else ("PMC_METADATA_PRESENT" if meta["PMCID"] != "NOT_AVAILABLE" else "ABSTRACT_OR_JOURNAL_METADATA"),
            "source_url_reference": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            "screening_origin": "PUBMED_BROAD_QUERY" if pmid in broad_ids else "TASK039A_OVERLAP_ORIENTATION",
            "screening_note": reason,
        })
    return rows


def provenance_links(evidence: list[dict[str, str]], pubs: dict[str, dict[str, str]], retrieval: dict[str, object]) -> list[dict[str, str]]:
    payload = next(p for p in retrieval["payloads"] if p["payload_path"].endswith("pubmed_screened_records.xml"))
    rows = []
    for ev in evidence:
        pub = pubs[ev["publication_id"]]
        rows.append({
            "external_provenance_link_id": stable_id("EXTPROV", ev["external_evidence_id"], pub["publication_id"]),
            "external_evidence_id": ev["external_evidence_id"], "EnsemblID": ENSEMBL_ID,
            "publication_id": pub["publication_id"], "PMID": pub["PMID"], "PMCID": pub["PMCID"], "DOI": pub["DOI"],
            "source_location": ev["source_location"], "dataset_or_cohort": ev["dataset_or_cohort"],
            "model_system": ev["model_system"], "raw_payload_path": payload["payload_path"],
            "raw_payload_sha256": payload["sha256"], "source_entity": "PUBMED_PRIMARY_PUBLICATION",
            "identifier_reconciliation": f"{ENSEMBL_ID}|MMP11|PubMed:{pub['PMID']}",
            "provenance_status": "COMPLETE_PRIMARY_SOURCE_TRACE",
        })
    return rows


def dependency_map(evidence: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    def dep(source: str, target: str, relation: str, level: str, rationale: str) -> None:
        rows.append({
            "dependency_id": stable_id("EXTDEP", source, target, relation), "EnsemblID": ENSEMBL_ID,
            "source_evidence_id": source, "related_entity_id": target,
            "relationship_type": relation, "dependency_level": level,
            "rationale": rationale,
            "independence_boundary": "NO_DEPENDENCY_IDENTIFIED does not prove statistical independence.",
        })

    # Every evidence unit retains publication-level dependence.
    for ev in evidence:
        dep(ev["external_evidence_id"], ev["publication_id"], "SHARED_PUBLICATION", "DEPENDENT_WITHIN_PUBLICATION",
            "Evidence units from one publication are not independent replications.")
        datasets = [x for x in ev["dataset_or_cohort"].split("|") if x and x not in {"NOT_APPLICABLE", "NONE"}]
        for dataset in datasets:
            dep(ev["external_evidence_id"], dataset, "SHARED_DATASET", "DATASET_LINEAGE_RETAINED",
                "This evidence unit is derived from the named dataset/cohort.")

    # Cross-project and cross-publication relationships that must not be inferred from counts.
    tcga_units = [x["external_evidence_id"] for x in evidence if "TCGA-LUAD" in x["dataset_or_cohort"]]
    for eid in tcga_units:
        dep(eid, "TASK039A_PRIMARY_TRANSCRIPTOMIC_EVIDENCE", "SHARED_DATASET", "DEPENDENT_DATASET_LINEAGE",
            "Published TCGA-LUAD reanalysis shares biological data lineage with the project DE analysis.")
    for dataset in ["GSE10072", "GSE18842", "GSE43458", "GSE43767", "E-MEXP-231"]:
        units = [x["external_evidence_id"] for x in evidence if dataset in x["dataset_or_cohort"]]
        for eid in units:
            dep(eid, f"TASK039A_OT_OR_EXPRESSION_ATLAS::{dataset}", "SHARED_DATASET", "DEPENDENT_SOURCE_LINEAGE",
                "The accession is also represented in frozen Task #039A Open Targets/Expression Atlas records.")
    for pmid in ["31024988", "36756152", "35422093", "39904499", "40552583"]:
        for ev in [x for x in evidence if x["publication_id"] == pub_id(pmid)]:
            dep(ev["external_evidence_id"], f"TASK039A_OPEN_TARGETS_LITERATURE::PMID_{pmid}", "SHARED_PUBLICATION", "DEPENDENT_PUBLICATION_LINEAGE",
                "The same publication identifier occurs in Task #039A Open Targets literature evidence.")
    for model in ["A549", "PC9"]:
        units = [x["external_evidence_id"] for x in evidence if model in x["model_system"]]
        for eid in units:
            dep(eid, f"MODEL_SYSTEM::{model}", "SHARED_MODEL_SYSTEM", "POSSIBLE_DEPENDENCY",
                "Reuse of a model system is recorded; it does not by itself prove experimental dependence.")
    # Specific within-paper experimental groupings.
    for eid in ["EXT_31024988_05", "EXT_31024988_06", "EXT_31024988_08"]:
        dep(eid, "EXPERIMENT_GROUP_31024988_A549_CRISPR", "SHARED_EXPERIMENT", "DEPENDENT_EXPERIMENT",
            "Readouts share the A549 depletion experiment or its derived cells.")
    for eid in ["EXT_31024988_09", "EXT_31024988_10", "EXT_31024988_12"]:
        dep(eid, "REAGENT_31024988_ANTI_MMP11", "POSSIBLE_DEPENDENCY", "SHARED_REAGENT_PUBLICATION",
            "Antibody studies share a reagent and publication; source does not establish independent reagent validation.")
    for eid in ["EXT_36756152_03", "EXT_36756152_05"]:
        dep(eid, "COHORT_2023_LUAD_37", "SAME_COHORT", "DEPENDENT_COHORT_LINEAGE",
            "MMP11 and immune-tissue observations were derived from the same 37-case clinical cohort.")
    for eid, entity, rationale in [
        ("EXT_34671675_02", "KM_PLOTTER_UNDERLYING_DATASET", "The paper does not expose sufficient accession-level cohort identity for the survival analysis."),
        ("EXT_39672019_01", "LUAD_SC_DATASET_2025_ACCESSION", "The accessible source audit did not resolve an accession for the single-cell dataset."),
        ("EXT_39672019_02", "LUAD_SURVIVAL_2025_ACCESSION", "The accessible source audit did not resolve an accession for the survival cohort."),
        ("EXT_37602450_01", "MODEL_LINC00511_CELL_IDENTITY", "Cell-line and histology identity were insufficiently explicit in accessible source text."),
        ("EXT_19949890_01", "DATASET_2010_UNRESOLVED", "The computational network's underlying accession was not resolved."),
    ]:
        dep(eid, entity, "UNKNOWN", "UNKNOWN", rationale)
    for ev in evidence:
        if ev["experimental_modality"] in {
            "RNA-seq reanalysis", "microarray reanalysis", "single-cell reanalysis",
            "integrative bioinformatics", "computational immune deconvolution",
            "computational association", "computational prediction", "Kaplan-Meier web-tool analysis",
            "integrative biocomputation",
        }:
            dep(ev["external_evidence_id"], ev["dataset_or_cohort"], "DERIVED_REANALYSIS", "DEPENDENT_TRANSFORMATION",
                "The reported observation is a derived analysis of the named source dataset/cohort.")
    return rows


def build_search_strategy(retrieval: dict[str, object]) -> dict[str, object]:
    payloads = {Path(p["payload_path"]).name: p for p in retrieval["payloads"] if p["payload_path"] != "NOT_RETAINED"}
    broad = json.loads((RAW / "pubmed_esearch_broad.json").read_text())["esearchresult"]
    functional = json.loads((RAW / "pubmed_esearch_functional.json").read_text())["esearchresult"]
    epmc = json.loads((RAW / "europe_pmc_search.json").read_text())
    trials = json.loads((RAW / "clinicaltrials_search.json").read_text())
    searches = [
        {"search_id": "SEARCH_PUBMED_BROAD", "search_source": "PubMed", "search_role": "PRIMARY_SCREENING_FRAME",
         "contributes_to_formal_publication_denominator": True, "exact_query": BROAD_QUERY,
         "search_timestamp": retrieval["retrieval_timestamp_utc"], "result_count": int(broad["count"]),
         "returned_identifiers": broad["idlist"], "pagination_completeness_status": "COMPLETE_COUNT_AND_ID_LIST_RETRIEVED",
         "retrieval_method": "NCBI E-utilities ESearch JSON", "source_version_or_date": "Live PubMed at retrieval timestamp",
         "raw_payload_path": payloads["pubmed_esearch_broad.json"]["payload_path"], "raw_payload_sha256": payloads["pubmed_esearch_broad.json"]["sha256"]},
        {"search_id": "SEARCH_PUBMED_FUNCTIONAL", "search_source": "PubMed", "search_role": "SUPPLEMENTARY_DISCOVERY",
         "contributes_to_formal_publication_denominator": False, "exact_query": FUNCTION_QUERY,
         "search_timestamp": retrieval["retrieval_timestamp_utc"], "result_count": int(functional["count"]),
         "returned_identifiers": functional["idlist"], "pagination_completeness_status": "COMPLETE_COUNT_AND_ID_LIST_RETRIEVED",
         "retrieval_method": "NCBI E-utilities ESearch JSON", "source_version_or_date": "Live PubMed at retrieval timestamp",
         "raw_payload_path": payloads["pubmed_esearch_functional.json"]["payload_path"], "raw_payload_sha256": payloads["pubmed_esearch_functional.json"]["sha256"]},
        {"search_id": "SEARCH_EUROPE_PMC_BROAD", "search_source": "Europe PMC", "search_role": "SUPPLEMENTARY_DISCOVERY",
         "contributes_to_formal_publication_denominator": False, "exact_query": EUROPE_PMC_QUERY,
         "search_timestamp": retrieval["retrieval_timestamp_utc"], "result_count": int(epmc.get("hitCount", 0)),
         "returned_identifiers": [x.get("pmid") or x.get("id") for x in epmc.get("resultList", {}).get("result", [])],
         "pagination_completeness_status": "NOT_EXHAUSTIVELY_SCREENED_HIGH_RECALL_SUPPLEMENTARY_QUERY",
         "screening_scope_note": "The 1,383-hit result set was not exhaustively paginated or screened and is outside the formal publication denominator.",
         "retrieval_method": "Europe PMC REST search core JSON", "source_version_or_date": "Live Europe PMC at retrieval timestamp",
         "raw_payload_path": payloads["europe_pmc_search.json"]["payload_path"], "raw_payload_sha256": payloads["europe_pmc_search.json"]["sha256"]},
        {"search_id": "SEARCH_CLINICALTRIALS_MMP11", "search_source": "ClinicalTrials.gov", "search_role": "CLINICAL_DEVELOPMENT_CHECK",
         "contributes_to_formal_publication_denominator": False, "exact_query": CLINICAL_TRIALS_QUERY,
         "search_timestamp": retrieval["retrieval_timestamp_utc"], "result_count": int(trials.get("totalCount", len(trials.get("studies", [])))),
         "returned_identifiers": [x.get("protocolSection", {}).get("identificationModule", {}).get("nctId") for x in trials.get("studies", [])],
         "pagination_completeness_status": "COMPLETE_IF_NO_NEXT_PAGE_TOKEN" if not trials.get("nextPageToken") else "PARTIAL_PAGE_TOKEN_PRESENT",
         "retrieval_method": "ClinicalTrials.gov API v2", "source_version_or_date": "Live ClinicalTrials.gov at retrieval timestamp",
         "raw_payload_path": payloads["clinicaltrials_search.json"]["payload_path"], "raw_payload_sha256": payloads["clinicaltrials_search.json"]["sha256"]},
        {"search_id": "TASK039A_OVERLAP_ORIENTATION_IDENTIFIERS", "search_source": "Frozen Task #039A Open Targets and Expression Atlas lineages",
         "search_role": "OVERLAP_ORIENTATION", "contributes_to_formal_publication_denominator": True,
         "exact_query": "Resolve and screen publication identifiers already present in frozen Task #039A evidence lineages",
         "search_timestamp": retrieval["retrieval_timestamp_utc"], "result_count": len(OT_ORIENTATION_PMIDS),
         "returned_identifiers": OT_ORIENTATION_PMIDS, "pagination_completeness_status": "COMPLETE_FROZEN_IDENTIFIER_SET",
         "retrieval_method": "Frozen Task #039A identifier overlap audit followed by PubMed metadata reconciliation",
         "source_version_or_date": "Task #039A frozen at Git commit dc5dc17",
         "raw_payload_path": payloads["pubmed_screened_records.xml"]["payload_path"],
         "raw_payload_sha256": payloads["pubmed_screened_records.xml"]["sha256"]},
    ]
    formal_denominator = int(broad["count"]) + len(OT_ORIENTATION_PMIDS)
    return {
        "registry_version": REGISTRY_VERSION,
        "documentation_patch_version": DOCUMENTATION_PATCH_VERSION,
        "target_identity": {"EnsemblID": ENSEMBL_ID, "display_symbol": SYMBOL, "accepted_search_synonyms": ["MMP11", "matrix metalloproteinase 11", "stromelysin-3"]},
        "retrieval_mode": "MUTABLE_EXTERNAL_SOURCE_RETRIEVAL_FROZEN_AS_RAW_PAYLOADS",
        "future_network_byte_identity_claimed": False,
        "offline_transformation_deterministic": True,
        "allowed_search_roles": sorted(SEARCH_ROLES),
        "searches": searches,
        "formal_publication_screening_frame": {
            "definition": "Complete PubMed broad-query records plus unique frozen Task #039A overlap-orientation records",
            "contributing_search_roles": ["PRIMARY_SCREENING_FRAME", "OVERLAP_ORIENTATION"],
            "pubmed_primary_screen_count": int(broad["count"]),
            "overlap_orientation_record_count": len(OT_ORIENTATION_PMIDS),
            "formal_publication_screening_denominator": formal_denominator,
            "excluded_from_denominator": ["SUPPLEMENTARY_DISCOVERY", "CLINICAL_DEVELOPMENT_CHECK"],
            "boundary_note": "Europe PMC supplementary hits and ClinicalTrials.gov lexical hits do not contribute to publications screened.",
        },
        "orientation_identifier_source": {"source": "Frozen Task #039A Open Targets and Expression Atlas lineages", "PMIDs": OT_ORIENTATION_PMIDS, "search_role": "OVERLAP_ORIENTATION"},
        "disclaimer": DISCLAIMER,
    }


def validate_and_write() -> dict[str, object]:
    OUT.mkdir(parents=True, exist_ok=True)
    if not (RAW / "retrieval_manifest.json").exists():
        raise SystemExit("Raw retrieval payloads are absent. Run with --retrieve once, then rerun offline.")
    before_hashes = {name: sha256(INTERNAL / name) for name in FROZEN_INPUTS}
    biological_hashes_before = {
        name: sha256(OUT / name) for name in EXPECTED_TASK039B_BIOLOGICAL_HASHES
        if (OUT / name).is_file()
    }
    biological_counts_before = {
        "evidence_units": sum(1 for _ in csv.DictReader((OUT / "external_evidence_registry.csv").open())),
        "dependencies": sum(1 for _ in csv.DictReader((OUT / "external_dependency_map.csv").open())),
    } if (OUT / "external_evidence_registry.csv").is_file() and (OUT / "external_dependency_map.csv").is_file() else {
        "evidence_units": "NOT_PRESENT", "dependencies": "NOT_PRESENT"
    }
    identity = json.loads((INTERNAL / "mmp11_identity.json").read_text())
    identity_text = json.dumps(identity)
    checks: list[tuple[str, bool, str]] = []
    checks.append(("frozen_target_identity", ENSEMBL_ID in identity_text and SYMBOL in identity_text, "Exact EnsemblID and display symbol reconcile to Task #039A."))
    checks.append(("frozen_task039a_hashes_pinned", before_hashes == EXPECTED_TASK039A_HASHES, "Task #039A inputs match their reviewed SHA256 values."))

    retrieval = json.loads((RAW / "retrieval_manifest.json").read_text())
    search_strategy = build_search_strategy(retrieval)
    (OUT / "search_strategy.json").write_text(json.dumps(search_strategy, indent=2, sort_keys=True) + "\n")

    metadata = parse_pubmed()
    broad_ids = json.loads((RAW / "pubmed_esearch_broad.json").read_text())["esearchresult"]["idlist"]
    pubs = publication_registry(metadata, broad_ids)
    pub_by_id = {x["publication_id"]: x for x in pubs}
    evidence = evidence_catalogue()
    datasets = dataset_catalogue()
    models = model_catalogue()
    provenance = provenance_links(evidence, pub_by_id, retrieval)
    dependencies = dependency_map(evidence)
    exclusions = [{
        "source_identifier": x["PMID"], "title": x["title"], "exclusion_reason": x["exclusion_reason"],
        "disease_specificity_issue": x["screening_note"], "evidence_type_issue": "NO_INCLUDED_PRIMARY_OR_BOUNDED_LUAD_EVIDENCE_UNIT",
        "duplicate_status": "NOT_DUPLICATE", "provenance_issue": "NONE_IDENTIFIED",
    } for x in pubs if x["inclusion_status"] == "EXCLUDED"]
    trial_payload = json.loads((RAW / "clinicaltrials_search.json").read_text())
    trial_exclusion_reasons = {
        "NCT04001816": "Orthodontic bracket trial; lexical query false positive and no MMP11 intervention or biomarker.",
        "NCT07329179": "Dental sinus-lifting trial; lexical query false positive and no MMP11 intervention or biomarker.",
        "NCT04043013": "Orthodontic bracket-prescription trial; lexical query false positive and no MMP11 intervention or biomarker.",
        "NCT05414370": "Hyperoxia/pulmonary-inflammation study; no MMP11 intervention or biomarker in the registered record.",
        "NCT01472445": "Breast-cancer vitamin-D study; no MMP11 intervention or biomarker in the registered record.",
    }
    for study in trial_payload.get("studies", []):
        ident = study.get("protocolSection", {}).get("identificationModule", {})
        nct = ident.get("nctId", "UNKNOWN_NCT")
        exclusions.append({
            "source_identifier": nct,
            "title": ident.get("briefTitle", "NOT_REPORTED"),
            "exclusion_reason": trial_exclusion_reasons.get(nct, "No MMP11-specific intervention, biomarker, or LUAD evidence located in the registered record."),
            "disease_specificity_issue": "NO_MMP11_LUAD_CLINICAL_DEVELOPMENT_CONTEXT",
            "evidence_type_issue": "CLINICALTRIALS_QUERY_FALSE_POSITIVE",
            "duplicate_status": "NOT_DUPLICATE",
            "provenance_issue": "NONE_IDENTIFIED",
        })

    write_csv(OUT / "publication_registry.csv", pubs)
    write_csv(OUT / "external_evidence_registry.csv", evidence)
    write_csv(OUT / "experimental_model_registry.csv", models)
    write_csv(OUT / "dataset_registry.csv", datasets)
    write_csv(OUT / "external_provenance_links.csv", provenance)
    write_csv(OUT / "external_dependency_map.csv", dependencies)
    write_csv(OUT / "evidence_exclusion_log.csv", exclusions)

    search_by_id = {x["search_id"]: x for x in search_strategy["searches"]}
    formal_frame = search_strategy["formal_publication_screening_frame"]
    contributing_searches = [
        x for x in search_strategy["searches"]
        if x["contributes_to_formal_publication_denominator"]
    ]

    allowed_status = {"OBSERVED_SUPPORTIVE", "OBSERVED_CONTRADICTORY", "OBSERVED_NULL", "CONTEXT_DEPENDENT", "INSUFFICIENTLY_SPECIFIC", "UNRESOLVED"}
    allowed_rel = {"SHARED_DATASET", "SHARED_PUBLICATION", "SHARED_EXPERIMENT", "SHARED_MODEL_SYSTEM", "DERIVED_REANALYSIS", "SAME_COHORT", "PARTIAL_COHORT_OVERLAP", "POSSIBLE_DEPENDENCY", "NO_DEPENDENCY_IDENTIFIED", "UNKNOWN"}
    checks.extend([
        ("pubmed_special_study_identity", metadata["31024988"]["PMCID"] == "PMC6477516" and metadata["31024988"]["DOI"] == "10.1016/j.omto.2019.03.012" and metadata["31024988"]["title"] == "Matrix Metalloproteinase 11 Is a Potential Therapeutic Target in Lung Adenocarcinoma.", "PMID 31024988 reconciles to exact title, PMCID, and DOI."),
        ("raw_payload_integrity", all(p.get("payload_path") == "NOT_RETAINED" or (ROOT / str(p["payload_path"])).is_file() and sha256(ROOT / str(p["payload_path"])) == p["sha256"] for p in retrieval["payloads"]), "Every retained raw payload matches its frozen SHA256."),
        ("unique_publication_ids", len(pubs) == len({x["publication_id"] for x in pubs}), "No duplicate publication identifiers."),
        ("unique_evidence_units", len(evidence) == len({x["external_evidence_id"] for x in evidence}), "No duplicate bounded evidence-unit identifiers."),
        ("evidence_identity", all(x["EnsemblID"] == ENSEMBL_ID for x in evidence), "All project-side evidence joins use immutable EnsemblID."),
        ("controlled_evidence_status", all(x["evidence_status"] in allowed_status for x in evidence), "All evidence statuses use the controlled vocabulary."),
        ("traceable_evidence", len(provenance) == len(evidence) and all(x["publication_id"] in pub_by_id for x in evidence), "Every evidence unit has a publication and provenance link."),
        ("included_publications_have_evidence", all(any(e["publication_id"] == p["publication_id"] for e in evidence) for p in pubs if p["inclusion_status"] == "INCLUDED"), "Every included publication supplies at least one bounded evidence unit."),
        ("model_publication_links", all(all(x in pub_by_id for x in m["publication_id"].split("|")) for m in models), "Experimental-model publication foreign keys reconcile."),
        ("dataset_model_references_resolve", all(all(ref in {d["dataset_id"] for d in datasets} | {m["model_id"] for m in models} for ref in e["dataset_or_cohort"].split("|")) for e in evidence), "Every evidence dataset/cohort reference resolves to the dataset or model registry."),
        ("disease_context_complete", all(x["disease_context"] and x["histology_specificity"] for x in evidence), "Every evidence unit has disease/histology context."),
        ("provenance_status_complete", all(x["provenance_completeness_status"] for x in evidence), "Every evidence unit has provenance status."),
        ("dataset_accessions_unique", len(datasets) == len({x["dataset_id"] for x in datasets}), "Dataset registry identifiers are unique."),
        ("tcga_overlap_explicit", any(x["uses_tcga"] == "TRUE" and "SHARED_DATASET" in x["relation_to_task039a"] for x in datasets), "TCGA-LUAD reuse is explicitly linked to Task #039A."),
        ("publication_dependency_complete", all(any(d["source_evidence_id"] == x["external_evidence_id"] and d["relationship_type"] == "SHARED_PUBLICATION" for d in dependencies) for x in evidence), "Every evidence unit has publication-level dependency."),
        ("dependency_vocabulary", all(x["relationship_type"] in allowed_rel for x in dependencies), "Dependency relationships use allowed concepts."),
        ("exclusion_reasons_complete", all(x["exclusion_reason"] for x in exclusions), "All excluded screening records have reasons."),
        ("null_context_retained", any(x["evidence_status"] == "OBSERVED_NULL" for x in evidence) and any(x["evidence_status"] == "CONTEXT_DEPENDENT" for x in evidence), "Null and context-dependent evidence are retained."),
        ("no_false_clinical_development", not any(x["evidence_domain"] == "H_CLINICAL_DEVELOPMENT" for x in evidence), "No clinical-development unit was created without a relevant trial."),
        ("clinicaltrials_false_positives_retained", len(trial_payload.get("studies", [])) == 5 and all(nct in {x["source_identifier"] for x in exclusions} for nct in trial_exclusion_reasons), "All five ClinicalTrials.gov lexical false positives are retained in the exclusion log."),
        ("search_roles_explicit", all(x.get("search_role") in SEARCH_ROLES for x in search_strategy["searches"]), "Every registered search has an allowed explicit search role."),
        ("formal_denominator_roles_only", {x["search_role"] for x in contributing_searches} == {"PRIMARY_SCREENING_FRAME", "OVERLAP_ORIENTATION"}, "Only primary-screening and overlap-orientation records contribute to the publication denominator."),
        ("formal_publication_denominator", formal_frame["pubmed_primary_screen_count"] == 30 and formal_frame["overlap_orientation_record_count"] == 7 and formal_frame["formal_publication_screening_denominator"] == 37 and len(pubs) == 37, "Formal screening frame is 30 complete PubMed broad-query records plus 7 unique Task #039A orientation records."),
        ("europe_pmc_supplementary_not_exhaustive", search_by_id["SEARCH_EUROPE_PMC_BROAD"]["search_role"] == "SUPPLEMENTARY_DISCOVERY" and search_by_id["SEARCH_EUROPE_PMC_BROAD"]["result_count"] == 1383 and search_by_id["SEARCH_EUROPE_PMC_BROAD"]["pagination_completeness_status"] == "NOT_EXHAUSTIVELY_SCREENED_HIGH_RECALL_SUPPLEMENTARY_QUERY" and not search_by_id["SEARCH_EUROPE_PMC_BROAD"]["contributes_to_formal_publication_denominator"], "Europe PMC's 1,383-hit high-recall query is explicitly supplementary and not exhaustively screened."),
        ("clinicaltrials_outside_publication_denominator", search_by_id["SEARCH_CLINICALTRIALS_MMP11"]["search_role"] == "CLINICAL_DEVELOPMENT_CHECK" and search_by_id["SEARCH_CLINICALTRIALS_MMP11"]["result_count"] == 5 and not search_by_id["SEARCH_CLINICALTRIALS_MMP11"]["contributes_to_formal_publication_denominator"], "ClinicalTrials.gov lexical hits remain a separate clinical-development check."),
        ("task039b_registry_counts_frozen", len(pubs) == 37 and sum(x["inclusion_status"] == "INCLUDED" for x in pubs) == 30 and sum(x["inclusion_status"] == "EXCLUDED" for x in pubs) == 7 and len(evidence) == 56 and len(provenance) == 56 and len(dependencies) == 197, "Publication, evidence, provenance, and dependency counts remain frozen."),
    ])
    forbidden = {"score", "rank", "ranking", "recommendation", "therapeutic_direction", "priority"}
    fields = set().union(*(set(x) for x in evidence + pubs + datasets + models + provenance + dependencies))
    checks.append(("forbidden_fields_absent", not forbidden.intersection(fields), "No score/rank/recommendation/therapeutic-direction fields."))

    after_hashes = {name: sha256(INTERNAL / name) for name in FROZEN_INPUTS}
    checks.append(("frozen_inputs_unchanged", before_hashes == after_hashes, "Task #039A frozen inputs are byte-unchanged."))
    biological_hashes_after = {name: sha256(OUT / name) for name in EXPECTED_TASK039B_BIOLOGICAL_HASHES}
    checks.append(("task039b_biological_hashes_pinned", biological_hashes_after == EXPECTED_TASK039B_BIOLOGICAL_HASHES, "All Task #039B biological registries retain their pre-patch SHA256 values."))
    checks.append(("task039b_biological_content_unchanged", not biological_hashes_before or biological_hashes_before == biological_hashes_after, "Task #039B biological evidence content is byte-unchanged from the pre-patch state."))

    status_counts = Counter(x["evidence_status"] for x in evidence)
    domain_counts = Counter(x["evidence_domain"] for x in evidence)
    included_count = sum(x["inclusion_status"] == "INCLUDED" for x in pubs)
    tcga_units = sum("TCGA-LUAD" in x["dataset_or_cohort"] for x in evidence)
    distinct_dataset_units = sum(
        any(g in x["dataset_or_cohort"] for g in ["GSE7670", "GSE68465", "GSE32863", "GSE19804"])
        for x in evidence
    )
    functional_units = sum(x["evidence_domain"] == "D_FUNCTIONAL_PERTURBATION" for x in evidence)
    vivo_units = sum(x["evidence_domain"] == "F_IN_VIVO" or "XENOGRAFT" in x["evidence_type"] for x in evidence)
    intervention_units = sum(x["evidence_domain"] == "G_INTERVENTION" for x in evidence)
    unresolved_deps = sum(x["dependency_level"] == "UNKNOWN" or x["relationship_type"] == "UNKNOWN" for x in dependencies)

    claim_boundary = f"""# MMP11 external evidence claim boundary v0.1

{DISCLAIMER}

## Interpretation contract

| Evidence domain | Supported interpretation | Not supported |
|---|---|---|
| Transcriptomic / expression | A source-defined tumour-associated expression observation exists in the stated cohort. | Expression association is not disease causality, cell-type attribution, or therapeutic actionability. |
| Protein / tissue | MMP11 protein or staining was observed in the reported biospecimen and assay context. | A tissue or serum difference is not diagnostic validation, causal proof, or treatment response. |
| Clinical association / prognosis | A reported association, null result, or subgroup result exists under the source analysis. | Prognostic association is not therapeutic causality; a null in one context is not universal absence. |
| Functional perturbation | Changing MMP11 or a reported regulatory axis altered a bounded cell-model readout. | Cell perturbation is not patient efficacy, and downstream readouts do not prove direct mediation. |
| Mechanistic | A source reported a pathway, regulatory, stromal, or computational relationship in a specified model. | Association or pathway readout is not a complete causal mechanism. |
| In vivo | A bounded xenograft experiment reported a tumour-growth effect. | Xenograft effect is not clinical efficacy or human safety. |
| Intervention | A preclinical anti-MMP11 antibody or compound-context observation exists. | Preclinical antibody effect is not a validated therapeutic intervention; multi-target exposure is not MMP11-specific efficacy. |
| Clinical development | No relevant registered MMP11 clinical study was identified by the frozen query. | Search absence is not proof that no study exists and is not evidence against the target. |

## Dependency boundaries

- The external acquisition is bounded by the frozen search strategy and is not claimed to be an exhaustive systematic review of all MMP11 literature.
- Multiple records from one publication are not independent replications.
- Published TCGA-LUAD analyses share dataset lineage with Task #039A and are not independent transcriptomic replication.
- GEO accessions are assessed individually; reuse across papers is explicit.
- `NO_DEPENDENCY_IDENTIFIED` means only that no dependency was identified from available provenance. It does not prove statistical independence.
- Absence of contradictory evidence is not proof of consistency.
"""
    (OUT / "external_claim_boundary.md").write_text(claim_boundary)

    summary = f"""# MMP11 external evidence summary v0.1

{DISCLAIMER}

## Scope and identity

This acquisition reconciled **{ENSEMBL_ID}** to the frozen Task #039A identity and used **MMP11** only as a display/search synonym. Project-side joins remain EnsemblID-based. It describes external observations; it does not provide an overall conclusion.

## Acquisition inventory

- Publications screened: **{len(pubs)}** ({len(broad_ids)} from the complete PubMed broad query plus {len(OT_ORIENTATION_PMIDS)} Task #039A overlap-orientation records)
- Publications included for at least one bounded observation: **{included_count}**
- Publications excluded with retained reasons: **{len(pubs) - included_count}**
- Bounded evidence units: **{len(evidence)}**
- Datasets/cohorts: **{len(datasets)}**
- Experimental models: **{len(models)}**
- External provenance links: **{len(provenance)}**
- Dependency relationships: **{len(dependencies)}**

## Search coverage boundary

The PubMed broad query was the primary formal publication screening frame. Its complete set of **{len(broad_ids)}** records was combined with **{len(OT_ORIENTATION_PMIDS)}** unique Task #039A overlap-orientation records, producing the formal denominator of **{len(pubs)} publications screened**.

Europe PMC was used only as a supplementary high-recall discovery and cross-check source. Its **{search_by_id['SEARCH_EUROPE_PMC_BROAD']['result_count']:,}** hits were not exhaustively paginated or screened and are not part of the publication denominator. ClinicalTrials.gov was a separate clinical-development check and its lexical hits are also outside that denominator.

Task #039B is therefore a bounded provenance-aware evidence acquisition, not a formal systematic review or a claim of exhaustive literature coverage.

## Evidence units by domain

""" + "\n".join(f"- {k}: **{v}**" for k, v in sorted(domain_counts.items())) + f"""

## Evidence states retained

""" + "\n".join(f"- {k}: **{v}**" for k, v in sorted(status_counts.items())) + f"""

No unit was labelled `OBSERVED_CONTRADICTORY` in this bounded search. That absence must not be interpreted as proof of consistency. Null findings include germline susceptibility, EGFR-subtype, cytotoxic-T-cell, immune-checkpoint-benefit, POSTN-paper prognosis, stage-I survival, and recurrence analyses. Context-dependent and insufficiently specific findings remain visible rather than being promoted to LUAD-specific support.

## Special audit: PMID 31024988

The expected identifier was independently reconciled as PMID **31024988**, PMCID **PMC6477516**, DOI **10.1016/j.omto.2019.03.012**. Separate evidence units represent its GEO analysis, TCGA analysis, patient IHC, serum ELISA, A549/PC9 perturbation and rescue, migration/invasion, xenografts, and antibody experiments. They retain `SHARED_PUBLICATION`, dataset, experiment, model-system, and reagent relationships and therefore are not treated as independent votes.

## Cross-lineage and modality observations

- TCGA-overlapping evidence units: **{tcga_units}**. Each shares biological dataset lineage with Task #039A.
- Potentially distinct GEO-dataset evidence units under the conservative accession audit: **{distinct_dataset_units}**. “Potentially distinct” is not proof of statistical independence.
- Functional perturbation units: **{functional_units}**.
- In vivo units: **{vivo_units}**.
- Preclinical intervention units: **{intervention_units}**.
- ClinicalTrials.gov records returned for the frozen MMP11 query: **{search_strategy['searches'][3]['result_count']}**. All five were screened as lexical false positives and retained in the exclusion log; no MMP11 clinical-development evidence unit was created.

## Reproducibility boundary

The retained raw payloads are immutable within this task and are listed with retrieval timestamps and SHA256 hashes. Transformation from those frozen payloads is deterministic. PubMed, Europe PMC, GEO, PMC, and ClinicalTrials.gov are mutable external services, so future network retrieval is not claimed to be byte-identical.

## Unresolved limitations

- Some older NSCLC studies do not separate adenocarcinoma results.
- Some computational studies do not expose accession-level cohort provenance in accessible text.
- A source reporting a model, pathway, or antibody effect does not independently validate specificity, generalizability, efficacy, or safety.
- Publication and dataset overlap can be documented, but absence of a discovered overlap cannot prove independence.
"""
    (OUT / "mmp11_external_evidence_summary.md").write_text(summary)

    all_pass = all(ok for _, ok, _ in checks)
    report = f"""# Task #039B.1 validation report

{DISCLAIMER}

Overall validation: **{'PASS' if all_pass else 'FAIL'}**

| Check | Result | Detail |
|---|---|---|
""" + "\n".join(f"| `{name}` | **{'PASS' if ok else 'FAIL'}** | {detail} |" for name, ok, detail in checks) + f"""

## Reproducibility statement

- Deterministic transformation of the frozen retrieved payloads: **validated by repeat execution in completion checks**.
- Mutable external retrieval: **not claimed to be byte-identical in the future**.
- Retrieval timestamp: `{retrieval['retrieval_timestamp_utc']}`.
- Generator: `{GENERATOR_VERSION}`.
- Documentation patch: `{DOCUMENTATION_PATCH_VERSION}`.
"""
    (OUT / "validation_report.md").write_text(report)

    git_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    session = "\n".join([
        f"registry_version={REGISTRY_VERSION}", f"generator_version={GENERATOR_VERSION}",
        f"documentation_patch_version={DOCUMENTATION_PATCH_VERSION}",
        f"python_version={platform.python_version()}", f"platform={platform.platform()}",
        f"retrieval_timestamp_utc={retrieval['retrieval_timestamp_utc']}",
        "network_usage_original_acquisition=Official PubMed, PubMed Central, Europe PMC, NCBI GEO, and ClinicalTrials.gov retrieval only",
        "network_usage_task039b_1_regeneration=NONE_EXISTING_FROZEN_RAW_PAYLOADS_ONLY",
        "network_retrieval_mutable=TRUE", "offline_transformation_deterministic=TRUE",
        "future_network_byte_identity_claimed=FALSE", f"git_head={git_head}",
        "git_worktree_state=reported_at_task_completion_not_embedded_to_preserve_deterministic_transformation",
        "frozen_task039a_hashes=" + json.dumps(before_hashes, sort_keys=True),
        f"presentation_disclaimer={DISCLAIMER}", "",
    ])
    (OUT / "session_info.txt").write_text(session)

    metrics = {
        "resolved_target_identity": ENSEMBL_ID, "publications_screened": len(pubs),
        "publications_included": included_count, "publications_excluded": len(pubs) - included_count,
        "bounded_external_evidence_units": len(evidence), "evidence_units_by_domain": dict(sorted(domain_counts.items())),
        "datasets_identified": len(datasets), "experimental_models_identified": len(models),
        "tcga_overlapping_evidence_units": tcga_units, "potentially_distinct_dataset_evidence_units": distinct_dataset_units,
        "functional_perturbation_evidence_units": functional_units, "in_vivo_evidence_units": vivo_units,
        "intervention_evidence_units": intervention_units,
        "contradictory_null_context_dependent_units": sum(status_counts[x] for x in ["OBSERVED_CONTRADICTORY", "OBSERVED_NULL", "CONTEXT_DEPENDENT"]),
        "unresolved_dependency_units": unresolved_deps, "external_provenance_link_count": len(provenance),
        "dependency_relationship_count": len(dependencies), "validation": "PASS" if all_pass else "FAIL",
        "formal_publication_screening_denominator": formal_frame["formal_publication_screening_denominator"],
        "pubmed_primary_screen_count": formal_frame["pubmed_primary_screen_count"],
        "orientation_record_count": formal_frame["overlap_orientation_record_count"],
        "europe_pmc_supplementary_hit_count": search_by_id["SEARCH_EUROPE_PMC_BROAD"]["result_count"],
        "europe_pmc_screening_role": search_by_id["SEARCH_EUROPE_PMC_BROAD"]["search_role"],
        "clinicaltrials_lexical_hit_count": search_by_id["SEARCH_CLINICALTRIALS_MMP11"]["result_count"],
        "evidence_unit_count_before": biological_counts_before["evidence_units"],
        "evidence_unit_count_after": len(evidence),
        "dependency_count_before": biological_counts_before["dependencies"],
        "dependency_count_after": len(dependencies),
        "files_modified": [
            "analysis/39B_acquire_mmp11_external_evidence.py",
            "outputs/mmp11_external_evidence_v0.1/search_strategy.json",
            "outputs/mmp11_external_evidence_v0.1/external_claim_boundary.md",
            "outputs/mmp11_external_evidence_v0.1/mmp11_external_evidence_summary.md",
            "outputs/mmp11_external_evidence_v0.1/validation_report.md",
            "outputs/mmp11_external_evidence_v0.1/session_info.txt",
        ],
    }
    if not all_pass:
        raise AssertionError("Validation failed: " + ", ".join(name for name, ok, _ in checks if not ok))
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--retrieve", action="store_true", help="Retrieve and freeze official external payloads if absent")
    args = parser.parse_args()
    if args.retrieve:
        retrieve_payloads()
    metrics = validate_and_write()
    print(json.dumps(metrics, indent=2, sort_keys=True))
    print("files_modified:")
    for path in metrics["files_modified"]:
        print(f"- {path}")
    print("frozen_biological_registries_modified: none")


if __name__ == "__main__":
    main()
