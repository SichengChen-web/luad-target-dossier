# Evidence Layer Summary

**Task:** #010  
**Genes retained:** 29,606 / 29,606  
**U2 genes retained:** 14,064 / 14,064  
**Immutable key:** versioned `EnsemblID`

## Retrieval coverage

| Evidence field | All tested genes | U2 genes |
|---|---:|---:|
| Open Targets target record | 28,893 (97.59%) | 13,691 (97.35%) |
| Direct LUAD association | 8,393 (28.35%) | 4,871 (34.63%) |
| Ontology-expanded LUAD association | 8,406 (28.39%) | 4,877 (34.68%) |
| Nonzero Open Targets bibliography count | 21,681 (73.23%) | 10,397 (73.93%) |
| Nonzero Open Targets drug/candidate record count | 1,443 (4.87%) | 815 (5.79%) |
| ChEMBL target annotation | 5,963 (20.14%) | 2,767 (19.67%) |

Counts describe retrieved records only. They are not target scores, ranks, or
statements of biological importance.

## Disease query

- Disease ID: `MONDO_0005061`
- Disease label: `lung adenocarcinoma`
- Direct Platform association universe: **8,745** targets
- Ontology-expanded association universe: **8,760** targets

Direct and ontology-expanded evidence are retained separately. All association
scores and datasource/datatype values are unmodified Open Targets source-native
fields, not project-generated scores.

## Source snapshot

- Open Targets data `26.06`;
  API `26.6.3`.
- ChEMBL `ChEMBL_37`, released
  `2026-05-01`.
- Open Targets mapped IDs absent from the current API: **0**
- ChEMBL rows with partial one-to-many retrieval: **0**
- ChEMBL mapped rows absent from the current API: **0**

Network access was limited to official Open Targets and ChEMBL APIs. No package
was installed or updated. Response hashes and request provenance are recorded
in `session_info.txt`.

## Interpretation limits

- Bibliography values are count fields only; no publication content was
  retrieved.
- Literature volume does not establish causality or target quality.
- A ChEMBL target record indicates database availability, not compound quality,
  potency, druggability, or therapeutic suitability.
- A source-native association score is not a confidence probability and was not
  used to rank genes.
- Zero means the queried API returned a count of zero. `NOT_AVAILABLE` means the
  source could not be queried because the required identifier was unavailable.

## Explicit non-claims

Task #010 generated no target rank, project score, gene or drug prioritization,
therapeutic direction, biological interpretation, or treatment recommendation.
