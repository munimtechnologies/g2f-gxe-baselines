# g2f-levelmeta 0.1.0: result (5 of 5 held; the 2026 level rule is chosen on the 4 most recent seasons, by a margin inside the noise)

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed it yet. Text CC BY 4.0; code
Apache-2.0. Not agronomic advice.

RESULT-MARKER: g2f-levelmeta-0.1.0-result

Grades the pre-registration [`docs/g2f-levelmeta-0.1.0.md`](g2f-levelmeta-0.1.0.md) (written 2026-11-10
about 20:45 UTC). The sealed job `g2f-levelmeta-dry-v1` started at 01:37 UTC on 2026-11-11. It waited
for that file to be public, then downloaded the published `g2f_entry.py`, `g2f_level.py`,
`g2f_levelmeta.py`, the test and the expectations, and passed the unit tests. It then ran the unchanged
`g2f_level.py choose --folds 9` on the G2F 2024 release, followed by `g2f_levelmeta.py` (standard library
only, 1 CPU, 1 GB, 75 s in all). Outputs:
[`results/g2f_level_folds9_2024.json`](../results/g2f_level_folds9_2024.json) and
[`results/g2f_levelmeta_2024.json`](../results/g2f_levelmeta_2024.json).

## Grades

| Check | Held? | What came out |
|---|---|---|
| M1 reproduction | **held** | all 18 per-rule level RMSEs for fold 2023, fold 2022 and the 2024 check equal g2f-level 0.1.0's to 4 places; targets are 2019-2024 |
| M2 all seasons beat two | **held** | k=all 2.1840 vs k=2 2.2888 Mg/ha |
| M3 recent_mean worst fixed rule | **held** | recent_mean 2.6725; the other five fixed rules lie between 2.1269 and 2.1885 |
| M4 choosing gains little | **held** | best way of choosing (k=4) 2.1590 vs fixed site_all 2.1885: 0.03 Mg/ha better, far under the 0.15 bar |
| M5 level floor in every target | **held** | best rule in each target: 2019 2.266, 2020 1.721, 2021 1.672, 2022 2.651, 2023 1.600, 2024 1.966 Mg/ha; none below 1.2 |

## The numbers

Mean level RMSE (Mg/ha) over the six target seasons 2019-2024. Each target's levels are built from earlier
seasons only and scored against that season's observed environment means.

| Way of choosing the rule | Mean level RMSE |
|---|---|
| **k=4: choose on the 4 most recent earlier seasons** | **2.1590** |
| k=all: choose on every earlier season | 2.1840 |
| fixed site_all (today's level) | 2.1885 |
| k=1: choose on the last season | 2.2297 |
| k=2: choose on the last two seasons (g2f-level 0.1.0's default) | 2.2888 |

What each way of choosing picked, and its RMSE, per target (site_all for comparison):

| Target | k=1 | k=2 | k=4 | k=all | site_all | best rule in hindsight |
|---|---|---|---|---|---|---|
| 2019 | shrunk 2.729 | shrunk 2.729 | shrunk 2.729 | shrunk 2.729 | 2.652 | trend 2.266 |
| 2020 | trend 2.130 | trend 2.130 | shrunk 1.816 | shrunk 1.816 | 1.779 | anomaly 1.721 |
| 2021 | anomaly 1.836 | anomaly 1.836 | shrunk 1.672 | shrunk 1.672 | 1.946 | shrunk 1.672 |
| 2022 | shrunk 2.837 | shrunk 2.837 | shrunk 2.837 | shrunk 2.837 | **2.651** | site_all 2.651 |
| 2023 | site_all 1.720 | shrunk 1.817 | anomaly 1.686 | shrunk 1.817 | 1.720 | trend 1.600 |
| 2024 | trend 2.126 | site_all 2.383 | anomaly 2.214 | shrunk 2.233 | 2.383 | recent3 1.966 |

(shrunk = site_anomaly_shrunk, anomaly = site_anomaly, trend = site_anomaly_trend, recent3 = site_recent3.)

The six fixed rules over the same targets (reported, not choosable, because picking among them here would
be a choice made on the answers): site_anomaly 2.1269, site_anomaly_trend 2.1355, site_recent3 2.1752,
site_anomaly_shrunk 2.1840, site_all 2.1885, recent_mean 2.6725. Best rule per target: trend twice,
and site_all, recent3, anomaly and shrunk once each; recent_mean never.

Earlier seasons, scored here for the first time (each trained only on the seasons before it), best rule
per season: 2015 shrunk 1.92, 2016 trend 1.75, 2017 shrunk 2.27, 2018 shrunk 2.03, 2019 trend 2.27,
2020 anomaly 1.72, 2021 shrunk 1.67. With all ten seasons up to 2024, k=1 would choose site_recent3,
k=2 and k=4 the trend rule, and k=all the shrunk anomaly.

## The decision for 2026 (applies only if the 2026 round is scored by error)

By the pre-registered rule, the lowest mean among the four ways of choosing and fixed site_all wins:
**k=4**. If the 2026 metric is error-based, the 2026 levels come from
`python g2f_level.py choose --data-dir <2026 release> --out-dir <out> --folds 4` (on the 2026 release
the four most recent training seasons should be 2025, 2024, 2023 and 2022), and the entry uses that
rule's levels. The runner-up is **k=all** (2.1840, `--folds 99`). It is the "level rule that came second"
for slot 3 of [g2f-2026-portfolio 0.1.0](g2f-2026-portfolio-0.1.0.md). If k=4 and k=all choose the same
rule on the 2026 release, slot 3 would duplicate slot 1 and is skipped by that note's duplicate rule.

Read this decision for what it is. k=4 beats fixed site_all by 0.03 Mg/ha. That is well inside the
0.1 Mg/ha the pre-registration called noise, and k=4 beats site_all in only 3 of the 6 targets (2021,
2023, 2024). Most of its edge comes from 2021 (-0.27) and 2024 (-0.17). The rule was fixed in advance,
so it is followed. The honest summary is that **choosing a level rule from history is about as good as
not choosing at all**, and the 2026 level will still be roughly 2 Mg/ha off whichever way it is picked.

## What this means

- **History cannot find the season's level.** In the ten seasons from 2015 to 2024, the best of the six
  history rules missed the environment means by 1.60 to 2.65 Mg/ha (level RMSE; lowest: the trend rule on
  2023), and the season-to-season swings
  are larger than the differences between rules. If the 2026 round is scored by error, the gain has to
  come from in-season information (the weather and environmental covariates of the test trials), not
  from a cleverer way of averaging past seasons. The in-season level study is next if the 2026 rules
  name an error metric.
- **Choosing on two seasons was the worst way to choose** (k=2, 2.29), worse than never choosing. This is
  the same lesson as in the mix-weight studies: a choice made on few seasons is mostly noise.
- All of this matters only for an error metric. The 2024 round scored mean within-environment Pearson r,
  which ignores levels. The 2026 metric is read when the training data are released (2026-11-16).

## Limits

- Six targets, three of them (2022-2024) already seen before the run; M1 and M5's 2022-2024 parts were
  known in advance. Only the 2019-2021 targets and the comparisons across ways of choosing were new.
- Early targets have short histories (2019 is chosen on 2015-2018), which favours rules that need little
  history.
- Locations are matched by site code, as in `g2f_entry`; the 2026 trials may add new locations.
- Uploads go through Sheehan Munim's EvalAI team account, and only when he says so.

MV2, Munim, Inc., mv2@munimtech.com
