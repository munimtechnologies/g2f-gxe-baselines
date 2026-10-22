# g2f-envkernel 0.1.0: result

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed the numbers yet. Text CC BY 4.0;
code Apache-2.0.

This grades the pre-registration [`g2f-envkernel-0.1.0-prereg.md`](g2f-envkernel-0.1.0-prereg.md),
which was committed to this repository (release v0.1.0) before the job `g2f-envkernel-v1` read any
yield data. The job ran in a sealed container on 2026-10-22 (01:34-01:44 UTC): it waited for the
pre-registration to be public, passed its offline tests, then fit the model and scored it. Outputs are
in [`results/g2f_envkernel.json`](../results/g2f_envkernel.json),
[`results/g2f_envkernel_2024_env_r.csv`](../results/g2f_envkernel_2024_env_r.csv) and
[`results/g2f_envkernel_2024_predictions.csv`](../results/g2f_envkernel_2024_predictions.csv).

## What the model does

Model M2 of g2f-baseline 0.1.0 (a marker ridge shrunk toward each hybrid's own mean) refitted for each
test environment, with training environments weighted by how close their environmental covariates (the
organisers' EC files, reduced to 10 principal components, 62.5% of the variance) are to the test
environment's. Equal weights ("uniform") reproduce M2 exactly. The kernel bandwidth h was chosen inside
each fold by validating on the last training year only, then refitted on all training years and scored
once on the held-out year. EC coverage on the 2024 fold: 95.7% of test environments and 88.6% of
training environments had an EC row (2425 markers, ridge lambda 1000 on every fold).

## Scores (mean within-environment Pearson r)

| Fold | inner-chosen h | chosen r | uniform r (= M2) | chosen - uniform | hindsight-best h (r) |
|---|---|---|---|---|---|
| 2022 | uniform | 0.3257 | 0.3257 | 0.0000 | h2 (0.3263) |
| 2023 | h2 | 0.4387 | 0.4371 | +0.0016 | h1 (0.4392) |
| 2024 | h1 | 0.2807 | 0.2802 | +0.0005 | h2 (0.2847) |

## Predictions, graded

All four pre-registered predictions and the hypothesis held:

- **P1 held.** chosen - uniform on 2024 = **+0.0005**, inside [-0.02, +0.03] (point estimate was +0.005).
- **P2 held.** The inner validation chose a non-uniform h in **2 of 3** folds (h2 in 2023, h1 in 2024;
  uniform in 2022), meeting the "at least 2 of 3" bar exactly.
- **P3 held.** 2024 test-environment EC coverage **95.7%** (>= 90%) and 2014-2023 training-environment
  coverage **88.6%** (>= 80%).
- **P4 held.** On 2024, the best h chosen with hindsight (h2) beats uniform by **+0.0045** (< 0.03).
- **H1 held** (we gave it ~35%). The chosen h scored **at least as well as uniform on all three folds**
  (equal in 2022, +0.0016 in 2023, +0.0005 in 2024).

## Decision

The fixed decision rule was: adopt the kernel in MV2's 2026 entry only if H1 holds **and** the chosen h
gains at least +0.01 on 2024. H1 held, but the 2024 gain is **+0.0005**, twenty times below the +0.01
bar. **So the kernel is not adopted.** The 2026 entry keeps M2, and the next attempt is a different GxE
model, not a retuned kernel.

## Why the gain is so small

The kernel is well-behaved but almost inert. The per-environment table shows why: weighting by EC
similarity helps in about as many 2024 environments as it hurts, and the two roughly cancel. Comparing
the chosen h1 against uniform, it helps most in MOH1 (+0.031), NEH2 (+0.024), WIH2 (+0.024) and IAH4
(+0.020), and hurts most in WIH3 (-0.057), WIH1 (-0.040), NYH2 (-0.015) and MNH1 (-0.013). Down-weighting
distant training environments loses information where a hybrid's rank is stable across very different
sites, and gains it only where a site is genuinely idiosyncratic; on 2024 these balance out. The inner
validation correctly sensed this and picked uniform outright for the 2022 fold.

## Reading

A whole-environment similarity kernel cannot learn **which** hybrids respond to **which** covariate; it
only reweights environments wholesale. On the 2024 G2F maize answers that buys essentially nothing over
treating every environment equally. A model that lets genotype and environment interact at the level of
markers and covariates (a reaction-norm model), or that first separates the ~12% of 2024 rows that are
previously grown hybrids from the ~88% that are new, is the more promising next step. The next
pre-registered study, [`g2f-checkhybrid-0.1.0-prereg.md`](g2f-checkhybrid-0.1.0-prereg.md), does that
split before building any such model.

## Limits

- One fixed list of bandwidths, 10 PCs and a prior weight of 1, all set before the run.
- EC values are the organisers' derived covariates; their quality was not checked.
- The 2022 and 2023 folds are not the competition's original test sets.
