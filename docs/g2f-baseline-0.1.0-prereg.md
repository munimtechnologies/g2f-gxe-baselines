# g2f-baseline 0.1.0: pre-registration

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed it yet. Text CC BY 4.0; code Apache-2.0.

Written 2026-10-21 (about 23:40 UTC), before the job `g2f-baseline-v1` ran and before any yield value,
genotype value or 2024 observed value of the release below was read. Only the public file list, file
sizes and the data papers' descriptions were read.

## Why

The Genomes to Fields (G2F) Maize GxE Prediction Competition (maizegxeprediction.org) pays $4,000 plus
travel. Its 2026 edition opens 2026-11-16. MV2 intends to enter as Munim, Inc., with models built by AI
agents in his name. Before building anything clever, he needs an honest floor: what do simple, open
genomic baselines score on the competition's own metric? This job sets that floor on three held-out
years.

## Data

G2F 2024 competition release, CyVerse DOI 10.25739/78mn-4394 (PDDL): training traits 2014-2023,
genotypes for 2014-2025 hybrids (numerical file; VCF as fallback), the 2024 submission template and the
organisers' released 2024 observed values (7_Testing_Observed_Values.csv).

## Metric

Competition metric: Pearson r between predicted and observed yield inside each environment, averaged
over environments. A model that predicts a constant inside an environment scores 0 there.
Environments with fewer than 3 observed rows are skipped.

## Folds

- 2022: train 2014-2021, test 2022 plots (Env x Hybrid mean yield).
- 2023: train 2014-2022, test 2023.
- 2024: train 2014-2023, test = template rows with a released observed value.

## Models (all fixed in code before the run; nothing tuned on test years)

On yield z-scored within each training environment:
- M0: the hybrid's mean (0 if never tested).
- M1: ridge regression of hybrid means on standardised markers; lambda chosen by 5-fold CV over
  training hybrids from {1e1, ..., 1e6}.
- M2: M1 + n/(n+5) x (hybrid mean - M1), n = training plots of the hybrid.
- M3: M2 + c/(c+10) x the hybrid's mean residual at the same location (c = its plots there).

## Predictions

- P1: M1 on 2024 scores a mean within-environment r in [0.10, 0.45]; point estimate 0.28.
- P2: M2 >= M1 on 2024, and on at least 2 of the 3 folds.
- P3: M3 - M2 on 2024 lies in [-0.02, +0.05]: location-specific hybrid effects add little, because
  most test hybrids have few or no plots at the same location.
- P4: share of 2024 test rows whose hybrid has training plots lies in [0.20, 0.90]; point 0.50.
- P5: the best model's score varies by at least 0.05 between the three folds (max - min).

## What would count as new

Published papers describe the 2022 and 2024 data and the 2022 results; the 2024 paper does not
report a baseline score. To our knowledge no open, pre-registered baseline ladder scored on the released
2024 answers exists. This is a benchmark, not a new method.

## Limits

- Additive marker effects only; no weather, soil or environmental covariates (that is the next step).
- Hybrids are genotyped by projected calls; parents are not included.
- The 2022 and 2023 folds score all reported plots of that year, not the competition's original test
  set, so they are only roughly comparable to past leaderboards.
