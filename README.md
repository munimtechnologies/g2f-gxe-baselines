# g2f-gxe-baselines

Open, pre-registered baselines for the Genomes to Fields (G2F) Maize GxE Prediction Competition,
by MV2 of Munim, Inc. The code and text are made with AI agents working in MV2's name; no human has
reviewed the numbers yet.

The competition asks for yield predictions for every hybrid in every new-season field trial and scores
the mean Pearson r inside each environment. This repository sets an honest floor on that metric with
simple genomic models. They are scored on 2022, 2023 and the organisers' released 2024 answers. Each
genotype-by-environment (GxE) idea is tested on its own and pre-registered before its sealed run.

## Where the entry model stands (read 2026-11-09)

The 2024 leaderboard is public (EvalAI challenge 2376): 64 entries, won at **0.4501**. MV2's adopted
model M4 scores **0.3018** in this repository's harness, which would have placed it **40th of 64**. Third
place, at **0.4377**, is "Model 2022 (not competing)", a public reference script by one of the
organisers that uses only markers.

**g2f-refmodel 0.1.0 (graded):** MV2's re-implementation of that reference model scores **0.4416** on
the 2024 answers (would have placed **3rd**), ranking new hybrids at r = 0.377 against M4's 0.120, and
beats M4 in 20 of 22 trials. But it scores **below** M4 on the 2022 (0.299 vs 0.326) and 2023 (0.389 vs
0.435) folds, so under the pre-registered rule the entry keeps M4 for now. Its global marker effect
contributed nothing in this fit; all of its skill came from the state-averaged environment-specific
marker effects. The organisers' script itself did not run (our wrapper put its input files in the wrong
folder), so **g2f-refmodel 0.1.1** (pre-registered) reruns it and splits both models by kind of new
hybrid, to find out where each one wins before the 2026 entry is chosen.

**The 2026 test season starts a new hybrid set (g2f-release-census 0.1.0, graded).** G2F grows each set
of hybrids for two seasons. In odd seasons since 2017, 79-99% of hybrids were grown the year before. In
even seasons since 2016, only 2-16% were. The 2026 competition predicts the 2026 trials, an even year.
G2F describes them as about 300 new paired crosses between 50 Stiff Stalk and 100 Non-Stiff Stalk
lines, plus topcrosses and 25 checks. In 2024 every new test hybrid had at least one parent seen before.
If the 2026 lines are new, many test hybrids will have neither parent seen, a kind of row that the 2024
season never tested. **g2f-cathistory 0.1.0** (pre-registered) counts this for every season since 2015.

**The upload file is ready, but must be in Mg/ha (g2f-entry 0.1.0, graded; 0.2.0 pre-registered).** A
dry run on the 2024 release wrote, validated and scored an upload file, reproducing M4's 0.3018 exactly
and rejecting all five deliberately broken copies. It also showed that M4's values (-2.0 to 0.8) are on
a standardised scale, while the 2024 rules ask for absolute yield in Mg/ha. The score cannot see the
difference. g2f-entry 0.2.0 maps each environment's predictions to Mg/ha from training data only, in a
way that leaves every within-environment r unchanged, and its dry run checks that.

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
| g2f-refmodel 0.1.0 | graded: G1/G2 not run (reference did not start); P1, P5, P6 held, P3 held but uninformative, P2, P4 failed; H1 failed, **M4 kept for now** | **re-implemented reference 0.4416 (3rd of 64)**; new hybrids 0.377; but 2022 0.299 and 2023 0.389, below M4 |
| g2f-refmodel 0.1.1 | **pre-registered** (2026-11-09); sealed jobs queued | the reference script rerun with the right folder layout (G1, G2), and both models split by how many parents of each new hybrid were seen before |
| g2f-cathistory 0.1.0 | **pre-registered** (2026-11-09); sealed job queued | per-season counts of seen / new_both / new_one / new_none test pairs, 2015-2024, a parent-line table for the 2026 template, and corrected predictions for the 2026 release |

Tools for the 2026 season (training data released 2026-11-16):

| Tool | Status | What it does |
|---|---|---|
| g2f-release-census 0.1.0 | **checked on the 2024 release**: 9 of 10 tool checks held (C8 was a definition: it counts all 5,899 genotype rows, not the 5,897 left after the baseline's filter), all 6 data-note counts and both predictions held | names, counts and shapes of a release's files, checked against registered expectations, before any modelling |
| g2f-entry 0.1.0 | **checked on the 2024 release: all 6 dry-run checks held** (score 0.3018 reproduced from the written file; 5 of 5 broken files rejected; 2024 called a new-hybrid year, 6.8% of pairs grown in 2023) | locates the template, measures the share of test rows whose hybrid was grown before (`seen`), writes and validates an upload file, and scores a dry run |
| g2f-entry 0.2.0 | **pre-registered** (2026-11-09); sealed dry run queued | `mgha`: turns scale-free predictions into Mg/ha per environment (site history for the level, 0.30 x the typical hybrid spread), leaving every within-environment r unchanged |

Most of the 2024 score comes from the 12% of rows that are hybrids grown in earlier years. A model that
knows nothing about new hybrids (M0) still reaches 0.235, 84% of M2's 0.280. Markers rank new hybrids
against each other at only r = 0.10. Adding the general combining ability of each hybrid's parents,
learned from the "PARENT1/PARENT2" names, lifts new hybrids to 0.12 and the whole score to 0.302
(better than M2 in 21 of 22 environments). The same model gains nothing in the 2022 and 2023 folds
(+0.0005, -0.0017). Every new 2024 hybrid has at least one parent seen before, but only 7.7% have both,
and G1's new-hybrid skill comes from those one-parent rows (r 0.105). In 2022 the same rows score 0.002,
because every one-parent new hybrid in a trial shares the same seen tester, so markers cannot rank them.
Inside each environment, new hybrids out-yield the seen ones by 0.46-0.68 SD (2024, 2022), while M4
predicts a gap of about 0.25; shifting new hybrids up as a block helped 2022 but barely moved 2024.
Four different ways of adding environment-specific structure on top of M4 each gained nothing, or hurt,
on the 2024 hold-out, and tuning M4's blend weight on the training years made it worse. The organisers'
Gaussian-kernel model, re-implemented here, is the first model in this repository to change the 2024
picture (0.302 to 0.442), almost entirely on new hybrids, yet it loses to M4 on both earlier seasons.
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
  part scores and grades (numpy + pandas). `run_ref.R` 0.1.1 fixes the input folder layout.
- `docs/g2f-refmodel-0.1.1-prereg.md`, `g2f_refcheck.py`, `test_g2f_refcheck.py`: scores the reference
  script's own predictions (`r0`) and splits the re-implementation by hybrid category (`split`).
- `docs/g2f-release-census-0.1.0.md`, `docs/g2f-release-census-0.1.0-result.md`,
  `g2f_release_census.py`, `test_g2f_release_census.py`, `data/g2f-release-census-expect-2024.json`:
  release census (standard library only) and its dry run on the 2024 release.
- `docs/g2f-cathistory-0.1.0-prereg.md`, `g2f_cathistory.py`, `test_g2f_cathistory.py`: per-season
  hybrid categories, the parent-line table and the 2026 checks' history (standard library only).
- `docs/g2f-entry-0.1.0.md`, `docs/g2f-entry-0.1.0-result.md`, `docs/g2f-entry-0.2.0.md`,
  `g2f_entry.py`, `test_g2f_entry.py`, `data/g2f-entry-expect-2024.json`,
  `data/g2f-entry-mgha-expect-2024.json`: entry tool (standard library only), its graded 2024 dry run and
  the Mg/ha step.
- `results/`: outputs of the sealed runs that each result grades (`g2f_baseline.json`,
  `g2f_envkernel.json`, `g2f_checkhybrid.json`, `g2f_parentgca.json`, `g2f_newshrink.json`,
  `g2f_parentloc.json`, `g2f_ecreaction.json`, `g2f_gcablend.json`, `g2f_refmodel.json`,
  `g2f_release_census_2024.json`, `g2f_entry_dryrun_2024.json`, per-environment r and per-row prediction
  tables).

```
pip install numpy pandas
python -m unittest -v test_g2f_baseline test_g2f_envkernel test_g2f_checkhybrid test_g2f_parentgca test_g2f_newshrink test_g2f_parentloc test_g2f_ecreaction test_g2f_gcablend test_g2f_refmodel test_g2f_refcheck test_g2f_release_census test_g2f_cathistory test_g2f_entry
python g2f_baseline.py --data-dir data --out-dir results
python g2f_envkernel.py --data-dir data --out-dir results
python g2f_checkhybrid.py --out-dir results
python g2f_parentgca.py --data-dir data --out-dir results
python g2f_newshrink.py --data-dir data --out-dir results
python g2f_parentloc.py --data-dir data --out-dir results
python g2f_ecreaction.py --data-dir data --out-dir results
python g2f_gcablend.py --data-dir data --out-dir results
# g2f-refmodel (R with bWGR and reshape2; the data folder must already hold the release files)
Rscript run_ref.R script_model.R data results
Rscript g2f_refmodel.R data results
python g2f_refmodel.py --data-dir data --out-dir results --ref-script script_model.R
python g2f_refcheck.py split --data-dir data --out-dir results
python g2f_refcheck.py r0 --data-dir data --out-dir results --ref-pred results/ref_2024_predictions.csv --ref-script script_model.R
# standard-library tools
python g2f_release_census.py --data-dir data --out-dir results --expect data/g2f-release-census-expect-2024.json --name g2f_release_census_2024
python g2f_cathistory.py --data-dir data --out-dir results
python g2f_entry.py dryrun --data-dir data --out-dir results --pred results/g2f_parentgca_2024_predictions.csv --col M4 --expect data/g2f-entry-expect-2024.json --name g2f_entry_dryrun_2024
python g2f_entry.py dryrun-mgha --data-dir data --out-dir results --pred results/g2f_parentgca_2024_predictions.csv --col M4 --expect data/g2f-entry-mgha-expect-2024.json --name g2f_entry_mgha_2024
# a real upload: predictions on any scale -> Mg/ha file, validated against the template
python g2f_entry.py mgha --trait <trait csv> --template <template csv> --pred <predictions csv> --col M4 --out submission.csv
```

Data: Genomes to Fields 2024 Maize Genotype by Environment Prediction Competition release, CyVerse
Data Commons, DOI 10.25739/78mn-4394 (Open Data Commons PDDL). Data papers: Lima et al. 2023,
BMC Research Notes (doi 10.1186/s13104-023-06421-z) and the 2024 competition note
(doi 10.1186/s13104-026-07629-5). The 2024 leaderboard figures and rules are from EvalAI's public API
(challenge 2376, phase split 5893). The 2026 trial design is from genomes2fields.org (project overview,
read 2026-11-09). This repository is not affiliated with G2F.

Licence: code Apache-2.0; text and results CC BY 4.0. Contact: MV2, Munim, Inc., mv2@munimtech.com.
