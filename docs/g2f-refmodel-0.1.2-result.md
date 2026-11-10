# g2f-refmodel 0.1.2: result (the organisers' reference script runs under bWGR 2.2.13 and confirms the harness)

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed it yet. Text CC BY 4.0; code
Apache-2.0.

RESULT-MARKER: g2f-refmodel-0.1.2-result

Graded 2026-11-10 (about 05:00 UTC) against [the pre-registration](g2f-refmodel-0.1.2-prereg.md),
which was public before the sealed job `g2f-refr0-v2` started (it waits for the PREREG-MARKER).
The job finished 2026-11-10 03:41 UTC (69 minutes, peak memory 2.9 GB). Raw output:
[`results/g2f_refr0.json`](../results/g2f_refr0.json).

## All five checks held

| Check | Bar | Value | Held? |
|---|---|---|---|
| **P11** the script runs to the end under bWGR 2.2.13 | prediction file written | ran in 11.9 minutes, all 10,057 template rows predicted | **yes** |
| **G1** harness matches the leaderboard | \|R0 - 0.43766\| <= 0.01 | R0 = **0.4377** (difference below 0.0001) | **yes** |
| **G2** re-implementation faithful | \|full - R0\| <= 0.005 | 0.4416 - 0.4377 = **0.0039** | **yes** |
| **P10** same predictions | mean within-env r >= 0.99 | **0.9966** (23 environments) | **yes** |
| **P12** current bWGR fails again with the same error | same R error | bWGR 2.2.18: `contrasts can be applied only to factors with 2 or more levels` | **yes** |

Setup: R 4.6.2, Debian, bWGR 2.2.13 installed from the CRAN archive into its own library and first on
the search path (the job printed "bWGR version that will load: 2.2.13"). The reference script
(github.com/alenxav/Lectures, `G2F_GxE_2024/script_model.R`, SHA-256 `b55c5fa7...d1359b`) was run
unmodified; it is downloaded at run time and not copied here.

## What follows (fixed in the pre-registration)

- **P11 and G1 hold, so this repository's 2024 places are confirmed by the organisers' own code.**
  Scoring the organisers' script's own predictions with this repository's harness gives 0.4377, the
  leaderboard's figure for "Model 2022 (not competing)" (3rd of 64). So the harness reproduces EvalAI's
  2024 metric, and the places quoted here (M4 0.3018 = 40th of 64; full 0.4416 = 3rd) stand.
- **G2 and P10 hold:** MV2's re-implementation (`full`) is faithful. It makes almost the same
  predictions (mean within-environment r 0.997) and scores 0.004 higher, from small differences in
  input handling (it drops rows with no yield and trims names).
- **P11 and P12 hold:** the failure in 0.1.1 is a change in bWGR between 2.2.13 (2024-12-05) and
  2.2.18 (2026-07-25), not a fault in this repository's wrapper. One issue may be opened on the
  reference script's repository once a person has read this result.

Split by hybrid category (reported, not graded): the script scores 0.5646 on hybrids grown in earlier
seasons and 0.3770 on new hybrids.

## Diagnosis of the bWGR 2.2.18 failure (reported, not graded)

The diagnostics in `run_ref.R` 0.1.2 printed what the script had built when it stopped under bWGR
2.2.18:

- The training table passed to `mm()` had **0 rows** (28 columns), so the error comes from an empty
  input, not from the model.
- The marker kernel `X` had the expected size (5,899 hybrids x 5,893 columns), and the
  hybrid-by-environment table `Y` kept 247 environments but **0 hybrids**.
- The list of hybrids found in both `Y` and `X` was **NULL**, not an empty character vector. In R this
  happens when one side has no row names.

So under 2.2.18, one of the bWGR helpers the script uses on the marker matrix before `mm()` (`IMP`,
`EigenGAU` or `K2X`) most likely returns a matrix without the hybrid row names. The script then finds
no hybrids in common and filters every row away. This fits a detail of MV2's re-implementation
(`g2f_refmodel.R`), which runs under 2.2.18: it copies the hybrid names back onto the imputed marker
matrix and onto the kernel covariates explicitly after `IMP` and `K2X`. This is a hypothesis, not yet a test: the small
sealed job `g2f-bwgr-dimnames-v1` checks each of the three helpers on a toy matrix under both
releases and reports which one drops the names.

## Limits

- One release, one season, one platform. The organisers' own run, whose R and package versions are
  not published, may have differed in details; G1 says the result does not.
- The 0.0039 gap between `full` and the script is not explained row by row.

MV2, Munim, Inc., mv2@munimtech.com
