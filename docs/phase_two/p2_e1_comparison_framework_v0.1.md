# P2-E1 Comparison Framework and Codebook v0.1

**Project:** LUAD Target Evidence Dossier  
**Workstream:** P2-E1 — Related Work and Gap Analysis  
**Version:** v0.1  
**Date:** 3 September 2026  
**Status:** Prospective codebook; no system has been assessed

## 1. Purpose

This codebook makes the P2-E1 capability comparison reproducible. It defines what is compared, where a capability must be observed, which evidence can support a determination, and how uncertainty is encoded.

The matrix is a set of categorical, evidence-linked observations. It is not a scorecard, maturity model, ranking, endorsement, or measure of biomedical utility.

## 2. Matrix identity and grain

One row represents:

```text
(system_assessment_id, dimension_id, assessed_surface)
```

`system_assessment_id` binds system name, product scope, version or access-date snapshot, and assessment date. Separate versions or materially different products receive separate IDs.

No row may merge multiple dimensions or surfaces. A user-interface capability cannot be inferred from a backend schema, and a conceptual method cannot be inferred to be implemented in released data.

## 3. Assessed surfaces

| Surface | Definition |
|---|---|
| `CONCEPTUAL_MODEL` | Capability asserted or permitted by a formal method, ontology, or conceptual specification |
| `INGESTED_RECORD` | Capability populated in the system's source or normalized atomic records |
| `INTERNAL_OR_RELEASED_MODEL` | Capability present in an inspectable schema, graph, database export, or released data model |
| `API_OR_EXPORT` | Capability exposed in a documented or captured machine-readable interface |
| `USER_INTERFACE` | Capability visible and interpretable in a captured user-facing interface |
| `TARGET_LEVEL_SYNTHESIS` | Capability retained or linked in the target or target–disease summary used for downstream interpretation |
| `EVALUATION` | Capability or its consequence empirically evaluated rather than merely implemented |

If a surface is inaccessible, use the appropriate uncertainty state; do not infer its state from another surface.

## 4. Controlled capability states

| State | Operational rule | Evidence requirement | Permitted interpretation |
|---|---|---|---|
| `PRESENT_VERIFIED` | The full dimension definition is directly documented or observed for the exact system version and surface | At least one qualifying atomic evidence item; triangulation required for mutable or ambiguous surfaces | Capability is verified within the stated boundary |
| `PARTIAL_VERIFIED` | A strict subset is verified or implementation is present but does not meet all defined subcriteria | Evidence for present and unmet/limited subcriteria | Only the named subset is verified |
| `ABSENT_EXPLICIT` | Primary, version-bounded material explicitly states that the capability is unsupported, excluded, unavailable, or outside design | Direct primary evidence plus exact scope | Explicit absence only within the stated version and surface |
| `NOT_FOUND_IN_REVIEWED_MATERIALS` | Prespecified eligible materials were reviewed and no qualifying evidence was located | Search-scope record, materials reviewed, and reviewer attestation | Documentation/observation not found; capability absence is not established |
| `UNCLEAR` | Relevant evidence is ambiguous, internally inconsistent, or insufficient for a stable determination | Conflicting/ambiguous evidence links and explanation | Capability cannot be resolved |
| `NOT_APPLICABLE` | The dimension does not logically apply to the system's declared purpose or surface | Scope-based rationale reviewed by two reviewers | No comparison is made for this cell |
| `NOT_ASSESSED` | Assessment has not been completed | Reason and planned disposition | No inference is permitted |

`ABSENT_EXPLICIT` must never be assigned solely from unsuccessful searching, UI non-observation, an empty result, or undocumented behavior.

### 4.1 Operational meaning of “first-class”

For P2-E1, a concept is a **first-class structured capability** only when it has a stable, addressable field, entity, relation, or controlled state with defined semantics and an evidence link showing that it is populated or enforced on the assessed surface. It must be independently queryable, exportable, or traversable, rather than recoverable only by interpreting prose.

The following do not by themselves establish a first-class capability:

- a general disclaimer;
- a methods-paper discussion with no implementation link;
- the theoretical expressivity of a graph or ontology;
- a free-text note without controlled semantics;
- a citation list disconnected from evidence items; or
- information available upstream but dropped from the assessed downstream surface.

A documented but non-structured treatment may qualify as `PARTIAL_VERIFIED` when it satisfies a named subset of a dimension. The final synthesis must state whether it is comparing first-class representation, human-readable documentation, or both.

## 5. Evidence types and precedence

| Evidence type | Best use | Limitation |
|---|---|---|
| Versioned schema, ontology, or released data | Verify implemented fields and relations | Expressivity does not prove population, exposure, or user interpretation |
| Official API/export documentation plus captured response | Verify exposed machine-readable capability | Mutable endpoint requires access-date and capture boundary |
| Official technical documentation or release notes | Verify intended current behavior and changes | May omit edge cases or implementation detail |
| Source code or ETL at an immutable commit | Verify implemented logic | Deployed behavior may differ; repository scope must be established |
| Primary system/method paper | Verify reported design and historical behavior | Does not automatically describe the current version |
| Independent empirical evaluation | Verify observed performance or consequences | Version and task may differ from current scope |
| Captured user-interface observation | Verify visible capability at access date | Non-observation cannot establish absence |
| Review article | Discover systems and synthesize context | Insufficient alone for exact current capability |
| Commercial or marketing material | Candidate discovery only | Cannot alone verify technical capability or performance |

When sources disagree, do not apply a hidden precedence rule. Record both, check version and surface differences, and use `UNCLEAR` unless the conflict can be resolved transparently.

## 6. Capability dimensions

### Identity and scope

#### `DIM_00_PURPOSE_AND_DECISION_ROLE`

**Question:** Is the system's intended purpose and the role of its outputs in research, prioritization, prediction, evidence organization, or decision support explicit?

Presence requires a bounded first-party purpose statement and interpretable output semantics. It does not imply that the stated purpose is achieved. This dimension is used to prevent unlike systems from being compared as though they solve the same task.

#### `DIM_01_ENTITY_IDENTITY`

**Question:** Are target, disease, drug, dataset, publication, experiment, and other relevant entities represented with stable identifiers and declared namespaces?

`PRESENT_VERIFIED` requires stable identity for the entities used by the assessed surface, not merely display names. `PARTIAL_VERIFIED` applies when only a subset or ambiguous namespace mapping is exposed.

#### `DIM_02_SCOPE_AND_COVERAGE`

**Question:** Does the system expose what entities, evidence types, sources, dates, or queries were eligible and covered?

Presence requires interpretable denominators or explicit coverage metadata. A large record count alone is not coverage semantics.

### Evidence state and atomicity

#### `DIM_03_EVIDENCE_UNIT`

**Question:** Is the atomic evidence unit defined and distinguishable from an aggregate, assertion, source row, or display item?

Presence requires a documented or inspectable unit and its relationship to aggregates.

#### `DIM_04_EVIDENCE_STATE`

**Question:** Are evidence observations represented by explicit, defined states rather than inferred solely from values or counts?

Record the vocabulary and whether it is categorical, probabilistic, numeric, or free text. Do not equate a score with an evidence-state model.

#### `DIM_05_NEGATIVE_NULL_CONTEXT`

**Question:** Can negative, null, non-supportive, or context-dependent findings be preserved without being collapsed into absence?

Presence requires explicit semantics and a retained linkage to the finding context.

### Provenance and traceability

#### `DIM_06_SOURCE_ATTRIBUTION`

**Question:** Can a represented item be attributed to its immediate source?

A source label or citation can satisfy this dimension but not the stronger lineage dimensions below.

#### `DIM_07_RECORD_LEVEL_PROVENANCE`

**Question:** Can each evidence item be traced to a stable source record, publication location, dataset observation, or immutable artifact?

Generic source lists or target-level citations are partial unless the record-to-source relation is reconstructable.

#### `DIM_08_DERIVATION_LINEAGE`

**Question:** Are transformations from source item through normalization, aggregation, and target-level output represented or reconstructable?

Presence requires explicit derivation links, transformation metadata, or an equivalent auditable chain—not only final citations.

#### `DIM_09_QUERY_AND_SNAPSHOT_PROVENANCE`

**Question:** Are retrieval scope, query parameters, time, release, snapshot, and completeness/failure metadata preserved?

An access date alone is partial unless the retrieved content and scope can be reconstructed.

#### `DIM_10_TARGET_TO_SOURCE_TRACEABILITY`

**Question:** Can a user traverse from a target-level statement or state back to the underlying evidence items and their sources?

Presence is assessed on the exact downstream surface; upstream availability alone is partial or belongs in another row.

### Dependency and reuse

#### `DIM_11_EXPLICIT_DEPENDENCY_MODEL`

**Question:** Does the system represent relationships such as derived-from, duplicates, shared dataset, shared publication, shared experiment, shared model, or reused assertion as explicit structured objects or relations?

Citation co-occurrence and reviewer-inferred overlap do not satisfy full presence.

#### `DIM_12_INDEPENDENCE_BOUNDARY`

**Question:** Does the representation prevent or flag the interpretation of related records as independent corroboration?

Presence requires an explicit rule, relation, grouping, or evaluated mechanism at the assessed surface. Deduplication of identical IDs alone is partial when non-identical derived records remain.

#### `DIM_13_AGGREGATION_DEPENDENCY_HANDLING`

**Question:** Does aggregation account for, preserve, or expose evidence dependence rather than treating all records as exchangeable independent units?

Record whether the dependency affects calculation, display, grouping, or only documentation.

### Missingness and uncertainty

#### `DIM_14_MISSINGNESS_VOCABULARY`

**Question:** Are biologically absent, no eligible record, not found, not queried, query failed, inaccessible, unknown, and not applicable states distinguished where relevant?

`PRESENT_VERIFIED` requires defined distinctions appropriate to system scope; it does not require irrelevant states.

#### `DIM_15_COVERAGE_VS_NEGATIVE_RESULT`

**Question:** Does the system prevent lack of a returned record from being interpreted automatically as a negative biological finding?

Presence requires an explicit semantic or implemented guard, not only a general disclaimer detached from outputs.

#### `DIM_16_UNCERTAINTY_REPRESENTATION`

**Question:** Is uncertainty represented with defined semantics and linked to its source, estimate, judgment, coverage limitation, or transformation?

Numeric confidence, evidence grade, missingness, and free-text caveats must be described separately.

#### `DIM_17_CONFLICT_PRESERVATION`

**Question:** Can contradictory evidence states, directions, or interpretations coexist and remain traceable through synthesis?

An aggregate that cancels opposing values without surfacing the conflict is not full presence.

### Claims and interpretation

#### `DIM_18_CLAIM_OBJECT`

**Question:** Are bounded claims or assertions represented separately from the records that support, challenge, or contextualize them?

Presence requires an explicit claim/assertion unit and relations to evidence; prose summaries alone are partial at most.

#### `DIM_19_CLAIM_BOUNDARY`

**Question:** Does the system encode or enforce what may and may not be concluded from an evidence type or synthesis state?

Disclaimers, structured scope fields, output constraints, and executable rules must be coded distinctly in the rationale.

#### `DIM_20_PRECLINICAL_CLINICAL_BOUNDARY`

**Question:** Are preclinical observations, clinical investigation, efficacy, safety, and clinical validation kept semantically distinct?

Presence requires the distinction to survive the assessed target-level surface.

#### `DIM_21_ASSOCIATION_CAUSALITY_BOUNDARY`

**Question:** Does the representation distinguish association, mechanistic support, causality, actionability, and recommendation?

A methods-paper disclaimer without corresponding output semantics is partial on output surfaces.

### Aggregation, versioning, and audit

#### `DIM_22_AGGREGATION_TRANSPARENCY`

**Question:** Are target-level combinations, scores, categories, summaries, or transformations defined and reconstructable from inputs?

Open-source status alone does not demonstrate reconstructability for the assessed release.

#### `DIM_23_INFORMATION_RETENTION`

**Question:** Are provenance, dependency, missingness, conflict, uncertainty, and claim context retained or linked after aggregation?

Code this dimension only after the constituent dimensions have been assessed. State exactly which information is retained or lost.

#### `DIM_24_VERSIONING_AND_CHANGE_HISTORY`

**Question:** Are data, schema, method, and platform versions distinguishable, with material changes documented?

Publication year or current webpage date alone is partial.

#### `DIM_25_REPRODUCIBILITY`

**Question:** Can the assessed result be regenerated or reconstructed from identified inputs, versions, parameters, and code or method?

Repeatable access to a mutable current result without frozen inputs is partial.

#### `DIM_26_HUMAN_AUDITABILITY`

**Question:** Can a knowledgeable reviewer inspect the relevant evidence, relations, missingness, transformations, and claim scope with a bounded reconstruction burden?

If empirically evaluated, record the task and result under `EVALUATION`; otherwise presence means inspectability only, not demonstrated usability.

### AI-specific transparency

#### `DIM_27_AI_OUTPUT_GROUNDING`

**Question:** For AI-generated target statements, are individual outputs linked to retrievable supporting records or passages?

This dimension is `NOT_APPLICABLE` only when the assessed system produces no AI-generated interpretation.

#### `DIM_28_AI_SOURCE_AND_MODEL_BOUNDARY`

**Question:** Are retrieval/training sources, model/version, generation date, and distinction between source evidence and generated interpretation recorded at a useful audit level?

General provider names without output-level or run-level boundaries are partial.

## 7. Evidence-ledger relationship types

Each atomic evidence item must use one relationship:

- `SUPPORTS_FULL` — supports all required subcriteria for the bounded cell;
- `SUPPORTS_PARTIAL` — supports a named subset;
- `SUPPORTS_EXPLICIT_ABSENCE` — directly supports `ABSENT_EXPLICIT`;
- `CHALLENGES` — conflicts with a proposed determination;
- `CONTEXT_ONLY` — defines scope or terminology without determining the cell;
- `SUPERSEDED` — historically relevant but replaced by a later version.

The matrix rationale must resolve or retain every `CHALLENGES` item. Evidence items are not votes and must not be counted as independent support without a dependency assessment.

## 8. Dependency among review sources

The source registry records relationships including:

- `SAME_DOCUMENT_VERSION`;
- `UPDATED_VERSION_OF`;
- `PREPRINT_VERSION_OF`;
- `DERIVED_FROM_FIRST_PARTY_DOCS`;
- `SAME_UNDERLYING_EVALUATION`;
- `SAME_DATASET_OR_BENCHMARK`;
- `INDEPENDENCE_NOT_ESTABLISHED`;
- `INDEPENDENT_WITH_STATED_BASIS`.

Multiple documents describing the same system release or evaluation do not become independent corroboration merely because they have different citations.

## 9. Matrix rationale rules

Rationales must:

1. state the observed capability and limitation, not praise or criticize the system;
2. identify the exact version and surface;
3. use dimension vocabulary;
4. distinguish implementation from documentation and evaluation;
5. avoid inferring negative capability from silence;
6. avoid equating record volume, citations, or scores with evidence strength; and
7. fit within 500 characters, with detail retained in the evidence ledger.

## 10. Reviewer coding and adjudication

At least two reviewers independently code:

- all cells for systems central to the eventual gap statement;
- all `ABSENT_EXPLICIT` cells;
- all AI-specific cells used in narrative claims;
- all cells with conflicting evidence; and
- a stratified sample of remaining systems, dimensions, surfaces, and states.

Report raw agreement and dimension-level agreement. Cohen's kappa may be reported when sample size and prevalence permit interpretation. A consensus cell does not erase initial reviewer codes.

Adjudication records the final state, adjudicator, rationale, and evidence IDs. If ambiguity cannot be resolved, the final state is `UNCLEAR`.

## 11. Derived summaries allowed and prohibited

Allowed descriptive summaries include:

- counts and percentages of cell states with explicit denominators;
- per-dimension distributions by system category and assessed surface;
- lists of verified implementation patterns;
- lists of unresolved documentation gaps;
- version-change tables; and
- evidence-linked examples and counterexamples.

Prohibited summaries include:

- total capability scores;
- weighted dimensions;
- system rankings or tiers;
- “best,” “leading,” or “most complete” labels derived from cell counts;
- treating `NOT_FOUND_IN_REVIEWED_MATERIALS` as `ABSENT_EXPLICIT`;
- treating inaccessible proprietary surfaces as evidence of absence; and
- treating multiple dependent documents as independent support.

## 12. Capability-matrix validation

Validation must fail when:

- a matrix key is duplicated;
- a state is outside the controlled vocabulary;
- a version/date or assessed surface is blank;
- a verified or explicitly absent state lacks qualifying evidence;
- an uncertainty state lacks its required rationale;
- an evidence ID does not resolve to the source registry;
- a source marked superseded is used as sole evidence of current capability;
- a challenged determination is silently finalized;
- a cell merges versions, products, dimensions, or surfaces; or
- a derived output contains a composite score, rank, recommendation, or unbounded capability-absence claim.

Passing these checks establishes traceable application of this comparison codebook. It does not establish that a system is scientifically valid, that its users interpret evidence correctly, or that the LUAD framework improves biomedical decisions.
