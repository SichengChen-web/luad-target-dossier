# Disease Association Component Validation Plan v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Version:** v0.1  
**Component:** `COMP_DISEASE_ASSOCIATION`  
**Status:** Prospective validation plan; no retrieval or materialization authorized

## 1. Purpose

This plan defines how a future implementation of the disease-association component must be validated before scoped materialization.

Validation concerns infrastructure fidelity only. It does not validate disease biology, target importance, therapeutic relevance, target suitability, or evidence strength.

## 2. Current validation disposition

This Task #032B-1 registration can undergo documentation validation only.

The following do not yet exist and therefore cannot be operationally validated:

- frozen disease-context ontology identity;
- authorized sources and source versions;
- source snapshot;
- machine-readable component schema;
- extractor and extraction rules;
- executable state-rule registry;
- component generator;
- generated component or profile artifacts.

No external retrieval may be performed to fill these gaps in this task.

## 3. Prospective validation phases

### Phase A — Registration validation

Validate the four Task #032B-1 documents for:

- exact component identity;
- one bounded observation question;
- Task #032A terminology compatibility;
- immutable `EnsemblID` binding;
- evidence record unit and source roles;
- feature, provenance, dependency, missingness, and state contracts;
- explicit unassigned version blockers;
- interpretation boundaries;
- statement that registration does not authorize retrieval.

Phase A produces documentation findings only and no evidence artifact.

### Phase B — Schema and synthetic-fixture validation

After separate review authorizes implementation, validate a machine-readable schema and deterministic rules using version-controlled synthetic structural fixtures. Fixtures must not require network access or live source data.

Required fixture families:

- identity and disease-context mapping;
- each source role and record granularity;
- record availability and duplicate reconciliation;
- all five feature-missingness values;
- all five component states and precedence overlaps;
- complete, incomplete, broken, and ambiguous provenance;
- dependent, partially dependent, unknown, affirmatively independent, and not-applicable relationships;
- prohibited-field rejection;
- malformed and undeclared field rejection;
- byte-identical repeat generation.

Phase B does not authorize real evidence retrieval or profile release.

### Phase C — Frozen-source pilot validation

Only after a separate task authorizes retrieval and freezes an immutable source snapshot may a deterministic pilot be validated.

The pilot selection rule must be structural and deterministic. It must not manually choose famous genes, disease drivers, high-association records, or promising targets.

Required outcomes:

- source and query provenance reconciliation;
- exact target and disease identity mapping;
- raw-to-normalized feature fidelity;
- record-level lineage and dependency preservation;
- state and missingness reproduction;
- no evaluative output;
- byte-identical regeneration;
- preserved frozen input hashes.

### Phase D — Full-universe readiness validation

Before full profile materialization, validate:

- exact 29,606-entity universe and canonical order when that frozen universe is the declared target;
- one component instance per immutable `EnsemblID`;
- exact source-snapshot identity;
- partition and manifest design;
- complete record-level provenance;
- dependency-graph reconciliation;
- missingness and state distributions as audit metadata only;
- full deterministic regeneration;
- artifact governance and lifecycle gate.

Passing Phase D does not scientifically validate any target or automatically promote a profile release.

## 4. Identity validation

Assert:

- `component_id = COMP_DISEASE_ASSOCIATION`;
- `component_version = COMP_DISEASE_ASSOCIATION_V0.1`;
- serialized `component_definition_version` equals `component_version`;
- exact immutable `EnsemblID` is the only entity join key;
- exact disease-context ID and ontology version are frozen before any source record is accepted;
- source target and disease identifiers remain preserved;
- no symbol-based join or manual mapping occurs;
- one component-instance identity is unique within a source snapshot.

## 5. Evidence-record and source-role validation

For every normalized record, verify:

- one immutable raw record or artifact reference exists;
- source-native record identity is stable or deterministically derived;
- record granularity is one of `SOURCE_ATOMIC`, `SOURCE_AGGREGATE`, `MIXED`, `UNKNOWN`;
- source role is registered;
- aggregate records are not decomposed into apparent independent records;
- duplicates do not create additional apparent observations;
- conflicting payloads under one source identity are not silently merged;
- no source-native association metric becomes an evaluative normalized feature.

## 6. Feature validation

For every proposed feature, verify:

- stable feature ID and name;
- declared data type and controlled vocabulary;
- deterministic value from frozen source records;
- declared state-input status;
- exact feature-level missingness;
- required provenance relationships;
- correct role and cardinality;
- no undeclared feature;
- no score, weight, rank, confidence, importance, quality, causal, or therapeutic field.

Set-valued fields must use a frozen canonical order. Counts must reconcile distinct record identities and remain labelled as audit metadata only.

## 7. State validation

Validate exactly:

- `OBSERVED`;
- `PARTIAL`;
- `CONFLICTING`;
- `MISSING`;
- `NOT_QUERIED`.

Required tests:

1. one base fixture for each state;
2. `CONFLICTING` precedence over every lower state;
3. `OBSERVED` precedence over `MISSING`, `PARTIAL`, and `NOT_QUERIED` where malformed overlap is intentionally tested;
4. `MISSING` precedence over `PARTIAL` and `NOT_QUERIED`;
5. `PARTIAL` precedence over `NOT_QUERIED`;
6. no-match and multiple-invalid-input failure paths;
7. structural conflict limited to registered identity, mapping, payload, role, and provenance conditions;
8. exact state preservation in future profile and evidence-landscape projections.

Runtime state selection must use a versioned executable evaluator. Human or LLM state assignment is prohibited.

## 8. Missingness validation

Validate exactly:

- `OBSERVED`;
- `NOT_FOUND`;
- `NOT_QUERIED`;
- `NOT_APPLICABLE`;
- `UNKNOWN`.

Required boundary tests confirm:

- completed in-scope query with no returned records can retain `NOT_FOUND` without becoming negative evidence;
- an unattempted query remains `NOT_QUERIED`;
- deterministic non-applicability remains `NOT_APPLICABLE`;
- unresolved retrieval, parsing, mapping, or coverage remains `UNKNOWN`;
- blank strings, empty lists, zero, and false do not silently replace missingness;
- component state `MISSING` remains distinct from feature missingness.

## 9. Provenance validation

For every feature-to-record relationship, resolve and verify:

- `feature_id`;
- `claim_id`;
- `evidence_record_id`;
- `source_id` and source version;
- `artifact_id`, size, and SHA256;
- `dependency_id` or controlled sentinel;
- `extraction_rule_id`;
- `extractor_version`;
- component, schema, source-snapshot, state-rule, and generator versions;
- query record and disease/target mapping records where applicable.

Assert uniqueness of `(feature_id, evidence_record_id)`. A feature without required lineage fails validation. Counts and summaries cannot substitute for record relationships.

## 10. Dependency validation

Required fixtures cover:

- `SAME_SOURCE / DEPENDENT`;
- `SHARED_DATASET / DEPENDENT`;
- `PARTIAL / PARTIALLY_DEPENDENT`;
- `UNKNOWN / UNKNOWN`;
- affirmatively documented `INDEPENDENT / INDEPENDENT`;
- `NOT_APPLICABLE / NOT_APPLICABLE`;
- invalid type-level combinations;
- unresolved members and duplicate members;
- cross-source records sharing an upstream record or dataset.

Assert that:

- dependency members resolve to records;
- dependent records are not treated as independent;
- cross-source identity does not imply independence;
- `NOT_APPLICABLE` does not become independent;
- unknown dependence remains unknown;
- profile and landscape representations preserve exact dependency references.

## 11. Determinism validation

Given identical frozen inputs and versions, require:

- byte-identical normalized features;
- byte-identical component objects;
- byte-identical provenance and dependency artifacts;
- byte-identical schemas, indexes, manifests, and reports;
- identical partition assignment and canonical ordering;
- matching artifact sizes and SHA256 hashes.

Prohibit randomness, wall-clock-derived values, mutable network responses during materialization, manual runtime edits, and AI/LLM decisions.

## 12. Interpretation-safety validation

Inspect machine-readable schemas, field names, controlled values, fixtures, reports, and generated objects.

Reject any generated field or conclusion representing:

- association or evidence strength;
- confidence metric;
- target or disease importance;
- causal interpretation;
- target quality, suitability, score, rank, priority, or selection;
- therapeutic relevance, direction, or recommendation;
- biological interpretation;
- runtime AI/LLM judgement.

Governance documents may name these terms only to state prohibitions.

## 13. Compatibility validation

### Task #028

Verify immutable `EnsemblID`, independent version axes, record-level provenance, distinct missingness, non-ordinal component states, deterministic generation, and explicit interpretation boundaries.

### Task #031

Verify future landscape projection can represent:

- `PRESENT_IN_SOURCE_PROFILE` or a separately governed absence status;
- exact component state;
- every feature missingness value;
- every `(feature_id, evidence_record_id, dependency_id)` relationship;
- stable component and profile limitation IDs;
- source profile identity and hash.

### Task #032A

Verify identity naming, component lifecycle, source-snapshot separation, shared state/missingness vocabularies, provenance fields, dependency model, determinism, and prohibited outputs.

## 14. Validation gates

| Gate | Current status | Requirement to pass |
|---|---|---|
| Registration documentation | Ready for static review | All four documents consistent and frozen-context hashes unchanged |
| Disease-context identity | Blocked | Exact ontology ID, version, and mapping policy frozen |
| Source contract | Blocked | Sources, releases, queries, licensing, and snapshot governance separately approved |
| Schema and feature rules | Blocked | Machine-readable schema and deterministic rules reviewed |
| Executable state rules | Blocked | Rule registry and all boundary fixtures pass |
| Extractor and generator | Blocked | Versioned implementations pass deterministic tests |
| Frozen-source pilot | Blocked | Separate retrieval authorization and immutable snapshot exist |
| Full materialization | Blocked | All prior gates pass with human scoped authorization |

## 15. Validation output contract

A future validation report must record:

- validation run and component identities;
- every input and output artifact ID, size, SHA256, and version;
- fixture inventory and results;
- record, provenance, dependency, state, and missingness reconciliation;
- deterministic repeat-generation result;
- interpretation-safety result;
- limitations and unresolved paths;
- technical and scientific review statuses;
- intended profile lifecycle destination;
- human governance disposition.

Automated tests may report facts. They must not authorize retrieval, materialization, or lifecycle promotion.

## 16. Current validation checklist

- [x] Documentation-only scope is explicit.
- [x] No external retrieval is authorized or performed.
- [x] Exact component identity is defined.
- [x] Bounded question, record unit, roles, features, states, missingness, provenance, and dependency requirements are specified.
- [x] Interpretation and evaluation prohibitions are explicit.
- [ ] Disease context and sources are frozen.
- [ ] Machine-readable implementation exists.
- [ ] Fixtures have been executed.
- [ ] A source snapshot exists.
- [ ] Any component or profile has been generated.

## 17. Related documents

- [Disease Association Component Registration v0.1](disease_association_component_registration_v0.1.md)
- [Disease Association Component Scope v0.1](disease_association_component_scope_v0.1.md)
- [Disease Association Component Feature Contract v0.1](disease_association_component_feature_contract_v0.1.md)
- [Component Validation Requirements v0.1](component_validation_requirements_v0.1.md)

