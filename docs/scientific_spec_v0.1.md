# Scientific Spec v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Version:** v0.1  
**Date:** 13 August 2026  
**Status:** Working scientific specification

## 1. Project Objective

Develop a reproducible, evidence-grounded computational workflow that starts from a lung adenocarcinoma (LUAD) transcriptomic signature and prioritizes candidate therapeutic targets by integrating multiple independent lines of drug-discovery evidence.

The system should not merely identify genes that are differentially expressed. It should distinguish between:

1. genes that are strongly supported and actionable therapeutic targets; and
2. genes that are biologically plausible and druggable but relatively under-explored.

Every major conclusion in the final target dossier must be traceable to an identifiable data source.

---

## 2. Primary Research Question

**Among genes differentially expressed in LUAD, which genes have the strongest combined evidence for being therapeutically relevant and actionable drug targets?**

## 3. Secondary Research Question

**Among sufficiently supported and tractable LUAD candidates, which targets appear relatively under-explored and may represent interesting drug-discovery opportunities?**

These are deliberately treated as two related but distinct ranking problems.

---

## 4. Central Scientific Principle

Differential expression is a **candidate-generation signal**, not proof that a gene is a therapeutic target.

A gene may be strongly differentially expressed because it is:

* involved causally in disease biology;
* downstream of another causal process;
* a compensatory response;
* associated with altered tumour-cell composition;
* or otherwise correlated with disease without being therapeutically useful.

Therefore:

**Expression association ≠ disease causality ≠ therapeutic actionability.**

Target prioritization must integrate several complementary evidence dimensions.

---

## 5. Scope

### Disease

Lung adenocarcinoma (LUAD).

### Initial biological input

Tumour-versus-normal transcriptomic data, initially using an open dataset such as TCGA/recount3.

### Candidate-generation method

Differential-expression analysis using limma/voom or an equivalent reproducible workflow.

### External evidence sources

* Open Targets
* ChEMBL
* ClinicalTrials.gov
* openFDA
* Europe PMC

Additional sources may be added later only when they answer a clearly defined scientific question.

---

## 6. Candidate Definition

Candidate targets will initially be generated from statistically and biologically meaningful differential expression between LUAD tumour and normal tissue.

For each gene, the minimum expression record should include:

* gene identifier;
* gene symbol;
* log2 fold change;
* direction of differential expression;
* p-value;
* FDR-adjusted p-value;
* relevant expression-quality information.

Exact thresholds such as:

`FDR < threshold`

and

`|log2FC| > threshold`

will **not be permanently fixed in v0.1**.

They will be selected after inspecting the actual distribution of the LUAD data and will subsequently be versioned.

Candidate generation must also undergo basic quality control and biological sanity checking.

Where feasible, replication or confirmation in an independent dataset should be considered.

---

## 7. Evidence Dimensions

Each candidate will be evaluated across distinct evidence dimensions.

### 7.1 Expression Evidence

Question:

**Is the target consistently and substantially dysregulated in LUAD?**

Initial source:

LUAD transcriptomic analysis.

Important limitation:

Expression alone does not demonstrate causality.

---

### 7.2 Disease-Relevance Evidence

Question:

**How strongly is the target connected to LUAD biology, and what type of evidence supports this connection?**

Primary source:

Open Targets.

Evidence should not be treated as a single undifferentiated number where avoidable.

Relevant evidence types and provenance should be retained.

---

### 7.3 Causal / Mechanistic Support

Question:

**Is there evidence that perturbing the target could influence disease-relevant biology rather than merely correlate with it?**

Possible sources:

* Open Targets evidence;
* Europe PMC;
* perturbational or functional evidence available through relevant databases.

Causal evidence should be distinguished explicitly from associative evidence.

### 7.4 Tractability / Druggability

Question:

**Can the target realistically be modulated using a therapeutic modality?**

Possible evidence includes:

* small-molecule tractability;
* antibody tractability;
* known ligandability;
* existing pharmacological precedent.

Primary sources:

Open Targets and ChEMBL.

Biological importance and druggability must remain distinct concepts.

### 7.5 Existing Pharmacological Evidence

Question:

**Are there compounds known to interact with or modulate the target?**

Primary source:

ChEMBL.

Evidence should eventually distinguish between different qualities of pharmacological evidence rather than treating every compound–target record equally.

Relevant factors may include:

* assay type;
* potency;
* target confidence;
* mechanism of action;
* approved versus experimental compounds.

The exact rules remain to be defined after inspecting real ChEMBL data.

### 7.6 Clinical Development Evidence

Question:

**Has pharmacological modulation of this target or closely related therapeutic strategies reached human clinical investigation?**

Primary source:

ClinicalTrials.gov.

Possible features include:

* number of relevant trials;
* disease relevance of the trial;
* intervention;
* development phase;
* trial status.

Clinical development indicates maturity and translational precedent but does not by itself prove target validity.

### 7.7 Safety Evidence

Question:

**Is there evidence suggesting that modulation of the target may create important on-target or drug-related safety concerns?**

Possible sources:

* Open Targets;
* openFDA;
* published literature.

Safety data must be interpreted conservatively.

Adverse-event report counts must not automatically be interpreted as causal evidence of toxicity.

Safety should therefore initially be represented as structured evidence and flags rather than a simplistic adverse-event count.

### 7.8 Direction of Action

Question:

**Is the observed disease-associated direction compatible with the proposed therapeutic mechanism?**

Example:

`Target upregulated in LUAD`

does **not automatically imply**

`Target should be inhibited`.

Direction-of-action assessment should eventually combine:

* expression direction;
* functional evidence;
* genetic or perturbational evidence where available;
* drug mechanism of action;
* mechanistic literature.

For v0.1, directionality will be recorded explicitly as:

* supportive;
* conflicting;
* unknown.

It will not yet be assigned an arbitrary numerical score.

### 7.9 Under-Exploration / Development Saturation

The project will use **under-exploration** rather than treating “novelty” as synonymous with lack of evidence.

A gene with:

* no publications,
* no drugs,
* no trials

is not automatically an attractive novel target.

Under-exploration becomes interesting only after the target has passed a minimum biological-support and tractability threshold.

Possible indicators include:

* limited relevant clinical development;
* limited mature pharmacology;
* comparatively limited disease-specific literature;
* limited existing therapeutic competition.

The exact quantitative definition will be developed after inspection of real evidence distributions.

---

## 8. Target-Assessment Architecture

The project adopts a modular target-assessment structure inspired by the GOT-IT principle that different scientific questions require different assessment blocks.

### Analyst Agent

Responsibilities:

* expression-data QC;
* differential-expression analysis;
* candidate generation.

It does not decide whether a target is therapeutically viable.

### Evidence Scout Agent

Responsibilities:

* determine which predefined evidence queries are required;
* call database-specific tools;
* collect evidence.

It does not invent evidence.

### Database Clients / Tools

Examples:

* Open Targets client;
* ChEMBL client;
* ClinicalTrials.gov client;
* openFDA client;
* Europe PMC client.

These should be deterministic software components rather than independent LLM judges.

### Evidence Normalizer

Responsibilities:

Convert heterogeneous database responses into a common evidence schema while preserving:

* source;
* source identifier;
* query;
* raw evidence;
* normalized field;
* timestamp/provenance where appropriate.

### Scoring Engine

The numerical ranking algorithm must be:

* deterministic;
* transparent;
* reproducible;
* version-controlled.

LLMs must **not independently assign arbitrary numerical scores**.

The same evidence and scoring configuration must always generate the same numerical result.

### Validator

The Validator evaluates whether the prioritization workflow is trustworthy.

It does not modify scores simply because a result “looks wrong”.

It executes a predefined validation protocol and reports failures, instability and uncertainty.

### Reporter Agent

The Reporter converts validated structured evidence into human-readable target dossiers.

It may summarize and reason over retrieved evidence but must not generate unsupported scientific claims.

Claims should be linked to identifiable evidence records wherever possible.

---

## 9. Ranking Strategy

The system will produce two conceptually distinct rankings.

### Ranking A — Established / Actionable Targets

Purpose:

Identify candidates with strong evidence supporting therapeutic relevance and realistic drug-development potential.

Candidate dimensions include:

* expression support;
* disease relevance;
* mechanistic/causal support;
* tractability;
* pharmacological evidence;
* clinical evidence;
* safety;
* direction-of-action coherence.

### Ranking B — Under-Explored Opportunities

Purpose:

Identify targets that have sufficient biological support and tractability but appear relatively under-developed.

Conceptually:

**Support + tractability + mechanistic plausibility + low development saturation**

rather than:

**lack of evidence = novelty**.

A minimum support threshold will therefore be required before a target can receive a meaningful under-exploration ranking.

---

## 10. Scoring Philosophy

Scientific Spec v0.1 does **not freeze exact numerical weights**.

The initial scoring system should be deliberately simple and interpretable.

Likely approach:

1. transform heterogeneous evidence into predefined normalized features;
2. combine features using a transparent deterministic model;
3. store scoring weights in a versioned configuration;
4. test whether rankings are robust to reasonable changes in weights;
5. revise the score only after validation.

The first scoring implementation will therefore be called:

**Scoring Model v0.1**

and should be treated as a hypothesis rather than ground truth.

Missing evidence must be distinguished from explicit negative evidence.

---

## 11. Validation Framework

Validation is treated as an independent scientific component of the project.

### 11.1 Data / Pipeline Validation

Confirm that:

* the correct target is queried;
* the correct LUAD disease identifier is used;
* API fields are parsed correctly;
* missing data are handled correctly;
* evidence provenance is retained.

---

### 11.2 Expression Validation

Check:

* sample grouping;
* normalization;
* possible batch effects;
* reproducibility of the DE workflow;
* biological plausibility of results.

Where feasible, assess replication using an independent dataset or analysis.

---

### 11.3 Positive-Control Validation

Use established LUAD-relevant actionable targets as positive controls.

The appropriate question is:

**Among known actionable targets that are present in the expression-derived candidate pool, does the prioritization framework tend to rank them appropriately?**

Failure of a known LUAD driver to be differentially expressed does not automatically indicate failure of the prioritization system.

---

### 11.4 Negative-Control Validation

Include weakly related, poorly supported or otherwise appropriate negative/control genes.

The system should distinguish strong supported targets from weak controls rather than simply assigning high scores to most candidates.

---

### 11.5 Weight Sensitivity Analysis

Perturb reasonable scoring weights and determine whether top-ranked targets remain reasonably stable.

Highly unstable rankings should be reported rather than hidden.

---

### 11.6 Evidence-Source Ablation

Repeat ranking while removing individual evidence sources or dimensions.

Examples:

* without Open Targets;
* without ChEMBL;
* without clinical evidence.

This evaluates what each source contributes to prioritization.

---

### 11.7 Evidence Convergence

Greater confidence should be assigned when independent evidence sources converge on a compatible therapeutic hypothesis.

Agreement among multiple correlated records from one database should not automatically be treated as equivalent to independent evidence.

---

### 11.8 Citation / Claim Validation

Every major factual claim in the final dossier should be checked against its underlying evidence record.

Unsupported statements should be:

* removed;
* marked uncertain;
* or explicitly labelled as hypotheses.

An LLM agreeing with another LLM does **not** constitute scientific validation.

---

## 12. GOT-IT Adaptation

The project adapts the GOT-IT logic computationally rather than attempting to reproduce the entire preclinical target-validation framework.

### Critical-Path Questions

Used to determine:

**What must we know before considering a target credible enough to progress?**

Examples:

* Is the observed relationship association or evidence of causation?
* Is the target likely to be safe?
* Is modulation technically feasible?
* Is there meaningful differentiation or unmet opportunity?

### Experimental-Approach Questions → Computational Tasks

In this project, many EAQ-like activities become:

* database queries;
* differential-expression analyses;
* evidence extraction;
* cross-source comparison;
* validation analyses.

### Data-Quality Layer

Every evidence block should additionally ask:

* Where did this evidence come from?
* How reliable is it?
* Is it independent?
* Has it been replicated?
* Are important biases or limitations known?

### Milestones and Go / No-Go Decisions

Evidence collection should be iterative.

If an assessment block reveals insufficient or conflicting evidence, the workflow may return to additional evidence collection rather than forcing progression.

---

## 13. Initial Milestones

### M0 — Scientific specification

Scientific Spec v0.1 documented and version-controlled.

**Status: complete.**

### M1 — Expression Candidate Generation

Produce a reproducible LUAD differential-expression candidate table with basic QC.

### M2 — Single-Source Evidence MVP

For a small number of candidate genes, retrieve and normalize Open Targets evidence.

Goal:

`gene → query → raw evidence → normalized evidence`

must work reproducibly.

### M3 — Multi-Source Evidence Integration

Add ChEMBL and subsequently other justified sources.

### M4 — Scoring Model v0.1

Implement deterministic actionability and under-exploration ranking.

### M5 — Validation

Run positive controls, negative controls, sensitivity analysis and source ablation.

### M6 — Evidence-Grounded Dossier

Generate human-readable, cited target dossiers and a simple dashboard.

---

## 14. Expected Deliverables

The final project should produce:

1. a reproducible LUAD differential-expression candidate list;
2. structured multi-source target evidence;
3. an actionable-target ranking;
4. an under-explored-opportunity ranking;
5. target dossier cards with source grounding;
6. a validation report;
7. version-controlled code and scoring configuration;
8. a demonstration/dashboard suitable for presentation.

---

## 15. Explicit Non-Claims

This computational project will **not** claim that:

* differential expression proves causality;
* a high score proves that a target will succeed clinically;
* lack of previous research proves novelty or therapeutic value;
* adverse-event database associations prove target-mediated toxicity;
* LLM consensus constitutes biological validation;
* computational evidence replaces experimental target validation.

The output is a **prioritization and hypothesis-generation system**, not definitive target validation.

---

## 16. Known Limitations

Important anticipated limitations include:

* association–causation ambiguity;
* tumour heterogeneity;
* possible cell-composition effects in bulk transcriptomics;
* dataset and batch effects;
* incomplete or biased public databases;
* under-reporting of negative evidence;
* correlated evidence across databases;
* incomplete direction-of-action information;
* absence of direct wet-lab validation within the current project scope.

Because LUAD is an oncological disease, evidence frameworks derived primarily from germline genetics for complex non-cancer diseases must be adapted rather than transferred uncritically.

---

## 17. Decisions Deliberately Deferred to v0.2

The following will be resolved after inspection of real project data:

* final DE thresholds;
* number of candidates entering evidence mining;
* exact Open Targets fields;
* exact ChEMBL evidence-quality rules;
* quantitative under-exploration definition;
* feature normalization strategy;
* numerical scoring weights;
* positive and negative control panels;
* treatment of missing evidence;
* exact directionality rules.

These are research decisions that should be informed by observed data rather than arbitrarily fixed before implementation.
