# Profile Release Policy v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Version:** v0.1  
**Status:** Frozen governance specification

## 1. Purpose

This policy defines the evidence, validation, provenance, versioning, and publication gates for a Target Evidence Profile release. A release is an immutable collection of profiles governed under one lifecycle state.

Release approval verifies representation and reproducibility. It does not validate targets and must not introduce scoring, ranking, target prioritization, therapeutic recommendation, candidate selection, or biological interpretation.

## 2. Release identity

Every release must have:

- immutable release identifier;
- lifecycle state;
- target-universe identifier and deterministic order;
- `schema_version`;
- `profile_version`;
- `evidence_snapshot_version`;
- included component identifiers and component-definition versions;
- state-rule, extractor, and generator versions;
- input and output artifact identifiers, sizes, and SHA256 hashes;
- immutable storage references for externally governed artifacts;
- validation and scientific-review records;
- limitations and unresolved issues.

Release identity must not depend on gene symbols, wall-clock-generated row identifiers, randomness, target scores, rankings, or AI decisions.

## 3. Version separation policy

The release manifest must store schema, profile, and evidence-snapshot versions as separate required fields:

- `schema_version` defines representation and machine validation.
- `profile_version` defines component assembly and profile semantics.
- `evidence_snapshot_version` defines the frozen evidence contents and source releases.

Component-definition, rule, extractor, and generator versions must also remain independently traceable. A release must fail validation if any required version is missing, ambiguous, or replaced by one generic project version.

## 4. Required release artifacts

At minimum, a governed release must provide or reference:

1. profile schema;
2. profile payload or governed external artifact;
3. release manifest;
4. complete profile-to-feature and feature-to-record provenance;
5. component definitions and executable state-rule versions;
6. input evidence manifest and source versions;
7. validation report;
8. lifecycle and scientific-review record appropriate to the declared state;
9. session/environment record sufficient for regeneration;
10. checksums and immutable storage references for every external artifact;
11. interpretation boundaries, known limitations, and unresolved conflicts.

Summaries and counts cannot replace the complete profile or provenance artifacts.

## 5. Release gates

### Gate A — Identity and schema

- Every profile has one immutable `EnsemblID`.
- Profile IDs regenerate deterministically from governed identity fields.
- Profile count, target universe, and ordering match the release manifest.
- The payload validates against the exact declared schema.
- No undeclared fields are present.

### Gate B — Feature and component fidelity

- Every included component is registered and versioned.
- Every feature value is identical to its frozen normalized source or follows an explicitly registered deterministic transformation.
- Feature data types and controlled vocabularies match their dictionary.
- Component states reproduce under the exact executable rules and precedence.
- Component and rule review statuses satisfy the lifecycle destination.

### Gate C — Provenance and dependency

- Every feature has complete, uncompressed record-level provenance.
- Every `(feature_id, evidence_record_id)` relationship is unique.
- Claim, record, source, artifact, dependency, extraction-rule, extractor, and generator references resolve.
- Dependent records remain labelled as dependent and are not counted as independent votes.
- Large provenance artifacts satisfy their external artifact governance contract.

### Gate D — Missingness and uncertainty

- `OBSERVED`, `NOT_FOUND`, `NOT_QUERIED`, `NOT_APPLICABLE`, and `UNKNOWN` remain distinct.
- Missing evidence is not converted to negative evidence.
- `NOT_QUERIED` is not presented as biological absence.
- Conflicts and unresolved uncertainty are retained rather than silently resolved.
- Applicable missingness and state-boundary fixtures pass.

### Gate E — Determinism and reproducibility

- Identical frozen inputs, schemas, rules, and generator versions produce byte-identical outputs.
- Input and output SHA256 hashes and sizes match the manifest.
- External storage references retrieve exact hash-matching artifacts.
- No wall-clock value, randomness, network-dependent mutable response, manual edit, or AI runtime decision changes a governed profile value or state.
- Regeneration instructions and environment requirements are documented.

### Gate F — Interpretation safety

- No score, rank, priority, confidence metric, target prioritization, candidate selection, therapeutic recommendation, or biological interpretation appears in profile artifacts.
- Structural states are not presented as ordinal quality levels.
- Profile or component completeness is not presented as target quality.
- Evidence-record counts are labelled as audit metadata only.
- Scientific claims do not exceed the evidence and profile interpretation boundaries.

### Gate G — Lifecycle authorization

- All requirements for the declared lifecycle state have passed.
- Required technical and scientific reviewers are recorded.
- No lifecycle state was skipped.
- Review scope, findings, unresolved issues, and disposition are preserved.
- Promotion was a human governance action and not an AI/LLM runtime decision.

## 6. Lifecycle-specific release policy

| Lifecycle state | Release audience | Minimum gate outcome |
|---|---|---|
| `PILOT_VALIDATION_ONLY` | Architecture and validation reviewers | Gates A–F pass for deterministic pilot scope; limitations and untested paths explicit |
| `INTERNAL_VALIDATION` | Authorized internal reviewers | Gates A–F pass for complete declared internal universe; registered components and boundary fixtures validated |
| `SCIENTIFIC_REVIEWED` | Scientific governance reviewers | Internal gates pass plus independent scientific review of meanings, boundaries, dependencies, and uncertainty |
| `PUBLIC_RELEASE` | Public users | All gates pass; immutable artifacts, external storage references, review records, and public limitations are available |

Passing a release gate does not imply favorable evidence for any target.

## 7. Change, correction, and withdrawal policy

1. Frozen release artifacts are immutable.
2. Corrected evidence or profile bytes require a new evidence snapshot, profile, schema, component, rule, extractor, generator, or release version as appropriate.
3. A superseding release must reference the prior release and explain the governed reason for change without overwriting it.
4. A withdrawal notice must identify the affected release, reason, scope, and replacement if any; the historical manifest and hashes remain traceable.
5. Storage migration without byte changes may update governed storage references while retaining artifact identity and checksum.
6. Release notes cannot retroactively add target scores, rankings, prioritization, therapeutic recommendations, or biological interpretations to a profile release.

## 8. Current Task #027 disposition

Task #027 is a `PILOT_VALIDATION_ONLY` artifact. It demonstrated deterministic ten-profile materialization for `COMP_TRANSCRIPTOMIC_EVIDENCE`, exact feature fidelity, uncompressed provenance, and byte-identical regeneration.

It is not eligible for a higher lifecycle state yet because:

- only a deterministic ten-entity pilot was materialized;
- only the transcriptomic component exists;
- `MISSING`, `NOT_QUERIED`, and `PARTIAL` profile paths were not exercised;
- Task #025 rules remain `AWAITING_INDEPENDENT_SCIENTIFIC_REVIEW`;
- the Task #026 provenance artifact's concrete external storage reference remains pending.

## 9. Release validation checklist

- [ ] Immutable release, target-universe, and profile identities are declared.
- [ ] Lifecycle state is declared and its entry requirements pass.
- [ ] Schema, profile, evidence-snapshot, component, rule, extractor, and generator versions are separate and exact.
- [ ] All required artifacts exist or have immutable resolvable storage references.
- [ ] Artifact sizes and SHA256 hashes match the manifest.
- [ ] Schema and cardinality checks pass.
- [ ] Every feature value matches its governed normalized source.
- [ ] Every feature has complete uncompressed provenance.
- [ ] Composite provenance keys are unique and all foreign keys resolve.
- [ ] Dependency relationships and controlled missingness are preserved.
- [ ] State rules reproduce deterministically and have the required review status.
- [ ] Identical frozen inputs regenerate byte-identical outputs.
- [ ] No score, ranking, target prioritization, recommendation, candidate selection, biological interpretation, or hidden aggregation exists.
- [ ] No AI or LLM runtime decision contributed to profiles, states, validation, or promotion.
- [ ] Limitations, conflicts, untested paths, and unresolved issues are explicit.
- [ ] Required human technical and scientific review records are complete.

