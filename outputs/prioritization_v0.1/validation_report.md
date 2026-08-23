# Transparent Prioritization Prototype v0.1 validation report

**Task:** #035B  
**Validation status:** PASS  
**Schema:** `PRIORITIZATION_OUTPUT_SCHEMA_V0.1`  
**Rule catalog:** `PRIORITIZATION_RULE_CATALOG_V0.1`

## Structural materialization

- Representations: **29,606**
- Preserved component-state snapshots: **59,212**
- Rule-trace steps: **118,424**
- Every representation contains four rule evaluations in fixed order and exactly one true result.

## Non-ordinal category reconciliation

- `CATEGORY_A`: 7,690
- `CATEGORY_B`: 17,851
- `CATEGORY_C`: 4,065
- `CATEGORY_UNASSIGNED`: 0

These counts are structural reconciliation metadata. Categories have no order, weight, desirability, or scientific meaning beyond their frozen predicates.

## Validation results

| Validation | Result |
|---|---|
| Exactly 29,606 representations in canonical EnsemblID order | PASS |
| One representation per frozen Evidence Summary | PASS |
| Source summary identity and content SHA256 preserved | PASS |
| Component IDs, versions, states, records, and limitations preserved | PASS |
| All four rules evaluated in fixed order 1–4 | PASS |
| Predicate IDs and boolean results reproduced | PASS |
| Exactly one true rule and correct category for every object | PASS |
| Recursive prohibited-field scan | PASS |
| Schema validation for every object | PASS |
| Every frozen source partition size and SHA256 reconciled twice | PASS |
| Two independent complete regenerations | PASS — byte-identical |
| Frozen repository input hashes unchanged | PASS |
| Gene symbols or external knowledge | NOT USED |
| Network/API access | PROHIBITED; NOT USED |
| Runtime AI/LLM decisions | PROHIBITED; NONE USED |

## Payload governance

- Artifact ID: `ART_PRZV01_SET_011A39B150DEF9E56A43CBF9`
- Payload size: **94,591,468 bytes**
- Partition-set SHA256: `011a39b150def9e56a43cbf97ff3985111dab0c5fe6d4fea3b3312f27961f65b`
- Storage reference placeholder: `external+sha256://PENDING/luad-target-dossier/prioritization-v0.1/ART_PRZV01_SET_011A39B150DEF9E56A43CBF9/`
- Ordinary Git tracking: `EXTERNALIZED_BY_ARTIFACT_DESIGN`
- The immutable JSONL partitions are held in content-addressed local staging outside the repository; durable registration remains pending.

## Interpretation boundary

This artifact is a deterministic structural routing representation. It is not a ranking, score, target selection, recommendation, biological interpretation, confidence estimate, probability estimate, or prediction of drug success.
