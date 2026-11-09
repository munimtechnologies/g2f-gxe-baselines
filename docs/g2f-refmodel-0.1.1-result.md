# g2f-refmodel 0.1.1: result (where each model wins; the reference script still did not run)

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed it yet. Text CC BY 4.0; code
Apache-2.0.

RESULT-MARKER: g2f-refmodel-0.1.1-result

Graded 2026-11-09 (about 22:40 UTC) against [the pre-registration](g2f-refmodel-0.1.1-prereg.md),
written before either sealed job ran. Raw output: [`results/g2f_refsplit.json`](../results/g2f_refsplit.json).

## Job A, `g2f-refsplit-v1` (finished 2026-11-09 17:05 UTC): gate and all three predictions held

The test pairs were put into the same categories as g2f-newshrink: **seen** (grown in an earlier
season), or new with both, one or neither parent seen as a parent of an earlier hybrid. MV2's
re-implementation of the organisers' reference model (`full`, from g2f-refmodel 0.1.0, unchanged) was
then scored inside each category. Metric: mean within-environment Pearson r.

| Check | Bar | Value | Held? |
|---|---|---|---|
| **S1** category counts match g2f-newshrink (6 counts, within 2%) | 2% | all 6 exact (0.0%) | **yes** |
| **P7** 2022, new_one: full beats M4 | > 0.1435 | **0.1671** | **yes** |
| **P8** 2022, new_both: full below M4 | < 0.4301 | **0.3041** | **yes** |
| **P9** 2024, new_one: full at least 0.30 | >= 0.30 | **0.3898** | **yes** |

Full scores by category (M4's published category scores in brackets, where they exist):

| Fold | seen | new_both | new_one | all rows |
|---|---|---|---|---|
| 2022 (816 / 1,896 / 9,126 rows) | 0.510 | 0.304 (M4 0.430) | 0.167 (M4 0.144) | 0.299 (M4 0.326) |
| 2023 (11,540 / 67 / 7 rows) | 0.393 | too few rows | too few rows | 0.389 (M4 0.435) |
| 2024 (1,172 / 638 / 7,676 rows) | 0.576 | 0.290 (M4 0.123) | 0.390 (M4 0.107) | 0.442 (M4 0.302) |

No test pair in 2022, 2023 or 2024 had neither parent seen before.

What this says:

- **The kernel model's edge is on new hybrids with one parent seen.** It beats M4 there in both
  seasons (2022 by +0.024, 2024 by +0.283). On new hybrids with both parents seen, it beats M4 in
  2024 but loses clearly in 2022 (0.304 vs 0.430), where M4's parent combining-ability term has
  plenty of history to work with.
- **Its global marker effect still adds nothing.** The variant with only the state-specific marker
  effects (`b2`) has the same score as `full` in every category and fold, to four decimals.
- **It overstates how much new hybrids out-yield seen ones.** Inside each environment, new hybrids
  out-yield seen ones by 0.68 SD in 2022 and 0.46 SD in 2024 (observed, z-scores); `full` predicts
  1.06 and 0.83. In 2023, with only 75 new rows, it predicts -1.53 against an observed -0.16. M4
  predicts a gap of about 0.25 (g2f-newshrink), too small. Neither model gets the level of new
  hybrids right, which is one reason to try mixing them.

**Rule fixed in the pre-registration:** S1 and P7 hold, so a category switch is tested: full's
ranking for new_one hybrids, M4 for the rest, with any weight chosen on the 2022 fold only and 2024
as the forward check. It is pre-registered as [g2f-switch 0.1.0](g2f-switch-0.1.0-prereg.md). The
pre-registration expected this study on the 2026 training release. It is being run now on the 2024
release, because the 2022 and 2024 folds are the same seasons either way. It will be repeated on the
2026 release before any upload.

## Job B, `g2f-refr0-v1` (finished 2026-11-09 17:01 UTC): G1, G2 and P10 not graded

The wrapper fix worked: the script found its inputs and ran for 7.9 minutes, through the marker
filtering and kernel steps. It then stopped inside bWGR's `mm()` while "Setting random effect design
matrices", with the R error `contrasts can be applied only to factors with 2 or more levels`. No
prediction file was written, so **G1, G2 and P10 are not graded**, and every 2024 leaderboard place in
this repository stays measured by this repository's harness only.

The job used R 4.6.2 and bWGR 2.2.18 (current on CRAN). MV2's own re-implementation makes the same
`mm()` call with the same bWGR and does not fail. Its inputs differ in two ways: missing yields are
dropped first, and names are trimmed. So the cause is probably in what the script passes to `mm()`,
or in a bWGR change since the 2024 competition, when bWGR 2.2.13 (released 2024-12-05) was current.
[g2f-refmodel 0.1.2](g2f-refmodel-0.1.2-prereg.md) reruns the script under bWGR 2.2.13, still
unmodified, and prints what the script had built if it fails again.

## Limits

- M4's category scores are the published g2f-newshrink ones, not recomputed (g2f-switch 0.1.0
  recomputes M4 on both folds).
- The parent rule splits names on `/`. Hybrids named without a slash (commercial checks) count their
  whole name as one parent.
- One release, three folds. No person has checked these numbers.

MV2, Munim, Inc., mv2@munimtech.com
