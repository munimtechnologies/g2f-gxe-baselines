# g2f-parentgca 0.1.0: result

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed the numbers yet. Text CC BY 4.0;
code Apache-2.0.

This grades the pre-registration [`g2f-parentgca-0.1.0-prereg.md`](g2f-parentgca-0.1.0-prereg.md),
committed to this repository (release v0.3.0) before the job `g2f-parentgca-v1` read any yield data. The
job ran in a sealed container on 2026-10-22 (06:15-06:19 UTC). It confirmed the pre-registration was
public, passed its 10 offline tests, then fitted and scored all three folds. Outputs:
[`results/g2f_parentgca.json`](../results/g2f_parentgca.json),
[`results/g2f_parentgca_2024_env_r.csv`](../results/g2f_parentgca_2024_env_r.csv) and
[`results/g2f_parentgca_2024_predictions.csv`](../results/g2f_parentgca_2024_predictions.csv).

## Checks

- **Reproduction gate passed.** 2024 all-rows mean within-environment r: M0 0.2353, M1 0.2386,
  M2 0.2802, the same as g2f-baseline 0.1.0.
- **Every scored hybrid name is a two-way cross** ("PARENT1/PARENT2") in all three folds.
- **G1 fit.** Parent ridge on 1,824 (2022), 2,252 (2023) and 2,255 (2024) parents. The CV picked
  lambda 1.0 in every fold, with CV r over training hybrids of 0.44-0.45 (the marker ridge reaches
  0.53-0.55 on the same target).

## Scores (mean within-environment Pearson r)

| Fold | M2 (baseline) | G1 parent GCA alone | **M4** = 50/50 blend, shrunk to own mean | M4 - M2 |
|---|---|---|---|---|
| 2022 (28 envs) | 0.3257 | 0.2580 | 0.3262 | +0.0005 |
| 2023 (27 envs) | 0.4371 | 0.4088 | 0.4354 | -0.0017 |
| 2024 (22 envs) | 0.2802 | 0.2846 | **0.3018** | **+0.0216** |

2024 split by whether the hybrid was grown in 2014-2023 (as in g2f-checkhybrid):

| Subset | M1 marker ridge | M2 | G1 | M4 |
|---|---|---|---|---|
| seen hybrids (12%) | 0.498 | 0.594 | 0.561 | 0.594 |
| new hybrids (88%) | 0.101 | 0.101 | 0.094 | **0.120** |

## Predictions, graded

Three of four predictions held, and the hypothesis held.

- **P1 held.** **100%** of new-hybrid rows have at least one parent seen in a 2014-2023 hybrid
  (bar: at least 50%; point 85%).
- **P2 failed.** Only **7.7%** of new-hybrid rows have *both* parents seen (bar: at least 20%; point 35%).
  In 2022 the share was 17.2%. New 2024 hybrids are almost all a new inbred crossed to a parent used
  before.
- **P3 held.** G1 ranks new hybrids at mean r **0.094** (bar: above 0.05; point 0.08). That is close to
  the marker ridge's 0.101 with no marker data. It is negative in 6 of 22 environments (GAH2, ILH1, INH1,
  MNH1, WIH1, WIH3) and above 0.25 in 5 (DEH1, IAH4, MOH1, NCH1, NEH1).
- **P4 held.** M4 - M2 on 2024 is **+0.0216** (range -0.02 to +0.04; point +0.005, so the gain was
  four times the point guess).
- **H1 held** (we gave it about 25%). M4 - M2 is +0.0216 on 2024 (bar: at least +0.01), and +0.0005
  on 2022 and -0.0017 on 2023 (bar: no worse than -0.005 on either).

## What this shows

1. **Blending parent GCA into the marker ridge lifts the 2024 score from 0.280 to 0.302.** M4 beats M2
   in 21 of 22 environments (the exception is INH1, 0.419 vs 0.431). All of the gain comes from new
   hybrids (r 0.101 to 0.120); seen hybrids are unchanged (0.594). The two genetic signals are only
   partly redundant, so averaging them ranks new hybrids better than either one alone.
2. **In 2024 the parent signal is mostly one parent deep.** With both parents seen in only 7.7% of
   new rows, G1 can usually tell new hybrids in one environment apart only by their one known
   parent. That parent is very likely a long-used tester. The next study checks this directly by
   scoring G1 separately on rows with one and with two parents seen.
3. **The gain did not show up in the other two folds.** 2023 is almost all seen hybrids (99.4% of rows),
   so a new-hybrid model has nothing to do there. But 2022 looks like 2024 (6.9% of rows seen), and M4
   gained only +0.0005 there. The 2024 gain may partly be specific to that year's tester mix. The
   pre-registered rule still adopts M4, because it never cost more than 0.002 in any fold.
4. **Of the six 2024 environments where the history-only M0 beat M2,** M4 now beats M0 in four (GAH1, ILH1,
   TXH1, WIH2). It still trails in GAH2 and WIH3.

Parent general combining ability is a standard idea in maize breeding. What this repository adds is an
open, pre-registered test of it on the G2F 2024 release, scored against the organisers' released
answers and split by seen and new hybrids. A short search found no published per-fold G2F comparison
like this.

## Decision (fixed in advance)

**H1 held, so MV2's 2026 G2F entry uses M4 in place of M2.** As the pre-registration said, the next
study, [`g2f-newshrink-0.1.0-prereg.md`](g2f-newshrink-0.1.0-prereg.md), builds on M4. It recalibrates
new-hybrid predictions as a block, using a scale and an offset chosen on the 2022 fold. It also measures
how much of G1's new-hybrid signal comes from rows with only one parent seen.

## Limits

- Three folds, and only 2024 and 2022 have many new hybrids. The differences are not significance tests.
- Parent names are taken as written; spelling variants of one inbred count as different parents.
- The 50/50 weight was fixed in advance and not tuned. A tuned weight could do better or worse.
