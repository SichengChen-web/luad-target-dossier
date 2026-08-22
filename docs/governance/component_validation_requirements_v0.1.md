# Component Validation Requirements v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Version:** v0.1  
**Status:** Frozen governance specification

## 1. Purpose

This specification defines the minimum validation required before a registered evidence component may be materialized within a governed Target Evidence Profile.

Validation tests representation fidelity, provenance, missingness, dependency preservation, determinism, and interpretation safety. It does not validate a target biologically and must not produce a score, rank, confidence metric, target-quality assessment, therapeutic recommendation, or runtime AI decision.

## 2. Validation inputs

Every validation run must start from a frozen input manifest containing:

- component registration and `component_id`;
- `component_version`, bound to `component_definition_version`;
- `schema_version`;
- `source_snapshot_version` and all source versions;
- `extractor_version`;
- `state_rule_version`;
- `generator_version`;
- feature dictionary and executable extraction rules;
- executable component-state predicates and precedence;
- provenance and dependency schemas;
- every input artifact ID, size, SHA256, and immutable storage reference where applicable;
- validation fixture IDs and expected structural results.

Validation must fail before generation if an input, version, hash, or identity is absent or inconsistent.

## 3. Required validation domains

### 3.1 Identity and version validation

Verify:

- `EnsemblID` is the only immutable entity key;
- one component instance maps to one `(EnsemblID, component_id, component_version, source_snapshot_version)` tuple;
- no gene-symbol join, fallback, or silent repair occurs;
- component, schema, source-snapshot, extractor, rule, generator, profile, and evidence-snapshot versions are present and not collapsed;
- `component_version` equals serialized `component_definition_version`;
- duplicate component-instance identities are absent.

### 3.2 Scientific-scope validation

Verify:

- the component answers one bounded observation question;
- every feature belongs to the registered scope;
- all source roles and record types are registered;
- applicability and exclusion rules are deterministic;
- every limitation and interpretation boundary propagates to the component manifest and downstream representation;
- no feature encodes an unstated scientific judgement.

### 3.3 Schema and feature validation

Verify:

- every serialized object validates against the exact `schema_version`;
- no undeclared field exists;
- feature IDs, names, types, controlled values, order, and cardinalities match the feature contract;
- extracted values reproduce exactly from frozen source records and registered rules;
- a feature without required provenance fails validation;
- feature counts are labelled as audit reconciliation only.

### 3.4 Component-state validation

The shared vocabulary is:

- `OBSERVED`;
- `PARTIAL`;
- `CONFLICTING`;
- `MISSING`;
- `NOT_QUERIED`.

Verify:

- every state has an executable, versioned component-specific predicate;
- precedence is exactly `CONFLICTING > OBSERVED > MISSING > PARTIAL > NOT_QUERIED`;
- a deterministic evaluator, not a human or LLM, selects the runtime state;
- one and only one final state is emitted after precedence;
- source state and downstream Task #031-style landscape state are identical;
- structural states are never treated as ordinal categories.

Required fixtures:

1. one base fixture that resolves to each state;
2. precedence-overlap fixtures for every higher-over-lower state boundary;
3. malformed-input and no-match failure fixtures;
4. identity-conflict and evidence-conflict fixtures where the component contract distinguishes them;
5. repeat-run fixtures that produce byte-identical state output.

### 3.5 Missingness validation

The feature-level vocabulary is:

- `OBSERVED`;
- `NOT_FOUND`;
- `NOT_QUERIED`;
- `NOT_APPLICABLE`;
- `UNKNOWN`.

Verify:

- all five values remain distinct in schema and materialization;
- missingness is copied or resolved only by a registered deterministic rule;
- `NOT_FOUND` is not converted to negative evidence;
- `NOT_QUERIED` is not converted to missing biology;
- `NOT_APPLICABLE` is not converted to absence;
- `UNKNOWN` is not silently repaired;
- component-level `MISSING` is not substituted for feature missingness;
- downstream profile and landscape representations preserve the exact source value.

Required fixtures include one valid example for each missingness value and failure fixtures for blank, unknown, or misspelled values outside the vocabulary.

### 3.6 Provenance validation

For every feature-to-record relationship, verify resolution of:

- `feature_id`;
- `claim_id`;
- `evidence_record_id`;
- `source_id` and source version;
- `artifact_id`, size, and SHA256;
- `dependency_id` or controlled sentinel;
- `extraction_rule_id`;
- `extractor_version`;
- component, source-snapshot, state-rule, schema, and generator versions.

Verify uniqueness of `(feature_id, evidence_record_id)`. Multiple evidence records must remain separate relationships. A summary or count must not replace lineage.

### 3.7 Dependency validation

Verify:

- every dependency member resolves to an evidence record;
- relationship type and dependency level use the registered vocabulary;
- `SHARED_DATASET`, `SAME_SOURCE`, partial, unknown, independent, and not-applicable paths have fixtures;
- dependent and partially dependent records retain their links;
- `NOT_APPLICABLE` is not treated as affirmative independence;
- `INDEPENDENT` has affirmative source-traceable justification;
- dependency grouping is unchanged in profile and landscape representations;
- no record duplication creates an additional apparent observation.

The normative details are in [Component Dependency Model v0.1](component_dependency_model_v0.1.md).

### 3.8 Determinism and reproducibility validation

Verify:

- the same frozen inputs and versions generate byte-identical component payloads;
- partition assignment and canonical ordering are deterministic;
- metadata and manifests regenerate byte-identically;
- all output sizes and SHA256 values reconcile;
- no random seed, wall-clock field, mutable network response, manual runtime edit, or AI/LLM judgement contributes to output bytes;
- the generator can rerun after its own commit without requiring current `HEAD` to equal a historical base commit;
- the frozen base commit remains an ancestor and frozen inputs remain unchanged relative to it where Git checks are used.

### 3.9 Interpretation-boundary validation

Inspect schemas, field names, controlled values, reports, and runtime output for prohibited evaluative content.

Prohibited output fields or generated conclusions include:

- scores or weighted aggregates;
- ranks or priorities;
- confidence metrics;
- evidence-strength categories;
- target quality or target selection;
- therapeutic direction or recommendations;
- biological interpretation;
- AI/LLM-generated runtime judgements.

Terms may appear in governance documents solely to state prohibitions. They must not appear as evaluative data fields or generated target conclusions.

## 4. Validation matrix

| Validation gate | Minimum pass condition | Failure consequence |
|---|---|---|
| Identity | Unique immutable tuples and no symbol joins | Stop materialization |
| Versions | Every independent version axis resolves exactly | Stop materialization |
| Scope | Every feature and record role is registered | Stop and revise registration |
| Schema | All objects validate with no undeclared fields | Reject generated artifact |
| State | Five-state predicates, precedence, and fixtures pass | Stop materialization |
| Missingness | Five-value semantics and fixtures pass unchanged | Stop materialization |
| Provenance | Complete resolvable record-level lineage | Reject generated artifact |
| Dependency | All relationships and unknowns preserved | Reject generated artifact |
| Determinism | Full repeat generation is byte-identical | Reject generator version |
| Interpretation safety | No prohibited evaluative field or runtime decision | Reject component release |
| Frozen-artifact integrity | Input hashes unchanged after validation | Stop and investigate |

Passing every gate confirms infrastructure conformance only.

## 5. Materialization-readiness record

A successful validation must produce a signed or otherwise governed human review record containing:

- validation run identity;
- exact input and output manifests;
- all versions and hashes;
- fixture inventory and results;
- validation-gate outcomes;
- observed limitations and untested paths;
- technical review status;
- scientific review status;
- authorized profile lifecycle destination;
- disposition: `APPROVED_FOR_SCOPED_MATERIALIZATION`, `CHANGES_REQUIRED`, or `REJECTED_WITH_RATIONALE`.

Automated validation may compute pass/fail facts. It must not make the human governance decision to promote a component or profile release.

## 6. Compatibility with Tasks #028–#031

The current governed architecture demonstrates the following compatible patterns:

- Task #028 separates profile lifecycle, component state, feature missingness, and interpretation boundaries.
- Task #030 preserves 29,606 immutable `EnsemblID` profiles, complete provenance, and Task #025 state-rule identity.
- Task #031 separately represents component availability, state, feature missingness, dependency references, and stable limitation IDs.
- The current materialized snapshot contains `OBSERVED` and `CONFLICTING` component states, while all five states remain schema-valid and fixture-tested.
- The current feature snapshot contains only `OBSERVED` missingness, so non-observed materialized paths remain an explicit limitation.
- Task #025 rules remain `AWAITING_INDEPENDENT_SCIENTIFIC_REVIEW`; infrastructure validation does not erase that status.

This specification does not modify or revalidate those frozen artifacts.

## 7. Validation checklist

- [ ] Frozen input manifest exists and all hashes match.
- [ ] Identity and version axes are complete and compatible.
- [ ] Scientific scope and non-claims are explicit.
- [ ] Schema and features pass exact validation.
- [ ] All state, precedence, and missingness fixtures pass.
- [ ] Provenance and dependency lineage reconcile record by record.
- [ ] Full regeneration is byte-identical.
- [ ] Existing artifacts remain unchanged.
- [ ] No external retrieval occurs during component materialization validation.
- [ ] No scoring, ranking, confidence metric, target quality, therapeutic recommendation, biological interpretation, or runtime AI decision is generated.
- [ ] Human authorization and intended profile lifecycle destination are recorded separately.

## 8. Related specifications

- [Evidence Component Interface Specification v0.1](evidence_component_interface_specification_v0.1.md)
- [Component Registration Policy v0.1](component_registration_policy_v0.1.md)
- [Component Dependency Model v0.1](component_dependency_model_v0.1.md)
- [Profile Release Policy v0.1](profile_release_policy_v0.1.md)

