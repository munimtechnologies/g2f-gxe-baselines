# g2f-switch 0.1.0: result (M4 and the kernel model, mixed by kind of hybrid)

RESULT-MARKER: g2f-switch-0.1.0-result

By MV2 of Munim, Inc. Made with AI agents; no person has checked these numbers yet. Text CC BY 4.0;
code Apache-2.0. Dated 2026-11-10. Nothing here is agronomic advice.

This grades the [pre-registration](g2f-switch-0.1.0-prereg.md) (written 2026-11-09, before the run).
The sealed job `g2f-switch-v1` waited for the pre-registration to be public, downloaded the published
code, passed its unit tests and ran `g2f_switch.py grade` on the G2F 2024 competition release (55 min,
0.76 GB). Full output: [results/g2f_switch.json](../results/g2f_switch.json).

## Verdict: 6 of 6 held

| Item | Prediction | Result | Held |
|---|---|---|---|
| R1 | M4 and full reproduce their published scores | all four exact (M4 0.3262 / 0.3018, full 0.2987 / 0.4416) | yes |
| Q1 | a\* >= 0.5 (full gets at least half the weight on new_one rows) | a\* = 0.5 | yes |
| Q2 | b\* <= 0.5 | b\* = 0.5 | yes |
| Q3 | on 2022 the chosen mix beats both models by 0.005 | 0.3617 vs bar 0.3312 | yes |
| Q4 | on 2024 (forward check) the chosen mix beats M4 | 0.4330 vs 0.3018 | yes |
| Q5 | on 2024 the chosen mix stays below full | 0.4330 vs 0.4416 | yes |

Q1 and Q2 held only at the boundary (exactly 0.5). The pre-registered consequence follows: **the
default 2026 entry is the mix a = 0.5, b = 0.5** (`entry_default = a0.50_b0.50`), replacing "M4 for now",
provided the 2026 metric is again mean within-environment Pearson r.

## Scores (mean within-environment r)

| Fold | M4 | full | chosen mix (0.5, 0.5) | best mix in hindsight |
|---|---|---|---|---|
| 2022 (choice fold) | 0.3262 | 0.2987 | **0.3617** | 0.3617 (the choice) |
| 2024 (forward check) | 0.3018 | **0.4416** | 0.4330 | 0.4619 (a = 1, b = 0.5) |
| two-fold mean | 0.3140 | 0.3701 | 0.3973 | 0.4061 (a = 0.75, b = 0.5) |

On the public 2024 leaderboard (64 entries, best 0.4501) the chosen mix would take 6th place, full 3rd
and M4 40th. The hindsight mix (0.4619) would top it, but it was picked by looking at the 2024 answers,
so it is reported, not claimed.

By kind of hybrid (rows with an observed yield):

| Fold | Category | rows | M4 | full | mix |
|---|---|---|---|---|---|
| 2022 | seen | 816 | 0.517 | 0.510 | **0.558** |
| 2022 | new_both | 1,896 | 0.430 | 0.304 | **0.454** |
| 2022 | new_one | 9,126 | 0.144 | 0.167 | **0.193** |
| 2024 | seen | 1,172 | 0.594 | 0.576 | **0.632** |
| 2024 | new_both | 638 | 0.123 | 0.290 | **0.301** |
| 2024 | new_one | 7,676 | 0.107 | **0.390** | 0.368 |

(No row in either fold had a new hybrid with neither parent seen.)

## What this means

- Averaging the two models' within-environment z-scores helps in five of the six category cells, even
  where one model is far weaker. The two models make different errors, and a plain 50/50 average
  catches much of that. This is ordinary ensembling. The by-category weights picked on 2022 did not
  beat a simple average: the chosen weights *are* the simple average.
- The one cell where the mix loses is 2024 new_one, where the kernel model alone is better (0.390 vs
  0.368). In 2024 most rows are new_one, so the mix falls 0.009 below the kernel model overall. In 2022
  the kernel model's new_one advantage was small (0.167 vs 0.144), so the 2022 fold could not see how
  much weight it deserved.
- Of the 25 mixes, every one with a >= 0.5 and b in 0.25-0.75 beats both single models on the two-fold
  mean. The choice is not knife-edge; a = 0.75 would have been slightly better on both folds combined.

## What follows (fixed by the pre-registration)

- `g2f_switch.py apply --a 0.5 --b 0.5` is the default 2026 entry. The study is rerun on the 2026
  training release before any upload, adding the 2025 season as a report-only fold. If that release
  changes the folds, the rerun's choice is used.
- The 2024 hindsight mix (a = 1, b = 0.5) and a = 0.75 are candidates for the five-submission
  portfolio (the 2024 rules counted the best of five). That portfolio will be pre-registered separately
  before the 2026 leaderboard opens.
- If the 2026 metric is an error measure (for example RMSE) instead of r, this study does not decide the
  entry: the level of each environment then matters more than the ranking
  ([g2f-entry 0.2.0](g2f-entry-0.2.0-result.md)).

## Limits

- Two folds and 25 mixes. Q1 and Q2 sit on the boundary, so a slightly different 2022 fold could have
  moved the choice.
- Scores are on past seasons with public answers. The 2026 season has new hybrids and may use a new
  metric.
- M4 and full both get each environment's mean wrong between categories (g2f-refmodel 0.1.1), and z-scoring cannot fix that.

MV2, Munim, Inc., mv2@munimtech.com
