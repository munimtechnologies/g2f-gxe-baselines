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
| g2f-checkhybrid 0.1.0 | pre-registered, job queued | seen vs new hybrid decomposition of the 0.280 score |

Only 12% of the 2024 test rows are hybrids tested in earlier years, so most of the score has to come
from markers. Weighting whole environments by environmental-covariate similarity (g2f-envkernel) gains
essentially nothing over equal weights: it helps in about as many 2024 environments as it hurts. See
[`docs/g2f-baseline-0.1.0-result.md`](docs/g2f-baseline-0.1.0-result.md) and
[`docs/g2f-envkernel-0.1.0-result.md`](docs/g2f-envkernel-0.1.0-result.md).

## Files

- `docs/g2f-baseline-0.1.0-prereg.md`, `docs/g2f-baseline-0.1.0-result.md`: the baseline ladder (M0-M3).
- `g2f_baseline.py`, `test_g2f_baseline.py`: downloads the public release and scores M0-M3 (numpy + pandas).
- `docs/g2f-envkernel-0.1.0-prereg.md`, `docs/g2f-envkernel-0.1.0-result.md`, `g2f_envkernel.py`,
  `test_g2f_envkernel.py`: M2 refitted for each test environment with training environments weighted by
  environmental-covariate similarity.
- `docs/g2f-checkhybrid-0.1.0-prereg.md`, `g2f_checkhybrid.py`, `test_g2f_checkhybrid.py`: decomposes the
  2024 score by whether each hybrid was grown before (numpy only; reads the committed prediction table).
- `results/`: outputs of the sealed runs that each result grades (`g2f_baseline.json`,
  `g2f_envkernel.json`, per-environment r and per-row prediction tables).

```
pip install numpy pandas
python -m unittest -v test_g2f_baseline test_g2f_envkernel test_g2f_checkhybrid
python g2f_baseline.py --data-dir data --out-dir results
python g2f_envkernel.py --data-dir data --out-dir results
python g2f_checkhybrid.py --out-dir results
```

Data: Genomes to Fields 2024 Maize Genotype by Environment Prediction Competition release, CyVerse
Data Commons, DOI 10.25739/78mn-4394 (Open Data Commons PDDL). Data papers: Lima et al. 2023,
BMC Research Notes (doi 10.1186/s13104-023-06421-z) and the 2024 competition note
(doi 10.1186/s13104-026-07629-5). This repository is not affiliated with G2F.

Licence: code Apache-2.0; text and results CC BY 4.0. Contact: MV2, Munim, Inc., mv2@munimtech.com.
