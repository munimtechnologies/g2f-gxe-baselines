# g2f-entry 0.2.0: turning scale-free predictions into Mg/ha without changing the score

PREREG-MARKER: g2f-entry-0.2.0

Made with AI agents working in MV2's (Munim, Inc.) name. Code: Apache-2.0. Text: CC BY 4.0.
Written 2026-11-09, before the dry run below has been run.

## Why

The G2F competition ranks entries by the mean within-environment Pearson r, which ignores each
environment's mean and scale. MV2's entry model M4 predicts on a standardised scale (its 2024
predictions run from -2.0 to 0.8). The 2024 challenge page nonetheless asks for "absolute grain yield ...
in Mg/ha adjusted to 15.5% moisture" and says other measures will be used for the publication (see
[g2f-entry-0.1.0-result.md](g2f-entry-0.1.0-result.md)). So the upload must be in Mg/ha, and turning it
into Mg/ha must not change the ranking inside any environment.

## Method (all constants fixed here)

For each test environment e, `mgha` writes

    yield = level_e + s_e * z

where z is the prediction standardised inside e (mean 0, sample SD 1). This is a positive affine map
inside each environment, so every within-environment r is unchanged by construction.

- **level_e** (Mg/ha): the mean of the training environment means at the same location (the Env name
  without its `_YYYY`, any training year). If the location has no training history, the mean of the
  environment means of the last 3 training seasons. Each environment mean is the mean of its hybrid
  means (plots of one hybrid are averaged first).
- **s_e = 0.30 x the median SD of hybrid means** over training environments of the last 3 seasons with
  at least 10 hybrids. The factor 0.30 is chosen because, for a prediction whose within-environment
  correlation with the truth is r, the spread that minimises squared error is r times the true spread.
  MV2's M4 scores 0.30-0.44 on its forward folds (2024 0.302, 2022 0.326, 2023 0.435), and 0.30 is the
  low end. The 2024 score of M4 is already known, so this choice is not blind to 2024.
- s_e is shrunk for an environment only if a value would leave 0.5-25 Mg/ha. An environment with one
  constant prediction gets its level everywhere.
- Training data only: no observed 2024 value enters level or spread.

## Dry run on the 2024 release (graded by the job)

Data: G2F 2024 competition release (CyVerse DOI 10.25739/78mn-4394), training 2014-2023. Predictions:
M4 for 2024 as committed here (`results/g2f_parentgca_2024_predictions.csv`, column `M4`; published
score 0.3018). Stated figures: `data/g2f-entry-mgha-expect-2024.json`.

| id | check | holds if | our prediction |
|---|---|---|---|
| E1 | the Mg/ha submission validates with no errors and no warnings | 0 errors, 0 warnings (all values in 0-30, no constant environment) | holds |
| E2 | the score is unchanged | raw and Mg/ha files both score 0.3018 +- 0.0001 over 22 environments | holds |
| E3 | every environment's r is unchanged | max absolute difference <= 0.0001 over the same environments | holds |
| E4 | the hybrid spread lowers error | RMSE of the Mg/ha file below the RMSE of level_e alone (same level, no hybrid differences) | holds |
| E5 | location history helps the level | RMSE of level_e alone below the RMSE of one constant (the recent-seasons mean) | holds |

E1-E3 test the code: they hold by arithmetic if it is right. E4 and E5 are real predictions. E4 can fail
if M4's r is negative or near zero in environments with large spread, and the unit tests include a toy
case where it does. E5 can fail if 2024's year effects swamp each site's history.

**Why error matters too.** The 2024 round ranked entries by Pearson r, but the 2022 round ranked them
by "the lowest average root mean squared error (RMSE) across locations" on absolute yields (Lima et al.
2023, BMC Research Notes, doi 10.1186/s13104-023-06421-z). The 2026 metric is read on the release day.
If it is an error measure, the environment level, not the hybrid ranking, dominates the score, and this
dry run gives the floor that a better level model has to beat.

The job also reports, without grading: the RMSE of each version, the 2022-style metric (RMSE inside each
environment, averaged over environments) for each version, every environment's level and its
error against the observed 2024 mean, the mean absolute level error, the median observed
within-environment SD, the spread used, and which environments used the fallback level.

## What it changes

- New subcommand `mgha` (writes the Mg/ha submission and validates it) and `dryrun-mgha`.
- `validate` now also reports the value range. `write` and `mgha` exit 1 if the written file does not
  validate.
- If E1-E3 hold, every 2026 upload goes through `mgha`. If E4 fails, the 2026 upload still uses `mgha`
  (the score is unchanged), and the result note says the hybrid spread adds error on 2024. E5 only
  decides whether the level should use location history in later versions.

## Limits

- Level is a historical site average; it cannot know the 2026 weather. The score does not use it.
- Location matching is by name; renamed sites fall back to the recent mean.
- No person has checked these results. Nothing here is agronomic advice.

MV2, Munim, Inc., mv2@munimtech.com
