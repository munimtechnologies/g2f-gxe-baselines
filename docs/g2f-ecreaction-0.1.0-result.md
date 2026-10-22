# g2f-ecreaction 0.1.0: result

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed the numbers yet. Text CC BY 4.0;
code Apache-2.0.

This grades the pre-registration [`g2f-ecreaction-0.1.0-prereg.md`](g2f-ecreaction-0.1.0-prereg.md),
committed to this repository (release v0.6.0) before the job `g2f-ecreaction-v1` read any yield data. The
job ran in a sealed container on 2026-10-22 (12:02-12:09 UTC, 413 s, peak 0.71 GB). It confirmed the
pre-registration was public (first attempt), passed its 11 offline tests, then fitted the reaction norm
and scored all three folds. Outputs: [`results/g2f_ecreaction.json`](../results/g2f_ecreaction.json) and
[`results/g2f_ecreaction_2024_env_r.csv`](../results/g2f_ecreaction_2024_env_r.csv).

## Checks

- **Reproduction gate passed.** 2024 all-rows mean within-environment r: M2 0.2802 and M4 0.3018, the
  same as earlier studies, and the grid point alpha = 0 equals M4 (0.3018).
- The marker matrix (2,425 markers) was reduced to 20 PCs; the organisers' EC files gave 654 covariates
  over 263 environments, reduced to 10 PCs (62.5% of the variance). The reaction-norm ridge chose
  lambda = 100 on every fold.

## Selection and scores (mean within-environment Pearson r)

The 2022 grid chose **alpha\* = 0**, so M7 = M4 on every fold. The alpha grid, by fold (all-rows mean
within-environment r):

| alpha | 0 (= M4) | 0.5 | 1 | 2 |
|---|---|---|---|---|
| 2022 (28 envs, selection fold, in-sample) | **0.3262** | 0.3166 | 0.2944 | 0.2421 |
| 2023 (27 envs) | 0.4354 | 0.4390 | **0.4395** | 0.4326 |
| 2024 (22 envs) | **0.3018** | 0.2954 | 0.2736 | 0.2243 |

On the **2022 selection fold** every nonzero alpha scores below alpha = 0, so the null weight is chosen
and M7 equals M4. Applied forward, M7 = M4 on 2024: 0.3018, unchanged. Had the weight instead been tuned
on 2023 (where alpha = 1 gains +0.0041), it would have scored **0.2736** on 2024, **-0.0282** below M4.

## Predictions, graded

Two of five predictions held; the hypothesis failed.

- **P1 failed.** The reaction-norm model's grouped-CV r on the 2024 training data is **0.227** (bar: at
  least 0.30; point 0.45). The PC-reduced marker-by-covariate model carries signal, but less than hoped.
- **P2 held.** On 2024 the within-environment spread of the interaction term is **54%** of M4's (bar: at
  least 5%; point 0.15). The reaction norm genuinely reorders hybrids within a field: it is nonzero on
  95.8% of rows and almost uncorrelated with M4 (pooled r 0.015).
- **P3 held.** On 2024, M7 - M4 is **0.000** (bar: between -0.01 and +0.02), because alpha\* = 0.
- **P4 failed.** The 2022 selection picks **alpha\* = 0** (bar: alpha\* > 0; about 55%). Every nonzero
  weight hurts the selection fold.
- **P5 failed.** On 2024 **new** rows, M7 - M4 is **0.000** (bar: above 0): with alpha\* = 0, M7 equals
  M4 by construction, so it cannot beat it.
- **H1 failed** (we gave it about 12%). M7 - M4 is 0.000 on both 2024 (bar: at least +0.01) and 2023.

## What this shows

1. **The reaction norm has real within-season signal that does not pay off forward.** The interaction
   term is large (its within-environment spread is half of M4's, and it is nonzero on 95.8% of 2024
   rows) and the PC model predicts held-out yield at r = 0.23, yet adding any positive weight lowers the
   within-environment score on the 2022 selection fold **and** on the 2024 hold-out. The one fold it
   helps is 2023 (+0.0041 at alpha = 1), and even there a weight tuned on 2023 loses 0.028 on 2024.
2. **This is the fourth environment-specific device to gain nothing on the 2024 hold-out,** after a
   hybrid-by-location residual (M3), covariate-weighted refitting (g2f-envkernel) and a parent-by-location
   offset (g2f-parentloc). Each adds a way for hybrids to rank differently from field to field; each
   either fits the training years and reverses forward, or carries signal that the forward-season ranking
   does not reward. The consistent lesson is that one genomic value per hybrid, used in every
   environment (M4), is hard to beat for the forward within-environment ranking on these data.

Marker-by-covariate reaction norms are a standard genomic-G×E model family. What is new here is an open,
pre-registered test of one, added as a controlled correction on the simple M4 baseline, against the
within-environment metric on the released G2F 2024 answers, with the finding that a reaction norm with
genuine within-season signal still does not improve the forward ranking.

## Decision (fixed in advance)

**H1 failed, so MV2's 2026 G2F entry keeps M4** (0.302 on the 2024 answers). P5 failed, so the
pre-registered branch turns away from environment-specific ranking terms. Before the 2026 training
release opens (2026-11-16), the next study, [`g2f-gcablend-0.1.0-prereg.md`](g2f-gcablend-0.1.0-prereg.md),
asks a question about the entry model itself: M4 fixes its marker-ridge/parent-GCA blend weight at 0.5 a
priori. Parent GCA is the one component that helped the 2024 hold-out (+0.0216 over M2) yet barely moved
2022 (+0.0005) and slightly hurt 2023 (-0.0017), so that study tests whether tuning the blend weight on
the two training years beats the a-priori 0.5 on the forward 2024 season, or whether the year-specific
value of parent GCA makes the fixed weight the safer entry.

## Limits

- One selection fold with three nonzero values of alpha; markers and covariates are each reduced to a
  handful of principal components, so fine, non-linear or single-marker reaction norms are not captured.
  The interaction is bilinear in the two PC spaces.
- Environments without an EC row, and hybrids without genotypes, get no interaction term.
- Reaction norms are a known model family; the contribution is the pre-registered test on the released
  2024 answers against the within-environment metric, not the model itself.
