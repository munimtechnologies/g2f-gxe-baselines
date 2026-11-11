# g2f-2026-release 0.1.0: what the 2026 training release should look like (pre-registered before it exists)

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed it yet. Text CC BY 4.0; code
Apache-2.0. Not agronomic advice.

PREREG-MARKER: g2f-2026-release-0.1.0

Written 2026-11-11 (about 03:45 UTC), five days before the G2F 2026 competition's training data go to
registered participants (2026-11-16, maizegxeprediction.org). No 2026 file has been seen. These
predictions are graded by hand from the outputs of the tools already in this repository, run unchanged on
the release (`g2f_release_census.py`, `g2f_predict.py plan`, `g2f_cathistory.py`-style categories and
`g2f_refold.py choose`). They are graded only if MV2's team receives the release; if it does not, this
note stays ungraded and says so.

## Why

Every decision for the 2026 entry has been fixed in advance from the 2015-2024 seasons: the mix weights
(g2f-switch, g2f-refold), the upload order (g2f-2026-portfolio 0.1.0) and the yield-level rule for an
error metric (g2f-levelmeta 0.1.0: `--folds 4`). Those decisions assume the 2026 release looks like
past releases. This note writes down what that assumption means in numbers, so release day can show
which parts still hold before anything is fitted.

## Predictions

Definitions as in g2f-cathistory 0.1.0: a test pair is *seen* if its hybrid has a yield record in any
earlier season, *new_one* if the hybrid is new but exactly one parent line was used in an earlier
hybrid, *new_both* if both were, and *new_none* if neither was.

- **R1 (layout):** the release holds the same roles as 2024 (trait/yield table, metadata, genotype
  matrix, environmental covariates, weather, soil, submission template), and `g2f_predict.py plan` finds
  every role without a code change. Training yield records end with the 2025 season.
- **R2 (new-hybrid season):** 2026 is an even season, so at most 25% of template pairs are *seen*
  (even seasons since 2018: 7-22%), and `g2f_refold.py choose --folds 4` types 2026 as a new-hybrid
  season (below its 0.70 threshold).
- **R3 (matched folds):** with `--folds 4` the candidate hold-out seasons are 2025, 2024, 2023 and 2022,
  and the folds matching the 2026 type are 2024 and 2022.
- **R4 (checks and testers):** the template holds at least 15 of the 19 check hybrids named for 2026 on
  genomes2fields.org, and every one present is *seen*. At least a third of the new hybrids in the template
  have LH287 or LH244 as a parent.
- **R5 (size):** the template covers between 15 and 35 environments.
- **R6 (the open question, stated as a guess):** at least 20% of template pairs are *new_none*. This is
  the least certain prediction. It rests on the about 300 paired crosses between 150 lines whose origin
  G2F has not stated; if those lines were used before, it fails. If it holds, the 2016 study
  (the only past season with many *new_none* pairs, 23.7%) is run before the first upload.

## What each outcome changes

- R1 fails: no modelling until the tools are fixed in a new tested version, graded on the 2024 release
  again.
- R2 or R3 fails: the refold choice is still made by `g2f_refold.py` as registered, but
  g2f-2026-portfolio 0.2.0 must say why the season looks different and whether slot 1 should stay the
  refold choice.
- R4 or R5 fails: reported only; no decision depends on them.
- R6 holds: the 2016 study first, as above. R6 fails: no extra study.

None of these outcomes changes the level decision (g2f-levelmeta 0.1.0), which applies only if the 2026
round is scored by error, nor the upload order, which can only change through version 0.2.0 of the
portfolio note.

## Limits

- The 2026 trial design is taken from genomes2fields.org (read 2026-11-09). The organisers may release
  only part of it, or add trials.
- Grading needs the release, which goes only to registered participants; MV2's team registration is
  with Sheehan Munim. Uploads go through his EvalAI team account, and only when he says so.

MV2, Munim, Inc., mv2@munimtech.com
