# Project Overview v1.0

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Documentation version:** `PROJECT_DOCUMENTATION_V1.0`  
**Status:** Validated project documentation candidate; no release package created

## 1. Purpose and positioning

The project provides a deterministic architecture for representing evidence associated with LUAD expression-derived entities. Its purpose is to preserve evidence identity, availability, missingness, provenance, dependencies, and limitations so that future scientific review can inspect the basis of a dossier without hidden aggregation.

The framework does not itself determine target quality, therapeutic value, clinical utility, or a preferred target. It is infrastructure for evidence organization and hypothesis generation.

## 2. Why representation precedes interpretation

Evidence sources answer different questions and can share underlying datasets. A transcriptomic association, a disease-association record, a tractability observation, and a clinical record are not interchangeable votes. Missing records may reflect query scope or source coverage rather than biology. Representing source identity, dependency, and missingness before interpretation prevents record counts or database presence from becoming implicit scientific conclusions.

The current multi-component release includes transcriptomic and disease-association components only. Future components require separate registration, source contracts, snapshots, feature extraction, validation, and materialization under the governed component interface.

## 3. Architecture

```text
Frozen source observations and snapshots
  -> COMP_TRANSCRIPTOMIC_EVIDENCE_V0.1
  -> COMP_DISEASE_ASSOCIATION_V0.1
  -> Multi-component Evidence Landscape
  -> Evidence Summary
  -> Transparent non-ordinal structural routing
  -> Representative structural case dossiers
  -> Governed communication artifacts
```

The architecture preserves one immutable EnsemblID universe of 29,606 entities. Each representation layer retains its own schema, generator, component, rule-catalog, snapshot, and artifact version axes.

## 4. Governed layers

| Layer | Governed release identity | Purpose boundary |
|---|---|---|
| Evidence Landscape | `LNDREL_3D3A189C362A4D29E5CA04A47656DA6C` | Structural composition of component, feature, provenance, dependency, missingness, and limitation references |
| Evidence Summary | `SUMREL_43EA4FD9EE02963DA2E94BD1A9FFFC53` | Deterministic structural projection of one landscape per entity |
| Structural routing | `PRZREL_940BC24427791A7E054B54F533E77B48` | Fixed-rule, non-ordinal routing with complete trace |
| Case dossiers | `CASEREL_678B829DF020D9D6D041B1437855B322` | Deterministic representative presentation patterns |
| Communication artifacts | `PRESREL_33D749BD474B0A185D098F7A82822138` | Human-readable structural summaries without added evidence |

No layer produces an overall state, evidence-strength measure, target score, rank, or recommendation.

## 5. Artifact governance

Artifact Registry `ARTREGISTRY_19B7D25723B0715B860E8DA3BAF02396` contains 41 records: 15 scientific-scope, 22 governance, and 4 communication artifacts.

### Git-managed records

Git-managed artifacts use repository-relative paths and are validated against registered sizes and SHA256 values. These include manifests, indexes, policies, schemas, validation reports, session metadata, generator source, and communication documents.

### External immutable payload references

| Artifact ID | Governed size (bytes) | Partition-set SHA256 |
|---|---:|---|
| `ART_LNDV02_SET_756809652ACB00343DA20824` | 3,386,989,421 | `756809652acb00343da20824dfec74550c01f649fe78159a6e6bc762e546ea21` |
| `ART_PRZV01_SET_011A39B150DEF9E56A43CBF9` | 94,591,468 | `011a39b150def9e56a43cbf97ff3985111dab0c5fe6d4fea3b3312f27961f65b` |
| `ART_SUMV01_SET_9C7750D42301093888A120CE` | 1,876,140,432 | `9c7750d42301093888a120ce9b4231d7b33724e17c1dc40a57c60ffa92c81291` |

External rows are metadata references only. Their payloads are not copied into Git by documentation or registry tasks. Durable public distribution remains a separate future action.

## 6. Reproducibility model

The [Reproducibility Report v0.1](reproducibility_report_v0.1.md) documents:

- deterministic generation under frozen inputs;
- metadata and schema validation;
- byte-size and SHA256 integrity checks;
- cross-layer identity reconciliation;
- provenance, dependency, missingness, and limitation preservation;
- explicit boundaries on biological, clinical, and therapeutic claims.

Report `REPROREPORT_74749D374714B211F18005E812BBBBBA` re-hashed all 38 Git-managed Artifact Registry rows and used the three external payload rows as metadata references only.

## 7. Validation architecture

Validation is layered and fail-closed:

1. schema checks constrain required fields and controlled vocabularies;
2. frozen-hash checks detect input mutation;
3. identity checks preserve the canonical entity universe and release links;
4. lineage checks preserve source, provenance, and dependency references;
5. missingness checks preserve controlled meanings;
6. deterministic regeneration compares generated bytes;
7. prohibited-field checks reject hidden evaluation concepts.

Validation failures are reported rather than repaired by altering frozen artifacts.

## 8. Interpretation boundaries

- DE is not target proof.
- Evidence representation is not ranking.
- Missing evidence is not negative evidence.
- Routing categories are not target priorities.
- Computational validation is not biological validation.
- Representative cases are presentation examples, not preferred targets.
- Release or registry inclusion is not therapeutic endorsement.

## 9. Release and documentation status

Task #037A established `RELEASE_MANIFEST_SCHEMA_V0.1` for a future package. Task #037B created an artifact registry. Task #037C documented computational reproducibility. Task #037D creates the GitHub-facing documentation set only.

No release package, upload, external retrieval, scientific regeneration, target evaluation, or artifact lifecycle promotion occurs in this documentation release.

## 10. Reviewer entry points

- [Repository README](../README.md)
- [Scientific Specification v0.1](scientific_spec_v0.1.md)
- [Reproducibility Report v0.1](reproducibility_report_v0.1.md)
- [Release Package Specification v0.1](governance/release_package_specification_v0.1.md)
- [Artifact Registry Policy v0.1](governance/artifact_registry_policy_v0.1.md)
- [Artifact Registry CSV](../outputs/artifact_registry_v0.1/artifact_registry.csv)
- [Presentation architecture summary](../outputs/presentation_artifacts_v0.1/architecture_summary.md)
- [Release Notes v1.0](release_notes_v1.0.md)
