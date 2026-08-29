# MMP11 internal evidence audit validation

> MMP11 is used as an illustrative biological worked example for scientific communication. Its inclusion is not the result of a project-level therapeutic target ranking, scoring, or recommendation procedure.

**Overall validation: PASS**

| Check | Result |
|---|---|
| Immutable EnsemblID consistency | PASS |
| No symbol-based artifact joins | PASS |
| Primary numerical reconciliation | PASS |
| Sensitivity numerical reconciliation | PASS |
| Task #014 transcriptomic source records resolve | PASS |
| Disease raw source records resolve | PASS |
| All feature provenance relationships resolve | PASS |
| Component identities reconcile | PASS |
| Downstream representation identities reconcile | PASS |
| Component states preserved downstream | PASS |
| Frozen input hashes verified before generation | PASS |
| External network access | PASS |
| Runtime AI decisions | PASS |
| No target evaluation fields generated | PASS |

## Determinism and scope controls

- Frozen input files: 34; each SHA256 matched the generator's pinned value before generation.
- Frozen hashes are checked again after output writing by the executable.
- Output generation is performed twice in memory and must be byte-identical before files are written.
- Network access: prohibited and not used.
- Runtime AI decisions: prohibited and not used.
- Existing scientific/governance artifacts: read-only; working-tree scope is enforced.
- Differential-expression fitting, component regeneration, target evaluation, and therapeutic interpretation: not performed.

## Counts

- Bounded governed source-evidence units: 16.
- Individual sensitivity model rows: 6.
- Feature-level provenance relationships: 229.
- Qualitative dependency-map relationships: 21.

> MMP11 is used as an illustrative biological worked example for scientific communication. Its inclusion is not the result of a project-level therapeutic target ranking, scoring, or recommendation procedure.
