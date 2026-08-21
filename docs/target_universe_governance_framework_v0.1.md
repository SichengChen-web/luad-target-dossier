# Target Universe Governance Framework v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Task:** #022 — Target Universe Governance Framework  
**Version:** v0.1  
**Date:** 21 August 2026  
**Status:** Working governance specification

## Scientific question and decision boundary

The scientific question is correctly formulated if “allowed to enter profiling” means membership in a named, versioned scope. It would be incorrectly formulated if membership were treated as evidence that one gene is more important, actionable, druggable, or clinically relevant than another.

Task #022 therefore defines an object-governance layer:

> For an immutable gene entity, which target-universe membership state is justified by which frozen rule, source artifact, timestamp, and reason?

It does not create a final candidate list. It does not judge target quality or interpret evidence.

## Target entity

A target entity is the exact Ensembl gene record represented by the versioned `EnsemblID` preserved from the frozen registries. In the current inputs, values such as `ENSG00000108576.9` identify the entity.

- `EnsemblID` is the only immutable join key.
- `Symbol` and `gene_type` are permitted display annotations.
- `EnsemblID_base` may exist upstream but is not a target-universe join key.
- Symbols cannot be used to join, repair, replace, or manually infer identity.
- External evidence identifiers remain annotations in their own governed layers and do not replace EnsemblID.

A future `target_manifest.csv` represents exactly one `target_universe_id` and `target_universe_version`. Within that snapshot, EnsemblID must be unique. Multiple universe snapshots are stored as separate immutable artifacts rather than appended into an ambiguously keyed file.

## Eligibility versus membership

Eligibility means that a frozen, versioned rule can evaluate the entity for a defined universe. Membership is the controlled state produced by that rule. Eligibility must not depend on an unstated judgment such as “important target,” “low-value gene,” or “interesting biology.”

Each future membership record requires:

- the exact EnsemblID;
- a universe ID and content-derived version;
- one membership state;
- a versioned rule ID;
- source artifact IDs and SHA256 hashes;
- a frozen membership timestamp;
- a neutral, template-generated reason; and
- explicit annotation availability.

No manual row edit is valid without a new governed source, rule, generator run, QC record, and universe version.

## Universe model

The framework represents four universe types without instantiating their gene memberships.

### Universe A — All tested genes

Question: Was the entity present in the exact frozen tested-gene analysis scope?

The current registries contain an explicit `U0_tested` field. A future executable Universe A definition may name that field and freeze the candidate/integrated registry hashes. Presence in Universe A means tested in that analysis scope only.

It does not mean that the entity is disease related, causal, actionable, or druggable.

### Universe B — DE-supported genes

Question: Does the entity meet one explicitly declared, frozen DE membership definition?

The existing registry distinguishes `U1_DE` from `U2_effect_supported_DE`. Task #022 does not choose between them because that would be a new scientific scope decision. A future Universe B version must name the exact Boolean field and its upstream scientific definition. Changing the named DE layer creates a different universe version.

Membership records an analysis-defined scope. It does not establish causality, therapeutic relevance, or target quality.

### Universe C — Evidence-profiled entities

Question: Does a released, QC-passing Task #021-compatible profile artifact exist for the entity?

Membership depends on materialization provenance and QC, not on whether component evidence is observed, partial, missing, not queried, or conflicting. Profile completeness and record quantity cannot govern membership.

Task #022 creates no profile and no Universe C membership.

### Universe D — Future therapeutic development universe

Question: Has a later scientific task approved a versioned, neutral membership definition for a therapeutic-development scope?

No such definition is supplied. Its current governance state is `FUTURE_SCOPE`. Existing DE, drug, tractability, safety, clinical, or profile fields must not be used as an implicit filter. This is deliberate deferral, not missing implementation.

## Membership states

### INCLUDED

The exact deterministic inclusion condition evaluates true under the frozen universe definition.

`INCLUDED` means in scope. It does not mean favorable, validated, or recommended.

### EXCLUDED

The exact deterministic exclusion condition evaluates true for this universe definition.

`EXCLUDED` means outside the defined scope. It does not mean biologically bad, uninteresting, unsupported in every context, or unsuitable for therapy. Excluded entities remain present in the membership ledger with their source, rule, timestamp, and neutral reason.

### NOT_ASSESSED

Membership could not be resolved from the frozen source and rule without inference, repair, or an invalid coercion. Missing or invalid membership data must not be converted to `EXCLUDED`.

### FUTURE_SCOPE

The entity or universe definition belongs to a later governed scope. This state preserves deliberate deferral without claiming inclusion or exclusion.

## Future target_manifest.csv

`outputs/target_universe_governance/target_universe_schema.csv` defines the future long-form manifest fields. Required user-specified fields are retained, with additional fields needed for Task #021 compatibility, versioning, deterministic order, and provenance.

The manifest has one row per EnsemblID for one universe snapshot. Every row remains in the ledger, including `EXCLUDED`, `NOT_ASSESSED`, and `FUTURE_SCOPE` rows. A downstream Task #021 materialization run may use only `INCLUDED` rows, preserving their governed `target_order`.

`inclusion_timestamp` equals the frozen `membership_timestamp` only for `INCLUDED` rows. Other states use the explicit `NOT_APPLICABLE` sentinel. This distinguishes the timestamp of the membership snapshot from entry into the included scope.

## Membership reasons and provenance

Permitted reasons describe rule evaluation, for example:

> Present in the frozen tested-gene registry under the declared all-tested rule.

Prohibited reasons include:

- important target;
- low-value gene removed;
- insufficiently druggable;
- clinically irrelevant; or
- unfavorable evidence profile.

Reasons are emitted from controlled templates, not entered as unconstrained scientific interpretation. Every reason resolves to a rule ID, a source artifact ID, a verified SHA256, and a frozen snapshot timestamp.

## Versioning contract

A future universe snapshot uses a content-derived version identifier calculated from the canonical serialization of:

```text
universe definition
        + ordered source artifact IDs and SHA256 hashes
        + canonical membership rules
        + generation script SHA256
```

The recommended identifier form is:

```text
TU-<definition-semver>-<first-16-hex-of-SHA256>
```

The complete SHA256 is recorded in the run manifest. Any change to the definition, source content, membership rules, or generator produces a new version and new artifact. A prior manifest is never overwritten or silently revised.

The future target manifest cannot contain its own SHA256 because doing so would create a circular hash. Its artifact ID and final SHA256 are frozen in the downstream materialization input manifest. Per-row `source_artifact_id` and `source_artifact_sha256` instead identify the artifacts that justify membership.

## Deterministic generation contract

Future membership generation must:

1. validate the universe definition, generator, rules, source artifacts, and hashes;
2. validate unique, nonempty, versioned EnsemblIDs;
3. preserve the declared frozen source order;
4. evaluate the exact rule set without symbol fallback or manual inference;
5. emit exactly one controlled membership state per source entity;
6. preserve every entity, including non-included states;
7. copy only permitted source annotations;
8. serialize canonically and calculate the output SHA256;
9. repeat generation and require byte-identical output; and
10. register the manifest as a governed artifact before profile materialization.

Failures stop release. The generator cannot silently drop, add, merge, reorder, repair, or reinterpret entities.

## Interpretation boundaries

Target-universe membership can establish only:

- entity identity in a frozen scope;
- whether a deterministic membership condition resolved;
- why it resolved; and
- the provenance and version of that resolution.

It cannot establish:

- biological importance or causality;
- evidence quality or independence;
- druggability, efficacy, or safety;
- clinical relevance or benefit;
- target ordering or relative merit;
- therapeutic direction; or
- a recommendation to progress a target.

## Frozen inputs and validation

Task #022 uses no external data. It hash-pins and validates:

- `outputs/integrated_registry/integrated_target_registry.csv`;
- `outputs/candidate_registry/candidate_registry.csv`;
- `outputs/evidence_profiles/profile_schema.csv`; and
- `outputs/profile_materialization/profile_builder_contract.md`.

The two registries must retain exactly 29,606 identically ordered, unique EnsemblIDs and matching identity, annotation, U0, U1, and U2 fields. Task #020 must still define EnsemblID as immutable. Task #021 must still require a unique ordered target manifest and prohibit symbol fallback.

The builder verifies the frozen Task #021 base commit is an ancestor of the current HEAD, the named inputs are unchanged relative to that commit, input SHA256 hashes match before and after generation, and no existing tracked file changes.

## Deliberately deferred decisions

Task #022 does not decide:

- whether Universe B uses U1_DE, U2_effect_supported_DE, or a future definition;
- the membership criteria for Universe D;
- which universe should be used for the first materialization campaign;
- whether or when evidence acquisition should expand; or
- how any target should be interpreted scientifically or therapeutically.

These require explicit later scientific questions and must create new versioned artifacts rather than retroactive edits.
