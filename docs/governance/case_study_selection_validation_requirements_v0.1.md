# Case Study Selection Validation Requirements v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Task:** #036A  
**Version:** v0.1  
**Status:** Governance requirements; no representative case selected

## 1. Purpose and boundary

These requirements validate the Case Study Selection schema and any future deterministic selector. Validation establishes source fidelity, eligibility traceability, neutral deterministic sampling, and interpretation safety. It does not validate target biology, therapeutic relevance, or presentation claims.

## 2. Frozen inputs

Before schema generation or future selection, verify exact hashes for:

- Task #035A prioritization governance, schema, rule catalog, and validation requirements;
- Task #035B materializer, manifest, index, partition manifest, validation report, session record, and immutable payload references;
- the Case Study Selection framework, rule catalog, schema, and selector version.

Repeat frozen artifact checks after generation. Any unexpected modification, missing artifact, or substituted source must fail closed. Prioritization representations remain read-only.

## 3. Schema requirements

The schema must:

- declare JSON Schema Draft 2020-12;
- close every object with `additionalProperties: false`;
- require immutable identity and source hashes;
- require exact source prioritization and Evidence Summary identities;
- require preservation of source prioritization rule traces;
- require component IDs, versions, states, source record IDs, and limitations;
- require one case category, case rule ID, complete predicate trace, structural reason, selection method, and token SHA256;
- constrain categories, rules, predicates, states, and reason codes to controlled vocabularies;
- reject undeclared and prohibited fields.

Every local `$ref` must resolve.

## 4. Source identity and fidelity

A future selector must verify:

- every eligibility evaluation refers to exactly one frozen prioritization representation;
- `EnsemblID`, canonical universe ordinal, representation ID, schema version, framework version, rule-catalog version, and source content SHA256 are exact;
- source Evidence Summary identity and content SHA256 are exact;
- all four source prioritization trace steps are unchanged;
- component IDs, versions, states, source component-record IDs, and limitations are unchanged;
- summary-level limitations are unchanged;
- no gene-symbol join, identity repair, evidence retrieval, or source reconstruction occurs.

## 5. Eligibility validation

Evaluate all four case rules for every source representation and confirm:

- fixed trace ordinals 1 through 4;
- exact case-rule and predicate identifiers;
- input pointers resolve to preserved source fields;
- observed values equal source values;
- predicate booleans reproduce exactly;
- selected `case_rule_id` is true;
- category and structural reason code match the selected rule;
- overlapping predicates remain visible rather than being collapsed.

## 6. Neutral deterministic selection validation

For each category:

1. reconcile the complete eligible pool;
2. independently regenerate every category-salted selection token;
3. confirm the token input tuple and canonical JSON bytes;
4. confirm the selected token is lexicographically smallest within that category;
5. confirm exactly one slot is filled when eligible records exist;
6. preserve an explicit unfilled status when no eligible record exists;
7. confirm no token is treated as a score or compared across categories.

Complete eligible-pool validation is required; sampling cannot validate deterministic selection.

## 7. Boundary fixtures

Fixtures must cover:

- all components observed → complete pattern;
- partial component state → partial pattern;
- mixed observed and missing/not-queried states → partial pattern;
- conflicting component state → conflict pattern;
- one or more limitation identifiers → limitation pattern;
- overlap between limitation and each state-based category;
- empty category behavior;
- wrong rule/category/reason mapping rejection;
- incomplete or reordered predicate trace rejection;
- changed source rule trace rejection;
- changed component state or limitation rejection;
- deterministic token reproduction.

Fixtures use synthetic identities and are not project case selections.

## 8. Prohibited-field validation

Recursively reject exact fields:

- `best_target`;
- `top_target`;
- `rank`;
- `ranking`;
- `score`;
- `priority_score`;
- `recommendation`;
- `target_quality`;
- `evidence_strength`.

Also reject aliases or structures implementing target optimization, ordering, scoring, recommendation, evidence-strength estimation, biological interpretation, or therapeutic interpretation.

## 9. Non-ordinality and interpretation safety

Confirm that:

- categories have no numeric encoding, weight, stage, tier, or desirability order;
- selection tokens are not exposed as target-ordering values;
- `CASE_COMPLETE_PATTERN` is not described as biologically complete or favorable;
- `CASE_CONFLICT_PATTERN` is not treated as failure;
- limitations are not penalties;
- no selected case is described as best, top, optimal, important, actionable, or recommended;
- case eligibility and selection do not promote scientific lifecycle status.

## 10. Determinism

Identical frozen inputs, schema, rules, framework, and selector version must produce byte-identical selected-case records and traces. A future materializer must run two independent complete eligibility and selection passes and compare bytes, hashes, eligible pools, tokens, and slot outcomes.

No output may depend on wall-clock time, randomness, hostname, mutable external state, manual case substitution, or runtime AI/LLM decisions.

## 11. Task #036A validation boundary

Task #036A must verify:

- compatibility with Task #035A and Task #035B terminology and hashes;
- deterministic schema generation;
- local Markdown-link resolution;
- prohibited-field rejection;
- frozen prior artifact hashes unchanged;
- no case-selection output, eligible pool, target selection, network access, or package installation.

## 12. Future materialization gate

- [ ] Frozen prioritization payload and all metadata resolve.
- [ ] Complete identity and source trace reconciliation passes.
- [ ] All case predicates reproduce.
- [ ] Eligible pools and tokens reproduce completely.
- [ ] One slot per non-empty category is selected neutrally.
- [ ] Empty categories remain unfilled.
- [ ] Prohibited-field and interpretation-safety checks pass.
- [ ] Two complete regenerations are byte-identical.
- [ ] No target ranking, optimization, recommendation, or biological claim exists.

## 13. Related governance

- [Case Study Selection Framework v0.1](case_study_selection_framework_v0.1.md)
- [Case Study Selection Rule Catalog v0.1](case_study_selection_rule_catalog_v0.1.md)
- [Prioritization Validation Requirements v0.1](prioritization_validation_requirements_v0.1.md)
- [Case Study Selection schema v0.1](../../schemas/case_study_selection_schema_v0.1.json)

