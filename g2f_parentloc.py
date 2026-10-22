# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
"""g2f_parentloc 0.1.0: parent-by-location effects on top of g2f_parentgca's M4.

A training hybrid's residual in an environment is its mean within-environment z yield there minus its
mean over all its training environments (only hybrids grown in at least two training environments).
A parent's effect at a location is the sum of the residuals of every training hybrid with that parent
grown at that location, divided by (count + k). M6 = M4 + the sum of the hybrid's distinct parents'
effects at the test environment's location (0 for a parent never grown there).
k is chosen once on the 2022 fold (trained on 2014-2021) from K_GRID or 'off' (M6 = M4) and applied
unchanged to 2023 and 2024 (the organisers' released answers). The full grid is reported for every fold.
Also reports, per fold, how many new-hybrid rows have a parent grown at the same location before, how
many distinct seen parents the new hybrids of each environment have, and in how many environments G1
is constant among new hybrids with exactly one seen parent.
Needs g2f_baseline.py and g2f_parentgca.py 0.1.0 (same repository), numpy and pandas.
"""
import argparse
import json
import os

import numpy as np
import pandas as pd

import g2f_baseline as gb
import g2f_parentgca as pg

K_GRID = (5.0, 20.0, 80.0, 320.0)
SELECT_YEAR = "2022"
BASELINE_2024 = {"M2": 0.2802, "M4": 0.3018}
REPRO_TOL = 0.005
MODELS = ("M2", "M4", "M6")


def key(k):
    return "off" if k is None else "k=%g" % k


def residuals(train):
    """(loc, Hybrid, resid) per training environment for hybrids grown in at least two environments."""
    eh = gb.zscore_train(train).groupby(["Env", "Hybrid"], as_index=False)["z"].mean()
    eh = eh[eh.groupby("Hybrid")["z"].transform("count") >= 2].copy()
    eh["resid"] = eh["z"] - eh.groupby("Hybrid")["z"].transform("mean")
    eh["loc"] = eh["Env"].map(gb.env_location)
    return eh[["loc", "Hybrid", "resid"]].reset_index(drop=True)


def parent_loc(res):
    """{(parent, loc): (sum of residuals, count)} over residual rows of hybrids with that parent."""
    acc = {}
    for loc, h, r in zip(res["loc"], res["Hybrid"], res["resid"]):
        for p in set(pg.parents(h)):
            s, c = acc.get((p, loc), (0.0, 0))
            acc[(p, loc)] = (s + float(r), c + 1)
    return acc


def effect(acc, hybrids, envs, k):
    """Sum over each hybrid's distinct parents of (residual sum / (count + k)) at the env's location."""
    out = np.zeros(len(hybrids))
    if k is None:
        return out
    for i, (h, e) in enumerate(zip(hybrids, envs)):
        loc = gb.env_location(e)
        for p in set(pg.parents(h)):
            s, c = acc.get((p, loc), (0.0, 0))
            out[i] += s / (c + k)
    return out


def with_m6(preds, acc, k):
    return preds.assign(M6=preds["M4"].to_numpy(dtype=float) + effect(acc, preds["Hybrid"], preds["Env"], k))


def choose(scores, k_grid=K_GRID):
    """Best k on the grid; ties go to the larger k, and 'off' (M4) counts as the largest."""
    pts = list(k_grid) + [None]
    return max(enumerate(pts), key=lambda ip: (round(scores[key(ip[1])], 6), ip[0]))[1]


def pool(train):
    """Every parent of a training hybrid (g2f_parentgca's parent pool)."""
    return {p for h in gb.zscore_train(train)["Hybrid"].unique() for p in pg.parents(h)}


def diagnostics(out, acc, seen_parents):
    """Location coverage and parent diversity of the observed new-hybrid rows."""
    new = out[~out["seen"].to_numpy(dtype=bool) & out["obs"].notna().to_numpy()]
    if new.empty:
        return {"new_rows": 0, "share_new_rows_parent_at_location": None,
                "distinct_seen_parents_per_env": None, "one_parent_envs": 0,
                "share_one_parent_envs_constant_G1": None}
    at_loc = [any((p, gb.env_location(e)) in acc for p in pg.parents(h))
              for h, e in zip(new["Hybrid"], new["Env"])]
    distinct = new.groupby("Env")["Hybrid"].agg(
        lambda hs: len({p for h in hs for p in pg.parents(h) if p in seen_parents}))
    one = new[[sum(p in seen_parents for p in pg.parents(h)) == 1 for h in new["Hybrid"]]]
    g = one.groupby("Env")["G1"]
    sizes, spread = g.size(), g.agg(lambda v: float(np.ptp(v.to_numpy(dtype=float))))
    eligible = [e for e in sizes.index if sizes[e] >= gb.MIN_ROWS]
    const = [bool(spread[e] < 1e-9) for e in eligible]
    return {"new_rows": int(len(new)),
            "share_new_rows_parent_at_location": round(float(np.mean(at_loc)), 4),
            "distinct_seen_parents_per_env": {"median": float(np.median(distinct)),
                                              "min": int(distinct.min()), "envs": int(len(distinct))},
            "one_parent_envs": len(eligible),
            "share_one_parent_envs_constant_G1": round(float(np.mean(const)), 4) if const else None}


def fold(train, test, geno_names, Z, lambdas=gb.LAMBDAS, k_grid=K_GRID):
    """g2f_parentgca predictions for one fold, the parent-by-location table, the k grid and diagnostics."""
    preds, info = pg.fit_predict(train, test, geno_names, Z, lambdas=lambdas)
    res = residuals(train)
    acc = parent_loc(res)
    grid = {key(k): gb.score(with_m6(preds, acc, k), ("M6",))["M6"]["mean_r"] for k in k_grid}
    grid[key(None)] = gb.score(preds, ("M4",))["M4"]["mean_r"]
    entry = {"fit": info, "grid": grid, "residual_rows": int(len(res)), "parent_locations": len(acc),
             "diagnostics": diagnostics(preds, acc, pool(train))}
    return preds, acc, entry


def grade(results):
    """Pre-registered predictions P1-P5 and hypothesis H1 (docs/g2f-parentloc-0.1.0-prereg.md)."""
    f = results["folds"]
    d24, d22 = f["2024"]["diagnostics"], f["2022"]["diagnostics"]
    at_loc = d24["share_new_rows_parent_at_location"]
    distinct = (d24["distinct_seen_parents_per_env"] or {}).get("median")
    const = d22["share_one_parent_envs_constant_G1"]
    d = {y: round(f[y]["score"]["M6"]["mean_r"] - f[y]["score"]["M4"]["mean_r"], 4) for y in ("2023", "2024")}
    new = f["2024"]["score_new"]
    dn = None
    if new["M6"]["mean_r"] is not None and new["M4"]["mean_r"] is not None:
        dn = round(new["M6"]["mean_r"] - new["M4"]["mean_r"], 4)
    g = {"P1_2024_new_rows_parent_at_location_ge_0.70": {"value": at_loc,
                                                          "held": at_loc is not None and at_loc >= 0.70},
         "P2_2024_median_distinct_seen_parents_ge_3": {"value": distinct,
                                                       "held": distinct is not None and distinct >= 3},
         "P3_2022_share_one_parent_envs_constant_G1_ge_0.5": {"value": const,
                                                              "held": const is not None and const >= 0.5},
         "P4_M6_minus_M4_2024_in_-0.005_0.02": {"value": d["2024"], "held": -0.005 <= d["2024"] <= 0.02},
         "P5_M6_minus_M4_2024_new_rows_gt_0": {"value": dn, "held": dn is not None and dn > 0}}
    g["H1_adopt_M6"] = {"value": d, "held": bool(d["2024"] >= 0.01 and d["2023"] >= -0.005)}
    return g


def reproduces(f24):
    s = f24["score"]
    ok = all(s[m]["mean_r"] is not None and abs(s[m]["mean_r"] - v) <= REPRO_TOL
             for m, v in BASELINE_2024.items())
    return bool(ok and abs(f24["grid"][key(None)] - s["M4"]["mean_r"]) <= 1e-4)


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
    results = {"version": "0.1.0", "parentgca_version": "0.1.0", "k_grid": list(K_GRID),
               "select_year": SELECT_YEAR, "markers_used": int(Z.shape[1]), "folds": {}}
    print(json.dumps(results), flush=True)

    preds, accs = {}, {}
    for year in gb.HOLDOUT_YEARS:
        train, test = gb.holdout(trait, year)
        preds[str(year)], accs[str(year)], results["folds"][str(year)] = fold(train, test, geno_names, Z)
        print(year, json.dumps(results["folds"][str(year)]["grid"]), flush=True)
    test = template.merge(observed, on=["Env", "Hybrid"], how="left")
    preds["2024"], accs["2024"], results["folds"]["2024"] = fold(trait, test, geno_names, Z)
    print(2024, json.dumps(results["folds"]["2024"]["grid"]), flush=True)

    k = choose(results["folds"][SELECT_YEAR]["grid"])
    results["chosen"] = {"k": k, "key": key(k)}
    for y, p in preds.items():
        p = preds[y] = with_m6(p, accs[y], k)
        seen = p["seen"].to_numpy(dtype=bool)
        f = results["folds"][y]
        f["score"] = gb.score(p, MODELS)
        f["score_seen"] = gb.score(p[seen], MODELS)
        f["score_new"] = gb.score(p[~seen], MODELS)
    results["reproduces_baseline"] = reproduces(results["folds"]["2024"])
    results["grading"] = grade(results)

    p24 = preds["2024"]
    per_env = pd.DataFrame({m: gb.env_r(p24, m) for m in MODELS})
    new24 = p24[~p24["seen"].to_numpy(dtype=bool)]
    for m in ("M4", "M6"):
        per_env[m + "_new"] = pd.Series(gb.env_r(new24, m))
    per_env.index.name = "Env"
    per_env.round(4).to_csv(os.path.join(args.out_dir, "g2f_parentloc_2024_env_r.csv"))
    with open(os.path.join(args.out_dir, "g2f_parentloc.json"), "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=1, sort_keys=True)
    print(json.dumps({"chosen": results["chosen"], "reproduces_baseline": results["reproduces_baseline"],
                      "grading": results["grading"],
                      "scores": {y: {m: f["score"][m]["mean_r"] for m in MODELS}
                                 for y, f in results["folds"].items()},
                      "diagnostics": {y: f["diagnostics"] for y, f in results["folds"].items()}},
                     indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
