# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
"""g2f_release_census 0.1.0: names-and-counts census of a Genomes to Fields GxE competition release.

Reads every file in a data folder and reports, without summarising any yield value:
  - file names, sizes and SHA-256, and a role guessed from the file name (trait, template, ...);
  - for each CSV: its columns, row count, environments, years, locations, location prefixes
    (state or province codes) and hybrids;
  - for the training trait file: how many rows have a numeric yield cell, and which environments,
    hybrids, locations and parents those rows cover;
  - for the submission template: how many (Env, Hybrid) pairs have a hybrid, a location, a
    hybrid-at-location and both parents already seen in training rows with a yield, and how many
    hybrids are genotyped;
  - for a numeric genotype file: orientation, taxa and marker counts; for a VCF: sample and
    variant-line counts;
  - for an observed-values file (released after a competition): how many template pairs have an
    observation and how many environments have at least 3 observed pairs (the scoring minimum).
Whether a cell holds a number is checked; no value is averaged, ranked or printed.
Optionally compares the counts with stated figures (--expect JSON). Standard library only.
"""
import argparse
import csv
import hashlib
import json
import math
import os
import sys
import urllib.request

VERSION = "0.1.0"
# (role, substrings of the lower-case file name); the first match wins.
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
    ("inbreds", ("key_inbreds",)),
)
YIELD_COL = "Yield_Mg_ha"
MIN_OBS = 3


def role_of(name):
    low = os.path.basename(name).lower()
    for role, pats in ROLES:
        if any(p in low for p in pats):
            return role
    return "other"


def split_of(name):
    low = name.lower()
    if "testing" in low:
        return "testing"
    if "training" in low:
        return "training"
    return None


def env_year(env):
    tail = str(env).strip().rsplit("_", 1)[-1]
    return int(tail) if len(tail) == 4 and tail.isdigit() else None


def env_location(env):
    env = str(env).strip()
    return env.rsplit("_", 1)[0] if env_year(env) is not None else env


def loc_prefix(loc):
    loc = str(loc).strip()
    return loc[:2].upper() if len(loc) >= 2 else loc.upper()


def parents(hybrid):
    """(parent1, parent2) from a 'P1/P2' hybrid name, else None."""
    parts = [p.strip() for p in str(hybrid).split("/")]
    if len(parts) == 2 and all(parts):
        return parts[0], parts[1]
    return None


def is_number(text):
    try:
        x = float(text)
    except (TypeError, ValueError):
        return False
    return not (math.isnan(x) or math.isinf(x))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def env_summary(envs):
    envs = sorted(envs)
    locs = {env_location(e) for e in envs}
    prefixes = {}
    for e in envs:
        p = loc_prefix(env_location(e))
        prefixes[p] = prefixes.get(p, 0) + 1
    years = sorted({y for y in (env_year(e) for e in envs) if y is not None})
    return {"envs": len(envs), "locations": len(locs), "years": years,
            "envs_without_year": sum(1 for e in envs if env_year(e) is None),
            "envs_by_prefix": dict(sorted(prefixes.items()))}


def csv_census(path):
    """(summary dict, detail dict of sets) for one CSV. Detail keeps the names for cross-file counts."""
    with open(path, encoding="utf-8-sig", errors="replace", newline="") as fh:
        reader = csv.reader(fh)
        header = [h.strip() for h in next(reader, [])]
        idx = {h: i for i, h in enumerate(header)}
        ie, ih, iy, iv = idx.get("Env"), idx.get("Hybrid"), idx.get("Year"), idx.get(YIELD_COL)
        rows = short = 0
        envs, hybrids, pairs, years = set(), set(), set(), set()
        f_envs, f_hybrids, f_pairs, f_lochyb = set(), set(), set(), set()
        f_year_hybrids = {}
        filled = 0
        for row in reader:
            if not row or all(not c.strip() for c in row):
                continue
            rows += 1
            if len(row) < len(header):
                short += 1

            def cell(i):
                return row[i].strip() if i is not None and i < len(row) else ""

            e, h = cell(ie), cell(ih)
            if e:
                envs.add(e)
            if h:
                hybrids.add(h)
            if e and h:
                pairs.add((e, h))
            if cell(iy):
                years.add(cell(iy))
            if iv is not None and is_number(cell(iv)):
                filled += 1
                if e:
                    f_envs.add(e)
                if h:
                    f_hybrids.add(h)
                if e and h:
                    f_pairs.add((e, h))
                    f_lochyb.add((env_location(e), h))
                yr = cell(iy)
                yr = int(yr) if len(yr) == 4 and yr.isdigit() else env_year(e)
                if h and yr is not None:
                    f_year_hybrids.setdefault(yr, set()).add(h)
    summary = {"columns": header, "rows": rows, "short_rows": short}
    if ie is not None:
        summary["env"] = env_summary(envs)
    if ih is not None:
        summary["hybrids"] = len(hybrids)
    if ie is not None and ih is not None:
        summary["env_hybrid_pairs"] = len(pairs)
    if iy is not None:
        summary["year_values"] = sorted(years)
    if iv is not None:
        summary["rows_with_numeric_yield"] = filled
        summary["envs_with_numeric_yield"] = len(f_envs)
        summary["hybrids_with_numeric_yield"] = len(f_hybrids)
        summary["pairs_with_numeric_yield"] = len(f_pairs)
    detail = {"envs": envs, "hybrids": hybrids, "pairs": pairs, "f_envs": f_envs,
              "f_hybrids": f_hybrids, "f_pairs": f_pairs, "f_lochyb": f_lochyb,
              "f_year_hybrids": f_year_hybrids}
    return summary, detail


def year_overlap(year_hybrids):
    """Per year (rows with a numeric yield): hybrids, and how many were already in the year before
    and in any earlier year. Shows whether a trial cycle repeats its hybrids in the next season."""
    out, earlier = [], set()
    for y in sorted(year_hybrids):
        hs = year_hybrids[y]
        prev = year_hybrids.get(y - 1, set())
        out.append({"year": y, "hybrids": len(hs), "in_previous_year": len(hs & prev),
                    "in_any_earlier_year": len(hs & earlier)})
        earlier |= hs
    return out


def _split(line, sep):
    line = line.rstrip("\r\n")
    return line.split() if sep is None else line.split(sep)


def numeric_census(path, known=()):
    """(summary, set of taxa) for a delimited numeric genotype file in either orientation."""
    known = set(known)
    header, sep, names, widths, skipped = None, None, [], set(), 0
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            s = line.strip()
            if header is None:
                if not s or s.lower().startswith("<numeric"):
                    skipped += 1
                    continue
                sep = "\t" if "\t" in line else ("," if "," in line else None)
                header = _split(line, sep)
                continue
            if not s:
                continue
            parts = _split(line, sep)
            names.append(parts[0].strip())
            widths.add(len(parts))
    header = header or [""]
    cols = [c.strip() for c in header[1:]]
    in_rows, in_cols = len(set(names) & known), len(set(cols) & known)
    transposed = in_cols > in_rows
    taxa = cols if transposed else names
    return ({"header_lines_skipped": skipped, "first_header_cell": header[0].strip(),
             "data_rows": len(names), "header_columns": len(cols), "row_widths": sorted(widths),
             "orientation": "taxa_in_columns" if transposed else "taxa_in_rows",
             "taxa": len(taxa), "distinct_taxa": len(set(taxa)),
             "markers": len(names) if transposed else len(cols),
             "taxa_matching_trait_hybrids": max(in_rows, in_cols)}, set(taxa))


def vcf_census(path):
    meta = variants = 0
    samples = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith("##"):
                meta += 1
            elif line.startswith("#"):
                samples = [s.strip() for s in line.rstrip("\r\n").split("\t")[9:]]
            elif line.strip():
                variants += 1
    return {"meta_lines": meta, "samples": len(samples), "distinct_samples": len(set(samples)),
            "variant_lines": variants}, set(samples)


def line_count(path):
    n = 0
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.strip():
                n += 1
    return n


def cross_counts(trait, template, taxa=None, observed=None):
    """Flat counts linking the template (and observed file) to the training trait file."""
    out = {}
    if trait is not None:
        out["trait_year_overlap"] = year_overlap(trait["f_year_hybrids"])
    if template is None:
        return out
    pairs = template["pairs"]
    out["template_pairs"] = len(pairs)
    if trait is not None:
        seen_h = trait["f_hybrids"]
        seen_loc = {env_location(e) for e in trait["f_envs"]}
        seen_par = set()
        for h in seen_h:
            p = parents(h)
            if p:
                seen_par.update(p)
        th = template["hybrids"]
        out["template_hybrids_seen"] = len(th & seen_h)
        out["template_pairs_hybrid_seen"] = sum(1 for e, h in pairs if h in seen_h)
        out["template_pairs_location_seen"] = sum(1 for e, h in pairs if env_location(e) in seen_loc)
        out["template_pairs_hybrid_seen_at_location"] = sum(
            1 for e, h in pairs if (env_location(e), h) in trait["f_lochyb"])
        both = one = 0
        for e, h in pairs:
            p = parents(h)
            k = 0 if p is None else (p[0] in seen_par) + (p[1] in seen_par)
            both += k == 2
            one += k == 1
        out["template_pairs_both_parents_seen"] = both
        out["template_pairs_one_parent_seen"] = one
        out["template_pairs_unparsed_hybrid"] = sum(1 for e, h in pairs if parents(h) is None)
        out["template_envs_in_training"] = len(template["envs"] & trait["envs"])
        years = trait["f_year_hybrids"]
        if years:
            last = max(years)
            out["last_training_year"] = last
            out["template_hybrids_in_last_training_year"] = len(th & years[last])
            out["template_pairs_hybrid_in_last_training_year"] = sum(
                1 for e, h in pairs if h in years[last])
    if taxa is not None:
        out["template_hybrids_genotyped"] = len(template["hybrids"] & taxa)
        out["template_pairs_genotyped"] = sum(1 for e, h in pairs if h in taxa)
        if trait is not None:
            out["geno_taxa_outside_trait_and_template"] = len(
                taxa - trait["hybrids"] - template["hybrids"])
    if observed is not None:
        obs = observed["f_pairs"]
        out["template_pairs_with_observation"] = len(pairs & obs)
        out["observed_pairs_outside_template"] = len(obs - pairs)
        per_env = {}
        for e, h in pairs & obs:
            per_env[e] = per_env.get(e, 0) + 1
        out["observed_envs_with_3plus"] = sum(1 for n in per_env.values() if n >= MIN_OBS)
        out["template_envs_without_3_observed"] = sorted(
            e for e in template["envs"] if per_env.get(e, 0) < MIN_OBS)
    return out


def flatten(results):
    """Flat {key: number} view used for --expect checks."""
    flat = dict(results.get("cross", {}))
    for role in ("trait", "template", "observed"):
        s = results.get("by_role", {}).get(role)
        if not s:
            continue
        flat[role + "_rows"] = s.get("rows")
        if "env" in s:
            flat[role + "_envs"] = s["env"]["envs"]
            flat[role + "_locations"] = s["env"]["locations"]
        if "hybrids" in s:
            flat[role + "_hybrids"] = s["hybrids"]
        for k in ("rows_with_numeric_yield", "envs_with_numeric_yield", "hybrids_with_numeric_yield",
                  "pairs_with_numeric_yield"):
            if k in s:
                flat[role + "_" + k] = s[k]
    g = results.get("by_role", {}).get("geno_numeric")
    if g:
        flat["geno_taxa"] = g["distinct_taxa"]
        flat["geno_markers"] = g["markers"]
    return flat


def check(flat, expect):
    """{key: {value, spec, held}} for specs {"eq": n} or {"min": a, "max": b} (either bound optional)."""
    res = {}
    for key, spec in expect.items():
        v = flat.get(key)
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            held = False
        elif "eq" in spec:
            held = v == spec["eq"]
        else:
            held = spec.get("min", -math.inf) <= v <= spec.get("max", math.inf)
        res[key] = {"value": v, "spec": {k: spec[k] for k in spec if k in ("eq", "min", "max")},
                    "source": spec.get("source", ""), "held": bool(held)}
    return res


def fetch(base, rels, data_dir):
    for rel in rels:
        path = os.path.join(data_dir, os.path.basename(rel))
        if not os.path.exists(path):
            urllib.request.urlretrieve(base.rstrip("/") + "/" + rel.lstrip("/"), path)
            print("downloaded", rel, os.path.getsize(path), "bytes", flush=True)


def census(data_dir):
    files, details, by_role = [], {}, {}
    paths = []
    for root, dirs, names in os.walk(data_dir):
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))
        for n in sorted(names):
            if not n.startswith("."):
                paths.append(os.path.join(root, n))
    geno_paths = []
    for p in paths:
        rel = os.path.relpath(p, data_dir).replace(os.sep, "/")
        rec = {"file": rel, "bytes": os.path.getsize(p), "sha256": sha256(p), "role": role_of(rel),
               "split": split_of(rel)}
        if rel.lower().endswith(".csv"):
            rec["csv"], details[rel] = csv_census(p)
        elif rec["role"] == "vcf":
            rec["vcf"], details[rel] = vcf_census(p)
        elif rec["role"] == "geno_numeric":
            geno_paths.append((rec, p))
        else:
            rec["nonblank_lines"] = line_count(p)
        files.append(rec)

    def pick(role):
        cands = [r for r in files if r["role"] == role and "csv" in r]
        return max(cands, key=lambda r: r["bytes"]) if cands else None

    trait_rec, tmpl_rec, obs_rec = pick("trait"), pick("template"), pick("observed")
    trait = details.get(trait_rec["file"]) if trait_rec else None
    taxa = None
    for rec, p in geno_paths:
        rec["numeric"], t = numeric_census(p, trait["hybrids"] if trait else ())
        if taxa is None:
            taxa = t
            by_role["geno_numeric"] = rec["numeric"]
    if taxa is None:
        for rec in files:
            if rec["role"] == "vcf" and "vcf" in rec:
                taxa = details[rec["file"]]
                break
    for role, rec in (("trait", trait_rec), ("template", tmpl_rec), ("observed", obs_rec)):
        if rec:
            by_role[role] = rec["csv"]
    cross = cross_counts(trait, details.get(tmpl_rec["file"]) if tmpl_rec else None, taxa,
                         details.get(obs_rec["file"]) if obs_rec else None)
    return {"version": VERSION, "data_dir_files": len(files), "files": files,
            "roles_used": {k: (v["file"] if v else None) for k, v in
                           (("trait", trait_rec), ("template", tmpl_rec), ("observed", obs_rec))},
            "by_role": by_role, "cross": cross}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data-dir", default="/data")
    ap.add_argument("--out-dir", default="/out")
    ap.add_argument("--base", default="", help="download base URL for --files (optional)")
    ap.add_argument("--files", nargs="*", default=[], help="paths under --base to fetch if missing")
    ap.add_argument("--expect", default="", help="JSON file of stated figures to compare")
    ap.add_argument("--name", default="g2f_release_census")
    args = ap.parse_args(argv)
    if args.base and args.files:
        fetch(args.base, args.files, args.data_dir)
    res = census(args.data_dir)
    res["flat"] = flatten(res)
    if args.expect:
        with open(args.expect, encoding="utf-8") as fh:
            exp = json.load(fh)
        res["expect"] = check(res["flat"], exp.get("checks", exp))
        res["expect_held"] = sum(1 for v in res["expect"].values() if v["held"])
        res["expect_total"] = len(res["expect"])
    os.makedirs(args.out_dir, exist_ok=True)
    with open(os.path.join(args.out_dir, args.name + ".json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, sort_keys=True)
    for rec in res["files"]:
        print("file", rec["file"], rec["bytes"], rec["role"], flush=True)
    print(json.dumps({"flat": res["flat"], "expect": res.get("expect")}, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
