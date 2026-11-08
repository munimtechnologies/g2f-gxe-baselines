# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
# g2f-refmodel 0.1.0: runs the G2F organisers' public reference script ("Model 2022 (not competing)",
# github.com/alenxav/Lectures, G2F_GxE_2024/script_model.R) UNMODIFIED on the public 2024 release and
# copies its prediction file to <out_dir>/ref_2024_predictions.csv. The script is downloaded when the job
# is set up and is not redistributed. This step never fails the job: an error is printed and the
# re-implementation step still runs.
# Usage: Rscript run_ref.R <script> <data_dir> <out_dir>
args <- commandArgs(trailingOnly = TRUE)
script <- normalizePath(args[1])
data_dir <- normalizePath(args[2])
out_dir <- args[3]
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
out_dir <- normalizePath(out_dir)

wd <- file.path(tempdir(), "ref")
for (d in c(wd, file.path(wd, "Training_data"), file.path(wd, "Testing_data"))) {
  dir.create(d, recursive = TRUE, showWarnings = FALSE)
}
link <- function(f, sub) {
  src <- file.path(data_dir, f)
  if (!file.exists(src)) cat("missing input:", src, "\n")
  file.symlink(src, file.path(wd, f))
  file.symlink(src, file.path(wd, sub, f))
}
link("1_Training_Trait_Data_2014_2023.csv", "Training_data")
link("5_Genotype_Data_All_2014_2025_Hybrids_numerical.txt", "Training_data")
link("1_Submission_Template_2024.csv", "Testing_data")
setwd(wd)

pdf(file.path(out_dir, "ref_plots.pdf"))
t0 <- Sys.time()
ok <- tryCatch({
  source(script, echo = FALSE)
  TRUE
}, error = function(e) {
  cat("REFERENCE SCRIPT ERROR:", conditionMessage(e), "\n")
  FALSE
})
try(graphics.off(), silent = TRUE)
cat("reference script ran:", ok, "in",
    round(as.numeric(difftime(Sys.time(), t0, units = "mins")), 1), "minutes\n")

outf <- file.path(wd, "Prediction_Submission_Template.csv")
if (file.exists(outf)) {
  file.copy(outf, file.path(out_dir, "ref_2024_predictions.csv"), overwrite = TRUE)
  cat("copied", outf, "\n")
} else {
  cat("no prediction file; files in the working folder:\n")
  print(list.files(wd, recursive = TRUE))
}
print(sessionInfo())
quit(status = 0)
