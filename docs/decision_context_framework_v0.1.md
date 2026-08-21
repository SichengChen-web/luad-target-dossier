# Decision Context Calibration Framework v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Task:** #019 — decision context calibration  
**Version:** v0.1  
**Date:** 21 August 2026  
**Status:** Working qualitative decision framework

## Purpose

Task #019 defines which evidence domains can inform three distinct scientific questions and establishes the maximum interpretation allowed for every evidence type in the existing ontology.

The framework separates:

1. **evidence generation** — producing, retrieving, normalizing, and validating source-grounded records; from
2. **decision interpretation** — deciding which bounded scientific question those records can inform.

It performs neither activity on genes in this task. It creates qualitative interpretation architecture only.

## Frozen foundation

The framework is built from the committed Task #018 artifact-governance bundle and the existing Task #013–#014 evidence ontology and claim architecture. Task #018 provides the hash and reproducibility contract; Task #013 provides the eight domains, 17 evidence types, source lineage, and dependency relationships; Task #014 provides bounded claim, missingness, uncertainty, and record-dependency semantics.

At runtime the builder:

- validates all 193 artifacts in the Task #018 manifest against current size and SHA256;
- reconciles the Task #018 governance-control hashes to its session record;
- requires exactly eight ontology domains and 17 evidence types;
- validates 31 ontology independence relationships and six source-lineage entities;
- validates 148,030 bounded claims, five current claim types, 77,202 dependency edges, and six claim source entities; and
- fails if any frozen input or existing tracked file changes.

## Meaning of support levels

Support levels describe the role of an evidence domain for a scientific question. They are not ordered weights and must not be converted into numbers without a separate reviewed specification.

| Support level | Meaning |
| --- | --- |
| `REQUIRED` | The context cannot be interpreted as supported until this domain is adequately characterized with valid provenance. |
| `RELEVANT` | The domain can strengthen, qualify, conflict with, or limit the context interpretation but cannot automatically substitute for a required domain. |
| `OPTIONAL` | The domain may provide useful context but is neither necessary nor sufficient for the decision question. |
| `NOT_APPLICABLE` | The domain does not directly support this context question; its records remain available for other contexts. |

Missing required evidence leaves the context **unresolved**. It is not negative evidence and does not count against a gene. Similarly, `NOT_FOUND`, `NOT_QUERIED`, and retrieval failure retain the Task #014 meanings and cannot be collapsed.

## Context 1 — Biological Discovery

**Question:** Is this gene worth further biological investigation?

### Required domains

- transcriptomic discovery;
- disease association.

These establish the project's expression-derived LUAD observation and an external disease-context evidence state. Both remain associative.

### Relevant domains

- genetic evidence;
- functional dependency.

These can test causal plausibility and disease-model function. Genetic alteration does not automatically predict pharmacological modulation, and model dependency does not establish patient benefit.

### Optional domains

- pharmacology;
- tractability.

These may provide experimental-tool or modality context but cannot decide whether the biology is important.

Clinical development and safety do not directly support the biological-discovery question. They remain essential in the other contexts and are not discarded.

### Interpretation boundary

This context can justify additional biological investigation. It cannot establish causality, drug efficacy, safety, clinical benefit, or intervention direction.

## Context 2 — Therapeutic Development

**Question:** Does this target have evidence relevant to drug development feasibility?

### Required domains

- pharmacology;
- tractability;
- safety.

Pharmacology must move beyond target presence to appropriate compound, assay, potency, selectivity, and mechanism evidence. Tractability must remain modality-specific. Safety must include known liabilities and explicit missingness; absence of a returned record is not evidence of safety.

### Relevant domains

- transcriptomic discovery;
- disease association;
- genetic evidence;
- functional dependency.

These inform disease rationale and biological plausibility but do not establish modality feasibility or an acceptable therapeutic window.

### Optional domain

- clinical development.

Human development precedent can inform feasibility, but absence of a trial does not prove development is infeasible.

### Interpretation boundary

This context can describe whether development-relevant evidence exists. It cannot establish biological causality, efficacy, acceptable dose, clinical success, or a favorable benefit-risk balance.

## Context 3 — Translational Context

**Question:** Is there evidence supporting potential clinical relevance?

### Required domains

- disease association;
- pharmacology;
- clinical development;
- safety.

Potential clinical relevance requires traceable disease context, intervention-to-target linkage, trial-level human-development evidence, and risk context. Platform-level candidate counts do not substitute for trial records.

### Relevant domains

- transcriptomic discovery;
- genetic evidence;
- functional dependency;
- tractability.

These may define patient context, mechanism, model response, or modality plausibility. None establishes clinical utility.

### Interpretation boundary

This context can document human investigation and a bounded translational rationale. It cannot establish efficacy, approval, patient benefit, clinical utility, or a favorable benefit-risk balance.

## Evidence-type boundaries

`interpretation_boundary_registry.csv` covers all 17 Task #013 evidence types. Each row records:

- the maximum statement supported;
- conclusions that remain unsupported;
- additional evidence classes needed for broader interpretation;
- minimum provenance; and
- known dependency risks.

Key boundaries include:

- Differential expression supports a tumour-associated molecular alteration, not causality or drug efficacy.
- Model sensitivity supports robustness to related analyses, not independent replication.
- Open Targets association views support source-native disease associations, not causal target validity.
- Literature counts support retrieval volume, not evidence quality or novelty.
- ChEMBL target annotation supports target identity/availability, not compound activity.
- Compound-target activity can support a bounded interaction record, not in-vivo efficacy or disease relevance.
- Tractability supports modality feasibility, not biological causality or clinical success.
- Trial evidence supports human investigation, not efficacy or approval.
- Safety-liability records support documented concerns, not causal toxicity; missing records do not support safety.

## Current versus future-compatible evidence

The claim architecture currently instantiates transcriptomic discovery, disease association, pharmacology annotations, tractability, and safety claims. Four evidence types remain explicitly future-compatible and not queried:

- `EV_GENETIC_CANCER`;
- `EV_FUNCTIONAL_CRISPR_DEPENDENCY`;
- `EV_CHEMBL_COMPOUND_TARGET`;
- `EV_CLINICAL_TRIAL_DEVELOPMENT`.

A future-compatible domain may be `REQUIRED` for a decision context. That means the context is currently unresolved; it does not authorize inference from a weaker substitute.

## Provenance and dependency rules

Every interpretation must retain this chain:

```text
evidence record
      ↓
source entity and source-native identifier
      ↓
source release, query, and retrieval timestamp
      ↓
dependency and upstream-lineage review
      ↓
frozen artifact path, size, and SHA256
```

Evidence fields are not independent merely because they occur in different columns, files, APIs, or decision contexts. TCGA effect, significance, and S1–S6 robustness share a cohort. Open Targets direct/indirect associations overlap. Open Targets drug, tractability, safety, and literature fields share a platform and can reuse upstream evidence. ChEMBL records can be upstream of Open Targets pharmacology and tractability.

The same evidence may be relevant to more than one context, but reuse across contexts does not create additional evidence.

## Separation from future assessment

This framework does not define a target-assessment algorithm. A future assessment task would need to specify:

1. the eligible gene universe;
2. evidence adequacy criteria within each required domain;
3. conflict-resolution and missingness rules;
4. source-dependency handling;
5. context-specific validation and controls; and
6. explicit rules for reporting unresolved conclusions.

Those decisions must be reviewed before gene-level assessment. This Task #019 framework supplies only the scientific interpretation boundary.

## Explicit non-claims

Task #019 does not analyze genes, score evidence, rank targets, select candidates, recommend targets, infer therapeutic direction, or generate an intervention hypothesis. It does not establish causality, efficacy, safety, clinical benefit, or a benefit-risk conclusion.
