# g2f-refold 0.1.0: result of the 2024 dry run

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed it yet. Text CC BY 4.0; code
Apache-2.0. Not agronomic advice.

RESULT-MARKER: g2f-refold-0.1.0-result

Pre-registration: docs/g2f-refold-0.1.0.md (2026-11-10). Rerun note: docs/g2f-refold-0.1.0-rerun.md.
Output: results/g2f_refold_2024.json.

## What ran

The first sealed dry run (`g2f-refold-dry-v1`, 2026-11-10) stopped at a bug in a test helper under
pandas 3.1, before any data were scored (see the rerun note). The helper was fixed, nothing else
changed, and the rerun `g2f-refold-dry-v2` ran on 2026-11-12 from 12:31 to 12:37 UTC (python:3.12,
numpy 2.5.4, pandas 3.1.1, 1 CPU, 2 GB asked, 0.33 GB peak) on the public 2024 release:

1. `check_prereg.py` fetched the published tool, the fixed test, the registered expectations and the
   committed kernel-model predictions for 2022 and 2023 from GitHub, after the rerun note was public.
2. `python -m unittest -v test_g2f_refold`: **8 of 8 tests passed** (the 7 original tests, unchanged,
   plus the new test of the fixed helper).
3. `python g2f_refold.py choose ... --expect g2f-refold-expect-2024.json --name g2f_refold_2024`.

## Grading: all 6 held

| Check | Registered | Got | Held |
|---|---|---|---|
| D1 season typing | 2024 = new_hybrids (6.8% of pairs grown in 2023); 2023 = repeated, 2022 = new | 2024 new_hybrids, 688 of 10,057 pairs (6.84%); 2023 repeated (99.35%); 2022 new (6.89%) | yes |
| D2 folds chosen on | [2022], matched = true | [2022], matched = true | yes |
| D3 2022 fold reproduced | M4 0.3262, full 0.2987 (+-0.0005) | M4 0.3262, full 0.2987 | yes |
| D4 entry | a0.50_b0.50, 0.3617 on 2022 (g2f-switch's choice) | a0.50_b0.50, 0.3617 | yes |
| D5 (prediction) 2023 fold: M4 beats full | M4 > full | M4 0.4354, full 0.3893 | yes |
| D6 (prediction) 2023 fold: chosen b at most 0.5 | b <= 0.5 | a 0.0, b 0.5 (0.4617) | yes |

Here a is the weight on the kernel model ("full") for new hybrids with one parent seen, and b the
weight on full for every other row; M4 gets the rest (g2f-switch 0.1.0 definition).

## Decision (as registered)

D1-D4 all held, so **g2f-refold 0.1.0 chooses the 2026 mix weights**. Release-day order: census;
`Rscript g2f_refmodel.R <release> <out> all 4`; `python g2f_refold.py choose --data-dir <release>
--full-dir <out>/preds --folds 4`; `python g2f_predict.py predict ... --a <a> --b <b>`. This is the
first file in the pre-registered 2026 upload order (docs/g2f-2026-portfolio-0.2.0.md); if refold
fails on the 2026 release, the first file is (0.5, 0.5) instead. Uploads still go through Sheehan
Munim's EvalAI account only when he says so, and only if he registers the entry.

## What else the run shows (descriptive, not graded)

- **The 2023 fold barely sees a.** 2023 has only 75 scored rows that are not "seen" hybrids (67
  new_both, 7 new_one, 1 new_none), and the new_one category gets no score there (too few rows), so a has
  almost no rows to act on: at each b, the 2023 grid moves by at most 0.0002 across a. All of the 2023 signal is in b,
  which peaks at 0.5 (0.4617) and falls to 0.3893 at b = 1. This is why a repeated-hybrid season
  cannot choose a, and why refold only chooses on seasons of the test season's type.
- **2022 by hybrid category, chosen mix vs the two single models:** seen 0.5576 (M4 0.5172, full
  0.5097); new_both 0.4536 (0.4301, 0.3041); new_one 0.1925 (0.1435, 0.1671). The mix beats both
  single models in all three categories of the 2022 fold.
- **Two-fold mean (2022 and 2023), not used for the choice:** the grid now peaks at a = b = 0.5
  (0.4117), ahead of (0.5, 0.25) 0.4099, (0.75, 0.5) 0.4092 and (0.25, 0.5) 0.4091. The
  pre-registration quoted a guide figure of (0.75, 0.5) at 0.4061 from earlier g2f-switch numbers and
  said it was "a guide, not a prediction"; the difference was not investigated further, since the
  two-fold mean does not decide anything.

## Limits

- One graded fold of each type exists on the 2024 release. This run checks plumbing and reproduction of
  g2f-switch's choice, not whether (0.5, 0.5) will be the best weights in 2026.
- Which of the four hold-out seasons match the 2026 test season's type is only known once the 2026
  release exists; what the release should look like is pre-registered in docs/g2f-2026-release-0.1.0.md
  and graded on release day.
- The 2026 rules score mean per-location r; refold chooses on mean within-environment r. Where a location
  has one environment the two are the same; release day checks for locations with more than one.
