# Target Evidence Profile Release Specification v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Task:** #024 — Target Evidence Profile Release Specification  
**Version:** v0.1  
**Date:** 21 August 2026  
**Status:** Future release contract; no profile release performed

## Scientific question

Before a full target evidence profile collection can be released, what must be true so that every profile remains identifiable, reconstructible, reproducible, and safe to interpret?

This is correctly framed as a release-contract question. Release readiness is independent of whether any gene appears biologically interesting or therapeutically attractive.

## Scope and non-scope

This specification defines:

- target-profile and release identity;
- required, optional, and prohibited fields;
- evidence, source, dependency, missingness, and artifact references;
- generator and rule provenance;
- canonical serialization;
- blocking release QC; and
- release withholding and version-evolution behavior.

It does not instantiate a target universe, materialize profiles, rank targets, calculate scores, recommend targets, infer therapeutic direction, or generate biological conclusions.

## Frozen basis

The specification hash-pins only:

- `outputs/profile_materialization/materialization_schema.csv`;
- `outputs/profile_materialization/component_state_resolution_registry.csv`;
- `outputs/profile_materialization/profile_builder_contract.md`;
- `outputs/profile_validation/profile_validation_summary.md`; and
- `outputs/target_universe_governance/target_universe_schema.csv`.

Task #023 passed representation validation with documented limitations. Those limitations become explicit release requirements here; they are not treated as resolved merely because validation examples passed.

## 1. Identity model

### Target entity

`EnsemblID` is the only immutable entity and join key. It must match the versioned EnsemblID from one `INCLUDED` row in a frozen Task #022-compatible target manifest.

Symbols and gene types are display annotations only. They cannot join, replace, repair, merge, or infer an EnsemblID.

### Profile identity

One target profile is the set of exactly 11 component rows for one EnsemblID under one profile version and one evidence snapshot.

```text
profile_id = SHA256(
    EnsemblID
    | profile_version
    | evidence_snapshot_version
    | input_manifest_sha256
    | rules_sha256
)
```

`profile_id` must be recomputed during QC. Random UUIDs are prohibited.

### Profile version

`profile_version` identifies profile structure and interpretation semantics. It changes when any required or optional field, component meaning, state semantics, interpretation boundary, or canonical serialization contract changes.

A new profile version is not evidence that a target is better or more mature.

### Evidence snapshot version

`evidence_snapshot_version` identifies the exact evidence content used by a profile. It is content-derived from canonical ordered:

- evidence artifact IDs and SHA256 hashes;
- claim, record, source, and dependency registries;
- source releases and API/data versions;
- disease and target query scopes;
- retrieval completeness/failure manifests; and
- input-manifest serialization version.

The recommended form is:

```text
ES-<semantic-version>-<first-16-hex-of-full-manifest-SHA256>
```

The complete manifest SHA256 is retained separately. Changing any evidence artifact, source release, or query scope creates a new evidence snapshot.

### Release identity

A release contains one frozen target-universe version, profile version, evidence snapshot, generator, executable rule set, serialization version, profile-data artifact, QC artifact, and supporting relational artifacts.

`release_id` is a SHA256-derived identifier over that complete canonical release configuration. Any change creates a new release. Previously released artifacts are immutable and may only be marked `SUPERSEDED`, never overwritten.

## 2. Profile structure

The release schema catalog distinguishes four types of fields.

### Required identity and state fields

Required fields include:

- `profile_id`;
- `EnsemblID`;
- `profile_version`;
- `evidence_snapshot_version`;
- `component_id`;
- `component_state`;
- `state_rule_id` and `state_rule_version`; and
- deterministic `state_rationale`.

### Required lineage and uncertainty fields

Every component row carries exact references to:

- claims;
- atomic evidence records;
- source entities and versions;
- artifacts and their explicit hashes;
- record-level missingness and uncertainty;
- dependency edges, relationships, and levels;
- conflict records and rationale; and
- provenance-completeness state.

Required collections use explicit `NONE`, never blank cells.

### Optional annotations

Optional fields are restricted to display-only source annotations:

- `Symbol`;
- `gene_type`;
- source-grounded external identifier annotations; and
- deterministic non-interpretive display notes.

Removing or changing an optional annotation must not change profile identity, component state, evidence membership, ordering, or release status unless the profile-version contract itself changes.

### Prohibited fields and derivations

Profile data and sidecars must not contain direct fields, aliases, or hidden equivalents for:

- score;
- rank;
- priority;
- recommendation;
- target selection;
- therapeutic direction;
- aggregate target state;
- aggregate confidence;
- completeness percentage;
- independent-evidence vote count; or
- development decision.

The prohibition applies to code paths and derived sidecars as well as CSV headers. Component states cannot be arithmetically or heuristically collapsed.

## 3. Evidence representation

### Claims and records

`claim_ids` and `evidence_record_ids` are unique, lexically sorted stable IDs. Every claim resolves to the same EnsemblID and an allowed component domain. Every record resolves to a linked claim, source entity, source-native identifier, and frozen artifact.

Deduplication is allowed only by identical `record_id`. Reusing a record across components preserves the same ID and does not create a second observation.

### Sources and artifacts

Every source ID has an explicit source version. Every artifact ID is explicitly paired as:

```text
artifact_id=sha256
```

Unpaired parallel lists are not acceptable because they can lose artifact-to-hash identity.

### Dependencies

Task #023 showed that relationship/level category lists alone are not a standalone representation of pairwise dependency. Release v0.1 therefore requires:

- `dependency_edge_ids`;
- `dependency_id=relationship` mappings; and
- `dependency_id=dependency_level` mappings.

Every edge remains resolvable to its exact two record endpoints and review status in the frozen dependency graph. Absence of an edge never becomes `INDEPENDENT`.

The frozen dependency registry remains a required release artifact even when component rows carry edge IDs.

## 4. Missingness and uncertainty

Component state is one of exactly:

- `OBSERVED`;
- `PARTIAL`;
- `MISSING`;
- `NOT_QUERIED`; or
- `CONFLICTING`.

The states have no numerical order.

### Record-level preservation

Task #023 showed that category lists alone do not identify which record carries which state. Release rows therefore require:

```text
record_id=missingness_status
record_id=uncertainty_status
```

for every linked record.

### State boundaries

- `OBSERVED` requires the component-specific qualifying criterion and complete minimum provenance.
- `PARTIAL` means some assessment exists but evidence, linkage, coverage, versioning, or provenance is incomplete.
- `MISSING` requires completion of the entire frozen component query scope with no qualifying record and no unresolved failure or unknown coverage.
- `NOT_QUERIED` means no eligible acquisition or valid assessment covered the component.
- `CONFLICTING` requires a prespecified comparison rule and retains every conflicting record.

`MISSING` and `NOT_QUERIED` are not negative biological evidence. `OBSERVED` is not favorable evidence. Conflict resolution cannot choose or average a preferred record.

## 5. Provenance requirements

Before generation, the run configuration freezes:

- generator ID, version, and executed-file SHA256;
- executable state-rule ID/version and complete rules SHA256;
- profile version;
- evidence snapshot version;
- target-universe version;
- target/input manifest hashes;
- source versions;
- materialization snapshot timestamp; and
- serialization version.

Each component row propagates the applicable values. `provenance_complete=TRUE` is permitted only when every claim, record, source, artifact, dependency, rule, and source version resolves exactly. `UNKNOWN` source versions or hashes block complete provenance and release.

The frozen materialization timestamp is read from configuration. Wall-clock time cannot change profile bytes.

## 6. Executable rule requirement

Task #021 defines 55 controlled semantic predicates in prose. Task #023 verified that validation conditions can address all five states but warned that prose is not a machine-executable rule language.

A full release is therefore blocked until:

1. every component/state predicate has an executable, reviewed, versioned implementation;
2. every implementation has a stable rule ID;
3. rule IDs map one-to-one to Task #021 semantic predicates;
4. precedence is frozen as `CONFLICTING → OBSERVED → MISSING → PARTIAL → NOT_QUERIED`;
5. unit and boundary fixtures pass for all 55 rules; and
6. the complete executable rule artifact is hash-pinned.

An LLM or unconstrained free text cannot resolve component states.

## 7. Canonical release bundle

A release bundle must include or resolvably reference:

1. release manifest;
2. frozen target-universe manifest and QC;
3. canonical long-form profile data;
4. release schema and interpretation boundaries;
5. executable state/rationale rules and tests;
6. evidence claim registry;
7. atomic evidence-record registry;
8. source-entity/version registry;
9. dependency graph;
10. query-coverage and missingness/failure manifest;
11. artifact manifest containing IDs, sizes, SHA256 hashes, generators, and dependencies;
12. release QC results;
13. deterministic recovery-run hash comparison; and
14. session/environment metadata.

Large governed artifacts may remain in external storage, but the release manifest must preserve immutable resolvable locations, sizes, hashes, and storage status.

## 8. Release QC and decision

Release uses fail-closed semantics. Every gate in `profile_release_qc_matrix.csv` is blocking.

### Identity validation

- EnsemblIDs match the frozen included universe exactly.
- Symbols were not used for joins.
- Profile IDs recompute.
- Exactly `N` profiles and `N × 11` unique component rows exist, where `N` comes from the frozen target manifest.

Task #024 does not assume `N=29,606` because Task #022 did not instantiate a target universe.

### Lineage validation

- All claims, records, sources, source versions, and source-native identifiers resolve.
- Record counts reconcile to exact IDs.
- Reused records retain their stable IDs.
- Every artifact ID maps to one verified hash.

### Dependency validation

- The profile edge set equals the induced frozen dependency subgraph.
- Endpoints, relationships, levels, and review states reconcile.
- Unknown lineage remains unknown.
- Dependent records are never treated as independent votes.

### Missingness validation

- Every record-level missingness/uncertainty mapping matches its frozen record.
- Exactly one valid state resolves per component.
- Query coverage supports `MISSING` versus `NOT_QUERIED`.
- Conflict records and rules remain explicit.

### Deterministic regeneration

An independent clean run using identical frozen inputs, generator, rules, timestamp, and serialization must reproduce every release artifact byte-for-byte. Input hashes are checked before and after generation; final output hashes are frozen only after canonical serialization.

### Interpretation-safety validation

Schemas, generator code, outputs, sidecars, rationale templates, and documentation are scanned for prohibited fields, aliases, hidden aggregation, and unsupported conclusions.

### Release status

- `RELEASED`: every blocking gate passed and the QC artifact/hash is frozen.
- `WITHHELD`: at least one blocking gate failed or a required artifact is absent/unknown.
- `SUPERSEDED`: an immutable earlier release has a later version; its content remains unchanged.

No partial repair or silent omission is allowed. A corrected release receives a new release ID.

## Limitations

This specification does not prove that a future builder complies with it. In particular:

- no executable rule artifact exists in Task #024;
- no target universe manifest is instantiated;
- no full profile dataset or release bundle is generated;
- unacquired evidence domains remain outside the current evidence snapshot; and
- real conflict fixtures currently cover transcriptomic sensitivity conflicts, not every evidence component.

These are release preconditions or documented scope limits, not reasons to score or exclude genes.
