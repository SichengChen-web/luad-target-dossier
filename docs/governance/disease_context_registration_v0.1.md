# Disease Context Registration v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Registration version:** v0.1  
**Component:** `COMP_DISEASE_ASSOCIATION`  
**Context status:** `FROZEN_FOR_SCOPED_SNAPSHOT_RETRIEVAL`  
**Decision date:** 22 August 2026

## 1. Purpose

This record freezes the lung-adenocarcinoma disease identity, ontology boundary, mapping rule, inclusion model, explicit exclusions, and context artifact identity for the future Open Targets Platform 26.06 snapshot.

It does not retrieve a disease record, access an ontology endpoint, perform free-text matching, or map evidence at runtime.

## 2. Frozen disease-context identity

| Field | Frozen value |
|---|---|
| `disease_context_id` | `MONDO_0005061` |
| `disease_context_label` | `lung adenocarcinoma` |
| `ontology` | Mondo Disease Ontology as embedded by Open Targets Platform |
| `ontology_version` | `OPEN_TARGETS_PLATFORM_26.06_DISEASE_ONTOLOGY_SNAPSHOT` |
| `mapping_rule_version` | `DA_LUAD_CONTEXT_MAPPING_V0.1` |
| `inclusion_model` | `EXACT_ONLY` |
| `inclusion_boundary_version` | `DA_LUAD_EXACT_INCLUSION_V0.1` |
| `exclusion_boundary_version` | `DA_LUAD_NONEXACT_EXCLUSION_V0.1` |
| `context_artifact_id` | `CTX_LUAD_MONDO_0005061_EXACT_V0_1` |
| `context_contract_sha256` | `edbd20f04671d61a3338c596d07712361d64bed3c9706c213485b22af1ef15d2` |
| Source release binding | Open Targets Platform `26.06` |
| Mapping execution | Deterministic exact-ID comparison only |

The ontology version is deliberately source-bound: it identifies the disease ontology graph actually embedded in the selected Open Targets Platform 26.06 release. It does not assert an unverified standalone Mondo release number.

## 3. Governance basis

Existing project-local official-source metadata records:

- `MONDO_0005061`;
- label `lung adenocarcinoma`;
- Open Targets data release `26.06`;
- Open Targets API metadata version `26.6.3`.

The evidence is recorded in `outputs/evidence_layer/session_info.txt`, SHA256 `2e1331f88685c5686e7e1f9dbf13e5f741ae46a8c460d1da8af596ef85c08d5c`, and the historical plan `docs/evidence_layer_plan_v0.1.md`, SHA256 `6e72e4932f02d939498269387ff2e3904ff3ad409440a29f7f3bf7f87d99359c`.

These artifacts support context selection but are not the future disease-context snapshot. Future retrieval must validate the exact ID and label in the official 26.06 `disease` dataset and preserve that source record and file hash.

## 4. Inclusion model

The frozen inclusion model is `EXACT_ONLY`.

An evidence record is eligible for the disease-association snapshot only when:

`source diseaseId == MONDO_0005061`

Additional requirements:

- the source disease identifier is taken from the Open Targets 26.06 raw record;
- the selected release `disease` dataset contains `MONDO_0005061`;
- the source label resolves to `lung adenocarcinoma`, or a label discrepancy is reported as a structural conflict;
- the record satisfies the selected source and query-scope contracts;
- no hierarchy expansion, synonym matching, text similarity, or manual interpretation contributes to inclusion.

Exact membership is a query-scope fact. It does not establish that the record is biologically correct or causal.

## 5. Inclusion boundary

Included:

- exact source disease identifier `MONDO_0005061` only.

Not additionally included:

- descendants of `MONDO_0005061`;
- ancestors of `MONDO_0005061`;
- mapped synonyms without the exact identifier;
- cross-ontology equivalents not materialized as exact `MONDO_0005061` in the source record;
- records returned only through Open Targets indirect/ontology-expanded association views.

Any future decision to include descendants, ancestors, or an allowlist requires a new disease-context version, mapping-rule version, query-scope version, and source snapshot.

## 6. Exclusion boundary

The following are excluded from this exact-only context unless their source record disease ID is exactly `MONDO_0005061`:

- broader lung cancer concepts;
- non-small-cell lung cancer concepts;
- other lung cancer histologies;
- lung cancer not otherwise specified;
- metastatic disease concepts;
- mixed lung cancer cohorts;
- pan-cancer concepts;
- precancerous or non-malignant lung conditions;
- descendants or subtypes represented by a non-exact disease ID;
- obsolete, replaced, ambiguous, or unresolved disease IDs;
- free-text labels and synonyms without exact source identity.

Exclusion is from this component query scope only. It is not negative evidence and does not make a biological claim about those disease concepts.

## 7. Mapping rule

Mapping rule `DA_LUAD_CONTEXT_MAPPING_V0.1` is:

1. Read the source `diseaseId` exactly as serialized in the frozen raw record.
2. If it equals `MONDO_0005061`, assign source mapping outcome `EXACT_CONTEXT_MATCH`.
3. If it is any other stable identifier, assign `EXCLUDED_BY_VERSIONED_RULE` for this context.
4. If the field is absent, malformed, ambiguous, or unresolvable, preserve the appropriate `UNRESOLVED_MAPPING` or `UNKNOWN_MAPPING_STATUS` condition.
5. If the selected release disease entity record for `MONDO_0005061` is absent or label identity conflicts, stop snapshot validation.

No source identifier is converted to `MONDO_0005061` through label matching, synonym search, ontology traversal, manual judgement, or LLM runtime mapping.

## 8. Normalized mapping-status translation

| Source mapping outcome | Task #032B-1 structural status |
|---|---|
| Exact raw `diseaseId = MONDO_0005061` | `NOT_REQUIRED` for an additional mapping operation, with exact-identity provenance |
| `EXCLUDED_BY_VERSIONED_RULE` | Record is outside normalized component scope; raw exclusion ledger retains provenance |
| `AMBIGUOUS_MAPPING` | `CONFLICTING` or `UNRESOLVED` only under a future executable reviewed rule; no runtime choice |
| `OBSOLETE_OR_REPLACED` | `UNRESOLVED` unless a future versioned replacement artifact resolves it |
| `UNRESOLVED_MAPPING` | `UNRESOLVED` |
| `UNKNOWN_MAPPING_STATUS` | `UNKNOWN` |

The future executable feature and state rules must freeze the ambiguous-mapping branch before materialization.

## 9. Context artifact identity

Canonical disease-context payload:

```json
{"disease_context_id":"MONDO_0005061","disease_context_label":"lung adenocarcinoma","exclusion_rule":"all source disease identifiers other than MONDO_0005061","inclusion_model":"EXACT_ONLY","inclusion_rule":"source_disease_id == MONDO_0005061","mapping_rule_version":"DA_LUAD_CONTEXT_MAPPING_V0.1","ontology":"Mondo Disease Ontology as embedded by Open Targets Platform","ontology_version":"OPEN_TARGETS_PLATFORM_26.06_DISEASE_ONTOLOGY_SNAPSHOT"}
```

Canonical payload SHA256:

`edbd20f04671d61a3338c596d07712361d64bed3c9706c213485b22af1ef15d2`

This contract hash identifies the context semantics. The future source snapshot must additionally retain the exact 26.06 disease dataset artifact IDs, sizes, and SHA256 values.

## 10. Ontology and license provenance

The context uses the Mondo identifier embedded in Open Targets Platform 26.06. The official Open Targets license page reviewed on 22 August 2026 lists:

- Platform data: `CC0-1.0`;
- MONDO: `CC-BY-4.0`.

The future retrieval must capture exact license documentation and release metadata. If the 26.06 release provides a standalone upstream Mondo release identifier, it must be recorded as additional provenance without changing the source-bound `ontology_version` in this v0.1 context.

## 11. No free-text or runtime mapping

Prohibited:

- matching the phrase “lung adenocarcinoma” without exact source ID;
- accepting a synonym or broader label at runtime;
- calling a live ontology service during extraction or materialization;
- resolving disease identity with an LLM;
- adding descendants because they appear biologically related;
- changing context membership based on association results.

## 12. Interpretation boundary

The frozen context defines record eligibility. It does not determine:

- disease-driver status or causality;
- target importance;
- evidence strength or confidence;
- therapeutic relevance or target suitability;
- target score, rank, priority, selection, or recommendation.

## 13. Context-change policy

A new context version is required for any change to:

- disease ID or label identity rule;
- ontology or source release binding;
- ontology version;
- exact-only inclusion model;
- inclusion or exclusion membership;
- mapping outcome or normalized-status translation;
- context canonical payload.

Any such change also requires a new query-scope version and source snapshot.

## 14. Context validation checklist

- [x] Exact disease ID and label are frozen.
- [x] Ontology and source-bound ontology version are frozen.
- [x] Mapping-rule version is frozen.
- [x] Inclusion model is `EXACT_ONLY`.
- [x] Inclusion and exclusion boundaries are explicit.
- [x] Canonical context payload and SHA256 are recorded.
- [x] Free-text and runtime LLM mapping are prohibited.
- [ ] Exact 26.06 disease dataset record, artifact size, and SHA256 are captured during retrieval.
- [ ] Ambiguous-mapping executable rule branch is frozen before materialization.

## 15. Related governance

- [Disease Association Source Selection Record v0.1](disease_association_source_selection_record_v0.1.md)
- [Disease Association Materialization Authorization v0.1](disease_association_materialization_authorization_v0.1.md)
- [Disease Context Definition Policy v0.1](disease_context_definition_policy_v0.1.md)

