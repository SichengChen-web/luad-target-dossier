# Profile Artifact Partition Strategy v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Version:** v0.1  
**Status:** Frozen partition specification; no artifacts generated

## 1. Purpose

This document defines deterministic physical partitioning for a future full-universe Target Evidence Profile release. Partitioning supports bounded artifact sizes, independent validation, immutable external storage, and dependency-aware regeneration without creating biological groups.

Partitions are infrastructure units only. Partition identifiers and processing order are not scores, ranks, priorities, target selections, confidence metrics, or biological interpretations.

## 2. Governing principles

1. Partition assignment uses immutable `EnsemblID` only.
2. The function is deterministic, versioned, independent of evidence values, and stable when unrelated profiles change.
3. Global canonical order remains the frozen Task #026 universe order.
4. Partitioning must preserve complete profile and record-level provenance.
5. Partition bytes are immutable after hash freeze.
6. Git stores metadata; large partition payloads are managed externally.
7. No runtime AI/LLM decision may assign, split, merge, validate, or route a partition.

## 3. Frozen partition function

Partition strategy identifier:

`ENSEMBL_SHA256_PREFIX_2_V0.1`

For each versioned EnsemblID string:

1. encode the exact `EnsemblID` as UTF-8 with no trimming or case conversion;
2. compute SHA256;
3. take the first two lowercase hexadecimal characters;
4. assign partition `p00` through `pff`.

Formally:

`partition_id = "p" + lowercase(SHA256(UTF8(EnsemblID)))[0:2]`

This defines 256 possible partitions. It does not use gene symbol, chromosome, gene type, expression value, FDR status, component state, evidence availability, or any biological attribute.

The partition function must have boundary fixtures containing fixed EnsemblID-to-partition mappings before implementation. Any change to encoding, digest algorithm, prefix length, or naming creates a new `partition_strategy_version` and requires full repartitioning.

## 4. Canonical ordering inside partitions

Each profile retains its global one-based `universe_ordinal` from the frozen Task #026 feature order. Within every partition:

- profile rows are ordered by ascending `universe_ordinal`;
- provenance rows are ordered by `universe_ordinal`, component order, feature-dictionary order, and `evidence_record_id`;
- no lexicographic gene-symbol order is permitted;
- identical inputs must yield identical line order and bytes.

Partition concatenation order is `p00` through `pff`, but this physical order does not replace global canonical universe order. Reconstruction of global order uses `universe_ordinal` from the profile index.

## 5. Artifact layout

A future release uses a logical layout equivalent to:

```text
release_metadata/
  full_profile_release_manifest.json
  universe_manifest.csv
  profile_index.csv
  profile_partition_manifest.csv
  profile_dependency_manifest.csv
  validation_report.md
profiles/
  p00/profiles.jsonl
  ...
  pff/profiles.jsonl
provenance/
  p00/profile_provenance_links.csv
  ...
  pff/profile_provenance_links.csv
```

This is a logical external-artifact contract, not a request to create these directories or files now.

### 5.1 Profile partitions

Each populated `profiles.jsonl` contains one complete profile object per line. Canonical serialization must be versioned and specify UTF-8, LF line endings, deterministic key ordering, deterministic number/string representation, no wall-clock fields, and one terminal newline.

### 5.2 Provenance partitions

Each provenance partition is the uncompressed tabular projection of the embedded profile lineage for the same EnsemblIDs. Its relationship key remains `(feature_id, evidence_record_id)`. Embedded and tabular lineage must match exactly.

### 5.3 Empty partitions

The partition manifest must enumerate all 256 partition identifiers. An empty partition records zero counts and `EMPTY_NO_ARTIFACT`; it must not point to an invented file. A populated partition must have both governed profile and provenance artifact records.

## 6. Manifest and index contracts

### 6.1 Profile index

One row per full-universe profile:

- `EnsemblID`;
- `universe_ordinal`;
- deterministic `profile_id`;
- `profile_version`;
- `evidence_snapshot_version`;
- `partition_strategy_version`;
- `partition_id`;
- profile partition artifact identifier;
- per-profile canonical content SHA256;
- component-set identifier or exact registered component list.

The profile index must contain exactly 29,606 rows and must be sorted by `universe_ordinal`.

### 6.2 Partition manifest

One row per partition and artifact role:

- release identifier;
- partition identifier;
- artifact role (`PROFILE_PAYLOAD` or `PROVENANCE_LINKS`);
- artifact identifier;
- schema version;
- profile count;
- provenance-link count where applicable;
- file size in bytes;
- SHA256;
- generator version;
- storage reference;
- validation status.

### 6.3 Release manifest

The release manifest freezes the universe, schema, profile, evidence snapshot, components, rules, extractors, generator, partition strategy, index/manifest hashes, global counts, lifecycle state, validation reports, and limitations.

## 7. Git and external storage boundary

Git-managed metadata includes schemas, code, partition strategy, small manifests/indexes, checksums, audit reports, and storage references. If an index or manifest exceeds the Task #018 governance threshold, Git retains a hash-frozen manifest stub and the full object is managed externally.

Externally managed immutable artifacts include profile JSONL partitions and provenance CSV partitions. Every external object must be version-pinned, size/hash validated on retrieval, and reproducible from frozen inputs. A mutable `latest` location is insufficient as the sole reference.

## 8. Deterministic generation contract

For each partition:

1. validate the global universe manifest and input hashes;
2. select EnsemblIDs by the frozen partition function only;
3. materialize each profile independently from frozen features, provenance, components, and rules;
4. order profiles by `universe_ordinal`;
5. emit canonical profile and provenance bytes;
6. validate schema, source-value identity, missingness, lineage, dependency, and rule output;
7. regenerate and compare bytes under the deterministic test protocol;
8. compute counts, size, and SHA256;
9. record an immutable storage reference;
10. update manifests only through a new immutable release candidate.

Parallel processing is permitted only when final ordering and bytes are independent of worker count, scheduling, hostname, temporary paths, and completion order.

## 9. Incremental partition behavior

The logical affected set is defined at profile level. The physical regeneration set is the unique set of partitions containing affected profiles.

For each affected partition:

- rematerialize every profile assigned to that partition from frozen inputs;
- reuse unaffected profile units only through verified content-addressed inputs, never by unchecked text splicing;
- restore canonical partition order;
- regenerate both profile and provenance partition artifacts;
- re-run all partition validations;
- issue new artifact identifiers, hashes, sizes, and storage references.

Unaffected partitions must retain byte-identical artifacts and hashes. A partition-strategy change requires full repartitioning.

## 10. Partition validation checklist

- [ ] Partition strategy identifier and function match this specification.
- [ ] Every full-universe EnsemblID maps to exactly one partition.
- [ ] No unknown or duplicate EnsemblID appears.
- [ ] All 256 partition identifiers are represented in the manifest.
- [ ] Per-partition and global profile counts reconcile to 29,606.
- [ ] Global ordinals are unique, contiguous, and source-order preserving.
- [ ] Profile and provenance membership agree within every partition.
- [ ] Composite provenance keys are unique.
- [ ] Embedded and tabular lineage match exactly.
- [ ] Canonical ordering and serialization fixtures pass.
- [ ] Two identical partition builds are byte-identical.
- [ ] Every populated external artifact has a size, SHA256, and immutable storage reference.
- [ ] No partition field or order is presented as score, rank, priority, selection, or interpretation.
- [ ] No AI or LLM runtime decision participates.

