# Reproducibility Report v0.1

**Project:** LUAD Expression → Druggable-Target Evidence Dossier  
**Report version:** `REPRODUCIBILITY_REPORT_V0.1`  
**Release context:** Pre-release reproducibility and governance record; no release package generated  
**Artifact registry:** `ARTREGISTRY_19B7D25723B0715B860E8DA3BAF02396` (`ARTIFACT_REGISTRY_V0.1`)

## 1. Project identity and purpose

This project represents evidence structure and provenance. Its computational framework organizes frozen evidence observations, missingness states, dependencies, limitations, deterministic structural routing, and presentation-oriented case patterns.

It does not establish:

- biological validation;
- therapeutic value;
- clinical utility;
- target recommendation.

The release context is governed by [Release Package Specification v0.1](governance/release_package_specification_v0.1.md), [Release Scope Policy v0.1](governance/release_scope_policy_v0.1.md), and [Release Validation Requirements v0.1](governance/release_validation_requirements_v0.1.md). Task #037C documents reproducibility only; it does not create, freeze, or release a package.

## 2. Computational lifecycle

```text
Input data
  -> Evidence components
  -> Evidence landscape
  -> Evidence summary
  -> Structural routing
  -> Case dossiers
  -> Communication artifacts
```

### 2.1 Input data

Earlier governed tasks froze the source observations that feed the profile architecture: transcriptomic features derived from the governed LUAD expression workflow and a pinned disease-association evidence snapshot. Task #037C does not reopen, retrieve, normalize, or reinterpret those source records.

The multi-component source profile records evidence snapshot `EVIDENCE_SNAPSHOT_32C_CBFD2625F8B0CBB855DB90CBC8E2D605` and integration release `PROFILE_INTEGRATION_RELEASE_8007AAA939B733EE6619F1FCFB87CAE8`.

### 2.2 Evidence components

Each of the 29,606 immutable EnsemblID entities has two separately represented component slots:

- `COMP_TRANSCRIPTOMIC_EVIDENCE_V0.1`;
- `COMP_DISEASE_ASSOCIATION_V0.1`.

Component states describe structural evidence conditions. They are not combined into a global assessment.

### 2.3 Evidence landscape

Release `LNDREL_3D3A189C362A4D29E5CA04A47656DA6C` contains 29,606 structural landscapes and preserves 2,517,118 provenance relationships plus 3,430,043 dependency relationships. The landscape represents feature availability, missingness, provenance, dependencies, and limitations without target evaluation.

### 2.4 Evidence Summary

Release `SUMREL_43EA4FD9EE02963DA2E94BD1A9FFFC53` contains 29,606 summaries. It preserves the two component versions, 1,213,846 feature-missingness references, and 3,430,043 dependency relationships from the landscape projection.

### 2.5 Structural routing

Release `PRZREL_940BC24427791A7E054B54F533E77B48` contains 29,606 transparent routing representations and 118,424 fixed-order rule-trace steps. Routing categories are non-ordinal structural categories. They are not priorities.

### 2.6 Case dossiers

Release `CASEREL_678B829DF020D9D6D041B1437855B322` contains 4 filled representative structural case slots. Each was selected from a complete eligible pool by the frozen category-salted SHA256 minimum rule. Selection is a reproducible presentation mechanism, not target selection.

### 2.7 Communication artifacts

Release `PRESREL_33D749BD474B0A185D098F7A82822138` contains governed architecture, evidence-layer, case-pattern, and provenance-flow summaries. These artifacts communicate existing representations without adding literature, biological claims, or therapeutic conclusions.

## 3. Artifact governance

The [Artifact Registry v0.1](../outputs/artifact_registry_v0.1/artifact_registry.csv) contains 41 records:

- 15 scientific-scope computational artifacts;
- 22 governance artifacts;
- 4 communication artifacts;
- 38 Git-managed file records;
- 3 external immutable payload references.

The registry is governed by [Artifact Registry Policy v0.1](governance/artifact_registry_policy_v0.1.md). Each row preserves an immutable artifact ID, path or logical external locator, artifact and schema versions, generating task, lifecycle state, validation disposition, SHA256, byte size, storage reference, provenance reference, and dependency reference.

All registered artifacts are currently recorded as `VALIDATED`; none is promoted by this report to `FROZEN` or `RELEASED`.

### 3.1 Git-managed artifacts

Git-managed records point to repository-relative files. Reproducibility validation recalculates each file's size and SHA256 and compares them with the frozen registry. Source code, schemas, policies, manifests, indexes, validation reports, session metadata, and small communication artifacts can therefore be audited without opening large external payloads.

### 3.2 External immutable payload references

| Artifact ID | Governed size (bytes) | Partition-set SHA256 | Storage reference |
|---|---:|---|---|
| `ART_LNDV02_SET_756809652ACB00343DA20824` | 3,386,989,421 | `756809652acb00343da20824dfec74550c01f649fe78159a6e6bc762e546ea21` | `external+sha256://luad-target-dossier/evidence-landscape-v0.2/ART_LNDV02_SET_756809652ACB00343DA20824/` |
| `ART_PRZV01_SET_011A39B150DEF9E56A43CBF9` | 94,591,468 | `011a39b150def9e56a43cbf97ff3985111dab0c5fe6d4fea3b3312f27961f65b` | `external+sha256://PENDING/luad-target-dossier/prioritization-v0.1/ART_PRZV01_SET_011A39B150DEF9E56A43CBF9/` |
| `ART_SUMV01_SET_9C7750D42301093888A120CE` | 1,876,140,432 | `9c7750d42301093888a120ce9b4231d7b33724e17c1dc40a57c60ffa92c81291` | `external+sha256://PENDING/luad-target-dossier/evidence-summary-v0.1/ART_SUMV01_SET_9C7750D42301093888A120CE/` |

The three references describe 5,357,721,321 governed bytes in total. Task #037C neither reads nor copies those payload bytes. Their storage references identify content-addressed local staging or pending durable registration; this report does not claim public release availability.

### 3.3 Versioning, identity, and provenance

- Artifact IDs identify immutable registry entries; source-native external IDs remain unchanged.
- Component, schema, representation, evidence-snapshot, registry, report, and future release versions remain separate axes.
- SHA256 verifies byte identity, not scientific correctness.
- Provenance references record upstream release or contract identity.
- Dependency references preserve computational lineage and must not be interpreted as independent evidence votes.

The future release-manifest contract is `RELEASE_MANIFEST_SCHEMA_V0.1`. Its presence defines package structure but does not create a package.

## 4. Reproducibility model

### 4.1 Reproducible computational properties

| Property | Governed claim |
|---|---|
| Deterministic generation | Identical frozen inputs, generator versions, and rules produce byte-identical governed outputs where each task's validation report states this result. |
| Metadata validation | Identities, versions, dimensions, controlled vocabularies, lifecycle states, and source-release links are checked deterministically. |
| Schema validation | Closed schemas constrain required fields and reject undeclared or prohibited structural fields. |
| Artifact integrity | Registered Git-managed bytes are checked by size and SHA256; external payloads are checked through frozen metadata identities and partition-set hashes. |
| Provenance preservation | Layer-to-layer identities, content hashes, dependency relationships, missingness, and limitation references remain traceable. |

### 4.2 Not claimed

This project does not claim:

- biological reproducibility;
- clinical reproducibility;
- therapeutic prediction;
- experimental target validation;
- efficacy, safety, or clinical benefit.

Computational regeneration can demonstrate that governed software transforms the same frozen inputs into the same bytes. It cannot demonstrate that a molecular observation is causal or therapeutically useful.

## 5. Validation framework

### 5.1 Frozen hashes

Every governed task checks frozen input hashes before and after generation. The Artifact Registry independently records and validates 38 Git-managed file artifacts and three external payload references. Task #037C re-hashes every Git-managed registry row before generating this report.

### 5.2 Deterministic regeneration

The landscape, Evidence Summary, structural routing, case dossier, and presentation tasks each record two complete byte-identical generations. Task #037C similarly generates this report and its governance metadata twice and compares the bytes.

### 5.3 Dependency preservation

The landscape records ordered dependency relationships without collapsing dependent records. Evidence Summaries preserve those relationships, routing preserves component-state snapshots and source-summary identities, and case dossiers preserve routing identities, rule traces, limitations, and deterministic selection tokens. The Artifact Registry requires all registered dependency references to resolve and its dependency graph to remain acyclic.

### 5.4 Schema validation

Layer-specific schemas preserve identity, component state, missingness, provenance, dependency, limitation, and version contracts. Task #037A defines the future release-manifest schema; Task #037B defines the registry schema. Schema conformance is structural validation only.

### 5.5 Prohibited-field checks

Previous generators recursively reject fields that would introduce scores, rankings, priorities, confidence metrics, recommendations, target-quality assertions, or evidence-strength assertions. Task #037C preserves those boundaries and adds none of those values.

## 6. Reproducibility boundaries and limitations

1. **Differential expression is candidate generation, not target proof.** Expression association does not establish disease causality or therapeutic actionability.
2. **Evidence representation is not ranking.** Structural component states and evidence availability do not establish comparative target quality.
3. **Missing evidence is not negative evidence.** `MISSING`, `NOT_QUERIED`, `NOT_FOUND`, and related controlled states must retain their governed meanings.
4. **Routing categories are not priorities.** The transparent categories are non-ordinal rule outcomes and must not be read as a preferred order.
5. **Artifact validation is not biological validation.** Hash, schema, lineage, and deterministic-regeneration checks establish computational integrity only.
6. **External storage is not yet a public release.** The registry contains metadata references to immutable payload sets, but durable distribution remains a future release action.
7. **The registry is intentionally bounded.** Registry v0.1 covers the declared release-framework inputs and does not claim exhaustive coverage of every historical repository artifact.
8. **No wet-lab replication is performed here.** Experimental validation remains outside this computational framework.

## 7. Reproduction contract

A future reproducibility exercise should:

1. verify the registry, policy, schema, generator, and frozen release identities;
2. verify every Git-managed byte size and SHA256;
3. resolve external immutable payloads by source-native ID and partition-set SHA256 without rewriting identifiers;
4. use the recorded generator, schema, component, rule-catalog, and snapshot versions;
5. regenerate only the authorized layer under its frozen contract;
6. compare every generated byte, index identity, dependency reference, and validation disposition;
7. report mismatches rather than changing frozen inputs or manufacturing agreement.

This report documents that contract. It does not execute it for the scientific layers.

## 8. Report provenance and status

This report is generated deterministically by `analysis/37C_generate_reproducibility_report.py` from frozen manifests and Artifact Registry v0.1. Its own SHA256 and generator identity are recorded in `outputs/reproducibility_report_v0.1/reproducibility_report_manifest.json`.

Status: validated governance documentation candidate. No release package was created, and no artifact lifecycle state was advanced.
