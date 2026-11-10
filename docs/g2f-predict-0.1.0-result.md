# g2f-predict 0.1.0: result (release-day entry builder, dry run on the 2024 release)

RESULT-MARKER: g2f-predict-0.1.0-result

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed it yet. Text CC BY 4.0; code
Apache-2.0. Not agronomic advice.

Graded 2026-11-10 against [the pre-registration](g2f-predict-0.1.0.md). The sealed job
`g2f-predict-dry-v1` waited for that file to be public, downloaded the published code, passed its unit
tests (`test_g2f_predict`), then ran `plan` and `predict` on the G2F 2024 release volume. Its
`--full` input was the committed `results/g2f_refmodel_2024_predictions.csv`. It took 19 minutes on 1
CPU and peaked at 0.81 GB. Outputs: [`results/g2f_predict_2024.json`](../results/g2f_predict_2024.json)
and [`results/g2f_predict_plan.json`](../results/g2f_predict_plan.json). The three upload files it
wrote (M4, full, mix) are not committed, because they are files for the 2024 leaderboard, not results.

## Grades: all 5 held

| Item | Pre-registered | Result | Held |
|---|---|---|---|
| P1 | trait, template, genotype and observed files found; test season 2024 | all four roles found; season 2024 (from `1_Submission_Template_2024.csv`) | yes |
| P2 | M4 scores 0.3018 +- 0.0005 | 0.3018 | yes |
| P3 | mix (a = b = 0.5) scores 0.4330 +- 0.0005 | 0.4330 | yes |
| P4 | M4, full and mix Mg/ha files validate with every row; M4 and mix need no filled rows | 10,057 of 10,057 rows each; 0 filled in all three | yes |
| P5 | written M4 and mix files score within 0.0002 of their unscaled columns, over 22 environments | M4 0.3018 vs 0.3018, mix 0.4330 vs 0.4330, 22 environments each | yes |

## Reported, not graded

- **Plan:** 10,057 template pairs in 23 environments; training seasons 2014-2023 (164,921 rows with a
  yield). 12.2% of pairs have a hybrid grown before, 6.8% one grown in 2023, so the season is called a
  new-hybrid season, as g2f-entry 0.1.0 found.
- **Pairs by hybrid category:** seen 1,223; new hybrid with both parents seen 688; with one parent seen
  8,146; with neither parent seen 0.
- **Full** scores 0.4416, as published by g2f-refmodel 0.1.0.
- **By category** (mean within-environment r; rows with an observed yield):

| Category | rows | M4 | full | mix |
|---|---|---|---|---|
| seen | 1,172 | 0.594 | 0.576 | **0.632** |
| new_both | 638 | 0.123 | 0.290 | **0.301** |
| new_one | 7,676 | 0.107 | **0.390** | 0.368 |

  These match g2f-switch 0.1.0 to four decimals, so the new code path builds exactly the mix that
  study graded.
- **Mg/ha files:** every file uses a site-history level for all 22 scored environments and the same
  0.53 Mg/ha hybrid spread. Values range from 0.50-13.19 (M4; one environment's spread was shrunk to
  stay inside the 0.5-25 band), 1.73-14.02 (full) and 0.53-13.53 (mix).

## What this means

`g2f_predict.py predict` is now the checked way to build every 2026 upload file. It finds a release's
files in any layout and never downloads, and on a past season it reproduces the graded scores exactly.
The weights it mixes with are chosen per release by `g2f_refold.py` (pre-registered in
[g2f-refold-0.1.0.md](g2f-refold-0.1.0.md)), so the 2026 entry is not tied to choices made on 2022.

## Limits

- This checks plumbing and reproduction on a past season, not skill on 2026.
- The 2026 metric and file names are not public yet. If the metric is an error measure such as RMSE,
  the Mg/ha level matters, and the site-history level ran about 1 Mg/ha low on 2024 (g2f-entry 0.2.0).

MV2, Munim, Inc., mv2@munimtech.com
