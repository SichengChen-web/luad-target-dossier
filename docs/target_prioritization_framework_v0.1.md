# Target Prioritization Philosophy and Decision Framework v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Task:** #015 — target prioritization philosophy and decision framework  
**Version:** v0.1  
**Date:** 21 August 2026  
**Status:** Decision-framework specification; no prioritization implemented

## 1. Purpose and scope

Target prioritization is not a single context-free question. The evidence that matters, the interpretation of missing data, and the acceptable uncertainty all depend on the decision being supported.

This framework defines how future analyses should interpret, aggregate, and communicate evidence. It does not rank targets, calculate target scores, select genes, or make therapeutic recommendations.

The framework builds on the existing project architecture:

- Task #012 provides a one-gene-per-row integrated evidence registry;
- Task #013 defines evidence domains, source lineage, and qualitative dependencies;
- Task #014 represents bounded claims, traceable evidence records, source entities, dependency edges, missingness, and uncertainty.

Those structures make evidence auditable. They do not, by themselves, determine which target should progress.

## 2. Purpose of prioritization: decision contexts

Future work must state its decision context before comparing target evidence. Results produced for one context must not be presented as a universal ordering.

### A. Biological discovery prioritization

**Decision question:** Which genes have strong evidence of involvement in LUAD biology?

Relevant evidence domains and concepts include:

- transcriptomic discovery;
- robustness of the expression result across prespecified analyses;
- LUAD disease association;
- genetic or other mechanistic evidence when available;
- functional-dependency or perturbational evidence when available.

This context asks whether a gene is plausibly involved in disease biology. It does not ask whether the gene can be modulated with a therapeutic modality.

A biologically important gene may be difficult to drug. Conversely, a tractable protein may have weak evidence of being important to LUAD. Biological relevance and druggability must therefore remain separate assessments.

Current boundary: the project has transcriptomic and Open Targets disease-association evidence, but dedicated genetic and functional-dependency layers remain future-compatible. Their absence is an evidence gap, not evidence that a gene lacks a causal or functional role.

### B. Therapeutic development opportunity

**Decision question:** Which genes show evidence compatible with future drug development?

Relevant evidence domains and concepts include:

- tractability by specific modalities;
- source-grounded pharmacology;
- compound–target and mechanism evidence when available;
- clinical-development evidence when available;
- technical feasibility and modality fit.

This context asks whether a target could plausibly be modulated and whether development precedent exists. It does not establish that modulating the target would benefit patients or that the target is biologically central to LUAD.

Drug or candidate records demonstrate activity, annotation, or development precedent only to the extent supported by their source records. They do not prove disease causality, therapeutic efficacy, or superiority over another target.

Current boundary: the project contains Open Targets drug/candidate summaries, ChEMBL target annotations, and source-native tractability assessments. It does not yet contain a complete compound-activity, potency, mechanism, or trial-level clinical-development layer.

### C. Translational risk assessment

**Decision question:** What factors may limit successful therapeutic development?

Relevant evidence domains and concepts include:

- target safety liabilities;
- expression or function in normal tissues;
- essentiality and loss-of-function tolerance;
- toxicity evidence;
- on-target versus compound-specific adverse effects;
- uncertainty and incomplete safety coverage.

This context identifies possible limitations, unanswered questions, and evidence conflicts. It does not reduce safety to a binary label and does not automatically reject a target because a liability is present.

Current boundary: the project contains Open Targets safety-liability evidence states. Dedicated normal-tissue, essentiality, openFDA, and broader toxicity evidence are not yet complete. Missing risk evidence must remain visible rather than being interpreted as low risk.

### Context separation

The three contexts answer different questions:

| Context | Central question | What it must not be confused with |
|---|---|---|
| Biological discovery | Is the gene involved in LUAD biology? | Druggability or clinical readiness |
| Therapeutic development | Can the target plausibly be modulated and developed? | Biological importance or efficacy |
| Translational risk | What could limit development or safe modulation? | A binary safe/unsafe decision |

A target can have a strong profile in one context and an incomplete or concerning profile in another. Future reports must show that structure rather than compressing it into a universal target score.

## 3. Evidence hierarchy

The hierarchy organizes scientific questions; it is not a numerical ladder and does not imply that a later layer is always stronger than an earlier one.

### Layer 1 — Discovery evidence

**Scientific question:** Is there a reproducible signal connecting the gene to LUAD?

Examples include:

- tumour-versus-normal differential expression;
- effect size and direction;
- statistical evidence;
- prespecified sensitivity and robustness diagnostics;
- disease-association records;
- source-grounded literature evidence.

**Interpretation boundary:** Discovery evidence generates and qualifies hypotheses. Differential expression and association do not establish causality, therapeutic direction, or actionability. Multiple statistics calculated from the same cohort remain one related body of evidence rather than independent confirmation.

### Layer 2 — Mechanistic evidence

**Scientific question:** Is there evidence that changing the target influences LUAD-relevant biology rather than merely correlating with it?

Examples include:

- somatic or germline genetic evidence;
- CRISPR or other functional-dependency evidence;
- perturbational experiments;
- pathway and mechanism evidence;
- replication in distinct biological systems;
- direction-of-action evidence.

**Interpretation boundary:** Mechanistic evidence can strengthen a causal hypothesis but remains dependent on experimental context, model validity, dose, direction, and replication. A cell-line dependency does not automatically establish patient benefit, and genetic loss does not necessarily predict pharmacological inhibition.

Current dedicated mechanistic evidence is incomplete. Future profiles must show this gap explicitly.

### Layer 3 — Development evidence

**Scientific question:** Can the target be modulated with a plausible therapeutic modality, and what development precedent exists?

Examples include:

- small-molecule, antibody, PROTAC, or other modality tractability;
- compound–target interactions;
- potency, selectivity, and mechanism of action;
- pharmacological precedent;
- clinical candidates;
- human trials and development phase.

**Interpretation boundary:** Tractability and pharmacological precedent do not establish disease relevance, efficacy, or clinical success. Target annotation is not compound activity. A positive source-native tractability bucket is not a project decision and must not be counted as an independent vote when it shares ChEMBL or clinical-precedence lineage.

### Layer 4 — Risk evidence

**Scientific question:** What evidence suggests biological, safety, or translational limitations, and what important risks remain unknown?

Examples include:

- curated target safety liabilities;
- normal-tissue expression and physiological function;
- essentiality and genetic constraint;
- on-target and compound-related toxicity;
- adverse-event evidence interpreted conservatively;
- evidence conflicts and incomplete coverage.

**Interpretation boundary:** A liability is a reason for investigation, not an automatic rejection rule. Absence of a safety record does not establish safety. Adverse-event associations do not automatically demonstrate target-mediated causality.

## 4. Evidence aggregation principles

### Rule 1 — Evidence records are not independent by default

Records may share:

- biological samples or cohorts;
- source databases;
- publications;
- compounds;
- trials;
- analysis methods;
- upstream aggregators;
- ontology-expanded views of the same evidence.

Different columns, API fields, or output files do not prove independence. Task #013 relationships and Task #014 dependency edges must be reviewed before any aggregation.

### Rule 2 — Aggregate at evidence-domain level, not raw-feature level

Raw fields first describe the state, strength, consistency, and limitations of one evidence domain. They must not each become a separate vote.

Examples:

- logFC, FDR, and S1–S6 stability qualify one transcriptomic discovery domain;
- Open Targets direct and indirect associations are overlapping views within disease association;
- multiple tractability buckets describe modality feasibility within one tractability domain;
- safety-liability record counts describe retrieved safety evidence rather than a safety score.

Domain-level synthesis prevents sources with many fields or records from dominating merely because they expose more data.

### Rule 3 — Consider dependencies before aggregation

Before combining evidence, future analyses must determine whether records are:

- independent under documented assumptions;
- partially dependent;
- derived from the same source;
- unresolved or unknown.

Known dependencies must be retained in the result. Unknown dependencies must remain unknown rather than being assumed independent.

Multiple database records do not necessarily represent multiple independent observations. Several records can describe the same experiment, publication, compound, trial, target mechanism, or upstream evidence event.

### Rule 4 — Convergence matters more than volume

Compatible evidence from genuinely distinct domains and source lineages can increase confidence in a bounded hypothesis. A large number of correlated records from one source does not provide the same convergence.

Convergence must also be scientifically compatible. Expression direction, perturbational effect, pharmacological mechanism, and proposed direction of action may conflict even when each source individually reports evidence.

### Rule 5 — Preserve conflicts and evidence gaps

Aggregation must not erase disagreement, instability, missing data, or source limitations. A future synthesized result must expose which domains support a claim, which conflict, and which remain unobserved.

## 5. Target evidence profile concept

Future outputs should be context-specific target evidence profiles rather than universal target scores.

A target evidence profile should contain:

### Discovery evidence

- expression effect, direction, and statistical evidence;
- robustness across prespecified analyses;
- disease-association evidence;
- limitations such as tumour heterogeneity and association–causation ambiguity.

### Mechanistic evidence

- genetic evidence;
- functional dependency;
- perturbational or causal evidence;
- direction-of-action coherence;
- replication and model context.

### Development evidence

- modality-specific tractability;
- pharmacology and mechanism;
- compound or biologic precedent;
- clinical-development state;
- dependency or overlap with other development records.

### Risk evidence

- safety liabilities;
- normal-tissue context;
- essentiality and physiological function;
- toxicity evidence;
- unresolved risk questions.

### Cross-cutting information

- uncertainty categories;
- missing evidence and why it is missing;
- conflicting records;
- source versions and provenance;
- record dependencies;
- retrieval timestamps;
- claim and record identifiers.

Profiles should state bounded conclusions such as “LUAD association evidence was retrieved” or “small-molecule tractability assessments were present.” They must not silently convert those observations into “good target,” “safe target,” “should inhibit,” or “best candidate.”

## 6. Missingness and uncertainty

### Missing evidence is not negative evidence

The project distinguishes source observations from evidence gaps.

Examples:

- no safety-liability record does not imply safety;
- no functional-dependency data does not imply that the target is nonessential;
- no clinical trial does not imply lack of therapeutic potential;
- no compound record does not prove that the target is undruggable;
- no association returned by one database does not prove absence of disease relevance.

The Task #014 missingness states must remain explicit:

| State | Meaning for interpretation |
|---|---|
| `OBSERVED` | The defined analysis or retrieval produced the represented record/state |
| `NOT_FOUND` | A defined query returned no corresponding record; not negative biological evidence |
| `NOT_QUERIED` | The query was not performed or could not be performed |
| `NOT_APPLICABLE` | The evidence concept does not apply to that entity |
| `UNKNOWN` | Required lineage or state remains unresolved |

### Uncertainty categories

Future evidence profiles must expose the existing controlled categories:

- **Source limitation:** the evidence source answers only a bounded question or has known design limitations.
- **Incomplete coverage:** public data, identifier mapping, literature, trials, or safety surveillance may omit relevant evidence.
- **Conflicting evidence:** prespecified records or analyses disagree and the conflict must remain visible.
- **Dependency uncertainty:** overlap between sources or records is possible but unresolved.
- **Temporal uncertainty:** an evolving database, trial, or evidence base may change after the recorded release.

Uncertainty must be communicated qualitatively and with provenance. It must not be hidden inside an unexplained numerical adjustment.

## 7. Constraints on any future scoring system

No scoring system is implemented by this document. If one is proposed later, it must satisfy all of the following requirements.

### Decision context

- Define the concrete decision being supported.
- Specify the population, disease context, modality assumptions, and intended user.
- Avoid presenting a context-specific model as a universal target ranking.

### Domain-level design

- Aggregate evidence domains rather than summing raw columns or record counts.
- Define how within-domain conflicts, missingness, and source-native evidence states are represented.
- Prevent a database with many correlated fields from receiving disproportionate influence.

### Provenance and dependency

- Preserve claim, record, source, release, and retrieval provenance.
- Apply the Task #013 independence framework and Task #014 dependency graph.
- Deduplicate shared publications, datasets, compounds, trials, and upstream database records where possible.
- Keep unresolved overlap explicit.

### Uncertainty and validation

- Expose uncertainty and missing evidence in every result.
- Avoid false precision unsupported by the evidence.
- Store all assumptions and parameters in a version-controlled configuration.
- Use a deterministic and reproducible implementation.
- Perform sensitivity analysis, evidence-source ablation, control evaluation, and stability reporting before scientific use.

### Explicit prohibitions

A future system must not use:

- a universal target score across incompatible decision contexts;
- hidden or unexplained weights;
- unexplained rankings;
- raw evidence counting as a proxy for confidence;
- missing evidence as a negative value by default;
- duplicated or correlated records as independent support;
- an LLM to assign arbitrary numerical scores.

Any numerical model must be presented as a decision aid under explicit assumptions, not as ground truth.

## 8. Interpretation boundaries

The following boundaries apply to all future evidence profiles and decision analyses.

### Differential expression

Differential expression is a candidate-generation and discovery signal. It does not prove disease causality, essentiality, therapeutic direction, or benefit from target modulation.

### Disease association

A disease-association record supports a bounded association claim. It does not necessarily identify the causal mechanism or establish that the target is therapeutically actionable.

### Drug and pharmacology evidence

Drug, candidate, or ChEMBL annotation evidence does not prove target validity, LUAD relevance, clinical efficacy, or acceptable selectivity. Target availability is not equivalent to pharmacological activity.

### Tractability

Tractability indicates source-derived evidence relevant to a modality. It does not prove that modulation is biologically appropriate, safe, developable in the intended context, or likely to succeed clinically.

### Clinical development

Clinical investigation demonstrates translational precedent, not target validation or successful efficacy. Trial count and development phase must not become automatic measures of target quality.

### Safety

Presence of a safety liability does not automatically reject a target. Absence of a safety record does not prove safety. Safety evidence must retain source, biological context, exposure, direction, and uncertainty.

### Direction of action

Expression direction alone does not determine whether a target should be inhibited or activated. Direction requires compatible functional, perturbational, genetic, pharmacological, and mechanistic evidence.

## 9. Communication requirements

Future target reports should:

- identify the decision context prominently;
- organize evidence by the four layers and Task #013 domains;
- distinguish observed, missing, conflicting, and uncertain evidence;
- link claims to Task #014 record and source identifiers;
- disclose known and unresolved dependencies;
- separate source-native metrics from project-defined interpretations;
- state what the evidence does not establish;
- avoid recommendation language unless a separately authorized decision process exists.

An appropriate conclusion describes an evidence profile and its limitations. It does not claim that computational evidence definitively validates a therapeutic target.

## 10. Current project decision state

The project now has the architecture required to describe evidence consistently and audit its lineage. It does not yet have an authorized target-prioritization model.

Before any future ranking or scoring work begins, a new versioned specification must define:

- the precise decision context;
- which evidence domains are in scope;
- minimum evidence requirements;
- dependency-handling rules;
- uncertainty and missingness treatment;
- interpretation of conflicts;
- validation controls;
- sensitivity analyses;
- reporting language and non-claims.

Until those decisions are reviewed and frozen, the scientifically appropriate output is a target evidence profile—not a universal score or ranking.
