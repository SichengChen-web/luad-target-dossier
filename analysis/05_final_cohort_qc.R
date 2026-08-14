#!/usr/bin/env Rscript

# Final canonical TCGA-LUAD RNA cohort construction and sample QC.
#
# This script applies only the prespecified, provenance-backed cohort rules
# from Task #005. It does not fit a differential-expression model, perform
# batch correction, select candidates, score targets, or save an expression
# matrix, DGEList, or RangedSummarizedExperiment to the repository.

required_packages <- c(
    "recount3", "SummarizedExperiment", "edgeR", "limma"
)
missing_packages <- required_packages[
    !vapply(required_packages, requireNamespace, logical(1), quietly = TRUE)
]
if (length(missing_packages) > 0L) {
    stop(
        "Missing required package(s): ", paste(missing_packages, collapse = ", "),
        ". Install with: BiocManager::install(c(",
        paste(sprintf('"%s"', missing_packages), collapse = ", "),
        "), ask = FALSE, update = FALSE)"
    )
}

suppressPackageStartupMessages(library(recount3))
suppressPackageStartupMessages(library(SummarizedExperiment))
suppressPackageStartupMessages(library(edgeR))

script_argument <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
if (length(script_argument) == 1L) {
    script_path <- normalizePath(sub("^--file=", "", script_argument))
    repository_root <- dirname(dirname(script_path))
} else {
    repository_root <- normalizePath(getwd())
}

output_dir <- file.path(repository_root, "outputs", "final_sample_qc")
figure_dir <- file.path(output_dir, "figures")
dir.create(figure_dir, recursive = TRUE, showWarnings = FALSE)

task2_project_file <- file.path(
    repository_root, "outputs", "reconnaissance", "project_record.csv"
)
task4_gene_file <- file.path(
    repository_root, "outputs", "sample_qc", "gene_filter_status.csv"
)
task4_metrics_file <- file.path(
    repository_root, "outputs", "sample_qc", "sample_qc_metrics.csv"
)
audit_ledger_file <- file.path(
    repository_root, "outputs", "replicate_ffpe_audit",
    "rna_biospecimen_hierarchy_ledger.csv"
)
a278_audit_file <- file.path(
    repository_root, "outputs", "replicate_ffpe_audit", "a278_aliquot_audit.csv"
)
evidence_sources_file <- file.path(
    repository_root, "outputs", "replicate_ffpe_audit", "evidence_sources.csv"
)
required_input_files <- c(
    task2_project_file, task4_gene_file, task4_metrics_file,
    audit_ledger_file, a278_audit_file, evidence_sources_file
)
missing_input_files <- required_input_files[!file.exists(required_input_files)]
if (length(missing_input_files) > 0L) {
    stop(
        "Required prior-task file(s) missing: ",
        paste(missing_input_files, collapse = ", ")
    )
}

is_missing <- function(x) {
    is.na(x) | trimws(as.character(x)) == ""
}

task2_project <- read.csv(task2_project_file, stringsAsFactors = FALSE)
task4_gene_status <- read.csv(task4_gene_file, stringsAsFactors = FALSE)
task4_metrics <- read.csv(task4_metrics_file, stringsAsFactors = FALSE)
audit_ledger <- read.csv(audit_ledger_file, stringsAsFactors = FALSE)
a278_audit <- read.csv(a278_audit_file, stringsAsFactors = FALSE)
evidence_sources <- read.csv(evidence_sources_file, stringsAsFactors = FALSE)

if (nrow(task2_project) != 1L) {
    stop("Task #002 project_record.csv must contain exactly one row.")
}
expected_task2_values <- c(
    project = "LUAD",
    organism = "human",
    file_source = "tcga",
    project_home = "data_sources/tcga",
    project_type = "data_sources",
    annotation = "gencode_v26",
    assay_names = "raw_counts"
)
for (field in names(expected_task2_values)) {
    if (!field %in% names(task2_project) ||
        !identical(
            as.character(task2_project[[field]]),
            expected_task2_values[[field]]
        )) {
        stop(
            "Task #002 project record does not have expected `", field,
            " = ", expected_task2_values[[field]], "`."
        )
    }
}

required_audit_fields <- c(
    "expression_record_name", "aliquot_barcode", "current_gdc_is_ffpe",
    "historical_noncanonical", "historical_ffpe_annotation",
    "historical_ffpe_source"
)
if (length(setdiff(required_audit_fields, names(audit_ledger))) > 0L) {
    stop("Task #004B ledger is missing required evidence fields.")
}
required_a278_fields <- c(
    "aliquot_barcode", "historical_noncanonical",
    "historical_ffpe_annotation", "historical_ffpe_source"
)
if (length(setdiff(required_a278_fields, names(a278_audit))) > 0L) {
    stop("Task #004B A278 audit is missing required evidence fields.")
}

historical_ffpe_validation_barcodes <- unique(as.character(
    a278_audit$aliquot_barcode[
        as.logical(a278_audit$historical_noncanonical) &
            a278_audit$historical_ffpe_annotation ==
                "Item is noncanonical; FFPE Validation"
    ]
))
if (length(historical_ffpe_validation_barcodes) != 12L ||
    any(is_missing(historical_ffpe_validation_barcodes))) {
    stop(
        "Expected exactly 12 source-traced historical noncanonical ",
        "FFPE-validation aliquot barcodes from Task #004B."
    )
}

source_url <- function(source_name) {
    matched <- evidence_sources$url[evidence_sources$source == source_name]
    if (length(matched) != 1L || is_missing(matched)) {
        stop("Could not resolve one evidence URL for: ", source_name)
    }
    matched
}
gdac_2014_ffpe_url <- source_url("Broad GDAC 2014-04-16 FFPE Cases")

recount3_url <- Sys.getenv(
    "RECOUNT3_URL",
    unset = "https://recount-opendata.s3.amazonaws.com/recount3/release"
)
cache_dir <- Sys.getenv(
    "RECOUNT3_CACHE_DIR",
    unset = "/private/tmp/luad-recount3-cache"
)
dir.create(cache_dir, recursive = TRUE, showWarnings = FALSE)
bfc <- recount3_cache(cache_dir)

supported_human_annotations <- annotation_options("human")
if (!"gencode_v26" %in% supported_human_annotations) {
    stop(
        "Required annotation 'gencode_v26' is not present in ",
        "annotation_options('human')."
    )
}

projects <- available_projects(
    organism = "human",
    recount3_url = recount3_url,
    bfc = bfc,
    available_homes = "data_sources/tcga"
)
project_record <- projects[
    projects$project == "LUAD" &
        projects$organism == "human" &
        projects$file_source == "tcga" &
        projects$project_home == "data_sources/tcga" &
        projects$project_type == "data_sources",
    ,
    drop = FALSE
]
if (nrow(project_record) != 1L) {
    stop("Expected exactly one TCGA-LUAD recount3 project record.")
}

rse <- create_rse(
    project_info = project_record,
    type = "gene",
    annotation = "gencode_v26",
    bfc = bfc,
    recount3_url = recount3_url
)
if (!inherits(rse, "RangedSummarizedExperiment") ||
    !identical(metadata(rse)$project, "LUAD") ||
    !identical(metadata(rse)$project_home, "data_sources/tcga") ||
    !identical(metadata(rse)$annotation, "gencode_v26") ||
    !identical(assayNames(rse), "raw_counts")) {
    stop("Loaded object failed pinned TCGA-LUAD/gencode_v26 identity checks.")
}
expected_dimensions <- c(
    as.integer(task2_project$n_features_loaded),
    as.integer(task2_project$n_samples_loaded)
)
if (!identical(as.integer(dim(rse)), expected_dimensions)) {
    stop("Loaded RSE dimensions do not match Task #002.")
}

sample_metadata <- as.data.frame(colData(rse))
verified_fields <- c(
    external_id = "external_id",
    rail_id = "rail_id",
    case_id = "tcga.gdc_cases.case_id",
    case_submitter_id = "tcga.gdc_cases.submitter_id",
    sample_id = "tcga.gdc_cases.samples.sample_id",
    sample_submitter_id = "tcga.gdc_cases.samples.submitter_id",
    sample_type_id = "tcga.gdc_cases.samples.sample_type_id",
    sample_type = "tcga.gdc_cases.samples.sample_type",
    current_gdc_is_ffpe = "tcga.gdc_cases.samples.is_ffpe",
    portion_id = "tcga.gdc_cases.samples.portions.portion_id",
    portion_submitter_id = "tcga.gdc_cases.samples.portions.submitter_id",
    analyte_id = "tcga.gdc_cases.samples.portions.analytes.analyte_id",
    analyte_submitter_id = "tcga.gdc_cases.samples.portions.analytes.submitter_id",
    aliquot_id = paste0(
        "tcga.gdc_cases.samples.portions.analytes.aliquots.", "aliquot_id"
    ),
    aliquot_submitter_id = paste0(
        "tcga.gdc_cases.samples.portions.analytes.aliquots.", "submitter_id"
    ),
    aliquot_source_center = paste0(
        "tcga.gdc_cases.samples.portions.analytes.aliquots.", "source_center"
    ),
    batch_number = "tcga.cgc_case_batch_number",
    tissue_source_site = "tcga.gdc_cases.tissue_source_site.name",
    tissue_source_site_code = "tcga.gdc_cases.tissue_source_site.code",
    average_mapped_length = "recount_qc.star.average_mapped_length",
    all_mapped_reads = "recount_qc.star.all_mapped_reads",
    gdc_file_name = "tcga.gdc_file_name",
    cgc_filename = "tcga.cgc_filename",
    platform = "tcga.gdc_platform",
    experimental_strategy = "tcga.gdc_experimental_strategy",
    center_code = "tcga.gdc_center.code",
    center_name = "tcga.gdc_center.name",
    cgc_file_submitter_id = "tcga.cgc_file_submitter_id",
    cgc_file_file_id = "tcga.cgc_file_file_id",
    cgc_file_aliquot = "tcga.cgc_file_aliquot",
    experiment_file_id = "tcga.gdc_metadata_files.file_id.experiment",
    experiment_file_name = "tcga.gdc_metadata_files.file_name.experiment",
    run_file_id = "tcga.gdc_metadata_files.file_id.run",
    run_file_name = "tcga.gdc_metadata_files.file_name.run"
)
missing_fields <- setdiff(verified_fields, names(sample_metadata))
if (length(missing_fields) > 0L) {
    stop(
        "Required current colData field(s) missing: ",
        paste(missing_fields, collapse = ", ")
    )
}
value_for <- function(role) sample_metadata[[verified_fields[[role]]]]

aliquot_barcodes <- as.character(value_for("aliquot_submitter_id"))
barcode_pattern <- paste0(
    "^TCGA-([A-Z0-9]{2})-([A-Z0-9]{4})-([0-9]{2})([A-Z])-",
    "([0-9]{2})([A-Z])-([A-Z0-9]{4})-([0-9]{2})$"
)
barcode_prototype <- data.frame(
    tss_code = character(), participant_code = character(),
    sample_type_code = character(), vial_code = character(),
    portion_code = character(), analyte_code = character(),
    plate_code = character(), center_code = character(),
    stringsAsFactors = FALSE
)
parsed <- strcapture(barcode_pattern, aliquot_barcodes, barcode_prototype)
if (anyNA(parsed)) {
    stop("At least one aliquot barcode failed the documented TCGA parser.")
}
parsed$case_barcode <- paste(
    "TCGA", parsed$tss_code, parsed$participant_code, sep = "-"
)
parsed$tcga_sample_barcode <- paste0(
    parsed$case_barcode, "-", parsed$sample_type_code
)
parsed$vial_barcode <- paste0(parsed$tcga_sample_barcode, parsed$vial_code)
parsed$portion_barcode <- paste0(parsed$vial_barcode, "-", parsed$portion_code)
parsed$analyte_barcode <- paste0(parsed$portion_barcode, parsed$analyte_code)
parsed$reconstructed_aliquot <- paste0(
    parsed$analyte_barcode, "-", parsed$plate_code, "-", parsed$center_code
)
if (!identical(parsed$reconstructed_aliquot, aliquot_barcodes)) {
    stop("TCGA aliquot barcode reconstruction failed.")
}

record_ledger <- data.frame(
    expression_record_index = seq_len(ncol(rse)),
    expression_record_name = colnames(rse),
    external_id = as.character(value_for("external_id")),
    rail_id = value_for("rail_id"),
    case_id = as.character(value_for("case_id")),
    case_submitter_id = as.character(value_for("case_submitter_id")),
    tcga_sample_barcode = parsed$tcga_sample_barcode,
    sample_id = as.character(value_for("sample_id")),
    sample_submitter_id = as.character(value_for("sample_submitter_id")),
    sample_type = as.character(value_for("sample_type")),
    group = ifelse(
        as.character(value_for("sample_type")) == "Primary Tumor", "tumor",
        ifelse(
            as.character(value_for("sample_type")) == "Solid Tissue Normal",
            "normal", NA_character_
        )
    ),
    vial_code = parsed$vial_code,
    vial_barcode = parsed$vial_barcode,
    portion_id = as.character(value_for("portion_id")),
    portion_barcode = parsed$portion_barcode,
    analyte_id = as.character(value_for("analyte_id")),
    analyte_barcode = parsed$analyte_barcode,
    aliquot_id = as.character(value_for("aliquot_id")),
    aliquot_barcode = aliquot_barcodes,
    current_gdc_is_ffpe = as.logical(value_for("current_gdc_is_ffpe")),
    batch_number = as.character(value_for("batch_number")),
    tissue_source_site = as.character(value_for("tissue_source_site")),
    tissue_source_site_code = as.character(value_for("tissue_source_site_code")),
    gdc_file_name = as.character(value_for("gdc_file_name")),
    cgc_filename = as.character(value_for("cgc_filename")),
    platform = as.character(value_for("platform")),
    experimental_strategy = as.character(value_for("experimental_strategy")),
    sequencing_center_code = as.character(value_for("center_code")),
    sequencing_center_name = as.character(value_for("center_name")),
    aliquot_source_center = as.character(value_for("aliquot_source_center")),
    cgc_file_submitter_id = as.character(value_for("cgc_file_submitter_id")),
    cgc_file_file_id = as.character(value_for("cgc_file_file_id")),
    cgc_file_aliquot = as.character(value_for("cgc_file_aliquot")),
    experiment_file_id = as.character(value_for("experiment_file_id")),
    experiment_file_name = as.character(value_for("experiment_file_name")),
    run_file_id = as.character(value_for("run_file_id")),
    run_file_name = as.character(value_for("run_file_name")),
    star_all_mapped_reads = as.numeric(value_for("all_mapped_reads")),
    average_mapped_read_length = as.numeric(value_for("average_mapped_length")),
    stringsAsFactors = FALSE,
    check.names = FALSE
)

audit_match <- match(
    record_ledger$expression_record_name,
    audit_ledger$expression_record_name
)
if (anyNA(audit_match) || anyDuplicated(audit_match) ||
    !identical(
        record_ledger$aliquot_barcode,
        as.character(audit_ledger$aliquot_barcode[audit_match])
    )) {
    stop("Current RSE records do not map one-to-one to the Task #004B ledger.")
}
if (!identical(
    record_ledger$current_gdc_is_ffpe,
    as.logical(audit_ledger$current_gdc_is_ffpe[audit_match])
)) {
    stop("Current GDC is_ffpe values differ from the Task #004B audit.")
}
record_ledger$historical_annotation <- as.character(
    audit_ledger$historical_ffpe_annotation[audit_match]
)
record_ledger$historical_evidence_source <- as.character(
    audit_ledger$historical_ffpe_source[audit_match]
)

historical_rows <- record_ledger$aliquot_barcode %in%
    historical_ffpe_validation_barcodes
if (sum(historical_rows) != 12L ||
    !setequal(
        record_ledger$aliquot_barcode[historical_rows],
        historical_ffpe_validation_barcodes
    ) || any(record_ledger$current_gdc_is_ffpe[historical_rows])) {
    stop(
        "Historical FFPE-validation evidence did not resolve to exactly 12 ",
        "current-GDC-non-FFPE aliquot records."
    )
}

record_ledger$exclusion_reason <- NA_character_
record_ledger$evidence_type <- NA_character_
record_ledger$evidence_source <- NA_character_

nonprimary_rows <- !record_ledger$sample_type %in%
    c("Primary Tumor", "Solid Tissue Normal")
record_ledger$exclusion_reason[nonprimary_rows] <- paste0(
    "excluded_nonprimary_sample_type:", record_ledger$sample_type[nonprimary_rows]
)
record_ledger$evidence_type[nonprimary_rows] <-
    "current_GDC_sample_type"
record_ledger$evidence_source[nonprimary_rows] <-
    "recount3 colData: tcga.gdc_cases.samples.sample_type"

current_ffpe_rows <- !nonprimary_rows & record_ledger$current_gdc_is_ffpe
record_ledger$exclusion_reason[current_ffpe_rows] <-
    "excluded_current_GDC_is_ffpe_TRUE"
record_ledger$evidence_type[current_ffpe_rows] <-
    "current_GDC_sample_level_FFPE_flag"
record_ledger$evidence_source[current_ffpe_rows] <- paste(
    "recount3 colData: tcga.gdc_cases.samples.is_ffpe;",
    "Task #004B source-traced historical annotation"
)

historical_exclusion_rows <- !nonprimary_rows & !current_ffpe_rows &
    historical_rows
record_ledger$exclusion_reason[historical_exclusion_rows] <-
    "excluded_exact_historical_noncanonical_FFPE_validation_aliquot"
record_ledger$evidence_type[historical_exclusion_rows] <-
    "historical_aliquot_level_noncanonical_FFPE_validation_annotation"
record_ledger$evidence_source[historical_exclusion_rows] <-
    gdac_2014_ffpe_url

record_ledger$included_final_record_pool <- is.na(record_ledger$exclusion_reason)

if (sum(nonprimary_rows) != 2L ||
    !all(record_ledger$sample_type[nonprimary_rows] == "Recurrent Tumor")) {
    stop("Expected exactly two Recurrent Tumor records outside the primary groups.")
}
if (sum(current_ffpe_rows) != 12L) {
    stop("Expected exactly 12 current GDC is_ffpe == TRUE primary records.")
}
if (sum(historical_exclusion_rows) != 12L) {
    stop("Expected exactly 12 historical FFPE-validation exclusions.")
}
if (sum(record_ledger$included_final_record_pool) != 575L) {
    stop("Expected 575 records before same-aliquot technical resolution.")
}

exclusion_audit <- record_ledger[
    !record_ledger$included_final_record_pool,
    c(
        "expression_record_index", "expression_record_name",
        "case_submitter_id", "tcga_sample_barcode", "sample_type",
        "aliquot_barcode", "exclusion_reason", "evidence_type",
        "evidence_source", "current_gdc_is_ffpe", "historical_annotation"
    ),
    drop = FALSE
]
exclusion_audit <- exclusion_audit[order(
    exclusion_audit$exclusion_reason,
    exclusion_audit$aliquot_barcode
), ]

retained_indices <- which(record_ledger$included_final_record_pool)
retained_ledger <- record_ledger[retained_indices, , drop = FALSE]
record_counts <- compute_read_counts(
    rse[, retained_indices],
    round = TRUE,
    avg_mapped_read_length = verified_fields[["average_mapped_length"]]
)
if (!identical(dim(record_counts), c(nrow(rse), nrow(retained_ledger))) ||
    anyNA(record_counts) || any(!is.finite(record_counts)) ||
    any(record_counts < 0)) {
    stop("Final-pool compute_read_counts() returned invalid counts.")
}

remaining_sample_counts <- table(retained_ledger$tcga_sample_barcode)
repeated_samples <- names(remaining_sample_counts[remaining_sample_counts > 1L])
expected_duplicate_sample <- "TCGA-38-4625-01"
expected_duplicate_aliquot <- "TCGA-38-4625-01A-01R-1206-07"
if (!identical(repeated_samples, expected_duplicate_sample) ||
    unname(remaining_sample_counts[expected_duplicate_sample]) != 2L) {
    stop(
        "After evidence-backed exclusions, the only repeated TCGA sample must be ",
        expected_duplicate_sample, " with two records. Observed: ",
        paste(repeated_samples, collapse = ", ")
    )
}
duplicate_rows <- which(
    retained_ledger$tcga_sample_barcode == expected_duplicate_sample
)
if (!all(
    retained_ledger$aliquot_barcode[duplicate_rows] == expected_duplicate_aliquot
)) {
    stop("The remaining repeated TCGA-38-4625 sample is not one exact aliquot.")
}

same_fields <- c(
    "case_id", "case_submitter_id", "sample_id", "sample_submitter_id",
    "vial_barcode", "portion_id", "portion_barcode", "analyte_id",
    "analyte_barcode", "aliquot_id", "aliquot_barcode", "sample_type",
    "platform", "experimental_strategy", "sequencing_center_code",
    "sequencing_center_name", "aliquot_source_center", "cgc_file_aliquot"
)
distinct_fields <- c(
    "expression_record_name", "external_id", "rail_id", "gdc_file_name",
    "cgc_filename", "cgc_file_submitter_id", "cgc_file_file_id",
    "experiment_file_id", "experiment_file_name", "run_file_id",
    "run_file_name"
)
same_field_checks <- vapply(same_fields, function(field) {
    values <- retained_ledger[[field]][duplicate_rows]
    !any(is_missing(values)) && length(unique(as.character(values))) == 1L
}, logical(1))
distinct_field_checks <- vapply(distinct_fields, function(field) {
    values <- retained_ledger[[field]][duplicate_rows]
    !any(is_missing(values)) && length(unique(as.character(values))) == 2L
}, logical(1))
if (!all(same_field_checks) || !all(distinct_field_checks)) {
    stop(
        "TCGA-38-4625 provenance is insufficient for technical aggregation. ",
        "Failed same-field checks: ",
        paste(names(same_field_checks)[!same_field_checks], collapse = ", "),
        "; failed distinct-record checks: ",
        paste(
            names(distinct_field_checks)[!distinct_field_checks],
            collapse = ", "
        )
    )
}

duplicate_counts <- record_counts[, duplicate_rows, drop = FALSE]
duplicate_pearson <- suppressWarnings(cor(
    duplicate_counts[, 1L], duplicate_counts[, 2L], method = "pearson"
))
duplicate_spearman <- suppressWarnings(cor(
    duplicate_counts[, 1L], duplicate_counts[, 2L], method = "spearman"
))
technical_duplicate_resolution <- retained_ledger[
    duplicate_rows,
    c(
        "expression_record_index", "expression_record_name", "external_id",
        "rail_id", "case_id", "case_submitter_id", "tcga_sample_barcode",
        "sample_id", "sample_submitter_id", "vial_barcode", "portion_id",
        "portion_barcode", "analyte_id", "analyte_barcode", "aliquot_id",
        "aliquot_barcode", "sample_type", "platform",
        "experimental_strategy", "sequencing_center_code",
        "sequencing_center_name", "gdc_file_name", "cgc_filename",
        "cgc_file_submitter_id", "cgc_file_file_id", "experiment_file_id",
        "experiment_file_name", "run_file_id", "run_file_name",
        "star_all_mapped_reads"
    ),
    drop = FALSE
]
technical_duplicate_resolution$record_read_count_library_size <- colSums(
    duplicate_counts
)
technical_duplicate_resolution$all_biological_identifiers_match <-
    all(same_field_checks)
technical_duplicate_resolution$all_record_file_run_identifiers_distinct <-
    all(distinct_field_checks)
technical_duplicate_resolution$raw_read_count_pearson <- duplicate_pearson
technical_duplicate_resolution$raw_read_count_spearman <- duplicate_spearman
technical_duplicate_resolution$resolution <-
    "sum_gene_level_read_counts_true_same_aliquot_sequencing_replication"
technical_duplicate_resolution$resolved_final_observation <-
    expected_duplicate_sample

sample_order <- unique(retained_ledger$tcga_sample_barcode)
sample_level_counts <- sumTechReps(
    record_counts,
    ID = retained_ledger$tcga_sample_barcode
)
if (!identical(colnames(sample_level_counts), sample_order)) {
    stop("Technical aggregation returned an unexpected sample order.")
}
expected_libraries <- as.numeric(tapply(
    colSums(record_counts),
    factor(retained_ledger$tcga_sample_barcode, levels = sample_order),
    sum
))
if (!isTRUE(all.equal(
    unname(colSums(sample_level_counts)), expected_libraries, tolerance = 0
))) {
    stop("Same-aliquot technical aggregation did not preserve read counts.")
}

first_record <- match(sample_order, retained_ledger$tcga_sample_barcode)
final_cohort_ledger <- retained_ledger[
    first_record,
    c(
        "tcga_sample_barcode", "sample_id", "sample_submitter_id", "case_id",
        "case_submitter_id", "sample_type", "group", "vial_barcode",
        "portion_id", "portion_barcode", "analyte_id", "analyte_barcode",
        "aliquot_id", "aliquot_barcode", "current_gdc_is_ffpe",
        "batch_number", "tissue_source_site", "tissue_source_site_code",
        "platform", "experimental_strategy", "sequencing_center_name"
    ),
    drop = FALSE
]
final_cohort_ledger$final_observation_index <- seq_along(sample_order)
records_per_final_sample <- table(retained_ledger$tcga_sample_barcode)
final_cohort_ledger$n_expression_records_aggregated <- as.integer(
    records_per_final_sample[sample_order]
)
collapse_values <- function(field, sample_name) {
    paste(
        retained_ledger[[field]][
            retained_ledger$tcga_sample_barcode == sample_name
        ],
        collapse = ";"
    )
}
final_cohort_ledger$source_expression_record_indices <- vapply(
    sample_order,
    function(x) collapse_values("expression_record_index", x),
    character(1)
)
final_cohort_ledger$source_expression_record_names <- vapply(
    sample_order,
    function(x) collapse_values("expression_record_name", x),
    character(1)
)
final_cohort_ledger$source_external_ids <- vapply(
    sample_order,
    function(x) collapse_values("external_id", x),
    character(1)
)
final_cohort_ledger$source_file_names <- vapply(
    sample_order,
    function(x) collapse_values("gdc_file_name", x),
    character(1)
)
final_cohort_ledger$technical_resolution <- ifelse(
    final_cohort_ledger$tcga_sample_barcode == expected_duplicate_sample,
    "two_distinct_sequencing_records_same_exact_aliquot_summed",
    "single_expression_record_no_aggregation"
)
final_cohort_ledger <- final_cohort_ledger[, c(
    "final_observation_index", setdiff(
        names(final_cohort_ledger), "final_observation_index"
    )
)]
rownames(final_cohort_ledger) <- final_cohort_ledger$tcga_sample_barcode

n_final <- nrow(final_cohort_ledger)
n_tumor <- sum(final_cohort_ledger$sample_type == "Primary Tumor")
n_normal <- sum(final_cohort_ledger$sample_type == "Solid Tissue Normal")
n_cases <- length(unique(final_cohort_ledger$case_id))
observed_assertions <- c(
    final_observations = n_final,
    primary_tumor = n_tumor,
    solid_tissue_normal = n_normal,
    unique_cases = n_cases
)
expected_assertions <- c(
    final_observations = 574L,
    primary_tumor = 515L,
    solid_tissue_normal = 59L,
    unique_cases = 516L
)
if (!identical(as.integer(observed_assertions), as.integer(expected_assertions))) {
    stop(
        "Final cohort dimensions differ from reproducibility expectations. ",
        "Observed: ",
        paste(names(observed_assertions), observed_assertions, collapse = ", "),
        ". Expected: ",
        paste(names(expected_assertions), expected_assertions, collapse = ", "),
        ". Reinspect exclusions and duplicate provenance; do not manufacture counts."
    )
}
if (anyDuplicated(final_cohort_ledger$tcga_sample_barcode)) {
    stop("A TCGA sample barcode has multiple final independent observations.")
}

case_group_table <- table(
    final_cohort_ledger$case_id,
    factor(final_cohort_ledger$group, levels = c("normal", "tumor"))
)
if (any(case_group_table[, "tumor"] > 1L)) {
    stop("At least one case has multiple final Primary Tumor observations.")
}
if (any(case_group_table[, "normal"] > 1L)) {
    stop("At least one case has multiple final Solid Tissue Normal observations.")
}
n_matched <- sum(
    case_group_table[, "tumor"] == 1L & case_group_table[, "normal"] == 1L
)
n_tumor_only <- sum(
    case_group_table[, "tumor"] == 1L & case_group_table[, "normal"] == 0L
)
n_normal_only <- sum(
    case_group_table[, "tumor"] == 0L & case_group_table[, "normal"] == 1L
)
n_multiple_same_group <- sum(
    case_group_table[, "tumor"] > 1L | case_group_table[, "normal"] > 1L
)
case_pairing_summary <- data.frame(
    metric = c(
        "unique_cases", "tumor_only_cases", "normal_only_cases",
        "matched_tumor_normal_cases", "cases_with_multiple_tumor_observations",
        "cases_with_multiple_normal_observations",
        "cases_with_multiple_same_group_observations"
    ),
    value = c(
        n_cases, n_tumor_only, n_normal_only, n_matched,
        sum(case_group_table[, "tumor"] > 1L),
        sum(case_group_table[, "normal"] > 1L), n_multiple_same_group
    ),
    stringsAsFactors = FALSE
)

gene_data <- as.data.frame(rowData(rse))
required_gene_fields <- c("gene_id", "gene_name", "gene_type")
if (length(setdiff(required_gene_fields, names(gene_data))) > 0L) {
    stop("Required gencode_v26 gene annotation fields are missing.")
}
gene_annotation <- data.frame(
    EnsemblID = as.character(gene_data$gene_id),
    Symbol = as.character(gene_data$gene_name),
    gene_type = as.character(gene_data$gene_type),
    stringsAsFactors = FALSE
)
if (any(is_missing(gene_annotation$EnsemblID)) ||
    anyDuplicated(gene_annotation$EnsemblID)) {
    stop("Gene identifiers are missing or duplicated.")
}
rownames(sample_level_counts) <- gene_annotation$EnsemblID
rownames(gene_annotation) <- gene_annotation$EnsemblID

final_cohort_ledger$group <- factor(
    final_cohort_ledger$group, levels = c("normal", "tumor")
)
dge <- DGEList(
    counts = sample_level_counts,
    samples = final_cohort_ledger,
    group = final_cohort_ledger$group,
    genes = gene_annotation
)
if (!identical(colnames(dge), rownames(dge$samples)) ||
    !identical(rownames(dge), rownames(dge$genes))) {
    stop("DGEList sample/gene traceability failed.")
}

library_sizes_before_filtering <- dge$samples$lib.size
keep_by_filter <- filterByExpr(dge, group = dge$samples$group)
gene_filter_status <- cbind(
    dge$genes,
    keep_by_filterByExpr = unname(keep_by_filter)
)
dge_filtered <- dge[keep_by_filter, , keep.lib.sizes = FALSE]
dge_filtered <- normLibSizes(dge_filtered, method = "TMM")
library_sizes_after_filtering <- dge_filtered$samples$lib.size
tmm_factors <- dge_filtered$samples$norm.factors
effective_library_sizes <- library_sizes_after_filtering * tmm_factors

log_cpm <- cpm(
    dge_filtered,
    log = TRUE,
    prior.count = 2,
    normalized.lib.sizes = TRUE
)
mds <- plotMDS(dge_filtered, top = 500, plot = FALSE)
mds1 <- as.numeric(mds$x)
mds2 <- as.numeric(mds$y)
pca <- prcomp(t(log_cpm), center = TRUE, scale. = FALSE, rank. = 5)
pca_coordinates <- pca$x
pca_variance_percent <- 100 * pca$sdev^2 / sum(pca$sdev^2)
gene_log_cpm_median <- apply(log_cpm, 1L, median)
rle_values <- sweep(log_cpm, 1L, gene_log_cpm_median, FUN = "-")
rle_median <- apply(rle_values, 2L, median)
rle_iqr <- apply(rle_values, 2L, IQR)
rm(rle_values)

sample_qc_metrics <- data.frame(
    final_observation_index = seq_len(ncol(dge_filtered)),
    tcga_sample_barcode = dge_filtered$samples$tcga_sample_barcode,
    sample_id = dge_filtered$samples$sample_id,
    sample_submitter_id = dge_filtered$samples$sample_submitter_id,
    case_id = dge_filtered$samples$case_id,
    case_submitter_id = dge_filtered$samples$case_submitter_id,
    sample_type = dge_filtered$samples$sample_type,
    group = as.character(dge_filtered$samples$group),
    batch_number = dge_filtered$samples$batch_number,
    tissue_source_site = dge_filtered$samples$tissue_source_site,
    tissue_source_site_code = dge_filtered$samples$tissue_source_site_code,
    n_expression_records_aggregated =
        dge_filtered$samples$n_expression_records_aggregated,
    raw_library_size_before_filtering = library_sizes_before_filtering,
    raw_library_size_after_filtering = library_sizes_after_filtering,
    tmm_normalization_factor = tmm_factors,
    effective_library_size = effective_library_sizes,
    MDS1 = mds1,
    MDS2 = mds2,
    PC1 = pca_coordinates[, 1L],
    PC2 = pca_coordinates[, 2L],
    PC3 = pca_coordinates[, 3L],
    PC4 = pca_coordinates[, 4L],
    PC5 = pca_coordinates[, 5L],
    RLE_median_logCPM = rle_median,
    RLE_IQR_logCPM = rle_iqr,
    stringsAsFactors = FALSE,
    check.names = FALSE
)

level_value <- function(x) {
    answer <- as.character(x)
    answer[is_missing(answer)] <- "<missing>"
    answer
}
contingency_summary <- function(level, level_name, metadata) {
    level <- level_value(level)
    result <- do.call(rbind, lapply(sort(unique(level)), function(value) {
        rows <- level == value
        n_tumor_level <- sum(metadata$group[rows] == "tumor")
        n_normal_level <- sum(metadata$group[rows] == "normal")
        data.frame(
            level = value,
            n_tumor = n_tumor_level,
            n_normal = n_normal_level,
            total = n_tumor_level + n_normal_level,
            both_groups_represented =
                n_tumor_level > 0L & n_normal_level > 0L,
            tumor_only = n_tumor_level > 0L & n_normal_level == 0L,
            normal_only = n_tumor_level == 0L & n_normal_level > 0L,
            stringsAsFactors = FALSE
        )
    }))
    names(result)[names(result) == "level"] <- level_name
    result
}
sample_type_by_batch <- contingency_summary(
    final_cohort_ledger$batch_number, "batch_number", final_cohort_ledger
)
sample_type_by_tss <- contingency_summary(
    final_cohort_ledger$tissue_source_site,
    "tissue_source_site",
    final_cohort_ledger
)
sample_type_by_tss$tissue_source_site_code <- vapply(
    sample_type_by_tss$tissue_source_site,
    function(site) paste(
        unique(final_cohort_ledger$tissue_source_site_code[
            final_cohort_ledger$tissue_source_site == site
        ]),
        collapse = ";"
    ),
    character(1)
)
sample_type_by_tss <- sample_type_by_tss[, c(
    "tissue_source_site", "tissue_source_site_code", "n_tumor", "n_normal",
    "total", "both_groups_represented", "tumor_only", "normal_only"
)]

batch_values <- level_value(final_cohort_ledger$batch_number)
tss_values <- level_value(final_cohort_ledger$tissue_source_site)
observed_batch_tss <- unique(data.frame(
    batch_number = batch_values,
    tissue_source_site = tss_values,
    stringsAsFactors = FALSE
))
batch_by_tss <- do.call(rbind, lapply(seq_len(nrow(observed_batch_tss)), function(i) {
    rows <- batch_values == observed_batch_tss$batch_number[i] &
        tss_values == observed_batch_tss$tissue_source_site[i]
    data.frame(
        batch_number = observed_batch_tss$batch_number[i],
        tissue_source_site = observed_batch_tss$tissue_source_site[i],
        n_tumor = sum(final_cohort_ledger$group[rows] == "tumor"),
        n_normal = sum(final_cohort_ledger$group[rows] == "normal"),
        total = sum(rows),
        both_groups_represented =
            any(final_cohort_ledger$group[rows] == "tumor") &
                any(final_cohort_ledger$group[rows] == "normal"),
        stringsAsFactors = FALSE
    )
}))
batch_by_tss <- batch_by_tss[order(
    batch_by_tss$batch_number, batch_by_tss$tissue_source_site
), ]

design_input <- data.frame(
    group = factor(final_cohort_ledger$group, levels = c("normal", "tumor")),
    batch_number = factor(final_cohort_ledger$batch_number),
    tissue_source_site = factor(final_cohort_ledger$tissue_source_site),
    stringsAsFactors = FALSE
)
rownames(design_input) <- final_cohort_ledger$tcga_sample_barcode

contrast_is_estimable <- function(design, coefficient_name) {
    coefficient_index <- match(coefficient_name, colnames(design))
    if (is.na(coefficient_index)) return(FALSE)
    decomposition <- svd(design, nu = 0L, nv = ncol(design))
    tolerance <- max(dim(design)) * max(decomposition$d) * .Machine$double.eps
    matrix_rank <- sum(decomposition$d > tolerance)
    if (matrix_rank == ncol(design)) return(TRUE)
    null_space <- decomposition$v[
        , seq.int(matrix_rank + 1L, ncol(design)), drop = FALSE
    ]
    contrast <- numeric(ncol(design))
    contrast[coefficient_index] <- 1
    max(abs(crossprod(null_space, contrast))) < sqrt(.Machine$double.eps)
}

design_diagnostic <- function(design_name, formula, variables) {
    complete_rows <- complete.cases(design_input[, variables, drop = FALSE])
    input <- droplevels(design_input[complete_rows, , drop = FALSE])
    design <- model.matrix(formula, data = input)
    matrix_rank <- qr(design)$rank
    nonestimable <- limma::nonEstimable(design)
    if (is.null(nonestimable)) nonestimable <- character(0)
    data.frame(
        design = design_name,
        formula = paste(deparse(formula), collapse = " "),
        n = nrow(design),
        n_samples_available = nrow(design_input),
        n_samples_excluded_missing = nrow(design_input) - nrow(design),
        n_coefficients = ncol(design),
        coefficients = paste(colnames(design), collapse = ";"),
        rank = matrix_rank,
        residual_df = nrow(design) - matrix_rank,
        full_rank = matrix_rank == ncol(design),
        tumor_vs_normal_estimable = contrast_is_estimable(design, "grouptumor"),
        nonestimable_coefficients = paste(nonestimable, collapse = ";"),
        stringsAsFactors = FALSE
    )
}
design_diagnostics <- rbind(
    design_diagnostic("A", ~ group, c("group")),
    design_diagnostic("B", ~ group + batch_number, c("group", "batch_number")),
    design_diagnostic(
        "C", ~ group + tissue_source_site,
        c("group", "tissue_source_site")
    ),
    design_diagnostic(
        "D", ~ group + batch_number + tissue_source_site,
        c("group", "batch_number", "tissue_source_site")
    )
)

christiana_rows <- sample_qc_metrics$tissue_source_site_code == "44"
n_christiana_final <- sum(christiana_rows)
prior_ffpe_affected_cases <- sort(unique(
    record_ledger$case_submitter_id[current_ffpe_rows]
))
prior_ffpe_case_primary_rows <-
    sample_qc_metrics$case_submitter_id %in% prior_ffpe_affected_cases &
        sample_qc_metrics$sample_type == "Primary Tumor"
n_prior_ffpe_case_primary_final <- sum(prior_ffpe_case_primary_rows)
if (length(prior_ffpe_affected_cases) != 12L ||
    n_prior_ffpe_case_primary_final != 11L) {
    stop(
        "Expected 12 prior FFPE-affected cases and 11 retained canonical ",
        "Primary Tumor observations from those cases."
    )
}
pc2_rank_low <- rank(sample_qc_metrics$PC2, ties.method = "first")
rle_rank_high <- rank(-sample_qc_metrics$RLE_IQR_logCPM, ties.method = "first")
bottom_affected_n <- order(sample_qc_metrics$PC2)[
    seq_len(n_prior_ffpe_case_primary_final)
]
prior_ffpe_cases_exact_low_pc2_cluster <- setequal(
    which(prior_ffpe_case_primary_rows), bottom_affected_n
)
excluded_prior_cluster_absent <- !any(
    final_cohort_ledger$aliquot_barcode %in%
        exclusion_audit$aliquot_barcode[
            exclusion_audit$current_gdc_is_ffpe
        ]
)
ffpe_cluster_assessment <- data.frame(
    metric = c(
        "prior_current_GDC_FFPE_records_remaining",
        "final_Christiana_observations",
        "Christiana_observations_among_lowest_12_PC2",
        "Christiana_observations_among_highest_12_RLE_IQR",
        "retained_primary_tumors_from_12_prior_FFPE_affected_cases",
        "affected_case_primary_tumors_among_lowest_12_PC2",
        "affected_case_primary_tumors_among_highest_12_RLE_IQR",
        "affected_case_primary_tumors_exactly_occupy_lowest_11_PC2",
        "affected_case_primary_tumor_maximum_RLE_IQR",
        "final_samples_with_RLE_IQR_above_2",
        "final_maximum_RLE_IQR",
        "prior_exact_FFPE_cluster_absent"
    ),
    value = c(
        as.character(0L),
        n_christiana_final,
        sum(christiana_rows & pc2_rank_low <= 12L),
        sum(christiana_rows & rle_rank_high <= 12L),
        n_prior_ffpe_case_primary_final,
        sum(prior_ffpe_case_primary_rows & pc2_rank_low <= 12L),
        sum(prior_ffpe_case_primary_rows & rle_rank_high <= 12L),
        prior_ffpe_cases_exact_low_pc2_cluster,
        max(sample_qc_metrics$RLE_IQR_logCPM[prior_ffpe_case_primary_rows]),
        sum(sample_qc_metrics$RLE_IQR_logCPM > 2),
        max(sample_qc_metrics$RLE_IQR_logCPM),
        excluded_prior_cluster_absent
    ),
    stringsAsFactors = FALSE
)

group_symbols <- c(normal = 1L, tumor = 16L)
sample_symbols <- unname(group_symbols[as.character(final_cohort_ledger$group)])
png(
    file.path(figure_dir, "library_size_diagnostic.png"),
    width = 1200, height = 800, res = 150
)
boxplot(
    log10(library_sizes_after_filtering) ~ final_cohort_ledger$group,
    xlab = "Biological group", ylab = "log10 filtered raw library size",
    main = "Final-cohort library-size diagnostic"
)
dev.off()

png(
    file.path(figure_dir, "tmm_normalization_factor_diagnostic.png"),
    width = 1200, height = 800, res = 150
)
boxplot(
    tmm_factors ~ final_cohort_ledger$group,
    xlab = "Biological group", ylab = "TMM normalization factor",
    main = "Final-cohort TMM-factor diagnostic"
)
abline(h = 1, lty = 2)
dev.off()

png(
    file.path(figure_dir, "mds_by_group.png"),
    width = 1200, height = 800, res = 150
)
plot(
    mds1, mds2, pch = sample_symbols,
    xlab = mds$axislabel[mds$dim.plot[1L]],
    ylab = mds$axislabel[mds$dim.plot[2L]],
    main = "Final-cohort edgeR MDS by group"
)
legend("topright", legend = names(group_symbols), pch = group_symbols, bty = "n")
dev.off()

png(
    file.path(figure_dir, "pca_logcpm_by_group.png"),
    width = 1200, height = 800, res = 150
)
plot(
    pca_coordinates[, 1L], pca_coordinates[, 2L], pch = sample_symbols,
    xlab = sprintf("PC1 (%.1f%%)", pca_variance_percent[1L]),
    ylab = sprintf("PC2 (%.1f%%)", pca_variance_percent[2L]),
    main = "Final-cohort PCA of TMM-aware log-CPM"
)
legend("topright", legend = names(group_symbols), pch = group_symbols, bty = "n")
dev.off()

png(
    file.path(figure_dir, "pca_christiana_highlight.png"),
    width = 1200, height = 800, res = 150
)
plot(
    pca_coordinates[, 1L], pca_coordinates[, 2L],
    pch = ifelse(christiana_rows, 16L, 1L),
    col = ifelse(christiana_rows, "firebrick", "grey55"),
    xlab = sprintf("PC1 (%.1f%%)", pca_variance_percent[1L]),
    ylab = sprintf("PC2 (%.1f%%)", pca_variance_percent[2L]),
    main = "Final-cohort PCA: Christiana TSS highlighted"
)
legend(
    "topright", legend = c("Christiana", "other TSS"),
    pch = c(16L, 1L), col = c("firebrick", "grey55"), bty = "n"
)
dev.off()

png(
    file.path(figure_dir, "pca_prior_ffpe_cases_highlight.png"),
    width = 1200, height = 800, res = 150
)
plot(
    pca_coordinates[, 1L], pca_coordinates[, 2L],
    pch = ifelse(prior_ffpe_case_primary_rows, 16L, 1L),
    col = ifelse(prior_ffpe_case_primary_rows, "firebrick", "grey55"),
    xlab = sprintf("PC1 (%.1f%%)", pca_variance_percent[1L]),
    ylab = sprintf("PC2 (%.1f%%)", pca_variance_percent[2L]),
    main = "Final PCA: retained tumours from prior FFPE-affected cases"
)
legend(
    "topright",
    legend = c("retained affected-case tumour", "other final observation"),
    pch = c(16L, 1L), col = c("firebrick", "grey55"), bty = "n"
)
dev.off()

png(
    file.path(figure_dir, "rle_sample_summary.png"),
    width = 1400, height = 700, res = 150
)
par(mfrow = c(1, 2))
boxplot(
    rle_median ~ final_cohort_ledger$group,
    xlab = "Biological group", ylab = "Sample median RLE (log-CPM)",
    main = "Final-cohort RLE median"
)
abline(h = 0, lty = 2)
boxplot(
    rle_iqr ~ final_cohort_ledger$group,
    xlab = "Biological group", ylab = "Sample RLE IQR (log-CPM)",
    main = "Final-cohort RLE spread"
)
dev.off()

png(
    file.path(figure_dir, "pc2_vs_rle_prior_ffpe_cases.png"),
    width = 1200, height = 800, res = 150
)
plot(
    sample_qc_metrics$PC2, sample_qc_metrics$RLE_IQR_logCPM,
    pch = ifelse(prior_ffpe_case_primary_rows, 16L, 1L),
    col = ifelse(prior_ffpe_case_primary_rows, "firebrick", "grey55"),
    xlab = "Final-cohort PC2", ylab = "Final-cohort RLE IQR (log-CPM)",
    main = "Final PC2/RLE: prior FFPE-affected cases"
)
legend(
    "topright",
    legend = c("retained affected-case tumour", "other final observation"),
    pch = c(16L, 1L), col = c("firebrick", "grey55"), bty = "n"
)
dev.off()

png(
    file.path(figure_dir, "pc2_vs_rle_christiana.png"),
    width = 1200, height = 800, res = 150
)
plot(
    sample_qc_metrics$PC2, sample_qc_metrics$RLE_IQR_logCPM,
    pch = ifelse(christiana_rows, 16L, 1L),
    col = ifelse(christiana_rows, "firebrick", "grey55"),
    xlab = "Final-cohort PC2", ylab = "Final-cohort RLE IQR (log-CPM)",
    main = "Final-cohort PC2 versus RLE spread"
)
legend(
    "topright", legend = c("Christiana", "other TSS"),
    pch = c(16L, 1L), col = c("firebrick", "grey55"), bty = "n"
)
dev.off()

n_genes_before <- nrow(dge)
n_genes_after <- nrow(dge_filtered)
n_task4_genes_before <- nrow(task4_gene_status)
n_task4_genes_after <- sum(as.logical(task4_gene_status$keep_by_filterByExpr))
task4_tmm_min <- min(task4_metrics$tmm_normalization_factor)
task4_tmm_median <- median(task4_metrics$tmm_normalization_factor)
task4_tmm_max <- max(task4_metrics$tmm_normalization_factor)
n_batch_levels <- nrow(sample_type_by_batch)
n_tss_levels <- nrow(sample_type_by_tss)
n_batch_both <- sum(sample_type_by_batch$both_groups_represented)
n_tss_both <- sum(sample_type_by_tss$both_groups_represented)
n_tss_per_batch <- tapply(tss_values, batch_values, function(x) length(unique(x)))
n_batch_per_tss <- tapply(batch_values, tss_values, function(x) length(unique(x)))

format_number <- function(x, digits = 4L) {
    format(x, digits = digits, big.mark = ",", scientific = FALSE, trim = TRUE)
}
design_lines <- vapply(seq_len(nrow(design_diagnostics)), function(i) {
    row <- design_diagnostics[i, ]
    paste0(
        "- Design ", row$design, " (`", row$formula, "`): n = ", row$n,
        ", coefficients = ", row$n_coefficients, ", rank = ", row$rank,
        ", residual df = ", row$residual_df, ", full rank = ", row$full_rank,
        ", tumour-vs-normal estimable = ", row$tumor_vs_normal_estimable,
        if (nzchar(row$nonestimable_coefficients)) {
            paste0("; non-estimable: `", row$nonestimable_coefficients, "`")
        } else {
            "; no non-estimable coefficients"
        },
        "."
    )
}, character(1))

summary_lines <- c(
    "# Final canonical TCGA-LUAD RNA cohort and QC",
    "",
    paste0("Generated: ", format(Sys.time(), tz = "UTC"), " UTC"),
    "",
    "## Scope and software",
    "",
    paste0(
        "The original TCGA-LUAD recount3 `gencode_v26` object contained ",
        nrow(rse), " genes and ", ncol(rse), " expression records. This run used ",
        "R ", as.character(getRversion()), ", recount3 ",
        as.character(packageVersion("recount3")), ", SummarizedExperiment ",
        as.character(packageVersion("SummarizedExperiment")), ", edgeR ",
        as.character(packageVersion("edgeR")), ", and limma ",
        as.character(packageVersion("limma")), "."
    ),
    "",
    "## 1. Why Task #004's 587 observations were provisional",
    "",
    paste(
        "Task #004 grouped every primary tumour/normal record by GDC `sample_id`",
        "before the lower biospecimen hierarchy had been audited. Task #004B then",
        "showed that one GDC sample can contain biologically consequential distinct",
        "RNA aliquots, so most of those apparent repeats could not be assumed to be",
        "technical lanes or summed safely."
    ),
    "",
    "## 2. Evidence-backed exclusions",
    "",
    paste0(
        "The two official `Recurrent Tumor` records were outside the primary groups. ",
        "Twelve primary-tumour records with current GDC `is_ffpe == TRUE` were ",
        "excluded because they are current sample-level FFPE records and were the ",
        "A277 01B/01C records responsible for the prior low-PC2 cluster."
    ),
    paste0(
        "A separate exact list of 12 A278 aliquots was excluded because Task #004B ",
        "source-traced each barcode to the historical annotation `Item is ",
        "noncanonical; FFPE Validation`. They are described as historically ",
        "annotated noncanonical FFPE-validation aliquots—not as current GDC FFPE ",
        "samples. No exclusion was generalized from vial letter or plate code."
    ),
    "",
    "## 3. The one justified technical aggregation",
    "",
    paste0(
        "After exclusions, only ", expected_duplicate_sample, " remained repeated. ",
        "Its two records have the same UUID-defined case, GDC sample, vial, portion, ",
        "RNA analyte, exact aliquot, and biological sample type. They share Illumina ",
        "HiSeq RNA-seq and UNC center metadata, but have distinct filenames, file ",
        "IDs, experiment IDs, run IDs, recount3 IDs, and library sizes. Their raw ",
        "read-count correlation is Pearson ", sprintf("%.4f", duplicate_pearson),
        ". These two gene-count columns were therefore summed as sequencing ",
        "replication of one exact RNA aliquot. No other records were summed."
    ),
    "",
    "## 4. Final cohort and case structure",
    "",
    paste0(
        "The frozen cohort has ", n_final, " biological observations: ", n_tumor,
        " Primary Tumor and ", n_normal, " Solid Tissue Normal, from ", n_cases,
        " unique cases. There are ", n_matched, " matched tumour-normal cases, ",
        n_tumor_only, " tumour-only cases, and ", n_normal_only,
        " normal-only case. No case has multiple observations within either ",
        "biological group."
    ),
    "",
    "## 5. Gene filtering and TMM after cohort cleanup",
    "",
    paste0(
        "All gene types were retained initially. Final-cohort `filterByExpr()` kept ",
        format_number(n_genes_after, 8), " of ",
        format_number(n_genes_before, 8), " genes; Task #004 had kept ",
        format_number(n_task4_genes_after, 8), " of ",
        format_number(n_task4_genes_before, 8), ". After filtering, library sizes ",
        "were recalculated and TMM factors were recomputed from scratch. Final ",
        "factors range from ", format_number(min(tmm_factors), 5), " to ",
        format_number(max(tmm_factors), 5), " (median ",
        format_number(median(tmm_factors), 5), "), compared with Task #004's ",
        format_number(task4_tmm_min, 5), " to ",
        format_number(task4_tmm_max, 5), " (median ",
        format_number(task4_tmm_median, 5), "). TMM changes downstream scaling; ",
        "it does not rewrite the raw counts."
    ),
    "",
    "## 6. From-scratch PCA, MDS, and RLE assessment",
    "",
    paste0(
        "All coordinates and RLE summaries were recomputed using only the final ",
        "cohort. PC1 and PC2 explain ", sprintf("%.2f", pca_variance_percent[1L]),
        "% and ", sprintf("%.2f", pca_variance_percent[2L]), "%. The exact 12 ",
        "current-FFPE records are absent. The final cohort contains ",
        n_christiana_final, " Christiana observations; ",
        sum(christiana_rows & pc2_rank_low <= 12L),
        " are among the 12 lowest PC2 values and ",
        sum(christiana_rows & rle_rank_high <= 12L),
        " are among the 12 highest RLE-IQR values. More directly, the 12 prior ",
        "FFPE-affected cases contribute ", n_prior_ffpe_case_primary_final,
        " retained canonical Primary Tumor observations; ",
        sum(prior_ffpe_case_primary_rows & pc2_rank_low <= 12L),
        " is among the 12 lowest PC2 values and ",
        sum(prior_ffpe_case_primary_rows & rle_rank_high <= 12L),
        " are among the 12 highest RLE-IQR values. Those retained tumours exactly ",
        "occupy the lowest 11 PC2 positions = ",
        prior_ffpe_cases_exact_low_pc2_cluster, ". Thus the previous discrete ",
        "FFPE-defined low-PC2 cluster ",
        if (excluded_prior_cluster_absent &&
            !prior_ffpe_cases_exact_low_pc2_cluster) {
            "is absent after the prespecified exclusions."
        } else {
            "requires further review in the final-cohort figures."
        }
    ),
    paste0(
        "Final RLE IQR ranges from ", format_number(min(rle_iqr), 5), " to ",
        format_number(max(rle_iqr), 5), "; ", sum(rle_iqr > 2),
        " final observations exceed 2. No sample was excluded because of its ",
        "PCA, MDS, library-size, TMM, or RLE position."
    ),
    "",
    "## 7. Batch, tissue-source-site, and candidate designs",
    "",
    paste0(
        "The final cohort contains ", n_batch_levels, " CGC batch levels; ",
        n_batch_both, " contain both groups. It contains ", n_tss_levels,
        " tissue-source-site levels; ", n_tss_both, " contain both groups. ",
        sum(n_tss_per_batch > 1L), " batches span more than one TSS, and ",
        sum(n_batch_per_tss > 1L), " TSS levels span more than one batch. ",
        "The contingency tables show the remaining imbalance and confounding."
    ),
    design_lines,
    "",
    "## 8. Decision still unresolved before differential expression",
    "",
    paste(
        "The final statistical design is not yet selected. The next scientific",
        "decision must determine whether batch, tissue-source site, neither, or a",
        "different justified adjustment belongs in the model, and how the 58",
        "matched cases should be handled relative to the much larger unpaired",
        "cohort. These diagnostics describe estimability; they do not choose a model."
    ),
    "",
    "## Explicitly not performed",
    "",
    "This task did **not** perform:",
    "",
    "- `voomLmFit`;",
    "- `eBayes`;",
    "- `topTable`;",
    "- differential-expression testing;",
    "- batch correction;",
    "- candidate selection;",
    "- scoring.",
    ""
)

write.csv(
    final_cohort_ledger,
    file.path(output_dir, "final_cohort_ledger.csv"),
    row.names = FALSE,
    na = ""
)
write.csv(
    exclusion_audit,
    file.path(output_dir, "exclusion_audit.csv"),
    row.names = FALSE,
    na = ""
)
write.csv(
    technical_duplicate_resolution,
    file.path(output_dir, "technical_duplicate_resolution.csv"),
    row.names = FALSE,
    na = ""
)
write.csv(
    gene_filter_status,
    file.path(output_dir, "gene_filter_status.csv"),
    row.names = FALSE,
    na = ""
)
write.csv(
    sample_qc_metrics,
    file.path(output_dir, "sample_qc_metrics.csv"),
    row.names = FALSE,
    na = ""
)
write.csv(
    design_diagnostics,
    file.path(output_dir, "design_diagnostics.csv"),
    row.names = FALSE,
    na = ""
)
write.csv(
    sample_type_by_batch,
    file.path(output_dir, "sample_type_by_batch.csv"),
    row.names = FALSE,
    na = ""
)
write.csv(
    sample_type_by_tss,
    file.path(output_dir, "sample_type_by_tss.csv"),
    row.names = FALSE,
    na = ""
)
write.csv(
    batch_by_tss,
    file.path(output_dir, "batch_by_tss.csv"),
    row.names = FALSE,
    na = ""
)
write.csv(
    case_pairing_summary,
    file.path(output_dir, "case_pairing_summary.csv"),
    row.names = FALSE,
    na = ""
)
write.csv(
    ffpe_cluster_assessment,
    file.path(output_dir, "ffpe_cluster_assessment.csv"),
    row.names = FALSE,
    na = ""
)
writeLines(
    summary_lines,
    file.path(output_dir, "final_sample_qc_summary.md"),
    useBytes = TRUE
)

message("Final TCGA-LUAD cohort QC complete. Outputs: ", output_dir)
