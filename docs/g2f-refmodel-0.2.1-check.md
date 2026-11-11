# g2f-refmodel 0.2.1: plan regression (4 of 4 held)

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed it yet. Text CC BY 4.0; code
Apache-2.0. Not agronomic advice.

RESULT-MARKER: g2f-refmodel-0.2.1-check

## What 0.2.1 changes

`g2f_refmodel.R` is MV2's own re-implementation of the organisers' public Gaussian-kernel reference
model (the "full" model of g2f-switch). Version 0.2.0 learned to find a release's files by role
(docs/g2f-refmodel-0.2.0-check.md). Its `plan` mode, which lists the files and folds and fits nothing,
printed hold-outs "none" because the hold-out seasons were worked out only in `all` mode. That was check
K1's only failure. Version 0.2.1:

- makes `plan` list exactly the hold-out folds that `all` would fit;
- adds an optional fourth argument, the number of hold-out seasons (default 2, as in 0.1.0 and 0.2.0);
- changes no fitting line. The 0.4416 reproduction of the 2024 test fold (check K3) was graded on 0.2.0.

Usage: `Rscript g2f_refmodel.R <data_dir> <out_dir> [all|test|plan] [n_holdouts]`.

## The check

This is a regression of a small change, not a pre-registered study: the checks were written into
`regress_plan.py` before the run but were not committed to GitHub first.

Job `g2f-refmodel3-plan-v1` (r-base image with python3; 2026-11-10 21:20-21:23 UTC, 168 s; 1 CPU,
2 GB; data volume = the public G2F 2024 release). It ran `plan` four times and graded the plan files:

| Check | Run | Expected | Got | Held |
|---|---|---|---|---|
| K1 | 2024 release, default | version 0.2.1, test fold 2024, hold-outs "2023 2022" | same | yes |
| K2 | simulated 2026 layout (the 2024 files linked under 2026-style names in `Training_data/` and `Testing_data/`) | test fold 2026; the renamed trait, template and genotype files found; hold-outs "2023 2022" | same | yes |
| K4 | 2024 release, `plan 4` | hold-outs "2023 2022 2021 2020" | same | yes |
| K5 | 2024 release, `plan 0` | hold-outs "none" | same | yes |

Every run found the same 164,921 trait rows (2014-2023) and the same template (10,057 pairs in 23
environments). In the simulated layout the trait file keeps its real content, so its years still read
2014-2023; only the names changed. Output: results/g2f_refmodel_plan_regress.json.

## What it means for the 2026 entry

On release day (training data are due 2026-11-16) the kernel model's predictions for the 2026 test
season and for its hold-out seasons come from one command, with no edit for the new file names:

```
Rscript g2f_refmodel.R <release folder> <out> plan 4   # list files and folds first (no fitting)
Rscript g2f_refmodel.R <release folder> <out> all 4    # then fit; about 6 minutes per fold here
python g2f_refold.py choose --data-dir <release folder> --out-dir results --full-dir <out>/preds --folds 4
```

With four hold-outs on a 2026 release (training up to 2025), the folds are 2025, 2024, 2023 and 2022;
g2f-refold then chooses the mix weights on the folds of the test season's type.

Limits: K2 links the 2024 files under 2026-style names; the real 2026 release may differ in ways a
rename cannot show (new columns, other folders). The `plan` run on the real release is the first thing
to look at on release day.
