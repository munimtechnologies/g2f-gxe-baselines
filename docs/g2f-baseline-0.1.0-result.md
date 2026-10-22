# g2f-baseline 0.1.0: result

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed these numbers yet.
Text CC BY 4.0; code Apache-2.0.

This grades [`g2f-baseline-0.1.0-prereg.md`](g2f-baseline-0.1.0-prereg.md), written before the job ran.
`g2f_baseline.py` ran once, unchanged, in a sealed compute job (g2f-baseline-v1, 2026-10-21,
23:15-23:20 UTC, python:3.12, numpy 2.1.3, pandas 2.2.3, 2 CPU, peak memory 0.74 GB). Its 12 offline
tests passed first. The job's outputs are committed in `results/`: `g2f_baseline.json` (every fold),
`g2f_2024_env_r.csv` (r per 2024 environment) and `g2f_2024_predictions.csv` (every 2024 template row).

## Summary

- **4 of 5 predictions held. P4 did not.** Only 12% of the 2024 test rows are hybrids with any
  training plots, well under the predicted range of 20-90%.
- On the organisers' released 2024 answers, the best simple model (M2: marker ridge shrunk toward the
  hybrid's own mean) scores a mean within-environment r of **0.280** over 22 environments.
- Shrinking toward the hybrid's own mean helps every time: M2 beats M1 in all 3 folds and in all 22
  of the 2024 environments.
- A location-specific adjustment (M3) adds nothing on 2024 (-0.0003) and a little on 2022 and 2023
  (+0.010, +0.007).
- For rough context, M3's 0.335 on 2022 would have placed about 4th by within-environment r on the
  2022 competition leaderboard (winner 0.357), with the caveats below.

## Scores (mean within-environment Pearson r)

| Fold | Train years | Test envs scored | Test hybrids | Rows with seen hybrid | M0 | M1 | M2 | M3 |
|---|---|---|---|---|---|---|---|---|
| 2022 | 2014-2021 | 28 | 553 | 6.9% | 0.164 | 0.324 | 0.326 | **0.335** |
| 2023 | 2014-2022 | 27 | 556 | 99.4% | 0.427 | 0.411 | 0.437 | **0.444** |
| 2024 | 2014-2023 | 22 of 23 | 1,063 | 12.2% | 0.235 | 0.239 | **0.280** | 0.280 |

M0 = hybrid's training mean (0 if never tested); M1 = ridge regression on 2,425 markers (lambda 1,000,
chosen by 5-fold CV over training hybrids in every fold); M2 = M1 shrunk toward the hybrid mean with
k = 5; M3 = M2 plus the hybrid's shrunk residual at the same location (k = 10). Yield was z-scored
within each training environment. The 2024 fold scores the 9,486 of 10,057 template rows that have a
released observed value; one of the 23 environments had too few to score.

## Predictions

| Item | Pre-registered | Result | Grade |
|---|---|---|---|
| P1 M1 on 2024 | 0.28 [0.10, 0.45] | 0.239 | held |
| P2 M2 >= M1 on 2024, and on >= 2 of 3 folds | yes | 2024: 0.280 vs 0.239; 3 of 3 folds | held |
| P3 M3 - M2 on 2024 | [-0.02, +0.05] | -0.0003 | held |
| P4 share of 2024 test rows whose hybrid has training plots | 0.50 [0.20, 0.90] | 0.122 | **not held** |
| P5 best model's spread across folds | >= 0.05 | 0.444 - 0.280 = 0.164 | held |

**P4, read plainly.** The guess assumed the 2024 trials would repeat many earlier hybrids. They did
not: 88% of the 2024 rows are hybrids never tested before, close to the 2022 trials (93% new; the
competition paper reports that only 8% of 2022 hybrids had been tested before). 2023 is the
exception: 99% of its rows are hybrids already tested in earlier years. That is why every model
scores much higher on 2023, and why 2023 says little about predicting new hybrids.

## What the numbers say

1. **For new hybrids, marker effects are most of the signal, and they are weak.** On 2024, M1 alone
   scores 0.239. The ridge's own cross-validation over training hybrid means scores r = 0.55, so a
   good share of what predicts a hybrid's average does not carry over to its rank inside a single
   2024 field.
2. **The few repeated hybrids matter more than their share suggests.** M0 gives every new hybrid the
   same value (0) and still scores 0.235 on 2024, beating M1 in 10 of the 22 environments. The
   likeliest reason is that the 12% of repeated rows are check hybrids grown across years, whose
   long-run means separate them from the rest of each field. This was not tested here.
3. **Location-specific memory does not help new hybrids.** M3 only adjusts hybrids already grown at
   that location, which is under 10% of rows in 2022 and 2024.
4. **Next step:** the remaining gains, if any, must come from genotype-by-environment effects, the
   part these models leave out. That is the pre-registered follow-up `g2f-envkernel 0.1.0`.

## Context: the 2022 competition (rough comparison only)

The 2022 competition's paper (Genetics 2024, doi 10.1093/genetics/iyae195; bioRxiv
10.1101/2024.09.13.612969), Table 2, reports average within-environment Pearson r for the top teams:
CLAC (winner) 0.357, CGM 0.353, UCD_MegaLMM 0.338, then 0.272; the best ensemble of the top five
teams reached 0.369. M3's 0.335 on our 2022 fold would sit just below third. This comparison is
rough, for four reasons:
- 2022 was ranked by RMSE, so teams were not optimising r.
- Our fold scores all reported 2022 plots (28 environments, 553 hybrids), not the 2022 template
  (26 environments, 548 hybrids).
- We used the later 2024 release's cleaned traits and genotypes, not the files 2022 teams had.
- Our models are chosen and run after the fact, with no deadline.

The 2024 competition note (BMC Research Notes, doi 10.1186/s13104-026-07629-5) says 2024 was ranked
by mean within-environment r, but it gives no scores, so the 2024 fold here has no leaderboard to
compare with.

## Limits

- Additive marker effects only: no weather, soil or environmental covariates.
- One fixed lambda grid and fixed shrinkage constants (k = 5, 10), set before the run and never tuned.
- The "seen hybrid" share counts hybrids with any training plot, including check hybrids.
- The 2022 and 2023 folds score all reported plots of that year, not each competition's test set.
- No human has checked these numbers or the published scores quoted above.

## Reproduce

```
pip install numpy==2.1.3 pandas==2.2.3
python -m unittest -v test_g2f_baseline
python g2f_baseline.py --data-dir data --out-dir results
```

Data: Genomes to Fields 2024 competition release, CyVerse DOI 10.25739/78mn-4394 (PDDL).
