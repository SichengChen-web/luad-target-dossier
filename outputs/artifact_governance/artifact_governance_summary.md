# Task #018 artifact governance summary

**Artifacts inventoried:** 193  
**Git tracked:** 190  
**Untracked Task #018 definitions:** 2  
**Ignored large artifacts included:** 1  
**Files over 100 MB:** 1  
**Output artifacts at or above 50 MB review threshold:** 4

## Classification

| Class | Meaning | Artifacts | Total bytes | Git policy |
| --- | --- | ---: | ---: | --- |
| A | Source-controlled artifacts | 34 | 836,114 | Track directly in Git after review; keep text-based and diffable where practical. |
| B | Reproducible derived artifacts | 154 | 198,043,953 | Track small review-critical artifacts; otherwise store externally with a manifest and hash. |
| C | External source snapshots | 1 | 1,102 | Track small metadata/manifests; do not commit bulky source payloads by default. |
| D | Large data objects | 4 | 325,511,835 | Do not add to ordinary Git; use external storage by default or Git LFS only when justified before first commit. |

## Files over 100 MB

- `outputs/evidence_claim_architecture/evidence_record_registry.csv` — 139,836,748 bytes; Class D; `IGNORED_NOT_TRACKED`; SHA256 `76ec5056fb4e468176073073532204d231765d4f0cd70dbb6cfe4ad8bf752343`

## Large output review

- `outputs/evidence_claim_architecture/evidence_record_registry.csv` — 139,836,748 bytes; Class D; `IGNORED_NOT_TRACKED`
- `outputs/evidence_claim_architecture/missingness_uncertainty_registry.csv` — 52,066,346 bytes; Class D; `TRACKED_GIT`
- `outputs/integrated_registry/integrated_target_registry.csv` — 60,222,492 bytes; Class D; `TRACKED_GIT`
- `outputs/tractability_safety/tractability_assessments.csv` — 73,386,249 bytes; Class D; `TRACKED_GIT`

## Governance observation

1 file over 100 MB is not tracked by Git. It is currently ignored and retained locally; this task did not delete, move, add, or alter it. Before relying on it across environments, the project needs an immutable external-storage location or a separately approved Git LFS decision plus a committed retrieval/reconstruction manifest.

The three tracked Class D CSVs between 50 MB and 100 MB also warrant storage review before continued growth. Their current Git state was not changed.

## Validation boundary

All Task #001–#017 tracked files matched the frozen Git worktree before and after generation. The known ignored Task #014 record table retained its expected size and SHA256. HEAD did not change. No network access, package installation, file deletion, output rewrite, commit, push, Git LFS operation, or history rewrite occurred.

The governance control bundle is intentionally excluded from its own manifest to avoid self-referential hashes. Its output hashes are recorded in `session_info.txt`.
