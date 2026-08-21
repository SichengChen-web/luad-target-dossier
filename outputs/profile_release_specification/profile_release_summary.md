# Task #024 target evidence profile release specification summary

**Specification status:** COMPLETE  
**Profile release attempted:** No  
**Populated target profiles generated:** 0  
**Release schema definitions:** 56 (41 required, 4 optional, 11 prohibited)  
**Normative requirements:** 35  
**Blocking QC gates:** 29  
**Specification validation checks:** 18/18  
**Scores, rankings, target selections, recommendations, or biological conclusions generated:** No

## Release identity

One target profile is the complete set of 11 component rows for one immutable EnsemblID under one `profile_version` and one `evidence_snapshot_version`. Its deterministic identifier is:

```text
SHA256(EnsemblID | profile_version | evidence_snapshot_version | input_manifest_sha256 | rules_sha256)
```

`profile_version` identifies structure and interpretation semantics. `evidence_snapshot_version` identifies exact evidence artifacts, source releases, query scopes, and hashes. Changing either creates a different profile identity.

## Required representation

Every component retains exact claim, record, source, source-version, artifact, and artifact-hash references. Task #023 limitations are made explicit release requirements: record-level missingness/uncertainty use `record_id=status` pairs, and dependencies use exact edge IDs with edge-to-relationship and edge-to-level mappings.

The five states remain `OBSERVED`, `PARTIAL`, `MISSING`, `NOT_QUERIED`, and `CONFLICTING`. They are availability/uncertainty states with no numerical order or favorable/unfavorable meaning.

## Release decision

A future bundle may use `release_status=RELEASED` only when every blocking QC gate passes. Any identity, lineage, dependency, missingness, provenance, interpretation-safety, or deterministic-regeneration failure produces `WITHHELD`; the builder may not silently repair or partially release the profiles.

The expected number of profiles is parameterized as `N`, the number of `INCLUDED` EnsemblIDs in the frozen target manifest. Release requires exactly `N` unique profiles and `N × 11` component rows. Task #024 does not assume or instantiate a 29,606-entity manifest.

## Interpretation safety

Profile artifacts explicitly prohibit scores, ranks, priorities, recommendations, target-selection fields, therapeutic direction, overall target states, confidence aggregates, completeness percentages, and independent-evidence vote counts. Equivalent hidden derivations in code or sidecars are also prohibited.

## Preconditions carried forward from Task #023

1. Before full release, all 55 controlled-prose component/state predicates require executable, reviewed, versioned implementations tied to the frozen semantic predicates.
2. Release bundles must retain the frozen relational registries and exact record-status/dependency-edge mappings so profiles are reconstructible rather than dependent on lossy category lists.
3. Unacquired evidence domains remain `NOT_QUERIED`; they cannot be converted into missing or negative evidence.
4. Conflict validation must retain every record and never choose or average a preferred result.

## Limitations

This specification defines release readiness but does not demonstrate that a future full materializer satisfies it. No target universe was instantiated, no executable rule artifact was created, no release bundle was generated, and no biological or therapeutic interpretation was performed.
