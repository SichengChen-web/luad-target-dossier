# LUAD Expression → Druggable-Target Evidence Dossier

## Project identity

This repository develops a reproducible, evidence-grounded framework for organizing evidence relevant to lung adenocarcinoma target research. It begins with governed transcriptomic and disease-association observations and preserves their structure, missingness, provenance, dependencies, limitations, and version history through auditable target evidence dossiers.

The framework is an evidence-representation and hypothesis-organization system. It is not a target-ranking system, a clinical decision tool, or experimental target validation.

## Scientific motivation

Differential expression can identify disease-associated molecular changes, but it does not prove causality, drug efficacy, safety, or therapeutic value. External evidence can also be incomplete, dependent, or absent for reasons unrelated to biology. The project therefore represents evidence and its provenance before any future target-level interpretation.

This separation makes it possible to inspect what was observed, what was not found, what was not queried, which records are dependent, and which limitations remain—without silently converting evidence availability into target quality.

## Framework architecture

```text
Transcriptomic evidence component     Disease association evidence component
                  \                         /
                   -> Evidence Landscape ->
                      Evidence Summary
                            |
                    Structural Routing
                            |
                Representative Case Dossiers
```

- `COMP_TRANSCRIPTOMIC_EVIDENCE_V0.1` represents governed transcriptomic observations.
- `COMP_DISEASE_ASSOCIATION_V0.1` represents governed disease-association observations.
- The Multi-component Evidence Landscape preserves component states, feature missingness, provenance, dependencies, and limitations for 29,606 immutable EnsemblID entities.
- Evidence Summaries provide deterministic structural projections of landscapes.
- Structural routing applies a transparent, non-ordinal rule catalog and preserves complete rule traces.
- Representative Case Dossiers provide deterministic presentation examples of governed structural patterns; they are not selected as preferred targets.

See the [Project Overview v1.0](docs/project_overview_v1.0.md) and the original [Scientific Specification v0.1](docs/scientific_spec_v0.1.md).

## Reproducibility and artifact governance

The [Artifact Registry v0.1](outputs/artifact_registry_v0.1/artifact_registry.csv) records 41 computational artifacts with immutable identities, versions, SHA256 values, provenance references, dependencies, lifecycle states, and storage references.

- 38 Git-managed artifacts can be checked directly by file size and SHA256.
- 3 large immutable payload sets are represented by source-native IDs, partition-set hashes, sizes, and external-storage references rather than copied into Git.
- The [Reproducibility Report v0.1](docs/reproducibility_report_v0.1.md) separates computational reproducibility from biological, clinical, and therapeutic claims.
- The [Release Package Specification v0.1](docs/governance/release_package_specification_v0.1.md) defines future packaging and lifecycle rules. No release package is created by this documentation task.

## Validation

The governed framework validates:

- deterministic, byte-identical regeneration under frozen inputs and versions;
- artifact size and SHA256 integrity;
- immutable EnsemblID identity and canonical ordering;
- schema and controlled-vocabulary conformance;
- provenance and dependency preservation;
- missingness and limitation preservation;
- recursive rejection of prohibited evaluation fields.

Computational validation demonstrates structural and reproducibility conformance. It does not establish biological truth.

## Limitations

- **Differential expression is not target proof.** Association does not establish causality or therapeutic actionability.
- **Evidence representation is not ranking.** Evidence structure and availability do not establish comparative target quality.
- **Missing evidence is not negative evidence.** `MISSING`, `NOT_FOUND`, and `NOT_QUERIED` retain distinct governed meanings.
- **Routing categories are not target priorities.** They are non-ordinal structural rule outcomes.
- **Computational validation is not biological validation.** Hashes, schemas, and deterministic regeneration do not demonstrate efficacy, safety, or clinical benefit.
- External payload storage remains governed separately from public release distribution.

## Communication materials

Validated communication artifacts are available as:

- [Architecture summary](outputs/presentation_artifacts_v0.1/architecture_summary.md)
- [Evidence-layer summary](outputs/presentation_artifacts_v0.1/evidence_layer_summary.csv)
- [Case-pattern summary](outputs/presentation_artifacts_v0.1/case_pattern_summary.csv)
- [Provenance-flow summary](outputs/presentation_artifacts_v0.1/provenance_flow_summary.md)

Poster materials: none are registered in Artifact Registry v0.1; no poster is claimed in this documentation release.

## Documentation release

- [Project Overview v1.0](docs/project_overview_v1.0.md)
- [Release Notes v1.0](docs/release_notes_v1.0.md)
- [Reproducibility Report v0.1](docs/reproducibility_report_v0.1.md)
- Presentation release: `PRESREL_33D749BD474B0A185D098F7A82822138`

This documentation describes frozen computational artifacts. It introduces no new scientific evidence, ranking, score, recommendation, or biological claim.
