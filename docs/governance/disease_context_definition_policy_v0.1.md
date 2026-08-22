# Disease Context Definition Policy v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Version:** v0.1  
**Component:** `COMP_DISEASE_ASSOCIATION`  
**Status:** Frozen governance policy; disease context not yet assigned

## 1. Purpose

This policy defines how a future lung-adenocarcinoma disease context must be identified, versioned, bounded, mapped, and validated before disease-association retrieval can be authorized.

It deliberately does not guess an ontology identifier, access an ontology service, retrieve evidence, or decide that a broader or narrower disease record belongs to the project context.

## 2. Disease-context identity contract

Every registered disease context must define:

| Required field | Meaning |
|---|---|
| `disease_context_id` | Stable ontology identifier used as the primary disease-context identity |
| `disease_context_label` | Human-readable label from the frozen ontology release |
| `ontology` | Stable ontology or controlled disease-vocabulary identity |
| `ontology_version` | Exact ontology release/version used for context and hierarchy |
| `mapping_rule_version` | Version of the deterministic source-disease-to-context mapping rules |
| `inclusion_boundary_version` | Version of exact, hierarchy, or allowlist inclusion rules |
| `exclusion_boundary_version` | Version of explicit exclusions and reasons |
| `disease_context_artifact_id` | Frozen machine-readable context artifact |
| `disease_context_artifact_sha256` | Hash of that artifact |
| `review_status` | Technical and scientific governance status |

All fields must be frozen before retrieval. A label without an ontology ID and version is not a governed context.

## 3. Current unassigned context

The scientific project context is lung adenocarcinoma, but the following remain unassigned:

- `disease_context_id`;
- `ontology`;
- `ontology_version`;
- `mapping_rule_version`;
- inclusion and exclusion boundary versions.

No default ontology, current release, synonym, or hierarchy is inferred in this task. Retrieval remains blocked until a future review freezes these values.

## 4. Inclusion-boundary models

A future disease-context registration must choose and version exactly one primary inclusion model:

### 4.1 `EXACT_ONLY`

Include only records whose source disease identity maps exactly to the frozen `disease_context_id` under the reviewed mapping artifact.

### 4.2 `EXACT_PLUS_EXPLICIT_DESCENDANTS`

Include the exact context plus a frozen, enumerated descendant set derived from the specified ontology version and hierarchy rule. The descendant artifact and its hash are mandatory.

### 4.3 `EXPLICIT_ALLOWLIST`

Include only an explicitly reviewed list of source disease identifiers. Every member must carry an inclusion rationale and provenance.

### 4.4 Multiple representations

If more than one inclusion model is scientifically required, each must have a separate context or query-scope identity. Records from distinct scopes must not be silently merged.

No inclusion model is selected by this policy.

## 5. Required inclusion boundary

The frozen context artifact must enumerate:

- exact included disease identifiers;
- ontology namespace and version for each identifier;
- whether inclusion is exact or rule-derived;
- source of the hierarchy or mapping relationship;
- mapping rule ID and version;
- inclusion rationale code;
- effective context/query-scope version;
- artifact and record provenance.

Inclusion is a query-membership decision only. It does not state disease causality or target relevance.

## 6. Required exclusion boundary

The context definition must explicitly classify or leave unresolved:

- broader lung cancer concepts;
- non-small-cell lung cancer concepts;
- other lung histologies;
- metastatic disease concepts;
- mixed or unspecified lung cancer cohorts;
- pan-cancer records;
- precancerous or non-malignant lung conditions;
- obsolete, deprecated, merged, or replaced disease identifiers;
- ambiguous text labels without stable disease identity.

Each explicit exclusion must have:

- source disease identifier;
- ontology and version;
- exclusion rationale code;
- mapping-rule version;
- provenance artifact.

This policy does not decide the classification of any particular term. It requires those decisions to be explicit and versioned.

## 7. Source disease mapping contract

Every source disease identifier must resolve to one structural mapping outcome:

| Mapping outcome | Meaning |
|---|---|
| `EXACT_CONTEXT_MATCH` | Source identifier exactly equals the frozen context identity |
| `INCLUDED_BY_VERSIONED_RULE` | Source identifier enters through the frozen hierarchy or allowlist rule |
| `EXCLUDED_BY_VERSIONED_RULE` | Source identifier is explicitly outside the frozen context |
| `AMBIGUOUS_MAPPING` | More than one incompatible context resolution remains |
| `OBSOLETE_OR_REPLACED` | Source or ontology marks the identifier obsolete, merged, or replaced |
| `UNRESOLVED_MAPPING` | No deterministic mapping can be established |
| `UNKNOWN_MAPPING_STATUS` | Mapping provenance or ontology coverage is incomplete |

The normalized Task #032B-1 mapping feature must deterministically translate these source mapping outcomes to its controlled structural statuses:

- resolved exact or rule-based membership → `RESOLVED`;
- exact source identity requiring no mapping operation → documented `NOT_REQUIRED` where the feature contract permits;
- ambiguous incompatible mappings → `CONFLICTING` or `UNRESOLVED` according to a frozen rule;
- unresolved or obsolete mappings → `UNRESOLVED` unless a reviewed replacement rule resolves them;
- incomplete mapping provenance → `UNKNOWN`.

The translation rule must be frozen before implementation. No manual or AI/LLM runtime mapping is permitted.

## 8. Ontology snapshot requirements

The disease context must reference an immutable ontology snapshot or a governed external artifact with:

- ontology identity and version;
- official release information;
- retrieval or acquisition metadata;
- term and hierarchy artifact IDs;
- artifact formats, sizes, and SHA256 values;
- license information;
- deprecated/replaced-term metadata;
- source documentation artifact and checksum.

A live ontology endpoint must not be queried during normalization or materialization.

## 9. Mapping artifact requirements

The frozen mapping artifact must preserve, for every mapping assertion:

- source disease identifier and namespace;
- source vocabulary version;
- target disease-context identifier;
- mapping outcome;
- mapping method and rule ID;
- evidence/provenance record ID;
- source and artifact IDs;
- ontology version;
- ambiguity and replacement status;
- reviewer status where a human scientific decision was required.

Human-reviewed mapping decisions must be made before runtime and serialized as frozen artifacts. Runtime AI decisions are prohibited.

## 10. Synonym and text-label policy

Synonyms and text labels may assist review but cannot independently establish context membership. A mapping based on a synonym requires a frozen ontology or mapping assertion connecting the source identifier to the context.

Free-text similarity, gene/disease name matching, or LLM interpretation must not assign a disease context at runtime.

## 11. Version-change policy

A new disease-context or mapping-rule version is required when any of the following changes:

- `disease_context_id` or ontology;
- ontology version;
- hierarchy traversal semantics;
- allowlist or descendant membership;
- explicit exclusion membership;
- obsolete/replacement handling;
- synonym or cross-ontology mapping behavior;
- mapping status translation;
- any context or mapping artifact byte.

Such a change also requires a new query-scope version, source snapshot version, and containing profile evidence-snapshot version when it affects retrieved or included records.

## 12. Missingness and conflict boundaries

- An unattempted mapping is `NOT_QUERIED`, not unresolved biology.
- A completed mapping search with no mapping may be `NOT_FOUND` at feature level and `UNRESOLVED_MAPPING` structurally.
- An inapplicable mapping operation may be `NOT_APPLICABLE` only under a deterministic exact-identity rule.
- Incomplete ontology or mapping coverage remains `UNKNOWN`.
- Multiple incompatible source-to-context mappings may support structural `CONFLICTING` state.

None of these states determines whether a target has biological involvement in disease.

## 13. Interpretation boundary

Disease-context mapping establishes query membership and provenance only. It does not establish:

- that a source association record is correct;
- disease-driver status or causality;
- target importance;
- therapeutic relevance or suitability;
- evidence strength or confidence;
- ranking, scoring, prioritization, or recommendation.

Runtime API dependence, mutable ontology lookups, biological interpretation, target prioritization, scoring, and ranking are prohibited. A future runtime must consume frozen context and mapping artifacts rather than a live ontology or an AI/LLM decision.

## 14. Disease-context checklist

- [ ] `disease_context_id` and label are frozen.
- [ ] Ontology identity and exact version are frozen.
- [ ] Inclusion model and enumerated membership are frozen.
- [ ] Exclusion boundary and rationale codes are frozen.
- [ ] Mapping rules and status translation are versioned.
- [ ] Ontology and mapping artifacts have sizes, SHA256 values, and license records.
- [ ] Ambiguous, obsolete, unresolved, and unknown mappings remain explicit.
- [ ] No live ontology or runtime AI decision is required.
- [ ] Context membership is not interpreted biologically or therapeutically.
- [ ] A separate human governance action authorizes use in retrieval.

## 15. Related policies

- [Disease Association Source Contract v0.1](disease_association_source_contract_v0.1.md)
- [Disease Association Snapshot Policy v0.1](disease_association_snapshot_policy_v0.1.md)
- [Disease Association Query Scope Policy v0.1](disease_association_query_scope_policy_v0.1.md)
- [Disease Association Component Scope v0.1](disease_association_component_scope_v0.1.md)
