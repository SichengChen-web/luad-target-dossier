# Identifier Normalization Plan v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Task:** #009 — identifier normalization  
**Version:** v0.1  
**Date:** 21 August 2026  
**Status:** Implemented mapping plan

## Purpose and boundaries

Task #009 creates an auditable identifier layer for every gene in the
Task #008 candidate registry. It connects the immutable, versioned Ensembl
identifier to identifier systems needed by later evidence retrieval.

This task does not rank genes, calculate target or therapeutic scores, infer
therapeutic direction, prioritize drugs, or interpret biological relevance.
A missing external identifier is a mapping result, not negative biological
evidence.

## Frozen input

The sole registry input is
`outputs/candidate_registry/candidate_registry.csv`. The committed Task #008
base is `c420cbe07715a15000dbf2d4c7d9f2dc3fb7c662`, and the expected input
SHA256 is
`8055a9d99d058d219399957e62f6a3cccc3dd2217bc028d1d11dd4dc667f90e2`.

The script requires this commit to be an ancestor of the current `main`
branch and requires the registry to remain unchanged relative to that commit.
The registry must contain exactly 29,606 rows and unique `EnsemblID` values.

## Immutable identifier policy

- `EnsemblID` is the immutable primary key and is copied without alteration.
- `EnsemblID_base`, `Symbol`, and `gene_type` are copied from Task #008.
- `EnsemblID_base` is the only mapping key used for HGNC and Open Targets.
- Gene symbols are never used to infer or rescue a mapping.
- Symbols may be compared after an exact identifier match as a QC check only.
- External identifiers are added in separate fields; no identifier replaces
  another.
- Multiple identifiers are sorted, deduplicated, and joined with `|`.
- An absent mapping is written explicitly as `NOT_FOUND`.

## Authoritative mapping sources

### HGNC, Entrez, and UniProt

The script downloads the HGNC complete approved-gene TSV from:

`https://storage.googleapis.com/public-download-files/hgnc/tsv/tsv/hgnc_complete_set.txt`

Exact `ensembl_gene_id` values retrieve `hgnc_id`, `entrez_id`, and
`uniprot_ids`. Response date, ETag, byte size, and SHA256 are recorded in
`session_info.txt`. HGNC documents the complete set and field definitions at
<https://hgnc.genenames.org/download/>.

### Open Targets

Open Targets uses the Ensembl gene ID as its primary human target identifier.
The script verifies actual presence by batch-querying exact `EnsemblID_base`
values through:

`https://api.platform.opentargets.org/api/v4/graphql`

Only the returned target `id` is retained. No association, tractability, drug,
or disease evidence is requested. Platform data and API versions are recorded.
The identifier convention is documented at
<https://platform-docs.opentargets.org/target>.

### ChEMBL

The script enumerates current human target components from:

`https://www.ebi.ac.uk/chembl/api/data/target_component.json`

The query is restricted to human components (`tax_id=9606`) and projected to
component accession, component ID, and linked ChEMBL target IDs. Registry genes
are joined to these records only through UniProt accessions obtained from the
exact HGNC–Ensembl mapping. Gene symbols are not used. ChEMBL version and
release date come from its official status endpoint. Pagination is documented
at <https://chembl.gitbook.io/chembl-interface-documentation/web-services/chembl-data-web-services>.

A gene may legitimately occur in several ChEMBL target records, including
single proteins and protein complexes. All such records are retained; no
preferred target is chosen.

## Mapping status vocabulary

Each external identifier has a corresponding status and source field.

| Status | Meaning |
|---|---|
| `UNIQUE` | Exactly one identifier was obtained through the declared route |
| `ONE_TO_MANY` | Multiple valid identifiers were obtained and all are retained |
| `AMBIGUOUS` | The exact Ensembl mapping matched multiple HGNC records, so downstream attribution is not uniquely resolved |
| `NOT_FOUND` | The declared source and route were queried but returned no mapping |

`ONE_TO_MANY` is not automatically an error. It is separated from
`AMBIGUOUS` because several UniProt accessions or ChEMBL targets may be valid
representations of one gene. Row-level `one_to_many_fields`,
`ambiguous_mapping`, and `ambiguous_fields` make these cases auditable.

## Output columns

`identifier_mapping.csv` contains:

- the four frozen input identity fields;
- `HGNC_ID`, `Entrez_ID`, `UniProt_ID`, `OpenTargets_target_ID`, and
  `ChEMBL_target_ID`;
- one status and one source field per external identifier;
- the ChEMBL join basis and matched UniProt accessions;
- post-mapping symbol QC status;
- row-level one-to-many and ambiguity fields;
- a conservative note where needed.

Compact source labels are used in the CSV. Exact URLs, source versions,
retrieval timestamps, request counts, byte counts, and response hashes are
stored in `session_info.txt`.

## Quality control

The build fails unless:

- all 29,606 Task #008 genes remain present exactly once and in input order;
- `EnsemblID` remains unchanged and unique;
- required input identity fields are populated;
- every external mapping has a status and source;
- all missing mappings equal `NOT_FOUND` rather than an empty value;
- Open Targets returns only submitted Ensembl IDs;
- ChEMBL mappings arise from exact UniProt accession joins;
- no score, rank, priority, or therapeutic-interpretation field is emitted.

`mapping_qc.csv` reports mapping and status counts for the full U0 tested
universe and the U2 evidence-candidate subset. `mapping_summary.md` explains
coverage and warnings in human-readable form.

## Network and reproducibility statement

Network access is required because Task #009 uses current official identifier
resources and no frozen mapping tables were present locally. No package is
installed or updated. Raw responses are processed in memory and are not added
to the repository. Their content hashes and release metadata are recorded so
the retrieval session can be audited.

Because HGNC, Open Targets, and ChEMBL evolve, a later rerun may produce a
different mapping. The generated CSVs and recorded source versions form a
versioned mapping snapshot for review. Future milestones must not silently
refresh mappings while claiming to use this snapshot.

## Explicit non-claims

An identifier match does not establish disease relevance, causality,
druggability, therapeutic direction, safety, clinical actionability, or
novelty. A ChEMBL mapping only establishes that a gene-associated component
occurs in a ChEMBL target record; it does not establish compound quality or
therapeutic suitability.
