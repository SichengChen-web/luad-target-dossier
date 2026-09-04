#!/usr/bin/env python3
"""Run the P2-E1B search-strategy pilot and build discovery-only artifacts.

Mutable network responses are captured once. All registries and audits are
deterministic transformations of the frozen raw payloads. This task does not
perform formal screening, capability coding, ranking, or gap/novelty analysis.
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import json
import platform
import re
import subprocess
import sys
import time
import urllib.parse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "phase_two" / "p2_e1_pilot_v0.1"
SEARCH = OUT / "search"
RAW = SEARCH / "raw_retrieval"
DISCOVERY = OUT / "discovery"
AUDIT = OUT / "audit"
MANIFEST = SEARCH / "retrieval_manifest.json"
GENERATOR_VERSION = "P2_E1B_SEARCH_STRATEGY_PILOT_GENERATOR_V0.1"
PILOT_DISCLAIMER = (
    "Pilot results are not the formal P2-E1 screening denominator and do not "
    "establish a related-work gap."
)
CAPTURE_LIMIT = 30
DATE_FROM = "2010-01-01"
DATE_TO = "2026-09-03"
ASSISTANCE_MODE = "AI_ASSISTED_DISCOVERY"

FROZEN_INPUT_HASHES = {
    "docs/phase_two/p2_e1_related_work_protocol_v0.1.md": "208c19c6a9835af2f6c0e0543ad44be284fc8a4aeee8e9533fc59116e5180f00",
    "docs/phase_two/p2_e1_comparison_framework_v0.1.md": "4452c2839951db7bd7070b2610172ed0639a8c77b53f3ab8c02e9bf35b8d4e79",
    "docs/phase_two/p2_e1_templates/capability_evidence_ledger_template.csv": "a364dbe69729e8fbbbd999b0f13ef6dc0e8cb302dffbd621dd20b127f5f2f8d6",
    "docs/phase_two/p2_e1_templates/capability_matrix_template.csv": "043947160440bfbf237441a59df738339388530f3116a948f732aeb08d3af9a4",
    "docs/phase_two/p2_e1_templates/claim_ledger_template.csv": "f1932399c0eae8f9d0fba08a628d0657a8a6630eb90c85cc9f08374247269b52",
    "docs/phase_two/p2_e1_templates/screening_ledger_template.csv": "ec4a2bcd076d0fde847822044ca73325737c7faec25eb46cc6ef2d952e3ff504",
    "docs/phase_two/p2_e1_templates/search_log_template.csv": "fc13d9f642c6b9aa690da3186977848c07033c1d26d892b69e22f6fd78ffdf2d",
    "docs/phase_two/p2_e1_templates/source_registry_template.csv": "4612aa4b1066b2115bfafcb952435472cac26de86daec77c699d5ff04e546c5f",
    "docs/phase_two/p2_e1_templates/system_registry_template.csv": "6bd90642c033a7c9d33d6d0492947dd75b3023a336792ab2b4e2e6a734358988",
}

CATEGORIES = {
    "CAT_01": "target_evidence_integration_target_prioritization",
    "CAT_02": "open_targets",
    "CAT_03": "biomedical_drug_target_knowledge_graphs",
    "CAT_04": "provenance_systems_standards",
    "CAT_05": "evidence_synthesis_assessment_systems",
    "CAT_06": "missingness_uncertainty_conflict_dependence_methods",
    "CAT_07": "ai_assisted_target_discovery",
}

QUERY_FAMILIES = [
    {
        "id": "QF01_TARGET_INTEGRATION",
        "categories": ["CAT_01"],
        "focus": "CATEGORY_DISCOVERY",
        "pubmed": '(("drug target"[Title/Abstract] OR "therapeutic target"[Title/Abstract] OR "target prioritization"[Title/Abstract] OR "target prioritisation"[Title/Abstract]) AND ("evidence integration"[Title/Abstract] OR "heterogeneous evidence"[Title/Abstract] OR "data integration"[Title/Abstract] OR "multi-omics"[Title/Abstract] OR "evidence framework"[Title/Abstract]))',
        "openalex": '"drug target" ("evidence integration" OR "target prioritization" OR "heterogeneous evidence" OR "data integration" OR multi-omics)',
    },
    {
        "id": "QF02_OPEN_TARGETS",
        "categories": ["CAT_02", "CAT_01"],
        "focus": "CATEGORY_DISCOVERY_NAMED_SYSTEM",
        "pubmed": '("Open Targets Platform"[Title/Abstract] OR "Open Targets Genetics"[Title/Abstract] OR "Open Targets"[Corporate Author])',
        "openalex": '"Open Targets Platform" OR "Open Targets Genetics"',
    },
    {
        "id": "QF03_KNOWLEDGE_GRAPHS",
        "categories": ["CAT_03", "CAT_01"],
        "focus": "CATEGORY_DISCOVERY",
        "pubmed": '(("knowledge graph"[Title/Abstract] OR "evidence graph"[Title/Abstract] OR "semantic graph"[Title/Abstract]) AND (biomedical[Title/Abstract] OR "drug target"[Title/Abstract] OR "target discovery"[Title/Abstract] OR "target prioritization"[Title/Abstract]))',
        "openalex": '("knowledge graph" OR "evidence graph") (biomedical OR "drug target" OR "target discovery" OR "target prioritization")',
    },
    {
        "id": "QF04_PROVENANCE",
        "categories": ["CAT_04"],
        "focus": "CATEGORY_DISCOVERY",
        "pubmed": '((provenance[Title/Abstract] OR lineage[Title/Abstract] OR attribution[Title/Abstract] OR traceability[Title/Abstract] OR "source tracking"[Title/Abstract] OR derivation[Title/Abstract]) AND (biomedical[Title/Abstract] OR bioinformatics[Title/Abstract]) AND (integration[Title/Abstract] OR evidence[Title/Abstract] OR database[Title/Abstract]))',
        "openalex": '(provenance OR lineage OR attribution OR traceability OR "source tracking" OR derivation) (biomedical OR bioinformatics) (integration OR evidence OR database)',
    },
    {
        "id": "QF05_EVIDENCE_SYNTHESIS",
        "categories": ["CAT_05"],
        "focus": "CATEGORY_DISCOVERY",
        "pubmed": '(("evidence synthesis"[Title/Abstract] OR "evidence assessment"[Title/Abstract] OR "systematic review"[Title/Abstract] OR "living review"[Title/Abstract]) AND (software[Title/Abstract] OR platform[Title/Abstract] OR tool[Title/Abstract] OR system[Title/Abstract]) AND (provenance[Title/Abstract] OR "missing data"[Title/Abstract] OR uncertainty[Title/Abstract] OR conflict[Title/Abstract] OR dependence[Title/Abstract] OR "evidence grading"[Title/Abstract]))',
        "openalex": '("evidence synthesis" OR "evidence assessment" OR "systematic review" OR "living review") (software OR platform OR tool OR system) (provenance OR "missing data" OR uncertainty OR conflict OR dependence OR "evidence grading")',
    },
    {
        "id": "QF06_MISSING_UNCERTAIN_DEPENDENT",
        "categories": ["CAT_06", "CAT_05"],
        "focus": "CATEGORY_DISCOVERY",
        "pubmed": '(("missing data"[Title/Abstract] OR "data absence"[Title/Abstract] OR coverage[Title/Abstract] OR "not observed"[Title/Abstract] OR "unavailable evidence"[Title/Abstract] OR "incomplete evidence"[Title/Abstract] OR uncertainty[Title/Abstract] OR conflict[Title/Abstract] OR "non-independent evidence"[Title/Abstract] OR "correlated evidence"[Title/Abstract] OR "evidence reuse"[Title/Abstract] OR "duplicate evidence"[Title/Abstract] OR "shared dataset"[Title/Abstract] OR "overlapping cohort"[Title/Abstract]) AND ("evidence synthesis"[Title/Abstract] OR "evidence integration"[Title/Abstract] OR meta-analysis[Title/Abstract] OR "knowledge graph"[Title/Abstract]))',
        "openalex": '("missing data" OR "data absence" OR coverage OR "not observed" OR "unavailable evidence" OR "incomplete evidence" OR uncertainty OR conflict OR "non-independent evidence" OR "correlated evidence" OR "evidence reuse" OR "duplicate evidence" OR "shared dataset" OR "overlapping cohort") ("evidence synthesis" OR "evidence integration" OR meta-analysis OR "knowledge graph")',
    },
    {
        "id": "QF07_AI_TARGET_DISCOVERY",
        "categories": ["CAT_07", "CAT_01"],
        "focus": "CATEGORY_DISCOVERY",
        "pubmed": '(("drug target discovery"[Title/Abstract] OR "therapeutic target discovery"[Title/Abstract] OR "target prioritization"[Title/Abstract] OR "target identification"[Title/Abstract]) AND ("artificial intelligence"[Title/Abstract] OR "machine learning"[Title/Abstract] OR "large language model"[Title/Abstract] OR "natural language processing"[Title/Abstract] OR "graph neural network"[Title/Abstract]) AND (evidence[Title/Abstract] OR provenance[Title/Abstract] OR citation[Title/Abstract] OR "knowledge graph"[Title/Abstract] OR interpretation[Title/Abstract]))',
        "openalex": '("drug target discovery" OR "therapeutic target discovery" OR "target prioritization" OR "target identification") ("artificial intelligence" OR "machine learning" OR "large language model" OR "natural language processing" OR "graph neural network") (evidence OR provenance OR citation OR "knowledge graph" OR interpretation)',
    },
    {
        "id": "QF08_COUNTER_DEPENDENCY",
        "categories": ["CAT_06", "CAT_05", "CAT_01"],
        "focus": "COUNTEREXAMPLE_DEPENDENCY",
        "pubmed": '(("non-independent evidence"[Title/Abstract] OR "dependent evidence"[Title/Abstract] OR "correlated evidence"[Title/Abstract] OR "evidence reuse"[Title/Abstract] OR "duplicate evidence"[Title/Abstract] OR "shared dataset"[Title/Abstract] OR "overlapping cohort"[Title/Abstract]) AND ("evidence synthesis"[Title/Abstract] OR "evidence integration"[Title/Abstract] OR meta-analysis[Title/Abstract] OR framework[Title/Abstract]))',
        "openalex": '("non-independent evidence" OR "dependent evidence" OR "correlated evidence" OR "evidence reuse" OR "duplicate evidence" OR "shared dataset" OR "overlapping cohort") ("evidence synthesis" OR "evidence integration" OR meta-analysis OR framework)',
    },
    {
        "id": "QF09_COUNTER_MISSINGNESS",
        "categories": ["CAT_06", "CAT_05"],
        "focus": "COUNTEREXAMPLE_MISSINGNESS",
        "pubmed": '(("structured missingness"[Title/Abstract] OR "missingness mechanism"[Title/Abstract] OR "missing data"[Title/Abstract] OR "data absence"[Title/Abstract] OR "not observed"[Title/Abstract] OR "unavailable evidence"[Title/Abstract] OR "incomplete evidence"[Title/Abstract]) AND (ontology[Title/Abstract] OR "data model"[Title/Abstract] OR framework[Title/Abstract] OR "evidence synthesis"[Title/Abstract] OR "knowledge graph"[Title/Abstract]) AND (biomedical[Title/Abstract] OR clinical[Title/Abstract] OR health[Title/Abstract]))',
        "openalex": '("structured missingness" OR "missingness mechanism" OR "missing data" OR "data absence" OR "not observed" OR "unavailable evidence" OR "incomplete evidence") (ontology OR "data model" OR framework OR "evidence synthesis" OR "knowledge graph") (biomedical OR clinical OR health)',
    },
    {
        "id": "QF10_COUNTER_PROVENANCE_AGGREGATION",
        "categories": ["CAT_04", "CAT_03", "CAT_01"],
        "focus": "COUNTEREXAMPLE_PROVENANCE_THROUGH_AGGREGATION",
        "pubmed": '((provenance[Title/Abstract] OR lineage[Title/Abstract] OR derivation[Title/Abstract] OR traceability[Title/Abstract] OR "source attribution"[Title/Abstract]) AND (aggregation[Title/Abstract] OR summarization[Title/Abstract] OR "evidence integration"[Title/Abstract] OR "data integration"[Title/Abstract]) AND (biomedical[Title/Abstract] OR "knowledge graph"[Title/Abstract] OR "drug target"[Title/Abstract]))',
        "openalex": '(provenance OR lineage OR derivation OR traceability OR "source attribution") (aggregation OR summarization OR "evidence integration" OR "data integration") (biomedical OR "knowledge graph" OR "drug target")',
    },
    {
        "id": "QF11_COUNTER_CLAIM_EVIDENCE",
        "categories": ["CAT_04", "CAT_05", "CAT_06", "CAT_07"],
        "focus": "COUNTEREXAMPLE_CLAIM_EVIDENCE_BOUNDARY",
        "pubmed": '(("claim evidence"[Title/Abstract] OR "claim-evidence"[Title/Abstract] OR "evidence graph"[Title/Abstract] OR nanopublication[Title/Abstract] OR argumentation[Title/Abstract]) AND (biomedical[Title/Abstract] OR scientific[Title/Abstract] OR clinical[Title/Abstract]) AND (causality[Title/Abstract] OR interpretation[Title/Abstract] OR provenance[Title/Abstract] OR assertion[Title/Abstract] OR knowledge[Title/Abstract]))',
        "openalex": '("claim evidence" OR "claim-evidence" OR "evidence graph" OR nanopublication OR argumentation) (biomedical OR scientific OR clinical) (causality OR interpretation OR provenance OR assertion OR knowledge)',
    },
    {
        "id": "QF12_CLAIM_BOUNDARY_VARIANTS",
        "categories": ["CAT_01", "CAT_05", "CAT_06"],
        "focus": "COUNTEREXAMPLE_CLAIM_EVIDENCE_BOUNDARY",
        "pubmed": '(("evidence interpretation"[Title/Abstract] OR "evidence grading"[Title/Abstract] OR "strength of evidence"[Title/Abstract] OR "causal inference boundary"[Title/Abstract] OR "association versus causality"[Title/Abstract] OR "clinical translation"[Title/Abstract]) AND ("drug target"[Title/Abstract] OR "target evidence"[Title/Abstract] OR biomedical[Title/Abstract] OR "evidence synthesis"[Title/Abstract] OR "knowledge graph"[Title/Abstract]))',
        "openalex": '("evidence interpretation" OR "evidence grading" OR "strength of evidence" OR "causal inference boundary" OR "association versus causality" OR "clinical translation") ("drug target" OR "target evidence" OR biomedical OR "evidence synthesis" OR "knowledge graph")',
    },
    {
        "id": "QF13_COUNTER_CONFLICT_PRESERVATION",
        "categories": ["CAT_05", "CAT_06", "CAT_03"],
        "focus": "COUNTEREXAMPLE_CONFLICT_PRESERVATION",
        "pubmed": '(("conflicting evidence"[Title/Abstract] OR "conflict preservation"[Title/Abstract] OR "contradictory evidence"[Title/Abstract] OR "evidence conflict"[Title/Abstract]) AND ("evidence synthesis"[Title/Abstract] OR "evidence integration"[Title/Abstract] OR "systematic review"[Title/Abstract] OR "knowledge graph"[Title/Abstract]) AND (representation[Title/Abstract] OR model[Title/Abstract] OR preservation[Title/Abstract] OR reconciliation[Title/Abstract]))',
        "openalex": '("conflicting evidence" OR "conflict preservation" OR "contradictory evidence" OR "evidence conflict") ("evidence synthesis" OR "evidence integration" OR "systematic review" OR "knowledge graph") (representation OR model OR preservation OR reconciliation)',
    },
    {
        "id": "QF14_COUNTER_AI_GROUNDING",
        "categories": ["CAT_07", "CAT_01"],
        "focus": "COUNTEREXAMPLE_AI_OUTPUT_SOURCE_GROUNDING",
        "pubmed": '((("artificial intelligence"[Title/Abstract] OR "large language model"[Title/Abstract] OR "AI-assisted"[Title/Abstract]) AND ("target discovery"[Title/Abstract] OR "target prioritization"[Title/Abstract] OR "drug discovery"[Title/Abstract])) AND (grounding[Title/Abstract] OR citation[Title/Abstract] OR "source attribution"[Title/Abstract] OR "evidence link"[Title/Abstract] OR provenance[Title/Abstract] OR traceability[Title/Abstract]))',
        "openalex": '(("artificial intelligence" OR "large language model" OR "AI-assisted") ("target discovery" OR "target prioritization" OR "drug discovery")) (grounding OR citation OR "source attribution" OR "evidence link" OR provenance OR traceability)',
    },
]

OT_DOC_PATHS = {
    "README.md": "documentation_landing",
    "getting-started.md": "data_model_orientation",
    "data-access/README.md": "data_access_overview",
    "data-access/graphql-api.md": "api_documentation",
    "data-access/datasets.md": "export_and_dataset_documentation",
    "evidence.md": "evidence_documentation",
    "associations.md": "association_aggregation_scoring_documentation",
    "release-notes.md": "release_version_information",
    "citation.md": "primary_platform_publications",
    "web-interface/evidence-pages.md": "evidence_user_interface_surface",
    "web-interface/associations-on-the-fly.md": "target_synthesis_user_interface_surface",
}

SYSTEM_PATTERNS = [
    ("Open Targets Platform", ["open targets platform", "open targets genetics"], ["CAT_02", "CAT_01"], "IMPLEMENTED_SYSTEM", "DIRECT"),
    ("Pharos", ["pharos", "target central resource database", "tcrd"], ["CAT_01"], "IMPLEMENTED_SYSTEM", "DIRECT"),
    ("Illuminating the Druggable Genome", ["illuminating the druggable genome"], ["CAT_01"], "IMPLEMENTED_SYSTEM", "DIRECT"),
    ("DisGeNET", ["disgenet"], ["CAT_03", "CAT_01"], "IMPLEMENTED_SYSTEM", "DIRECT"),
    ("Hetionet", ["hetionet"], ["CAT_03"], "IMPLEMENTED_SYSTEM", "DIRECT"),
    ("DRKG", ["drug repurposing knowledge graph", "drkg"], ["CAT_03", "CAT_07"], "IMPLEMENTED_SYSTEM", "DIRECT"),
    ("PrimeKG", ["primekg"], ["CAT_03"], "IMPLEMENTED_SYSTEM", "ADJACENT"),
    ("SPOKE", ["scalable precision medicine open knowledge engine", "spoke knowledge graph"], ["CAT_03"], "IMPLEMENTED_SYSTEM", "ADJACENT"),
    ("Bio2RDF", ["bio2rdf"], ["CAT_03", "CAT_04"], "IMPLEMENTED_SYSTEM", "ADJACENT"),
    ("OpenBioLink", ["openbiolink"], ["CAT_03"], "IMPLEMENTED_SYSTEM", "ADJACENT"),
    ("PharmKG", ["pharmkg"], ["CAT_03"], "IMPLEMENTED_SYSTEM", "DIRECT"),
    ("BioKG", ["biokg"], ["CAT_03"], "IMPLEMENTED_SYSTEM", "ADJACENT"),
    ("Monarch Initiative", ["monarch initiative"], ["CAT_03", "CAT_04"], "IMPLEMENTED_SYSTEM", "ADJACENT"),
    ("W3C PROV", ["w3c prov", "prov-o", "prov ontology", "provenance ontology"], ["CAT_04"], "PROVENANCE_MODEL_OR_STANDARD", "ADJACENT"),
    ("Nanopublications", ["nanopublication", "nanopublications"], ["CAT_04", "CAT_05"], "PROVENANCE_MODEL_OR_STANDARD", "ADJACENT"),
    ("Biological Expression Language", ["biological expression language"], ["CAT_03", "CAT_04"], "PROVENANCE_MODEL_OR_STANDARD", "ADJACENT"),
    ("GRADE", ["gradepro", "grading of recommendations assessment development and evaluation"], ["CAT_05"], "EVIDENCE_ASSESSMENT_METHOD_OR_SYSTEM", "ADJACENT"),
    ("EPPI-Reviewer", ["eppi-reviewer"], ["CAT_05"], "IMPLEMENTED_SYSTEM", "ADJACENT"),
    ("RobotReviewer", ["robotreviewer"], ["CAT_05", "CAT_07"], "IMPLEMENTED_SYSTEM", "ADJACENT"),
    ("ASReview", ["asreview"], ["CAT_05", "CAT_07"], "IMPLEMENTED_SYSTEM", "ADJACENT"),
    ("PandaOmics", ["pandaomics", "panda omics"], ["CAT_07", "CAT_01"], "IMPLEMENTED_SYSTEM", "DIRECT"),
    ("BenevolentAI", ["benevolentai", "benevolent ai"], ["CAT_07", "CAT_01"], "IMPLEMENTED_SYSTEM", "DIRECT"),
    ("TxGNN", ["txgnn"], ["CAT_07", "CAT_03"], "IMPLEMENTED_SYSTEM", "DIRECT"),
    ("Therapeutics Data Commons", ["therapeutics data commons"], ["CAT_07", "CAT_03"], "IMPLEMENTED_SYSTEM", "ADJACENT"),
]

FORBIDDEN_CAPABILITY_STATES = {
    "PRESENT_VERIFIED", "PARTIAL_VERIFIED", "ABSENT_EXPLICIT",
    "NOT_FOUND_IN_REVIEWED_MATERIALS", "NOT_APPLICABLE", "NOT_ASSESSED",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def stable_id(prefix: str, *parts: object) -> str:
    value = "||".join(str(part).strip() for part in parts)
    return f"{prefix}_{hashlib.sha256(value.encode('utf-8')).hexdigest()[:20].upper()}"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", (value or "").lower())).strip()


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def fetch(url: str, destination: Path) -> tuple[bool, str]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "curl", "-fsSL", "--retry", "3", "--retry-delay", "1",
        "--connect-timeout", "30", "--max-time", "180",
        "-A", "luad-target-dossier-p2-e1b/0.1 (research search pilot)",
        "-o", str(destination), url,
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        return True, ""
    except subprocess.CalledProcessError as exc:
        if destination.exists():
            destination.unlink()
        detail = (exc.stderr or exc.stdout or str(exc)).strip().replace("\n", " ")
        return False, detail[:1000]


def payload_record(event_id: str, path: Path, source: str, url: str, query: str) -> dict[str, Any]:
    return {
        "search_event_id": event_id,
        "payload_path": str(path.relative_to(ROOT)),
        "source": source,
        "url": url,
        "exact_query": query,
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def retrieve_payloads() -> None:
    if MANIFEST.exists():
        print("Frozen P2-E1B retrieval manifest exists; mutable retrieval skipped.")
        return

    RAW.mkdir(parents=True, exist_ok=True)
    started_at = utc_now()
    events: list[dict[str, Any]] = []
    payloads: list[dict[str, Any]] = []

    for index, family in enumerate(QUERY_FAMILIES, start=1):
        family_id = family["id"]
        categories = family["categories"]
        focus = family["focus"]

        pubmed_event = f"P2E1B_PUBMED_{index:02d}"
        pubmed_query = f'({family["pubmed"]}) AND ("{DATE_FROM}"[Date - Publication] : "{DATE_TO}"[Date - Publication])'
        esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + urllib.parse.urlencode({
            "db": "pubmed", "term": pubmed_query, "retmode": "json",
            "retmax": str(CAPTURE_LIMIT), "sort": "relevance",
        })
        esearch_path = RAW / f"{pubmed_event.lower()}_esearch.json"
        executed_at = utc_now()
        ok, error = fetch(esearch_url, esearch_path)
        event: dict[str, Any] = {
            "search_event_id": pubmed_event,
            "search_role": "PILOT_SEARCH",
            "stream": "SCHOLARLY_DISCOVERY",
            "source_name": "PubMed",
            "source_provider": "NCBI",
            "search_type": "BIOMEDICAL_BIBLIOGRAPHIC_API",
            "query_family_id": family_id,
            "protocol_categories": categories,
            "counterexample_focus": focus if focus.startswith("COUNTEREXAMPLE") else "NOT_APPLICABLE",
            "exact_query": pubmed_query,
            "filters": {"publication_date_from": DATE_FROM, "publication_date_to": DATE_TO, "sort": "relevance"},
            "executed_at": executed_at,
            "timezone": "UTC",
            "source_url_or_endpoint": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/",
            "request_url": esearch_url,
            "result_count": "NOT_EXPOSED_DUE_TO_RETRIEVAL_FAILURE",
            "result_count_status": "UNAVAILABLE",
            "captured_result_count": 0,
            "pagination_completeness_boundary": "NO_RESULTS_CAPTURED",
            "export_capture_method": "NCBI_ESEARCH_JSON_PLUS_ESUMMARY_JSON",
            "network_status": "SUCCESS" if ok else "FAILED",
            "retrieval_error": error,
            "payload_paths": [],
        }
        if ok:
            payloads.append(payload_record(pubmed_event, esearch_path, "PubMed", esearch_url, pubmed_query))
            event["payload_paths"].append(str(esearch_path.relative_to(ROOT)))
            data = json.loads(esearch_path.read_text(encoding="utf-8"))
            result = data.get("esearchresult", {})
            ids = result.get("idlist", [])
            count = int(result.get("count", 0))
            event["result_count"] = count
            event["result_count_status"] = "SOURCE_EXPOSED_TOTAL"
            event["captured_result_count"] = len(ids)
            event["pagination_completeness_boundary"] = f"FIRST_{len(ids)}_OF_{count}_SORT_RELEVANCE;RETSTART_0;RETMAX_{CAPTURE_LIMIT}"
            if ids:
                esummary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?" + urllib.parse.urlencode({
                    "db": "pubmed", "id": ",".join(ids), "retmode": "json",
                })
                esummary_path = RAW / f"{pubmed_event.lower()}_esummary.json"
                time.sleep(0.36)
                summary_ok, summary_error = fetch(esummary_url, esummary_path)
                if summary_ok:
                    payloads.append(payload_record(pubmed_event, esummary_path, "PubMed", esummary_url, ",".join(ids)))
                    event["payload_paths"].append(str(esummary_path.relative_to(ROOT)))
                else:
                    event["network_status"] = "PARTIAL"
                    event["retrieval_error"] = summary_error
        events.append(event)
        time.sleep(0.36)

        openalex_event = f"P2E1B_OPENALEX_{index:02d}"
        openalex_query = family["openalex"]
        openalex_url = "https://api.openalex.org/works?" + urllib.parse.urlencode({
            "search": openalex_query,
            "filter": f"from_publication_date:{DATE_FROM},to_publication_date:{DATE_TO}",
            "per-page": str(CAPTURE_LIMIT),
            "page": "1",
            "sort": "relevance_score:desc",
        })
        openalex_path = RAW / f"{openalex_event.lower()}_works.json"
        executed_at = utc_now()
        ok, error = fetch(openalex_url, openalex_path)
        event = {
            "search_event_id": openalex_event,
            "search_role": "PILOT_SEARCH",
            "stream": "SCHOLARLY_DISCOVERY",
            "source_name": "OpenAlex",
            "source_provider": "OurResearch",
            "search_type": "MULTIDISCIPLINARY_SCHOLARLY_API",
            "query_family_id": family_id,
            "protocol_categories": categories,
            "counterexample_focus": focus if focus.startswith("COUNTEREXAMPLE") else "NOT_APPLICABLE",
            "exact_query": openalex_query,
            "filters": {"publication_date_from": DATE_FROM, "publication_date_to": DATE_TO, "sort": "relevance_score:desc"},
            "executed_at": executed_at,
            "timezone": "UTC",
            "source_url_or_endpoint": "https://api.openalex.org/works",
            "request_url": openalex_url,
            "result_count": "NOT_EXPOSED_DUE_TO_RETRIEVAL_FAILURE",
            "result_count_status": "UNAVAILABLE",
            "captured_result_count": 0,
            "pagination_completeness_boundary": "NO_RESULTS_CAPTURED",
            "export_capture_method": "OPENALEX_WORKS_API_JSON",
            "network_status": "SUCCESS" if ok else "FAILED",
            "retrieval_error": error,
            "payload_paths": [],
        }
        if ok:
            payloads.append(payload_record(openalex_event, openalex_path, "OpenAlex", openalex_url, openalex_query))
            event["payload_paths"].append(str(openalex_path.relative_to(ROOT)))
            data = json.loads(openalex_path.read_text(encoding="utf-8"))
            count = int(data.get("meta", {}).get("count", 0))
            captured = len(data.get("results", []))
            event["result_count"] = count
            event["result_count_status"] = "SOURCE_EXPOSED_TOTAL"
            event["captured_result_count"] = captured
            event["pagination_completeness_boundary"] = f"FIRST_{captured}_OF_{count}_SORT_RELEVANCE;PAGE_1;PER_PAGE_{CAPTURE_LIMIT}"
        events.append(event)

    # Open Targets is prespecified; capture official docs only after scholarly discovery.
    repo_event = "P2E1B_OT_ORIENTATION_REPOSITORY"
    commit_url = "https://api.github.com/repos/opentargets/platform-docs/commits/main"
    commit_path = RAW / "open_targets_platform_docs_commit_main.json"
    executed_at = utc_now()
    ok, error = fetch(commit_url, commit_path)
    repo_record: dict[str, Any] = {
        "search_event_id": repo_event,
        "search_role": "PILOT_SEARCH",
        "stream": "FIRST_PARTY_ORIENTATION",
        "source_name": "Open Targets Platform Documentation",
        "source_provider": "Open Targets via GitHub",
        "search_type": "TARGETED_FIRST_PARTY_REPOSITORY_ORIENTATION",
        "query_family_id": "OT_FIRST_PARTY_ORIENTATION",
        "protocol_categories": ["CAT_02", "CAT_01"],
        "counterexample_focus": "NOT_APPLICABLE",
        "exact_query": "Resolve the current official opentargets/platform-docs main commit and documentation tree",
        "filters": {"repository": "opentargets/platform-docs", "ref": "main"},
        "executed_at": executed_at,
        "timezone": "UTC",
        "source_url_or_endpoint": commit_url,
        "request_url": commit_url,
        "result_count": 0,
        "result_count_status": "ORIENTATION_MATERIAL_COUNT",
        "captured_result_count": 0,
        "pagination_completeness_boundary": "OFFICIAL_REPOSITORY_COMMIT_AND_FULL_RECURSIVE_TREE",
        "export_capture_method": "GITHUB_REPOSITORY_API_JSON_AND_RAW_IMMUTABLE_COMMIT_FILES",
        "network_status": "SUCCESS" if ok else "FAILED",
        "retrieval_error": error,
        "payload_paths": [],
        "resolved_commit_sha": "NOT_AVAILABLE",
    }
    if ok:
        payloads.append(payload_record(repo_event, commit_path, "Open Targets Platform Documentation", commit_url, repo_record["exact_query"]))
        repo_record["payload_paths"].append(str(commit_path.relative_to(ROOT)))
        commit_data = json.loads(commit_path.read_text(encoding="utf-8"))
        commit_sha = commit_data.get("sha", "")
        repo_record["resolved_commit_sha"] = commit_sha or "NOT_AVAILABLE"
        tree_url = f"https://api.github.com/repos/opentargets/platform-docs/git/trees/{commit_sha}?recursive=1"
        tree_path = RAW / f"open_targets_platform_docs_tree_{commit_sha[:12]}.json"
        tree_ok, tree_error = fetch(tree_url, tree_path)
        if tree_ok:
            payloads.append(payload_record(repo_event, tree_path, "Open Targets Platform Documentation", tree_url, "recursive repository tree"))
            repo_record["payload_paths"].append(str(tree_path.relative_to(ROOT)))
            tree = json.loads(tree_path.read_text(encoding="utf-8"))
            available = {item.get("path") for item in tree.get("tree", []) if item.get("type") == "blob"}
            captured_docs = 0
            for doc_index, (doc_path, orientation_role) in enumerate(OT_DOC_PATHS.items(), start=1):
                doc_event_id = f"P2E1B_OTDOC_{doc_index:02d}"
                raw_url = f"https://raw.githubusercontent.com/opentargets/platform-docs/{commit_sha}/{urllib.parse.quote(doc_path)}"
                destination = RAW / "open_targets_docs" / doc_path.replace("/", "__")
                doc_executed_at = utc_now()
                if doc_path in available:
                    doc_ok, doc_error = fetch(raw_url, destination)
                else:
                    doc_ok, doc_error = False, "PATH_NOT_PRESENT_IN_FROZEN_REPOSITORY_TREE"
                doc_record = {
                    "search_event_id": doc_event_id,
                    "search_role": "PILOT_SEARCH",
                    "stream": "FIRST_PARTY_ORIENTATION",
                    "source_name": "Open Targets Platform Documentation",
                    "source_provider": "Open Targets via GitHub",
                    "search_type": "TARGETED_FIRST_PARTY_DOCUMENT_CAPTURE",
                    "query_family_id": "OT_FIRST_PARTY_ORIENTATION",
                    "protocol_categories": ["CAT_02", "CAT_01"],
                    "counterexample_focus": "NOT_APPLICABLE",
                    "exact_query": f"OFFICIAL_REPOSITORY_PATH::{doc_path}@{commit_sha}",
                    "filters": {"orientation_role": orientation_role, "repository_commit": commit_sha},
                    "executed_at": doc_executed_at,
                    "timezone": "UTC",
                    "source_url_or_endpoint": raw_url,
                    "request_url": raw_url,
                    "result_count": 1 if doc_ok else 0,
                    "result_count_status": "ORIENTATION_MATERIAL_COUNT",
                    "captured_result_count": 1 if doc_ok else 0,
                    "pagination_completeness_boundary": "ONE_EXACT_FILE_AT_IMMUTABLE_COMMIT",
                    "export_capture_method": "RAW_GITHUB_IMMUTABLE_COMMIT_FILE",
                    "network_status": "SUCCESS" if doc_ok else "FAILED",
                    "retrieval_error": doc_error,
                    "payload_paths": [],
                    "resolved_commit_sha": commit_sha,
                    "orientation_role": orientation_role,
                    "repository_path": doc_path,
                }
                if doc_ok:
                    captured_docs += 1
                    payloads.append(payload_record(doc_event_id, destination, "Open Targets Platform Documentation", raw_url, doc_record["exact_query"]))
                    doc_record["payload_paths"].append(str(destination.relative_to(ROOT)))
                events.append(doc_record)
            repo_record["result_count"] = captured_docs
            repo_record["captured_result_count"] = captured_docs
        else:
            repo_record["network_status"] = "PARTIAL"
            repo_record["retrieval_error"] = tree_error
    events.append(repo_record)

    manifest = {
        "pilot_id": "P2_E1B_SEARCH_STRATEGY_PILOT_V0.1",
        "generator_version": GENERATOR_VERSION,
        "retrieval_started_at_utc": started_at,
        "retrieval_completed_at_utc": utc_now(),
        "mutable_network_retrieval": True,
        "future_network_byte_identity_claimed": False,
        "captured_page_is_formal_denominator": False,
        "capture_limit_per_scholarly_event": CAPTURE_LIMIT,
        "events": sorted(events, key=lambda row: row["search_event_id"]),
        "payloads": sorted(payloads, key=lambda row: (row["search_event_id"], row["payload_path"])),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def repair_open_targets_orientation() -> None:
    """Retry failed immutable-commit docs through GitHub's blob API.

    The original raw-URL failures remain in each event and in a repair history.
    This function is explicit because a completed manifest is otherwise frozen.
    """
    if not MANIFEST.exists():
        raise SystemExit("Open Targets repair requires an existing retrieval manifest.")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    repo_event = next(
        (event for event in manifest["events"] if event["search_event_id"] == "P2E1B_OT_ORIENTATION_REPOSITORY"),
        None,
    )
    if not repo_event or repo_event.get("resolved_commit_sha") in {None, "", "NOT_AVAILABLE"}:
        raise SystemExit("Open Targets repository commit was not resolved; blob repair is unavailable.")
    commit_sha = repo_event["resolved_commit_sha"]
    tree_payload = next(
        (ROOT / payload["payload_path"] for payload in manifest["payloads"] if "open_targets_platform_docs_tree_" in payload["payload_path"]),
        None,
    )
    if not tree_payload or not tree_payload.exists():
        raise SystemExit("Frozen Open Targets repository tree is unavailable.")
    tree = json.loads(tree_payload.read_text(encoding="utf-8"))
    blob_by_path = {
        item.get("path"): item.get("sha")
        for item in tree.get("tree", [])
        if item.get("type") == "blob" and item.get("path") in OT_DOC_PATHS
    }
    repair_started = utc_now()
    attempted = 0
    recovered = 0
    for event in manifest["events"]:
        if event.get("search_type") != "TARGETED_FIRST_PARTY_DOCUMENT_CAPTURE":
            continue
        if str(event.get("network_status", "")).startswith("SUCCESS"):
            continue
        attempted += 1
        doc_path = event["repository_path"]
        blob_sha = blob_by_path.get(doc_path)
        event.setdefault("prior_retrieval_errors", []).append({
            "method": event.get("export_capture_method"),
            "url": event.get("request_url"),
            "error": event.get("retrieval_error", ""),
        })
        if not blob_sha:
            event["retrieval_error"] = "PATH_OR_BLOB_SHA_NOT_PRESENT_IN_FROZEN_REPOSITORY_TREE"
            continue
        blob_url = f"https://api.github.com/repos/opentargets/platform-docs/git/blobs/{blob_sha}"
        destination = RAW / "open_targets_docs" / f"{doc_path.replace('/', '__')}.github_blob.json"
        ok, error = fetch(blob_url, destination)
        if not ok:
            event["retrieval_error"] = error
            continue
        # Validate that the API response contains decodable content before registration.
        blob = json.loads(destination.read_text(encoding="utf-8"))
        encoded = blob.get("content", "").replace("\n", "")
        try:
            decoded = base64.b64decode(encoded, validate=True)
        except Exception as exc:
            event["retrieval_error"] = f"GITHUB_BLOB_CONTENT_DECODE_FAILED:{type(exc).__name__}"
            continue
        if not decoded:
            event["retrieval_error"] = "GITHUB_BLOB_CONTENT_EMPTY"
            continue
        manifest["payloads"].append(payload_record(
            event["search_event_id"], destination, "Open Targets Platform Documentation",
            blob_url, f"GITHUB_BLOB::{doc_path}@{commit_sha}",
        ))
        event["payload_paths"].append(str(destination.relative_to(ROOT)))
        event["network_status"] = "SUCCESS_AFTER_GITHUB_BLOB_RETRY"
        event["retrieval_error"] = ""
        event["request_url"] = blob_url
        event["source_url_or_endpoint"] = blob_url
        event["export_capture_method"] = "GITHUB_GIT_BLOB_API_JSON_AT_IMMUTABLE_COMMIT"
        event["result_count"] = 1
        event["captured_result_count"] = 1
        event["pagination_completeness_boundary"] = "ONE_EXACT_GIT_BLOB_AT_IMMUTABLE_COMMIT"
        event["blob_sha"] = blob_sha
        recovered += 1
    manifest.setdefault("retrieval_repair_history", []).append({
        "repair_id": stable_id("REPAIR", commit_sha, repair_started, attempted),
        "repair_started_at_utc": repair_started,
        "repair_completed_at_utc": utc_now(),
        "reason": "RAW_GITHUB_DELIVERY_TIMEOUTS_FOR_REQUIRED_OPEN_TARGETS_ORIENTATION_FILES",
        "replacement_method": "GITHUB_GIT_BLOB_API_AT_SAME_FROZEN_COMMIT",
        "attempted_event_count": attempted,
        "recovered_event_count": recovered,
        "original_failures_retained": True,
    })
    manifest["retrieval_completed_at_utc"] = utc_now()
    manifest["events"] = sorted(manifest["events"], key=lambda row: row["search_event_id"])
    manifest["payloads"] = sorted(manifest["payloads"], key=lambda row: (row["search_event_id"], row["payload_path"]))
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Open Targets orientation repair: attempted={attempted}; recovered={recovered}")


def repair_pubmed_event(event_id: str) -> None:
    """Retry one failed PubMed event with its exact frozen query and log history."""
    if not MANIFEST.exists():
        raise SystemExit("PubMed event repair requires an existing retrieval manifest.")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    event = next((row for row in manifest["events"] if row["search_event_id"] == event_id), None)
    if not event or event.get("source_name") != "PubMed":
        raise SystemExit(f"Not a registered PubMed event: {event_id}")
    if str(event.get("network_status", "")).startswith("SUCCESS"):
        print(f"PubMed event already successful; repair skipped: {event_id}")
        return
    repair_started = utc_now()
    event.setdefault("prior_retrieval_errors", []).append({
        "method": event.get("export_capture_method"),
        "url": event.get("request_url"),
        "error": event.get("retrieval_error", ""),
    })
    esearch_path = RAW / f"{event_id.lower()}_esearch_retry.json"
    ok, error = fetch(event["request_url"], esearch_path)
    recovered = False
    if ok:
        manifest["payloads"].append(payload_record(event_id, esearch_path, "PubMed", event["request_url"], event["exact_query"]))
        event["payload_paths"].append(str(esearch_path.relative_to(ROOT)))
        data = json.loads(esearch_path.read_text(encoding="utf-8"))
        result = data.get("esearchresult", {})
        ids = result.get("idlist", [])
        count = int(result.get("count", 0))
        summary_ok = True
        summary_error = ""
        if ids:
            esummary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?" + urllib.parse.urlencode({
                "db": "pubmed", "id": ",".join(ids), "retmode": "json",
            })
            esummary_path = RAW / f"{event_id.lower()}_esummary_retry.json"
            time.sleep(0.36)
            summary_ok, summary_error = fetch(esummary_url, esummary_path)
            if summary_ok:
                manifest["payloads"].append(payload_record(event_id, esummary_path, "PubMed", esummary_url, ",".join(ids)))
                event["payload_paths"].append(str(esummary_path.relative_to(ROOT)))
        event["result_count"] = count
        event["result_count_status"] = "SOURCE_EXPOSED_TOTAL"
        event["captured_result_count"] = len(ids) if summary_ok else 0
        event["pagination_completeness_boundary"] = f"FIRST_{len(ids) if summary_ok else 0}_OF_{count}_SORT_RELEVANCE;RETSTART_0;RETMAX_{CAPTURE_LIMIT}"
        event["network_status"] = "SUCCESS_AFTER_EXACT_QUERY_RETRY" if summary_ok else "PARTIAL_AFTER_EXACT_QUERY_RETRY"
        event["retrieval_error"] = summary_error
        recovered = summary_ok
    else:
        event["retrieval_error"] = error
    manifest.setdefault("retrieval_repair_history", []).append({
        "repair_id": stable_id("REPAIR", event_id, repair_started),
        "repair_started_at_utc": repair_started,
        "repair_completed_at_utc": utc_now(),
        "reason": "RETRY_TRANSIENT_PUBMED_EVENT_FAILURE_WITH_EXACT_PRESERVED_QUERY",
        "event_id": event_id,
        "replacement_method": "SAME_NCBI_EUTILITIES_ENDPOINT_AND_EXACT_QUERY",
        "recovered": recovered,
        "original_failure_retained": True,
    })
    manifest["retrieval_completed_at_utc"] = utc_now()
    manifest["events"] = sorted(manifest["events"], key=lambda row: row["search_event_id"])
    manifest["payloads"] = sorted(manifest["payloads"], key=lambda row: (row["search_event_id"], row["payload_path"]))
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"PubMed event repair: event={event_id}; recovered={str(recovered).upper()}")


def add_query_family(family_id: str) -> None:
    """Append a newly specified pilot family without rewriting prior events."""
    if not MANIFEST.exists():
        raise SystemExit("Adding a query family requires an existing retrieval manifest.")
    family = next((row for row in QUERY_FAMILIES if row["id"] == family_id), None)
    if not family:
        raise SystemExit(f"Unknown configured query family: {family_id}")
    index = QUERY_FAMILIES.index(family) + 1
    event_ids = {f"P2E1B_PUBMED_{index:02d}", f"P2E1B_OPENALEX_{index:02d}"}
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    existing = {row["search_event_id"] for row in manifest["events"]}
    if event_ids & existing:
        print(f"Query family already captured; addition skipped: {family_id}")
        return
    started_at = utc_now()
    new_events: list[dict[str, Any]] = []
    new_payloads: list[dict[str, Any]] = []

    pubmed_event = f"P2E1B_PUBMED_{index:02d}"
    pubmed_query = f'({family["pubmed"]}) AND ("{DATE_FROM}"[Date - Publication] : "{DATE_TO}"[Date - Publication])'
    esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + urllib.parse.urlencode({
        "db": "pubmed", "term": pubmed_query, "retmode": "json",
        "retmax": str(CAPTURE_LIMIT), "sort": "relevance",
    })
    esearch_path = RAW / f"{pubmed_event.lower()}_esearch.json"
    executed_at = utc_now()
    ok, error = fetch(esearch_url, esearch_path)
    pubmed_record: dict[str, Any] = {
        "search_event_id": pubmed_event, "search_role": "PILOT_SEARCH",
        "stream": "SCHOLARLY_DISCOVERY", "source_name": "PubMed", "source_provider": "NCBI",
        "search_type": "BIOMEDICAL_BIBLIOGRAPHIC_API", "query_family_id": family_id,
        "protocol_categories": family["categories"], "counterexample_focus": family["focus"],
        "exact_query": pubmed_query,
        "filters": {"publication_date_from": DATE_FROM, "publication_date_to": DATE_TO, "sort": "relevance"},
        "executed_at": executed_at, "timezone": "UTC",
        "source_url_or_endpoint": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/",
        "request_url": esearch_url, "result_count": "NOT_EXPOSED_DUE_TO_RETRIEVAL_FAILURE",
        "result_count_status": "UNAVAILABLE", "captured_result_count": 0,
        "pagination_completeness_boundary": "NO_RESULTS_CAPTURED",
        "export_capture_method": "NCBI_ESEARCH_JSON_PLUS_ESUMMARY_JSON",
        "network_status": "SUCCESS" if ok else "FAILED", "retrieval_error": error,
        "payload_paths": [],
    }
    if ok:
        new_payloads.append(payload_record(pubmed_event, esearch_path, "PubMed", esearch_url, pubmed_query))
        pubmed_record["payload_paths"].append(str(esearch_path.relative_to(ROOT)))
        result = json.loads(esearch_path.read_text(encoding="utf-8")).get("esearchresult", {})
        ids = result.get("idlist", [])
        count = int(result.get("count", 0))
        pubmed_record["result_count"] = count
        pubmed_record["result_count_status"] = "SOURCE_EXPOSED_TOTAL"
        pubmed_record["captured_result_count"] = len(ids)
        pubmed_record["pagination_completeness_boundary"] = f"FIRST_{len(ids)}_OF_{count}_SORT_RELEVANCE;RETSTART_0;RETMAX_{CAPTURE_LIMIT}"
        if ids:
            esummary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?" + urllib.parse.urlencode({
                "db": "pubmed", "id": ",".join(ids), "retmode": "json",
            })
            esummary_path = RAW / f"{pubmed_event.lower()}_esummary.json"
            time.sleep(0.36)
            summary_ok, summary_error = fetch(esummary_url, esummary_path)
            if summary_ok:
                new_payloads.append(payload_record(pubmed_event, esummary_path, "PubMed", esummary_url, ",".join(ids)))
                pubmed_record["payload_paths"].append(str(esummary_path.relative_to(ROOT)))
            else:
                pubmed_record["network_status"] = "PARTIAL"
                pubmed_record["retrieval_error"] = summary_error
    new_events.append(pubmed_record)

    openalex_event = f"P2E1B_OPENALEX_{index:02d}"
    openalex_query = family["openalex"]
    openalex_url = "https://api.openalex.org/works?" + urllib.parse.urlencode({
        "search": openalex_query,
        "filter": f"from_publication_date:{DATE_FROM},to_publication_date:{DATE_TO}",
        "per-page": str(CAPTURE_LIMIT), "page": "1", "sort": "relevance_score:desc",
    })
    openalex_path = RAW / f"{openalex_event.lower()}_works.json"
    executed_at = utc_now()
    ok, error = fetch(openalex_url, openalex_path)
    openalex_record: dict[str, Any] = {
        "search_event_id": openalex_event, "search_role": "PILOT_SEARCH",
        "stream": "SCHOLARLY_DISCOVERY", "source_name": "OpenAlex", "source_provider": "OurResearch",
        "search_type": "MULTIDISCIPLINARY_SCHOLARLY_API", "query_family_id": family_id,
        "protocol_categories": family["categories"], "counterexample_focus": family["focus"],
        "exact_query": openalex_query,
        "filters": {"publication_date_from": DATE_FROM, "publication_date_to": DATE_TO, "sort": "relevance_score:desc"},
        "executed_at": executed_at, "timezone": "UTC",
        "source_url_or_endpoint": "https://api.openalex.org/works", "request_url": openalex_url,
        "result_count": "NOT_EXPOSED_DUE_TO_RETRIEVAL_FAILURE", "result_count_status": "UNAVAILABLE",
        "captured_result_count": 0, "pagination_completeness_boundary": "NO_RESULTS_CAPTURED",
        "export_capture_method": "OPENALEX_WORKS_API_JSON",
        "network_status": "SUCCESS" if ok else "FAILED", "retrieval_error": error,
        "payload_paths": [],
    }
    if ok:
        new_payloads.append(payload_record(openalex_event, openalex_path, "OpenAlex", openalex_url, openalex_query))
        openalex_record["payload_paths"].append(str(openalex_path.relative_to(ROOT)))
        data = json.loads(openalex_path.read_text(encoding="utf-8"))
        count = int(data.get("meta", {}).get("count", 0))
        captured = len(data.get("results", []))
        openalex_record["result_count"] = count
        openalex_record["result_count_status"] = "SOURCE_EXPOSED_TOTAL"
        openalex_record["captured_result_count"] = captured
        openalex_record["pagination_completeness_boundary"] = f"FIRST_{captured}_OF_{count}_SORT_RELEVANCE;PAGE_1;PER_PAGE_{CAPTURE_LIMIT}"
    new_events.append(openalex_record)

    manifest["events"].extend(new_events)
    manifest["payloads"].extend(new_payloads)
    manifest.setdefault("retrieval_repair_history", []).append({
        "repair_id": stable_id("ADDITION", family_id, started_at),
        "repair_started_at_utc": started_at,
        "repair_completed_at_utc": utc_now(),
        "reason": "REQUIREMENTS_CROSS_CHECK_IDENTIFIED_UNTESTED_EXPLICIT_COUNTEREXAMPLE_OR_SYNONYM_VARIANT",
        "query_family_id": family_id,
        "event_ids": sorted(event_ids),
        "prior_events_rewritten": False,
    })
    manifest["retrieval_completed_at_utc"] = utc_now()
    manifest["events"] = sorted(manifest["events"], key=lambda row: row["search_event_id"])
    manifest["payloads"] = sorted(manifest["payloads"], key=lambda row: (row["search_event_id"], row["payload_path"]))
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Query-family addition: family={family_id}; events_added=2")


def correct_manifest_metadata() -> None:
    """Correct a non-scientific repair-history label without changing payloads."""
    if not MANIFEST.exists():
        raise SystemExit("Manifest metadata correction requires an existing retrieval manifest.")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    old = "REQUIREMENTS_CROSS_CHECK_IDENTIFIED_UNTESTED_EXPLICIT_CLAIM_BOUNDARY_VARIANTS"
    new = "REQUIREMENTS_CROSS_CHECK_IDENTIFIED_UNTESTED_EXPLICIT_COUNTEREXAMPLE_OR_SYNONYM_VARIANT"
    corrected = []
    for item in manifest.get("retrieval_repair_history", []):
        if item.get("reason") == old:
            item["prior_reason_label"] = old
            item["reason"] = new
            corrected.append(item.get("query_family_id", "UNKNOWN"))
    if corrected:
        manifest.setdefault("metadata_correction_history", []).append({
            "correction_id": stable_id("METACORR", old, new, *corrected),
            "field": "retrieval_repair_history.reason",
            "old_value": old,
            "new_value": new,
            "affected_query_families": sorted(corrected),
            "payload_bytes_changed": False,
            "event_query_bytes_changed": False,
            "reason": "The prior label was too narrow for conflict-preservation and AI-grounding additions.",
        })
        MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Manifest metadata correction: corrected={len(corrected)}")


def invert_abstract(index: dict[str, list[int]] | None) -> str:
    if not index:
        return ""
    positions: list[tuple[int, str]] = []
    for word, locs in index.items():
        positions.extend((int(pos), word) for pos in locs)
    return " ".join(word for _, word in sorted(positions))


def pubmed_records(event: dict[str, Any]) -> list[dict[str, Any]]:
    paths = [ROOT / path for path in event.get("payload_paths", []) if "_esummary" in path and path.endswith(".json")]
    if not paths:
        return []
    data = json.loads(paths[0].read_text(encoding="utf-8"))
    result = data.get("result", {})
    records = []
    for pmid in result.get("uids", []):
        item = result.get(pmid, {})
        article_ids = {entry.get("idtype", ""): entry.get("value", "") for entry in item.get("articleids", [])}
        records.append({
            "provider_record_id": f"PMID:{pmid}",
            "title": item.get("title", "").rstrip("."),
            "authors": "; ".join(a.get("name", "") for a in item.get("authors", []) if a.get("name")),
            "organization": "",
            "publication_date": item.get("pubdate", ""),
            "year": (re.search(r"(?:19|20)\d{2}", item.get("pubdate", "")) or ["UNKNOWN"])[0],
            "doi": article_ids.get("doi", ""),
            "pmid": pmid,
            "pmcid": article_ids.get("pmc", ""),
            "openalex_id": "",
            "persistent_identifier": f"PMID:{pmid}",
            "source_type": "SCHOLARLY_RECORD",
            "venue": item.get("fulljournalname", item.get("source", "")),
            "work_type": "|".join(item.get("pubtype", [])),
            "peer_review_status": "UNRESOLVED_FROM_DISCOVERY_METADATA",
            "party_relationship": "UNRESOLVED_FROM_DISCOVERY_METADATA",
            "abstract_or_description": "",
            "raw_source": "PubMed",
            "raw_payload_path": str(paths[0].relative_to(ROOT)),
            "is_retracted": "UNRESOLVED_FROM_DISCOVERY_METADATA",
        })
    return records


def openalex_records(event: dict[str, Any]) -> list[dict[str, Any]]:
    paths = [ROOT / path for path in event.get("payload_paths", []) if path.endswith("_works.json")]
    if not paths:
        return []
    data = json.loads(paths[0].read_text(encoding="utf-8"))
    records = []
    for item in data.get("results", []):
        ids = item.get("ids") or {}
        doi = (item.get("doi") or ids.get("doi") or "").replace("https://doi.org/", "")
        pmid = (ids.get("pmid") or "").replace("https://pubmed.ncbi.nlm.nih.gov/", "")
        pmcid = (ids.get("pmcid") or "").replace("https://www.ncbi.nlm.nih.gov/pmc/articles/", "").rstrip("/")
        authors = "; ".join(
            a.get("author", {}).get("display_name", "")
            for a in item.get("authorships", [])
            if a.get("author", {}).get("display_name")
        )
        source = ((item.get("primary_location") or {}).get("source") or {}).get("display_name", "")
        records.append({
            "provider_record_id": item.get("id", ""),
            "title": item.get("title", ""),
            "authors": authors,
            "organization": "",
            "publication_date": item.get("publication_date", ""),
            "year": item.get("publication_year", "UNKNOWN"),
            "doi": doi,
            "pmid": pmid,
            "pmcid": pmcid,
            "openalex_id": item.get("id", ""),
            "persistent_identifier": doi and f"DOI:{doi}" or item.get("id", ""),
            "source_type": "SCHOLARLY_RECORD",
            "venue": source,
            "work_type": item.get("type", ""),
            "peer_review_status": "UNRESOLVED_FROM_DISCOVERY_METADATA",
            "party_relationship": "UNRESOLVED_FROM_DISCOVERY_METADATA",
            "abstract_or_description": invert_abstract(item.get("abstract_inverted_index")),
            "raw_source": "OpenAlex",
            "raw_payload_path": str(paths[0].relative_to(ROOT)),
            "is_retracted": str(bool(item.get("is_retracted", False))).upper(),
        })
    return records


def discovery_key(record: dict[str, Any]) -> str:
    if record.get("doi"):
        return f"DOI::{record['doi'].lower()}"
    if record.get("pmid"):
        return f"PMID::{record['pmid']}"
    title = normalize_text(record.get("title", ""))
    return f"TITLE_YEAR::{title}::{record.get('year', 'UNKNOWN')}"


def classify_preliminary_relevance(title: str, description: str, categories: set[str], event_count: int) -> tuple[str, str]:
    text = normalize_text(f"{title} {description}")
    signals = [
        "open targets", "target prioritization", "target prioritisation", "drug target",
        "therapeutic target", "knowledge graph", "evidence graph", "evidence synthesis",
        "evidence assessment", "provenance", "traceability", "nanopublication",
        "missing data", "uncertainty", "dependent evidence", "overlapping cohort",
        "artificial intelligence", "machine learning", "large language model",
    ]
    matched = sorted({term for term in signals if term in text})
    target_context = any(term in text for term in ("target", "drug", "therapeutic", "biomedical", "clinical", "evidence"))
    if len(matched) >= 2 or (event_count >= 2 and matched):
        return "LIKELY_RELEVANT", f"DISCOVERY_KEYWORDS:{'|'.join(matched[:6])};EVENTS:{event_count}"
    if matched or target_context or len(categories) >= 2:
        return "POSSIBLY_RELEVANT", f"LIMITED_DISCOVERY_SIGNAL:{'|'.join(matched[:4]) or 'CATEGORY_CONTEXT'};EVENTS:{event_count}"
    if text:
        return "LIKELY_OUT_OF_SCOPE", "NO_TARGET_EVIDENCE_OR_REPRESENTATION_SIGNAL_IN_CAPTURED_METADATA"
    return "UNRESOLVED", "TITLE_AND_DESCRIPTION_INSUFFICIENT"


def build_search_log(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    payload_lookup: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for payload in manifest["payloads"]:
        payload_lookup[payload["search_event_id"]].append(payload)
    rows = []
    for event in manifest["events"]:
        event_payloads = payload_lookup.get(event["search_event_id"], [])
        rows.append({
            "search_event_id": event["search_event_id"],
            "search_role": event["search_role"],
            "stream": event["stream"],
            "source_name": event["source_name"],
            "source_provider": event["source_provider"],
            "search_type": event["search_type"],
            "query_family_id": event["query_family_id"],
            "protocol_categories": "|".join(event["protocol_categories"]),
            "counterexample_focus": event["counterexample_focus"],
            "exact_query": event["exact_query"],
            "filters": json.dumps(event["filters"], sort_keys=True, separators=(",", ":")),
            "executed_at": event["executed_at"],
            "timezone": event["timezone"],
            "result_count": event["result_count"],
            "result_count_status": event["result_count_status"],
            "captured_result_count": event["captured_result_count"],
            "pagination_completeness_boundary": event["pagination_completeness_boundary"],
            "export_capture_method": event["export_capture_method"],
            "source_url_or_endpoint": event["source_url_or_endpoint"],
            "request_url": event["request_url"],
            "raw_payload_paths": "|".join(p["payload_path"] for p in event_payloads) or "NOT_RETAINED",
            "raw_payload_sha256s": "|".join(p["sha256"] for p in event_payloads) or "NOT_AVAILABLE",
            "network_status": event["network_status"],
            "retrieval_error": event.get("retrieval_error", ""),
            "peer_checker_id": "PENDING",
            "assistance_mode": ASSISTANCE_MODE,
            "notes": "Pilot only; not a production-search denominator.",
        })
    fields = [
        "search_event_id", "search_role", "stream", "source_name", "source_provider",
        "search_type", "query_family_id", "protocol_categories", "counterexample_focus",
        "exact_query", "filters", "executed_at", "timezone", "result_count",
        "result_count_status", "captured_result_count", "pagination_completeness_boundary",
        "export_capture_method", "source_url_or_endpoint", "request_url",
        "raw_payload_paths", "raw_payload_sha256s", "network_status", "retrieval_error",
        "peer_checker_id", "assistance_mode", "notes",
    ]
    write_csv(SEARCH / "pilot_search_log.csv", fields, rows)
    return rows


def build_source_registry(manifest: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
    merged: dict[str, dict[str, Any]] = {}
    retrieved_before_dedup = 0
    scholarly_events = [e for e in manifest["events"] if e["stream"] == "SCHOLARLY_DISCOVERY"]
    for event in scholarly_events:
        records = pubmed_records(event) if event["source_name"] == "PubMed" else openalex_records(event)
        retrieved_before_dedup += len(records)
        for record in records:
            key = discovery_key(record)
            if key not in merged:
                merged[key] = {**record, "event_ids": set(), "categories": set(), "provider_ids": set(), "payload_paths": set()}
            target = merged[key]
            target["event_ids"].add(event["search_event_id"])
            target["categories"].update(event["protocol_categories"])
            target["provider_ids"].add(record["provider_record_id"])
            target["payload_paths"].add(record["raw_payload_path"])
            for field in ("doi", "pmid", "pmcid", "openalex_id", "authors", "publication_date", "venue", "abstract_or_description"):
                if not target.get(field) and record.get(field):
                    target[field] = record[field]
            if record["raw_source"] not in target.get("raw_source", ""):
                target["raw_source"] = "|".join(sorted(set(target.get("raw_source", "").split("|")) | {record["raw_source"]}))

    rows: list[dict[str, Any]] = []
    for key, record in merged.items():
        relevance, rationale = classify_preliminary_relevance(
            record["title"], record.get("abstract_or_description", ""), record["categories"], len(record["event_ids"])
        )
        canonical = record.get("doi") and f"DOI:{record['doi'].lower()}" or record.get("pmid") and f"PMID:{record['pmid']}" or key
        rows.append({
            "provisional_source_id": stable_id("P2SRC", canonical),
            "title": record["title"],
            "authors_or_organization": record.get("authors") or record.get("organization") or "NOT_AVAILABLE_IN_CAPTURED_METADATA",
            "year_or_date": record.get("publication_date") or record.get("year") or "UNKNOWN",
            "doi": record.get("doi", ""),
            "pmid": record.get("pmid", ""),
            "pmcid": record.get("pmcid", ""),
            "openalex_id": record.get("openalex_id", ""),
            "other_persistent_identifier": record.get("persistent_identifier", ""),
            "source_type": record["source_type"],
            "discovery_search_event_ids": "|".join(sorted(record["event_ids"])),
            "candidate_review_categories": "|".join(sorted(record["categories"])),
            "peer_review_status": record["peer_review_status"],
            "party_relationship": record["party_relationship"],
            "preliminary_relevance_flag": relevance,
            "preliminary_relevance_rationale": rationale,
            "venue_or_surface": record.get("venue", ""),
            "work_type": record.get("work_type", ""),
            "provider_record_ids": "|".join(sorted(record["provider_ids"])),
            "raw_payload_paths": "|".join(sorted(record["payload_paths"])),
            "retraction_status": record.get("is_retracted", "UNRESOLVED_FROM_DISCOVERY_METADATA"),
            "discovery_only_not_screening": "TRUE",
            "assistance_mode": ASSISTANCE_MODE,
        })

    # Register each captured official Open Targets material as a source candidate.
    for event in manifest["events"]:
        if event["search_type"] != "TARGETED_FIRST_PARTY_DOCUMENT_CAPTURE" or not str(event["network_status"]).startswith("SUCCESS"):
            continue
        path = event["repository_path"]
        rows.append({
            "provisional_source_id": stable_id("P2SRC", "opentargets/platform-docs", event["resolved_commit_sha"], path),
            "title": f"Open Targets Platform Documentation — {event['orientation_role'].replace('_', ' ')}",
            "authors_or_organization": "Open Targets",
            "year_or_date": event["executed_at"],
            "doi": "",
            "pmid": "",
            "pmcid": "",
            "openalex_id": "",
            "other_persistent_identifier": f"GITHUB:opentargets/platform-docs@{event['resolved_commit_sha']}:{path}",
            "source_type": "OFFICIAL_FIRST_PARTY_DOCUMENTATION",
            "discovery_search_event_ids": event["search_event_id"],
            "candidate_review_categories": "CAT_01|CAT_02",
            "peer_review_status": "NOT_APPLICABLE_DOCUMENTATION",
            "party_relationship": "FIRST_PARTY",
            "preliminary_relevance_flag": "LIKELY_RELEVANT",
            "preliminary_relevance_rationale": f"PRESPECIFIED_OPEN_TARGETS_ORIENTATION:{event['orientation_role']}",
            "venue_or_surface": "Official opentargets/platform-docs repository",
            "work_type": event["orientation_role"],
            "provider_record_ids": event["exact_query"],
            "raw_payload_paths": "|".join(event["payload_paths"]),
            "retraction_status": "NOT_APPLICABLE_DOCUMENTATION",
            "discovery_only_not_screening": "TRUE",
            "assistance_mode": ASSISTANCE_MODE,
        })

    rows = sorted(rows, key=lambda row: (row["title"].lower(), row["provisional_source_id"]))
    fields = [
        "provisional_source_id", "title", "authors_or_organization", "year_or_date",
        "doi", "pmid", "pmcid", "openalex_id", "other_persistent_identifier",
        "source_type", "discovery_search_event_ids", "candidate_review_categories",
        "peer_review_status", "party_relationship", "preliminary_relevance_flag",
        "preliminary_relevance_rationale", "venue_or_surface", "work_type",
        "provider_record_ids", "raw_payload_paths", "retraction_status",
        "discovery_only_not_screening", "assistance_mode",
    ]
    write_csv(DISCOVERY / "provisional_source_registry.csv", fields, rows)
    return rows, retrieved_before_dedup


def build_system_registry(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: dict[str, dict[str, Any]] = {}
    for canonical, aliases, categories, kind, relevance in SYSTEM_PATTERNS:
        matches = []
        for source in source_rows:
            text = normalize_text(source["title"])
            if any(normalize_text(alias) in text for alias in aliases):
                matches.append(source)
        if not matches:
            continue
        candidates[canonical] = {
            "canonical_name": canonical,
            "aliases": aliases,
            "categories": set(categories),
            "candidate_kind": kind,
            "target_level_relevance": relevance,
            "sources": matches,
            "reason": "CANONICAL_NAME_OR_ALIAS_PRESENT_IN_CAPTURED_PILOT_SOURCE",
        }

    # Retain likely relevant named frameworks/methods not covered by the alias list.
    framework_terms = ("framework", "platform", "system", "tool", "method", "model", "knowledge graph", "ontology", "standard")
    for source in source_rows:
        if source["source_type"] != "SCHOLARLY_RECORD" or source["preliminary_relevance_flag"] != "LIKELY_RELEVANT":
            continue
        title_norm = normalize_text(source["title"])
        if not any(term in title_norm for term in framework_terms):
            continue
        already = any(source in candidate["sources"] for candidate in candidates.values())
        if already:
            continue
        canonical = source["title"]
        candidates[canonical] = {
            "canonical_name": canonical,
            "aliases": [],
            "categories": set(source["candidate_review_categories"].split("|")),
            "candidate_kind": "METHOD_OR_IMPLEMENTATION_STATUS_UNRESOLVED",
            "target_level_relevance": "UNRESOLVED_FROM_DISCOVERY_METADATA",
            "sources": [source],
            "reason": "LIKELY_RELEVANT_FRAMEWORK_OR_METHOD_TITLE_RETRIEVED_IN_PILOT",
        }

    rows = []
    for canonical, candidate in candidates.items():
        sources = candidate["sources"]
        first_party = [s["provisional_source_id"] for s in sources if s["party_relationship"] == "FIRST_PARTY"]
        version_info = sorted({s["other_persistent_identifier"] for s in sources if "GITHUB:opentargets/platform-docs@" in s["other_persistent_identifier"]})
        discovery_ids = sorted({s["provisional_source_id"] for s in sources})
        rows.append({
            "provisional_system_id": stable_id("P2SYS", canonical),
            "canonical_name": canonical,
            "aliases": "|".join(candidate["aliases"]) or "NONE_RECORDED",
            "candidate_categories": "|".join(sorted(candidate["categories"])),
            "candidate_kind": candidate["candidate_kind"],
            "target_level_relevance": candidate["target_level_relevance"],
            "first_party_source_candidate_ids": "|".join(first_party) or "NONE_IDENTIFIED_IN_CAPTURED_PILOT",
            "version_or_snapshot_information": "|".join(version_info) or "NOT_ESTABLISHED_IN_DISCOVERY_METADATA",
            "discovery_evidence_source_ids": "|".join(discovery_ids),
            "discovery_search_event_ids": "|".join(sorted({eid for s in sources for eid in s["discovery_search_event_ids"].split("|")})),
            "reason_for_retaining_candidate": candidate["reason"],
            "discovery_only_no_capability_coding": "TRUE",
            "assistance_mode": ASSISTANCE_MODE,
        })
    rows.sort(key=lambda row: (row["canonical_name"].lower(), row["provisional_system_id"]))
    fields = [
        "provisional_system_id", "canonical_name", "aliases", "candidate_categories",
        "candidate_kind", "target_level_relevance", "first_party_source_candidate_ids",
        "version_or_snapshot_information", "discovery_evidence_source_ids",
        "discovery_search_event_ids", "reason_for_retaining_candidate",
        "discovery_only_no_capability_coding", "assistance_mode",
    ]
    write_csv(DISCOVERY / "provisional_system_registry.csv", fields, rows)
    return rows


def build_anchor_audit(system_rows: list[dict[str, Any]], source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    source_lookup = {row["provisional_source_id"]: row for row in source_rows}
    rows = []
    for system in system_rows:
        event_ids = set(system["discovery_search_event_ids"].split("|"))
        families = set()
        generic_events = []
        named_events = []
        first_party_events = []
        for event_id in event_ids:
            if event_id.startswith("P2E1B_OTDOC_") or event_id == "P2E1B_OT_ORIENTATION_REPOSITORY":
                first_party_events.append(event_id)
            elif event_id in {"P2E1B_PUBMED_02", "P2E1B_OPENALEX_02"}:
                named_events.append(event_id)
                families.add("QF02_OPEN_TARGETS")
            else:
                generic_events.append(event_id)
                match = re.search(r"_(\d{2})$", event_id)
                if match:
                    index = int(match.group(1)) - 1
                    if 0 <= index < len(QUERY_FAMILIES):
                        families.add(QUERY_FAMILIES[index]["id"])
        entry_basis = None
        if system["canonical_name"] == "Open Targets Platform":
            entry_basis = "PRESPECIFIED_PROJECT_BRIEF"
        elif len({f for f in families if f != "QF02_OPEN_TARGETS"}) >= 2:
            entry_basis = "REPEATED_ACROSS_INDEPENDENT_GENERIC_QUERY_FAMILIES"
        if not entry_basis:
            continue
        source_ids = system["discovery_evidence_source_ids"].split("|")
        rows.append({
            "anchor_id": stable_id("P2ANCHOR", system["provisional_system_id"]),
            "provisional_system_id": system["provisional_system_id"],
            "canonical_name": system["canonical_name"],
            "anchor_entry_basis": entry_basis,
            "entry_evidence_source_ids": "|".join(source_ids),
            "generic_search_event_ids": "|".join(sorted(generic_events)) or "NONE",
            "recovered_by_generic_search": "TRUE" if generic_events else "FALSE",
            "named_system_search_event_ids": "|".join(sorted(named_events)) or "NONE",
            "required_named_system_search": "TRUE" if named_events and not generic_events else "FALSE",
            "targeted_first_party_event_ids": "|".join(sorted(first_party_events)) or "NONE",
            "citation_chasing_status": "NOT_EXECUTED",
            "formal_recall_claimed": "FALSE",
            "diagnostic_only": "TRUE",
        })
    rows.sort(key=lambda row: row["canonical_name"].lower())
    fields = [
        "anchor_id", "provisional_system_id", "canonical_name", "anchor_entry_basis",
        "entry_evidence_source_ids", "generic_search_event_ids", "recovered_by_generic_search",
        "named_system_search_event_ids", "required_named_system_search",
        "targeted_first_party_event_ids", "citation_chasing_status",
        "formal_recall_claimed", "diagnostic_only",
    ]
    write_csv(DISCOVERY / "anchor_recovery_audit.csv", fields, rows)
    return rows


def build_query_sensitivity(search_rows: list[dict[str, Any]], source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    source_by_event: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for source in source_rows:
        for event_id in source["discovery_search_event_ids"].split("|"):
            source_by_event[event_id].append(source)
    rows = []
    for family in QUERY_FAMILIES:
        index = QUERY_FAMILIES.index(family) + 1
        event_ids = {f"P2E1B_PUBMED_{index:02d}", f"P2E1B_OPENALEX_{index:02d}"}
        events = [row for row in search_rows if row["search_event_id"] in event_ids]
        total_exposed = sum(int(row["result_count"]) for row in events if str(row["result_count"]).isdigit())
        captured = sum(int(row["captured_result_count"]) for row in events)
        unique_sources = {s["provisional_source_id"]: s for event_id in event_ids for s in source_by_event.get(event_id, [])}
        signal_count = sum(s["preliminary_relevance_flag"] in {"LIKELY_RELEVANT", "POSSIBLY_RELEVANT"} for s in unique_sources.values())
        signal_fraction = signal_count / len(unique_sources) if unique_sources else 0.0
        duplicate_fraction = 1 - (len(unique_sources) / captured) if captured else 0.0
        failure = not events or all(row["network_status"] == "FAILED" for row in events)
        if failure or not unique_sources:
            flag = "INSUFFICIENT_TO_JUDGE"
        elif signal_fraction < 0.30:
            flag = "RETRIEVAL_NOISY"
        elif total_exposed < 10:
            flag = "RETRIEVAL_NARROW"
        elif total_exposed > 5000:
            flag = "RETRIEVAL_BROAD"
        else:
            flag = "RETRIEVAL_BALANCED"
        specific_notes = []
        if family["id"] == "QF04_PROVENANCE":
            specific_notes.append("Generic workflow/laboratory lineage noise requires human review.")
        if family["id"] == "QF03_KNOWLEDGE_GRAPHS":
            specific_notes.append("Graph prediction papers may dominate over representation systems.")
        if family["id"] == "QF07_AI_TARGET_DISCOVERY":
            specific_notes.append("Predictive-method records may not expose evidence-integration semantics; marketing pages were not part of scholarly API retrieval.")
        rows.append({
            "query_family_id": family["id"],
            "protocol_categories": "|".join(family["categories"]),
            "counterexample_focus": family["focus"] if family["focus"].startswith("COUNTEREXAMPLE") else "NOT_APPLICABLE",
            "search_event_ids": "|".join(sorted(event_ids)),
            "providers_queried": "PubMed|OpenAlex",
            "source_exposed_result_count_sum": total_exposed,
            "captured_records_before_cross_event_dedup": captured,
            "unique_sources_in_family_capture": len(unique_sources),
            "discovery_signal_count": signal_count,
            "discovery_signal_fraction": f"{signal_fraction:.3f}",
            "cross_provider_or_event_duplicate_fraction": f"{duplicate_fraction:.3f}",
            "query_diagnostic": flag,
            "bounded_rationale": (
                f"First-page pilot capture only: {signal_count}/{len(unique_sources)} unique captured records had automated discovery signals; "
                f"providers exposed {total_exposed} total results. This is not recall or precision. {' '.join(specific_notes)}"
            ).strip(),
            "human_review_status": "PENDING",
            "assistance_mode": ASSISTANCE_MODE,
        })
    fields = [
        "query_family_id", "protocol_categories", "counterexample_focus", "search_event_ids",
        "providers_queried", "source_exposed_result_count_sum",
        "captured_records_before_cross_event_dedup", "unique_sources_in_family_capture",
        "discovery_signal_count", "discovery_signal_fraction",
        "cross_provider_or_event_duplicate_fraction", "query_diagnostic",
        "bounded_rationale", "human_review_status", "assistance_mode",
    ]
    write_csv(AUDIT / "query_sensitivity_audit.csv", fields, rows)
    return rows


def build_counterexample_summary(source_rows: list[dict[str, Any]], sensitivity_rows: list[dict[str, Any]]) -> None:
    lines = [
        "# P2-E1B Counterexample-Oriented Discovery Summary",
        "",
        PILOT_DISCLAIMER,
        "",
        "This audit deliberately searched for prior work that could challenge the Phase Two candidate gap. Titles listed below are discovery candidates only. Their technical capabilities have not been verified, and presence in this list is not a capability determination.",
        "",
    ]
    for audit in sensitivity_rows:
        focus = audit["counterexample_focus"]
        if focus == "NOT_APPLICABLE":
            continue
        event_ids = set(audit["search_event_ids"].split("|"))
        candidates = [
            source for source in source_rows
            if event_ids.intersection(source["discovery_search_event_ids"].split("|"))
            and source["preliminary_relevance_flag"] in {"LIKELY_RELEVANT", "POSSIBLY_RELEVANT"}
        ][:10]
        lines.extend([
            f"## {focus}",
            "",
            f"- Search events: `{audit['search_event_ids']}`",
            f"- Query diagnostic: `{audit['query_diagnostic']}`",
            f"- Candidate sources with discovery signals in the captured page: {len(candidates)} shown (maximum 10)",
            "",
        ])
        if candidates:
            for source in candidates:
                lines.append(f"- `{source['provisional_source_id']}` — {source['title']}")
        else:
            lines.append("- No source with the automated discovery signal was captured; this does not establish absence of a counterexample.")
        lines.extend(["", "Required next step: human screening and primary-material verification in later P2-E1 work; no capability inference is permitted here.", ""])
    (AUDIT / "counterexample_discovery_summary.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def build_amendments(sensitivity_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows = [{
        "issue_id": "P2E1B_AMEND_001",
        "location": "P2-E1 protocol governing-input status",
        "observed_problem": "The task brief describes the protocol, codebook, and templates as committed, but they are outside the current Git HEAD. P2-E1B froze their observed bytes without changing them.",
        "proposed_change": "Before P2-E1C, establish a reviewed immutable Git identity for the governing inputs or explicitly designate a content-hash freeze independent of Git.",
        "affects_eligibility": "NO",
        "affects_search_denominator": "NO",
        "affects_capability_semantics": "NO",
        "recommendation": "CLARIFICATION",
    }, {
        "issue_id": "P2E1B_AMEND_002",
        "location": "P2-E1 protocol Section 6 and Section 7.1",
        "observed_problem": "The concept blocks do not yet contain frozen source-specific PubMed fielding or OpenAlex free-text translation rules.",
        "proposed_change": "After human review of this pilot, add an approved source-specific production-query appendix and record any query changes as a protocol amendment.",
        "affects_eligibility": "NO",
        "affects_search_denominator": "YES",
        "affects_capability_semantics": "NO",
        "recommendation": "MINOR_AMENDMENT",
    }, {
        "issue_id": "P2E1B_AMEND_003",
        "location": "P2-E1 protocol Section 7.1",
        "observed_problem": "OpenAlex full-text search does not implement PubMed field tags or identical Boolean semantics, so paired queries are concept translations rather than syntactic replicas.",
        "proposed_change": "State explicitly that cross-database translations preserve concepts but may use provider-specific retrieval semantics; peer-check each production translation.",
        "affects_eligibility": "NO",
        "affects_search_denominator": "YES",
        "affects_capability_semantics": "NO",
        "recommendation": "CLARIFICATION",
    }]
    noisy = [row["query_family_id"] for row in sensitivity_rows if row["query_diagnostic"] == "RETRIEVAL_NOISY"]
    broad = [row["query_family_id"] for row in sensitivity_rows if row["query_diagnostic"] == "RETRIEVAL_BROAD"]
    if noisy or broad:
        rows.append({
            "issue_id": "P2E1B_AMEND_004",
            "location": "P2-E1 protocol Section 6 search concepts",
        "observed_problem": f"Automated first-page diagnostics flagged noisy families {'/'.join(noisy) or 'NONE'} and broad families {'/'.join(broad) or 'NONE'}; these labels require human confirmation.",
            "proposed_change": "Have a human review stratified result samples and approve narrower or split production queries only where the captured records demonstrate a reproducible blind spot or noise mechanism.",
            "affects_eligibility": "NO",
            "affects_search_denominator": "YES",
            "affects_capability_semantics": "NO",
            "recommendation": "MINOR_AMENDMENT",
        })
    lines = [
        "# P2-E1B Protocol Amendment Candidates",
        "",
        PILOT_DISCLAIMER,
        "",
        "These are proposals only. No governing protocol, codebook, or template has been changed.",
        "",
        "| Issue | Location | Observed pilot problem | Proposed change | Eligibility | Search denominator | Capability semantics | Recommendation |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        cells = [row[key].replace("|", "/") for key in ("issue_id", "location", "observed_problem", "proposed_change", "affects_eligibility", "affects_search_denominator", "affects_capability_semantics", "recommendation")]
        lines.append("| " + " | ".join(cells) + " |")
    (AUDIT / "protocol_amendment_candidates.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rows


def build_pilot_summary(
    manifest: dict[str, Any], source_rows: list[dict[str, Any]], system_rows: list[dict[str, Any]],
    anchors: list[dict[str, Any]], sensitivity: list[dict[str, Any]], before_dedup: int,
) -> None:
    category_counts = Counter()
    for source in source_rows:
        for category in source["candidate_review_categories"].split("|"):
            category_counts[category] += 1
    scholarly_events = [e for e in manifest["events"] if e["stream"] == "SCHOLARLY_DISCOVERY"]
    ot_docs = [s for s in source_rows if s["source_type"] == "OFFICIAL_FIRST_PARTY_DOCUMENTATION"]
    lines = [
        "# P2-E1B Search Pilot Summary",
        "",
        PILOT_DISCLAIMER,
        "",
        "## Pilot scope",
        "",
        f"- Scholarly sources queried: PubMed (NCBI) and OpenAlex (OurResearch)",
        f"- Scholarly pilot search events: {len(scholarly_events)}",
        f"- Candidate records captured before cross-event deduplication: {before_dedup}",
        f"- Provisional unique source records including first-party orientation materials: {len(source_rows)}",
        f"- Provisional systems/methods: {len(system_rows)}",
        f"- Open Targets first-party materials registered: {len(ot_docs)}",
        f"- Anchors: {len(anchors)}",
        "",
        "Captured scholarly records are first-page samples, not all provider-exposed results. Automated preliminary relevance labels are discovery triage, not screening decisions.",
        "",
        "## Candidate sources by protocol category",
        "",
        "| Category | Provisional source count |",
        "|---|---:|",
    ]
    for category, label in CATEGORIES.items():
        lines.append(f"| `{category}` — {label} | {category_counts[category]} |")
    lines.extend(["", "## Query-family diagnostics", "", "| Query family | Diagnostic | Exposed total across providers | Unique captured sources |", "|---|---|---:|---:|"])
    for row in sensitivity:
        lines.append(f"| `{row['query_family_id']}` | `{row['query_diagnostic']}` | {row['source_exposed_result_count_sum']} | {row['unique_sources_in_family_capture']} |")
    lines.extend([
        "",
        "## Human-review boundary",
        "",
        "Search translation, metadata normalization, preliminary relevance labelling, and candidate extraction were AI-assisted. No second human reviewer was fabricated. Human peer checking, formal dual screening, and adjudication remain pending for P2-E1C.",
        "",
        "## Interpretation boundary",
        "",
        "This pilot assesses retrieval behavior only. Candidate presence does not verify any capability; non-retrieval does not establish absence. No system ranking, capability matrix, novelty statement, or universal gap conclusion is produced.",
    ])
    (AUDIT / "pilot_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def verify_frozen_inputs() -> tuple[bool, list[str]]:
    errors = []
    for relative, expected in FROZEN_INPUT_HASHES.items():
        path = ROOT / relative
        if not path.exists():
            errors.append(f"missing frozen input: {relative}")
        elif sha256(path) != expected:
            errors.append(f"frozen input hash mismatch: {relative}")
    return not errors, errors


def core_paths() -> list[Path]:
    return [
        SEARCH / "pilot_search_log.csv",
        DISCOVERY / "provisional_source_registry.csv",
        DISCOVERY / "provisional_system_registry.csv",
        DISCOVERY / "anchor_recovery_audit.csv",
        AUDIT / "query_sensitivity_audit.csv",
        AUDIT / "counterexample_discovery_summary.md",
        AUDIT / "protocol_amendment_candidates.md",
        AUDIT / "pilot_summary.md",
    ]


def build_core(manifest: dict[str, Any]) -> dict[str, Any]:
    search_rows = build_search_log(manifest)
    source_rows, before_dedup = build_source_registry(manifest)
    system_rows = build_system_registry(source_rows)
    anchors = build_anchor_audit(system_rows, source_rows)
    sensitivity = build_query_sensitivity(search_rows, source_rows)
    build_counterexample_summary(source_rows, sensitivity)
    amendments = build_amendments(sensitivity)
    build_pilot_summary(manifest, source_rows, system_rows, anchors, sensitivity, before_dedup)
    return {
        "search_rows": search_rows,
        "source_rows": source_rows,
        "system_rows": system_rows,
        "anchors": anchors,
        "sensitivity": sensitivity,
        "amendments": amendments,
        "before_dedup": before_dedup,
    }


def validate(manifest: dict[str, Any], built: dict[str, Any], repeat_ok: bool) -> list[dict[str, str]]:
    search_rows = built["search_rows"]
    source_rows = built["source_rows"]
    system_rows = built["system_rows"]
    source_ids = {row["provisional_source_id"] for row in source_rows}
    event_ids = {row["search_event_id"] for row in search_rows}
    checks: list[tuple[str, bool, str]] = []
    frozen_ok, frozen_errors = verify_frozen_inputs()
    checks.append(("frozen_governing_inputs", frozen_ok, "; ".join(frozen_errors) or "All nine observed governing-input hashes match."))
    checks.append(("unique_search_event_ids", len(event_ids) == len(search_rows), f"{len(search_rows)} rows; {len(event_ids)} unique IDs."))
    checks.append(("all_searches_labelled_pilot", all(row["search_role"] == "PILOT_SEARCH" for row in search_rows), "All search roles must be PILOT_SEARCH."))
    checks.append(("exact_queries_preserved", all(row["exact_query"].strip() for row in search_rows), "No blank query/capture specification."))
    checks.append(("retrieval_metadata_complete", all(row["source_name"] and row["source_provider"] and row["executed_at"] and row["timezone"] and row["pagination_completeness_boundary"] for row in search_rows), "Source/provider/time/timezone/boundary required."))
    checks.append(("result_counts_recorded", all(str(row["result_count"]).strip() for row in search_rows), "Source count or explicit unavailable state retained."))
    payload_ok = all((ROOT / p["payload_path"]).exists() and sha256(ROOT / p["payload_path"]) == p["sha256"] for p in manifest["payloads"])
    checks.append(("raw_payload_integrity", payload_ok, f"{len(manifest['payloads'])} retained payloads checked."))
    source_fk = all(set(row["discovery_search_event_ids"].split("|")).issubset(event_ids) for row in source_rows)
    checks.append(("source_event_foreign_keys", source_fk, f"{len(source_rows)} provisional sources resolve to pilot events."))
    system_fk = all(set(row["discovery_evidence_source_ids"].split("|")).issubset(source_ids) for row in system_rows)
    checks.append(("system_source_foreign_keys", system_fk and bool(system_rows), f"{len(system_rows)} provisional systems/methods resolve to source candidates."))
    ot_roles = {e.get("orientation_role") for e in manifest["events"] if str(e.get("network_status", "")).startswith("SUCCESS")}
    required_ot = set(OT_DOC_PATHS.values())
    checks.append(("open_targets_orientation_registered", required_ot.issubset(ot_roles), f"{len(required_ot & ot_roles)}/{len(required_ot)} required orientation roles captured."))
    counter_focus = {row["counterexample_focus"] for row in search_rows if row["network_status"] != "FAILED"}
    required_counter = {
        "COUNTEREXAMPLE_DEPENDENCY", "COUNTEREXAMPLE_MISSINGNESS",
        "COUNTEREXAMPLE_PROVENANCE_THROUGH_AGGREGATION", "COUNTEREXAMPLE_CLAIM_EVIDENCE_BOUNDARY",
        "COUNTEREXAMPLE_CONFLICT_PRESERVATION", "COUNTEREXAMPLE_AI_OUTPUT_SOURCE_GROUNDING",
    }
    checks.append(("counterexample_searches_executed", required_counter.issubset(counter_focus), f"{len(required_counter & counter_focus)}/{len(required_counter)} required focuses executed."))
    structured_fields = set().union(*(set(row) for row in source_rows + system_rows)) if source_rows or system_rows else set()
    capability_state_fields = {
        field for field in structured_fields
        if field in {"final_state", "reviewer_1_state", "reviewer_2_state", "capability_state"}
        or field.startswith("dimension_")
    }
    capability_states_absent = not capability_state_fields
    checks.append(("no_capability_matrix_states", capability_states_absent, "Discovery registries contain no capability-state coding."))
    prelim_allowed = {"LIKELY_RELEVANT", "POSSIBLY_RELEVANT", "LIKELY_OUT_OF_SCOPE", "UNRESOLVED"}
    checks.append(("discovery_labels_only", all(row["preliminary_relevance_flag"] in prelim_allowed and row["discovery_only_not_screening"] == "TRUE" for row in source_rows), "No formal inclusion/exclusion decisions."))
    checks.append(("human_identity_boundary", all(row["peer_checker_id"] == "PENDING" and row["assistance_mode"] == ASSISTANCE_MODE for row in search_rows), "AI assistance distinguished; second human not fabricated."))
    checks.append(("offline_reconstruction_deterministic", repeat_ok, "Two consecutive offline core builds produced identical SHA256 values."))
    checks.append(("future_network_identity_not_claimed", manifest.get("future_network_byte_identity_claimed") is False, "Mutable future retrieval is not claimed byte-identical."))
    checks.append(("no_formal_denominator_claim", manifest.get("captured_page_is_formal_denominator") is False, PILOT_DISCLAIMER))
    return [{"check": name, "result": "PASS" if ok else "FAIL", "detail": detail} for name, ok, detail in checks]


def write_validation(checks: list[dict[str, str]]) -> None:
    overall = all(row["result"] == "PASS" for row in checks)
    lines = [
        "# P2-E1B Validation Report", "", PILOT_DISCLAIMER, "",
        f"Overall validation: **{'PASS' if overall else 'FAIL'}**", "",
        "| Check | Result | Detail |", "|---|---|---|",
    ]
    for row in checks:
        lines.append(f"| `{row['check']}` | **{row['result']}** | {row['detail'].replace('|', '/')} |")
    lines.extend([
        "", "## Interpretation boundary", "",
        "Validation establishes retrieval-accounting and deterministic-transformation integrity only. It does not validate candidate relevance, system capabilities, a related-work gap, novelty, or comparative system quality.",
    ])
    (AUDIT / "validation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_session(manifest: dict[str, Any], checks: list[dict[str, str]]) -> None:
    git_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    lines = [
        f"pilot_id={manifest['pilot_id']}",
        f"generator_version={GENERATOR_VERSION}",
        f"python_version={platform.python_version()}",
        f"platform={platform.platform()}",
        f"git_head={git_head}",
        f"retrieval_started_at_utc={manifest['retrieval_started_at_utc']}",
        f"retrieval_completed_at_utc={manifest['retrieval_completed_at_utc']}",
        "bibliographic_source=PubMed/NCBI",
        "multidisciplinary_source=OpenAlex/OurResearch",
        "all_search_roles=PILOT_SEARCH",
        "assistance_mode=AI_ASSISTED_DISCOVERY",
        "human_reviewer_2=PENDING",
        "peer_checker=PENDING",
        "network_retrieval_mutable=TRUE",
        "future_network_byte_identity_claimed=FALSE",
        "offline_transformation_deterministic=TRUE",
        f"validation_overall={'PASS' if all(c['result'] == 'PASS' for c in checks) else 'FAIL'}",
        f"frozen_input_hashes={json.dumps(FROZEN_INPUT_HASHES, sort_keys=True)}",
        f"pilot_disclaimer={PILOT_DISCLAIMER}",
    ]
    (AUDIT / "session_info.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def completion_report(manifest: dict[str, Any], built: dict[str, Any], checks: list[dict[str, str]]) -> str:
    search_rows = built["search_rows"]
    scholarly = [row for row in search_rows if row["stream"] == "SCHOLARLY_DISCOVERY"]
    category_counts = Counter()
    for source in built["source_rows"]:
        for category in source["candidate_review_categories"].split("|"):
            category_counts[category] += 1
    sensitivity_counts = Counter(row["query_diagnostic"] for row in built["sensitivity"])
    amendment_counts = Counter(row["recommendation"] for row in built["amendments"])
    ot_docs = sum(row["source_type"] == "OFFICIAL_FIRST_PARTY_DOCUMENTATION" for row in built["source_rows"])
    anchors_generic = sum(row["recovered_by_generic_search"] == "TRUE" for row in built["anchors"])
    anchors_named = sum(row["required_named_system_search"] == "TRUE" for row in built["anchors"])
    status_counts = Counter(row["network_status"] for row in search_rows)
    created = [
        "analysis/P2_E1B_run_search_strategy_pilot.py",
        "docs/phase_two/p2_e1_search_strategy_pilot_plan_v0.1.md",
        "outputs/phase_two/p2_e1_pilot_v0.1/search/pilot_search_log.csv",
        "outputs/phase_two/p2_e1_pilot_v0.1/search/raw_retrieval/",
        "outputs/phase_two/p2_e1_pilot_v0.1/search/retrieval_manifest.json",
        "outputs/phase_two/p2_e1_pilot_v0.1/discovery/provisional_source_registry.csv",
        "outputs/phase_two/p2_e1_pilot_v0.1/discovery/provisional_system_registry.csv",
        "outputs/phase_two/p2_e1_pilot_v0.1/discovery/anchor_recovery_audit.csv",
        "outputs/phase_two/p2_e1_pilot_v0.1/audit/query_sensitivity_audit.csv",
        "outputs/phase_two/p2_e1_pilot_v0.1/audit/counterexample_discovery_summary.md",
        "outputs/phase_two/p2_e1_pilot_v0.1/audit/protocol_amendment_candidates.md",
        "outputs/phase_two/p2_e1_pilot_v0.1/audit/pilot_summary.md",
        "outputs/phase_two/p2_e1_pilot_v0.1/audit/validation_report.md",
        "outputs/phase_two/p2_e1_pilot_v0.1/audit/session_info.txt",
    ]
    lines = [
        "P2-E1B COMPLETION REPORT",
        "bibliographic/citation sources queried: PubMed (NCBI); OpenAlex (OurResearch)",
        f"number of pilot search events: {len(search_rows)} ({len(scholarly)} scholarly; {len(search_rows) - len(scholarly)} first-party orientation)",
        f"candidate sources retrieved before deduplication: {built['before_dedup']}",
        f"provisional unique candidate sources: {len(built['source_rows'])}",
        f"provisional systems/methods discovered: {len(built['system_rows'])}",
        "candidates by protocol category: " + "; ".join(f"{key}={category_counts[key]}" for key in CATEGORIES),
        f"Open Targets first-party materials registered: {ot_docs}",
        f"counterexample-oriented searches executed: {sum(row['counterexample_focus'] != 'NOT_APPLICABLE' and row['network_status'] != 'FAILED' for row in scholarly)}",
        f"anchors registered: {len(built['anchors'])}",
        f"anchors recovered by generic search: {anchors_generic}",
        f"anchors requiring named-system search: {anchors_named}",
        "query families flagged broad/balanced/narrow/noisy: " + "; ".join(f"{key}={sensitivity_counts[key]}" for key in ["RETRIEVAL_BROAD", "RETRIEVAL_BALANCED", "RETRIEVAL_NARROW", "RETRIEVAL_NOISY", "INSUFFICIENT_TO_JUDGE"]),
        "protocol amendment candidates by severity: " + "; ".join(f"{key}={amendment_counts[key]}" for key in ["NO_CHANGE", "CLARIFICATION", "MINOR_AMENDMENT", "MAJOR_AMENDMENT"]),
        "network retrieval status: " + "; ".join(f"{key}={status_counts[key]}" for key in sorted(status_counts)),
        f"validation: {'PASS' if all(c['result'] == 'PASS' for c in checks) else 'FAIL'}",
        "files created:",
    ]
    lines.extend(f"  - {path}" for path in created)
    lines.extend([
        "files modified:",
        "  - NONE (frozen Phase One and P2-E1 governing inputs unchanged)",
        PILOT_DISCLAIMER,
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true", help="Require and reuse frozen raw payloads; do not access the network.")
    parser.add_argument("--repair-open-targets", action="store_true", help="Retry failed Open Targets docs through immutable GitHub blob IDs and retain original failures.")
    parser.add_argument("--repair-pubmed-event", help="Retry one failed PubMed event using its exact preserved query and retain the original failure.")
    parser.add_argument("--add-query-family", help="Append one newly configured query family without rewriting prior event history.")
    parser.add_argument("--correct-manifest-metadata", action="store_true", help="Correct the logged reason label for appended query families without changing payload or query bytes.")
    args = parser.parse_args()

    frozen_ok, errors = verify_frozen_inputs()
    if not frozen_ok:
        raise SystemExit("Frozen governing-input validation failed: " + "; ".join(errors))
    active_modes = sum(bool(value) for value in (args.offline, args.repair_open_targets, args.repair_pubmed_event, args.add_query_family, args.correct_manifest_metadata))
    if active_modes > 1:
        raise SystemExit("--offline, repair modes, and --add-query-family are mutually exclusive.")
    if args.offline and not MANIFEST.exists():
        raise SystemExit("Offline mode requires an existing frozen retrieval manifest.")
    if args.repair_open_targets:
        repair_open_targets_orientation()
    elif args.repair_pubmed_event:
        repair_pubmed_event(args.repair_pubmed_event)
    elif args.add_query_family:
        add_query_family(args.add_query_family)
    elif args.correct_manifest_metadata:
        correct_manifest_metadata()
    elif not args.offline:
        retrieve_payloads()
    if not MANIFEST.exists():
        raise SystemExit("Retrieval manifest is unavailable.")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    first = build_core(manifest)
    first_hashes = {str(path.relative_to(ROOT)): sha256(path) for path in core_paths()}
    second = build_core(manifest)
    second_hashes = {str(path.relative_to(ROOT)): sha256(path) for path in core_paths()}
    repeat_ok = first_hashes == second_hashes
    checks = validate(manifest, second, repeat_ok)
    write_validation(checks)
    write_session(manifest, checks)
    report = completion_report(manifest, second, checks)
    print(report)
    return 0 if all(check["result"] == "PASS" for check in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
