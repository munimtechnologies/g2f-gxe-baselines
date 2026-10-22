# g2f-parentloc 0.1.0: pre-registration

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed it yet. Text CC BY 4.0; code
Apache-2.0.

Written 2026-10-22 (about 10:30 UTC), after the graded g2f-newshrink 0.1.0 result and before the job
`g2f-parentloc-v1` ran. The job waits until this file is public on GitHub before it reads any yield data,
so these predictions are fixed first. No parent-by-location table, k grid, location coverage or parent
count per environment was computed before writing them. Already known from earlier results: the
all-rows, seen and new scores of M2, G1 and M4, the parent-coverage shares, G1's new-hybrid r split by
one or both parents seen, and that hybrid-by-location residuals (M3) gained nothing over M2 on 2024.

## Why

[g2f-newshrink 0.1.0](g2f-newshrink-0.1.0-result.md) found that in 2024, G1 ranks new hybrids with only
one parent seen before at r 0.105: one known parent, very likely a tester, carries the signal. Its
pre-registered rule therefore picks tester-by-environment effects as the next idea. M4 gives each hybrid
one value for every environment. But a tester's hybrids may do better at some locations than others,
and a tester is grown at a location in many hybrids, so its location effect can be estimated from far
more plots than any one hybrid's (which is why M3's hybrid-by-location residual added nothing).

## Method (code: `g2f_parentloc.py`, tests: `test_g2f_parentloc.py`)

- **Residuals.** For each training hybrid grown in at least two training environments: its mean
  within-environment z yield in an environment minus its mean over all its training environments.
- **Parent-by-location effect.** For parent p and location L (environment name without the year): the
  sum of the residuals of every training hybrid with parent p grown at L, divided by (count + k).
- **M6** = M4 + the sum of the hybrid's distinct parents' effects at the test environment's location.
  A parent never grown at that location adds 0. Seen and new hybrids are treated the same way.
- **Selection.** k in (5, 20, 80, 320) or "off" (M6 = M4), chosen by the all-rows score on the **2022
  fold** (trained on 2014-2021). Ties go to the larger k, and "off" counts as the largest. k\* is then
  applied unchanged to 2023 and 2024. **2024 is the real test.** The grid is reported for every fold.
- **Diagnostics** on each fold's new-hybrid rows: the share with at least one parent grown at the same
  location before; the median number of distinct seen parents among the new hybrids of an environment;
  and, among environments with at least 3 new rows that have exactly one parent seen, the share where G1
  is the same for all those rows (so it scores r = 0 there).
- **Reproduction gate.** 2024 all-rows M2 0.2802 and M4 0.3018 within 0.005, and "off" must equal M4.
  Otherwise the result is void.

## Predictions

- **P1:** at least **70%** of 2024 new-hybrid rows have a parent grown at the same location before.
  Point 85%.
- **P2:** the median 2024 environment has **at least 3** distinct seen parents among its new hybrids
  (G1's r of 0.105 on one-parent rows needs several testers per trial). Point 4.
- **P3:** in **2022**, G1 is constant among the one-parent new rows in **at least half** of the eligible
  environments. This would explain why G1 scored only 0.002 on those rows in 2022. Point 60%.
- **P4:** on 2024, M6 - M4 lies **between -0.005 and +0.02**. Point +0.004.
- **P5:** on 2024 **new** rows, M6 ranks better than M4 (difference above 0). Point +0.005.

## Hypothesis and decision (fixed now)

- **H1 (adopt M6 with k\*):** M6 - M4 >= **+0.01** on 2024 **and** M6 - M4 >= -0.005 on 2023. About a
  15% chance. If k\* is "off", M6 equals M4 and H1 fails by construction.
- If H1 holds, MV2's 2026 entry uses M6. If it fails, it keeps M4. If P5 holds, the next study extends
  the parent effects from the same location to environments with similar weather and soil. Otherwise
  the next study tests a marker-by-environmental-covariate reaction norm. Each gets its own
  pre-registration.

## Limits

- One selection fold with four values of k; the 2022 gain is in-sample.
- Locations are matched by name only. A location that moved fields keeps its name; a new location
  gets no effect.
- Residuals are taken from each hybrid's plain mean over training environments, not from M4. Parent
  names are taken as written, so spelling variants count as different parents.
