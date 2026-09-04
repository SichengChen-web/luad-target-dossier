# P2-E1B Protocol Amendment Candidates

Pilot results are not the formal P2-E1 screening denominator and do not establish a related-work gap.

These are proposals only. No governing protocol, codebook, or template has been changed.

| Issue | Location | Observed pilot problem | Proposed change | Eligibility | Search denominator | Capability semantics | Recommendation |
|---|---|---|---|---|---|---|---|
| P2E1B_AMEND_001 | P2-E1 protocol governing-input status | The task brief describes the protocol, codebook, and templates as committed, but they are outside the current Git HEAD. P2-E1B froze their observed bytes without changing them. | Before P2-E1C, establish a reviewed immutable Git identity for the governing inputs or explicitly designate a content-hash freeze independent of Git. | NO | NO | NO | CLARIFICATION |
| P2E1B_AMEND_002 | P2-E1 protocol Section 6 and Section 7.1 | The concept blocks do not yet contain frozen source-specific PubMed fielding or OpenAlex free-text translation rules. | After human review of this pilot, add an approved source-specific production-query appendix and record any query changes as a protocol amendment. | NO | YES | NO | MINOR_AMENDMENT |
| P2E1B_AMEND_003 | P2-E1 protocol Section 7.1 | OpenAlex full-text search does not implement PubMed field tags or identical Boolean semantics, so paired queries are concept translations rather than syntactic replicas. | State explicitly that cross-database translations preserve concepts but may use provider-specific retrieval semantics; peer-check each production translation. | NO | YES | NO | CLARIFICATION |
| P2E1B_AMEND_004 | P2-E1 protocol Section 6 search concepts | Automated first-page diagnostics flagged noisy families NONE and broad families QF01_TARGET_INTEGRATION/QF03_KNOWLEDGE_GRAPHS/QF04_PROVENANCE/QF05_EVIDENCE_SYNTHESIS/QF06_MISSING_UNCERTAIN_DEPENDENT/QF07_AI_TARGET_DISCOVERY/QF08_COUNTER_DEPENDENCY/QF09_COUNTER_MISSINGNESS/QF10_COUNTER_PROVENANCE_AGGREGATION/QF11_COUNTER_CLAIM_EVIDENCE/QF12_CLAIM_BOUNDARY_VARIANTS/QF13_COUNTER_CONFLICT_PRESERVATION/QF14_COUNTER_AI_GROUNDING; these labels require human confirmation. | Have a human review stratified result samples and approve narrower or split production queries only where the captured records demonstrate a reproducible blind spot or noise mechanism. | NO | YES | NO | MINOR_AMENDMENT |
