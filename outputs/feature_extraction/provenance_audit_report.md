# Task #026-B — Provenance Artifact Audit Report

## 1. Audit scope

This independent structural audit evaluated the existing Task #026 transcriptomic feature and provenance artifacts against the frozen Task #012 and Task #014 evidence lineage. It did not modify or regenerate Task #026 artifacts, execute Task #025 state rules, create profiles, score or rank genes, select targets, or make biological or therapeutic interpretations.

The audit treated `EnsemblID` as the immutable entity key. Gene symbols were not used for joins.

## 2. Input artifact hashes

| Artifact | SHA256 |
|---|---|
| `outputs/feature_extraction/transcriptomic_features.csv` | `4014469439ff14d27c451a356cf7711daa7a5331c58326eced2cf96edb298844` |
| `outputs/feature_extraction/feature_dictionary.csv` | `d3ffd865251674eef14c5f79c8651363a0c1497ef2d5e652a2744fb31f326abd` |
| `outputs/feature_extraction/feature_provenance_registry.csv` | `68ba8096563358b539360963da7d2856fcb0f888673da9989741b95549f3b246` |
| `outputs/feature_extraction/extraction_manifest.json` | `7d62eaf07d38f64e35e395a3f33367b66f7803ab6710e1fccd507eb11840e944` |
| `outputs/feature_extraction/extraction_summary.md` | `8b99394ff7bb959987332a96ddccb33b32a2c4259f1fdf11662d3af6242e2949` |
| `outputs/integrated_registry/integrated_target_registry.csv` | `0587fc6901267b18c8144644571f89ac2cc46053b57ea5def4093795fdbc4c26` |
| `outputs/evidence_claim_architecture/evidence_claim_registry.csv` | `0d963a4c5c8f9586f81369e33df0a2b7e57bb37ac8ceab4ce54498baf2351a66` |
| `outputs/evidence_claim_architecture/evidence_record_registry.csv` | `76ec5056fb4e468176073073532204d231765d4f0cd70dbb6cfe4ad8bf752343` |
| `outputs/evidence_claim_architecture/source_entity_registry.csv` | `1b1379066226b5f69b626fe4a97628f7b6da6e585515aa8609218eef65bf8056` |
| `outputs/evidence_claim_architecture/evidence_dependency_graph.csv` | `011839f10c48e197f9f1c0e2262565e562d3a2cf53dd0936f21ddcb4ed5c2256` |

The three core Task #026 output hashes agree exactly with `extraction_manifest.json`. This audit did not regenerate features; deterministic regeneration remains documented by the frozen Task #026 manifest and session record.

## 3. Validation results and failure counts

| Audit check | Observed | Expected | Status |
|---|---:|---:|---|
| Provenance rows | 1,036,210 | 1,036,210 | PASS |
| Unique feature-value IDs | 651,332 | 29,606 × 22 = 651,332 | PASS |
| Feature IDs with multiple record links | 384,878 | See cardinality clarification | REVIEW |
| Duplicate `(feature_id, evidence_record_id)` links | 0 | 0 | PASS |
| Feature values without provenance | 0 | 0 | PASS |
| Missing required provenance-role links | 0 | 0 | PASS |
| Broken feature links | 0 | 0 | PASS |
| Broken claim links | 0 | 0 | PASS |
| Broken evidence-record links | 0 | 0 | PASS |
| Broken source links | 0 | 0 | PASS |
| Invalid extraction-rule links | 0 | 0 | PASS |
| Dependency conflicts | 0 | 0 | PASS |
| Independence violations | 0 | 0 | PASS |
| Missingness violations | 0 | 0 | PASS |
| Manifest core-hash identity failures | 0 | 0 | PASS |
| Forbidden aggregation fields | 0 | 0 | PASS |

## 4. Artifact integrity and feature coverage

All required files exist and the provenance schema is exactly:

`feature_id → EnsemblID → feature_name → claim_id → evidence_record_id → source_id → artifact_id → dependency_id → feature_missingness_status → extraction_rule_id → extractor_version`

The feature table contains 29,606 unique EnsemblIDs and the dictionary defines 22 features, giving 651,332 distinct gene–feature values. Every one has explicit provenance. The audit found no missing feature provenance and no missing expected primary or robustness record link.

### Cardinality clarification

`feature_id` identifies one normalized feature value for one EnsemblID; it is not the row identifier of the provenance link table. Therefore, a feature that depends on both `TRANSCRIPT_PRIMARY` and `TRANSCRIPT_ROBUSTNESS` correctly appears on two provenance rows with the same `feature_id` and different `evidence_record_id` values.

- 266,454 feature IDs have one evidence-record link: 9 single-record features × 29,606 genes.
- 384,878 feature IDs have two evidence-record links: 13 multi-record features × 29,606 genes.
- These second links account for 384,878 additional provenance rows.
- Duplicate composite `(feature_id, evidence_record_id)` links: **0**.

Under a literal requirement that `feature_id` itself be unique in every provenance row, the observed count is not zero. Under the Task #026 explicit many-to-one lineage model, this repetition is required rather than erroneous duplication. Governance documentation should formally declare `(feature_id, evidence_record_id)` as the provenance-link key, or introduce a separate unique `provenance_link_id` in a future version. No Task #026 artifact was changed in this audit.

## 5. Foreign-key and extraction-rule lineage

Every provenance row resolved through the complete chain:

`feature_id → EnsemblID → claim_id → evidence_record_id → source_id`

The independently reconstructed deterministic feature IDs matched all rows. Claim IDs resolved to transcriptomic claims for the same EnsemblID; record IDs resolved to the stated claim and source; and source IDs resolved to the frozen Task #014 source registry.

Every `feature_name`, `extraction_rule_id`, and `extractor_version` matched `feature_dictionary.csv`. Invalid rule links: **0**.

## 6. Dependency and evidence-inflation audit

The frozen Task #014 graph contains 29,606 transcriptomic dependency edges. Every audited multi-record feature points to a relationship with:

- relationship: `SHARED_DATASET`;
- dependency level: `DEPENDENT`.

No primary/robustness pair was labelled `INDEPENDENT`. No aggregation score, rank, priority, recommendation, target selection, or therapeutic-direction field exists in the feature table. Evidence-record counts remain audit metadata and are not interpreted as evidence strength.

Dependency conflicts: **0**. Independence violations: **0**.

## 7. Missingness audit

The controlled vocabulary remains:

- `OBSERVED`
- `NOT_FOUND`
- `NOT_QUERIED`
- `NOT_APPLICABLE`
- `UNKNOWN`

All 59,212 frozen transcriptomic source records are `OBSERVED`, and all 1,036,210 feature provenance links therefore correctly carry `feature_missingness_status=OBSERVED`. No invalid state or conversion to negative biological evidence was found.

Because this frozen transcriptomic corpus contains only observed records, it does not empirically exercise feature propagation for `NOT_FOUND`, `NOT_QUERIED`, `NOT_APPLICABLE`, or `UNKNOWN`. Their distinct definitions are preserved in the feature dictionary, but future non-observed fixtures are still needed before those runtime paths can be governance-validated.

## 8. Scientific interpretation boundaries

This audit verifies artifact structure and traceability only. It does not establish target causality, importance, efficacy, safety, actionability, clinical relevance, therapeutic direction, or target quality. Multiple records linked to one feature are dependent lineage records, not independent votes. Missing evidence must remain distinct from negative evidence.

## 9. Governance conclusion and unresolved issues

The provenance artifact is **scientifically acceptable for governance review with one explicit schema clarification**. All lineage, coverage, rule, dependency, inflation, missingness, and hash checks pass.

It is not a clean zero-issue release audit under the literal statement that duplicate `feature_id` values must equal zero, because the current many-to-one schema deliberately reuses a feature-value ID across distinct evidence-record links. Governance review must freeze the provenance-link primary-key semantics before release. Non-observed missingness propagation also remains untested by the current all-observed transcriptomic corpus.

