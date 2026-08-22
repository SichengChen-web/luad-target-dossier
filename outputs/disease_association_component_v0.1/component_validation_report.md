# Disease Association Component Validation Report

**Task:** #032B-2E  
**Component:** `COMP_DISEASE_ASSOCIATION`  
**Component version:** `COMP_DISEASE_ASSOCIATION_V0.1`  
**Validation status:** **PASS**

## Materialized component

- Immutable component instances: 29,606
- Features per instance: 19
- Total feature instances: 562,514
- Uncompressed provenance relationships: 1,480,908
- Direct raw-record relationships: 977,145
- Query-scope relationships: 503,763
- Component-record bytes: 1,550,091,187
- Component-record SHA256: `ecde83c5f3d28441c0e439b2ede6621f484b5b592a96370052911984868ad264`
- Component-index SHA256: `7637c4da5f2286acb082b5382ae9f9bf50b08b2342d861e60ba388d729295c9e`

## Independent version axes

- Component version: `COMP_DISEASE_ASSOCIATION_V0.1`
- Component schema version: `DISEASE_ASSOCIATION_COMPONENT_SCHEMA_V0.1`
- Source snapshot version: `DA_OT_26_06_MONDO_0005061_SHA256_84949b70be605fea`
- Feature schema version: `DISEASE_ASSOCIATION_FEATURE_SCHEMA_V0.1`
- Feature generator version: `DISEASE_ASSOCIATION_FEATURE_GENERATOR_V0.1`
- State-rule version: `DA_COMPONENT_STATE_RULES_V0.1`
- Extractor version: `DISEASE_ASSOCIATION_FEATURE_EXTRACTOR_V0.1`
- Component generator version: `DISEASE_ASSOCIATION_COMPONENT_GENERATOR_V0.1`

## Structural component states

- `OBSERVED`: 8,393
- `PARTIAL`: 713
- `CONFLICTING`: 0
- `MISSING`: 20,500
- `NOT_QUERIED`: 0

These are structural evidence conditions only. They are non-ordinal and do not represent disease relevance, target quality, importance, confidence, priority, or therapeutic value.

## Feature missingness

- `OBSERVED`: 448,056
- `NOT_FOUND`: 106,065
- `NOT_QUERIED`: 0
- `NOT_APPLICABLE`: 0
- `UNKNOWN`: 8,393

`NOT_FOUND` remains a completed-query structural outcome and is not negative evidence. Feature missingness is not substituted by component state.

## Validation checks

- PASS — `frozen_input_hashes`: 23 frozen files verified
- PASS — `raw_snapshot_local_artifacts`: 148 local snapshot artifacts verified by size and SHA256
- PASS — `entity_identity`: 29606 ordered immutable EnsemblID records
- PASS — `component_identity`: all index identities exact
- PASS — `feature_fidelity`: 562514 exact source feature instances
- PASS — `state_fidelity`: {"MISSING":20500,"OBSERVED":8393,"PARTIAL":713}
- PASS — `provenance_completeness`: 1480908 uncompressed relationships
- PASS — `raw_record_lineage`: 977145 direct links resolve against 75165 raw records
- PASS — `dependency_preservation`: {"DEPENDENT":938938,"NOT_APPLICABLE":541970}
- PASS — `missingness_preservation`: {"NOT_FOUND":106065,"OBSERVED":448056,"UNKNOWN":8393}
- PASS — `forbidden_field_detection`: no prohibited component/index field names
- PASS — `deterministic_component_records`: full second-pass byte comparison and SHA256 match
- PASS — `deterministic_component_index`: byte-identical regenerated index
- PASS — `no_network`: offline frozen artifacts only
- PASS — `no_profiles`: no target profile artifact generated
- PASS — `no_evaluation`: no scoring, ranking, priority, recommendation, or interpretation

## Provenance and dependency boundary

Every Task #032B-2D `(feature_id, evidence_record_id)` relationship is embedded separately below its feature. Each relationship retains its raw-record, source, snapshot-artifact, extraction-rule, and dependency identifiers. Same-source and shared-dataset relationships remain dependent; `NOT_APPLICABLE` is not rewritten as independence. Counts in this report and index are audit reconciliation fields and do not replace lineage.

## Authorization and lifecycle boundary

The explicit Task #032B-2E instruction is the scoped execution authority for this component materialization. The earlier Task #032B-2B retrieval-only authorization remains unchanged as a historical governance record. This component artifact does not create or promote a Target Evidence Profile lifecycle state.

## Interpretation boundary

This component materializes validated structural observations only. It generates no target profile, score, rank, priority, recommendation, disease-relevance interpretation, therapeutic interpretation, or biological conclusion. No network, live source, randomness, or runtime AI/LLM decision was used.
