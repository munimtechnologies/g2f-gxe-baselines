# g2f-refmodel 0.1.2: pre-registration (the reference script under the 2024 bWGR release)

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed it yet. Text CC BY 4.0; code
Apache-2.0.

PREREG-MARKER: g2f-refmodel-0.1.2

Written 2026-11-09 (about 22:45 UTC), after [g2f-refmodel 0.1.1](g2f-refmodel-0.1.1-result.md) and
before the job below runs. The job waits until this file is public on GitHub.

## Why

The organisers' public reference script ("Model 2022 (not competing)", 0.4377 on the 2024
leaderboard, 3rd of 64) is the only outside check of this repository's scoring harness. In 0.1.1 it
found its inputs and ran for 7.9 minutes, then stopped inside bWGR's `mm()` with `contrasts can be
applied only to factors with 2 or more levels`, under R 4.6.2 and bWGR 2.2.18. bWGR 2.2.13
(CRAN, 2024-12-05) was the current release during the 2024 competition.

## Job `g2f-refr0-v2` (R + Python)

1. Installs bWGR 2.2.13 from the CRAN archive into its own library, next to the current release.
2. `run_ref.R` 0.1.2 runs the downloaded script **unmodified** with bWGR 2.2.13 first on the search
   path, and records the script's SHA-256 and the bWGR version it loaded. If the script fails, it
   prints the call stack and the size, column types and distinct Env/Hybrid counts of the objects
   the script had built (no yields).
3. `g2f_refcheck.py r0` (unchanged since 0.1.1) scores the prediction file on the released 2024
   answers and grades G1, G2 and P10.
4. For diagnosis only, the script is run again with the current bWGR (output in `cran/`, not graded).

Gates and predictions carried over unchanged from 0.1.1, graded on step 2's file only:

- **G1 (harness matches the leaderboard):** R0 within **0.01** of 0.43766. Point 0.85.
- **G2 (re-implementation faithful):** |full (0.4416) - R0| <= **0.005**. Point 0.70.
- **P10 (same predictions):** mean within-environment Pearson r between R0's and full's predictions
  (all template rows) **>= 0.99**. Point 0.60.

New:

- **P11:** under bWGR 2.2.13 the script runs to the end and writes its prediction file. Point 0.55.
- **P12:** under the current bWGR (step 4) it stops again with the same error. Point 0.80.

## What follows (fixed now)

- If P11 holds and G1 holds: this repository's 2024 places are confirmed by the organisers' own
  code. If G1 fails, every 2024 place here is marked unverified.
- If P11 holds and P12 holds: the failure is a bWGR version change. MV2 may open one issue on the
  reference script's repository saying so, with the R error and the two versions, once a person has
  read this result.
- If P11 fails: the diagnostics decide whether to try once more. Nothing in the script is ever
  edited.

## Limits

- One release, one season. The leaderboard score was produced by the organisers' own run, whose R
  and package versions are not published.

MV2, Munim, Inc., mv2@munimtech.com
