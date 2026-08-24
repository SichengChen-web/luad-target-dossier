# Release Scope Policy v0.1

**Policy:** `RELEASE_SCOPE_POLICY_V0.1`  
**Applies to:** future manifests governed by `RELEASE_MANIFEST_SCHEMA_V0.1`

## 1. Scope principle

Release inclusion is an artifact-governance decision. Inclusion means that identified bytes, provenance, versions, validation status, and storage location are disclosed. It does not mean that the artifact's scientific content is biologically validated or therapeutically endorsed.

The package contract is defined in the [Release Package Specification v0.1](release_package_specification_v0.1.md). Validation gates are defined in the [Release Validation Requirements v0.1](release_validation_requirements_v0.1.md).

## 2. Scientific artifact scope

The scientific scope supports the following governed artifact types:

1. evidence components, preserving independent component versions and source-snapshot axes;
2. the multi-component evidence landscape;
3. Evidence Summary representations;
4. transparent non-ordinal routing representations;
5. representative structural case dossiers.

Scientific artifacts are included as frozen structural evidence representations. Their inclusion does not generate new evidence, evaluate a target, or convert missingness into negative evidence.

## 3. Governance artifact scope

The governance scope supports:

- machine-readable schemas;
- policy and specification documents;
- validation requirements and reports;
- artifact, partition, provenance, dependency, and release manifests;
- deterministic generator source and session metadata.

Governance artifacts define or verify contracts. They do not replace source evidence or underlying record-level lineage.

## 4. Communication artifact scope

The communication scope supports:

- validated presentation artifacts;
- figures registered with source-artifact and generator provenance;
- poster materials registered with source-artifact and generator provenance.

Figures and poster materials are eligible artifact types, not assumed existing outputs. A future manifest may include them only when their immutable bytes, versions, generating task, validation status, provenance, and storage reference are registered. Task #037A creates none.

Communication artifacts must preserve the interpretation boundaries of their sources. Layout, labels, or visual emphasis must not introduce an ordering, score, recommendation, biological claim, or hidden target evaluation.

## 5. Required and conditional inclusion

A future reproducible research release must include or reference:

- the release manifest and its schema;
- all schemas and policies needed to interpret included records;
- validation reports for every included artifact;
- immutable hashes for all included bytes;
- provenance and dependency manifests needed to trace each representation;
- deterministic generators or a documented execution contract;
- external-storage references for payloads not stored in Git.

An artifact may be omitted only with an explicit exclusion reason. Omission must not be represented as absence of scientific evidence.

## 6. Storage boundary

### Git-managed

Source code, small schemas, governance documents, manifests, indexes, checksums, session records, and small validated outputs normally enter Git.

### Externally managed

Large immutable payloads remain outside ordinary Git when governed size or artifact policies require it. Their manifest records must include content identity, size, SHA256, storage class, storage URI or governed placeholder, availability status, and provenance.

`FROZEN` requires immutable bytes and complete content identity. `RELEASED` additionally requires an approved retrievable storage reference; local staging or a pending placeholder is insufficient for public release.

## 7. Explicit exclusions

The release scope excludes:

- newly retrieved or newly inferred evidence;
- unregistered mutable source data;
- runtime AI/LLM decisions;
- target scores or rankings;
- candidate or target recommendations;
- biological or therapeutic claims created by packaging;
- secrets, credentials, local caches, and undocumented environment artifacts.

## 8. Scope changes

Adding a new artifact type, component, source snapshot, communication product, or storage class requires reviewed governance and a new compatible release version. Existing frozen artifacts must not be rewritten to simulate compatibility.

