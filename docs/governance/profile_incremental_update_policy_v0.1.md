# Profile Incremental Update Policy v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Version:** v0.1  
**Status:** Frozen update specification; no regeneration performed

## 1. Purpose

This policy defines dependency-aware regeneration for future full-universe Target Evidence Profile releases. Its purpose is to avoid unnecessary full rebuilds while preserving immutable identities, complete provenance, deterministic bytes, version separation, and release auditability.

Incremental update decisions are infrastructure decisions. They must not depend on biological importance, scores, ranks, priorities, confidence metrics, target selection, therapeutic recommendations, or AI/LLM runtime judgement.

## 2. Immutability model

A frozen profile release is never updated in place. Every change produces a new candidate release manifest and new artifact identities for changed artifacts. Unaffected artifacts may be referenced unchanged only when their bytes, hashes, schema compatibility, dependencies, and release-policy reuse conditions are proven.

Incremental regeneration changes the amount of recomputation, not the scientific identity rules. The new release still records complete `schema_version`, `profile_version`, `evidence_snapshot_version`, component, rule, extractor, generator, partition, and lifecycle versions as separate governed fields.

## 3. Dependency model

Each profile must have a machine-readable dependency record containing at least:

- `EnsemblID` and deterministic `profile_id`;
- universe/snapshot identity;
- normalized feature row identifier and source artifact hash;
- all feature IDs;
- all `(feature_id, evidence_record_id)` provenance keys;
- claim, source, artifact, and dependency identifiers;
- component-definition versions;
- state-rule versions;
- extractor and generator versions;
- schema/profile versions;
- partition strategy and assigned partition.

The dependency manifest must allow a changed input artifact or record to resolve to an exact affected EnsemblID set without gene-symbol joins or free-text inference.

## 4. Change detection

Every incremental candidate begins with immutable old/new manifests and an exact change manifest. Changes are identified by stable keys and content hashes, not filenames or modification times.

Required change classes:

- universe identity/order change;
- normalized feature value or missingness change;
- provenance relationship or dependency change;
- evidence-record, claim, source, or artifact version change;
- component definition change;
- state-rule predicate/precedence change;
- extractor change;
- profile assembly change;
- schema/serialization change;
- generator change;
- partition strategy change;
- documentation/storage-reference change with no payload-byte change.

If the changed scope cannot be proven from governed manifests, the update must use a full rebuild.

## 5. Affected-set resolution

### 5.1 Profile-level affected set

A profile is affected when any of its declared inputs or governing contracts changes. The affected set is the union of EnsemblIDs reached through the dependency manifest.

The affected-set artifact must record:

- change identifier and class;
- old/new artifact identifiers and hashes;
- deterministic dependency traversal rule;
- affected EnsemblIDs in canonical universe order;
- affected profile count;
- affected partition identifiers;
- reason each profile is included;
- proof or validation that other profiles are unaffected.

### 5.2 Partition-level regeneration set

Physical partition artifacts are immutable. Therefore:

`affected_partitions = unique(partition_id for each affected EnsemblID)`

Every affected partition is regenerated and validated as a whole. Unaffected partitions are reused only if their stored bytes and hashes match the prior release and their schemas/contracts remain compatible.

## 6. Change-to-regeneration rules

| Change | Minimum logical scope | Physical consequence |
|---|---|---|
| Feature/provenance value changes for exact EnsemblIDs | Those EnsemblIDs | Regenerate their partitions |
| Evidence source release with verified record-level delta | Profiles linked to changed records | Regenerate affected partitions |
| Evidence source release without complete delta/equivalence proof | All profiles consuming the source | Regenerate all relevant partitions |
| Component definition change | All profiles containing that component | Usually all current partitions |
| State-rule or precedence change | All profiles containing that component | Regenerate all relevant partitions |
| Extractor behavior change | All features produced by that extractor and dependent profiles | Regenerate affected/all relevant partitions |
| Profile assembly/component-set change | All profiles under that profile version | Full profile rebuild |
| Schema or canonical serialization change | Every serialized profile/artifact | Full rebuild and repartition serialization |
| Generator change | Scope proven by deterministic equivalence tests; otherwise all profiles | Regenerate proven scope or full rebuild |
| Partition strategy change | All profiles | Full repartitioning |
| Universe addition/removal/reorder | New universe/snapshot; affected identity/index scope | Rebuild indexes/manifests and all impacted partitions; full validation |
| Storage-reference change with identical bytes/hash | No profile | Metadata-only governed update |
| Documentation clarification with no semantic/payload change | No profile | Documentation/manifest review only |

No change may be classified as metadata-only if it alters evidence meaning, missingness, dependency, profile fields, serialization bytes, or interpretation boundaries.

## 7. Incremental materialization procedure

1. Freeze old and new input manifests and all version axes.
2. Validate the prior release and artifact availability.
3. Generate the exact change manifest by stable keys and hashes.
4. Traverse the frozen dependency graph to produce the affected EnsemblID set.
5. Resolve affected partitions under the unchanged partition strategy.
6. Rematerialize affected profiles from frozen new inputs.
7. Regenerate each affected profile and provenance partition in canonical order.
8. Reuse unaffected partition artifacts only after hash and compatibility validation.
9. Rebuild global universe, profile index, partition, dependency, and release manifests as required.
10. Run complete validation across the assembled new release, not only changed profiles.
11. Run incremental boundary fixtures and deterministic sampling under the new release ID.
12. Freeze new sizes, hashes, immutable storage references, limitations, and validation results.

Incremental execution may reduce computation but cannot reduce final release validation coverage.

## 8. Determinism and reuse

Reusable objects must be content-addressed or otherwise hash-verified. Cache keys include all inputs that affect bytes, including schema, profile, snapshot, component, rule, extractor, generator, partition strategy, and serialization versions.

Reuse is prohibited when:

- any cache-key input is missing or ambiguous;
- the prior artifact hash cannot be verified;
- dependency scope is unknown;
- generator equivalence is unproven;
- canonical ordering or serialization changed;
- a reused artifact would report incompatible release metadata.

Parallel incremental generation must produce identical bytes regardless of worker count or completion order.

## 9. Provenance continuity

For every changed profile, the new release must preserve or update every record-level provenance relationship explicitly. Unchanged relationships retain stable feature/evidence-record identities when their governed meanings and source records are unchanged. Added, removed, or changed relationships must be visible in a provenance delta report.

The composite key remains `(feature_id, evidence_record_id)`. Counts cannot replace relationship deltas. Dependent records cannot be collapsed during update or reused as independent evidence.

## 10. Validation requirements

Every incremental release must validate:

- old/new manifest and hash integrity;
- exact change classification;
- affected-set completeness and unaffected-set proof;
- affected partition regeneration;
- unchanged partition byte/hash identity;
- full-universe counts, identity, ordering, and index reconciliation;
- all feature values, missingness, provenance, dependencies, and states across the complete assembled release;
- deterministic regeneration of affected partitions and global manifests;
- boundary fixtures for the change class;
- deterministic sampling audit under the new release identifier;
- absence of scores, rankings, priorities, confidence metrics, selection, interpretation, recommendations, and AI runtime decisions.

Any unexplained difference outside the declared affected set fails incremental reuse and requires expanded regeneration, potentially a full rebuild.

## 11. Lifecycle and review

An incremental release does not inherit lifecycle state automatically. It must pass the gates appropriate to its change class and desired state. Evidence, component, rule, profile, schema, or interpretation-boundary changes require renewed scientific review at the governed scope before `SCIENTIFIC_REVIEWED` or `PUBLIC_RELEASE`.

Materializing fewer partitions does not reduce review obligations and does not constitute target validation.

## 12. Incremental update checklist

- [ ] Old/new inputs, versions, manifests, and hashes are frozen.
- [ ] Change class is explicit and deterministic.
- [ ] Dependency traversal yields an exact affected EnsemblID set.
- [ ] Unaffected-set proof is recorded.
- [ ] Affected partitions are complete and canonically regenerated.
- [ ] Unaffected partition bytes and hashes are unchanged.
- [ ] Global indexes/manifests reconcile the complete 29,606-profile universe.
- [ ] Provenance deltas preserve every composite relationship.
- [ ] Complete release validation passes after assembly.
- [ ] Boundary fixtures and deterministic sampling audit pass.
- [ ] No manual, biological, scoring, ranking, priority, confidence, selection, recommendation, or AI decision affects scope.
- [ ] Lifecycle promotion is reviewed separately.
- [ ] Uncertainty or an unprovable affected set triggers a full rebuild.

## 13. Unresolved operational assumptions

- Future evidence sources may not provide reliable record-level deltas; those updates will require broader regeneration.
- The concrete content-addressed cache and external storage systems are not selected here.
- Future components may introduce cross-profile or cohort-level dependencies; each must register how affected sets are resolved before incremental updates are allowed.
- Performance thresholds do not override the full-rebuild fallback when dependency completeness is uncertain.
