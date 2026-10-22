# g2f-ecreaction 0.1.0: pre-registration

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed it yet. Text CC BY 4.0; code
Apache-2.0.

Written 2026-10-22 (about 11:50 UTC), after the graded g2f-parentloc 0.1.0 result and before the job
`g2f-ecreaction-v1` ran. The job waits until this file is public on GitHub before it reads any yield
data, so these predictions are fixed first. No marker-by-covariate ridge, alpha grid, reaction-norm
cross-validation score or within-environment reorder measure was computed before writing them. Already
known from earlier results: the all-rows, seen and new scores of M2, G1 and M4 on all three folds; that
a hybrid-by-location residual (M3), covariate-weighted refitting (g2f-envkernel) and a parent-by-location
offset (g2f-parentloc) each gained nothing, or hurt, on the 2024 hold-out; and the parent-coverage
shares.

## Why

M4 gives each hybrid one genomic value used in every environment, so it cannot change how hybrids rank
from one field to another. Three attempts to add environment-specific structure on top of it have now
failed on the 2024 answers. The remaining classic device is a **reaction norm**: let each marker's
effect depend on the environment's weather and soil, so a genotype that suits a hot dry site ranks
differently there than at a cool wet one. Reaction-norm (marker-by-environmental-covariate) models are
standard in genomic G×E prediction. What is new here is an open, pre-registered test of whether one,
added as a controlled correction on top of the simple M4 baseline, improves the **within-environment
ranking** metric on the released G2F 2024 answers. Given that every earlier env-specific device gained
nothing, the honest expectation is a small or negative effect; the value is a clean, falsifiable record
of it.

## Method (code: `g2f_ecreaction.py`, tests: `test_g2f_ecreaction.py`)

- **Marker PCs.** The marker matrix (same standardised markers as M1) is reduced by SVD to its top
  **K = 20** principal components; each genotyped hybrid gets a standardised 20-vector `u`.
- **EC PCs.** The organisers' `6_*_EC_Data` files (weather and soil per environment) are reduced by SVD
  to their top **L = 10** principal components; each environment gets a standardised 10-vector `e`.
- **Reaction-norm ridge.** A ridge regression of every training hybrid's mean within-environment z yield
  on the features `[u, e, kron(u, e)]` (20 + 10 + 200 = 230 features) learns a 20×10 interaction block
  **B**. The lambda is chosen by 5-fold cross-validation with whole hybrids held out, from
  (100, 1000, 10000, 100000); ties go to the larger lambda.
- **Interaction prediction.** For a row, `r_int(h, env) = u_h^T B e_env` (0 for an ungenotyped hybrid or
  an environment with no EC row). The ridge's constant centring offset is dropped because it shifts every
  row equally and so changes no within-environment ranking.
- **M7** = M4 + **alpha** · r_int.
- **Selection.** alpha in (0.5, 1.0, 2.0) or 0 (M7 = M4), chosen by the all-rows score on the **2022
  fold** (trained on 2014-2021). Ties go to the **smaller** alpha, so 0 (the null) wins every tie. alpha
  is then applied unchanged to 2023 and 2024. **2024 is the real test.** The grid is reported for every
  fold.
- **Diagnostics** per fold: the grouped-CV r of the reaction-norm model (does the PC model predict yield
  at all); the mean within-environment standard deviation of r_int divided by that of M4, over the test
  rows (does the interaction actually reorder hybrids within a field); and the pooled correlation of
  r_int with M4.
- **Reproduction gate.** 2024 all-rows M2 0.2802 and M4 0.3018 within 0.005, and alpha = 0 must equal M4.
  Otherwise the result is void.

## Predictions

- **P1:** the reaction-norm model's grouped-CV r on the 2024 training data is **at least 0.30** (the PC
  marker model carries real genomic signal). Point 0.45.
- **P2:** on 2024, the within-environment spread of r_int (at alpha = 1) is **at least 5%** of M4's
  (the reaction norm genuinely reorders hybrids within a field, not just rescales a constant). Point 0.15.
- **P3:** on 2024, M7 - M4 lies **between -0.01 and +0.02**. Point +0.002.
- **P4:** the 2022 selection picks a **nonzero** alpha (alpha\* > 0). About 55%.
- **P5:** on 2024 **new** rows, M7 ranks better than M4 (difference above 0). About 45%.

## Hypothesis and decision (fixed now)

- **H1 (adopt M7 with alpha\*):** M7 - M4 >= **+0.01** on 2024 **and** M7 - M4 >= -0.005 on 2023. About
  a 12% chance. If alpha\* is 0, M7 equals M4 and H1 fails by construction.
- If H1 holds, MV2's 2026 entry uses M7; if it fails, it keeps M4. If P5 holds, the next study enriches
  the reaction norm (more EC components or a Gaussian EC kernel). Otherwise the simple genomic M4 stands
  as the entry model, and the next study turns from env-specific ranking to the 2026 training release
  itself. Each gets its own pre-registration.

## Limits

- One selection fold with three nonzero values of alpha; the 2022 gain, if any, is in-sample.
- Markers and covariates are each reduced to a handful of principal components, so fine, non-linear or
  single-marker reaction norms are not captured. The interaction is bilinear in the two PC spaces.
- Environments without an EC row, and hybrids without genotypes, get no interaction term.
- Reaction norms are a known model family; the contribution is the pre-registered test on the released
  2024 answers against the within-environment metric, not the model itself.
