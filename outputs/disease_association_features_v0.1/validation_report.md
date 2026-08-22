# Disease Association Feature Extraction Validation Report

**Task:** #032B-2D  
**Component:** `COMP_DISEASE_ASSOCIATION`  
**Source snapshot:** `DA_OT_26_06_MONDO_0005061_SHA256_84949b70be605fea`  
**Validation status:** **PASS**

## Generated layer

- Immutable entities: 29,606
- Registered structural feature definitions: 19
- Feature instances: 562,514
- Uncompressed feature-to-record provenance relationships: 1,480,908
- Feature table SHA256: `3eee6bb0a3f55e051427fdd7f67fd974604abe9bc11477b2e3be73c561201418`
- Feature dictionary SHA256: `690f5d23fd6de3a949d77b60e19fad6655fec83441afcb31d1c2dfd46532be32`
- Provenance registry SHA256: `d3f16e0a621e0b129c3d42e7bc01cb2042d1cef05374c19b1e23643043545480`

Source-native association metrics remain only in the frozen raw Parquet records. They are not normalized feature values or state inputs.

## Actual structural component states

- `CONFLICTING`: 0
- `OBSERVED`: 8,393
- `MISSING`: 20,500
- `PARTIAL`: 713
- `NOT_QUERIED`: 0

These states are non-ordinal structural labels. `MISSING` means a complete resolved query returned no qualifying record; it is not negative evidence. `PARTIAL` identifies unresolved infrastructure conditions and is not a judgement about a target.

## Feature-level missingness observations

- `OBSERVED`: 448,056
- `NOT_FOUND`: 106,065
- `NOT_QUERIED`: 0
- `NOT_APPLICABLE`: 0
- `UNKNOWN`: 8,393

The `UNKNOWN` feature-missingness observations arise from the deliberately unresolved source-native record-granularity classification. This feature is not a state input.

## Executable state fixtures

- PASS — `FIX_OBSERVED`: expected `OBSERVED`, observed `OBSERVED`
- PASS — `FIX_MISSING`: expected `MISSING`, observed `MISSING`
- PASS — `FIX_PARTIAL`: expected `PARTIAL`, observed `PARTIAL`
- PASS — `FIX_NOT_QUERIED`: expected `NOT_QUERIED`, observed `NOT_QUERIED`
- PASS — `FIX_CONFLICTING`: expected `CONFLICTING`, observed `CONFLICTING`
- PASS — `FIX_CONFLICT_PRECEDENCE_OVER_PARTIAL`: expected `CONFLICTING`, observed `CONFLICTING`

## Validation checks

- PASS — `frozen_input_hashes`: 19 inputs verified
- PASS — `entity_identity`: 29606 ordered EnsemblID rows
- PASS — `registered_feature_definitions`: 19 exact Task032B-1 definitions
- PASS — `raw_record_lineage`: 75165 immutable raw records resolved
- PASS — `feature_provenance_completeness`: 562514 feature instances have lineage
- PASS — `uncompressed_provenance`: 1480908 separate feature-to-record links
- PASS — `missingness_vocabulary`: ["NOT_FOUND","OBSERVED","UNKNOWN"]
- PASS — `component_state_vocabulary`: {"MISSING":20500,"OBSERVED":8393,"PARTIAL":713}
- PASS — `state_fixture_coverage`: 6 fixtures including precedence
- PASS — `dependency_preservation`: every raw record has dependent or NOT_APPLICABLE classification
- PASS — `forbidden_field_detection`: no prohibited output field names
- PASS — `source_native_metric_exclusion`: no source metric exposed as normalized feature
- PASS — `deterministic_feature_table`: byte-identical regeneration
- PASS — `deterministic_feature_dictionary`: byte-identical regeneration
- PASS — `deterministic_provenance`: byte-identical independent regeneration
- PASS — `no_network`: extractor contains no network client or live source call
- PASS — `no_profiles`: no profile artifact generated
- PASS — `no_evaluation`: no scoring, ranking, recommendation, or biological interpretation

## Dependency boundary

Every association record retains its own provenance relationship. Entities with multiple records are labelled `SAME_SOURCE`; records sharing one Open Targets source dataset additionally retain `SHARED_DATASET`. A single record or zero records use `NOT_APPLICABLE`. No record is labelled independent.

## Interpretation boundary

This layer describes evidence availability, record structure, mapping, provenance, dependency, missingness, and structural state only. It does not establish disease causality, biological importance, evidence strength, target quality, therapeutic value, ranking, recommendation, or target selection. No profile was generated.
