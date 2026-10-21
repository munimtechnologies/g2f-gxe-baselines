# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
"""g2f_baseline 0.1.0: open baselines for the G2F maize GxE yield prediction competition.

Scores four simple models with the competition metric (mean within-environment Pearson r)
on three held-out years: 2022 and 2023 (trained on earlier years only) and 2024 (trained on
2014-2023, scored against the organisers' released 7_Testing_Observed_Values.csv).
Data: Genomes to Fields 2024 competition release, CyVerse DOI 10.25739/78mn-4394 (PDDL).
Models, all on within-environment z-scored yield:
  M0 hybrid mean over training plots (0 for hybrids never tested)
  M1 ridge regression of hybrid means on markers (lambda by 5-fold CV over hybrids)
  M2 M1 shrunk toward the hybrid's own mean: M1 + n/(n+5) * (mean - M1)
  M3 M2 plus the hybrid's shrunken residual at the same location: + c/(c+10) * resid
Within-environment r ignores environment means, so only the ranking of hybrids inside each
environment is scored. numpy and pandas only.
"""
import argparse
import json
import os
import urllib.request

import numpy as np
import pandas as pd

BASE = ("https://data.cyverse.org/dav-anon/iplant/home/shared/commons_repo/curated/"
        "GenomesToFields_GenotypeByEnvironment_PredictionCompetition_2025/")
FILES = {
    "trait": "Training_data/1_Training_Trait_Data_2014_2023.csv",
    "geno": "Training_data/5_Genotype_Data_All_2014_2025_Hybrids_numerical.txt",
    "vcf": "Training_data/5_Genotype_Data_All_2014_2025_Hybrids.vcf",
    "template": "Testing_data/1_Submission_Template_2024.csv",
    "observed": "Testing_data/7_Testing_Observed_Values.csv",
}
LAMBDAS = (10.0, 100.0, 1000.0, 10000.0, 100000.0, 1000000.0)
K_HYBRID = 5.0
K_LOC = 10.0
MIN_ROWS = 3
MODELS = ("M0", "M1", "M2", "M3")
HOLDOUT_YEARS = (2022, 2023)


def fetch(data_dir, key):
    path = os.path.join(data_dir, os.path.basename(FILES[key]))
    if not os.path.exists(path):
        urllib.request.urlretrieve(BASE + FILES[key], path)
    print("data", key, path, os.path.getsize(path), "bytes", flush=True)
    return path


def env_location(env):
    return str(env).strip().rsplit("_", 1)[0]


def env_year(env):
    tail = str(env).strip().rsplit("_", 1)[-1]
    return int(tail) if tail.isdigit() else None


def load_trait(path):
    df = pd.read_csv(path, low_memory=False)
    df["Env"] = df["Env"].astype(str).str.strip()
    df["Hybrid"] = df["Hybrid"].astype(str).str.strip()
    if "Year" in df.columns:
        df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    else:
        df["Year"] = df["Env"].map(env_year)
    df["Yield_Mg_ha"] = pd.to_numeric(df["Yield_Mg_ha"], errors="coerce")
    df = df.dropna(subset=["Yield_Mg_ha", "Year"])
    df["Year"] = df["Year"].astype(int)
    return df[["Env", "Year", "Hybrid", "Yield_Mg_ha"]].reset_index(drop=True)


def load_pairs(path, value_name=None):
    """Env, Hybrid (and the yield column renamed to value_name) from a template-format file."""
    df = pd.read_csv(path)
    df["Env"] = df["Env"].astype(str).str.strip()
    df["Hybrid"] = df["Hybrid"].astype(str).str.strip()
    if value_name is None:
        return df[["Env", "Hybrid"]].drop_duplicates().reset_index(drop=True)
    col = "Yield_Mg_ha" if "Yield_Mg_ha" in df.columns else \
        [c for c in df.columns if c not in ("Env", "Hybrid")][0]
    df[value_name] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=[value_name])
    return df.groupby(["Env", "Hybrid"], as_index=False)[value_name].mean()


def read_numeric(path, names):
    """(hybrid names, hybrids x markers array) from a delimited numeric file, either orientation."""
    skip = 0
    with open(path, encoding="utf-8", errors="replace") as fh:
        first = fh.readline()
        while first and (not first.strip() or first.strip().lower().startswith("<numeric")):
            skip += 1
            first = fh.readline()
    sep = "\t" if "\t" in first else ("," if "," in first else r"\s+")
    df = pd.read_csv(path, sep=sep, skiprows=skip, index_col=0)
    df.index = [str(i).strip() for i in df.index]
    df.columns = [str(c).strip() for c in df.columns]
    names = set(names)
    in_rows = int(df.index.isin(names).sum())
    in_cols = int(df.columns.isin(names).sum())
    if in_rows == 0 and in_cols == 0:
        raise ValueError("no hybrid names found in %s" % path)
    if in_cols > in_rows:
        df = df.loc[:, df.columns.isin(names)].T
    else:
        df = df[df.index.isin(names)]
    df = df[~df.index.duplicated()]
    mat = df.apply(pd.to_numeric, errors="coerce")
    if mat.notna().to_numpy().mean() < 0.5:
        raise ValueError("genotype values in %s are not numeric" % path)
    return list(mat.index), mat.to_numpy(dtype=float)


def read_vcf(path, names):
    """(hybrid names, hybrids x markers alt-allele dosage) from a VCF."""
    names = set(names)
    keep, samples, cols = None, None, []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith("##"):
                continue
            parts = line.rstrip("\r\n").split("\t")
            if line.startswith("#"):
                samples = [s.strip() for s in parts[9:]]
                keep = [i for i, s in enumerate(samples) if s in names]
                if not keep:
                    raise ValueError("no hybrid names found in %s" % path)
                continue
            fmt = parts[8].split(":") if len(parts) > 8 else ["GT"]
            gi = fmt.index("GT") if "GT" in fmt else 0
            vals = np.full(len(keep), np.nan)
            for j, i in enumerate(keep):
                alleles = parts[9 + i].split(":")[gi].replace("|", "/").split("/")
                if "." not in alleles:
                    vals[j] = sum(1 for a in alleles if a != "0")
            cols.append(vals)
    if keep is None:
        raise ValueError("no #CHROM header in %s" % path)
    return [samples[i] for i in keep], np.column_stack(cols)


def standardize(G):
    """Impute missing calls with the marker mean; drop empty and constant markers; z-score."""
    G = np.array(G, dtype=float)
    G = G[:, ~np.all(np.isnan(G), axis=0)]
    mean = np.nanmean(G, axis=0)
    G = np.where(np.isnan(G), mean, G)
    sd = G.std(axis=0)
    keep = sd > 0
    return (G[:, keep] - mean[keep]) / sd[keep]


def ridge_fit(Z, y, lam):
    zmean = Z.mean(axis=0)
    Zc = Z - zmean
    mu = float(y.mean())
    beta = np.linalg.solve(Zc.T @ Zc + lam * np.eye(Z.shape[1]), Zc.T @ (y - mu))
    return mu, zmean, beta


def choose_lambda(Z, y, lambdas=LAMBDAS, folds=5, seed=0):
    """Lambda with the best CV correlation over hybrids (ties go to the larger lambda)."""
    order = np.random.default_rng(seed).permutation(len(y))
    parts = np.array_split(order, folds)
    preds = {lam: np.empty(len(y)) for lam in lambdas}
    for part in parts:
        train = np.setdiff1d(order, part)
        zmean = Z[train].mean(axis=0)
        Zc = Z[train] - zmean
        mu = float(y[train].mean())
        A, b = Zc.T @ Zc, Zc.T @ (y[train] - mu)
        eye = np.eye(Z.shape[1])
        for lam in lambdas:
            beta = np.linalg.solve(A + lam * eye, b)
            preds[lam][part] = mu + (Z[part] - zmean) @ beta
    scores = {lam: float(np.corrcoef(preds[lam], y)[0, 1]) for lam in lambdas}
    best = max(lambdas, key=lambda lam: (round(scores[lam], 6), lam))
    return best, scores


def zscore_train(train):
    tr = train.copy()
    stats = tr.groupby("Env")["Yield_Mg_ha"].agg(["mean", "std", "count"])
    tr = tr.join(stats, on="Env")
    tr = tr[(tr["count"] >= 2) & (tr["std"] > 0)].copy()
    tr["z"] = (tr["Yield_Mg_ha"] - tr["mean"]) / tr["std"]
    return tr


def fit_predict(train, test, geno_names, Z, k_hybrid=K_HYBRID, k_loc=K_LOC, lambdas=LAMBDAS):
    """Columns M0-M3 for every test (Env, Hybrid) row, plus a dict describing the fit."""
    tr = zscore_train(train)
    hm = tr.groupby("Hybrid")["z"].agg(["mean", "count"])
    row = {h: i for i, h in enumerate(geno_names)}
    fit_h = [h for h in hm.index if h in row]
    y = hm.loc[fit_h, "mean"].to_numpy(dtype=float)
    Zf = Z[[row[h] for h in fit_h]]
    lam, cv = choose_lambda(Zf, y, lambdas)
    mu, zmean, beta = ridge_fit(Zf, y, lam)
    gall = mu + (Z - zmean) @ beta
    g = {h: float(gall[i]) for h, i in row.items()}
    m0 = hm["mean"].to_dict()
    n = hm["count"].to_dict()

    def m2(h):
        base = g.get(h, 0.0)
        if h in m0:
            return base + n[h] / (n[h] + k_hybrid) * (m0[h] - base)
        return base

    tr["loc"] = tr["Env"].map(env_location)
    tr["resid"] = tr["z"] - tr["Hybrid"].map(m2)
    lr = tr.groupby(["loc", "Hybrid"])["resid"].agg(["mean", "count"])
    loc_adj = {key: c / (c + k_loc) * m for key, m, c in zip(lr.index, lr["mean"], lr["count"])}

    out = test.copy()
    out["M0"] = out["Hybrid"].map(lambda h: m0.get(h, 0.0))
    out["M1"] = out["Hybrid"].map(lambda h: g.get(h, 0.0))
    out["M2"] = out["Hybrid"].map(m2)
    out["M3"] = [p + loc_adj.get((env_location(e), h), 0.0)
                 for p, e, h in zip(out["M2"], out["Env"], out["Hybrid"])]
    hybrids = out["Hybrid"]
    info = {"train_rows": int(len(tr)), "train_envs": int(tr["Env"].nunique()),
            "train_hybrids": int(len(hm)), "ridge_hybrids": int(len(fit_h)), "lambda": lam,
            "cv_r": {str(k): round(v, 4) for k, v in cv.items()},
            "test_rows": int(len(out)), "test_envs": int(out["Env"].nunique()),
            "test_hybrids": int(hybrids.nunique()),
            "share_rows_hybrid_seen": round(float(hybrids.isin(set(m0)).mean()), 4),
            "share_rows_hybrid_genotyped": round(float(hybrids.isin(set(row)).mean()), 4),
            "share_rows_hybrid_seen_at_location": round(float(np.mean(
                [(env_location(e), h) in loc_adj for e, h in zip(out["Env"], hybrids)])), 4)}
    return out, info


def env_r(df, col, obs="obs"):
    """{env: Pearson r} inside each environment; a constant prediction scores 0.
    Environments with fewer than MIN_ROWS observed rows or constant observations are skipped."""
    res = {}
    for env, grp in df.groupby("Env"):
        grp = grp.dropna(subset=[obs, col])
        if len(grp) < MIN_ROWS or grp[obs].std() == 0:
            continue
        if grp[col].std() == 0:
            res[env] = 0.0
        else:
            res[env] = float(np.corrcoef(grp[obs], grp[col])[0, 1])
    return res


def score(df, models=MODELS):
    out = {}
    for m in models:
        rs = env_r(df, m)
        out[m] = {"mean_r": round(float(np.mean(list(rs.values()))), 4) if rs else None,
                  "envs": len(rs)}
    return out


def holdout(trait, year):
    train = trait[trait["Year"] < year]
    test = trait[trait["Year"] == year].groupby(["Env", "Hybrid"], as_index=False)["Yield_Mg_ha"].mean()
    return train, test.rename(columns={"Yield_Mg_ha": "obs"})


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data-dir", default="/data")
    ap.add_argument("--out-dir", default="/out")
    args = ap.parse_args()
    os.makedirs(args.data_dir, exist_ok=True)
    os.makedirs(args.out_dir, exist_ok=True)

    trait = load_trait(fetch(args.data_dir, "trait"))
    template = load_pairs(fetch(args.data_dir, "template"))
    observed = load_pairs(fetch(args.data_dir, "observed"), "obs")
    names = set(trait["Hybrid"]) | set(template["Hybrid"])
    try:
        geno_names, G = read_numeric(fetch(args.data_dir, "geno"), names)
        source = "numerical"
    except (ValueError, pd.errors.ParserError) as exc:
        print("numerical genotype file not usable (%s); reading the VCF" % exc, flush=True)
        geno_names, G = read_vcf(fetch(args.data_dir, "vcf"), names)
        source = "vcf"
    Z = standardize(G)
    results = {"version": "0.1.0", "genotype_source": source, "genotyped_hybrids": len(geno_names),
               "markers_used": int(Z.shape[1]), "trait_rows": int(len(trait)),
               "trait_years": sorted(int(y) for y in trait["Year"].unique()),
               "k_hybrid": K_HYBRID, "k_loc": K_LOC, "folds": {}}
    print(json.dumps(results), flush=True)

    for year in HOLDOUT_YEARS:
        train, test = holdout(trait, year)
        preds, info = fit_predict(train, test, geno_names, Z)
        results["folds"][str(year)] = {"fit": info, "score": score(preds)}
        print(year, json.dumps(results["folds"][str(year)]), flush=True)

    test = template.merge(observed, on=["Env", "Hybrid"], how="left")
    preds, info = fit_predict(trait, test, geno_names, Z)
    info["template_rows_with_observation"] = int(test["obs"].notna().sum())
    results["folds"]["2024"] = {"fit": info, "score": score(preds)}
    print(2024, json.dumps(results["folds"]["2024"]), flush=True)

    per_env = pd.DataFrame({m: env_r(preds, m) for m in MODELS})
    per_env.index.name = "Env"
    per_env.round(4).to_csv(os.path.join(args.out_dir, "g2f_2024_env_r.csv"))
    preds.round(5).to_csv(os.path.join(args.out_dir, "g2f_2024_predictions.csv"), index=False)
    with open(os.path.join(args.out_dir, "g2f_baseline.json"), "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=1, sort_keys=True)
    print(json.dumps({y: f["score"] for y, f in results["folds"].items()}, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
