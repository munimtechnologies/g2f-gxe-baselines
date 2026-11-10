# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
"""g2f_predict 0.1.0: release-day entry builder for the G2F maize GxE competition, for any release layout.

plan     the files found below --data-dir (g2f_entry.find_release, by role, in any sub-folder), the
         test season, the share of template pairs grown before, and how many template pairs fall in
         each hybrid category (seen, new_both, new_one, new_none). Fits nothing.
predict  M4 (g2f_parentgca 0.1.0) for every template pair. With --full (a table with Env, Hybrid and a
         'full' column, e.g. preds/<season>.csv from g2f_refmodel.R) also the g2f-switch mix
         a*z(full) + (1-a)*z(M4) on new_one rows and b*z(full) + (1-b)*z(M4) elsewhere, z inside each
         environment (default a = b = 0.5, the graded g2f-switch 0.1.0 entry default). Every model
         column becomes an upload file in Mg/ha (g2f_entry mgha: a positive affine map per environment,
         so within-environment r is unchanged), filled in the template's own row order and checked with
         g2f_entry validate. If the release also holds an observed-values file (a past season), every
         column and every file is scored. --expect grades checks P1-P5 of docs/g2f-predict-0.1.0.md.
Never downloads anything: all inputs come from --data-dir and --full; a missing file is an error.
Needs g2f_baseline.py, g2f_parentgca.py, g2f_refcheck.py, g2f_switch.py and g2f_entry.py from this
repository, numpy and pandas.
"""
import argparse
import json
import os

import numpy as np
import pandas as pd

import g2f_entry as ge
import g2f_refcheck as rc
import g2f_switch as sw

VERSION = "0.1.0"
NEEDED = ("trait", "template", "geno_numeric")
DEFAULT_A = 0.5
DEFAULT_B = 0.5


def release(data_dir):
    """{role: path} from g2f_entry.find_release. Raises FileNotFoundError if a needed role is missing;
    nothing is ever downloaded."""
    rel = ge.find_release(data_dir)
    missing = [r for r in NEEDED if r not in rel]
    if missing:
        raise FileNotFoundError("missing below %s: %s (g2f_predict never downloads)"
                                % (data_dir, ", ".join(missing)))
    return rel


def test_season(template_path, envs=()):
    """The template's season: the last year in its file name, else the most common Env year."""
    ys = ge.name_years(template_path)
    if ys:
        return ys[-1]
    years = [y for y in (ge.env_year(e) for e in envs) if y is not None]
    if not years:
        return None
    return max(sorted(set(years)), key=years.count)


def load(rel):
    """(trait, template pairs) as pandas frames, read with g2f_baseline's loaders."""
    import g2f_baseline as gb
    return gb.load_trait(rel["trait"]), gb.load_pairs(rel["template"])


def category_counts(train_hybrids, hybrids):
    cats = rc.categorize(train_hybrids, hybrids)
    return {c: int(sum(1 for x in cats if x == c)) for c in rc.CATEGORIES}


def fit_m4(trait, template, geno_path):
    """(Env, Hybrid, M4 frame, fit info): g2f_parentgca.fit_predict trained on every training row,
    exactly as g2f_switch builds its 2024 fold."""
    import g2f_baseline as gb
    import g2f_parentgca as pg
    names = set(trait["Hybrid"]) | set(template["Hybrid"])
    geno_names, G = gb.read_numeric(geno_path, names)
    Z = gb.standardize(G)
    out, info = pg.fit_predict(trait, template, geno_names, Z)
    keep = {k: info[k] for k in ("lambda", "gca_lambda", "train_rows", "test_rows",
                                 "share_rows_hybrid_seen", "share_rows_hybrid_genotyped") if k in info}
    return out[["Env", "Hybrid", "M4"]], keep


def plan(data_dir):
    rel = release(data_dir)
    trait, template = load(rel)
    seen = ge.seen_share(rel["trait"], rel["template"])
    return {"version": VERSION,
            "files": {r: os.path.relpath(p, data_dir).replace(os.sep, "/") for r, p in rel.items()},
            "test_season": test_season(rel["template"], template["Env"]),
            "training_years": [int(trait["Year"].min()), int(trait["Year"].max())],
            "training_rows": int(len(trait)),
            "template_pairs": int(len(template)), "template_envs": int(template["Env"].nunique()),
            "seen": seen, "decision": ge.decide(seen["share_in_last_year"]),
            "categories": category_counts(trait["Hybrid"].unique(), template["Hybrid"])}


def build(data_dir, out_dir, full_path=None, a=DEFAULT_A, b=DEFAULT_B, m4_fn=None,
          min_hybrids=ge.MIN_HYBRIDS):
    """Predictions table, one Mg/ha upload file per model column, and a summary dict."""
    os.makedirs(out_dir, exist_ok=True)
    rel = release(data_dir)
    trait, template = load(rel)
    season = test_season(rel["template"], template["Env"])
    tag = season if season is not None else "test"
    res = {"version": VERSION,
           "files": {r: os.path.relpath(p, data_dir).replace(os.sep, "/") for r, p in rel.items()},
           "test_season": season,
           "training_years": [int(trait["Year"].min()), int(trait["Year"].max())],
           "template_pairs": int(len(template)), "template_envs": int(template["Env"].nunique()),
           "categories": category_counts(trait["Hybrid"].unique(), template["Hybrid"])}
    m4, res["m4_fit"] = (m4_fn or fit_m4)(trait, template, rel["geno_numeric"])
    m4 = rc.strip_keys(m4.copy()).drop_duplicates(subset=["Env", "Hybrid"])
    df = template.merge(m4[["Env", "Hybrid", "M4"]], on=["Env", "Hybrid"], how="left")
    res["rows_without_M4"] = int(df["M4"].isna().sum())
    cols = ["M4"]
    if full_path:
        full = rc.strip_keys(pd.read_csv(full_path)).drop_duplicates(subset=["Env", "Hybrid"])
        df = df.merge(full[["Env", "Hybrid", "full"]], on=["Env", "Hybrid"], how="left")
        res["full"] = {"source": os.path.basename(full_path), "rows_without_full": int(df["full"].isna().sum())}
        mixed = sw.apply_mix(df, trait["Hybrid"].unique(), a, b)
        df["cat"] = mixed["cat"].to_numpy()
        df["mix"] = mixed["mix"].to_numpy()
        res["mix"] = {"a": a, "b": b, "name": sw.key(a, b)}
        cols += ["full", "mix"]
    else:
        df["cat"] = rc.categorize(trait["Hybrid"].unique(), df["Hybrid"])
    df.to_csv(os.path.join(out_dir, "predictions_%s.csv" % tag), index=False)

    subs = {}
    for col in cols:
        preds = {(e, h): float(v) for e, h, v in zip(df["Env"], df["Hybrid"], df[col]) if pd.notna(v)}
        mg, mplan, info = ge.mgha_predictions(rel["trait"], rel["template"], preds, min_hybrids=min_hybrids)
        path = os.path.join(out_dir, "submission_%s_%s.csv" % (tag, col))
        w = ge.write_submission(rel["template"], mg, path, fill="env_mean")
        v = ge.validate_submission(rel["template"], path)
        subs[col] = {"file": os.path.basename(path), "write": w,
                     "validate": {k: v[k] for k in ("ok", "errors", "warnings", "rows", "template_rows", "range")
                                  if k in v},
                     "spread_mgha": round(mplan["spread"], 4),
                     "spread_shrunk_envs": len(info["spread_shrunk_envs"]),
                     "envs_level_from_location": sum(1 for x in mplan["envs"].values() if x["source"] == "location")}
        if "observed" in rel:
            s = ge.score_submission(path, rel["observed"])
            subs[col]["score"] = {k: s[k] for k in ("mean_r", "envs", "pairs_scored")}
    res["submissions"] = subs
    if "observed" in rel:
        import g2f_baseline as gb
        obs = gb.load_pairs(rel["observed"], "obs")
        sc = df.merge(obs, on=["Env", "Hybrid"], how="left")
        res["scores_raw"] = {c: rc.mean_r(sc, c)[0] for c in cols}
        res["scores_by_category"] = {}
        for cat in rc.CATEGORIES:
            sub = sc[sc["cat"] == cat]
            res["scores_by_category"][cat] = {c: rc.mean_r(sub, c)[0] for c in cols}
            res["scores_by_category"][cat]["rows_observed"] = int(sub["obs"].notna().sum())
    return res


def grade_expect(res, expect):
    """Checks P1-P5 of docs/g2f-predict-0.1.0.md."""
    g = {}
    tol = expect.get("tol", 0.0005)
    roles = sorted(res.get("files", {}))
    need = expect.get("roles", list(NEEDED) + ["observed"])
    g["P1_release_and_season"] = {"value": {"roles": roles, "season": res.get("test_season")},
                                  "held": all(r in roles for r in need)
                                  and res.get("test_season") == expect.get("season")}
    raw = res.get("scores_raw", {})
    for item, col in (("P2_M4_reproduced", "M4"), ("P3_mix_reproduced", "mix")):
        v, want = raw.get(col), expect.get(col)
        g[item] = {"value": v, "expected": want,
                   "held": v is not None and want is not None and abs(v - want) <= tol}
    subs = res.get("submissions", {})
    ok4 = bool(subs) and all(s["validate"].get("ok") and s["validate"].get("rows") == s["validate"].get("template_rows")
                             for s in subs.values())
    ok4 = ok4 and all(subs[c]["write"]["filled_by_env_mean"] == 0 for c in ("M4", "mix") if c in subs)
    g["P4_files_validate"] = {"value": {c: {"ok": s["validate"].get("ok"), "rows": s["validate"].get("rows"),
                                            "filled": s["write"]["filled_by_env_mean"]} for c, s in subs.items()},
                              "held": bool(ok4)}
    diffs = {}
    for c in ("M4", "mix"):
        s = subs.get(c, {}).get("score", {})
        if s.get("mean_r") is not None and raw.get(c) is not None:
            diffs[c] = {"file": s["mean_r"], "raw": raw[c], "envs": s.get("envs")}
    ok5 = len(diffs) == 2 and all(abs(d["file"] - d["raw"]) <= expect.get("file_tol", 0.0002)
                                  and d["envs"] == expect.get("envs") for d in diffs.values())
    g["P5_mgha_keeps_score"] = {"value": diffs, "held": bool(ok5)}
    return g


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--data-dir", required=True)
    p.add_argument("--out-dir")
    q = sub.add_parser("predict")
    q.add_argument("--data-dir", required=True)
    q.add_argument("--out-dir", required=True)
    q.add_argument("--full")
    q.add_argument("--a", type=float, default=DEFAULT_A)
    q.add_argument("--b", type=float, default=DEFAULT_B)
    q.add_argument("--expect")
    q.add_argument("--name", default="g2f_predict")
    args = ap.parse_args(argv)
    if args.cmd == "plan":
        res = plan(args.data_dir)
        if args.out_dir:
            os.makedirs(args.out_dir, exist_ok=True)
            with open(os.path.join(args.out_dir, "g2f_predict_plan.json"), "w", encoding="utf-8") as fh:
                json.dump(res, fh, indent=1, sort_keys=True)
        print(json.dumps(res, indent=1, sort_keys=True))
        return 0
    res = build(args.data_dir, args.out_dir, args.full, args.a, args.b)
    if args.expect:
        with open(args.expect, encoding="utf-8") as fh:
            expect = json.load(fh)
        res["expect"] = expect
        res["grading"] = grade_expect(res, expect)
        res["held"] = sum(1 for v in res["grading"].values() if v["held"])
        res["total"] = len(res["grading"])
    with open(os.path.join(args.out_dir, args.name + ".json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, sort_keys=True, default=lambda o: o.item() if isinstance(o, np.generic) else str(o))
    print(json.dumps({k: res.get(k) for k in ("test_season", "categories", "scores_raw", "grading", "held", "total")},
                     indent=1, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
