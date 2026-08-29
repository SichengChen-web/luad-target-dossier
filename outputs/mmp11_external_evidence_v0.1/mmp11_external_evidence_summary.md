# MMP11 external evidence summary v0.1

MMP11 is being used as an illustrative biological worked example. External evidence is organized to demonstrate provenance-aware evidence synthesis and does not constitute a project-level therapeutic target ranking, validation, or recommendation.

## Scope and identity

This acquisition reconciled **ENSG00000099953.9** to the frozen Task #039A identity and used **MMP11** only as a display/search synonym. Project-side joins remain EnsemblID-based. It describes external observations; it does not provide an overall conclusion.

## Acquisition inventory

- Publications screened: **37** (30 from the complete PubMed broad query plus 7 Task #039A overlap-orientation records)
- Publications included for at least one bounded observation: **30**
- Publications excluded with retained reasons: **7**
- Bounded evidence units: **56**
- Datasets/cohorts: **35**
- Experimental models: **23**
- External provenance links: **56**
- Dependency relationships: **197**

## Search coverage boundary

The PubMed broad query was the primary formal publication screening frame. Its complete set of **30** records was combined with **7** unique Task #039A overlap-orientation records, producing the formal denominator of **37 publications screened**.

Europe PMC was used only as a supplementary high-recall discovery and cross-check source. Its **1,383** hits were not exhaustively paginated or screened and are not part of the publication denominator. ClinicalTrials.gov was a separate clinical-development check and its lexical hits are also outside that denominator.

Task #039B is therefore a bounded provenance-aware evidence acquisition, not a formal systematic review or a claim of exhaustive literature coverage.

## Evidence units by domain

- A_TRANSCRIPTOMIC_EXPRESSION: **14**
- B_PROTEIN_TISSUE: **9**
- C_CLINICAL_ASSOCIATION: **13**
- D_FUNCTIONAL_PERTURBATION: **4**
- E_MECHANISTIC: **12**
- F_IN_VIVO: **1**
- G_INTERVENTION: **3**

## Evidence states retained

- CONTEXT_DEPENDENT: **19**
- INSUFFICIENTLY_SPECIFIC: **13**
- OBSERVED_NULL: **7**
- OBSERVED_SUPPORTIVE: **17**

No unit was labelled `OBSERVED_CONTRADICTORY` in this bounded search. That absence must not be interpreted as proof of consistency. Null findings include germline susceptibility, EGFR-subtype, cytotoxic-T-cell, immune-checkpoint-benefit, POSTN-paper prognosis, stage-I survival, and recurrence analyses. Context-dependent and insufficiently specific findings remain visible rather than being promoted to LUAD-specific support.

## Special audit: PMID 31024988

The expected identifier was independently reconciled as PMID **31024988**, PMCID **PMC6477516**, DOI **10.1016/j.omto.2019.03.012**. Separate evidence units represent its GEO analysis, TCGA analysis, patient IHC, serum ELISA, A549/PC9 perturbation and rescue, migration/invasion, xenografts, and antibody experiments. They retain `SHARED_PUBLICATION`, dataset, experiment, model-system, and reagent relationships and therefore are not treated as independent votes.

## Cross-lineage and modality observations

- TCGA-overlapping evidence units: **7**. Each shares biological dataset lineage with Task #039A.
- Potentially distinct GEO-dataset evidence units under the conservative accession audit: **3**. “Potentially distinct” is not proof of statistical independence.
- Functional perturbation units: **4**.
- In vivo units: **2**.
- Preclinical intervention units: **3**.
- ClinicalTrials.gov records returned for the frozen MMP11 query: **5**. All five were screened as lexical false positives and retained in the exclusion log; no MMP11 clinical-development evidence unit was created.

## Reproducibility boundary

The retained raw payloads are immutable within this task and are listed with retrieval timestamps and SHA256 hashes. Transformation from those frozen payloads is deterministic. PubMed, Europe PMC, GEO, PMC, and ClinicalTrials.gov are mutable external services, so future network retrieval is not claimed to be byte-identical.

## Unresolved limitations

- Some older NSCLC studies do not separate adenocarcinoma results.
- Some computational studies do not expose accession-level cohort provenance in accessible text.
- A source reporting a model, pathway, or antibody effect does not independently validate specificity, generalizability, efficacy, or safety.
- Publication and dataset overlap can be documented, but absence of a discovered overlap cannot prove independence.
