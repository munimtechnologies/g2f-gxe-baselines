# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
"""g2f_newshrink 0.1.0: recalibrate new-hybrid predictions as a block (scale s, offset o).

Seen hybrids (grown in a training year) keep g2f_parentgca's M4. Inside each test environment the new
hybrids get M5 = c + o + s * (M4 - c), where c is the mean M4 of the environment's new-hybrid rows
(observed yields are not used). s = 1, o = 0 gives M4.
(s, o) is chosen once on the 2022 fold (trained on 2014-2021) and applied unchanged to 2023 and 2024
(the organisers' released answers). The full grid is reported for every fold; the 2024 grid is
descriptive only. Also reports G1 and M4 new-hybrid r split by how many parents were seen in training,
and the new-minus-seen level gap in observed z yield and in M4.
Needs g2f_baseline.py and g2f_parentgca.py 0.1.0 (same repository), numpy and pandas.
"""
import argparse
import json
import os

import numpy as np
import pandas as pd

import g2f_baseline as gb
import g2f_parentgca as pg

S_GRID = (0.0, 0.25, 0.5, 0.75, 1.0)
O_GRID = (-0.5, -0.25, 0.0, 0.25, 0.5)
SELECT_YEAR = "2022"
BASELINE_2024 = {"M2": 0.2802, "M4": 0.3018}
REPRO_TOL = 0.005
MODELS = ("M2", "M4", "M5")


def key(s, o):
    return "s=%.2f,o=%+.2f" % (s, o)


def recalibrate(out, s, o, col="M4"):
    """col for seen rows; new rows pulled toward their environment's mean new prediction and shifted."""
    new = ~out["seen"].to_numpy(dtype=bool)
    res = out[col].to_numpy(dtype=float).copy()
    if new.any():
        c = out.loc[new].groupby("Env")[col].transform("mean").to_numpy(dtype=float)
        res[new] = c + o + s * (res[new] - c)
    return res


def grid(out, s_grid=S_GRID, o_grid=O_GRID):
    """{key(s, o): all-rows mean within-environment r} for every grid point."""
    df = out.copy()
    res = {}
    for s in s_grid:
        for o in o_grid:
            df["M5"] = recalibrate(out, s, o)
            res[key(s, o)] = gb.score(df, ("M5",))["M5"]["mean_r"]
    return res


def choose(scores, s_grid=S_GRID, o_grid=O_GRID):
    """Best (s, o) on the grid; ties go to the point nearest M4 (s = 1, o = 0)."""
    pts = [(s, o) for s in s_grid for o in o_grid]
    return max(pts, key=lambda p: (round(scores[key(*p)], 6), -abs(1.0 - p[0]) - abs(p[1])))


def known_parents(train, hybrids):
    """How many of each hybrid's parents (0-2) appear in a training hybrid's name (g2f_parentgca's pool)."""
    pool = {p for h in gb.zscore_train(train)["Hybrid"].unique() for p in pg.parents(h)}
    return np.array([sum(p in pool for p in pg.parents(h)) for h in hybrids], dtype=int)


def new_split(out, known):
    """G1 and M4 r on new rows with exactly one and with both parents seen."""
    new = ~out["seen"].to_numpy(dtype=bool)
    res = {}
    for k, name in ((1, "one_parent_seen"), (2, "both_parents_seen")):
        sub = out[new & (known == k)]
        res[name] = dict(gb.score(sub, ("G1", "M4")), rows=int(sub["obs"].notna().sum()))
    return res


def level_gap(out, col):
    """Mean over environments of (mean col of new rows - mean col of seen rows), observed rows only.
    For col == 'obs' the yields are z-scored within each environment first."""
    df = out[out["obs"].notna()].copy()
    if col == "obs":
        g = df.groupby("Env")["obs"]
        df["obs"] = (df["obs"] - g.transform("mean")) / g.transform("std")
    gaps = []
    for _, grp in df.groupby("Env"):
        s = grp["seen"].to_numpy(dtype=bool)
        v = grp[col].to_numpy(dtype=float)
        if s.any() and (~s).any():
            gap = v[~s].mean() - v[s].mean()
            if np.isfinite(gap):
                gaps.append(gap)
    return round(float(np.mean(gaps)), 4) if gaps else None


def fold(train, test, geno_names, Z, lambdas=gb.LAMBDAS):
    """g2f_parentgca predictions for one fold plus the recalibration grid and diagnostics."""
    preds, info = pg.fit_predict(train, test, geno_names, Z, lambdas=lambdas)
    known = known_parents(train, preds["Hybrid"])
    entry = {"fit": info, "grid": grid(preds), "new_split": new_split(preds, known),
             "level_gap": {"obs_z": level_gap(preds, "obs"), "M4": level_gap(preds, "M4")}}
    return preds, entry


def grade(results):
    """Pre-registered predictions P1-P5 and hypothesis H1 (docs/g2f-newshrink-0.1.0-prereg.md)."""
    f = results["folds"]
    s, o = results["chosen"]["s"], results["chosen"]["o"]
    g24 = f["2024"]["grid"]
    best_s = choose(g24, o_grid=(0.0,))[0]
    drop = round(g24[key(1.0, 0.0)] - g24[key(0.0, 0.0)], 4)
    one = f["2024"]["new_split"]["one_parent_seen"]["G1"]["mean_r"]
    d = {y: round(f[y]["score"]["M5"]["mean_r"] - f[y]["score"]["M4"]["mean_r"], 4) for y in ("2023", "2024")}
    g = {"P1_chosen_s_ge_0.75": {"value": s, "held": s >= 0.75},
         "P2_2024_best_s_at_o0_lt_1": {"value": best_s, "held": best_s < 1.0},
         "P3_G1_new_one_parent_gt_0.05": {"value": one, "held": one is not None and one > 0.05},
         "P4_M4_minus_s0_2024_ge_0.02": {"value": drop, "held": drop >= 0.02},
         "P5_abs_chosen_o_le_0.25": {"value": o, "held": abs(o) <= 0.25}}
    g["H1_adopt_M5"] = {"value": d, "held": bool(d["2024"] >= 0.01 and d["2023"] >= -0.005)}
    return g


def reproduces(f24):
    s = f24["score"]
    ok = all(s[m]["mean_r"] is not None and abs(s[m]["mean_r"] - v) <= REPRO_TOL
             for m, v in BASELINE_2024.items())
    return bool(ok and abs(f24["grid"][key(1.0, 0.0)] - s["M4"]["mean_r"]) <= 1e-4)


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
    results = {"version": "0.1.0", "parentgca_version": "0.1.0", "s_grid": list(S_GRID),
               "o_grid": list(O_GRID), "select_year": SELECT_YEAR, "markers_used": int(Z.shape[1]),
               "folds": {}}
    print(json.dumps(results), flush=True)

    preds = {}
    for year in gb.HOLDOUT_YEARS:
        train, test = gb.holdout(trait, year)
        preds[str(year)], results["folds"][str(year)] = fold(train, test, geno_names, Z)
        print(year, json.dumps(results["folds"][str(year)]["grid"]), flush=True)
    test = template.merge(observed, on=["Env", "Hybrid"], how="left")
    preds["2024"], results["folds"]["2024"] = fold(trait, test, geno_names, Z)
    print(2024, json.dumps(results["folds"]["2024"]["grid"]), flush=True)

    s, o = choose(results["folds"][SELECT_YEAR]["grid"])
    results["chosen"] = {"s": s, "o": o}
    for y, p in preds.items():
        p["M5"] = recalibrate(p, s, o)
        results["folds"][y]["score"] = gb.score(p, MODELS)
    results["reproduces_baseline"] = reproduces(results["folds"]["2024"])
    results["grading"] = grade(results)

    p24 = preds["2024"]
    per_env = pd.DataFrame({m: gb.env_r(p24, m) for m in MODELS})
    per_env.index.name = "Env"
    per_env.round(4).to_csv(os.path.join(args.out_dir, "g2f_newshrink_2024_env_r.csv"))
    with open(os.path.join(args.out_dir, "g2f_newshrink.json"), "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=1, sort_keys=True)
    print(json.dumps({"chosen": results["chosen"], "reproduces_baseline": results["reproduces_baseline"],
                      "grading": results["grading"],
                      "scores": {y: {m: f["score"][m]["mean_r"] for m in MODELS}
                                 for y, f in results["folds"].items()},
                      "new_split_2024": results["folds"]["2024"]["new_split"],
                      "level_gap": {y: f["level_gap"] for y, f in results["folds"].items()}},
                     indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
