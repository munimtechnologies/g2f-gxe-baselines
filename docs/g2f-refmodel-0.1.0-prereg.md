# g2f-refmodel 0.1.0: pre-registration

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed it yet. Text CC BY 4.0; code
Apache-2.0.

PREREG-MARKER: g2f-refmodel-0.1.0

Written 2026-11-08 (about 17:00 UTC), before the sealed job `g2f-refmodel-v1` ran. The job waits until
this file is public on GitHub before it fits or scores anything, so these predictions are fixed first.

## Why: MV2's entry model would have placed 40th

The 2024 G2F leaderboard is public (EvalAI challenge 2376, phase split 5893; read 2026-11-08 through
EvalAI's public API). It lists 64 entries, each a team's best mean within-environment Pearson r on the
2024 trials:

| Place | Entry | Mean r |
|---|---|---|
| 1 | Naaa | 0.4501 |
| 2 | NJUST_KMG1 | 0.4440 |
| 3 | **Model 2022 (not competing)** | **0.4377** |
| 4 | wer2 (not competing) | 0.4377 |
| 5 | PARaBra | 0.4371 |
| 10 | fortunehy | 0.4129 |
| 20 | DeepGE | 0.3676 |
| 39 | KAUSTians | 0.3071 |
| 40 | Hey | 0.3017 |
| 64 | Phenix | -0.0245 |

MV2's adopted entry model M4 scores **0.3018** on the organisers' released 2024 answers in this
repository's harness (g2f-parentgca 0.1.0). If that harness measures what the leaderboard measures, M4
would have placed **40th of 64** (38th of the 62 competing teams), 0.148 below the winner. The four
pre-registered studies in this repository that tried to improve on M4 gained at most 0.002.

The entry "Model 2022 (not competing)" links to a public R script by one of the competition's
organisers: github.com/alenxav/Lectures, `G2F_GxE_2024/script_model.R` (52 lines; the repository shows
no licence, so the script is **not** copied here; the job downloads it at run time and records its
SHA-256). As described from reading it, the script:

1. keeps only training environments whose two-letter **state** code (first two characters of `Env`,
   e.g. `IA` from `IAH4_2023`) appears in the 2024 test set;
2. keeps markers with variance above 0.01 in both the test hybrids and the training hybrids, imputes
   missing calls, builds a **Gaussian kernel** of the markers (bWGR `EigenGAU`) and turns it into
   principal-component covariates (`K2X`);
3. fits a **single-step mixed model** on raw plot yields with random environment and hybrid effects,
   the hybrid effect carried by those covariates (bWGR `mm`): a global marker effect **B1**;
4. centres yields within environment, reshapes them to a hybrid-by-environment matrix (environments with
   more than 100 hybrids), fits a **multivariate** model across environments (bWGR `ZSEMF`) and
   averages its environment-specific marker effects within each state: **B2**;
5. predicts each test hybrid in each state as its Gaussian-kernel covariates times (B1 + B2), centred,
   plus the state's mean yield.

Nothing in it uses weather, soil or management data. On the leaderboard it scores 0.4377, 0.136 above M4.
This study finds out whether that gap is real in MV2's harness, and where it comes from.

## Method (code: `run_ref.R`, `g2f_refmodel.R`, `g2f_refmodel.py`; tests: `test_g2f_refmodel.py`)

- **R0, the reference itself.** `run_ref.R` runs the downloaded script **unmodified** on the public 2024
  release (CyVerse DOI 10.25739/78mn-4394), with bWGR from CRAN (GPL-3; the version is logged), and
  keeps its prediction file. 2024 only, since the script is written for 2024.
- **Re-implementation.** `g2f_refmodel.R` is MV2's own code, written from the description above (not
  from a copy of the script), so the steps can be switched off one at a time and run on earlier years.
  It differs from the script in three small, logged ways: plots with no yield are dropped first; test
  hybrids without genotypes get only their state's mean (a constant within the environment); a state
  with no training environment kept falls back to B1. Variants:
  - **full** = B1 + B2 (the reference's model);
  - **b1** = global marker effect only;
  - **b2** = state-specific marker effects only;
  - **allloc** = full, but trained on every location instead of only the test states (it reuses the
    same marker filter and kernel, to save a second eigen-decomposition).
- **Folds.** 2024 (train 2014-2023, test = the released 2024 answers), 2023 (train before 2023) and
  2022 (train before 2022), the same three folds as every earlier study.
- **Blend.** On 2024, **blend** = 0.5 x the within-environment z-score of full + 0.5 x that of M4. The
  weight is fixed now at 0.5 and is not tuned. M4's 2024 predictions are read from this repository's
  committed `results/g2f_parentgca_2024_predictions.csv`, which also gives each 2024 row's
  seen-or-new-hybrid flag for the split.
- **Metric.** As in every earlier study: the mean over environments of the Pearson r inside each
  environment (at least 3 observed rows; a constant prediction scores 0). Each 2024 score is also placed
  on the 64-entry leaderboard (place = 1 + the number of entries scoring strictly higher).
- M4's reference points (published): 2022 **0.3262**, 2023 **0.4354**, 2024 **0.3018**.

## Gates

- **G1 (the harness matches the leaderboard):** R0 scored in this harness is within **0.01** of the
  leaderboard's 0.43766. If R0 does not run, G1 is "not run", the claims below rest on the
  re-implementation alone, and that is said in the result.
- **G2 (the re-implementation is faithful):** full is within **0.005** of R0 on 2024. If not, the
  ablations (P3, P4) are reported but flagged as possibly not describing the reference.

## Predictions

- **P1:** on 2024, the reference (R0, or full if R0 does not run) scores **at least 0.10 above M4**
  (>= 0.4018). Point 0.75.
- **P2:** full also beats M4 on **both** earlier folds (2022 > 0.3262 and 2023 > 0.4354). Point 0.55:
  M4 is strong on 2023, which is mostly previously grown hybrids.
- **P3:** on 2024, **b2 >= b1**: the state-specific marker effects carry at least as much as the global
  one. Point 0.55.
- **P4:** on 2024, training only on the test states helps: **full - allloc >= 0.005**. Point 0.55.
- **P5:** on 2024, the 50/50 **blend with M4 scores below full**: M4 adds nothing on top. Point 0.70.
- **P6:** on 2024, full ranks **new hybrids** (88% of rows) at **r >= 0.25**, against M4's 0.120: the
  gap is mostly about new hybrids. Point 0.60.

## Hypothesis and decision (fixed now)

- **H1 (switch the entry's baseline):** the reference beats M4 on 2024 by **at least 0.05** **and**
  full's mean over 2022 and 2023 is above M4's (0.3808). If H1 holds, MV2's 2026 entry starts from the
  re-implemented reference model (credited to its author in the entry and the code), and the next
  studies try to add to it (M4's own-mean shrinkage for seen hybrids, parent GCA, weather) on the
  2026 training data released on 2026-11-16. If H1 fails, the entry keeps M4 and the result says why.
- Either way the result reports every variant on every fold, the 2024 leaderboard place of each, and
  the seen/new split.

## Limits

- The description of the script was made by reading it; a step can still be misread, which is what G2
  checks. The script is the organisers' 2024 baseline, not the 2024 winner's model; nobody is claiming
  it is the best possible.
- The leaderboard scored teams' best submissions, chosen with feedback from that same leaderboard, so a
  placing computed here for a single fixed model is a rough guide, not a result.
- bWGR's current CRAN version (2.2.18, July 2026) may differ from the one used in January 2025; G1 is
  the check for that.
- Three folds, one data release. Whatever holds here is about the G2F 2014-2024 data and this metric.
