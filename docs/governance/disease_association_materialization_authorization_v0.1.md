# Disease Association Materialization Authorization v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Authorization version:** v0.1  
**Component:** `COMP_DISEASE_ASSOCIATION`  
**Current authorization status:** `APPROVED_FOR_SNAPSHOT_RETRIEVAL`  
**Authorization date:** 22 August 2026

## 1. Purpose

This record freezes the entity universe, source, disease context, permitted retrieval mode, raw dataset scope, and governance gates for a future disease-association source snapshot.

Despite the historical filename required by Task #032B-2B, this record does not authorize component or profile materialization. It authorizes only scoped snapshot retrieval. `RETRIEVED` and `MATERIALIZED` remain unattained statuses.

No retrieval, API call, download, snapshot, extractor, normalized feature, evidence component, profile, score, or ranking is produced by this record.

## 2. Authorization status model

| Status | Meaning | Current disposition |
|---|---|---|
| `PROPOSED` | Source, context, universe, and scope have been proposed but retrieval is not authorized | Completed |
| `APPROVED_FOR_SNAPSHOT_RETRIEVAL` | A separate retrieval task may acquire only the frozen source/release/datasets/context/universe under this scope | **Current** |
| `RETRIEVED` | Raw artifacts, manifests, license evidence, hashes, and completeness validation exist | Not attained |
| `MATERIALIZED` | A reviewed extractor and executable state rules generated a validated component from the frozen snapshot | Not attained and not authorized |

Statuses are procedural and non-ordinal with respect to target evidence. They do not indicate biological validity or target quality.

## 3. Authorization identity

| Field | Frozen value |
|---|---|
| `authorization_id` | `AUTH_DA_OT_26_06_SNAPSHOT_V0_1` |
| `authorization_status` | `APPROVED_FOR_SNAPSHOT_RETRIEVAL` |
| `component_id` | `COMP_DISEASE_ASSOCIATION` |
| `component_version` | `COMP_DISEASE_ASSOCIATION_V0.1` |
| `source_id` | `SRC_OPEN_TARGETS_PLATFORM` |
| `source_version` | `26.06` |
| `access_mode` | `OFFICIAL_RELEASE_PINNED_PARQUET_DATA_DOWNLOADS` |
| Authorized datasets | `disease`, `target`, `evidence` |
| `disease_context_id` | `MONDO_0005061` |
| Inclusion model | `EXACT_ONLY` |
| `entity_universe_id` | `UNIV_TASK030_ENSEMBL_29606_V0_1` |
| Retrieval authority basis | Explicit Task #032B-2B project instruction |
| Materialization authority | `NOT_AUTHORIZED` |

## 4. Registered entity universe

The future query universe is the complete Task #030 profile universe.

| Field | Frozen value |
|---|---|
| `entity_universe_id` | `UNIV_TASK030_ENSEMBL_29606_V0_1` |
| Universe artifact | `outputs/profile_release_candidate_v0.1/universe_manifest.csv` |
| Artifact ID | `ART_TASK030_UNIVERSE_MANIFEST_V0_1` |
| Artifact size | `9,179,140` bytes |
| Artifact SHA256 | `e4b304eb5fde7690a1525b404f5d1a011837fd88f774b4dbb2838f2c81b9c1ab` |
| Entity count | `29,606` |
| Immutable key | Versioned `EnsemblID` |
| Unique versioned IDs | `29,606` |
| Unique Ensembl base IDs | `29,606` |
| Canonical order | Exact Task #030 `universe_ordinal`, inherited from Task #026 feature-row order |
| Partition reference | Task #030 `ENSEMBL_SHA256_PREFIX_2_V0.1` where partition compatibility is needed |

### Rationale

The Task #030 universe is selected because it is the complete governed Target Evidence Profile universe. Reusing it preserves identity, cardinality, ordering, and profile compatibility without evidence-based or biological filtering.

No entity is excluded based on expression direction, statistical significance, candidate membership, disease-association availability, gene type, druggability, perceived importance, or therapeutic interest.

## 5. Target mapping scope

The authorized source mapping rule is `DA_OT_ENSEMBL_BASE_MAPPING_V0.1`:

1. Preserve versioned project `EnsemblID` as immutable identity.
2. Derive source target ID by removing the version suffix after the first period.
3. Validate source target identity against the frozen Open Targets 26.06 `target` dataset.
4. Preserve both project and source identifiers.
5. Record `NOT_FOUND`, ambiguous, conflicting, or unknown mappings explicitly.
6. Stop on base-ID collisions or one-to-many source mappings unless a future reviewed amendment defines them.

The current universe has no base-ID collision. The retrieval task must independently reproduce that assertion.

Gene symbols are prohibited as query or join keys.

## 6. Authorized disease scope

The disease context is frozen by `CTX_LUAD_MONDO_0005061_EXACT_V0_1`:

- exact raw `diseaseId = MONDO_0005061`;
- label validation against `lung adenocarcinoma`;
- ontology version `OPEN_TARGETS_PLATFORM_26.06_DISEASE_ONTOLOGY_SNAPSHOT`;
- mapping rule `DA_LUAD_CONTEXT_MAPPING_V0.1`;
- no descendants, ancestors, indirect association expansion, synonyms, broader terms, or free-text matching.

## 7. Authorized raw retrieval scope

Permitted:

- obtain official release `26.06` Parquet artifacts for `disease`, `target`, and `evidence` from release-pinned Open Targets data-download infrastructure;
- obtain official 26.06 release metadata, schema metadata, license documentation, and file inventories required to validate those artifacts;
- retrieve all required partitions needed to demonstrate complete coverage of the selected datasets;
- retain complete source-native raw records and response/file metadata;
- create retrieval manifests, per-file hashes, per-entity coverage ledgers, and snapshot QC artifacts;
- create a deterministic raw subset/index for exact `MONDO_0005061` and the registered universe only after preserving its source-file lineage.

Not permitted:

- live GraphQL evidence retrieval;
- mutable current BigQuery tables;
- web-interface exports;
- unversioned latest-release aliases;
- any release other than `26.06`;
- any source beyond Open Targets Platform;
- ontology-expanded or indirect disease associations;
- evidence filters based on source-native score, perceived strength, confidence, importance, or target promise;
- normalized feature extraction;
- component or profile materialization.

If an exact 26.06 release artifact is no longer available, retrieval must stop rather than substitute a newer release.

## 8. Query and filter scope

The future retrieval specification must implement:

- source release exact match: `26.06`;
- source dataset allowlist: `disease`, `target`, `evidence`;
- target universe: all 29,606 registered entities through the reviewed base-ID mapping;
- disease inclusion: exact `MONDO_0005061` only;
- evidence datasource/type inclusion: all source-native values present for exact in-scope evidence records;
- evidence score threshold: none;
- source-native record field preservation: complete;
- deterministic duplicate detection without silent merging;
- canonical raw-record ordering independent of source-native association score;
- complete mapping, coverage, failure, and exclusion ledgers.

No biologically adaptive query or filter is authorized.

## 9. Snapshot deliverable boundary

The authorized future retrieval task may produce only source-snapshot artifacts required by Task #032B-2A policy, including:

- raw source files or governed immutable external references;
- source release and schema manifests;
- retrieval manifest;
- disease-context and entity-universe references;
- query/filter manifest;
- license artifact/reference;
- file-size and SHA256 inventory;
- per-entity and per-partition coverage ledger;
- retrieval QC and validation report;
- `source_snapshot_version` after all bytes and scope fields are frozen.

It must not produce normalized component features, component states, target profiles, evidence landscapes, scores, rankings, or recommendations.

## 10. Retrieval completion gates

Status may advance to `RETRIEVED` only when:

- exact 26.06 release identity and official release date are captured;
- exact official artifact paths and file inventory are recorded;
- every required file matches recorded size and SHA256;
- official dataset schemas are frozen;
- license documentation and attribution guidance are captured;
- the `disease` dataset validates `MONDO_0005061` and label;
- the `target` dataset supports the registered Ensembl mapping ledger;
- the `evidence` dataset scope is complete;
- every entity has a coverage ledger row;
- exact disease inclusion and all exclusions reconcile;
- retrieval failures, retries, duplicates, and unknowns are explicit;
- snapshot regeneration/replay requires no live source;
- frozen Task #032A/#032B governance artifacts remain unchanged.

Any failed gate retains `APPROVED_FOR_SNAPSHOT_RETRIEVAL` or records a failed retrieval attempt; it does not silently advance status.

## 11. Materialization boundary

This record does not authorize status `MATERIALIZED`.

Materialization requires a future separate governance action after:

- a complete validated snapshot exists;
- machine-readable component schema is frozen;
- `extractor_version` and deterministic extraction rules are implemented and reviewed;
- executable five-state rules and fixtures pass;
- provenance, dependency, missingness, and interpretation-safety validation passes;
- a scoped component/profile lifecycle destination is approved.

## 12. Authorization identity payload

Canonical authorization payload:

```json
{"access_mode":"OFFICIAL_RELEASE_PINNED_PARQUET_DATA_DOWNLOADS","authorization_id":"AUTH_DA_OT_26_06_SNAPSHOT_V0_1","authorized_datasets":["disease","evidence","target"],"component_id":"COMP_DISEASE_ASSOCIATION","component_version":"COMP_DISEASE_ASSOCIATION_V0.1","disease_context_id":"MONDO_0005061","entity_universe_id":"UNIV_TASK030_ENSEMBL_29606_V0_1","entity_universe_sha256":"e4b304eb5fde7690a1525b404f5d1a011837fd88f774b4dbb2838f2c81b9c1ab","inclusion_model":"EXACT_ONLY","prohibited_access":["LIVE_GRAPHQL_EVIDENCE_RETRIEVAL","BIGQUERY_CURRENT_TABLES","WEB_UI_EXPORT"],"source_id":"SRC_OPEN_TARGETS_PLATFORM","source_version":"26.06","status":"APPROVED_FOR_SNAPSHOT_RETRIEVAL"}
```

Canonical payload SHA256:

`67da4f87e97f3fe6bdfd2870f8fd0376924a7468af11fe4c2be01133f82cf519`

## 13. Governance and interpretation boundary

Authorization confirms only that a future retrieval task may acquire the specified release and raw datasets under the frozen scope.

It does not establish:

- disease causality or driver status;
- evidence strength or confidence;
- target importance, quality, suitability, or priority;
- therapeutic relevance or direction;
- a target ranking, selection, or recommendation.

No runtime AI decision may change source, release, disease context, universe, filters, inclusion, or status.

## 14. Current status checklist

- [x] `PROPOSED` scope completed.
- [x] Source, release, access mode, disease context, universe, and retrieval boundary frozen.
- [x] `APPROVED_FOR_SNAPSHOT_RETRIEVAL` is current.
- [ ] `RETRIEVED` has been attained.
- [ ] `MATERIALIZED` has been attained or authorized.
- [x] No retrieval or evidence artifact is created by this record.
- [x] No biological filtering, scoring, ranking, or target prioritization is authorized.

## 15. Related governance

- [Disease Association Source Selection Record v0.1](disease_association_source_selection_record_v0.1.md)
- [Disease Context Registration v0.1](disease_context_registration_v0.1.md)
- [Disease Association Query Scope Policy v0.1](disease_association_query_scope_policy_v0.1.md)
- [Disease Association Snapshot Policy v0.1](disease_association_snapshot_policy_v0.1.md)

