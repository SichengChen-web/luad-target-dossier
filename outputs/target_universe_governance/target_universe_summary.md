# Task #022 target universe governance summary

**Target manifests populated:** 0  
**Target profiles populated:** 0  
**Future target_manifest schema fields:** 17  
**Membership-rule templates:** 11  
**Frozen registry identities validated:** 29,606  
**Validation checks passed:** 12/12  
**Scores, rankings, selections, recommendations, or therapeutic interpretations generated:** No

## Scientific formulation

The governing question is well formed when interpreted as entity and scope definition: which immutable gene entities are members of a named, versioned universe, under which frozen rule and provenance? It is not a question about which genes are better targets.

A target entity is the exact versioned Ensembl gene record carried by `EnsemblID`. `Symbol` and `gene_type` are permitted display annotations only. A future manifest covers one universe ID and version so EnsemblID remains unique within that snapshot.

## Universe concepts

| Universe | Membership meaning | Boundary |
| --- | --- | --- |
| All tested genes | Membership in an explicitly frozen tested-gene analysis scope | No inference about biological interest |
| DE-supported genes | Membership in one explicitly named frozen DE layer | Task #022 does not choose U1_DE versus U2_effect_supported_DE |
| Evidence-profiled entities | Existence of a released, QC-passing Task #021-compatible profile | Profile state or completeness is not target quality |
| Future therapeutic development universe | Definition intentionally deferred | No current drug, tractability, safety, clinical, or DE field is an implicit filter |

## Membership states

- `INCLUDED`: the exact versioned rule evaluates true.
- `EXCLUDED`: the entity is outside this universe's defined scope; this is not a biological judgment.
- `NOT_ASSESSED`: available frozen information cannot resolve membership without inference or repair.
- `FUTURE_SCOPE`: the entity or universe definition is intentionally reserved for a later version.

Every future decision records its source, rule ID, artifact ID and SHA256, frozen membership timestamp, and neutral reason. Manual edits without provenance and symbol-based joins are prohibited.

## Version and release contract

A future `target_universe_version` must be content-derived from the canonical universe definition, ordered source artifact IDs and hashes, canonical membership rules, and generator script hash. Changing any element creates a new version; prior manifests are immutable.

The future manifest must preserve source order through `target_order`. Task #021 may materialize profiles only from `INCLUDED` rows after the manifest itself is registered externally with an artifact ID and SHA256. The manifest must not contain its own hash because that would create a circular identity; its hash belongs in the materialization run manifest.

## Frozen input validation

The Task #008 candidate and Task #012 integrated registries each contain 29,606 unique, identically ordered EnsemblIDs. Their U0/U1/U2 counts remain 29,606, 21,232, and 14,064. These counts validate identity only and do not instantiate a universe in Task #022.

Task #020 still defines EnsemblID as immutable, and the frozen Task #021 contract still requires a unique ordered target universe manifest while prohibiting symbol fallback. All four frozen input hashes matched before and after generation.

## Deliberately unresolved

- whether a DE-supported universe should use U1_DE, U2_effect_supported_DE, or a future versioned definition;
- which entities should enter any future therapeutic-development universe;
- when an evidence-profile materialization campaign should begin; and
- any scientific interpretation of membership, evidence state, or exclusion.
