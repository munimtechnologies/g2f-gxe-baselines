# g2f-refmodel 0.1.0: result

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed the numbers yet. Text CC BY 4.0;
code Apache-2.0.

RESULT-MARKER: g2f-refmodel-0.1.0-result

This grades the pre-registration [`g2f-refmodel-0.1.0-prereg.md`](g2f-refmodel-0.1.0-prereg.md),
committed to this repository (release v0.9.0) before the sealed job read any yield data. The job
`g2f-refmodel-v2` ran on 2026-11-09 (finished 05:09 UTC, peak memory 3.25 GB; it was paused once by a
scheduled compute lease and resumed). It confirmed the pre-registration was public, passed its offline
tests, then ran the steps below. bWGR 2.2.18 from CRAN, R 4.6.2.

Outputs: [`results/g2f_refmodel.json`](../results/g2f_refmodel.json),
[`results/g2f_refmodel_2024_env_r.csv`](../results/g2f_refmodel_2024_env_r.csv), and the per-row
predictions of every variant on every fold
([`2024`](../results/g2f_refmodel_2024_predictions.csv),
[`2023`](../results/g2f_refmodel_2023_predictions.csv),
[`2022`](../results/g2f_refmodel_2022_predictions.csv)).

## What went wrong first: the reference script did not run (R0)

The organisers' script reads its three input files from a folder named
`Maize_GxE_Competition_Data_2024/` (`Training_data/` and `Testing_data/` inside it). Our wrapper
`run_ref.R` linked the files into `Training_data/` and `Testing_data/` at the top of its working
folder instead, so the script stopped at its first `read.csv` ("cannot open the connection") and wrote
no predictions. This was our wrapper's mistake, not the script's. Two consequences, both as the
pre-registration said they would be handled:

- **G1 and G2 are "not run".** The harness was not checked against the reference's own predictions,
  and the re-implementation was not checked against the reference. The claims below rest on MV2's
  re-implementation alone.
- The pre-registration's P1 falls back to the re-implementation (`full`), as written.

The JSON file records G1 and G2 as `"held": false, "value": null`; read that as "not run". The rerun
with the corrected folder layout is pre-registered as
[g2f-refmodel 0.1.1](g2f-refmodel-0.1.1-prereg.md).

One indirect sign that the harness and the re-implementation are close to the leaderboard: `full`
scores **0.4416** on the 2024 answers, **0.004** from the reference's leaderboard score of 0.4377. That
is not G1, which needs the reference's own predictions.

## Scores (mean within-environment Pearson r)

| Variant | 2022 (28 envs) | 2023 (27 envs) | 2024 (22 envs) | 2024 leaderboard place (of 64) |
|---|---|---|---|---|
| **full** (B1 + B2, test states only) | 0.2987 | 0.3893 | **0.4416** | **3** |
| b2 (state-specific marker effects) | 0.2987 | 0.3893 | 0.4416 | 3 |
| b1 (global marker effect) | 0.0000 | 0.0000 | 0.0000 | 64 |
| allloc (full, trained on every state) | 0.3015 | 0.3899 | 0.4418 | 3 |
| blend (0.5 full + 0.5 M4, z-scored) | - | - | 0.4330 | 6 |
| **M4** (MV2's adopted model; published) | **0.3262** | **0.4354** | 0.3018 | 40 |

2024 split by whether the hybrid was grown in an earlier year (1,223 template rows seen, 8,834 new):

| | seen hybrids | new hybrids |
|---|---|---|
| full | 0.5762 | **0.3769** |
| M4 | **0.5936** | 0.1198 |

Per environment on 2024, full beats M4 in **20 of 22** trials (the exceptions are MNH1 and NEH3), and
the 50/50 blend beats full in 8 of 22.

## The global marker effect contributed nothing

In MV2's fit the global marker effect B1 from bWGR's `mm` carried no ranking at all: `b1` scores
0.0000 in every environment of every fold (its predictions are constant inside each environment), and
`full` equals `b2` to four decimals on every fold. So the model that scored 0.4416 is, in practice,
the Gaussian-kernel covariates times the **state-averaged environment-specific marker effects** from
the multivariate `ZSEMF` fit, plus each state's mean yield. Whether the same is true inside the
organisers' script (same package, same call) is one of the questions for the 0.1.1 rerun. It may also
mean our `mm` call or bWGR 2.2.18 returns zero marker effects for this design; we have not found out
which.

## Predictions, graded

- **G1 not run; G2 not run** (see above).
- **P1 held** (point 0.75). On 2024 the re-implementation scores **0.1398** above M4 (bar 0.10).
- **P2 failed** (point 0.55). full is **below** M4 on both earlier folds: 2022 by 0.0275, 2023 by
  0.0461.
- **P3 held, but it says nothing** (point 0.55). b2 (0.4416) >= b1 (0.0000), only because b1 is
  constant. It cannot tell whether state-specific effects beat a working global one.
- **P4 failed** (point 0.55). Training only on the test states did not help: full - allloc =
  **-0.0002** (bar +0.005). The same holds on 2022 (-0.0028) and 2023 (-0.0006).
- **P5 held** (point 0.70). The 50/50 blend with M4 scores **0.0086 below** full on 2024.
- **P6 held** (point 0.60). full ranks new 2024 hybrids at **r = 0.377**, against M4's 0.120.
- **H1 failed.** The 2024 gain (0.1398) clears its 0.05 bar, but full's mean over 2022 and 2023 is
  **0.344**, below M4's 0.3808.

## Decision (fixed in advance)

**H1 failed, so, as pre-registered, MV2's 2026 entry keeps M4 for now.** The result is not a simple
"M4 is better", though, and the next step follows from that.

## What this shows

1. **The organisers' kernel model, as re-implemented here, is a top-3 model on the 2024 answers and a
   worse model than M4 on 2022 and 2023.** Its whole 2024 advantage is on new hybrids (0.377 vs 0.120);
   on hybrids grown before, M4's own-mean shrinkage stays slightly ahead (0.594 vs 0.576).
2. **"New hybrid" is not one thing.** 2022 was also a season of mostly new hybrids (93% of rows), yet
   M4 beat full there. From the published g2f-newshrink split, M4's 2022 new hybrids with both parents
   seen before scored 0.430 (1,896 rows) and those with one parent seen 0.144 (9,126 rows); in 2024 the
   same groups scored 0.123 and 0.107. The 0.1.1 study splits full the same way, to find out on which
   kind of new hybrid each model wins before the 2026 entry is chosen.
3. **Season-to-season swings dominate.** One fixed model moves from 3rd place (2024) to below MV2's
   mid-table model (2022, 2023). Any choice made for 2026 should be made on the 2026 test set's
   structure (how many hybrids and parents were grown before), which MV2's `g2f_entry.py seen` measures
   from the template as soon as it is released.

## Limits

- The reference script itself has not yet been run in this harness, so nothing here is a statement
  about the organisers' script; it is about MV2's re-implementation of its described steps.
- b1 being constant may be a misuse of `mm` in our code rather than a property of the model; until the
  0.1.1 rerun compares the reference's own predictions, P3 is uninformative.
- Three folds and one data release; the leaderboard place is for a single fixed model, whereas
  leaderboard entries are each team's best of several submissions.
- The test-state filter and the 2-letter state grouping use the `Env` prefix; Ontario (`ON`) and
  Germany (`GE`) are treated as "states" like the US ones.
