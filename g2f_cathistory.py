# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
"""g2f-cathistory 0.1.0: per-season hybrid categories in the G2F competition data.

For every season Y from 2015 on, each (Env, Hybrid) pair with a numeric yield is put in one of four
categories against all hybrids with a numeric yield in seasons before Y: 'seen' (the hybrid itself was
grown before), 'new_both', 'new_one' or 'new_none' (how many of the parents named in "PARENT1/PARENT2"
are parents of some earlier hybrid). It also writes a table of every parent line with the seasons it was
grown in, checks the hybrid names against the trait file's own parent columns, and looks up the 2026
core check hybrids in the training seasons. Standard library only. Prints counts and names, never a
yield value.
"""
import argparse
import csv
import json
import math
import os
from collections import Counter, defaultdict

VERSION = "0.1.0"
CATEGORIES = ("seen", "new_both", "new_one", "new_none")
# The 19 named (non-commercial) core checks of the 2026-2027 G2F GxE experiments, as listed on
# genomes2fields.org/about/project-overview/ (read 2026-11-09).
CHECKS_2026 = ("2369/LH123HT", "B14A/OH43", "B37/H95", "B73/MO17", "B73/PHN82", "CG119/CG108",
               "LH195/PHZ51", "LH244/PHK76", "LH287/LH244", "PH24E/LH244", "PHB47/PHN82",
               "PHB47/PHZ51", "PHG29/PHG47", "PHG39/PHN82", "PHR03/LH244", "PHRE1/PHTD5",
               "TX777/LH195", "01DIB2/LH287", "01CSI6/LH287")
# Pair counts by category printed by this repository's g2f-newshrink 0.1.0 run.
REF_2024 = {"seen": 1172, "new_one": 7676, "new_both": 638}
REF_2022 = {"seen": 816, "new_one": 9126, "new_both": 1896}
EVEN = ("2016", "2018", "2020", "2022", "2024")
ODD = ("2017", "2019", "2021", "2023")


def is_number(text):
    try:
        v = float(str(text).strip())
    except ValueError:
        return False
    return not (math.isnan(v) or math.isinf(v))


def parents(hybrid):
    """The parent names on either side of '/' in a hybrid name (empty parts dropped)."""
    return tuple(p.strip() for p in str(hybrid).split("/") if p.strip())


def categorize(hybrid, train, pool):
    if hybrid in train:
        return "seen"
    k = sum(1 for p in parents(hybrid) if p in pool)
    return "new_both" if k >= 2 else ("new_one" if k == 1 else "new_none")


def env_year(env):
    tail = str(env).rsplit("_", 1)[-1]
    return int(tail) if tail.isdigit() else None


def find_file(data_dir, key):
    hits = []
    for root, _dirs, files in os.walk(data_dir):
        for name in files:
            low = name.lower()
            if key in low and not low.endswith(".zip"):
                hits.append(os.path.join(root, name))
    if not hits:
        raise FileNotFoundError("no file with %r in %s" % (key, data_dir))
    return sorted(hits)[0]


def read_rows(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        reader.fieldnames = [str(c).strip() for c in reader.fieldnames]
        for row in reader:
            yield {k: (v or "").strip() for k, v in row.items() if k is not None}


def load_records(trait_path, observed_path=None):
    """(year, env, hybrid, parent1, parent2, has_yield) for the trait file and the observed file."""
    recs = []
    for row in read_rows(trait_path):
        env, hyb = row.get("Env", ""), row.get("Hybrid", "")
        if not env or not hyb:
            continue
        year = None
        if is_number(row.get("Year", "")):
            year = int(float(row["Year"]))
        if year is None:
            year = env_year(env)
        if year is None:
            continue
        recs.append((year, env, hyb, row.get("Hybrid_Parent1", ""), row.get("Hybrid_Parent2", ""),
                     is_number(row.get("Yield_Mg_ha", ""))))
    if observed_path:
        for row in read_rows(observed_path):
            env, hyb = row.get("Env", ""), row.get("Hybrid", "")
            year = env_year(env)
            if not env or not hyb or year is None:
                continue
            recs.append((year, env, hyb, "", "", is_number(row.get("Yield_Mg_ha", ""))))
    return recs


def season_table(recs, first=2015):
    pairs = defaultdict(set)
    hybrids = defaultdict(set)
    for year, env, hyb, _p1, _p2, ok in recs:
        if ok:
            pairs[year].add((env, hyb))
            hybrids[year].add(hyb)
    out = {}
    for year in sorted(pairs):
        if year < first:
            continue
        train = set()
        for y in pairs:
            if y < year:
                train |= hybrids[y]
        pool = {p for h in train for p in parents(h)}
        cat_of = {h: categorize(h, train, pool) for h in hybrids[year]}
        by_pair = Counter(cat_of[h] for _e, h in pairs[year])
        by_hyb = Counter(cat_of.values())
        n = len(pairs[year])
        per_parent = Counter(p for h in hybrids[year] for p in set(parents(h)))
        seen_parent = Counter()
        for _e, h in pairs[year]:
            if cat_of[h] == "new_one":
                for p in parents(h):
                    if p in pool:
                        seen_parent[p] += 1
        n_one = by_pair.get("new_one", 0)
        top_seen = seen_parent.most_common(1)
        out[str(year)] = {
            "pairs": n, "hybrids": len(hybrids[year]), "train_hybrids": len(train),
            "parent_pool": len(pool),
            "pairs_by_category": {c: by_pair.get(c, 0) for c in CATEGORIES},
            "hybrids_by_category": {c: by_hyb.get(c, 0) for c in CATEGORIES},
            "share_by_category": {c: round(by_pair.get(c, 0) / n, 4) if n else None
                                  for c in CATEGORIES},
            "unparsed_pairs": sum(1 for _e, h in pairs[year] if len(parents(h)) != 2),
            "distinct_parents": len(per_parent),
            "top_parents_by_hybrids": [[p, c] for p, c in
                                       sorted(per_parent.items(), key=lambda t: (-t[1], t[0]))[:5]],
            "new_one_top_seen_parent": ([top_seen[0][0], round(top_seen[0][1] / n_one, 4)]
                                        if top_seen and n_one else None),
        }
    return out


def parent_table(recs):
    info = defaultdict(lambda: {"hybrids": set(), "pairs": set(), "years": set()})
    for year, env, hyb, _p1, _p2, ok in recs:
        if not ok:
            continue
        for p in set(parents(hyb)):
            info[p]["hybrids"].add(hyb)
            info[p]["pairs"].add((env, hyb))
            info[p]["years"].add(year)
    rows = []
    for p in sorted(info):
        ys = sorted(info[p]["years"])
        rows.append({"parent": p, "hybrids": len(info[p]["hybrids"]),
                     "env_hybrid_pairs": len(info[p]["pairs"]), "first_year": ys[0],
                     "last_year": ys[-1], "years": ";".join(str(y) for y in ys)})
    return rows


def name_check(recs):
    """Distinct (hybrid, parent1, parent2) combinations in the trait file with both parent columns
    filled: does splitting the hybrid name at '/' give the same two parents?"""
    combos = {(h, p1, p2) for _y, _e, h, p1, p2, _ok in recs if p1 and p2}
    bad = sorted(c for c in combos if sorted(parents(c[0])) != sorted([c[1], c[2]]))
    n = len(combos)
    return {"combos": n, "agree": n - len(bad), "disagree": len(bad),
            "agree_share": round((n - len(bad)) / n, 4) if n else None,
            "disagree_examples": [list(c) for c in bad[:10]]}


def check_lookup(recs, checks=CHECKS_2026):
    years = defaultdict(set)
    for year, _e, hyb, _p1, _p2, ok in recs:
        if ok:
            years[hyb].add(year)
    upper = defaultdict(set)
    for h, ys in years.items():
        upper[h.upper()] |= ys
    out = []
    for c in checks:
        a = parents(c)
        swapped = "/".join(reversed(a)) if len(a) == 2 else c
        if c in years:
            match, ys = "exact", years[c]
        elif c.upper() in upper:
            match, ys = "case", upper[c.upper()]
        elif swapped.upper() in upper:
            match, ys = "swapped", upper[swapped.upper()]
        else:
            match, ys = "none", set()
        out.append({"check": c, "match": match, "years": sorted(ys)})
    counts = Counter(r["match"] for r in out)
    return {"checks": out, "exact": counts.get("exact", 0), "case": counts.get("case", 0),
            "swapped": counts.get("swapped", 0), "none": counts.get("none", 0)}


def within(value, target, tol):
    return value is not None and abs(value - target) <= tol * target


def grade(seasons, checks, names):
    g = {}

    def cats(year):
        return seasons.get(year, {}).get("pairs_by_category")

    c24, c22 = cats("2024"), cats("2022")
    g["K1_2024_counts_match_newshrink"] = {
        "value": c24, "held": bool(c24) and c24.get("new_none") == 0
        and all(within(c24.get(k), t, 0.01) for k, t in REF_2024.items())}
    g["K2_2022_counts_match_newshrink"] = {
        "value": c22, "held": bool(c22) and all(within(c22.get(k), t, 0.02)
                                                for k, t in REF_2022.items())}
    shares = [(y, s["share_by_category"]["new_none"]) for y, s in sorted(seasons.items())
              if s["share_by_category"]["new_none"] is not None]
    worst = max(shares, key=lambda t: t[1]) if shares else None
    g["H1_new_none_at_most_5pct_every_season"] = {
        "value": worst, "held": worst is not None and worst[1] <= 0.05}
    largest = {}
    for y in EVEN:
        c = cats(y)
        largest[y] = max(CATEGORIES, key=lambda k: c.get(k, 0)) if c else None
    g["H2_new_one_largest_in_even_seasons"] = {
        "value": largest, "held": all(v == "new_one" for v in largest.values())}
    seen = {y: seasons.get(y, {}).get("share_by_category", {}).get("seen") for y in ODD}
    g["H3_seen_at_least_75pct_in_odd_seasons"] = {
        "value": seen, "held": all(v is not None and v >= 0.75 for v in seen.values())}
    g["H4_at_least_15_checks_exact"] = {"value": checks.get("exact"),
                                        "held": (checks.get("exact") or 0) >= 15}
    top = seasons.get("2024", {}).get("top_parents_by_hybrids", [])
    top2 = {str(p).upper() for p, _c in top[:2]}
    g["H5_PHP02_LH287_top_two_2024"] = {"value": top[:2], "held": top2 == {"PHP02", "LH287"}}
    share = names.get("agree_share")
    g["H6_name_split_agrees_99pct"] = {"value": share, "held": share is not None and share >= 0.99}
    return g


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data-dir", default="/data")
    ap.add_argument("--out-dir", default="/out")
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    trait = find_file(args.data_dir, "training_trait")
    try:
        observed = find_file(args.data_dir, "testing_observed")
    except FileNotFoundError:
        observed = None
    print("trait", os.path.basename(trait), "observed",
          os.path.basename(observed) if observed else None, flush=True)
    recs = load_records(trait, observed)
    seasons = season_table(recs)
    names = name_check(recs)
    checks = check_lookup(recs)
    ptab = parent_table(recs)
    res = {"version": VERSION, "files": [os.path.basename(trait)] +
           ([os.path.basename(observed)] if observed else []),
           "seasons": seasons, "name_check": names, "checks_2026": checks,
           "parents": len(ptab)}
    res["grades"] = grade(seasons, checks, names)
    res["held"] = sum(1 for v in res["grades"].values() if v["held"])
    res["graded"] = len(res["grades"])
    with open(os.path.join(args.out_dir, "g2f_cathistory.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, sort_keys=True)
    with open(os.path.join(args.out_dir, "g2f_parents_2014_2024.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["parent", "hybrids", "env_hybrid_pairs", "first_year",
                                           "last_year", "years"])
        w.writeheader()
        w.writerows(ptab)
    print(json.dumps(res, indent=1, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
