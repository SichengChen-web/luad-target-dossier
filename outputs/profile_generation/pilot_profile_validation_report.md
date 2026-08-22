# Task #027 pilot profile validation report

## Scope

This pilot deterministically materializes transcriptomic evidence observations for ten immutable EnsemblIDs. It executes the frozen Task #025 transcriptomic state predicates only. It does not evaluate target quality, score or rank targets, select therapeutic candidates, recommend therapies, infer biological importance, or generate biological interpretations.

## Deterministic pilot selection

Rule `PILOT_SELECTION_2X2X2_PLUS_LEXICAL_FILL_V0.1`: Select the lexicographically smallest EnsemblID in each of the eight effect_direction_observed x fdr_pass_status x sensitivity_consistency_category cells, in frozen cell order; then add the two lexicographically smallest remaining EnsemblIDs.

| EnsemblID | Basis | Direction | FDR status | Sensitivity category |
|---|---|---|---|---|
| `ENSG00000000003.14` | CELL_1 | TUMOR_HIGHER | THRESHOLD_MET | CONSISTENT_DIRECTION |
| `ENSG00000229097.1` | CELL_2 | TUMOR_HIGHER | THRESHOLD_MET | MIXED_DIRECTION |
| `ENSG00000001631.15` | CELL_3 | TUMOR_HIGHER | THRESHOLD_NOT_MET | CONSISTENT_DIRECTION |
| `ENSG00000003987.13` | CELL_4 | TUMOR_HIGHER | THRESHOLD_NOT_MET | MIXED_DIRECTION |
| `ENSG00000000938.12` | CELL_5 | TUMOR_LOWER | THRESHOLD_MET | CONSISTENT_DIRECTION |
| `ENSG00000073169.13` | CELL_6 | TUMOR_LOWER | THRESHOLD_MET | MIXED_DIRECTION |
| `ENSG00000002330.13` | CELL_7 | TUMOR_LOWER | THRESHOLD_NOT_MET | CONSISTENT_DIRECTION |
| `ENSG00000000971.15` | CELL_8 | TUMOR_LOWER | THRESHOLD_NOT_MET | MIXED_DIRECTION |
| `ENSG00000000419.12` | LEXICAL_FILL_1 | TUMOR_HIGHER | THRESHOLD_MET | CONSISTENT_DIRECTION |
| `ENSG00000000457.13` | LEXICAL_FILL_2 | TUMOR_HIGHER | THRESHOLD_MET | CONSISTENT_DIRECTION |

This mechanical pilot-universe selection is not scientific target selection.

## Profile schema

- Schema: `TARGET_EVIDENCE_PROFILE_PILOT_SCHEMA_V0.1`
- Profile version: `PILOT_TARGET_EVIDENCE_PROFILE_V0.1`
- Evidence snapshot: `TASK026_TRANSCRIPTOMIC_FEATURES_SHA256_4014469439ff14d27c451a356cf7711daa7a5331c58326eced2cf96edb298844`
- Immutable identity: `EnsemblID`
- Profiles: 10
- Component per profile: `COMP_TRANSCRIPTOMIC_EVIDENCE` only
- Features per profile: 22
- Feature values are stored as their exact Task #026 strings.
- Every feature embeds all governed provenance links without compression.
- Component states are structural Task #025 rule outputs; they are not target evaluations.

## Validation results

- Closed schema and required-field validation: **PASS**.
- Ten unique EnsemblIDs and deterministic order: **PASS**.
- Direction/FDR/sensitivity coverage: **PASS**.
- Profile feature values identical to Task #026: **PASS** (0 mismatches).
- Missingness identical to Task #026 provenance: **PASS** (0 mismatches).
- Every profile feature has provenance: **PASS** (0 missing).
- Uncompressed provenance relationships: **PASS** (350 links).
- Task #025 typed input and precedence contract: **PASS**.
- Structural component-state counts: `{"CONFLICTING":4,"OBSERVED":6}`.
- Forbidden field detection: **PASS**.
- Byte-identical two-pass generation: **PASS**.
- Frozen input hashes unchanged after generation: **PASS**.
- Network access, package installation, randomness, wall-clock values, LLM decisions, scoring, ranking, recommendation, and biological interpretation: **NOT USED / NOT GENERATED**.

## Core output hashes

- `pilot_profiles.json`: `c7a08a6c165c6e2fd6ada63333a7be4cb2c34333ee92051cc8c60de1da50774d`
- `pilot_profile_provenance_links.csv`: `b3bb00437f6d6c085d7dcdecbaf95cc1bf686e75dc968e8781c02c878ae7bde0`
- `profile_schema_v0.1.json`: `c19eff421654bdc002dc3901adec694f8a3ccf76cb4901970d858f3c699ae750`

## Interpretation boundaries and unresolved assumptions

The pilot validates the current transcriptomic component only. It does not validate future external-source components or a complete multi-domain profile. The selected records instantiate `OBSERVED` and `CONFLICTING` structural component states; the current all-observed Task #026 snapshot does not exercise `MISSING`, `NOT_QUERIED`, or `PARTIAL` profile paths.

Task #025 rules retain `AWAITING_INDEPENDENT_SCIENTIFIC_REVIEW`; these pilot objects are labelled `PILOT_VALIDATION_ONLY` and are not a release of scientific target conclusions. The Task #026-A concrete external storage reference remains pending; this pilot uses the locally available canonical artifact whose SHA256 matches the frozen governance specification.
