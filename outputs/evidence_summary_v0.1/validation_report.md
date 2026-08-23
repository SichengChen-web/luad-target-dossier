# Evidence Summary v0.1 validation report

**Task:** #034B  
**Validation status:** PASS  
**Schema:** `EVIDENCE_SUMMARY_SCHEMA_V0.1`  
**Representation:** `EVIDENCE_AGGREGATION_REPRESENTATION_V0.1`

## Structural materialization

- Evidence Summary objects: **29,606**
- Component summaries: **59,212**
- Feature-missingness references: **1,213,846**
- Dependency summaries: **2,517,118**
- Ordered dependency relationships: **3,430,043**
- Multi-relationship dependency summaries: **912,925**

Every summary was projected from exactly one frozen Task #033B-2 landscape. No component or evidence record was rebuilt.

## Validation results

| Validation | Result |
|---|---|
| Exactly 29,606 summaries in canonical EnsemblID order | PASS |
| One summary per source landscape | PASS |
| Summary identity tuple and source-landscape content hash | PASS |
| Exactly two ordered components and exact component versions | PASS |
| Component states preserved | PASS |
| All feature missingness values preserved | PASS |
| Dependency identities and ordered relationship arrays preserved | PASS |
| `SAME_SOURCE` and `SHARED_DATASET` retained separately | PASS |
| Source-native artifact IDs, namespaces, and SHA256 hashes preserved | PASS |
| Summary and component limitation identifiers preserved | PASS |
| Evidence Summary schema validation for every object | PASS |
| Recursive prohibited-field scan for every object | PASS |
| Every frozen source partition size and SHA256 reconciled twice | PASS |
| Two independent complete regenerations | PASS — byte-identical partitions and metadata |
| Frozen repository input hashes unchanged | PASS |
| Network/API access | PROHIBITED; NOT USED |
| Runtime AI/LLM decisions | PROHIBITED; NONE USED |

## Large artifact governance

- Partition-set artifact ID: `ART_SUMV01_SET_9C7750D42301093888A120CE`
- Aggregate payload size: **1,876,140,432 bytes**
- Partition-set SHA256: `9c7750d42301093888a120ce9b4231d7b33724e17c1dc40a57c60ffa92c81291`
- Storage reference placeholder: `external+sha256://PENDING/luad-target-dossier/evidence-summary-v0.1/ART_SUMV01_SET_9C7750D42301093888A120CE/`
- The immutable JSONL partitions are held in content-addressed local staging outside the repository.
- Durable external storage registration remains pending; no payload file is present in ordinary Git.

## Interpretation boundary

This release candidate establishes structural representation, lineage, and deterministic reproducibility only. It contains no target evaluation, score, rank, priority, confidence measure, overall state, recommendation, target-quality field, evidence-strength field, biological interpretation, or therapeutic conclusion.
