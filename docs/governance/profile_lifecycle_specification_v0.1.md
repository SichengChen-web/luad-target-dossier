# Profile Lifecycle Specification v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Version:** v0.1  
**Status:** Frozen governance specification

## 1. Purpose and boundary

This specification defines governance states and permitted transitions for Target Evidence Profile releases. A lifecycle state describes validation and release maturity. It does not describe evidence strength, target quality, biological importance, therapeutic potential, or priority.

Lifecycle advancement must never be driven by a target score, rank, candidate selection, therapeutic recommendation, biological interpretation, or AI/LLM runtime decision.

## 2. Lifecycle object

Lifecycle state applies to a manifested profile release, not independently to a gene or evidence component. Every release must declare exactly one state and retain the manifest, hashes, validation records, review records, limitations, and generator identities associated with entry into that state.

Component evidence states such as `OBSERVED`, `CONFLICTING`, `MISSING`, `PARTIAL`, and `NOT_QUERIED` are structurally different from lifecycle states. A component state cannot automatically promote or block a lifecycle state; lifecycle gates evaluate whether the state was represented and validated correctly, not whether it looks scientifically favorable.

## 3. Lifecycle states

### 3.1 `PILOT_VALIDATION_ONLY`

Purpose: validate schema, materialization rules, lineage propagation, controlled missingness, state evaluation, and deterministic regeneration on a bounded deterministic universe.

Required characteristics:

- the pilot universe and deterministic selection rule are explicit;
- profiles are labelled as pilot artifacts;
- all feature values match frozen normalized inputs;
- all provenance relationships are complete and uncompressed;
- schema and deterministic regeneration checks pass;
- untested components, states, and missingness paths are reported.

Permitted use: architecture and validation review only.

Not permitted: public scientific claims, full-universe completeness claims, target evaluation, scoring, ranking, prioritization, therapeutic recommendation, or biological interpretation.

Task #027 is governed at this state.

### 3.2 `INTERNAL_VALIDATION`

Purpose: validate a registered profile definition over its declared internal release universe and evidence snapshot.

Entry requirements:

- all included components are registered and versioned;
- the target universe and order are frozen;
- the complete declared universe materializes deterministically;
- schema, identity, feature-value, lineage, dependency, missingness, and rule validations pass;
- positive, negative, conflict, partial, missing, and not-queried fixtures are tested where the component contract permits them;
- large governed artifacts have validated checksums and resolvable storage references for internal use;
- limitations and unresolved review items are recorded.

Permitted use: internal technical and scientific audit.

Not permitted: public release or claims that the profiles validate targets.

### 3.3 `SCIENTIFIC_REVIEWED`

Purpose: record that qualified human scientific reviewers have reviewed evidence meanings, source limitations, dependency treatment, missingness semantics, state predicates, interpretation boundaries, and unresolved uncertainty for the declared release.

Entry requirements:

- all `INTERNAL_VALIDATION` gates pass;
- component definitions and executable state rules have completed the required scientific review rather than retaining an awaiting-review status;
- review identities, scope, version, findings, and disposition are recorded;
- scientific reviewers confirm that profile fields do not overstate what the evidence supports;
- conflicts and missing evidence remain explicit;
- review does not introduce manual scores, rankings, recommendations, or hidden profile edits.

`SCIENTIFIC_REVIEWED` means the representation and its boundaries were reviewed. It does not mean a target is biologically validated, effective, safe, clinically useful, or recommended.

### 3.4 `PUBLIC_RELEASE`

Purpose: publish an immutable, reproducible profile release with complete documentation, accessible governed artifacts, and explicit interpretation limits.

Entry requirements:

- all `SCIENTIFIC_REVIEWED` gates pass;
- the release manifest and all referenced artifacts are immutable and retrievable;
- external artifact storage references, sizes, and SHA256 checksums resolve and validate;
- public schemas, component definitions, lifecycle state, source versions, limitations, review records, and QC results are included;
- deterministic regeneration instructions are complete;
- no restricted, sensitive, or unlicensed data are exposed;
- the release is assigned an immutable release identifier.

Public release does not authorize scoring, ranking, target prioritization, therapeutic recommendation, or biological interpretation unless a separate future governed framework explicitly permits a different artifact class. This profile framework does not permit those outputs.

## 4. Transition model

The permitted forward sequence is:

`PILOT_VALIDATION_ONLY → INTERNAL_VALIDATION → SCIENTIFIC_REVIEWED → PUBLIC_RELEASE`

Rules:

1. No state may be skipped.
2. Promotion requires all entry requirements for the destination state.
3. Promotion is a recorded governance action over an immutable candidate release; it is never inferred from profile contents.
4. Runtime AI or LLM decisions cannot approve, reject, or propose a transition.
5. A failed gate returns the artifact for correction under a new generator, schema, profile, component, rule, or evidence-snapshot version as appropriate.
6. Corrected bytes must not replace a previously frozen release under the same identity.
7. A public release may be superseded or withdrawn through a documented notice, but its original manifested artifacts and hashes remain historically identifiable.

## 5. Version changes and lifecycle consequences

| Change | Minimum consequence |
|---|---|
| Evidence values, records, source release, or input hashes change | New evidence snapshot and re-enter validation |
| Profile assembly or included components change | New profile version and re-enter validation |
| Serialized structure or constraints change | New schema version and schema validation |
| Component meaning, missingness, dependency, or feature interface changes | New component definition version and scientific review |
| State predicate or precedence changes | New state-rule version and rule/fixture review |
| Extractor or generator behavior changes | New implementation version and deterministic regeneration validation |
| Documentation-only clarification with no semantic or artifact change | Document version change; lifecycle impact must be recorded explicitly |

A lifecycle label from one version cannot be inherited automatically by another version.

## 6. Lifecycle validation checklist

- [ ] Release identity and lifecycle state are explicit.
- [ ] The immediately preceding lifecycle state was completed.
- [ ] Required artifacts and validation reports exist and match their hashes.
- [ ] Schema, profile, evidence-snapshot, component, rule, extractor, and generator versions are recorded separately.
- [ ] The declared target universe and ordering are reproducible.
- [ ] Identity, value, missingness, lineage, dependency, rule, and determinism checks pass.
- [ ] Review status of every included component and state rule meets the destination gate.
- [ ] Untested states, missingness paths, and future components are disclosed.
- [ ] No score, rank, priority, target prioritization, therapeutic recommendation, or biological interpretation influenced transition.
- [ ] No AI or LLM runtime decision influenced transition.
- [ ] Promotion authority, review scope, findings, and disposition are recorded.
- [ ] A failed or superseded release remains historically traceable.

## 7. Current lifecycle position

The Task #027 pilot remains `PILOT_VALIDATION_ONLY`. It cannot advance automatically. In particular, the current Task #025 state rules retain `AWAITING_INDEPENDENT_SCIENTIFIC_REVIEW`, non-observed transcriptomic paths remain incompletely exercised, future components are not implemented, and the Task #026 provenance artifact's external storage reference remains pending.

