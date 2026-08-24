# Release Notes v1.0

**Release:** Project documentation v1.0  
**Release type:** Documentation and communication only  
**Status:** Validated documentation candidate; no computational release package created

## Summary

Version 1.0 provides the final GitHub-facing documentation for the governed LUAD Target Evidence Dossier framework. It explains the scientific motivation, architecture, artifact governance, validation model, reproducibility boundaries, and current limitations without generating or reinterpreting scientific evidence.

## Documentation included

- [README](../README.md)
- [Project Overview v1.0](project_overview_v1.0.md)
- [Reproducibility Report v0.1](reproducibility_report_v0.1.md)
- [Scientific Specification v0.1](scientific_spec_v0.1.md)
- [Release governance](governance/release_package_specification_v0.1.md)
- [Artifact Registry](../outputs/artifact_registry_v0.1/artifact_registry.csv)

## Framework status represented

- 29,606 immutable EnsemblID entities are preserved across the governed multi-component universe.
- Two evidence components are represented independently by version: transcriptomic evidence and disease association.
- Landscape, Evidence Summary, and structural routing layers retain source identities and structural states.
- `CASEREL_678B829DF020D9D6D041B1437855B322` contains four deterministic representative case-pattern slots.
- `PRESREL_33D749BD474B0A185D098F7A82822138` provides four validated communication artifacts.
- `ARTREGISTRY_19B7D25723B0715B860E8DA3BAF02396` registers 41 computational artifacts, including three external immutable payload references.
- `REPROREPORT_74749D374714B211F18005E812BBBBBA` documents the computational reproducibility model and its boundaries.

These are structural inventory statements, not biological or therapeutic conclusions.

## Validation disposition

The documentation generator validates:

- deterministic, byte-identical documentation generation;
- required Markdown sections and terminology;
- resolution of all local links;
- frozen upstream SHA256 values;
- Artifact Registry file integrity;
- cross-document release identities;
- absence of scientific artifact generation or modification.

## Communication materials

- [Architecture summary](../outputs/presentation_artifacts_v0.1/architecture_summary.md)
- [Evidence-layer summary](../outputs/presentation_artifacts_v0.1/evidence_layer_summary.csv)
- [Case-pattern summary](../outputs/presentation_artifacts_v0.1/case_pattern_summary.csv)
- [Provenance-flow summary](../outputs/presentation_artifacts_v0.1/provenance_flow_summary.md)

Poster materials: not available in Artifact Registry v0.1 and not claimed for this release.

## Known limitations

- Differential expression remains a candidate-generation signal, not target proof.
- Evidence representation does not establish a target ranking.
- Missing evidence is not negative evidence.
- Structural routing categories are non-ordinal and are not target priorities.
- Computational validation does not constitute biological validation.
- Registry v0.1 is intentionally bounded to the declared release-framework inputs.
- External immutable payloads require separate durable-storage governance before a public computational package can be released.

## Not included

This documentation release does not include:

- new evidence retrieval or scientific analysis;
- rebuilt components, landscapes, summaries, routing representations, or dossiers;
- target scores, rankings, recommendations, or therapeutic direction;
- biological, clinical, or therapeutic claims;
- a release package, external upload, or artifact lifecycle promotion.

## Version boundary

Documentation v1.0 is versioned separately from component, schema, evidence-snapshot, artifact, registry, and future package versions. Updating documentation must not silently mutate frozen computational artifacts.
