# SPDX-License-Identifier: Apache-2.0
# dimcheck.R 0.1.0 (g2f-refmodel 0.1.2 follow-up): which bWGR helper drops a marker matrix's row names?
# Usage: Rscript dimcheck.R <library folder or "none"> <output json>
# Builds a toy 0/1/2 marker matrix with hybrid row names and some missing calls, then applies
# IMP, EigenGAU and K2X (each with its first argument only) and records, for every step, the class,
# dimensions and whether row and column names survive. Prints only signatures, never function bodies.
# Made with AI agents working in MV2's (Munim, Inc.) name.
args <- commandArgs(trailingOnly = TRUE)
lib <- if (length(args) >= 1) args[1] else "none"
out <- if (length(args) >= 2) args[2] else "dimcheck.json"
if (lib != "none") .libPaths(c(lib, .libPaths()))
suppressPackageStartupMessages(library(bWGR))
ver <- as.character(packageVersion("bWGR"))
cat("bWGR", ver, "from", find.package("bWGR"), "\n")

set.seed(1)
n <- 30; p <- 50
Z <- matrix(sample(0:2, n * p, replace = TRUE), n, p)
Z[sample(length(Z), 40)] <- NA
rownames(Z) <- paste0("H", seq_len(n))
colnames(Z) <- paste0("m", seq_len(p))

describe <- function(x) {
  if (inherits(x, "error")) return(list(error = conditionMessage(x)))
  d <- dim(x)
  list(class = paste(class(x), collapse = "/"),
       dim = if (is.null(d)) length(x) else as.integer(d),
       has_rownames = !is.null(rownames(x)),
       rownames_match_input = identical(rownames(x), rownames(Z)),
       has_colnames = !is.null(colnames(x)),
       any_na = if (is.numeric(x)) any(is.na(x)) else FALSE)
}
step <- function(f, x) tryCatch(f(x), error = function(e) e)

sig <- function(name) if (exists(name)) paste(head(deparse(args(get(name))), 2), collapse = " ") else "absent"
res <- list(version = "0.1.0", bwgr = ver,
            signatures = list(IMP = sig("IMP"), EigenGAU = sig("EigenGAU"), K2X = sig("K2X")),
            input = describe(Z))
Zi <- step(IMP, Z);            res$IMP <- describe(Zi)
Zc <- if (inherits(Zi, "error")) Z else Zi
K  <- step(EigenGAU, Zc);      res$EigenGAU <- describe(K)
X  <- if (inherits(K, "error")) K else step(K2X, K)
res$K2X <- describe(X)
# Same chain on an input with complete calls (IMP should then have nothing to fill).
Zf <- Z; Zf[is.na(Zf)] <- 1
res$IMP_complete <- describe(step(IMP, Zf))
for (k in c("input", "IMP", "EigenGAU", "K2X", "IMP_complete")) {
  v <- res[[k]]
  cat(sprintf("%-13s %s\n", k, paste(names(v), sapply(v, function(z) paste(z, collapse = "x")),
                                     sep = "=", collapse = " ")))
}
# Minimal JSON writer (no extra packages).
js <- function(x) {
  if (is.list(x)) {
    if (is.null(names(x))) return(paste0("[", paste(sapply(x, js), collapse = ","), "]"))
    return(paste0("{", paste(sprintf("\"%s\":%s", names(x), sapply(x, js)), collapse = ","), "}"))
  }
  if (is.logical(x)) return(if (length(x) == 1) tolower(as.character(x)) else
    paste0("[", paste(tolower(as.character(x)), collapse = ","), "]"))
  if (is.numeric(x)) return(if (length(x) == 1) as.character(x) else
    paste0("[", paste(x, collapse = ","), "]"))
  s <- gsub("\"", "'", gsub("\\\\", "/", paste(x, collapse = " ")))
  paste0("\"", s, "\"")
}
dir.create(dirname(out), showWarnings = FALSE, recursive = TRUE)
writeLines(js(res), out)
cat("wrote", out, "\n")
