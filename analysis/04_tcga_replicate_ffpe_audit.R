#!/usr/bin/env Rscript

# TCGA-LUAD RNA replicate and FFPE audit.
#
# This script audits the original recount3 expression records. It does not
# filter genes, normalize counts, aggregate records, delete samples, perform
# differential-expression testing, correct batch effects, or save a matrix.

required_packages <- c("recount3", "SummarizedExperiment")
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

script_argument <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
if (length(script_argument) == 1L) {
    script_path <- normalizePath(sub("^--file=", "", script_argument))
    repository_root <- dirname(dirname(script_path))
} else {
    repository_root <- normalizePath(getwd())
}

output_dir <- file.path(repository_root, "outputs", "replicate_ffpe_audit")
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

task2_project_file <- file.path(
    repository_root, "outputs", "reconnaissance", "project_record.csv"
)
task4_metrics_file <- file.path(
    repository_root, "outputs", "sample_qc", "sample_qc_metrics.csv"
)
if (!file.exists(task2_project_file)) {
    stop("Task #002 project record is missing: ", task2_project_file)
}
if (!file.exists(task4_metrics_file)) {
    stop("Task #004 sample QC metrics are missing: ", task4_metrics_file)
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

task4_metrics <- read.csv(task4_metrics_file, stringsAsFactors = FALSE)
required_task4_fields <- c(
    "sample_id", "sample_submitter_id", "n_expression_records_aggregated",
    "raw_library_size_before_filtering", "raw_library_size_after_filtering",
    "tmm_normalization_factor", "effective_library_size", "MDS1", "MDS2",
    "PC1", "PC2", "RLE_median_logCPM", "RLE_IQR_logCPM"
)
missing_task4_fields <- setdiff(required_task4_fields, names(task4_metrics))
if (length(missing_task4_fields) > 0L) {
    stop(
        "Task #004 sample_qc_metrics.csv is missing: ",
        paste(missing_task4_fields, collapse = ", ")
    )
}
if (anyDuplicated(task4_metrics$sample_id)) {
    stop("Task #004 sample_qc_metrics.csv has duplicated sample_id values.")
}

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
    stop("Required annotation 'gencode_v26' is unavailable.")
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
    stop("Expected exactly one TCGA-LUAD project record; found ", nrow(project_record))
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
    stop("Loaded RSE does not identify pinned TCGA-LUAD/gencode_v26.")
}
if (!identical(assayNames(rse), "raw_counts")) {
    stop("Expected exactly one assay named `raw_counts`.")
}
expected_dimensions <- c(
    as.integer(task2_project$n_features_loaded),
    as.integer(task2_project$n_samples_loaded)
)
if (!identical(as.integer(dim(rse)), expected_dimensions)) {
    stop("Loaded RSE dimensions do not match Task #002.")
}

sample_metadata <- as.data.frame(colData(rse))
is_missing <- function(x) {
    is.na(x) | trimws(as.character(x)) == ""
}

field_category <- function(field_name) {
    if (grepl("ffpe", field_name, ignore.case = TRUE)) return("ffpe")
    if (grepl("preserv|fixation|frozen", field_name, ignore.case = TRUE)) {
        return("preservation")
    }
    if (grepl("tumor_descriptor", field_name, ignore.case = TRUE)) {
        return("tumor_descriptor")
    }
    if (grepl("tissue_type", field_name, ignore.case = TRUE)) {
        return("tissue_type")
    }
    if (grepl("annotations?", field_name, ignore.case = TRUE)) {
        return("annotation")
    }
    if (grepl("aliquot", field_name, ignore.case = TRUE)) return("aliquot")
    if (grepl("analyte", field_name, ignore.case = TRUE)) return("analyte")
    if (grepl("portion", field_name, ignore.case = TRUE)) return("portion")
    if (grepl("vial", field_name, ignore.case = TRUE)) return("vial")
    if (grepl("sample", field_name, ignore.case = TRUE)) return("sample")
    if (grepl("^recount_(qc|seq_qc)\\.", field_name, ignore.case = TRUE) ||
        grepl("quality|qc_flag|flag", field_name, ignore.case = TRUE)) {
        return("qc_or_flag")
    }
    "other"
}

metadata_field_inventory <- do.call(rbind, lapply(
    names(sample_metadata),
    function(field_name) {
        values <- sample_metadata[[field_name]]
        complete_values <- as.character(values[!is_missing(values)])
        unique_values <- unique(complete_values)
        data.frame(
            field_name = field_name,
            R_class = paste(class(values), collapse = ";"),
            audit_category = field_category(field_name),
            relevant_to_replicate_ffpe_audit =
                field_category(field_name) != "other",
            n_records = length(values),
            n_nonmissing = length(complete_values),
            n_missing = sum(is_missing(values)),
            n_unique_nonmissing = length(unique_values),
            example_values = paste(head(unique_values, 5L), collapse = " | "),
            stringsAsFactors = FALSE
        )
    }
))

fields_matching <- function(pattern) {
    names(sample_metadata)[grepl(pattern, names(sample_metadata), ignore.case = TRUE)]
}
concept_patterns <- c(
    is_ffpe = "ffpe",
    preservation_method = "preserv|fixation|frozen",
    sample_or_vial = "samples\\.(sample_id|submitter_id|sample_type)|cgc_sample",
    portion = "portions\\.|cgc_portion",
    analyte = "analytes\\.|cgc_.*analyte",
    aliquot = "aliquots\\.|cgc_.*aliquot",
    tumor_descriptor = "tumor_descriptor",
    tissue_type = "tissue_type",
    annotations = "annotations?",
    qc_or_flags = "^recount_(qc|seq_qc)\\.|quality|qc_flag|flag"
)
metadata_concept_availability <- do.call(rbind, lapply(
    names(concept_patterns),
    function(concept) {
        matched <- fields_matching(concept_patterns[[concept]])
        nonempty <- matched[vapply(
            matched,
            function(field) any(!is_missing(sample_metadata[[field]])),
            logical(1)
        )]
        data.frame(
            concept = concept,
            available_field_count = length(matched),
            fields_with_any_value_count = length(nonempty),
            available_fields = paste(matched, collapse = ";"),
            fields_with_any_value = paste(nonempty, collapse = ";"),
            stringsAsFactors = FALSE
        )
    }
))

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
    current_cgc_is_ffpe = "tcga.cgc_sample_is_ffpe",
    portion_id = "tcga.gdc_cases.samples.portions.portion_id",
    portion_submitter_id = "tcga.gdc_cases.samples.portions.submitter_id",
    portion_number = "tcga.gdc_cases.samples.portions.portion_number",
    analyte_id = "tcga.gdc_cases.samples.portions.analytes.analyte_id",
    analyte_submitter_id = "tcga.gdc_cases.samples.portions.analytes.submitter_id",
    analyte_type = "tcga.gdc_cases.samples.portions.analytes.analyte_type",
    analyte_type_id = "tcga.gdc_cases.samples.portions.analytes.analyte_type_id",
    aliquot_id = paste0(
        "tcga.gdc_cases.samples.portions.analytes.aliquots.", "aliquot_id"
    ),
    aliquot_submitter_id = paste0(
        "tcga.gdc_cases.samples.portions.analytes.aliquots.", "submitter_id"
    ),
    tissue_source_site = "tcga.gdc_cases.tissue_source_site.name",
    tissue_source_site_code = "tcga.gdc_cases.tissue_source_site.code",
    batch_number = "tcga.cgc_case_batch_number",
    average_mapped_length = "recount_qc.star.average_mapped_length",
    all_mapped_reads = "recount_qc.star.all_mapped_reads",
    input_reads = "recount_qc.star.number_of_input_reads",
    uniquely_mapped_reads = "recount_qc.star.uniquely_mapped_reads_number",
    uniquely_mapped_percent = "recount_qc.star.uniquely_mapped_reads_.",
    exon_assigned_reads = "recount_qc.exon_fc_count_all.assigned",
    gene_assigned_reads = "recount_qc.gene_fc_count_all.assigned"
)
missing_verified_fields <- setdiff(verified_fields, names(sample_metadata))
if (length(missing_verified_fields) > 0L) {
    stop(
        "Required current colData field(s) missing: ",
        paste(missing_verified_fields, collapse = ", ")
    )
}
value_for <- function(role) sample_metadata[[verified_fields[[role]]]]

aliquot_barcodes <- as.character(value_for("aliquot_submitter_id"))
barcode_pattern <- paste0(
    "^TCGA-([A-Z0-9]{2})-([A-Z0-9]{4})-([0-9]{2})([A-Z])-",
    "([0-9]{2})([A-Z])-([A-Z0-9]{4})-([0-9]{2})$"
)
barcode_prototype <- data.frame(
    tss_code = character(),
    participant_code = character(),
    sample_type_code = character(),
    vial_code = character(),
    portion_code = character(),
    analyte_code = character(),
    plate_code = character(),
    center_code = character(),
    stringsAsFactors = FALSE
)
parsed <- strcapture(barcode_pattern, aliquot_barcodes, barcode_prototype)
if (anyNA(parsed)) {
    stop("At least one aliquot submitter ID failed the documented TCGA parser.")
}

parsed$case_barcode <- paste("TCGA", parsed$tss_code, parsed$participant_code, sep = "-")
parsed$tcga_sample_barcode <- paste0(
    parsed$case_barcode, "-", parsed$sample_type_code
)
parsed$vial_barcode <- paste0(parsed$tcga_sample_barcode, parsed$vial_code)
parsed$portion_barcode <- paste0(parsed$vial_barcode, "-", parsed$portion_code)
parsed$analyte_barcode <- paste0(parsed$portion_barcode, parsed$analyte_code)
parsed$aliquot_barcode_reconstructed <- paste0(
    parsed$analyte_barcode, "-", parsed$plate_code, "-", parsed$center_code
)

sample_type_code_metadata <- sprintf("%02d", as.integer(value_for("sample_type_id")))
compare_when_present <- function(parsed_values, metadata_values) {
    present <- !is_missing(metadata_values)
    c(
        n_records_checked = sum(present),
        n_pass = sum(
            as.character(parsed_values[present]) ==
                as.character(metadata_values[present]),
            na.rm = TRUE
        ),
        n_reference_missing = sum(!present)
    )
}
comparison_parsed_values <- list(
    parsed$case_barcode,
    parsed$vial_barcode,
    parsed$portion_barcode,
    parsed$analyte_barcode,
    parsed$sample_type_code,
    as.integer(parsed$portion_code),
    parsed$analyte_code
)
comparison_metadata_values <- list(
    value_for("case_submitter_id"),
    value_for("sample_submitter_id"),
    value_for("portion_submitter_id"),
    value_for("analyte_submitter_id"),
    sample_type_code_metadata,
    as.integer(value_for("portion_number")),
    value_for("analyte_type_id")
)
metadata_comparisons <- do.call(
    rbind,
    Map(compare_when_present, comparison_parsed_values, comparison_metadata_values)
)
comparison_mismatch_examples <- vapply(
    seq_along(comparison_parsed_values),
    function(i) {
        parsed_values <- comparison_parsed_values[[i]]
        metadata_values <- comparison_metadata_values[[i]]
        mismatch <- which(
            !is_missing(metadata_values) &
                as.character(parsed_values) != as.character(metadata_values)
        )
        if (length(mismatch) == 0L) return("")
        paste0(
            aliquot_barcodes[mismatch],
            " [parsed=", parsed_values[mismatch],
            "; metadata=", metadata_values[mismatch], "]",
            collapse = " | "
        )
    },
    character(1)
)
barcode_parser_validation <- data.frame(
    check = c(
        "all_aliquot_barcodes_match_documented_pattern",
        "reconstructed_aliquot_matches_current_submitter_id",
        "parsed_case_matches_current_case_submitter_id",
        "parsed_vial_matches_current_sample_submitter_id",
        "parsed_portion_matches_current_portion_submitter_id",
        "parsed_analyte_matches_current_analyte_submitter_id",
        "parsed_sample_type_code_matches_current_metadata",
        "parsed_portion_number_matches_current_metadata",
        "parsed_analyte_code_matches_current_metadata"
    ),
    n_records_checked = c(
        ncol(rse),
        ncol(rse),
        metadata_comparisons[, "n_records_checked"]
    ),
    n_pass = c(
        sum(grepl(barcode_pattern, aliquot_barcodes)),
        sum(parsed$aliquot_barcode_reconstructed == aliquot_barcodes),
        metadata_comparisons[, "n_pass"]
    ),
    n_reference_missing = c(
        0L,
        0L,
        metadata_comparisons[, "n_reference_missing"]
    ),
    mismatch_examples = c("", "", comparison_mismatch_examples),
    stringsAsFactors = FALSE
)
barcode_parser_validation$expected_pass <-
    barcode_parser_validation$n_records_checked
barcode_parser_validation$all_passed <-
    barcode_parser_validation$n_pass == barcode_parser_validation$expected_pass
barcode_parser_validation$parser_critical <- c(TRUE, TRUE, rep(FALSE, 7L))
if (any(
    barcode_parser_validation$parser_critical &
        !barcode_parser_validation$all_passed
)) {
    failed_checks <- barcode_parser_validation[
        barcode_parser_validation$parser_critical &
            !barcode_parser_validation$all_passed,
        c("check", "n_pass", "expected_pass")
    ]
    stop(
        "TCGA barcode parser validation failed: ",
        paste(
            sprintf(
                "%s (%d/%d)",
                failed_checks$check,
                failed_checks$n_pass,
                failed_checks$expected_pass
            ),
            collapse = "; "
        )
    )
}

optional_value <- function(pattern) {
    matched <- fields_matching(pattern)
    if (length(matched) == 0L) return(rep(NA_character_, ncol(rse)))
    if (length(matched) == 1L) return(as.character(sample_metadata[[matched]]))
    vapply(seq_len(ncol(rse)), function(i) {
        pieces <- vapply(matched, function(field) {
            value <- sample_metadata[[field]][i]
            if (is_missing(value)) "" else paste0(field, "=", as.character(value))
        }, character(1))
        paste(pieces[nzchar(pieces)], collapse = " | ")
    }, character(1))
}

annotation_fields <- fields_matching("annotations?")
annotation_summary <- vapply(seq_len(ncol(rse)), function(i) {
    pieces <- vapply(annotation_fields, function(field) {
        value <- sample_metadata[[field]][i]
        if (is_missing(value)) "" else paste0(field, "=", as.character(value))
    }, character(1))
    paste(pieces[nzchar(pieces)], collapse = " | ")
}, character(1))

read_counts <- compute_read_counts(
    rse,
    round = TRUE,
    avg_mapped_read_length = verified_fields[["average_mapped_length"]]
)
if (!identical(dim(read_counts), dim(rse)) || anyNA(read_counts) ||
    any(!is.finite(read_counts)) || any(read_counts < 0)) {
    stop("compute_read_counts() returned invalid record-level read counts.")
}
record_library_size <- colSums(read_counts)

ledger <- data.frame(
    expression_record_index = seq_len(ncol(rse)),
    expression_record_name = colnames(rse),
    external_id = as.character(value_for("external_id")),
    rail_id = value_for("rail_id"),
    case_id = as.character(value_for("case_id")),
    case_submitter_id = as.character(value_for("case_submitter_id")),
    tcga_sample_barcode = parsed$tcga_sample_barcode,
    gdc_sample_id = as.character(value_for("sample_id")),
    gdc_sample_submitter_id = as.character(value_for("sample_submitter_id")),
    sample_type_code = parsed$sample_type_code,
    sample_type = as.character(value_for("sample_type")),
    vial_code = parsed$vial_code,
    vial_barcode = parsed$vial_barcode,
    portion_id = as.character(value_for("portion_id")),
    portion_code = parsed$portion_code,
    portion_barcode = parsed$portion_barcode,
    gdc_portion_number = as.character(value_for("portion_number")),
    gdc_portion_submitter_id = as.character(value_for("portion_submitter_id")),
    parsed_portion_agrees_with_gdc =
        parsed$portion_barcode == as.character(value_for("portion_submitter_id")),
    analyte_id = as.character(value_for("analyte_id")),
    analyte_code = parsed$analyte_code,
    analyte_type = as.character(value_for("analyte_type")),
    analyte_barcode = parsed$analyte_barcode,
    aliquot_id = as.character(value_for("aliquot_id")),
    aliquot_barcode = aliquot_barcodes,
    plate_code = parsed$plate_code,
    center_code = parsed$center_code,
    current_gdc_is_ffpe = as.logical(value_for("current_gdc_is_ffpe")),
    current_cgc_is_ffpe = as.character(value_for("current_cgc_is_ffpe")),
    preservation_metadata = optional_value("preserv|fixation|frozen"),
    tumor_descriptor_metadata = optional_value("tumor_descriptor"),
    tissue_type_metadata = optional_value("tissue_type"),
    current_annotation_metadata = annotation_summary,
    tissue_source_site = as.character(value_for("tissue_source_site")),
    tissue_source_site_code = as.character(value_for("tissue_source_site_code")),
    batch_number = as.character(value_for("batch_number")),
    read_count_library_size = record_library_size,
    star_all_mapped_reads = as.numeric(value_for("all_mapped_reads")),
    star_number_of_input_reads = as.numeric(value_for("input_reads")),
    star_uniquely_mapped_reads = as.numeric(value_for("uniquely_mapped_reads")),
    star_uniquely_mapped_percent = as.numeric(value_for("uniquely_mapped_percent")),
    recount_exon_assigned_reads = as.numeric(value_for("exon_assigned_reads")),
    recount_gene_assigned_reads = as.numeric(value_for("gene_assigned_reads")),
    average_mapped_read_length = as.numeric(value_for("average_mapped_length")),
    stringsAsFactors = FALSE,
    check.names = FALSE
)

task4_match <- match(ledger$gdc_sample_id, task4_metrics$sample_id)
ledger$task4_metrics_available <- !is.na(task4_match)
ledger$task4_metrics_scope <- ifelse(
    is.na(task4_match),
    "not_in_Task4_primary_tumor_normal_cohort",
    ifelse(
        task4_metrics$n_expression_records_aggregated[task4_match] > 1L,
        "Task4_sum_across_multiple_records_for_GDC_sample_id",
        "Task4_single_record_GDC_sample_id"
    )
)
ledger$task4_n_expression_records_aggregated <-
    task4_metrics$n_expression_records_aggregated[task4_match]
ledger$task4_sample_level_raw_library_size_before_filtering <-
    task4_metrics$raw_library_size_before_filtering[task4_match]
ledger$task4_sample_level_raw_library_size_after_filtering <-
    task4_metrics$raw_library_size_after_filtering[task4_match]
ledger$task4_sample_level_tmm_factor <-
    task4_metrics$tmm_normalization_factor[task4_match]
ledger$task4_sample_level_effective_library_size <-
    task4_metrics$effective_library_size[task4_match]
ledger$task4_sample_level_MDS1 <- task4_metrics$MDS1[task4_match]
ledger$task4_sample_level_MDS2 <- task4_metrics$MDS2[task4_match]
ledger$task4_sample_level_PC1 <- task4_metrics$PC1[task4_match]
ledger$task4_sample_level_PC2 <- task4_metrics$PC2[task4_match]
ledger$task4_sample_level_RLE_median <-
    task4_metrics$RLE_median_logCPM[task4_match]
ledger$task4_sample_level_RLE_IQR <- task4_metrics$RLE_IQR_logCPM[task4_match]

# Curated exact barcode lists from archived official Broad GDAC reports.
# These are evidence records, not a rule inferred from the plate or vial alone.
historical_ffpe_validation_a278 <- c(
    "TCGA-44-2656-01A-02R-A278-07",
    "TCGA-44-2662-01A-01R-A278-07",
    "TCGA-44-2665-01A-01R-A278-07",
    "TCGA-44-2666-01A-01R-A278-07",
    "TCGA-44-2668-01A-01R-A278-07",
    "TCGA-44-3917-01A-01R-A278-07",
    "TCGA-44-3918-01A-01R-A278-07",
    "TCGA-44-4112-01A-01R-A278-07",
    "TCGA-44-5645-01A-01R-A278-07",
    "TCGA-44-6146-01A-11R-A278-07",
    "TCGA-44-6147-01A-11R-A278-07",
    "TCGA-44-6775-01A-11R-A278-07"
)
historical_ffpe_a277 <- c(
    "TCGA-44-2656-01B-06R-A277-07",
    "TCGA-44-2662-01B-02R-A277-07",
    "TCGA-44-2665-01B-06R-A277-07",
    "TCGA-44-2666-01B-02R-A277-07",
    "TCGA-44-2668-01B-02R-A277-07",
    "TCGA-44-3917-01B-02R-A277-07",
    "TCGA-44-3918-01B-02R-A277-07",
    "TCGA-44-4112-01B-06R-A277-07",
    "TCGA-44-5645-01B-04R-A277-07",
    "TCGA-44-6146-01B-04R-A277-07",
    "TCGA-44-6147-01B-06R-A277-07",
    "TCGA-44-6775-01C-02R-A277-07"
)

gdac_2017_replicate_pairs <- data.frame(
    removed_older_aliquot = c(
        "TCGA-44-2656-01A-02R-0946-07",
        "TCGA-44-2662-01A-01R-0946-07",
        "TCGA-44-2666-01A-01R-0946-07",
        "TCGA-44-2668-01A-01R-0946-07",
        "TCGA-44-3918-01A-01R-1107-07",
        "TCGA-44-5645-01A-01R-1628-07",
        "TCGA-44-6146-01A-11R-1755-07",
        "TCGA-44-6147-01A-11R-1755-07",
        "TCGA-44-6775-01A-11R-1858-07"
    ),
    chosen_later_aliquot = c(
        "TCGA-44-2656-01A-02R-A278-07",
        "TCGA-44-2662-01A-01R-A278-07",
        "TCGA-44-2666-01A-01R-A278-07",
        "TCGA-44-2668-01A-01R-A278-07",
        "TCGA-44-3918-01A-01R-A278-07",
        "TCGA-44-5645-01A-01R-A278-07",
        "TCGA-44-6146-01A-11R-A278-07",
        "TCGA-44-6147-01A-11R-A278-07",
        "TCGA-44-6775-01A-11R-A278-07"
    ),
    stringsAsFactors = FALSE
)

current_a278 <- ledger$aliquot_barcode[ledger$plate_code == "A278"]
current_ffpe <- ledger$aliquot_barcode[ledger$current_gdc_is_ffpe]
if (!setequal(current_a278, historical_ffpe_validation_a278)) {
    stop("Current A278 RNA aliquots do not match the curated historical list.")
}
if (!setequal(current_ffpe, historical_ffpe_a277)) {
    stop("Current GDC is_ffpe RNA records do not match the historical A277 list.")
}

ledger$historical_noncanonical <-
    ledger$aliquot_barcode %in% c(
        historical_ffpe_validation_a278, historical_ffpe_a277
    )
ledger$historical_ffpe_annotation <- ifelse(
    ledger$aliquot_barcode %in% historical_ffpe_validation_a278,
    "Item is noncanonical; FFPE Validation",
    ifelse(
        ledger$aliquot_barcode %in% historical_ffpe_a277,
        "Item is noncanonical; FFPE",
        NA_character_
    )
)
ledger$historical_ffpe_source <- ifelse(
    ledger$aliquot_barcode %in% historical_ffpe_validation_a278,
    "Broad GDAC 2014-04-16 FFPE Cases",
    ifelse(
        ledger$aliquot_barcode %in% historical_ffpe_a277,
        "Broad GDAC 2016-01-28 LUAD FFPE Cases",
        NA_character_
    )
)
ledger$ffpe_or_ffpe_validation_record <-
    ledger$current_gdc_is_ffpe | ledger$historical_noncanonical
ledger$gdac_2017_replicate_status <- ifelse(
    ledger$aliquot_barcode %in% gdac_2017_replicate_pairs$chosen_later_aliquot,
    "chosen_later_plate_by_GDAC_analyte_replicate_filter",
    ifelse(
        ledger$aliquot_barcode %in% gdac_2017_replicate_pairs$removed_older_aliquot,
        "removed_older_plate_by_GDAC_analyte_replicate_filter",
        "not_listed_in_curated_2017_mRNA_pair_table"
    )
)

count_records <- function(key) {
    counts <- table(key)
    as.integer(counts[key])
}
count_distinct <- function(child, parent) {
    groups <- split(seq_along(parent), parent)
    counts <- vapply(groups, function(i) length(unique(child[i])), integer(1))
    as.integer(counts[parent])
}

ledger$n_expression_records_for_tcga_sample <- count_records(
    ledger$tcga_sample_barcode
)
ledger$n_gdc_sample_ids_for_tcga_sample <- count_distinct(
    ledger$gdc_sample_id, ledger$tcga_sample_barcode
)
ledger$n_vials_for_tcga_sample <- count_distinct(
    ledger$vial_code, ledger$tcga_sample_barcode
)
ledger$n_analytes_for_portion <- count_distinct(
    ledger$analyte_id, ledger$portion_id
)
ledger$n_aliquots_for_analyte <- count_distinct(
    ledger$aliquot_id, ledger$analyte_id
)
ledger$n_expression_records_for_aliquot <- count_records(ledger$aliquot_id)
ledger$multiple_vial_tcga_sample <- ledger$n_vials_for_tcga_sample > 1L
ledger$multiple_analyte_portion <- ledger$n_analytes_for_portion > 1L
ledger$multiple_aliquot_analyte <- ledger$n_aliquots_for_analyte > 1L
ledger$multiple_expression_record_aliquot <-
    ledger$n_expression_records_for_aliquot > 1L

ledger$candidate_status <- NA_character_
repeated_decision_rows <- ledger$n_expression_records_for_tcga_sample > 1L
ledger$candidate_status[repeated_decision_rows] <- "unresolved"
ledger$candidate_status[
    repeated_decision_rows & ledger$ffpe_or_ffpe_validation_record
] <- "ffpe_exclude_candidate"
ledger$candidate_status[
    repeated_decision_rows & !ledger$ffpe_or_ffpe_validation_record &
        ledger$vial_code == "A"
] <- "canonical_candidate"
ledger$candidate_status[
    repeated_decision_rows & ledger$multiple_expression_record_aliquot &
        !ledger$ffpe_or_ffpe_validation_record
] <- "replicate_review"

pairwise_rows <- list()
pairwise_index <- 0L
repeated_groups <- split(
    which(repeated_decision_rows),
    ledger$tcga_sample_barcode[repeated_decision_rows]
)
for (group_name in names(repeated_groups)) {
    indices <- repeated_groups[[group_name]]
    pairs <- combn(indices, 2L)
    for (j in seq_len(ncol(pairs))) {
        first <- pairs[1L, j]
        second <- pairs[2L, j]
        relationship <- if (ledger$aliquot_id[first] == ledger$aliquot_id[second]) {
            "same_aliquot_multiple_expression_records"
        } else if (ledger$analyte_id[first] == ledger$analyte_id[second]) {
            "same_analyte_multiple_aliquots"
        } else if (ledger$gdc_sample_id[first] == ledger$gdc_sample_id[second]) {
            "same_GDC_sample_different_analyte_or_portion"
        } else {
            "different_vials_same_TCGA_sample_type"
        }
        first_counts <- read_counts[, first]
        second_counts <- read_counts[, second]
        pairwise_index <- pairwise_index + 1L
        pairwise_rows[[pairwise_index]] <- data.frame(
            tcga_sample_barcode = group_name,
            case_submitter_id = ledger$case_submitter_id[first],
            relationship = relationship,
            first_expression_record_index = first,
            first_aliquot_barcode = ledger$aliquot_barcode[first],
            first_candidate_status = ledger$candidate_status[first],
            second_expression_record_index = second,
            second_aliquot_barcode = ledger$aliquot_barcode[second],
            second_candidate_status = ledger$candidate_status[second],
            raw_read_counts_exactly_identical = identical(
                as.vector(first_counts), as.vector(second_counts)
            ),
            raw_read_count_pearson = suppressWarnings(cor(
                first_counts, second_counts, method = "pearson"
            )),
            raw_read_count_spearman = suppressWarnings(cor(
                first_counts, second_counts, method = "spearman"
            )),
            maximum_absolute_read_count_difference = max(abs(
                first_counts - second_counts
            )),
            first_read_count_library_size = record_library_size[first],
            second_read_count_library_size = record_library_size[second],
            second_to_first_library_size_ratio =
                record_library_size[second] / record_library_size[first],
            first_star_all_mapped_reads = ledger$star_all_mapped_reads[first],
            second_star_all_mapped_reads = ledger$star_all_mapped_reads[second],
            stringsAsFactors = FALSE
        )
    }
}
replicate_pairwise_qc <- do.call(rbind, pairwise_rows)

affected_cases <- sort(unique(
    ledger$case_submitter_id[ledger$aliquot_barcode %in% historical_ffpe_a277]
))
christiana_rows <- ledger$case_submitter_id %in% affected_cases &
    ledger$sample_type == "Primary Tumor"
christiana_comparison <- ledger[christiana_rows, , drop = FALSE]
christiana_comparison$record_role <- ifelse(
    christiana_comparison$aliquot_barcode %in% historical_ffpe_validation_a278,
    "01A_noncanonical_FFPE_validation_A278",
    ifelse(
        christiana_comparison$current_gdc_is_ffpe,
        "01B_or_01C_noncanonical_FFPE_A277",
        "01A_other_RNA_aliquot"
    )
)
pc2_rank <- rank(task4_metrics$PC2, ties.method = "first")
rle_rank_desc <- rank(-task4_metrics$RLE_IQR_logCPM, ties.method = "first")
rank_match <- match(christiana_comparison$gdc_sample_id, task4_metrics$sample_id)
christiana_comparison$task4_PC2_rank_lowest_first <- pc2_rank[rank_match]
christiana_comparison$task4_RLE_IQR_rank_highest_first <- rle_rank_desc[rank_match]
christiana_comparison$is_one_of_12_lowest_Task4_PC2_samples <-
    christiana_comparison$task4_PC2_rank_lowest_first <= 12L
christiana_comparison$is_one_of_12_highest_Task4_RLE_IQR_samples <-
    christiana_comparison$task4_RLE_IQR_rank_highest_first <= 12L
christiana_comparison <- christiana_comparison[order(
    christiana_comparison$case_submitter_id,
    christiana_comparison$vial_code,
    christiana_comparison$plate_code
), ]

current_ffpe_sample_ids <- unique(ledger$gdc_sample_id[
    ledger$current_gdc_is_ffpe & ledger$sample_type == "Primary Tumor"
])
bottom_12_pc2_sample_ids <- task4_metrics$sample_id[order(task4_metrics$PC2)[1:12]]
bottom_12_pc2_exactly_current_ffpe_bc <- setequal(
    current_ffpe_sample_ids, bottom_12_pc2_sample_ids
)
n_current_ffpe_in_top_12_rle <- sum(
    current_ffpe_sample_ids %in%
        task4_metrics$sample_id[order(
            task4_metrics$RLE_IQR_logCPM, decreasing = TRUE
        )[1:12]]
)

a278_audit <- ledger[ledger$aliquot_barcode %in% historical_ffpe_validation_a278,
    , drop = FALSE
]
a278_audit$paired_current_older_aliquot <- vapply(
    a278_audit$analyte_id,
    function(analyte_id) {
        candidates <- ledger$aliquot_barcode[
            ledger$analyte_id == analyte_id & ledger$plate_code != "A278"
        ]
        paste(candidates, collapse = ";")
    },
    character(1)
)
a278_audit$n_paired_current_older_aliquots <- ifelse(
    nzchar(a278_audit$paired_current_older_aliquot),
    lengths(strsplit(a278_audit$paired_current_older_aliquot, ";", fixed = TRUE)),
    0L
)
a278_audit$paired_older_record_index <- vapply(
    a278_audit$paired_current_older_aliquot,
    function(barcode) {
        if (!nzchar(barcode)) return(NA_integer_)
        match(strsplit(barcode, ";", fixed = TRUE)[[1L]][1L], ledger$aliquot_barcode)
    },
    integer(1)
)
a278_audit$paired_older_read_count_library_size <-
    ledger$read_count_library_size[a278_audit$paired_older_record_index]
a278_audit$paired_older_star_all_mapped_reads <-
    ledger$star_all_mapped_reads[a278_audit$paired_older_record_index]
a278_audit$paired_raw_read_count_pearson <- vapply(
    seq_len(nrow(a278_audit)),
    function(i) {
        paired <- a278_audit$paired_older_record_index[i]
        if (is.na(paired)) return(NA_real_)
        suppressWarnings(cor(
            read_counts[, a278_audit$expression_record_index[i]],
            read_counts[, paired],
            method = "pearson"
        ))
    },
    numeric(1)
)
a278_audit$historical_2017_pair_verification <- ifelse(
    a278_audit$aliquot_barcode %in% gdac_2017_replicate_pairs$chosen_later_aliquot,
    "verified_as_chosen_later_plate_in_cited_GDAC_2017_mRNA_report",
    "not_listed_as_mRNA_pair_in_cited_GDAC_2017_snapshot"
)

repeated_sample_decision_table <- ledger[repeated_decision_rows, , drop = FALSE]
repeated_sample_decision_table <- repeated_sample_decision_table[order(
    repeated_sample_decision_table$tcga_sample_barcode,
    repeated_sample_decision_table$vial_code,
    repeated_sample_decision_table$plate_code,
    repeated_sample_decision_table$expression_record_index
), ]

primary_rows <- ledger$sample_type %in% c("Primary Tumor", "Solid Tissue Normal")
scenario_candidate_rows <- primary_rows & !ledger$ffpe_or_ffpe_validation_record
scenario_repeated_groups <- table(ledger$tcga_sample_barcode[scenario_candidate_rows])
canonical_non_ffpe_scenario <- data.frame(
    metric = c(
        "original_primary_tumor_normal_expression_records",
        "provisional_ffpe_or_ffpe_validation_exclude_candidates",
        "remaining_candidate_expression_records_before_replicate_resolution",
        "remaining_primary_tumor_expression_records",
        "remaining_solid_tissue_normal_expression_records",
        "remaining_unique_tcga_sample_barcodes",
        "remaining_unique_gdc_sample_ids",
        "remaining_unique_cases",
        "remaining_tcga_sample_barcodes_with_multiple_expression_records",
        "potential_records_after_one_record_per_tcga_sample_resolution"
    ),
    value = c(
        sum(primary_rows),
        sum(primary_rows & ledger$ffpe_or_ffpe_validation_record),
        sum(scenario_candidate_rows),
        sum(scenario_candidate_rows & ledger$sample_type == "Primary Tumor"),
        sum(scenario_candidate_rows & ledger$sample_type == "Solid Tissue Normal"),
        length(unique(ledger$tcga_sample_barcode[scenario_candidate_rows])),
        length(unique(ledger$gdc_sample_id[scenario_candidate_rows])),
        length(unique(ledger$case_id[scenario_candidate_rows])),
        sum(scenario_repeated_groups > 1L),
        length(unique(ledger$tcga_sample_barcode[scenario_candidate_rows]))
    ),
    interpretation = c(
        "No selection applied; Primary Tumor plus Solid Tissue Normal only.",
        "12 current GDC FFPE A277 records plus 12 historical noncanonical FFPE-validation A278 records.",
        "Still includes unresolved duplicate recount3 records for one aliquot.",
        "Record count, not yet a final independent-observation count.",
        "No normal record is flagged by the current/historical FFPE evidence used here.",
        "Conceptual TCGA sample barcode excludes vial and lower biospecimen levels.",
        "GDC sample IDs remaining under this provisional rule.",
        "One affected case has no remaining record under this provisional rule.",
        "The TCGA-38-4625 aliquot still has two recount3 expression records.",
        "Illustrative only; requires a separate, justified replicate choice."
    ),
    stringsAsFactors = FALSE
)

repeat_structure_summary <- data.frame(
    metric = c(
        "expression_records",
        "current_gdc_ffpe_records",
        "historical_noncanonical_ffpe_validation_A278_records",
        "historical_noncanonical_ffpe_A277_records",
        "tcga_sample_barcodes_with_multiple_vials",
        "portions_with_multiple_analytes",
        "analytes_with_multiple_aliquots",
        "aliquots_with_multiple_expression_records",
        "barcode_to_gdc_portion_metadata_mismatches",
        "repeated_tcga_sample_groups_in_decision_table",
        "bottom_12_PC2_exactly_current_FFPE_B_or_C",
        "current_FFPE_B_or_C_records_among_top_12_RLE_IQR"
    ),
    value = c(
        nrow(ledger),
        sum(ledger$current_gdc_is_ffpe),
        sum(ledger$aliquot_barcode %in% historical_ffpe_validation_a278),
        sum(ledger$aliquot_barcode %in% historical_ffpe_a277),
        length(unique(ledger$tcga_sample_barcode[ledger$multiple_vial_tcga_sample])),
        length(unique(ledger$portion_id[ledger$multiple_analyte_portion])),
        length(unique(ledger$analyte_id[ledger$multiple_aliquot_analyte])),
        length(unique(ledger$aliquot_id[ledger$multiple_expression_record_aliquot])),
        sum(!ledger$parsed_portion_agrees_with_gdc),
        length(unique(ledger$tcga_sample_barcode[repeated_decision_rows])),
        bottom_12_pc2_exactly_current_ffpe_bc,
        n_current_ffpe_in_top_12_rle
    ),
    stringsAsFactors = FALSE
)

evidence_sources <- data.frame(
    source = c(
        "GDC TCGA Barcode documentation",
        "GDC Portion / Analyte Codes",
        "Broad GDAC 2014-04-16 FFPE Cases",
        "Broad GDAC 2016-01-28 LUAD FFPE Cases",
        "Broad GDAC 2017-10-29 Replicate Samples"
    ),
    url = c(
        "https://docs.gdc.cancer.gov/Encyclopedia/pages/TCGA_Barcode/",
        "https://gdc.cancer.gov/resources-tcga-users/tcga-code-tables/portion-analyte-codes",
        "https://gdac.broadinstitute.org/runs/stddata__2014_04_16/samples_report/FFPE_Cases.html",
        "https://gdac.broadinstitute.org/runs/stddata__latest/samples_report/LUAD_FFPE_Cases.html",
        "https://gdac.broadinstitute.org/runs/gdc/report_2017_10_29/Replicate_Samples.html"
    ),
    evidence_used = c(
        "Barcode hierarchy and component semantics.",
        "R means RNA; A278 is a plate code, not an analyte code.",
        "Exact A278 RNA aliquots annotated Item is noncanonical / FFPE Validation.",
        "Exact B/C A277 RNA aliquots annotated Item is noncanonical / FFPE.",
        "Nine current older-vs-A278 RNA pairs and the later-plate replicate rule."
    ),
    stringsAsFactors = FALSE
)

scenario_value <- function(metric) {
    canonical_non_ffpe_scenario$value[
        canonical_non_ffpe_scenario$metric == metric
    ]
}
status_counts <- table(repeated_sample_decision_table$candidate_status)
status_lines <- paste0(
    "- `", names(status_counts), "`: ", as.integer(status_counts)
)

summary_lines <- c(
    "# TCGA-LUAD RNA replicate and FFPE audit",
    "",
    paste0("Generated: ", format(Sys.time(), tz = "UTC"), " UTC"),
    "",
    "## Scope",
    "",
    paste0(
        "This audit reloaded the original ", nrow(rse), " × ", ncol(rse),
        " TCGA-LUAD recount3 `gencode_v26` object and inspected all ",
        ncol(sample_metadata), " current `colData()` fields. It did not filter, ",
        "normalize, aggregate, delete, or perform differential-expression analysis."
    ),
    "",
    "## 1. Why GDC sample_id alone was insufficient",
    "",
    paste(
        "A GDC `sample_id` identifies the current sample entity, but one such entity",
        "can still contain more than one RNA aliquot or more than one recount3",
        "expression record. In this dataset, 11 RNA analytes have multiple aliquots,",
        "and one aliquot has two recount3 expression records. Therefore, matching",
        "only on `sample_id` does not prove that columns are sequencing lanes or",
        "technical replicates that should be summed."
    ),
    "",
    "## 2. Biospecimen hierarchy and validated barcode parser",
    "",
    "The documented TCGA hierarchy used here is:",
    "",
    "`case → TCGA sample type → vial → portion → analyte → aliquot → recount3 expression record`",
    "",
    paste(
        "A vial is an ordered subdivision of a TCGA sample; a portion is material",
        "cut from the vial; an analyte is the molecular material extracted from the",
        "portion; and an aliquot is a plate/well distribution of that analyte. The",
        "letter `R` is the RNA analyte code. `A278` occupies the plate segment of the",
        "aliquot barcode—it is not a sample, vial, portion, or analyte code."
    ),
    paste0(
        "All ", nrow(ledger), " aliquot barcodes matched the documented structure, ",
        "and every aliquot was reconstructed exactly. Case, vial, analyte, ",
        "sample-type code, and analyte code agreed with current recount3/GDC ",
        "metadata. Two FFPE records have inconsistent parallel portion metadata: ",
        "TCGA-44-6146-01B-04R-A277-07 encodes portion 04 while the portion fields ",
        "say 03, and TCGA-44-4112-01B-06R-A277-07 encodes portion 06 while those ",
        "fields say 05. The validation table preserves these discrepancies."
    ),
    "",
    "## 3. What current colData can and cannot tell us",
    "",
    paste0(
        "Current `tcga.gdc_cases.samples.is_ffpe` identifies ",
        sum(ledger$current_gdc_is_ffpe), " records as FFPE; the parallel CGC field ",
        "agrees. All are the 12 Christiana 01B/01C A277 RNA records."
    ),
    paste(
        "No preservation-method, tumour-descriptor, or tissue-type field is present",
        "in this recount3 `colData()`. Sample- and portion-level annotation columns",
        "exist but contain no values for these 601 records. The field inventories",
        "make these absences explicit rather than filling them by guesswork."
    ),
    "",
    "## 4. The 12 Christiana B/C records and the Task #004 anomaly",
    "",
    paste0(
        "The 12 lowest PC2 sample-level values from Task #004 are exactly the 12 ",
        "current GDC FFPE 01B/01C samples: ",
        bottom_12_pc2_exactly_current_ffpe_bc, ". All 12 have RLE IQR above 2.0; ",
        n_current_ffpe_in_top_12_rle,
        " of them occupy the 12 highest RLE-IQR ranks. Thus FFPE status explains ",
        "the discrete low-PC2 cluster and most of the extreme RLE spread, although ",
        "high RLE is not unique to FFPE records."
    ),
    paste(
        "The archived 2016 LUAD FFPE report independently lists these exact A277",
        "RNA barcodes as `Item is noncanonical` with note `FFPE`. This audit does",
        "not delete them; it labels them `ffpe_exclude_candidate` provisionally."
    ),
    paste(
        "PCA, RLE, and TMM columns are carried over from Task #004. For a B/C",
        "sample with one expression record they are record-specific; for an 01A",
        "sample with two aliquots they describe the previously aggregated GDC",
        "sample and are explicitly labelled `aggregated_sample_level_not_record_specific`.",
        "They must not be interpreted as separate A278-versus-older-aliquot metrics."
    ),
    "",
    "## 5. What A278 represents",
    "",
    paste0(
        "There are ", nrow(a278_audit), " current A278 RNA aliquots. Current GDC ",
        "sample-level `is_ffpe` is FALSE for them because they belong to 01A sample ",
        "entities. However, the archived 2014 GDAC FFPE report lists every exact ",
        "A278 RNA barcode here as `Item is noncanonical` / `FFPE Validation`. This ",
        "is aliquot-level historical evidence that is absent from current `colData()`."
    ),
    paste0(
        sum(a278_audit$n_paired_current_older_aliquots > 0L), " of the 12 A278 ",
        "records have an older aliquot from the same current GDC RNA analyte; the ",
        "TCGA-44-3917 A278 record has no older RNA aliquot in this recount3 object. ",
        "Nine pairs are also explicitly present in the cited 2017 GDAC mRNA ",
        "replicate table, where the generic later-plate rule chose A278. The two ",
        "remaining current pairs are not independently listed as mRNA pairs in that ",
        "snapshot."
    ),
    paste0(
        "For the 11 current A278/older-aliquot pairs, raw reconstructed read-count ",
        "Pearson correlations range from ",
        format(
            min(a278_audit$paired_raw_read_count_pearson, na.rm = TRUE),
            digits = 4
        ),
        " to ",
        format(
            max(a278_audit$paired_raw_read_count_pearson, na.rm = TRUE),
            digits = 4
        ),
        ". Record-level library sizes, mapped-read fields, and pairwise correlations ",
        "are retained in the A278 and pairwise-QC tables without normalization or summing."
    ),
    paste(
        "These historical records encode two different ideas: GDAC's generic",
        "replicate filter preferred a later plate, while the earlier FFPE report",
        "identified A278 as noncanonical FFPE-validation material. For a canonical",
        "non-FFPE cohort, the latter evidence is directly relevant; the apparent",
        "conflict must not be hidden by summing the two aliquots."
    ),
    "",
    "## 6. Why sumTechReps() was not automatically justified",
    "",
    paste(
        "The repeated 01A columns are distinct aliquots of the same RNA analyte, not",
        "documented sequencing lanes. One aliquot may be canonical material while",
        "the A278 aliquot is historical FFPE-validation material. Summing would mix",
        "different biospecimen statuses and erase the evidence needed to choose the",
        "canonical observation. The separate TCGA-38-4625 case contains two recount3",
        "records for the exact same aliquot, but even there this audit does not choose",
        "or aggregate a record because their provenance and count differences require",
        "a dedicated decision."
    ),
    "",
    "## 7. Provisional decision table",
    "",
    "The repeated-sample table uses only the requested provisional labels:",
    "",
    status_lines,
    "",
    paste(
        "`canonical_candidate` marks non-FFPE 01A RNA records where a competing",
        "historical FFPE/FFPE-validation record exists. `ffpe_exclude_candidate`",
        "marks current FFPE or exact historically noncanonical FFPE-validation",
        "barcodes. `replicate_review` marks the unresolved exact-aliquot duplicate.",
        "No label has been applied as a cohort operation."
    ),
    "",
    "## 8. What a canonical non-FFPE scenario would look like",
    "",
    paste0(
        "Starting with ", scenario_value(
            "original_primary_tumor_normal_expression_records"
        ), " primary tumour/normal expression records, a provisional rule that ",
        "removes the 12 current FFPE A277 records and the 12 historical ",
        "FFPE-validation A278 records would leave ", scenario_value(
            "remaining_candidate_expression_records_before_replicate_resolution"
        ), " candidate records: ", scenario_value(
            "remaining_primary_tumor_expression_records"
        ), " Primary Tumor and ", scenario_value(
            "remaining_solid_tissue_normal_expression_records"
        ), " Solid Tissue Normal."
    ),
    paste0(
        "Those records represent ", scenario_value(
            "remaining_unique_tcga_sample_barcodes"
        ), " TCGA sample barcodes and ", scenario_value(
            "remaining_unique_cases"
        ), " cases. One TCGA sample barcode still has two recount3 records for the ",
        "same aliquot, so a true one-record-per-sample cohort would contain ",
        scenario_value("potential_records_after_one_record_per_tcga_sample_resolution"),
        " observations only after that separate replicate choice is justified. This ",
        "scenario is descriptive and was not applied."
    ),
    "",
    "## 9. Evidence sources",
    "",
    "- [GDC TCGA Barcode documentation](https://docs.gdc.cancer.gov/Encyclopedia/pages/TCGA_Barcode/) — barcode hierarchy.",
    "- [GDC Portion / Analyte Codes](https://gdc.cancer.gov/resources-tcga-users/tcga-code-tables/portion-analyte-codes) — `R` means RNA.",
    "- [Broad GDAC 2014 FFPE Cases](https://gdac.broadinstitute.org/runs/stddata__2014_04_16/samples_report/FFPE_Cases.html) — exact A278 noncanonical FFPE-validation annotations.",
    "- [Broad GDAC 2016 LUAD FFPE Cases](https://gdac.broadinstitute.org/runs/stddata__latest/samples_report/LUAD_FFPE_Cases.html) — exact B/C A277 noncanonical FFPE annotations.",
    "- [Broad GDAC 2017 Replicate Samples](https://gdac.broadinstitute.org/runs/gdc/report_2017_10_29/Replicate_Samples.html) — later-plate RNA replicate-selection records.",
    "",
    "## Explicitly not performed",
    "",
    "- gene filtering or normalization;",
    "- TMM recalculation or new PCA/RLE analysis;",
    "- record aggregation or deletion;",
    "- differential-expression testing;",
    "- batch correction;",
    "- final cohort selection.",
    ""
)

write.csv(
    metadata_field_inventory,
    file.path(output_dir, "coldata_field_inventory.csv"),
    row.names = FALSE,
    na = ""
)
write.csv(
    metadata_concept_availability,
    file.path(output_dir, "metadata_concept_availability.csv"),
    row.names = FALSE,
    na = ""
)
write.csv(
    barcode_parser_validation,
    file.path(output_dir, "barcode_parser_validation.csv"),
    row.names = FALSE,
    na = ""
)
write.csv(
    ledger,
    file.path(output_dir, "rna_biospecimen_hierarchy_ledger.csv"),
    row.names = FALSE,
    na = ""
)
write.csv(
    repeat_structure_summary,
    file.path(output_dir, "repeat_structure_summary.csv"),
    row.names = FALSE,
    na = ""
)
write.csv(
    repeated_sample_decision_table,
    file.path(output_dir, "repeated_sample_decision_table.csv"),
    row.names = FALSE,
    na = ""
)
write.csv(
    replicate_pairwise_qc,
    file.path(output_dir, "replicate_pairwise_qc.csv"),
    row.names = FALSE,
    na = ""
)
write.csv(
    christiana_comparison,
    file.path(output_dir, "christiana_ffpe_comparison.csv"),
    row.names = FALSE,
    na = ""
)
write.csv(
    a278_audit,
    file.path(output_dir, "a278_aliquot_audit.csv"),
    row.names = FALSE,
    na = ""
)
write.csv(
    canonical_non_ffpe_scenario,
    file.path(output_dir, "canonical_non_ffpe_scenario.csv"),
    row.names = FALSE,
    na = ""
)
write.csv(
    evidence_sources,
    file.path(output_dir, "evidence_sources.csv"),
    row.names = FALSE,
    na = ""
)
writeLines(
    summary_lines,
    file.path(output_dir, "replicate_ffpe_audit_summary.md"),
    useBytes = TRUE
)

message("TCGA RNA replicate/FFPE audit complete. Outputs: ", output_dir)
