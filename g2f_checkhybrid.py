# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
"""g2f_checkhybrid 0.1.0: decompose the 2024 G2F within-environment score by seen vs new hybrids.

Reads only the baseline run's committed, immutable per-row prediction table
(results/g2f_2024_predictions.csv at tag v0.1.0: columns Env, Hybrid, obs, M0, M1, M2, M3), classifies
each row as "seen" (M0 != 0, a hybrid grown in 2014-2023) or "new" (M0 == 0), and rescores the mean
within-environment Pearson r of each model on each subset. No new model is fit. Needs numpy only.
"""
import argparse
import csv
import io
import json
import os
import urllib.request

import numpy as np

CSV_URL = ("https://raw.githubusercontent.com/munimtechnologies/g2f-gxe-baselines/v0.1.0/"
           "results/g2f_2024_predictions.csv")
MODELS = ("M0", "M1", "M2", "M3")
MIN_ROWS = 3
# baseline 0.1.0 all-rows 2024 scores, reproduced as a sanity gate (must match within TOL)
BASELINE = {"M0": 0.2353, "M1": 0.2386, "M2": 0.2802, "M3": 0.2799}
TOL = 0.005


def fetch(url, out_dir):
    """Download the prediction table once; cache it under out_dir so a rerun is offline-friendly."""
    local = os.path.join(out_dir, "g2f_2024_predictions.csv")
    if not os.path.exists(local):
        with urllib.request.urlopen(url, timeout=60) as resp:
            data = resp.read()
        with open(local, "wb") as fh:
            fh.write(data)
    with open(local, "r", encoding="utf-8") as fh:
        return parse(fh.read())


def parse(text):
    """-> list of dicts {Env, Hybrid, obs(float|None), M0..M3(float)}."""
    rows = []
    for r in csv.DictReader(io.StringIO(text)):
        obs = r.get("obs", "")
        try:
            obs = float(obs)
            if not np.isfinite(obs):
                obs = None
        except (ValueError, TypeError):
            obs = None
        row = {"Env": (r["Env"] or "").strip(), "Hybrid": (r.get("Hybrid") or "").strip(), "obs": obs}
        for m in MODELS:
            row[m] = float(r[m])
        rows.append(row)
    return rows


def pearson(pred, obs):
    """Pearson r, or None if fewer than MIN_ROWS points or no variance in either series."""
    pred = np.asarray(pred, dtype=float)
    obs = np.asarray(obs, dtype=float)
    if len(pred) < MIN_ROWS or pred.std() == 0 or obs.std() == 0:
        return None
    return float(np.corrcoef(pred, obs)[0, 1])


def subset_mask(rows, which):
    """Boolean list: 'all', 'seen' (M0 != 0) or 'new' (M0 == 0), restricted to finite obs."""
    out = []
    for r in rows:
        ok = r["obs"] is not None
        if which == "seen":
            ok = ok and r["M0"] != 0.0
        elif which == "new":
            ok = ok and r["M0"] == 0.0
        out.append(ok)
    return out


def env_scores(rows, which):
    """{env: {n, M0..M3 r or None}} for one subset."""
    mask = subset_mask(rows, which)
    sel = [r for r, m in zip(rows, mask) if m]
    envs = {}
    for r in sel:
        envs.setdefault(r["Env"], []).append(r)
    out = {}
    for env, ers in envs.items():
        obs = [r["obs"] for r in ers]
        rec = {"n": len(ers)}
        for m in MODELS:
            rec[m] = pearson([r[m] for r in ers], obs)
        out[env] = rec
    return out


def mean_defined(scores, model):
    """Mean r over environments where `model` is defined, and that count."""
    vals = [s[model] for s in scores.values() if s[model] is not None]
    return (round(float(np.mean(vals)), 4) if vals else None), len(vals)


def mean_both(scores, a, b):
    """Means of a and b over environments where BOTH are defined (fair comparison)."""
    pairs = [(s[a], s[b]) for s in scores.values() if s[a] is not None and s[b] is not None]
    if not pairs:
        return None, None, 0
    va = round(float(np.mean([p[0] for p in pairs])), 4)
    vb = round(float(np.mean([p[1] for p in pairs])), 4)
    return va, vb, len(pairs)


def analyze(rows):
    """Full decomposition + grading."""
    scores = {w: env_scores(rows, w) for w in ("all", "seen", "new")}

    # built-in checks
    new_violations = sum(1 for r in rows if r["M0"] == 0.0 and abs(r["M2"] - r["M1"]) > 1e-6)
    overall = {m: mean_defined(scores["all"], m) for m in MODELS}
    repro_ok = all(overall[m][0] is not None and abs(overall[m][0] - BASELINE[m]) <= TOL
                   for m in MODELS)

    means = {w: {m: mean_defined(scores[w], m) for m in MODELS} for w in ("all", "seen", "new")}

    # P1: seen subset defined (>=3 seen rows with obs variance) in >= 15 envs
    seen_defined_envs = sum(1 for s in scores["seen"].values()
                            if s["n"] >= MIN_ROWS and s["M0"] is not None)
    p1 = seen_defined_envs >= 15
    # P2: mean M0 r on seen > 0.40
    m0_seen = means["seen"]["M0"][0]
    p2 = m0_seen is not None and m0_seen > 0.40
    # P3: mean M2 r on new > 0.10
    m2_new = means["new"]["M2"][0]
    p3 = m2_new is not None and m2_new > 0.10
    # P4: |mean M2 - mean M0| on seen (common envs) < 0.10
    m2s, m0s, n_p4 = mean_both(scores["seen"], "M2", "M0")
    p4 = m2s is not None and abs(m2s - m0s) < 0.10
    # H1: mean M2 > mean M1 on seen (common envs)
    m2h, m1h, n_h1 = mean_both(scores["seen"], "M2", "M1")
    h1 = m2h is not None and m2h > m1h

    decision = ("strengthen genomic signal for new hybrids (parent/tester GCA or marker-by-covariate "
                "reaction norm)" if p3 else
                "model the seen minority plus the environment mean; move effort off per-hybrid genomic GxE")

    return {
        "version": "0.1.0",
        "source": CSV_URL,
        "n_rows_total": len(rows),
        "n_rows_with_obs": sum(1 for r in rows if r["obs"] is not None),
        "n_rows_seen": sum(1 for r in rows if r["obs"] is not None and r["M0"] != 0.0),
        "n_rows_new": sum(1 for r in rows if r["obs"] is not None and r["M0"] == 0.0),
        "new_m2_equals_m1_violations": new_violations,
        "overall_mean_within_env_r": {m: {"mean_r": overall[m][0], "envs": overall[m][1]}
                                      for m in MODELS},
        "reproduces_baseline": repro_ok,
        "means": {w: {m: {"mean_r": means[w][m][0], "envs": means[w][m][1]} for m in MODELS}
                  for w in ("all", "seen", "new")},
        "seen_defined_envs": seen_defined_envs,
        "comparisons": {
            "seen_M2_vs_M0": {"M2": m2s, "M0": m0s, "envs": n_p4},
            "seen_M2_vs_M1": {"M2": m2h, "M1": m1h, "envs": n_h1},
        },
        "grading": {
            "P1_seen_defined_ge_15": {"held": bool(p1), "value": seen_defined_envs},
            "P2_M0_seen_gt_0.40": {"held": bool(p2), "value": m0_seen},
            "P3_M2_new_gt_0.10": {"held": bool(p3), "value": m2_new},
            "P4_abs_M2_minus_M0_seen_lt_0.10": {"held": bool(p4),
                                                "value": (round(m2s - m0s, 4) if m2s is not None else None)},
            "H1_M2_gt_M1_seen": {"held": bool(h1),
                                 "value": (round(m2h - m1h, 4) if m2h is not None else None)},
        },
        "decision_next_model": decision,
        "env_scores": {w: {e: scores[w][e] for e in sorted(scores[w])} for w in ("all", "seen", "new")},
    }


def write_env_csv(result, path):
    rows = sorted(set(result["env_scores"]["all"]))
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        head = ["Env"]
        for sub in ("all", "seen", "new"):
            head.append("n_%s" % sub)
            head += ["%s_%s" % (m, sub) for m in MODELS]
        w.writerow(head)
        for env in rows:
            line = [env]
            for sub in ("all", "seen", "new"):
                s = result["env_scores"][sub].get(env)
                if s is None:
                    line += [0] + ["" for _ in MODELS]
                else:
                    line.append(s["n"])
                    line += ["" if s[m] is None else round(s[m], 4) for m in MODELS]
            w.writerow(line)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out-dir", default="/out")
    ap.add_argument("--url", default=CSV_URL)
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    rows = fetch(args.url, args.out_dir)
    result = analyze(rows)
    with open(os.path.join(args.out_dir, "g2f_checkhybrid.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1, sort_keys=True)
    write_env_csv(result, os.path.join(args.out_dir, "g2f_checkhybrid_env_r.csv"))
    print(json.dumps({k: result[k] for k in ("reproduces_baseline", "new_m2_equals_m1_violations",
                                             "means", "grading", "decision_next_model")},
                     indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
