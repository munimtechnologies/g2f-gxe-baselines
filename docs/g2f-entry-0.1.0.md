# g2f-entry 0.1.0: build, check and score a G2F competition submission file

PREREG-MARKER: g2f-entry-0.1.0

Made with AI agents working in MV2's (Munim, Inc.) name. Code: Apache-2.0. Text: CC BY 4.0.
Written 2026-11-09, before the dry run below has been run.

## Why

The Genomes to Fields (G2F) 2026 maize GxE prediction competition is expected to open on 2026-11-16,
with a leaderboard from 2026-12-15 and the last submissions on 2027-01-15. Its About page (read
2026-11-09) says registered participants get 2014-2025 trial data plus 2026 weather and test-set
inputs, that each team's highest-scoring submission counts, and that submissions must be public on
EvalAI. The 2024 round allowed five submissions in total. Either way, a file that uploads but is
wrong is a lost try that scores near zero: rows shifted against the template, or an environment
holding one constant value. `g2f_entry.py` makes the file the same way every time and checks it
before upload. It also scores it locally against any year whose answers are public.

Note on the census pre-registration: `docs/g2f-release-census-0.1.0.md` predicted (R1) training
seasons 2014-2024 and framed R3 around 2024 yield rows. The About page now says training runs to
2025 and the test season is 2026, so R1 will most likely fail as written, and R3's quantity is
the share of template pairs whose hybrid has a yield row in the last training year (2025), which is
what both tools compute. Neither note is edited; the census result will report this.

## What it does (standard library only)

- `locate`: finds the trait, submission template, observed-values and genotype files in a release
  folder by their names (the same roles as `g2f_release_census.py`), with the years in each name.
- `seen`: counts how many distinct template (Env, Hybrid) pairs have a hybrid with a training yield
  row in any year, and in the last training year. It then applies rule R3 that
  `docs/g2f-release-census-0.1.0.md` fixed in advance: if at least 70% have a last-year row, the
  entry model is chosen on the 2023-like fold (repeated hybrids); otherwise on the 2024-like fold
  (mostly new hybrids).
- `write`: fills `Yield_Mg_ha` in the template from any predictions CSV (Env, Hybrid and a value
  column), keeping the template's columns and row order. A template row with no prediction stops it,
  unless `--fill env_mean` is given. A pair listed twice with different values stops it.
- `validate`: the submission must have the template's header, the same number of rows, the same
  Env/Hybrid in every row in the same order, and a finite number in every yield cell. It warns (but
  does not fail) when an environment has one constant prediction (that environment scores 0) or
  when values fall outside 0-30 Mg/ha. Exit code 1 on any error.
- `score`: the competition metric as MV2's earlier harness computes it. That is the mean
  within-environment Pearson r over environments with at least 3 observed pairs and non-constant
  observations; a constant prediction scores 0.
- `dryrun`: all of the above on a past release, plus five deliberately broken copies of the written
  submission (two rows swapped, one yield blank, last row dropped, yield column renamed, one yield
  "nan"), each of which `validate` must reject.

`test_g2f_entry.py` tests each part on small synthetic files.

## Dry run on the 2024 release (fixed now, graded by the job)

Data: the G2F 2024 competition release (CyVerse DOI 10.25739/78mn-4394), the same files MV2's
earlier jobs use. Predictions: MV2's adopted M4 model for 2024, as committed in this repository
(`results/g2f_parentgca_2024_predictions.csv`, column `M4`), whose published score is 0.3018.
Stated figures are in `data/g2f-entry-expect-2024.json` (the job's `expect_dryrun_2024.json`,
byte-identical).

| id | check | holds if |
|---|---|---|
| D1 | `locate` finds the trait, template, observed and numeric genotype files | all four found |
| D2 | every 2024 template row has an M4 prediction | 0 missing |
| D3 | the written submission validates | 0 errors |
| D4 | scoring the written file against the 2024 observed values reproduces M4's published score | 0.3018 within 0.0001, over 22 environments |
| D5 | each of the five broken copies is rejected | 5 of 5 |
| D6 | the seen share matches the baseline job's 0.1216, and rule R3 calls 2024 a new-hybrid year | share in 0.1211-0.1221 and setting `new_hybrids` |

D4 is the important one. It shows that a file made by `write` keeps every prediction on its own
row, all the way through to the score.

The job also reports two figures that are not stated in advance: how many 2024 template pairs have
a hybrid with a 2023 yield row (the R3 quantity on a year whose answer is known), and the
per-environment r.

If D1-D5 do not all hold, the tool is fixed before any 2026 file is uploaded. D6 tests the census
rule's arithmetic on a known year.

## Limits

- It checks the file against the template only. It cannot know rules the 2026 competition may add
  (file name, extra columns, upload size); read the 2026 rules on the release day.
- "Seen" compares hybrid names exactly, after trimming spaces; G2F renames some hybrids between
  seasons.
- A file that passes `validate` can still be a poor prediction; the score on past years is the only
  guide, and the 2026 answers are not public.
- No person has checked these results. Nothing here is agronomic advice.

MV2, Munim, Inc., mv2@munimtech.com
