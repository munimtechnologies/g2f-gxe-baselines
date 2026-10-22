# g2f-newshrink 0.1.0: result

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed the numbers yet. Text CC BY 4.0;
code Apache-2.0.

This grades the pre-registration [`g2f-newshrink-0.1.0-prereg.md`](g2f-newshrink-0.1.0-prereg.md),
committed to this repository (release v0.4.0) before the job `g2f-newshrink-v1` read any yield data. The
job ran in a sealed container on 2026-10-22 (08:21-08:26 UTC). It confirmed the pre-registration was
public (first attempt), passed its 10 offline tests, then fitted and scored all three folds. Outputs:
[`results/g2f_newshrink.json`](../results/g2f_newshrink.json) and
[`results/g2f_newshrink_2024_env_r.csv`](../results/g2f_newshrink_2024_env_r.csv).

## Checks

- **Reproduction gate passed.** 2024 all-rows mean within-environment r: M2 0.2802 and M4 0.3018, the
  same as g2f-parentgca 0.1.0, and grid point (s = 1, o = 0) equals M4 (0.3018).

## Selection and scores (mean within-environment Pearson r)

The 2022 grid chose **s\* = 1.0, o\* = +0.25**: new hybrids keep M4's spread and are shifted up by a
quarter of a within-environment standard deviation relative to seen hybrids.

| Fold | M2 | M4 | **M5(1, +0.25)** | M5 - M4 |
|---|---|---|---|---|
| 2022 (28 envs, selection fold, in-sample) | 0.3257 | 0.3262 | 0.3378 | +0.0116 |
| 2023 (27 envs) | 0.4371 | 0.4354 | 0.4344 | -0.0010 |
| 2024 (22 envs) | 0.2802 | 0.3018 | 0.3031 | **+0.0013** |

On 2024, M5 beats M4 in 10 of 22 environments and trails in 12 (largest gain MOH1 +0.025, largest loss
ILH1 -0.035).

The grid is flat in s near 1 and peaked in o near +0.25 on both 2022 and 2024:

| s (o = 0) | 0 | 0.25 | 0.5 | 0.75 | 1 |
|---|---|---|---|---|---|
| 2022 | 0.2188 | 0.2777 | 0.3106 | 0.3237 | 0.3262 |
| 2024 | 0.2805 | 0.2915 | 0.2986 | 0.3018 | 0.3018 |

| o (s = 1) | -0.5 | -0.25 | 0 | +0.25 | +0.5 |
|---|---|---|---|---|---|
| 2022 | 0.2339 | 0.2901 | 0.3262 | 0.3378 | 0.3332 |
| 2024 | 0.2003 | 0.2672 | 0.3018 | 0.3031 | 0.2898 |

## Predictions, graded

Four of five predictions held; the hypothesis failed.

- **P1 held.** s\* = **1.0** (bar: at least 0.75; point 1.0).
- **P2 failed.** On the 2024 grid at o = 0, s = 0.75 and s = 1 tie at 0.3018 (to four decimals), and
  the pre-registered tie rule sends a tie to the point nearest M4, so the best s is **1.0** (bar: below 1).
  There is no sign that M4's new-hybrid predictions are spread too widely for their skill.
- **P3 held.** On 2024 new rows with exactly one parent seen in training (7,676 rows), G1 ranks
  hybrids at mean r **0.105** (bar: above 0.05; point 0.08). On the 638 new rows with both parents seen
  it is 0.101, so the one-parent signal carries G1's new-hybrid skill.
- **P4 held.** M4 - M5(0, 0) on 2024 is **+0.0213** (bar: at least 0.02; point 0.04): ranking new
  hybrids at all is worth about 0.02, but less than we guessed.
- **P5 held.** |o\*| = **0.25** (bar: at most 0.25; point 0), right at the bar.
- **H1 failed** (we gave it about 20%). M5 - M4 is +0.0013 on 2024 (bar: at least +0.01) and -0.0010 on
  2023 (bar: no worse than -0.005).

## What this shows

1. **New hybrids out-yield the seen ones inside each environment, and M4 under-predicts the gap.** The
   mean new-minus-seen gap in within-environment z yield is **+0.68** in 2022 and **+0.46** in 2024
   (2023: -0.13 on only 75 new rows). M4 predicts **+0.23** and **+0.27**. The seen hybrids are mostly
   older hybrids grown again, so this looks like genetic progress that a model fitted on past hybrid
   means cannot see. Shifting new hybrids up by 0.25 recovers +0.012 in 2022 but only +0.001 in 2024,
   so the block offset is not worth adopting.
2. **Squeezing the new-hybrid predictions never helps.** Scores fall steadily as s goes below 0.75 in
   both 2022 and 2024. Flattening every new hybrid in an environment to one value (s = 0) costs 0.021
   in 2024 and 0.107 in 2022.
3. **Why M4 gained in 2024 but not in 2022.** In 2022, G1 ranks new hybrids with exactly one seen parent
   at r **0.002** (9,126 rows), against 0.105 in 2024. It ranks the 2022 new hybrids with both parents
   seen (1,896 rows, 17%) at 0.40, but that block is too small to move the total. One possible reason,
   not yet checked: in 2022, the one-parent hybrids in each environment may all share the same seen
   parent (one tester per trial), so G1 is constant among them and scores 0. The next study tests this
   directly.

Recalibrating a block of new entries against repeated checks is a common idea in plant breeding trial
analysis. What is new here is an open, pre-registered test of it on the G2F 2024 release, together with
the measured new-versus-seen yield gap in each fold. A short search found no published G2F analysis of
this gap.

## Decision (fixed in advance)

**H1 failed, so MV2's 2026 G2F entry keeps M4.** P3 held, so the next study,
[`g2f-parentloc-0.1.0-prereg.md`](g2f-parentloc-0.1.0-prereg.md), models tester-by-environment effects:
how each parent's hybrids have done at the same location before, shrunk by sample size. It also checks
whether the one-parent hybrids in each 2022 trial share one seen parent.

## Limits

- One selection fold. The 2022 gain of +0.012 is in-sample.
- P2 failed on a tie at four decimals; the two points differ by less than the rounding.
- s and o are the same in every environment, and new hybrids are treated as one block.
