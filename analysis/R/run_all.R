# ==============================================================================
# run_all.R
# Purpose: Execute the full analysis pipeline in sequence, with error handling
#          and timing information for each step.
# Usage:   source("analysis/R/run_all.R") from the project root directory,
#          or set PROJECT_ROOT before sourcing.
# ==============================================================================

cat("================================================================\n")
cat("  crossover-edtech-toolkit: Full Analysis Pipeline\n")
cat("  Started: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S"), "\n")
cat("================================================================\n\n")

# Record overall start time
pipeline_start <- Sys.time()

# --------------------------------------------------------------------------
# Determine project root
# --------------------------------------------------------------------------

if (!exists("PROJECT_ROOT")) {
  PROJECT_ROOT <- tryCatch({
    script_dir <- dirname(sys.frame(1)$ofile)
    normalizePath(file.path(script_dir, "..", ".."), winslash = "/")
  }, error = function(e) {
    normalizePath(".", winslash = "/")
  })
}

SCRIPT_DIR <- file.path(PROJECT_ROOT, "analysis", "R")

# --------------------------------------------------------------------------
# Define pipeline steps
# --------------------------------------------------------------------------

scripts <- c(
  "00_setup.R",
  "01_data_import_clean.R",
  "02_descriptive_stats.R",
  "03_instrument_validation.R",
  "04_paired_comparisons.R",
  "05_mixed_anova.R",
  "06_effect_sizes.R",
  "07_carryover_analysis.R",
  "08_perception_analysis.R",
  "09_visualizations.R"
)

# --------------------------------------------------------------------------
# Execute each script with error handling
# --------------------------------------------------------------------------

results <- data.frame(
  script   = character(),
  status   = character(),
  duration = numeric(),
  message  = character(),
  stringsAsFactors = FALSE
)

for (script in scripts) {
  script_path <- file.path(SCRIPT_DIR, script)

  cat(paste0(">>> Running: ", script, "\n"))
  step_start <- Sys.time()

  tryCatch({
    withCallingHandlers(
      source(script_path, local = FALSE),
      warning = function(w) {
        cat(paste0("    WARNING: ", conditionMessage(w), "\n"))
        invokeRestart("muffleWarning")
      }
    )
    step_end <- Sys.time()
    duration <- as.numeric(difftime(step_end, step_start, units = "secs"))

    results <- rbind(results, data.frame(
      script   = script,
      status   = "SUCCESS",
      duration = round(duration, 2),
      message  = "",
      stringsAsFactors = FALSE
    ))

    cat(paste0(">>> ", script, " completed in ", round(duration, 2), " seconds.\n\n"))

  }, error = function(e) {
    step_end <- Sys.time()
    duration <- as.numeric(difftime(step_end, step_start, units = "secs"))

    results <<- rbind(results, data.frame(
      script   = script,
      status   = "ERROR",
      duration = round(duration, 2),
      message  = conditionMessage(e),
      stringsAsFactors = FALSE
    ))

    cat(paste0("*** ERROR in ", script, ": ", conditionMessage(e), "\n\n"))
  })
}

# --------------------------------------------------------------------------
# Pipeline summary
# --------------------------------------------------------------------------

pipeline_end <- Sys.time()
total_duration <- as.numeric(difftime(pipeline_end, pipeline_start, units = "secs"))

cat("\n================================================================\n")
cat("  Pipeline Summary\n")
cat("================================================================\n\n")

n_success <- sum(results$status == "SUCCESS")
n_error   <- sum(results$status == "ERROR")

cat(paste0("  Total scripts:   ", length(scripts), "\n"))
cat(paste0("  Successful:      ", n_success, "\n"))
cat(paste0("  Errors:          ", n_error, "\n"))
cat(paste0("  Total duration:  ", round(total_duration, 2), " seconds\n\n"))

# Print detailed results
cat("  Step-by-step results:\n")
cat("  ", paste(rep("-", 70), collapse = ""), "\n")

for (i in seq_len(nrow(results))) {
  status_icon <- ifelse(results$status[i] == "SUCCESS", "[OK]", "[!!]")
  cat(sprintf("  %s %-35s %8.2fs  %s\n",
              status_icon,
              results$script[i],
              results$duration[i],
              results$message[i]))
}

cat("  ", paste(rep("-", 70), collapse = ""), "\n")

# Save pipeline log
log_file <- file.path(PROJECT_ROOT, "output", "pipeline_log.csv")
results$timestamp <- format(Sys.time(), "%Y-%m-%d %H:%M:%S")
write.csv(results, log_file, row.names = FALSE)
cat(paste0("\n  Pipeline log saved to: ", log_file, "\n"))

if (n_error > 0) {
  cat("\n  Some scripts failed. Check error messages above.\n")
} else {
  cat("\n  All scripts completed successfully.\n")
  cat("  Output files are in: ", file.path(PROJECT_ROOT, "output"), "\n")
}

cat(paste0("\n  Finished: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S"), "\n"))
cat("================================================================\n")
