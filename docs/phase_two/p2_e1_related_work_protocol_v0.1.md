# P2-E1 Related Work and Gap Analysis Research Protocol v0.1

**Project:** LUAD Target Evidence Dossier  
**Workstream:** P2-E1 — Related Work and Gap Analysis  
**Version:** v0.1  
**Date:** 3 September 2026  
**Status:** Prospective protocol; searches, screening, capability assessments, and novelty claims not yet executed

## 1. Purpose

This protocol defines how P2-E1 will identify, verify, and compare prior work before the project makes a gap or novelty claim. The study is a structured scoping review plus a version-bounded capability audit. It is designed to answer what existing approaches represent, how directly those capabilities are evidenced, and which narrower problem—if any—remains insufficiently addressed.

P2-E1 evaluates representations and documented system capabilities. It does not evaluate whether a gene is a good target, rank systems, infer therapeutic value, or biologically validate the Phase One framework.

This document contains no related-work findings. Names and categories below define search and verification scope; they do not imply that any system has or lacks a capability.

## 2. Methodological claims being tested

P2-E1 is authorized only to test these claims:

1. whether the literature identifies a recurring need to integrate heterogeneous biomedical target evidence while preserving its interpretation context;
2. whether selected, transparently sampled system families explicitly represent provenance, dependency, missingness, uncertainty or conflict, and claim boundaries;
3. whether those semantics remain present through target-level aggregation or are available only in upstream records or documentation; and
4. whether an evidence-supported, bounded gap can be stated without converting a limited review into a universal absence or priority claim.

The candidate proposition that dependency, missingness, and interpretation boundaries are not consistently represented as first-class objects is a hypothesis, not a finding. It must be narrowed, revised, or rejected according to the resulting evidence.

## 3. Research questions

### RQ1 — Problem and need

What representation problems are reported when heterogeneous biomedical target evidence is combined, summarized, or used downstream?

Subquestions:

- Which evidence states or contextual qualifiers are liable to be lost during integration or aggregation?
- What harms or analytic errors are reported from provenance loss, evidence reuse, dependence, duplicate records, missingness collapse, conflict suppression, or interpretation overreach?
- At what unit are these problems discussed: source, record, dataset, publication, experiment, model, target–disease pair, target profile, or decision output?

### RQ2 — Existing capability

How do eligible systems document and expose the following at the user-visible or machine-readable target-synthesis level?

- entity and identifier semantics;
- evidence-state semantics;
- record- and source-level provenance;
- evidence dependencies and reuse;
- missingness and coverage states;
- uncertainty and conflict;
- transformation and aggregation lineage;
- claim or interpretation boundaries; and
- versioning, traceability, and reproducibility.

### RQ3 — Persistence through synthesis

When a capability exists upstream, is it retained, linked, summarized, or lost in downstream target-level views and exports?

### RQ4 — Bounded gap

Across the explicitly reviewed system universe, which combinations of capabilities are:

- verified as present;
- verified as partially present;
- explicitly unsupported in a bounded version;
- not found in reviewed materials;
- unclear;
- not applicable; or
- not assessed?

What is the narrowest defensible gap statement supported by that distribution and by counterevidence?

### RQ5 — Relationship to the Phase One framework

Which verified distinctions are represented by the Phase One framework, and which are shared with, differ from, or remain untested against prior systems?

This question supports positioning only. It must not be used to declare superiority, biological validity, clinical utility, or target-selection performance.

## 4. Review design and unit of analysis

The study has two linked evidence streams:

1. **Literature stream:** scholarly work used to characterize problems, methods, evaluations, and historical system descriptions.
2. **Capability-verification stream:** versioned primary system material used to assess current or historical capabilities, including official schemas, data models, documentation, APIs, release notes, repositories, and reproducible interface or export observations.

The streams must not be substituted for one another. A paper can establish what a publication reported at its date; it cannot alone establish the current behavior of a changing platform. Current documentation can establish a documented interface; it cannot establish empirical benefit unless an evaluation supports that claim.

The primary comparison unit is:

```text
(system_id, system_version_or_snapshot, capability_dimension_id, assessed_surface)
```

`assessed_surface` distinguishes at least the underlying data model, ingestible record, user interface, API/export, aggregate target view, and published method. A capability available in one surface must not be imputed to another.

The evidence-extraction unit is one source passage, schema element, observed interface behavior, or evaluated result that supports or challenges one bounded capability statement.

## 5. Literature and system categories

P2-E1 will search the following overlapping categories. Category assignment describes function, not quality or maturity.

1. **Target-evidence integration and target-prioritization frameworks** — methods or platforms that combine multiple evidence types at target or target–disease level.
2. **Open Targets** — its publications and versioned first-party platform, schema, API, evidence, association, and scoring documentation. Inclusion here is required by the project brief but does not predetermine any assessment.
3. **Drug–target and biomedical knowledge graphs** — graphs used to integrate biological, disease, drug, experiment, or literature assertions relevant to target-level synthesis.
4. **Biomedical provenance systems and standards** — models or implementations that represent source, derivation, attribution, workflow, record, or entity lineage.
5. **Evidence-synthesis and evidence-assessment systems** — systematic-review, evidence-grading, living-review, or structured evidence tools with relevant handling of provenance, dependence, missingness, uncertainty, or claim scope.
6. **Missingness, uncertainty, conflict, and evidence-dependence methods** — methodological work that provides usable semantics for absent observations, coverage, correlated evidence, reuse, duplication, or contradictory findings.
7. **AI-assisted target-discovery systems** — systems that use machine learning, language models, or other AI to integrate or interpret target evidence and expose enough methods or outputs for capability verification.

A work may belong to multiple categories. Category counts are descriptive and must not be treated as independent evidence counts.

## 6. Search concepts

Searches will combine one or more terms from each relevant concept block. Exact syntax will be translated per database and preserved verbatim in the search log.

### A. Target and decision context

`drug target`, `therapeutic target`, `target identification`, `target discovery`, `target validation`, `target prioritization`, `target evidence`, `target-disease association`

### B. Integration or synthesis

`evidence integration`, `data integration`, `evidence synthesis`, `multi-omics`, `heterogeneous evidence`, `knowledge graph`, `knowledge base`, `evidence graph`, `data fusion`, `aggregation`

### C. Representation properties

`provenance`, `lineage`, `source attribution`, `dependency`, `dependence`, `reuse`, `duplicate`, `non-independent`, `missingness`, `not found`, `not queried`, `coverage`, `uncertainty`, `conflict`, `contradiction`, `traceability`, `auditability`, `claim`, `interpretation boundary`

### D. Computational approach

`machine learning`, `artificial intelligence`, `language model`, `graph neural network`, `target prediction`, `decision support`

### E. Named-system verification

The exact system name plus relevant capability and documentation terms such as `schema`, `data model`, `API`, `evidence`, `provenance`, `release`, `version`, `missing`, `dependency`, `score`, `aggregation`, and `export`.

Search strings must be broad enough to locate counterexamples, not only sources that use the Phase One vocabulary. Pilot searches may add synonyms, but every change must be versioned in the search log and applied consistently to the applicable source.

## 7. Information sources and search workflow

### 7.1 Scholarly discovery

At minimum, execute searches in one biomedical bibliographic database and one multidisciplinary citation database if accessible. Record database name, provider, coverage, exact query, filters, execution timestamp with timezone, result count, export format, and export SHA256.

Use backward and forward citation chasing for included framework papers, major system descriptions, and methodological anchors. Record citation-chasing records as distinct search events. Search relevant preprint sources only when needed to capture emerging AI-assisted systems; preprints remain labelled as non-peer-reviewed.

### 7.2 Grey and first-party literature

Search official system websites, documentation, schemas, API references, release notes, technical reports, model cards, and repositories. First-party materials are mandatory for capability verification. Commercial or marketing pages may identify candidates but cannot, by themselves, verify a technical capability or comparative performance claim.

### 7.3 Search interval and update

Use a default publication interval of 1 January 2010 through the final search date because the review focuses on contemporary computational integration. Include earlier seminal provenance or evidence-synthesis work when discovered through targeted searches or citation chasing, recording the exception basis.

Run a documented update search within 30 calendar days before manuscript submission. A changing platform must also receive a capability refresh at that time or be reported using its older frozen assessment date.

### 7.4 Search freeze

Before screening, freeze:

- every exact query and date;
- exported result files or immutable references;
- result counts and deduplication inputs;
- file hashes;
- software or manual deduplication rule; and
- reviewer assignments.

Search results are prospective P2-E1 evidence artifacts and must not alter frozen Phase One artifacts.

## 8. Eligibility criteria

### 8.1 Include when all applicable criteria hold

- The work or system addresses at least one review category in Section 5.
- It describes a method, data model, implementation, evaluation, or documented capability relevant to at least one comparison dimension.
- The full text, complete technical documentation, schema, or equivalent primary material is accessible to reviewers.
- The version or publication date can be recorded.
- For capability-matrix inclusion, the system exposes enough first-party or directly inspectable material to make at least one non-`NOT_ASSESSED` determination.
- For AI-assisted systems, the material connects AI outputs to target evidence integration or interpretation rather than mentioning AI only incidentally.

### 8.2 Exclude when any applicable criterion holds

- The work solely reports a biological target result without describing an evidence-integration or representation method.
- The work is solely a predictive performance paper with no target-evidence representation, provenance, missingness, dependency, uncertainty, or claim-boundary relevance.
- The item is an editorial, news story, unsourced marketing claim, slide fragment, or inaccessible abstract with insufficient methods.
- It is a duplicate report of the same system version with no additional relevant information; the relationship is recorded rather than silently discarded.
- It concerns clinical validation, therapeutic recommendation, or target ranking only, without informing a P2-E1 representation question.
- The language cannot be reliably reviewed by the available team. Such records receive an explicit language-exclusion code and count.

### 8.3 No outcome-based eligibility

A source must not be excluded because it contradicts the hypothesized gap, reports a strong existing capability, or uses different terminology. Contrary evidence is actively retained.

## 9. System-universe construction

Use two nested universes so that broad evidence mapping is not confused with the deeper capability audit.

### 9.1 Evidence-map universe

Register every system described by an included source and assign all applicable categories. No eligible system is removed from the evidence map because documentation is sparse, access is restricted, or its capabilities challenge the candidate gap.

### 9.2 Capability-audit universe

A system enters the full matrix when all of these outcome-blind conditions hold:

1. it is an implemented or released system rather than only a proposed conceptual method;
2. it produces or exposes target-, target–disease-, or evidence-level synthesis relevant to at least one P2-E1 dimension;
3. a product/version boundary or explicit access-date snapshot can be assigned;
4. at least one first-party technical source or directly inspectable released surface is available; and
5. the system can receive at least one non-`NOT_ASSESSED` capability determination.

Open Targets enters the audit universe by prespecification in the project brief but remains subject to the same cell-level evidence rules. Conceptual provenance standards and non-target evidence-synthesis systems may enter a separate reference matrix for relevant dimensions; their cells must not be pooled with implemented target-synthesis systems.

Do not impose an unreported convenience cap. If the eligible audit universe is too large for dual coding, retain all eligible systems for single extraction, define a stratified dual-coded audit sample before capability results are inspected, and disclose the resource constraint. Any narrower system subset used in a manuscript figure must have a prospective, reproducible selection rule and the full matrix must remain available.

Build the universes in this order:

1. populate candidates from database searches, included reviews, citation chasing, expert suggestions recorded before assessment, and named systems in the project brief;
2. apply source and system eligibility criteria without consulting the desired gap conclusion;
3. assign categories and universe disposition with controlled reasons;
4. freeze the audit universe before full capability coding; and
5. record later discoveries as update-search additions rather than silently changing the denominator.

The report must state exact denominators for both universes and each category, and must not generalize beyond them. If one system has multiple materially different products or releases, create separate versioned assessments or explicitly bound the assessed surface.

## 10. Screening and reviewer process

### 10.1 Deduplication

Deduplicate scholarly records using persistent identifiers first, then normalized title, year, and first author. Preserve links among preprint, conference, journal, correction, retraction, and versioned reports. Prefer the most complete version for extraction while retaining the lineage.

### 10.2 Two-stage screening

Two reviewers independently screen:

1. title and abstract or summary; then
2. full text or full technical material.

Before production screening, both reviewers code the same pilot set sampled across categories and refine only ambiguous instructions. Protocol changes receive a new version or amendment; they are not silently applied.

Disagreements are resolved by discussion and, when unresolved, a third adjudicator. Preserve both initial decisions, conflict status, final decision, adjudicator, exclusion reason, and timestamp.

### 10.3 Agreement reporting

Report raw agreement for both stages and Cohen's kappa when category prevalence and sample size make it interpretable. Agreement metrics describe screening reproducibility, not literature quality or framework correctness.

## 11. Data extraction

Use the templates under `docs/phase_two/p2_e1_templates/`. Extraction is performed at three linked levels:

- **system registry:** system identity, family, scope, versions, and assessed surfaces;
- **source registry:** bibliographic or technical source identity, type, status, version/date, URL or persistent identifier, capture date, and immutable local reference or hash;
- **capability evidence ledger:** atomic evidence for or against one capability determination, with exact location, evidence type, reviewer, and interpretive note.

Each source receives a stable `source_id`; each system/version receives a stable `system_assessment_id`; each atomic evidence item receives a stable `capability_evidence_id`. Free-text notes cannot substitute for these links.

Extract reported evaluations separately from capability descriptions. A system paper's claimed benefit and an independent empirical comparison are different evidence types.

## 12. Capability assessment and matrix

The governed dimensions, assessed surfaces, evidence hierarchy, and controlled cell states are defined in [P2-E1 Comparison Framework and Codebook v0.1](p2_e1_comparison_framework_v0.1.md).

Every capability-matrix cell must contain:

- one system assessment and version/date boundary;
- one capability dimension;
- one assessed surface;
- one controlled state;
- one or more supporting evidence IDs when required;
- reviewer and adjudication state;
- a short bounded rationale; and
- the date last verified.

No composite score, weighted total, rank, star rating, maturity level, or winner is permitted. Counts of verified cells describe documented representation coverage within the reviewed set; they do not measure system quality.

## 13. Absence-of-evidence rules

The following distinctions are mandatory:

- `ABSENT_EXPLICIT` requires direct, version-bounded evidence that the assessed capability is unsupported, excluded, unavailable, or outside the system's documented design. Reviewer failure to locate a feature is insufficient.
- `NOT_FOUND_IN_REVIEWED_MATERIALS` means the prespecified search of eligible materials did not locate evidence. It is not absence of capability.
- `UNCLEAR` means relevant material exists but cannot support a consistent determination.
- `NOT_ASSESSED` means the prespecified assessment was not completed.
- `NOT_APPLICABLE` requires a documented reason tied to the system scope and dimension definition.

Interface observation can verify that a feature was exposed during a captured session, but failure to observe it cannot establish `ABSENT_EXPLICIT`. Lack of a public API does not imply lack of an internal data model. Lack of a visible user-interface field does not imply that provenance is absent from downloadable data, and the converse also holds.

## 14. Version- and date-dependent capabilities

Every system determination is bounded by:

- product or platform name;
- release, API, schema, repository commit, document version, or `VERSION_NOT_DISCLOSED`;
- assessed surface;
- document publication/update date when available;
- reviewer access date and timezone; and
- archived URL, immutable capture, checksum, or repository commit when legally and technically feasible.

Do not combine evidence from different versions into a synthetic current capability. If a capability changes, retain separate assessments or a change record with `valid_from`, `valid_to`, and evidence links. A publication describing an older release receives `HISTORICAL_VERSION`; it does not verify the current release.

If a live platform does not disclose a version, label the result `ACCESS_DATE_SNAPSHOT`, preserve what was observed, and state that future reproducibility is limited.

## 15. Category-specific verification rules

### 15.1 Open Targets

Verify claims against versioned first-party data-model/schema, API/export, evidence and association documentation, and release information, supplemented by platform publications. Keep evidence records, association aggregation, scores, source attribution, and user-interface presentation separate. Confirm whether a property survives into the target-level surface being compared. Do not infer current behavior from a historical paper alone.

### 15.2 Biomedical and drug–target knowledge graphs

Verify using the graph schema or ontology, ingestion/ETL description, provenance model, accessible graph or export, repository/release identity, and primary methods paper where available. Distinguish a source citation on a node or edge from explicit derivation lineage; distinguish multiple edges from independent evidence; and distinguish the theoretical expressivity of the graph formalism from fields actually populated in the released graph.

### 15.3 Evidence-synthesis tools

Verify against current manuals, data models, protocols, exports, and empirical evaluations. Keep source citation, study-level risk of bias, certainty judgments, missing-study methods, missing-field states, and dependence handling distinct. A generic free-text note does not automatically qualify as a first-class structured capability.

### 15.4 AI-assisted target-discovery systems

Verify technical capability using primary methods, model/system documentation, data or model cards, traceable outputs, and versioned product documentation when available. Record whether generated statements link to source records, whether training or retrieval sources are disclosed at an auditable level, whether evidence reuse or dependence is represented, and whether uncertainty or claim scope is explicit. Marketing material may identify a system but cannot verify these properties. Predictive accuracy does not demonstrate provenance or claim-boundary correctness.

### 15.5 Target-prioritization frameworks

Verify input evidence units, aggregation rules, scoring or weighting, treatment of missing inputs, provenance retention, dependency assumptions, output semantics, and validation design from primary methods and implementation materials. A transparent scoring formula is not by itself evidence-dependency modeling, and a source list is not by itself record-level provenance.

### 15.6 Provenance systems and standards

Separate conceptual expressivity, implementation support, and use in target-evidence synthesis. A standard capable of representing derivation does not show that a platform instantiates derivation links in released data.

## 16. Quality and bias controls

For each source, record:

- source type and peer-review status;
- first-party, independent, or secondary relationship to the system;
- version and recency;
- method detail and inspectability;
- declared funding or conflicts when available;
- correction, retraction, or supersession status; and
- which claims the source is permitted to support.

Do not reduce these fields to one quality score. First-party sources are preferred for implementation facts; independent studies are preferred for comparative performance or impact. Review articles support discovery and context but should not be the sole basis of a specific current-platform capability claim.

Bias controls include dual screening, dual capability coding for a stratified sample, prespecified cell-state rules, explicit counterexample searches, retention of conflicting evidence, version-bounded claims, and a claim audit before prose drafting.

## 17. Synthesis plan

### 17.1 Descriptive synthesis

Report:

- search and screening flow;
- included sources and systems by category;
- capability states by dimension, surface, system, and version;
- areas of agreement, divergence, ambiguity, and documentation insufficiency;
- changes across versions when evidenced; and
- counterexamples to each proposed gap statement.

Any proportion must state its numerator, denominator, unit, and sampling boundary. Do not interpret a count of systems as evidence strength or system quality.

### 17.2 Gap-statement ladder

Draft conclusions from weakest to strongest:

1. **Observation:** describe verified matrix results for named systems/versions.
2. **Pattern:** describe a recurring result within an explicit reviewed denominator.
3. **Bounded gap:** state which combination of semantics was not found or was only partly verified in that reviewed universe.
4. **Novelty:** use `novel`, `first`, `unique`, or universal absence language only if the search scope can support it, all apparent counterexamples have been resolved, and the claim passes independent audit.

Default wording is bounded: “Among the systems and versions reviewed…” A result dominated by `NOT_FOUND_IN_REVIEWED_MATERIALS`, `UNCLEAR`, or `NOT_ASSESSED` supports a documentation-gap conclusion, not a capability-absence conclusion.

### 17.3 Comparison with this project

Map Phase One semantics using the same dimensions and evidence rules, citing frozen project artifacts. Do not give the home framework preferential interpretations. If a capability is only specified but not materialized, code the corresponding assessed surface accordingly. Artifact validation remains distinct from biological validation.

## 18. Claim ledger and wording controls

Every manuscript-relevant claim must have a claim-ledger row containing:

- exact proposed claim text;
- claim type and scope;
- supporting evidence IDs;
- challenging or counterexample evidence IDs;
- system/version denominator where applicable;
- allowed wording strength;
- unresolved limitations;
- reviewer and adjudication status; and
- final disposition: retained, narrowed, rejected, or pending.

The following are prohibited without direct evidence and scope qualification:

- “no existing system”;
- “existing approaches ignore”;
- “the first framework”;
- “solves evidence integration”;
- “more accurate,” “better,” or “superior” without a matched empirical evaluation;
- claims that representation correctness establishes biological or clinical validity.

## 19. Validation criteria

### 19.1 Protocol readiness gate

Before searches begin, confirm:

- research questions map to comparison dimensions and planned outputs;
- inclusion/exclusion rules can be applied without knowing the desired conclusion;
- every controlled matrix state has an operational rule;
- every template key and cross-reference is defined;
- the platform version/date policy is executable;
- category-specific verification rules identify acceptable primary evidence;
- counterevidence and unresolved evidence have explicit storage paths; and
- no Phase One artifact is designated for modification.

### 19.2 Pilot gate

Before full screening and coding:

- dual-screen a stratified pilot set;
- dual-code at least two systems from different categories across all applicable dimensions;
- document ambiguities and amend the protocol/codebook if required;
- verify that every non-`NOT_ASSESSED` cell can be reconstructed from the evidence ledger; and
- freeze the amended protocol, templates, reviewer guidance, and search exports.

### 19.3 Final evidence-integrity gate

The completed P2-E1 package must satisfy:

- all search events have exact queries, dates, result counts, and immutable export references;
- all screened records have both initial decisions and a final disposition;
- every full-text exclusion has one controlled reason;
- every included system has an identity, category, scope, assessed surface, and version/date boundary;
- every matrix cell uses a controlled state;
- every `PRESENT_VERIFIED`, `PARTIAL_VERIFIED`, and `ABSENT_EXPLICIT` cell has qualifying evidence;
- every `NOT_FOUND_IN_REVIEWED_MATERIALS`, `UNCLEAR`, `NOT_APPLICABLE`, and `NOT_ASSESSED` cell carries the required rationale;
- all current-platform claims use current first-party evidence or are explicitly labelled historical/access-date bounded;
- all proposed gap statements include counterexample searches and explicit denominators;
- a second reviewer audits all high-strength gap/novelty claims and a stratified sample of remaining cells;
- unresolved conflicts remain visible; and
- the narrative contains no target ranking, therapeutic recommendation, clinical validation, or inference that evidence count equals evidence strength.

## 20. Planned P2-E1 artifacts

Protocol-stage artifacts created now:

1. `docs/phase_two/p2_e1_related_work_protocol_v0.1.md` — this prospective protocol.
2. `docs/phase_two/p2_e1_comparison_framework_v0.1.md` — capability dimensions, surfaces, state codebook, and evidence rules.
3. `docs/phase_two/p2_e1_templates/search_log_template.csv`.
4. `docs/phase_two/p2_e1_templates/screening_ledger_template.csv`.
5. `docs/phase_two/p2_e1_templates/system_registry_template.csv`.
6. `docs/phase_two/p2_e1_templates/source_registry_template.csv`.
7. `docs/phase_two/p2_e1_templates/capability_evidence_ledger_template.csv`.
8. `docs/phase_two/p2_e1_templates/capability_matrix_template.csv`.
9. `docs/phase_two/p2_e1_templates/claim_ledger_template.csv`.

Execution-stage artifacts to be created only after protocol approval and search execution:

1. `outputs/phase_two/p2_e1_v0.1/search/` — query logs, exports or governed external references, hashes, and deduplication report.
2. `outputs/phase_two/p2_e1_v0.1/screening/screening_ledger.csv` and screening-flow summary.
3. `outputs/phase_two/p2_e1_v0.1/extraction/system_registry.csv`, `source_registry.csv`, and `capability_evidence_ledger.csv`.
4. `outputs/phase_two/p2_e1_v0.1/synthesis/capability_matrix.csv`, `claim_ledger.csv`, and category-level descriptive tables.
5. `outputs/phase_two/p2_e1_v0.1/related_work_gap_analysis.md` — evidence-linked narrative findings.
6. `outputs/phase_two/p2_e1_v0.1/validation_report.md` and `session_info.txt` — protocol conformance, dates, versions, hashes, agreement results, amendments, and limitations.

The version label will be advanced if the protocol changes materially after piloting. Execution artifacts must identify the exact protocol and codebook version used.

## 21. Exact execution workflow

1. Approve or amend this protocol and the comparison codebook.
2. Assign stable reviewer and adjudicator IDs; pilot the screening and coding instructions.
3. Translate concept blocks into source-specific queries; peer-check each translation before execution.
4. Execute and freeze scholarly searches and first-party documentation searches in the search log.
5. Deduplicate while preserving publication and version lineage.
6. Conduct independent title/abstract and full-text screening; adjudicate disagreements.
7. Construct and freeze the stratified system universe with documented inclusion reasons.
8. Register sources and system versions before capability judgment.
9. Extract atomic capability evidence with exact locations and evidence relationships.
10. Independently code the prespecified audit sample; adjudicate and update only through governed amendments.
11. Materialize the full capability matrix without composite scores or rankings.
12. Search specifically for counterexamples to each emerging gap statement.
13. Draft the claim ledger before drafting the related-work narrative.
14. Run the final evidence-integrity gate and independent high-strength-claim audit.
15. Write the bounded gap analysis, reporting unresolved and contrary evidence.
16. Re-run the update search and mutable-platform refresh before manuscript submission.

## 22. Interpretation boundaries

P2-E1 can establish what a bounded set of sources and system versions documents or exposes. It cannot establish that undocumented capabilities do not exist internally, that a representation is used correctly in practice, that richer representation improves biological discovery, or that the Phase One framework is novel, superior, clinically valid, or therapeutically useful. Those claims require different evidence and, where applicable, later Phase Two evaluations.
