# g2f-entry 0.1.0: dry run on the 2024 release, graded

RESULT-MARKER: g2f-entry-0.1.0-result

Made with AI agents working in MV2's (Munim, Inc.) name. Code: Apache-2.0. Text and data: CC BY 4.0.
Graded 2026-11-09 from the sealed job `g2f-entry-dryrun-v1` (2026-11-09 12:16-12:20 UTC, python:3.12,
standard library only, 222 s). It ran only after the pre-registration
[g2f-entry-0.1.0.md](g2f-entry-0.1.0.md) was public, then ran the 14 unit tests (all passed) and the
dry run. Full output: [results/g2f_entry_dryrun_2024.json](../results/g2f_entry_dryrun_2024.json).

## Checks: all six held

| id | check | holds if | found | grade |
|---|---|---|---|---|
| D1 | `locate` finds trait, template, observed, numeric genotype files | all four | all four (`1_Training_Trait_Data_2014_2023.csv`, `1_Submission_Template_2024.csv`, `7_Testing_Observed_Values.csv`, `5_Genotype_Data_All_2014_2025_Hybrids_numerical.txt`) | **held** |
| D2 | every 2024 template row has an M4 prediction | 0 missing | 0 of 10,057 | **held** |
| D3 | the written submission validates | 0 errors | 0 errors, 10,057 rows, 23 environments | **held** |
| D4 | scoring the written file reproduces M4's published score | 0.3018 +- 0.0001 over 22 envs | 0.3018 over 22 environments (9,486 scored pairs) | **held** |
| D5 | five broken copies are rejected | 5 of 5 | 5 of 5 (swapped rows, blank yield, dropped last row, renamed yield column, "nan") | **held** |
| D6 | seen share matches 0.1216; rule R3 says new-hybrid year | 0.1211-0.1221 and `new_hybrids` | 0.1216 (1,223 of 10,057 pairs); `new_hybrids` | **held** |

D4 is the important one: a file built by `write` keeps every prediction on its own template row all the
way to the score. The 23rd template environment has no observed values in the released answers, so it
is not scored (22 environments), as in every earlier 2024 score in this repository.

## Figures not stated in advance

- **The R3 quantity on a year whose answer is known:** 688 of the 10,057 template pairs (6.84%) have a
  hybrid with a 2023 yield row, far below the 70% threshold, so R3 calls 2024 a new-hybrid year. That
  matches the census of earlier seasons (even seasons repeat 2-16% of hybrids).
- **Per-environment r of M4 on 2024** ranges from 0.153 (NYH3_2024) and 0.164 (IAH2_2024) to 0.451
  (OHH1_2024) and 0.461 (MNH1_2024); the full table is in the results file.

## One finding that changes the entry: the upload must be in Mg/ha

`validate` warned that M4's predictions run from -2.008 to 0.832, which are not plausible yields. M4
works on a standardised scale. The score cannot see this, because the within-environment Pearson r
ignores each environment's mean and scale. But the 2024 challenge page (EvalAI challenge 2376,
evaluation details, read 2026-11-09) asks for "absolute grain yield for each hybrid in each test
environment in Mg/ha adjusted to 15.5% moisture". It also says "other ways of evaluating the models will
also be employed for publication purposes". An entry on a standardised scale would score the same but
break the stated format and look poor on any error-based measure in the paper.

So the 2026 upload must be turned into Mg/ha first, without changing the within-environment ranking.
[g2f-entry 0.2.0](g2f-entry-0.2.0.md) adds that step (`mgha`) and pre-registers its own dry run.

## Limits

- The dry run checks the file against the 2024 template only. The 2026 rules may differ (file name,
  extra columns); they are re-read on the release day.
- No person has checked these results. Nothing here is agronomic advice.

MV2, Munim, Inc., mv2@munimtech.com
