# P2-E1B Search Pilot Summary

Pilot results are not the formal P2-E1 screening denominator and do not establish a related-work gap.

## Pilot scope

- Scholarly sources queried: PubMed (NCBI) and OpenAlex (OurResearch)
- Scholarly pilot search events: 28
- Candidate records captured before cross-event deduplication: 824
- Provisional unique source records including first-party orientation materials: 769
- Provisional systems/methods: 44
- Open Targets first-party materials registered: 11
- Anchors: 10

Captured scholarly records are first-page samples, not all provider-exposed results. Automated preliminary relevance labels are discovery triage, not screening decisions.

## Candidate sources by protocol category

| Category | Provisional source count |
|---|---:|
| `CAT_01` — target_evidence_integration_target_prioritization | 430 |
| `CAT_02` — open_targets | 54 |
| `CAT_03` — biomedical_drug_target_knowledge_graphs | 166 |
| `CAT_04` — provenance_systems_standards | 171 |
| `CAT_05` — evidence_synthesis_assessment_systems | 398 |
| `CAT_06` — missingness_uncertainty_conflict_dependence_methods | 343 |
| `CAT_07` — ai_assisted_target_discovery | 173 |

## Query-family diagnostics

| Query family | Diagnostic | Exposed total across providers | Unique captured sources |
|---|---|---:|---:|
| `QF01_TARGET_INTEGRATION` | `RETRIEVAL_BROAD` | 40862 | 59 |
| `QF02_OPEN_TARGETS` | `RETRIEVAL_BALANCED` | 2272 | 43 |
| `QF03_KNOWLEDGE_GRAPHS` | `RETRIEVAL_BROAD` | 22363 | 57 |
| `QF04_PROVENANCE` | `RETRIEVAL_BROAD` | 1617655 | 60 |
| `QF05_EVIDENCE_SYNTHESIS` | `RETRIEVAL_BROAD` | 2795331 | 60 |
| `QF06_MISSING_UNCERTAIN_DEPENDENT` | `RETRIEVAL_BROAD` | 4426826 | 59 |
| `QF07_AI_TARGET_DISCOVERY` | `RETRIEVAL_BROAD` | 12894 | 59 |
| `QF08_COUNTER_DEPENDENCY` | `RETRIEVAL_BROAD` | 11315 | 52 |
| `QF09_COUNTER_MISSINGNESS` | `RETRIEVAL_BROAD` | 3203194 | 59 |
| `QF10_COUNTER_PROVENANCE_AGGREGATION` | `RETRIEVAL_BROAD` | 559415 | 55 |
| `QF11_COUNTER_CLAIM_EVIDENCE` | `RETRIEVAL_BROAD` | 1195178 | 60 |
| `QF12_CLAIM_BOUNDARY_VARIANTS` | `RETRIEVAL_BROAD` | 72245 | 57 |
| `QF13_COUNTER_CONFLICT_PRESERVATION` | `RETRIEVAL_BROAD` | 25026 | 59 |
| `QF14_COUNTER_AI_GROUNDING` | `RETRIEVAL_BROAD` | 16136 | 56 |

## Human-review boundary

Search translation, metadata normalization, preliminary relevance labelling, and candidate extraction were AI-assisted. No second human reviewer was fabricated. Human peer checking, formal dual screening, and adjudication remain pending for P2-E1C.

## Interpretation boundary

This pilot assesses retrieval behavior only. Candidate presence does not verify any capability; non-retrieval does not establish absence. No system ranking, capability matrix, novelty statement, or universal gap conclusion is produced.
