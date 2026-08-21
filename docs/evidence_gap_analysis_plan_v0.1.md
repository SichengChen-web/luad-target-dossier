# Evidence Gap Analysis and Validation Strategy v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Task:** #016 — evidence gap analysis and validation strategy  
**Version:** v0.1  
**Date:** 21 August 2026  
**Status:** Implemented descriptive gap-analysis plan

## Purpose and boundaries

Task #016 describes which evidence classes are present, partial, missing, unresolved, or not applicable for every immutable Ensembl gene. Its purpose is to identify evidence needed to interpret a target profile more completely—not to decide which target is best.

This task does not rank, score, prioritize, select, or recommend targets. The required `recommended_future_evidence_type` field identifies evidence classes that could reduce uncertainty. It is not a target recommendation and does not define an ordering of genes.

## Frozen inputs

The analysis is grounded in these committed, read-only inputs:

| Input | SHA256 |
|---|---|
| `outputs/integrated_registry/integrated_target_registry.csv` | `0587fc6901267b18c8144644571f89ac2cc46053b57ea5def4093795fdbc4c26` |
| `outputs/evidence_claim_architecture/evidence_claim_registry.csv` | `0d963a4c5c8f9586f81369e33df0a2b7e57bb37ac8ceab4ce54498baf2351a66` |
| `outputs/evidence_claim_architecture/evidence_record_registry.csv` | `76ec5056fb4e468176073073532204d231765d4f0cd70dbb6cfe4ad8bf752343` |
| `outputs/evidence_claim_architecture/missingness_uncertainty_registry.csv` | `3bbe080b1ed46dd159a86b53fb707572f988361af96e001188b69da0daa9147d` |
| `docs/target_prioritization_framework_v0.1.md` | `9d7c76235a9272cf62157eb322cc8d0f55dc2af697958d707b28e43c06334213` |

The builder fails if any hash changes, if the integrated registry no longer contains 29,606 unique EnsemblIDs and 14,064 U2 genes, or if Task #014 claim/record/missingness links no longer validate.

## Controlled status vocabulary

The five allowed gap statuses are:

| Status | Meaning |
|---|---|
| `OBSERVED` | The profile contains the defined evidence needed for the bounded current status |
| `PARTIAL` | Some relevant evidence is present, but one or more required subdomains remain absent or unresolved |
| `MISSING` | The current project snapshot lacks the required evidence class |
| `UNKNOWN` | Available records do not permit the evidence state to be resolved |
| `NOT_APPLICABLE` | The evidence question does not apply to the entity |

These are categorical descriptions, not ordered numerical values. `MISSING` does not mean that the biological property is absent.

## Domain derivation rules

### Discovery evidence

**Question:** Is there LUAD-associated discovery evidence?

- `OBSERVED`: effect-supported U2 differential expression, at least one returned Open Targets LUAD association view, and no prespecified expression sign-conflict flag.
- `PARTIAL`: U1 differential expression and/or a returned LUAD association is present, but the complete bounded discovery definition is not met.
- `MISSING`: neither U1 differential expression nor a returned LUAD association is present in the current snapshot.

Primary and S1–S6 fields remain related evidence from the same cohort. An `OBSERVED` discovery state does not establish causality.

### Mechanistic evidence

**Question:** Is there evidence supporting biological mechanism?

Dedicated genetic, functional-dependency, and perturbational evidence have not yet been retrieved. Therefore the current per-gene status is `MISSING` for all genes. This is a project-wide evidence gap, not evidence that any target lacks a mechanism or dependency.

### Therapeutic development evidence

**Question:** Is there evidence supporting therapeutic feasibility?

- `PARTIAL`: at least one positive bounded pharmacology-annotation record or tractability record is present.
- `MISSING`: neither is present.

No gene can be considered completely characterized in this layer because compound activity/mechanism and trial-level clinical-development evidence are incomplete or absent. Drug counts, target annotations, and tractability buckets do not establish therapeutic value.

### Risk evidence

**Question:** Are safety and translational risks characterized?

- `PARTIAL`: at least one Open Targets safety-liability record is present.
- `MISSING`: no safety-liability record was retrieved or the target was not mapped.

Normal-tissue context, essentiality, and broader toxicity evidence are absent, so the risk layer cannot be complete. `MISSING` is not evidence of safety, and `PARTIAL` is not a binary unsafe classification.

### Evidence maturity

**Question:** Is evidence availability sufficient to interpret the target profile?

- `PARTIAL`: at least one of discovery, development, or risk contains observed/partial bounded evidence.
- `MISSING`: none of those current domains contains bounded positive evidence.

Maturity describes structural evidence availability and interpretability, not target quality. It cannot be complete while dedicated mechanistic, clinical-development, normal-tissue, essentiality, and toxicity domains remain absent.

## Missing evidence and uncertainty fields

`missing_evidence_domains` is a deterministic pipe-delimited inventory. Every row records the current project-wide gaps in:

- genetic evidence;
- functional dependency;
- perturbational evidence;
- trial-level clinical development;
- normal-tissue context;
- essentiality;
- toxicity evidence.

Gene-specific missing association, pharmacology, tractability, and safety-liability states are appended when their Task #014 claims have no supporting record.

`known_uncertainties` preserves the Task #014 categories and always includes `INCOMPLETE_COVERAGE` because the universal gaps apply to every profile. Conflicting expression evidence remains visible.

`recommended_future_evidence_type` lists evidence classes that could reduce the corresponding gaps. The list is an uncertainty-reduction inventory, not a target recommendation, gene selection, or priority sequence.

## Validation strategy matrix

The matrix connects each major gap to:

- a potential data-source class;
- the bounded scientific question it could answer;
- uncertainty categories it could reduce;
- source-dependency checks;
- an interpretation boundary.

The matrix covers independent LUAD replication, disease-association detail, genetics, functional dependency, perturbation, compound activity/mechanism, modality-specific tractability, clinical development, normal-tissue context, essentiality/constraint, and toxicity evidence.

It does not authorize a network retrieval, experiment, target progression, or therapeutic decision. Each future data addition requires its own versioned retrieval and validation specification.

## Missingness and non-claims

Missing evidence is not negative evidence:

- no dependency data does not mean nondependency;
- no compound record does not prove undruggability;
- no trial does not prove lack of potential;
- no normal-tissue or essentiality record does not establish low risk;
- no safety-liability record does not establish safety.

Task #016 does not determine biological importance, causal validity, druggability, clinical readiness, safety, therapeutic direction, target quality, selection, priority, or rank.

## Reproducibility and validation

The builder uses only Python standard-library modules and performs no network access. It validates:

- all frozen input hashes;
- the committed Task #015 base and clean tracked worktree;
- EnsemblID count, uniqueness, and order;
- Task #014 claim identities and five-domain coverage;
- all Task #014 evidence-record links and supporting counts;
- claim missingness and uncertainty consistency;
- controlled output statuses;
- explicit universal evidence gaps;
- absence of forbidden score, rank, selection, priority, recommendation, and therapeutic-direction fields.

The session file records input/output hashes, environment, Git provenance, validation counts, and explicit non-generation of scoring, ranking, prioritization, target selection, or therapeutic recommendations.
