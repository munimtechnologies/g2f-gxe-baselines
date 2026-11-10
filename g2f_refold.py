# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
"""g2f_refold 0.1.0: re-chooses the g2f-switch mix weights for any release, on the hold-out seasons that
look most like the test season.

g2f-switch 0.1.0 chose its weights (a for new hybrids with one parent seen, b for every other row) on
the 2022 season and checked them on 2024, with 2022 and 2024 written into the code. On a later release
the same idea needs other seasons. `choose`:

1. finds the release files by role (g2f_predict.release; never downloads) and the test season;
2. calls the test season "new_hybrids" or "repeated_hybrids" from the share of template pairs whose
   hybrid was grown in the last training season (g2f_entry.decide, threshold 0.70);
3. holds out each of the --folds most recent training seasons in turn (default 2, the folds that
   `g2f_refmodel.R ... all` writes) and types each the same way, against the season before it;
4. for every hold-out season with kernel-model ("full") predictions, rebuilds M4 (g2f_parentgca 0.1.0)
   trained on earlier seasons only, z-scores both models inside each environment and scores the 5 x 5
   (a, b) grid (g2f_switch.grid_scores);
5. chooses (a, b) on the mean grid over the hold-out seasons of the same type as the test season (ties
   go to the smaller a + b, then the smaller a, as g2f_switch.choose). If none has the same type, the
   most recent hold-out season with full predictions is used and `matched` is false.

The chosen (a, b) is what `g2f_predict.py predict --a --b` then uses for the upload.
--expect grades checks D1-D6 of docs/g2f-refold-0.1.0.md.
Needs g2f_baseline.py, g2f_parentgca.py, g2f_refcheck.py, g2f_switch.py, g2f_entry.py and
g2f_predict.py from this repository, numpy and pandas.
"""
import argparse
import json
import os

import numpy as np
import pandas as pd

import g2f_entry as ge
import g2f_predict as gp
import g2f_refcheck as rc
import g2f_switch as sw

VERSION = "0.1.0"
N_FOLDS = 2
FIT_KEYS = ("lambda", "gca_lambda", "train_rows", "test_rows")


def describe(trait, pairs, last, label):
    """Type of a season: share of its distinct (Env, Hybrid) pairs whose hybrid has a trait row in
    season `last`, and g2f_entry.decide's setting for that share."""
    pairs = pairs[["Env", "Hybrid"]].drop_duplicates()
    n = int(len(pairs))
    grown = set(trait.loc[trait["Year"] == last, "Hybrid"]) if last is not None else set()
    k = int(pairs["Hybrid"].isin(grown).sum())
    share = round(k / n, 4) if n else None
    return {"season": label, "pairs": n, "last_training_year": last,
            "pairs_hybrid_in_last_year": k, "share_in_last_year": share,
            "setting": ge.decide(share)["setting"]}


def test_info(trait, template, season):
    return describe(trait, template, int(trait["Year"].max()), season)


def fold_info(trait, year):
    before = trait[trait["Year"] < year]
    last = int(before["Year"].max()) if len(before) else None
    return describe(trait, trait[trait["Year"] == year], last, int(year))


def candidate_years(trait, n=N_FOLDS):
    """The n most recent training seasons, newest first (never the earliest season, which has no
    earlier data to train on)."""
    ys = sorted({int(y) for y in trait["Year"]}, reverse=True)
    return ys[:max(0, min(n, len(ys) - 1))]


def pick_folds(test, folds, have=None):
    """(seasons to choose on, matched). folds are newest first; have = seasons with full predictions."""
    usable = [f for f in folds if have is None or f["season"] in have]
    matched = [f["season"] for f in usable
               if f["setting"] == test.get("setting") and f["setting"] != "unknown"]
    if matched:
        return matched, True
    return ([usable[0]["season"]] if usable else []), False


def mean_grid(grids):
    """{key: mean of the grids' scores}, only for keys scored in every grid; rounded to 4 decimals."""
    if not grids:
        return {}
    out = {}
    for k in grids[0]:
        vals = [g.get(k) for g in grids]
        if all(v is not None for v in vals):
            out[k] = round(float(np.mean(vals)), 4)
    return out


def entry_rule(grid):
    ch = sw.choose(grid) if grid else None
    if ch is None:
        return {"name": sw.key(0.0, 0.0), "a": 0.0, "b": 0.0, "score": None,
                "why": "no hold-out season with full predictions to choose on; M4 alone"}
    a, b = ch
    return {"name": sw.key(a, b), "a": a, "b": b, "score": grid[sw.key(a, b)]}


def real_m4(trait, template, geno_path):
    """M4 fitter for hold-out folds, with genotypes read exactly as g2f_switch and g2f_predict do."""
    import g2f_baseline as gb
    import g2f_parentgca as pg
    names = set(trait["Hybrid"]) | set(template["Hybrid"])
    geno_names, G = gb.read_numeric(geno_path, names)
    Z = gb.standardize(G)
    return lambda train, test: pg.fit_predict(train, test, geno_names, Z)


def fold_frame(trait, year, full, m4_fn):
    """Env, Hybrid, obs, M4, full, cat for one hold-out season, and fit info."""
    import g2f_baseline as gb
    train, test = gb.holdout(trait, year)
    preds, info = m4_fn(train, test)
    df = rc.strip_keys(preds[["Env", "Hybrid", "obs", "M4"]].copy())
    df = df.merge(full[["Env", "Hybrid", "full"]], on=["Env", "Hybrid"], how="left")
    df["cat"] = rc.categorize(train["Hybrid"].unique(), df["Hybrid"])
    fit = {k: info[k] for k in FIT_KEYS if k in info}
    fit["rows_without_full"] = int(df["full"].isna().sum())
    return df, fit


def evaluate_fold(df):
    df, r = sw.evaluate(df)
    r["rows_observed_by_category"] = {c: int(((df["cat"] == c) & df["obs"].notna()).sum())
                                      for c in rc.CATEGORIES}
    ch = sw.choose(r["grid"])
    if ch is None:
        r["chosen"] = None
        return r
    r["chosen"] = {"a": ch[0], "b": ch[1], "score": r["grid"][sw.key(*ch)]}
    df["chosen"] = sw.mix(df, ch[0], ch[1])
    r["by_category"] = sw.category_scores(df, ["M4", "full", "chosen"])
    return r


def full_sources(years, full_dir=None, full_paths=None):
    """{season: path}: <full_dir>/<season>.csv where present (g2f_refmodel.R's preds/ folder), then any
    explicit season=path pairs."""
    paths = {}
    for y in years:
        p = os.path.join(full_dir, "%d.csv" % y) if full_dir else None
        if p and os.path.exists(p):
            paths[y] = p
    for y, p in (full_paths or {}).items():
        paths[int(y)] = p
    return paths


def run(data_dir, full_paths=None, full_dir=None, n_folds=N_FOLDS, m4_fn=None):
    rel = gp.release(data_dir)
    trait, template = gp.load(rel)
    season = gp.test_season(rel["template"], template["Env"])
    test = test_info(trait, template, season)
    years = candidate_years(trait, n_folds)
    folds = [fold_info(trait, y) for y in years]
    paths = full_sources(years, full_dir, full_paths)
    have = {y for y in years if y in paths}
    choose_on, matched = pick_folds(test, folds, have)
    res = {"version": VERSION,
           "files": {r: os.path.relpath(p, data_dir).replace(os.sep, "/") for r, p in rel.items()},
           "test": test, "folds_considered": folds, "choose_on": choose_on, "matched": matched,
           "metric": "mean within-environment Pearson r (>= 3 rows)", "grid": list(sw.GRID), "folds": {}}
    if m4_fn is None and have:
        m4_fn = real_m4(trait, template, rel["geno_numeric"])
    for y in years:
        if y not in have:
            res["folds"][str(y)] = {"skipped": "no full predictions for this season"}
            continue
        full = rc.strip_keys(pd.read_csv(paths[y])).drop_duplicates(subset=["Env", "Hybrid"])
        df, fit = fold_frame(trait, y, full, m4_fn)
        r = evaluate_fold(df)
        r["fit"] = fit
        r["full_source"] = os.path.basename(paths[y])
        res["folds"][str(y)] = r
        print("fold", y, json.dumps(r["raw"]), json.dumps(r["chosen"]), flush=True)
    res["choice_grid"] = mean_grid([res["folds"][str(y)]["grid"] for y in choose_on])
    res["entry"] = entry_rule(res["choice_grid"])
    return res


def grade_expect(res, expect):
    """Checks D1-D6 of docs/g2f-refold-0.1.0.md."""
    g = {}
    tol = expect.get("tol", 0.0005)
    t = res.get("test", {})
    fs = {str(f["season"]): f["setting"] for f in res.get("folds_considered", [])}
    g["D1_season_and_settings"] = {
        "value": {"season": t.get("season"), "test_setting": t.get("setting"), "folds": fs},
        "held": t.get("season") == expect.get("season") and t.get("setting") == expect.get("test_setting")
        and fs == expect.get("folds")}
    g["D2_choose_on"] = {"value": {"choose_on": res.get("choose_on"), "matched": res.get("matched")},
                         "held": res.get("choose_on") == expect.get("choose_on") and res.get("matched") is True}
    devs = {}
    ok = bool(expect.get("raw"))
    for fold, cols in sorted(expect.get("raw", {}).items()):
        raw = res.get("folds", {}).get(fold, {}).get("raw", {})
        for col, want in sorted(cols.items()):
            v = raw.get(col)
            devs["%s_%s" % (col, fold)] = {"expected": want, "got": v}
            ok = ok and v is not None and abs(v - want) <= tol
    g["D3_fold_reproduced"] = {"value": devs, "held": bool(ok)}
    e = res.get("entry", {})
    want = expect.get("entry_score")
    g["D4_entry"] = {"value": {"name": e.get("name"), "score": e.get("score")},
                     "held": e.get("name") == expect.get("entry") and e.get("score") is not None
                     and want is not None and abs(e["score"] - want) <= tol}
    rep = res.get("folds", {}).get(str(expect.get("report_fold", "")), {})
    raw = rep.get("raw", {})
    m, f = raw.get("M4"), raw.get("full")
    g["D5_report_fold_M4_beats_full"] = {"value": {"M4": m, "full": f},
                                         "held": m is not None and f is not None and m > f}
    ch = rep.get("chosen") or {}
    g["D6_report_fold_b_at_most_half"] = {"value": ch or None,
                                          "held": ch.get("b") is not None and ch["b"] <= 0.5}
    return g


def parse_full(items):
    out = {}
    for it in items or []:
        y, _, p = it.partition("=")
        if not p:
            raise SystemExit("--full needs SEASON=PATH, got %r" % it)
        out[int(y)] = p
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("choose")
    c.add_argument("--data-dir", required=True)
    c.add_argument("--out-dir", required=True)
    c.add_argument("--full-dir", help="folder with <season>.csv kernel-model predictions (g2f_refmodel.R preds/)")
    c.add_argument("--full", action="append", help="SEASON=PATH, repeatable; overrides --full-dir")
    c.add_argument("--folds", type=int, default=N_FOLDS)
    c.add_argument("--expect")
    c.add_argument("--name", default="g2f_refold")
    args = ap.parse_args(argv)
    res = run(args.data_dir, parse_full(args.full), args.full_dir, args.folds)
    if args.expect:
        with open(args.expect, encoding="utf-8") as fh:
            expect = json.load(fh)
        res["expect"] = expect
        res["grading"] = grade_expect(res, expect)
        res["held"] = sum(1 for v in res["grading"].values() if v["held"])
        res["total"] = len(res["grading"])
    os.makedirs(args.out_dir, exist_ok=True)
    with open(os.path.join(args.out_dir, args.name + ".json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, sort_keys=True,
                  default=lambda o: o.item() if isinstance(o, np.generic) else str(o))
    print(json.dumps({k: res.get(k) for k in ("test", "choose_on", "matched", "entry", "grading", "held", "total")},
                     indent=1, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
