# P2-E1B Search Strategy Pilot Plan v0.1

**Project:** LUAD Target Evidence Dossier  
**Workstream:** P2-E1B — Search Strategy Pilot and Discovery-Universe Construction  
**Version:** v0.1  
**Date:** 3 September 2026  
**Status:** Operational pilot plan; not a production search protocol or related-work finding

## 1. Purpose and governing boundary

P2-E1B tests whether the search concepts in the frozen P2-E1 protocol retrieve a broad and balanced discovery set across its seven literature categories. It constructs provisional source and system/method universes, diagnoses query behavior, orients later reviewers to current Open Targets first-party materials, and records candidate protocol amendments.

The governing inputs are read-only:

- `docs/phase_two/p2_e1_related_work_protocol_v0.1.md`;
- `docs/phase_two/p2_e1_comparison_framework_v0.1.md`; and
- the seven files under `docs/phase_two/p2_e1_templates/`.

Their SHA256 values are recorded by the pilot session metadata and checked during every run. Although these inputs are currently outside the repository's committed `HEAD`, P2-E1B treats their observed starting bytes as frozen. Their uncommitted state is documented as a governance issue, not silently corrected.

Every retrieval in this task is labelled `PILOT_SEARCH`. Pilot results are not the formal P2-E1 screening denominator and do not establish a related-work gap.

## 2. Pilot sources

### 2.1 Biomedical bibliographic source

PubMed is queried through the NCBI E-utilities API. Each event captures the exact translated query, ESearch response, returned total count, first-page PMID boundary, and ESummary metadata for the captured PMIDs.

### 2.2 Multidisciplinary scholarly source

OpenAlex is queried through its public Works API. It is treated as a multidisciplinary scholarly metadata source, not as a search-engine substitute. Each event captures the exact search text, date filter, returned total count, and first page of work metadata.

### 2.3 Targeted first-party orientation

After Open Targets is identified as the protocol-prespecified candidate, the pilot captures the official `opentargets/platform-docs` repository commit and tree, then retrieves selected documentation files by immutable commit SHA. The selection covers documentation landing/data model, data access, GraphQL, datasets/exports, evidence, associations/scoring, releases, citation/publications, and relevant user-interface evidence/association surfaces.

This orientation registers materials only. It does not code any of the 29 capability dimensions or make a gap claim.

## 3. Query families

Seven paired PubMed/OpenAlex discovery families implement the protocol categories:

1. target-evidence integration and target prioritization;
2. Open Targets;
3. biomedical or drug-target knowledge graphs;
4. provenance systems and standards;
5. evidence-synthesis and evidence-assessment systems;
6. missingness, uncertainty, conflict, and dependence methods; and
7. AI-assisted target discovery.

Seven additional paired counterexample families deliberately seek:

- explicit dependence, shared-dataset, cohort-overlap, reuse, or duplicate-evidence handling;
- structured missingness and coverage distinctions;
- structured provenance retained through aggregation; and
- claim–evidence graphs; and
- the requested claim-boundary variants: evidence interpretation, evidence grading, strength of evidence, causal-inference boundary, association versus causality, and clinical translation;
- conflict-preserving evidence synthesis; and
- AI output-to-source grounding, citation, attribution, or traceability.

The exact source-specific translations are embedded in the generator and serialized verbatim in `pilot_search_log.csv`. The pilot captures only the first 30 results ordered by each provider's relevance mechanism. The exposed total is retained separately. No captured first page is described as exhaustive.

## 4. Mutable retrieval and frozen transformation

Network retrieval occurs once per output directory. Every retained payload has a source URL, timestamp, byte size, and SHA256 in `retrieval_manifest.json`. Retrieval failures are retained as manifest records rather than erased. Mutable future responses are not expected to be byte-identical.

After capture, source normalization, deduplication, candidate labelling, system discovery, anchor auditing, and report generation operate only on frozen local payloads. Re-running in offline mode must reproduce the deterministic derived artifacts byte for byte.

## 5. Discovery-only labels

Sources receive one preliminary relevance flag:

- `LIKELY_RELEVANT`;
- `POSSIBLY_RELEVANT`;
- `LIKELY_OUT_OF_SCOPE`; or
- `UNRESOLVED`.

These flags are automated discovery triage to make the pilot inspectable. They are not inclusion/exclusion decisions and must not enter the production screening ledger.

Systems and methods are retained when a configured canonical name/alias occurs in a captured source or when a likely relevant framework/method paper is retrieved. Each provisional system row links to at least one provisional source and states why it was retained. No capability state vocabulary is allowed in the provisional registries.

## 6. Query sensitivity audit

Each query family is assigned one descriptive diagnostic:

- `RETRIEVAL_BROAD`;
- `RETRIEVAL_BALANCED`;
- `RETRIEVAL_NARROW`;
- `RETRIEVAL_NOISY`; or
- `INSUFFICIENT_TO_JUDGE`.

The assignment uses exposed result count, captured-page keyword relevance, redundancy after deduplication, and family-specific noise signals. These are pilot diagnostics, not sensitivity, recall, precision, or quality estimates.

## 7. Anchor recovery

Open Targets is an anchor because the project brief prespecified it. Other candidate anchors enter only if they are recovered across at least two independent generic query families or are identified through a retrieved review/framework source. The audit records whether each anchor appeared in a generic search, the named Open Targets search, targeted first-party orientation, or citation-chasing route.

No formal recall estimate is calculated. Citation chasing is not executed in this pilot unless explicitly recorded; a pending route remains `NOT_EXECUTED`.

## 8. Human review boundary

The pilot records `AI_ASSISTED_DISCOVERY` for automated search translation, metadata triage, and registry construction. `reviewer_2_id` and `peer_checker_id` remain `PENDING` unless a real human identity is supplied. The generator and Codex are not represented as independent human reviewers. Formal dual screening is deferred to P2-E1C.

## 9. Validation and completion

The generator checks identifier uniqueness, exact query retention, pilot labels, timestamps/timezones, result-count and pagination fields, payload hashes, registry foreign keys, Open Targets orientation coverage, all four required counterexample families, prohibited capability-state vocabulary, absence of screening decisions, prohibited novelty/ranking language, frozen governing-input hashes, and repeatable offline derivation.

Outputs are written only under:

- `analysis/P2_E1B_run_search_strategy_pilot.py`;
- this plan; and
- `outputs/phase_two/p2_e1_pilot_v0.1/`.

No Phase One artifact, frozen P2-E1 input, Git commit, or remote repository is modified.
