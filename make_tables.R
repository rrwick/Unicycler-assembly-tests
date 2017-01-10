library(readr)
library(knitr)

table_format <- "markdown"


filter_results <- function(results, exclude_random_seqs = TRUE, exclude_bad_illumina = FALSE, read_set_type = NULL, assembler = NULL, version = NULL, setting = NULL, illumina_qual = NULL, long_qual = NULL) {
  if (exclude_random_seqs) {results <- results[!grepl("random_sequences", results$`Reference name`), ]}
  if (!is.null(read_set_type)) {results <- results[results$`Read set type` == read_set_type,]}
  if (!is.null(assembler)) {results <- results[results$Assembler == assembler,]}
  if (!is.null(version)) {results <- results[results$`Assembler version` == version,]}
  if (!is.null(setting)) {results <- results[results$`Assembler setting/output` == setting,]}
  if (!is.null(illumina_qual)) {results <- results[results$`Fake Illumina read quality` == illumina_qual,]}
  if (exclude_bad_illumina) {results <- results[results$`Fake Illumina read quality` != "bad",]}
  if (!is.null(long_qual)) {results <- results[results$`Fake long read quality` == long_qual,]}
  return(results)
}

get_values <- function(results, attribute) {
  values <- unlist(subset(results, select=attribute), use.names = FALSE)
  return(values)
}

get_numeric_values <- function(results, attribute) {
  values = as.character(get_values(results, attribute))
  values <- values[values != "" & values != "-" & !is.na(values)]
  return(as.numeric(values))
}

get_mean <- function(results, attribute, decimals) {
  val <- mean(get_numeric_values(results, attribute), na.rm = TRUE)
  if (!is.finite(val)) {return("-")}
  return(format(round(val, decimals), nsmall = decimals))
}

get_means <- function(result_groups, attribute, decimals) {
  means = c()
  for (i in 1:length(result_groups))
    means[i] <- get_mean(result_groups[[i]], attribute, decimals)
  return(means)
}

get_assembler_names <- function(result_groups) {
  assembler_names = c()
  for (i in 1:length(result_groups))
    assembler_names[i] <- result_groups[[i]]$Assembler[1]
  return(assembler_names)
}

get_assembler_versions <- function(result_groups) {
  assembler_versions = c()
  for (i in 1:length(result_groups))
    assembler_versions[i] <- result_groups[[i]]$`Assembler version`[1]
  return(assembler_versions)
}

get_assembler_settings <- function(result_groups) {
  assembler_settings = c()
  for (i in 1:length(result_groups)) {
    setting <- result_groups[[i]]$`Assembler setting/output`[1]
    if (is.na(setting))
      assembler_settings[i] <- ""
    else if (setting == "before_rr")
      assembler_settings[i] <- "before RR"
    else
      assembler_settings[i] <- setting
  }
  return(assembler_settings)
}

get_assembler_successes <- function(result_groups) {
  assembler_successes = c()
  for (i in 1:length(result_groups)) {
    results <- result_groups[[i]]$`Assembly result`
    successes <- 0
    total <- length(results)
    for (result in results) {
      if (result == "success")
        successes <- successes + 1
    }
    assembler_successes[i] <- paste(as.character(successes), "/", as.character(total), sep="")
  }
  return(assembler_successes)
}

short_read_table <- function(results, illumina_qual) {
  result_groups = list()
  result_groups[[1]] <- filter_results(results, assembler = "VelvetOptimiser", version = "2.2.5", illumina_qual = illumina_qual, exclude_random_seqs = TRUE, read_set_type = "short-only")
  result_groups[[2]] <- filter_results(results, assembler = "SPAdes", version = "3.9.1", setting = "before_rr", illumina_qual = illumina_qual, exclude_random_seqs = TRUE, read_set_type = "short-only")
  result_groups[[3]] <- filter_results(results, assembler = "SPAdes", version = "3.9.1", setting = "contigs", illumina_qual = illumina_qual, exclude_random_seqs = TRUE, read_set_type = "short-only")
  result_groups[[4]] <- filter_results(results, assembler = "SPAdes", version = "3.9.1", setting = "scaffolds", illumina_qual = illumina_qual, exclude_random_seqs = TRUE, read_set_type = "short-only")
  result_groups[[5]] <- filter_results(results, assembler = "ABySS", version = "2.0.2", setting = "contigs", illumina_qual = illumina_qual, exclude_random_seqs = TRUE, read_set_type = "short-only")
  result_groups[[6]] <- filter_results(results, assembler = "ABySS", version = "2.0.2", setting = "scaffolds", illumina_qual = illumina_qual, exclude_random_seqs = TRUE, read_set_type = "short-only")
  result_groups[[7]] <- filter_results(results, assembler = "Unicycler", version = "0.2.0", setting = "conservative", illumina_qual = illumina_qual, exclude_random_seqs = TRUE, read_set_type = "short-only")
  result_groups[[8]] <- filter_results(results, assembler = "Unicycler", version = "0.2.0", setting = "normal", illumina_qual = illumina_qual, exclude_random_seqs = TRUE, read_set_type = "short-only")
  result_groups[[9]] <- filter_results(results, assembler = "Unicycler", version = "0.2.0", setting = "bold", illumina_qual = illumina_qual, exclude_random_seqs = TRUE, read_set_type = "short-only")
  
  assembler_names <- get_assembler_names(result_groups)
  assembler_versions <- get_assembler_versions(result_groups)
  assembler_settings <- get_assembler_settings(result_groups)
  assembler_successes <- get_assembler_successes(result_groups)
  n50 = get_means(result_groups, "N50", 0)
  nga50 = get_means(result_groups, "NGA50", 0)
  misassemblies = get_means(result_groups, "Total misassemblies", 2)
  small_err = get_means(result_groups, "# small errors per 100 kbp", 2)
  time = get_means(result_groups, "Assembly time (minutes)", 2)
  
  short_read_results <- data.frame(assembler_names, assembler_versions, assembler_settings, assembler_successes, n50, nga50, misassemblies, small_err, time)  
  colnames(short_read_results) = c("Assembler", "Version", "Setting/output", "Successful assembly", "N50", "NGA50", "Misassemblies", "Small errors (per 100 kbp)", "Time (minutes)")
  
  kable(short_read_results, format = table_format)
}

hybrid_table <- function(results, illumina_qual = NULL, long_qual = NULL, exclude_bad_illumina = FALSE) {
  result_groups = list()
  result_groups[[1]] <- filter_results(results, assembler = "SPAdes", version = "3.9.1", setting = "contigs", illumina_qual = illumina_qual, long_qual = long_qual, exclude_random_seqs = TRUE, read_set_type = "hybrid", exclude_bad_illumina = exclude_bad_illumina)
  result_groups[[2]] <- filter_results(results, assembler = "SPAdes", version = "3.9.1", setting = "scaffolds", illumina_qual = illumina_qual, long_qual = long_qual, exclude_random_seqs = TRUE, read_set_type = "hybrid", exclude_bad_illumina = exclude_bad_illumina)
  result_groups[[3]] <- filter_results(results, assembler = "npScarf", version = "1.6-10a", setting = "only_contigs", illumina_qual = illumina_qual, long_qual = long_qual, exclude_random_seqs = TRUE, read_set_type = "hybrid", exclude_bad_illumina = exclude_bad_illumina)
  result_groups[[4]] <- filter_results(results, assembler = "npScarf", version = "1.6-10a", setting = "with_graph", illumina_qual = illumina_qual, long_qual = long_qual, exclude_random_seqs = TRUE, read_set_type = "hybrid", exclude_bad_illumina = exclude_bad_illumina)
  result_groups[[5]] <- filter_results(results, assembler = "Unicycler", version = "0.2.0", setting = "conservative", illumina_qual = illumina_qual, long_qual = long_qual, exclude_random_seqs = TRUE, read_set_type = "hybrid", exclude_bad_illumina = exclude_bad_illumina)
  result_groups[[6]] <- filter_results(results, assembler = "Unicycler", version = "0.2.0", setting = "normal", illumina_qual = illumina_qual, long_qual = long_qual, exclude_random_seqs = TRUE, read_set_type = "hybrid", exclude_bad_illumina = exclude_bad_illumina)
  result_groups[[7]] <- filter_results(results, assembler = "Unicycler", version = "0.2.0", setting = "bold", illumina_qual = illumina_qual, long_qual = long_qual, exclude_random_seqs = TRUE, read_set_type = "hybrid", exclude_bad_illumina = exclude_bad_illumina)
  
  assembler_names <- get_assembler_names(result_groups)
  assembler_versions <- get_assembler_versions(result_groups)
  assembler_settings <- get_assembler_settings(result_groups)
  assembler_successes <- get_assembler_successes(result_groups)
  n50 = get_means(result_groups, "N50", 0)
  nga50 = get_means(result_groups, "NGA50", 0)
  misassemblies = get_means(result_groups, "Total misassemblies", 2)
  small_err = get_means(result_groups, "# small errors per 100 kbp", 2)
  time = get_means(result_groups, "Assembly time (minutes)", 2)
  
  short_read_results <- data.frame(assembler_names, assembler_versions, assembler_settings, assembler_successes, n50, nga50, misassemblies, small_err, time)  
  colnames(short_read_results) = c("Assembler", "Version", "Setting/output", "Successful assembly", "N50", "NGA50", "Misassemblies", "Small errors (per 100 kbp)", "Time (minutes)")
  
  kable(short_read_results, format = table_format)
}

results <- read_delim("~/Desktop/results.tsv", "\t", escape_double = FALSE, trim_ws = TRUE)
results$`# small errors per 100 kbp` <- results$`# mismatches per 100 kbp` + results$`# indels per 100 kbp`
results$`Assembly time (minutes)` <- results$`Assembly time (seconds)` / 60.0

short_read_table(results, "bad")
short_read_table(results, "medium")
short_read_table(results, "good")

hybrid_table(results, illumina_qual = "bad")
hybrid_table(results, illumina_qual = "medium")
hybrid_table(results, illumina_qual = "good")
hybrid_table(results, long_qual = "bad", exclude_bad_illumina = TRUE)
hybrid_table(results, long_qual = "medium", exclude_bad_illumina = TRUE)
hybrid_table(results, long_qual = "good", exclude_bad_illumina = TRUE)


hybrid_table(results, illumina_qual = "bad", long_qual = "bad")
hybrid_table(results, illumina_qual = "bad", long_qual = "medium")
hybrid_table(results, illumina_qual = "bad", long_qual = "good")
hybrid_table(results, illumina_qual = "medium", long_qual = "bad")
hybrid_table(results, illumina_qual = "medium", long_qual = "medium")
hybrid_table(results, illumina_qual = "medium", long_qual = "good")
hybrid_table(results, illumina_qual = "good", long_qual = "bad")
hybrid_table(results, illumina_qual = "good", long_qual = "medium")
hybrid_table(results, illumina_qual = "good", long_qual = "good")
