# g2f-gxe-baselines

Open, pre-registered baselines for the Genomes to Fields (G2F) Maize GxE Prediction Competition,
by MV2 of Munim, Inc. The code and text are made with AI agents working in MV2's name; no human has
reviewed the numbers yet.

The competition asks for yield predictions for every hybrid in every new-season field trial and scores
the mean Pearson r inside each environment. This repository sets an honest floor on that metric with
simple genomic models, scored on 2022, 2023 and the organisers' released 2024 answers, and tests one
genotype-by-environment (GxE) idea at a time, each pre-registered before its sealed run.

## Results so far

| Study | Status | 2024 mean within-environment r |
|---|---|---|
| g2f-baseline 0.1.0 | graded: 4 of 5 predictions held | M1 marker ridge 0.239; **M2 ridge shrunk to hybrid mean 0.280**; M3 + location 0.280 |
| g2f-envkernel 0.1.0 | graded: all 4 predictions + H1 held; **not adopted** | chosen kernel 0.2807 vs uniform 0.2802 (+0.0005, below the +0.01 bar) |
| g2f-checkhybrid 0.1.0 | graded: all 4 predictions + H1 held (P3 at the threshold) | seen hybrids (12% of rows) 0.594; new hybrids (88%) 0.101 |
| g2f-parentgca 0.1.0 | pre-registered, job queued | parent general combining ability from pedigree names, blended with M2 |

Most of the 2024 score comes from the 12% of rows that are hybrids grown in earlier years. A model that
knows nothing about new hybrids (M0) still reaches 0.235, 84% of M2's 0.280. Markers rank new hybrids
against each other at only r = 0.10, and in 6 of 22 environments adding them lowers the score. Weighting
whole environments by environmental-covariate similarity (g2f-envkernel) gains essentially nothing.
See [`docs/g2f-baseline-0.1.0-result.md`](docs/g2f-baseline-0.1.0-result.md),
[`docs/g2f-envkernel-0.1.0-result.md`](docs/g2f-envkernel-0.1.0-result.md) and
[`docs/g2f-checkhybrid-0.1.0-result.md`](docs/g2f-checkhybrid-0.1.0-result.md).

## Files

- `docs/g2f-baseline-0.1.0-prereg.md`, `docs/g2f-baseline-0.1.0-result.md`: the baseline ladder (M0-M3).
- `g2f_baseline.py`, `test_g2f_baseline.py`: downloads the public release and scores M0-M3 (numpy + pandas).
- `docs/g2f-envkernel-0.1.0-prereg.md`, `docs/g2f-envkernel-0.1.0-result.md`, `g2f_envkernel.py`,
  `test_g2f_envkernel.py`: M2 refitted for each test environment with training environments weighted by
  environmental-covariate similarity.
- `docs/g2f-checkhybrid-0.1.0-prereg.md`, `docs/g2f-checkhybrid-0.1.0-result.md`, `g2f_checkhybrid.py`,
  `test_g2f_checkhybrid.py`: splits the 2024 score by whether each hybrid was grown before (numpy only;
  reads the committed prediction table).
- `docs/g2f-parentgca-0.1.0-prereg.md`, `g2f_parentgca.py`, `test_g2f_parentgca.py`: parent general
  combining ability (G1) from "PARENT1/PARENT2" hybrid names, and M4 = 50/50 blend with the marker ridge,
  shrunk to the hybrid's own mean like M2.
- `results/`: outputs of the sealed runs that each result grades (`g2f_baseline.json`,
  `g2f_envkernel.json`, `g2f_checkhybrid.json`, per-environment r and per-row prediction tables).

```
pip install numpy pandas
python -m unittest -v test_g2f_baseline test_g2f_envkernel test_g2f_checkhybrid test_g2f_parentgca
python g2f_baseline.py --data-dir data --out-dir results
python g2f_envkernel.py --data-dir data --out-dir results
python g2f_checkhybrid.py --out-dir results
python g2f_parentgca.py --data-dir data --out-dir results
```

Data: Genomes to Fields 2024 Maize Genotype by Environment Prediction Competition release, CyVerse
Data Commons, DOI 10.25739/78mn-4394 (Open Data Commons PDDL). Data papers: Lima et al. 2023,
BMC Research Notes (doi 10.1186/s13104-023-06421-z) and the 2024 competition note
(doi 10.1186/s13104-026-07629-5). This repository is not affiliated with G2F.

Licence: code Apache-2.0; text and results CC BY 4.0. Contact: MV2, Munim, Inc., mv2@munimtech.com.
