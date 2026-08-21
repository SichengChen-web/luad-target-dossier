# Evidence Layer Plan v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Task:** #010 — external evidence retrieval  
**Version:** v0.1  
**Date:** 21 August 2026  
**Status:** Implemented retrieval plan

## Purpose and boundaries

Task #010 adds source-native external evidence fields to every gene in the
Task #009 identifier-normalized registry. It is a retrieval and normalization
task only.

This task does not rank targets, calculate project scores, prioritize genes or
drugs, infer therapeutic direction, make therapeutic recommendations, or
interpret biological relevance. Open Targets association scores are retained
only as explicitly labeled source-native evidence values; they are not project
scores and are never used to order rows.

## Frozen inputs

The primary input is:

`outputs/identifier_normalization/identifier_mapping.csv`

It is frozen at Task #009 commit
`436436715af43a0dc69a6a51acf82b435f65cf6c` with SHA256:

`ff50b9cc50006710e681bd0d0f21fa3790becc3cd20a476dbbb6ac5459c1594e`

Task #009 did not carry the Task #008 U2 flag into its mapping CSV. Therefore,
the committed file below is used only as a read-only U2 membership reference:

`outputs/candidate_registry/candidate_registry.csv`

Its expected SHA256 is
`8055a9d99d058d219399957e62f6a3cccc3dd2217bc028d1d11dd4dc667f90e2`.
The U2 reference is joined by immutable `EnsemblID`; no expression statistic,
queue, rank, or other scientific field is imported.

The builder requires all 29,606 identifiers to match exactly between the two
files and requires exactly 14,064 U2 genes.

## Identifier policy

- Versioned Task #009 `EnsemblID` remains the immutable output key.
- Open Targets queries use only the Task #009 `OpenTargets_target_ID`.
- ChEMBL queries use only the Task #009 `ChEMBL_target_ID` values.
- Gene symbols are copied as metadata but are never query or join keys.
- No missing identifier or evidence field is rescued manually.
- Input row order is retained and has no ranking meaning.

## Official sources

Network access is restricted to:

- Open Targets Platform GraphQL API:
  `https://api.platform.opentargets.org/api/v4/graphql`
- ChEMBL data web service:
  `https://www.ebi.ac.uk/chembl/api/data/`

The Open Targets data/API versions and ChEMBL database version/release date
are retrieved from official metadata endpoints. Exact request templates,
request counts, byte counts, and hashes of response bytes are recorded in
`session_info.txt`. No package is installed or updated.

## LUAD disease identity

The pinned disease entity is:

- ID: `MONDO_0005061`
- label: `lung adenocarcinoma`

This was resolved with the official Open Targets search API before
implementation. At runtime the script retrieves the entity by exact ID and
fails unless the API returns that ID and label.

## Open Targets evidence retrieval

### Target annotation and literature counts

For every mapped Open Targets target, one batched target query retrieves:

- Open Targets target ID;
- approved name, approved symbol and biotype as source annotations;
- bibliography `count` and `filteredCount` fields only;
- `drugAndClinicalCandidates.count` as a source-native record count.

No publication rows, titles, abstracts, identifiers, snippets, or narrative
text are retrieved. The bibliography fields are stored as source-native count
fields and are not interpreted as proof of target validity.

### LUAD target–disease associations

The disease-centric `associatedTargets` endpoint is paginated to retrieve the
complete association set for `MONDO_0005061` twice:

1. `enableIndirect: false` — direct evidence only;
2. `enableIndirect: true` — evidence expanded through disease-ontology
   descendants.

These views remain separate. For each matching registry gene the layer stores:

- association presence/count;
- the source-native overall association score;
- source-native datasource and datatype scores as deterministic JSON.

Pages use the API maximum of 3,000 rows and the explicit source-native
`orderByScore: "score"` ordering. Tied scores can still yield duplicate rows at
page boundaries. The script therefore performs a bounded deterministic
recovery using page sizes 3,000, 2,999, and 2,500 as needed, unions only
byte-equivalent normalized records, and fails unless the union contains exactly
the API-reported number of unique target associations. Traversal/page sizes,
duplicate counts, and union counts are retained in session provenance.

The indirect view stores its source-native overall score separately. A zero
count means no association row was returned by that exact versioned query; it
is not a biological conclusion.

Open Targets documents the distinction between direct and indirect
associations at <https://platform-docs.opentargets.org/associations> and its
GraphQL interface at
<https://platform-docs.opentargets.org/data-access/graphql-api>.

## ChEMBL target evidence

The official ChEMBL target endpoint is fully paginated with a field projection
limited to existing target annotations:

- `target_chembl_id`;
- preferred target name;
- target type;
- organism and taxon ID;
- species-group flag.

Only target IDs already mapped in Task #009 are attached to registry rows.
Annotations for one-to-many targets are retained in a sorted JSON list; no
preferred target is selected. ChEMBL documents target records and pagination
at
<https://chembl.gitbook.io/chembl-interface-documentation/web-services/chembl-data-web-services>.

Task #010 does not retrieve compound activities, potency, mechanisms,
clinical trials, or make any inference about druggability.

## Explicit evidence states

| State | Meaning |
|---|---|
| `PRESENT` | The official API returned the mapped target/annotation |
| `NOT_MAPPED` | Task #009 provided no identifier for this source |
| `NOT_FOUND_IN_API` | A mapped identifier was queried but absent from the current API |
| `PARTIAL` | Some, but not all, one-to-many ChEMBL target IDs were returned |
| `NO_ASSOCIATION_RETURNED` | The exact LUAD association query returned no row |

Numeric zero is used only when the API successfully returned a count of zero.
Fields that could not be queried because no identifier existed use
`NOT_AVAILABLE`, not zero.

## Output structure

`evidence_registry.csv` contains one row per immutable `EnsemblID`, with:

- frozen identity and external identifier fields;
- U2 membership copied from the frozen reference;
- Open Targets target annotation and count-only literature fields;
- direct and indirect LUAD association fields;
- ChEMBL target availability and target annotations;
- explicit retrieval states and compact source labels.

`evidence_qc.csv` reports coverage and evidence-state counts for both the full
tested universe and the U2 subset. `evidence_summary.md` reports descriptive
retrieval counts without ordering or prioritization.

## Validation requirements

The build fails unless:

- exactly 29,606 unique `EnsemblID` rows remain in input order;
- the U2 reference contains and preserves exactly 14,064 genes;
- input identity and identifier fields remain unchanged;
- Open Targets returns only submitted target IDs;
- LUAD association pages are complete and contain unique target IDs;
- ChEMBL target pages are complete and contain unique target IDs;
- every queried field has explicit source and state information;
- no project score, rank, priority, recommendation, or therapeutic-direction
  field is emitted.

## Reproducibility limitations

The official APIs are evolving resources. A later rerun may yield changed
counts or annotations. Generated outputs and recorded source versions form a
reviewable evidence snapshot. Future tasks must not silently refresh this
snapshot while claiming to use Task #010 evidence.

No raw API response is committed. Hashes of concatenated response bytes in
request order, together with request templates and source metadata, allow the
retrieval session to be audited without adding large raw payloads.

## Explicit non-claims

Evidence presence, literature volume, drug/candidate record count, association
score, or ChEMBL availability does not establish causality, target quality,
druggability, safety, therapeutic direction, or clinical actionability.
