# Full Universe Profile Materialization Specification v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Version:** v0.1  
**Status:** Frozen scaling specification; no full-universe materialization authorized by this document

## 1. Purpose and boundary

This specification defines how the frozen Target Evidence Profile architecture can scale from the deterministic Task #027 pilot to the complete normalized EnsemblID universe. It governs identity, ordering, profile units, partitioning, provenance, deterministic generation, reproducibility, artifact management, validation, incremental updates, and lifecycle boundaries.

This is not a profile-generation task. It does not create 29,606 profiles, new evidence, scores, rankings, priorities, target selections, biological interpretations, or therapeutic recommendations. It does not authorize AI or LLM runtime decisions.

This specification depends on the frozen Task #026 feature/provenance layer, [Task #026 Provenance Artifact Governance v0.1](task026_provenance_artifact_governance_v0.1.md), the Task #027 pilot contract, and the Task #028 Target Evidence Profile governance documents.

## 2. Full profile universe

### 2.1 Universe definition

The v0.1 full materialization universe is every immutable `EnsemblID` row in the frozen Task #026 `transcriptomic_features.csv` artifact:

- expected rows: **29,606**;
- expected unique immutable identifiers: **29,606**;
- inclusion rule: all normalized feature rows;
- exclusion rule: none.

No biological, statistical, biotype, mapping, evidence-availability, component-state, or target-development filter may change this universe. U1/U2 membership, expression direction, FDR status, sensitivity category, gene type, and external mapping status are profile observations or annotations, not universe filters.

### 2.2 Canonical ordering

The canonical global order is the exact row order of the frozen Task #026 feature artifact identified by its evidence-snapshot hash. Each EnsemblID receives a one-based `universe_ordinal` from that order.

Canonical order must not be regenerated from gene symbols, lexicographic sorting, database order, partition order, or a later source snapshot. A new or reordered universe requires a new evidence-snapshot/universe identity and validation.

### 2.3 Universe manifest

Before materialization, a frozen universe manifest must record for every row:

- `EnsemblID`;
- `universe_ordinal`;
- source feature artifact identifier and SHA256;
- profile version;
- evidence snapshot version;
- deterministic partition identifier.

The manifest must assert 29,606 rows, 29,606 unique EnsemblIDs, contiguous ordinals, exact source order, and no symbol-based identity resolution.

## 3. Profile identity and version boundaries

One target profile is identified by:

`(EnsemblID, profile_version, evidence_snapshot_version)`

A deterministic `profile_id` may encode that tuple. The identifier must not depend on gene symbol, partition, row offset, generation time, randomness, mutable network state, or AI judgement. Moving a profile between storage partitions must not change its profile identity.

The release must record independent version axes:

- `schema_version`: serialized structure and validation constraints;
- `profile_version`: profile assembly semantics and included component contract;
- `evidence_snapshot_version`: exact feature, provenance, and source evidence values/hashes;
- `component_definition_version`: component question and interface;
- `state_rule_version`: executable predicates and precedence;
- `extractor_version`: source-record-to-feature transformation;
- `generator_version`: profile materialization and serialization implementation;
- `partition_strategy_version`: partition function and partition-file contract.

No generic project version may replace these fields. A change in one axis does not silently change another.

## 4. Materialization architecture

### 4.1 Profile unit

The atomic scientific unit is one complete profile object for one EnsemblID under one profile and evidence-snapshot version. The unit contains:

- deterministic profile identity;
- lifecycle/release metadata reference;
- registered component objects;
- exact normalized feature values;
- controlled missingness;
- structural state-rule identities and versions;
- complete uncompressed record-level provenance.

The current materializable component remains `COMP_TRANSCRIPTOMIC_EVIDENCE`. Future components cannot appear until registered under [Profile Component Model v0.1](profile_component_model_v0.1.md) and independently implemented and validated.

### 4.2 Deterministic flow

The governed flow is:

`frozen universe manifest → frozen feature/provenance snapshot → registered component materialization → deterministic partition assignment → canonical serialization → exhaustive validation → partition hashes → release manifest → immutable external storage references`

No stage may use randomness, wall-clock values in governed payloads, mutable API responses, manual row edits, gene-symbol joins, or AI/LLM runtime decisions.

### 4.3 Partition architecture

Profiles and their tabular provenance projection are partitioned using the frozen strategy in [Profile Artifact Partition Strategy v0.1](profile_artifact_partition_strategy_v0.1.md). Partition assignment is based only on immutable EnsemblID bytes and is independent of biological features.

Partition files are storage and regeneration units, not scientific cohorts. Global canonical order is preserved through `universe_ordinal` and the release index even though physical partition order differs.

### 4.4 Manifest and index design

The full release requires:

1. **Release manifest** — release identity, lifecycle, all version axes, source artifacts, global counts, artifact hashes, storage references, validation status, and limitations.
2. **Universe manifest** — one row per EnsemblID with canonical ordinal and snapshot identity.
3. **Profile index** — one row per profile with `profile_id`, EnsemblID, ordinal, partition, profile artifact identifier, and per-profile content hash.
4. **Partition manifest** — one row per partition artifact with role, partition identifier, row/profile/link counts, size, SHA256, generator version, and immutable storage reference.
5. **Dependency/affected-set manifest** — profile-to-input dependencies needed for validated incremental regeneration.

Every index and manifest must be deterministically ordered and hash-frozen.

## 5. Provenance preservation

Every full-universe profile feature must preserve complete record-level lineage. The provenance relationship key remains:

`(feature_id, evidence_record_id)`

Requirements:

- `feature_id` identifies one normalized feature value for one EnsemblID;
- `evidence_record_id` identifies one evidence-lineage relationship;
- repeated `feature_id` values are permitted for distinct evidence records;
- duplicate composite keys are prohibited;
- claim, source, artifact, dependency, extraction-rule, extractor-version, and missingness lineage must resolve;
- dependent records remain separate and retain their dependency relationship;
- provenance cannot be replaced with counts, summaries, or aggregate metrics;
- embedded profile lineage and the tabular provenance projection must be exactly equivalent.

Evidence-record count is audit metadata. It must not become a measure of evidence strength or target quality.

## 6. Artifact governance

### 6.1 Git-managed governance metadata

Git stores small, reviewable, version-controlled artifacts:

- materializer source code and workflow definitions;
- profile and component schemas;
- feature dictionaries and rule registries where size permits;
- universe, profile-index, partition, dependency, and release manifests where governance thresholds permit;
- checksums, sizes, artifact identifiers, and storage references;
- validation, lifecycle, audit, and scientific-review reports;
- reproducibility instructions and governance documentation.

### 6.2 Externally managed immutable artifacts

External immutable storage manages large generated payloads:

- full profile JSONL partitions;
- full profile-provenance partitions;
- any manifest or index that exceeds the governed Git threshold;
- future large component payloads.

The complete external artifacts remain canonical. Git metadata does not substitute for them. Every external artifact must have a stable artifact identifier, schema version, exact byte size, SHA256, generation task, generator version, and immutable storage reference. Retrieval must fail on size or hash mismatch.

This specification does not select an external storage provider or create storage objects.

## 7. Incremental regeneration

Incremental regeneration follows [Profile Incremental Update Policy v0.1](profile_incremental_update_policy_v0.1.md).

Only profiles whose declared dependencies changed should be logically rematerialized. Because partition files are immutable physical artifacts, every partition containing at least one changed profile must be regenerated in full from unchanged and changed profile units, canonically reordered, revalidated, and rehashed. Unaffected partition bytes and hashes must be reused exactly.

A complete rebuild is required when the affected set cannot be proven, when partition assignment changes, when canonical serialization changes, or when a global rule/schema/profile contract affects all profiles. Efficiency never overrides lineage completeness or deterministic identity.

## 8. Validation architecture

Validation follows [Profile Validation Strategy v0.1](profile_validation_strategy_v0.1.md) and includes three complementary layers:

1. **Complete automated validation** over all 29,606 profile units and every provenance relationship.
2. **Deterministic boundary fixtures** for schemas, feature values, missingness, dependencies, and each applicable structural state boundary.
3. **Deterministic sampling audit** for independent human inspection of source-to-profile traceability; sampling supplements and never replaces exhaustive automated validation.

All outputs must regenerate byte-identically from the same frozen inputs, versions, rules, and generator.

## 9. Lifecycle boundary

Generating all 29,606 profiles does not constitute scientific validation and does not automatically change lifecycle state.

A full-universe candidate build may enter `INTERNAL_VALIDATION` only after the required internal gates pass and the promotion is recorded as a human governance action. It cannot become `SCIENTIFIC_REVIEWED` until independent scientific review requirements pass, and it cannot become `PUBLIC_RELEASE` until all public-release, artifact-access, and review gates in [Profile Release Policy v0.1](profile_release_policy_v0.1.md) pass.

Profile contents, component states, record counts, completeness, or apparent consistency cannot trigger lifecycle promotion.

## 10. Prohibitions

The full-universe architecture must not introduce:

- scores or weighted aggregates;
- rankings or priority labels;
- target prioritization or candidate selection;
- confidence metrics;
- therapeutic recommendations or direction;
- biological interpretation;
- evidence-count voting;
- runtime AI or LLM decisions.

Partition assignment, validation sampling, and processing order are infrastructure mechanisms and must never be presented as target rankings.

## 11. Preconditions before implementation

- [ ] Full-universe schema and profile versions are frozen.
- [ ] Evidence snapshot and exact Task #026 input hashes are frozen.
- [ ] The 29,606-row universe manifest and canonical order are validated.
- [ ] Current component definition, state rules, extractor, and generator versions are frozen.
- [ ] Partition strategy and canonical serialization are fixture-tested.
- [ ] External storage and immutable reference format are operationally resolved.
- [ ] Complete automated, boundary-fixture, and deterministic sampling protocols are executable.
- [ ] Incremental dependency and affected-set manifests are defined.
- [ ] No prohibited field or runtime decision path exists.
- [ ] Lifecycle entry remains a separate recorded governance decision.

## 12. Unresolved assumptions

- Only `COMP_TRANSCRIPTOMIC_EVIDENCE` is currently materializable; future component count and payload size are unknown.
- A concrete external storage provider, retention policy, and immutable storage-reference format remain operationally unresolved.
- Full-universe schema, profile, component-definition, generator, and release identifiers must be frozen before implementation; this document does not assign a release.
- Current observed transcriptomic data do not exercise all missingness/state paths; deterministic fixtures remain required.
- Any future universe change requires a separate versioned decision and cannot silently alter the 29,606-row v0.1 universe.

