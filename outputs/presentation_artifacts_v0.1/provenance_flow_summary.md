# Provenance Flow Summary v0.1

## Required provenance backbone

```text
GOVERNED_SOURCE_RECORDS
  -> EVIDENCE_SNAPSHOT_32C_CBFD2625F8B0CBB855DB90CBC8E2D605
  -> COMP_TRANSCRIPTOMIC_EVIDENCE_V0.1 + COMP_DISEASE_ASSOCIATION_V0.1
  -> LNDREL_3D3A189C362A4D29E5CA04A47656DA6C
  -> SUMREL_43EA4FD9EE02963DA2E94BD1A9FFFC53
  -> CASEREL_678B829DF020D9D6D041B1437855B322
```

This is the required `source -> snapshot -> component -> landscape -> summary -> dossier` communication path. `GOVERNED_SOURCE_RECORDS` is a structural origin label, not a new source artifact.

## Expanded governed routing path

```text
source record references
  -> frozen evidence snapshot
  -> separately represented evidence component records
  -> multi-component landscape
  -> evidence summary
  -> PRZREL_940BC24427791A7E054B54F533E77B48
  -> representative case dossier
```

The transparent routing representation mediates the summary-to-dossier link. It preserves source summary identity, component states, limitations, fixed-order rule traces, and the assigned non-ordinal category. The dossier then preserves the source representation identity and deterministic selection token.

## Lineage preservation

- Landscape records retain feature, provenance, dependency, missingness, and limitation references.
- Evidence Summaries retain landscape identity and content hash references.
- Transparent routing representations retain Evidence Summary identity and content hash references.
- Case dossiers retain routing representation identity, Evidence Summary identity, component versions and states, limitations, rule traces, and selection tokens.
- This presentation layer cites those governed identities and hashes without copying or altering underlying evidence payloads.

## Boundary

The arrows record derivation and traceability only. They do not represent evidence strength, causal direction, biological importance, or therapeutic conclusions.
