# Case Study Communication Specification v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Task:** #038A  
**Version:** `CASE_STUDY_COMMUNICATION_V0.1`  
**Status:** Structural scientific communication layer

## 1. Purpose

This specification governs the deterministic transformation of the four frozen Task #036B representative case dossiers into human-readable tables and figures for presentations, posters, and project documentation. The communication artifacts expose evidence structure; they do not add evidence or interpret target biology.

The selected EnsemblID identities remain deterministic structural representatives. They are not preferred, optimal, validated, or recommended targets.

## 2. Frozen source relationship

```text
Task #036A case-pattern governance
                ↓
Task #036B deterministic representative dossier
                ↓
Task #036C structural communication context
                ↓
Task #038A case-study communication view
```

Task #038A may copy or structurally label only fields already present in the frozen dossiers. It must not rebuild selection, access earlier payloads to enrich a case, retrieve evidence, add gene symbols, or introduce biological narratives.

## 3. Communication cases

Exactly four governed slots are communicated in frozen Task #036A order:

1. `CASE_COMPLETE_PATTERN`;
2. `CASE_PARTIAL_PATTERN`;
3. `CASE_CONFLICT_PATTERN`;
4. `CASE_LIMITATION_PATTERN`.

Every artifact must communicate these interpretation boundaries verbatim:

- **Complete evidence ≠ best target**
- **Partial evidence ≠ negative evidence**
- **Conflict ≠ failure**
- **Limitation ≠ rejection**

The cases remain non-ordinal. Their category-salted SHA256 tokens are deterministic sampling devices and must not be used for cross-case ordering.

## 4. Required communication fields

Each case row and figure preserves:

- immutable `EnsemblID` and canonical universe ordinal;
- case category, case-selection ID, case rule, structural reason code, and deterministic selection method;
- component IDs, versions, states, and source component-record IDs;
- a bounded feature-availability label derived only from each frozen component state;
- source Evidence Summary and prioritization representation identities;
- all summary-level and component-level limitation identifiers.

## 5. Feature-availability boundary

Task #036B dossiers expose component states but do not expose record-level feature inventories. Therefore v0.1 uses this fixed structural communication map only:

| Frozen component state | Communication label |
|---|---|
| `OBSERVED` | `OBSERVATION_STRUCTURE_AVAILABLE` |
| `PARTIAL` | `PARTIAL_OBSERVATION_STRUCTURE_AVAILABLE` |
| `CONFLICTING` | `CONFLICTING_OBSERVATION_STRUCTURE_AVAILABLE` |
| `MISSING` | `SOURCE_COMPONENT_STATE_MISSING` |
| `NOT_QUERIED` | `SOURCE_COMPONENT_STATE_NOT_QUERIED` |

These labels do not reconstruct features, measure evidence quantity, or convert missingness into negative evidence.

## 6. Provenance and dependency communication

The communication lineage is:

```text
source component-record references
                ↓
source Evidence Summary identity
                ↓
source prioritization representation identity
                ↓
frozen case-selection identity
```

Task #036B dossiers do not expose dependency-edge inventories. Figures must state `SOURCE_EVIDENCE_SUMMARY_REFERENCE_ONLY` and point to the frozen Evidence Summary identity. No dependency edge may be invented, flattened, counted as an independent vote, or inferred from component state.

## 7. Figure contract

Each communication-ready SVG must:

- display one exact EnsemblID structural representative;
- show both component identities, versions, states, and feature-availability labels;
- show provenance references and preserved limitations;
- disclose the dependency-detail boundary;
- use controlled state labels without desirability ordering;
- include an accessible SVG title and description;
- contain no external font, script, network resource, or mutable reference.

The four deterministic figures are:

- [Complete evidence pattern](../figures/complete_evidence_pattern.svg)
- [Partial evidence pattern](../figures/partial_evidence_pattern.svg)
- [Conflict evidence pattern](../figures/conflict_evidence_pattern.svg)
- [Limitation evidence pattern](../figures/limitation_evidence_pattern.svg)

## 8. Prohibitions

The communication layer must not retrieve evidence, access APIs, regenerate upstream artifacts, add gene symbols, create biological narratives, recommend targets, or introduce target scores, ranks, priorities, confidence estimates, evidence-strength measures, or runtime AI/LLM decisions.

Visual emphasis and color distinguish pattern types only; they must not encode quality, desirability, or priority.

## 9. Validation

Generation must validate:

- exact Task #036A/#036B/#036C/#037D frozen hashes;
- reconciliation of dossier, index, and presentation identities;
- exact component-state, provenance-reference, and limitation fidelity;
- the fixed feature-availability mapping;
- explicit dependency-detail boundaries;
- well-formed, self-contained SVG output;
- recursive prohibited-field absence from structured outputs;
- resolution of local Markdown links;
- two byte-identical complete generations;
- no network access or runtime AI decisions.

Structural and computational validation does not constitute biological validation.

## 10. Related artifacts

- [Case Study Selection Framework v0.1](governance/case_study_selection_framework_v0.1.md)
- [Case Study Selection Rule Catalog v0.1](governance/case_study_selection_rule_catalog_v0.1.md)
- [Task #036B case dossiers](../outputs/case_dossiers_v0.1/case_dossiers.json)
- [Task #036C presentation artifacts](../outputs/presentation_artifacts_v0.1/presentation_manifest.json)
- [Project Overview v1.0](project_overview_v1.0.md)
