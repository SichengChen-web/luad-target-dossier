# Evidence Artifact Governance and Reproducibility Plan v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Task:** #018 — evidence artifact governance and reproducibility  
**Version:** v0.1  
**Date:** 21 August 2026  
**Status:** Working governance specification

## Purpose

This plan governs how computational artifacts are classified, tracked, frozen, reproduced, and validated as the project grows. It is not a biological analysis and makes no gene- or target-level assessment.

The governance objective is to ensure that a reviewer can answer five questions for every governed artifact:

1. What is it?
2. Where did it come from?
3. Which inputs and generator produced it?
4. Did it pass its defined QC?
5. Does its current content match the frozen hash?

## Artifact classes

### Class A — Source-controlled artifacts

Class A contains human-maintained analysis scripts, documentation, schemas, configuration, and workflow definitions. These artifacts normally enter ordinary Git after review because they are compact, diffable, and define how the project behaves.

Required controls include version history, review, syntax or format validation, and explicit references to task specifications or scientific decisions.

### Class B — Reproducible derived artifacts

Class B contains generated registries, summaries, figures, session records, and QC outputs that can be recreated from frozen inputs and a versioned generator.

Small, review-critical Class B files may enter Git. Bulky, frequently regenerated, or low-review-value derivatives should use external storage with a committed manifest. A derived artifact must never be treated as reproducible merely because it was committed: its inputs, generator, runtime, QC, and hash must also be known.

### Class C — External source snapshots

Class C contains external release metadata, dataset manifests, bounded schema snapshots, and source-version records. Small metadata and manifests may enter Git when licensing permits. Large external payloads normally belong in immutable external storage.

Required provenance includes official source, release/version, acquisition time, query or selection scope, license or redistribution constraint where applicable, immutable URI, file size, and SHA256.

### Class D — Large data objects

Class D contains large matrices, large evidence tables, omics objects, and other payloads unsuitable for ordinary Git blobs. In this v0.1 framework, an output at or above 50,000,000 bytes enters storage review; any file above 100,000,000 bytes is explicitly flagged. Known large-object formats also enter Class D regardless of current size.

Class D defaults to immutable external/object storage plus a small committed manifest. Git LFS is an exception for files that genuinely require version-coupled checkout semantics and must be configured before first commit.

## Manifest scope

The Task #018 manifest includes:

- every Git-tracked file;
- every non-ignored untracked project file; and
- every ignored physical file over 100 MB, so a large local artifact cannot disappear from governance merely because `.gitignore` hides it.

Local ignored files below 100 MB, such as `.DS_Store`, `.Rhistory`, virtual environments, and caches, are excluded because they are development artifacts rather than project evidence.

The Task #018 governance output directory is excluded from its own manifest. This avoids the impossible requirement that a manifest contain its own final content hash. `session_info.txt` instead freezes the hashes of the manifest, classification table, contract, and summary. The Task #018 script and plan remain ordinary inventoried artifacts.

## Manifest fields

Each artifact record contains:

- a stable path-derived `artifact_id`;
- repository-relative path;
- artifact class;
- exact byte size;
- SHA256 content hash;
- known generator;
- known input dependencies or an explicit documentation state;
- Git tracking status;
- an over-100-MB flag;
- a large-output review flag; and
- a flag for large files not tracked by Git.

The manifest records current state. It does not change tracking, move files, delete files, or decide retroactively how an existing artifact should be migrated.

## Classification rules

Classification is deterministic and mutually exclusive:

1. Files above 100 MB, output artifacts at or above 50 MB, and known large-object formats are Class D.
2. External manifests and explicitly named source/schema snapshots are Class C unless they meet Class D criteria.
3. Other files under `outputs/` are Class B.
4. Remaining scripts, documentation, configuration, and root project files are Class A.

The size thresholds are governance triggers, not scientific quality thresholds.

## Storage decision framework

### Ordinary Git

Use for Class A and for small Class B/Class C artifacts needed for review and downstream validation. Files should be text-based and reasonably diffable where practical.

### Git LFS

Consider only when a large artifact must remain coupled to Git commits, licensing permits distribution, collaborators need checkout semantics, and quota/bandwidth implications are understood. LFS tracking must precede the first commit of the large content. Git LFS does not replace provenance, QC, or hashes.

### External storage

Prefer for reproducible large derivatives, matrices, omics objects, external payload snapshots, and frequently refreshed data. Use immutable or versioned locations and keep a small Git-tracked manifest containing the URI, size, SHA256, source/release, schema, generator, dependencies, and reconstruction instructions.

## Reproducibility lifecycle

Every future task follows:

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

A change in source release, input hash, schema, code, parameters, or dependency lineage creates a new artifact version. Missing files and hash mismatches must fail clearly. Regeneration must not silently substitute data or overwrite frozen inputs.

## Current audit boundary

Task #018 starts from committed Task #017 at Git commit `96f6cb103e8341a9b0eec4ba65f58fb65aa6bb9b`. The builder requires a clean tracked worktree and validates that all 190 committed Task #001–#017 files remain unchanged.

The known ignored record-level Task #014 artifact is also pinned before and after generation:

- path: `outputs/evidence_claim_architecture/evidence_record_registry.csv`
- size: 139,836,748 bytes
- SHA256: `76ec5056fb4e468176073073532204d231765d4f0cd70dbb6cfe4ad8bf752343`

This task does not alter its storage or tracking state.

## Validation and non-actions

The builder verifies unique artifact paths and IDs, valid SHA256 values, explicit classification, nonblank required fields, large-file detection, the known ignored artifact, unchanged Git HEAD, and a clean tracked/staged diff after generation.

Task #018 performs no network access, package installation, file deletion, output migration, Git LFS operation, commit, push, or history rewrite. It does not analyze genes, score or rank targets, select candidates, or make biological interpretations.
