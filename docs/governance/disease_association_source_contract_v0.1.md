# Disease Association Source Contract v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Version:** v0.1  
**Component:** `COMP_DISEASE_ASSOCIATION`  
**Status:** Frozen governance contract; no source selected and no retrieval authorized

## 1. Purpose

This contract defines the eligibility, registration, provenance, versioning, and reproducibility requirements that a future disease-association source must satisfy before evidence ingestion can be proposed.

It does not select a provider, authorize a database query, access an API, download evidence, create a source snapshot, implement an extractor, or materialize a component.

Registration does not authorize retrieval.

The source contract governs record representation only. Source inclusion does not validate disease causality, target importance, therapeutic relevance, target suitability, or evidence quality.

## 2. Compatibility boundary

This contract implements the Task #032A universal component interface for the Task #032B-1 registration:

- `component_id = COMP_DISEASE_ASSOCIATION`;
- `component_version = COMP_DISEASE_ASSOCIATION_V0.1`;
- immutable target identity is exact `EnsemblID`;
- feature values follow the reviewed Task #032B-1 feature contract;
- component states and feature missingness remain separate;
- record-level provenance and dependency are mandatory;
- materialization must use a frozen source snapshot rather than a runtime source response.

No field in this contract authorizes scoring, ranking, confidence metrics, target prioritization, target quality, biological interpretation, or therapeutic recommendations.

## 3. Source eligibility requirements

A future source is eligible for review only if it satisfies all requirements below.

### 3.1 Stable identifiers

The source must provide or permit deterministic preservation of:

- source identity and governing authority;
- source target identifiers and identifier namespace;
- source disease identifiers and disease ontology or vocabulary;
- source evidence-record identifiers, or immutable payloads from which deterministic record IDs can be derived;
- source evidence-type identifiers where present;
- release, version, or snapshot identity.

Gene symbols alone are not sufficient target identifiers. Free-text disease labels alone are not sufficient disease identifiers.

### 3.2 Documented record semantics

The source must document, or expose enough official metadata to freeze:

- what one returned disease-association record represents;
- whether records are source-atomic or source-aggregate;
- how target and disease entities are linked;
- evidence-type field semantics;
- null, absent, redacted, and not-applicable values;
- duplicate, replacement, obsolete, and withdrawn record behavior;
- pagination, ordering, filtering, and aggregation behavior;
- whether source-native numeric values are raw measurements, aggregate metrics, display values, or derived source outputs.

Undocumented numerical fields must remain raw and must not become normalized features.

### 3.3 Provenance availability

The source must allow each retrieved record to be traced to:

- source ID and source version;
- release identity or release metadata;
- retrieval method and query scope;
- raw artifact and record location;
- source target and disease identifiers;
- record identity and record granularity;
- applicable source evidence-type identity;
- license or terms governing storage and reuse.

If record-level provenance cannot be preserved, the source is ineligible for component ingestion.

### 3.4 Versioning and release stability

The source must expose at least one reproducible version boundary:

- named release;
- dated immutable dump;
- versioned endpoint response contract plus immutable captured responses;
- official snapshot or archive with checksums;
- another reviewed mechanism that distinguishes content changes.

A mutable endpoint without capturable release, response, or artifact identity is not eligible for governed materialization.

### 3.5 Reproducibility

The source must support capture of:

- exact query or bulk-extraction specification;
- all parameters, filters, pagination, and response fields;
- source version and release information;
- raw response bytes or immutable bulk artifact;
- retrieval metadata;
- artifact sizes and SHA256 checksums;
- license information;
- completeness and failure ledger.

Future component extraction must be reproducible from the captured snapshot without contacting the source again.

### 3.6 License and retention

Before retrieval, governance review must confirm:

- license name or terms identifier;
- license version or effective date where available;
- permitted local storage and redistribution;
- attribution requirements;
- restrictions on derived artifacts;
- whether raw records may enter external immutable storage;
- whether public release is permitted;
- license evidence artifact and checksum.

If licensing does not permit the required snapshot and audit model, the source must not be used.

## 4. Source rejection conditions

A proposed source must be rejected or remain blocked when any of the following applies:

- no stable source, target, disease, or record identity can be preserved;
- only gene-symbol matching is possible;
- record semantics or aggregation behavior cannot be documented;
- source version or release cannot be identified or captured;
- raw responses cannot be retained or hash-manifested;
- provenance cannot resolve records to artifacts;
- licensing is absent, incompatible, or unresolved;
- query coverage cannot be audited;
- the source requires a live mutable response during component materialization;
- normalized use would require manual or AI/LLM interpretation;
- the only usable output is an undocumented score, rank, or recommendation.

## 5. Required source registration record

Every future source proposal must define:

| Field | Requirement |
|---|---|
| `source_id` | Stable project identifier for the source |
| `source_name` | Official source name |
| `source_authority` | Organization responsible for the source |
| `source_access_mode` | Versioned bulk artifact, captured API, or another reviewed mode |
| `source_version` | Exact source version used for retrieval |
| `source_release_id` | Exact release identifier, if distinct from version |
| `source_release_date` | Official release date with provenance, if available |
| `record_semantics_version` | Version of the reviewed source-field and record-unit mapping |
| `target_identifier_namespace` | Source target identifier namespace and version |
| `disease_identifier_namespace` | Source disease ontology/vocabulary and version |
| `record_identifier_contract` | Native stable ID or deterministic raw-payload ID rule |
| `evidence_type_vocabulary_version` | Source-native vocabulary version or explicit `NOT_PROVIDED` |
| `license_id` | License or terms identity |
| `license_version` | Version/effective date or explicit unresolved status |
| `source_documentation_artifact_id` | Frozen documentation/reference artifact |
| `source_documentation_sha256` | Hash of the governed documentation artifact |
| `review_status` | Technical and scientific governance disposition |

Unassigned or unresolved fields block retrieval authorization unless a reviewed policy explicitly permits a controlled sentinel.

## 6. Source-role mapping

An approved source contract must map source objects to the Task #032B-1 roles:

- `ROLE_QUERY_SCOPE_RECORD`;
- `ROLE_DISEASE_ASSOCIATION_RECORD`;
- `ROLE_DISEASE_CONTEXT_MAPPING`;
- `ROLE_TARGET_IDENTITY_MAPPING`;
- `ROLE_DEPENDENCY_ASSERTION`.

The mapping must specify required fields, cardinality, missingness behavior, raw artifact location, and dependency implications for each role.

Naming a provider is not enough. A source must demonstrate how its actual record model satisfies every required role or how a controlled missing/unknown condition is represented.

## 7. Evidence record unit

The normalized evidence record unit remains one immutable source-returned disease-association object:

`source target entity → source disease entity → source record identity → frozen raw payload`

Record granularity must be one of:

- `SOURCE_ATOMIC`;
- `SOURCE_AGGREGATE`;
- `MIXED`;
- `UNKNOWN`.

Source aggregates remain single records. An internal source count, category, or metric must not be expanded into multiple apparent records without stable atomic source identities and a new reviewed extraction contract.

## 8. Raw and normalized separation

### 8.1 Raw layer

The raw snapshot may preserve source-native values, including:

- identifiers and labels;
- evidence-type fields;
- numeric fields and source-native metrics;
- nested records and aggregates;
- null and absent fields;
- source warnings and annotations;
- response headers and release metadata.

Raw preservation does not endorse or interpret a source-native value.

### 8.2 Normalized component layer

Normalized values must be produced only through the reviewed [Disease Association Component Feature Contract v0.1](disease_association_component_feature_contract_v0.1.md), a versioned extractor, and frozen mapping artifacts.

The normalized layer may contain availability, record structure, provenance, dependency, and missingness features. It must not introduce source or cross-source association strength, confidence, importance, causal status, target quality, rank, priority, recommendation, or free-text biological interpretation.

### 8.3 Separation rules

1. Raw artifacts are immutable and never overwritten by normalization.
2. Normalized records reference exact raw `evidence_record_id` and `artifact_id` values.
3. Source-native fields absent from the reviewed feature contract remain raw only.
4. Normalization never silently repairs identity or missingness.
5. Extractor changes require a new `extractor_version`; raw-byte changes require a new `source_snapshot_version`.
6. A normalized count cannot replace record-level provenance.

## 9. Dependency requirements

The source contract must document whether records share:

- one source aggregate;
- one underlying dataset;
- one cohort or evidence object;
- one publication or upstream record;
- one query response;
- partial or unknown origin.

Same-source and shared-dataset records remain dependent. Cross-source records are not automatically independent. `INDEPENDENT` requires affirmative source-traceable justification. `UNKNOWN` and `NOT_APPLICABLE` remain distinct.

## 10. Source-version change policy

A new `source_snapshot_version` is required when any of the following changes:

- source version or release;
- raw artifact bytes;
- query scope or parameters;
- disease-context definition or mapping artifact;
- target-universe manifest;
- source-field selection;
- pagination or completeness result;
- source documentation that changes record meaning;
- license terms affecting storage or release.

A semantic change to the component feature or record contract additionally requires a new `component_version`.

## 11. Runtime boundary

Live source access may occur only in a separately authorized retrieval task that produces a frozen snapshot. Extractors, component generators, profile materializers, and evidence-landscape builders must consume immutable local or governed external artifacts with verified hashes.

Runtime API dependence and mutable source responses are prohibited.

## 12. Current disposition

No disease-association source is selected, approved, queried, or snapshotted by this specification.

The following remain unassigned:

- `source_id` and provider;
- source version and release;
- access mode;
- disease and target identifier namespaces;
- record semantics version;
- license identity;
- source snapshot version.

These are future review decisions, not values to infer from repository history or general knowledge.

## 13. Source contract checklist

- [ ] Stable source, target, disease, and record identifiers exist.
- [ ] Record unit, aggregation, null, and replacement semantics are documented.
- [ ] Exact source version and release boundary are capturable.
- [ ] Raw bytes, retrieval metadata, size, and SHA256 can be preserved.
- [ ] License permits the governed retention and release plan.
- [ ] Source roles map deterministically to source records.
- [ ] Disease context and query scope are independently frozen.
- [ ] Dependency information and unknowns are representable.
- [ ] Raw and normalized layers remain separate.
- [ ] Materialization does not depend on a live API.
- [ ] No scoring, ranking, target prioritization, biological interpretation, or therapeutic recommendation is introduced.
- [ ] A human governance record separately authorizes retrieval.

## 14. Related policies

- [Disease Context Definition Policy v0.1](disease_context_definition_policy_v0.1.md)
- [Disease Association Snapshot Policy v0.1](disease_association_snapshot_policy_v0.1.md)
- [Disease Association Query Scope Policy v0.1](disease_association_query_scope_policy_v0.1.md)
- [Disease Association Component Registration v0.1](disease_association_component_registration_v0.1.md)
- [Evidence Component Interface Specification v0.1](evidence_component_interface_specification_v0.1.md)
