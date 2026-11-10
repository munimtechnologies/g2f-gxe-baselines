# g2f-entry 0.2.0: result (the Mg/ha step leaves the score unchanged; the site level is the weak part)

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed it yet. Text CC BY 4.0; code
Apache-2.0.

RESULT-MARKER: g2f-entry-0.2.0-result

Graded 2026-11-10 (about 05:00 UTC) against [the pre-registration](g2f-entry-0.2.0.md), written before
the dry run. Sealed job `g2f-mgha-dryrun-v1` finished 2026-11-10 01:49 UTC (3 minutes). Raw output:
[`results/g2f_entry_mgha_2024.json`](../results/g2f_entry_mgha_2024.json).

Data: G2F 2024 competition release (CyVerse DOI 10.25739/78mn-4394), training 2014-2023, scored on the
organisers' released 2024 answers (9,486 scored pairs in 22 environments; the template has 10,057
pairs in 23). Predictions: MV2's M4, as committed in `results/g2f_parentgca_2024_predictions.csv`.

## All five checks held

| id | check | value | held? |
|---|---|---|---|
| E1 | Mg/ha file validates, 0 errors, 0 warnings | 10,057 rows, 23 environments, values 0.50-13.19 Mg/ha | **yes** |
| E2 | score unchanged (0.3018 +- 0.0001, 22 environments) | raw 0.3018, Mg/ha 0.3018 | **yes** |
| E3 | every environment's r unchanged (<= 0.0001) | largest difference 6e-8 | **yes** |
| E4 | hybrid spread lowers error (RMSE below level alone) | 2.9016 vs 2.9517 Mg/ha | **yes** |
| E5 | site history beats one constant | level alone 2.9517 vs recent-seasons mean 3.1882 | **yes** |

Every environment's level came from its own site's training history except one: ONH3 had no
history and used the recent-seasons mean (9.67 Mg/ha). The spread was 0.30 x 1.76 = 0.53 Mg/ha per
standard unit. One environment (SCH1, level 4.53 Mg/ha, not scored) had its spread shrunk to stay
above 0.5 Mg/ha.

**What follows (fixed in the pre-registration):** E1-E3 hold, so every 2026 upload goes through
`g2f_entry.py mgha`. E5 holds, so the level keeps using site history.

## What the dry run says about an error-based metric (reported, not graded)

| Version | RMSE over all pairs | 2022-style metric (RMSE inside each environment, averaged) |
|---|---|---|
| recent-seasons mean (one constant) | 3.188 | 3.086 |
| site level only | 2.952 | 2.850 |
| site level + M4 spread (`mgha`) | **2.902** | **2.799** |

- **The level, not the hybrid ranking, dominates the error.** The site levels miss each 2024
  environment's observed mean by 2.04 Mg/ha on average (absolute), more than the typical spread of
  hybrids inside an environment (median SD 1.86 Mg/ha). Adding M4's hybrid differences lowers the
  RMSE by only 0.05 Mg/ha.
- **The miss is mostly one-sided.** In 14 of 22 environments the site's history was below the 2024
  mean; on average the level was 0.97 Mg/ha too low (largest misses: NEH3 -5.29, MOH1 -3.74, NYH2
  -3.59, OHH1 -3.57 Mg/ha). A level that follows each site's recent seasons, or a yield trend, may do
  better. That is a new idea, and it would have to be pre-registered and checked on the 2022 and 2023
  folds before it is used.
- This matters only if the 2026 round is scored by an error measure, as in 2022. The 2024 round used
  the within-environment Pearson r, which ignores the level entirely. The 2026 metric will be read
  when the training data are released (2026-11-16).

## Limits

- One season (2024) and one prediction column (M4). The spread factor 0.30 was chosen knowing M4's
  2024 score, as the pre-registration says.
- No weather data enter the level. No person has checked these numbers. Nothing here is agronomic
  advice.

MV2, Munim, Inc., mv2@munimtech.com
