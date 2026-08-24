# Release Validation Requirements v0.1

**Requirements:** `RELEASE_VALIDATION_REQUIREMENTS_V0.1`  
**Schema:** [Release Manifest Schema v0.1](../../schemas/release_manifest_schema_v0.1.json)

## 1. Purpose

These requirements define the fail-closed checks required before a future package can move through `PROPOSED`, `VALIDATED`, `FROZEN`, and `RELEASED`. They validate artifact integrity and reproducibility, not biological truth.

See the [Release Package Specification v0.1](release_package_specification_v0.1.md) and [Release Scope Policy v0.1](release_scope_policy_v0.1.md).

## 2. Manifest schema validation

A candidate manifest must:

- validate against `RELEASE_MANIFEST_SCHEMA_V0.1`;
- contain a unique release identity tuple;
- use only controlled release, lifecycle, validation, artifact-type, scope, provenance, and storage vocabularies;
- contain unique artifact IDs and relative paths;
- reconcile declared artifact count with the artifact array;
- preserve independent component and artifact version axes;
- reject unknown or prohibited fields at every object boundary.

## 3. Artifact integrity validation

For every artifact:

- resolve the exact registered byte object;
- verify file size and SHA256;
- verify artifact version and generating task;
- verify validation status and lifecycle eligibility;
- verify the upstream provenance identity and hash;
- verify the storage reference and availability state;
- reject symlink substitution or mutable replacement where the storage policy forbids it.

Partitioned or externally managed payloads additionally require partition count, member inventory, per-member size and SHA256, partition-set identity, and aggregate reconciliation.

## 4. Cross-layer reconciliation

The release validator must reconcile:

- exactly 29,606 immutable EnsemblID entities and canonical order where the included layer contract requires the full universe;
- two registered evidence component versions;
- landscape-to-summary identities and hashes;
- summary-to-routing identities and hashes;
- routing-to-case-dossier identities, rule traces, and deterministic selection tokens;
- presentation-artifact source release identities;
- component state, missingness, dependency, limitation, and provenance preservation asserted by upstream reports.

The release validator must not rerun scientific analyses to manufacture agreement. It compares frozen artifacts and their declared contracts.

## 5. Lifecycle gates

### Gate to `VALIDATED`

- schema validation passes;
- all required artifact checks pass;
- provenance and storage references are structurally complete;
- prohibited-field scan passes;
- failures and exclusions are explicit.

### Gate to `FROZEN`

- all included artifacts are `VALIDATED`;
- inventory, versions, hashes, sizes, provenance, and storage references are fixed;
- deterministic manifest regeneration is byte-identical;
- freeze authorization is recorded by a future release process.

### Gate to `RELEASED`

- the release manifest is `FROZEN`;
- all included artifacts are frozen and retrievable from their approved storage references;
- pending local-only storage placeholders are resolved or explicitly excluded;
- release authorization and distribution metadata are recorded.

No Task #037A output passes or attempts the `FROZEN` or `RELEASED` gates for a concrete package.

## 6. Determinism

The same frozen inputs, schema-generator version, and policy versions must produce byte-identical schema and schema-governance outputs. Generated governance bytes must not depend on randomness, wall-clock time, network access, APIs, external knowledge, or runtime AI/LLM decisions.

## 7. Prohibited-field validation

The validator must recursively reject exact fields including:

```text
score
rank
ranking
priority_score
confidence
probability
recommendation
target_quality
evidence_strength
biological_claim
therapeutic_direction
```

Closed schema objects must also reject undeclared fields. Rewording a prohibited concept does not make it acceptable.

## 8. Frozen-input protection

Before and after schema generation or future release materialization:

- hash every frozen input artifact;
- fail on any mismatch;
- verify that no previous scientific, governance, or communication artifact changed;
- permit writes only to the task's declared new paths;
- record final Git status without committing or pushing unless a later task explicitly authorizes it.

## 9. Required report

A release validation report must record:

- schema and policy versions;
- release identity under test;
- artifact counts by scope and storage class;
- all validation dispositions;
- exclusions, unavailable payloads, and pending storage actions;
- deterministic regeneration result;
- frozen-input hash reconciliation;
- explicit statement that packaging is not biological validation or target recommendation.

