# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
"""g2f_refmodel 0.1.0: scores the G2F organisers' public reference model and MV2's re-implementation.

Reads the prediction tables written by run_ref.R (the unmodified reference script, 2024 only) and
g2f_refmodel.R (variants full, b1, b2, allloc on the 2024, 2023 and 2022 folds), the public 2024 answers,
the training trait file, and MV2's adopted M4 predictions for 2024 committed in this repository. Scores
everything by the competition metric (mean within-environment Pearson r; environments with at least 3
observed rows; a constant prediction scores 0, exactly as g2f_baseline), places each 2024 score on the
public 2024 leaderboard, and grades docs/g2f-refmodel-0.1.0-prereg.md. numpy and pandas only.
"""
import argparse
import hashlib
import json
import os
import urllib.request

import numpy as np
import pandas as pd

M4_URL = ("https://raw.githubusercontent.com/munimtechnologies/g2f-gxe-baselines/main/results/"
          "g2f_parentgca_2024_predictions.csv")
REF_URL = ("https://raw.githubusercontent.com/alenxav/Lectures/master/G2F_GxE_2024/script_model.R")
# Public 2024 leaderboard (EvalAI challenge 2376, phase split 5893, read 2026-11-08): the best Mean_r of
# each of its 64 entries, rounded to 6 decimals, in leaderboard order. Places 3 and 4 are the two
# "not competing" entries.
LEADERBOARD_2024 = (
    0.450054, 0.444016, 0.437658, 0.437658, 0.437097, 0.426054, 0.425742, 0.414302,
    0.414063, 0.412884, 0.405235, 0.403289, 0.393626, 0.385322, 0.382543, 0.379316,
    0.371653, 0.371444, 0.370229, 0.367559, 0.367501, 0.367162, 0.365618, 0.358477,
    0.352806, 0.351555, 0.349462, 0.349414, 0.346075, 0.344262, 0.344002, 0.343741,
    0.341293, 0.328706, 0.321922, 0.321481, 0.316296, 0.311257, 0.307070, 0.301745,
    0.298699, 0.292001, 0.291312, 0.287832, 0.285541, 0.277010, 0.274781, 0.267951,
    0.255806, 0.245274, 0.195234, 0.164707, 0.160126, 0.159352, 0.156285, 0.148111,
    0.137599, 0.113092, 0.071899, 0.047834, 0.017298, 0.016730, 0.001232, -0.024543)
REFERENCE_LEADERBOARD = 0.4376582214813316   # "Model 2022 (not competing)", unrounded
M4_SCORES = {"2022": 0.3262, "2023": 0.4354, "2024": 0.3018}
MIN_ROWS = 3
VARIANTS = ("full", "b1", "b2", "allloc")
FOLDS = ("2024", "2023", "2022")
FILES = {"trait": "1_Training_Trait_Data_2014_2023.csv",
         "template": "1_Submission_Template_2024.csv",
         "observed": "7_Testing_Observed_Values.csv"}


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


def mean_r(df, col):
    """(mean within-environment r rounded to 4 decimals or None, number of environments scored)."""
    if col not in df.columns:
        return None, 0
    rs = env_r(df, col)
    return (round(float(np.mean(list(rs.values()))), 4) if rs else None), len(rs)


def place(score, board=LEADERBOARD_2024):
    """Leaderboard place a score would take: 1 + the number of entries scoring strictly higher."""
    if score is None:
        return None
    return 1 + sum(1 for s in board if s > score)


def zwithin(df, col):
    """Within-environment z-score of a column (population SD); a constant environment gives 0."""
    g = df.groupby("Env")[col]
    mu = g.transform("mean")
    sd = g.transform(lambda s: s.std(ddof=0))
    return ((df[col] - mu) / sd.replace(0, np.nan)).fillna(0.0)


def blend(df, a, b, w=0.5):
    return w * zwithin(df, a) + (1.0 - w) * zwithin(df, b)


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


def fold_obs(trait, year):
    t = trait[trait["Year"] == int(year)]
    out = t.groupby(["Env", "Hybrid"], as_index=False)["Yield_Mg_ha"].mean()
    return out.rename(columns={"Yield_Mg_ha": "obs"})


def read_info(path):
    if not os.path.exists(path):
        return {}
    df = pd.read_csv(path, dtype=str)
    return dict(zip(df["key"], df["value"]))


def _d(a, b):
    return None if a is None or b is None else round(a - b, 4)


def grade(s):
    """Gates G1-G2, predictions P1-P6 and hypothesis H1 of docs/g2f-refmodel-0.1.0-prereg.md.
    s = {"2024": {"ref": r, "full": r, "b1": r, "b2": r, "allloc": r, "blend": r, "full_new": r},
         "2023": {"full": r, ...}, "2022": {"full": r, ...}}; missing scores are None or absent."""
    y24, y23, y22 = s.get("2024", {}), s.get("2023", {}), s.get("2022", {})
    ref, full = y24.get("ref"), y24.get("full")
    best = ref if ref is not None else full
    g = {}
    d_ref = None if ref is None else round(abs(ref - REFERENCE_LEADERBOARD), 4)
    g["G1_harness_matches_leaderboard"] = {"value": d_ref, "held": d_ref is not None and d_ref <= 0.01}
    d_imp = None if (ref is None or full is None) else round(abs(full - ref), 4)
    g["G2_reimplementation_matches_reference"] = {"value": d_imp,
                                                  "held": d_imp is not None and d_imp <= 0.005}
    d1 = _d(best, M4_SCORES["2024"])
    g["P1_reference_beats_M4_2024_by_0.10"] = {"value": d1, "held": d1 is not None and d1 >= 0.10}
    f22, f23 = y22.get("full"), y23.get("full")
    g["P2_full_beats_M4_2022_and_2023"] = {
        "value": [_d(f22, M4_SCORES["2022"]), _d(f23, M4_SCORES["2023"])],
        "held": f22 is not None and f23 is not None and f22 > M4_SCORES["2022"] and f23 > M4_SCORES["2023"]}
    d3 = _d(y24.get("b2"), y24.get("b1"))
    g["P3_state_effects_at_least_global_2024"] = {"value": d3, "held": d3 is not None and d3 >= 0}
    d4 = _d(full, y24.get("allloc"))
    g["P4_test_state_filter_helps_2024"] = {"value": d4, "held": d4 is not None and d4 >= 0.005}
    d5 = _d(y24.get("blend"), full)
    g["P5_blend_with_M4_below_full_2024"] = {"value": d5, "held": d5 is not None and d5 < 0}
    fn = y24.get("full_new")
    g["P6_full_new_hybrids_at_least_0.25"] = {"value": fn, "held": fn is not None and fn >= 0.25}
    m_full = None if (f22 is None or f23 is None) else round((f22 + f23) / 2, 4)
    m_m4 = round((M4_SCORES["2022"] + M4_SCORES["2023"]) / 2, 4)
    g["H1_switch_entry_baseline"] = {
        "value": {"gain_2024": d1, "full_mean_2022_2023": m_full, "m4_mean_2022_2023": m_m4},
        "held": d1 is not None and d1 >= 0.05 and m_full is not None and m_full > m_m4}
    return g


def sha256(path):
    if not path or not os.path.exists(path):
        return None
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data-dir", default="/data")
    ap.add_argument("--out-dir", default="/out")
    ap.add_argument("--ref-script", default="/work/ref/script_model.R")
    args = ap.parse_args()
    pred_dir = os.path.join(args.out_dir, "preds")
    dd = args.data_dir

    trait = load_trait(os.path.join(dd, FILES["trait"]))
    template = read_pairs(os.path.join(dd, FILES["template"]))
    observed = read_pairs(os.path.join(dd, FILES["observed"]), "obs")
    m4 = strip_keys(pd.read_csv(M4_URL))[["Env", "Hybrid", "M4", "seen"]]
    m4 = m4.drop_duplicates(subset=["Env", "Hybrid"])

    results = {"version": "0.1.0", "metric": "mean within-environment Pearson r (>= 3 rows)",
               "reference_script": {"url": REF_URL, "sha256": sha256(args.ref_script)},
               "m4_reference_scores": M4_SCORES, "leaderboard_reference": REFERENCE_LEADERBOARD,
               "folds": {}}
    scores = {}
    per_env = {}
    for fold in FOLDS:
        if fold == "2024":
            base = template.merge(observed, on=["Env", "Hybrid"], how="left")
        else:
            base = fold_obs(trait, fold)
        path = os.path.join(pred_dir, fold + ".csv")
        fr = {"info": read_info(os.path.join(pred_dir, fold + "_info.csv")),
              "predictions_found": os.path.exists(path)}
        df = base.copy()
        if os.path.exists(path):
            p = strip_keys(pd.read_csv(path)).drop_duplicates(subset=["Env", "Hybrid"])
            df = df.merge(p[["Env", "Hybrid"] + [v for v in VARIANTS if v in p.columns]],
                          on=["Env", "Hybrid"], how="left")
        cols = [v for v in VARIANTS if v in df.columns]
        if fold == "2024":
            ref_path = os.path.join(args.out_dir, "ref_2024_predictions.csv")
            fr["reference_ran"] = os.path.exists(ref_path)
            if os.path.exists(ref_path):
                df = df.merge(read_pairs(ref_path, "ref"), on=["Env", "Hybrid"], how="left")
                fr["ref_rows_without_prediction"] = int(df["ref"].isna().sum())
                cols = ["ref"] + cols
            df = df.merge(m4, on=["Env", "Hybrid"], how="left")
            cols.append("M4")
            if "full" in df.columns and df["full"].notna().any():
                ok = df["full"].notna() & df["M4"].notna()
                df.loc[ok, "blend"] = blend(df[ok], "full", "M4").to_numpy()
                cols.append("blend")
        sc = {}
        for c in cols:
            sc[c], n_env = mean_r(df, c)
            fr.setdefault("envs_scored", {})[c] = n_env
        if fold == "2024":
            seen = df["seen"].map(lambda v: str(v).strip().lower() == "true")
            fr["rows_seen"] = int(seen.sum())
            fr["rows_new"] = int((~seen).sum())
            for c in ("ref", "full", "b1", "b2", "M4"):
                if c in df.columns:
                    sc[c + "_new"] = mean_r(df[~seen], c)[0]
                    sc[c + "_seen"] = mean_r(df[seen], c)[0]
            fr["leaderboard_place"] = {c: place(sc.get(c)) for c in cols}
            per_env = {c: env_r(df, c) for c in cols}
            keep = ["Env", "Hybrid"] + [c for c in ("full", "b1", "b2", "allloc", "blend") if c in df.columns]
            df[keep].round(5).to_csv(os.path.join(args.out_dir, "g2f_refmodel_2024_predictions.csv"),
                                     index=False)
        fr["score"] = sc
        scores[fold] = sc
        results["folds"][fold] = fr
        print(fold, json.dumps(sc, sort_keys=True), flush=True)

    results["grading"] = grade(scores)
    if per_env:
        pe = pd.DataFrame(per_env)
        pe.index.name = "Env"
        pe.round(4).to_csv(os.path.join(args.out_dir, "g2f_refmodel_2024_env_r.csv"))
    with open(os.path.join(args.out_dir, "g2f_refmodel.json"), "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=1, sort_keys=True)
    print(json.dumps({"grading": results["grading"],
                      "places_2024": results["folds"]["2024"].get("leaderboard_place")},
                     indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
