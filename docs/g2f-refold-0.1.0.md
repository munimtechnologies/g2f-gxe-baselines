# g2f-refold 0.1.0: pre-registration (re-choosing the mix weights on any release)

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed it yet. Text CC BY 4.0; code
Apache-2.0. Not agronomic advice.

PREREG-MARKER: g2f-refold-0.1.0

Written 2026-11-10 (about 15:30 UTC), before the sealed job `g2f-refold-dry-v1` runs. The job waits
until this file is public on GitHub, then downloads and runs the published code. Nothing below has
been computed with `g2f_refold.py` yet.

## Why

g2f-switch 0.1.0 (graded, 6 of 6 held) made a mix of M4 and the kernel model ("full") the default 2026
entry: a * z(full) + (1 - a) * z(M4) on new hybrids with one parent seen, b * z(full) + (1 - b) * z(M4)
on every other row, with z taken inside each environment. Its weights a = b = 0.5 were chosen on 2022
and checked on 2024. Both seasons are written into `g2f_switch.py`, so the study cannot be rerun on the
2026 release, which g2f-switch's result and g2f-predict 0.1.0 both promised before any upload.

`g2f_refold.py choose` does the same choice on any release:

1. It finds the release files by role and never downloads (g2f_predict.release). The test season is
   the year in the template's file name.
2. It types the test season with g2f_entry.decide (threshold 0.70) from the share of template pairs
   whose hybrid was grown in the last training season. Below 0.70 it is "new_hybrids", otherwise
   "repeated_hybrids".
3. It holds out each of the `--folds` most recent training seasons, default 2, which are the folds
   `g2f_refmodel.R <release> <out> all` writes. Each fold is typed the same way, against the season
   before it.
4. For each hold-out season that has full predictions (`--full-dir`, i.e. g2f_refmodel.R's `preds/`,
   or `--full SEASON=PATH`), it rebuilds M4 trained on earlier seasons only and scores the 5 x 5
   (a, b) grid.
5. It chooses (a, b) on the mean grid over the hold-out seasons of the test season's type. Ties go to
   the smaller a + b, then the smaller a. If no fold has the same type, it uses the most recent fold
   with full predictions and reports `matched: false`.

## Dry run on the 2024 release (graded by `grade_expect`, expectations in `data/g2f-refold-expect-2024.json`)

Inputs: the G2F 2024 release volume, and the committed kernel-model predictions
`results/g2f_refmodel_2022_predictions.csv` and `results/g2f_refmodel_2023_predictions.csv`
(g2f-refmodel 0.1.0). The fold count is the default 2.

- **D1:** test season 2024, typed "new_hybrids" (6.8% of pairs grown in 2023, g2f-entry 0.1.0). The two
  hold-out seasons are 2023 ("repeated_hybrids") and 2022 ("new_hybrids").
- **D2:** it chooses on [2022], with matched = true.
- **D3:** on the 2022 fold, M4 scores 0.3262 and full 0.2987, each +- 0.0005 (g2f-switch 0.1.0 R1).
- **D4:** the entry is a0.50_b0.50, scoring 0.3617 +- 0.0005 on 2022, which reproduces g2f-switch
  0.1.0's choice through the new, season-free code path.
- **D5 (a prediction, not a reproduction):** on the 2023 fold, M4 scores higher than full. The
  g2f-refmodel 0.1.0 result reported 0.435 vs 0.389, but the 2023 M4 here is rebuilt by this code.
- **D6 (a prediction):** on the 2023 fold, where about 99% of pairs are hybrids grown before, the chosen
  b is at most 0.5.

Also reported, not graded: both folds' full grids, the scores by hybrid category, and fit details.

## What follows

- If D1-D4 hold, `g2f_refold.py` is how the 2026 weights are chosen. Run order on the 2026 release:
  census; `Rscript g2f_refmodel.R <release> <out> all 4` (0.2.1 adds the hold-out count; four
  seasons, 2025 down to 2022); `python g2f_refold.py choose --data-dir <release> --full-dir
  <out>/preds --folds 4`; then `g2f_predict.py predict --full <out>/preds/2026.csv --a <a> --b <b>`.
  With four folds, both earlier new-hybrid seasons (expected: 2024 and 2022) are averaged, if the
  2025 release repeats 2024's hybrids as G2F's two-season design implies. On today's numbers that mean
  grid peaks at a = 0.75, b = 0.5 (g2f-switch two-fold mean 0.4061). That figure is a guide, not a
  prediction: the 2026 release's 2024 fold is scored on its own rows.
- If D1 or D2 fails, the season typing is wrong and is fixed first. If D3 or D4 fails, no 2026
  weights come from this code until the difference from g2f-switch is found.
- D5 and D6 are reported either way and do not block the tool.
- Uploads go through Sheehan Munim's EvalAI team account, and only when he says so.

## Limits

- One graded fold of each type exists on the 2024 release. This checks plumbing and reproduction,
  not that the chosen weights will be best on 2026.
- The 2026 metric is not known yet. Weights are chosen on mean within-environment r, the 2024 metric.

MV2, Munim, Inc., mv2@munimtech.com
