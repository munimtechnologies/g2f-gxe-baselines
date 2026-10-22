# g2f-envkernel 0.1.0: pre-registration

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed it yet. Text CC BY 4.0; code Apache-2.0.

Written 2026-10-22 (about 01:40 UTC), after the graded g2f-baseline 0.1.0 result and before the job
`g2f-envkernel-v1` ran. No value in the environmental-covariate (EC) files has been read; only their
names and sizes in the public release listing. The job's first step waits until this file is public
on GitHub, so the model cannot read any yield data before these predictions are committed.

## Why

g2f-baseline 0.1.0 found that the best simple model (M2) scores a mean within-environment r of 0.280
on the 2024 answers, and that a location-specific memory (M3) adds nothing. Those models give every
environment the same hybrid ranking. The competition metric only scores rankings inside each
environment, so any further gain has to come from genotype-by-environment (GxE) effects. This is the
simplest open test of that: rank hybrids for a new field by how they did in fields with similar
weather and soil.

## Method

- **Covariates.** The organisers' EC files (`6_Training_EC_Data_2014_2023.csv`,
  `6_Testing_EC_Data_2024.csv`): one row per environment. Text columns, columns more than 50% missing,
  constant columns and any `Year` column are dropped. Gaps are filled with the column mean, columns
  are z-scored over all environments, and the first 10 principal components are kept. No yield is
  used here.
- **Weights.** For a test environment e, each training environment j gets
  w_j = exp(-d²(e, j) / (h x s)), where d is the distance in PC space and s is the median squared
  distance between training environments. Weights are scaled to mean 1. Training environments
  without an EC row get the median weight. A test environment without an EC row gets equal weights.
- **Model.** M2 of g2f-baseline 0.1.0, refitted for each test environment on weighted hybrid means
  t = (sum of w x z + 1 x the unweighted mean) / (sum of w + 1). The ridge penalty is the fold's
  lambda from 5-fold CV on unweighted means, as in 0.1.0. Shrinkage toward the hybrid's own weighted
  mean uses k = 5 and the weighted plot count. With equal weights this is exactly M2 (tested).
- **Bandwidths.** h in {0.25, 0.5, 1, 2} and "uniform" (= M2).
- **Choosing h without the test year.** In each fold, h is chosen by training on all years before
  the last training year and scoring on that year (2021 for the 2022 fold, 2022 for 2023, 2023 for
  2024). Ties go to the wider kernel, with uniform counting as widest. The chosen h is then refitted
  on all training years and scored once on the held-out year. Scores for every h are also reported,
  but only the chosen one counts as the model's result.
- **Folds and metric.** As in 0.1.0: 2022 and 2023 (all reported plots of that year, trained only on
  earlier years) and 2024 (the organisers' released observed values). Mean within-environment Pearson
  r, skipping environments with fewer than 3 observed rows.

## Predictions

- **P1:** chosen minus uniform on 2024 lies in [-0.02, +0.03]; point estimate +0.005.
- **P2:** the inner validation picks a non-uniform h in at least 2 of the 3 folds.
- **P3:** at least 90% of the 2024 test environments, and at least 80% of the 2014-2023 training
  environments, have an EC row.
- **P4:** on 2024, even the best h chosen with hindsight beats uniform by less than 0.03.

## Hypothesis

- **H1:** the chosen h scores at least as well as uniform on all 3 folds. We give this about a 35%
  chance. It is the result that would make the model worth using in MV2's 2026 entry.

## Decision rule (fixed now)

The model goes into the 2026 entry only if H1 holds and the chosen h gains at least +0.01 on 2024.
Otherwise the entry keeps M2, and the next attempt is a different GxE model, not a retuned kernel.

## Limits

- One fixed list of bandwidths, 10 PCs and a prior weight of 1, all set before the run.
- EC values are the organisers' derived covariates; their quality was not checked.
- A kernel on whole-environment similarity cannot learn which hybrids respond to which covariate.
  That is a richer model, left for later.
- The 2022 and 2023 folds are not the competitions' original test sets.
