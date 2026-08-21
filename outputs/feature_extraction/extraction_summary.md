# Task #026 transcriptomic feature extraction summary

## Scope

This layer deterministically represents frozen transcriptomic observations and evidence availability. It does not execute Task #025 state rules, materialize target profiles, score or rank genes, select candidates, infer biological importance, or infer therapeutic direction.

## Extracted architecture

- Immutable entities retained: **29,606** unique EnsemblIDs in Task #012 order.
- Normalized features per entity: **22**.
- Task #025 typed evaluator inputs implemented: **11**.
- Explicit feature-to-record provenance links: **1,036,210**.
- Transcriptomic claims: one per EnsemblID.
- Source records: one `TRANSCRIPT_PRIMARY` and one `TRANSCRIPT_ROBUSTNESS` per EnsemblID.
- Dependency treatment: primary and S1-S6 records remain linked as `SHARED_DATASET` / `DEPENDENT`; they are not independent votes.

## Descriptive observations

- Frozen U1 (BH FDR < 0.05): **21,232**.
- Frozen U2 (U1 plus absolute primary logFC at least 0.5): **14,064**.
- Primary direction categories: `{"TUMOR_HIGHER":15283,"TUMOR_LOWER":14323}`.
- Absolute primary logFC threshold categories: `{"THRESHOLD_MET":14361,"THRESHOLD_NOT_MET":15245}`.
- Sensitivity direction consistency categories: `{"CONSISTENT_DIRECTION":26171,"MIXED_DIRECTION":3435}`.
- Frozen Task #014 transcript conflict conditions represented: **3,435**.

These are structural/statistical descriptions of the frozen analysis. They do not establish causality, importance, efficacy, safety, actionability, or therapeutic direction.

## Validation

- Frozen input SHA256 hashes: **PASS**.
- Task #012 row count, order, unique EnsemblID, U1, and U2 assertions: **PASS**.
- Task #013 evidence-type and dependency semantics: **PASS**.
- Task #014 claim, record, source, raw-reference, missingness, and dependency links: **PASS**.
- Task #021 role/type compatibility: **PASS**.
- Task #025 exact 11-feature typed input contract: **PASS**.
- Every feature has at least one explicit provenance link to a valid claim, evidence record, source, artifact, extraction rule, and extractor version: **PASS**.
- Controlled feature values and missingness vocabulary: **PASS**.
- Forbidden field detection: **PASS**.
- Byte-identical two-pass regeneration: **PASS**.
- Previous frozen artifact hashes unchanged after generation: **PASS**.
- Network, package installation, randomness, wall-clock values, LLM runtime decisions, profile generation, scoring, ranking, candidate selection, and biological interpretation: **NOT USED / NOT GENERATED**.

## Interpretation and review boundaries

`THRESHOLD_NOT_MET` is a frozen statistical observation and is not negative biological evidence. `NOT_FOUND` and `NOT_QUERIED` remain distinct controlled missingness states; neither is converted to biological absence. Record counts are audit metadata only.

The Task #025 state rules remain `AWAITING_INDEPENDENT_SCIENTIFIC_REVIEW`; this extractor does not resolve or release component states. External-source extractors remain unimplemented and require separate source-specific contracts. The explicit provenance registry is expected to be a large derived artifact and should be handled under the Task #018 artifact-governance policy before commit or release.
