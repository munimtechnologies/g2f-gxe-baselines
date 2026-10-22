# g2f-parentloc 0.1.0: result

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed the numbers yet. Text CC BY 4.0;
code Apache-2.0.

This grades the pre-registration [`g2f-parentloc-0.1.0-prereg.md`](g2f-parentloc-0.1.0-prereg.md),
committed to this repository (release v0.5.0) before the job `g2f-parentloc-v1` read any yield data. The
job ran in a sealed container on 2026-10-22 (10:12-10:16 UTC). It confirmed the pre-registration was
public (first attempt), passed its 10 offline tests, then fitted and scored all three folds. Outputs:
[`results/g2f_parentloc.json`](../results/g2f_parentloc.json) and
[`results/g2f_parentloc_2024_env_r.csv`](../results/g2f_parentloc_2024_env_r.csv).

## Checks

- **Reproduction gate passed.** 2024 all-rows mean within-environment r: M2 0.2802 and M4 0.3018, the
  same as earlier studies, and the grid point k = "off" equals M4 (0.3018).

## Selection and scores (mean within-environment Pearson r)

The 2022 grid chose **k\* = 20**: each parent's past residuals at a location are summed and divided by
(count + 20) before being added to M4.

| Fold | M2 | M4 | **M6 (k = 20)** | M6 - M4 |
|---|---|---|---|---|
| 2022 (28 envs, selection fold, in-sample) | 0.3257 | 0.3262 | 0.3327 | +0.0065 |
| 2023 (27 envs) | 0.4371 | 0.4354 | 0.4475 | +0.0121 |
| 2024 (22 envs) | 0.2802 | 0.3018 | **0.2862** | **-0.0156** |

The k grid, by fold (all-rows mean within-environment r):

| k | 5 | 20 | 80 | 320 | off (= M4) |
|---|---|---|---|---|---|
| 2022 (selection) | 0.3231 | **0.3327** | 0.3302 | 0.3277 | 0.3262 |
| 2023 | 0.4484 | 0.4475 | 0.4398 | 0.4367 | 0.4354 |
| 2024 | 0.2896 | 0.2862 | 0.2830 | 0.2869 | **0.3018** |

On 2024 **every** value of k scores below M4: the parent-by-location offset is harmful in the held-out
year no matter how hard it is shrunk. It is NOT adopted.

## Predictions, graded

Three of five predictions held; the hypothesis failed.

- **P1 held.** **95.8%** of 2024 new-hybrid rows have a parent grown at the same location before (bar:
  at least 70%; point 85%).
- **P2 held.** The median 2024 environment has **27** distinct seen parents among its new hybrids
  (bar: at least 3; point 4), minimum 10 over 22 environments.
- **P3 held.** In 2022, G1 is constant among the one-parent new rows in **100%** of the eligible
  environments (bar: at least 50%; point 60%). This confirms why G1 scored only r = 0.002 on those rows
  in 2022: every one-parent new hybrid in a trial shares the same seen tester, so G1 cannot rank them.
- **P4 failed.** On 2024, M6 - M4 is **-0.0156** (bar: between -0.005 and +0.02). The offset hurts more
  than the small gain we expected.
- **P5 failed.** On 2024 **new** rows, M6 - M4 is **-0.0273** (bar: above 0). The offset hurts new
  hybrids most of all.
- **H1 failed** (we gave it about 15%). M6 - M4 is -0.0156 on 2024 (bar: at least +0.01), though +0.0121
  on 2023 (bar: no worse than -0.005).

## What this shows

1. **A parent-by-location effect fits the training years but does not carry forward one year.** Split by
   whether a hybrid was grown before, M6 - M4 in 2024 is **-0.0065** on seen hybrids and **-0.0273** on
   new ones, yet in 2022 it is **+0.0375** on seen hybrids (new: -0.0012). So the same device that lifts
   the within-period 2022 and 2023 folds reverses sign on the 2024 hold-out. The residuals are estimated
   over 2014-2023 and simply do not predict how a parent's hybrids will rank at a location in a new
   season.
2. **A few environments do the damage.** The 2024 per-environment M6 - M4 is strongly negative at
   IAH4 (0.364 -> 0.097, -0.267) and DEH1 (0.184 -> 0.027, -0.157), and positive at NCH1 (0.251 ->
   0.388, +0.136). The loss is concentrated where a parent's past location residual points the wrong way
   for the new hybrids there, which the within-environment metric punishes heavily.
3. **The pre-registered diagnostics all held.** New 2024 hybrids almost always have a parent with a
   location history (95.8%), trials have many distinct seen parents (median 27), and the 2022 one-parent
   trials really do share a single tester. The mechanism we wanted to exploit is present; it just does
   not generalise across seasons.

Location and tester-by-environment adjustments are standard in multi-environment trial analysis. What is
new here is an open, pre-registered test of one on the released G2F 2024 answers, with the finding that
it helps the within-season folds yet fails to transfer forward. This is the third env-specific device
(after M3's hybrid-by-location residual and g2f-envkernel's covariate weighting) to gain nothing on the
2024 hold-out.

## Decision (fixed in advance)

**H1 failed, so MV2's 2026 G2F entry keeps M4.** P5 failed, so the pre-registered branch turns from
same-location parent effects to a **marker-by-environmental-covariate reaction norm**: the next study,
[`g2f-ecreaction-0.1.0-prereg.md`](g2f-ecreaction-0.1.0-prereg.md), lets each marker's effect vary with
the environment's weather and soil, added as a controlled correction on top of M4.

## Limits

- One selection fold with four values of k; the 2022 and 2023 gains are within the training window.
- Locations are matched by name only; a parent never grown at a location adds nothing.
- Residuals are taken from each hybrid's plain mean over training environments, not from M4, and parent
  names are read as written, so spelling variants count as different parents.
</content>
</invoke>
