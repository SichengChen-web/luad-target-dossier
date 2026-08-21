#!/usr/bin/env python3
"""Build the Task #024 target evidence profile release specification.

This standard-library builder defines the future release schema, requirements,
and QC gates for materialized target evidence profiles. It creates no profiles,
gene assessments, scores, rankings, selections, or recommendations.
"""

from __future__ import annotations

import csv
import hashlib
import io
import platform
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK023_BASE_COMMIT = "c2b635e27da63d5136a83be073e4c9f92babae66"
EXPECTED_BRANCH = "main"
EXPECTED_REMOTE_FRAGMENT = "SichengChen-web/luad-target-dossier"
RELEASE_SPEC_VERSION = "PROFILE_RELEASE_SPEC_V0.1"

SCRIPT_PATH = ROOT / "analysis/24_build_profile_release_specification.py"
PLAN_PATH = ROOT / "docs/profile_release_specification_v0.1.md"
OUTPUT_DIR = ROOT / "outputs/profile_release_specification"
SCHEMA_PATH = OUTPUT_DIR / "profile_release_schema.csv"
REQUIREMENTS_PATH = OUTPUT_DIR / "profile_release_requirements.csv"
QC_PATH = OUTPUT_DIR / "profile_release_qc_matrix.csv"
SUMMARY_PATH = OUTPUT_DIR / "profile_release_summary.md"
SESSION_PATH = OUTPUT_DIR / "session_info.txt"

INPUTS = {
    "materialization_schema": ROOT / "outputs/profile_materialization/materialization_schema.csv",
    "state_registry": ROOT / "outputs/profile_materialization/component_state_resolution_registry.csv",
    "builder_contract": ROOT / "outputs/profile_materialization/profile_builder_contract.md",
    "validation_summary": ROOT / "outputs/profile_validation/profile_validation_summary.md",
    "universe_schema": ROOT / "outputs/target_universe_governance/target_universe_schema.csv",
}

EXPECTED_HASHES = {
    "materialization_schema": "9324374e39fb844c224961db319e4ddf9979512026062ededb5e59e505318701",
    "state_registry": "302fe6fef0eaf76daedbd51cbd9c430cb38bdbe231991f6e2551de0da59a94be",
    "builder_contract": "3b9ae40e670349be387e351426bf5418e7ede8de2ff780e19e63050d2e7bf29b",
    "validation_summary": "e61c67fbe11abca8f02a727a6b4fcd2c44f615b99bbe3910db979b2f20edd296",
    "universe_schema": "f1d611151a1ce7b15f6ff596d74b36a38d26f8503d6fe843f73ae1293babd8f3",
}

ALLOWED_UNTRACKED_FILES = {
    "analysis/24_build_profile_release_specification.py",
    "docs/profile_release_specification_v0.1.md",
}
ALLOWED_UNTRACKED_PREFIX = "outputs/profile_release_specification/"

PROFILE_STATES = "OBSERVED|PARTIAL|MISSING|NOT_QUERIED|CONFLICTING"
PROHIBITED_PROFILE_FIELDS = {
    "score",
    "rank",
    "priority",
    "recommendation",
    "target_selection",
    "therapeutic_direction",
    "aggregate_target_state",
    "aggregate_confidence",
    "completeness_percentage",
    "independent_evidence_vote_count",
    "development_decision",
}

SCHEMA_ROWS = [
    # Release manifest identity and frozen configuration.
    (1, "release_id", "RELEASE_MANIFEST", "REQUIRED", "STRING", "SHA256_DERIVED_ID", "Release configuration", "Stable identity for one complete immutable release bundle.", "Recompute from release spec, universe, profile/evidence versions, input manifest, generator, rules, and serialization hashes.", "Release identity contains no target assessment."),
    (2, "release_spec_version", "RELEASE_MANIFEST", "REQUIRED", "STRING", "PROFILE_RELEASE_SPEC_V0.1", "This specification", "Version of the release contract.", "Exact controlled value.", "Spec versions are not evidence maturity levels."),
    (3, "release_status", "RELEASE_MANIFEST", "REQUIRED", "CATEGORY", "WITHHELD|RELEASED|SUPERSEDED", "Release QC decision", "Lifecycle state of the immutable release bundle.", "RELEASED only after every MUST QC gate passes; failures produce WITHHELD.", "Release status does not state target quality."),
    (4, "target_universe_id", "RELEASE_MANIFEST", "REQUIRED", "STRING", "CONTROLLED_UNIVERSE_ID", "Frozen Task #022-compatible manifest", "Universe family used for this materialization.", "Must resolve to the target manifest artifact.", "Universe membership is scope, not target selection."),
    (5, "target_universe_version", "RELEASE_MANIFEST", "REQUIRED", "STRING", "CONTENT_DERIVED_VERSION", "Frozen target manifest", "Immutable universe snapshot version.", "Must match every released profile input manifest.", "A universe version does not imply scientific merit."),
    (6, "input_manifest_sha256", "RELEASE_MANIFEST", "REQUIRED", "SHA256", "64_HEX_CHARACTERS", "Frozen materialization input manifest", "Hash covering every input artifact, version, rule, and query scope.", "Recompute before and after materialization.", "A hash establishes identity, not validity."),
    (7, "release_qc_artifact_id", "RELEASE_MANIFEST", "REQUIRED", "STRING", "GOVERNED_ARTIFACT_ID", "Release QC bundle", "Artifact identifier for the complete release QC results.", "Must resolve to one frozen QC artifact.", "QC provenance is not evidence about a target."),
    (8, "release_qc_artifact_sha256", "RELEASE_MANIFEST", "REQUIRED", "SHA256", "64_HEX_CHARACTERS", "Release QC bundle", "Hash of the complete release QC results.", "Must match the governed QC artifact.", "Passing software QC does not validate biology."),
    # One target profile identity.
    (9, "profile_id", "PROFILE", "REQUIRED", "STRING", "SHA256_DERIVED_ID", "Immutable entity and version tuple", "Stable identity for one target under one profile/evidence snapshot.", "SHA256(EnsemblID|profile_version|evidence_snapshot_version|input_manifest_sha256|rules_sha256).", "Identity is not an assessment."),
    (10, "EnsemblID", "PROFILE", "REQUIRED", "STRING", "IMMUTABLE_VERSIONED_ENSEMBL_GENE_ID", "Frozen target manifest", "Only entity and join key.", "Exact byte-for-byte match to one included target-manifest row; unique among profiles.", "Symbol cannot replace or repair it."),
    (11, "profile_version", "PROFILE", "REQUIRED", "STRING", "VERSIONED_SCHEMA_AND_SEMANTICS", "Frozen profile configuration", "Version of profile structure and component interpretation semantics.", "Changes whenever required/optional fields or interpretation semantics change.", "A newer profile version is not a better target."),
    (12, "evidence_snapshot_version", "PROFILE", "REQUIRED", "STRING", "CONTENT_DERIVED_EVIDENCE_SNAPSHOT", "Frozen evidence input manifest", "Version identifying the exact evidence, source releases, query scopes, and hashes.", "Derived from canonical ordered evidence artifact IDs/hashes and source versions.", "Snapshot recency is not evidence strength."),
    # Long-form component identity/state.
    (13, "component_id", "COMPONENT", "REQUIRED", "STRING", "CONTROLLED_TASK020_COMPONENT_ID", "Frozen component registry", "Component represented by this long-form row.", "Exactly 11 unique component rows per profile in frozen order.", "Components are organizational blocks, not votes."),
    (14, "component_state", "COMPONENT", "REQUIRED", "CATEGORY", PROFILE_STATES, "Executable state rules", "Evidence availability/uncertainty state.", "Exactly one state per component under frozen precedence.", "States are non-numerical and not favorable/unfavorable."),
    (15, "state_rule_id", "COMPONENT", "REQUIRED", "STRING", "EXECUTABLE_VERSIONED_RULE_ID", "Frozen executable rule registry", "Exact rule that resolved the component state.", "Must resolve to tested code/configuration and the Task #021 semantic predicate.", "Free-text or LLM judgment cannot resolve state."),
    (16, "state_rule_version", "COMPONENT", "REQUIRED", "STRING", "VERSIONED_VALUE", "Frozen executable rule registry", "Version of the state-resolution implementation.", "Must match release-level rules artifact and hash.", "Rule version is provenance, not confidence."),
    (17, "state_rationale", "COMPONENT", "REQUIRED", "STRING", "DETERMINISTIC_BOUNDED_TEMPLATE", "Resolved rule and linked evidence", "Traceable explanation of the satisfied predicate and unresolved limitations.", "Generated by a frozen template; must cite linked IDs and cannot exceed evidence meaning.", "No therapeutic conclusion permitted."),
    # Evidence lineage.
    (18, "claim_ids", "PROVENANCE", "REQUIRED", "PIPE_DELIMITED_ID_LIST", "CLAIM_IDS_OR_NONE", "Frozen claim registry", "Bounded claim identifiers linked to the component.", "Unique, lexically sorted, and resolvable to EnsemblID/component domains.", "Claim count is not evidence strength."),
    (19, "evidence_record_ids", "PROVENANCE", "REQUIRED", "PIPE_DELIMITED_ID_LIST", "RECORD_IDS_OR_NONE", "Frozen evidence-record registry", "Atomic evidence records represented by the component.", "Unique, sorted, and each record resolves through a claim to the same EnsemblID.", "Records are not independent votes."),
    (20, "source_entity_ids", "PROVENANCE", "REQUIRED", "PIPE_DELIMITED_ID_LIST", "SOURCE_IDS_OR_NONE", "Frozen source registry", "Source entities underlying linked records.", "Every observed record resolves to one source entity.", "Different sources may remain dependent."),
    (21, "source_versions", "PROVENANCE", "REQUIRED", "PIPE_DELIMITED_KEY_VALUE_LIST", "SOURCE_ID_EQUALS_VERSION_OR_UNKNOWN", "Frozen source registry", "Explicit source release/version for linked records.", "One entry per source ID; UNKNOWN blocks provenance_complete=TRUE.", "A version does not establish quality."),
    (22, "artifact_ids", "PROVENANCE", "REQUIRED", "PIPE_DELIMITED_ID_LIST", "GOVERNED_ARTIFACT_IDS", "Frozen input manifest", "Artifacts required to reconstruct component evidence.", "Unique and sorted; includes claims, records, sources, dependencies, rules, and source data as applicable.", "Artifact count is not evidence quantity."),
    (23, "artifact_sha256s", "PROVENANCE", "REQUIRED", "PIPE_DELIMITED_KEY_VALUE_LIST", "ARTIFACT_ID_EQUALS_SHA256", "Frozen input manifest", "Explicit artifact-to-hash mapping.", "Exactly one verified hash per artifact ID; positional unpaired hash lists are prohibited.", "Hashes do not establish scientific validity."),
    # Task #023 relational-preservation extensions.
    (24, "record_missingness_pairs", "UNCERTAINTY", "REQUIRED", "PIPE_DELIMITED_KEY_VALUE_LIST", "RECORD_ID_EQUALS_MISSINGNESS", "Frozen evidence-record registry", "Exact record-level missingness mapping.", "Every evidence_record_id appears exactly once with OBSERVED, NOT_FOUND, NOT_QUERIED, NOT_APPLICABLE, or UNKNOWN.", "Missingness is not negative evidence."),
    (25, "record_uncertainty_pairs", "UNCERTAINTY", "REQUIRED", "PIPE_DELIMITED_KEY_VALUE_LIST", "RECORD_ID_EQUALS_UNCERTAINTY", "Frozen evidence-record registry", "Exact record-level uncertainty mapping.", "Every evidence_record_id maps to its controlled source uncertainty.", "Uncertainty is not a numerical penalty."),
    (26, "dependency_edge_ids", "DEPENDENCY", "REQUIRED", "PIPE_DELIMITED_ID_LIST", "DEPENDENCY_IDS_OR_NONE", "Frozen dependency graph", "Exact dependency edges induced among component records.", "Every edge resolves to two linked evidence_record_ids; no edge is inferred or omitted.", "No edge does not prove independence."),
    (27, "dependency_relationships", "DEPENDENCY", "REQUIRED", "PIPE_DELIMITED_KEY_VALUE_LIST", "DEPENDENCY_ID_EQUALS_RELATIONSHIP", "Frozen dependency graph", "Exact edge-to-relationship mapping.", "One mapping per dependency_edge_id.", "Relationships are not numerical weights."),
    (28, "dependency_levels", "DEPENDENCY", "REQUIRED", "PIPE_DELIMITED_KEY_VALUE_LIST", "DEPENDENCY_ID_EQUALS_LEVEL", "Frozen dependency graph", "Exact edge-to-qualitative dependency level mapping.", "One mapping per dependency_edge_id; UNKNOWN remains UNKNOWN.", "Dependency level is not a score."),
    (29, "conflict_present", "UNCERTAINTY", "REQUIRED", "CATEGORY", "TRUE|FALSE|UNKNOWN", "Executable component comparison rule", "Whether a material conflict is documented.", "Must reconcile with component_state and conflict IDs.", "FALSE means no defined conflict found, not universal agreement."),
    (30, "conflict_record_ids", "UNCERTAINTY", "REQUIRED", "PIPE_DELIMITED_ID_LIST", "RECORD_IDS_OR_NONE", "Frozen conflict rule", "Records participating in a component conflict.", "Required when conflict_present=TRUE; subset of evidence_record_ids.", "Conflicting records cannot be discarded or averaged away."),
    (31, "conflict_description", "UNCERTAINTY", "REQUIRED", "STRING", "DETERMINISTIC_TEXT_OR_NONE", "Frozen conflict rule/template", "Bounded description of the conflict and comparison scope.", "Required for TRUE; NONE otherwise unless UNKNOWN needs an explicit limitation.", "Does not choose a preferred record."),
    (32, "provenance_complete", "PROVENANCE", "REQUIRED", "CATEGORY", "TRUE|FALSE|UNKNOWN", "Release provenance validation", "Whether minimum component provenance is present.", "TRUE requires complete record/source/artifact/rule mappings.", "Complete provenance does not mean strong evidence."),
    (33, "evidence_record_count", "AUDIT", "REQUIRED", "INTEGER", "NONNEGATIVE_INTEGER", "Exact evidence_record_ids count", "Audit count of linked atomic records.", "Must equal the number of non-NONE record IDs.", "Quantity is not quality or independence."),
    (34, "observed_record_count", "AUDIT", "REQUIRED", "INTEGER", "NONNEGATIVE_INTEGER", "record_missingness_pairs", "Audit count whose record-level state is OBSERVED.", "Must not exceed evidence_record_count.", "More observed records do not imply stronger support."),
    (35, "maturity_description", "INTERPRETATION", "REQUIRED", "STRING", "BOUNDED_DETERMINISTIC_TEXT", "Frozen component template", "What evidence is characterized and what remains unresolved.", "Cannot change component_state or aggregate components.", "Maturity is availability, not target quality."),
    # Generator and serialization provenance.
    (36, "generator_id", "REPRODUCIBILITY", "REQUIRED", "STRING", "GOVERNED_GENERATOR_ID", "Frozen run configuration", "Identity of the materialization generator.", "Must resolve to source-controlled code.", "Generator identity does not validate scientific logic."),
    (37, "generator_version", "REPRODUCIBILITY", "REQUIRED", "STRING", "VERSIONED_VALUE", "Frozen run configuration", "Version of materialization behavior.", "Exact value frozen before generation.", "Version is not evidence maturity."),
    (38, "generator_sha256", "REPRODUCIBILITY", "REQUIRED", "SHA256", "64_HEX_CHARACTERS", "Frozen generator artifact", "Content hash of executed generator.", "Must match the executed file.", "A hash does not prove correct logic."),
    (39, "rules_sha256", "REPRODUCIBILITY", "REQUIRED", "SHA256", "64_HEX_CHARACTERS", "Executable rule artifact", "Hash covering executable state and rationale rules.", "Used in profile_id and verified before/after generation.", "Rules cannot contain hidden aggregation."),
    (40, "generated_at_utc", "REPRODUCIBILITY", "REQUIRED", "DATETIME", "FROZEN_ISO8601_UTC", "Frozen run configuration", "Materialization snapshot time.", "Copied from configuration; wall clock cannot alter rows.", "Recency is not relevance."),
    (41, "serialization_version", "REPRODUCIBILITY", "REQUIRED", "STRING", "CANONICAL_CSV_VERSION", "Frozen run configuration", "Canonical output-format version.", "Controls header, row order, quoting, lists, booleans, integers, and sentinels.", "Format does not change evidence meaning."),
    # Optional display-only annotations.
    (42, "Symbol", "OPTIONAL_ANNOTATION", "OPTIONAL", "STRING", "SOURCE_VALUE|NOT_FOUND", "Frozen identity annotation", "Human-readable display annotation.", "Copied after EnsemblID joins; never used as a key or repair.", "Symbol is not identity."),
    (43, "gene_type", "OPTIONAL_ANNOTATION", "OPTIONAL", "STRING", "SOURCE_VALUE|NOT_FOUND", "Frozen identity annotation", "Source-provided gene-type display annotation.", "Copied without recoding; cannot alter component state.", "Gene type does not imply relevance or druggability."),
    (44, "external_identifier_annotations", "OPTIONAL_ANNOTATION", "OPTIONAL", "JSON", "SOURCE_GROUNDED_IDENTIFIERS_OR_NONE", "Frozen identifier mapping", "Display-only external identifiers with their source/status.", "No symbol inference; ambiguous and missing mappings remain explicit.", "External IDs do not replace EnsemblID."),
    (45, "display_note", "OPTIONAL_ANNOTATION", "OPTIONAL", "STRING", "DETERMINISTIC_BOUNDED_TEXT_OR_NONE", "Frozen display template", "Non-interpretive display clarification.", "Cannot introduce claims, ordering, recommendations, or therapeutic meaning.", "Presentation only."),
    # Prohibited profile fields: present only as release-schema prohibitions.
    (46, "score", "PROHIBITED", "PROHIBITED", "NONE", "MUST_NOT_EXIST", "Release safety boundary", "Any numerical or categorical target score.", "Header/value absence required.", "No scoring in evidence profiles."),
    (47, "rank", "PROHIBITED", "PROHIBITED", "NONE", "MUST_NOT_EXIST", "Release safety boundary", "Any target ordering field.", "Header/value absence required.", "No ranking in evidence profiles."),
    (48, "priority", "PROHIBITED", "PROHIBITED", "NONE", "MUST_NOT_EXIST", "Release safety boundary", "Any priority label or tier.", "Header/value absence required.", "No prioritization in evidence profiles."),
    (49, "recommendation", "PROHIBITED", "PROHIBITED", "NONE", "MUST_NOT_EXIST", "Release safety boundary", "Any recommendation field.", "Header/value absence required.", "No target recommendation."),
    (50, "target_selection", "PROHIBITED", "PROHIBITED", "NONE", "MUST_NOT_EXIST", "Release safety boundary", "Any target selection decision.", "Header/value absence required.", "Universe membership is not selection."),
    (51, "therapeutic_direction", "PROHIBITED", "PROHIBITED", "NONE", "MUST_NOT_EXIST", "Release safety boundary", "Any inferred therapeutic mechanism direction.", "Header/value absence required.", "No therapeutic-direction inference."),
    (52, "aggregate_target_state", "PROHIBITED", "PROHIBITED", "NONE", "MUST_NOT_EXIST", "Hidden-aggregation boundary", "Any combined overall profile state.", "Header/value absence required.", "Components cannot be collapsed into one judgment."),
    (53, "aggregate_confidence", "PROHIBITED", "PROHIBITED", "NONE", "MUST_NOT_EXIST", "Hidden-aggregation boundary", "Any combined confidence metric.", "Header/value absence required.", "Uncertainty cannot become a hidden score."),
    (54, "completeness_percentage", "PROHIBITED", "PROHIBITED", "NONE", "MUST_NOT_EXIST", "Hidden-aggregation boundary", "Any profile-completeness percentage.", "Header/value absence required.", "Completeness is not quality."),
    (55, "independent_evidence_vote_count", "PROHIBITED", "PROHIBITED", "NONE", "MUST_NOT_EXIST", "Dependency boundary", "Any count treating records/domains as independent votes.", "Header/value absence required.", "Independence requires explicit reviewed lineage."),
    (56, "development_decision", "PROHIBITED", "PROHIBITED", "NONE", "MUST_NOT_EXIST", "Interpretation boundary", "Any progress/stop or development decision.", "Header/value absence required.", "Evidence organization is separate from decisions."),
]

REQUIREMENT_ROWS = [
    ("REL_ID_001", "IDENTITY", "PROFILE", "MUST", "EnsemblID is the only immutable entity/join key and must match the frozen included target-manifest value byte-for-byte.", "Prevents identity drift and symbol joins.", "Unique-key and exact-value comparison to target manifest.", "WITHHOLD_RELEASE", "Task #022 universe schema and Task #021 contract"),
    ("REL_ID_002", "IDENTITY", "PROFILE", "MUST", "profile_id uses EnsemblID, profile_version, evidence_snapshot_version, input_manifest_sha256, and rules_sha256 in the canonical formula.", "A profile changes identity when evidence or rules change.", "Recompute every profile_id.", "WITHHOLD_RELEASE", "Task #021 deterministic identity refined for explicit evidence snapshot"),
    ("REL_ID_003", "IDENTITY", "RELEASE", "MUST", "release_id is content-derived from the complete frozen release configuration and cannot use randomness or wall time.", "Makes the release reproducible and immutable.", "Recompute release_id from canonical configuration.", "WITHHOLD_RELEASE", "Task #021 determinism contract"),
    ("REL_ID_004", "IDENTITY", "PROFILE", "MUST", "Each EnsemblID has exactly one profile_id and exactly 11 unique component rows.", "Prevents silent omission or duplication.", "Cardinality and composite-key checks.", "WITHHOLD_RELEASE", "Task #021 cardinality contract"),
    ("REL_VER_001", "VERSIONING", "PROFILE", "MUST", "profile_version changes when schema, component semantics, or interpretation boundaries change.", "Separates structural meaning from evidence updates.", "Compare version manifest to schema/rule hashes.", "WITHHOLD_RELEASE", "Release identity model"),
    ("REL_VER_002", "VERSIONING", "PROFILE", "MUST", "evidence_snapshot_version is content-derived from ordered evidence artifacts, source versions, and query scopes.", "Prevents two evidence snapshots sharing an ambiguous label.", "Recompute snapshot version from evidence manifest.", "WITHHOLD_RELEASE", "Release identity model"),
    ("REL_VER_003", "VERSIONING", "RELEASE", "MUST", "Prior released bundles are immutable; changed inputs or rules create a new release_id.", "Preserves audit history.", "Artifact-registry and hash comparison.", "WITHHOLD_RELEASE", "Task #018/Task #022 governance principles"),
    ("REL_STR_001", "STRUCTURE", "COMPONENT", "MUST", "Required fields are present, nonblank, and conform to controlled data types and sentinels.", "Avoids silent information loss.", "Schema validation.", "WITHHOLD_RELEASE", "profile_release_schema.csv"),
    ("REL_STR_002", "STRUCTURE", "COMPONENT", "MUST", "Optional annotations cannot affect joins, state resolution, ordering, or release eligibility.", "Separates display from evidence meaning.", "Static code/dataflow check plus mutation test.", "WITHHOLD_RELEASE", "Task #022 identifier policy"),
    ("REL_STR_003", "STRUCTURE", "PROFILE", "MUST_NOT", "No prohibited field, alias, derived equivalent, or hidden aggregation may appear in profile data or sidecars.", "Prevents evidence organization becoming prioritization.", "Header/schema scan and prohibited-derivation tests.", "WITHHOLD_RELEASE", "Task #020–#024 interpretation boundaries"),
    ("REL_LIN_001", "LINEAGE", "COMPONENT", "MUST", "Every claim_id resolves to the same EnsemblID and an allowed component evidence domain.", "Preserves bounded claim meaning.", "Referential-integrity join by IDs only.", "WITHHOLD_RELEASE", "Task #021 evidence selection"),
    ("REL_LIN_002", "LINEAGE", "COMPONENT", "MUST", "Every evidence_record_id resolves to a linked claim_id and source_entity_id.", "Preserves atomic evidence lineage.", "Referential-integrity validation.", "WITHHOLD_RELEASE", "Task #021 provenance propagation"),
    ("REL_LIN_003", "LINEAGE", "COMPONENT", "MUST", "Records may be deduplicated only by identical record_id; reuse across components retains the same ID.", "Prevents unsupported merging or double creation.", "Record-ID uniqueness and reuse audit.", "WITHHOLD_RELEASE", "Task #021 evidence selection"),
    ("REL_LIN_004", "LINEAGE", "COMPONENT", "MUST", "Artifact IDs are explicitly paired with hashes and include every registry needed to reconstruct lineage.", "Makes provenance independently checkable.", "Artifact resolution and hash verification.", "WITHHOLD_RELEASE", "Task #023 relational limitation"),
    ("REL_DEP_001", "DEPENDENCY", "COMPONENT", "MUST", "dependency_edge_ids encode the exact induced graph among component evidence records.", "Retains which record pair is dependent.", "Recompute induced graph from frozen dependency registry.", "WITHHOLD_RELEASE", "Task #023 dependency limitation"),
    ("REL_DEP_002", "DEPENDENCY", "COMPONENT", "MUST", "Each dependency ID maps to its exact endpoints, relationship, level, and review status in the frozen graph.", "Prevents lossy category-only dependency representation.", "Edge-level referential validation.", "WITHHOLD_RELEASE", "Task #023 validation finding"),
    ("REL_DEP_003", "DEPENDENCY", "COMPONENT", "MUST_NOT", "Absence of an edge cannot be emitted or interpreted as INDEPENDENT.", "Unknown lineage is not independence.", "Rule and output scan.", "WITHHOLD_RELEASE", "Task #021 dependency contract"),
    ("REL_MIS_001", "MISSINGNESS", "COMPONENT", "MUST", "Every record has an explicit record_id=missingness mapping.", "Preserves record-level meaning that set-like lists cannot encode.", "Reconstruct and compare to frozen record registry.", "WITHHOLD_RELEASE", "Task #023 missingness limitation"),
    ("REL_MIS_002", "MISSINGNESS", "COMPONENT", "MUST", "OBSERVED, PARTIAL, MISSING, NOT_QUERIED, and CONFLICTING remain distinct component states.", "Prevents missingness collapse.", "Controlled-vocabulary and state-rule validation.", "WITHHOLD_RELEASE", "Task #021 state model"),
    ("REL_MIS_003", "MISSINGNESS", "COMPONENT", "MUST", "MISSING requires completed defined query scope with no qualifying record and no unknown/failure.", "Separates absence after assessment from non-acquisition.", "Coverage manifest and rule predicate test.", "WITHHOLD_RELEASE", "Task #021 MISSING predicate"),
    ("REL_MIS_004", "MISSINGNESS", "COMPONENT", "MUST", "NOT_QUERIED requires no eligible acquisition or valid assessment and cannot be inferred from zero/blank.", "Preserves acquisition boundary.", "Query-log and rule predicate test.", "WITHHOLD_RELEASE", "Task #021 NOT_QUERIED predicate"),
    ("REL_MIS_005", "MISSINGNESS", "COMPONENT", "MUST", "Conflicting records, IDs, and comparison rule are retained without choosing or averaging.", "Preserves uncertainty and avoids hidden adjudication.", "Conflict-record subset and rationale validation.", "WITHHOLD_RELEASE", "Task #021 CONFLICTING predicate"),
    ("REL_PROV_001", "PROVENANCE", "RELEASE", "MUST", "Generator ID, version, executable hash, rules version/hash, and serialization version are frozen before materialization.", "Makes the computation identifiable.", "Run-manifest preflight and postflight hash checks.", "WITHHOLD_RELEASE", "Task #021 run configuration"),
    ("REL_PROV_002", "PROVENANCE", "COMPONENT", "MUST", "Every linked source has an explicit version; UNKNOWN prevents provenance_complete=TRUE.", "Avoids unversioned evidence claims.", "Source-version reconciliation.", "WITHHOLD_RELEASE", "Task #021 source contract"),
    ("REL_PROV_003", "PROVENANCE", "RELEASE", "MUST", "The release bundle includes or resolvably references the frozen target manifest, schema, rules, claims, records, sources, dependency graph, artifact manifest, QC, and session metadata.", "A profile must remain reconstructible.", "Release-bundle inventory check.", "WITHHOLD_RELEASE", "Task #023 relational validation"),
    ("REL_RULE_001", "RULES", "RELEASE", "MUST", "All 55 component/state predicates have executable, reviewed, versioned implementations tied to the frozen Task #021 semantic predicates.", "Controlled prose alone cannot guarantee deterministic execution.", "Unit/fixture tests and exact predicate-ID/hash mapping.", "WITHHOLD_RELEASE", "Task #023 representation limitation"),
    ("REL_RULE_002", "RULES", "COMPONENT", "MUST", "State precedence is CONFLICTING, OBSERVED, MISSING, PARTIAL, NOT_QUERIED and exactly one state resolves.", "Makes resolution deterministic.", "Precedence and mutual-resolution tests.", "WITHHOLD_RELEASE", "Task #021 state registry"),
    ("REL_DET_001", "DETERMINISM", "RELEASE", "MUST", "Identical frozen inputs, generator, rules, timestamp, and serialization produce byte-identical complete release bundles.", "Enables reproducible recovery.", "Independent clean regeneration and SHA256 comparison.", "WITHHOLD_RELEASE", "Task #021 and Task #023 determinism"),
    ("REL_DET_002", "DETERMINISM", "COMPONENT", "MUST", "Target order follows the frozen manifest; component order follows the frozen registry; list values are unique and canonically ordered.", "Prevents nondeterministic row/list order.", "Canonical-order validation.", "WITHHOLD_RELEASE", "Task #021 canonical serialization"),
    ("REL_DET_003", "DETERMINISM", "RELEASE", "MUST_NOT", "Wall clock, locale, filesystem traversal, randomness, process ID, Symbol, or LLM output may influence profile bytes.", "Removes non-reproducible inputs.", "Environment mutation tests and static code review.", "WITHHOLD_RELEASE", "Task #021 deterministic contract"),
    ("REL_QC_001", "RELEASE_QC", "RELEASE", "MUST", "Identity, lineage, dependency, missingness, provenance, interpretation-safety, and regeneration gates all pass before status=RELEASED.", "No partial release of an invalid bundle.", "QC matrix completion and zero FAIL checks.", "WITHHOLD_RELEASE", "Task #023 validation domains"),
    ("REL_QC_002", "RELEASE_QC", "RELEASE", "MUST", "Input hashes are verified before and after generation and output hashes are frozen only after canonical serialization.", "Detects mid-run mutation.", "Preflight/postflight hash comparison.", "WITHHOLD_RELEASE", "Task #021 QC contract"),
    ("REL_INT_001", "INTERPRETATION", "PROFILE", "MUST_NOT", "Component states or record counts may not be combined into a score, rank, priority, recommendation, overall state, or completeness percentage.", "Prevents hidden prioritization.", "Schema, code, and output derivation audit.", "WITHHOLD_RELEASE", "Task #020–#024 non-inference rules"),
    ("REL_INT_002", "INTERPRETATION", "PROFILE", "MUST_NOT", "OBSERVED may not be labeled favorable and MISSING/NOT_QUERIED may not be labeled unfavorable or negative.", "Preserves missingness meaning.", "Template and output text scan.", "WITHHOLD_RELEASE", "Task #021 interpretation boundary"),
    ("REL_INT_003", "INTERPRETATION", "PROFILE", "MUST_NOT", "Profiles may not assert causality, efficacy, safety, clinical benefit, therapeutic direction, or target recommendation.", "Separates evidence organization from decision interpretation.", "Controlled-language and prohibited-claim scan.", "WITHHOLD_RELEASE", "Task #019–#024 boundaries"),
]

QC_ROWS = [
    ("QC_PRE_001", "PREFLIGHT", "RELEASE", "All declared input artifacts exist and match ID, size, SHA256, and version.", "ZERO_MISMATCHES", "input_manifest|artifact_manifest", "BLOCKING", "WITHHOLD_RELEASE", "TRUE"),
    ("QC_PRE_002", "PREFLIGHT", "RELEASE", "Target manifest is released, unique by EnsemblID, explicitly ordered, and contains one universe version.", "ALL_PASS", "target_manifest|target_manifest_qc", "BLOCKING", "WITHHOLD_RELEASE", "TRUE"),
    ("QC_PRE_003", "PREFLIGHT", "RELEASE", "Executed generator and executable rule artifacts match their frozen hashes.", "EXACT_HASH_MATCH", "generator|rule_artifact", "BLOCKING", "WITHHOLD_RELEASE", "TRUE"),
    ("QC_ID_001", "IDENTITY", "PROFILE", "Every profile EnsemblID matches one INCLUDED target-manifest entity; no Symbol join occurred.", "N_OF_N_MATCH", "profile_data|target_manifest", "BLOCKING", "WITHHOLD_RELEASE", "TRUE"),
    ("QC_ID_002", "IDENTITY", "PROFILE", "profile_id recomputes exactly and is unique.", "N_UNIQUE_VALID_IDS", "profile_data|input_manifest|rules", "BLOCKING", "WITHHOLD_RELEASE", "TRUE"),
    ("QC_ID_003", "IDENTITY", "PROFILE", "Exactly 11 unique component rows exist per profile and no extra target is present.", "N_TIMES_11_ROWS", "profile_data|component_registry", "BLOCKING", "WITHHOLD_RELEASE", "TRUE"),
    ("QC_STR_001", "STRUCTURE", "COMPONENT", "Required fields are present/nonblank; optional fields conform; prohibited fields and aliases are absent.", "ZERO_SCHEMA_VIOLATIONS", "profile_data|release_schema", "BLOCKING", "WITHHOLD_RELEASE", "TRUE"),
    ("QC_STR_002", "STRUCTURE", "COMPONENT", "Canonical types, booleans, integers, timestamps, sentinels, and list ordering validate.", "ZERO_SERIALIZATION_VIOLATIONS", "profile_data|serialization_config", "BLOCKING", "WITHHOLD_RELEASE", "TRUE"),
    ("QC_LIN_001", "LINEAGE", "COMPONENT", "Every claim ID resolves to the component EnsemblID and allowed domain.", "ALL_CLAIMS_RESOLVE", "profile_data|claim_registry", "BLOCKING", "WITHHOLD_RELEASE", "TRUE"),
    ("QC_LIN_002", "LINEAGE", "COMPONENT", "Every record resolves to a linked claim/source and retained source-native identifier.", "ALL_RECORDS_RESOLVE", "profile_data|record_registry|source_registry", "BLOCKING", "WITHHOLD_RELEASE", "TRUE"),
    ("QC_LIN_003", "LINEAGE", "COMPONENT", "Record IDs are unique within components and reused rather than duplicated across components.", "ZERO_UNSUPPORTED_DUPLICATES", "profile_data|record_registry", "BLOCKING", "WITHHOLD_RELEASE", "TRUE"),
    ("QC_ART_001", "PROVENANCE", "COMPONENT", "Every artifact ID has an explicit verified ID=SHA256 mapping and reconstructs linked evidence.", "ALL_ARTIFACTS_RESOLVE", "profile_data|artifact_manifest", "BLOCKING", "WITHHOLD_RELEASE", "TRUE"),
    ("QC_SRC_001", "PROVENANCE", "COMPONENT", "Every source ID has an explicit source version and all profile source sets reconcile to records.", "ALL_SOURCES_VERSIONED", "profile_data|source_registry", "BLOCKING", "WITHHOLD_RELEASE", "TRUE"),
    ("QC_DEP_001", "DEPENDENCY", "COMPONENT", "Induced dependency edge IDs exactly match the frozen graph for component record sets.", "EXACT_EDGE_SET_MATCH", "profile_data|dependency_graph", "BLOCKING", "WITHHOLD_RELEASE", "TRUE"),
    ("QC_DEP_002", "DEPENDENCY", "COMPONENT", "Each edge retains endpoints, relationship, level, and review status; UNKNOWN remains UNKNOWN.", "ALL_EDGE_MAPPINGS_MATCH", "profile_data|dependency_graph", "BLOCKING", "WITHHOLD_RELEASE", "TRUE"),
    ("QC_DEP_003", "DEPENDENCY", "RELEASE", "No code or output infers INDEPENDENT from an absent edge or counts dependent records as votes.", "ZERO_INDEPENDENCE_INFERENCE", "generator|rules|profile_data", "BLOCKING", "WITHHOLD_RELEASE", "TRUE"),
    ("QC_MIS_001", "MISSINGNESS", "COMPONENT", "Every record_id=missingness and record_id=uncertainty pair matches the frozen record registry.", "ALL_RECORD_STATES_MATCH", "profile_data|record_registry", "BLOCKING", "WITHHOLD_RELEASE", "TRUE"),
    ("QC_MIS_002", "MISSINGNESS", "COMPONENT", "All five component states are controlled and exactly one rule resolves per component.", "ONE_VALID_STATE_PER_COMPONENT", "profile_data|executable_rules", "BLOCKING", "WITHHOLD_RELEASE", "TRUE"),
    ("QC_MIS_003", "MISSINGNESS", "COMPONENT", "MISSING and NOT_QUERIED predicates reconcile to frozen query coverage and failure states.", "ZERO_STATE_COLLAPSE", "profile_data|query_manifest|executable_rules", "BLOCKING", "WITHHOLD_RELEASE", "TRUE"),
    ("QC_CON_001", "CONFLICT", "COMPONENT", "Conflict states retain every conflict record and exact rule; no record is chosen or averaged away.", "ALL_CONFLICTS_RECONCILE", "profile_data|record_registry|rules", "BLOCKING", "WITHHOLD_RELEASE", "TRUE"),
    ("QC_RULE_001", "RULES", "RELEASE", "All 55 Task #021 semantic predicates map one-to-one to executable reviewed rules and fixture tests.", "55_OF_55_PASS", "state_registry|executable_rules|rule_tests", "BLOCKING", "WITHHOLD_RELEASE", "TRUE"),
    ("QC_RULE_002", "RULES", "RELEASE", "Rule precedence and mutually exclusive final resolution pass for every component/state fixture.", "ALL_RULE_TESTS_PASS", "executable_rules|rule_tests", "BLOCKING", "WITHHOLD_RELEASE", "TRUE"),
    ("QC_CNT_001", "COUNTS", "COMPONENT", "Evidence and observed record counts reconcile exactly to IDs and record-level mappings.", "ZERO_COUNT_MISMATCHES", "profile_data", "BLOCKING", "WITHHOLD_RELEASE", "TRUE"),
    ("QC_INT_001", "INTERPRETATION_SAFETY", "RELEASE", "No score, rank, priority, recommendation, selection, direction, overall state, confidence aggregate, or completeness percentage exists.", "ZERO_PROHIBITED_FIELDS_OR_DERIVATIONS", "schema|generator|profile_data|sidecars", "BLOCKING", "WITHHOLD_RELEASE", "TRUE"),
    ("QC_INT_002", "INTERPRETATION_SAFETY", "COMPONENT", "State rationales and maturity text are deterministic, source-bounded, and contain no prohibited conclusions.", "ZERO_UNSUPPORTED_CLAIMS", "profile_data|templates|evidence_records", "BLOCKING", "WITHHOLD_RELEASE", "TRUE"),
    ("QC_DET_001", "DETERMINISM", "RELEASE", "Independent clean regeneration yields byte-identical profile data and sidecars.", "ALL_OUTPUT_SHA256_MATCH", "recovery_run|release_bundle", "BLOCKING", "WITHHOLD_RELEASE", "TRUE"),
    ("QC_DET_002", "DETERMINISM", "RELEASE", "Input hashes remain unchanged before/after and output hashes match the release manifest.", "ZERO_HASH_DRIFT", "preflight|postflight|release_manifest", "BLOCKING", "WITHHOLD_RELEASE", "TRUE"),
    ("QC_BND_001", "BUNDLE", "RELEASE", "Every required release artifact is present/resolvable and the bundle inventory contains no undeclared file.", "EXACT_INVENTORY_MATCH", "release_manifest|artifact_manifest", "BLOCKING", "WITHHOLD_RELEASE", "TRUE"),
    ("QC_REL_001", "RELEASE_DECISION", "RELEASE", "All blocking QC results pass and are frozen before release_status becomes RELEASED.", "ZERO_BLOCKING_FAILURES", "release_qc_artifact", "BLOCKING", "WITHHOLD_RELEASE", "TRUE"),
]


def fail(message: str) -> None:
    raise RuntimeError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def run_git(*args: str, check: bool = True) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    if check and result.returncode != 0:
        fail(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def git_paths(*args: str) -> set[str]:
    return {line for line in run_git(*args).splitlines() if line}


def validate_repository() -> dict[str, str]:
    root = Path(run_git("rev-parse", "--show-toplevel")).resolve()
    branch = run_git("branch", "--show-current")
    head = run_git("rev-parse", "HEAD")
    base = run_git("rev-parse", TASK023_BASE_COMMIT)
    remote = run_git("remote", "get-url", "origin")
    if root != ROOT or branch != EXPECTED_BRANCH or EXPECTED_REMOTE_FRAGMENT not in remote:
        fail(f"Repository identity mismatch: root={root}, branch={branch}, remote={remote}")
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", base, head], cwd=ROOT, check=False)
    if ancestor.returncode != 0:
        fail("Frozen Task #023 base commit is not an ancestor of HEAD.")
    if run_git("diff", "--name-only") or run_git("diff", "--cached", "--name-only"):
        fail("Tracked or staged changes exist; previous artifacts will not be modified.")
    changed_inputs = git_paths(
        "diff", "--name-only", f"{base}..{head}", "--",
        *(relative(path) for path in INPUTS.values()),
    )
    if changed_inputs:
        fail(f"Frozen Task #020–#023 inputs changed after base commit: {sorted(changed_inputs)}")
    untracked = git_paths("ls-files", "--others", "--exclude-standard")
    unexpected = {
        path for path in untracked
        if path not in ALLOWED_UNTRACKED_FILES and not path.startswith(ALLOWED_UNTRACKED_PREFIX)
    }
    if unexpected:
        fail(f"Unexpected untracked files: {sorted(unexpected)}")
    return {
        "root": str(root), "branch": branch, "head": head, "base": base,
        "remote": remote, "snapshot": run_git("show", "-s", "--format=%cI", base),
    }


def validate_hashes() -> dict[str, str]:
    observed = {}
    for name, path in INPUTS.items():
        if not path.is_file():
            fail(f"Missing frozen input: {relative(path)}")
        digest = sha256(path)
        if digest != EXPECTED_HASHES[name]:
            fail(f"Frozen input hash mismatch for {relative(path)}: {digest}")
        observed[name] = digest
    return observed


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate_inputs() -> dict[str, int]:
    materialization = read_csv(INPUTS["materialization_schema"])
    states = read_csv(INPUTS["state_registry"])
    universe = read_csv(INPUTS["universe_schema"])
    if len(materialization) != 15 or len(states) != 55 or len(universe) != 17:
        fail("Frozen schema/rule cardinalities changed.")
    state_pairs = {(row["component_id"], row["resolved_state"]) for row in states}
    if len(state_pairs) != 55 or {row["resolved_state"] for row in states} != set(PROFILE_STATES.split("|")):
        fail("Frozen component-state architecture changed.")
    universe_ensembl = next((row for row in universe if row["field_name"] == "EnsemblID"), None)
    if not universe_ensembl or "only immutable entity and join key" not in universe_ensembl["definition"].lower():
        fail("Frozen target-universe EnsemblID policy changed.")

    contract = INPUTS["builder_contract"].read_text(encoding="utf-8")
    contract_phrases = (
        "SHA256(EnsemblID + \"|\" + profile_version + \"|\" + input_manifest_hash + \"|\" + rules_hash)",
        "Every profile row must carry:",
        "Records are deduplicated only when `record_id` is identical.",
        "byte-identical recovery generation",
    )
    if any(phrase not in contract for phrase in contract_phrases):
        fail("Frozen profile-builder contract boundary changed.")
    validation = INPUTS["validation_summary"].read_text(encoding="utf-8")
    validation_phrases = (
        "PASS WITH REPRESENTATION LIMITATIONS",
        "State predicates are controlled prose.",
        "Profiles are relational, not standalone.",
        "Canonical byte determinism | PASS",
    )
    if any(phrase not in validation for phrase in validation_phrases):
        fail("Frozen Task #023 validation findings changed.")
    return {
        "materialization_contract_rows": len(materialization),
        "component_state_rules": len(states),
        "target_universe_schema_fields": len(universe),
        "builder_contract_boundaries": len(contract_phrases),
        "validation_findings_consumed": len(validation_phrases),
    }


def schema_records() -> list[dict[str, str]]:
    fields = [
        "field_order", "field_name", "record_scope", "requirement_level",
        "data_type", "allowed_values", "source_or_derivation", "definition",
        "release_validation", "interpretation_boundary",
    ]
    return [dict(zip(fields, map(str, row))) for row in SCHEMA_ROWS]


def requirement_records() -> list[dict[str, str]]:
    fields = [
        "requirement_id", "requirement_category", "applies_to", "normative_level",
        "requirement", "scientific_rationale", "validation_method", "failure_action",
        "frozen_provenance_basis",
    ]
    return [dict(zip(fields, map(str, row))) for row in REQUIREMENT_ROWS]


def qc_records() -> list[dict[str, str]]:
    fields = [
        "qc_id", "qc_stage", "applies_to", "validation_check", "release_expectation",
        "required_evidence_artifact", "severity", "failure_action", "automatable",
    ]
    return [dict(zip(fields, map(str, row))) for row in QC_ROWS]


def validate_outputs(
    schema: list[dict[str, str]], requirements: list[dict[str, str]], qc: list[dict[str, str]]
) -> list[dict[str, str]]:
    checks = []

    def check(name: str, passed: bool, observed: object, expected: object, detail: str) -> None:
        checks.append({"check": name, "status": "PASS" if passed else "FAIL", "observed": str(observed), "expected": str(expected), "detail": detail})
        if not passed:
            fail(f"Release specification validation failed: {name}")

    fields = {row["field_name"]: row for row in schema}
    required_identity = {"EnsemblID", "profile_id", "profile_version", "evidence_snapshot_version"}
    required_lineage = {"claim_ids", "evidence_record_ids", "source_entity_ids", "source_versions", "artifact_ids", "artifact_sha256s", "dependency_edge_ids"}
    required_provenance = {"generator_version", "generator_sha256", "state_rule_version", "rules_sha256", "source_versions"}
    required_missingness = {"component_state", "record_missingness_pairs", "record_uncertainty_pairs", "conflict_record_ids"}
    prohibited = {name for name, row in fields.items() if row["requirement_level"] == "PROHIBITED"}
    qc_stages = {row["qc_stage"] for row in qc}
    required_qc_stages = {"IDENTITY", "LINEAGE", "DEPENDENCY", "MISSINGNESS", "DETERMINISM", "INTERPRETATION_SAFETY", "RELEASE_DECISION"}

    check("schema_field_names_unique", len(fields) == len(schema), len(fields), len(schema), "No duplicate release field definitions.")
    check("identity_fields_required", required_identity.issubset(fields) and all(fields[name]["requirement_level"] == "REQUIRED" for name in required_identity), len(required_identity.intersection(fields)), len(required_identity), "Immutable entity plus profile/evidence versions.")
    check("lineage_fields_required", required_lineage.issubset(fields) and all(fields[name]["requirement_level"] == "REQUIRED" for name in required_lineage), len(required_lineage.intersection(fields)), len(required_lineage), "Claims, records, sources, artifacts, and dependencies.")
    check("record_level_missingness_required", required_missingness.issubset(fields), len(required_missingness.intersection(fields)), len(required_missingness), "Task #023 record-level limitation addressed.")
    check("provenance_fields_required", required_provenance.issubset(fields), len(required_provenance.intersection(fields)), len(required_provenance), "Generator/rules/artifact/source versions.")
    check("five_states_exact", fields["component_state"]["allowed_values"] == PROFILE_STATES, fields["component_state"]["allowed_values"], PROFILE_STATES, "No state collapse or numerical ordering.")
    check("optional_annotations_present", {"Symbol", "gene_type", "external_identifier_annotations", "display_note"}.issubset(fields) and all(fields[name]["requirement_level"] == "OPTIONAL" for name in {"Symbol", "gene_type", "external_identifier_annotations", "display_note"}), "4 optional annotations", "4 optional annotations", "Display cannot affect identity or state.")
    check("prohibited_fields_exact", prohibited == PROHIBITED_PROFILE_FIELDS, sorted(prohibited), sorted(PROHIBITED_PROFILE_FIELDS), "Scores, ranks, recommendations, and hidden aggregation prohibited.")
    check("requirement_ids_unique", len({row["requirement_id"] for row in requirements}) == len(requirements), len({row["requirement_id"] for row in requirements}), len(requirements), "Stable normative requirements.")
    check("executable_rules_release_gate", any(row["requirement_id"] == "REL_RULE_001" and row["normative_level"] == "MUST" and row["failure_action"] == "WITHHOLD_RELEASE" for row in requirements), "blocking", "blocking", "Task #023 controlled-prose limitation becomes a release gate.")
    check("relational_mapping_release_gate", all(name in fields for name in ("record_missingness_pairs", "record_uncertainty_pairs", "dependency_edge_ids", "dependency_relationships", "dependency_levels")), "explicit mappings", "explicit mappings", "Task #023 relational limitation addressed.")
    check("qc_ids_unique", len({row["qc_id"] for row in qc}) == len(qc), len({row["qc_id"] for row in qc}), len(qc), "Stable QC checks.")
    check("required_qc_stages", required_qc_stages.issubset(qc_stages), len(required_qc_stages.intersection(qc_stages)), len(required_qc_stages), "All requested release validation domains.")
    check("all_qc_blocking", all(row["severity"] == "BLOCKING" and row["failure_action"] == "WITHHOLD_RELEASE" for row in qc), "all blocking", "all blocking", "No partial release after failed integrity/safety QC.")
    check("no_populated_profiles", not any((OUTPUT_DIR / name).exists() for name in ("target_profiles.csv", "target_evidence_profiles.csv", "profiles.csv")), "none", "none", "Specification only.")

    for table_name, table in (("schema", schema), ("requirements", requirements), ("qc", qc)):
        check(f"{table_name}_all_cells_nonblank", all(all(value != "" for value in row.values()) for row in table), "all nonblank", "all nonblank", "No implicit requirements or validation gaps.")
    return checks


def csv_bytes(rows: list[dict[str, str]]) -> bytes:
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue().encode("utf-8")


def summary_bytes(
    schema: list[dict[str, str]], requirements: list[dict[str, str]],
    qc: list[dict[str, str]], checks: list[dict[str, str]],
) -> bytes:
    required_n = sum(row["requirement_level"] == "REQUIRED" for row in schema)
    optional_n = sum(row["requirement_level"] == "OPTIONAL" for row in schema)
    prohibited_n = sum(row["requirement_level"] == "PROHIBITED" for row in schema)
    lines = [
        "# Task #024 target evidence profile release specification summary",
        "",
        "**Specification status:** COMPLETE  ",
        "**Profile release attempted:** No  ",
        "**Populated target profiles generated:** 0  ",
        f"**Release schema definitions:** {len(schema)} ({required_n} required, {optional_n} optional, {prohibited_n} prohibited)  ",
        f"**Normative requirements:** {len(requirements)}  ",
        f"**Blocking QC gates:** {len(qc)}  ",
        f"**Specification validation checks:** {sum(row['status'] == 'PASS' for row in checks)}/{len(checks)}  ",
        "**Scores, rankings, target selections, recommendations, or biological conclusions generated:** No",
        "",
        "## Release identity",
        "",
        "One target profile is the complete set of 11 component rows for one immutable EnsemblID under one `profile_version` and one `evidence_snapshot_version`. Its deterministic identifier is:",
        "",
        "```text",
        "SHA256(EnsemblID | profile_version | evidence_snapshot_version | input_manifest_sha256 | rules_sha256)",
        "```",
        "",
        "`profile_version` identifies structure and interpretation semantics. `evidence_snapshot_version` identifies exact evidence artifacts, source releases, query scopes, and hashes. Changing either creates a different profile identity.",
        "",
        "## Required representation",
        "",
        "Every component retains exact claim, record, source, source-version, artifact, and artifact-hash references. Task #023 limitations are made explicit release requirements: record-level missingness/uncertainty use `record_id=status` pairs, and dependencies use exact edge IDs with edge-to-relationship and edge-to-level mappings.",
        "",
        "The five states remain `OBSERVED`, `PARTIAL`, `MISSING`, `NOT_QUERIED`, and `CONFLICTING`. They are availability/uncertainty states with no numerical order or favorable/unfavorable meaning.",
        "",
        "## Release decision",
        "",
        "A future bundle may use `release_status=RELEASED` only when every blocking QC gate passes. Any identity, lineage, dependency, missingness, provenance, interpretation-safety, or deterministic-regeneration failure produces `WITHHELD`; the builder may not silently repair or partially release the profiles.",
        "",
        "The expected number of profiles is parameterized as `N`, the number of `INCLUDED` EnsemblIDs in the frozen target manifest. Release requires exactly `N` unique profiles and `N × 11` component rows. Task #024 does not assume or instantiate a 29,606-entity manifest.",
        "",
        "## Interpretation safety",
        "",
        "Profile artifacts explicitly prohibit scores, ranks, priorities, recommendations, target-selection fields, therapeutic direction, overall target states, confidence aggregates, completeness percentages, and independent-evidence vote counts. Equivalent hidden derivations in code or sidecars are also prohibited.",
        "",
        "## Preconditions carried forward from Task #023",
        "",
        "1. Before full release, all 55 controlled-prose component/state predicates require executable, reviewed, versioned implementations tied to the frozen semantic predicates.",
        "2. Release bundles must retain the frozen relational registries and exact record-status/dependency-edge mappings so profiles are reconstructible rather than dependent on lossy category lists.",
        "3. Unacquired evidence domains remain `NOT_QUERIED`; they cannot be converted into missing or negative evidence.",
        "4. Conflict validation must retain every record and never choose or average a preferred result.",
        "",
        "## Limitations",
        "",
        "This specification defines release readiness but does not demonstrate that a future full materializer satisfies it. No target universe was instantiated, no executable rule artifact was created, no release bundle was generated, and no biological or therapeutic interpretation was performed.",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def session_bytes(
    git_info: dict[str, str], hashes: dict[str, str], counts: dict[str, int],
    checks: list[dict[str, str]], outputs: dict[Path, bytes],
) -> bytes:
    values = {
        "task": "024",
        "purpose": "target evidence profile release specification",
        "release_spec_version": RELEASE_SPEC_VERSION,
        "specification_snapshot_time_utc": git_info["snapshot"],
        "wall_clock_used_in_generated_outputs": "FALSE",
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "git_branch": git_info["branch"],
        "git_head": git_info["head"],
        "git_origin": git_info["remote"],
        "frozen_task023_base_commit": git_info["base"],
        "network_access": "NOT_USED",
        "packages_installed_or_updated": "FALSE",
        "previous_artifacts_modified": "FALSE",
        "populated_profiles_generated": "FALSE",
        "scoring_generated": "FALSE",
        "ranking_generated": "FALSE",
        "therapeutic_target_selection_generated": "FALSE",
        "target_recommendations_generated": "FALSE",
        "therapeutic_interpretation_generated": "FALSE",
        "biological_conclusions_generated": "FALSE",
        "git_commit_or_push": "FALSE",
        "script_sha256": sha256(SCRIPT_PATH),
        "plan_sha256": sha256(PLAN_PATH),
        "specification_result": "COMPLETE_PROFILE_RELEASE_NOT_ATTEMPTED",
    }
    for name, digest in hashes.items():
        values[f"frozen_input_sha256.{relative(INPUTS[name])}"] = digest
    for name, count in counts.items():
        values[f"validated_count.{name}"] = str(count)
    for row in checks:
        values[f"validation.{row['check']}"] = row["status"]
    for path, content in outputs.items():
        values[f"output_sha256.{relative(path)}"] = hashlib.sha256(content).hexdigest()
    return "".join(f"{key}={values[key]}\n" for key in sorted(values)).encode("utf-8")


def validate_postflight(start_head: str) -> None:
    if run_git("rev-parse", "HEAD") != start_head:
        fail("Git HEAD changed during Task #024.")
    if run_git("diff", "--name-only") or run_git("diff", "--cached", "--name-only"):
        fail("An existing tracked file changed during Task #024.")
    validate_hashes()


def main() -> None:
    git_info = validate_repository()
    hashes = validate_hashes()
    input_counts = validate_inputs()
    schema = schema_records()
    requirements = requirement_records()
    qc = qc_records()
    checks = validate_outputs(schema, requirements, qc)
    scientific_outputs = {
        SCHEMA_PATH: csv_bytes(schema),
        REQUIREMENTS_PATH: csv_bytes(requirements),
        QC_PATH: csv_bytes(qc),
        SUMMARY_PATH: summary_bytes(schema, requirements, qc, checks),
    }
    counts = {
        **input_counts,
        "release_schema_definitions": len(schema),
        "required_release_fields": sum(row["requirement_level"] == "REQUIRED" for row in schema),
        "optional_release_fields": sum(row["requirement_level"] == "OPTIONAL" for row in schema),
        "prohibited_release_fields": sum(row["requirement_level"] == "PROHIBITED" for row in schema),
        "normative_requirements": len(requirements),
        "blocking_qc_gates": len(qc),
    }
    session = session_bytes(git_info, hashes, counts, checks, scientific_outputs)
    all_outputs = {**scientific_outputs, SESSION_PATH: session}
    repeated_scientific = {
        SCHEMA_PATH: csv_bytes(schema),
        REQUIREMENTS_PATH: csv_bytes(requirements),
        QC_PATH: csv_bytes(qc),
        SUMMARY_PATH: summary_bytes(schema, requirements, qc, checks),
    }
    repeated_session = session_bytes(git_info, hashes, counts, checks, repeated_scientific)
    if all_outputs != {**repeated_scientific, SESSION_PATH: repeated_session}:
        fail("Repeated release-specification construction was not byte-identical.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    allowed = {path.name for path in all_outputs}
    unexpected = {path.name for path in OUTPUT_DIR.iterdir() if path.name not in allowed}
    if unexpected:
        fail(f"Unexpected Task #024 output files: {sorted(unexpected)}")
    for path, content in all_outputs.items():
        path.write_bytes(content)
    validate_postflight(git_info["head"])

    print("Created files:")
    for path in all_outputs:
        print(f"- {relative(path)}")
    print(f"Release schema definitions: {len(schema)}")
    print(f"Normative requirements: {len(requirements)}")
    print(f"Blocking QC gates: {len(qc)}")
    print(f"Specification validation checks passed: {sum(row['status'] == 'PASS' for row in checks)}/{len(checks)}")
    print("No populated profiles, scores, rankings, selections, recommendations, or biological conclusions were generated.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
