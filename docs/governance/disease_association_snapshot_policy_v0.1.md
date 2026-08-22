# Disease Association Snapshot Policy v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Version:** v0.1  
**Component:** `COMP_DISEASE_ASSOCIATION`  
**Status:** Frozen governance policy; no snapshot created

## 1. Purpose

This policy defines how a future disease-association retrieval must be captured as an immutable, auditable, reproducible source snapshot before normalization or component materialization.

It does not retrieve data, access an API, create a snapshot artifact, or assign a `source_snapshot_version`.

## 2. Snapshot principle

The governed sequence is:

`approved source contract → frozen disease context → frozen query scope → authorized retrieval → immutable raw snapshot → validation → normalized features`

Normalization, component generation, profile materialization, and evidence-landscape representation must consume the immutable snapshot. They must not depend on a live database or runtime API response.

## 3. Snapshot identity

Every snapshot must have:

- `source_snapshot_id` — stable project artifact identity;
- `source_snapshot_version` — immutable content-and-scope version;
- `source_id`;
- `source_version`;
- source release ID and official release information;
- `disease_context_id`, ontology, and ontology version;
- `query_scope_id` and query-scope version;
- entity-universe artifact ID and SHA256;
- snapshot manifest artifact ID and SHA256;
- retrieval implementation/version identity;
- completeness status;
- license identity and version.

Snapshot identity must not depend on a gene symbol, random value, mutable latest-release alias, or unrecorded runtime choice.

## 4. Required snapshot manifest

### 4.1 Source and release information

The manifest must record:

- source ID, name, and authority;
- exact `source_version`;
- source release ID;
- official release date where available;
- release documentation identity and artifact hash;
- access mode and access-location identity;
- source record-semantics version;
- source target and disease identifier namespaces;
- source evidence-type vocabulary version where present.

If a source does not provide a field, the manifest must use an explicit controlled status such as `NOT_PROVIDED` or `UNKNOWN`, with an eligibility-review disposition.

### 4.2 Query and retrieval metadata

The manifest must record:

- query-scope ID and version;
- canonical query template or bulk-selection rule;
- complete parameters and filters;
- target entity universe and canonical order;
- disease context and mapping-rule version;
- requested response fields;
- pagination, ordering, batching, and retry rules;
- retrieval software identity and version;
- retrieval start and completion timestamps in UTC;
- endpoint or bulk-artifact identity;
- response release headers, ETag, Last-Modified, or analogous source metadata where available;
- per-query, per-batch, or per-entity completion ledger;
- failed, retried, omitted, and unresolved requests;
- network and HTTP status summaries as retrieval provenance only.

Retrieval timestamps are provenance of the raw snapshot. They must not be regenerated during component materialization or used in deterministic profile values.

### 4.3 Artifact inventory

For every raw or metadata artifact, record:

- `artifact_id`;
- relative path or immutable external storage reference;
- artifact role;
- media type and serialization format;
- compression format where applicable;
- file size in bytes;
- SHA256;
- record count when deterministically countable;
- partition or batch identity;
- source/query provenance;
- validation status.

Large raw artifacts may be externally governed, but the repository must retain schemas, manifests, checksums, retrieval specifications, and audit reports according to project artifact governance.

### 4.4 License information

The manifest must record:

- license or terms ID;
- license version or effective date;
- official license reference or frozen license artifact;
- license artifact SHA256;
- permitted storage, redistribution, and derived-use status;
- attribution requirement;
- access restrictions;
- review status for internal and public release.

License uncertainty blocks snapshot release and downstream materialization.

## 5. Raw artifact preservation

Raw artifacts must preserve source-native bytes as received or an explicitly documented lossless packaging of those bytes.

The raw layer may contain:

- source-native numeric metrics;
- identifiers and labels;
- nested evidence structures;
- null or absent fields;
- warnings and annotations;
- response envelopes and headers;
- aggregate objects;
- source error records.

Raw preservation does not make a field a normalized feature and does not authorize interpretation.

## 6. Canonical packaging

The snapshot specification must freeze:

- file naming and partition strategy;
- character encoding;
- line endings;
- JSON/CSV serialization rules where repackaging is permitted;
- compression tool and version where compressed bytes define artifact identity;
- record ordering;
- manifest ordering;
- duplicate response handling;
- failed-response preservation;
- canonical checksum procedure.

If exact server response bytes are available, they should remain separately hashed even when a deterministic normalized raw-record package is also created.

## 7. Completeness statuses

Every snapshot must declare exactly one:

- `COMPLETE` — all required scope units completed and reconciled;
- `PARTIAL` — some required scope units failed, were omitted, or remain unresolved;
- `FAILED` — the retrieval cannot support a governed snapshot;
- `NOT_EXECUTED` — retrieval was not attempted.

Only `COMPLETE` may support a component-wide complete query-scope assertion. A `PARTIAL` snapshot may be retained for audit or validation but must propagate incomplete coverage and cannot be silently treated as complete.

## 8. Per-entity retrieval ledger

For every immutable `EnsemblID` in the declared universe, the snapshot must record:

- universe ordinal;
- requested source target identity or mapping request;
- disease-context request;
- query/batch identity;
- attempt status;
- completion status;
- response artifact and record location;
- number of source records returned as audit metadata;
- retrieval failure and retry status;
- target and disease mapping status;
- query coverage status;
- checksum linkage.

Zero returned records must remain distinct from no query, query failure, mapping failure, and unknown coverage.

## 9. Snapshot hashing and version assignment

The `source_snapshot_version` must derive from or unambiguously reference a canonical manifest containing:

- source/release identity;
- disease-context identity;
- query-scope identity;
- entity-universe identity;
- complete artifact inventory and SHA256 values;
- retrieval implementation version;
- license identity;
- completeness status.

Any raw byte, required manifest field, artifact inventory, scope definition, or completeness result change creates a new snapshot version.

Re-running the same query does not recreate the same snapshot by assertion. Hash equality must demonstrate byte identity; otherwise the rerun is a distinct snapshot or documented retrieval replicate.

## 10. Validation requirements

Before normalization, validate:

- all required manifest fields exist;
- source, release, disease-context, query-scope, and entity-universe identities match approvals;
- every artifact exists and matches size and SHA256;
- record counts and partitions reconcile;
- every scope unit has a ledger row;
- duplicates, retries, failures, and omissions are explicit;
- raw records retain source identifiers and record granularity;
- license review permits the intended use;
- no artifact was manually edited after hashing;
- regeneration or replay from the frozen raw snapshot requires no source access.

## 11. Raw-to-normalized boundary

The raw snapshot is immutable input. A future normalized feature layer must:

- use only reviewed feature and mapping contracts;
- record extractor and extraction-rule versions;
- preserve source record and artifact IDs;
- retain feature-level missingness;
- preserve dependency relationships;
- fail on unresolved required provenance;
- create new derived artifacts and hashes without changing raw files.

Source-native values not registered in the feature contract remain raw only. Normalization must not translate a source-native metric into strength, confidence, importance, ranking, priority, target quality, causal status, or therapeutic relevance.

## 12. Runtime and mutation prohibitions

Prohibited:

- live API or database dependence during extraction, component generation, profile materialization, validation replay, or evidence-landscape generation;
- mutable latest-release references without captured exact release identity;
- overwriting a frozen raw snapshot;
- silently replacing failed or missing response partitions;
- modifying raw values during normalization;
- manual or AI/LLM runtime decisions;
- scoring, ranking, target prioritization, biological interpretation, or therapeutic recommendation.

Corrections require a new snapshot or derived-artifact version, as appropriate.

## 13. License and withdrawal changes

If source license terms change after snapshot creation:

1. preserve the historical manifest and hashes;
2. record the new license status and effective date;
3. stop any release or redistribution that is no longer permitted;
4. publish a governed withdrawal or restriction notice;
5. do not overwrite the historical snapshot record.

A storage migration may retain artifact identity only when bytes and hashes remain unchanged and storage-reference governance is updated.

## 14. Current disposition

No source snapshot, raw record, retrieval manifest, query ledger, or license artifact is created by this policy. `source_snapshot_version` remains `UNASSIGNED_NO_RETRIEVAL_AUTHORIZED`.

## 15. Snapshot checklist

- [ ] Source contract and disease context are approved.
- [ ] Query scope and entity universe are frozen.
- [ ] Retrieval is separately authorized.
- [ ] Source version, release, and record semantics are recorded.
- [ ] Retrieval metadata and per-entity ledger are complete.
- [ ] Every raw artifact has size, SHA256, and storage reference.
- [ ] License information and release permissions are frozen.
- [ ] Completeness status is explicit.
- [ ] Raw and normalized layers remain separate.
- [ ] Downstream generation requires no runtime API.
- [ ] No biological interpretation, score, rank, or prioritization is introduced.

## 16. Related policies

- [Disease Association Source Contract v0.1](disease_association_source_contract_v0.1.md)
- [Disease Context Definition Policy v0.1](disease_context_definition_policy_v0.1.md)
- [Disease Association Query Scope Policy v0.1](disease_association_query_scope_policy_v0.1.md)
- [Disease Association Component Feature Contract v0.1](disease_association_component_feature_contract_v0.1.md)

