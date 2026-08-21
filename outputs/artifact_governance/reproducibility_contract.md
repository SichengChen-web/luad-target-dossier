# Reproducibility Contract v0.1

## Contract chain

```text
input manifest
      ↓
versioned analysis script and configuration
      ↓
generated artifact
      ↓
QC validation
      ↓
SHA256 hash freeze and session provenance
```

Every future task must declare its input paths, immutable identifiers, source versions, expected hashes, generator, runtime configuration, output paths, missingness rules, QC assertions, and interpretation boundary before an artifact is treated as frozen.

## Required task record

Each task must preserve:

1. **Input manifest:** relative path or immutable external URI, artifact class, file size, SHA256, source/release, acquisition timestamp where relevant, and dependency lineage.
2. **Generator:** version-controlled script, parameters/configuration, package/runtime versions, Git branch and commit, and network-use declaration.
3. **Generated artifact:** stable schema, immutable primary key where applicable, deterministic ordering where meaningful, explicit missingness, and no silent overwrites of frozen inputs.
4. **QC validation:** row counts, uniqueness, referential integrity, schema checks, expected-versus-observed assertions, and domain-specific validation.
5. **Hash freeze:** SHA256 for every frozen input and output, plus a session record that binds hashes to the Git commit and runtime.

## What enters ordinary Git

- Class A source-controlled artifacts should enter Git after review.
- Small Class B outputs may enter Git when they are necessary for scientific review, validation, or downstream reproducibility and remain reasonably diffable.
- Small Class C release metadata and manifests may enter Git when licensing permits.
- No secret, credential, personal cache, virtual environment, or transient application file enters Git.

Generated files do not enter Git merely because they exist. Their inclusion requires a documented review purpose, stable generation, and acceptable repository impact.

## What does not enter ordinary Git

- Class D matrices, large evidence tables, omics objects, raw API payload collections, and bulky external datasets.
- Reconstructable caches and intermediate files with no review value.
- Restricted, licensed, sensitive, or redistribution-prohibited source data.
- Files approaching or exceeding host limits before an explicit storage decision.

Files stored outside Git require a small committed manifest containing immutable location, size, SHA256, source/release, schema, generator, and retrieval or reconstruction instructions. Missing external payloads must fail clearly rather than trigger silent substitution.

## Git LFS decision rule

Git LFS is appropriate only when a large file must remain version-coupled to repository commits, collaborators need Git-like checkout semantics, redistribution is permitted, and storage/bandwidth quotas are understood. LFS tracking must be configured **before the file's first commit**.

A file above 50 MB requires storage review. A file above 100 MB must not be added as an ordinary Git blob. Git LFS does not make a reproducible derivative scientifically preferable to external storage and does not replace source, version, schema, or checksum metadata.

This task does not install or configure Git LFS and does not migrate existing files.

## When external storage is preferred

Use immutable external/object storage for reproducible large derivatives, raw or versioned source snapshots, large matrices, frequently refreshed datasets, and artifacts that do not need line-level Git review. Prefer content-addressed or versioned locations with retention controls. The repository should retain the manifest and reconstruction contract.

## Freeze and change control

- A frozen artifact is identified by path, size, SHA256, generator, input hashes, and Git commit/session record.
- Regeneration must write a new version or be explicitly approved as a replacement; discrepancies must be reported.
- Changed source releases, schemas, parameters, or dependencies require a new task/version and refreshed QC.
- `NOT_FOUND`, `NOT_QUERIED`, retrieval failure, and negative evidence must remain distinct.
- Derived summaries never replace their underlying record-level provenance.
- Git history must not be rewritten to implement routine artifact governance. Any future repository migration is a separate, explicitly authorized operation with backups and collaborator coordination.

## Governance-manifest boundary

`artifact_manifest.csv` inventories all Git-tracked files, all non-ignored untracked project files, and ignored files over 100 MB at the scan boundary. Local ignored files below that threshold are excluded. The Task #018 governance output directory is excluded from its own manifest because a manifest cannot contain its own final SHA256 without changing itself. `session_info.txt` freezes the hashes of the manifest, classification, contract, and summary instead.
