# Task #026 Provenance Artifact Governance v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Version:** v0.1  
**Status:** Frozen governance decision

## 1. Background

Task #026 created `feature_provenance_registry.csv` as the explicit lineage layer between normalized transcriptomic feature values and their source evidence records. The artifact contains 1,036,210 provenance links. A feature value may depend on more than one evidence record, including the dependent `TRANSCRIPT_PRIMARY` and `TRANSCRIPT_ROBUSTNESS` records derived from the same TCGA-LUAD dataset.

Task #026-B independently confirmed complete feature coverage, zero broken feature/claim/record/source links, zero dependency conflicts, and zero evidence-inflation violations. It also established that repeated `feature_id` values are the expected representation of many-to-one lineage rather than duplicate evidence links.

This specification governs storage and identity of the full immutable provenance artifact. It does not change feature values, extractor behavior, provenance meaning, dependency semantics, or evidence interpretation.

## 2. Scientific rationale

Provenance is part of the scientific evidence architecture, not optional execution metadata. A future target evidence profile must remain traceable from a normalized feature through its claim, evidence record, source, dependency relationship, generating artifact, extraction rule, and extractor version.

The full record-level artifact is therefore canonical. Counts, summaries, checksums, manifests, and audit reports describe or validate it but do not replace it. Preserving every evidence-record relationship prevents dependent records from being silently collapsed, recast as independent support, or converted into an apparent confidence measure.

Large immutable provenance artifacts need not reside directly in Git to remain reproducible. Their scientific identity is established by immutable bytes, a versioned schema, complete generation metadata, a cryptographic checksum, and a resolvable storage reference.

## 3. Frozen decisions

### Decision 1 — Provenance relationship key

The provenance relationship key is:

`(feature_id, evidence_record_id)`

`feature_id` identifies one normalized feature value for one immutable target entity. `evidence_record_id` identifies one source evidence record contributing lineage to that feature value. `feature_id` alone is not required to be unique in a provenance table.

Two rows sharing a `feature_id` but carrying different `evidence_record_id` values are distinct lineage relationships. Two rows sharing both values are duplicate provenance links and are prohibited within one artifact version.

### Decision 2 — Large artifact governance

Git stores the reproducibility and governance layer:

- source code;
- schemas and controlled vocabularies;
- generation and input manifests;
- audit reports and QC summaries;
- checksums, sizes, versions, and storage references.

Large immutable generated artifacts are managed outside the Git repository. The complete externally stored artifact remains canonical. A repository manifest or summary must never be treated as a substitute for the full artifact.

This decision does not move, delete, compress, or rewrite the current Task #026 artifact. Externalization is a separate controlled operation.

### Decision 3 — Reproducibility contract

Every externally managed artifact must have all of the following metadata before release:

- stable artifact identifier;
- schema version;
- SHA256 checksum of the exact canonical bytes;
- exact uncompressed file size in bytes;
- generating task identifier;
- extractor or generator version;
- immutable or version-pinned storage reference.

Missing, placeholder, mutable, or unresolvable metadata fails release validation.

### Decision 4 — Lineage preservation

The following transformations are prohibited:

- replacing record-level provenance with counts or summaries;
- collapsing dependent evidence records into one untraceable row;
- treating multiple lineage records as independent votes;
- converting lineage quantity into a confidence, quality, priority, or other target-evaluation metric;
- removing claim, evidence-record, source, artifact, dependency, extraction-rule, or generator relationships required by the governed schema.

Storage changes must preserve the exact logical relationships and controlled missingness semantics.

## 4. Provenance key definition

### Relationship identity

Within one artifact version, the composite key `(feature_id, evidence_record_id)` must be unique and non-missing.

The Task #026 artifact contains:

- 651,332 unique feature-value IDs;
- 1,036,210 unique provenance relationships;
- 0 duplicate `(feature_id, evidence_record_id)` links.

Features derived from one record have one relationship row. Features derived from both primary and robustness records have two rows with the same `feature_id` and distinct `evidence_record_id` values. Their dependency relationship must remain explicitly linked as `SHARED_DATASET` with dependency level `DEPENDENT`.

### Required relationship fields

Each provenance relationship must preserve at least:

- `feature_id`;
- immutable target `EnsemblID`;
- `feature_name`;
- `claim_id`;
- `evidence_record_id`;
- `source_id`;
- originating `artifact_id`;
- `dependency_id` or explicit `NOT_APPLICABLE` where the governed schema permits it;
- controlled `feature_missingness_status`;
- `extraction_rule_id`;
- `extractor_version`.

The composite key defines relationship uniqueness. A future `provenance_link_id` may be added as a deterministic surrogate identifier, but it must not replace or weaken the composite-key validation.

## 5. Artifact storage policy

### Canonical external object

The canonical object must be stored under an immutable object version, content-addressed reference, or equivalently version-pinned external location. A mutable `latest` reference is insufficient as the sole storage reference.

The external system must support retrieval of the complete artifact without row removal or semantic transformation. Access controls, retention rules, and backup or mirroring policies must not alter the canonical bytes.

### Repository record

The Git-tracked manifest for an external artifact must record:

| Field | Requirement |
|---|---|
| `artifact_id` | Stable and unique within project governance |
| `relative_logical_name` | Human-readable project artifact path/name |
| `schema_version` | Exact governed schema identifier |
| `sha256` | SHA256 of canonical stored bytes |
| `file_size_bytes` | Exact canonical byte size |
| `generation_task` | Task that generated the artifact |
| `generator_version` | Exact extractor/generator version |
| `input_manifest_reference` | Versioned inputs and hashes used for generation |
| `storage_reference` | Immutable, version-pinned retrieval reference |
| `audit_status` | Latest governed integrity/lineage audit outcome |

For the current artifact, the frozen identity values are:

| Field | Value |
|---|---|
| Artifact identifier | `ART_TASK026_TRANSCRIPTOMIC_FEATURE_PROVENANCE_V0_1` |
| Logical name | `outputs/feature_extraction/feature_provenance_registry.csv` |
| Schema version | `FEATURE_PROVENANCE_REGISTRY_SCHEMA_V0.1` |
| SHA256 | `68ba8096563358b539360963da7d2856fcb0f888673da9989741b95549f3b246` |
| File size | `318603824` bytes |
| Generation task | `TASK026` |
| Extractor version | `TRANSCRIPTOMIC_FEATURE_EXTRACTOR_V0.1` |
| Storage reference | Pending a separate controlled externalization operation |

The pending storage reference means the policy is frozen but external release is not yet complete. A concrete immutable reference must be recorded before the repository copy can be removed or an external artifact release can be declared reproducible.

### Retrieval validation

Every retrieval must verify the byte size and SHA256 before the artifact is accepted as an input. A mismatch must stop the consuming workflow. Silent repair, partial acceptance, or fallback to a similarly named object is prohibited.

## 6. Reproducibility requirements

The reproducibility chain is:

`frozen input manifest → versioned extractor → canonical generated artifact → QC/audit validation → SHA256 freeze → immutable storage reference`

A reproducible regeneration must use the same frozen inputs, extractor version, schema, rules, and deterministic serialization contract. The regenerated artifact must match the governed SHA256 to be considered the same artifact version.

Before an external artifact is released or consumed, validation must confirm:

1. the artifact identifier and schema version match the manifest;
2. file size and SHA256 match exactly;
3. the composite provenance key is unique;
4. every feature has its required record-level provenance;
5. all claim, record, source, artifact, rule, and version foreign keys resolve;
6. all dependency relationships remain present and retain their governed relationship and level;
7. controlled missingness values are preserved without conversion to negative evidence;
8. no scoring, ranking, confidence, priority, selection, or recommendation field has been introduced;
9. the audit result and any unresolved limitations are recorded.

Checksums establish byte identity, not scientific validity. Audit reports establish compliance with defined checks, not target validity or therapeutic relevance.

## 7. Future compatibility considerations

- A schema change creates a new schema version and regenerated artifact version. Existing canonical objects must not be overwritten.
- A change in feature rules, input evidence records, source versions, dependency semantics, serialization, or extractor version requires a new artifact identity and checksum.
- Moving an unchanged canonical object between storage systems may add a new immutable storage reference, but the artifact identifier, size, and checksum remain unchanged.
- Mirrors are permitted only when each retrieved copy validates to the same checksum. No mirror becomes authoritative merely because it is more convenient to access.
- Future evidence domains may create more than two lineage relationships per feature. The composite-key rule remains valid and record count must not be interpreted as evidence strength.
- Dependency metadata must survive storage-format changes. A columnar or database representation may supplement the canonical CSV only if it preserves the complete logical schema and is separately versioned and hashed.
- Controlled missingness states must remain distinguishable across migrations. `NOT_FOUND`, `NOT_QUERIED`, `NOT_APPLICABLE`, and `UNKNOWN` must not be collapsed into one null value.
- Future target evidence profiles must reference the governed artifact identifier, checksum, feature IDs, and evidence-record relationships needed to reconstruct their lineage.
- External storage provider selection, credentials, retention duration, and the concrete storage reference are operational decisions outside this specification. They must be resolved before external release without changing the frozen scientific governance rules above.

