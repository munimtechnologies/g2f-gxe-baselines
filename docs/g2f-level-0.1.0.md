# g2f-level 0.1.0: pre-registration (choosing each environment's yield level, in case 2026 is scored by error)

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed it yet. Text CC BY 4.0; code
Apache-2.0. Not agronomic advice.

PREREG-MARKER: g2f-level-0.1.0

Written 2026-11-10 (about 16:50 UTC), before the sealed job `g2f-level-dry-v1` runs. The job waits until
this file is public on GitHub, then downloads and runs the published code. Nothing below has been
computed with `g2f_level.py` on real data yet. The reproduction numbers in L1 come from the published
`results/g2f_entry_mgha_2024.json` (g2f-entry 0.2.0); the env-level RMSE 2.3829 was computed by hand from
its 22 published per-environment level errors.

## Why

The 2024 round scored the mean Pearson r inside each environment, which ignores each environment's
yield level. The 2022 round scored RMSE inside each location, which does not. The 2026 metric will only
be known when the training data come out (2026-11-16). g2f-entry 0.2.0 showed that under an error metric
the level dominates: its site-history levels (the mean of every past environment at the same location)
missed the 22 scored 2024 environments' means by 2.04 Mg/ha on average and were 0.97 Mg/ha too low on
average, while the hybrid ranking lowered the RMSE by only 0.05 Mg/ha. g2f-entry's result named a
level from recent seasons or a yield trend as the thing to pre-register and test on the 2022 and 2023
folds first. This is that test, done before the 2026 metric is known, so the tool is ready either way.

## The tool

`g2f_level.py choose` (standard library only; needs `g2f_entry.py` 0.2.0) builds levels from training
environment means only (mean of per-hybrid means, `g2f_entry.training_env_stats`) with six fixed rules:

| Rule | Level for a test environment |
|---|---|
| site_all | mean of all training environments at the same location (any year); else the recent mean. Exactly `g2f_entry.scale_plan`, today's level. |
| site_recent3 | mean of the location's 3 most recent training environments; else the recent mean |
| recent_mean | one constant: mean of the environment means of the last 3 training seasons |
| site_anomaly | recent mean + the location's mean anomaly (environment mean minus its season's mean); a new location uses its state's (first two letters) mean anomaly, else 0 |
| site_anomaly_shrunk | as site_anomaly, with the anomaly multiplied by n / (n + 2) |
| site_anomaly_trend | as site_anomaly, with a least-squares line of environment mean on year (all training environments) as the base, read at the test season |

The constants (3 seasons, k = 2, at least 3 hybrids per hold-out target) are fixed here and not tuned.
It holds out each of the `--folds` most recent training seasons (default 2; on the 2024 release 2023
and 2022), training on earlier seasons only, and scores each rule by the RMSE of its levels against that
season's environment means. It chooses the rule with the lowest mean RMSE over the folds; ties go to the
earlier rule in the table. With an observed-values file (a past season) it also scores every rule on it:
level RMSE, MAE and bias (level minus observed mean) over environments, and the level-only upload
scored by pooled RMSE over pairs and by the 2022 metric (RMSE inside each environment, averaged).

## Dry run on the 2024 release (graded by `grade_expect`, expectations in `data/g2f-level-expect-2024.json`)

- **L1 (reproduction):** test season 2024, folds [2023, 2022]. On the 2024 answers, site_all gives pooled
  RMSE 2.9517, 2022-metric RMSE 2.8497, level MAE 2.0354, bias -0.9707 and level RMSE 2.3829; recent_mean
  gives pooled RMSE 3.1882 and 2022-metric RMSE 3.0862. Each within 0.0005.
- **L2 (prediction):** the rule chosen on the 2022 and 2023 folds is not site_all. Older seasons drag the
  all-years site mean away from the current level.
- **L3 (prediction):** the chosen rule's level RMSE on 2024 is below site_all's (2.3829).
- **L4 (prediction):** every rule's mean bias on 2024 is negative. No rule built only from past seasons
  foresees that 2024 was a high-yield season (g2f-entry: 14 of 22 environments above their level).
- **L5 (prediction):** every rule's level RMSE on 2024 is at least 1.5 Mg/ha. Site history alone cannot
  say how good a season will be; that needs weather or other in-season data.
- **L6 (prediction):** on the folds, site_anomaly_shrunk has a lower mean RMSE than site_anomaly.
  Locations with one or two seasons give noisy anomalies.

Also reported, not graded: per-fold scores for every rule, each rule's worst three misses, the season
means, the trend slope, and the chosen rule's levels for the template.

## What follows

- If L1 holds and the 2026 rules turn out to score error (RMSE or similar), the rule chosen on the 2026
  release's own folds sets the levels, through `g2f_level.entry_plan` (g2f_entry's plan with the levels
  replaced). That wiring into `g2f_predict.py` is a separate, tested change, made only if the 2026
  metric needs it.
- If 2026 is scored by within-environment r again, nothing changes: levels do not affect that score.
- If L1 fails, the difference from g2f-entry 0.2.0 is found before any level is used.
- If L5 fails for some rule, that rule is reported as a strong level; if L5 holds, the next level study
  is in-season covariates (weather), pre-registered separately.
- Uploads go through Sheehan Munim's EvalAI team account, and only when he says so.

## Limits

- One graded season (2024). Two folds to choose on. Level RMSE over about 20 environments is noisy.
- The 2024 numbers in L1 were known before this was written; only L2-L6 are predictions.
- Locations are matched by name (G2F's site code before the year), as g2f_entry does; a renamed field
  counts as a new location.

MV2, Munim, Inc., mv2@munimtech.com
