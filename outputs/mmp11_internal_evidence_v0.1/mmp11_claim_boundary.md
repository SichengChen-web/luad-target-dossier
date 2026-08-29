# MMP11 internal evidence claim boundary

> MMP11 is used as an illustrative biological worked example for scientific communication. Its inclusion is not the result of a project-level therapeutic target ranking, scoring, or recommendation procedure.

This boundary applies only to evidence already frozen inside this repository. It adds no literature, experimental, clinical, or therapeutic evidence.

## Identity block

**SUPPORTED INTERPRETATION**

- The frozen Task #009 mapping uniquely links display symbol `MMP11` to immutable project identifier `ENSG00000099953.9` and records the biotype `protein_coding`.
- All audit joins after identity resolution use `EnsemblID`.

**NOT SUPPORTED**

- Identifier resolution does not establish disease causality, biological importance, or therapeutic suitability.

## Primary transcriptomic block

**SUPPORTED INTERPRETATION**

- The frozen S0 `Tumor - Normal` analysis contains a LUAD tumour-versus-normal expression association for `ENSG00000099953.9` with recorded logFC `5.18003235678542` and BH FDR `1.79025769607393e-37`.
- Task #008 records U0=`TRUE`, U1=`TRUE`, U2=`TRUE`, effect band `A`, and retrieval queue `QUEUE_A_CANONICAL` under its frozen candidate-generation rules.

**NOT SUPPORTED**

- Differential expression does not establish disease causality, therapeutic causality, therapeutic direction, drug efficacy, clinical benefit, clinical safety, target validation, target superiority, or target recommendation.
- Effect band and retrieval queue are project workflow labels, not target rankings or therapeutic judgements.

## Sensitivity block

**SUPPORTED INTERPRETATION**

- All six prespecified S1-S6 model outputs are direction-concordant with S0; all six have BH FDR below 0.05 in their frozen results.
- Task #008/#007 records model-dependent status `FALSE` under its frozen definition.

**NOT SUPPORTED**

- S0 and S1-S6 are analyses of the same frozen TCGA-LUAD dataset. Concordance characterizes model robustness; it is not independent replication and must not be counted as seven independent observations.
- Model robustness does not establish causality or therapeutic validity.

## Disease-association block

**SUPPORTED INTERPRETATION**

- The governed component records 14 source-native Open Targets release 26.06 records for exact disease context `MONDO_0005061` and mapped target `ENSG00000099953`.
- The component state is `OBSERVED`, meaning the governed structural predicates found the required record/provenance conditions.

**NOT SUPPORTED**

- Presence or count of source-native disease-association records does not establish evidence strength, disease causality, therapeutic causality, target importance, target validity, or target suitability.
- Records sharing Open Targets Platform or dataset lineage are not automatically independent votes.
- Source-native numerical association values are not exposed or interpreted by this audit.

## Downstream representation block

**SUPPORTED INTERPRETATION**

- Component identities and states reconcile through the integrated profile, evidence landscape, evidence summary, and transparent structural-routing representation.

**NOT SUPPORTED**

- Repetition through governed layers is transformation lineage, not additional evidence.
- The non-ordinal routing category `CATEGORY_A` is not a target rank, quality statement, recommendation, or evidence-strength claim.

## Global boundary

The project-internal evidence may support bounded statements about LUAD tumour-versus-normal expression association, model robustness of that association, and the presence of source-native LUAD disease-association records. It does **not** establish disease causality, therapeutic causality, therapeutic direction, drug efficacy, clinical benefit, clinical safety, target validation, target superiority, or target recommendation.

> MMP11 is used as an illustrative biological worked example for scientific communication. Its inclusion is not the result of a project-level therapeutic target ranking, scoring, or recommendation procedure.
