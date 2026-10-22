# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
"""g2f_parentgca 0.1.0: parent general combining ability (GCA) from G2F hybrid pedigree names.

G2F hybrid names are "PARENT1/PARENT2". G1 is a ridge regression of each training hybrid's mean
z-scored yield on 0/1 indicators of its two parents (one pool of parents, whichever side of the
cross), lambda by 5-fold CV over hybrids. A new hybrid borrows the effects of any parent seen in
training; a hybrid with no known parent gets the same constant as every other such hybrid.
M4 blends G1 50/50 with g2f_baseline's marker ridge M1 and shrinks the blend toward the hybrid's own
mean exactly as M2 does (so with a GCA weight of 0, M4 is M2).
Scored like g2f_baseline 0.1.0 (2022, 2023 and the organisers' released 2024 answers) on all rows,
and on 2024 also separately on previously grown ("seen") and new hybrids.
Needs g2f_baseline.py 0.1.0 (same repository), numpy and pandas.
"""
import argparse
import json
import os

import numpy as np
import pandas as pd

import g2f_baseline as gb

GCA_LAMBDAS = (0.3, 1.0, 3.0, 10.0, 30.0, 100.0)
W_GCA = 0.5
MODELS = gb.MODELS + ("G1", "M4")
BASELINE_2024 = {"M0": 0.2353, "M1": 0.2386, "M2": 0.2802}
REPRO_TOL = 0.005


def parents(hybrid):
    """The two parent names of 'P1/P2' (stripped, upper-cased); () unless the name is a two-way cross."""
    parts = [p.strip().upper() for p in str(hybrid).split("/")]
    if len(parts) != 2 or not all(parts):
        return ()
    return tuple(parts)


def design(hybrids, index):
    """hybrids x parents 0/1 matrix over the parents in index; parents not in index are left out."""
    X = np.zeros((len(hybrids), len(index)))
    for i, h in enumerate(hybrids):
        for p in parents(h):
            j = index.get(p)
            if j is not None:
                X[i, j] = 1.0
    return X


def fit_gca(train, lambdas=GCA_LAMBDAS):
    """Ridge of training hybrid means (within-environment z) on parent indicators."""
    hm = gb.zscore_train(train).groupby("Hybrid")["z"].mean()
    fit_h = [h for h in hm.index if parents(h)]
    index = {p: j for j, p in enumerate(sorted({p for h in fit_h for p in parents(h)}))}
    X = design(fit_h, index)
    y = hm.loc[fit_h].to_numpy(dtype=float)
    lam, cv = gb.choose_lambda(X, y, lambdas)
    mu, xmean, beta = gb.ridge_fit(X, y, lam)
    return {"index": index, "mu": mu, "xmean": xmean, "beta": beta, "lambda": lam,
            "cv_r": {str(k): round(v, 4) for k, v in cv.items()},
            "gca_hybrids": len(fit_h), "train_hybrids": int(len(hm)), "parents": len(index)}


def predict_gca(gca, hybrids):
    return gca["mu"] + (design(hybrids, gca["index"]) - gca["xmean"]) @ gca["beta"]


def coverage(hybrids, index):
    """Shares of the given rows whose name is a two-way cross, with >= 1 and with 2 parents in index."""
    hybrids = list(hybrids)
    if not hybrids:
        return {"rows": 0, "named_cross": None, "one_parent_seen": None, "both_parents_seen": None}
    known = [sum(p in index for p in parents(h)) for h in hybrids]
    return {"rows": len(hybrids),
            "named_cross": round(float(np.mean([bool(parents(h)) for h in hybrids])), 4),
            "one_parent_seen": round(float(np.mean([k >= 1 for k in known])), 4),
            "both_parents_seen": round(float(np.mean([k == 2 for k in known])), 4)}


def fit_predict(train, test, geno_names, Z, lambdas=gb.LAMBDAS, gca_lambdas=GCA_LAMBDAS,
                w_gca=W_GCA, k_hybrid=gb.K_HYBRID):
    """g2f_baseline's M0-M3 plus G1 (parent GCA), M4 (blend shrunk to own mean) and a 'seen' flag."""
    out, info = gb.fit_predict(train, test, geno_names, Z, k_hybrid=k_hybrid, lambdas=lambdas)
    out = out.reset_index(drop=True)
    gca = fit_gca(train, gca_lambdas)
    hm = gb.zscore_train(train).groupby("Hybrid")["z"].agg(["mean", "count"])
    out["G1"] = predict_gca(gca, list(out["Hybrid"]))
    blend = (1.0 - w_gca) * out["M1"] + w_gca * out["G1"]
    m0 = out["Hybrid"].map(hm["mean"])
    n = out["Hybrid"].map(hm["count"]).fillna(0.0)
    out["M4"] = np.where(m0.notna(), blend + n / (n + k_hybrid) * (m0.fillna(0.0) - blend), blend)
    out["seen"] = m0.notna()
    rows = out[out["obs"].notna()] if "obs" in out.columns else out
    info.update({"gca_lambda": gca["lambda"], "gca_cv_r": gca["cv_r"], "gca_hybrids": gca["gca_hybrids"],
                 "gca_parents": gca["parents"], "w_gca": w_gca,
                 "coverage_new_rows": coverage(rows.loc[~rows["seen"], "Hybrid"], gca["index"]),
                 "coverage_all_rows": coverage(rows["Hybrid"], gca["index"])})
    return out, info


def grade(folds):
    """Pre-registered predictions P1-P4 and hypothesis H1 (docs/g2f-parentgca-0.1.0-prereg.md)."""
    f = folds["2024"]
    cov = f["fit"]["coverage_new_rows"]
    s, new = f["score"], f["score_new"]
    d = {y: round(folds[y]["score"]["M4"]["mean_r"] - folds[y]["score"]["M2"]["mean_r"], 4)
         for y in folds}
    g = {"P1_one_parent_seen_ge_0.50": {"value": cov["one_parent_seen"],
                                        "held": cov["one_parent_seen"] is not None
                                        and cov["one_parent_seen"] >= 0.50},
         "P2_both_parents_seen_ge_0.20": {"value": cov["both_parents_seen"],
                                          "held": cov["both_parents_seen"] is not None
                                          and cov["both_parents_seen"] >= 0.20},
         "P3_G1_new_gt_0.05": {"value": new["G1"]["mean_r"],
                               "held": new["G1"]["mean_r"] is not None and new["G1"]["mean_r"] > 0.05},
         "P4_M4_minus_M2_2024_in_-0.02_0.04": {"value": d["2024"], "held": -0.02 <= d["2024"] <= 0.04}}
    held_h1 = d["2024"] >= 0.01 and all(d[y] >= -0.005 for y in d if y != "2024")
    g["H1_adopt_M4"] = {"value": d, "held": bool(held_h1)}
    return g


def reproduces(score):
    return all(score[m]["mean_r"] is not None and abs(score[m]["mean_r"] - v) <= REPRO_TOL
               for m, v in BASELINE_2024.items())


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
    results = {"version": "0.1.0", "baseline_version": "0.1.0", "w_gca": W_GCA,
               "gca_lambdas": list(GCA_LAMBDAS), "markers_used": int(Z.shape[1]), "folds": {}}
    print(json.dumps(results), flush=True)

    for year in gb.HOLDOUT_YEARS:
        train, test = gb.holdout(trait, year)
        preds, info = fit_predict(train, test, geno_names, Z)
        results["folds"][str(year)] = {"fit": info, "score": gb.score(preds, MODELS)}
        print(year, json.dumps(results["folds"][str(year)]), flush=True)

    test = template.merge(observed, on=["Env", "Hybrid"], how="left")
    preds, info = fit_predict(trait, test, geno_names, Z)
    seen = preds["seen"].to_numpy(dtype=bool)
    results["folds"]["2024"] = {"fit": info, "score": gb.score(preds, MODELS),
                                "score_seen": gb.score(preds[seen], MODELS),
                                "score_new": gb.score(preds[~seen], MODELS)}
    print(2024, json.dumps(results["folds"]["2024"]), flush=True)
    results["reproduces_baseline"] = reproduces(results["folds"]["2024"]["score"])
    results["grading"] = grade(results["folds"])

    per_env = pd.DataFrame({m: gb.env_r(preds, m) for m in MODELS})
    for m in ("M1", "G1", "M4"):
        per_env[m + "_new"] = pd.Series(gb.env_r(preds[~seen], m))
    per_env.index.name = "Env"
    per_env.round(4).to_csv(os.path.join(args.out_dir, "g2f_parentgca_2024_env_r.csv"))
    preds.round(5).to_csv(os.path.join(args.out_dir, "g2f_parentgca_2024_predictions.csv"), index=False)
    with open(os.path.join(args.out_dir, "g2f_parentgca.json"), "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=1, sort_keys=True)
    print(json.dumps({"reproduces_baseline": results["reproduces_baseline"],
                      "grading": results["grading"],
                      "scores": {y: {m: f["score"][m]["mean_r"] for m in ("M2", "G1", "M4")}
                                 for y, f in results["folds"].items()}}, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
