# Task #011 tractability and target-safety evidence summary

**Open Targets Platform data release:** 26.06  
**Open Targets API version:** 26.6.3  
**Genes retained:** 29,606  
**U2 genes retained:** 14,064

## Interpretation boundary

This layer preserves source-native Open Targets tractability assessments and safety-liability records. It does not rank, score, prioritize, recommend, or infer therapeutic direction. A positive tractability assessment is modality-relevant evidence, not proof that a target should be pursued. The number of positive buckets is not a project score.

**Absence of a curated safety-liability record is absence of retrieved evidence, not evidence of safety.** Presence of a liability is likewise not an automatic reason to reject a target.

## Tractability retrieval

| Scope | Genes | Mapped targets | Targets with assessment records | Assessment records | TRUE assessment records |
| --- | --- | --- | --- | --- | --- |
| All tested genes | 29606 | 28893 | 16894 | 473032 | 55761 |
| U2 genes | 14064 | 13691 | 8014 | 224392 | 26936 |

Source-native modality/assessment-value counts:

| Modality | Records | TRUE | FALSE |
| --- | --- | --- | --- |
| AB | 152046 | 18869 | 133177 |
| OC | 50682 | 455 | 50227 |
| PR | 135152 | 25184 | 109968 |
| SM | 135152 | 11253 | 123899 |

## Safety-liability retrieval

| Scope | Genes | Targets with record(s) | Mapped targets with zero records | Safety-liability records |
| --- | --- | --- | --- | --- |
| All tested genes | 29606 | 898 | 27995 | 4087 |
| U2 genes | 14064 | 520 | 13171 | 2558 |

Safety datasource record counts:

| Datasource | Records |
| --- | --- |
| AOP-Wiki | 220 |
| Bowes et al. (2012) | 291 |
| Brennan et al. (2024) | 202 |
| ClinPGx | 1493 |
| Force et al. (2011) | 46 |
| Lamore et al. (2017) | 30 |
| Lynch et al. (2017) | 1198 |
| ToxCast | 363 |
| Urban et al. (2012) | 244 |

## Missingness

`TARGET_NOT_MAPPED` means Task #009 provided no Open Targets target ID. `TARGET_PRESENT_NO_SAFETY_RECORD_RETURNED` means the mapped target was returned but its current safety-liability array was empty; it does not mean safe or low risk. `SAFETY_RECORD_PRESENT` means at least one source record was returned. `API_FIELD_NOT_AVAILABLE_OR_RETRIEVAL_FAILURE` is reserved for a missing required field or failed/missing target retrieval.

The long-form tables include explicit placeholder rows for genes without source records. Placeholder rows are not counted as tractability assessments or safety liabilities.

## Evidence-overlap warning

Open Targets tractability assessments may incorporate source data such as ChEMBL and clinical precedence. They must not be assumed independent of Task #010 drug/candidate counts or future ChEMBL clinical-development evidence. Task #011 stores the source-native assessment records only.

## Schema and provenance

The builder first introspected the deployed GraphQL types and failed unless all required fields and types matched the focused schema. Exact used fields/types, query hashes, release metadata, request/response counts, byte counts, response hashes, timestamps, input hashes, and output hashes are recorded in the schema snapshot and session file. No raw response dump was saved.

## Non-claims

No target score, tractability score, safety score, priority, rank, recommendation, therapeutic direction, or biological interpretation was generated.
