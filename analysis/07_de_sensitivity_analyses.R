#!/usr/bin/env Rscript

# Task #007: six prespecified TCGA-LUAD differential-expression sensitivity
# analyses. The committed Task #006 table is S0 and is never refitted here.
# No count matrix, DGEList, EList, or RSE is saved to the repository.

required_packages <- c(
    "recount3", "SummarizedExperiment", "edgeR", "limma", "statmod"
)
missing_packages <- required_packages[
    !vapply(required_packages, requireNamespace, logical(1), quietly = TRUE)
]
if (length(missing_packages) > 0L) {
    stop(
        "Missing required package(s): ", paste(missing_packages, collapse = ", "),
        ". Task #007 forbids package installation or updates."
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

frozen_task006_base <- "a3920f5a0916e63312fd7879cf7b189aa0332943"
git_value <- function(...) {
    trimws(system2("git", c(...), stdout = TRUE, stderr = TRUE))
}
git_status_code <- function(...) {
    as.integer(suppressWarnings(system2(
        "git", c(...), stdout = FALSE, stderr = FALSE
    )))
}
current_head <- git_value("-C", repository_root, "rev-parse", "HEAD")
if (!identical(git_value("-C", repository_root, "branch", "--show-current"), "main") ||
    !grepl(
        "SichengChen-web/luad-target-dossier",
        git_value("-C", repository_root, "remote", "get-url", "origin"),
        fixed = TRUE
    )) {
    stop("Task #007 Git branch or remote identity check failed.")
}
if (git_status_code(
    "-C", repository_root, "merge-base", "--is-ancestor",
    frozen_task006_base, current_head
) != 0L) {
    stop(
        "Frozen Task #006 base commit is not an ancestor of current HEAD: ",
        frozen_task006_base
    )
}
frozen_task006_paths <- c(
    "analysis/06_primary_differential_expression.R",
    "docs/de_design_decision_v0.1.md",
    "outputs/differential_expression/primary_de_results.csv",
    "outputs/differential_expression/primary_model_diagnostics.csv",
    "outputs/differential_expression/de_threshold_summary.csv",
    "outputs/differential_expression/design_matrix.csv",
    "outputs/differential_expression/contrast_matrix.csv"
)
if (git_status_code(
    "-C", repository_root, "diff", "--quiet",
    frozen_task006_base, current_head, "--", frozen_task006_paths
) != 0L) {
    stop(
        "Committed Task #006 frozen reference files differ between base commit ",
        frozen_task006_base, " and current HEAD."
    )
}
git_status <- git_value(
    "-C", repository_root, "status", "--porcelain", "--untracked-files=all"
)
git_status <- git_status[nzchar(git_status)]
if (length(git_status) > 0L) {
    if (any(substr(git_status, 1L, 2L) != "??")) {
        stop("A tracked file is modified; Task #007 will not continue.")
    }
    untracked_paths <- substring(git_status, 4L)
    allowed_untracked <-
        untracked_paths == "analysis/07_de_sensitivity_analyses.R" |
        untracked_paths == "docs/de_sensitivity_analysis_plan_v0.1.md" |
        startsWith(untracked_paths, "outputs/de_sensitivity/")
    if (any(!allowed_untracked)) {
        stop(
            "Unexpected untracked file(s) outside Task #007 scope: ",
            paste(untracked_paths[!allowed_untracked], collapse = ", ")
        )
    }
}

all_models <- c("S1", "S2", "S3", "S4", "S5", "S6")
execution_order <- c("S1", "S6", "S2", "S3", "S4", "S5")
trailing_arguments <- commandArgs(trailingOnly = TRUE)
model_argument <- grep("^--models=", trailing_arguments, value = TRUE)
if (length(model_argument) > 1L) {
    stop("Provide at most one --models= argument.")
}
if (length(model_argument) == 0L) {
    requested_models <- execution_order
} else {
    model_text <- sub("^--models=", "", model_argument)
    if (toupper(trimws(model_text)) == "NONE") {
        requested_models <- character(0)
    } else {
        requested_models <- toupper(trimws(strsplit(model_text, ",", fixed = TRUE)[[1L]]))
        if (length(requested_models) == 0L || any(!requested_models %in% all_models) ||
            anyDuplicated(requested_models)) {
            stop(paste(
                "--models must be NONE or a unique comma-separated subset of",
                "S1,S2,S3,S4,S5,S6."
            ))
        }
        requested_models <- execution_order[execution_order %in% requested_models]
    }
}

output_dir <- file.path(repository_root, "outputs", "de_sensitivity")
result_dir <- file.path(output_dir, "results")
figure_dir <- file.path(output_dir, "figures")
dir.create(result_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(figure_dir, recursive = TRUE, showWarnings = FALSE)

task_start <- proc.time()
format_number <- function(x, digits = 7L) {
    format(x, digits = digits, scientific = FALSE, trim = TRUE)
}
is_missing <- function(x) {
    is.na(x) | trimws(as.character(x)) == ""
}
elapsed_row <- function(metric, start_time, detail = "") {
    difference <- proc.time() - start_time
    data.frame(
        metric = metric,
        elapsed_seconds = unname(difference[["elapsed"]]),
        user_seconds = unname(difference[["user.self"]]),
        system_seconds = unname(difference[["sys.self"]]),
        detail = detail,
        recorded_utc = format(Sys.time(), tz = "UTC"),
        stringsAsFactors = FALSE
    )
}
runtime_file <- file.path(output_dir, "runtime_metrics.csv")
update_runtime <- function(new_row) {
    existing <- if (file.exists(runtime_file)) {
        read.csv(runtime_file, stringsAsFactors = FALSE)
    } else {
        new_row[0, , drop = FALSE]
    }
    existing <- existing[existing$metric != new_row$metric, , drop = FALSE]
    updated <- rbind(existing, new_row)
    metric_order <- c(
        "frozen_DGE_reconstruction", execution_order,
        "combined_comparison_output_generation", "total_Task_007_execution"
    )
    updated <- updated[order(match(updated$metric, metric_order)), , drop = FALSE]
    write.csv(updated, runtime_file, row.names = FALSE, na = "")
}
replace_model_rows <- function(file, new_rows, model_field = "model") {
    existing <- if (file.exists(file)) {
        read.csv(file, stringsAsFactors = FALSE, check.names = FALSE)
    } else {
        new_rows[0, , drop = FALSE]
    }
    replacing <- unique(as.character(new_rows[[model_field]]))
    if (nrow(existing) > 0L) {
        existing <- existing[
            !as.character(existing[[model_field]]) %in% replacing,
            , drop = FALSE
        ]
    }
    combined <- rbind(existing, new_rows)
    model_order <- c("S0", execution_order)
    combined <- combined[
        order(match(as.character(combined[[model_field]]), model_order)),
        , drop = FALSE
    ]
    write.csv(combined, file, row.names = FALSE, na = "")
}

input_paths <- list(
    task2_project = file.path(repository_root, "outputs", "reconnaissance", "project_record.csv"),
    final_ledger = file.path(repository_root, "outputs", "final_sample_qc", "final_cohort_ledger.csv"),
    gene_filter = file.path(repository_root, "outputs", "final_sample_qc", "gene_filter_status.csv"),
    task5_metrics = file.path(repository_root, "outputs", "final_sample_qc", "sample_qc_metrics.csv"),
    primary_results = file.path(repository_root, "outputs", "differential_expression", "primary_de_results.csv"),
    primary_diagnostics = file.path(repository_root, "outputs", "differential_expression", "primary_model_diagnostics.csv"),
    primary_thresholds = file.path(repository_root, "outputs", "differential_expression", "de_threshold_summary.csv"),
    primary_design = file.path(repository_root, "outputs", "differential_expression", "design_matrix.csv"),
    primary_contrast = file.path(repository_root, "outputs", "differential_expression", "contrast_matrix.csv")
)
missing_inputs <- names(input_paths)[!file.exists(unlist(input_paths))]
if (length(missing_inputs) > 0L) {
    stop("Missing frozen input(s): ", paste(missing_inputs, collapse = ", "))
}

task2_project <- read.csv(input_paths$task2_project, stringsAsFactors = FALSE)
final_ledger <- read.csv(input_paths$final_ledger, stringsAsFactors = FALSE)
stored_gene_filter <- read.csv(input_paths$gene_filter, stringsAsFactors = FALSE)
task5_metrics <- read.csv(input_paths$task5_metrics, stringsAsFactors = FALSE)
primary_results <- read.csv(
    input_paths$primary_results, stringsAsFactors = FALSE, check.names = FALSE
)
primary_diagnostics <- read.csv(
    input_paths$primary_diagnostics, stringsAsFactors = FALSE
)
primary_design <- read.csv(
    input_paths$primary_design, stringsAsFactors = FALSE, check.names = FALSE
)
primary_contrast <- read.csv(
    input_paths$primary_contrast, stringsAsFactors = FALSE, check.names = FALSE
)

primary_metric <- function(metric) {
    value <- primary_diagnostics$value[primary_diagnostics$metric == metric]
    if (length(value) != 1L) stop("Missing or duplicated primary metric: ", metric)
    value
}
required_primary_columns <- c(
    "EnsemblID", "Symbol", "gene_type", "logFC", "AveExpr", "t",
    "P.Value", "adj.P.Val", "B"
)
if (nrow(primary_results) != 29606L ||
    !all(required_primary_columns %in% names(primary_results)) ||
    anyDuplicated(primary_results$EnsemblID) ||
    primary_metric("observations") != "574" ||
    primary_metric("Tumor_observations") != "515" ||
    primary_metric("Normal_observations") != "59" ||
    primary_metric("unique_cases") != "516" ||
    primary_metric("matched_cases") != "58" ||
    primary_metric("batch_number_source") != "tcga.cgc_case_batch_number" ||
    primary_metric("blocking_variable") != "case_id" ||
    primary_metric("sample.weights") != "FALSE" ||
    primary_metric("tested_genes") != "29606" ||
    primary_metric("sensitivity_analyses_fitted") != "0") {
    stop("Committed S0 primary result failed frozen-reference assertions.")
}
if (nrow(primary_design) != 574L ||
    sum(primary_design$group == "Tumor") != 515L ||
    sum(primary_design$group == "Normal") != 59L ||
    length(unique(primary_design$case_id)) != 516L ||
    primary_contrast$Tumor_vs_Normal[primary_contrast$coefficient == "Normal"] != -1 ||
    primary_contrast$Tumor_vs_Normal[primary_contrast$coefficient == "Tumor"] != 1 ||
    any(primary_contrast$Tumor_vs_Normal[
        !primary_contrast$coefficient %in% c("Normal", "Tumor")
    ] != 0)) {
    stop("Committed S0 design or contrast failed identity assertions.")
}

reconstruction_start <- proc.time()
if (nrow(task2_project) != 1L || nrow(final_ledger) != 574L ||
    !identical(final_ledger$final_observation_index, seq_len(574L)) ||
    sum(final_ledger$sample_type == "Primary Tumor") != 515L ||
    sum(final_ledger$sample_type == "Solid Tissue Normal") != 59L ||
    length(unique(final_ledger$case_id)) != 516L ||
    nrow(stored_gene_filter) != 63856L ||
    sum(as.logical(stored_gene_filter$keep_by_filterByExpr)) != 29606L ||
    nrow(task5_metrics) != 574L ||
    !identical(task5_metrics$tcga_sample_barcode, final_ledger$tcga_sample_barcode)) {
    stop("Frozen Task #005 manifest, filter, or QC input failed assertions.")
}
aggregation_structure <- table(final_ledger$n_expression_records_aggregated)
if (!identical(names(aggregation_structure), c("1", "2")) ||
    !identical(as.integer(aggregation_structure), c(573L, 1L))) {
    stop("Frozen technical-aggregation structure differs from Task #005.")
}
technical_row <- which(final_ledger$n_expression_records_aggregated == 2L)
if (length(technical_row) != 1L ||
    final_ledger$tcga_sample_barcode[technical_row] != "TCGA-38-4625-01" ||
    final_ledger$technical_resolution[technical_row] !=
        "two_distinct_sequencing_records_same_exact_aliquot_summed") {
    stop("Frozen same-aliquot sequencing aggregation is not reproduced.")
}

remote_recount3_root <-
    "https://recount-opendata.s3.amazonaws.com/recount3/release"
cache_dir <- Sys.getenv(
    "RECOUNT3_CACHE_DIR", unset = "/private/tmp/luad-recount3-cache"
)
if (!dir.exists(cache_dir)) {
    stop("Existing recount3 cache is unavailable; Task #007 network access is off.")
}
bfc <- recount3_cache(cache_dir)
cache_info <- as.data.frame(BiocFileCache::bfcinfo(bfc))
offline_recount3_root <- file.path(
    "/private/tmp", "luad-task007-recount3-offline-release"
)
needed_relative_paths <- c(
    "human/data_sources/tcga/metadata/tcga.recount_project.MD.gz",
    "human/data_sources/tcga/metadata/AD/LUAD/tcga.tcga.LUAD.MD.gz",
    "human/data_sources/tcga/metadata/AD/LUAD/tcga.recount_project.LUAD.MD.gz",
    "human/data_sources/tcga/metadata/AD/LUAD/tcga.recount_qc.LUAD.MD.gz",
    "human/data_sources/tcga/metadata/AD/LUAD/tcga.recount_seq_qc.LUAD.MD.gz",
    "human/annotations/gene_sums/human.gene_sums.G026.gtf.gz",
    "human/data_sources/tcga/gene_sums/AD/LUAD/tcga.gene_sums.LUAD.G026.gz"
)
for (relative_path in needed_relative_paths) {
    remote_url <- paste0(remote_recount3_root, "/", relative_path)
    matches <- which(cache_info$rname == remote_url)
    if (length(matches) != 1L || !file.exists(cache_info$rpath[matches])) {
        stop("Exact cached recount3 resource unavailable: ", remote_url)
    }
    cached_path <- cache_info$rpath[matches]
    mirror_path <- file.path(offline_recount3_root, relative_path)
    dir.create(dirname(mirror_path), recursive = TRUE, showWarnings = FALSE)
    if (file.exists(mirror_path)) {
        if (!identical(normalizePath(mirror_path), normalizePath(cached_path))) {
            stop("Offline mirror does not resolve to exact cached resource: ", mirror_path)
        }
    } else if (!file.symlink(cached_path, mirror_path)) {
        stop("Could not create cached-resource symlink: ", mirror_path)
    }
}
if (!"gencode_v26" %in% annotation_options("human")) {
    stop("Required annotation gencode_v26 is unavailable.")
}
projects <- available_projects(
    organism = "human", recount3_url = offline_recount3_root,
    bfc = bfc, available_homes = "data_sources/tcga"
)
project_record <- projects[
    projects$project == "LUAD" & projects$organism == "human" &
        projects$file_source == "tcga" &
        projects$project_home == "data_sources/tcga" &
        projects$project_type == "data_sources",
    , drop = FALSE
]
if (nrow(project_record) != 1L) {
    stop("Expected exactly one cached TCGA-LUAD recount3 project record.")
}
rse <- create_rse(
    project_info = project_record, type = "gene", annotation = "gencode_v26",
    bfc = bfc, recount3_url = offline_recount3_root
)
if (!inherits(rse, "RangedSummarizedExperiment") ||
    !identical(metadata(rse)$project, "LUAD") ||
    !identical(metadata(rse)$project_home, "data_sources/tcga") ||
    !identical(metadata(rse)$annotation, "gencode_v26") ||
    !identical(assayNames(rse), "raw_counts") ||
    !identical(
        as.integer(dim(rse)),
        c(as.integer(task2_project$n_features_loaded),
          as.integer(task2_project$n_samples_loaded))
    )) {
    stop("Reconstructed RSE failed pinned TCGA-LUAD/gencode_v26 assertions.")
}

sample_metadata <- as.data.frame(colData(rse))
verified_fields <- c(
    case_id = "tcga.gdc_cases.case_id",
    sample_id = "tcga.gdc_cases.samples.sample_id",
    sample_submitter_id = "tcga.gdc_cases.samples.submitter_id",
    sample_type = "tcga.gdc_cases.samples.sample_type",
    aliquot_submitter_id = paste0(
        "tcga.gdc_cases.samples.portions.analytes.aliquots.", "submitter_id"
    ),
    batch_number = "tcga.cgc_case_batch_number",
    tissue_source_site = "tcga.gdc_cases.tissue_source_site.name",
    tissue_source_site_code = "tcga.gdc_cases.tissue_source_site.code",
    average_mapped_length = "recount_qc.star.average_mapped_length"
)
if (length(setdiff(verified_fields, names(sample_metadata))) > 0L) {
    stop("Required current recount3 colData field is missing.")
}
source_records_by_observation <- strsplit(
    final_ledger$source_expression_record_names, ";", fixed = TRUE
)
source_record_counts <- lengths(source_records_by_observation)
source_record_names <- unlist(source_records_by_observation, use.names = FALSE)
if (!identical(source_record_counts, final_ledger$n_expression_records_aggregated) ||
    sum(source_record_counts) != 575L || anyDuplicated(source_record_names)) {
    stop("Frozen source-record multiplicities are inconsistent.")
}
source_indices <- match(source_record_names, colnames(rse))
if (anyNA(source_indices)) stop("Frozen source record is absent from recount3.")
manifest_row_for_source <- rep(seq_len(574L), source_record_counts)
assert_source_field <- function(role, ledger_field) {
    current <- as.character(sample_metadata[[verified_fields[[role]]]][source_indices])
    frozen <- as.character(final_ledger[[ledger_field]][manifest_row_for_source])
    if (!identical(current, frozen)) {
        stop("Current colData differs from frozen ledger for role: ", role)
    }
}
assert_source_field("case_id", "case_id")
assert_source_field("sample_id", "sample_id")
assert_source_field("sample_submitter_id", "sample_submitter_id")
assert_source_field("sample_type", "sample_type")
assert_source_field("aliquot_submitter_id", "aliquot_barcode")
assert_source_field("batch_number", "batch_number")
assert_source_field("tissue_source_site", "tissue_source_site")
assert_source_field("tissue_source_site_code", "tissue_source_site_code")

selected_rse <- rse[, source_indices]
record_counts <- compute_read_counts(
    selected_rse, round = TRUE,
    avg_mapped_read_length = verified_fields[["average_mapped_length"]]
)
if (!identical(dim(record_counts), c(63856L, 575L)) ||
    anyNA(record_counts) || any(!is.finite(record_counts)) ||
    any(record_counts < 0)) {
    stop("compute_read_counts() returned invalid frozen-source values.")
}
aggregation_ids <- final_ledger$tcga_sample_barcode[manifest_row_for_source]
sample_level_counts <- sumTechReps(record_counts, ID = aggregation_ids)
if (!identical(colnames(sample_level_counts), final_ledger$tcga_sample_barcode) ||
    ncol(sample_level_counts) != 574L) {
    stop("Reconstructed observation order differs from frozen manifest.")
}

gene_data <- as.data.frame(rowData(rse))
gene_annotation <- data.frame(
    EnsemblID = as.character(gene_data$gene_id),
    Symbol = as.character(gene_data$gene_name),
    gene_type = as.character(gene_data$gene_type),
    stringsAsFactors = FALSE
)
if (any(is_missing(gene_annotation$EnsemblID)) ||
    anyDuplicated(gene_annotation$EnsemblID) ||
    !identical(gene_annotation$EnsemblID, stored_gene_filter$EnsemblID) ||
    !identical(gene_annotation$Symbol, stored_gene_filter$Symbol) ||
    !identical(gene_annotation$gene_type, stored_gene_filter$gene_type)) {
    stop("Reconstructed gencode_v26 annotation differs from Task #005.")
}
rownames(sample_level_counts) <- gene_annotation$EnsemblID
rownames(gene_annotation) <- gene_annotation$EnsemblID

sample_data <- final_ledger
sample_data$group <- factor(
    ifelse(sample_data$sample_type == "Primary Tumor", "Tumor", "Normal"),
    levels = c("Normal", "Tumor")
)
sample_data$batch_number <- factor(as.character(sample_data$batch_number))
sample_data$tissue_source_site <- factor(as.character(sample_data$tissue_source_site))
sample_data$case_id <- as.character(sample_data$case_id)
rownames(sample_data) <- sample_data$tcga_sample_barcode
if (!identical(as.integer(table(sample_data$group)), c(59L, 515L)) ||
    anyNA(sample_data$batch_number) || anyNA(sample_data$tissue_source_site) ||
    anyNA(sample_data$case_id)) {
    stop("Frozen modelling metadata are incomplete or inconsistent.")
}
dge_unfiltered <- DGEList(
    counts = sample_level_counts, samples = sample_data,
    group = sample_data$group, genes = gene_annotation
)
recomputed_keep <- filterByExpr(dge_unfiltered, group = sample_data$group)
stored_keep <- as.logical(stored_gene_filter$keep_by_filterByExpr)
if (!identical(unname(recomputed_keep), unname(stored_keep))) {
    stop("Recomputed filterByExpr mask differs from frozen Task #005 mask.")
}
dge <- dge_unfiltered[stored_keep, , keep.lib.sizes = FALSE]
dge <- normLibSizes(dge, method = "TMM")
tmm_tolerance <- 1e-12
max_tmm_difference <- max(abs(
    dge$samples$norm.factors - task5_metrics$tmm_normalization_factor
))
if (!identical(dim(dge), c(29606L, 574L)) ||
    !is.finite(max_tmm_difference) || max_tmm_difference > tmm_tolerance) {
    stop("Frozen DGEList dimensions or TMM reproducibility assertion failed.")
}

case_group_table <- table(sample_data$case_id, sample_data$group)
matched_cases <- rownames(case_group_table)[
    case_group_table[, "Normal"] == 1L & case_group_table[, "Tumor"] == 1L
]
if (length(matched_cases) != 58L || any(case_group_table > 1L)) {
    stop("Frozen pairing structure differs from Task #006.")
}
support_rows <- lapply(
    c("batch_number", "tissue_source_site"),
    function(variable) {
        support <- table(
            level = as.character(sample_data[[variable]]),
            group = sample_data$group
        )
        data.frame(
            variable = variable,
            level = rownames(support),
            Normal = as.integer(support[, "Normal"]),
            Tumor = as.integer(support[, "Tumor"]),
            contains_both_groups =
                support[, "Normal"] > 0L & support[, "Tumor"] > 0L,
            stringsAsFactors = FALSE
        )
    }
)
write.csv(
    do.call(rbind, support_rows),
    file.path(output_dir, "design_group_support_counts.csv"),
    row.names = FALSE, na = ""
)
update_runtime(elapsed_row(
    "frozen_DGE_reconstruction", reconstruction_start,
    paste0(
        "Exact cached TCGA-LUAD/gencode_v26; max TMM difference ",
        format(max_tmm_difference, scientific = TRUE)
    )
))
rm(rse, selected_rse, record_counts, sample_level_counts, dge_unfiltered)
invisible(gc())

model_definitions <- list(
    S1 = list(
        label = "Omit case blocking",
        formula = "~ 0 + group + batch_number",
        block = FALSE, sample_weights = FALSE, cohort = "all"
    ),
    S2 = list(
        label = "Omit TCGA/BCR case-batch adjustment",
        formula = "~ 0 + group",
        block = TRUE, sample_weights = FALSE, cohort = "all"
    ),
    S3 = list(
        label = "TSS instead of TCGA/BCR case-batch",
        formula = "~ 0 + group + tissue_source_site",
        block = TRUE, sample_weights = FALSE, cohort = "all"
    ),
    S4 = list(
        label = "TCGA/BCR case-batch plus TSS",
        formula = "~ 0 + group + batch_number + tissue_source_site",
        block = TRUE, sample_weights = FALSE, cohort = "all"
    ),
    S5 = list(
        label = "Sample-quality weights",
        formula = "~ 0 + group + batch_number",
        block = TRUE, sample_weights = TRUE, cohort = "all"
    ),
    S6 = list(
        label = "Matched pairs only",
        formula = "~ 0 + group + case_id",
        block = FALSE, sample_weights = FALSE, cohort = "matched"
    )
)

threshold_rows <- function(model, results) {
    make_row <- function(criterion, selected) {
        data.frame(
            model = model,
            criterion = criterion,
            Up = sum(selected & results$logFC > 0),
            Down = sum(selected & results$logFC < 0),
            Total = sum(selected),
            direction_definition = paste(
                "Up: logFC > 0 (higher in Tumor);",
                "Down: logFC < 0 (lower in Tumor)"
            ),
            stringsAsFactors = FALSE
        )
    }
    fdr05 <- results$adj.P.Val < 0.05
    rbind(
        make_row("BH FDR < 0.05", fdr05),
        make_row("BH FDR < 0.01", results$adj.P.Val < 0.01),
        make_row("BH FDR < 0.05 and |logFC| >= 0.5", fdr05 & abs(results$logFC) >= 0.5),
        make_row("BH FDR < 0.05 and |logFC| >= 1", fdr05 & abs(results$logFC) >= 1),
        make_row("BH FDR < 0.05 and |logFC| >= 2", fdr05 & abs(results$logFC) >= 2)
    )
}
threshold_file <- file.path(output_dir, "de_threshold_summary_by_model.csv")
replace_model_rows(threshold_file, threshold_rows("S0", primary_results))

design_diagnostic <- function(model, design) {
    singular_values <- svd(design, nu = 0L, nv = 0L)$d
    column_norms <- sqrt(colSums(design^2))
    if (any(column_norms == 0)) stop(model, " design contains a zero column.")
    normalized_design <- sweep(design, 2L, column_norms, "/")
    normalized_singular_values <- svd(normalized_design, nu = 0L, nv = 0L)$d
    nonzero_cutoff <- max(dim(normalized_design)) *
        max(normalized_singular_values) * .Machine$double.eps
    nonzero <- normalized_singular_values > nonzero_cutoff
    condition_number <- max(normalized_singular_values) /
        min(normalized_singular_values[nonzero])
    data.frame(
        model = model,
        n_rows = nrow(design),
        n_columns = ncol(design),
        rank = qr(design)$rank,
        nominal_residual_df = nrow(design) - qr(design)$rank,
        singular_values = paste(format(singular_values, digits = 16), collapse = ";"),
        normalized_singular_values = paste(
            format(normalized_singular_values, digits = 16), collapse = ";"
        ),
        normalized_condition_number = condition_number,
        calculation = paste(
            "Each nonzero design column scaled to unit L2 norm;",
            "max singular value divided by smallest nonzero singular value"
        ),
        stringsAsFactors = FALSE
    )
}

fit_sensitivity <- function(model) {
    definition <- model_definitions[[model]]
    model_start <- proc.time()
    if (definition$cohort == "matched") {
        sample_index <- dge$samples$case_id %in% matched_cases
        model_dge <- dge[, sample_index, keep.lib.sizes = FALSE]
        model_dge <- normLibSizes(model_dge, method = "TMM")
    } else {
        model_dge <- dge
    }
    model_samples <- model_dge$samples
    model_samples$group <- factor(model_samples$group, levels = c("Normal", "Tumor"))
    model_samples$batch_number <- factor(as.character(model_samples$batch_number))
    model_samples$tissue_source_site <- factor(
        as.character(model_samples$tissue_source_site)
    )
    model_samples$case_id <- factor(as.character(model_samples$case_id))
    design <- model.matrix(as.formula(definition$formula), data = model_samples)
    colnames(design)[colnames(design) == "groupNormal"] <- "Normal"
    colnames(design)[colnames(design) == "groupTumor"] <- "Tumor"
    rownames(design) <- model_samples$tcga_sample_barcode
    expected_dimensions <- if (model == "S6") c(116L, 59L) else switch(
        model, S1 = c(574L, 21L), S2 = c(574L, 2L),
        S3 = c(574L, 34L), S4 = c(574L, 53L), S5 = c(574L, 21L)
    )
    expected_group_counts <- if (model == "S6") c(58L, 58L) else c(59L, 515L)
    if (!identical(as.integer(dim(design)), expected_dimensions) ||
        !identical(as.integer(table(model_samples$group)), expected_group_counts) ||
        nrow(model_dge) != 29606L || qr(design)$rank != ncol(design) ||
        !all(c("Normal", "Tumor") %in% colnames(design))) {
        stop(model, " cohort or design assertions failed.")
    }
    if (model == "S6") {
        if (length(unique(model_samples$case_id)) != 58L ||
            !any(startsWith(colnames(design), "case_id")) ||
            any(grepl("batch_number|tissue_source_site", colnames(design)))) {
            stop("S6 fixed-effect definition is not exact.")
        }
    } else if (any(startsWith(colnames(design), "case_id"))) {
        stop(model, " unexpectedly includes case_id as a fixed effect.")
    }
    if (model == "S2" && ncol(design) != 2L) stop("S2 contains an unintended covariate.")
    if (model == "S3" && any(grepl("batch_number", colnames(design)))) {
        stop("S3 unexpectedly contains batch_number.")
    }
    if (model %in% c("S1", "S5") &&
        any(grepl("tissue_source_site", colnames(design)))) {
        stop(model, " unexpectedly contains TSS.")
    }
    expected_contrast <- setNames(numeric(ncol(design)), colnames(design))
    expected_contrast[c("Normal", "Tumor")] <- c(-1, 1)
    contrast <- matrix(
        expected_contrast,
        ncol = 1L,
        dimnames = list(colnames(design), "Tumor_vs_Normal")
    )
    if (!identical(
        as.numeric(contrast[, "Tumor_vs_Normal"]), as.numeric(expected_contrast)
    )) {
        stop(model, " contrast is not exactly Tumor - Normal.")
    }
    block <- if (definition$block) as.character(model_samples$case_id) else NULL
    if (xor(is.null(block), !definition$block)) {
        stop(model, " block setting is not exact.")
    }
    model_messages <- character(0)
    model_warnings <- character(0)
    voom_file <- file.path(figure_dir, paste0(model, "_voom_mean_variance.png"))
    png(voom_file, width = 1200, height = 900, res = 150)
    device_closed <- FALSE
    on.exit({
        if (!device_closed && grDevices::dev.cur() > 1L) grDevices::dev.off()
    }, add = TRUE)
    voom_fit <- withCallingHandlers(
        edgeR::voomLmFit(
            model_dge,
            design = design,
            block = block,
            sample.weights = definition$sample_weights,
            normalize.method = "none",
            plot = TRUE,
            save.plot = TRUE,
            keep.EList = TRUE
        ),
        message = function(condition) {
            model_messages <<- c(model_messages, conditionMessage(condition))
            invokeRestart("muffleMessage")
        },
        warning = function(condition) {
            model_warnings <<- c(model_warnings, conditionMessage(condition))
        }
    )
    grDevices::dev.off()
    device_closed <- TRUE
    if (is.null(voom_fit$EList) || nrow(voom_fit$EList$E) != 29606L ||
        ncol(voom_fit$EList$E) != nrow(design)) {
        stop(model, " voomLmFit output has unexpected dimensions.")
    }
    has_sample_weights <- "sample.weight" %in% names(voom_fit$targets)
    if (!identical(has_sample_weights, definition$sample_weights)) {
        stop(model, " sample-quality weight setting was not honored.")
    }
    consensus_correlation <- if (definition$block) voom_fit$correlation else NA_real_
    if (definition$block &&
        (length(consensus_correlation) != 1L || !is.finite(consensus_correlation))) {
        stop(model, " blocking correlation is not finite.")
    }
    contrast_fit <- limma::contrasts.fit(voom_fit, contrast)
    ebayes_fit <- limma::eBayes(contrast_fit, trend = FALSE, robust = TRUE)
    result <- limma::topTable(
        ebayes_fit, coef = "Tumor_vs_Normal", number = Inf,
        adjust.method = "BH", sort.by = "P"
    )
    if (nrow(result) != 29606L ||
        !all(required_primary_columns %in% names(result)) ||
        anyDuplicated(result$EnsemblID) ||
        !setequal(result$EnsemblID, primary_results$EnsemblID) ||
        anyNA(result[required_primary_columns]) ||
        any(!is.finite(as.matrix(result[c(
            "logFC", "AveExpr", "t", "P.Value", "adj.P.Val", "B"
        )])))) {
        stop(model, " topTable failed gene-universe or finite-value assertions.")
    }
    result <- result[, required_primary_columns]
    residual_df <- as.numeric(voom_fit$df.residual)
    nominal_residual_df <- nrow(design) - qr(design)$rank
    residual_summary <- c(
        min = min(residual_df), Q1 = unname(quantile(residual_df, 0.25)),
        median = median(residual_df), mean = mean(residual_df),
        Q3 = unname(quantile(residual_df, 0.75)), max = max(residual_df)
    )
    reduced_index <- which(residual_df < nominal_residual_df)
    reduced_rows <- data.frame(
        model = model,
        EnsemblID = model_dge$genes$EnsemblID[reduced_index],
        Symbol = model_dge$genes$Symbol[reduced_index],
        gene_type = model_dge$genes$gene_type[reduced_index],
        df.residual = residual_df[reduced_index],
        nominal_residual_df = nominal_residual_df,
        df_loss = nominal_residual_df - residual_df[reduced_index],
        stringsAsFactors = FALSE
    )
    condition_row <- design_diagnostic(model, design)
    group_support <- list(
        batch_levels = nlevels(model_samples$batch_number),
        batch_both = sum(rowSums(table(model_samples$batch_number, model_samples$group) > 0) == 2L),
        tss_levels = nlevels(model_samples$tissue_source_site),
        tss_both = sum(rowSums(table(model_samples$tissue_source_site, model_samples$group) > 0) == 2L)
    )
    model_time <- elapsed_row(
        model, model_start,
        paste0(definition$label, "; fit plus immediate checkpoint preparation")
    )
    diagnostic_row <- data.frame(
        model = model,
        label = definition$label,
        formula = definition$formula,
        observations = nrow(design),
        Tumor = sum(model_samples$group == "Tumor"),
        Normal = sum(model_samples$group == "Normal"),
        unique_cases = length(unique(model_samples$case_id)),
        matched_cases = sum(rowSums(table(model_samples$case_id, model_samples$group) > 0) == 2L),
        tested_genes = nrow(result),
        design_columns = ncol(design),
        design_rank = qr(design)$rank,
        nominal_residual_df = nominal_residual_df,
        coefficient_names = paste(colnames(design), collapse = ";"),
        contrast = "Tumor_vs_Normal = Tumor - Normal",
        contrast_vector = paste(
            paste0(names(expected_contrast), "=", expected_contrast), collapse = ";"
        ),
        positive_logFC = "higher expression in Tumor",
        block = if (definition$block) "case_id" else "NULL",
        case_id_fixed_effect = model == "S6",
        sample.weights = definition$sample_weights,
        consensus_correlation = consensus_correlation,
        residual_df_min = residual_summary["min"],
        residual_df_Q1 = residual_summary["Q1"],
        residual_df_median = residual_summary["median"],
        residual_df_mean = residual_summary["mean"],
        residual_df_Q3 = residual_summary["Q3"],
        residual_df_max = residual_summary["max"],
        genes_below_nominal_residual_df = length(reduced_index),
        all_zero_genes_in_model_cohort = sum(rowSums(model_dge$counts) == 0),
        batch_levels = group_support$batch_levels,
        batch_levels_with_both_groups = group_support$batch_both,
        tss_levels = group_support$tss_levels,
        tss_levels_with_both_groups = group_support$tss_both,
        voom_messages = paste(trimws(model_messages), collapse = " | "),
        warnings = paste(unique(model_warnings), collapse = " | "),
        stringsAsFactors = FALSE,
        check.names = FALSE
    )

    write.csv(
        result, file.path(result_dir, paste0(model, "_de_results.csv")),
        row.names = FALSE, na = ""
    )
    replace_model_rows(
        file.path(output_dir, "model_diagnostics.csv"), diagnostic_row
    )
    replace_model_rows(
        file.path(output_dir, "design_condition_diagnostics.csv"), condition_row
    )
    if (nrow(reduced_rows) == 0L) {
        reduced_rows <- data.frame(
            model = character(), EnsemblID = character(), Symbol = character(),
            gene_type = character(), df.residual = numeric(),
            nominal_residual_df = numeric(), df_loss = numeric(),
            stringsAsFactors = FALSE
        )
        existing_reduced_file <- file.path(output_dir, "reduced_residual_df_genes.csv")
        if (file.exists(existing_reduced_file)) {
            existing_reduced <- read.csv(existing_reduced_file, stringsAsFactors = FALSE)
            existing_reduced <- existing_reduced[existing_reduced$model != model, , drop = FALSE]
            write.csv(existing_reduced, existing_reduced_file, row.names = FALSE, na = "")
        } else {
            write.csv(reduced_rows, existing_reduced_file, row.names = FALSE, na = "")
        }
    } else {
        replace_model_rows(
            file.path(output_dir, "reduced_residual_df_genes.csv"), reduced_rows
        )
    }
    replace_model_rows(threshold_file, threshold_rows(model, result))

    if (model == "S5") {
        sample_weight <- as.numeric(voom_fit$targets$sample.weight)
        if (length(sample_weight) != 574L || anyNA(sample_weight) ||
            any(!is.finite(sample_weight)) || any(sample_weight <= 0)) {
            stop("S5 returned invalid sample-quality weights.")
        }
        qc_index <- match(
            model_samples$tcga_sample_barcode, task5_metrics$tcga_sample_barcode
        )
        if (anyNA(qc_index)) stop("S5 QC join failed.")
        weights_output <- data.frame(
            tcga_sample_barcode = model_samples$tcga_sample_barcode,
            case_id = as.character(model_samples$case_id),
            group = as.character(model_samples$group),
            batch_number = as.character(model_samples$batch_number),
            tissue_source_site = as.character(model_samples$tissue_source_site),
            sample_weight = sample_weight,
            RLE_IQR_logCPM = task5_metrics$RLE_IQR_logCPM[qc_index],
            effective_library_size = task5_metrics$effective_library_size[qc_index],
            PC1 = task5_metrics$PC1[qc_index],
            PC2 = task5_metrics$PC2[qc_index],
            stringsAsFactors = FALSE
        )
        summarize_weight <- function(values, category, label) {
            values_summary <- c(
                min = min(values), Q1 = unname(quantile(values, 0.25)),
                median = median(values), mean = mean(values),
                Q3 = unname(quantile(values, 0.75)), max = max(values)
            )
            data.frame(
                category = category, group_or_metric = label,
                statistic = names(values_summary), value = as.numeric(values_summary),
                n = length(values), stringsAsFactors = FALSE
            )
        }
        weight_summary <- rbind(
            summarize_weight(sample_weight, "distribution", "All"),
            summarize_weight(sample_weight[model_samples$group == "Tumor"], "distribution", "Tumor"),
            summarize_weight(sample_weight[model_samples$group == "Normal"], "distribution", "Normal"),
            data.frame(
                category = "association",
                group_or_metric = rep(c("RLE_IQR_logCPM", "effective_library_size"), each = 2L),
                statistic = rep(c("Pearson", "Spearman"), 2L),
                value = c(
                    cor(sample_weight, weights_output$RLE_IQR_logCPM, method = "pearson"),
                    cor(sample_weight, weights_output$RLE_IQR_logCPM, method = "spearman"),
                    cor(sample_weight, weights_output$effective_library_size, method = "pearson"),
                    cor(sample_weight, weights_output$effective_library_size, method = "spearman")
                ),
                n = 574L, stringsAsFactors = FALSE
            )
        )
        write.csv(
            weights_output, file.path(output_dir, "S5_sample_quality_weights.csv"),
            row.names = FALSE, na = ""
        )
        write.csv(
            weight_summary, file.path(output_dir, "S5_sample_weight_summary.csv"),
            row.names = FALSE, na = ""
        )
        png(
            file.path(figure_dir, "S5_sample_quality_weights.png"),
            width = 1200, height = 900, res = 150
        )
        boxplot(
            sample_weight ~ model_samples$group,
            col = c("steelblue3", "firebrick3"), outline = FALSE,
            xlab = "Biological group", ylab = "Empirical sample-quality weight",
            main = "S5 sample-quality weights by group"
        )
        stripchart(
            sample_weight ~ model_samples$group,
            vertical = TRUE, method = "jitter", pch = 16,
            col = grDevices::adjustcolor("black", alpha.f = 0.35),
            add = TRUE
        )
        abline(h = 1, lty = 2)
        grDevices::dev.off()
    }
    update_runtime(model_time)
    writeLines(
        capture.output(sessionInfo()), file.path(output_dir, "session_info.txt"),
        useBytes = TRUE
    )
    message(
        model, " checkpoint complete: ", nrow(result), " genes; ",
        nrow(design), " observations; rank ", qr(design)$rank
    )
    invisible(gc())
}

for (model in requested_models) {
    fit_sensitivity(model)
}

expected_result_files <- file.path(result_dir, paste0(all_models, "_de_results.csv"))
if (!all(file.exists(expected_result_files))) {
    missing_models <- all_models[!file.exists(expected_result_files)]
    message(
        "Requested model checkpoint(s) complete. Full cross-model outputs await: ",
        paste(missing_models, collapse = ", ")
    )
    quit(save = "no", status = 0L)
}

comparison_start <- proc.time()
sensitivity_results <- setNames(lapply(all_models, function(model) {
    result <- read.csv(
        file.path(result_dir, paste0(model, "_de_results.csv")),
        stringsAsFactors = FALSE, check.names = FALSE
    )
    if (nrow(result) != 29606L ||
        !all(required_primary_columns %in% names(result)) ||
        anyDuplicated(result$EnsemblID) ||
        !setequal(result$EnsemblID, primary_results$EnsemblID)) {
        stop("Checkpoint result failed validation: ", model)
    }
    result
}), all_models)

comparison_rows <- list()
top_overlap_rows <- list()
fdr_overlap_rows <- list()
dependent_rows <- list()
delta_matrix <- matrix(
    NA_real_, nrow = nrow(primary_results), ncol = length(all_models),
    dimnames = list(primary_results$EnsemblID, all_models)
)
logfc_matrix <- cbind(S0 = primary_results$logFC)

for (model in all_models) {
    sensitivity <- sensitivity_results[[model]]
    index <- match(primary_results$EnsemblID, sensitivity$EnsemblID)
    if (anyNA(index)) stop("Could not join ", model, " to S0 by EnsemblID.")
    sensitivity_by_primary <- sensitivity[index, , drop = FALSE]
    logfc_matrix <- cbind(logfc_matrix, sensitivity_by_primary$logFC)
    colnames(logfc_matrix)[ncol(logfc_matrix)] <- model
    delta <- sensitivity_by_primary$logFC - primary_results$logFC
    delta_matrix[, model] <- delta
    comparison_rows[[model]] <- data.frame(
        model = model,
        pearson_logFC = cor(
            sensitivity_by_primary$logFC, primary_results$logFC, method = "pearson"
        ),
        spearman_logFC = cor(
            sensitivity_by_primary$logFC, primary_results$logFC, method = "spearman"
        ),
        sign_concordance = mean(
            sign(sensitivity_by_primary$logFC) == sign(primary_results$logFC)
        ),
        genes_compared = 29606L,
        delta_logFC_median = median(delta),
        delta_logFC_median_absolute = median(abs(delta)),
        delta_logFC_maximum_absolute = max(abs(delta)),
        stringsAsFactors = FALSE
    )
    for (n_top in c(100L, 500L)) {
        primary_top <- head(primary_results$EnsemblID, n_top)
        sensitivity_top <- head(sensitivity$EnsemblID, n_top)
        intersection <- length(intersect(primary_top, sensitivity_top))
        union <- length(union(primary_top, sensitivity_top))
        top_overlap_rows[[paste(model, n_top)]] <- data.frame(
            model = model, top_n = n_top,
            intersection = intersection, union = union,
            jaccard = intersection / union,
            ranking = "topTable sort.by=P",
            stringsAsFactors = FALSE
        )
    }
    primary_sig <- primary_results$adj.P.Val < 0.05
    sensitivity_sig <- sensitivity_by_primary$adj.P.Val < 0.05
    intersection_sig <- primary_sig & sensitivity_sig
    union_sig <- primary_sig | sensitivity_sig
    primary_up <- primary_sig & primary_results$logFC > 0
    primary_down <- primary_sig & primary_results$logFC < 0
    sensitivity_up <- sensitivity_sig & sensitivity_by_primary$logFC > 0
    sensitivity_down <- sensitivity_sig & sensitivity_by_primary$logFC < 0
    fdr_overlap_rows[[model]] <- data.frame(
        model = model,
        S0_significant = sum(primary_sig),
        sensitivity_significant = sum(sensitivity_sig),
        intersection = sum(intersection_sig),
        union = sum(union_sig),
        jaccard = sum(intersection_sig) / sum(union_sig),
        S0_only = sum(primary_sig & !sensitivity_sig),
        sensitivity_only = sum(sensitivity_sig & !primary_sig),
        S0_Up = sum(primary_up),
        sensitivity_Up = sum(sensitivity_up),
        Up_intersection = sum(primary_up & sensitivity_up),
        S0_Down = sum(primary_down),
        sensitivity_Down = sum(sensitivity_down),
        Down_intersection = sum(primary_down & sensitivity_down),
        stringsAsFactors = FALSE
    )
    largest <- head(order(abs(delta), decreasing = TRUE), 50L)
    dependent_rows[[model]] <- data.frame(
        model = model,
        EnsemblID = primary_results$EnsemblID[largest],
        Symbol = primary_results$Symbol[largest],
        gene_type = primary_results$gene_type[largest],
        logFC_primary = primary_results$logFC[largest],
        logFC_sensitivity = sensitivity_by_primary$logFC[largest],
        delta_logFC = delta[largest],
        abs_delta_logFC = abs(delta[largest]),
        FDR_primary = primary_results$adj.P.Val[largest],
        FDR_sensitivity = sensitivity_by_primary$adj.P.Val[largest],
        P_primary = primary_results$P.Value[largest],
        P_sensitivity = sensitivity_by_primary$P.Value[largest],
        stringsAsFactors = FALSE
    )
    png(
        file.path(figure_dir, paste0(model, "_logfc_vs_primary.png")),
        width = 1000, height = 1000, res = 150
    )
    plot(
        primary_results$logFC, sensitivity_by_primary$logFC,
        pch = 16, cex = 0.25,
        col = grDevices::adjustcolor("black", alpha.f = 0.25),
        xlab = "S0 primary Tumor - Normal logFC",
        ylab = paste0(model, " Tumor - Normal logFC"),
        main = paste0(model, " effect sizes versus committed S0")
    )
    abline(a = 0, b = 1, col = "firebrick", lty = 2, lwd = 2)
    legend(
        "topleft",
        legend = paste0(
            "Pearson r = ",
            format_number(comparison_rows[[model]]$pearson_logFC, 5)
        ),
        bty = "n"
    )
    grDevices::dev.off()
}

comparison_metrics <- do.call(rbind, comparison_rows)
top_overlap_summary <- do.call(rbind, top_overlap_rows)
fdr_overlap_summary <- do.call(rbind, fdr_overlap_rows)
model_dependent_genes <- do.call(rbind, dependent_rows)
write.csv(
    comparison_metrics, file.path(output_dir, "comparison_metrics.csv"),
    row.names = FALSE, na = ""
)
write.csv(
    top_overlap_summary, file.path(output_dir, "top_overlap_summary.csv"),
    row.names = FALSE, na = ""
)
write.csv(
    fdr_overlap_summary, file.path(output_dir, "fdr_overlap_summary.csv"),
    row.names = FALSE, na = ""
)
write.csv(
    model_dependent_genes, file.path(output_dir, "model_dependent_genes.csv"),
    row.names = FALSE, na = ""
)

correlation_matrix <- cor(logfc_matrix, method = "pearson")
png(
    file.path(figure_dir, "logfc_correlation_heatmap.png"),
    width = 1100, height = 1000, res = 150
)
image(
    seq_len(ncol(correlation_matrix)), seq_len(nrow(correlation_matrix)),
    t(correlation_matrix[nrow(correlation_matrix):1, , drop = FALSE]),
    col = grDevices::colorRampPalette(c("white", "steelblue4"))(100),
    zlim = c(min(correlation_matrix), 1), axes = FALSE,
    xlab = "", ylab = "", main = "All-gene Pearson logFC correlation"
)
axis(1, at = seq_len(ncol(correlation_matrix)), labels = colnames(correlation_matrix))
axis(
    2, at = seq_len(nrow(correlation_matrix)),
    labels = rev(rownames(correlation_matrix)), las = 1
)
for (i in seq_len(nrow(correlation_matrix))) {
    for (j in seq_len(ncol(correlation_matrix))) {
        text(j, nrow(correlation_matrix) - i + 1L,
             labels = sprintf("%.3f", correlation_matrix[i, j]), cex = 0.7)
    }
}
box()
grDevices::dev.off()

png(
    file.path(figure_dir, "delta_logfc_by_sensitivity.png"),
    width = 1200, height = 900, res = 150
)
boxplot(
    delta_matrix, col = "grey80", outline = TRUE, pch = 16, cex = 0.25,
    xlab = "Sensitivity", ylab = "logFC sensitivity - logFC primary",
    main = "Effect-size changes relative to committed S0"
)
abline(h = 0, lty = 2, col = "firebrick")
grDevices::dev.off()

all_thresholds <- read.csv(threshold_file, stringsAsFactors = FALSE)
fdr_counts <- all_thresholds[all_thresholds$criterion == "BH FDR < 0.05", ]
fdr_counts <- fdr_counts[match(c("S0", all_models), fdr_counts$model), ]
count_matrix <- rbind(Up = fdr_counts$Up, Down = fdr_counts$Down)
png(
    file.path(figure_dir, "de_counts_by_model.png"),
    width = 1200, height = 900, res = 150
)
barplot(
    count_matrix, names.arg = fdr_counts$model, beside = FALSE,
    col = c("firebrick3", "steelblue3"),
    xlab = "Model", ylab = "Genes at BH FDR < 0.05",
    main = "Descriptive DE counts by model",
    legend.text = c("Up in Tumor", "Down in Tumor"),
    args.legend = list(x = "topright", bty = "n")
)
grDevices::dev.off()

model_diagnostics <- read.csv(
    file.path(output_dir, "model_diagnostics.csv"), stringsAsFactors = FALSE,
    check.names = FALSE
)
condition_diagnostics <- read.csv(
    file.path(output_dir, "design_condition_diagnostics.csv"),
    stringsAsFactors = FALSE
)
if (!setequal(model_diagnostics$model, all_models) ||
    !setequal(condition_diagnostics$model, all_models)) {
    stop("Combined model diagnostics do not contain exactly S1-S6.")
}
for (model in all_models) {
    row <- model_diagnostics[model_diagnostics$model == model, , drop = FALSE]
    definition <- model_definitions[[model]]
    expected_observations <- if (model == "S6") 116L else 574L
    expected_columns <- switch(
        model, S1 = 21L, S2 = 2L, S3 = 34L,
        S4 = 53L, S5 = 21L, S6 = 59L
    )
    expected_block <- if (definition$block) "case_id" else "NULL"
    if (nrow(row) != 1L || row$formula != definition$formula ||
        row$observations != expected_observations ||
        row$tested_genes != 29606L || row$design_columns != expected_columns ||
        row$design_rank != expected_columns ||
        row$contrast != "Tumor_vs_Normal = Tumor - Normal" ||
        row$positive_logFC != "higher expression in Tumor" ||
        row$block != expected_block ||
        as.logical(row$sample.weights) != definition$sample_weights ||
        as.logical(row$case_id_fixed_effect) != (model == "S6")) {
        stop("Recovered checkpoint model definition failed validation: ", model)
    }
}

update_runtime(elapsed_row(
    "combined_comparison_output_generation", comparison_start,
    "S0 joins, metrics, summary tables, and figures"
))
if (length(requested_models) == 0L) {
    component_runtime <- read.csv(runtime_file, stringsAsFactors = FALSE)
    required_components <- c(
        "frozen_DGE_reconstruction", execution_order,
        "combined_comparison_output_generation"
    )
    component_runtime <- component_runtime[
        match(required_components, component_runtime$metric), , drop = FALSE
    ]
    if (anyNA(component_runtime$metric)) {
        stop("Comparison-only recovery cannot total incomplete runtime checkpoints.")
    }
    update_runtime(data.frame(
        metric = "total_Task_007_execution",
        elapsed_seconds = sum(component_runtime$elapsed_seconds),
        user_seconds = sum(component_runtime$user_seconds),
        system_seconds = sum(component_runtime$system_seconds),
        detail = paste(
            "Sum of recorded required components across checkpoint/recovery executions;",
            "excludes the stopped pre-fit S6 attempt and orchestration gaps"
        ),
        recorded_utc = format(Sys.time(), tz = "UTC"),
        stringsAsFactors = FALSE
    ))
} else {
    update_runtime(elapsed_row(
        "total_Task_007_execution", task_start,
        paste0("Requested models: ", paste(requested_models, collapse = ","))
    ))
}
runtime_lines <- read.csv(runtime_file, stringsAsFactors = FALSE)
model_line <- function(model) {
    diagnostic <- model_diagnostics[model_diagnostics$model == model, ]
    comparison <- comparison_metrics[comparison_metrics$model == model, ]
    condition <- condition_diagnostics[condition_diagnostics$model == model, ]
    paste0(
        "- **", model, " — ", diagnostic$label, ":** formula `",
        diagnostic$formula, "`; block `", diagnostic$block,
        "`; sample.weights `", diagnostic$sample.weights, "`; design ",
        diagnostic$observations, " × ", diagnostic$design_columns,
        ", rank ", diagnostic$design_rank,
        ", nominal residual df ", diagnostic$nominal_residual_df,
        ", genes below nominal residual df ",
        diagnostic$genes_below_nominal_residual_df,
        ", normalized condition number ",
        format_number(condition$normalized_condition_number, 6),
        ", block correlation ",
        ifelse(is.na(diagnostic$consensus_correlation), "not applicable",
               format_number(diagnostic$consensus_correlation, 7)),
        ", Pearson/Spearman logFC correlation with S0 ",
        format_number(comparison$pearson_logFC, 6), "/",
        format_number(comparison$spearman_logFC, 6),
        ", sign concordance ",
        format_number(comparison$sign_concordance, 6), "."
    )
}
top_dependent_line <- function(model) {
    rows <- model_dependent_genes[model_dependent_genes$model == model, ]
    rows <- head(rows, 5L)
    labels <- ifelse(is_missing(rows$Symbol), rows$EnsemblID, rows$Symbol)
    paste0(
        "- **", model, ":** ",
        paste0(labels, " (Δ=", format_number(rows$delta_logFC, 5), ")", collapse = "; ")
    )
}
s5_weight_summary <- read.csv(
    file.path(output_dir, "S5_sample_weight_summary.csv"),
    stringsAsFactors = FALSE
)
s5_all <- s5_weight_summary[
    s5_weight_summary$category == "distribution" &
        s5_weight_summary$group_or_metric == "All", ]
s5_stat <- function(statistic) s5_all$value[s5_all$statistic == statistic]
s5_value <- function(category, group_or_metric, statistic) {
    row <- s5_weight_summary[
        s5_weight_summary$category == category &
            s5_weight_summary$group_or_metric == group_or_metric &
            s5_weight_summary$statistic == statistic, , drop = FALSE
    ]
    if (nrow(row) != 1L) stop("S5 summary lookup failed.")
    row$value
}
summary_lines <- c(
    "# Prespecified DE sensitivity-analysis summary",
    "",
    paste0("Generated: ", format(Sys.time(), tz = "UTC"), " UTC"),
    "",
    "## Frozen reference and reconstruction",
    "",
    paste(
        "The committed Task #006 primary result was used as S0 and was not refitted.",
        "The frozen 29,606 × 574 DGEList was reconstructed once from exact cached",
        "TCGA-LUAD/gencode_v26 files. The Task #005 gene mask and TMM factors",
        "matched their committed references."
    ),
    "",
    paste(
        "Every sensitivity used the explicit `Tumor - Normal` contrast; positive",
        "logFC means higher expression in Tumor. `batch_number`, where present,",
        "is `tcga.cgc_case_batch_number`: TCGA/BCR case-batch structure, not a",
        "proven RNA-seq sequencing batch."
    ),
    "",
    "## Exact model results",
    "",
    vapply(execution_order, model_line, character(1)),
    "",
    paste(
        "Singular values and column-L2-normalized condition numbers are descriptive",
        "diagnostics only; no arbitrary pass/fail threshold was applied."
    ),
    "",
    "## Top-gene and FDR overlap",
    "",
    vapply(all_models, function(model) {
        top100 <- top_overlap_summary[
            top_overlap_summary$model == model & top_overlap_summary$top_n == 100L, ]
        top500 <- top_overlap_summary[
            top_overlap_summary$model == model & top_overlap_summary$top_n == 500L, ]
        fdr <- fdr_overlap_summary[fdr_overlap_summary$model == model, ]
        paste0(
            "- **", model, ":** top-100/top-500 intersections ",
            top100$intersection, "/", top500$intersection,
            "; BH FDR < 0.05 intersection ", fdr$intersection,
            " and Jaccard ", format_number(fdr$jaccard, 6), "."
        )
    }, character(1)),
    "",
    "## Largest model-dependent genes",
    "",
    vapply(all_models, top_dependent_line, character(1)),
    "",
    paste(
        "These genes are ranked only by absolute `delta_logFC`; the list does not",
        "rank model quality or select therapeutic targets."
    ),
    "",
    "## S5 sample-quality weights",
    "",
    paste0(
        "S5 weights ranged from ", format_number(s5_stat("min"), 7), " to ",
        format_number(s5_stat("max"), 7), ", with median ",
        format_number(s5_stat("median"), 7), ". No sample was removed."
    ),
    "",
    paste0(
        "The descriptive median weight was ",
        format_number(s5_value("distribution", "Normal", "median"), 7),
        " for Normal and ",
        format_number(s5_value("distribution", "Tumor", "median"), 7),
        " for Tumor. The Pearson/Spearman associations with RLE IQR were ",
        format_number(s5_value("association", "RLE_IQR_logCPM", "Pearson"), 7),
        "/",
        format_number(s5_value("association", "RLE_IQR_logCPM", "Spearman"), 7),
        "; associations with effective library size were ",
        format_number(s5_value(
            "association", "effective_library_size", "Pearson"
        ), 7),
        "/",
        format_number(s5_value(
            "association", "effective_library_size", "Spearman"
        ), 7),
        ". These diagnostics did not trigger sample exclusion or model selection."
    ),
    "",
    "## S6 matched-pairs-only analysis",
    "",
    paste(
        "S6 used exactly 58 matched cases (116 observations), retained all 29,606",
        "frozen genes, recalculated library sizes and TMM factors after sample",
        "subsetting, and used case_id fixed effects without blocking. Reduced",
        "statistical significance is expected from the reduction from 574 to 116",
        "observations and is not by itself evidence of effect-size instability."
    ),
    "",
    "## Runtime",
    "",
    vapply(seq_len(nrow(runtime_lines)), function(i) {
        paste0(
            "- ", runtime_lines$metric[i], ": ",
            format_number(runtime_lines$elapsed_seconds[i], 7), " elapsed seconds."
        )
    }, character(1)),
    "",
    "## Interpretation boundary",
    "",
    paste(
        "The six prespecified sensitivities are robustness diagnostics. No model",
        "replaces the committed primary result based on DE counts. Task #007 did",
        "not run a seventh model, TREAT, enrichment, target selection, candidate",
        "ranking, druggability analysis, batch correction, or causal inference."
    ),
    ""
)
writeLines(
    summary_lines, file.path(output_dir, "sensitivity_summary.md"), useBytes = TRUE
)
writeLines(
    capture.output(sessionInfo()), file.path(output_dir, "session_info.txt"),
    useBytes = TRUE
)

message("Task #007 sensitivity analyses complete: ", output_dir)
