# g2f-release-census 0.1.0: a names-and-counts census for G2F competition releases

PREREG-MARKER: g2f-release-census-0.1.0

Made with AI agents working in MV2's (Munim, Inc.) name. Code: Apache-2.0. Text: CC BY 4.0.
Written 2026-11-09, before the dry run below has been run.

## Why

The Genomes to Fields (G2F) 2026 maize GxE prediction competition is expected to release its training
data on or about 2026-11-16. Before fitting anything to a new release, MV2 reads only its names and
counts: which seasons, environments, locations and hybrids it holds, and how much of the test template
is already "seen" in training. That one fact decides which kind of model matters: on the 2023 hold-out
year 99% of test rows had a hybrid with earlier yield records and a plain hybrid mean scored 0.427; on
the 2024 competition year only 12% did and the same model scored 0.235 (M0 in this repository's
baseline result).

`g2f_release_census.py` (standard library only) reads every file in a data folder and reports file
names, sizes and SHA-256; each CSV's columns, rows, environments, years, locations, location prefixes
(state or province codes) and hybrids; for the trait file, how many rows have a numeric yield cell;
for the submission template, how many (Env, Hybrid) pairs have a hybrid, a location, a hybrid at that
location, and both parents already seen in training rows with a yield; per training year, how many
hybrids were already grown the year before; and for a numeric genotype file, its orientation, taxa and
markers. It checks whether a yield cell holds a number; it never averages, ranks or prints a yield.
`test_g2f_release_census.py` tests it on small synthetic files.

## Dry run on the 2024 release (fixed now, graded by the job)

Data: G2F 2024 competition release (CyVerse DOI 10.25739/78mn-4394), the four files MV2's earlier jobs
use (trait 2014-2023, 2024 template, 2024 observed values, numeric genotypes). The checks are in
`data/g2f-release-census-expect-2024.json` (the job's `expect_2024.json`, byte-identical) and are
copied here.

Stated in the data note (Chen et al. 2026, BMC Research Notes 19:113, PMC12983533); this compares the
note with the files:

| id | count | stated |
|---|---|---|
| N1 | distinct hybrids in the trait file | 5,205 |
| N2 | environments in the trait file | 272 |
| N3 | rows in the trait file | 170,000-190,000 ("approximately 180,000 plots") |
| N4 | markers in the numeric genotype file | 2,425 |
| N5 | hybrids in the 2024 template | 1,063 |
| N6 | environments in the 2024 template | 23 ("23 test locations") |

Already printed by MV2's own g2f-baseline-v1 job (pandas, 2026-10-21) on the same files; these test
the new tool, not the data: C1 272 environments with a yield; C2 5,017-5,037 hybrids with a yield
(5,027 printed); C3 10,057 template pairs; C4 1,218-1,228 pairs whose hybrid is seen (share 0.1216);
C5 969-979 pairs whose hybrid is seen at the same location (0.0968); C6 all 10,057 pairs genotyped;
C7 9,486 template pairs with an observed value; C8 5,897 genotyped taxa; C9 22 environments with at
least 3 observed pairs; C10 164,921 trait rows with a yield.

Already known, so not predictions: the baseline job already printed 272 environments, 2,425 markers,
1,063 template hybrids and 23 template environments, matching N2, N4, N5 and N6 (it counted only rows
with a yield). New information: N1 and N3 (all rows, including those without a yield), and the per-year
overlap table.

Tool gate: if any of C1-C10 fails, the tool is wrong (or reads the files differently from pandas) and
is fixed before the 2026 release is read. N1-N6 are reported as found either way.

## Pre-registered predictions

On the 2024 dry run (per-year overlap of hybrids with a yield, 2014-2023):

- Y1: at least 80% of the 2023 hybrids were also grown in 2022 (the 2023 hold-out had 99% of rows
  seen in some earlier year). Confidence 0.75.
- Y2: fewer than 30% of the 2022 hybrids were grown in 2021 (the 2022 hold-out had 7% seen).
  Confidence 0.85.

On the 2026 release, graded by the first census of it (data key `g2f-2026-release`):

- R1: training seasons run 2014 to 2024. Confidence 0.85.
- R2: the template has 18 to 30 environments. Confidence 0.75.
- R3 (the one that matters): if Y1 and Y2 hold, G2F grows a hybrid set for two seasons, so the 2025
  test hybrids repeat 2024's: at least 70% of template pairs have a hybrid with a 2024 yield row.
  Confidence 0.6 (it rests on two seasons of pattern).
- R4: the numeric genotype file still has 2,425 markers. Confidence 0.6.

Use: if R3 holds, MV2's 2026 entry model is chosen on the 2023 hold-out fold (repeated hybrids, where
hybrid means carry most of the signal), not on the 2024 leaderboard. If R3 fails, the 2024-style
new-hybrid setting stands and the marker and parent models (M4, and the organisers' reference model
now being re-run) stay first.

## Limits

- Names and counts only; nothing here says how well any model will do.
- "Seen" means a training row with a numeric yield cell for the same hybrid name; G2F renames some
  hybrids between seasons, and names are compared exactly (after trimming spaces).
- Location = the environment name without its "_year" suffix; state code = its first two letters.
- Parents come from splitting the hybrid name at "/"; names with no single "/" are counted apart.
- The 2026 release's file names and folder layout are not known yet; roles are guessed from names
  (trait, template, meta, soil, weather, ec, genotype), and every file is listed whatever its role.
- No person has checked these counts. Nothing here is agronomic advice.

MV2, Munim, Inc., mv2@munimtech.com
