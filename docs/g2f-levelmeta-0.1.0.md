# g2f-levelmeta 0.1.0: pre-registration (how many past seasons should choose the yield-level rule?)

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed it yet. Text CC BY 4.0; code
Apache-2.0. Not agronomic advice.

PREREG-MARKER: g2f-levelmeta-0.1.0

Written 2026-11-10 (about 20:45 UTC), before the sealed job `g2f-levelmeta-dry-v1` runs. The job waits
until this file is public on GitHub, then downloads and runs the published code. Seasons 2015-2021 have
not been scored with `g2f_level.py` yet. Seasons 2022, 2023 and 2024 are already known from
[g2f-level 0.1.0](g2f-level-0.1.0-result.md); the predictions below say which parts that knowledge
already settles.

## Why

g2f-level 0.1.0 chose the yield-level rule on two hold-out seasons and kept site history (site_all),
but each of the three seasons scored so far had a different best rule (2023: trend, 2022: site history,
2024: the location's last three seasons). Two seasons may be too few to choose on. If the 2026 round is
scored by error, the level is most of the score, so how the rule is chosen on the 2026 release should be
settled now, on past seasons, and not after seeing 2026 data.

## Method

1. Run `g2f_level.py choose` 0.1.0, unchanged, on the 2024 release with `--folds 9`. This scores all six
   rules on every season from 2015 to 2023, each trained on earlier seasons only, plus the 2024 answers.
2. `g2f_levelmeta.py` (new, standard library only) replays the choice for every target season s that
   has at least 4 earlier scored seasons (so s = 2019-2024, six targets). For s it chooses the rule on
   the k most recent scored seasons before s, the way `g2f_level.py choose --folds k` would on a release
   ending the season before s (lowest mean level RMSE rounded to 4 places; ties to the earlier rule),
   for k = 1, 2, 4 and all. It scores the chosen rule on s.
3. It compares, by mean level RMSE over the six targets: the four ways of choosing (k=1, k=2, k=4,
   k=all) and each fixed rule.

## Decision (applies only if the 2026 metric is error-based)

Among the four ways of choosing and fixed site_all, the lowest mean level RMSE over 2019-2024 (rounded to
4 places) sets how the 2026 level is chosen. Ties go, in order, to fixed site_all, then k=all, k=4,
k=2, k=1. If it is a k, the 2026 run uses `g2f_level.py choose --folds k` (k=all: `--folds 99`) on the
2026 release and that rule's levels. If it is fixed site_all, the entry keeps g2f-entry 0.2.0's levels.
No other fixed rule can be chosen this way: picking the best fixed rule over the same six seasons would
be a choice made on the answers.

## Checks (graded by `grade`, expectations in `data/g2f-levelmeta-expect-2024.json`)

- **M1 (reproduction):** the 9-fold run gives the same per-rule level RMSE as g2f-level 0.1.0 for the
  2023 and 2022 folds and the 2024 check (all 18 numbers within 0.0001), and the targets are
  2019-2024.
- **M2 (prediction):** choosing on all earlier seasons (k=all) has a lower mean level RMSE over the
  targets than choosing on two (k=2, today's default).
- **M3 (prediction):** recent_mean (one constant for every environment) has the highest mean level RMSE
  of the six fixed rules. Locations differ in level more than seasons do.
- **M4 (prediction):** choosing gains little: no way of choosing beats fixed site_all's mean by more than
  0.15 Mg/ha.
- **M5 (prediction):** in every target season, even the best rule misses by at least 1.2 Mg/ha level
  RMSE. Already true for 2022-2024 (best 2.65, 1.60, 1.97), so only 2019-2021 can break it.

Also reported, not graded: the best rule of each target season, how often each rule is best, each k's
choice for every target, and what each k would choose from all seasons up to 2024.

## Limits

- Six targets, half of them already seen; any difference under about 0.1 Mg/ha is noise.
- Early targets have short histories (2019 is chosen on 2015-2018 alone), which favours rules that need
  little history.
- Locations are matched by site code, as in g2f_entry; the 2026 trials may add new locations.
- Uploads go through Sheehan Munim's EvalAI team account, and only when he says so.

MV2, Munim, Inc., mv2@munimtech.com
