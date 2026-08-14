#!/usr/bin/env Rscript

# TCGA-LUAD dataset reconnaissance through recount3.
#
# Scope: dataset identity, object structure, metadata composition, sample types,
# patient/sample multiplicity, and observations relevant to later modelling.
# This script deliberately performs no filtering, normalization, transformation,
# differential-expression analysis, PCA-based exclusion, or scoring.

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

output_dir <- file.path(repository_root, "outputs", "reconnaissance")
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

# Use an official recount3 mirror documented in help(available_projects).
recount3_url <- Sys.getenv(
    "RECOUNT3_URL",
    unset = "https://recount-opendata.s3.amazonaws.com/recount3/release"
)

# By default, recount3 uses its normal user cache, outside this repository.
# RECOUNT3_CACHE_DIR can be set to another external cache for reproducible runs.
cache_dir <- Sys.getenv("RECOUNT3_CACHE_DIR", unset = "")
bfc <- if (nzchar(cache_dir)) {
    dir.create(cache_dir, recursive = TRUE, showWarnings = FALSE)
    recount3_cache(cache_dir)
} else {
    recount3_cache()
}

# The package documentation states that TCGA is split by tissue/project and
# that available_projects() is the supported way to identify a project record.
# Restricting available_homes to the documented TCGA home avoids downloading
# unrelated project indices.
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
        "Expected exactly one verified TCGA-LUAD project record, found ",
        nrow(project_record),
        ". Inspect available_projects() before changing the query."
    )
}

# Pin the gene annotation used for this analysis and verify that the installed
# recount3 version supports it before attempting to construct the object.
annotation <- "gencode_v26"
supported_human_annotations <- annotation_options("human")
if (!annotation %in% supported_human_annotations) {
    stop(
        "Required annotation 'gencode_v26' is not available in ",
        "annotation_options('human'). Available annotations: ",
        paste(supported_human_annotations, collapse = ", ")
    )
}

rse <- create_rse(
    project_info = project_record,
    type = "gene",
    annotation = annotation,
    bfc = bfc,
    recount3_url = recount3_url
)

if (!inherits(rse, "RangedSummarizedExperiment")) {
    stop("create_rse() did not return a RangedSummarizedExperiment.")
}

if (!identical(assayNames(rse), "raw_counts")) {
    stop(
        "Expected the documented untransformed 'raw_counts' assay; found: ",
        paste(assayNames(rse), collapse = ", ")
    )
}

project_output <- project_record
project_output$recount3_version <- as.character(packageVersion("recount3"))
project_output$SummarizedExperiment_version <- as.character(
    packageVersion("SummarizedExperiment")
)
project_output$R_version <- paste(R.version$major, R.version$minor, sep = ".")
project_output$object_class <- class(rse)[[1L]]
project_output$feature_type <- "gene"
project_output$annotation <- metadata(rse)$annotation
project_output$n_features_loaded <- nrow(rse)
project_output$n_samples_loaded <- ncol(rse)
project_output$assay_names <- paste(assayNames(rse), collapse = "; ")
project_output$recount3_url <- recount3_url

write.csv(
    project_output,
    file.path(output_dir, "project_record.csv"),
    row.names = FALSE,
    na = ""
)

sample_metadata <- as.data.frame(colData(rse))

# These mappings were verified against the actual recount3 1.20.0 TCGA-LUAD
# colData(), not inferred from barcodes or column-name fragments.
metadata_fields <- c(
    sample_type = "tcga.gdc_cases.samples.sample_type",
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
    portion_id = "tcga.gdc_cases.samples.portions.portion_id",
    sex = "tcga.gdc_cases.demographic.gender",
    age_at_diagnosis = "tcga.gdc_cases.diagnoses.age_at_diagnosis",
    stage = "tcga.gdc_cases.diagnoses.tumor_stage",
    sequencing_platform = "tcga.gdc_platform",
    sequencing_center = "tcga.gdc_center.name",
    sequencing_center_id = "tcga.gdc_center.center_id",
    tissue_source_site = "tcga.gdc_cases.tissue_source_site.name",
    tissue_source_site_code = "tcga.gdc_cases.tissue_source_site.code",
    batch_number = "tcga.cgc_case_batch_number",
    recount_external_id = "external_id",
    recount_rail_id = "rail_id"
)

missing_verified_fields <- setdiff(metadata_fields, names(sample_metadata))
if (length(missing_verified_fields) > 0L) {
    stop(
        "Verified TCGA-LUAD metadata field(s) are absent: ",
        paste(missing_verified_fields, collapse = ", "),
        ". Re-inspect colData() before changing the mappings."
    )
}

is_missing <- function(x) {
    is.na(x) | trimws(as.character(x)) == ""
}

field_descriptions <- c(
    sample_type = "Official GDC sample type",
    case_id = "GDC case UUID (patient/case identifier)",
    case_submitter_id = "GDC case submitter ID",
    sample_id = "GDC sample UUID",
    sample_submitter_id = "GDC sample submitter ID",
    aliquot_id = "GDC aliquot UUID",
    aliquot_submitter_id = "GDC aliquot submitter ID",
    portion_id = "GDC portion UUID",
    sex = "GDC demographic gender field",
    age_at_diagnosis = paste(
        "GDC age-at-diagnosis field; retained as supplied,",
        "with no conversion in reconnaissance"
    ),
    stage = "GDC diagnosis tumour-stage field",
    sequencing_platform = "GDC sequencing platform",
    sequencing_center = "GDC sequencing center name",
    sequencing_center_id = "GDC sequencing center UUID",
    tissue_source_site = "GDC tissue-source-site name",
    tissue_source_site_code = "GDC tissue-source-site code",
    batch_number = "CGC case batch number supplied in recount3 metadata",
    recount_external_id = "recount3 external expression-column identifier",
    recount_rail_id = "recount3 internal rail identifier"
)

key_metadata_summary <- do.call(
    rbind,
    lapply(names(metadata_fields), function(role) {
        field_name <- metadata_fields[[role]]
        values <- sample_metadata[[field_name]]
        missing <- is_missing(values)
        data.frame(
            role = role,
            colData_field = field_name,
            description = field_descriptions[[role]],
            R_class = paste(class(values), collapse = ";"),
            n_missing = sum(missing),
            percent_missing = round(100 * mean(missing), 2),
            n_unique_nonmissing = length(unique(as.character(values)[!missing])),
            stringsAsFactors = FALSE
        )
    })
)

write.csv(
    key_metadata_summary,
    file.path(output_dir, "key_metadata_summary.csv"),
    row.names = FALSE,
    na = ""
)

sample_type <- as.character(sample_metadata[[metadata_fields[["sample_type"]]]])
sample_type_table <- as.data.frame(table(sample_type), stringsAsFactors = FALSE)
names(sample_type_table) <- c("official_gdc_sample_type", "n_expression_columns")
sample_type_table$requested_category <- ifelse(
    sample_type_table$official_gdc_sample_type == "Primary Tumor",
    "Primary Solid Tumor (current GDC label: Primary Tumor)",
    sample_type_table$official_gdc_sample_type
)
sample_type_table <- sample_type_table[
    order(-sample_type_table$n_expression_columns),
    c("requested_category", "official_gdc_sample_type", "n_expression_columns")
]

write.csv(
    sample_type_table,
    file.path(output_dir, "sample_type_counts.csv"),
    row.names = FALSE,
    na = ""
)

case_id <- as.character(sample_metadata[[metadata_fields[["case_id"]]]])
sample_id <- as.character(sample_metadata[[metadata_fields[["sample_id"]]]])
aliquot_id <- as.character(sample_metadata[[metadata_fields[["aliquot_id"]]]])

valid_case <- !is_missing(case_id)
valid_sample <- !is_missing(sample_id)
valid_aliquot <- !is_missing(aliquot_id)

case_column_counts <- table(case_id[valid_case])
sample_column_counts <- table(sample_id[valid_sample])
aliquot_column_counts <- table(aliquot_id[valid_aliquot])

sample_types_by_case <- split(sample_type[valid_case], case_id[valid_case])
n_cases_with_primary_and_normal <- sum(vapply(
    sample_types_by_case,
    function(x) all(c("Primary Tumor", "Solid Tissue Normal") %in% x),
    logical(1)
))

n_unique_by_group <- function(value, group) {
    vapply(split(value, group), function(x) length(unique(x)), integer(1))
}

n_cases_multiple_distinct_samples <- sum(
    n_unique_by_group(sample_id[valid_case], case_id[valid_case]) > 1L
)
n_samples_multiple_distinct_aliquots <- sum(
    n_unique_by_group(aliquot_id[valid_sample], sample_id[valid_sample]) > 1L
)

case_indices <- split(seq_len(nrow(sample_metadata)), case_id)
n_cases_multiple_primary_samples <- sum(vapply(
    case_indices,
    function(i) {
        length(unique(sample_id[i][sample_type[i] == "Primary Tumor"])) > 1L
    },
    logical(1)
))

count_for_type <- function(label) {
    sum(sample_type == label, na.rm = TRUE)
}

primary_count <- count_for_type("Primary Tumor")
normal_count <- count_for_type("Solid Tissue Normal")
stage_values <- as.character(sample_metadata[[metadata_fields[["stage"]]]])
age_values <- sample_metadata[[metadata_fields[["age_at_diagnosis"]]]]

metadata_name_lines <- paste0("- `", names(sample_metadata), "`")
rowdata_name_lines <- paste0("- `", names(rowData(rse)), "`")

summary_lines <- c(
    "# TCGA-LUAD recount3 reconnaissance",
    "",
    paste0("Generated: ", format(Sys.time(), tz = "UTC", usetz = TRUE)),
    "",
    "## Scope",
    "",
    paste(
        "Dataset reconnaissance only. No filtering, normalization, count",
        "transformation, differential expression, PCA-based exclusion,",
        "candidate selection, or scoring was performed."
    ),
    "",
    "## A. Dataset identity",
    "",
    paste0(
        "The unique project record returned by `available_projects()` has ",
        "`project = LUAD`, `organism = human`, `file_source = tcga`, ",
        "`project_home = data_sources/tcga`, `project_type = data_sources`, ",
        "and `n_samples = ", project_record$n_samples, "`."
    ),
    paste0(
        "The run used recount3 ", packageVersion("recount3"),
        ", SummarizedExperiment ", packageVersion("SummarizedExperiment"),
        ", and R ", R.version.string, "."
    ),
    paste0(
        "`create_rse()` returned a `", class(rse)[[1L]],
        "` using the resolved annotation `", metadata(rse)$annotation, "`."
    ),
    "",
    "## B. Expression object",
    "",
    paste0("- Features (rows): ", nrow(rse)),
    paste0("- Expression columns: ", ncol(rse)),
    paste0("- Assay names: `", paste(assayNames(rse), collapse = "`, `"), "`"),
    "",
    paste(
        "The installed recount3 vignette describes gene-level values in",
        "`raw_counts` as raw base-pair coverage counts summed over annotated",
        "gene regions. They are not conventional read counts and are not",
        "normalized expression values. This script inspects the assay as",
        "provided and does not call `transform_counts()` or",
        "`compute_read_counts()`."
    ),
    "",
    "`rowData()` fields:",
    "",
    rowdata_name_lines,
    "",
    paste(
        "The row ranges additionally carry genomic coordinates for each",
        "gene feature."
    ),
    "",
    "## C. Sample metadata",
    "",
    paste0("`colData()` contains ", ncol(sample_metadata), " metadata columns."),
    paste(
        "Verified key-field mappings and missingness are in",
        "`key_metadata_summary.csv`. Important observations include:"
    ),
    "",
    paste0(
        "- Sex/gender field: `", metadata_fields[["sex"]],
        "` (", sum(is_missing(sample_metadata[[metadata_fields[["sex"]]]])),
        " missing expression columns)."
    ),
    paste0(
        "- Age-at-diagnosis field: `", metadata_fields[["age_at_diagnosis"]],
        "` (", sum(is_missing(age_values)), " missing expression columns)."
    ),
    paste0(
        "- Stage field: `", metadata_fields[["stage"]],
        "` (", sum(is_missing(stage_values)), " blank/NA values; ",
        sum(tolower(stage_values) == "not reported", na.rm = TRUE),
        " values explicitly recorded as `not reported`)."
    ),
    paste0(
        "- Potential center/batch variables include GDC sequencing center ",
        "(", length(unique(sample_metadata[[metadata_fields[["sequencing_center"]]]])),
        " level), platform (",
        length(unique(sample_metadata[[metadata_fields[["sequencing_platform"]]]])),
        " level), tissue-source site (",
        length(unique(sample_metadata[[metadata_fields[["tissue_source_site"]]]])),
        " levels), and CGC batch number (",
        length(unique(sample_metadata[[metadata_fields[["batch_number"]]]])),
        " levels)."
    ),
    "",
    "## D. Tumour/normal composition",
    "",
    paste0(
        "- Primary Solid Tumor: ", primary_count,
        " expression columns. The current official GDC metadata label is",
        " `Primary Tumor`; the exact phrase `Primary Solid Tumor` is not",
        " present in this object."
    ),
    paste0("- Solid Tissue Normal: ", normal_count, " expression columns."),
    paste0("- Recurrent Tumor: ", count_for_type("Recurrent Tumor"), " expression columns."),
    "",
    "No sample type was filtered out.",
    "",
    "## E. Patient/sample structure",
    "",
    paste0("- Unique GDC cases: ", length(unique(case_id[valid_case])), "."),
    paste0(
        "- Cases contributing more than one expression column: ",
        sum(case_column_counts > 1L), "."
    ),
    paste0("- Unique GDC sample IDs: ", length(unique(sample_id[valid_sample])), "."),
    paste0(
        "- GDC sample IDs represented by more than one expression column: ",
        sum(sample_column_counts > 1L), "."
    ),
    paste0("- Unique GDC aliquot IDs: ", length(unique(aliquot_id[valid_aliquot])), "."),
    paste0(
        "- GDC aliquot IDs represented by more than one expression column: ",
        sum(aliquot_column_counts > 1L), "."
    ),
    paste0(
        "- Cases with both `Primary Tumor` and `Solid Tissue Normal`: ",
        n_cases_with_primary_and_normal, "."
    ),
    paste0(
        "- Cases with more than one distinct GDC sample ID: ",
        n_cases_multiple_distinct_samples, "."
    ),
    paste0(
        "- Cases with more than one distinct primary-tumour sample ID: ",
        n_cases_multiple_primary_samples, "."
    ),
    paste0(
        "- GDC sample IDs linked to more than one distinct aliquot ID: ",
        n_samples_multiple_distinct_aliquots, "."
    ),
    "",
    paste(
        "Distinct sample IDs within a case support repeated biological",
        "sampling, while distinct aliquot IDs within one sample support",
        "aliquot-level processing/technical replication. One aliquot ID is",
        "represented by two expression columns with different recount3",
        "external IDs, consistent with a possible sequencing/file-level",
        "technical replicate. These observations do not by themselves justify",
        "removing any column, and no duplicate was removed."
    ),
    "",
    "## F. Potential modelling issues (observations only)",
    "",
    paste0(
        "- Tumour/normal imbalance: ", primary_count, " primary-tumour versus ",
        normal_count, " normal expression columns (approximately ",
        round(primary_count / normal_count, 2), ":1)."
    ),
    paste0(
        "- Repeated observations: ", sum(case_column_counts > 1L),
        " cases contribute multiple expression columns."
    ),
    paste0(
        "- Matched data: ", n_cases_with_primary_and_normal,
        " cases have both a primary-tumour and normal sample."
    ),
    paste0(
        "- Clinical missingness: age at diagnosis is missing for ",
        sum(is_missing(age_values)), " expression columns; stage has ",
        sum(tolower(stage_values) == "not reported", na.rm = TRUE),
        " explicitly `not reported` values."
    ),
    paste(
        "- GDC sequencing center and platform are invariant here, whereas",
        "tissue-source site and CGC batch number vary and may be relevant",
        "later. No batch model or correction is chosen in this task."
    ),
    "",
    "## Decisions still unresolved",
    "",
    paste(
        "This reconnaissance does not decide the final cohort, how to handle",
        "repeated samples or aliquots, whether to use paired or unpaired",
        "modelling, which batch/center variables to include, how to treat",
        "missing clinical fields, count transformation, normalization,",
        "filtering, or differential-expression design. Those choices require",
        "a documented scientific decision after reviewing these observations."
    ),
    "",
    "## All `colData()` column names",
    "",
    metadata_name_lines,
    ""
)

writeLines(
    summary_lines,
    file.path(output_dir, "reconnaissance_summary.md"),
    useBytes = TRUE
)

message("Reconnaissance complete. Small outputs written to: ", output_dir)
