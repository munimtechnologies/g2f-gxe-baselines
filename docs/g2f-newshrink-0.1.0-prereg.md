# g2f-newshrink 0.1.0: pre-registration

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed it yet. Text CC BY 4.0; code
Apache-2.0.

Written 2026-10-22 (about 07:50 UTC), after the graded g2f-parentgca 0.1.0 result and before the job
`g2f-newshrink-v1` ran. The job waits until this file is public on GitHub before it reads any yield data,
so these predictions are fixed first. No recalibration grid and no split of G1 by parent coverage
was computed before writing them. Already known from earlier results: the all-rows and seen/new
scores of M2, G1 and M4, and the parent-coverage shares.

## Why

[g2f-checkhybrid 0.1.0](g2f-checkhybrid-0.1.0-result.md) showed that the metric (mean within-environment
Pearson r over all rows) pays for two things. One is ranking the seen minority. The other is placing the
88% new hybrids, ranked at only r of about 0.1, correctly against that minority. [g2f-parentgca
0.1.0](g2f-parentgca-0.1.0-result.md) adopted M4, which ranks new hybrids at r 0.12. If those
predictions are spread too widely for their skill, or sit at the wrong level relative to the seen
hybrids, they dilute the seen hybrids' clean signal. This study tests one idea: recalibrate the new
hybrids as a block.

## Method (code: `g2f_newshrink.py`, tests: `test_g2f_newshrink.py`)

- **M5(s, o).** Seen hybrids (grown in a training year) keep M4. Inside each test environment, every new
  hybrid gets M5 = c + o + s x (M4 - c), where c is the mean M4 of that environment's new-hybrid rows (all
  test rows; observed yields are not used). s = 1, o = 0 is M4.
- **Grid.** s in (0, 0.25, 0.5, 0.75, 1) and o in (-0.5, -0.25, 0, +0.25, +0.5), in within-environment
  z units, 25 points in all.
- **Selection.** (s\*, o\*) is the grid point with the best all-rows score on the **2022 fold** (trained on
  2014-2021; 6.9% of rows seen, the fold most like 2024). Ties go to the point nearest M4. (s\*, o\*) is
  then applied unchanged to 2023 and 2024. The 2022 gain is in-sample, and 2023 has only 75 new rows,
  so **2024 is the real test**. The full grid is reported for every fold, but the 2024 grid is
  descriptive only.
- **Diagnostics.** On each fold's new rows, G1 and M4 r split by whether exactly one or both parents
  were seen in training (same parent pool as g2f-parentgca). Also the mean gap between new and seen
  rows, both in observed within-environment z yield and in M4.
- **Reproduction gate.** 2024 all-rows M2 0.2802 and M4 0.3018 within 0.005, and the grid point
  (1, 0) must equal M4. Otherwise the result is void.

## Predictions

- **P1:** s\* chosen on 2022 is **at least 0.75**. Markers ranked 2022's new hybrids well (M1 0.324 vs
  M0 0.164). Point 1.0.
- **P2:** on the 2024 grid at o = 0, the best s is **below 1** (the 2024 new-hybrid predictions are
  over-spread for their skill). Point 0.75.
- **P3:** on 2024 new rows with **exactly one** parent seen, mean G1 within-environment r is **above
  0.05** (the one-parent, likely tester, signal alone carries most of G1's 0.094). Point 0.08.
- **P4:** on 2024, M4 minus M5(0, 0) is **at least 0.02** (ranking new hybrids at all is worth
  something). Point 0.04.
- **P5:** the chosen offset satisfies **|o\*| <= 0.25**. Point 0.

## Hypothesis and decision (fixed now)

- **H1 (adopt M5(s\*, o\*)):** M5 - M4 >= **+0.01** on 2024 **and** M5 - M4 >= -0.005 on 2023. About a
  20% chance. If (s\*, o\*) = (1, 0), M5 equals M4 and H1 fails by construction.
- If H1 holds, MV2's 2026 entry uses M5(s\*, o\*). If it fails, it keeps M4. If P3 holds, the next study
  models tester-by-environment effects. Otherwise it tests a marker-by-environmental-covariate reaction
  norm. Each gets its own pre-registration.

## Limits

- One selection fold. A grid of 25 points chosen on 28 environments can overfit a little; 2024 is
  scored only once, at the chosen point.
- c uses all test rows in 2024 (template), but only observed rows in the 2022 and 2023 hold-outs.
  Neither uses yields.
- s and o are the same in every environment.
