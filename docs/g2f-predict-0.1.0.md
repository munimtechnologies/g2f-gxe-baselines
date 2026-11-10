# g2f-predict 0.1.0: pre-registration (release-day entry builder, dry run on the 2024 release)

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed it yet. Text CC BY 4.0; code
Apache-2.0.

PREREG-MARKER: g2f-predict-0.1.0

Written 2026-11-10 (about 12:00 UTC), before the sealed job `g2f-predict-dry-v1` runs. The job waits
until this file is public on GitHub, then downloads and runs the published code. Nothing below has
been computed with `g2f_predict.py` yet.

## Why

The 2026 training data reach registered participants on 2026-11-16. Until now the Python side of this
repository could only build the 2024 entry. `g2f_baseline.fetch` looks for exact 2024 file names and
otherwise *downloads the 2024 files from CyVerse*, so a 2026 run could silently train and predict on
the wrong season. The graded pieces exist separately: M4 (g2f-parentgca 0.1.0), the switch mix
(g2f-switch 0.1.0, default a = b = 0.5), and the Mg/ha upload step (g2f-entry 0.2.0).
`g2f_predict.py` joins them for any release layout:

- `plan`: finds the trait, template and genotype files by role, in any sub-folder
  (`g2f_entry.find_release`). Reads the test season from the template's file name and counts the
  template pairs per hybrid category. Fits nothing.
- `predict`: M4 for every template pair, plus the kernel model's predictions from `g2f_refmodel.R`
  (`--full`), and the switch mix of the two. Each column becomes an Mg/ha upload file in the template's
  row order, which is then validated. If the release holds an observed-values file, every column and
  every file is scored.
- It never downloads anything. A missing trait, template or genotype file is an error (unit-tested
  with downloads disabled).

## Dry run (graded by the job's own `grade_expect`, expectations in `data/g2f-predict-expect-2024.json`)

On the G2F 2024 release volume, with the committed `results/g2f_refmodel_2024_predictions.csv` as `--full`:

- **P1:** the trait, template, genotype and observed files are found, and the test season is 2024.
- **P2:** M4 scores 0.3018 +- 0.0005 (published by g2f-parentgca 0.1.0 and reproduced exactly by g2f-switch).
- **P3:** the mix (a = b = 0.5) scores 0.4330 +- 0.0005 (g2f-switch 0.1.0 result).
- **P4:** all three Mg/ha files (M4, full, mix) validate against the template with every row present.
  M4 and the mix need no filled rows.
- **P5:** the written M4 and mix files score within 0.0002 of their unscaled columns, over 22
  environments, so the Mg/ha step changes no within-environment r.

Also reported, not graded: the plan output (files, season, category counts, share of pairs grown
before), full's score (expected 0.4416), the scores by category, and the Mg/ha spread.

## What follows

- If P1-P5 hold, `g2f_predict.py predict` is how every 2026 upload file is built. Run order: census of
  the 2026 release; `g2f_refmodel.R <release> <out> test` for `full`; then `g2f_predict.py predict --full
  <out>/preds/2026.csv`. The g2f-switch study is rerun on the 2026 release first, as pre-registered.
- If any item fails, no 2026 file is built with it until the cause is found and a fixed version passes
  its own dry run.
- Uploads go through Sheehan Munim's EvalAI team account, and only when he says so.

## Limits

- This checks plumbing and reproduction on a past season, not skill on 2026.
- The 2026 file names and metric are not known yet. If the metric is an error measure (for example
  RMSE), the Mg/ha level matters and this tool's level rule (site history) is known to run about
  1 Mg/ha low on 2024 (g2f-entry 0.2.0).

MV2, Munim, Inc., mv2@munimtech.com
