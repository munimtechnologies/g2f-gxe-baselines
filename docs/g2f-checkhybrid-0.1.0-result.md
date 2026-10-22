# g2f-checkhybrid 0.1.0: result

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed the numbers yet. Text CC BY 4.0;
code Apache-2.0.

This grades the pre-registration [`g2f-checkhybrid-0.1.0-prereg.md`](g2f-checkhybrid-0.1.0-prereg.md),
committed to this repository (release v0.2.0) before the job `g2f-checkhybrid-v1` read the observed-yield
column. The job ran in a sealed container on 2026-10-22 (04:42-04:44 UTC): it confirmed the
pre-registration was public, passed its offline tests, then split the committed v0.1.0 prediction table.
Outputs: [`results/g2f_checkhybrid.json`](../results/g2f_checkhybrid.json) and
[`results/g2f_checkhybrid_env_r.csv`](../results/g2f_checkhybrid_env_r.csv).

## Checks

- **Reproduction gate passed.** All-rows mean within-environment r over the 22 scored 2024 environments:
  M0 0.2353, M1 0.2386, M2 0.2802, M3 0.2799, the same as g2f-baseline 0.1.0.
- **Split check passed.** 0 new rows where M2 differs from M1.
- **Rows.** 10,057 template rows, 9,486 with an observed yield: **1,172 seen** (12.4%) and **8,314 new**.
  Each environment has 26-73 seen rows. Several have exactly 27, which looks like a shared check set.

## Scores (mean within-environment Pearson r, 22 environments)

| Subset | M0 own mean | M1 marker ridge | M2 ridge shrunk to own mean | M3 + location |
|---|---|---|---|---|
| all rows | 0.235 | 0.239 | 0.280 | 0.280 |
| seen hybrids (12%) | 0.589 | 0.498 | **0.594** | 0.588 |
| new hybrids (88%) | undefined (constant) | 0.101 | 0.101 | 0.101 |

## Predictions, graded

All four predictions and the hypothesis held. P3 held only by a hair.

- **P1 held.** Seen r is defined in **22 of 22** environments (bar: at least 15).
- **P2 held.** Mean M0 r on seen hybrids is **0.589** (bar: above 0.40; point 0.50).
- **P3 held, at the threshold.** Mean M2 r on new hybrids is **0.1006** (bar: above 0.10; point 0.20).
  The margin is 0.0006, so this is effectively a tie with the bar, and the point guess was twice too
  high. r is positive in 21 of 22 environments (WIH3 is -0.085) and above 0.10 in 10 of 22. The
  range is from 0.023 (NEH2) to 0.251 (INH1).
- **P4 held.** On seen hybrids, M2 - M0 = **+0.0048** (bar: |difference| below 0.10; point +0.03).
- **H1 held** (we gave it about 65%). On seen hybrids, M2 beats M1 by **+0.096**.

## What this shows

1. **Most of the 2024 score comes from the 12% of rows that are previously grown hybrids.** M0 knows
   nothing about new hybrids. It gives all of them the same value, yet it reaches 0.235 on all rows, 84% of
   M2's 0.280. The metric is a within-environment correlation over *all* rows, so it pays for two things:
   ranking the seen minority (r about 0.59 from their own history) and placing that minority
   correctly against the mass of new hybrids. Ranking new hybrids against each other earns only about
   0.10.
2. **Markers add little for new hybrids, and in some environments they cost.** In 6 of the 22
   environments (GAH1, GAH2, ILH1, TXH1, WIH2, WIH3), M0, which treats every new hybrid as identical, beats
   M2 on all rows. In all six, markers rank new hybrids poorly (new-hybrid r -0.085 to 0.080). Four other
   environments are just as low (DEH1, NEH2, NYH3, ONH3) and M2 still wins there, so low marker skill is
   necessary for this but not enough on its own. Where it happens, spreading noisy marker predictions
   across 88% of the rows dilutes the clean signal from the seen minority.
3. **For seen hybrids, their own history is almost all that matters.** M2 adds only +0.005 over M0, and
   the location-specific residual (M3) adds nothing (0.588 vs 0.594).

This fits a published observation from the 2022 competition: only 8% of the 2022 test hybrids had been
tested before, and a team that left genetics out entirely placed second (Genetics 2024, iyae195). In a
short search we did not find a published per-row split of the 2024 within-environment score by
seen versus new hybrid, as given here.

## Decision (fixed in advance)

The rule was: if P3 holds, the next model strengthens the genomic signal for new hybrids
(parent/tester general combining ability, or a marker-by-covariate reaction norm). If it fails, effort
moves to the seen minority and the environment mean. **P3 held, so the rule picks the genomic route.**
Because P3 held only by 0.0006, both routes stay open. The next study,
[`g2f-parentgca-0.1.0-prereg.md`](g2f-parentgca-0.1.0-prereg.md), tests parent general combining
ability (GCA) from the hybrid pedigree names (P1/P2), blended with the marker ridge. Its adoption bar is
the same +0.01 over M2 used for g2f-envkernel. Finding 2 suggests a later study: shrink the marker
predictions for new hybrids toward a common value, so they cannot drown out the seen minority. That
would need its own pre-registration.

## Limits

- One season (2024). The split is descriptive, not a significance test.
- "Seen" means grown anywhere in 2014-2023, not necessarily at the same location.
- The split inherits every modelling choice of g2f-baseline 0.1.0, whose predictions it reads.
