# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
# g2f-refmodel run_ref.R 0.1.2: runs the G2F organisers' public reference script ("Model 2022 (not
# competing)", github.com/alenxav/Lectures, G2F_GxE_2024/script_model.R) UNMODIFIED on the public 2024
# release and copies its prediction file to <out_dir>/ref_2024_predictions.csv. The script is downloaded
# when the job is set up and is not redistributed. This step never fails the job: an error is printed and
# the later steps still run.
# 0.1.1: the script reads its inputs from Maize_GxE_Competition_Data_2024/Training_data/ and
# .../Testing_data/ under its working folder; the files are linked in all three places.
# 0.1.2 (docs/g2f-refmodel-0.1.2-prereg.md): optional 4th argument, a library folder put first on the
# search path (to run the script with the bWGR release of the 2024 competition); prints the bWGR version
# used; when the script stops with an error, prints the call stack and the size and column types of the
# objects it had built (names, counts and classes only, never a yield).
# Usage: Rscript run_ref.R <script> <data_dir> <out_dir> [<lib_dir> | none]
.mv2 <- new.env()
local({
  args <- commandArgs(trailingOnly = TRUE)
  .mv2$script <- normalizePath(args[1])
  .mv2$data_dir <- normalizePath(args[2])
  out_dir <- args[3]
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  .mv2$out_dir <- normalizePath(out_dir)
  .mv2$lib <- if (length(args) >= 4 && args[4] != "none" && dir.exists(args[4])) normalizePath(args[4]) else NA
}, envir = globalenv())

if (!is.na(.mv2$lib)) .libPaths(c(.mv2$lib, .libPaths()))
cat("library search path:", paste(.libPaths(), collapse = " | "), "\n")
cat("bWGR version that will load:", tryCatch(as.character(packageVersion("bWGR")),
                                              error = function(e) "not installed"), "\n")

.mv2$wd <- file.path(tempdir(), "ref")
.mv2$rel <- "Maize_GxE_Competition_Data_2024"
local({
  subs <- c("Training_data", "Testing_data", file.path(.mv2$rel, "Training_data"),
            file.path(.mv2$rel, "Testing_data"))
  for (d in c(.mv2$wd, file.path(.mv2$wd, subs))) {
    dir.create(d, recursive = TRUE, showWarnings = FALSE)
  }
  link <- function(f, sub) {
    src <- file.path(.mv2$data_dir, f)
    if (!file.exists(src)) cat("missing input:", src, "\n")
    file.symlink(src, file.path(.mv2$wd, f))
    file.symlink(src, file.path(.mv2$wd, sub, f))
    file.symlink(src, file.path(.mv2$wd, .mv2$rel, sub, f))
  }
  link("1_Training_Trait_Data_2014_2023.csv", "Training_data")
  link("5_Genotype_Data_All_2014_2025_Hybrids_numerical.txt", "Training_data")
  link("1_Submission_Template_2024.csv", "Testing_data")
})
setwd(.mv2$wd)

.mv2$diag <- function() {
  g <- globalenv()
  for (nm in c("dta", "PSet", "Y", "X", "Z", "overlap", "loc_mu", "fit1", "fit2")) {
    if (!exists(nm, envir = g, inherits = FALSE)) {
      cat("diag:", nm, "absent\n")
      next
    }
    v <- get(nm, envir = g)
    d <- if (is.null(dim(v))) length(v) else paste(dim(v), collapse = " x ")
    cat("diag:", nm, "class", paste(class(v), collapse = "/"), "size", d, "\n")
    if (is.data.frame(v)) {
      cls <- vapply(v, function(col) class(col)[1], "")
      cat("diag:", nm, "columns:", paste(names(v), cls, sep = ":", collapse = " "), "\n")
      for (cn in intersect(c("Env", "Hybrid", "Loc"), names(v))) {
        cat("diag:", nm, "distinct", cn, length(unique(v[[cn]])), "\n")
      }
      if ("Yield_Mg_ha" %in% names(v)) {
        cat("diag:", nm, "Yield_Mg_ha missing", sum(is.na(v$Yield_Mg_ha)), "of", nrow(v), "\n")
      }
    }
  }
}

pdf(file.path(.mv2$out_dir, "ref_plots.pdf"))
.mv2$t0 <- Sys.time()
.mv2$calls <- NULL
.mv2$ok <- tryCatch({
  withCallingHandlers(source(.mv2$script, echo = FALSE),
                      error = function(e) .mv2$calls <- sys.calls())
  TRUE
}, error = function(e) {
  cat("REFERENCE SCRIPT ERROR:", conditionMessage(e), "\n")
  if (!is.null(.mv2$calls)) {
    cat("call stack (innermost last):\n")
    for (cl in utils::tail(.mv2$calls, 12)) {
      cat("  ", substr(paste(deparse(cl, nlines = 1), collapse = ""), 1, 160), "\n")
    }
  }
  .mv2$diag()
  FALSE
})
try(graphics.off(), silent = TRUE)
cat("reference script ran:", .mv2$ok, "in",
    round(as.numeric(difftime(Sys.time(), .mv2$t0, units = "mins")), 1), "minutes\n")

.mv2$outf <- file.path(.mv2$wd, "Prediction_Submission_Template.csv")
if (file.exists(.mv2$outf)) {
  file.copy(.mv2$outf, file.path(.mv2$out_dir, "ref_2024_predictions.csv"), overwrite = TRUE)
  cat("copied", .mv2$outf, "\n")
} else {
  cat("no prediction file; files in the working folder:\n")
  print(list.files(.mv2$wd, recursive = TRUE))
}
print(sessionInfo())
quit(status = 0)
