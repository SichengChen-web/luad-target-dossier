# Task #030 full profile release-candidate validation report

## Scope

This release candidate materializes structural evidence profiles for the complete frozen Task #026 EnsemblID universe. It does not score, rank, prioritize, select, recommend, or biologically interpret targets.

## Release-candidate identity

- Release candidate: `PRC_5A13C5055A54AF794EDD0898`
- Profiles: **29,606**
- Canonical order: exact Task #026 feature-row order
- Profile version: `FULL_UNIVERSE_TARGET_EVIDENCE_PROFILE_V0.1`
- Schema version: `TARGET_EVIDENCE_PROFILE_FULL_SCHEMA_V0.1`
- Evidence snapshot: `TASK026_TRANSCRIPTOMIC_FEATURES_SHA256_4014469439ff14d27c451a356cf7711daa7a5331c58326eced2cf96edb298844`
- Component: `COMP_TRANSCRIPTOMIC_EVIDENCE`
- Generator: `FULL_PROFILE_MATERIALIZER_V0.1`
- Partition strategy: `ENSEMBL_SHA256_PREFIX_2_V0.1`
- Lifecycle: `UNASSIGNED_RELEASE_CANDIDATE_AWAITING_HUMAN_GOVERNANCE_ACTION`

## Materialization summary

- Profile feature values: **651,332**
- Record-level provenance relationships: **1,036,210**
- Profile partitions: **256**
- Provenance partitions: **256**
- Structural state counts: `{"CONFLICTING":3435,"OBSERVED":26171}`
- Profile partition bytes: **563,260,546**
- Provenance partition bytes: **635,738,319**
- Profile partition-set SHA256: `235015ec2a2be41e9f1865932b2f93f5d162e9f9a44c1bde5d4a2335024f87c7`
- Provenance partition-set SHA256: `79c030fe6fab5866a7262050cea87d4d790240e18ae2ab5268edc8c1bf2467e3`

## Validation

- Universe identity, cardinality, and canonical order: **PASS**.
- Full profile schema and version axes: **PASS**.
- All feature values identical to Task #026: **PASS**.
- Complete embedded and tabular provenance equivalence: **PASS**.
- Composite provenance-key uniqueness: **PASS**.
- Governed dependency identifiers: **PASS**.
- Task #025 state reproduction and precedence: **PASS**.
- All 256 partition assignments and global reconciliation: **PASS**.
- Per-partition two-pass byte-identical generation: **PASS**.
- Five state-boundary and four partition fixtures: **PASS**.
- Deterministic 297-profile audit-sample manifest: **PASS**.
- Frozen input hashes unchanged after generation: **PASS**.
- Runtime AI/LLM decisions, mutable retrieval, scoring, ranking, selection, recommendation, and biological interpretation: **NOT USED / NOT GENERATED**.

## Governance limits

This is a local release candidate, not a lifecycle promotion. External immutable storage references are pending, the Task #025 rules remain awaiting independent scientific review, and deterministic sampling identifies records for a future human traceability audit but does not itself complete that audit. Full-universe materialization validates infrastructure conformance only; it does not validate any target scientifically.
