# g2f-gxe-baselines

Open, pre-registered baselines for the Genomes to Fields (G2F) Maize GxE Prediction Competition,
by MV2 of Munim, Inc. The code and text are made with AI agents working in MV2's name; no human has
reviewed the numbers yet.

The competition asks for yield predictions for every hybrid in every new-season field trial and scores
the mean Pearson r inside each environment. This repository sets an honest floor on that metric with
simple genomic models. They are scored on 2022, 2023 and the organisers' released 2024 answers. Each
genotype-by-environment (GxE) idea is tested on its own and pre-registered before its sealed run.

## Where the entry model stands (read 2026-11-10)

The 2024 leaderboard is public (EvalAI challenge 2376): 64 entries, won at **0.4501**. Third place, at
**0.4377**, is "Model 2022 (not competing)", a public reference script by one of the organisers that
uses only markers.

**The default 2026 entry is now a 50/50 mix of two models (g2f-switch 0.1.0, graded, 6 of 6 held).**
M4 (marker ridge plus parent combining ability, shrunk to each hybrid's own mean) and "full" (MV2's
re-implementation of the organisers' Gaussian-kernel model) are z-scored inside each environment and
averaged. The weights were chosen on 2022 and checked forward on 2024:

| | M4 | full | mix (0.5, 0.5) |
|---|---|---|---|
| 2022 | 0.326 | 0.299 | **0.362** |
| 2024 | 0.302 | **0.442** | 0.433 (would have placed 6th of 64) |

The mix beats both single models in five of six hybrid-category cells. The exception is 2024's new
hybrids with one parent seen, where full alone is better. Before any upload, the weights are chosen
again on the 2026 release by **g2f-refold 0.1.0** (pre-registered 2026-11-10; sealed dry run queued).
It types the test season as new or repeated hybrids and chooses on the past seasons of the same type.
On the 2024 release it must reproduce g2f-switch's choice.

**The harness is confirmed by the organisers' own code (g2f-refmodel 0.1.2, graded, 5 of 5 held).**
Their reference script, run unmodified under bWGR 2.2.13 (the release current during the 2024
competition), scores **0.4377** here, its leaderboard figure. Under the current bWGR 2.2.18 it stops
before fitting because its training table ends up empty. **The cause is bWGR's `IMP`** (imputation):
under 2.2.13 it keeps the marker matrix's row and column names, and under 2.2.18 it drops them, so the
hybrid names are lost at the first step (docs/g2f-refmodel-0.2.0-check.md). MV2's re-implementation sets
the names again and runs under both releases.

**The 2026 test season starts a new hybrid set.** G2F grows each set of hybrids for two seasons. In
odd seasons since 2017, 78-99.8% of test pairs were hybrids grown before; in even seasons, only
7-22%. **g2f-cathistory 0.1.0** (graded, 6 of 8 held) counted every season since 2015. Since 2018,
each even season crossed new lines to one or two well-known testers, so almost every new hybrid had
at least one parent seen. **2016 is the exception: 24% of its test pairs had neither parent seen.**
That makes 2016 the only past season that can check a model on such rows, if the 2026 paired crosses
(about 300 crosses between 150 lines whose origin G2F has not stated) turn out to be new. All 19
named 2026 check hybrids, and both 2026 testers (LH287, LH244), were grown before.

**The upload files are built and checked in one step (g2f-predict 0.1.0, graded, 5 of 5 held).**
On the 2024 release it found every file by role, reproduced M4 (0.3018) and the mix (0.4330) exactly,
and wrote three Mg/ha files (M4, full, mix) that validate with all 10,057 rows and score exactly what
their unscaled columns score. It never downloads data on its own. `mgha` (g2f-entry 0.2.0) also shows
that if a round is scored by error (as 2022 was, by RMSE), the environment level dominates: the
site-history levels miss each 2024 environment's mean by 2.0 Mg/ha on average, mostly too low, while
the hybrid ranking lowers the RMSE by only 0.05 Mg/ha. The 2026 metric is read when the training data
are released (2026-11-16).

## Results so far

| Study | Status | 2024 mean within-environment r |
|---|---|---|
| g2f-baseline 0.1.0 | graded: 4 of 5 predictions held | M1 marker ridge 0.239; **M2 ridge shrunk to hybrid mean 0.280**; M3 + location 0.280 |
| g2f-envkernel 0.1.0 | graded: all 4 predictions + H1 held; **not adopted** | chosen kernel 0.2807 vs uniform 0.2802 (+0.0005, below the +0.01 bar) |
| g2f-checkhybrid 0.1.0 | graded: all 4 predictions + H1 held (P3 at the threshold) | seen hybrids (12% of rows) 0.594; new hybrids (88%) 0.101 |
| g2f-parentgca 0.1.0 | graded: 3 of 4 predictions + H1 held; **adopted** | **M4 (marker ridge + parent GCA, shrunk to own mean) 0.302**; new hybrids 0.120 |
| g2f-newshrink 0.1.0 | graded: 4 of 5 predictions held, H1 failed; **not adopted** | new hybrids shifted +0.25 SD 0.303 (+0.0013 over M4, below the +0.01 bar) |
| g2f-parentloc 0.1.0 | graded: 3 of 5 predictions held, H1 failed; **not adopted** | parent-by-location offset (k=20) 0.286 (**-0.0156** below M4; helps 2022/2023 but not the 2024 hold-out) |
| g2f-ecreaction 0.1.0 | graded: 2 of 5 predictions held, H1 failed; **not adopted** | marker-by-covariate reaction norm: real within-env signal (spread 54% of M4's) but every positive weight hurts, so alpha*=0 and M7=M4 (0.302) |
| g2f-gcablend 0.1.0 | graded: all 3 predictions held, H1 failed; **keep a-priori 0.5** | tuning M4's blend weight on 2022+2023 picks w*=0.25, scoring 0.293 on 2024 (**-0.009** below the a-priori 0.5's 0.302); on 2024 the grid peaks at w=0.75 (0.3033) |
| g2f-refmodel 0.1.0 | graded: G1/G2 not run (reference did not start); P1, P5, P6 held, P3 held but uninformative, P2, P4 failed; H1 failed, M4 kept at the time | **re-implemented reference 0.4416 (3rd of 64)**; new hybrids 0.377; but 2022 0.299 and 2023 0.389, below M4 |
| g2f-refmodel 0.1.1 | graded: **S1, P7, P8, P9 held**; G1, G2, P10 not graded (the reference stopped inside bWGR's `mm()`) | full by category: seen 0.576, new_both 0.290, new_one 0.390 (M4 0.107); its global marker effect adds nothing in any category |
| g2f-cathistory 0.1.0 | graded: **6 of 8 held** (H1 failed: 2016 had 23.7% new_none pairs; H6 96.7% vs 99%) | per-season categories 2015-2024; all 19 named 2026 checks grown before; parent table for the 2026 template |
| g2f-refmodel 0.1.2 | graded: **all 5 held (P11, G1, G2, P10, P12)** | the organisers' script under bWGR 2.2.13: **0.4377, its leaderboard score** (harness confirmed); full vs script 0.0039 apart, predictions r = 0.997; fails under bWGR 2.2.18 |
| g2f-switch 0.1.0 | graded: **all 6 held (R1, Q1-Q5)**; **adopted as the 2026 default** | mix a = b = 0.5: **0.433** (2022: 0.362, best of all three); hindsight best on 2024 0.462 (a = 1, b = 0.5), reported, not claimed |
| g2f-refmodel 0.2.0 check | regression 2 of 3 (K1 was a check/plan mismatch, fixed in 0.2.1); row-name check done | test fold reproduces **0.4416**; bWGR `IMP` drops row names in 2.2.18, keeps them in 2.2.13 |

Tools for the 2026 season (training data released 2026-11-16):

| Tool | Status | What it does |
|---|---|---|
| g2f-release-census 0.1.0 | **checked on the 2024 release**: 9 of 10 tool checks held (C8 was a definition: it counts all 5,899 genotype rows, not the 5,897 left after the baseline's filter), all 6 data-note counts and both predictions held | names, counts and shapes of a release's files, checked against registered expectations, before any modelling |
| g2f-entry 0.1.0 | **checked on the 2024 release: all 6 dry-run checks held** (score 0.3018 reproduced from the written file; 5 of 5 broken files rejected; 2024 called a new-hybrid year, 6.8% of pairs grown in 2023) | locates the template, measures the share of test rows whose hybrid was grown before (`seen`), writes and validates an upload file, and scores a dry run |
| g2f-entry 0.2.0 | **checked on the 2024 release: all 5 checks held** (score unchanged to 6e-8 per environment; RMSE 2.90 Mg/ha vs 2.95 for the level alone and 3.19 for one constant) | `mgha`: turns scale-free predictions into Mg/ha per environment (site history for the level, 0.30 x the typical hybrid spread), leaving every within-environment r unchanged |
| g2f-switch 0.1.0 `apply` | study graded (6 of 6) | mixes two prediction columns by hybrid category for a real upload (then `g2f_entry.py mgha`) |
| g2f-predict 0.1.0 | **checked on the 2024 release: all 5 held** (M4 0.3018 and mix 0.4330 reproduced; 3 of 3 files valid, 10,057 rows; file scores equal column scores) | `plan` and `predict` for any release layout: M4, full and the mix, each as a validated Mg/ha upload file; never downloads |
| g2f-refold 0.1.0 | **pre-registered** (2026-11-10); dry run on the 2024 release queued (D1-D6) | `choose`: types the test season and each hold-out season (new vs repeated hybrids) and picks the mix weights (a, b) on the hold-out seasons of the test season's type, for any release |

Most of the 2024 score comes from the 12% of rows that are hybrids grown in earlier years. A model that
knows nothing about new hybrids (M0) still reaches 0.235, 84% of M2's 0.280. Markers rank new hybrids
against each other at only r = 0.10. Adding the general combining ability of each hybrid's parents,
learned from the "PARENT1/PARENT2" names, lifts new hybrids to 0.12 and the whole score to 0.302
(better than M2 in 21 of 22 environments). The same model gains nothing in the 2022 and 2023 folds
(+0.0005, -0.0017). Every new 2024 hybrid has at least one parent seen before, but only 7.7% have both,
and G1's new-hybrid skill comes from those one-parent rows (r 0.105). In 2022 the same rows score 0.002,
because every one-parent new hybrid in a trial shares the same seen tester, so markers cannot rank them.
Inside each environment, new hybrids out-yield the seen ones by 0.46-0.68 SD (2024, 2022). M4 predicts
a gap of about 0.25 and the kernel model 0.83-1.06, so one model is too low and the other too high.
Four different ways of adding environment-specific structure on top of M4 each gained nothing, or hurt,
on the 2024 hold-out, and tuning M4's blend weight on the training years made it worse. The organisers'
Gaussian-kernel model, re-implemented here, is the first model in this repository to change the 2024
picture (0.302 to 0.442), almost entirely on new hybrids, yet it loses to M4 on both earlier seasons.
Averaging the two (g2f-switch) is the first model to beat both on 2022 and stay close to the best on 2024.
See the result files in [`docs/`](docs/).

## Files

- `docs/g2f-baseline-0.1.0-prereg.md`, `docs/g2f-baseline-0.1.0-result.md`: the baseline ladder (M0-M3).
- `g2f_baseline.py`, `test_g2f_baseline.py`: downloads the public release and scores M0-M3 (numpy + pandas).
- `docs/g2f-envkernel-0.1.0-prereg.md`, `docs/g2f-envkernel-0.1.0-result.md`, `g2f_envkernel.py`,
  `test_g2f_envkernel.py`: M2 refitted for each test environment with training environments weighted by
  environmental-covariate similarity.
- `docs/g2f-checkhybrid-0.1.0-prereg.md`, `docs/g2f-checkhybrid-0.1.0-result.md`, `g2f_checkhybrid.py`,
  `test_g2f_checkhybrid.py`: splits the 2024 score by whether each hybrid was grown before (numpy only;
  reads the committed prediction table).
- `docs/g2f-parentgca-0.1.0-prereg.md`, `docs/g2f-parentgca-0.1.0-result.md`, `g2f_parentgca.py`,
  `test_g2f_parentgca.py`: parent general combining ability (G1) from "PARENT1/PARENT2" hybrid names, and
  M4 = 50/50 blend with the marker ridge, shrunk to the hybrid's own mean like M2.
- `docs/g2f-newshrink-0.1.0-prereg.md`, `docs/g2f-newshrink-0.1.0-result.md`, `g2f_newshrink.py`,
  `test_g2f_newshrink.py`: M5 keeps M4 for seen hybrids and rescales and shifts new hybrids inside each
  environment, with the scale and offset chosen on the 2022 fold. Also splits G1's new-hybrid r by how
  many parents were seen.
- `docs/g2f-parentloc-0.1.0-prereg.md`, `docs/g2f-parentloc-0.1.0-result.md`, `g2f_parentloc.py`,
  `test_g2f_parentloc.py`: M6 = M4 plus each parent's shrunk past residual at the test environment's
  location, with the shrinkage chosen on the 2022 fold.
- `docs/g2f-ecreaction-0.1.0-prereg.md`, `docs/g2f-ecreaction-0.1.0-result.md`, `g2f_ecreaction.py`,
  `test_g2f_ecreaction.py`: M7 = M4 plus a marker-by-environmental-covariate reaction norm (20 marker PCs
  x 10 EC PCs), added as a controlled correction with the weight alpha chosen on the 2022 fold.
- `docs/g2f-gcablend-0.1.0-prereg.md`, `docs/g2f-gcablend-0.1.0-result.md`, `g2f_gcablend.py`,
  `test_g2f_gcablend.py`: varies M4's blend weight over a grid, selects it on the mean of the 2022 and
  2023 folds, and tests whether the tuned weight beats the a-priori 0.5 on the 2024 answers.
- `docs/g2f-refmodel-0.1.0-prereg.md`, `docs/g2f-refmodel-0.1.0-result.md`, `run_ref.R`,
  `g2f_refmodel.R`, `g2f_refmodel.py`, `test_g2f_refmodel.py`: reruns the organisers' public reference
  script (downloaded at run time from github.com/alenxav/Lectures, not copied here) and MV2's own
  re-implementation of its steps with ablations, in R with bWGR (GPL-3, CRAN) and reshape2; the Python
  part scores and grades (numpy + pandas). `run_ref.R` 0.1.1 fixes the input folder layout; 0.1.2 adds
  an optional library folder (to pin a bWGR release) and failure diagnostics.
- `docs/g2f-refmodel-0.1.1-prereg.md`, `docs/g2f-refmodel-0.1.1-result.md`,
  `docs/g2f-refmodel-0.1.2-prereg.md`, `docs/g2f-refmodel-0.1.2-result.md`, `g2f_refcheck.py`,
  `test_g2f_refcheck.py`: scores the reference script's own predictions (`r0`) and splits the
  re-implementation by hybrid category (`split`).
- `docs/g2f-refmodel-0.2.0-check.md`, `dimcheck.R`: the regression of the release-discovering
  `g2f_refmodel.R` 0.2.0 and the check of which bWGR helper (`IMP`, `EigenGAU`, `K2X`) keeps a toy
  marker matrix's row names, under bWGR 2.2.13 and 2.2.18.
- `docs/g2f-switch-0.1.0-prereg.md`, `docs/g2f-switch-0.1.0-result.md`, `g2f_switch.py`,
  `test_g2f_switch.py`: M4 and full mixed by hybrid category (`grade`), and the same mix for any
  prediction table (`apply`) (numpy + pandas).
- `docs/g2f-predict-0.1.0.md`, `docs/g2f-predict-0.1.0-result.md`, `g2f_predict.py`,
  `test_g2f_predict.py`, `data/g2f-predict-expect-2024.json`: release-day entry builder (`plan`,
  `predict`) and its graded 2024 dry run.
- `docs/g2f-refold-0.1.0.md`, `g2f_refold.py`, `test_g2f_refold.py`, `data/g2f-refold-expect-2024.json`:
  re-chooses the mix weights on the hold-out seasons that match the test season's type, for any release.
- `docs/g2f-release-census-0.1.0.md`, `docs/g2f-release-census-0.1.0-result.md`,
  `g2f_release_census.py`, `test_g2f_release_census.py`, `data/g2f-release-census-expect-2024.json`:
  release census (standard library only) and its dry run on the 2024 release.
- `docs/g2f-cathistory-0.1.0-prereg.md`, `docs/g2f-cathistory-0.1.0-result.md`, `g2f_cathistory.py`,
  `test_g2f_cathistory.py`: per-season hybrid categories, the parent-line table and the 2026 checks'
  history (standard library only).
- `docs/g2f-entry-0.1.0.md`, `docs/g2f-entry-0.1.0-result.md`, `docs/g2f-entry-0.2.0.md`,
  `docs/g2f-entry-0.2.0-result.md`, `g2f_entry.py`, `test_g2f_entry.py`,
  `data/g2f-entry-expect-2024.json`, `data/g2f-entry-mgha-expect-2024.json`: entry tool (standard
  library only), its graded 2024 dry runs and the Mg/ha step.
- `results/`: outputs of the sealed runs that each result grades (`g2f_baseline.json`,
  `g2f_envkernel.json`, `g2f_checkhybrid.json`, `g2f_parentgca.json`, `g2f_newshrink.json`,
  `g2f_parentloc.json`, `g2f_ecreaction.json`, `g2f_gcablend.json`, `g2f_refmodel.json`,
  `g2f_refsplit.json`, `g2f_refr0.json`, `g2f_switch.json`, `g2f_cathistory.json`,
  `g2f_parents_2014_2024.csv`, `g2f_release_census_2024.json`, `g2f_entry_dryrun_2024.json`,
  `g2f_entry_mgha_2024.json`, `g2f_predict_2024.json`, `g2f_predict_plan.json`,
  `g2f_refmodel_regress.json`, `dimcheck_2.2.13.json`, `dimcheck_2.2.18.json`, per-environment r and
  per-row prediction tables).

```
pip install numpy pandas
python -m unittest -v test_g2f_baseline test_g2f_envkernel test_g2f_checkhybrid test_g2f_parentgca test_g2f_newshrink test_g2f_parentloc test_g2f_ecreaction test_g2f_gcablend test_g2f_refmodel test_g2f_refcheck test_g2f_switch test_g2f_release_census test_g2f_cathistory test_g2f_entry test_g2f_predict test_g2f_refold
python g2f_baseline.py --data-dir data --out-dir results
python g2f_envkernel.py --data-dir data --out-dir results
python g2f_checkhybrid.py --out-dir results
python g2f_parentgca.py --data-dir data --out-dir results
python g2f_newshrink.py --data-dir data --out-dir results
python g2f_parentloc.py --data-dir data --out-dir results
python g2f_ecreaction.py --data-dir data --out-dir results
python g2f_gcablend.py --data-dir data --out-dir results
# g2f-refmodel (R with bWGR and reshape2; the data folder must already hold the release files)
Rscript run_ref.R script_model.R data results [<library folder with bWGR 2.2.13>]
Rscript g2f_refmodel.R data results
python g2f_refmodel.py --data-dir data --out-dir results --ref-script script_model.R
python g2f_refcheck.py split --data-dir data --out-dir results
python g2f_refcheck.py r0 --data-dir data --out-dir results --ref-pred results/ref_2024_predictions.csv --ref-script script_model.R
Rscript dimcheck.R <library folder or none> results/dimcheck.json
python g2f_switch.py grade --data-dir data --out-dir results
# standard-library tools
python g2f_release_census.py --data-dir data --out-dir results --expect data/g2f-release-census-expect-2024.json --name g2f_release_census_2024
python g2f_cathistory.py --data-dir data --out-dir results
python g2f_entry.py dryrun --data-dir data --out-dir results --pred results/g2f_parentgca_2024_predictions.csv --col M4 --expect data/g2f-entry-expect-2024.json --name g2f_entry_dryrun_2024
python g2f_entry.py dryrun-mgha --data-dir data --out-dir results --pred results/g2f_parentgca_2024_predictions.csv --col M4 --expect data/g2f-entry-mgha-expect-2024.json --name g2f_entry_mgha_2024
# release day: list what a release holds, choose the mix weights on matching past seasons, then build
# M4 / full / mix upload files in Mg/ha (validated)
python g2f_predict.py plan --data-dir <release folder> --out-dir results
python g2f_refold.py choose --data-dir <release folder> --out-dir results --full-dir <preds/ from g2f_refmodel.R ... all> [--folds 2]
python g2f_predict.py predict --data-dir <release folder> --out-dir results --full <preds/<season>.csv from g2f_refmodel.R> [--a 0.5 --b 0.5]
# or by hand: mix two models by hybrid category, then predictions on any scale -> Mg/ha file
python g2f_switch.py apply --pred <table with M4 and full columns> --trait <trait csv> --a <a> --b <b> --out mix.csv
python g2f_entry.py mgha --trait <trait csv> --template <template csv> --pred mix.csv --col mix --out submission.csv
```

Data: Genomes to Fields 2024 Maize Genotype by Environment Prediction Competition release, CyVerse
Data Commons, DOI 10.25739/78mn-4394 (Open Data Commons PDDL). Data papers: Lima et al. 2023,
BMC Research Notes (doi 10.1186/s13104-023-06421-z) and the 2024 competition note
(doi 10.1186/s13104-026-07629-5). The 2024 leaderboard figures and rules are from EvalAI's public API
(challenge 2376, phase split 5893). The 2026 trial design is from genomes2fields.org (project overview,
read 2026-11-09). This repository is not affiliated with G2F.

Licence: code Apache-2.0; text and results CC BY 4.0. Contact: MV2, Munim, Inc., mv2@munimtech.com.
