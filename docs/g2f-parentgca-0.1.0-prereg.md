# g2f-parentgca 0.1.0: pre-registration

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed it yet. Text CC BY 4.0; code
Apache-2.0.

Written 2026-10-22 (about 06:15 UTC), after the graded g2f-checkhybrid 0.1.0 result and before the job
`g2f-parentgca-v1` ran. The job waits until this file is public on GitHub before it reads any yield data,
so these predictions are fixed first. No 2024 parent-name coverage figure was computed before writing
them.

## Why

[g2f-checkhybrid 0.1.0](g2f-checkhybrid-0.1.0-result.md) found that the marker ridge ranks the 88% of
2024 rows that are new hybrids at a mean within-environment r of only **0.10**, while previously grown
hybrids are ranked at 0.59 from their own history. Its fixed decision rule (P3 held, at the threshold)
picks a model that strengthens the genetic signal for new hybrids. G2F hybrid names are pedigrees,
"PARENT1/PARENT2", and new hybrids are often new inbreds crossed to testers that have been used for
years. A parent's general combining ability (GCA), learned from every earlier hybrid that shares
it, may carry signal that 2,425 markers miss. This study tests that, one idea at a time, against M2.

## Method (code: `g2f_parentgca.py`, tests: `test_g2f_parentgca.py`)

- **Parents.** A name splits on "/" into exactly two non-empty parts (stripped, upper-cased). Any other
  name (for example a commercial check without "/") has no known parents.
- **G1, parent GCA.** Ridge regression of each training hybrid's mean within-environment z-scored yield
  (the same target as g2f-baseline's M1) on 0/1 indicators of its two parents. Parents form one pool,
  whichever side of the cross they are on. Lambda is chosen from (0.3, 1, 3, 10, 30, 100) by the same 5-fold
  CV over hybrids as M1. A test hybrid gets the effects of the parents seen in training; unseen parents
  add nothing.
- **M4, the candidate.** blend = 0.5 x M1 + 0.5 x G1 (fixed weight, not tuned), then shrunk toward the
  hybrid's own training mean exactly as M2 is: M4 = blend + n/(n+5) x (own mean - blend) for seen
  hybrids, M4 = blend for new ones. With a GCA weight of 0, M4 equals M2 (an offline test checks this).
- **Folds and metric.** As in g2f-baseline 0.1.0: hold out 2022 and 2023 (train on earlier years) and
  2024 (train on 2014-2023, scored on the organisers' released answers). Mean within-environment Pearson r
  via `g2f_baseline.score` (environments with fewer than 3 observed rows are skipped; a constant
  prediction within an environment scores 0). On 2024 the run also scores the seen and new subsets
  separately ("seen" = grown in 2014-2023).
- **Reproduction gate.** The 2024 all-rows scores of M0, M1, M2 must match g2f-baseline 0.1.0 (0.2353,
  0.2386, 0.2802) within 0.005, or the result is void.

## Predictions (2024 fold unless stated)

- **P1:** at least **50%** of new-hybrid rows with an observed yield have at least one parent seen in
  a 2014-2023 training hybrid. Point 85%.
- **P2:** at least **20%** of those rows have both parents seen. Point 35%.
- **P3:** mean G1 within-environment r on the **new** subset exceeds **0.05**. Point 0.08.
- **P4:** on all rows, M4 - M2 lies within **[-0.02, +0.04]**. Point +0.005.

## Hypothesis and decision (fixed now)

- **H1 (adopt M4):** M4 - M2 >= **+0.01** on 2024, **and** M4 - M2 >= -0.005 on both the 2022 and 2023
  folds. About a 25% chance.
- If H1 holds, MV2's 2026 G2F entry uses M4 in place of M2. If H1 fails, the entry keeps M2. The next study
  then tests the other lever that g2f-checkhybrid exposed: shrinking new-hybrid predictions toward a
  common value so they do not dilute the seen minority, or a marker-by-covariate reaction norm. Each gets
  its own pre-registration.

## Limits

- Parent names are taken as written; spelling variants of one inbred count as different parents.
- Testers carry no information *within* a tester group, so G1 ranks new hybrids within an environment only
  through their non-tester parent and through tester-group differences.
- One fixed blend weight. A different weight could do better, but tuning it on 2024 would leak.
