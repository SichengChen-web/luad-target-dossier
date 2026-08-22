# Multi-component Evidence Profile Integration Validation Report

**Task:** #032C  
**Validation status:** **PASS**  
**Profile version:** `TARGET_EVIDENCE_PROFILE_MULTICOMPONENT_V0.1`

## Integrated representation

- Immutable profiles: 29,606
- Components per profile: 2
- Component representations: 59,212
- Feature references: 1,213,846
- Uncompressed provenance relationships: 2,517,118
- Profile-record bytes: 2,151,412,821
- Profile-record SHA256: `8fab364cbe1318f49dd8b29501dd1439d1ae2a38161e090942801399bec7e156`
- Profile-index SHA256: `376e6d3440dba3ae392410cd2f836a9a700fe66248bf29257794b55015821a28`
- Evidence snapshot version: `EVIDENCE_SNAPSHOT_32C_CBFD2625F8B0CBB855DB90CBC8E2D605`

No overall component state, evidence score, confidence, rank, priority, or target evaluation is generated.

## Transcriptomic component states

- `OBSERVED`: 26,171
- `PARTIAL`: 0
- `CONFLICTING`: 3,435
- `MISSING`: 0
- `NOT_QUERIED`: 0

## Disease-association component states

- `OBSERVED`: 8,393
- `PARTIAL`: 713
- `CONFLICTING`: 0
- `MISSING`: 20,500
- `NOT_QUERIED`: 0

States remain independent structural labels from their source components. `MISSING` is not negative evidence and `NOT_QUERIED` is not biological absence.

## Validation checks

- PASS — `frozen_input_hashes`: 25 top-level artifacts verified
- PASS — `partition_integrity`: 768 Task #030/#031 partition files verified by size and SHA256
- PASS — `profile_identity`: 29606 unique profile identity tuples
- PASS — `canonical_order`: Task #030 canonical universe order preserved
- PASS — `component_presence`: both registered components present in every profile
- PASS — `component_independence`: two separately versioned component objects; no overall state
- PASS — `feature_fidelity`: 1213846 exact source feature objects
- PASS — `state_fidelity`: component states unchanged
- PASS — `missingness_fidelity`: feature missingness unchanged
- PASS — `provenance_completeness`: 2517118 uncompressed source relationships
- PASS — `task031_cross_validation`: transcriptomic states and dependency-reference counts reconciled
- PASS — `forbidden_field_detection`: no score/rank/priority/evaluation field names
- PASS — `deterministic_profile_records`: full second-pass byte comparison and SHA256 match
- PASS — `deterministic_profile_index`: byte-identical regenerated index
- PASS — `no_network`: frozen local artifacts only
- PASS — `no_evaluation`: no target scoring, ranking, selection, recommendation, or interpretation

## Lineage boundary

Every integrated profile retains two independently versioned component objects. Every source feature object and every feature-to-evidence-record provenance relationship is copied without loss. Source component record identifiers, content hashes, containing artifact identifiers, artifact hashes, state-rule metadata, and version axes remain explicit. Counts in the index and report are audit reconciliation fields and do not replace lineage.

## Lifecycle and interpretation boundary

This is a deterministic local multi-component integration candidate. It does not promote a Target Evidence Profile lifecycle state and does not validate any target scientifically. It contains no target scoring, ranking, prioritization, selection, recommendation, biological interpretation, therapeutic inference, or runtime AI/LLM judgement.

## Frozen-input verification

- Top-level frozen artifacts verified: 25
- Partition payload files verified: 768
- Network access: none
- Package installation: none
