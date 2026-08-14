#!/usr/bin/env Rscript

# TCGA-LUAD cohort-structure and count diagnostics through recount3.
#
# This task deliberately performs no gene filtering, normalization, TMM,
# PCA-based exclusion, differential expression, candidate-gene selection,
# batch correction, or scoring. No full expression/count matrix is written.

required_packages <- c("recount3", "SummarizedExperiment")
missing_packages <- required_packages[
    !vapply(required_packages, requireNamespace, logical(1), quietly = TRUE)
]
if (length(missing_packages) > 0L) {
    stop(
        "Missing required package(s): ",
        paste(missing_packages, collapse = ", "),
        ". Install with: BiocManager::install(c(",
        paste(sprintf('"%s"', missing_packages), collapse = ", "),
        "), ask = FALSE, update = FALSE)"
    )
}

suppressPackageStartupMessages(library(recount3))
suppressPackageStartupMessages(library(SummarizedExperiment))

script_argument <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
if (length(script_argument) == 1L) {
    script_path <- normalizePath(sub("^--file=", "", script_argument))
    repository_root <- dirname(dirname(script_path))
} else {
    repository_root <- normalizePath(getwd())
}

output_dir <- file.path(repository_root, "outputs", "cohort_diagnostics")
task2_project_file <- file.path(
    repository_root,
    "outputs",
    "reconnaissance",
    "project_record.csv"
)
if (!file.exists(task2_project_file)) {
    stop("Task #002 project record is missing: ", task2_project_file)
}

task2_project <- read.csv(task2_project_file, stringsAsFactors = FALSE)
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
        !identical(as.character(task2_project[[field]]), expected_task2_values[[field]])) {
        stop(
            "Task #002 project record does not have expected `", field,
            " = ", expected_task2_values[[field]], "`."
        )
    }
}

expected_dimensions <- c(
    features = as.integer(task2_project$n_features_loaded),
    expression_columns = as.integer(task2_project$n_samples_loaded)
)
if (anyNA(expected_dimensions)) {
    stop("Task #002 project record has invalid expected dimensions.")
}

recount3_url <- Sys.getenv(
    "RECOUNT3_URL",
    unset = "https://recount-opendata.s3.amazonaws.com/recount3/release"
)
cache_dir <- Sys.getenv("RECOUNT3_CACHE_DIR", unset = "")
bfc <- if (nzchar(cache_dir)) {
    dir.create(cache_dir, recursive = TRUE, showWarnings = FALSE)
    recount3_cache(cache_dir)
} else {
    recount3_cache()
}

supported_human_annotations <- annotation_options("human")
if (!"gencode_v26" %in% supported_human_annotations) {
    stop(
        "Required annotation 'gencode_v26' is not available in ",
        "annotation_options('human'). Available annotations: ",
        paste(supported_human_annotations, collapse = ", ")
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
    stop(
        "Expected exactly one TCGA-LUAD project record; found ",
        nrow(project_record), "."
    )
}

rse <- create_rse(
    project_info = project_record,
    type = "gene",
    annotation = "gencode_v26",
    bfc = bfc,
    recount3_url = recount3_url
)

if (!inherits(rse, "RangedSummarizedExperiment")) {
    stop("create_rse() did not return a RangedSummarizedExperiment.")
}
if (!identical(metadata(rse)$project, "LUAD") ||
    !identical(metadata(rse)$project_home, "data_sources/tcga") ||
    !identical(metadata(rse)$annotation, "gencode_v26")) {
    stop("Loaded RSE metadata does not identify pinned TCGA-LUAD/gencode_v26.")
}
if (!identical(assayNames(rse), "raw_counts")) {
    stop(
        "Expected exactly the untransformed `raw_counts` assay; found: ",
        paste(assayNames(rse), collapse = ", ")
    )
}
if (!identical(as.integer(dim(rse)), unname(expected_dimensions))) {
    stop(
        "Loaded RSE dimensions ", paste(dim(rse), collapse = " x "),
        " do not match Task #002 dimensions ",
        paste(expected_dimensions, collapse = " x "), "."
    )
}

sample_metadata <- as.data.frame(colData(rse))
verified_fields <- c(
    external_id = "external_id",
    rail_id = "rail_id",
    case_id = "tcga.gdc_cases.case_id",
    case_submitter_id = "tcga.gdc_cases.submitter_id",
    sample_id = "tcga.gdc_cases.samples.sample_id",
    sample_submitter_id = "tcga.gdc_cases.samples.submitter_id",
    aliquot_id = paste0(
        "tcga.gdc_cases.samples.portions.analytes.aliquots.",
        "aliquot_id"
    ),
    aliquot_submitter_id = paste0(
        "tcga.gdc_cases.samples.portions.analytes.aliquots.",
        "submitter_id"
    ),
    sample_type = "tcga.gdc_cases.samples.sample_type",
    batch_number = "tcga.cgc_case_batch_number",
    tissue_source_site = "tcga.gdc_cases.tissue_source_site.name",
    tissue_source_site_code = "tcga.gdc_cases.tissue_source_site.code",
    sequencing_platform = "tcga.gdc_platform",
    sequencing_center = "tcga.gdc_center.name",
    average_mapped_length = "recount_qc.star.average_mapped_length",
    all_mapped_reads = "recount_qc.star.all_mapped_reads",
    auc_all_reads_all_bases = "recount_qc.bc_auc.all_reads_all_bases"
)
missing_fields <- setdiff(verified_fields, names(sample_metadata))
if (length(missing_fields) > 0L) {
    stop(
        "Verified colData field(s) missing: ",
        paste(missing_fields, collapse = ", "),
        ". Re-inspect the actual RSE and installed recount3 documentation."
    )
}

is_missing <- function(x) {
    is.na(x) | trimws(as.character(x)) == ""
}

values_for <- function(role) {
    sample_metadata[[verified_fields[[role]]]]
}

expression_column_names <- colnames(rse)
if (is.null(expression_column_names) ||
    length(expression_column_names) != ncol(rse)) {
    stop("The RSE does not provide one column name per expression record.")
}

ledger <- data.frame(
    expression_column_index = seq_len(ncol(rse)),
    expression_column_name = expression_column_names,
    external_id = as.character(values_for("external_id")),
    rail_id = values_for("rail_id"),
    case_id = as.character(values_for("case_id")),
    case_submitter_id = as.character(values_for("case_submitter_id")),
    sample_id = as.character(values_for("sample_id")),
    sample_submitter_id = as.character(values_for("sample_submitter_id")),
    aliquot_id = as.character(values_for("aliquot_id")),
    aliquot_submitter_id = as.character(values_for("aliquot_submitter_id")),
    sample_type = as.character(values_for("sample_type")),
    batch_number = values_for("batch_number"),
    tissue_source_site = as.character(values_for("tissue_source_site")),
    tissue_source_site_code = as.character(values_for("tissue_source_site_code")),
    sequencing_platform = as.character(values_for("sequencing_platform")),
    sequencing_center = as.character(values_for("sequencing_center")),
    stringsAsFactors = FALSE,
    check.names = FALSE
)
ledger[[verified_fields[["average_mapped_length"]]]] <-
    values_for("average_mapped_length")
ledger[[verified_fields[["all_mapped_reads"]]]] <-
    values_for("all_mapped_reads")
ledger[[verified_fields[["auc_all_reads_all_bases"]]]] <-
    values_for("auc_all_reads_all_bases")

ledger$eligible_primary_comparison <- ledger$sample_type %in% c(
    "Primary Tumor",
    "Solid Tissue Normal"
)
ledger$group <- ifelse(
    ledger$sample_type == "Primary Tumor",
    "tumor",
    ifelse(
        ledger$sample_type == "Solid Tissue Normal",
        "normal",
        "excluded_other"
    )
)

count_records <- function(ids) {
    valid <- !is_missing(ids)
    result <- rep(NA_integer_, length(ids))
    counts <- table(ids[valid])
    result[valid] <- as.integer(counts[ids[valid]])
    result
}

count_distinct_children <- function(child, parent) {
    valid_parent <- !is_missing(parent)
    result <- rep(NA_integer_, length(parent))
    split_rows <- split(seq_along(parent)[valid_parent], parent[valid_parent])
    counts <- vapply(
        split_rows,
        function(i) length(unique(child[i][!is_missing(child[i])])),
        integer(1)
    )
    result[valid_parent] <- counts[parent[valid_parent]]
    result
}

ledger$n_expression_records_for_case <- count_records(ledger$case_id)
ledger$n_distinct_samples_for_case <- count_distinct_children(
    ledger$sample_id,
    ledger$case_id
)
ledger$n_expression_records_for_sample <- count_records(ledger$sample_id)
ledger$n_distinct_aliquots_for_sample <- count_distinct_children(
    ledger$aliquot_id,
    ledger$sample_id
)
ledger$n_expression_records_for_aliquot <- count_records(ledger$aliquot_id)

case_group_key <- paste(ledger$case_id, ledger$group, sep = "\r")
ledger$n_distinct_samples_for_case_and_group <- count_distinct_children(
    ledger$sample_id,
    case_group_key
)

primary_rows <- ledger$sample_type == "Primary Tumor"
primary_samples_by_case <- tapply(
    ledger$sample_id[primary_rows],
    ledger$case_id[primary_rows],
    function(x) length(unique(x[!is_missing(x)]))
)
cases_multiple_primary_samples <- names(primary_samples_by_case)[
    primary_samples_by_case > 1L
]

ledger$case_has_multiple_expression_records <-
    ledger$n_expression_records_for_case > 1L
ledger$case_has_multiple_distinct_sample_ids <-
    ledger$n_distinct_samples_for_case > 1L
ledger$case_has_multiple_primary_tumor_sample_ids <-
    ledger$case_id %in% cases_multiple_primary_samples
ledger$sample_has_multiple_distinct_aliquot_ids <-
    ledger$n_distinct_aliquots_for_sample > 1L
ledger$aliquot_has_multiple_expression_records <-
    ledger$n_expression_records_for_aliquot > 1L

ledger$status_excluded_nonprimary_sample_type <-
    !ledger$eligible_primary_comparison
ledger$status_review_multiple_expression_same_aliquot <-
    ledger$eligible_primary_comparison &
    ledger$aliquot_has_multiple_expression_records
ledger$status_review_multiple_aliquots_same_sample <-
    ledger$eligible_primary_comparison &
    ledger$sample_has_multiple_distinct_aliquot_ids
ledger$status_review_multiple_samples_same_case_and_group <-
    ledger$eligible_primary_comparison &
    ledger$n_distinct_samples_for_case_and_group > 1L
ledger$status_eligible_unambiguous <-
    ledger$eligible_primary_comparison &
    !ledger$status_review_multiple_expression_same_aliquot &
    !ledger$status_review_multiple_aliquots_same_sample &
    !ledger$status_review_multiple_samples_same_case_and_group

ledger$provisional_status <- "eligible_unambiguous"
ledger$provisional_status[
    ledger$status_review_multiple_samples_same_case_and_group
] <- "review_multiple_samples_same_case_and_group"
ledger$provisional_status[
    ledger$status_review_multiple_aliquots_same_sample
] <- "review_multiple_aliquots_same_sample"
ledger$provisional_status[
    ledger$status_review_multiple_expression_same_aliquot
] <- "review_multiple_expression_same_aliquot"
ledger$provisional_status[
    ledger$status_excluded_nonprimary_sample_type
] <- "excluded_nonprimary_sample_type"

repeated_case_fields <- c(
    "expression_column_index", "expression_column_name", "external_id",
    "case_id", "case_submitter_id", "sample_id", "sample_submitter_id",
    "aliquot_id", "aliquot_submitter_id", "sample_type", "group",
    "n_expression_records_for_case", "n_distinct_samples_for_case",
    "case_has_multiple_distinct_sample_ids",
    "case_has_multiple_primary_tumor_sample_ids",
    "n_distinct_samples_for_case_and_group"
)
repeated_cases <- ledger[
    ledger$case_has_multiple_expression_records,
    repeated_case_fields,
    drop = FALSE
]
repeated_cases <- repeated_cases[order(
    repeated_cases$case_submitter_id,
    repeated_cases$sample_type,
    repeated_cases$sample_submitter_id,
    repeated_cases$aliquot_submitter_id,
    repeated_cases$expression_column_index
), ]

repeated_sample_fields <- c(
    "expression_column_index", "expression_column_name", "external_id",
    "case_id", "case_submitter_id", "sample_id", "sample_submitter_id",
    "aliquot_id", "aliquot_submitter_id", "sample_type", "group",
    "n_expression_records_for_sample", "n_distinct_aliquots_for_sample"
)
repeated_samples <- ledger[
    ledger$sample_has_multiple_distinct_aliquot_ids,
    repeated_sample_fields,
    drop = FALSE
]
repeated_samples <- repeated_samples[order(
    repeated_samples$sample_submitter_id,
    repeated_samples$aliquot_submitter_id,
    repeated_samples$expression_column_index
), ]

repeated_aliquot_fields <- c(
    "expression_column_index", "expression_column_name", "external_id",
    "case_id", "case_submitter_id", "sample_id", "sample_submitter_id",
    "aliquot_id", "aliquot_submitter_id", "sample_type", "group",
    "n_expression_records_for_aliquot"
)
repeated_aliquots <- ledger[
    ledger$aliquot_has_multiple_expression_records,
    repeated_aliquot_fields,
    drop = FALSE
]
repeated_aliquots <- repeated_aliquots[order(
    repeated_aliquots$aliquot_submitter_id,
    repeated_aliquots$expression_column_index
), ]

raw_counts <- assay(rse, "raw_counts")
duplicate_aliquot_ids <- unique(repeated_aliquots$aliquot_id)
technical_checks <- list()
technical_check_index <- 0L
for (duplicate_aliquot_id in duplicate_aliquot_ids) {
    column_indices <- which(ledger$aliquot_id == duplicate_aliquot_id)
    column_pairs <- combn(column_indices, 2L)
    for (pair_index in seq_len(ncol(column_pairs))) {
        first_index <- column_pairs[1L, pair_index]
        second_index <- column_pairs[2L, pair_index]
        first_values <- raw_counts[, first_index]
        second_values <- raw_counts[, second_index]
        exactly_identical <- identical(
            as.vector(first_values),
            as.vector(second_values)
        )
        finite_pair <- is.finite(first_values) & is.finite(second_values)
        pearson <- if (sum(finite_pair) > 1L) {
            suppressWarnings(cor(
                first_values[finite_pair],
                second_values[finite_pair],
                method = "pearson"
            ))
        } else {
            NA_real_
        }
        maximum_absolute_difference <- if (all(finite_pair)) {
            max(abs(first_values - second_values))
        } else {
            NA_real_
        }
        technical_check_index <- technical_check_index + 1L
        technical_checks[[technical_check_index]] <- data.frame(
            aliquot_id = duplicate_aliquot_id,
            aliquot_submitter_id = ledger$aliquot_submitter_id[first_index],
            sample_id = ledger$sample_id[first_index],
            sample_submitter_id = ledger$sample_submitter_id[first_index],
            case_id = ledger$case_id[first_index],
            case_submitter_id = ledger$case_submitter_id[first_index],
            sample_type = ledger$sample_type[first_index],
            first_expression_column_index = first_index,
            first_expression_column_name = ledger$expression_column_name[first_index],
            first_external_id = ledger$external_id[first_index],
            second_expression_column_index = second_index,
            second_expression_column_name = ledger$expression_column_name[second_index],
            second_external_id = ledger$external_id[second_index],
            raw_counts_exactly_identical = exactly_identical,
            raw_counts_pearson_correlation = pearson,
            raw_counts_maximum_absolute_difference = maximum_absolute_difference,
            first_total_raw_coverage = sum(first_values),
            second_total_raw_coverage = sum(second_values),
            stringsAsFactors = FALSE
        )
    }
}
technical_duplicate_check <- if (length(technical_checks) > 0L) {
    do.call(rbind, technical_checks)
} else {
    NULL
}

average_mapped_length_before <- as.numeric(values_for("average_mapped_length"))
all_mapped_reads <- as.numeric(values_for("all_mapped_reads"))
auc_all_reads_all_bases <- as.numeric(values_for("auc_all_reads_all_bases"))

read_counts <- compute_read_counts(
    rse,
    round = TRUE,
    avg_mapped_read_length = verified_fields[["average_mapped_length"]]
)
average_mapped_length_after <- as.numeric(
    colData(rse)[[verified_fields[["average_mapped_length"]]]]
)

if (!identical(dim(read_counts), dim(rse))) {
    stop("compute_read_counts() returned unexpected dimensions.")
}

gene_read_count_library_size <- colSums(read_counts)
ledger$gene_read_count_library_size <- gene_read_count_library_size

empty_qc_row <- function() {
    data.frame(
        section = NA_character_, metric = NA_character_, group = NA_character_,
        n_total = NA_real_, n_complete = NA_real_, n_missing = NA_real_,
        n_nan = NA_real_, n_infinite = NA_real_, n_zero = NA_real_,
        n_negative = NA_real_, min = NA_real_, q1 = NA_real_,
        median = NA_real_, mean = NA_real_, q3 = NA_real_, max = NA_real_,
        value_numeric = NA_real_, value_text = NA_character_,
        stringsAsFactors = FALSE
    )
}

numeric_summary_row <- function(section, metric, group, values) {
    values <- as.numeric(values)
    finite_values <- values[is.finite(values)]
    row <- empty_qc_row()
    row$section <- section
    row$metric <- metric
    row$group <- group
    row$n_total <- length(values)
    row$n_complete <- length(finite_values)
    row$n_missing <- sum(is.na(values) & !is.nan(values))
    row$n_nan <- sum(is.nan(values))
    row$n_infinite <- sum(is.infinite(values))
    row$n_zero <- sum(finite_values == 0)
    row$n_negative <- sum(finite_values < 0)
    if (length(finite_values) > 0L) {
        quantiles <- quantile(
            finite_values,
            probs = c(0, 0.25, 0.5, 0.75, 1),
            names = FALSE
        )
        row$min <- quantiles[[1L]]
        row$q1 <- quantiles[[2L]]
        row$median <- quantiles[[3L]]
        row$mean <- mean(finite_values)
        row$q3 <- quantiles[[4L]]
        row$max <- quantiles[[5L]]
    }
    row
}

diagnostic_row <- function(section, metric, value_numeric, value_text = NA_character_,
                           n_complete = NA_real_) {
    row <- empty_qc_row()
    row$section <- section
    row$metric <- metric
    row$group <- "all"
    row$n_complete <- n_complete
    row$value_numeric <- value_numeric
    row$value_text <- value_text
    row
}

read_count_na_only <- sum(is.na(read_counts) & !is.nan(read_counts))
read_count_nan <- sum(is.nan(read_counts))
read_count_infinite <- sum(is.infinite(read_counts))
read_count_negative <- sum(read_counts < 0, na.rm = TRUE)

correlation_complete <- is.finite(gene_read_count_library_size) &
    is.finite(all_mapped_reads)
pearson_correlation <- cor(
    gene_read_count_library_size[correlation_complete],
    all_mapped_reads[correlation_complete],
    method = "pearson"
)
spearman_correlation <- cor(
    gene_read_count_library_size[correlation_complete],
    all_mapped_reads[correlation_complete],
    method = "spearman"
)

count_qc_summary <- do.call(rbind, list(
    numeric_summary_row(
        "input_qc_before_compute_read_counts",
        "average_mapped_length",
        "all",
        average_mapped_length_before
    ),
    numeric_summary_row(
        "input_qc_after_compute_read_counts",
        "average_mapped_length",
        "all",
        average_mapped_length_after
    ),
    numeric_summary_row("input_qc", "all_mapped_reads", "all", all_mapped_reads),
    numeric_summary_row(
        "input_qc",
        "auc_all_reads_all_bases",
        "all",
        auc_all_reads_all_bases
    ),
    diagnostic_row(
        "read_count_matrix",
        "dimensions",
        NA_real_,
        paste(dim(read_counts), collapse = " x ")
    ),
    diagnostic_row("read_count_matrix", "round_argument", 1, "TRUE"),
    diagnostic_row("read_count_matrix", "na_values", read_count_na_only),
    diagnostic_row("read_count_matrix", "nan_values", read_count_nan),
    diagnostic_row("read_count_matrix", "infinite_values", read_count_infinite),
    diagnostic_row("read_count_matrix", "negative_values", read_count_negative),
    numeric_summary_row(
        "gene_read_count_library_size",
        "colSums",
        "all",
        gene_read_count_library_size
    ),
    numeric_summary_row(
        "gene_read_count_library_size",
        "colSums",
        "tumor",
        gene_read_count_library_size[ledger$group == "tumor"]
    ),
    numeric_summary_row(
        "gene_read_count_library_size",
        "colSums",
        "normal",
        gene_read_count_library_size[ledger$group == "normal"]
    ),
    diagnostic_row(
        "library_size_vs_all_mapped_reads",
        "pearson_correlation",
        pearson_correlation,
        n_complete = sum(correlation_complete)
    ),
    diagnostic_row(
        "library_size_vs_all_mapped_reads",
        "spearman_correlation",
        spearman_correlation,
        n_complete = sum(correlation_complete)
    )
))

eligible_ledger <- ledger[ledger$eligible_primary_comparison, , drop = FALSE]
level_value <- function(x) {
    result <- as.character(x)
    result[is_missing(result)] <- "<missing>"
    result
}

batch_levels <- sort(unique(level_value(eligible_ledger$batch_number)))
sample_type_by_batch <- do.call(rbind, lapply(batch_levels, function(level) {
    rows <- level_value(eligible_ledger$batch_number) == level
    n_tumor <- sum(eligible_ledger$group[rows] == "tumor")
    n_normal <- sum(eligible_ledger$group[rows] == "normal")
    data.frame(
        batch_number = level,
        n_tumor = n_tumor,
        n_normal = n_normal,
        total = n_tumor + n_normal,
        both_groups_represented = n_tumor > 0L & n_normal > 0L,
        tumor_only = n_tumor > 0L & n_normal == 0L,
        normal_only = n_normal > 0L & n_tumor == 0L,
        stringsAsFactors = FALSE
    )
}))

tss_name <- level_value(eligible_ledger$tissue_source_site)
tss_code <- level_value(eligible_ledger$tissue_source_site_code)
tss_keys <- unique(data.frame(
    tissue_source_site = tss_name,
    tissue_source_site_code = tss_code,
    stringsAsFactors = FALSE
))
tss_keys <- tss_keys[order(tss_keys$tissue_source_site, tss_keys$tissue_source_site_code), ]
sample_type_by_tss <- do.call(rbind, lapply(seq_len(nrow(tss_keys)), function(i) {
    rows <- tss_name == tss_keys$tissue_source_site[[i]] &
        tss_code == tss_keys$tissue_source_site_code[[i]]
    n_tumor <- sum(eligible_ledger$group[rows] == "tumor")
    n_normal <- sum(eligible_ledger$group[rows] == "normal")
    data.frame(
        tissue_source_site = tss_keys$tissue_source_site[[i]],
        tissue_source_site_code = tss_keys$tissue_source_site_code[[i]],
        n_tumor = n_tumor,
        n_normal = n_normal,
        total = n_tumor + n_normal,
        both_groups_represented = n_tumor > 0L & n_normal > 0L,
        tumor_only = n_tumor > 0L & n_normal == 0L,
        normal_only = n_normal > 0L & n_tumor == 0L,
        stringsAsFactors = FALSE
    )
}))

platform_values <- unique(ledger$sequencing_platform[
    !is_missing(ledger$sequencing_platform)
])
center_values <- unique(ledger$sequencing_center[
    !is_missing(ledger$sequencing_center)
])

status_counts <- as.data.frame(
    table(ledger$provisional_status),
    stringsAsFactors = FALSE
)
names(status_counts) <- c("status", "n_records")
status_counts <- status_counts[order(status_counts$status), ]

library_summary <- function(group) {
    row <- count_qc_summary[
        count_qc_summary$section == "gene_read_count_library_size" &
            count_qc_summary$group == group,
        ,
        drop = FALSE
    ]
    row[1L, ]
}
format_number <- function(x, digits = 2L) {
    format(round(x, digits), big.mark = ",", scientific = FALSE, trim = TRUE)
}
library_summary_text <- function(group, label) {
    row <- library_summary(group)
    paste0(
        "- ", label, " (n = ", row$n_total, "): min ", format_number(row$min),
        ", Q1 ", format_number(row$q1), ", median ", format_number(row$median),
        ", mean ", format_number(row$mean), ", Q3 ", format_number(row$q3),
        ", max ", format_number(row$max), "."
    )
}
status_lines <- paste0(
    "- `", status_counts$status, "`: ", status_counts$n_records
)
review_flag_lines <- c(
    paste0(
        "- `review_multiple_expression_same_aliquot`: ",
        sum(ledger$status_review_multiple_expression_same_aliquot)
    ),
    paste0(
        "- `review_multiple_aliquots_same_sample`: ",
        sum(ledger$status_review_multiple_aliquots_same_sample)
    ),
    paste0(
        "- `review_multiple_samples_same_case_and_group`: ",
        sum(ledger$status_review_multiple_samples_same_case_and_group)
    )
)

n_cases_multiple_records <- length(unique(
    ledger$case_id[ledger$case_has_multiple_expression_records]
))
n_cases_multiple_samples <- length(unique(
    ledger$case_id[ledger$case_has_multiple_distinct_sample_ids]
))
n_cases_multiple_primary_samples <- length(cases_multiple_primary_samples)
n_samples_multiple_aliquots <- length(unique(
    ledger$sample_id[ledger$sample_has_multiple_distinct_aliquot_ids]
))
n_aliquots_multiple_records <- length(unique(
    ledger$aliquot_id[ledger$aliquot_has_multiple_expression_records]
))

technical_summary_lines <- if (is.null(technical_duplicate_check)) {
    "No aliquot has multiple expression records, so no raw-count pair exists."
} else {
    paste0(
        "The ", nrow(technical_duplicate_check), " duplicate-aliquot pair(s) ",
        "were compared gene by gene. Exact identity: ",
        paste(technical_duplicate_check$raw_counts_exactly_identical, collapse = ", "),
        "; Pearson correlation: ",
        paste(
            format(technical_duplicate_check$raw_counts_pearson_correlation, digits = 6),
            collapse = ", "
        ),
        "; maximum absolute difference: ",
        paste(
            technical_duplicate_check$raw_counts_maximum_absolute_difference,
            collapse = ", "
        ),
        ". No duplicate was selected or removed."
    )
}

summary_lines <- c(
    "# TCGA-LUAD cohort structure and count diagnostics",
    "",
    paste0("Generated: ", format(Sys.time(), tz = "UTC", usetz = TRUE)),
    "",
    "## Scope and verified input",
    "",
    paste0(
        "Task #003 reloaded the verified TCGA-LUAD gene-level ",
        "`RangedSummarizedExperiment` with annotation `gencode_v26`. The ",
        "object contains ", nrow(rse), " gene features and ", ncol(rse),
        " expression columns, and its only assay is `raw_counts`."
    ),
    "",
    "## 1. Why 601 columns are not 601 independent patients",
    "",
    paste0(
        "The 601 expression columns represent sequencing/expression records, ",
        "not independent people. They map to ",
        length(unique(ledger$case_id)), " cases, ",
        length(unique(ledger$sample_id)), " samples, and ",
        length(unique(ledger$aliquot_id)), " aliquots. Repeated records at ",
        "any level can create dependence that a later model must address."
    ),
    "",
    "## 2. Case, sample, aliquot, and expression record",
    "",
    "- A **case** is the patient-level GDC record.",
    "- A **sample** is a biospecimen collected from a case, such as tumour or normal tissue.",
    "- An **aliquot** is a processed portion derived from a sample.",
    "- An **expression record** is one column in the recount3 RSE, identified by its column/external ID.",
    "",
    "The observed hierarchy is:",
    "",
    "`case → sample → aliquot → expression record`",
    "",
    paste0("- Cases with multiple expression records: ", n_cases_multiple_records, "."),
    paste0("- Cases with multiple distinct sample IDs: ", n_cases_multiple_samples, "."),
    paste0(
        "- Cases with multiple distinct Primary Tumor sample IDs: ",
        n_cases_multiple_primary_samples, "."
    ),
    paste0("- Samples with multiple distinct aliquot IDs: ", n_samples_multiple_aliquots, "."),
    paste0("- Aliquots with multiple expression records: ", n_aliquots_multiple_records, "."),
    "",
    technical_summary_lines,
    "",
    "## 3. Provisional primary-comparison status",
    "",
    paste0(
        sum(ledger$eligible_primary_comparison),
        " records have sample type `Primary Tumor` or `Solid Tissue Normal`; ",
        sum(!ledger$eligible_primary_comparison),
        " other records are not eligible for that comparison. Statuses are ",
        "descriptive only and do not finalize a cohort."
    ),
    "",
    status_lines,
    "",
    paste(
        "The primary `provisional_status` above is mutually exclusive and",
        "uses the most specific observed repeat level (aliquot record, then",
        "sample aliquot, then case/group sample). Because review conditions",
        "can overlap, the ledger also retains independent Boolean flags. Their",
        "non-mutually-exclusive record counts are:"
    ),
    "",
    review_flag_lines,
    "",
    paste0(
        "The ", sum(ledger$status_eligible_unambiguous),
        " `eligible_unambiguous` records are straightforward candidates based ",
        "only on sample type and the repeat structures checked here. Review ",
        "statuses remain unresolved; no first row, random row, average, sum, ",
        "largest library, or highest mapped-read record was chosen."
    ),
    "",
    "## 4. What `compute_read_counts()` produced",
    "",
    paste0(
        "Using recount3 `compute_read_counts(round = TRUE)` produced an ",
        nrow(read_counts), " × ", ncol(read_counts),
        " matrix in memory. It converts raw base-pair coverage to estimated ",
        "read counts by dividing each column by its average mapped read ",
        "length and rounding. This is not normalization: it does not make ",
        "library sizes equal or correct composition effects. The complete ",
        "matrix was not saved."
    ),
    paste0(
        "Average mapped length had ", sum(is.na(average_mapped_length_before)),
        " missing, ", sum(average_mapped_length_before == 0, na.rm = TRUE),
        " zero, ", sum(average_mapped_length_before < 0, na.rm = TRUE),
        " negative, and ", sum(!is.finite(average_mapped_length_before)),
        " non-finite values before conversion; the same checks were repeated ",
        "after conversion."
    ),
    paste0(
        "The read-count matrix contained ", read_count_na_only, " NA, ",
        read_count_nan, " NaN, ", read_count_infinite, " infinite, and ",
        read_count_negative, " negative values."
    ),
    "",
    "## 5. Gene read-count library-size diagnostics",
    "",
    library_summary_text("all", "All expression records"),
    library_summary_text("tumor", "Primary Tumor"),
    library_summary_text("normal", "Solid Tissue Normal"),
    "",
    paste0(
        "Gene-level read-count library size versus STAR all mapped reads had ",
        "Pearson correlation ", format(pearson_correlation, digits = 6),
        " and Spearman correlation ", format(spearman_correlation, digits = 6),
        " across ", sum(correlation_complete), " complete records. This is a ",
        "sanity diagnostic, not proof that every mapped read belongs to an ",
        "annotated gene."
    ),
    "",
    "## 6. Tumour/normal overlap across batch and tissue-source site",
    "",
    paste0(
        "Among eligible records, ", nrow(sample_type_by_batch),
        " CGC batch levels were present and ",
        sum(sample_type_by_batch$both_groups_represented),
        " contained both tumour and normal records."
    ),
    paste0(
        nrow(sample_type_by_tss), " tissue-source sites were present and ",
        sum(sample_type_by_tss$both_groups_represented),
        " contained both tumour and normal records. Levels containing only ",
        "one group make group/batch or group/site separation a potential ",
        "modelling concern, but no correction was attempted."
    ),
    paste0(
        "Sequencing platform had ", length(platform_values), " non-missing level(s): ",
        paste(platform_values, collapse = ", "), ". Sequencing center had ",
        length(center_values), " non-missing level(s): ",
        paste(center_values, collapse = ", "), "."
    ),
    "",
    "## 7. Decisions still unresolved",
    "",
    "The following still require an explicit scientific decision:",
    "",
    "- how to resolve multiple expression records from one aliquot;",
    "- how to handle multiple aliquots from one sample;",
    "- how to handle multiple same-group samples from one case;",
    "- whether and how to use matched tumour-normal pairs;",
    "- the final eligible cohort and independence structure;",
    "- whether batch or tissue-source-site variables belong in the later model;",
    "- gene filtering, count normalization, and the differential-expression design.",
    "",
    "## 8. Explicitly not performed",
    "",
    "This task did **not** perform:",
    "",
    "- gene filtering;",
    "- normalization;",
    "- TMM;",
    "- PCA exclusion;",
    "- differential expression;",
    "- candidate-gene selection;",
    "- batch correction;",
    "- scoring.",
    ""
)

dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
write.csv(
    ledger,
    file.path(output_dir, "expression_record_ledger.csv"),
    row.names = FALSE,
    na = ""
)
write.csv(
    repeated_cases,
    file.path(output_dir, "repeated_cases.csv"),
    row.names = FALSE,
    na = ""
)
write.csv(
    repeated_samples,
    file.path(output_dir, "repeated_samples.csv"),
    row.names = FALSE,
    na = ""
)
write.csv(
    repeated_aliquots,
    file.path(output_dir, "repeated_aliquots.csv"),
    row.names = FALSE,
    na = ""
)
if (!is.null(technical_duplicate_check)) {
    write.csv(
        technical_duplicate_check,
        file.path(output_dir, "technical_duplicate_check.csv"),
        row.names = FALSE,
        na = ""
    )
}
write.csv(
    count_qc_summary,
    file.path(output_dir, "count_qc_summary.csv"),
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
writeLines(
    summary_lines,
    file.path(output_dir, "cohort_diagnostics_summary.md"),
    useBytes = TRUE
)

message("Cohort/count diagnostics complete. Outputs: ", output_dir)
