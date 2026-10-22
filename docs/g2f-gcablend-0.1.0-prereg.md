# g2f-gcablend 0.1.0: pre-registration

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed it yet. Text CC BY 4.0; code
Apache-2.0.

Written 2026-10-22 (about 13:15 UTC), after the graded g2f-ecreaction 0.1.0 result and before the job
`g2f-gcablend-v1` ran. The job waits until this file is public on GitHub before it reads any yield data,
so these predictions are fixed first. No weight grid, selection or 2024 score at any weight other than
the two already-published reference points was computed before writing them. Already known from earlier
results: the all-rows scores of M2 (= M4 at weight 0) and M4 (at weight 0.5) on all three folds -- 2022
0.3257 / 0.3262, 2023 0.4371 / 0.4354, 2024 0.2802 / 0.3018 -- and that parent GCA, the component M4
adds, helps the 2024 hold-out (+0.0216) but barely moves 2022 (+0.0005) and slightly hurts 2023
(-0.0017). The scores at weights 0.25, 0.75 and 1.0, and which weight the training years select, are
**not** known.

## Why

Every earlier study added environment-specific structure on top of M4 and gained nothing forward (four
in a row). This study does the opposite: it looks at M4 itself, the entry model. M4 blends the marker
ridge M1 with parent general combining ability G1 at a weight fixed **a priori at 0.5**, then shrinks
toward each hybrid's own training mean. That 0.5 was never tuned. The natural question for the entry is
whether tuning it would help. But parent GCA's value is strongly year-specific -- large on 2024, near
zero on 2022, slightly negative on 2023 -- so tuning the weight on the two available training years
(2022 and 2023) could pick a weight that discards most of the 2024 benefit. This is a clean,
pre-registered test of whether single-hyperparameter tuning of a G×E blend transfers across seasons, or
whether an untuned a-priori weight is the safer forward choice. Weight tuning is routine; what is new is
the open, pre-registered forward test on the released G2F 2024 answers against the within-environment
metric.

## Method (code: `g2f_gcablend.py`, tests: `test_g2f_gcablend.py`)

- **Grid.** The blend weight w is varied over **(0, 0.25, 0.5, 0.75, 1.0)**. For each fold, M1 (marker
  ridge) and G1 (parent GCA) are fitted **once**; M4 at weight w is `(1-w)*M1 + w*G1`, then shrunk
  toward the hybrid's own mean by `n/(n+5)` for seen hybrids, exactly as g2f_parentgca builds M4. w = 0
  reproduces M2; w = 0.5 reproduces the adopted M4. Everything else (the ridge lambdas, the GCA lambdas,
  the shrinkage constant) is unchanged from the published models.
- **Folds.** 2022 and 2023 (each trained on earlier years only) and the organisers' released 2024
  answers (trained on 2014-2023). The full grid is reported for every fold; 2024 is also split into
  previously grown ("seen") and new hybrids.
- **Selection.** The chosen weight **w\*** maximises the **mean all-rows within-environment r over the
  two training folds (2022 and 2023)**. Ties go to the weight nearest the a-priori default 0.5, then to
  the larger weight. w\* is then applied unchanged to 2024. **2024 is the real test.**
- **Reproduction gate.** The 2024 grid at w = 0 must be within 0.005 of 0.2802 (M2) and at w = 0.5
  within 0.005 of 0.3018 (M4). Otherwise the result is void.

## Predictions

- **P1:** the training-selected weight is **w\* <= 0.25** -- the two training years do not favour a GCA
  weight above the a-priori default, because parent GCA barely helps 2022 and hurts 2023. Point 0.70.
- **P2:** on the 2024 answers, M4 at w\* scores **no more than +0.002 above** M4 at the fixed default
  0.5 -- tuning the weight on past years does not beat the a-priori 0.5 forward. Point 0.72.
- **P3:** on 2024, the grid is **non-decreasing from w = 0 to w = 0.5** (M4 at 0.5 >= at 0.25 >= at 0),
  so the forward season rewards more GCA weight than the training years select. Point 0.65.

## Hypothesis and decision (fixed now)

- **H1 (adopt the tuned weight):** w\* differs from 0.5 **and** M4 at w\* scores **at least +0.005
  above** M4 at 0.5 on 2024. About a 12% chance. The honest expectation, given the year-specific value
  of parent GCA, is that H1 fails.
- If H1 holds, MV2's 2026 entry uses the tuned weight; if it fails, it keeps the a-priori 0.5. Either
  way, this closes the within-2024 model-tuning line for the entry: the next study waits for the 2026
  training release (opens 2026-11-16, a new data set), on which the adopted model is rerun before the
  competition. Each gets its own pre-registration.

## Limits

- Two training folds and a five-point weight grid; the selection uses only 2022 and 2023, so a weight
  that is best on their mean need not be best on either alone, and the grid is coarse.
- The marker ridge and GCA models are unchanged; only their blend weight varies. A per-hybrid or
  per-environment weight is not tested.
- The finding, whichever way it falls, is about these three seasons of G2F data and the
  within-environment metric, not about blend weights in general.
