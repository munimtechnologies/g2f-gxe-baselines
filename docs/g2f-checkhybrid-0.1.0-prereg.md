# g2f-checkhybrid 0.1.0: pre-registration

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed it yet. Text CC BY 4.0; code
Apache-2.0.

Written 2026-10-22 (about 04:00 UTC), after the graded g2f-baseline 0.1.0 and g2f-envkernel 0.1.0
results and before the job `g2f-checkhybrid-v1` ran. The job waits until this file is public on GitHub
before it reads any observed-yield column, so these predictions are fixed first.

## Why

g2f-baseline 0.1.0 reported, on the organisers' released 2024 answers, a mean within-environment
Pearson r of 0.235 for M0 (predict each hybrid's own historical mean), 0.239 for M1 (a marker ridge)
and 0.280 for M2 (M1 shrunk toward the hybrid's own mean). A puzzle sits inside those numbers: only
**12.2%** of the 2024 scored rows are hybrids that were grown in 2014-2023 ("seen"); the other 87.8%
are new. M0 is blind to every new hybrid (it can only return the global mean, a constant), yet M0 still
reaches 0.235 and even beats M1 in several environments. This study decomposes the 2024 score by
whether each hybrid was seen before, to find where each model's ranking skill actually comes from and
to decide which GxE model to build next for MV2's 2026 entry.

## Method

- **Input.** The committed, immutable per-row prediction table of the baseline run,
  `results/g2f_2024_predictions.csv` at tag v0.1.0 (columns `Env, Hybrid, obs, M0, M1, M2, M3`). No new
  model is fit. The observed-yield column `obs` is the only data read, and only after this file is
  public.
- **Seen vs new.** A row is **seen** if its M0 prediction is non-zero and **new** if M0 is exactly 0.0.
  This is exact by construction of the baseline: M0 is the hybrid's own z-scored training mean, and an
  unseen hybrid is given the global z-mean, which is 0. As a built-in check, for every new row M2 must
  equal M1 (M2 shrinks toward a hybrid mean that does not exist for a new hybrid), and the run reports
  the count of any violations; a non-zero count voids the split.
- **Scoring.** As in 0.1.0: mean within-environment Pearson r, over rows with a finite `obs`, skipping
  any (environment, subset) with fewer than 3 such rows or with no variance in `obs` or in the model's
  prediction. Means are taken over the environments where that model's r is defined. For comparisons
  between two models (P4, H1) the mean is taken over the environments where **both** are defined.
- **Reproduction check.** The run recomputes each model's all-rows mean within-environment r and must
  reproduce the baseline's 22-environment scores (M0 0.235, M1 0.239, M2 0.280) within 0.005; otherwise
  the result is void.

## Predictions

- **P1:** the seen subset has a defined within-environment r in at least **15** of the ~22 scored
  environments (i.e. >= 3 seen rows with variance).
- **P2:** mean M0 within-environment r on the **seen** subset exceeds **0.40** (well above its all-rows
  0.235): M0's ranking signal is concentrated in, and diluted across, the seen minority. Point 0.50.
- **P3:** mean M2 within-environment r on the **new** subset exceeds **0.10**: the marker ridge ranks
  never-before-grown hybrids above chance. Point 0.20.
- **P4:** on environments where both are defined on the seen subset, mean M2 and mean M0 differ by less
  than **0.10** in within-environment r: for previously grown hybrids their own history is nearly as
  informative as the full genomic model. Point M2 - M0 ~ +0.03.

## Hypothesis

- **H1:** on the seen subset, M2 beats M1 (mean M2 r > mean M1 r over environments where both are
  defined): a hybrid's own history adds ranking signal beyond markers alone for previously grown
  hybrids. About a 65% chance.

Note (not a prediction): M0 on the new subset is undefined everywhere by construction (a constant
prediction has no variance), which is itself the point - M0 carries no information about unseen hybrids.

## Decision rule (fixed now)

- If **P3 holds** (markers rank new hybrids above chance, mean M2 new r > 0.10), the next G2F model
  strengthens the genomic signal for unseen hybrids: parent/tester general-combining-ability from the
  hybrid pedigree names, or a marker-by-covariate reaction-norm model.
- If **P3 fails**, ranking new hybrids from these markers is near-hopeless, and the 2026 entry instead
  models the seen minority plus the environment-level mean, moving effort off per-hybrid genomic GxE.

## Limits

- The split rests on the baseline's committed predictions; it inherits their modelling choices.
- "Seen" means grown anywhere in 2014-2023, not necessarily at the same location.
- The 2024 answers are one season; the decomposition is not a significance test.
