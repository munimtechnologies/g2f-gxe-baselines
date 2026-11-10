# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
"""g2f_levelmeta 0.1.0: how many hold-out seasons should g2f_level use to choose its level rule?

g2f_level 0.1.0 scores six yield-level rules on each hold-out season (`folds`, each trained on earlier
seasons only) and on the test season's answers (`check`). This script reads one g2f_level result run
with many folds and replays the choice season by season, as if each season were the test season of a
release that ended the season before. For a target season s, the rule is chosen on the k most recent
scored seasons before s (k = 1, 2, 4 or all), the way `g2f_level.py choose --folds k` chooses (lowest
mean level RMSE rounded to 4 places, ties to the earlier rule), and it is scored on s. Targets are the
seasons with at least 4 earlier scored seasons. Each k, and each fixed rule, is compared by its mean
level RMSE over the targets, and the decision rule of docs/g2f-levelmeta-0.1.0.md is applied.
--expect grades checks M1-M5 of that file. Standard library only; reads JSON, never downloads.
"""
import argparse
import json
import os

VERSION = "0.1.0"
RULES = ("site_all", "site_recent3", "recent_mean", "site_anomaly", "site_anomaly_shrunk",
         "site_anomaly_trend")
KS = ("1", "2", "4", "all")
MIN_EARLIER = 4
DEFAULT_RULE = "site_all"
TIE_ORDER = ("fixed:site_all", "k=all", "k=4", "k=2", "k=1")


def rule_rmses(rules):
    return {r: rules[r]["rmse"] for r in RULES if r in rules and rules[r].get("rmse") is not None}


def season_table(level_res):
    """{season: {rule: level RMSE}} from a g2f_level result: every fold, plus the check season."""
    tab = {}
    for y, f in level_res.get("folds", {}).items():
        tab[int(y)] = rule_rmses(f.get("rules", {}))
    chk = level_res.get("check")
    season = level_res.get("test_season")
    if chk and season is not None:
        tab[int(season)] = rule_rmses(chk.get("rules", {}))
    return tab


def pick(tab, seasons):
    """Rule with the lowest mean RMSE over `seasons` (rules scored in all of them); ties: earlier rule."""
    means = {}
    for r in RULES:
        vals = [tab[s].get(r) for s in seasons]
        if vals and all(v is not None for v in vals):
            means[r] = round(sum(vals) / len(vals), 4)
    if not means:
        return None
    return min(means, key=lambda r: (means[r], RULES.index(r)))


def use_seasons(earlier, k):
    earlier = list(earlier)
    return earlier if k == "all" else earlier[-int(k):]


def best_rule(row):
    if not row:
        return None
    return min(row, key=lambda r: (row[r], RULES.index(r)))


def mean_or_none(vals):
    if not vals or any(v is None for v in vals):
        return None
    return round(sum(vals) / len(vals), 4)


def evaluate(tab, ks=KS, min_earlier=MIN_EARLIER):
    seasons = sorted(tab)
    targets = [s for s in seasons if sum(1 for t in seasons if t < s) >= min_earlier]
    per = {}
    for s in targets:
        earlier = [t for t in seasons if t < s]
        b = best_rule(tab[s])
        row = {"best": b, "best_rmse": tab[s].get(b) if b else None, "k": {}}
        for k in ks:
            r = pick(tab, use_seasons(earlier, k))
            row["k"][k] = {"rule": r, "rmse": tab[s].get(r) if r else None}
        per[str(s)] = row
    procs = {"k=" + k: mean_or_none([per[str(s)]["k"][k]["rmse"] for s in targets]) for k in ks}
    fixed = {r: mean_or_none([tab[s].get(r) for s in targets]) for r in RULES}
    wins = {r: sum(1 for s in targets if per[str(s)]["best"] == r) for r in RULES}
    after = {k: pick(tab, use_seasons(seasons, k)) for k in ks}
    cands = dict(procs)
    cands["fixed:" + DEFAULT_RULE] = fixed.get(DEFAULT_RULE)
    scored = {c: v for c, v in cands.items() if v is not None}
    decision = None
    if scored:
        decision = min(scored, key=lambda c: (scored[c], TIE_ORDER.index(c) if c in TIE_ORDER else 99))
    return {"seasons": seasons, "targets": targets, "per_target": per, "procedures": procs,
            "fixed": fixed, "wins": wins, "choice_after": after, "candidates": cands, "decision": decision}


def grade(meta, tab, expect):
    """Checks M1-M5 of docs/g2f-levelmeta-0.1.0.md."""
    g = {}
    tol = expect.get("tol", 0.0001)
    devs, ok = {}, True
    for s, want in sorted(expect.get("repro", {}).items()):
        for r, v in sorted(want.items()):
            got = tab.get(int(s), {}).get(r)
            devs["%s.%s" % (s, r)] = {"expected": v, "got": got}
            ok = ok and got is not None and abs(got - v) <= tol
    ok = ok and bool(devs) and meta["targets"] == expect.get("targets")
    g["M1_reproduces_two_fold_run"] = {"value": {"targets": meta["targets"], "numbers": devs}, "held": bool(ok)}
    p = meta["procedures"]
    a, b = p.get("k=all"), p.get("k=2")
    g["M2_all_seasons_beat_two"] = {"value": {"k=all": a, "k=2": b},
                                    "held": a is not None and b is not None and a < b}
    fx = {r: v for r, v in meta["fixed"].items() if v is not None}
    rm = fx.get("recent_mean")
    g["M3_recent_mean_worst_fixed_rule"] = {
        "value": fx, "held": rm is not None and all(v < rm for r, v in fx.items() if r != "recent_mean")}
    bar = expect.get("gain_bar", 0.15)
    procs = [v for v in p.values() if v is not None]
    sa = fx.get(DEFAULT_RULE)
    best = min(procs) if procs else None
    g["M4_choosing_gains_little"] = {"value": {"best_procedure": best, "fixed_site_all": sa, "bar": bar},
                                     "held": best is not None and sa is not None and best >= round(sa - bar, 4)}
    floor = expect.get("floor", 1.2)
    bests = {s: row["best_rmse"] for s, row in meta["per_target"].items()}
    g["M5_level_floor_every_target"] = {"value": {"floor": floor, "best_rmse": bests},
                                        "held": bool(bests) and all(v is not None and v >= floor
                                                                    for v in bests.values())}
    return g


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--level-json", required=True, help="output of g2f_level.py choose (many folds)")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--expect")
    ap.add_argument("--name", default="g2f_levelmeta")
    args = ap.parse_args(argv)
    with open(args.level_json, encoding="utf-8") as fh:
        lres = json.load(fh)
    tab = season_table(lres)
    meta = evaluate(tab)
    res = {"version": VERSION, "level_version": lres.get("version"), "test_season": lres.get("test_season"),
           "fold_years": lres.get("fold_years"), "min_earlier": MIN_EARLIER, "ks": list(KS),
           "table": {str(s): tab[s] for s in sorted(tab)}}
    res.update(meta)
    if args.expect:
        with open(args.expect, encoding="utf-8") as fh:
            expect = json.load(fh)
        res["expect"] = expect
        res["grading"] = grade(meta, tab, expect)
        res["held"] = sum(1 for v in res["grading"].values() if v["held"])
        res["total"] = len(res["grading"])
    os.makedirs(args.out_dir, exist_ok=True)
    with open(os.path.join(args.out_dir, args.name + ".json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, sort_keys=True)
    print(json.dumps({k: res.get(k) for k in ("targets", "procedures", "fixed", "wins", "choice_after",
                                              "decision", "grading", "held", "total")}, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
