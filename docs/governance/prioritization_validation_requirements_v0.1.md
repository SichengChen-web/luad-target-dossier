# Prioritization Validation Requirements v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Task:** #035A  
**Version:** v0.1  
**Status:** Governance requirements; no prioritization payload generated

## 1. Purpose and boundary

These requirements validate the Transparent Prioritization Prototype schema and any future deterministic category materializer. Validation establishes structural fidelity, rule traceability, mutual exclusivity, determinism, and interpretation safety. It does not validate targets biologically or therapeutically.

## 2. Frozen inputs

Before schema generation or future materialization, verify exact hashes for:

- Task #034A Evidence Summary governance, schema, and schema generator;
- Task #034B materializer, summary manifest, summary index, partition manifest, validation report, and session record;
- the applicable Prioritization Rule Catalog and output schema.

Repeat repository artifact hash validation after generation. Any unexpected change, missing input, or substituted artifact must fail closed. Evidence Summaries must remain read-only.

## 3. Schema validation

The schema must:

- declare JSON Schema Draft 2020-12;
- use closed object definitions;
- require immutable `EnsemblID` and deterministic representation identity;
- require exact source Evidence Summary identity and content SHA256;
- require ordered component ID/version/state snapshots;
- require summary and component limitation identifiers;
- require one controlled category, one assigned rule ID, and a complete rule trace;
- restrict categories and component states to controlled vocabularies;
- reject undeclared or prohibited fields.

Every local `$ref` must resolve. Every object schema must use `additionalProperties: false`.

## 4. Identity and source reconciliation

A future materializer must confirm:

- exactly one representation per source Evidence Summary;
- exact `EnsemblID`, source summary ID, schema version, summary version, and source content SHA256;
- exact canonical universe ordinal;
- no gene-symbol join, fallback mapping, target selection, or identifier repair;
- deterministic representation ID from the frozen identity tuple.

## 5. Component and limitation preservation

For every source summary:

- component count, order, IDs, versions, and states must match exactly;
- summary-level limitation identifiers must match exactly;
- each component's limitation identifiers must match exactly;
- no state or limitation may be inferred, removed, relabelled, penalized, weighted, or interpreted.

The prioritization representation must not create an overall component or evidence state.

## 6. Rule evaluation and trace validation

Validate every assignment against `PRIORITIZATION_RULE_CATALOG_V0.1`:

- all four rules are evaluated in fixed trace order;
- trace ordinals are exactly 1, 2, 3, and 4;
- rule and predicate IDs are exact;
- input JSON pointers resolve to the preserved component-state snapshot;
- observed values equal source component states;
- predicate results reproduce deterministically;
- exactly one predicate is true;
- `assigned_rule_id` is the true rule;
- category equals the catalog mapping for that rule;
- no hidden input or exception participates.

## 7. Boundary fixtures

Schema and rule fixtures must cover at least:

- all components `OBSERVED` → `CATEGORY_A`;
- mixed `OBSERVED` and `MISSING`/`NOT_QUERIED` → `CATEGORY_B`;
- any `PARTIAL` or `CONFLICTING` → `CATEGORY_C`;
- all `MISSING`/`NOT_QUERIED` → `CATEGORY_UNASSIGNED`;
- uncontrolled component state rejection;
- zero-match and multiple-match rejection;
- wrong category/rule mapping rejection;
- reordered or incomplete trace rejection;
- source-summary identity mismatch rejection;
- modified component or limitation rejection.

Fixtures use synthetic identities only and are not project target assignments.

## 8. Prohibited-field validation

Recursively reject exact fields:

- `score`;
- `ranking`;
- `rank`;
- `priority_score`;
- `confidence`;
- `probability`;
- `success_prediction`;
- `recommendation`;
- `target_quality`;
- `evidence_strength`.

Also reject aliases or structures that implement numeric scoring, target ordering, confidence estimation, probability estimation, success prediction, target selection, recommendation, evidence-strength estimation, or biological interpretation.

Prohibition text in governance or validation reports is permitted when explicitly framed as a non-claim.

## 9. Non-ordinality validation

Confirm that:

- categories have no numeric encoding or weight;
- no sort key, precedence value, desirability label, progression gate, or best/worst mapping exists;
- category counts are reconciliation metadata only;
- `CATEGORY_UNASSIGNED` is not treated as rejection or negative evidence;
- category labels are not used to order targets.

## 10. Determinism

Identical frozen summary bytes, schema, rule catalog, and generator version must produce byte-identical representations and traces. A future full materializer must perform two complete independent regenerations and compare bytes, sizes, hashes, identity order, rule results, and category reconciliation.

No value may depend on wall-clock time, randomness, hostname, mutable network responses, manual target exceptions, or runtime AI/LLM decisions.

## 11. Documentation and repository validation

Validate that:

- terminology is compatible with Task #034A Evidence Summary governance;
- all local Markdown links resolve;
- version and rule identifiers are exact;
- no Task #035A document claims target assignments were generated;
- no prior artifact changed;
- no prioritization payload, output registry, target selection, network retrieval, or package installation occurred.

## 12. Future materialization gate

- [ ] Frozen Evidence Summary payload and metadata resolve.
- [ ] Identity and canonical order reconcile.
- [ ] Component states and limitations reconcile.
- [ ] All rule traces reproduce exactly.
- [ ] Exactly one category rule matches every valid input.
- [ ] Prohibited-field and non-ordinality checks pass.
- [ ] Complete regeneration is byte-identical.
- [ ] No scoring, ranking, selection, recommendation, or interpretation exists.
- [ ] Category materialization is separately authorized.

## 13. Related governance

- [Transparent Prioritization Prototype Specification v0.1](prioritization_framework_specification_v0.1.md)
- [Prioritization Rule Catalog v0.1](prioritization_rule_catalog_v0.1.md)
- [Evidence Summary Validation Requirements v0.1](evidence_summary_validation_requirements_v0.1.md)
- [Prioritization Output schema v0.1](../../schemas/prioritization_output_schema_v0.1.json)

