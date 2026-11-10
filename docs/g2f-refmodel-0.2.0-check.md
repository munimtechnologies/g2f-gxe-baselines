# g2f-refmodel 0.2.0 regression and the bWGR row-name check

RESULT-MARKER: g2f-refmodel-0.2.0-check

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed it yet. Text CC BY 4.0; code
Apache-2.0.

Written 2026-11-10. It covers one sealed job, `g2f-refmodel2-regress-v2` (r-base, 2 CPU, 4 GB, peak
2.03 GB, 13 minutes, on the G2F 2024 release volume). The job did two things:

1. It checked the unpublished `g2f_refmodel.R` 0.2.0, which finds a release's files in any layout,
   against the published 0.1.0, using the job's own `regress.py` (K1-K3). These checks were written
   before the run but were not committed to GitHub first, so they are reported as a regression test,
   not as a pre-registered study.
2. It ran `dimcheck.R`, the follow-up promised in [g2f-refmodel 0.1.2](g2f-refmodel-0.1.2-result.md),
   under bWGR 2.2.13 and under the current CRAN bWGR. It installed 2.2.18 itself.

Outputs: [`results/g2f_refmodel_regress.json`](../results/g2f_refmodel_regress.json),
[`results/dimcheck_2.2.13.json`](../results/dimcheck_2.2.13.json) and
[`results/dimcheck_2.2.18.json`](../results/dimcheck_2.2.18.json).

## Regression: 2 of 3 held, and the miss was in the check

| Check | Expected | Got | Held |
|---|---|---|---|
| K1 | `plan` on the 2024 release: test fold 2024, hold-outs "2023 2022" | test fold 2024, hold-outs "none" | no |
| K2 | `plan` on a simulated 2026 layout (renamed files in sub-folders): test fold 2026, renamed files found | test fold 2026; trait, template and genotype files found in `Training_data/` and `Testing_data/` | yes |
| K3 | `test` run: full scores 0.4416 +- 0.0001 on the released 2024 answers | **0.4416** (b2 0.4416, allloc 0.4418, b1 0.000) | yes |

K1 failed because 0.2.0 worked out the hold-out seasons only in `all` mode. In `plan` mode it printed
"none" while `all` would have fit 2023 and 2022. The model itself is unchanged: K3 reproduces the
published 2024 score to four decimals. **0.2.1** (unpublished until it passes) makes `plan` list the
folds that `all` would fit. It also adds an optional fifth argument, the number of hold-out seasons,
which g2f-refold uses to score four past seasons on the 2026 release. It changes no fitting line. Its
`plan` outputs (K1, K2, a four-fold and a zero-fold plan) are checked by `g2f-refmodel3-plan-v1`
before it is committed.

b1 (the global marker effect alone) scores 0.000 again. g2f-refmodel 0.1.0 and 0.1.1 found the same:
in this fit, the global effect gives every hybrid the same value inside each environment.

## Which bWGR helper drops the hybrid names

`dimcheck.R` builds a 30 x 50 toy marker matrix with row names, column names and some missing calls.
It passes the matrix through the three bWGR helpers that the organisers' reference script chains
before fitting (imputation, Gaussian kernel, kernel-to-covariates), and records what comes back:

| Helper | bWGR 2.2.13 | bWGR 2.2.18 |
|---|---|---|
| `IMP` (impute missing calls) | 30 x 50, **row and column names kept**, no missing values | 30 x 50, **row and column names dropped**, no missing values |
| `EigenGAU` (Gaussian kernel) | 30 x 30, no names | 30 x 30, no names |
| `K2X` (kernel to covariates) | 30 x 30, no names | 30 x 30, no names |

The function signatures are identical in both releases. The only difference is that **`IMP` stopped
returning the input's row and column names** somewhere between 2.2.13 and 2.2.18 (2.2.18 was published
on CRAN on 2026-07-25). That explains the failure in g2f-refmodel 0.1.2. The hybrid names are lost at
the first step, nothing downstream can match training yields to marker rows, and the training table
ends up empty under the current release. Under 2.2.13 the same script reproduces its leaderboard
score of 0.4377. MV2's re-implementation sets the row names again after `IMP`, so it runs under both.

Anyone running the reference script today can either pin bWGR 2.2.13 (the archive tarball, as `run_ref.R`
0.1.2 does) or set the marker matrix's row names again after imputation. The bWGR maintainer is also
the author of the reference script. A short note to him is drafted and waits for a person to read it
before it is sent.

## Limits

- The toy matrix is small and synthetic. It shows what `IMP` returns, not why it changed.
- Only 2.2.13 and 2.2.18 were tested, not the releases in between.

MV2, Munim, Inc., mv2@munimtech.com
