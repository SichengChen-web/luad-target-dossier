# Multi-component Evidence Landscape v0.2 validation report

**Task:** #033B-2  
**Validation status:** PASS  
**Landscape version:** `MULTI_COMPONENT_EVIDENCE_LANDSCAPE_V0.2`

## Structural projection

- Landscapes: **29,606**
- Component references: **59,212**
- Feature references: **1,213,846**
- Record-level provenance/dependency references: **2,517,118**
- Ordered dependency relationships: **3,430,043**
- Provenance references with multiple dependency relationships: **912,925**
- External JSONL partitions: **256**

Each landscape is a structural projection of exactly one frozen Task #032C profile. No component was rebuilt from raw evidence.

## Validation results

| Validation | Result |
|---|---|
| Exact Task #032C EnsemblID universe and canonical order | PASS |
| 29,606 unique landscape and source-profile identities | PASS |
| Exactly two ordered components per landscape | PASS |
| Component versions and states preserved | PASS |
| Feature identity and missingness preserved | PASS |
| All 2,517,118 provenance relationships preserved separately | PASS |
| Ordered dependency arrays reconciled without collapsing `SAME_SOURCE` and `SHARED_DATASET` | PASS |
| Source-native artifact IDs and namespaces reconciled without rewriting | PASS |
| Applicable registered limitation IDs preserved | PASS |
| Historical `LIM_ONLY_TRANSCRIPTOMIC_COMPONENT` excluded | PASS |
| Task #033B-1.1 schema v0.2.1 validation for every landscape | PASS |
| Prohibited-field recursive scan for every landscape | PASS |
| Two independent complete regenerations | PASS — identical partition sizes and SHA256 hashes |
| Frozen input hashes unchanged | PASS |
| Network or API access | PROHIBITED; NOT USED |
| Runtime AI/LLM decisions | PROHIBITED; NONE USED |

## Component states

### `COMP_TRANSCRIPTOMIC_EVIDENCE`

- `OBSERVED`: 26,171
- `PARTIAL`: 0
- `CONFLICTING`: 3,435
- `MISSING`: 0
- `NOT_QUERIED`: 0

### `COMP_DISEASE_ASSOCIATION`

- `OBSERVED`: 8,393
- `PARTIAL`: 713
- `CONFLICTING`: 0
- `MISSING`: 20,500
- `NOT_QUERIED`: 0

## Feature missingness

### `COMP_TRANSCRIPTOMIC_EVIDENCE`

- `OBSERVED`: 651,332
- `NOT_FOUND`: 0
- `NOT_QUERIED`: 0
- `NOT_APPLICABLE`: 0
- `UNKNOWN`: 0

### `COMP_DISEASE_ASSOCIATION`

- `OBSERVED`: 448,056
- `NOT_FOUND`: 106,065
- `NOT_QUERIED`: 0
- `NOT_APPLICABLE`: 0
- `UNKNOWN`: 8,393

## Artifact governance

- External payload size: **3,386,989,421 bytes**
- Partition-set artifact: `ART_LNDV02_SET_756809652ACB00343DA20824`
- Partition-set SHA256: `756809652acb00343da20824dfec74550c01f649fe78159a6e6bc762e546ea21`
- Payload class: `CLASS_D_LARGE_DATA_OBJECT`
- Ordinary Git tracking: prohibited; JSONL partitions are held in content-addressed external local staging.
- Durable external storage registration remains a separate governance action.
- Git-managed index size: 25,976,563 bytes; SHA256 `fbd7a3b50e70c41aa2ddbf0361390fde23d12bc320a881a4da168ad1d145d6c8`
- Git-managed partition manifest size: 162,262 bytes; SHA256 `2ccc38a384fe816d50b2c5d8f4c528a49727189434fe4be41e70355ff146cf8d`

## Provenance-resolution boundary

The generator copied feature-to-record relationships from Task #032C. Small frozen lineage manifests were used only to resolve artifact hashes, governed dependency classifications, and applicable stable limitation identifiers already referenced by that lineage. No raw evidence source or API was accessed.

Task #032C does not register a disease-association limitation identifier. None was invented; the component limitation-reference array therefore remains empty.

## Interpretation boundary

This validation establishes structural, lineage, and reproducibility conformance only. The landscape contains no target evaluation, score, rank, priority, selection, recommendation, biological interpretation, therapeutic conclusion, or overall component state.
