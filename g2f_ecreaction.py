# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
"""g2f_ecreaction 0.1.0: a marker-by-environmental-covariate reaction norm on top of M4.

Each genotyped hybrid is reduced to K marker principal components (u) and each environment to L
principal components of the organisers' EC (weather and soil) data (e). A ridge regression of every
training hybrid's mean within-environment z yield on [u, e, kron(u, e)] learns a reaction norm: the
interaction block B (K x L) lets a marker PC's effect change with the environment. The interaction-only
prediction for a row is r_int(h, env) = u_h^T B e_env (0 for an ungenotyped hybrid or an environment
with no EC row). M7 = M4 + alpha * r_int, with alpha in ALPHA_GRID or 0 (M7 = M4). A constant shift of
r_int (the ridge centring offset) is dropped because it does not change any within-environment ranking.
alpha is chosen once on the 2022 fold (trained on 2014-2021) and applied unchanged to 2023 and 2024
(the organisers' released answers). The full grid is reported for every fold.
Also reports, per fold, the grouped-CV r of the reaction-norm model, how much r_int reorders hybrids
within an environment relative to M4, and the pooled correlation of r_int with M4.
Needs g2f_baseline.py and g2f_parentgca.py 0.1.0 (same repository), numpy and pandas.
"""
import argparse
import json
import os

import numpy as np
import pandas as pd

import g2f_baseline as gb
import g2f_parentgca as pg

gb.FILES.update({"ec_train": "Training_data/6_Training_EC_Data_2014_2023.csv",
                 "ec_test": "Testing_data/6_Testing_EC_Data_2024.csv"})
K_MARK = 20            # marker principal components
L_EC = 10             # environmental-covariate principal components
RN_LAMBDAS = (100.0, 1000.0, 10000.0, 100000.0)
ALPHA_GRID = (0.5, 1.0, 2.0)   # 0.0 (M7 = M4) is always included
SELECT_YEAR = "2022"
MAX_MISSING = 0.5
BASELINE_2024 = {"M2": 0.2802, "M4": 0.3018}
REPRO_TOL = 0.005
MODELS = ("M2", "M4", "M7")


def akey(a):
    return "a=0" if a == 0 else "a=%g" % a


def _standardize_cols(X):
    """Centre each column and scale to unit variance; leave constant columns at 0."""
    X = np.asarray(X, dtype=float)
    sd = X.std(axis=0)
    keep = sd > 0
    out = np.zeros_like(X)
    out[:, keep] = (X[:, keep] - X[:, keep].mean(axis=0)) / sd[keep]
    return out


def marker_scores(geno_names, Z, k=K_MARK):
    """{hybrid name: standardized top-k marker PC scores} from the SVD of the marker matrix."""
    U, S, _ = np.linalg.svd(Z, full_matrices=False)
    k = int(min(k, S.shape[0]))
    sc = _standardize_cols(U[:, :k] * S[:k])
    return {h: sc[i] for i, h in enumerate(geno_names)}, k


def load_ec(paths, l=L_EC, max_missing=MAX_MISSING):
    """{env: standardized top-l EC PC scores} from one or more EC files (one row per environment)."""
    frames = []
    for path in paths:
        df = pd.read_csv(path, low_memory=False)
        env_col = "Env" if "Env" in df.columns else df.columns[0]
        df[env_col] = df[env_col].astype(str).str.strip()
        df = df.set_index(env_col)
        df.index.name = "Env"
        df = df.drop(columns=[c for c in df.columns if str(c).strip().lower() == "year"])
        frames.append(df.apply(pd.to_numeric, errors="coerce"))
    ec = pd.concat(frames, axis=0, join="outer")
    ec = ec[~ec.index.duplicated()]
    ec = ec.loc[:, ec.isna().mean() <= max_missing]
    ec = ec.fillna(ec.mean())
    ec = ec.loc[:, ec.std() > 0]
    X = (ec.to_numpy(dtype=float) - ec.to_numpy(dtype=float).mean(axis=0)) / ec.to_numpy(dtype=float).std(axis=0)
    U, S, _ = np.linalg.svd(X, full_matrices=False)
    k = int(min(l, S.shape[0]))
    sc = _standardize_cols(U[:, :k] * S[:k])
    info = {"ec_envs": int(X.shape[0]), "ec_columns": int(X.shape[1]), "ec_pcs": int(k),
            "variance_explained": round(float((S[:k] ** 2).sum() / (S ** 2).sum()), 4) if S.size else 0.0}
    return {e: sc[i] for i, e in enumerate(ec.index)}, info


def features(U, E):
    """[u, e, kron(u, e)] for aligned marker-PC rows U (n x K) and EC-PC rows E (n x L)."""
    U, E = np.asarray(U, dtype=float), np.asarray(E, dtype=float)
    inter = (U[:, :, None] * E[:, None, :]).reshape(len(U), -1)
    return np.hstack([U, E, inter])


def observations(train, umap, emap):
    """(U, E, y, hybrids) for training hybrid-by-environment means with marker PCs and EC PCs."""
    tr = gb.zscore_train(train)
    obs = tr.groupby(["Env", "Hybrid"], as_index=False)["z"].mean()
    mask = np.array([h in umap for h in obs["Hybrid"]]) & obs["Env"].isin(emap).to_numpy()
    obs = obs[mask].reset_index(drop=True)
    U = np.array([umap[h] for h in obs["Hybrid"]]) if len(obs) else np.zeros((0, 0))
    E = np.array([emap[e] for e in obs["Env"]]) if len(obs) else np.zeros((0, 0))
    return U, E, obs["z"].to_numpy(dtype=float), obs["Hybrid"].to_numpy()


def cv_grouped(X, y, groups, lambdas=RN_LAMBDAS, folds=5, seed=0):
    """Best lambda by 5-fold CV with whole hybrids held out; ties go to the larger lambda."""
    uniq = np.array(sorted(set(groups)))
    fold_of_group = {g: i for g, i in zip(uniq, np.random.default_rng(seed).integers(0, folds, len(uniq)))}
    fold = np.array([fold_of_group[g] for g in groups])
    eye = np.eye(X.shape[1])
    preds = {lam: np.empty(len(y)) for lam in lambdas}
    for f in range(folds):
        te = fold == f
        tr = ~te
        if not te.any() or not tr.any():
            for lam in lambdas:
                preds[lam][te] = y[tr].mean() if tr.any() else 0.0
            continue
        xmean = X[tr].mean(axis=0)
        Xc = X[tr] - xmean
        mu = float(y[tr].mean())
        A, b = Xc.T @ Xc, Xc.T @ (y[tr] - mu)
        for lam in lambdas:
            beta = np.linalg.solve(A + lam * eye, b)
            preds[lam][te] = mu + (X[te] - xmean) @ beta
    scores = {lam: float(np.corrcoef(preds[lam], y)[0, 1]) if np.std(preds[lam]) > 0 else 0.0
              for lam in lambdas}
    best = max(lambdas, key=lambda lam: (round(scores[lam], 6), lam))
    return best, scores


def fit_rn(train, umap, emap, k, l, lambdas=RN_LAMBDAS):
    """Fit the reaction-norm ridge; return the interaction block B (k x l) and the grouped-CV r."""
    U, E, y, groups = observations(train, umap, emap)
    info = {"rn_rows": int(len(y)), "rn_hybrids": int(len(set(groups))), "marker_pcs": k, "ec_pcs": l,
            "interaction_features": k * l}
    if len(y) <= k + l + k * l:
        return {"B": np.zeros((k, l)), "lambda": None, "cv_r": 0.0, "cv_scores": {}, "info": info}
    X = features(U, E)
    lam, scores = cv_grouped(X, y, groups, lambdas)
    mu, xmean, beta = gb.ridge_fit(X, y, lam)
    B = beta[k + l:].reshape(k, l)
    info["cv_r"] = round(scores[lam], 4)
    return {"B": B, "lambda": lam, "cv_r": scores[lam], "cv_scores": scores, "info": info}


def r_int(preds, umap, emap, B):
    """u_h^T B e_env for every row (0 for an ungenotyped hybrid or an EC-less environment)."""
    k, l = B.shape
    U = np.array([umap.get(h, np.zeros(k)) for h in preds["Hybrid"]])
    E = np.array([emap.get(e, np.zeros(l)) for e in preds["Env"]])
    if len(preds) == 0:
        return np.zeros(0)
    return np.einsum("nk,kl,nl->n", U, B, E)


def with_m7(preds, rint, alpha):
    return preds.assign(M7=preds["M4"].to_numpy(dtype=float) + alpha * np.asarray(rint, dtype=float))


def choose(grid, alphas=ALPHA_GRID):
    """Best alpha on the grid; ties go to the smaller alpha (0 = M4 wins every tie)."""
    pts = [0.0] + list(alphas)
    return max(pts, key=lambda a: (round(grid[akey(a)], 6), -a))


def sd_ratio(preds, rint, min_rows=gb.MIN_ROWS):
    """Mean within-env SD of r_int divided by mean within-env SD of M4, over observed test rows."""
    df = preds.assign(_r=np.asarray(rint, dtype=float))
    df = df[df["obs"].notna()] if "obs" in df.columns else df
    rr, mm = [], []
    for _, grp in df.groupby("Env"):
        if len(grp) < min_rows:
            continue
        rr.append(float(grp["_r"].std()))
        mm.append(float(grp["M4"].std()))
    denom = float(np.mean(mm)) if mm else 0.0
    return round(float(np.mean(rr)) / denom, 4) if denom > 0 else None


def diagnostics(preds, rint):
    """How much the reaction norm reorders hybrids within an environment, and its overlap with M4."""
    df = preds.assign(_r=np.asarray(rint, dtype=float))
    df = df[df["obs"].notna()] if "obs" in df.columns else df
    cor = None
    if len(df) >= gb.MIN_ROWS and df["_r"].std() > 0 and df["M4"].std() > 0:
        cor = round(float(np.corrcoef(df["_r"], df["M4"])[0, 1]), 4)
    return {"int_main_sd_ratio": sd_ratio(preds, rint), "cor_int_m4": cor,
            "share_rows_rint_nonzero": round(float(np.mean(np.asarray(rint) != 0.0)), 4) if len(preds) else None}


def fold(train, test, geno_names, Z, umap, emap, k, l, lambdas=RN_LAMBDAS, alphas=ALPHA_GRID):
    """M2/M4 predictions, the reaction-norm interaction, the alpha grid and diagnostics for one fold."""
    preds, _ = pg.fit_predict(train, test, geno_names, Z)
    preds = preds.reset_index(drop=True)
    rn = fit_rn(train, umap, emap, k, l, lambdas)
    rint = r_int(preds, umap, emap, rn["B"])
    grid = {akey(a): gb.score(with_m7(preds, rint, a), ("M7",))["M7"]["mean_r"] for a in alphas}
    grid[akey(0.0)] = gb.score(preds.assign(M7=preds["M4"]), ("M7",))["M7"]["mean_r"]
    entry = {"fit": dict(rn["info"], lambda_rn=rn["lambda"]), "grid": grid, "rn_cv_r": round(rn["cv_r"], 4),
             "diagnostics": diagnostics(preds, rint)}
    return preds, rint, entry


def grade(results):
    """Pre-registered predictions P1-P5 and hypothesis H1 (docs/g2f-ecreaction-0.1.0-prereg.md)."""
    f = results["folds"]
    cv24 = f["2024"]["rn_cv_r"]
    ratio24 = f["2024"]["diagnostics"]["int_main_sd_ratio"]
    d = {y: round(f[y]["score"]["M7"]["mean_r"] - f[y]["score"]["M4"]["mean_r"], 4) for y in ("2023", "2024")}
    new = f["2024"]["score_new"]
    dn = None
    if new["M7"]["mean_r"] is not None and new["M4"]["mean_r"] is not None:
        dn = round(new["M7"]["mean_r"] - new["M4"]["mean_r"], 4)
    alpha = results["chosen"]["alpha"]
    g = {"P1_2024_rn_cv_r_ge_0.30": {"value": cv24, "held": cv24 is not None and cv24 >= 0.30},
         "P2_2024_int_main_sd_ratio_ge_0.05": {"value": ratio24,
                                               "held": ratio24 is not None and ratio24 >= 0.05},
         "P3_M7_minus_M4_2024_in_-0.01_0.02": {"value": d["2024"], "held": -0.01 <= d["2024"] <= 0.02},
         "P4_alpha_star_gt_0": {"value": alpha, "held": alpha is not None and alpha > 0},
         "P5_M7_minus_M4_2024_new_rows_gt_0": {"value": dn, "held": dn is not None and dn > 0}}
    g["H1_adopt_M7"] = {"value": d, "held": bool(d["2024"] >= 0.01 and d["2023"] >= -0.005)}
    return g


def reproduces(f24):
    s = f24["score"]
    ok = all(s[m]["mean_r"] is not None and abs(s[m]["mean_r"] - v) <= REPRO_TOL
             for m, v in BASELINE_2024.items())
    return bool(ok and abs(f24["grid"][akey(0.0)] - s["M4"]["mean_r"]) <= 1e-4)


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
    umap, k = marker_scores(geno_names, Z, K_MARK)
    emap, ec_info = load_ec([gb.fetch(args.data_dir, "ec_train"), gb.fetch(args.data_dir, "ec_test")], L_EC)
    l = ec_info["ec_pcs"]
    results = {"version": "0.1.0", "parentgca_version": "0.1.0", "marker_pcs": k, "ec": ec_info,
               "rn_lambdas": list(RN_LAMBDAS), "alpha_grid": list(ALPHA_GRID), "select_year": SELECT_YEAR,
               "markers_used": int(Z.shape[1]), "folds": {}}
    print(json.dumps(results), flush=True)

    preds, rints = {}, {}
    for year in gb.HOLDOUT_YEARS:
        train, test = gb.holdout(trait, year)
        preds[str(year)], rints[str(year)], results["folds"][str(year)] = \
            fold(train, test, geno_names, Z, umap, emap, k, l)
        print(year, json.dumps(results["folds"][str(year)]["grid"]), flush=True)
    test = template.merge(observed, on=["Env", "Hybrid"], how="left")
    preds["2024"], rints["2024"], results["folds"]["2024"] = \
        fold(trait, test, geno_names, Z, umap, emap, k, l)
    print(2024, json.dumps(results["folds"]["2024"]["grid"]), flush=True)

    alpha = choose(results["folds"][SELECT_YEAR]["grid"])
    results["chosen"] = {"alpha": alpha}
    for y in preds:
        p = preds[y] = with_m7(preds[y], rints[y], alpha)
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
    for m in ("M4", "M7"):
        per_env[m + "_new"] = pd.Series(gb.env_r(new24, m))
    per_env.index.name = "Env"
    per_env.round(4).to_csv(os.path.join(args.out_dir, "g2f_ecreaction_2024_env_r.csv"))
    with open(os.path.join(args.out_dir, "g2f_ecreaction.json"), "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=1, sort_keys=True)
    print(json.dumps({"chosen": results["chosen"], "reproduces_baseline": results["reproduces_baseline"],
                      "grading": results["grading"],
                      "scores": {y: {m: f["score"][m]["mean_r"] for m in MODELS}
                                 for y, f in results["folds"].items()}}, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
