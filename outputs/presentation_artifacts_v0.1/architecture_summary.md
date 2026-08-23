# Governed Evidence Architecture Summary v0.1

## Communication scope

This document describes frozen structural representations. It adds no evidence and makes no target-level biological or therapeutic claim. All identities below are immutable governed identifiers; gene symbols are not used.

## Evidence components

The 29,606-entity universe contains exactly two distinct component slots per entity:

| Component | Version | Recorded structural states |
|---|---|---|
| `COMP_TRANSCRIPTOMIC_EVIDENCE` | `COMP_TRANSCRIPTOMIC_EVIDENCE_V0.1` | `OBSERVED=26171`; `CONFLICTING=3435` |
| `COMP_DISEASE_ASSOCIATION` | `COMP_DISEASE_ASSOCIATION_V0.1` | `OBSERVED=8393`; `PARTIAL=713`; `MISSING=20500` |

Component states are structural conditions. They are preserved separately and are not combined into a global state.

## Representation layers

1. **Multi-component evidence landscape** — `LNDREL_3D3A189C362A4D29E5CA04A47656DA6C` composes component, feature, provenance, dependency, missingness, and limitation references for 29,606 immutable EnsemblID entities.
2. **Evidence Summary** — `SUMREL_43EA4FD9EE02963DA2E94BD1A9FFFC53` projects each landscape into one governed structural summary while retaining component states, missingness, dependency relationships, and limitations.
3. **Transparent routing representation** — `PRZREL_940BC24427791A7E054B54F533E77B48` applies the frozen non-ordinal rule catalog to each of 29,606 summaries and preserves a complete rule trace.
4. **Representative case dossiers** — `CASEREL_678B829DF020D9D6D041B1437855B322` contains 4 filled structural presentation slots selected from complete eligible pools by category-salted SHA256 minimum tokens.

## Interpretation boundary

The architecture organizes evidence records and structural states for traceable communication. Layer counts, states, categories, and selected cases are not comparative measurements and do not establish target importance, efficacy, safety, clinical value, or therapeutic suitability.
