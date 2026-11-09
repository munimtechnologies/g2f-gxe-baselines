# g2f-refmodel 0.1.1: pre-registration (rerun of the reference, and where each model wins)

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed it yet. Text CC BY 4.0; code
Apache-2.0.

PREREG-MARKER: g2f-refmodel-0.1.1

Written 2026-11-09 (about 07:30 UTC), after grading [g2f-refmodel 0.1.0](g2f-refmodel-0.1.0-result.md)
and before either job below runs. Both jobs wait until this file is public on GitHub. Nothing below
has been computed yet: the 0.1.0 job produced per-row predictions on 2022 and 2023 but no split of
them by hybrid type, and no run of the organisers' script.

## Why

0.1.0 left two questions open.

1. **The reference itself never ran.** Our wrapper put the input files in the wrong folder (the
   script reads `Maize_GxE_Competition_Data_2024/Training_data/...`). `run_ref.R` 0.1.1 now links the
   files there as well. Nothing else in it changes, and the script is still run unmodified.
2. **Why does the kernel model win 2024 but lose 2022, when both seasons are mostly new hybrids?**
   g2f-newshrink already split M4 by how many of a new hybrid's parents were seen in training. 0.1.1
   splits MV2's re-implementation (`full` from 0.1.0, unchanged) the same way.

## Job A: `g2f-refsplit-v1` (Python only; `g2f_refcheck.py split`)

Reads the committed 0.1.0 predictions for 2022, 2023 and 2024 and the public release. For each fold,
each test hybrid is put in one category:

- **seen**: it has a yield row in a training year (before the fold year; all of 2014-2023 for 2024);
- **new_both / new_one / new_none**: it is new, and 2, 1 or 0 of its parents (the two names on either
  side of `/` in its name) appear as a parent of some training hybrid.

Within-environment r (at least 3 observed rows; constant prediction = 0) is computed per category for
full, b2 and allloc. Also reported, not graded: the mean within-environment gap between new and seen
hybrids, in observed and in predicted z-scores.

**Gate S1 (the categories match g2f-newshrink's):** the observed-row counts are within 2% of the
published ones: 2022 seen 816, new_one 9,126, new_both 1,896; 2024 seen 1,172, new_one 7,676,
new_both 638. If S1 fails, the split is still reported, but P7-P9 are flagged as comparing different
groups.

M4's published r (g2f-newshrink 0.1.0): 2022 new_one **0.1435**, new_both **0.4301**; 2024 new_one
**0.1073**, new_both **0.1230**.

- **P7:** on 2022, full ranks **new_one** hybrids better than M4: r > 0.1435. Point 0.60.
- **P8:** on 2022, full ranks **new_both** hybrids worse than M4: r < 0.4301. Point 0.60.
- **P9:** on 2024, full ranks **new_one** hybrids at r >= 0.30. Point 0.65.

## Job B: `g2f-refr0-v1` (R + Python; `run_ref.R` 0.1.1, then `g2f_refcheck.py r0`)

Runs the downloaded script unmodified on the 2024 release (its SHA-256 is recorded) and scores its
prediction file against the released 2024 answers.

- **G1 (harness matches the leaderboard):** R0 within **0.01** of 0.43766. Point 0.85.
- **G2 (re-implementation faithful):** |full (0.4416) - R0| <= **0.005**. Point 0.70.
- **P10 (same predictions):** the mean over 2024 environments of the Pearson correlation between R0's
  and full's predictions (all template rows) is **>= 0.99**. Point 0.60. If it holds, the reference's
  global effect B1 adds as little as ours did.
- Also reported: R0's leaderboard place, and R0 on seen and new hybrids (M4's committed seen flag).

## What follows (fixed now)

- If **S1 and P7 hold**, the 2026 entry study, pre-registered on the 2026 training release after
  2026-11-16, tests a category switch: full's ranking for new hybrids with one parent seen, M4 for
  the rest. Any switch weight is chosen on the 2022 fold only, and 2024 is the forward check.
- If P7 fails, the kernel model's 2024 lead is treated as season-specific, and the entry stays M4
  unless the 2026 test set's structure looks like 2024's (fewer than 10% of new rows with both parents
  seen, measured by `g2f_entry.py seen`), in which case that same study compares full and M4 on the
  2024 fold.
- If G1 fails (R0 runs but is more than 0.01 from the leaderboard), every 2024 place in this repository
  is marked as unverified.

## Limits

- The parent rule (split on `/`) is MV2's reading of g2f-parentgca's; S1 checks it by counts only.
- M4's category scores are taken from the published g2f-newshrink file, not recomputed.
- One release, three folds. P10 uses predictions, not answers, so it is about agreement, not accuracy.
