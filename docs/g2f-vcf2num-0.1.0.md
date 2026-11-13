# g2f-vcf2num 0.1.0: a fallback for a VCF-only genotype release, and a year audit of the 2026 chain

Apache-2.0 code; this text CC BY 4.0. Made by AI agents working in the name of MV2 of Munim, Inc.
(mv2@munimtech.com). Written 2026-11-13, three days before the G2F 2026 data release (2026-11-16) and before
any 2026 file exists. No person has checked it.

## Why

The G2F 2026 release adds a season: training data now cover 2014-2025 (the dry runs used the 2024 release,
2014-2023). Before release day we read the code of every step in the release-day chain to look for two things:
a year written into the code, and an input the chain cannot do without.

## Year audit (read from the code at v0.11.9)

| Step | How it finds years | Hard-coded year in the logic? |
|---|---|---|
| g2f_entry.py (find_release, seen_share, decide) | files by role from their lower-case names; last training year = max year in the trait file | No. Only the wording of `decide`'s `choose_on` text mentions "2023-like"/"2024-like" |
| g2f_predict.py (plan, predict) | test season = last 20xx in the template's file name, else the most common Env year | No |
| g2f_refold.py (choose) | hold-out folds = the newest `--folds` training seasons, never the earliest | No |
| g2f_refmodel.R (plan, all) | test fold = first 20xx in the template's file name; hold-outs = the newest n training seasons | No; the 2024 file names are only defaults (see check 2 below) |
| g2f_switch.py, g2f_parentgca.py (helpers used by the chain: `GRID`, `apply_mix`, `fit_predict`) | given train/test frames | No. Their own study commands (`grade`, `main`) are fixed to the 2022/2024 folds, but the chain does not call them |
| g2f_baseline.py (`holdout`, `load_trait`) | `holdout(trait, year)` uses the year it is given | No. Its own `main` is the 2024 study and is not part of the chain |

So on the 2026 release, with the planned `--folds 4` / `all 4`, the hold-out folds become 2025, 2024, 2023 and
2022, each trained only on earlier seasons, and the test fold is trained on 2014-2025. Nothing needs changing
for the new year.

Two release-day consistency checks follow from the reading (both cheap, both on the `plan` outputs):

1. **Same test season in both legs.** Python takes the *last* 20xx in the template's file name, R the *first*.
   They agree for a name like `1_Submission_Template_2026.csv`. If the 2026 template name holds two years,
   `g2f_predict.py plan` and `refmodel_plan.txt` must show the same test season before anything is fitted.
2. **Same files in both legs.** R uses a 2024 default file name when that exact file sits at the top of the data
   folder, and otherwise the largest file matching the pattern; Python always takes the largest file per role.
   If a 2024 file is ever placed in the 2026 data folder, R would read it. `refmodel_plan.txt`'s
   `trait_file`, `template_file` and `geno_file` must match the census / `g2f_predict.py plan` roles.

## The one hard dependency: the numerical genotype file

Both legs need the organisers' TASSEL-style numerical genotype file:

- `g2f_predict.py` lists `geno_numeric` as a needed role and stops in `plan` and `predict` without it; it has
  no VCF reader.
- `g2f_refmodel.R` stops when no file matches `_numerical.txt`.

The 2024 release shipped one (`5_Genotype_Data_All_2014_2025_Hybrids_numerical.txt`: a `<Numeric>` line, a
`<Marker>` header, 5,899 taxa in rows, 2,425 markers). If the 2026 release ships only a VCF, the whole chain
stops on release day. `g2f_vcf2num.py` removes that risk.

## What g2f_vcf2num.py does

- Streams the VCF (plain or .gz) twice, using only the Python standard library, so a 1 GB job is enough.
- Codes each call as the share of non-reference alleles, rounded to the nearest half (0, 0.5, 1; missing = NA).
  TASSEL scores the major allele instead; per marker that is the same value or 1 - value, so marker variances
  (R's `var > 0.01` marker filter) and between-taxon distances (R's Gaussian kernel; Python z-scores each
  marker) are unchanged.
- Drops markers with more than 50% missing calls among the kept taxa or a minor allele frequency below 0.01,
  then keeps 2,425 of the rest evenly spaced in file order (the 2024 file's marker count). With `--keep` it
  keeps only taxa named in the trait and template files (the 2024 file had none outside them).
- Writes the 2024 layout to a name ending in `_numerical.txt` (it refuses any other name), so
  `g2f_entry.find_release` and R's `find_file` both pick it up with no other change.

12 unit tests: layout and codes, both filters, taxa filter, even thinning, repeated sample and marker names,
haploid/tetraploid/missing calls, .gz input, the name guard, a VCF without a header, the CLI, and (where the
rest of the repo imports) that `g2f_entry` gives the output the `geno_numeric` role and `g2f_baseline.read_numeric`
reads it back.

## Release-day rule (fixed now, before the data)

- If the 2026 release contains a `_numerical.txt` genotype file: use it; this tool is not used.
- If it contains only a VCF: run, once, with the defaults:
  `python g2f_vcf2num.py <vcf> <data_dir>/derived/<vcf name without .vcf>_numerical.txt --keep <trait csv>
  --keep <template csv> --summary /out/vcf2num.json`, then run the chain unchanged. The summary (taxa, markers
  read, passing and written, missing share) is published with the release-day results.
- No other marker settings are tried on the 2026 data.

## Limits

- The 2024 organisers' marker set (2,425 SNPs) came from their own filtering, which we do not know; evenly
  spaced markers after our filters are a stand-in, not a copy. Scores from a converted VCF may differ from scores
  the same models would get from an organisers' numerical file.
- Rounding to the nearest half only matters for non-diploid calls; maize hybrids are diploid.
- This has been tested on small made-up files only; it has never seen a G2F VCF.
