# Executable State Rule Registry v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Task:** #025 — Executable State Rule Registry  
**Version:** v0.1  
**Date:** 21 August 2026  
**Status:** Automated validation passed; independent scientific review pending

## Scientific purpose

Task #021 defined 55 component-state predicates in controlled prose. Task #023 showed that those predicates could represent the validation cases but warned that prose was not itself an executable rule language. Task #024 therefore made executable, reviewed, versioned predicates a blocking profile-release requirement.

Task #025 creates the governed executable state-machine layer. It does not create profiles or evaluate genes.

## Frozen inputs

The registry uses only:

- `outputs/profile_materialization/component_state_resolution_registry.csv`;
- `docs/profile_release_specification_v0.1.md`;
- `outputs/profile_release_specification/profile_release_requirements.csv`; and
- `outputs/profile_release_specification/profile_release_qc_matrix.csv`.

Every input is hash-pinned and rechecked after generation.

## One-to-one semantic mapping

Every frozen `(component_id, resolved_state)` row maps to exactly one executable rule with:

- stable `rule_id`;
- original component ID and component name;
- state and frozen precedence;
- registry version;
- SHA256 of the original Task #021 semantic predicate;
- original predicate text;
- canonical executable predicate JSON;
- typed normalized input-feature contract;
- required feature-extractor status;
- evaluator ID/version;
- fixture coverage;
- automated validation status;
- independent-review status; and
- interpretation boundary.

Rule IDs have the form:

```text
SRR_V0_1__<COMPONENT_TOKEN>__<STATE>
```

They are identifiers, not scores or evidence weights.

## Executable predicate language

Predicates are canonical JSON abstract syntax trees. The allow-listed operators are:

| Operator | Meaning | Allowed values |
| --- | --- | --- |
| `all` | all child predicates are true | nonempty predicate list |
| `any` | at least one child predicate is true | nonempty predicate list |
| `eq` | exact typed equality | Boolean or nonnegative integer |
| `ge` | integer greater than or equal | nonnegative integer |
| `gt` | integer greater than | nonnegative integer |

The evaluator does not use Python `eval`, dynamic imports, arbitrary expressions, free-text parsing, model calls, randomness, locale, filesystem order, or wall-clock time.

Unknown operators, undeclared features, missing values, extra values, type mismatches, and negative counts stop execution.

## Normalized feature contract

Each component has a distinct frozen feature namespace. Every namespace defines:

- component-specific material-conflict count;
- identity-conflict count;
- qualifying-record count;
- observed-context completeness;
- assessment-attempted state;
- query-scope completeness;
- atomic record count;
- component-specific partial-condition count;
- unknown-coverage state;
- retrieval-failure state;
- provenance completeness; and
- source-specific mapping validity when the semantic predicate requires it.

Feature definitions are grounded in the original Task #021 predicate. For example, transcript qualifying records mean the required primary and robustness roles, whereas pharmacology qualifying records mean compound-target assay/mechanism records with potency, units, target confidence, mechanism, and assay/source provenance.

The feature values are not target measurements, evidence scores, or confidence weights. Counts are predicate inputs such as “zero qualifying records” or “at least one traceable conflict.” They cannot be summed across components.

## Rule templates

The executable form preserves component-specific feature definitions while using a common typed state-machine skeleton.

### CONFLICTING

Matches when the component-specific material-conflict count or identity-conflict count is greater than zero.

### OBSERVED

Matches when:

- no component or identity conflict is present;
- the component-specific minimum qualifying-record count is met;
- required observed context is complete;
- provenance is complete; and
- required target/disease/linkage mapping is valid where applicable.

The transcript component requires both primary and robustness roles; other current component criteria require at least one qualifying record.

### MISSING

Matches when:

- no conflict is present;
- acquisition was attempted;
- the entire frozen component query scope completed;
- qualifying-record count is zero;
- coverage is not unknown;
- retrieval did not fail; and
- minimum query/source provenance is complete; and
- required mapping is valid where applicable.

This is absence after a complete defined assessment. It is not negative biological evidence.

### PARTIAL

Matches when:

- no conflict is present;
- an assessment was attempted or a record exists; and
- at least one component-specific incomplete-evidence, linkage, coverage, quality-context, or provenance condition is present.

### NOT_QUERIED

Matches when:

- no conflict is present;
- no eligible acquisition was attempted; and
- no component record exists.

It cannot be inferred from a returned zero, blank field, or failed retrieval.

## Resolution and precedence

All five predicates are evaluated deterministically. The first matched rule in this frozen order resolves:

```text
CONFLICTING
>
OBSERVED
>
MISSING
>
PARTIAL
>
NOT_QUERIED
```

The stored precedence integers 1–5 are control-flow positions only. They are not scientific scores, ordinal evidence quality, confidence, or rankings.

If no predicate matches, the evaluator returns `NO_RULE` and `NO_STATE`. This is a blocking error. It cannot choose the closest state, invoke a model, use a fallback default, or interpret the evidence.

## Test architecture

The registry is tested with 110 synthetic structural fixtures:

1. **55 positive-state fixtures:** one fixture for every component/state rule.
2. **44 conflict-guard fixtures:** four per component, verifying that a conflict condition prevents every lower state from resolving first.
3. **11 fail-closed fixtures:** one incoherent feature set per component, verifying that unresolved input stops without guessing.

Fixtures contain normalized Boolean/count values only. They do not represent genes, biological evidence, target profiles, or therapeutic hypotheses.

Each fixture records:

- canonical input-feature JSON;
- all individually matched rules;
- precedence trace;
- resolved and expected rule/state;
- deterministic repeat result;
- assertion; and
- validation status.

Every rule must have at least one passing positive fixture. Every fixture must pass before the registry is generated.

## Review governance

Automated validation and independent scientific review are distinct.

- `automated_validation_status=PASS` means the JSON predicate is well typed, deterministic, source-linked, fixture-covered, and resolves as expected.
- `review_status=AWAITING_INDEPENDENT_SCIENTIFIC_REVIEW` means no independent reviewer has yet approved the semantic-to-feature conversion.

Task #025 does not invent reviewer approval. Before profile release, an independent review must assess every component feature definition, expression, precedence interaction, and fixture boundary against the frozen Task #021 meaning.

Any approved change creates a new registry version and hashes; it cannot overwrite v0.1.

## Runtime prohibitions

Runtime state resolution must not:

- call an LLM or ask for free-text judgment;
- score or weight evidence;
- treat counts as evidence quality;
- combine components;
- convert missingness into favorable or unfavorable meaning;
- infer independence from no dependency edge;
- infer causality, efficacy, safety, clinical benefit, or therapeutic direction; or
- select, rank, prioritize, or recommend targets.

## Determinism

The same:

- frozen semantic registry;
- normalized feature values;
- executable registry version;
- evaluator implementation/version; and
- precedence configuration

must produce identical rule matches and final state. The registry, fixtures, summary, and session output are canonically serialized and generated twice in memory before writing.

## Release-readiness limitations

Task #025 supplies the executable predicate registry but does not complete profile-release readiness:

- source-record-to-normalized-feature extractors are not implemented;
- independent scientific review remains pending for all 55 rules;
- fixtures validate state-machine mechanics, not biological correctness;
- real-data conflicts are not available for every component; and
- no target manifest, target profile, or release bundle is generated.

These limitations must remain explicit. They cannot be resolved by scoring targets or by runtime model judgment.
