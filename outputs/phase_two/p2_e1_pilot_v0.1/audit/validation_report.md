# P2-E1B Validation Report

Pilot results are not the formal P2-E1 screening denominator and do not establish a related-work gap.

Overall validation: **PASS**

| Check | Result | Detail |
|---|---|---|
| `frozen_governing_inputs` | **PASS** | All nine observed governing-input hashes match. |
| `unique_search_event_ids` | **PASS** | 40 rows; 40 unique IDs. |
| `all_searches_labelled_pilot` | **PASS** | All search roles must be PILOT_SEARCH. |
| `exact_queries_preserved` | **PASS** | No blank query/capture specification. |
| `retrieval_metadata_complete` | **PASS** | Source/provider/time/timezone/boundary required. |
| `result_counts_recorded` | **PASS** | Source count or explicit unavailable state retained. |
| `raw_payload_integrity` | **PASS** | 55 retained payloads checked. |
| `source_event_foreign_keys` | **PASS** | 769 provisional sources resolve to pilot events. |
| `system_source_foreign_keys` | **PASS** | 44 provisional systems/methods resolve to source candidates. |
| `open_targets_orientation_registered` | **PASS** | 11/11 required orientation roles captured. |
| `counterexample_searches_executed` | **PASS** | 6/6 required focuses executed. |
| `no_capability_matrix_states` | **PASS** | Discovery registries contain no capability-state coding. |
| `discovery_labels_only` | **PASS** | No formal inclusion/exclusion decisions. |
| `human_identity_boundary` | **PASS** | AI assistance distinguished; second human not fabricated. |
| `offline_reconstruction_deterministic` | **PASS** | Two consecutive offline core builds produced identical SHA256 values. |
| `future_network_identity_not_claimed` | **PASS** | Mutable future retrieval is not claimed byte-identical. |
| `no_formal_denominator_claim` | **PASS** | Pilot results are not the formal P2-E1 screening denominator and do not establish a related-work gap. |

## Interpretation boundary

Validation establishes retrieval-accounting and deterministic-transformation integrity only. It does not validate candidate relevance, system capabilities, a related-work gap, novelty, or comparative system quality.
