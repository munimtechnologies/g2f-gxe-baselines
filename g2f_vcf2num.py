# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
"""g2f_vcf2num 0.1.0: turn a G2F genotype VCF into the numerical genotype file the chain reads.

Insurance for a release that ships only a VCF. g2f_predict.py (role geno_numeric, found by
g2f_entry.find_release) and g2f_refmodel.R (pattern _numerical.txt) both need the organisers'
TASSEL-style numerical file and stop without it. This writes the same layout as the 2024 file:
a "<Numeric>" line, a "<Marker>" header row, then one tab-separated row per taxon (taxa in rows),
each call coded as the share of non-reference alleles rounded to the nearest half (diploid:
0, 0.5, 1; missing: NA).

Coding note: TASSEL's numerical export scores the major allele instead (1 = homozygous major).
Per marker that is either the same value or 1 - value, so marker variances and the distances
between taxa do not change: the R kernel model (marker filter var > 0.01, Gaussian kernel) and
the z-scored Python ridge fit the same way under either coding.

Filters (defaults fixed before any 2026 data exist): a marker is dropped when more than
--max-missing of the kept taxa have no call, or when its minor allele frequency is below
--min-maf. --max-markers N keeps N of the passing markers evenly spaced in file order
(0 = keep all); the default 2425 is the marker count of the organisers' 2024 numerical file.

Usage: python g2f_vcf2num.py VCF OUT_numerical.txt [--keep trait.csv --keep template.csv]
       [--min-maf 0.01] [--max-missing 0.5] [--max-markers 2425] [--summary out.json]
"""
import argparse
import csv
import gzip
import json
import os
import sys

VERSION = "0.1.0"
MIN_MAF = 0.01
MAX_MISSING = 0.5
MAX_MARKERS = 2425  # markers in 5_Genotype_Data_All_2014_2025_Hybrids_numerical.txt (2024 release)
MISSING = 255
TEXT = {0: "0", 1: "0.5", 2: "1", MISSING: "NA"}


def open_text(path):
    if path.lower().endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return open(path, encoding="utf-8", errors="replace")


def keep_names(paths):
    """Hybrid names from the Hybrid column of each CSV (training trait data, submission template)."""
    names = set()
    for p in paths or ():
        with open(p, newline="", encoding="utf-8-sig", errors="replace") as fh:
            rd = csv.reader(fh)
            header = [h.strip() for h in next(rd, [])]
            if "Hybrid" not in header:
                raise ValueError("no Hybrid column in %s" % p)
            i = header.index("Hybrid")
            for row in rd:
                if len(row) > i and row[i].strip():
                    names.add(row[i].strip())
    return names


def call_code(sample_field, gi):
    """0, 1 or 2 = twice the non-reference allele share, rounded; MISSING when any allele is missing."""
    parts = sample_field.split(":")
    if gi >= len(parts):
        return MISSING
    alleles = parts[gi].strip().replace("|", "/").split("/")
    if any(a in (".", "") for a in alleles):
        return MISSING
    nonref = sum(1 for a in alleles if a != "0")
    return int(round(2.0 * nonref / len(alleles)))


def marker_stats(codes):
    """(share of taxa with no call, minor allele frequency among called taxa)."""
    called = [c for c in codes if c != MISSING]
    n = len(codes)
    miss = (n - len(called)) / n if n else 1.0
    if not called:
        return miss, 0.0
    p = sum(called) / (2.0 * len(called))
    return miss, min(p, 1.0 - p)


def iter_vcf(path, names=None):
    """Yields (None, kept sample names) once, then (marker id, codes) for each data line.

    Samples are kept in file order; a repeated sample name keeps its first column only;
    with names given, only samples in names are kept."""
    keep = None
    with open_text(path) as fh:
        for line in fh:
            if line.startswith("##"):
                continue
            parts = line.rstrip("\r\n").split("\t")
            if line.startswith("#"):
                samples = [s.strip() for s in parts[9:]]
                seen = set()
                keep = []
                for i, s in enumerate(samples):
                    if s in seen or (names is not None and s not in names):
                        continue
                    seen.add(s)
                    keep.append(i)
                if not keep:
                    raise ValueError("no samples kept from %s" % path)
                yield None, [samples[i] for i in keep]
                continue
            if keep is None:
                raise ValueError("data line before the #CHROM header in %s" % path)
            if len(parts) < 10:
                continue
            fmt = parts[8].split(":")
            gi = fmt.index("GT") if "GT" in fmt else 0
            mid = parts[2].strip()
            if mid in ("", "."):
                mid = "%s_%s" % (parts[0].strip(), parts[1].strip())
            yield mid, [call_code(parts[9 + i], gi) if 9 + i < len(parts) else MISSING for i in keep]
    if keep is None:
        raise ValueError("no #CHROM header in %s" % path)


def spread(n, k):
    """k indices out of range(n), evenly spaced in order (all of them when k <= 0 or k >= n)."""
    if k <= 0 or k >= n:
        return list(range(n))
    return [i * n // k for i in range(k)]


def unique_ids(ids):
    seen, out = {}, []
    for m in ids:
        if m in seen:
            seen[m] += 1
            out.append("%s_%d" % (m, seen[m]))
        else:
            seen[m] = 1
            out.append(m)
    return out


def convert(vcf, out_path, names=None, min_maf=MIN_MAF, max_missing=MAX_MISSING,
            max_markers=MAX_MARKERS):
    if not os.path.basename(out_path).lower().endswith("_numerical.txt"):
        raise ValueError("the output name must end in _numerical.txt so both legs of the chain find it")
    passing, total, samples = [], 0, None
    for mid, codes in iter_vcf(vcf, names):
        if mid is None:
            samples = codes
            continue
        miss, maf = marker_stats(codes)
        if miss <= max_missing and maf >= min_maf:
            passing.append(total)
        total += 1
    chosen = set(passing[i] for i in spread(len(passing), max_markers))
    if not chosen:
        raise ValueError("no marker passed the filters")
    ids, cols, j = [], [], 0
    for mid, codes in iter_vcf(vcf, names):
        if mid is None:
            continue
        if j in chosen:
            ids.append(mid)
            cols.append(bytes(codes))
        j += 1
    ids = unique_ids(ids)
    d = os.path.dirname(out_path)
    if d:
        os.makedirs(d, exist_ok=True)
    n_missing = 0
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("<Numeric>\n")
        fh.write("\t".join(["<Marker>"] + ids) + "\n")
        for s, name in enumerate(samples):
            row = [c[s] for c in cols]
            n_missing += sum(1 for v in row if v == MISSING)
            fh.write("\t".join([name] + [TEXT[v] for v in row]) + "\n")
    cells = len(samples) * len(ids)
    return {"version": VERSION, "vcf": os.path.basename(vcf), "out": os.path.basename(out_path),
            "taxa": len(samples), "markers_in_vcf": total, "markers_passing": len(passing),
            "markers_written": len(ids), "missing_share": round(n_missing / cells, 4) if cells else None,
            "min_maf": min_maf, "max_missing": max_missing, "max_markers": max_markers,
            "taxa_filter": None if names is None else len(names)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("vcf")
    ap.add_argument("out")
    ap.add_argument("--keep", action="append", help="CSV with a Hybrid column (repeatable); keep only those taxa")
    ap.add_argument("--min-maf", type=float, default=MIN_MAF)
    ap.add_argument("--max-missing", type=float, default=MAX_MISSING)
    ap.add_argument("--max-markers", type=int, default=MAX_MARKERS)
    ap.add_argument("--summary")
    a = ap.parse_args(argv)
    names = keep_names(a.keep) if a.keep else None
    res = convert(a.vcf, a.out, names, a.min_maf, a.max_missing, a.max_markers)
    print(json.dumps(res, sort_keys=True))
    if a.summary:
        with open(a.summary, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=1, sort_keys=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
