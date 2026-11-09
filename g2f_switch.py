# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
"""g2f_switch 0.1.0: M4 and the re-implemented reference model ("full") mixed by hybrid category.

grade  rebuilds M4 (g2f_parentgca 0.1.0) on the 2022 and 2024 folds, joins the committed g2f-refmodel
       0.1.0 "full" predictions, z-scores both inside each environment over every predicted row, and
       scores each mix  a * z(full) + (1 - a) * z(M4)  for new hybrids with exactly one parent seen in
       training (new_one) and  b * z(full) + (1 - b) * z(M4)  for every other row, with a and b on a
       5-point grid. (a, b) is chosen on 2022 only; 2024 is the forward check
       (docs/g2f-switch-0.1.0-prereg.md).
apply  writes the same mix for any prediction table (Env, Hybrid and two model columns), given the
       training trait file, for a real upload through g2f_entry.py mgha.
Metric: mean over environments of the within-environment Pearson r (g2f_refcheck.mean_r).
numpy and pandas; needs g2f_baseline.py, g2f_parentgca.py and g2f_refcheck.py from this repository.
"""
import argparse
import json
import os

import numpy as np
import pandas as pd

import g2f_refcheck as rc

VERSION = "0.1.0"
GRID = (0.0, 0.25, 0.5, 0.75, 1.0)
FOLDS = ("2022", "2024")
# published scores this run must reproduce (gate R1)
PUBLISHED = {"M4": {"2022": 0.3262, "2024": 0.3018},     # results/g2f_parentgca.json
             "full": {"2022": 0.2987, "2024": 0.4416}}   # results/g2f_refsplit.json, category "all"
REPRO_TOL = {"M4": 0.005, "full": 0.0005}
MIN_GAIN = 0.005


def zscore_env(df, col):
    """col z-scored inside each environment over the rows that have a value (population SD).
    Missing values, and every row of an environment whose values are constant, get 0."""
    vals = pd.to_numeric(df[col], errors="coerce")
    grp = vals.groupby(df["Env"])
    mean = grp.transform("mean")
    sd = grp.transform(lambda s: s.std(ddof=0))
    z = (vals - mean) / sd
    z = z.where(sd > 0, 0.0)
    return z.fillna(0.0)


def mix(df, a, b, zf="zf", zm="zm", cat="cat"):
    """a * zf + (1 - a) * zm on new_one rows, b * zf + (1 - b) * zm on all others."""
    w = np.where(df[cat].to_numpy() == "new_one", a, b)
    return w * df[zf].to_numpy(dtype=float) + (1.0 - w) * df[zm].to_numpy(dtype=float)


def key(a, b):
    return "a%.2f_b%.2f" % (a, b)


def grid_scores(df):
    """{key(a, b): mean within-environment r} over GRID x GRID; df needs Env, obs, cat, zf, zm."""
    out = {}
    work = df[["Env", "obs"]].copy()
    for a in GRID:
        for b in GRID:
            work["mix"] = mix(df, a, b)
            out[key(a, b)] = rc.mean_r(work, "mix")[0]
    return out


def choose(scores):
    """Best (a, b) by score; ties go to the smaller a + b, then the smaller a (closer to M4)."""
    best = None
    for a in GRID:
        for b in GRID:
            s = scores.get(key(a, b))
            if s is None:
                continue
            rank = (s, -(a + b), -a)
            if best is None or rank > best[0]:
                best = (rank, a, b)
    return None if best is None else (best[1], best[2])


def category_scores(df, cols):
    """{category: {col: mean within-environment r, 'rows_observed': n}}."""
    res = {}
    for c in rc.CATEGORIES:
        sub = df[df["cat"] == c]
        res[c] = {col: rc.mean_r(sub, col)[0] for col in cols}
        res[c]["rows_observed"] = int(sub["obs"].notna().sum())
    return res


def grade(res):
    """Gate R1 and predictions Q1-Q5 of docs/g2f-switch-0.1.0-prereg.md.
    res[fold] = {'raw': {'M4': r, 'full': r}, 'grid': {key: r}}. Returns (grades, (a, b) or None)."""
    g = {}
    devs = {}
    ok = True
    for m in ("M4", "full"):
        for f in FOLDS:
            v = res.get(f, {}).get("raw", {}).get(m)
            d = None if v is None else round(abs(v - PUBLISHED[m][f]), 4)
            devs["%s_%s" % (m, f)] = {"published": PUBLISHED[m][f], "got": v, "abs_dev": d}
            ok = ok and d is not None and d <= REPRO_TOL[m]
    g["R1_reproduces_published"] = {"held": bool(ok), "value": devs}
    names = ("Q1_chosen_a_at_least_0.5", "Q2_chosen_b_at_most_0.5", "Q3_chosen_beats_both_2022_by_0.005",
             "Q4_chosen_beats_M4_2024", "Q5_chosen_below_full_2024")
    g2022 = res.get("2022", {}).get("grid", {})
    g2024 = res.get("2024", {}).get("grid", {})
    ch = choose(g2022)
    if ch is None:
        for n in names:
            g[n] = {"held": None, "value": None}
        return g, None
    a, b = ch
    k = key(a, b)
    s22, s24 = g2022.get(k), g2024.get(k)
    m22, f22 = g2022.get(key(0.0, 0.0)), g2022.get(key(1.0, 1.0))
    m24, f24 = g2024.get(key(0.0, 0.0)), g2024.get(key(1.0, 1.0))
    bar3 = None if m22 is None or f22 is None else round(max(m22, f22) + MIN_GAIN, 4)
    g[names[0]] = {"value": a, "held": a >= 0.5}
    g[names[1]] = {"value": b, "held": b <= 0.5}
    g[names[2]] = {"value": s22, "bar": bar3,
                   "held": None if s22 is None or bar3 is None else bool(s22 >= bar3)}
    g[names[3]] = {"value": s24, "bar": m24,
                   "held": None if s24 is None or m24 is None else bool(s24 > m24)}
    g[names[4]] = {"value": s24, "bar": f24,
                   "held": None if s24 is None or f24 is None else bool(s24 < f24)}
    return g, ch


def entry_default(grades, ch):
    """The pre-registered default for the 2026 entry: the 2022-chosen mix if it beat M4 on 2024 (Q4),
    otherwise M4 alone."""
    if ch is not None and grades.get("Q4_chosen_beats_M4_2024", {}).get("held") is True:
        return key(*ch)
    return "M4"


def apply_mix(df, train_hybrids, a, b):
    """Env, Hybrid, cat, mix for a table with Env, Hybrid, M4 and full columns."""
    df = df.copy()
    df["cat"] = rc.categorize(train_hybrids, df["Hybrid"])
    df["zm"] = zscore_env(df, "M4")
    df["zf"] = zscore_env(df, "full")
    df["mix"] = mix(df, a, b)
    return df[["Env", "Hybrid", "cat", "mix"]]


# ---------------------------------------------------------------- sealed run

def build_fold(fold, trait, template, observed, geno_names, Z, full_src):
    import g2f_baseline as gb
    import g2f_parentgca as pg
    if fold == "2024":
        train = trait
        test = template.merge(observed, on=["Env", "Hybrid"], how="left")
    else:
        train, test = gb.holdout(trait, int(fold))
    preds, info = pg.fit_predict(train, test, geno_names, Z)
    df = preds[["Env", "Hybrid", "obs", "M4"]].copy()
    full = rc.strip_keys(pd.read_csv(full_src)).drop_duplicates(subset=["Env", "Hybrid"])
    df = df.merge(full[["Env", "Hybrid", "full"]], on=["Env", "Hybrid"], how="left")
    df["cat"] = rc.categorize(train["Hybrid"].unique(), df["Hybrid"])
    fit = {k: info[k] for k in ("lambda", "gca_lambda", "train_rows", "test_rows") if k in info}
    fit["rows_without_full"] = int(df["full"].isna().sum())
    return df, fit


def evaluate(df):
    df = df.copy()
    df["zm"] = zscore_env(df, "M4")
    df["zf"] = zscore_env(df, "full")
    return df, {"grid": grid_scores(df),
                "raw": {"M4": rc.mean_r(df, "M4")[0], "full": rc.mean_r(df, "full")[0]}}


def cmd_grade(args):
    import g2f_baseline as gb
    dd = args.data_dir
    trait = gb.load_trait(gb.fetch(dd, "trait"))
    template = gb.load_pairs(gb.fetch(dd, "template"))
    observed = gb.load_pairs(gb.fetch(dd, "observed"), "obs")
    names = set(trait["Hybrid"]) | set(template["Hybrid"])
    geno_names, G = gb.read_numeric(gb.fetch(dd, "geno"), names)
    Z = gb.standardize(G)
    res, frames = {}, {}
    for fold in FOLDS:
        df, fit = build_fold(fold, trait, template, observed, geno_names, Z, rc.PRED_URLS[fold])
        df, r = evaluate(df)
        r["fit"] = fit
        r["rows_observed_by_category"] = {c: int(((df["cat"] == c) & df["obs"].notna()).sum())
                                          for c in rc.CATEGORIES}
        res[fold], frames[fold] = r, df
        print(fold, json.dumps(r["raw"]), json.dumps(r["rows_observed_by_category"]), flush=True)
    grades, ch = grade(res)
    out = {"version": VERSION, "study": "g2f-switch-0.1.0", "grid": list(GRID),
           "metric": "mean within-environment Pearson r (>= 3 rows)", "published": PUBLISHED,
           "folds": res, "grading": grades, "entry_default": entry_default(grades, ch)}
    g22, g24 = res["2022"]["grid"], res["2024"]["grid"]
    out["two_fold_mean"] = {k: round((g22[k] + g24[k]) / 2, 4) for k in g22
                            if g22.get(k) is not None and g24.get(k) is not None}
    best24 = choose(g24)
    out["best_2024_hindsight"] = None if best24 is None else {"a": best24[0], "b": best24[1],
                                                               "score": g24[key(*best24)]}
    if ch is not None:
        out["chosen"] = {"a": ch[0], "b": ch[1], "score_2022": g22[key(*ch)], "score_2024": g24[key(*ch)]}
        for fold, df in frames.items():
            df["chosen"] = mix(df, ch[0], ch[1])
            res[fold]["by_category"] = category_scores(df, ["M4", "full", "chosen"])
        out["chosen_env_r_2024"] = {e: round(v, 4) for e, v in rc.env_r(frames["2024"], "chosen").items()}
    os.makedirs(args.out_dir, exist_ok=True)
    with open(os.path.join(args.out_dir, "g2f_switch.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
    print(json.dumps({k: out.get(k) for k in ("grading", "chosen", "entry_default", "best_2024_hindsight")},
                     indent=1, sort_keys=True))
    return 0


def cmd_apply(args):
    pred = rc.strip_keys(pd.read_csv(args.pred))
    trait = rc.load_trait(args.trait)
    df = pred[["Env", "Hybrid", args.m4_col, args.full_col]].rename(
        columns={args.m4_col: "M4", args.full_col: "full"})
    out = apply_mix(df, trait["Hybrid"].unique(), args.a, args.b)
    out.to_csv(args.out, index=False)
    print("wrote", len(out), "rows to", args.out, "categories:",
          json.dumps({str(k): int(v) for k, v in out["cat"].value_counts().items()}, sort_keys=True))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("grade")
    g.add_argument("--data-dir", default="/data")
    g.add_argument("--out-dir", default="/out")
    p = sub.add_parser("apply")
    p.add_argument("--pred", required=True)
    p.add_argument("--trait", required=True)
    p.add_argument("--m4-col", default="M4")
    p.add_argument("--full-col", default="full")
    p.add_argument("--a", type=float, required=True)
    p.add_argument("--b", type=float, required=True)
    p.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    return cmd_grade(args) if args.cmd == "grade" else cmd_apply(args)


if __name__ == "__main__":
    raise SystemExit(main())
