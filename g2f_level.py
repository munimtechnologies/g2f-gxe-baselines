# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
"""g2f_level 0.1.0: chooses how to set each test environment's yield level (Mg/ha) for a G2F upload.

Within-environment Pearson r (the 2024 metric) ignores each environment's level, but an error metric
(the 2022 round used RMSE inside each location) is driven by it: on the 2024 release, g2f-entry
0.2.0's site-history levels missed the environments' observed means by 2.04 Mg/ha on average, more
than the median within-environment SD of 1.86 Mg/ha. `choose` compares six level rules, all built
from training environment means only (g2f_entry.training_env_stats: mean of per-hybrid means):

  site_all             mean of every training environment at the same location, any year; else the
                       recent mean (exactly g2f_entry.scale_plan, the level used today)
  site_recent3         mean of the location's 3 most recent training environments; else recent mean
  recent_mean          one constant: mean of the environment means of the last 3 training seasons
  site_anomaly         recent mean + the location's mean anomaly (environment mean minus its season's
                       mean of environment means); a location with no history uses its state's (first
                       two letters) mean anomaly, else 0
  site_anomaly_shrunk  as site_anomaly, but the anomaly is multiplied by n / (n + 2), n = environments
                       it is averaged over
  site_anomaly_trend   as site_anomaly, but the base is a least-squares line of environment mean on
                       year over all training environments, read at the test season

It holds out each of the --folds most recent training seasons (default 2) in turn (training = earlier
seasons only; targets = that season's environments with at least 3 hybrids), scores each rule by the
RMSE of its levels against the environment means, and chooses the rule with the lowest mean RMSE over
the folds (ties: the earlier rule in the list above). If the release also has an observed-values file
(a past season), every rule is also scored on it: level RMSE, MAE and bias over environments, and
level-only upload scores (pooled RMSE over pairs, and the 2022 metric, RMSE inside each environment
averaged over environments). --expect grades checks L1-L6 of docs/g2f-level-0.1.0.md.
Standard library only; needs g2f_entry.py (0.2.0) from this repository. Never downloads anything.
"""
import argparse
import json
import math
import os

import g2f_entry as ge

VERSION = "0.1.0"
RECENT = ge.RECENT_YEARS
SHRINK_K = 2.0
MIN_TARGET_HYBRIDS = 3
N_FOLDS = 2
RULES = ("site_all", "site_recent3", "recent_mean", "site_anomaly", "site_anomaly_shrunk",
         "site_anomaly_trend")


def state_of(loc):
    return str(loc)[:2]


def years_of(stats):
    return sorted({s["year"] for s in stats.values() if s["year"] is not None})


def recent_mean(stats, recent=RECENT):
    """Mean of the environment means of the last `recent` seasons (as g2f_entry.scale_plan's fallback)."""
    ys = years_of(stats)[-recent:]
    if not ys:
        raise ValueError("no training environment has a year")
    return ge.mean([s["mean"] for s in stats.values() if s["year"] in ys])


def season_means(stats):
    acc = {}
    for s in stats.values():
        if s["year"] is not None:
            acc.setdefault(s["year"], []).append(s["mean"])
    return {y: sum(v) / len(v) for y, v in acc.items()}


def trend_at(stats, year):
    """(value at `year`, slope) of the least-squares line of environment mean on year."""
    pts = [(s["year"], s["mean"]) for s in stats.values() if s["year"] is not None]
    n = len(pts)
    mx = sum(x for x, _ in pts) / n
    my = sum(y for _, y in pts) / n
    sxx = sum((x - mx) ** 2 for x, _ in pts)
    if sxx == 0:
        return my, 0.0
    slope = sum((x - mx) * (y - my) for x, y in pts) / sxx
    return my + slope * (year - mx), slope


def anomalies(stats):
    """({location: [anomalies]}, {state: [anomalies]}); anomaly = env mean - its season's mean."""
    sm = season_means(stats)
    site, state = {}, {}
    for e, s in stats.items():
        if s["year"] is None:
            continue
        a = s["mean"] - sm[s["year"]]
        loc = ge.env_location(e)
        site.setdefault(loc, []).append(a)
        state.setdefault(state_of(loc), []).append(a)
    return site, state


def levels(rule, stats, envs, year):
    """{env: {"level", "source", "n"}} for each env in envs, from training stats only."""
    if rule not in RULES:
        raise ValueError("unknown rule %r" % rule)
    fallback = recent_mean(stats)
    envs = sorted(set(envs))
    out = {}
    if rule in ("site_all", "site_recent3"):
        by = {}
        for e, s in stats.items():
            by.setdefault(ge.env_location(e), []).append((s["year"] if s["year"] is not None else -1, s["mean"]))
        for e in envs:
            items = by.get(ge.env_location(e))
            if not items:
                out[e] = {"level": fallback, "source": "fallback", "n": 0}
                continue
            if rule == "site_all":
                ms = [m for _, m in items]
            else:
                ms = [m for _, m in sorted(items, key=lambda t: t[0])[-RECENT:]]
            out[e] = {"level": ge.mean(ms), "source": "site", "n": len(ms)}
        return out
    if rule == "recent_mean":
        return {e: {"level": fallback, "source": "fallback", "n": 0} for e in envs}
    site, state = anomalies(stats)
    base = trend_at(stats, year)[0] if rule == "site_anomaly_trend" else fallback
    for e in envs:
        loc = ge.env_location(e)
        if loc in site:
            a, src = site[loc], "site"
        elif state_of(loc) in state:
            a, src = state[state_of(loc)], "state"
        else:
            a, src = [], "fallback"
        n = len(a)
        m = sum(a) / n if n else 0.0
        if rule == "site_anomaly_shrunk":
            m *= n / (n + SHRINK_K)
        out[e] = {"level": base + m, "source": src, "n": n}
    return out


def level_errors(lv, targets):
    """RMSE, MAE and bias (level - target) over envs in both, plus the 3 largest misses."""
    errs = {e: lv[e]["level"] - t for e, t in sorted(targets.items()) if e in lv}
    n = len(errs)
    if not n:
        return {"envs": 0, "rmse": None, "mae": None, "bias": None, "worst": []}
    vals = list(errs.values())
    worst = sorted(errs.items(), key=lambda kv: (-abs(kv[1]), kv[0]))[:3]
    return {"envs": n, "rmse": round(math.sqrt(sum(x * x for x in vals) / n), 4),
            "mae": round(sum(abs(x) for x in vals) / n, 4), "bias": round(sum(vals) / n, 4),
            "worst": [[e, round(x, 4)] for e, x in worst]}


def fold_years(stats, n=N_FOLDS):
    """The n most recent training seasons, newest first, never the earliest season."""
    ys = sorted(years_of(stats), reverse=True)
    return ys[:max(0, min(n, len(ys) - 1))]


def fold(stats, year, min_hybrids=MIN_TARGET_HYBRIDS):
    train = {e: s for e, s in stats.items() if s["year"] is not None and s["year"] < year}
    targets = {e: s["mean"] for e, s in stats.items() if s["year"] == year and s["hybrids"] >= min_hybrids}
    res = {"season": int(year), "train_envs": len(train), "target_envs": len(targets),
           "recent_mean": round(recent_mean(train), 4), "season_mean": None, "rules": {}}
    if targets:
        res["season_mean"] = round(sum(targets.values()) / len(targets), 4)
    for r in RULES:
        lv = levels(r, train, targets, year)
        d = level_errors(lv, targets)
        d["from_site"] = sum(1 for v in lv.values() if v["source"] == "site")
        res["rules"][r] = d
    return res


def choose(folds):
    """(rule, {rule: mean fold RMSE}) over rules scored in every fold; ties go to the earlier rule."""
    table = {}
    for r in RULES:
        vals = [f["rules"][r]["rmse"] for f in folds]
        if vals and all(v is not None for v in vals):
            table[r] = round(sum(vals) / len(vals), 4)
    if not table:
        return None, table
    return min(table, key=lambda r: (table[r], RULES.index(r))), table


def template_pairs(template_path):
    header, rows = ge.read_csv(template_path)
    ie, ih = ge.key_index(header)
    return sorted({(ge.cell(r, ie), ge.cell(r, ih)) for r in rows})


def test_season(template_path, envs):
    ys = ge.name_years(template_path)
    if ys:
        return ys[-1]
    years = [y for y in (ge.env_year(e) for e in envs) if y is not None]
    return max(years) if years else None


def check(stats, pairs, obs, year):
    """Every rule scored against observed values of the test season."""
    envs = sorted({e for e, _ in pairs})
    obs_env = {}
    for (e, _h), v in obs.items():
        if e in envs:
            obs_env.setdefault(e, []).append(v)
    targets = {e: ge.mean(vs) for e, vs in sorted(obs_env.items())}
    out = {"envs_observed": len(targets),
           "season_mean": round(sum(targets.values()) / len(targets), 4) if targets else None,
           "rules": {}}
    for r in RULES:
        lv = levels(r, stats, envs, year)
        preds = {(e, h): lv[e]["level"] for e, h in pairs}
        d = level_errors(lv, targets)
        d["pooled_rmse"] = ge.rmse(preds, obs)["rmse"]
        d["env_rmse_mean_2022_metric"] = ge.env_rmse_mean(preds, obs)["mean_rmse"]
        out["rules"][r] = d
    return out


def entry_plan(trait_path, template_path, rule, min_hybrids=ge.MIN_HYBRIDS):
    """g2f_entry.scale_plan with each environment's level replaced by `rule`'s level, ready for
    g2f_entry.rescale (spread and fallback unchanged)."""
    stats = ge.training_env_stats(trait_path)
    envs = ge.template_envs(template_path)
    plan = ge.scale_plan(stats, envs, min_hybrids=min_hybrids)
    lv = levels(rule, stats, envs, test_season(template_path, envs))
    for e, v in lv.items():
        plan["envs"][e] = {"level": v["level"], "source": "%s:%s" % (rule, v["source"]), "seasons": v["n"]}
    plan["level_rule"] = rule
    return plan


def run(data_dir, n_folds=N_FOLDS):
    rel = ge.find_release(data_dir)
    for role in ("trait", "template"):
        if role not in rel:
            raise FileNotFoundError("no %s file below %s (g2f_level never downloads)" % (role, data_dir))
    stats = ge.training_env_stats(rel["trait"])
    pairs = template_pairs(rel["template"])
    envs = sorted({e for e, _ in pairs})
    season = test_season(rel["template"], envs)
    res = {"version": VERSION,
           "files": {r: os.path.relpath(p, data_dir).replace(os.sep, "/") for r, p in rel.items()},
           "test_season": season, "training_years": years_of(stats), "training_envs": len(stats),
           "template_pairs": len(pairs), "template_envs": len(envs), "rules": list(RULES),
           "shrink_k": SHRINK_K, "recent": RECENT, "min_target_hybrids": MIN_TARGET_HYBRIDS}
    years = fold_years(stats, n_folds)
    res["fold_years"] = years
    res["folds"] = {str(y): fold(stats, y) for y in years}
    for y in years:
        print("fold", y, json.dumps({r: v["rmse"] for r, v in res["folds"][str(y)]["rules"].items()}), flush=True)
    rule, table = choose([res["folds"][str(y)] for y in years])
    res["choice_table"] = table
    res["chosen"] = rule
    trend = trend_at(stats, season) if season is not None else (None, None)
    res["trend"] = {"value_at_test_season": None if trend[0] is None else round(trend[0], 4),
                    "slope_per_year": None if trend[1] is None else round(trend[1], 4)}
    if rule:
        lv = levels(rule, stats, envs, season)
        res["levels"] = {e: {"level": round(v["level"], 4), "source": v["source"], "n": v["n"]}
                         for e, v in lv.items()}
    if "observed" in rel:
        obs = ge.read_values(rel["observed"], None, dup="mean")
        res["check"] = check(stats, pairs, obs, season)
    return res


def grade_expect(res, expect):
    """Checks L1-L6 of docs/g2f-level-0.1.0.md."""
    g = {}
    tol = expect.get("tol", 0.0005)
    rules = res.get("check", {}).get("rules", {})
    devs, ok = {}, True
    for rule, want in sorted(expect.get("repro", {}).items()):
        for k, v in sorted(want.items()):
            got = rules.get(rule, {}).get(k)
            devs["%s.%s" % (rule, k)] = {"expected": v, "got": got}
            ok = ok and got is not None and abs(got - v) <= tol
    ok = ok and res.get("test_season") == expect.get("season") and res.get("fold_years") == expect.get("folds")
    g["L1_reproduces_entry_levels"] = {"value": {"season": res.get("test_season"), "folds": res.get("fold_years"),
                                                 "numbers": devs}, "held": bool(ok)}
    ch = res.get("chosen")
    g["L2_choice_is_not_site_all"] = {"value": {"chosen": ch, "table": res.get("choice_table")},
                                      "held": ch is not None and ch != "site_all"}
    c, s = rules.get(ch, {}).get("rmse"), rules.get("site_all", {}).get("rmse")
    g["L3_choice_beats_site_all_on_check"] = {"value": {"chosen": c, "site_all": s},
                                              "held": c is not None and s is not None and c < s}
    biases = {r: rules.get(r, {}).get("bias") for r in RULES}
    g["L4_every_rule_too_low_on_check"] = {"value": biases,
                                           "held": all(b is not None and b < 0 for b in biases.values())}
    rm = {r: rules.get(r, {}).get("rmse") for r in RULES}
    floor = expect.get("rmse_floor", 1.5)
    g["L5_no_rule_below_floor_on_check"] = {"value": {"floor": floor, "rmse": rm},
                                            "held": all(v is not None and v >= floor for v in rm.values())}
    t = res.get("choice_table", {})
    a, b = t.get("site_anomaly_shrunk"), t.get("site_anomaly")
    g["L6_shrinking_helps_on_folds"] = {"value": {"site_anomaly_shrunk": a, "site_anomaly": b},
                                        "held": a is not None and b is not None and a < b}
    return g


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("choose")
    c.add_argument("--data-dir", required=True)
    c.add_argument("--out-dir", required=True)
    c.add_argument("--folds", type=int, default=N_FOLDS)
    c.add_argument("--expect")
    c.add_argument("--name", default="g2f_level")
    args = ap.parse_args(argv)
    res = run(args.data_dir, args.folds)
    if args.expect:
        with open(args.expect, encoding="utf-8") as fh:
            expect = json.load(fh)
        res["expect"] = expect
        res["grading"] = grade_expect(res, expect)
        res["held"] = sum(1 for v in res["grading"].values() if v["held"])
        res["total"] = len(res["grading"])
    os.makedirs(args.out_dir, exist_ok=True)
    with open(os.path.join(args.out_dir, args.name + ".json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, sort_keys=True)
    print(json.dumps({k: res.get(k) for k in ("test_season", "fold_years", "choice_table", "chosen", "grading",
                                              "held", "total")}, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
