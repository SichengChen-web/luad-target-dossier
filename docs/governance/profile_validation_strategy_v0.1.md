# Profile Validation Strategy v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Version:** v0.1  
**Status:** Frozen validation specification; no profiles generated

## 1. Purpose

This strategy defines validation for a future 29,606-profile materialization. Validation asks whether profile artifacts preserve frozen identity, values, missingness, provenance, dependency, rules, versions, and reproducibility. It does not assess target quality, score or rank targets, prioritize candidates, interpret biology, or make therapeutic recommendations.

No validation result may be computed or adjudicated by a runtime AI/LLM decision.

## 2. Validation principles

1. Exhaustive automated validation covers every profile and provenance relationship.
2. Boundary fixtures validate deterministic semantics at known rule and missingness edges.
3. Deterministic sampling supports independent human traceability audit but never substitutes for exhaustive checks.
4. Validation failures stop release; they do not trigger manual data repair.
5. A passing validation establishes conformance to the frozen contract, not biological or therapeutic validity.

## 3. Validation inputs

The validator must freeze and hash:

- full universe manifest and canonical order;
- Task #026 feature table and feature dictionary;
- governed Task #026 provenance artifact;
- profile/component schemas;
- component definitions;
- executable state-rule registry and precedence;
- profile, schema, evidence-snapshot, component, rule, extractor, generator, and partition-strategy versions;
- profile index, partition manifest, and dependency/affected-set manifest;
- candidate release partition artifacts.

The validator must not use gene symbols as keys or retrieve mutable evidence during validation.

## 4. Complete automated validation

### 4.1 Universe and identity

- exactly 29,606 profiles;
- exactly 29,606 unique EnsemblIDs;
- profile EnsemblIDs exactly equal the Task #026 universe;
- global ordinals exactly preserve Task #026 row order;
- deterministic profile IDs match `(EnsemblID, profile_version, evidence_snapshot_version)`;
- every profile occurs in exactly one partition and one index row;
- no biological filtering or silent identity repair.

### 4.2 Schema and versioning

- every payload validates against the declared schema;
- no undeclared or forbidden field exists;
- `schema_version`, `profile_version`, and `evidence_snapshot_version` are distinct required fields;
- component, rule, extractor, generator, and partition versions resolve;
- every manifest and payload reports compatible versions.

### 4.3 Feature fidelity

For every EnsemblID and every governed feature:

- profile feature exists exactly once;
- `feature_id`, name, value, data type, and extractor version match Task #026;
- string/number/Boolean representation follows the frozen serialization contract;
- no score, rank, priority, confidence metric, target selection, biological interpretation, or recommendation field exists.

Expected mismatch count: zero.

### 4.4 Missingness

- each feature's missingness equals its governed provenance/input state;
- allowed states remain `OBSERVED`, `NOT_FOUND`, `NOT_QUERIED`, `NOT_APPLICABLE`, and `UNKNOWN`;
- no state is collapsed to generic null;
- `NOT_FOUND` is not converted to negative evidence;
- `NOT_QUERIED` is not converted to biological absence.

Expected violation count: zero.

### 4.5 Provenance and foreign keys

- every profile feature has at least one provenance relationship;
- every `(feature_id, evidence_record_id)` key is unique;
- embedded and tabular provenance are exactly equivalent;
- claim, evidence-record, source, artifact, dependency, extraction-rule, extractor, and generator references resolve;
- partition/global provenance counts reconcile;
- no relationship is compressed into counts or omitted.

Expected broken-link and missing-link counts: zero.

### 4.6 Dependency and evidence inflation

- dependent records retain their relationship and dependency level;
- `TRANSCRIPT_PRIMARY` and `TRANSCRIPT_ROBUSTNESS` remain `SHARED_DATASET` / `DEPENDENT`;
- no dependent records are relabelled independent;
- record or component counts are not aggregated into evaluative metrics;
- no component voting or hidden profile aggregation exists.

Expected dependency and inflation violations: zero.

### 4.7 State-rule reproduction

- typed inputs match the frozen component feature contract;
- executable predicates and precedence match the declared state-rule version;
- each component resolves deterministically under the frozen rules;
- stored state and rule identity reproduce exactly;
- rule review status is retained;
- no manual or AI runtime decision changes a state.

Expected state mismatches: zero.

### 4.8 Partition and artifact integrity

- partition assignment matches `ENSEMBL_SHA256_PREFIX_2_V0.1`;
- all 256 manifest partition identifiers reconcile;
- partition counts sum to global counts;
- profile/provenance membership and ordering match indexes;
- each artifact's byte size and SHA256 match its manifest;
- each external storage reference resolves to the exact bytes;
- unchanged partitions in an incremental release remain byte-identical.

### 4.9 Deterministic regeneration

At minimum:

- each partition is independently generated twice from identical frozen inputs and compared byte-for-byte;
- the global indexes/manifests are independently generated twice and compared byte-for-byte;
- one complete release regeneration reproduces every partition and manifest hash before lifecycle promotion.

No timestamp, temporary path, worker order, hostname, random seed, or mutable network response may affect governed bytes.

## 5. Deterministic boundary fixtures

Fixtures are versioned, synthetic or mechanically selected structural examples. They are not biologically chosen genes and are not target candidates.

Required fixture families:

1. **Identity fixtures** — valid EnsemblID, versioned/unversioned mismatch, duplicate identity, wrong feature identity.
2. **Profile schema fixtures** — required field, extra field, type mismatch, cardinality, version mismatch.
3. **Feature-value fixtures** — direction categories, FDR threshold met/not met, effect threshold met/not met, sensitivity consistency/mixed.
4. **Missingness fixtures** — all five allowed states and prohibited conversions.
5. **State fixtures** — `CONFLICTING`, `OBSERVED`, `MISSING`, `PARTIAL`, and `NOT_QUERIED`, including precedence guards.
6. **Provenance fixtures** — one-record feature, two-record dependent feature, duplicate composite key, missing claim/record/source/rule link.
7. **Dependency fixtures** — shared-dataset dependent pair, unknown relationship, prohibited false independence.
8. **Partition fixtures** — fixed EnsemblID-to-prefix mappings, first/last prefix, ordering, empty partition, multi-worker serialization equivalence.
9. **Incremental fixtures** — one-profile change, several changes in one partition, changes across partitions, global rule/schema change, unverifiable affected set.

Every fixture has a stable fixture ID, frozen input, expected outcome, version, and review status. Fixture outcomes are deterministic and cannot be supplied by an LLM at runtime.

## 6. Deterministic sampling audit

The sampling audit is a secondary human review of source-to-profile traceability after exhaustive automated validation.

For a release with `N` profiles:

1. compute `audit_key = SHA256(UTF8(release_id + "|" + EnsemblID))`;
2. sort ascending by `audit_key`, then EnsemblID;
3. select `ceil(0.01 × N)` profiles;
4. for the 29,606-profile v0.1 universe, select **297** profiles;
5. add all deterministic boundary-fixture entities not already selected;
6. record the algorithm, release ID, selected EnsemblIDs, and audit findings.

The audit hash order is not a target ranking and must never be exposed as one. Sampling does not permit automated checks to be skipped.

For each sampled profile, a reviewer traces:

- profile identity to universe manifest;
- every feature value to the Task #026 row and dictionary;
- missingness to provenance;
- every provenance relationship to claim, evidence record, source, artifact, and dependency;
- component state to typed inputs and rule ID;
- partition/index membership and hashes;
- absence of evaluative or interpretive fields.

Sample-audit discrepancies fail the release and trigger root-cause analysis over the complete affected scope, not correction of sampled rows alone.

## 7. Validation outputs

A future validation run must produce:

- machine-readable check registry with check IDs and pass/fail counts;
- universe/identity validation table;
- feature/value/missingness validation summary;
- provenance/dependency validation summary;
- state-rule reproduction summary;
- partition/hash reconciliation table;
- deterministic regeneration comparison;
- boundary-fixture result matrix;
- deterministic sampling manifest and human audit report;
- unresolved-issue registry;
- final validation report linked to the candidate release manifest.

These outputs are validation evidence, not target evidence.

## 8. Failure policy

- Any nonzero identity, value, missingness, broken-lineage, dependency, state, schema, partition, or hash violation blocks lifecycle promotion.
- Validation must not silently drop, repair, impute, reinterpret, or reorder a failing profile.
- Root cause and affected scope must be documented.
- Corrected artifacts require appropriate new versions and hashes.
- A validator cannot alter profile contents or state rules because a result appears undesirable.

## 9. Lifecycle boundary

Passing complete automated validation is necessary but not sufficient for `SCIENTIFIC_REVIEWED` or `PUBLIC_RELEASE`. Boundary fixtures and sampling audit validate representation. Independent scientific review separately evaluates whether evidence meanings, limitations, and interpretation boundaries are documented correctly.

No validation outcome constitutes target prioritization, therapeutic recommendation, or biological validation.

## 10. Validation checklist

- [ ] Frozen inputs and all version axes are hash-validated.
- [ ] Exhaustive checks cover all 29,606 profiles and all provenance links.
- [ ] Universe, identity, ordering, schema, and partition checks pass.
- [ ] Feature values and missingness exactly match governed inputs.
- [ ] Complete provenance and foreign-key checks pass.
- [ ] Dependency and evidence-inflation checks pass.
- [ ] State-rule reproduction passes without runtime judgement.
- [ ] Boundary fixtures cover all required families.
- [ ] Deterministic sampling selects 297 profiles plus fixture entities.
- [ ] Independent full regeneration reproduces every hash.
- [ ] No prohibited evaluative or interpretive field exists.
- [ ] No AI or LLM runtime decision participates.
- [ ] Failures, limitations, and untested paths are explicit.
- [ ] Lifecycle promotion remains a separate human governance action.

