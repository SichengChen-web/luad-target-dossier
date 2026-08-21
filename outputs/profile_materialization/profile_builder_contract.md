# Deterministic Target Evidence Profile Builder Contract v0.1

## Scope

This contract specifies how a future builder must transform a frozen target manifest and evidence architecture into Task #020 long-form target-component profiles. Task #021 supplies no target manifest and creates no target profiles.

The builder is an evidence-organization component. It must not perform biological analysis, reinterpret source records, infer missing linkages, aggregate component states, or generate therapeutic conclusions.

## Required frozen inputs

A future materialization requires one hash-pinned run manifest containing:

1. immutable target-universe manifest with unique EnsemblIDs and explicit target order;
2. Task #020 profile schema, component registry, and interpretation rules;
3. Task #019 evidence-type interpretation boundaries and decision contexts;
4. controlled evidence ontology and source lineage;
5. bounded claim registry;
6. atomic evidence-record registry;
7. source-entity/version registry;
8. missingness/uncertainty registry;
9. record dependency graph;
10. Task #018-style artifact manifest with path/URI, size, SHA256, generator, and dependencies; and
11. versioned run configuration containing profile version, generator version, rules hash, input-manifest hash, frozen materialization timestamp, and serialization format.

No gene symbol may replace EnsemblID or be used as a fallback join. A missing artifact, identifier, version, required field, or hash is a hard failure unless the profile schema explicitly represents the condition as missingness.

## Cardinality and identity

For `N` frozen targets, materialization creates exactly `N × 11` component rows. The unique row key is `(EnsemblID, component_id)`. Target order comes from the frozen target manifest; component order comes from Task #020. No target or component may be silently omitted.

`profile_id` is deterministic:

```text
SHA256(EnsemblID + "|" + profile_version + "|" + input_manifest_hash + "|" + rules_hash)
```

No random UUID, process ID, filesystem traversal order, locale, or wall-clock value may affect profile content.

## Evidence selection

For each target-component row:

1. select bounded claims by immutable EnsemblID and controlled component domain;
2. select linked records by claim ID and acceptable component evidence type/record role;
3. preserve stable claim, record, and source IDs;
4. validate each record against the frozen source/version and artifact hash;
5. attach source-specific missingness and uncertainty without recoding;
6. induce the dependency subgraph among linked records;
7. preserve unknown dependencies as unknown; and
8. evaluate the component-specific state predicates in frozen precedence.

Records are deduplicated only when `record_id` is identical. Similar values, shared targets, matching symbols, repeated publications, or related database fields are not sufficient grounds for deletion or merging.

## Deterministic state resolution

Each component uses the exact Task #020 vocabulary. Predicates are evaluated in this order:

1. `CONFLICTING`
2. `OBSERVED`
3. `MISSING`
4. `PARTIAL`
5. `NOT_QUERIED`

The first satisfied, fully validated predicate is emitted. Exactly one state must resolve.

### CONFLICTING

Requires a component-specific, prespecified comparison rule and traceable incompatible records. Conflict takes precedence over otherwise observed evidence. Every conflicting record remains in the profile.

### OBSERVED

Requires the component-specific qualifying evidence criterion, complete minimum provenance, no material conflict, and valid record/source/artifact links. Record presence alone is insufficient.

### MISSING

Requires completion of every source/query scope defined for the component, zero qualifying evidence, and no unknown coverage, retrieval failure, or unresolved identifier problem. `MISSING` is absence of qualifying evidence in the frozen scope, not negative biological evidence.

### PARTIAL

Applies when some assessment or evidence exists but the observed or missing predicate cannot be satisfied because coverage, linkage, provenance, source version, quality characterization, or dependency resolution is incomplete. `UNKNOWN` with any attempted assessment resolves here unless a defined conflict takes precedence.

### NOT_QUERIED

Applies only when no eligible evidence acquisition or assessment occurred for the component. It cannot be inferred from a zero value, blank field, or identifier failure hidden as absence.

## Provenance propagation

Every profile row must carry:

- claim IDs;
- evidence-record IDs;
- source-entity IDs;
- source versions;
- input artifact IDs;
- input SHA256 hashes;
- missingness and uncertainty categories;
- dependency relationships and qualitative levels;
- conflict status and rationale;
- provenance-completeness state;
- generator/rules versions; and
- frozen materialization timestamp.

Pipe-delimited identifiers are unique and lexically sorted. Empty lists use the explicit sentinel `NONE`. Counts reconcile to the propagated record IDs and remain audit metadata only.

## Dependency preservation

The builder computes the induced dependency subgraph among component records. It never infers independence from the absence of an edge. `UNKNOWN` remains `UNKNOWN`. Reusing one record in multiple profile components preserves the same record ID and source/dependency lineage and does not create another observation.

No source, column, modality bucket, candidate count, publication count, compound, or trial may be treated as an independent vote without an explicit reviewed dependency assertion.

## Explicit non-inference rules

The builder must not:

- combine component states into an overall state, score, weighted sum, or ordering;
- compute a completeness percentage;
- upgrade evidence maturity automatically because a record, source, or component was added;
- convert `MISSING`, `NOT_FOUND`, `NOT_QUERIED`, `UNKNOWN`, or retrieval failure into negative biological evidence;
- interpret `OBSERVED` as favorable evidence;
- treat record quantity as evidence quality;
- treat dependent or unknown-lineage records as independent;
- infer intervention–target–disease linkage from co-occurrence or counts;
- infer causality, efficacy, safety, clinical benefit, target selection, or therapeutic conclusions; or
- use an LLM or free-text judgment to resolve a deterministic state.

`maturity_description` is generated from fixed qualitative templates naming characterized and unresolved elements. It cannot change the component state or produce an aggregate assessment.

## Canonical serialization

Future CSV output must use:

- UTF-8;
- LF line endings;
- comma delimiter;
- RFC-compatible quoting;
- Task #020 header in numeric `field_order`;
- target order then component order;
- base-10 integers without grouping;
- `TRUE`, `FALSE`, or `UNKNOWN` booleans;
- ISO8601 UTC timestamp copied from frozen run configuration;
- lexically sorted unique pipe-delimited lists; and
- `NONE` for empty required list/text fields.

The wall clock must not populate `generated_at_utc`. A repeated run with identical inputs, generator version, rule hashes, frozen timestamp, and serialization version must produce byte-identical output.

## QC and release gate

Before release, validate:

- all input hashes before and after generation;
- unique EnsemblIDs and profile IDs;
- exactly 11 component rows per target;
- unique `(EnsemblID, component_id)` keys;
- controlled states and exactly one resolved state per component;
- all claims/records/sources/dependencies resolve;
- record counts reconcile to propagated IDs;
- all required provenance fields are explicit;
- no forbidden assessment fields exist;
- canonical row/header/list order;
- output SHA256; and
- byte-identical recovery generation.

Any failure stops release. The builder must not repair, substitute, drop, reorder, or reinterpret evidence silently.
