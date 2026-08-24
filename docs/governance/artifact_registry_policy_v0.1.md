# Artifact Registry Policy v0.1

**Policy:** `ARTIFACT_REGISTRY_POLICY_V0.1`  
**Registry schema:** [Artifact Registry Schema v0.1](../../schemas/artifact_registry_schema_v0.1.json)  
**Release contract:** [Release Package Specification v0.1](release_package_specification_v0.1.md)

## 1. Purpose

The artifact registry is a governed inventory of existing computational artifacts that a future release package may reference. It records immutable identity, version, provenance, validation, dependency, size, and storage metadata. It does not create a release package, copy payloads, generate evidence, validate biology, or recommend targets.

Artifact registration means only that an identified computational artifact is discoverable and auditable under this policy.

```text
registry inclusion != biological validation
registry inclusion != evidence strength
registry inclusion != target importance
registry inclusion != therapeutic recommendation
```

## 2. Registry v0.1 scope

The first registry is deliberately bounded to the frozen release-framework inputs named by Task #037B:

- Task #033B Multi-component Evidence Landscape outputs;
- Task #034B Evidence Summary outputs;
- Task #035B transparent routing representation outputs;
- Task #036B representative case-dossier outputs;
- Task #036C presentation outputs;
- Task #037A release-governance artifacts;
- the Task #037B policy, schema, and deterministic generator.

The registry does not claim to inventory every historical repository file. Expansion requires an explicit registry version change and deterministic regeneration.

Registry outputs are described by `artifact_registry_manifest.json`; they are not rows in their own v0.1 CSV because a registry cannot contain its own final content hash without circular identity. A future registry version may register the frozen v0.1 registry outputs.

## 3. Registry key and path

Each row has one immutable `artifact_id`.

- Existing source-native external payload IDs are preserved exactly.
- File artifacts without a source-native ID receive a deterministic `ARTREG_` identity derived from repository-relative path and SHA256.
- IDs are unique within a registry version and are never silently reassigned.

Each row also has one unique `relative_path`:

- Git-managed artifacts use their actual repository-relative path.
- External payloads use a unique logical locator of the form `EXTERNAL::<artifact_id>`. This is registry metadata, not a copied repository path.

## 4. Required record fields

Every registry record contains:

- `artifact_id`;
- `relative_path`;
- `artifact_type`;
- `artifact_scope`;
- `artifact_version`;
- `generating_task`;
- `lifecycle_state`;
- `validation_status`;
- `sha256`;
- `size_bytes`;
- `storage_class`;
- `storage_reference`;
- `provenance_reference`;
- `dependency_reference`.

`provenance_reference` identifies the governed upstream release, snapshot, or contract from which the artifact derives. `dependency_reference` contains registry artifact IDs separated by `|`, or `NOT_APPLICABLE` for a root artifact. Dependencies are structural lineage references, not independent evidence counts.

## 5. Artifact types and scopes

Controlled artifact scopes are:

- `SCIENTIFIC` — governed computational evidence representations and their payload metadata;
- `GOVERNANCE` — schemas, manifests, policies, validation reports, session metadata, and generators;
- `COMMUNICATION` — presentation summaries and communication materials derived from frozen representations.

Scope classification describes artifact function. It does not classify scientific merit.

## 6. Lifecycle and validation

The registry preserves the Task #037A lifecycle vocabulary:

```text
PROPOSED -> VALIDATED -> FROZEN -> RELEASED
```

Task #037B registers artifacts at their observed governed lifecycle state. Registration does not promote an artifact. Current validated local candidates remain `VALIDATED`; pending external storage prevents them from being represented as `RELEASED`.

`validation_status` records artifact-level validation disposition and remains separate from lifecycle state.

## 7. Storage policy

### Git-managed artifacts

`storage_class=GIT_MANAGED` and `storage_reference` is the repository-relative file path. The registry records exact byte size and SHA256.

### External immutable payloads

`storage_class=EXTERNAL_IMMUTABLE`. The registry records only:

- source-native artifact ID;
- governed total size;
- partition-set SHA256;
- source manifest and partition-manifest dependencies;
- source-provided storage reference or placeholder.

Task #037B must not open, copy, move, upload, or rewrite external payload bytes. A pending storage placeholder remains pending and cannot support a `RELEASED` disposition.

## 8. Determinism and change control

Identical frozen inputs, registry policy, schema, and generator version must produce byte-identical registry artifacts. Generation must not depend on network access, APIs, randomness, wall-clock values, runtime AI/LLM decisions, or biological interpretation.

Changing an artifact byte changes its SHA256 and deterministic registry ID. Changing registry scope, fields, controlled vocabulary, or dependency semantics requires a new registry schema or policy version.

## 9. Prohibited fields and inferences

The registry must not contain target-level score, rank, ranking, priority score, confidence, probability, recommendation, target quality, evidence strength, biological claim, or therapeutic direction fields. Unknown fields are rejected by the closed schema.

Counts in the registry describe files and bytes only. They must not be transformed into evidence or target metrics.

