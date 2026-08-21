# Tractability and Target-Safety Plan v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Task:** #011 — tractability and target-safety evidence layer  
**Version:** v0.1  
**Date:** 21 August 2026  
**Status:** Implemented retrieval plan

## Purpose and boundaries

Task #011 retrieves two target-level Open Targets evidence domains: source-native tractability assessments and curated/source-derived safety-liability records. It is an evidence retrieval and normalization task only.

A positive tractability assessment is evidence relevant to a modality, not proof that a target should be pursued. The number of positive assessment buckets is not a project score. Presence of a safety-liability record is not automatically a reason to reject a target, and **absence of a curated safety-liability record is absence of retrieved evidence, not evidence of safety**.

This task does not rank, score, prioritize, recommend, infer therapeutic direction, or decide whether any target is good, bad, safe, unsafe, actionable, or therapeutically appropriate.

## Frozen inputs and identity

The primary input is the committed Task #010 registry:

`outputs/evidence_layer/evidence_registry.csv`

The builder also cross-validates the committed Task #009 identifier map and Task #008 candidate registry:

- `outputs/identifier_normalization/identifier_mapping.csv`
- `outputs/candidate_registry/candidate_registry.csv`

All three files are frozen at Task #010 base commit `072f1e88b08a32077cc44596ad3a6c0235f7d7c5` with pinned SHA256 hashes. The builder requires 29,606 identical, uniquely versioned `EnsemblID` values in the same order and exactly 14,064 U2 genes.

Versioned `EnsemblID` remains the immutable output key. Open Targets queries use only Task #009 `OpenTargets_target_ID` values, which are cross-checked against `EnsemblID_base`. Symbols are copied as metadata and never used as query or join keys. Missing mappings are not rescued manually.

## Official source and release validation

The sole network source is the official Open Targets Platform GraphQL API:

`https://api.platform.opentargets.org/api/v4/graphql`

Before evidence retrieval, the builder queries official metadata and performs focused GraphQL introspection. The implemented snapshot reports Open Targets Platform data release 26.06 and API version 26.6.3.

The builder requires these deployed fields and observed types:

- `Target.id: String!`
- `Target.tractability: [Tractability!]!`
- `Tractability.label: String!`
- `Tractability.modality: String!`
- `Tractability.value: Boolean!`
- `Target.safetyLiabilities: [SafetyLiability!]!`
- `SafetyLiability.url: String`
- `SafetyLiability.literature: String`
- `SafetyLiability.effects: [SafetyEffects!]`
- `SafetyLiability.biosamples: [SafetyBiosample!]`
- `SafetyLiability.event: String`
- `SafetyLiability.eventId: String`
- `SafetyLiability.studies: [SafetyStudy!]`
- `SafetyLiability.datasource: String!`
- `SafetyEffects.direction: String!`, `dosing: String`
- `SafetyBiosample.cellFormat`, `cellLabel`, `cellId`, `tissueLabel`, and `tissueId: String`
- `SafetyStudy.description`, `type`, and `name: String`

If any required field or type is unavailable or changed, the builder stops rather than guessing an alternative or mixing releases. The focused, machine-readable snapshot is saved in `open_targets_schema_snapshot.json`.

## Tractability records

Every source tractability assessment is retained as a separate row with its exact source-native modality, label/assessment identifier, and Boolean value. No assessment is collapsed into a project-defined tractable/not-tractable conclusion.

The gene-level registry includes descriptive counts only: total records, total `TRUE` assessments, `TRUE` counts for the source-native modality codes `SM`, `AB`, `PR`, and `OC`, and deterministic JSON listing positive assessment labels by modality. These counts are retrieval summaries, not scores.

For genes with no source assessment, the long table includes one explicit placeholder row. `TARGET_NOT_MAPPED` denotes no Task #009 target mapping; `TARGET_PRESENT_NO_TRACTABILITY_RECORD_RETURNED` denotes an empty assessment array for a returned mapped target. Placeholder rows are not counted as source assessments.

## Safety-liability records and missingness

Every source safety-liability record is retained separately. Scalar event, event identifier, datasource, literature, and URL fields are preserved. Nested effects, biosamples, and studies are serialized as deterministic JSON, and a deterministic JSON copy of the complete queried source record provides a lossless audit representation of returned nulls, arrays, and values.

The mandatory gene-level safety states are:

| State | Meaning |
|---|---|
| `TARGET_NOT_MAPPED` | Task #009 supplied no Open Targets target ID |
| `TARGET_PRESENT_NO_SAFETY_RECORD_RETURNED` | The mapped target was returned and its safety-liability array was empty |
| `SAFETY_RECORD_PRESENT` | At least one safety-liability record was returned |
| `API_FIELD_NOT_AVAILABLE_OR_RETRIEVAL_FAILURE` | The required API field or mapped target retrieval was unavailable/failed |

The second state must never be relabeled `SAFE` or interpreted as low risk. The long table includes an explicit placeholder row for every gene without a returned record; placeholders are not counted as liabilities.

## Evidence-overlap boundary

Task #010 already contains source-native LUAD association, literature-count, and drug/candidate-count evidence. Task #011 does not retrieve those fields again.

Open Targets tractability may incorporate sources such as ChEMBL and clinical precedence. Its assessments therefore must not be assumed independent of Task #010 drug/candidate counts or future ChEMBL clinical-development evidence. This layer preserves source-native assessments without creating another purportedly independent project evidence dimension.

## Outputs and audit trail

- `tractability_safety_registry.csv`: one row per immutable Ensembl gene with explicit retrieval states and descriptive counts.
- `tractability_assessments.csv`: one row per assessment plus explicit missing placeholders.
- `safety_liabilities.csv`: one row per liability plus explicit missing placeholders.
- `tractability_safety_qc.csv`: assertions and all/U2 coverage, modality/value counts, safety statuses, and datasource counts.
- `tractability_safety_summary.md`: descriptive results and interpretation boundaries.
- `open_targets_schema_snapshot.json`: exact GraphQL fields/types used and query hashes.
- `session_info.txt`: release, timestamps, input/output hashes, request/response counts, byte counts, response hashes, environment, Git identity, and network provenance.

Only Python standard-library modules are used. No package is installed or updated, and no raw API response dump is saved.

## Validation requirements

The build fails unless:

- the registry contains exactly 29,606 unique `EnsemblID` rows in frozen input order;
- exactly 14,064 genes retain U2 membership;
- all queried target IDs come exactly from Task #009 mapping and no Symbol is used as a query key;
- frozen input hashes remain unchanged;
- required live GraphQL fields and types validate before evidence retrieval;
- every gene is represented in both long tables, including explicit missing placeholders;
- returned tractability values conform to the introspected Boolean type;
- nested safety fields conform to their introspected types and are preserved in deterministic JSON;
- no ranking, project-defined score, recommendation, or therapeutic-direction field is emitted;
- no committed Task #001–#010 file is modified.

## Explicit non-claims

Task #011 does not establish target quality, causality, actionability, safety, risk, clinical suitability, therapeutic direction, or superiority. Its outputs are source-grounded evidence records for later, separately specified assessment and validation.
