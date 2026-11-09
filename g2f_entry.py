# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
"""g2f_entry 0.2.0: build, check and score a Genomes to Fields GxE competition submission file.

Release-day helper for the G2F maize GxE prediction competition (standard library only):
  locate    find the trait, template, observed and genotype files in a release folder by name
  seen      share of template (Env, Hybrid) pairs whose hybrid has a training yield row, in any
            year and in the last training year, and the model-choice rule pre-registered in
            docs/g2f-release-census-0.1.0.md (R3: >= 70% in the last year = repeated hybrids)
  write     fill the submission template, row for row and in its own order, from a predictions CSV
  mgha      (new in 0.2.0) like write, but first turn scale-free predictions into absolute yields
            in Mg/ha, environment by environment, with a positive affine map, so the
            within-environment Pearson r (the ranking metric) is unchanged
  validate  check a submission against its template: same header, same rows in the same order,
            every yield a finite number; warn on environments with one constant prediction
  score     mean within-environment Pearson r against an observed-values file (environments with
            at least 3 observed rows; a constant prediction scores 0), as in g2f_baseline.py
  dryrun    all of the above on a past release, plus five deliberately broken copies of the
            submission that validate must reject
  dryrun-mgha  (new in 0.2.0) the mgha step on a past release: checks E1-E5 of
            docs/g2f-entry-0.2.0.md
Within-environment r ignores each environment's mean and scale, so only the ranking of hybrids
inside an environment matters for the score. The 2024 rules still ask for "absolute grain yield
... in Mg/ha", which is what mgha provides.
"""
import argparse
import csv
import json
import math
import os
import re
import sys
import urllib.request

VERSION = "0.2.0"
YIELD_COL = "Yield_Mg_ha"
MIN_ROWS = 3
REPEAT_THRESHOLD = 0.70
# mgha defaults, fixed in docs/g2f-entry-0.2.0.md before the dry run.
SHRINK = 0.30          # hybrid spread = SHRINK x median within-environment SD of training hybrid means
RECENT_YEARS = 3       # fallback level and spread come from the last 3 training seasons
MIN_HYBRIDS = 10       # environments with fewer hybrids do not inform the spread
LO, HI = 0.5, 25.0     # every Mg/ha value is kept inside this band (spread shrinks per env if needed)
# (role, substrings of the lower-case file name); the first match wins (as g2f_release_census.py).
ROLES = (
    ("observed", ("observed_values",)),
    ("template", ("submission_template",)),
    ("trait", ("trait_data",)),
    ("meta", ("meta_data",)),
    ("soil", ("soil_data",)),
    ("weather", ("weather_data",)),
    ("ec", ("ec_data",)),
    ("geno_numeric", ("_numerical",)),
    ("vcf", (".vcf",)),
)
CSV_ROLES = ("observed", "template", "trait", "meta", "soil", "weather", "ec")
FAULTS = ("swap_rows", "blank_value", "drop_last_row", "rename_yield_column", "nan_value")


def role_of(name):
    low = os.path.basename(name).lower()
    for role, pats in ROLES:
        if any(p in low for p in pats):
            return role
    return "other"


def env_year(env):
    tail = str(env).strip().rsplit("_", 1)[-1]
    return int(tail) if len(tail) == 4 and tail.isdigit() else None


def env_location(env):
    """Env name without its trailing _YYYY (IAH4_2024 -> IAH4); the name itself if it has none."""
    e = str(env).strip()
    return e.rsplit("_", 1)[0] if env_year(e) is not None and "_" in e else e


def is_number(text):
    try:
        x = float(text)
    except (TypeError, ValueError):
        return False
    return not (math.isnan(x) or math.isinf(x))


def name_years(path):
    """Four-digit years (2000-2099) in a file name, in order."""
    return [int(y) for y in re.findall(r"(?<!\d)(20\d\d)(?!\d)", os.path.basename(path))]


def find_release(data_dir):
    """{role: path} for each known role; the largest file wins when a role has several."""
    found = {}
    for root, dirs, names in os.walk(data_dir):
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))
        for n in sorted(names):
            if n.startswith("."):
                continue
            role = role_of(n)
            if role == "other" or (role in CSV_ROLES and not n.lower().endswith(".csv")):
                continue
            p = os.path.join(root, n)
            size = os.path.getsize(p)
            if role not in found or size > found[role][1]:
                found[role] = (p, size)
    return {r: v[0] for r, v in sorted(found.items())}


def read_csv(path):
    """(header, rows) with every cell stripped; blank lines are dropped."""
    with open(path, encoding="utf-8-sig", errors="replace", newline="") as fh:
        reader = csv.reader(fh)
        header = [h.strip() for h in next(reader, [])]
        rows = [[c.strip() for c in r] for r in reader if r and any(c.strip() for c in r)]
    return header, rows


def key_index(header):
    if "Env" not in header or "Hybrid" not in header:
        raise ValueError("no Env and Hybrid columns in header %r" % (header,))
    return header.index("Env"), header.index("Hybrid")


def value_index(header, col=None):
    """Index of col; without col, Yield_Mg_ha or else the first column that is not Env or Hybrid."""
    if col:
        return header.index(col) if col in header else None
    if YIELD_COL in header:
        return header.index(YIELD_COL)
    rest = [i for i, h in enumerate(header) if h not in ("Env", "Hybrid")]
    return rest[0] if rest else None


def cell(row, i):
    return row[i] if i is not None and i < len(row) else ""


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else None


def median(xs):
    xs = sorted(xs)
    n = len(xs)
    if not n:
        return None
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def sample_sd(xs):
    xs = list(xs)
    n = len(xs)
    if n < 2:
        return 0.0
    m = sum(xs) / n
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))


def read_values(path, col=None, dup="error"):
    """{(Env, Hybrid): float} from a CSV. Non-numeric cells are skipped. A pair listed twice with
    different values raises (dup="error") or is averaged (dup="mean")."""
    header, rows = read_csv(path)
    ie, ih = key_index(header)
    iv = value_index(header, col)
    if iv is None:
        raise ValueError("no value column %r in %s" % (col or YIELD_COL, path))
    acc = {}
    for r in rows:
        v = cell(r, iv)
        if is_number(v):
            acc.setdefault((cell(r, ie), cell(r, ih)), []).append(float(v))
    out = {}
    for k, vs in acc.items():
        if dup == "error" and len(set(vs)) > 1:
            raise ValueError("pair %s / %s has %d different values in %s" % (k[0], k[1], len(set(vs)), path))
        out[k] = sum(vs) / len(vs)
    return out


def submission_header(template_header):
    h = list(template_header)
    return h if YIELD_COL in h else h + [YIELD_COL]


def write_submission(template_path, preds, out_path, fill=None):
    """Write the template with Yield_Mg_ha filled from preds {(Env, Hybrid): value}, keeping the
    template's columns and row order. A template row without a prediction raises, unless
    fill="env_mean" (the mean prediction of its environment, else of all predictions)."""
    for k, v in preds.items():
        if not is_number(v):
            raise ValueError("prediction for %s / %s is not a finite number: %r" % (k[0], k[1], v))
    header, rows = read_csv(template_path)
    ie, ih = key_index(header)
    out_header = submission_header(header)
    iv = out_header.index(YIELD_COL)
    missing = [(cell(r, ie), cell(r, ih)) for r in rows if (cell(r, ie), cell(r, ih)) not in preds]
    if missing and fill != "env_mean":
        raise ValueError("%d template rows have no prediction; first: %s / %s"
                         % (len(missing), missing[0][0], missing[0][1]))
    env_vals = {}
    for (e, _h), v in preds.items():
        env_vals.setdefault(e, []).append(float(v))
    allv = [float(v) for v in preds.values()]
    overall = sum(allv) / len(allv) if allv else 0.0
    filled = 0
    with open(out_path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(out_header)
        for r in rows:
            r = list(r) + [""] * max(0, len(out_header) - len(r))
            k = (cell(r, ie), cell(r, ih))
            if k in preds:
                v = float(preds[k])
            else:
                vs = env_vals.get(k[0])
                v = sum(vs) / len(vs) if vs else overall
                filled += 1
            r[iv] = "%.6f" % v
            w.writerow(r[:len(out_header)])
    return {"rows": len(rows), "missing_predictions": len(missing), "filled_by_env_mean": filled}


def validate_submission(template_path, sub_path):
    """{"ok", "errors", "warnings", ...}: the submission must have the template's header (plus
    Yield_Mg_ha if the template lacks it), the template's rows in the same order, and a finite
    number in every yield cell."""
    errors, warnings = [], []
    t_header, t_rows = read_csv(template_path)
    s_header, s_rows = read_csv(sub_path)
    exp = submission_header(t_header)
    res = {"template_rows": len(t_rows), "rows": len(s_rows)}
    if s_header != exp:
        errors.append("header is %r, expected %r" % (s_header, exp))
    if len(s_rows) != len(t_rows):
        errors.append("%d data rows, the template has %d" % (len(s_rows), len(t_rows)))
    ie, ih = key_index(t_header)
    try:
        se, sh = key_index(s_header)
    except ValueError as exc:
        errors.append(str(exc))
        res.update({"ok": False, "errors": errors, "warnings": warnings})
        return res
    iv = s_header.index(YIELD_COL) if YIELD_COL in s_header else None
    if iv is None:
        errors.append("no %s column" % YIELD_COL)
    mism = bad = 0
    first_mism = first_bad = None
    per_env = {}
    for i, (t, s) in enumerate(zip(t_rows, s_rows)):
        tk, sk = (cell(t, ie), cell(t, ih)), (cell(s, se), cell(s, sh))
        if tk != sk:
            mism += 1
            if first_mism is None:
                first_mism = (i + 2, tk, sk)
        if iv is not None:
            v = cell(s, iv)
            if not is_number(v):
                bad += 1
                if first_bad is None:
                    first_bad = (i + 2, v)
            else:
                per_env.setdefault(sk[0], []).append(float(v))
    if mism:
        errors.append("%d rows differ from the template's Env/Hybrid order; first at line %d: %s / %s, "
                      "template has %s / %s" % (mism, first_mism[0], first_mism[2][0], first_mism[2][1],
                                                first_mism[1][0], first_mism[1][1]))
    if bad:
        errors.append("%d yield cells are not finite numbers; first at line %d: %r" % (bad, first_bad[0],
                                                                                        first_bad[1]))
    const = sorted(e for e, vs in per_env.items() if len(vs) >= 2 and max(vs) == min(vs))
    if const:
        warnings.append("%d environments have one constant prediction and would score 0: %s"
                        % (len(const), ", ".join(const)))
    vals = [v for vs in per_env.values() for v in vs]
    if vals and (min(vals) < 0 or max(vals) > 30):
        warnings.append("predictions run from %.3f to %.3f, outside 0-30 Mg/ha; within-environment r "
                        "ignores scale, but check whether the rules ask for yields in Mg/ha"
                        % (min(vals), max(vals)))
    res.update({"ok": not errors, "errors": errors, "warnings": warnings, "envs": len(per_env)})
    if vals:
        res["range"] = [round(min(vals), 4), round(max(vals), 4)]
    return res


def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    if sxx == 0 or syy == 0:
        return 0.0
    return sxy / math.sqrt(sxx * syy)


def env_pearson(preds, obs):
    """{env: unrounded r} over pairs in both dicts, with the score's skip rules."""
    by_env = {}
    for (e, h), p in sorted(preds.items()):
        if (e, h) in obs:
            by_env.setdefault(e, []).append((p, obs[(e, h)]))
    out = {}
    for e, pairs in sorted(by_env.items()):
        ps, os_ = [a for a, _ in pairs], [b for _, b in pairs]
        if len(pairs) < MIN_ROWS or max(os_) == min(os_):
            continue
        out[e] = 0.0 if max(ps) == min(ps) else pearson(ps, os_)
    return out


def score_submission(sub_path, observed_path, col=YIELD_COL):
    """Mean within-environment Pearson r of a submission against observed values (averaged per pair).
    Environments with fewer than MIN_ROWS observed rows or constant observations are skipped; a
    constant prediction scores 0."""
    preds = read_values(sub_path, col, dup="error")
    obs = read_values(observed_path, None, dup="mean")
    env_r = env_pearson(preds, obs)
    pairs = sum(1 for k in preds if k in obs)
    mean_r = round(sum(env_r.values()) / len(env_r), 4) if env_r else None
    return {"mean_r": mean_r, "envs": len(env_r), "pairs_scored": pairs,
            "env_r": {e: round(r, 4) for e, r in env_r.items()}}


def rmse(preds, obs):
    """{"rmse", "pairs"} over pairs present in both dicts (rmse None if none)."""
    d = [(preds[k] - obs[k]) ** 2 for k in preds if k in obs]
    return {"rmse": round(math.sqrt(sum(d) / len(d)), 4) if d else None, "pairs": len(d)}


def env_rmse_mean(preds, obs):
    """The 2022 competition's metric: RMSE inside each environment, averaged over environments."""
    by_env = {}
    for k, p in preds.items():
        if k in obs:
            by_env.setdefault(k[0], []).append((p - obs[k]) ** 2)
    per = [math.sqrt(sum(d) / len(d)) for d in by_env.values()]
    return {"mean_rmse": round(sum(per) / len(per), 4) if per else None, "envs": len(per)}


def row_year(ycell, env):
    if is_number(ycell):
        return int(float(ycell))
    return env_year(env)


def _trait_rows(trait_path):
    """Yields (env, hybrid, year, yield) for every training row with a numeric yield."""
    with open(trait_path, encoding="utf-8-sig", errors="replace", newline="") as fh:
        reader = csv.reader(fh)
        header = [h.strip() for h in next(reader, [])]
        ie, ih = key_index(header)
        iy = header.index("Year") if "Year" in header else None
        if YIELD_COL not in header:
            raise ValueError("no %s column in %s" % (YIELD_COL, trait_path))
        iv = header.index(YIELD_COL)
        for r in reader:
            v = cell(r, iv).strip()
            if not is_number(v):
                continue
            e, h = cell(r, ie).strip(), cell(r, ih).strip()
            yield e, h, row_year(cell(r, iy).strip(), e), float(v)


def trait_hybrid_years(trait_path):
    """{hybrid: set of years with a numeric yield row}, read row by row."""
    out = {}
    for _e, h, y, _v in _trait_rows(trait_path):
        if h and y is not None:
            out.setdefault(h, set()).add(y)
    return out


def training_env_stats(trait_path):
    """{env: {"year", "mean", "sd", "hybrids"}}: mean and sample SD of the per-hybrid mean yields of
    each training environment (plots of one hybrid are averaged first)."""
    acc, year = {}, {}
    for e, h, y, v in _trait_rows(trait_path):
        if not e or not h:
            continue
        acc.setdefault(e, {}).setdefault(h, []).append(v)
        if e not in year and y is not None:
            year[e] = y
    out = {}
    for e, hy in sorted(acc.items()):
        means = [sum(vs) / len(vs) for vs in hy.values()]
        out[e] = {"year": year.get(e, env_year(e)), "mean": sum(means) / len(means),
                  "sd": sample_sd(means), "hybrids": len(means)}
    return out


def scale_plan(stats, template_envs, shrink=SHRINK, recent=RECENT_YEARS, min_hybrids=MIN_HYBRIDS):
    """Level (Mg/ha) for each template environment and one hybrid spread, from training data only.
    level = mean of the training environment means at the same location (any year), else the mean
    of the environment means of the last `recent` training seasons; spread = shrink x the median
    SD of hybrid means over the recent environments with at least min_hybrids hybrids."""
    years = sorted({s["year"] for s in stats.values() if s["year"] is not None})
    if not years:
        raise ValueError("no training environment has a year")
    recent_years = years[-recent:]
    rec = [s for s in stats.values() if s["year"] in recent_years]
    fallback = mean(s["mean"] for s in rec)
    sds = [s["sd"] for s in rec if s["hybrids"] >= min_hybrids]
    if not sds:
        raise ValueError("no recent training environment has %d or more hybrids" % min_hybrids)
    by_loc = {}
    for e, s in stats.items():
        by_loc.setdefault(env_location(e), []).append(s["mean"])
    envs = {}
    for e in sorted(set(template_envs)):
        ms = by_loc.get(env_location(e))
        envs[e] = {"level": mean(ms) if ms else fallback,
                   "source": "location" if ms else "recent_mean", "seasons": len(ms or [])}
    return {"shrink": shrink, "median_sd": median(sds), "spread": shrink * median(sds),
            "fallback": fallback, "recent_years": recent_years, "sd_envs": len(sds), "envs": envs}


def rescale(preds, plan, lo=LO, hi=HI):
    """Mg/ha predictions: level_e + s_e * z, where z standardises the predictions inside each
    environment and s_e = plan spread, shrunk for an environment only if a value would leave
    [lo, hi]. A positive affine map per environment, so within-environment r is unchanged."""
    by_env = {}
    for (e, h), v in preds.items():
        by_env.setdefault(e, []).append(((e, h), float(v)))
    out, shrunk, levels = {}, [], {}
    for e, items in sorted(by_env.items()):
        info = plan["envs"].get(e)
        level = info["level"] if info else plan["fallback"]
        levels[e] = level
        room = min(level - lo, hi - level)
        if room <= 0:
            raise ValueError("level %.3f for %s is outside %.1f-%.1f Mg/ha" % (level, e, lo, hi))
        vals = [v for _, v in items]
        m, sd = sum(vals) / len(vals), sample_sd(vals)
        if sd == 0:
            for k, _ in items:
                out[k] = level
            continue
        s = plan["spread"]
        zmax = max(abs(v - m) / sd for v in vals)
        if s * zmax > room:
            s = room / zmax
            shrunk.append(e)
        for k, v in items:
            out[k] = level + s * (v - m) / sd
    return out, {"envs": len(by_env), "spread_shrunk_envs": shrunk,
                 "envs_without_plan": sorted(e for e in by_env if e not in plan["envs"])}


def seen_share(trait_path, template_path):
    """How many distinct template pairs have a hybrid with a training yield row (any year, last year)."""
    hy = trait_hybrid_years(trait_path)
    years = set()
    for ys in hy.values():
        years |= ys
    last = max(years) if years else None
    header, rows = read_csv(template_path)
    ie, ih = key_index(header)
    pairs = sorted({(cell(r, ie), cell(r, ih)) for r in rows})
    n = len(pairs)
    seen = sum(1 for _e, h in pairs if h in hy)
    in_last = sum(1 for _e, h in pairs if last in hy.get(h, ()))
    return {"template_pairs": n, "training_years": sorted(years), "last_training_year": last,
            "pairs_hybrid_seen": seen, "pairs_hybrid_in_last_year": in_last,
            "share_seen": round(seen / n, 4) if n else None,
            "share_in_last_year": round(in_last / n, 4) if n else None}


def decide(share_in_last_year, threshold=REPEAT_THRESHOLD):
    """Model-choice rule R3 of docs/g2f-release-census-0.1.0.md."""
    if share_in_last_year is None:
        return {"setting": "unknown", "threshold": threshold, "share_in_last_year": None,
                "choose_on": None}
    repeated = share_in_last_year >= threshold
    return {"setting": "repeated_hybrids" if repeated else "new_hybrids", "threshold": threshold,
            "share_in_last_year": share_in_last_year,
            "choose_on": ("the 2023-like fold (test hybrids grown the season before)" if repeated else
                          "the 2024-like fold (mostly hybrids never tested before)")}


def make_fault(header, rows, kind):
    """A deliberately broken copy (header, rows) of a valid submission."""
    h, rs = list(header), [list(r) for r in rows]
    iv = h.index(YIELD_COL)
    if kind == "swap_rows":
        rs[0], rs[1] = rs[1], rs[0]
    elif kind == "blank_value":
        rs[min(5, len(rs) - 1)][iv] = ""
    elif kind == "drop_last_row":
        rs = rs[:-1]
    elif kind == "rename_yield_column":
        h[iv] = "Yield"
    elif kind == "nan_value":
        rs[min(7, len(rs) - 1)][iv] = "nan"
    else:
        raise ValueError("unknown fault %r" % kind)
    return h, rs


def fault_checks(template_path, sub_path, work_dir):
    """{fault: {"rejected": bool, "errors": [...]}} for each fault in FAULTS."""
    header, rows = read_csv(sub_path)
    out = {}
    for kind in FAULTS:
        h, rs = make_fault(header, rows, kind)
        p = os.path.join(work_dir, "fault_%s.csv" % kind)
        with open(p, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh, lineterminator="\n")
            w.writerow(h)
            w.writerows(rs)
        v = validate_submission(template_path, p)
        out[kind] = {"rejected": not v["ok"], "errors": v["errors"]}
        os.remove(p)
    return out


def fetch(source, work_dir):
    if source.startswith("http://") or source.startswith("https://"):
        p = os.path.join(work_dir, os.path.basename(source.split("?")[0]) or "predictions.csv")
        urllib.request.urlretrieve(source, p)
        return p
    return source


def template_envs(template_path):
    header, rows = read_csv(template_path)
    ie, _ih = key_index(header)
    return sorted({cell(r, ie) for r in rows})


def mgha_predictions(trait_path, template_path, preds, shrink=SHRINK, min_hybrids=MIN_HYBRIDS):
    """(Mg/ha predictions, plan, rescale info) for predictions on any scale."""
    plan = scale_plan(training_env_stats(trait_path), template_envs(template_path), shrink=shrink,
                      min_hybrids=min_hybrids)
    mg, info = rescale(preds, plan)
    return mg, plan, info


def dryrun(data_dir, out_dir, pred_source, col, expect=None):
    """Locate, write, validate, score, fault-check and decide on a past release; grade expect."""
    os.makedirs(out_dir, exist_ok=True)
    rel = find_release(data_dir)
    res = {"version": VERSION, "release": {r: os.path.relpath(p, data_dir).replace(os.sep, "/")
                                           for r, p in rel.items()},
           "release_name_years": {r: name_years(p) for r, p in rel.items()},
           "predictions": {"source": pred_source, "column": col}}
    preds = read_values(fetch(pred_source, out_dir), col, dup="error")
    res["predictions"]["pairs"] = len(preds)
    sub = os.path.join(out_dir, "submission_dryrun.csv")
    res["write"] = write_submission(rel["template"], preds, sub)
    res["validate"] = validate_submission(rel["template"], sub)
    if "observed" in rel:
        res["score"] = score_submission(sub, rel["observed"])
    if "trait" in rel:
        res["seen"] = seen_share(rel["trait"], rel["template"])
        res["decision"] = decide(res["seen"]["share_in_last_year"])
    res["faults"] = fault_checks(rel["template"], sub, out_dir)
    if expect:
        res["expect"] = grade_dryrun(res, expect)
        res["expect_held"] = sum(1 for v in res["expect"].values() if v["held"])
        res["expect_total"] = len(res["expect"])
    return res


def grade_dryrun(res, expect):
    """Checks D1-D6 of docs/g2f-entry-0.1.0.md; expect holds the stated figures."""
    g = {}
    roles = sorted(res.get("release", {}))
    need = expect.get("roles", ["trait", "template", "observed", "geno_numeric"])
    g["D1_roles_found"] = {"value": roles, "held": all(r in roles for r in need)}
    w = res.get("write", {})
    g["D2_every_template_row_predicted"] = {"value": w.get("missing_predictions"),
                                            "held": w.get("missing_predictions") == 0}
    v = res.get("validate", {})
    g["D3_submission_validates"] = {"value": {"errors": len(v.get("errors", [])), "rows": v.get("rows")},
                                    "held": bool(v.get("ok"))}
    s = res.get("score", {})
    m = s.get("mean_r")
    ok4 = (m is not None and abs(m - expect["score"]) <= expect.get("score_tol", 0.0001)
           and s.get("envs") == expect.get("envs"))
    g["D4_score_reproduces_published"] = {"value": {"mean_r": m, "envs": s.get("envs")}, "held": ok4}
    f = res.get("faults", {})
    g["D5_all_faults_rejected"] = {"value": {k: f[k]["rejected"] for k in f},
                                   "held": len(f) == len(FAULTS) and all(f[k]["rejected"] for k in f)}
    sn, d = res.get("seen", {}), res.get("decision", {})
    lo, hi = expect.get("share_seen", [0, 1])
    sh = sn.get("share_seen")
    g["D6_seen_share_and_decision"] = {
        "value": {"share_seen": sh, "share_in_last_year": sn.get("share_in_last_year"),
                  "setting": d.get("setting")},
        "held": sh is not None and lo <= sh <= hi and d.get("setting") == expect.get("setting")}
    return g


def dryrun_mgha(data_dir, out_dir, pred_source, col, expect=None, shrink=SHRINK,
                min_hybrids=MIN_HYBRIDS):
    """The mgha step on a past release with public answers: checks E1-E5 of docs/g2f-entry-0.2.0.md."""
    os.makedirs(out_dir, exist_ok=True)
    rel = find_release(data_dir)
    for role in ("trait", "template", "observed"):
        if role not in rel:
            raise ValueError("no %s file under %s" % (role, data_dir))
    res = {"version": VERSION, "study": "g2f-entry-0.2.0-mgha",
           "release": {r: os.path.basename(rel[r]) for r in ("trait", "template", "observed")},
           "predictions": {"source": pred_source, "column": col}}
    preds = read_values(fetch(pred_source, out_dir), col, dup="error")
    res["predictions"]["pairs"] = len(preds)
    raw_sub = os.path.join(out_dir, "submission_raw.csv")
    write_submission(rel["template"], preds, raw_sub)
    res["score_raw"] = score_submission(raw_sub, rel["observed"])
    mg, plan, info = mgha_predictions(rel["trait"], rel["template"], preds, shrink, min_hybrids)
    sub = os.path.join(out_dir, "submission_mgha.csv")
    res["write"] = write_submission(rel["template"], mg, sub)
    res["validate"] = validate_submission(rel["template"], sub)
    res["score_mgha"] = score_submission(sub, rel["observed"])
    obs = read_values(rel["observed"], None, dup="mean")
    raw_r = env_pearson(read_values(raw_sub), obs)
    mg_r = env_pearson(read_values(sub), obs)
    diffs = [abs(raw_r[e] - mg_r.get(e, float("inf"))) for e in raw_r]
    res["env_r_max_abs_diff"] = max(diffs) if diffs else None
    res["env_r_sets_equal"] = sorted(raw_r) == sorted(mg_r)
    level = {k: plan["envs"].get(k[0], {"level": plan["fallback"]})["level"] for k in mg}
    const = {k: plan["fallback"] for k in mg}
    mg_file = read_values(sub)
    res["rmse"] = {"mgha": rmse(mg_file, obs), "level_only": rmse(level, obs),
                   "recent_mean": rmse(const, obs)}
    res["env_rmse_mean_2022_metric"] = {"mgha": env_rmse_mean(mg_file, obs),
                                        "level_only": env_rmse_mean(level, obs),
                                        "recent_mean": env_rmse_mean(const, obs)}
    obs_env = {}
    for (e, _h), v in obs.items():
        obs_env.setdefault(e, []).append(v)
    lvl_err = {e: round(plan["envs"][e]["level"] - mean(vs), 4)
               for e, vs in sorted(obs_env.items()) if e in plan["envs"]}
    res["level_error_by_env"] = lvl_err
    res["level_mean_abs_error"] = round(mean(abs(x) for x in lvl_err.values()), 4) if lvl_err else None
    res["observed_within_env_sd_median"] = round(median(sample_sd(vs) for vs in obs_env.values()), 4)
    res["plan"] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in plan.items() if k != "envs"}
    res["plan"]["envs_from_location"] = sum(1 for v in plan["envs"].values() if v["source"] == "location")
    res["plan"]["envs_total"] = len(plan["envs"])
    res["plan"]["levels"] = {e: round(v["level"], 4) for e, v in plan["envs"].items()}
    res["rescale"] = info
    if expect:
        res["expect"] = grade_mgha(res, expect)
        res["expect_held"] = sum(1 for v in res["expect"].values() if v["held"])
        res["expect_total"] = len(res["expect"])
    return res


def grade_mgha(res, expect):
    """Checks E1-E5 of docs/g2f-entry-0.2.0.md."""
    g = {}
    v = res["validate"]
    g["E1_mgha_validates_without_warnings"] = {
        "value": {"errors": len(v["errors"]), "warnings": len(v["warnings"]), "range": v.get("range")},
        "held": bool(v["ok"]) and not v["warnings"]}
    sr, sm = res["score_raw"], res["score_mgha"]
    tol = expect.get("score_tol", 0.0001)
    ok2 = (sr["mean_r"] is not None and sm["mean_r"] is not None
           and abs(sr["mean_r"] - expect["score"]) <= tol and abs(sm["mean_r"] - sr["mean_r"]) <= tol
           and sr["envs"] == sm["envs"] == expect["envs"])
    g["E2_score_unchanged"] = {"value": {"raw": sr["mean_r"], "mgha": sm["mean_r"], "envs": sm["envs"]},
                               "held": ok2}
    d = res["env_r_max_abs_diff"]
    g["E3_every_env_r_unchanged"] = {"value": d, "held": d is not None and res["env_r_sets_equal"]
                                     and d <= expect.get("r_tol", 0.0001)}
    r = res["rmse"]
    g["E4_rmse_below_level_only"] = {"value": {"mgha": r["mgha"]["rmse"], "level_only": r["level_only"]["rmse"]},
                                     "held": r["mgha"]["rmse"] < r["level_only"]["rmse"]}
    g["E5_location_level_beats_recent_mean"] = {
        "value": {"level_only": r["level_only"]["rmse"], "recent_mean": r["recent_mean"]["rmse"]},
        "held": r["level_only"]["rmse"] < r["recent_mean"]["rmse"]}
    return g


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("locate")
    p.add_argument("--data-dir", default="/data")
    p = sub.add_parser("seen")
    p.add_argument("--trait", required=True)
    p.add_argument("--template", required=True)
    p = sub.add_parser("write")
    p.add_argument("--template", required=True)
    p.add_argument("--pred", required=True, help="CSV (or URL) with Env, Hybrid and a value column")
    p.add_argument("--col", default=None, help="value column (default Yield_Mg_ha or the first other)")
    p.add_argument("--out", required=True)
    p.add_argument("--fill", choices=("env_mean",), default=None)
    p = sub.add_parser("mgha")
    p.add_argument("--trait", required=True)
    p.add_argument("--template", required=True)
    p.add_argument("--pred", required=True, help="CSV (or URL) with Env, Hybrid and a value column")
    p.add_argument("--col", default=None)
    p.add_argument("--out", required=True)
    p.add_argument("--shrink", type=float, default=SHRINK)
    p = sub.add_parser("validate")
    p.add_argument("--template", required=True)
    p.add_argument("--sub", required=True)
    p = sub.add_parser("score")
    p.add_argument("--sub", required=True)
    p.add_argument("--observed", required=True)
    for name in ("dryrun", "dryrun-mgha"):
        p = sub.add_parser(name)
        p.add_argument("--data-dir", default="/data")
        p.add_argument("--out-dir", default="/out")
        p.add_argument("--pred", required=True)
        p.add_argument("--col", required=True)
        p.add_argument("--expect", default="", help="JSON with the stated dry-run figures")
        p.add_argument("--name", default="g2f_entry_" + name.replace("-", "_"))
    a = ap.parse_args(argv)

    if a.cmd == "locate":
        rel = find_release(a.data_dir)
        out = {r: {"path": p, "years_in_name": name_years(p)} for r, p in rel.items()}
    elif a.cmd == "seen":
        out = seen_share(a.trait, a.template)
        out["decision"] = decide(out["share_in_last_year"])
    elif a.cmd == "write":
        work = os.path.dirname(os.path.abspath(a.out))
        out = write_submission(a.template, read_values(fetch(a.pred, work), a.col), a.out, a.fill)
        out["validate"] = validate_submission(a.template, a.out)
    elif a.cmd == "mgha":
        work = os.path.dirname(os.path.abspath(a.out))
        preds = read_values(fetch(a.pred, work), a.col)
        mg, plan, info = mgha_predictions(a.trait, a.template, preds, a.shrink)
        out = write_submission(a.template, mg, a.out)
        out["validate"] = validate_submission(a.template, a.out)
        out["rescale"] = info
        out["plan"] = {k: v for k, v in plan.items() if k != "envs"}
    elif a.cmd == "validate":
        out = validate_submission(a.template, a.sub)
    elif a.cmd == "score":
        out = score_submission(a.sub, a.observed)
    else:
        expect = None
        if a.expect:
            with open(a.expect, encoding="utf-8") as fh:
                expect = json.load(fh)
        run = dryrun if a.cmd == "dryrun" else dryrun_mgha
        out = run(a.data_dir, a.out_dir, a.pred, a.col, expect)
        with open(os.path.join(a.out_dir, a.name + ".json"), "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=1, sort_keys=True)
    print(json.dumps(out, indent=1, sort_keys=True))
    if a.cmd in ("validate", "write", "mgha") and not out.get("ok", out.get("validate", {}).get("ok", True)):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
