# g2f-switch 0.1.0: pre-registration (M4 and the kernel model, mixed by kind of hybrid)

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed it yet. Text CC BY 4.0; code
Apache-2.0.

PREREG-MARKER: g2f-switch-0.1.0

Written 2026-11-09 (about 22:45 UTC), before the sealed job `g2f-switch-v1` runs. The job waits until
this file is public on GitHub, then downloads and runs the published code. Nothing below has been
computed: per-row M4 predictions for the 2022 fold were never committed, so no mix of the two models
has been scored on any fold.

## Why

Two models in this repository each win somewhere (see [g2f-refmodel 0.1.1](g2f-refmodel-0.1.1-result.md)):

| Fold | M4 all rows | full all rows | M4 new_one | full new_one | M4 new_both | full new_both |
|---|---|---|---|---|---|---|
| 2022 | **0.326** | 0.299 | 0.144 | **0.167** | **0.430** | 0.304 |
| 2024 | 0.302 | **0.442** | 0.107 | **0.390** | 0.123 | **0.290** |

`full` (MV2's re-implementation of the organisers' Gaussian-kernel model) ranks new hybrids with one
parent seen better in both seasons. M4 (marker ridge plus parent combining ability, shrunk to the
hybrid's own past mean) is better on 2022 overall. The 0.1.1 rule says to test a switch, with weights
chosen on 2022 only and 2024 as the forward check. 2022 and 2024 are both even seasons with new hybrid
sets, like the 2026 test season.

## Method (`g2f_switch.py grade`)

- **M4** is rebuilt with the published `g2f_parentgca.py` 0.1.0 on the 2022 fold (train 2014-2021)
  and the 2024 fold (train 2014-2023; template rows, released answers). **full** is read from the
  committed `results/g2f_refmodel_<fold>_predictions.csv`.
- Each model's predictions are z-scored inside each environment over every predicted row. A missing
  prediction counts as 0.
- Each row gets the category used in 0.1.1 (seen, new_both, new_one, new_none). The mix is
  `a*z(full) + (1-a)*z(M4)` on new_one rows and `b*z(full) + (1-b)*z(M4)` on all other rows, with
  a and b each in {0, 0.25, 0.5, 0.75, 1} (25 mixes). (0, 0) is M4 and (1, 1) is full.
- Score: mean within-environment Pearson r (at least 3 observed rows; constant prediction = 0).
- **(a\*, b\*) = the best mix on 2022.** Ties go to the smaller a + b, then the smaller a.

## Gate and predictions (graded by the job's own `grade()`)

- **R1 (reproduction):** M4 within 0.005 of its published 0.3262 (2022) and 0.3018 (2024); full
  within 0.0005 of 0.2987 and 0.4416. If R1 fails, everything below is reported but flagged.
- **Q1:** a\* >= 0.5 (full gets at least half the weight on new_one rows). Confidence 0.6.
- **Q2:** b\* <= 0.5 (M4 gets at least half the weight elsewhere). Confidence 0.6.
- **Q3:** on 2022, the chosen mix beats both M4 and full by at least 0.005. Confidence 0.55.
- **Q4 (forward check):** on 2024, the chosen mix scores above M4 (0.3018). Confidence 0.8.
- **Q5:** on 2024, the chosen mix scores below full (0.4416). Confidence 0.65.

Also reported, not graded: all 25 mixes on both folds, their two-fold mean, the best 2024 mix in
hindsight, and each model's and the chosen mix's score by category.

## What follows (fixed now)

- **Default for the 2026 entry** (if the 2026 metric is again mean within-environment r): the chosen
  mix if Q4 holds, otherwise M4. The job writes this as `entry_default`.
- This replaces "M4 for now" in the README. The study is rerun on the 2026 training release before
  any upload, adding the 2025 season as a report-only fold. If that release changes the 2022 or 2024
  folds, the rerun's numbers are used.
- If the 2026 template has many new hybrids with neither parent seen (at least 20%, g2f-cathistory
  A5), those rows are not covered by this study. Their model is chosen on the 2016 season, the only
  past season with such rows (g2f-cathistory 0.1.0), and on a parents-held-out fold.
- `g2f_switch.py apply` writes the chosen mix for any table of M4 and full predictions. A real upload
  then goes through `g2f_entry.py mgha` and `validate`.

## Limits

- Two folds and 25 mixes, so the 2022 choice can overfit. That is why 2024 is kept as the forward check.
- z-scoring puts both models on one scale, but it cannot fix a wrong level between categories inside
  an environment. Both models get that level wrong, in opposite directions (0.1.1 result).
- No person has reviewed this. Nothing here is agronomic advice.

MV2, Munim, Inc., mv2@munimtech.com
