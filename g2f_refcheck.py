# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
"""g2f_refcheck 0.1.1: the two checks of docs/g2f-refmodel-0.1.1-prereg.md.

split  splits MV2's re-implementation of the organisers' reference model (g2f-refmodel 0.1.0 predictions)
       by hybrid category (seen; new with 2, 1 or 0 parents seen in training) on the 2022, 2023 and 2024
       folds, and grades gate S1 and predictions P7-P9.
r0     scores the prediction file of the organisers' script (written by run_ref.R) on the released 2024
       answers, and grades gates G1, G2 and prediction P10.
Metric everywhere: mean over environments of the Pearson r inside each environment (at least 3 observed
rows; a constant prediction scores 0), as in every study in this repository. numpy and pandas only.
"""
import argparse
import hashlib
import json
import os

import numpy as np
import pandas as pd

VERSION = "0.1.1"
RAW = "https://raw.githubusercontent.com/munimtechnologies/g2f-gxe-baselines/main/"
PRED_URLS = {f: RAW + "results/g2f_refmodel_%s_predictions.csv" % f for f in ("2024", "2023", "2022")}
M4_URL = RAW + "results/g2f_parentgca_2024_predictions.csv"
FILES = {"trait": "1_Training_Trait_Data_2014_2023.csv",
         "template": "1_Submission_Template_2024.csv",
         "observed": "7_Testing_Observed_Values.csv"}
FOLDS = ("2024", "2023", "2022")
VARIANTS = ("full", "b2", "allloc")
CATEGORIES = ("seen", "new_both", "new_one", "new_none")
MIN_ROWS = 3
REFERENCE_LEADERBOARD = 0.4376582214813316
FULL_2024 = 0.4416          # g2f-refmodel 0.1.0, variant full on the 2024 answers
# g2f-newshrink 0.1.0 (results/g2f_newshrink.json): observed-row counts and M4's r per category
NEWSHRINK_ROWS = {"2022": {"seen": 816, "new_one": 9126, "new_both": 1896},
                  "2024": {"seen": 1172, "new_one": 7676, "new_both": 638}}
M4_SPLIT = {"2022": {"new_one": 0.1435, "new_both": 0.4301},
            "2024": {"new_one": 0.1073, "new_both": 0.1230}}
# Public 2024 leaderboard (EvalAI challenge 2376, phase split 5893, read 2026-11-08), best Mean_r per entry.
LEADERBOARD_2024 = (
    0.450054, 0.444016, 0.437658, 0.437658, 0.437097, 0.426054, 0.425742, 0.414302,
    0.414063, 0.412884, 0.405235, 0.403289, 0.393626, 0.385322, 0.382543, 0.379316,
    0.371653, 0.371444, 0.370229, 0.367559, 0.367501, 0.367162, 0.365618, 0.358477,
    0.352806, 0.351555, 0.349462, 0.349414, 0.346075, 0.344262, 0.344002, 0.343741,
    0.341293, 0.328706, 0.321922, 0.321481, 0.316296, 0.311257, 0.307070, 0.301745,
    0.298699, 0.292001, 0.291312, 0.287832, 0.285541, 0.277010, 0.274781, 0.267951,
    0.255806, 0.245274, 0.195234, 0.164707, 0.160126, 0.159352, 0.156285, 0.148111,
    0.137599, 0.113092, 0.071899, 0.047834, 0.017298, 0.016730, 0.001232, -0.024543)


# ---------------------------------------------------------------- scoring

def _pearson(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if a.std() == 0 or b.std() == 0:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def env_r(df, col, obs="obs"):
    """{env: Pearson r of col with obs} inside each environment. Environments with fewer than MIN_ROWS
    rows having both values, or constant observations, are skipped; a constant prediction scores 0."""
    res = {}
    if col not in df.columns or obs not in df.columns:
        return res
    for env, grp in df.groupby("Env"):
        grp = grp.dropna(subset=[obs, col])
        if len(grp) < MIN_ROWS or grp[obs].std() == 0:
            continue
        res[env] = _pearson(grp[obs], grp[col])
    return res


def mean_r(df, col, obs="obs"):
    """(mean within-environment r rounded to 4 decimals, or None; number of environments scored)."""
    rs = env_r(df, col, obs)
    return (round(float(np.mean(list(rs.values()))), 4) if rs else None), len(rs)


def agreement(df, a, b):
    """Mean over environments of the Pearson r between two prediction columns (rows with both values,
    at least MIN_ROWS per environment; a constant column scores 0). Returns (mean or None, envs)."""
    rs = []
    for _, grp in df.groupby("Env"):
        grp = grp.dropna(subset=[a, b])
        if len(grp) < MIN_ROWS:
            continue
        rs.append(_pearson(grp[a], grp[b]))
    return (round(float(np.mean(rs)), 4) if rs else None), len(rs)


def place(score, board=LEADERBOARD_2024):
    """Leaderboard place a score would take: 1 + the number of entries scoring strictly higher."""
    if score is None:
        return None
    return 1 + sum(1 for s in board if s > score)


# ---------------------------------------------------------------- data

def strip_keys(df):
    df["Env"] = df["Env"].astype(str).str.strip()
    df["Hybrid"] = df["Hybrid"].astype(str).str.strip()
    return df


def read_pairs(path, value_name=None):
    """Env, Hybrid (and the yield column, averaged per pair, renamed to value_name)."""
    df = strip_keys(pd.read_csv(path))
    if value_name is None:
        return df[["Env", "Hybrid"]].drop_duplicates().reset_index(drop=True)
    col = "Yield_Mg_ha" if "Yield_Mg_ha" in df.columns else \
        [c for c in df.columns if c not in ("Env", "Hybrid")][0]
    df[value_name] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=[value_name])
    return df.groupby(["Env", "Hybrid"], as_index=False)[value_name].mean()


def load_trait(path):
    df = strip_keys(pd.read_csv(path, low_memory=False))
    if "Year" in df.columns:
        df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    else:
        df["Year"] = pd.to_numeric(df["Env"].str.rsplit("_", n=1).str[-1], errors="coerce")
    df["Yield_Mg_ha"] = pd.to_numeric(df["Yield_Mg_ha"], errors="coerce")
    df = df.dropna(subset=["Yield_Mg_ha", "Year"])
    df["Year"] = df["Year"].astype(int)
    return df[["Env", "Year", "Hybrid", "Yield_Mg_ha"]]


def fold_base(trait, fold, template=None, observed=None):
    """Rows to score for a fold: (Env, Hybrid, obs). 2024 = template joined to the released answers."""
    if fold == "2024":
        return template.merge(observed, on=["Env", "Hybrid"], how="left")
    t = trait[trait["Year"] == int(fold)]
    return t.groupby(["Env", "Hybrid"], as_index=False)["Yield_Mg_ha"].mean() \
        .rename(columns={"Yield_Mg_ha": "obs"})


# ---------------------------------------------------------------- categories

def parents(hybrid):
    """The parent names on either side of '/' in a hybrid name (empty parts dropped)."""
    return tuple(p.strip() for p in str(hybrid).split("/") if p.strip())


def categorize(train_hybrids, hybrids):
    """Category of each hybrid: 'seen' if it is among the training hybrids, otherwise 'new_both',
    'new_one' or 'new_none' by how many of its parents are parents of some training hybrid."""
    seen = set(train_hybrids)
    pool = {p for h in seen for p in parents(h)}
    out = []
    for h in hybrids:
        if h in seen:
            out.append("seen")
            continue
        k = sum(1 for p in parents(h) if p in pool)
        out.append("new_both" if k >= 2 else ("new_one" if k == 1 else "new_none"))
    return out


def level_gap(df, col):
    """Mean over environments of (mean z of new rows - mean z of seen rows) for col, z-scored inside
    each environment over rows with an observation; environments need >= 3 seen and >= 3 new rows."""
    gaps = []
    for _, grp in df.dropna(subset=["obs", col]).groupby("Env"):
        is_new = grp["cat"] != "seen"
        if is_new.sum() < MIN_ROWS or (~is_new).sum() < MIN_ROWS:
            continue
        sd = grp[col].std(ddof=0)
        if sd == 0:
            gaps.append(0.0)
            continue
        z = (grp[col] - grp[col].mean()) / sd
        gaps.append(float(z[is_new].mean() - z[~is_new].mean()))
    return (round(float(np.mean(gaps)), 4) if gaps else None), len(gaps)


def split_fold(base, preds, train_hybrids):
    """Scores per category for one fold. base: Env, Hybrid, obs; preds: Env, Hybrid + VARIANTS."""
    p = preds.drop_duplicates(subset=["Env", "Hybrid"])
    cols = [v for v in VARIANTS if v in p.columns]
    df = base.merge(p[["Env", "Hybrid"] + cols], on=["Env", "Hybrid"], how="left")
    df["cat"] = categorize(train_hybrids, df["Hybrid"])
    res = {"rows_observed": {}, "score": {}, "envs": {}}
    observed = df["obs"].notna()
    for c in CATEGORIES + ("new_all", "all"):
        if c == "all":
            sub = df
        elif c == "new_all":
            sub = df[df["cat"] != "seen"]
        else:
            sub = df[df["cat"] == c]
        res["rows_observed"][c] = int(sub["obs"].notna().sum())
        for v in cols:
            r, n = mean_r(sub, v)
            res["score"].setdefault(c, {})[v] = r
            res["envs"].setdefault(c, {})[v] = n
    res["level_gap"] = {"obs": level_gap(df[observed], "obs")[0]}
    for v in cols:
        res["level_gap"][v] = level_gap(df[observed], v)[0]
    return res


def grade_split(results):
    """Gate S1 and predictions P7-P9 of docs/g2f-refmodel-0.1.1-prereg.md."""
    g = {}
    devs = {}
    ok = True
    for fold, exp in NEWSHRINK_ROWS.items():
        got = results.get(fold, {}).get("rows_observed", {})
        for c, n in exp.items():
            m = got.get(c)
            d = None if m is None else round(abs(m - n) / n, 4)
            devs["%s_%s" % (fold, c)] = {"expected": n, "got": m, "rel_dev": d}
            ok = ok and d is not None and d <= 0.02
    g["S1_categories_match_newshrink"] = {"held": ok, "value": devs}

    def full(fold, cat):
        return results.get(fold, {}).get("score", {}).get(cat, {}).get("full")

    v7, v8, v9 = full("2022", "new_one"), full("2022", "new_both"), full("2024", "new_one")
    g["P7_full_beats_M4_2022_new_one"] = {"value": v7, "bar": M4_SPLIT["2022"]["new_one"],
                                          "held": v7 is not None and v7 > M4_SPLIT["2022"]["new_one"]}
    g["P8_full_below_M4_2022_new_both"] = {"value": v8, "bar": M4_SPLIT["2022"]["new_both"],
                                           "held": v8 is not None and v8 < M4_SPLIT["2022"]["new_both"]}
    g["P9_full_2024_new_one_at_least_0.30"] = {"value": v9, "bar": 0.30,
                                               "held": v9 is not None and v9 >= 0.30}
    return g


def grade_r0(r0, agree, full=FULL_2024):
    """Gates G1, G2 and prediction P10. Any missing input gives held = None ('not run')."""
    def gate(value, test):
        return {"value": value, "held": None if value is None else bool(test(value))}
    d1 = None if r0 is None else round(abs(r0 - REFERENCE_LEADERBOARD), 4)
    d2 = None if r0 is None else round(abs(full - r0), 4)
    return {"G1_harness_matches_leaderboard": gate(d1, lambda v: v <= 0.01),
            "G2_reimplementation_matches_reference": gate(d2, lambda v: v <= 0.005),
            "P10_reference_and_full_agree_0.99": gate(agree, lambda v: v >= 0.99)}


# ---------------------------------------------------------------- commands

def cmd_split(args):
    dd = args.data_dir
    trait = load_trait(os.path.join(dd, FILES["trait"]))
    template = read_pairs(os.path.join(dd, FILES["template"]))
    observed = read_pairs(os.path.join(dd, FILES["observed"]), "obs")
    results = {}
    for fold in FOLDS:
        src = os.path.join(args.pred_dir, "g2f_refmodel_%s_predictions.csv" % fold) if args.pred_dir \
            else PRED_URLS[fold]
        preds = strip_keys(pd.read_csv(src))
        train = trait[trait["Year"] < int(fold)]
        base = fold_base(trait, fold, template, observed)
        results[fold] = split_fold(base, preds, train["Hybrid"].unique())
        print(fold, json.dumps(results[fold]["rows_observed"]), json.dumps(results[fold]["score"]),
              flush=True)
    out = {"version": VERSION, "study": "g2f-refmodel-0.1.1 split", "metric":
           "mean within-environment Pearson r (>= 3 rows)", "m4_published": M4_SPLIT,
           "newshrink_rows": NEWSHRINK_ROWS, "folds": results, "grading": grade_split(results)}
    os.makedirs(args.out_dir, exist_ok=True)
    with open(os.path.join(args.out_dir, "g2f_refsplit.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
    print(json.dumps(out["grading"], indent=1, sort_keys=True))
    return 0


def sha256(path):
    if not path or not os.path.exists(path):
        return None
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def cmd_r0(args):
    dd = args.data_dir
    template = read_pairs(os.path.join(dd, FILES["template"]))
    observed = read_pairs(os.path.join(dd, FILES["observed"]), "obs")
    df = template.merge(observed, on=["Env", "Hybrid"], how="left")
    out = {"version": VERSION, "study": "g2f-refmodel-0.1.1 r0",
           "reference_script_sha256": sha256(args.ref_script),
           "reference_ran": os.path.exists(args.ref_pred)}
    r0 = agree = None
    if out["reference_ran"]:
        ref = read_pairs(args.ref_pred, "ref")
        df = df.merge(ref, on=["Env", "Hybrid"], how="left")
        out["ref_template_rows_without_prediction"] = int(df["ref"].isna().sum())
        full = strip_keys(pd.read_csv(args.full_pred)).drop_duplicates(subset=["Env", "Hybrid"])
        df = df.merge(full[["Env", "Hybrid", "full"]], on=["Env", "Hybrid"], how="left")
        m4 = strip_keys(pd.read_csv(args.m4_pred)).drop_duplicates(subset=["Env", "Hybrid"])
        df = df.merge(m4[["Env", "Hybrid", "seen"]], on=["Env", "Hybrid"], how="left")
        seen = df["seen"].map(lambda v: str(v).strip().lower() == "true")
        r0, n = mean_r(df, "ref")
        agree, n_agree = agreement(df, "ref", "full")
        out["score"] = {"ref": r0, "ref_seen": mean_r(df[seen], "ref")[0],
                        "ref_new": mean_r(df[~seen], "ref")[0], "full": mean_r(df, "full")[0]}
        out["envs_scored"] = n
        out["agreement_ref_full"] = {"mean_r": agree, "envs": n_agree}
        out["leaderboard_place"] = place(r0)
        out["env_r"] = {k: round(v, 4) for k, v in env_r(df, "ref").items()}
    out["grading"] = grade_r0(r0, agree)
    os.makedirs(args.out_dir, exist_ok=True)
    with open(os.path.join(args.out_dir, "g2f_refr0.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
    print(json.dumps({k: out.get(k) for k in ("reference_ran", "score", "agreement_ref_full",
                                               "leaderboard_place", "grading")}, indent=1, sort_keys=True))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("split")
    s.add_argument("--data-dir", default="/data")
    s.add_argument("--out-dir", default="/out")
    s.add_argument("--pred-dir", default=None, help="local folder of the 0.1.0 prediction files "
                   "(default: read them from this repository on GitHub)")
    r = sub.add_parser("r0")
    r.add_argument("--data-dir", default="/data")
    r.add_argument("--out-dir", default="/out")
    r.add_argument("--ref-pred", default="/out/ref_2024_predictions.csv")
    r.add_argument("--ref-script", default="/work/ref/script_model.R")
    r.add_argument("--full-pred", default=PRED_URLS["2024"])
    r.add_argument("--m4-pred", default=M4_URL)
    args = ap.parse_args(argv)
    return cmd_split(args) if args.cmd == "split" else cmd_r0(args)


if __name__ == "__main__":
    raise SystemExit(main())
