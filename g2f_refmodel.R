# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
# g2f-refmodel 0.1.0 (docs/g2f-refmodel-0.1.0-prereg.md): MV2's own re-implementation, written from a
# step-by-step description, of the public reference model that a G2F organiser posted to the 2024
# leaderboard as "Model 2022 (not competing)" (github.com/alenxav/Lectures, G2F_GxE_2024/script_model.R;
# that script is not copied here). Uses the bWGR package (GPL-3, CRAN) and reshape2 (CRAN).
# Variants per fold (prediction columns):
#   full   = Gaussian-kernel covariates x (global marker effect B1 + state-specific effects B2)
#   b1     = global marker effect only
#   b2     = state-specific marker effects only
#   allloc = full, trained on every location instead of only the test states
# Folds: 2024 (released answers; train 2014-2023), 2023 and 2022 (train on earlier years only).
# Usage: Rscript g2f_refmodel.R <data_dir> <out_dir>   -> <out_dir>/preds/<fold>.csv and <fold>_info.csv
suppressMessages({
  library(bWGR)
  library(reshape2)
})

args <- commandArgs(trailingOnly = TRUE)
data_dir <- if (length(args) >= 1) args[1] else "/data"
out_dir <- if (length(args) >= 2) args[2] else "/out"
pred_dir <- file.path(out_dir, "preds")
dir.create(pred_dir, recursive = TRUE, showWarnings = FALSE)

say <- function(...) {
  cat(format(Sys.time(), "%H:%M:%S"), ..., "\n")
  flush(stdout())
}

state_of <- function(env) substr(env, 1, 2)

year_of <- function(df) {
  if ("Year" %in% names(df)) suppressWarnings(as.integer(df$Year))
  else suppressWarnings(as.integer(sub(".*_", "", df$Env)))
}

kernel_covariates <- function(dta, pset, Z0) {
  test_h <- intersect(unique(pset$Hybrid), rownames(Z0))
  train_h <- intersect(unique(dta$Hybrid), rownames(Z0))
  v_test <- apply(Z0[test_h, , drop = FALSE], 2, var, na.rm = TRUE)
  v_train <- apply(Z0[train_h, , drop = FALSE], 2, var, na.rm = TRUE)
  keep <- which(v_test > 0.01 & v_train > 0.01)
  Z <- IMP(Z0[, keep])
  rownames(Z) <- rownames(Z0)
  X <- K2X(EigenGAU(Z))
  rownames(X) <- rownames(Z)
  colnames(X) <- paste0("pc", seq_len(ncol(X)))
  list(X = X, markers_kept = length(keep))
}

fit_variants <- function(dta, pset, X, loc_filter = TRUE) {
  dta$Loc <- state_of(dta$Env)
  pset$Loc <- state_of(pset$Env)
  if (loc_filter) dta <- dta[dta$Loc %in% unique(pset$Loc), ]
  loc_mu <- with(dta, tapply(Yield_Mg_ha, Env, mean, na.rm = TRUE))
  dta$cnt <- dta$Yield_Mg_ha - as.numeric(loc_mu[dta$Env])
  Y <- reshape2::acast(dta, Hybrid ~ Env, value.var = "cnt", fun.aggregate = mean)
  Y <- Y[, which(colSums(!is.na(Y)) > 100), drop = FALSE]
  overlap <- intersect(rownames(Y), rownames(X))
  Y <- Y[overlap, , drop = FALSE]
  dta <- dta[dta$Hybrid %in% overlap & dta$Env %in% colnames(Y), ]
  say("  fitting (loc_filter =", loc_filter, "): rows", nrow(dta), "envs", ncol(Y),
      "hybrids", length(overlap))

  fit1 <- mm(y = Yield_Mg_ha, random = ~Env + Hybrid, data = dta, M = list(Hybrid = X[overlap, ]))
  B1 <- as.vector(fit1$Mrk$Hybrid)
  say("  mm done; B1 length", length(B1))
  fit2 <- ZSEMF(Y, X[overlap, ], npc = -1)
  states <- state_of(colnames(Y))
  B2 <- apply(fit2$b, 1, function(x) tapply(x, states, mean))
  B2 <- if (is.matrix(B2)) t(B2) else matrix(B2, ncol = 1, dimnames = list(NULL, unique(states)))
  say("  ZSEMF done; B2", nrow(B2), "x", ncol(B2))

  center <- function(h) apply(h, 2, function(x) x - mean(x))
  hats <- list(full = center(X %*% (B1 + B2)),
               b2 = center(X %*% B2),
               b1 = center(X %*% matrix(B1, ncol = 1)))
  mu <- tapply(loc_mu, state_of(names(loc_mu)), mean)

  idx_h <- match(pset$Hybrid, rownames(X))
  m <- as.numeric(mu[pset$Loc])
  m[is.na(m)] <- 0
  b1v <- hats$b1[idx_h, 1]
  out <- data.frame(Env = pset$Env, Hybrid = pset$Hybrid, stringsAsFactors = FALSE)
  fallback <- rep(FALSE, nrow(pset))
  for (v in c("full", "b2")) {
    h <- hats[[v]]
    j <- match(pset$Loc, colnames(h))
    ok <- !is.na(idx_h) & !is.na(j)
    val <- rep(NA_real_, nrow(pset))
    val[ok] <- h[cbind(idx_h[ok], j[ok])]
    fb <- !is.na(idx_h) & is.na(j)
    val[fb] <- b1v[fb]
    fallback <- fallback | fb
    out[[v]] <- val + m
  }
  out$b1 <- b1v + m
  for (v in c("full", "b1", "b2")) {
    miss <- is.na(out[[v]])
    out[[v]][miss] <- m[miss]
  }
  info <- list(train_rows = nrow(dta), train_envs = ncol(Y), train_hybrids = length(overlap),
               states_fitted = paste(sort(colnames(hats$full)), collapse = " "),
               test_rows = nrow(pset), test_rows_ungenotyped = sum(is.na(idx_h)),
               test_rows_state_fallback = sum(fallback))
  list(pred = out, info = info)
}

geno_file <- file.path(data_dir, "5_Genotype_Data_All_2014_2025_Hybrids_numerical.txt")
Z0 <- as.matrix(read.csv(geno_file, sep = "\t", skip = 1, row.names = 1))
say("genotypes:", nrow(Z0), "hybrids x", ncol(Z0), "markers")

trait <- read.csv(file.path(data_dir, "1_Training_Trait_Data_2014_2023.csv"), stringsAsFactors = FALSE)
trait$Env <- trimws(trait$Env)
trait$Hybrid <- trimws(trait$Hybrid)
trait$Yield_Mg_ha <- suppressWarnings(as.numeric(trait$Yield_Mg_ha))
trait$Yr <- year_of(trait)
trait <- trait[!is.na(trait$Yield_Mg_ha) & !is.na(trait$Yr), ]
tmpl <- read.csv(file.path(data_dir, "1_Submission_Template_2024.csv"), stringsAsFactors = FALSE)
tmpl$Env <- trimws(tmpl$Env)
tmpl$Hybrid <- trimws(tmpl$Hybrid)

folds <- list("2024" = list(train = trait, pset = unique(tmpl[, c("Env", "Hybrid")])))
for (y in c(2023L, 2022L)) {
  folds[[as.character(y)]] <- list(train = trait[trait$Yr < y, ],
                                   pset = unique(trait[trait$Yr == y, c("Env", "Hybrid")]))
}

for (name in names(folds)) {
  f <- folds[[name]]
  say("fold", name, ": train rows", nrow(f$train), "test pairs", nrow(f$pset))
  t0 <- Sys.time()
  res <- tryCatch({
    pf <- f$train
    pf$Loc <- state_of(pf$Env)
    kc <- kernel_covariates(pf[pf$Loc %in% unique(state_of(f$pset$Env)), ], f$pset, Z0)
    say("  kernel covariates:", nrow(kc$X), "x", ncol(kc$X), "from", kc$markers_kept, "markers")
    r <- fit_variants(f$train, f$pset, kc$X, TRUE)
    r$info$markers_kept <- kc$markers_kept
    r$info$kernel_pcs <- ncol(kc$X)
    r$X <- kc$X
    r
  }, error = function(e) {
    say("ERROR in fold", name, ":", conditionMessage(e))
    NULL
  })
  if (is.null(res)) next
  pred <- res$pred
  info <- res$info
  res2 <- tryCatch(fit_variants(f$train, f$pset, res$X, FALSE), error = function(e) {
    say("ERROR in fold", name, "allloc:", conditionMessage(e))
    NULL
  })
  if (is.null(res2)) {
    pred$allloc <- NA_real_
  } else {
    pred$allloc <- res2$pred$full
    info$allloc_train_rows <- res2$info$train_rows
    info$allloc_train_envs <- res2$info$train_envs
  }
  info$minutes <- round(as.numeric(difftime(Sys.time(), t0, units = "mins")), 1)
  write.csv(pred, file.path(pred_dir, paste0(name, ".csv")), row.names = FALSE)
  write.csv(data.frame(key = names(info), value = vapply(info, as.character, ""),
                       stringsAsFactors = FALSE),
            file.path(pred_dir, paste0(name, "_info.csv")), row.names = FALSE)
  say("fold", name, "written in", info$minutes, "minutes")
  rm(res, res2)
  invisible(gc())
}
say("bWGR", as.character(packageVersion("bWGR")), "R", R.version.string)
