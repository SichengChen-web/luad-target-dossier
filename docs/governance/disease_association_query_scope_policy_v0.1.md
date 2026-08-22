# Disease Association Query Scope Policy v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Version:** v0.1  
**Component:** `COMP_DISEASE_ASSOCIATION`  
**Status:** Frozen governance policy; no query scope registered or executed

## 1. Purpose

This policy defines how the entity universe, disease context, query parameters, filters, coverage, and retrieval provenance must be frozen before disease-association evidence retrieval can be authorized.

It does not define a live endpoint, execute a query, retrieve records, or create evidence artifacts.

## 2. Query-scope identity

Every query scope must define:

- `query_scope_id`;
- `query_scope_version`;
- `component_id` and `component_version`;
- `source_id`, `source_version`, and release identity;
- `entity_universe_id` and universe artifact SHA256;
- `disease_context_id`, ontology, and ontology version;
- `mapping_rule_version`;
- canonical query template or bulk-selection rule;
- parameter and filter manifest;
- requested field set;
- pagination, batching, ordering, and retry contract;
- retrieval software/version identity;
- expected source-role coverage;
- completeness criteria;
- review status.

Any change to these fields requires a new query-scope version.

## 3. Entity-universe requirements

The entity universe must be an immutable manifest containing:

- exact `EnsemblID` values;
- canonical order and universe ordinal;
- universe version;
- source artifact ID, size, and SHA256;
- inclusion basis;
- explicit absence of symbol-based joins;
- expected entity count;
- duplicate-identity assertion;
- relation to the containing Target Evidence Profile universe.

No biological filtering, evidence-availability filtering, candidate selection, or target prioritization may occur during query-scope construction.

If the frozen Task #030 universe is selected in a future review, the query scope must preserve its exact 29,606 `EnsemblID` entities and canonical order. This policy does not itself select that universe.

The current `entity_universe_id` remains `UNASSIGNED_PENDING_QUERY_SCOPE_REVIEW`.

## 4. Disease-context requirements

The query scope must reference one frozen disease-context artifact satisfying [Disease Context Definition Policy v0.1](disease_context_definition_policy_v0.1.md).

Required context fields are:

- `disease_context_id`;
- ontology;
- ontology version;
- mapping-rule version;
- inclusion-boundary version;
- exclusion-boundary version;
- context artifact ID and SHA256.

The query must not use a free-text label, inferred synonym, current ontology alias, or mutable hierarchy lookup as the runtime disease identity.

## 5. Query model requirements

A future source-specific query scope must select and document one retrieval model:

- target-by-target query;
- disease-first query followed by exact universe filtering;
- versioned bulk-source extraction;
- another reviewed deterministic model.

The selected model must specify how result completeness and equivalence are tested. If multiple query models are used, their records and query provenance remain distinguishable.

## 6. Query parameters

The parameter manifest must record every explicit and implicit parameter, including:

- target identifier and identifier namespace;
- disease identifier and ontology namespace;
- requested evidence/record type fields;
- response-field selection;
- result limits;
- sorting/order parameters;
- pagination cursor or page rules;
- batch size;
- language or locale where relevant;
- endpoint or bulk table identity;
- include/exclude flags;
- source defaults that affect returned content;
- API or data-model version headers;
- authentication mode without storing secrets;
- timeout and retry behavior as retrieval control metadata.

Unrecorded server defaults are not acceptable when they affect record content or coverage.

## 7. Filter requirements

Every filter must be registered with:

- stable `filter_id`;
- field and operator;
- exact value or value-set artifact;
- purpose;
- inclusion or exclusion effect;
- missing-value behavior;
- source semantics version;
- deterministic application order;
- review status.

Filters may implement the frozen disease context and source record contract. They must not implement association-strength thresholds, confidence cutoffs, target-quality rules, rankings, priorities, or candidate selection.

No record may be excluded because it appears weak, uninteresting, non-actionable, or biologically implausible.

## 8. Requested record fields

The query scope must request or preserve fields needed to support:

- source target and disease identity;
- source record identity;
- record granularity;
- source evidence-type identity where present;
- raw payload preservation;
- record/source/release provenance;
- mapping provenance;
- dependency classification;
- null and missingness interpretation;
- duplicate and replacement handling;
- license attribution where record-specific.

Source-native fields outside the normalized feature contract may be captured in raw records. Requesting a source-native metric does not authorize normalized use.

## 9. Coverage and completeness contract

The scope must define completion at three levels:

### 9.1 Scope-level completeness

Every declared source partition, table, endpoint, evidence type, and disease-context route completed under the frozen rules.

### 9.2 Entity-level completeness

Every `EnsemblID` has a query-scope ledger entry distinguishing:

- attempted and completed;
- attempted with records returned;
- attempted with zero records returned;
- attempted but failed;
- not queried;
- target mapping unresolved;
- disease mapping unresolved;
- coverage unknown.

### 9.3 Record-level completeness

Every returned record has stable identity, raw artifact location, source/release provenance, and required role mapping.

Zero records returned is not equivalent to query failure, not queried, mapping failure, or unknown coverage.

## 10. Pagination, batching, and ordering

The query scope must freeze:

- pagination start and termination rules;
- cursor persistence;
- page/batch ordering;
- deterministic entity batching;
- duplicate records across pages;
- incomplete-page detection;
- rate-limit response behavior;
- retry count and backoff policy;
- terminal failure behavior;
- canonical raw artifact and record ordering.

Retries must preserve attempt provenance. A successful retry does not erase prior failures.

## 11. Retrieval provenance

Every query, batch, or bulk selection must preserve:

- query/batch ID;
- query-scope version;
- source and release identity;
- target entity or universe partition;
- disease context;
- exact parameters and filters;
- request identity or canonical request hash;
- response artifact ID, size, and SHA256;
- attempt and completion status;
- retrieval timestamp in UTC;
- response metadata needed to establish version and completeness;
- retry and failure history;
- retrieval implementation version.

Secrets, credentials, and tokens must never be written into retrieval provenance.

## 12. Raw-versus-normalized boundary

Query scope governs what raw source material is captured. It does not define normalized feature values beyond the already reviewed component feature contract.

Raw records may preserve all requested source-native values. Normalization must:

- consume only the frozen snapshot;
- use the reviewed feature contract and versioned extractor;
- preserve raw record and artifact references;
- retain controlled missingness and dependency;
- exclude unregistered source fields from normalized output;
- avoid biological interpretation or evaluation.

## 13. Query-scope version changes

A new `query_scope_version` and new source snapshot are required when any of the following changes:

- entity universe or order;
- disease context or mapping rule;
- source version or release;
- query model, endpoint, table, or bulk-selection rule;
- requested fields;
- parameters, filters, defaults, or value sets;
- pagination, batching, sorting, or retry behavior affecting coverage;
- record-role mapping;
- completeness criteria;
- retrieval implementation behavior.

## 14. Runtime prohibitions

Prohibited:

- runtime API dependence after the separately authorized snapshot retrieval;
- querying a live source during extraction, component generation, profile materialization, or evidence-landscape generation;
- using mutable latest aliases without captured exact release identity;
- query changes based on returned gene identity, association metric, perceived importance, or target promise;
- gene-symbol joins or manual disease mapping;
- dynamic filters chosen by an LLM;
- scoring, ranking, target prioritization, therapeutic recommendation, or biological interpretation.

## 15. Current disposition

No source, entity universe, disease context, query template, parameter set, filter set, retrieval implementation, or query-scope version is selected or executed by this policy.

The document is a future registration template, not an instruction to access a database.

## 16. Query-scope checklist

- [ ] Source and exact release are approved.
- [ ] Entity-universe manifest, count, order, and SHA256 are frozen.
- [ ] Disease context, ontology, version, and mapping rules are frozen.
- [ ] Query model, parameters, fields, and filters are complete.
- [ ] Pagination, batching, ordering, and retry semantics are deterministic.
- [ ] Per-entity and record-level completeness criteria are defined.
- [ ] Retrieval provenance excludes secrets and preserves attempts/failures.
- [ ] Raw source capture remains separate from normalized features.
- [ ] No evaluative or biologically adaptive filter is present.
- [ ] Runtime materialization requires no live source.
- [ ] Retrieval has a separate human governance authorization.

## 17. Related policies

- [Disease Association Source Contract v0.1](disease_association_source_contract_v0.1.md)
- [Disease Context Definition Policy v0.1](disease_context_definition_policy_v0.1.md)
- [Disease Association Snapshot Policy v0.1](disease_association_snapshot_policy_v0.1.md)
- [Disease Association Component Registration v0.1](disease_association_component_registration_v0.1.md)
