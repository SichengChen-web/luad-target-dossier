# Identifier Mapping Summary

**Task:** #009  
**Input genes retained:** 29,606 / 29,606  
**U2 evidence candidates retained:** 14,064 / 14,064  
**Primary key:** immutable versioned `EnsemblID`

## Mapping coverage

| Identifier | All tested genes | U2 genes | One-to-many, all genes | Ambiguous, all genes |
|---|---:|---:|---:|---:|
| HGNC | 24,474 (82.67%) | 11,647 (82.81%) | 0 | 1 |
| Entrez | 24,268 (81.97%) | 11,544 (82.08%) | 0 | 1 |
| UniProt | 17,699 (59.78%) | 8,441 (60.02%) | 44 | 0 |
| Open Targets | 28,893 (97.59%) | 13,691 (97.35%) | 0 | 0 |
| ChEMBL target | 5,963 (20.14%) | 2,767 (19.67%) | 1,465 | 0 |

`NOT_FOUND` is an explicit mapping result and does not mean that a gene lacks
biological relevance. Multiple identifiers are retained with `|`; the script
does not choose a preferred identifier.

## Quality-control observations

- Duplicate output `EnsemblID` values: **0**
- Missing registry rows: **0**
- Rows with at least one ambiguous mapping: **1**
- Rows with at least one one-to-many mapping: **1,501**
- Registry symbols differing from the current uniquely matched HGNC symbol:
  **3,531**

Symbol differences are warnings only. Symbols were never mapping keys and no
symbol-based rescue was attempted.

## Source snapshot

- HGNC complete set: last modified `Tue, 18 Aug 2026 12:31:23 GMT`;
  SHA256 `4ad72ffc6bca0d0858bb7234cfb3c7b1fb10e8e693e2f8d5c0842b4cfb03e748`.
- Open Targets Platform: data `26.06`;
  API `26.6.3`.
- ChEMBL: `ChEMBL_37`, released
  `2026-05-01`.

Network access was used only for these official identifier resources. No
package was installed or updated. Raw responses were processed in memory; URL,
request-count, byte-count, version, and response-hash provenance are recorded
in `session_info.txt`.

## Warnings and interpretation limits

- These are current external mappings applied to the older GENCODE v26 gene
  universe, so retired or changed records are expected.
- A ChEMBL one-to-many mapping can reflect single-protein, complex, family, or
  other target records. Task #009 does not select among them.
- The ChEMBL route requires an exact HGNC-supplied UniProt accession; genes
  without that bridge remain `NOT_FOUND` rather than being guessed by symbol.
- Source databases evolve. This output and its recorded versions constitute a
  snapshot and must not be silently refreshed in later analyses.

## Explicit non-claims

No target score, ranking, drug prioritization, therapeutic direction, or
biological interpretation was generated. Identifier coverage is not evidence
of target quality or actionability.
