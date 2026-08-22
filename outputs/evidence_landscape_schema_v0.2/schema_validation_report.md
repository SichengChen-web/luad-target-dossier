# Multi-component Evidence Landscape v0.2 schema validation report

**Task:** #033B-1  
**Schema version:** `EVIDENCE_LANDSCAPE_SCHEMA_V0.2`  
**Validation status:** PASS

## Scope

This report validates the machine-readable schema contract only. No landscape records, profiles, evidence, scores, ranks, priorities, recommendations, or interpretations were generated.

## Contract validation

| Check | Result |
|---|---|
| JSON Schema Draft 2020-12 declaration | PASS |
| Task #033A governance hashes and required terminology | PASS |
| Task #032C source-profile identity and component order | PASS |
| Immutable versioned `EnsemblID` required | PASS |
| Landscape identity tuple represented explicitly | PASS |
| Source-profile identity and content hash required | PASS |
| Exactly two ordered component references required | PASS |
| Component versions and five structural states represented | PASS |
| Feature and missingness references represented | PASS |
| Record-level provenance and dependency references required | PASS |
| Limitation references represented | PASS |
| Closed object schemas | PASS (29) |
| Prohibited fields rejected at closed object boundaries | PASS (7 names) |
| Frozen relevant prior-artifact hashes unchanged | PASS |
| In-memory double generation byte-identical | PASS |
| Network access | PROHIBITED; NOT USED |
| Package installation | PROHIBITED; NOT PERFORMED |
| Runtime AI decisions | PROHIBITED; NONE USED |
| Landscape payload generation | PROHIBITED; NONE GENERATED |

## Controlled vocabularies

Component states: `OBSERVED`, `PARTIAL`, `CONFLICTING`, `MISSING`, `NOT_QUERIED`.

Feature missingness: `OBSERVED`, `NOT_FOUND`, `NOT_QUERIED`, `NOT_APPLICABLE`, `UNKNOWN`.

## Prohibited fields

The strict, closed schema does not declare and therefore rejects: `score`, `ranking`, `priority`, `confidence`, `overall_state`, `recommendation`, and `interpretation`.

## Artifact identity

- Schema SHA256: `a52109fb90fda2493d99f20f51dacbf987a394678c90ee9e5d6c58a7afbc62ba`
- Schema byte size: `24022`
- Generator version: `LANDSCAPE_SCHEMA_CONTRACT_GENERATOR_V0.1`

## Boundary

This PASS establishes schema-contract conformance only. It does not validate or authorize a future landscape payload, release, lifecycle transition, or scientific interpretation.
