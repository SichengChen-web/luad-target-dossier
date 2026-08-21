# Target Evidence Profile Materialization Framework v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Task:** #021 — deterministic profile materialization contract  
**Version:** v0.1  
**Date:** 21 August 2026  
**Status:** Working materialization specification

## Purpose

Task #021 defines how a future software builder must transform frozen evidence records into the Task #020 long-form target evidence profile. It specifies required inputs, component-specific state resolution, provenance propagation, dependency preservation, canonical generation, QC, and release failure behavior.

No target universe is supplied in this task. Therefore no target profile or gene-level profile row is created.

## Scientific separation

The future builder is a deterministic evidence-organization component. It may:

- validate frozen evidence artifacts;
- join immutable IDs;
- organize claims and records into controlled profile components;
- copy missingness, uncertainty, and dependencies;
- resolve component states under reviewed predicates; and
- serialize and hash the resulting profile.

It may not reinterpret source evidence, invent linkages, generate new biological evidence, aggregate components, or form therapeutic conclusions.

## Frozen foundation

Task #021 hash-pins:

- Task #018 artifact governance and reproducibility contract;
- Task #019 decision contexts and evidence-type interpretation boundaries; and
- Task #020 profile schema, component registry, and interpretation rules.

The builder also validates every one of the 193 Task #018 governed artifacts, including the 139,836,748-byte Task #014 evidence-record registry with SHA256 `76ec5056fb4e468176073073532204d231765d4f0cd70dbb6cfe4ad8bf752343`.

## Future input contract

A materialization run requires a single frozen input manifest containing:

1. target-universe manifest keyed only by EnsemblID, with explicit order;
2. Task #020 28-field profile schema;
3. Task #020 11-component registry;
4. Task #019–#020 interpretation rules;
5. ontology domains and evidence types;
6. bounded claims;
7. atomic evidence records;
8. source entities and versions;
9. missingness and uncertainty records;
10. dependency graph;
11. artifact IDs, locations, sizes, SHA256 hashes, and generators; and
12. versioned run configuration.

The run configuration freezes `profile_version`, generator version, rule hash, input-manifest hash, materialization snapshot time, and serialization version.

Symbols cannot replace EnsemblID or be used for fallback joins. All source-native IDs remain attached to their records.

## Materialization sequence

```text
validate frozen input manifest and hashes
                    ↓
validate target, schema, component, evidence, and provenance vocabularies
                    ↓
create exactly 11 component slots per EnsemblID
                    ↓
link bounded claims and acceptable atomic evidence records
                    ↓
propagate source, version, artifact, missingness, uncertainty, and dependencies
                    ↓
resolve one component state under component-specific predicates
                    ↓
serialize in canonical order and format
                    ↓
run QC, repeat generation, compare bytes, and freeze output SHA256
```

Any failed validation stops release. The builder cannot silently repair, substitute, discard, or reinterpret data.

## Component input contracts

`component_state_resolution_registry.csv` names the exact current or future source-record roles and acceptable Task #013 evidence types for every component.

Current source-record roles are:

- `TRANSCRIPT_PRIMARY`;
- `TRANSCRIPT_ROBUSTNESS`;
- `OT_LUAD_ASSOCIATION`;
- `OT_DRUG_CANDIDATE`;
- `CHEMBL_TARGET_ANNOTATION`;
- `OT_TRACTABILITY_SUMMARY`; and
- `OT_SAFETY_SUMMARY`.

Future roles are named explicitly for genetics, functional dependency, compound-target evidence, trial-level development, and clinical linkage. Their presence in a contract is not evidence that those records currently exist.

For every component, the registry records:

- required evidence-record roles;
- acceptable evidence types;
- the predicate for each allowed state;
- required provenance;
- missingness handling;
- dependency preservation; and
- required state rationale.

## Deterministic component state resolution

Every component supports the Task #020 states:

- `OBSERVED`;
- `PARTIAL`;
- `MISSING`;
- `NOT_QUERIED`;
- `CONFLICTING`.

Predicates are evaluated in this frozen order:

1. `CONFLICTING`
2. `OBSERVED`
3. `MISSING`
4. `PARTIAL`
5. `NOT_QUERIED`

Exactly one state must resolve.

### CONFLICTING

Requires materially incompatible records under a component-specific comparison rule. It takes precedence over otherwise observed evidence. Conflict records are retained, not averaged or deleted.

### OBSERVED

Requires the component-specific qualifying record pattern, complete minimum provenance, valid claim/source/artifact links, and no material conflict. A record or nonzero count alone is insufficient.

### MISSING

Requires successful completion of every defined source/query scope for the component with zero qualifying evidence and no unresolved identifier, coverage, retrieval, or provenance problem. Missing is not negative evidence.

### PARTIAL

Requires at least some assessment or evidence, while coverage, record linkage, evidence-type criterion, provenance, version, quality characterization, or dependency resolution remains incomplete. `UNKNOWN` after an attempted assessment resolves here unless a defined conflict takes precedence.

### NOT_QUERIED

Requires that no eligible acquisition or assessment occurred. It cannot be inferred from zero, blank, unmapped, failed, or missing values.

## Important component-specific boundaries

- Transcriptomic `OBSERVED` requires primary and robustness records; S0–S6 remain one dependent TCGA evidence family.
- Disease association distinguishes returned association evidence from literature-only or incomplete datasource context.
- Genetics and functional dependency remain `NOT_QUERIED` until dedicated acquisitions exist.
- Pharmacology target annotations or candidate counts resolve at most `PARTIAL`; compound-target assay/mechanism evidence is needed for `OBSERVED`.
- Tractability modalities share one framework and cannot become multiple votes.
- Safety `MISSING` never means safe.
- Clinical development requires trial-level intervention–target–disease linkage; platform counts are insufficient.
- Human evidence must be explicitly human-derived in cohort or trial provenance.
- Clinical linkage requires a traceable linked record chain and cannot be inferred from co-occurring records.
- Risk context reuses the safety record lineage and separately states absent normal-tissue, essentiality, exposure, and toxicology evidence in its maturity description.

## Provenance propagation

Every materialized component row must preserve:

- claim IDs;
- evidence-record IDs;
- source-entity IDs;
- source versions;
- artifact IDs;
- artifact SHA256 hashes;
- missingness and uncertainty states;
- dependency relationships and qualitative levels;
- conflict status and explanation;
- provenance-completeness status;
- generator and rule versions; and
- frozen materialization time.

Identifiers are unique and lexically sorted within pipe-delimited lists. Empty required collections use `NONE`. Counts must reconcile to IDs and remain audit fields rather than quality measures.

## Dependency preservation

For each component, the builder induces the dependency subgraph among linked records. The graph is propagated without converting qualitative relationships into numbers.

- An absent dependency edge does not prove independence.
- `UNKNOWN` remains unknown.
- Reusing a record across components preserves the same record ID.
- Shared sources, datasets, publications, compounds, trials, and platform records are not independent votes.
- Deduplication occurs only by identical stable record ID unless a separate reviewed provenance task creates an explicit equivalence assertion.

## Deterministic identity, time, and serialization

The future `profile_id` is:

```text
SHA256(EnsemblID | profile_version | input_manifest_hash | rules_hash)
```

The profile contains exactly 11 rows per target, ordered by frozen target order and then Task #020 component order.

Output is canonical UTF-8 CSV with LF line endings, fixed header order, comma delimiter, RFC-compatible quoting, base-10 integers, controlled booleans, sorted list values, and explicit `NONE` sentinels.

`generated_at_utc` comes from the frozen run configuration. It must not read the wall clock during profile generation. Randomness, locale, process ID, filesystem traversal order, symbols, and LLM/free-text judgment cannot influence materialized content.

The same frozen inputs, generator version, rules, frozen timestamp, and serialization version must produce byte-identical output.

## Explicit non-inference rules

The future builder must not:

- combine components into any score, total, ordering, or overall state;
- calculate a completeness percentage;
- upgrade maturity automatically when records are added;
- convert missing, not found, not queried, unknown, or failed retrieval into negative evidence;
- interpret observed evidence as favorable evidence;
- use record quantity as quality or confidence;
- treat dependent or unknown-lineage records as independent;
- infer clinical linkages from co-occurrence;
- infer causality, efficacy, safety, clinical benefit, target selection, or therapeutic conclusions; or
- let an LLM resolve component states.

`maturity_description` uses deterministic qualitative templates and cannot change component state.

## QC and release contract

Release requires:

- matching input hashes before and after generation;
- unique EnsemblIDs and profile IDs;
- exactly 11 rows per target;
- unique EnsemblID/component keys;
- one controlled state per component;
- valid claim/record/source/dependency links;
- complete required provenance or explicit incomplete state;
- reconciled record counts;
- canonical ordering and serialization;
- absence of assessment fields;
- output SHA256; and
- byte-identical repeat generation.

Any failure blocks release. Task #021 itself performs no profile population, gene evaluation, network access, package installation, commit, or push.
