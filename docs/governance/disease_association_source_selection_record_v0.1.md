# Disease Association Source Selection Record v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Record version:** v0.1  
**Component:** `COMP_DISEASE_ASSOCIATION`  
**Decision status:** `SELECTED_FOR_SCOPED_SNAPSHOT_RETRIEVAL`  
**Decision date:** 22 August 2026

## 1. Purpose

This record freezes the selected source, release, access mode, record unit, identifier namespaces, provenance expectations, reproducibility basis, and license boundary for a future disease-association snapshot.

This is a governance decision, not a retrieval. No database, API, download, snapshot, extractor, evidence component, score, or ranking is created by this record.

Source selection does not imply biological truth, disease causality, evidence strength, target importance, target quality, therapeutic relevance, or target suitability.

## 2. Selection decision

| Field | Frozen value |
|---|---|
| `source_id` | `SRC_OPEN_TARGETS_PLATFORM` |
| `source_name` | Open Targets Platform |
| `source_authority` | Open Targets consortium |
| `source_version` | `26.06` |
| `source_release_id` | `OPEN_TARGETS_PLATFORM_26.06` |
| `source_release_date` | `NOT_RECORDED_IN_PROJECT_LOCAL_26.06_METADATA` |
| Corroborating API metadata version | `26.6.3` |
| `access_mode` | `OFFICIAL_RELEASE_PINNED_PARQUET_DATA_DOWNLOADS` |
| Authorized release datasets | `disease`, `target`, `evidence` |
| Primary record unit | `OPEN_TARGETS_SOURCE_NATIVE_EVIDENCE_RECORD` |
| Record granularity | `SOURCE_ATOMIC` where the official `evidence` dataset supplies stable evidence records; otherwise retain source-declared granularity without decomposition |
| Target identifier namespace | Ensembl gene ID |
| Disease identifier namespace | Open Targets disease ontology graph with Mondo identifiers |
| Platform data license | `CC0-1.0` |
| Mondo upstream license | `CC-BY-4.0` |
| Current source selection state | Frozen |

The source release date must be captured from the official 26.06 release manifest or release documentation during the future authorized snapshot retrieval. Its absence from the existing local API metadata does not permit an inferred date.

## 3. Governance evidence reviewed

### 3.1 Project-local version evidence

The existing Task #010 retrieval metadata is used only as source-selection evidence, not as the future canonical snapshot:

| Artifact | SHA256 | Relevant recorded fact |
|---|---|---|
| `outputs/evidence_layer/session_info.txt` | `2e1331f88685c5686e7e1f9dbf13e5f741ae46a8c460d1da8af596ef85c08d5c` | Open Targets data `26.06`, API `26.6.3`, disease `MONDO_0005061`, official GraphQL host, response-tracking metadata |
| `docs/evidence_layer_plan_v0.1.md` | `6e72e4932f02d939498269387ff2e3904ff3ad409440a29f7f3bf7f87d99359c` | Exact disease ID policy, direct/indirect query distinction, source-native association-field boundary |
| `analysis/10_build_evidence_layer.py` | `50136816005038bed3377923b1e31036ad3d2146daedc994548ccdbfbaec2a7a` | Prior deterministic retrieval implementation and query identity |

Task #010 did not retain complete raw API responses as governed artifacts. Its derived evidence registry is therefore rejected as the canonical Task #032B source snapshot.

### 3.2 Official governance references

Reviewed official documentation:

- Open Targets Platform data access: <https://platform-docs.opentargets.org/data-access>
- Release-pinned dataset downloads and Parquet structure: <https://platform-docs.opentargets.org/data-access/datasets>
- Platform license: <https://platform-docs.opentargets.org/licence>
- Target identity model: <https://platform-docs.opentargets.org/target>
- Platform release notes: <https://platform-docs.opentargets.org/release-notes>
- Open Targets partners and authority context: <https://opentargets.org/partners>

Documentation review date: 22 August 2026.

The official documentation states that systematic access is supported through release data downloads, the current download format is partitioned Parquet, Ensembl gene ID is the primary human target identifier, and Platform data are marked CC0 1.0. The future retrieval task must capture the exact official documents or release metadata it relies on and record their hashes.

## 4. Candidate evaluation

| Candidate | Version/access evaluated | Reproducibility | Record/provenance fit | License status | Decision |
|---|---|---|---|---|---|
| Open Targets Platform release-pinned data downloads | Release `26.06`; official Parquet datasets | Strong: release path, immutable captured files, partition manifests, and hashes can be preserved | Strong: Ensembl target IDs, Mondo disease IDs, source evidence records, disease and target entity tables | Platform data CC0 1.0; upstream Mondo CC BY 4.0 recorded | **Selected** |
| Open Targets live GraphQL API | API metadata `26.6.3`; mutable service response | Weaker for canonical snapshot: prior pagination showed duplicate-boundary behavior and complete raw responses were not retained | Returns useful entity/association views but many are aggregate representations | Same Platform data boundary | Rejected as canonical snapshot access; may not be used for evidence retrieval under this authorization |
| Open Targets BigQuery current tables | Public managed query service | Release pinning and exported raw-artifact identity were not established in the frozen local contract | Suitable in principle for structured filtering | Platform license applies | Not selected for v0.1; requires a separate source/access-mode amendment |
| Existing Task #010 `evidence_registry.csv` | Derived project artifact from data `26.06` | Hash-manifested derived table, but raw API evidence responses are not canonical frozen inputs | Summary/aggregate fields do not satisfy the new record-level raw snapshot contract | Project artifact under source terms | Rejected as future raw snapshot; retained unchanged as historical evidence layer |
| Other disease-association providers | No versioned project-local source contract reviewed | Not established | Not established | Not established | Deferred, not scientifically rejected; each requires a separate Task #032A-compatible registration |

Alternative rejection is based on snapshot and interface fit, not on biological correctness or comparative evidence strength.

## 5. Source authority

Open Targets Platform is maintained by the Open Targets public–private consortium. The official partners page identifies EMBL-EBI and the Wellcome Sanger Institute among current partners, alongside industry partners. Release datasets are distributed through official Open Targets/EMBL-EBI data infrastructure and listed by the Platform documentation.

Authority identifies the maintainer and release channel. It does not establish that any returned association record is biologically true.

## 6. Selected access mode

The canonical future snapshot must use official release-pinned Parquet data downloads for release `26.06`.

Authorized dataset roles:

| Dataset | Role |
|---|---|
| `disease` | Resolve and validate `MONDO_0005061`, label, ontology relationships, and disease entity provenance |
| `target` | Resolve Open Targets Ensembl target IDs and target entity provenance |
| `evidence` | Preserve source-native target–disease evidence records and their source fields |

The future retrieval task must discover and freeze the exact official release paths and file inventories from the 26.06 release documentation or manifest. Path guessing is prohibited.

The live GraphQL API, web-interface exports, and mutable current BigQuery tables are outside the selected canonical access mode.

## 7. Record semantics

The primary disease-association evidence record is one source-native record in the official Open Targets `evidence` dataset connecting a source `targetId`, source `diseaseId`, evidence source/datasource identity, and source-native raw payload.

Rules:

1. Preserve the complete raw record.
2. Preserve source-provided evidence and datasource identifiers.
3. Derive a deterministic `evidence_record_id` only when a stable source-native record ID is absent.
4. Do not split a source aggregate into apparent atomic evidence.
5. Do not treat distinct datasource rows as independent without dependency review.
6. Do not normalize source-native scores, p-values, odds ratios, or other metrics into Task #032B-1 v0.1 features.
7. Use counts only for audit reconciliation, never as evidence strength or target evaluation.

The `disease` and `target` datasets provide entity and mapping context, not additional independent association evidence.

## 8. Identifier namespaces

### 8.1 Target identity

Open Targets uses Ensembl gene IDs as primary human target identifiers. The frozen project universe retains versioned `EnsemblID`; the future source mapping rule is:

`source targetId = substring of EnsemblID before the first period`

Mapping rule ID: `DA_OT_ENSEMBL_BASE_MAPPING_V0.1`.

The current Task #030 universe contains 29,606 unique versioned Ensembl IDs and 29,606 unique base IDs. The future retrieval must repeat and record this assertion. Any collision, non-Ensembl target, ambiguous mapping, or missing target remains explicit and blocks silent assignment.

### 8.2 Disease identity

The selected disease identifier is exact `MONDO_0005061`, governed in [Disease Context Registration v0.1](disease_context_registration_v0.1.md).

Free-text disease matching, label-only matching, synonym inference, and runtime LLM mapping are prohibited.

## 9. Provenance capability

The selected source can support future capture of:

- source and release identity;
- source target and disease identifiers;
- source evidence/datasource identifiers;
- source-native raw record payloads;
- partition and file location;
- file size and SHA256;
- record/query inclusion rule;
- target and disease mapping records;
- license information;
- extraction-rule and extractor versions;
- dependency assertions.

Snapshot retrieval must fail if the selected release cannot provide these required provenance fields or immutable raw artifacts.

## 10. Dependency boundary

Open Targets integrates multiple upstream evidence providers. Records may share a datasource, dataset, study, publication, cohort, variant, or upstream record.

Therefore:

- records from one source aggregate are dependent;
- records sharing a dataset or upstream record are dependent;
- unresolved overlap remains `UNKNOWN`;
- different `sourceId` values do not prove independence;
- `NOT_APPLICABLE` does not mean independent;
- direct and ontology-expanded association summaries are not independent views.

The selected exact-only evidence-record scope does not authorize cross-record voting or aggregation.

## 11. Reproducibility requirements

Future retrieval must preserve:

- exact 26.06 release paths and official release metadata;
- complete downloaded-file inventory;
- raw bytes, sizes, and SHA256 values;
- retrieval start/end metadata and software version;
- license artifact/reference;
- disease context and query universe hashes;
- inclusion/filter specification;
- completeness ledger;
- deterministic raw record packaging without modifying source values.

All later extraction and materialization must run without network access from the frozen snapshot.

## 12. Licensing decision

The selected Platform data license is frozen as `CC0-1.0`, based on the official Open Targets license documentation reviewed on 22 August 2026. The upstream Mondo entry is listed as `CC-BY-4.0` in that documentation.

Future snapshot retrieval must capture:

- the exact license documentation used;
- access date;
- license artifact or immutable reference;
- artifact SHA256 where locally preserved;
- citation/attribution guidance;
- redistribution status for raw and derived artifacts.

If the 26.06 release manifest or license terms conflict with this record, retrieval must stop and return to governance review.

## 13. Source selection identity

Canonical source-selection payload:

```json
{"access_mode":"OFFICIAL_RELEASE_PINNED_PARQUET_DATA_DOWNLOADS","api_metadata_version":"26.6.3","authorized_datasets":["disease","evidence","target"],"disease_namespace":"Open Targets disease ontology graph with MONDO identifiers","license":"CC0-1.0","record_unit":"OPEN_TARGETS_SOURCE_NATIVE_EVIDENCE_RECORD","source_authority":"Open Targets consortium","source_id":"SRC_OPEN_TARGETS_PLATFORM","source_name":"Open Targets Platform","source_version":"26.06","target_namespace":"Ensembl gene ID"}
```

Canonical payload SHA256:

`0de4086e33775414f679bb5bdeda00c8c372fb4394d0a0f04009f54f81f8fb57`

Artifact identity: `SRCSEL_DA_OPEN_TARGETS_26_06_V0_1`.

## 14. Interpretation and use boundary

Selection means that the source satisfies the v0.1 governance requirements for a scoped future snapshot. It does not imply:

- source records are correct or causal;
- a target is important, suitable, or actionable;
- source-native association values measure project confidence;
- multiple records are independent;
- any target should be scored, ranked, prioritized, selected, or recommended.

## 15. Selection checklist

- [x] Stable source, release, target, disease, and record identities are available.
- [x] Record semantics and release-pinned access mode are defined.
- [x] Provenance and raw-record preservation are feasible.
- [x] Reproducibility uses immutable Parquet artifacts and hashes.
- [x] Platform and ontology license boundaries are recorded.
- [x] Rejected/deferred alternatives and reasons are explicit.
- [x] No live API is selected for canonical evidence retrieval.
- [x] No biological truth, evidence strength, target importance, or therapeutic meaning is inferred.
- [ ] Exact 26.06 release paths, release date, file inventory, and artifact hashes are captured during authorized retrieval.

## 16. Related governance

- [Disease Context Registration v0.1](disease_context_registration_v0.1.md)
- [Disease Association Materialization Authorization v0.1](disease_association_materialization_authorization_v0.1.md)
- [Disease Association Source Contract v0.1](disease_association_source_contract_v0.1.md)
- [Disease Association Snapshot Policy v0.1](disease_association_snapshot_policy_v0.1.md)

