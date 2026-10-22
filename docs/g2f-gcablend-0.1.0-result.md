# g2f-gcablend 0.1.0: result

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed the numbers yet. Text CC BY 4.0;
code Apache-2.0.

This grades the pre-registration [`g2f-gcablend-0.1.0-prereg.md`](g2f-gcablend-0.1.0-prereg.md),
committed to this repository (release v0.7.0) before the job `g2f-gcablend-v1` read any yield data. The
job ran in a sealed container on 2026-10-22 (13:29-13:36 UTC, 390 s). It confirmed the pre-registration
was public (first attempt), passed its offline tests, then fitted the blend grid and scored all three
folds. Outputs: [`results/g2f_gcablend.json`](../results/g2f_gcablend.json) and
[`results/g2f_gcablend_2024_env_r.csv`](../results/g2f_gcablend_2024_env_r.csv).

## Checks

- **Reproduction gate passed.** On the 2024 answers, the blend weight w = 0 scores 0.2802 (= M2) and
  w = 0.5 scores 0.3018 (= M4), the same as earlier studies, so the grid is anchored to the published
  reference points.

## Selection and scores (mean within-environment Pearson r)

The blend weight w sets how much parent general combining ability (G1) is mixed into the marker ridge
(M1) before shrinking to each hybrid's own training mean: w = 0 is M2, w = 0.5 is the adopted M4. The
full grid, all-rows within-environment r, by fold:

| w | 0 (= M2) | 0.25 | 0.5 (= M4) | 0.75 | 1.0 |
|---|---|---|---|---|---|
| 2022 (28 envs, training) | 0.3257 | **0.3304** | 0.3262 | 0.3036 | 0.2551 |
| 2023 (27 envs, training) | **0.4371** | 0.4363 | 0.4354 | 0.4342 | 0.4329 |
| mean of 2022, 2023 (selection) | 0.3814 | **0.3834** | 0.3808 | 0.3689 | 0.3440 |
| 2024 (22 envs, forward test) | 0.2802 | 0.2928 | 0.3018 | **0.3033** | 0.2930 |

The selection rule maximises the mean of the two training folds. 2022 peaks at w = 0.25 and 2023 peaks at
w = 0 (parent GCA barely helps 2022 and slightly hurts 2023), so their mean is highest at **w\* = 0.25**.
Applied forward to 2024, w\* = 0.25 scores **0.2928**, which is **0.009 below** the a-priori default
w = 0.5 (0.3018).

On 2024 the grid keeps rising past the default: it peaks at w = 0.75 (0.3033) and only falls at w = 1.0.
So the forward season actually rewards **more** parent-GCA weight than the training years select, and the
untuned a-priori 0.5 lands within 0.0015 of the 2024 oracle optimum, while the tuned 0.25 gives up most
of parent GCA's 2024 benefit.

## Predictions, graded

All three predictions held; the hypothesis failed.

- **P1 held** (point 0.70). The training-selected weight is **w\* = 0.25 (<= 0.25)**: the two training
  years do not favour a GCA weight above the a-priori default.
- **P2 held** (point 0.72). On the 2024 answers, M4 at w\* scores **0.009 below** M4 at the fixed 0.5
  (bar: no more than +0.002 above) -- tuning the weight on past years does not beat the a-priori 0.5
  forward; it loses.
- **P3 held** (point 0.65). On 2024 the grid is **non-decreasing from w = 0 to w = 0.5**
  (0.2802 <= 0.2928 <= 0.3018): the forward season rewards more GCA weight than the training years select.
- **H1 failed** (we gave it about 12%). w\* differs from 0.5, but M4 at w\* is **0.009 below** M4 at 0.5
  on 2024 (bar: at least +0.005 above), so the tuned weight is not adopted.

## What this shows

1. **Tuning the blend weight on the training years transfers worse than not tuning it.** The a-priori
   0.5 was never fit, yet it is within 0.0015 of the best weight on the 2024 hold-out (w = 0.75, 0.3033).
   The data-driven choice from 2022 and 2023, w\* = 0.25, instead scores 0.009 lower than that untuned
   0.5. Single-hyperparameter tuning of this G×E blend does not generalise across seasons, because the
   component it controls -- parent GCA -- is strongly year-specific (large on 2024, near zero on 2022,
   slightly negative on 2023), so the training years point the weight in the wrong direction for the
   forward season.
2. **The blend weight matters only for new hybrids.** Splitting the 2024 grid by whether a hybrid was
   grown before, the seen hybrids (12% of rows) score 0.594 at every weight from 0 to 1.0 -- essentially
   flat, because their own-mean shrinkage dominates. The new hybrids (88%) rise from 0.101 at w = 0 to a
   peak of 0.131 at w = 0.75, then fall. All of the weight sensitivity, and all of parent GCA's value,
   lives in the new hybrids that have no yield history of their own.
3. **This closes the within-2024 model-tuning line.** After four environment-specific add-ons that each
   gained nothing forward, this study looked at the entry model itself and found its one free
   a-priori constant, the 0.5 blend, is already near-optimal on the forward season and should not be
   retuned on the training years.

Blend-weight tuning is routine. What is new here is the open, pre-registered forward test on the released
G2F 2024 answers, against the within-environment metric, showing that an a-priori 0.5 beats the weight a
grid search selects on the two prior seasons.

## Decision (fixed in advance)

**H1 failed, so MV2's 2026 G2F entry keeps M4 at the a-priori 0.5 blend** (0.302 on the 2024 answers).
This study closes the within-2024 model-tuning line: there is no further question to ask of the 2024
answers that would not be post-hoc. The next study waits for the 2026 training release, which opens
2026-11-16 as a new data set; the adopted model (M4) will be rerun and re-registered on it before the
competition.

## Limits

- Two training folds and a five-point weight grid; the selection uses only the mean of 2022 and 2023, so
  a weight best on their mean need not be best on either alone, and the grid is coarse (the 2024 peak at
  w = 0.75 is not resolved finely).
- Only the single scalar blend weight varies; the marker ridge and parent-GCA models, their lambdas and
  the shrinkage constant are unchanged, and no per-hybrid or per-environment weight is tested.
- The finding is about these three seasons of G2F data and the within-environment metric, not about blend
  weights in general.
