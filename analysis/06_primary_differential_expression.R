#!/usr/bin/env Rscript

# Task #006: primary TCGA-LUAD differential-expression analysis.
#
# Frozen analysis:
#   design = ~ 0 + group + batch_number
#   contrast = Tumor - Normal
#   block = case_id
#   sample.weights = FALSE
#
# The script reconstructs Task #005 exactly, fits one primary model, and does
# not run any sensitivity analysis, TREAT analysis, enrichment, candidate
# selection, or druggability scoring. It does not save a count matrix,
# normalized matrix, DGEList, EList, or RSE to the repository.

required_packages <- c(
    "recount3", "SummarizedExperiment", "edgeR", "limma", "statmod"
)
missing_packages <- required_packages[
    !vapply(required_packages, requireNamespace, logical(1), quietly = TRUE)
]
if (length(missing_packages) > 0L) {
    stop(
        "Missing required package(s): ", paste(missing_packages, collapse = ", "),
        ". Task #006 forbids package installation or updates."
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

output_dir <- file.path(repository_root, "outputs", "differential_expression")
figure_dir <- file.path(output_dir, "figures")
dir.create(figure_dir, recursive = TRUE, showWarnings = FALSE)

task2_project_file <- file.path(
    repository_root, "outputs", "reconnaissance", "project_record.csv"
)
final_ledger_file <- file.path(
    repository_root, "outputs", "final_sample_qc", "final_cohort_ledger.csv"
)
gene_filter_file <- file.path(
    repository_root, "outputs", "final_sample_qc", "gene_filter_status.csv"
)
task5_metrics_file <- file.path(
    repository_root, "outputs", "final_sample_qc", "sample_qc_metrics.csv"
)
task5_design_file <- file.path(
    repository_root, "outputs", "final_sample_qc", "design_diagnostics.csv"
)
task5_summary_file <- file.path(
    repository_root, "outputs", "final_sample_qc", "final_sample_qc_summary.md"
)
required_input_files <- c(
    task2_project_file, final_ledger_file, gene_filter_file,
    task5_metrics_file, task5_design_file, task5_summary_file
)
missing_input_files <- required_input_files[!file.exists(required_input_files)]
if (length(missing_input_files) > 0L) {
    stop(
        "Frozen Task #005 input file(s) missing: ",
        paste(missing_input_files, collapse = ", ")
    )
}

is_missing <- function(x) {
    is.na(x) | trimws(as.character(x)) == ""
}
format_number <- function(x, digits = 5L) {
    format(x, digits = digits, big.mark = ",", scientific = FALSE, trim = TRUE)
}

task2_project <- read.csv(task2_project_file, stringsAsFactors = FALSE)
final_ledger <- read.csv(final_ledger_file, stringsAsFactors = FALSE)
stored_gene_filter <- read.csv(gene_filter_file, stringsAsFactors = FALSE)
task5_metrics <- read.csv(task5_metrics_file, stringsAsFactors = FALSE)
task5_design <- read.csv(task5_design_file, stringsAsFactors = FALSE)

if (nrow(task2_project) != 1L) {
    stop("Task #002 project record must contain exactly one row.")
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

required_ledger_fields <- c(
    "final_observation_index", "tcga_sample_barcode", "sample_id",
    "sample_submitter_id", "case_id", "case_submitter_id", "sample_type",
    "group", "batch_number", "tissue_source_site",
    "tissue_source_site_code", "aliquot_barcode",
    "n_expression_records_aggregated", "source_expression_record_names",
    "technical_resolution"
)
missing_ledger_fields <- setdiff(required_ledger_fields, names(final_ledger))
if (length(missing_ledger_fields) > 0L) {
    stop(
        "Final cohort ledger is missing: ",
        paste(missing_ledger_fields, collapse = ", ")
    )
}
if (nrow(final_ledger) != 574L ||
    !identical(final_ledger$final_observation_index, seq_len(574L)) ||
    anyDuplicated(final_ledger$tcga_sample_barcode) ||
    any(is_missing(final_ledger$tcga_sample_barcode))) {
    stop("Frozen final cohort ledger identity/order checks failed.")
}
if (sum(final_ledger$sample_type == "Primary Tumor") != 515L ||
    sum(final_ledger$sample_type == "Solid Tissue Normal") != 59L ||
    length(unique(final_ledger$case_id)) != 516L) {
    stop("Frozen final cohort dimensions differ from Task #005.")
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
    stop("Frozen TCGA-38-4625 technical resolution is not reproduced.")
}

required_filter_fields <- c(
    "EnsemblID", "Symbol", "gene_type", "keep_by_filterByExpr"
)
if (length(setdiff(required_filter_fields, names(stored_gene_filter))) > 0L ||
    nrow(stored_gene_filter) != 63856L ||
    sum(as.logical(stored_gene_filter$keep_by_filterByExpr)) != 29606L) {
    stop("Frozen Task #005 gene-filter table failed identity checks.")
}
required_task5_metric_fields <- c(
    "tcga_sample_barcode", "tmm_normalization_factor"
)
if (length(setdiff(required_task5_metric_fields, names(task5_metrics))) > 0L ||
    nrow(task5_metrics) != 574L ||
    !identical(
        task5_metrics$tcga_sample_barcode,
        final_ledger$tcga_sample_barcode
    )) {
    stop("Task #005 sample-QC metrics do not match the frozen manifest order.")
}

# Build a symlink-only local recount3 release mirror from exact cached files.
# recount3 checks URL availability before consulting BiocFileCache, so this
# keeps Task #006 offline without copying or replacing any data.
remote_recount3_root <-
    "https://recount-opendata.s3.amazonaws.com/recount3/release"
cache_dir <- Sys.getenv(
    "RECOUNT3_CACHE_DIR",
    unset = "/private/tmp/luad-recount3-cache"
)
if (!dir.exists(cache_dir)) {
    stop(
        "The existing recount3 cache is unavailable at ", cache_dir,
        ". Task #006 will not download data without explicit approval."
    )
}
bfc <- recount3_cache(cache_dir)
cache_info <- as.data.frame(BiocFileCache::bfcinfo(bfc))
offline_recount3_root <- file.path(
    "/private/tmp", "luad-task006-recount3-offline-release"
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
    if (length(matches) != 1L) {
        stop(
            "Expected one exact cached recount3 resource for ", remote_url,
            "; found ", length(matches), ". No download was attempted."
        )
    }
    cached_path <- cache_info$rpath[matches]
    if (!file.exists(cached_path)) {
        stop("Cached recount3 resource is missing on disk: ", cached_path)
    }
    mirror_path <- file.path(offline_recount3_root, relative_path)
    dir.create(dirname(mirror_path), recursive = TRUE, showWarnings = FALSE)
    if (file.exists(mirror_path)) {
        if (!identical(normalizePath(mirror_path), normalizePath(cached_path))) {
            stop(
                "Existing offline-mirror entry does not resolve to the exact ",
                "cached resource: ", mirror_path
            )
        }
    } else if (!file.symlink(cached_path, mirror_path)) {
        stop("Could not create temporary cached-resource symlink: ", mirror_path)
    }
}

supported_human_annotations <- annotation_options("human")
if (!"gencode_v26" %in% supported_human_annotations) {
    stop("Required annotation 'gencode_v26' is unavailable.")
}
projects <- available_projects(
    organism = "human",
    recount3_url = offline_recount3_root,
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
    stop("Expected exactly one cached TCGA-LUAD recount3 project record.")
}
rse <- create_rse(
    project_info = project_record,
    type = "gene",
    annotation = "gencode_v26",
    bfc = bfc,
    recount3_url = offline_recount3_root
)
if (!inherits(rse, "RangedSummarizedExperiment") ||
    !identical(metadata(rse)$project, "LUAD") ||
    !identical(metadata(rse)$project_home, "data_sources/tcga") ||
    !identical(metadata(rse)$annotation, "gencode_v26") ||
    !identical(assayNames(rse), "raw_counts")) {
    stop("Reconstructed object failed pinned TCGA-LUAD/gencode_v26 checks.")
}
expected_rse_dimensions <- c(
    as.integer(task2_project$n_features_loaded),
    as.integer(task2_project$n_samples_loaded)
)
if (!identical(as.integer(dim(rse)), expected_rse_dimensions)) {
    stop("Reconstructed RSE dimensions differ from Task #002.")
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
missing_current_fields <- setdiff(verified_fields, names(sample_metadata))
if (length(missing_current_fields) > 0L) {
    stop(
        "Required current colData field(s) missing: ",
        paste(missing_current_fields, collapse = ", ")
    )
}
value_for <- function(role) sample_metadata[[verified_fields[[role]]]]

source_records_by_observation <- strsplit(
    final_ledger$source_expression_record_names,
    ";",
    fixed = TRUE
)
source_record_counts <- lengths(source_records_by_observation)
if (!identical(source_record_counts, final_ledger$n_expression_records_aggregated) ||
    sum(source_record_counts) != 575L) {
    stop("Frozen manifest source-record multiplicities are inconsistent.")
}
source_record_names <- unlist(source_records_by_observation, use.names = FALSE)
if (anyDuplicated(source_record_names)) {
    stop("A source expression record appears in multiple final observations.")
}
source_indices <- match(source_record_names, colnames(rse))
if (anyNA(source_indices)) {
    stop("At least one frozen source expression record is absent from recount3.")
}
manifest_row_for_source <- rep(
    seq_len(nrow(final_ledger)), source_record_counts
)

assert_source_field <- function(role, manifest_field) {
    current <- as.character(value_for(role)[source_indices])
    frozen <- as.character(final_ledger[[manifest_field]][manifest_row_for_source])
    if (!identical(current, frozen)) {
        mismatch <- which(current != frozen | xor(is.na(current), is.na(frozen)))
        stop(
            "Current colData `", verified_fields[[role]],
            "` differs from frozen ledger field `", manifest_field,
            "` for ", length(mismatch), " source record(s)."
        )
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
    selected_rse,
    round = TRUE,
    avg_mapped_read_length = verified_fields[["average_mapped_length"]]
)
if (!identical(dim(record_counts), c(nrow(rse), 575L)) ||
    anyNA(record_counts) || any(!is.finite(record_counts)) ||
    any(record_counts < 0)) {
    stop("Frozen-source compute_read_counts() returned invalid values.")
}

aggregation_ids <- final_ledger$tcga_sample_barcode[manifest_row_for_source]
sample_level_counts <- sumTechReps(record_counts, ID = aggregation_ids)
if (!identical(
    colnames(sample_level_counts), final_ledger$tcga_sample_barcode
) || ncol(sample_level_counts) != 574L) {
    stop("Final observation order differs from the frozen cohort ledger.")
}
expected_libraries <- as.numeric(tapply(
    colSums(record_counts),
    factor(aggregation_ids, levels = final_ledger$tcga_sample_barcode),
    sum
))
if (!isTRUE(all.equal(
    unname(colSums(sample_level_counts)), expected_libraries, tolerance = 0
))) {
    stop("Frozen technical aggregation did not preserve read counts.")
}

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
    anyDuplicated(gene_annotation$EnsemblID) ||
    !identical(gene_annotation$EnsemblID, stored_gene_filter$EnsemblID) ||
    !identical(gene_annotation$Symbol, stored_gene_filter$Symbol) ||
    !identical(gene_annotation$gene_type, stored_gene_filter$gene_type)) {
    stop("Reconstructed gene annotation differs from Task #005.")
}
rownames(sample_level_counts) <- gene_annotation$EnsemblID
rownames(gene_annotation) <- gene_annotation$EnsemblID

sample_data <- final_ledger
sample_data$group <- factor(
    ifelse(
        sample_data$sample_type == "Primary Tumor", "Tumor",
        ifelse(
            sample_data$sample_type == "Solid Tissue Normal", "Normal", NA
        )
    ),
    levels = c("Normal", "Tumor")
)
if (anyNA(sample_data$group) ||
    !identical(as.integer(table(sample_data$group)), c(59L, 515L))) {
    stop("Frozen Tumor/Normal group construction failed.")
}
sample_data$batch_number <- factor(as.character(sample_data$batch_number))
sample_data$case_id <- as.character(sample_data$case_id)
rownames(sample_data) <- sample_data$tcga_sample_barcode

dge_unfiltered <- DGEList(
    counts = sample_level_counts,
    samples = sample_data,
    group = sample_data$group,
    genes = gene_annotation
)
recomputed_keep <- filterByExpr(
    dge_unfiltered, group = dge_unfiltered$samples$group
)
stored_keep <- as.logical(stored_gene_filter$keep_by_filterByExpr)
if (!identical(unname(recomputed_keep), unname(stored_keep))) {
    stop(
        "Recomputed filterByExpr() mask differs from frozen Task #005 mask for ",
        sum(recomputed_keep != stored_keep), " genes."
    )
}

dge <- dge_unfiltered[stored_keep, , keep.lib.sizes = FALSE]
dge <- normLibSizes(dge, method = "TMM")
if (nrow(dge) != 29606L || ncol(dge) != 574L) {
    stop("Frozen filtered DGEList dimensions are not 29,606 x 574.")
}
tmm_tolerance <- 1e-12
tmm_difference <- abs(
    dge$samples$norm.factors - task5_metrics$tmm_normalization_factor
)
max_tmm_difference <- max(tmm_difference)
if (!is.finite(max_tmm_difference) || max_tmm_difference > tmm_tolerance) {
    stop(
        "Recomputed TMM factors differ from Task #005; maximum absolute ",
        "difference = ", format(max_tmm_difference, scientific = TRUE),
        ", tolerance = ", format(tmm_tolerance, scientific = TRUE), "."
    )
}

group <- factor(dge$samples$group, levels = c("Normal", "Tumor"))
batch_number <- factor(as.character(dge$samples$batch_number))
case_id <- as.character(dge$samples$case_id)
design <- model.matrix(~ 0 + group + batch_number)
colnames(design)[colnames(design) == "groupNormal"] <- "Normal"
colnames(design)[colnames(design) == "groupTumor"] <- "Tumor"
rownames(design) <- dge$samples$tcga_sample_barcode
if (!all(c("Normal", "Tumor") %in% colnames(design)) ||
    any(grepl("case_id", colnames(design), fixed = TRUE))) {
    stop("Primary design coefficients are not the frozen explicit group design.")
}
design_rank <- qr(design)$rank
if (design_rank != ncol(design)) {
    stop("Primary design matrix is not full rank.")
}
contrast_matrix <- limma::makeContrasts(
    Tumor_vs_Normal = Tumor - Normal,
    levels = design
)
expected_contrast <- numeric(ncol(design))
names(expected_contrast) <- colnames(design)
expected_contrast["Tumor"] <- 1
expected_contrast["Normal"] <- -1
if (!identical(
    as.numeric(contrast_matrix[, "Tumor_vs_Normal"]),
    as.numeric(expected_contrast)
)) {
    stop("Primary contrast is not exactly Tumor - Normal.")
}

case_group_table <- table(case_id, group)
n_unique_cases <- nrow(case_group_table)
n_matched_cases <- sum(
    case_group_table[, "Normal"] == 1L & case_group_table[, "Tumor"] == 1L
)
if (n_unique_cases != 516L || n_matched_cases != 58L ||
    any(case_group_table > 1L)) {
    stop("Frozen case pairing structure failed primary-model checks.")
}
batch_group_table <- table(batch_number, group)
n_batch_levels <- nrow(batch_group_table)
n_batch_both_groups <- sum(
    batch_group_table[, "Normal"] > 0L & batch_group_table[, "Tumor"] > 0L
)

voom_messages <- character(0)
png(
    file.path(figure_dir, "voom_mean_variance.png"),
    width = 1200, height = 900, res = 150
)
voom_fit <- withCallingHandlers(
    edgeR::voomLmFit(
        dge,
        design = design,
        block = case_id,
        sample.weights = FALSE,
        normalize.method = "none",
        plot = TRUE,
        save.plot = TRUE,
        keep.EList = TRUE
    ),
    message = function(message_condition) {
        voom_messages <<- c(voom_messages, conditionMessage(message_condition))
        invokeRestart("muffleMessage")
    }
)
dev.off()

if (is.null(voom_fit$EList) || is.null(voom_fit$voom.xy) ||
    is.null(voom_fit$voom.line) ||
    "sample.weight" %in% names(voom_fit$targets) ||
    nrow(voom_fit$EList$E) != 29606L ||
    ncol(voom_fit$EList$E) != 574L) {
    stop("voomLmFit output does not match frozen Task #006 settings.")
}

# lmFit stores the exact final correlation supplied by voomLmFit in the
# fitted object. Read it directly so the primary model is fitted only once
# and the expensive gene-wise correlation estimator is not repeated.
consensus_correlation <- voom_fit$correlation
if (length(consensus_correlation) != 1L ||
    !is.finite(consensus_correlation)) {
    stop("Final consensus intra-case correlation is not finite.")
}

contrast_fit <- limma::contrasts.fit(voom_fit, contrast_matrix)
ebayes_fit <- limma::eBayes(
    contrast_fit,
    trend = FALSE,
    robust = TRUE
)
top_table <- limma::topTable(
    ebayes_fit,
    coef = "Tumor_vs_Normal",
    number = Inf,
    adjust.method = "BH",
    sort.by = "P"
)
if (nrow(top_table) != 29606L ||
    !all(c(
        "EnsemblID", "Symbol", "gene_type", "logFC", "AveExpr", "t",
        "P.Value", "adj.P.Val", "B"
    ) %in% names(top_table)) ||
    anyDuplicated(top_table$EnsemblID)) {
    stop("Primary topTable result failed tested-gene identity checks.")
}

# Descriptive, unadjusted group means from TMM-aware log-CPM. These are not
# fixed-effect coefficients or model-adjusted group estimates.
descriptive_log_cpm <- cpm(
    dge,
    log = TRUE,
    prior.count = 2,
    normalized.lib.sizes = TRUE
)
mean_log_cpm_tumor <- rowMeans(descriptive_log_cpm[, group == "Tumor", drop = FALSE])
mean_log_cpm_normal <- rowMeans(descriptive_log_cpm[, group == "Normal", drop = FALSE])
result_match <- match(top_table$EnsemblID, rownames(dge))
if (anyNA(result_match)) {
    stop("Could not map topTable genes to descriptive group summaries.")
}
primary_de_results <- top_table[, c(
    "EnsemblID", "Symbol", "gene_type", "logFC", "AveExpr", "t",
    "P.Value", "adj.P.Val", "B"
)]
primary_de_results$mean_logCPM_Tumor <-
    mean_log_cpm_tumor[result_match]
primary_de_results$mean_logCPM_Normal <-
    mean_log_cpm_normal[result_match]
if (anyNA(primary_de_results) ||
    any(!is.finite(as.matrix(primary_de_results[, c(
        "logFC", "AveExpr", "t", "P.Value", "adj.P.Val", "B",
        "mean_logCPM_Tumor", "mean_logCPM_Normal"
    )])))) {
    stop("Primary DE result contains missing or non-finite values.")
}
top_de_genes <- head(primary_de_results, 100L)

threshold_summary_row <- function(criterion, selected) {
    selected <- as.logical(selected)
    data.frame(
        criterion = criterion,
        Up = sum(selected & primary_de_results$logFC > 0),
        Down = sum(selected & primary_de_results$logFC < 0),
        Total = sum(selected),
        direction_definition =
            "Up: logFC > 0 (higher in Tumor); Down: logFC < 0 (lower in Tumor)",
        stringsAsFactors = FALSE
    )
}
fdr05 <- primary_de_results$adj.P.Val < 0.05
fdr01 <- primary_de_results$adj.P.Val < 0.01
de_threshold_summary <- rbind(
    threshold_summary_row("BH FDR < 0.05", fdr05),
    threshold_summary_row("BH FDR < 0.01", fdr01),
    threshold_summary_row(
        "BH FDR < 0.05 and |logFC| >= 0.5",
        fdr05 & abs(primary_de_results$logFC) >= 0.5
    ),
    threshold_summary_row(
        "BH FDR < 0.05 and |logFC| >= 1",
        fdr05 & abs(primary_de_results$logFC) >= 1
    ),
    threshold_summary_row(
        "BH FDR < 0.05 and |logFC| >= 2",
        fdr05 & abs(primary_de_results$logFC) >= 2
    )
)

residual_df <- as.numeric(voom_fit$df.residual)
nominal_residual_df <- nrow(design) - design_rank
residual_df_summary <- c(
    min = min(residual_df),
    Q1 = unname(quantile(residual_df, 0.25)),
    median = median(residual_df),
    mean = mean(residual_df),
    Q3 = unname(quantile(residual_df, 0.75)),
    max = max(residual_df)
)
n_below_nominal_residual_df <- sum(residual_df < nominal_residual_df)

plot_fit_by_original_order <- primary_de_results[
    match(rownames(dge), primary_de_results$EnsemblID),
    ,
    drop = FALSE
]
if (anyNA(plot_fit_by_original_order$EnsemblID)) {
    stop("Could not restore original gene order for diagnostics.")
}

png(
    file.path(figure_dir, "residual_df_histogram.png"),
    width = 1200, height = 800, res = 150
)
hist(
    residual_df,
    breaks = 40,
    xlab = "Gene-specific residual degrees of freedom",
    main = "Primary voom fit: residual degrees of freedom",
    col = "grey80",
    border = "white"
)
abline(v = nominal_residual_df, col = "firebrick", lty = 2, lwd = 2)
dev.off()

png(
    file.path(figure_dir, "plotSA.png"),
    width = 1200, height = 900, res = 150
)
limma::plotSA(
    ebayes_fit,
    main = "Primary empirical-Bayes variance diagnostic"
)
dev.off()

png(
    file.path(figure_dir, "md_plot.png"),
    width = 1200, height = 900, res = 150
)
plot(
    primary_de_results$AveExpr,
    primary_de_results$logFC,
    pch = 16,
    cex = 0.35,
    col = ifelse(fdr05, "firebrick", "grey65"),
    xlab = "Average expression (AveExpr)",
    ylab = "Tumor - Normal log2 fold change",
    main = "Primary Tumor - Normal MD plot"
)
abline(h = 0, lty = 2)
legend(
    "topright",
    legend = c("BH FDR < 0.05", "not BH FDR < 0.05"),
    pch = 16,
    col = c("firebrick", "grey65"),
    bty = "n"
)
dev.off()

neg_log10_p <- -log10(pmax(primary_de_results$P.Value, .Machine$double.xmin))
png(
    file.path(figure_dir, "volcano_plot.png"),
    width = 1200, height = 900, res = 150
)
plot(
    primary_de_results$logFC,
    neg_log10_p,
    pch = 16,
    cex = 0.35,
    col = ifelse(fdr05, "firebrick", "grey65"),
    xlab = "Tumor - Normal log2 fold change",
    ylab = "-log10(raw P value)",
    main = "Primary DE overview volcano plot"
)
abline(v = 0, lty = 2)
legend(
    "topright",
    legend = c("BH FDR < 0.05", "not BH FDR < 0.05"),
    pch = 16,
    col = c("firebrick", "grey65"),
    bty = "n"
)
dev.off()

png(
    file.path(figure_dir, "pvalue_histogram.png"),
    width = 1200, height = 800, res = 150
)
hist(
    primary_de_results$P.Value,
    breaks = seq(0, 1, by = 0.025),
    xlab = "Raw P value",
    main = "Primary Tumor - Normal raw P values",
    col = "grey75",
    border = "white"
)
dev.off()

design_matrix_output <- data.frame(
    final_observation_index = final_ledger$final_observation_index,
    tcga_sample_barcode = final_ledger$tcga_sample_barcode,
    case_id = case_id,
    group = as.character(group),
    batch_number = as.character(batch_number),
    design,
    check.names = FALSE,
    stringsAsFactors = FALSE
)
contrast_matrix_output <- data.frame(
    coefficient = rownames(contrast_matrix),
    Tumor_vs_Normal = as.numeric(contrast_matrix[, "Tumor_vs_Normal"]),
    stringsAsFactors = FALSE
)

diagnostic_rows <- list()
add_diagnostic <- function(metric, value, detail = "") {
    diagnostic_rows[[length(diagnostic_rows) + 1L]] <<- data.frame(
        metric = metric,
        value = as.character(value),
        detail = detail,
        stringsAsFactors = FALSE
    )
}
add_diagnostic("observations", nrow(design), "Frozen biological observations")
add_diagnostic("Tumor_observations", sum(group == "Tumor"))
add_diagnostic("Normal_observations", sum(group == "Normal"))
add_diagnostic("unique_cases", n_unique_cases)
add_diagnostic("matched_cases", n_matched_cases)
add_diagnostic(
    "batch_number_source",
    verified_fields[["batch_number"]],
    "TCGA/BCR case-batch structure; not a proven RNA-seq sequencing batch"
)
add_diagnostic("case_batch_levels", n_batch_levels)
add_diagnostic("case_batch_levels_with_both_groups", n_batch_both_groups)
add_diagnostic("design_rows", nrow(design))
add_diagnostic("design_columns", ncol(design))
add_diagnostic("design_coefficients", paste(colnames(design), collapse = ";"))
add_diagnostic("design_rank", design_rank)
add_diagnostic("design_full_rank", design_rank == ncol(design))
add_diagnostic("nominal_fixed_effect_residual_df", nominal_residual_df)
add_diagnostic(
    "contrast_definition",
    "Tumor_vs_Normal = Tumor - Normal",
    "Positive logFC means higher expression in Tumor"
)
add_diagnostic(
    "contrast_vector",
    paste(
        paste0(names(expected_contrast), "=", expected_contrast),
        collapse = ";"
    )
)
add_diagnostic("blocking_variable", "case_id")
add_diagnostic("case_id_in_fixed_effect_design", FALSE)
add_diagnostic("sample.weights", FALSE)
add_diagnostic("normalize.method_in_voomLmFit", "none")
add_diagnostic(
    "consensus_intra_case_correlation",
    format_number(consensus_correlation, 7)
)
add_diagnostic("tested_genes", nrow(primary_de_results))
add_diagnostic("frozen_filter_genes", sum(stored_keep))
add_diagnostic("filter_mask_exact_match", TRUE)
add_diagnostic("TMM_absolute_tolerance", tmm_tolerance)
add_diagnostic("TMM_maximum_absolute_difference", max_tmm_difference)
add_diagnostic("residual_df_min", residual_df_summary["min"])
add_diagnostic("residual_df_Q1", residual_df_summary["Q1"])
add_diagnostic("residual_df_median", residual_df_summary["median"])
add_diagnostic("residual_df_mean", residual_df_summary["mean"])
add_diagnostic("residual_df_Q3", residual_df_summary["Q3"])
add_diagnostic("residual_df_max", residual_df_summary["max"])
add_diagnostic(
    "genes_residual_df_below_nominal_maximum",
    n_below_nominal_residual_df
)
add_diagnostic(
    "voom_messages",
    paste(trimws(voom_messages), collapse = " | "),
    "Messages emitted by the single primary voomLmFit call"
)
add_diagnostic("sensitivity_analyses_fitted", 0)
primary_model_diagnostics <- do.call(rbind, diagnostic_rows)

threshold_line <- function(criterion) {
    row <- de_threshold_summary[de_threshold_summary$criterion == criterion, ]
    paste0(
        "- ", criterion, ": ", row$Total, " total (", row$Up,
        " Up; ", row$Down, " Down)."
    )
}
summary_lines <- c(
    "# Primary TCGA-LUAD differential-expression analysis",
    "",
    paste0("Generated: ", format(Sys.time(), tz = "UTC"), " UTC"),
    "",
    "## Frozen input reconstruction",
    "",
    paste0(
        "Task #006 reconstructed the pinned TCGA-LUAD recount3 gene-level ",
        "`gencode_v26` object from exact already-cached files without a network ",
        "download. The 574-observation Task #005 manifest was reproduced exactly: ",
        "515 Primary Tumor, 59 Solid Tissue Normal, 516 unique cases, and 58 ",
        "matched tumor-normal cases. Only the frozen two-record same-aliquot ",
        "aggregation for `TCGA-38-4625-01` was applied."
    ),
    paste0(
        "The authoritative Task #005 gene mask retained ", nrow(dge), " of ",
        nrow(dge_unfiltered), " genes. An independent `filterByExpr()` assertion ",
        "matched that mask exactly. TMM factors were reconstructed with maximum ",
        "absolute difference ", format(max_tmm_difference, scientific = TRUE),
        " versus the stored Task #005 factors, within the prespecified strict ",
        "tolerance ", format(tmm_tolerance, scientific = TRUE), "."
    ),
    "",
    "## Primary model",
    "",
    "The fixed-effect design was `~ 0 + group + batch_number`.",
    "",
    paste0(
        "`batch_number` came specifically from `",
        verified_fields[["batch_number"]], "`. It is a TCGA/BCR case-batch ",
        "structure used as a prespecified nuisance adjustment. It is not described ",
        "as a proven RNA-seq sequencing, lane, library-preparation, or run batch."
    ),
    paste0(
        "The design was ", nrow(design), " × ", ncol(design), " with rank ",
        design_rank, " and nominal fixed-effect residual df ",
        nominal_residual_df, ". `case_id` was used only as the blocking variable ",
        "in `voomLmFit`; it was not a fixed effect. `sample.weights = FALSE`, while ",
        "ordinary voom observation-level precision weights remained enabled."
    ),
    paste0(
        "The estimated consensus intra-case correlation was ",
        format_number(consensus_correlation, 7), ". The explicit contrast was ",
        "`Tumor_vs_Normal = Tumor - Normal`: positive logFC means higher expression ",
        "in Tumor and negative logFC means lower expression in Tumor."
    ),
    "",
    "## Differential-expression results",
    "",
    paste0(
        "All ", nrow(primary_de_results), " frozen genes were tested for the null ",
        "hypothesis logFC(Tumor - Normal) = 0. BH FDR was used for multiple-testing ",
        "control. No fold-change cutoff was part of the primary hypothesis test."
    ),
    threshold_line("BH FDR < 0.05"),
    threshold_line("BH FDR < 0.01"),
    threshold_line("BH FDR < 0.05 and |logFC| >= 0.5"),
    threshold_line("BH FDR < 0.05 and |logFC| >= 1"),
    threshold_line("BH FDR < 0.05 and |logFC| >= 2"),
    paste(
        "`mean_logCPM_Tumor` and `mean_logCPM_Normal` are descriptive, unadjusted",
        "group means of TMM-aware log-CPM. They are not model-adjusted coefficients."
    ),
    "",
    "## Diagnostics",
    "",
    paste0(
        "Gene-specific residual df had min ",
        format_number(residual_df_summary["min"], 7), ", Q1 ",
        format_number(residual_df_summary["Q1"], 7), ", median ",
        format_number(residual_df_summary["median"], 7), ", mean ",
        format_number(residual_df_summary["mean"], 7), ", Q3 ",
        format_number(residual_df_summary["Q3"], 7), ", and max ",
        format_number(residual_df_summary["max"], 7), ". ",
        n_below_nominal_residual_df, " genes were below the nominal maximum ",
        nominal_residual_df, "."
    ),
    paste(
        "The voom mean-variance plot, empirical-Bayes plotSA diagnostic, MD plot,",
        "raw-P-value histogram, residual-df histogram, and communication-oriented",
        "volcano plot are saved under `figures/`. An excess of small raw P values",
        "is not automatically interpreted as statistical inflation in this strong",
        "Tumor-versus-Normal biological comparison."
    ),
    "",
    "## Scope boundary",
    "",
    paste(
        "Task #006 fitted exactly one primary model. None of the six prespecified",
        "Task #007 sensitivity analyses was fitted. This task did not run TREAT,",
        "pathway enrichment, target selection, candidate ranking, druggability",
        "scoring, batch correction, or expression-matrix correction."
    ),
    ""
)

write.csv(
    primary_de_results,
    file.path(output_dir, "primary_de_results.csv"),
    row.names = FALSE,
    na = ""
)
write.csv(
    top_de_genes,
    file.path(output_dir, "top_de_genes.csv"),
    row.names = FALSE,
    na = ""
)
write.csv(
    primary_model_diagnostics,
    file.path(output_dir, "primary_model_diagnostics.csv"),
    row.names = FALSE,
    na = ""
)
write.csv(
    de_threshold_summary,
    file.path(output_dir, "de_threshold_summary.csv"),
    row.names = FALSE,
    na = ""
)
write.csv(
    design_matrix_output,
    file.path(output_dir, "design_matrix.csv"),
    row.names = FALSE,
    na = ""
)
write.csv(
    contrast_matrix_output,
    file.path(output_dir, "contrast_matrix.csv"),
    row.names = FALSE,
    na = ""
)
writeLines(
    summary_lines,
    file.path(output_dir, "primary_de_summary.md"),
    useBytes = TRUE
)
writeLines(
    capture.output(sessionInfo()),
    file.path(output_dir, "session_info.txt"),
    useBytes = TRUE
)

message("Task #006 primary differential expression complete: ", output_dir)
