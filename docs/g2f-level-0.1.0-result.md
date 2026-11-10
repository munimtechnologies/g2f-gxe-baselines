# g2f-level 0.1.0: result (3 of 6 held; the hold-out seasons kept today's site-history level)

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed it yet. Text CC BY 4.0; code
Apache-2.0. Not agronomic advice.

RESULT-MARKER: g2f-level-0.1.0-result

Grades the pre-registration [`docs/g2f-level-0.1.0.md`](g2f-level-0.1.0.md) (written 2026-11-10 about
16:50 UTC). The sealed job `g2f-level-dry-v1` started at 20:06 UTC on 2026-11-10, waited for that file to
be public, downloaded the published `g2f_entry.py`, `g2f_level.py`, its test and the expectations, passed
the unit tests, and ran `g2f_level.py choose` on the G2F 2024 release (standard library only, 77 s).
Output: [`results/g2f_level_2024.json`](../results/g2f_level_2024.json).

## Grades

| Check | Held? | What came out |
|---|---|---|
| L1 reproduction | **held** | all 7 numbers within 0.0005: site_all pooled RMSE 2.9517, 2022-metric 2.8497, MAE 2.0354, bias -0.9707, level RMSE 2.3831 (the hand figure 2.3829 came from rounded per-environment errors); recent_mean 3.1882 and 3.0862 |
| L2 choice is not site_all | **failed** | the 2022 + 2023 folds chose **site_all** (mean level RMSE 2.1852), just ahead of site_anomaly (2.1963) and site_anomaly_trend (2.2135) |
| L3 choice beats site_all on 2024 | **failed** | follows from L2: the chosen rule is site_all, 2.3831 both ways |
| L4 every rule too low on 2024 | **held** | bias from -0.24 (trend) to -1.09 (recent_mean) Mg/ha |
| L5 no rule below 1.5 Mg/ha on 2024 | **held** | lowest is site_recent3 at 1.9662 |
| L6 shrinking the anomaly helps on the folds | **failed** | the opposite: shrunk 2.3272 vs unshrunk 2.1963 (and 2.2326 vs 2.2141 on 2024) |

## The numbers

Level RMSE (Mg/ha) of each rule's environment levels against the observed environment means. Folds train
on earlier seasons only; 2024 trains on 2014-2023 and is scored on the organisers' released answers
(22 scored environments). The last column is the level-only upload scored by the 2022 metric (RMSE inside
each environment, averaged).

| Rule | fold 2023 | fold 2022 | folds mean | 2024 level RMSE | 2024 bias | 2024, 2022 metric |
|---|---|---|---|---|---|---|
| site_all (today's level) | 1.7199 | **2.6506** | **2.1852** | 2.3831 | -0.9707 | 2.8497 |
| site_recent3 | 1.8262 | 2.7166 | 2.2714 | **1.9662** | -0.5109 | **2.6068** |
| recent_mean | 2.6694 | 3.3957 | 3.0326 | 2.7088 | -1.0851 | 3.0862 |
| site_anomaly | 1.6857 | 2.7069 | 2.1963 | 2.2141 | -0.6640 | 2.7499 |
| site_anomaly_shrunk | 1.8174 | 2.8371 | 2.3272 | 2.2326 | -0.7472 | 2.7615 |
| site_anomaly_trend | **1.5998** | 2.8272 | 2.2135 | 2.1262 | **-0.2437** | 2.7087 |

Three seasons, three different winners: the trend rule on 2023, site history on 2022, and the location's
last three seasons on 2024. The 2022 fold is the one that kept site_all in front, and one environment
dominates it: every rule put GEH1_2022's level 7.7-9.5 Mg/ha above what it yielded. Removing GEH1_2022
by hand (from the published RMSEs and worst misses) does not change that fold's winner: site_all 2.04,
site_anomaly 2.11, site_recent3 2.13, trend 2.23, shrunk 2.37. On 2024, NEH3_2024 was the worst miss for
five of the six rules (3.6-5.3 Mg/ha too low). The 2024 environments averaged 10.76 Mg/ha; the trend line
read 10.09 at 2024 (slope +0.13 Mg/ha a year) and the last three seasons' mean was 9.67.

## What this means

- **The pre-registered procedure keeps site_all**, the level g2f-entry 0.2.0 already uses, so nothing
  in the entry changes. In hindsight site_recent3 would have lowered the 2024 level RMSE by 0.42 Mg/ha and
  the 2022-metric score by 0.24, but it was not chosen and is not claimed.
- **No rule built from past seasons gets the level closer than about 2 Mg/ha** (L5), and every rule was
  too low in a high-yield season (L4). History alone cannot see how good a season will be.
- **The folds disagree with each other** more than the rules differ, so choosing on two seasons is close
  to a coin toss. The next study, [g2f-levelmeta 0.1.0](g2f-levelmeta-0.1.0.md), replays the choice on
  every season from 2019 to 2024 with 1, 2, 4 or all earlier seasons, to settle how the level rule is
  chosen on the 2026 release.
- All of this matters only if the 2026 round is scored by error. The 2024 round scored within-environment
  correlation, which ignores levels. The 2026 metric is read when the training data come out
  (2026-11-16). If it is an error metric, the in-season (weather) level study named in the
  pre-registration comes next.

## Limits

- One graded season, two folds, about 20-28 environments each; level RMSE at this size is noisy.
- The L1 numbers were known before the run; only L2-L6 were predictions.
- GEH1_2022 was not looked into beyond the hand removal above; it may be a data or location issue.

MV2, Munim, Inc., mv2@munimtech.com
