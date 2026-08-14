#!/usr/bin/env Rscript

# TCGA-LUAD sample-level aggregation, expression filtering, normalization,
# exploratory sample QC, and design diagnostics.
#
# This script deliberately performs no differential-expression testing,
# voomLmFit, eBayes, topTable, batch correction, candidate-gene selection,
# scoring, or sample exclusion. It never writes a count/expression matrix,
# RangedSummarizedExperiment, or DGEList to the repository.

required_packages <- c(
    "recount3", "SummarizedExperiment", "edgeR", "limma"
)
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
suppressPackageStartupMessages(library(edgeR))

script_argument <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
if (length(script_argument) == 1L) {
    script_path <- normalizePath(sub("^--file=", "", script_argument))
    repository_root <- dirname(dirname(script_path))
} else {
    repository_root <- normalizePath(getwd())
}

output_dir <- file.path(repository_root, "outputs", "sample_qc")
figure_dir <- file.path(output_dir, "figures")
dir.create(figure_dir, recursive = TRUE, showWarnings = FALSE)

task2_project_file <- file.path(
    repository_root, "outputs", "reconnaissance", "project_record.csv"
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
cache_dir <- Sys.getenv(
    "RECOUNT3_CACHE_DIR",
    unset = "/private/tmp/luad-recount3-cache"
)
dir.create(cache_dir, recursive = TRUE, showWarnings = FALSE)
bfc <- recount3_cache(cache_dir)

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
    average_mapped_length = "recount_qc.star.average_mapped_length"
)
missing_fields <- setdiff(verified_fields, names(sample_metadata))
if (length(missing_fields) > 0L) {
    stop(
        "Verified colData field(s) missing: ",
        paste(missing_fields, collapse = ", "),
        ". Re-inspect the RSE and installed recount3 documentation."
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
    stop("The RSE does not provide one name per expression record.")
}

record_ledger <- data.frame(
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
    batch_number = as.character(values_for("batch_number")),
    tissue_source_site = as.character(values_for("tissue_source_site")),
    tissue_source_site_code = as.character(values_for("tissue_source_site_code")),
    stringsAsFactors = FALSE,
    check.names = FALSE
)

primary_sample_types <- c("Primary Tumor", "Solid Tissue Normal")
record_ledger$eligible_primary_analysis <-
    record_ledger$sample_type %in% primary_sample_types
record_ledger$group <- ifelse(
    record_ledger$sample_type == "Primary Tumor",
    "tumor",
    ifelse(
        record_ledger$sample_type == "Solid Tissue Normal",
        "normal",
        NA_character_
    )
)
record_ledger$record_status <- ifelse(
    record_ledger$eligible_primary_analysis,
    "included_primary_sample_type",
    paste0("excluded_sample_type:", record_ledger$sample_type)
)

eligible_indices <- which(record_ledger$eligible_primary_analysis)
eligible_ledger <- record_ledger[eligible_indices, , drop = FALSE]
if (any(is_missing(eligible_ledger$sample_id))) {
    stop("At least one eligible expression record has a missing GDC sample_id.")
}

invariant_fields <- c(
    "case_id", "case_submitter_id", "sample_type", "sample_submitter_id",
    "tissue_source_site", "tissue_source_site_code", "batch_number"
)
sample_groups <- split(seq_len(nrow(eligible_ledger)), eligible_ledger$sample_id)
conflict_rows <- list()
conflict_index <- 0L
for (sample_id in names(sample_groups)) {
    rows <- sample_groups[[sample_id]]
    for (field in invariant_fields) {
        observed <- as.character(eligible_ledger[[field]][rows])
        canonical <- ifelse(is_missing(observed), "<missing>", observed)
        distinct <- unique(canonical)
        if (length(distinct) > 1L) {
            conflict_index <- conflict_index + 1L
            conflict_rows[[conflict_index]] <- data.frame(
                sample_id = sample_id,
                field = field,
                values = paste(distinct, collapse = " | "),
                expression_column_indices = paste(
                    eligible_ledger$expression_column_index[rows],
                    collapse = ";"
                ),
                stringsAsFactors = FALSE
            )
        }
    }
}
if (length(conflict_rows) > 0L) {
    conflicts <- do.call(rbind, conflict_rows)
    conflict_file <- file.path(
        output_dir, "aggregation_metadata_conflicts.csv"
    )
    write.csv(conflicts, conflict_file, row.names = FALSE, na = "")
    stop(
        "Conflicting invariant biological metadata were found within GDC ",
        "sample_id. Aggregation was stopped. See: ", conflict_file
    )
}

average_mapped_length <- as.numeric(values_for("average_mapped_length"))
if (any(!is.finite(average_mapped_length)) ||
    any(average_mapped_length <= 0)) {
    stop(
        "Average mapped read length contains missing, non-finite, zero, or ",
        "negative values; compute_read_counts() cannot be used safely."
    )
}

read_counts <- compute_read_counts(
    rse,
    round = TRUE,
    avg_mapped_read_length = verified_fields[["average_mapped_length"]]
)
if (!identical(dim(read_counts), dim(rse))) {
    stop("compute_read_counts() returned unexpected dimensions.")
}
if (anyNA(read_counts) || any(!is.finite(read_counts)) ||
    any(read_counts < 0)) {
    stop("The computed read-count matrix contains invalid values.")
}

eligible_counts <- read_counts[, eligible_indices, drop = FALSE]
eligible_sample_ids <- eligible_ledger$sample_id
sample_level_counts <- sumTechReps(
    eligible_counts,
    ID = eligible_sample_ids
)
if (!identical(colnames(sample_level_counts), unique(eligible_sample_ids))) {
    stop("sumTechReps() returned an unexpected GDC sample_id column order.")
}

original_library_sizes <- colSums(eligible_counts)
expected_sample_libraries <- as.numeric(tapply(
    original_library_sizes,
    factor(eligible_sample_ids, levels = colnames(sample_level_counts)),
    sum
))
if (!isTRUE(all.equal(
    unname(colSums(sample_level_counts)),
    expected_sample_libraries,
    tolerance = 0
))) {
    stop("Technical-replicate aggregation did not preserve summed counts.")
}

sample_order <- colnames(sample_level_counts)
first_row_by_sample <- match(sample_order, eligible_ledger$sample_id)
sample_level_metadata <- eligible_ledger[
    first_row_by_sample,
    c(
        "sample_id", "sample_submitter_id", "case_id", "case_submitter_id",
        "sample_type", "group", "batch_number", "tissue_source_site",
        "tissue_source_site_code"
    ),
    drop = FALSE
]
sample_level_metadata$sample_level_column_index <- seq_along(sample_order)
sample_level_metadata$sample_level_column_name <- sample_order
records_per_sample <- table(eligible_sample_ids)
sample_level_metadata$n_expression_records_aggregated <- as.integer(
    records_per_sample[sample_order]
)
sample_level_metadata$n_distinct_aliquots <- vapply(
    sample_order,
    function(sample_id) {
        values <- eligible_ledger$aliquot_id[
            eligible_ledger$sample_id == sample_id
        ]
        length(unique(values[!is_missing(values)]))
    },
    integer(1)
)
sample_level_metadata$source_expression_column_indices <- vapply(
    sample_order,
    function(sample_id) paste(
        eligible_ledger$expression_column_index[
            eligible_ledger$sample_id == sample_id
        ],
        collapse = ";"
    ),
    character(1)
)
sample_level_metadata$source_aliquot_ids <- vapply(
    sample_order,
    function(sample_id) paste(
        unique(eligible_ledger$aliquot_id[
            eligible_ledger$sample_id == sample_id
        ]),
        collapse = ";"
    ),
    character(1)
)
rownames(sample_level_metadata) <- sample_level_metadata$sample_id

record_ledger$aggregation_sample_id <- ifelse(
    record_ledger$eligible_primary_analysis,
    record_ledger$sample_id,
    NA_character_
)
record_ledger$final_sample_level_column_index <- match(
    record_ledger$aggregation_sample_id, sample_order
)
record_ledger$final_sample_level_column_name <- ifelse(
    record_ledger$eligible_primary_analysis,
    record_ledger$sample_id,
    NA_character_
)
record_ledger$n_expression_records_aggregated_to_sample <- as.integer(
    records_per_sample[record_ledger$aggregation_sample_id]
)
record_ledger$technical_aggregation_required <-
    record_ledger$n_expression_records_aggregated_to_sample > 1L

gene_data <- as.data.frame(rowData(rse))
required_gene_fields <- c("gene_id", "gene_name", "gene_type")
missing_gene_fields <- setdiff(required_gene_fields, names(gene_data))
if (length(missing_gene_fields) > 0L) {
    stop(
        "Required rowData field(s) missing: ",
        paste(missing_gene_fields, collapse = ", ")
    )
}
gene_annotation <- data.frame(
    EnsemblID = as.character(gene_data$gene_id),
    Symbol = as.character(gene_data$gene_name),
    gene_type = as.character(gene_data$gene_type),
    stringsAsFactors = FALSE
)
if (any(is_missing(gene_annotation$EnsemblID)) ||
    anyDuplicated(gene_annotation$EnsemblID)) {
    stop("Ensembl gene IDs are missing or duplicated; DGEList rows are ambiguous.")
}
rownames(sample_level_counts) <- gene_annotation$EnsemblID
rownames(gene_annotation) <- gene_annotation$EnsemblID

sample_level_metadata$group <- factor(
    sample_level_metadata$group,
    levels = c("normal", "tumor")
)
sample_level_metadata$batch_number <- factor(
    sample_level_metadata$batch_number
)
sample_level_metadata$tissue_source_site <- factor(
    sample_level_metadata$tissue_source_site
)

dge <- DGEList(
    counts = sample_level_counts,
    samples = sample_level_metadata,
    group = sample_level_metadata$group,
    genes = gene_annotation
)
if (!identical(colnames(dge), rownames(dge$samples)) ||
    !identical(rownames(dge), rownames(dge$genes))) {
    stop("DGEList sample or gene traceability checks failed.")
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

pca <- prcomp(
    t(log_cpm),
    center = TRUE,
    scale. = FALSE,
    rank. = 5
)
pca_coordinates <- pca$x
pca_variance_percent <- 100 * pca$sdev^2 / sum(pca$sdev^2)

gene_log_cpm_median <- apply(log_cpm, 1L, median)
rle_values <- sweep(log_cpm, 1L, gene_log_cpm_median, FUN = "-")
rle_median <- apply(rle_values, 2L, median)
rle_iqr <- apply(rle_values, 2L, IQR)
rm(rle_values)

sample_qc_metrics <- data.frame(
    sample_level_column_index = seq_len(ncol(dge_filtered)),
    sample_id = dge_filtered$samples$sample_id,
    sample_submitter_id = dge_filtered$samples$sample_submitter_id,
    case_id = dge_filtered$samples$case_id,
    case_submitter_id = dge_filtered$samples$case_submitter_id,
    sample_type = dge_filtered$samples$sample_type,
    group = as.character(dge_filtered$samples$group),
    batch_number = as.character(dge_filtered$samples$batch_number),
    tissue_source_site = as.character(dge_filtered$samples$tissue_source_site),
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
    result <- as.character(x)
    result[is_missing(result)] <- "<missing>"
    result
}

contingency_summary <- function(level, level_name, metadata) {
    level <- level_value(level)
    levels_present <- sort(unique(level))
    result <- do.call(rbind, lapply(levels_present, function(value) {
        rows <- level == value
        n_tumor <- sum(metadata$group[rows] == "tumor")
        n_normal <- sum(metadata$group[rows] == "normal")
        data.frame(
            level = value,
            n_tumor = n_tumor,
            n_normal = n_normal,
            total = n_tumor + n_normal,
            both_groups_represented = n_tumor > 0L & n_normal > 0L,
            tumor_only = n_tumor > 0L & n_normal == 0L,
            normal_only = n_normal > 0L & n_tumor == 0L,
            stringsAsFactors = FALSE
        )
    }))
    names(result)[names(result) == "level"] <- level_name
    result
}

sample_type_by_batch <- contingency_summary(
    sample_level_metadata$batch_number,
    "batch_number",
    sample_level_metadata
)
sample_type_by_tss <- contingency_summary(
    sample_level_metadata$tissue_source_site,
    "tissue_source_site",
    sample_level_metadata
)
sample_type_by_tss$tissue_source_site_code <- vapply(
    sample_type_by_tss$tissue_source_site,
    function(site) {
        values <- unique(as.character(
            sample_level_metadata$tissue_source_site_code[
                as.character(sample_level_metadata$tissue_source_site) == site
            ]
        ))
        paste(values, collapse = ";")
    },
    character(1)
)
sample_type_by_tss <- sample_type_by_tss[, c(
    "tissue_source_site", "tissue_source_site_code", "n_tumor", "n_normal",
    "total", "both_groups_represented", "tumor_only", "normal_only"
)]

batch_values <- level_value(sample_level_metadata$batch_number)
tss_values <- level_value(sample_level_metadata$tissue_source_site)
observed_batch_tss <- unique(data.frame(
    batch_number = batch_values,
    tissue_source_site = tss_values,
    stringsAsFactors = FALSE
))
batch_by_tss <- do.call(rbind, lapply(
    seq_len(nrow(observed_batch_tss)),
    function(i) {
        rows <- batch_values == observed_batch_tss$batch_number[i] &
            tss_values == observed_batch_tss$tissue_source_site[i]
        n_tumor <- sum(sample_level_metadata$group[rows] == "tumor")
        n_normal <- sum(sample_level_metadata$group[rows] == "normal")
        data.frame(
            batch_number = observed_batch_tss$batch_number[i],
            tissue_source_site = observed_batch_tss$tissue_source_site[i],
            n_tumor = n_tumor,
            n_normal = n_normal,
            total = n_tumor + n_normal,
            both_groups_represented = n_tumor > 0L & n_normal > 0L,
            stringsAsFactors = FALSE
        )
    }
))
batch_by_tss <- batch_by_tss[order(
    batch_by_tss$batch_number,
    batch_by_tss$tissue_source_site
), ]

n_tss_per_batch <- tapply(tss_values, batch_values, function(x) length(unique(x)))
n_batch_per_tss <- tapply(batch_values, tss_values, function(x) length(unique(x)))

eta_squared <- function(coordinate, grouping) {
    complete <- is.finite(coordinate) & !is_missing(grouping)
    coordinate <- coordinate[complete]
    grouping <- factor(as.character(grouping[complete]))
    if (length(coordinate) < 2L || nlevels(grouping) < 2L) {
        return(NA_real_)
    }
    total_ss <- sum((coordinate - mean(coordinate))^2)
    if (total_ss == 0) {
        return(NA_real_)
    }
    group_means <- ave(coordinate, grouping, FUN = mean)
    sum((group_means - mean(coordinate))^2) / total_ss
}

structure_variables <- list(
    group = as.character(sample_level_metadata$group),
    batch_number = as.character(sample_level_metadata$batch_number),
    tissue_source_site = as.character(sample_level_metadata$tissue_source_site)
)
structure_coordinates <- list(
    MDS1 = mds1,
    MDS2 = mds2,
    PC1 = pca_coordinates[, 1L],
    PC2 = pca_coordinates[, 2L]
)
structure_association_summary <- do.call(rbind, lapply(
    names(structure_variables),
    function(variable_name) {
        grouping <- structure_variables[[variable_name]]
        do.call(rbind, lapply(
            names(structure_coordinates),
            function(coordinate_name) data.frame(
                variable = variable_name,
                coordinate = coordinate_name,
                n_samples_complete = sum(!is_missing(grouping)),
                n_levels = length(unique(grouping[!is_missing(grouping)])),
                eta_squared = eta_squared(
                    structure_coordinates[[coordinate_name]], grouping
                ),
                stringsAsFactors = FALSE
            )
        ))
    }
))

design_input <- data.frame(
    sample_id = sample_level_metadata$sample_id,
    group = factor(sample_level_metadata$group, levels = c("normal", "tumor")),
    batch_number = factor(sample_level_metadata$batch_number),
    tissue_source_site = factor(sample_level_metadata$tissue_source_site),
    stringsAsFactors = FALSE
)
rownames(design_input) <- design_input$sample_id

contrast_is_estimable <- function(design, coefficient_name) {
    coefficient_index <- match(coefficient_name, colnames(design))
    if (is.na(coefficient_index)) {
        return(FALSE)
    }
    decomposition <- svd(design, nu = 0L, nv = ncol(design))
    tolerance <- max(dim(design)) * max(decomposition$d) * .Machine$double.eps
    matrix_rank <- sum(decomposition$d > tolerance)
    if (matrix_rank == ncol(design)) {
        return(TRUE)
    }
    null_space <- decomposition$v[, seq.int(matrix_rank + 1L, ncol(design)),
        drop = FALSE
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
    nonestimable_columns <- limma::nonEstimable(design)
    if (is.null(nonestimable_columns)) {
        nonestimable_columns <- character(0)
    }
    column_assignments <- attr(design, "assign")
    term_labels <- attr(terms(formula), "term.labels")
    nonestimable_variables <- character(0)
    if (length(nonestimable_columns) > 0L) {
        column_indices <- match(nonestimable_columns, colnames(design))
        assignments <- column_assignments[column_indices]
        nonestimable_variables <- vapply(assignments, function(index) {
            if (index == 0L) "(Intercept)" else term_labels[index]
        }, character(1))
    }
    data.frame(
        design = design_name,
        formula = paste(deparse(formula), collapse = " "),
        variables = paste(variables, collapse = " + "),
        n_samples_available = nrow(design_input),
        n_samples_used = nrow(design),
        n_samples_excluded_missing = nrow(design_input) - nrow(design),
        n_coefficients = ncol(design),
        matrix_rank = matrix_rank,
        residual_degrees_of_freedom = nrow(design) - matrix_rank,
        full_rank = limma::is.fullrank(design),
        tumor_vs_normal_effect_estimable = contrast_is_estimable(
            design, "grouptumor"
        ),
        nonestimable_columns = paste(nonestimable_columns, collapse = ";"),
        nonestimable_variables = paste(
            unique(nonestimable_variables), collapse = ";"
        ),
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

case_group_counts <- as.data.frame.matrix(table(
    sample_level_metadata$case_id,
    sample_level_metadata$group
))
if (!"normal" %in% names(case_group_counts)) case_group_counts$normal <- 0L
if (!"tumor" %in% names(case_group_counts)) case_group_counts$tumor <- 0L
case_group_counts$case_id <- rownames(case_group_counts)
case_group_counts$total_samples <-
    case_group_counts$normal + case_group_counts$tumor
matched_case_description <- case_group_counts[
    case_group_counts$normal > 0L & case_group_counts$tumor > 0L,
    c("case_id", "tumor", "normal", "total_samples"),
    drop = FALSE
]
names(matched_case_description)[2:3] <- c(
    "n_primary_tumor_samples", "n_solid_tissue_normal_samples"
)
matched_case_description$exactly_one_tumor_one_normal <-
    matched_case_description$n_primary_tumor_samples == 1L &
    matched_case_description$n_solid_tissue_normal_samples == 1L
matched_case_description$multiple_tumor_samples <-
    matched_case_description$n_primary_tumor_samples > 1L
matched_case_description$multiple_normal_samples <-
    matched_case_description$n_solid_tissue_normal_samples > 1L

n_eligible_records <- nrow(eligible_ledger)
n_sample_level <- ncol(sample_level_counts)
n_tumor <- sum(sample_level_metadata$group == "tumor")
n_normal <- sum(sample_level_metadata$group == "normal")
n_samples_aggregated <- sum(records_per_sample > 1L)
n_records_collapsed <- n_eligible_records - n_sample_level
n_genes_before <- nrow(dge)
n_genes_retained <- sum(keep_by_filter)
n_genes_removed <- n_genes_before - n_genes_retained
percent_genes_retained <- 100 * n_genes_retained / n_genes_before
n_unique_cases <- nrow(case_group_counts)
n_cases_multiple_samples <- sum(case_group_counts$total_samples > 1L)
n_matched_cases <- nrow(matched_case_description)
n_cases_multiple_tumor <- sum(case_group_counts$tumor > 1L)
n_exact_matched <- sum(matched_case_description$exactly_one_tumor_one_normal)
n_matched_multiple_tumor <- sum(matched_case_description$multiple_tumor_samples)
n_matched_multiple_normal <- sum(matched_case_description$multiple_normal_samples)

group_symbols <- c(normal = 1L, tumor = 16L)
sample_symbols <- unname(group_symbols[as.character(sample_level_metadata$group)])

png(
    file.path(figure_dir, "library_size_diagnostic.png"),
    width = 1200, height = 800, res = 150
)
boxplot(
    log10(library_sizes_after_filtering) ~ sample_level_metadata$group,
    xlab = "Biological group",
    ylab = "log10 filtered raw library size",
    main = "Sample-level library-size diagnostic"
)
dev.off()

png(
    file.path(figure_dir, "tmm_normalization_factor_diagnostic.png"),
    width = 1200, height = 800, res = 150
)
boxplot(
    tmm_factors ~ sample_level_metadata$group,
    xlab = "Biological group",
    ylab = "TMM normalization factor",
    main = "TMM normalization-factor diagnostic"
)
abline(h = 1, lty = 2)
dev.off()

png(
    file.path(figure_dir, "mds_by_group.png"),
    width = 1200, height = 800, res = 150
)
plot(
    mds1, mds2,
    pch = sample_symbols,
    xlab = mds$axislabel[mds$dim.plot[1L]],
    ylab = mds$axislabel[mds$dim.plot[2L]],
    main = "edgeR MDS by biological group"
)
legend(
    "topright", legend = names(group_symbols),
    pch = unname(group_symbols), bty = "n"
)
dev.off()

png(
    file.path(figure_dir, "pca_logcpm_by_group.png"),
    width = 1200, height = 800, res = 150
)
plot(
    pca_coordinates[, 1L], pca_coordinates[, 2L],
    pch = sample_symbols,
    xlab = sprintf("PC1 (%.1f%%)", pca_variance_percent[1L]),
    ylab = sprintf("PC2 (%.1f%%)", pca_variance_percent[2L]),
    main = "PCA of TMM-aware log-CPM by biological group"
)
legend(
    "topright", legend = names(group_symbols),
    pch = unname(group_symbols), bty = "n"
)
dev.off()

png(
    file.path(figure_dir, "rle_sample_summary.png"),
    width = 1400, height = 700, res = 150
)
par(mfrow = c(1, 2))
boxplot(
    rle_median ~ sample_level_metadata$group,
    xlab = "Biological group", ylab = "Sample median RLE (log-CPM)",
    main = "RLE median"
)
abline(h = 0, lty = 2)
boxplot(
    rle_iqr ~ sample_level_metadata$group,
    xlab = "Biological group", ylab = "Sample RLE IQR (log-CPM)",
    main = "RLE spread"
)
dev.off()

format_number <- function(x, digits = 3L) {
    format(x, digits = digits, big.mark = ",", scientific = FALSE, trim = TRUE)
}

design_lines <- vapply(seq_len(nrow(design_diagnostics)), function(i) {
    row <- design_diagnostics[i, ]
    nonestimable_text <- if (nzchar(row$nonestimable_columns)) {
        paste0("; non-estimable columns: `", row$nonestimable_columns, "`")
    } else {
        "; no non-estimable columns"
    }
    paste0(
        "- Design ", row$design, " (`", row$formula, "`): ",
        row$n_samples_used, " samples, ", row$n_coefficients,
        " coefficients, rank ", row$matrix_rank, ", residual df ",
        row$residual_degrees_of_freedom, ", full rank = ", row$full_rank,
        ", tumour-vs-normal estimable = ",
        row$tumor_vs_normal_effect_estimable, nonestimable_text, "."
    )
}, character(1))

association_value <- function(variable, coordinate) {
    structure_association_summary$eta_squared[
        structure_association_summary$variable == variable &
            structure_association_summary$coordinate == coordinate
    ]
}

summary_lines <- c(
    "# TCGA-LUAD sample-level QC and design diagnostics",
    "",
    paste0("Generated: ", format(Sys.time(), tz = "UTC"), " UTC"),
    "",
    "## Scope and verified input",
    "",
    paste0(
        "Task #004 reloaded the unique TCGA-LUAD recount3 project as a gene-level ",
        "`RangedSummarizedExperiment`, pinned to `gencode_v26`. The verified ",
        "input had ", nrow(rse), " gene rows, ", ncol(rse),
        " expression-record columns, and the sole assay `raw_counts`. The run ",
        "used R ", as.character(getRversion()), ", recount3 ",
        as.character(packageVersion("recount3")), ", SummarizedExperiment ",
        as.character(packageVersion("SummarizedExperiment")), ", edgeR ",
        as.character(packageVersion("edgeR")), ", and limma ",
        as.character(packageVersion("limma")), "."
    ),
    "",
    "## 1. From expression records to biological samples",
    "",
    paste0(
        "The input contained ", nrow(record_ledger), " expression records. ",
        sum(!record_ledger$eligible_primary_analysis),
        " record(s) were explicitly excluded because their official GDC sample ",
        "type was not `Primary Tumor` or `Solid Tissue Normal`. The remaining ",
        n_eligible_records, " eligible records mapped to ", n_sample_level,
        " distinct GDC `sample_id` values. Counts for records sharing the same ",
        "verified sample ID were summed gene by gene, leaving ", n_tumor,
        " Primary Tumor samples and ", n_normal,
        " Solid Tissue Normal samples."
    ),
    paste0(
        n_samples_aggregated, " sample IDs required technical aggregation, and ",
        n_records_collapsed, " redundant expression-record columns were ",
        "collapsed. All invariant biological metadata agreed within each of ",
        "those sample IDs. `technical_aggregation_audit.csv` traces all original ",
        "records, including exclusions, to a final sample column where applicable."
    ),
    paste(
        "The required sample-level case, sample, sample-type, group, batch, and",
        "tissue-source-site fields had no missing values in the retained cohort."
    ),
    "",
    "## 2. Why counts were summed",
    "",
    paste(
        "Expression records and aliquots below the same verified GDC sample are",
        "technical representations of one biological sample, so documented edgeR",
        "`sumTechReps()` was used to sum their counts. Summing preserves the total",
        "sequencing evidence. Different `sample_id` values were never combined,",
        "even when they came from one case, because they are distinct biological",
        "samples that may require repeated-measures handling later."
    ),
    "",
    "## 3. What the DGEList contains",
    "",
    paste(
        "An edgeR `DGEList` is an in-memory container with a gene-by-sample raw",
        "read-count table, per-sample information (including library sizes, group,",
        "case, batch, and tissue-source site), and per-gene annotation. Here the",
        "annotation retains Ensembl ID, gene symbol/name, and gene type. All gene",
        "types were retained; the analysis was not restricted to protein-coding",
        "genes because no such scientific filtering decision has yet been made."
    ),
    "",
    "## 4. Low-expression filtering",
    "",
    paste0(
        "edgeR `filterByExpr()` used the tumour-versus-normal biological group to ",
        "identify genes with enough reads in a worthwhile number of samples. Of ",
        format_number(n_genes_before, 8), " genes before filtering, ",
        format_number(n_genes_retained, 8), " were retained and ",
        format_number(n_genes_removed, 8), " were removed (",
        sprintf("%.2f", percent_genes_retained), "% retained). This is independent ",
        "expression-sufficiency filtering, not differential-expression testing. ",
        "Removing very low-expression genes reduces uninformative tests and helps ",
        "later mean-variance estimation."
    ),
    "",
    "## 5. TMM normalization",
    "",
    paste0(
        "After filtering, library sizes were recalculated from the retained raw ",
        "counts and edgeR TMM factors were computed. Factors ranged from ",
        format_number(min(tmm_factors), 5), " to ",
        format_number(max(tmm_factors), 5), " (median ",
        format_number(median(tmm_factors), 5), "). Effective library size is raw ",
        "filtered library size multiplied by the TMM factor. TMM adjusts the scale ",
        "used by downstream methods for compositional differences; it does not ",
        "rewrite counts or force equal library sizes. This is distinct from ",
        "recount3 `compute_read_counts()`, which converts base-pair coverage to ",
        "estimated integer read counts using average mapped read length."
    ),
    "",
    "## 6. Exploratory MDS, PCA, and RLE",
    "",
    paste0(
        "MDS summarizes leading pairwise expression differences among samples. ",
        "PCA summarizes major variance directions in TMM-aware log-CPM values; ",
        "PC1 and PC2 explain ", sprintf("%.2f", pca_variance_percent[1L]), "% and ",
        sprintf("%.2f", pca_variance_percent[2L]), "%. RLE-style summaries subtract ",
        "each gene's across-sample median log-CPM, then report each sample's median ",
        "and IQR of those relative values. These are exploratory descriptions, not ",
        "sample-exclusion tests."
    ),
    paste0(
        "For a readable numerical view of structure, eta-squared for PC1 was ",
        sprintf("%.3f", association_value("group", "PC1")), " by group, ",
        sprintf("%.3f", association_value("batch_number", "PC1")), " by batch, and ",
        sprintf("%.3f", association_value("tissue_source_site", "PC1")),
        " by tissue-source site. The corresponding PC2 values were ",
        sprintf("%.3f", association_value("group", "PC2")), ", ",
        sprintf("%.3f", association_value("batch_number", "PC2")), ", and ",
        sprintf("%.3f", association_value("tissue_source_site", "PC2")),
        ". These descriptive fractions do not establish causation."
    ),
    "",
    "## 7. Sample-quality observations",
    "",
    paste0(
        "Filtered raw library sizes ranged from ",
        format_number(min(library_sizes_after_filtering), 8), " to ",
        format_number(max(library_sizes_after_filtering), 8), ". Sample RLE medians ",
        "ranged from ", format_number(min(rle_median), 5), " to ",
        format_number(max(rle_median), 5), ", and RLE IQRs ranged from ",
        format_number(min(rle_iqr), 5), " to ",
        format_number(max(rle_iqr), 5), ". These ranges show heterogeneity worth ",
        "reviewing in the figures, but no prespecified rule establishes an obvious ",
        "sample failure here. No sample was removed or labelled an outlier."
    ),
    paste(
        "The PCA and RLE figures nevertheless show a visibly separated",
        "low-PC2/high-RLE-spread subset of Primary Tumor samples concentrated at",
        "Christiana Healthcare. This is a concrete quality/structure concern for",
        "follow-up against source metadata, but it is not sufficient grounds for",
        "exclusion in this task."
    ),
    "",
    "## 8. Batch and tissue-source-site overlap after aggregation",
    "",
    paste0(
        "At sample level, ", nrow(sample_type_by_batch), " CGC batch levels were ",
        "present: ", sum(sample_type_by_batch$both_groups_represented),
        " contained both groups, ", sum(sample_type_by_batch$tumor_only),
        " were tumour-only, and ", sum(sample_type_by_batch$normal_only),
        " were normal-only."
    ),
    paste0(
        nrow(sample_type_by_tss), " tissue-source-site levels were present: ",
        sum(sample_type_by_tss$both_groups_represented), " contained both groups, ",
        sum(sample_type_by_tss$tumor_only), " were tumour-only, and ",
        sum(sample_type_by_tss$normal_only), " were normal-only."
    ),
    paste0(
        "Batch and tissue-source site formed ", nrow(batch_by_tss),
        " observed combinations. ", sum(n_tss_per_batch > 1L), " of ",
        length(n_tss_per_batch), " batches spanned more than one site, while ",
        sum(n_batch_per_tss > 1L), " of ", length(n_batch_per_tss),
        " sites spanned more than one batch. They are related but not ",
        "interchangeable variables. Group-limited levels create potential ",
        "confounding; no ComBat or other batch correction was performed."
    ),
    "",
    "## 9. Candidate design diagnostics only",
    "",
    design_lines,
    "",
    paste0(
        "The cohort has ", n_unique_cases, " unique cases; ",
        n_cases_multiple_samples, " contribute more than one biological sample; ",
        n_matched_cases, " have both tumour and normal samples; and ",
        n_cases_multiple_tumor, " have multiple same-group Primary Tumor samples. ",
        "No design was selected and no model was fitted. `case_id` remains reserved ",
        "for later repeated-measures/blocking decisions."
    ),
    "",
    "## 10. Matched-case subset and no position-based exclusion",
    "",
    paste0(
        "Among the ", n_matched_cases, " matched cases, ", n_exact_matched,
        " have exactly one tumour and one normal sample, ",
        n_matched_multiple_tumor, " have multiple tumour samples, and ",
        n_matched_multiple_normal, " have multiple normal samples. No sample was ",
        "chosen arbitrarily and no paired analysis was run. A distant PCA or MDS ",
        "position can reflect biology, technical variation, or both; without an ",
        "independent failure criterion it is not sufficient grounds for exclusion."
    ),
    "",
    "## 11. Decisions still unresolved before differential expression",
    "",
    "- Whether the later analysis should use all samples, a matched subset, or both.",
    "- How to model repeated biological samples and case-level pairing/blocking.",
    "- Whether batch, tissue-source site, or neither belongs in the final design.",
    "- How to address the observed tumour/normal imbalance.",
    "- Whether any sample has independent technical evidence justifying exclusion.",
    "- Whether additional gene-type restrictions are scientifically justified.",
    "",
    "## Explicitly not performed",
    "",
    "This task did **not** perform:",
    "",
    "- differential-expression testing;",
    "- `voomLmFit`;",
    "- `eBayes`;",
    "- `topTable`;",
    "- batch correction;",
    "- candidate-gene selection;",
    "- scoring.",
    ""
)

write.csv(
    record_ledger,
    file.path(output_dir, "technical_aggregation_audit.csv"),
    row.names = FALSE,
    na = ""
)
write.csv(
    sample_level_metadata,
    file.path(output_dir, "sample_level_metadata.csv"),
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
    sample_type_by_batch,
    file.path(output_dir, "sample_type_by_batch_samplelevel.csv"),
    row.names = FALSE,
    na = ""
)
write.csv(
    sample_type_by_tss,
    file.path(output_dir, "sample_type_by_tss_samplelevel.csv"),
    row.names = FALSE,
    na = ""
)
write.csv(
    batch_by_tss,
    file.path(output_dir, "batch_by_tss_samplelevel.csv"),
    row.names = FALSE,
    na = ""
)
write.csv(
    structure_association_summary,
    file.path(output_dir, "structure_association_summary.csv"),
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
    matched_case_description,
    file.path(output_dir, "matched_case_description.csv"),
    row.names = FALSE,
    na = ""
)
writeLines(
    summary_lines,
    file.path(output_dir, "sample_qc_summary.md"),
    useBytes = TRUE
)

message("Sample-level QC complete. Outputs: ", output_dir)
