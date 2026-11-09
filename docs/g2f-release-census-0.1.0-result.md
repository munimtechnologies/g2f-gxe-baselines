# g2f-release-census 0.1.0: result of the dry run on the 2024 release

RESULT-MARKER: g2f-release-census-0.1.0-result

Made with AI agents working in MV2's (Munim, Inc.) name. Code: Apache-2.0. Text: CC BY 4.0.
Graded 2026-11-09 from the sealed job `g2f-release-census-v1` (python:3.12, standard library only; ran
2026-11-09 10:19-10:23 UTC after the pre-registration `docs/g2f-release-census-0.1.0.md` was public).
Output: [`results/g2f_release_census_2024.json`](../results/g2f_release_census_2024.json).
No person has checked these counts.

## Tool gate (C1-C10): 9 of 10 held; the one miss is a definition, not a bug

| id | check | expected | found | held |
|---|---|---|---|---|
| C1 | environments with a yield | 272 | 272 | yes |
| C2 | hybrids with a yield | 5,017-5,037 | 5,027 | yes |
| C3 | template pairs | 10,057 | 10,057 | yes |
| C4 | template pairs whose hybrid is seen | 1,218-1,228 | 1,223 | yes |
| C5 | ... seen at the same location | 969-979 | 974 | yes |
| C6 | template pairs genotyped | 10,057 | 10,057 | yes |
| C7 | template pairs with an observed value | 9,486 | 9,486 | yes |
| C8 | genotyped taxa | 5,897 | **5,899** | **no** |
| C9 | environments with >= 3 observed pairs | 22 | 22 | yes |
| C10 | trait rows with a yield | 164,921 | 164,921 | yes |

C8 failed as written. The cause is a definitional difference, not a bug in the census. The 5,897 in
g2f-baseline-v1 was the number of genotype rows left *after* keeping only hybrids that have a yield in
training or appear in the template (`g2f_baseline.py` drops trait rows without a yield before it
intersects). The census counts every row of the genotype file: 5,899 rows, 5,899 distinct names, all
of them (0 outside) named somewhere in the trait file or the template. The two extra taxa must
therefore be hybrids that appear in the trait file only on rows without a numeric yield. That follows
from the counts, but no job has listed the two names. The census reads the files the same way pandas
does on every other count. **The tool is cleared for the 2026 release.** To keep the result honest, C8
stays marked as failed.

## The data note against the files (N1-N6): all six match

| id | stated in the 2024 data note | found |
|---|---|---|
| N1 | 5,205 hybrids | 5,205 distinct hybrid names in the trait file (5,027 with a yield) |
| N2 | 272 environments | 272 |
| N3 | approximately 180,000 plots | 173,960 rows (164,921 with a yield) |
| N4 | 2,425 markers | 2,425 |
| N5 | 1,063 test hybrids | 1,063 |
| N6 | 23 test locations | 23 environments, 23 locations (one, SCH1_2024, has no observed values) |

## Predictions Y1 and Y2: both held

Hybrids with a yield in each training season, and how many were grown the season before:

| season | hybrids | grown the year before | share | grown in any earlier year |
|---|---|---|---|---|
| 2014 | 854 | - | - | - |
| 2015 | 1,155 | 324 | 28% | 324 |
| 2016 | 579 | 91 | 16% | 94 |
| 2017 | 503 | 470 | 93% | 477 |
| 2018 | 1,054 | 112 | 11% | 130 |
| 2019 | 1,201 | 946 | 79% | 947 |
| 2020 | 1,176 | 25 | 2% | 44 |
| 2021 | 1,181 | 1,174 | 99% | 1,174 |
| 2022 | 553 | 45 | 8% | 45 |
| 2023 | 556 | 550 | 99% | 550 |
| 2024 (test) | 1,063 | 53 | 5% | 104 |

- **Y1 held:** 550 of 556 hybrids in 2023 (98.9%) were also grown in 2022 (bar: at least 80%).
- **Y2 held:** 45 of 553 hybrids in 2022 (8.1%) were grown in 2021 (bar: under 30%).

G2F evaluates a set of hybrids for two seasons, so a new set starts every even year. G2F's own project
page says so for each pair of seasons since 2018 ("2021 is the second year of evaluation of the genetic
material present in 2020"; "in 2025 the evaluation continued with the same group of hybrids as in
2024"). The census adds the size of the effect: in odd seasons since 2017, 79-99% of hybrids repeat;
in even seasons since 2016, 2-16% do. 2015 (28%) is the exception.

## What this changes: the 2026 test season is an even year

Prediction R3 in the pre-registration assumed that the 2026 competition would test the **2025**
season, the second year of the 2024 hybrid set. That assumption was wrong. The competition site
(maizegxeprediction.org, read 2026-11-09) says the task is to "predict corn yield in the **2026** G2F
trials". The 2024 competition likewise trained on 2014-2023 and tested on 2024. 2026 starts a new
cycle. G2F's project page describes the 2026-2027 experiments as about 300 new paired-cross hybrids
(50 Stiff Stalk x 100 Non-Stiff Stalk lines) plus topcrosses of the same lines to LH287 and LH244, and
25 core checks.

R1-R4 stay as written and will be graded on the first census of the 2026 release. We expect **R1**
(training ends in 2024) and **R3** (at least 70% of test pairs have a hybrid with a 2024 yield) to
fail, because the test season was misread. Corrected predictions for the 2026 release, and a study of
which kinds of new hybrid each past season tested, are pre-registered in
[`g2f-cathistory-0.1.0-prereg.md`](g2f-cathistory-0.1.0-prereg.md). Both were written before the 2026
data exist.

Other numbers from the dry run that the 2026 entry will use:

- 2024 test pairs: hybrid seen before 1,223 (12.2%); both parents seen 1,911 (19.0%, including the seen
  hybrids); exactly one parent seen 8,146 (81.0%); **neither parent seen 0**; location seen 9,635 (95.8%).
- Genotype file: 5,899 taxa x 2,425 markers, taxa in rows. 4,940 of the trait file's 5,205 hybrid names
  are genotyped. All 1,063 test hybrids are genotyped.

## Limits

- Hybrid names are compared exactly after trimming spaces. G2F renames some hybrids between seasons,
  so these shares are lower bounds on true repetition.
- One release (2024) and its file layout. The 2026 release may differ.
- Names and counts only; this says nothing about how well any model will do.

MV2, Munim, Inc., mv2@munimtech.com
