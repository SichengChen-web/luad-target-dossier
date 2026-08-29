# MMP11 internal project-evidence audit summary

> MMP11 is used as an illustrative biological worked example for scientific communication. Its inclusion is not the result of a project-level therapeutic target ranking, scoring, or recommendation procedure.

## Scope

This deterministic audit extracts only frozen repository evidence for `ENSG00000099953.9`. It did not use network access, query literature or APIs, rerun differential expression, rebuild components, or modify prior artifacts.

## Identity

The Task #009 mapping independently resolved display symbol `MMP11` to immutable `EnsemblID` `ENSG00000099953.9`. The recorded gene type is `protein_coding`. Symbol lookup was confined to initial identity resolution; every cross-artifact join used `EnsemblID`.

## Frozen transcriptomic observations

The primary S0 contrast is `Tumor - Normal (Tumor coefficient +1; Normal coefficient -1)`. Its frozen values are logFC `5.18003235678542`, p-value `6.17997488815631e-39`, and BH FDR `1.79025769607393e-37`. Task #008 records U0/U1/U2 as `TRUE/TRUE/TRUE`, effect band `A`, candidate queue `QUEUE_A_CANONICAL`, and model-dependent status `FALSE`.

Across S1-S6, `6/6` model directions are concordant with S0 and `6/6` have BH FDR below 0.05. These are dependent analyses of the same frozen cohort, not independent replications.

## Governed components

- Transcriptomic component: `COMP_TRANSCRIPTOMIC_EVIDENCE` / `COMP_TRANSCRIPTOMIC_EVIDENCE_V0.1`, state `OBSERVED`, 22 features, 35 provenance relationships.
- Disease-association component: `COMP_DISEASE_ASSOCIATION` / `COMP_DISEASE_ASSOCIATION_V0.1`, state `OBSERVED`, exact LUAD context `MONDO_0005061`, Open Targets release `26.06`, 14 qualifying raw records, 194 provenance relationships.

The disease record count is audit metadata only. It is not evidence strength, confidence, or a vote count. Record granularity is preserved as `UNKNOWN` where the governed component says so.

## Bounded source evidence and lineage

This package reports 16 governed source-evidence units: two Task #014 transcriptomic units (S0 primary plus the dependent S1-S6 robustness group) and 14 exact-context disease raw records. The six sensitivity result rows remain individually visible, but together map to one governed robustness record. The 35 transcriptomic and 194 disease feature relationships produce 229 uncompressed provenance links.

The qualitative dependency map contains 21 relationships: one S0/robustness shared-dataset edge, 14 Open Targets shared-lineage edges, and six derived-representation edges. Absence of a dependency edge must not be interpreted as evidence of independence.

## Downstream trace

MMP11 component identities reconcile through integrated profile `PRF_32C_9937B27EAECBF5AC5C8E2DFF6F489386`, landscape `LND_0F8BA957765701297F12664A6C06164B`, summary `SUM_5DFD9ACB76E4E7B2E667B7B4480DBA7A`, and transparent representation `PRZ_738BA8A6A4FC47D329D4DEAC33167DDF`. These objects repeat and reorganize existing evidence; they are not new observations. The transparent representation's `CATEGORY_A` label is non-ordinal structural routing, not a target ranking or recommendation.

Task #036C contains no MMP11-specific selected case row (`FALSE`). It therefore contributes no MMP11 entity-level evidence to this audit.

## Interpretation boundary

The extracted evidence may support bounded statements about LUAD tumour-versus-normal expression association, model robustness of that association, and the presence of source-native LUAD disease-association records. It does not establish disease causality, therapeutic causality, therapeutic direction, drug efficacy, clinical benefit, clinical safety, target validation, target superiority, or target recommendation.

See `mmp11_claim_boundary.md` for the block-by-block supported/not-supported specification.

> MMP11 is used as an illustrative biological worked example for scientific communication. Its inclusion is not the result of a project-level therapeutic target ranking, scoring, or recommendation procedure.
