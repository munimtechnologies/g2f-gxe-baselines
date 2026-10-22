# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
"""g2f_envkernel 0.1.0: environment-similarity weighting on top of g2f_baseline's M2 model.

For each test environment, every training environment gets a weight from how close its
environmental covariates (the organisers' 6_*_EC_Data files, reduced to principal components) are
to the test environment's. Model M2 of g2f_baseline 0.1.0 (marker ridge shrunk toward the
hybrid's own mean) is then refitted on the weighted hybrid means, so each environment gets its own
hybrid ranking. Equal weights ("uniform") reproduce M2 exactly.
The bandwidth is chosen inside each fold by validating on the last training year only, then the
chosen bandwidth is refitted on all training years and scored on the held-out year (2022, 2023 and
the organisers' released 2024 answers), with the competition metric (mean within-environment r).
Needs g2f_baseline.py 0.1.0 (same repository), numpy and pandas.
"""
import argparse
import json
import os

import numpy as np
import pandas as pd

import g2f_baseline as gb

gb.FILES.update({"ec_train": "Training_data/6_Training_EC_Data_2014_2023.csv",
                 "ec_test": "Testing_data/6_Testing_EC_Data_2024.csv"})
BANDWIDTHS = (0.25, 0.5, 1.0, 2.0, None)  # None = uniform weights (= M2)
N_PCS = 10
K_PRIOR = 1.0  # plots' worth of the hybrid's unweighted mean added to its weighted mean
MAX_MISSING = 0.5


def label(h):
    return "uniform" if h is None else "h%g" % h


def load_ec(paths, n_pcs=N_PCS):
    """{env: principal-component scores} from one or more EC files (one row per environment)."""
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
    ec = ec.loc[:, ec.isna().mean() <= MAX_MISSING]
    ec = ec.fillna(ec.mean())
    ec = ec.loc[:, ec.std() > 0]
    X = ec.to_numpy(dtype=float)
    X = (X - X.mean(axis=0)) / X.std(axis=0)
    U, S, _ = np.linalg.svd(X, full_matrices=False)
    k = min(n_pcs, X.shape[0] - 1, X.shape[1])
    scores = U[:, :k] * S[:k]
    explained = float((S[:k] ** 2).sum() / (S ** 2).sum()) if S.size else 0.0
    info = {"ec_envs": int(X.shape[0]), "ec_columns": int(X.shape[1]), "pcs": int(k),
            "variance_explained": round(explained, 4)}
    return {e: scores[i] for i, e in enumerate(ec.index)}, info


def distance_scale(envs, pcs):
    """Median squared distance between pairs of the given environments that have EC rows."""
    X = np.array([pcs[e] for e in envs if e in pcs])
    if len(X) < 2:
        return 1.0
    d2 = ((X[:, None, :] - X[None, :, :]) ** 2).sum(axis=2)
    med = float(np.median(d2[np.triu_indices(len(X), 1)]))
    return med if med > 0 else 1.0


def env_weights(target, envs, pcs, h, scale):
    """Weights (mean 1) over training envs for one test env. Uniform if h is None or the test env
    has no EC row; training envs without an EC row get the median weight."""
    w = np.ones(len(envs))
    if h is None or target not in pcs:
        return w
    have = np.array([e in pcs for e in envs])
    if not have.any():
        return w
    x = pcs[target]
    d2 = np.array([float(((pcs[e] - x) ** 2).sum()) for e in envs if e in pcs])
    wv = np.exp(-d2 / (h * scale))
    w[have] = wv
    w[~have] = np.median(wv)
    m = w.mean()
    return w / m if m > 0 else np.ones(len(envs))


def prepare(train, geno_names, Z, lambdas=gb.LAMBDAS):
    """Everything about one training set that does not depend on the environment weights."""
    tr = gb.zscore_train(train)
    hm = tr.groupby("Hybrid")["z"].agg(["mean", "count"])
    hybrids = list(hm.index)
    hpos = {h: i for i, h in enumerate(hybrids)}
    envs = sorted(tr["Env"].unique())
    epos = {e: i for i, e in enumerate(envs)}
    pairs = tr.groupby(["Hybrid", "Env"])["z"].agg(["sum", "count"]).reset_index()
    row = {h: i for i, h in enumerate(geno_names)}
    fit_h = [h for h in hybrids if h in row]
    Zf = Z[[row[h] for h in fit_h]]
    lam, cv = gb.choose_lambda(Zf, hm.loc[fit_h, "mean"].to_numpy(dtype=float), lambdas)
    zmean = Zf.mean(axis=0)
    Zc = Zf - zmean
    P = np.linalg.solve(Zc.T @ Zc + lam * np.eye(Z.shape[1]), Zc.T)
    return {"envs": envs, "hybrids": hybrids, "hpos": hpos, "row": row,
            "hi": pairs["Hybrid"].map(hpos).to_numpy(), "ei": pairs["Env"].map(epos).to_numpy(),
            "s": pairs["sum"].to_numpy(dtype=float), "n": pairs["count"].to_numpy(dtype=float),
            "mean": hm["mean"].to_numpy(dtype=float),
            "fit_i": np.array([hpos[h] for h in fit_h], dtype=int),
            "P": P, "G": Z - zmean, "lambda": lam, "cv_r": cv, "train_envs": len(envs)}


def predict_env(fit, w, test_hybrids, k_hybrid=gb.K_HYBRID):
    """M2 refitted on hybrid means weighted by w (one weight per training env)."""
    H = len(fit["hybrids"])
    pw = w[fit["ei"]]
    ws = np.bincount(fit["hi"], weights=pw * fit["s"], minlength=H)
    wn = np.bincount(fit["hi"], weights=pw * fit["n"], minlength=H)
    t = (ws + K_PRIOR * fit["mean"]) / (wn + K_PRIOR)
    y = t[fit["fit_i"]]
    mu = float(y.mean())
    gall = mu + fit["G"] @ (fit["P"] @ (y - mu))
    out = np.empty(len(test_hybrids))
    for j, h in enumerate(test_hybrids):
        base = float(gall[fit["row"][h]]) if h in fit["row"] else 0.0
        i = fit["hpos"].get(h)
        if i is not None:
            base += wn[i] / (wn[i] + k_hybrid) * (t[i] - base)
        out[j] = base
    return out


def predict(fit, test, pcs, bandwidths=BANDWIDTHS):
    """test with one prediction column per bandwidth."""
    out = test.copy().reset_index(drop=True)
    scale = distance_scale(fit["envs"], pcs)
    for h in bandwidths:
        out[label(h)] = np.nan
    for env, idx in out.groupby("Env").groups.items():
        hyb = list(out.loc[idx, "Hybrid"])
        for h in bandwidths:
            w = env_weights(env, fit["envs"], pcs, h, scale)
            out.loc[idx, label(h)] = predict_env(fit, w, hyb)
    return out


def choose(scores, bandwidths=BANDWIDTHS):
    """Best bandwidth by validation score; ties go to the wider kernel, uniform counting widest."""
    def key(h):
        s = scores[label(h)]["mean_r"]
        return (round(s, 6) if s is not None else -9.0, float("inf") if h is None else h)
    return max(bandwidths, key=key)


def run_fold(train, test, geno_names, Z, pcs, inner_year):
    inner_train = train[train["Year"] < inner_year]
    inner_test = train[train["Year"] == inner_year].groupby(
        ["Env", "Hybrid"], as_index=False)["Yield_Mg_ha"].mean().rename(columns={"Yield_Mg_ha": "obs"})
    cols = [label(h) for h in BANDWIDTHS]
    inner = gb.score(predict(prepare(inner_train, geno_names, Z), inner_test, pcs), cols)
    chosen = choose(inner)
    fit = prepare(train, geno_names, Z)
    preds = predict(fit, test, pcs)
    outer = gb.score(preds, cols)
    test_envs = sorted(test["Env"].unique())
    info = {"inner_year": inner_year, "inner_scores": inner, "chosen": label(chosen),
            "outer_scores": outer, "chosen_score": outer[label(chosen)]["mean_r"],
            "uniform_score": outer["uniform"]["mean_r"], "lambda": fit["lambda"],
            "train_envs": fit["train_envs"],
            "share_train_envs_with_ec": round(float(np.mean([e in pcs for e in fit["envs"]])), 4),
            "share_test_envs_with_ec": round(float(np.mean([e in pcs for e in test_envs])), 4)}
    if outer["uniform"]["mean_r"] is not None and info["chosen_score"] is not None:
        info["chosen_minus_uniform"] = round(info["chosen_score"] - outer["uniform"]["mean_r"], 4)
    return preds, info


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
    pcs, ec_info = load_ec([gb.fetch(args.data_dir, "ec_train"), gb.fetch(args.data_dir, "ec_test")])
    results = {"version": "0.1.0", "baseline_version": "0.1.0", "bandwidths": [label(h) for h in BANDWIDTHS],
               "k_prior": K_PRIOR, "ec": ec_info, "markers_used": int(Z.shape[1]), "folds": {}}
    print(json.dumps(results), flush=True)

    for year in gb.HOLDOUT_YEARS:
        train, test = gb.holdout(trait, year)
        _, info = run_fold(train, test, geno_names, Z, pcs, year - 1)
        results["folds"][str(year)] = info
        print(year, json.dumps(info), flush=True)

    test = template.merge(observed, on=["Env", "Hybrid"], how="left")
    preds, info = run_fold(trait, test, geno_names, Z, pcs, 2023)
    results["folds"]["2024"] = info
    print(2024, json.dumps(info), flush=True)

    cols = [label(h) for h in BANDWIDTHS]
    per_env = pd.DataFrame({c: gb.env_r(preds, c) for c in cols})
    per_env.index.name = "Env"
    per_env.round(4).to_csv(os.path.join(args.out_dir, "g2f_envkernel_2024_env_r.csv"))
    preds.round(5).to_csv(os.path.join(args.out_dir, "g2f_envkernel_2024_predictions.csv"), index=False)
    with open(os.path.join(args.out_dir, "g2f_envkernel.json"), "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=1, sort_keys=True)
    print(json.dumps({y: {k: f[k] for k in ("chosen", "chosen_score", "uniform_score")}
                      for y, f in results["folds"].items()}, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
