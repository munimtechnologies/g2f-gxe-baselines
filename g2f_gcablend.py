# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
"""g2f_gcablend 0.1.0: tuning M4's parent-GCA blend weight and testing whether it generalises forward.

M4 blends the marker ridge M1 with parent general combining ability G1 at a fixed weight w = 0.5, then
shrinks toward each hybrid's own mean. This varies w over a grid, fits M1 and G1 once per fold, and
selects w by the mean all-rows within-environment Pearson r over the two training folds (2022 and 2023),
applying it unchanged to the organisers' released 2024 answers. Parent GCA helps the 2024 hold-out
(+0.0216 over M2) but barely moves 2022 (+0.0005) and slightly hurts 2023 (-0.0017), so the test is
whether tuning this one hyperparameter on past years beats the a-priori 0.5 on a forward season. The
full grid is reported for every fold; w = 0 reproduces M2 and w = 0.5 reproduces the adopted M4.
Needs g2f_baseline.py and g2f_parentgca.py 0.1.0 (same repository), numpy and pandas.
"""
import argparse
import json
import os

import numpy as np
import pandas as pd

import g2f_baseline as gb
import g2f_parentgca as pg

W_GRID = (0.0, 0.25, 0.5, 0.75, 1.0)
W_DEFAULT = 0.5
SELECT_YEARS = ("2022", "2023")
BASELINE_2024 = {"M2": 0.2802, "M4": 0.3018}   # M4 at w = 0 and w = 0.5 respectively
REPRO_TOL = 0.005
MODELS = ("M2", "G1", "M4")


def wkey(w):
    return "w=%g" % w


def m4_grid(train, test, geno_names, Z, ws=W_GRID, k_hybrid=gb.K_HYBRID):
    """Fit M1 (marker ridge) and G1 (parent GCA) once; return base predictions and M4 at each weight.

    Reproduces g2f_parentgca's M4 exactly: blend = (1-w)*M1 + w*G1, then, for a hybrid seen in training,
    shrink toward its own mean m0 by n/(n+k_hybrid). w = 0 gives M2; w = 0.5 gives the adopted M4.
    """
    base, info = gb.fit_predict(train, test, geno_names, Z)
    base = base.reset_index(drop=True)
    gca = pg.fit_gca(train)
    hm = gb.zscore_train(train).groupby("Hybrid")["z"].agg(["mean", "count"])
    base["G1"] = pg.predict_gca(gca, list(base["Hybrid"]))
    m0 = base["Hybrid"].map(hm["mean"])
    n = base["Hybrid"].map(hm["count"]).fillna(0.0)
    base["seen"] = m0.notna()
    cols = {}
    for w in ws:
        blend = (1.0 - w) * base["M1"] + w * base["G1"]
        cols[w] = np.where(m0.notna(), blend + n / (n + k_hybrid) * (m0.fillna(0.0) - blend), blend)
    info.update({"gca_lambda": gca["lambda"], "gca_parents": gca["parents"], "w_default": W_DEFAULT})
    return base, cols, info


def grid_scores(base, cols, ws=W_GRID):
    """All-rows mean within-environment r for M4 at each weight w."""
    return {wkey(w): gb.score(base.assign(M4=cols[w]), ("M4",))["M4"]["mean_r"] for w in ws}


def argmax_w(grid, ws=W_GRID, w_default=W_DEFAULT):
    """Weight with the best grid score; ties go to the weight nearest w_default, then the larger w."""
    cand = [w for w in ws if grid.get(wkey(w)) is not None]
    return max(cand, key=lambda w: (round(grid[wkey(w)], 6), -abs(w - w_default), w))


def select(train_grids, ws=W_GRID, w_default=W_DEFAULT):
    """Weight with the best mean all-rows r over the training folds; ties nearest w_default, then larger."""
    mean = {}
    for w in ws:
        vals = [g[wkey(w)] for g in train_grids if g.get(wkey(w)) is not None]
        mean[w] = float(np.mean(vals)) if vals else None
    cand = [w for w in ws if mean[w] is not None]
    best = max(cand, key=lambda w: (round(mean[w], 6), -abs(w - w_default), w))
    return best, {wkey(w): (round(mean[w], 6) if mean[w] is not None else None) for w in ws}


def grade(results):
    """Pre-registered predictions P1-P3 and hypothesis H1 (docs/g2f-gcablend-0.1.0-prereg.md)."""
    g24 = results["folds"]["2024"]["grid"]
    wstar = results["chosen"]["w"]
    at_star = g24.get(wkey(wstar))
    at_def = g24.get(wkey(W_DEFAULT))
    diff = round(at_star - at_def, 4) if (at_star is not None and at_def is not None) else None
    seq = [g24.get(wkey(w)) for w in (0.0, 0.25, W_DEFAULT)]
    mono = all(v is not None for v in seq) and seq[2] >= seq[1] >= seq[0]
    g = {"P1_wstar_le_0.25": {"value": wstar, "held": wstar is not None and wstar <= 0.25},
         "P2_2024_tuned_not_above_default": {"value": diff, "held": diff is not None and diff <= 0.002},
         "P3_2024_grid_increasing_to_default": {"value": seq, "held": bool(mono)}}
    g["H1_adopt_tuned_weight"] = {"value": {"w": wstar, "diff_2024": diff},
                                  "held": bool(wstar is not None and wstar != W_DEFAULT
                                               and diff is not None and diff >= 0.005)}
    return g


def reproduces(f24):
    g24 = f24["grid"]
    check = {"M2": g24.get(wkey(0.0)), "M4": g24.get(wkey(W_DEFAULT))}
    return all(check[m] is not None and abs(check[m] - v) <= REPRO_TOL for m, v in BASELINE_2024.items())


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data-dir", default="/data")
    ap.add_argument("--out-dir", default="/out")
    args = ap.parse_args()
    os.makedirs(args.data_dir, exist_ok=True)
    os.makedirs(args.out_dir, exist_ok=True)

    trait = gb.load_trait(gb.fetch(args.data_dir, "trait"))
    template = gb.load_pairs(gb.fetch(args.data_dir, "template"))
    observed = gb.load_pairs(gb.fetch(args.data_dir, "observed"), "obs")
    names = set(trait["Hybrid"]) | set(template["Hybrid"])
    geno_names, G = gb.read_numeric(gb.fetch(args.data_dir, "geno"), names)
    Z = gb.standardize(G)
    results = {"version": "0.1.0", "parentgca_version": "0.1.0", "w_grid": list(W_GRID),
               "w_default": W_DEFAULT, "select_years": list(SELECT_YEARS),
               "markers_used": int(Z.shape[1]), "folds": {}}
    print(json.dumps(results), flush=True)

    base24 = cols24 = None
    for year in gb.HOLDOUT_YEARS:
        train, test = gb.holdout(trait, year)
        base, cols, info = m4_grid(train, test, geno_names, Z)
        results["folds"][str(year)] = {"fit": info, "grid": grid_scores(base, cols)}
        print(year, json.dumps(results["folds"][str(year)]["grid"]), flush=True)

    test = template.merge(observed, on=["Env", "Hybrid"], how="left")
    base24, cols24, info24 = m4_grid(trait, test, geno_names, Z)
    seen = base24["seen"].to_numpy(dtype=bool)
    grid24, grid24_seen, grid24_new = {}, {}, {}
    for w in W_GRID:
        dfw = base24.assign(M4=cols24[w])
        grid24[wkey(w)] = gb.score(dfw, ("M4",))["M4"]["mean_r"]
        grid24_seen[wkey(w)] = gb.score(dfw[seen], ("M4",))["M4"]["mean_r"]
        grid24_new[wkey(w)] = gb.score(dfw[~seen], ("M4",))["M4"]["mean_r"]
    results["folds"]["2024"] = {"fit": info24, "grid": grid24, "grid_seen": grid24_seen,
                                "grid_new": grid24_new}
    print(2024, json.dumps(grid24), flush=True)

    wstar, train_mean = select([results["folds"][y]["grid"] for y in SELECT_YEARS])
    results["chosen"] = {"w": wstar, "train_mean_r": train_mean,
                         "per_year_argmax": {y: argmax_w(results["folds"][y]["grid"])
                                             for y in ("2022", "2023", "2024")}}
    results["reproduces_baseline"] = reproduces(results["folds"]["2024"])
    results["grading"] = grade(results)

    per_env = pd.DataFrame({"M2": gb.env_r(base24, "M2"),
                            "M4_w0.5": gb.env_r(base24.assign(M4=cols24[W_DEFAULT]), "M4"),
                            "M4_wstar": gb.env_r(base24.assign(M4=cols24[wstar]), "M4")})
    per_env.index.name = "Env"
    per_env.round(4).to_csv(os.path.join(args.out_dir, "g2f_gcablend_2024_env_r.csv"))
    with open(os.path.join(args.out_dir, "g2f_gcablend.json"), "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=1, sort_keys=True)
    print(json.dumps({"chosen": {"w": results["chosen"]["w"],
                                 "train_mean_r": results["chosen"]["train_mean_r"],
                                 "per_year_argmax": results["chosen"]["per_year_argmax"]},
                      "reproduces_baseline": results["reproduces_baseline"],
                      "grading": results["grading"]}, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
