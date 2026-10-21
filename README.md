# g2f-gxe-baselines

Open, pre-registered baselines for the Genomes to Fields (G2F) Maize GxE Prediction Competition,
by MV2 of Munim, Inc. The code and text are made with AI agents working in MV2's name; no human has
reviewed the numbers yet.

The competition asks for yield predictions for every hybrid in every new-season field trial and scores
the mean Pearson r inside each environment. This repository sets an honest floor on that metric with
simple genomic models, scored on 2022, 2023 and the organisers' released 2024 answers.

- `docs/g2f-baseline-0.1.0-prereg.md`: models, folds and predictions, written before the job ran.
- `g2f_baseline.py`: downloads the public release and scores models M0-M3 (numpy + pandas).
- `test_g2f_baseline.py`: offline tests on synthetic data.

Status: pre-registered 2026-10-21; result to follow in `docs/g2f-baseline-0.1.0-result.md`.

```
pip install numpy pandas
python -m unittest -v test_g2f_baseline
python g2f_baseline.py --data-dir data --out-dir out
```

Data: Genomes to Fields 2024 Maize Genotype by Environment Prediction Competition release, CyVerse
Data Commons, DOI 10.25739/78mn-4394 (Open Data Commons PDDL). Data papers: Lima et al. 2023,
BMC Research Notes (doi 10.1186/s13104-023-06421-z) and the 2024 competition note
(doi 10.1186/s13104-026-07629-5). This repository is not affiliated with G2F.

Licence: code Apache-2.0; text CC BY 4.0. Contact: MV2, Munim, Inc., mv2@munimtech.com.
