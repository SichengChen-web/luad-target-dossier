# Prioritization Rule Catalog v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Task:** #035A  
**Catalog version:** `PRIORITIZATION_RULE_CATALOG_V0.1`  
**Status:** Reviewed structural rule specification; no target assignments generated

## 1. Purpose

This catalog defines four mutually exclusive structural predicates over the component states preserved in one Evidence Summary. The catalog produces non-ordinal category labels for transparent routing only. It does not score, rank, select, recommend, or interpret targets.

## 2. Controlled input

The sole rule input is the ordered `component_state_snapshot` copied from one frozen Evidence Summary. Each entry contains:

- `component_id`;
- `component_version`;
- `component_state`.

Allowed states are:

- `OBSERVED`;
- `PARTIAL`;
- `CONFLICTING`;
- `MISSING`;
- `NOT_QUERIED`.

The current source-summary component set is exactly:

1. `COMP_TRANSCRIPTOMIC_EVIDENCE_V0.1`;
2. `COMP_DISEASE_ASSOCIATION_V0.1`.

Component order is serialization metadata, not an order of importance.

## 3. Controlled predicates

### `PRULE_035A_001_PARTIAL_OR_CONFLICTING`

- **Predicate ID:** `PPRED_ANY_PARTIAL_OR_CONFLICTING_V0.1`
- **Category:** `CATEGORY_C`
- **Predicate:** at least one component state is `PARTIAL` or `CONFLICTING`.
- **Structural meaning:** the source summary contains a component-level partial or conflicting condition requiring explicit review.
- **Non-claim:** this does not mean the target is weak, unsafe, unsuitable, or scientifically conflicting across domains.

### `PRULE_035A_002_ALL_OBSERVED`

- **Predicate ID:** `PPRED_ALL_COMPONENTS_OBSERVED_V0.1`
- **Category:** `CATEGORY_A`
- **Predicate:** every component state is `OBSERVED`.
- **Structural meaning:** every registered component reports its governed observed structural state.
- **Non-claim:** this does not mean evidence is strong, independent, causal, actionable, complete, or favorable.

### `PRULE_035A_003_MIXED_OBSERVED_UNAVAILABLE`

- **Predicate ID:** `PPRED_MIXED_OBSERVED_AND_UNAVAILABLE_V0.1`
- **Category:** `CATEGORY_B`
- **Predicate:** at least one component state is `OBSERVED`; at least one is `MISSING` or `NOT_QUERIED`; and no component is `PARTIAL` or `CONFLICTING`.
- **Structural meaning:** observed and unavailable/not-queried component conditions coexist in the source summary.
- **Non-claim:** missing or unqueried evidence is not negative evidence, and the category does not measure evidence quality.

### `PRULE_035A_004_ALL_UNAVAILABLE`

- **Predicate ID:** `PPRED_ALL_COMPONENTS_UNAVAILABLE_V0.1`
- **Category:** `CATEGORY_UNASSIGNED`
- **Predicate:** every component state is `MISSING` or `NOT_QUERIED`.
- **Structural meaning:** the reviewed v0.1 catalog does not assign an A/B/C structural route when no component is `OBSERVED`, `PARTIAL`, or `CONFLICTING`.
- **Non-claim:** the target is not rejected, deprioritized, biologically absent, or unsupported.

## 4. Mutual exclusivity and completeness

For a non-empty component snapshot containing only controlled states, the four predicates partition the possible state patterns:

1. any `PARTIAL` or `CONFLICTING` state matches rule 001;
2. otherwise, all `OBSERVED` matches rule 002;
3. otherwise, a mixture of `OBSERVED` and `MISSING`/`NOT_QUERIED` matches rule 003;
4. otherwise, all `MISSING`/`NOT_QUERIED` matches rule 004.

This numbered audit order makes trace serialization deterministic. It is not category precedence, target ordering, rank, or priority. Exactly one predicate must be true. Zero or multiple true predicates are validation failures.

## 5. Category non-ordinality

`CATEGORY_A`, `CATEGORY_B`, `CATEGORY_C`, and `CATEGORY_UNASSIGNED` are opaque controlled identifiers. Alphabetical order has no scientific or operational meaning. Implementations must not:

- map them to numbers or weights;
- sort targets by category as an implied order;
- label them high, medium, or low;
- infer desirability or progression gates;
- treat `CATEGORY_UNASSIGNED` as failure or exclusion.

## 6. Rule-trace contract

Every future assignment must record all four rules in the fixed catalog order. Each trace step must preserve:

- `trace_step_ordinal` from 1 through 4;
- exact `rule_id`;
- exact `predicate_id`;
- boolean `predicate_result`;
- ordered input observations, each containing a JSON pointer and the exact controlled value read.

The assignment record must identify the single true `assigned_rule_id`. Free-text explanations, LLM rationales, manually added exceptions, or hidden predicates are prohibited.

## 7. Limitations and missingness

Limitation identifiers are retained in the output but do not participate in v0.1 predicates. Feature-level missingness is not a direct v0.1 rule input; only frozen component states are evaluated. Rules must not infer negative evidence from `MISSING`, `NOT_QUERIED`, or any limitation.

## 8. Change control

Changing a predicate, category mapping, input path, trace order, component-set assumption, or category vocabulary requires a new rule-catalog version and full validation. A correction must not overwrite this catalog. Rule changes do not retroactively change frozen assignments.

## 9. Prohibitions

The catalog must not introduce numeric scores, ranks, priority scores, confidence, probability, success predictions, recommendations, target quality, evidence strength, biological interpretation, therapeutic interpretation, external evidence retrieval, or runtime AI/LLM decisions.

## 10. Related governance

- [Transparent Prioritization Prototype Specification v0.1](prioritization_framework_specification_v0.1.md)
- [Prioritization Validation Requirements v0.1](prioritization_validation_requirements_v0.1.md)
- [Evidence Summary Component Policy v0.1](evidence_summary_component_policy_v0.1.md)

