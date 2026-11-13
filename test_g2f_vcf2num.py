# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
"""Unit tests for g2f_vcf2num 0.1.0 (standard library; two checks run only where the chain imports)."""
import contextlib
import gzip
import io
import json
import math
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import g2f_vcf2num as vn  # noqa: E402

try:
    import g2f_entry as ge
except Exception:  # pragma: no cover - only when the rest of the repo is absent
    ge = None
try:
    import g2f_baseline as gb
except Exception:  # pragma: no cover - needs numpy and pandas
    gb = None

HEAD = "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t"
VCF1 = ("##fileformat=VCFv4.2\n" + HEAD + "H1\tH2\tH3\tH4\n"
        "1\t100\tm1\tA\tG\t.\t.\t.\tGT\t0/0\t0/1\t1/1\t0|0\n"
        "1\t200\t.\tC\tT\t.\t.\t.\tGT:DP\t0/0:5\t./.:0\t0/0:3\t0/1:4\n"
        "1\t300\tm3\tG\tA\t.\t.\t.\tGT\t0/0\t0/0\t0/0\t0/0\n"
        "2\t50\tm4\tT\tC\t.\t.\t.\tGT\t./.\t./.\t./.\t1/1\n")
VCF_DUP = (HEAD + "H1\tH1\tH2\n"
           "1\t1\tm\tA\tG\t.\t.\t.\tGT\t0/1\t1/1\t0/0\n"
           "1\t2\tm\tA\tG\t.\t.\t.\tGT\t1/1\t0/0\t0/1\n")
OUT1 = ["<Numeric>", "<Marker>\tm1\t1_200", "H1\t0\t0", "H2\t0.5\tNA", "H3\t1\t0", "H4\t0\t0.5"]


class VcfToNumeric(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def put(self, name, text):
        p = os.path.join(self.d, name)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        return p

    def lines(self, path):
        with open(path, encoding="utf-8") as fh:
            return fh.read().splitlines()

    def test_layout_codes_and_filters(self):
        out = os.path.join(self.d, "g_numerical.txt")
        res = vn.convert(self.put("g.vcf", VCF1), out)
        self.assertEqual(self.lines(out), OUT1)
        self.assertEqual((res["taxa"], res["markers_in_vcf"], res["markers_passing"], res["markers_written"]),
                         (4, 4, 2, 2))
        self.assertAlmostEqual(res["missing_share"], 0.125, places=4)
        self.assertIsNone(res["taxa_filter"])

    def test_keep_names_restricts_taxa_before_filtering(self):
        out = os.path.join(self.d, "k_numerical.txt")
        res = vn.convert(self.put("g.vcf", VCF1), out, names={"H1", "H3"})
        self.assertEqual(self.lines(out), ["<Numeric>", "<Marker>\tm1", "H1\t0", "H3\t1"])
        self.assertEqual((res["markers_passing"], res["taxa_filter"]), (1, 2))

    def test_max_markers_thins_evenly(self):
        out = os.path.join(self.d, "t_numerical.txt")
        res = vn.convert(self.put("g.vcf", VCF1), out, max_markers=1)
        self.assertEqual(self.lines(out), ["<Numeric>", "<Marker>\tm1", "H1\t0", "H2\t0.5", "H3\t1", "H4\t0"])
        self.assertEqual(res["markers_written"], 1)

    def test_spread(self):
        self.assertEqual(vn.spread(10, 3), [0, 3, 6])
        self.assertEqual(vn.spread(5, 0), [0, 1, 2, 3, 4])
        self.assertEqual(vn.spread(3, 5), [0, 1, 2])
        self.assertEqual(vn.spread(7, 7), list(range(7)))

    def test_duplicate_samples_and_marker_ids(self):
        out = os.path.join(self.d, "d_numerical.txt")
        vn.convert(self.put("d.vcf", VCF_DUP), out)
        self.assertEqual(self.lines(out), ["<Numeric>", "<Marker>\tm\tm_2", "H1\t0.5\t1", "H2\t0\t0.5"])

    def test_call_codes(self):
        self.assertEqual(vn.call_code("1", 0), 2)
        self.assertEqual(vn.call_code("0/0/1/1", 0), 1)
        self.assertEqual(vn.call_code("./1", 0), vn.MISSING)
        self.assertEqual(vn.call_code("0/1", 3), vn.MISSING)
        self.assertEqual(vn.call_code("1|0:7", 0), 1)

    def test_gzip_input(self):
        p = os.path.join(self.d, "g.vcf.gz")
        with gzip.open(p, "wt", encoding="utf-8", newline="\n") as fh:
            fh.write(VCF1)
        out = os.path.join(self.d, "z_numerical.txt")
        vn.convert(p, out)
        self.assertEqual(self.lines(out), OUT1)

    def test_output_name_guard(self):
        with self.assertRaises(ValueError):
            vn.convert(self.put("g.vcf", VCF1), os.path.join(self.d, "g.txt"))

    def test_missing_header(self):
        p = self.put("n.vcf", "1\t1\tm\tA\tG\t.\t.\t.\tGT\t0/0\n")
        with self.assertRaises(ValueError):
            vn.convert(p, os.path.join(self.d, "n_numerical.txt"))

    def test_keep_names_and_cli(self):
        csvp = self.put("trait.csv", "Env,Hybrid,Yield_Mg_ha\nE1,H1,9\nE2, H3 ,8\n")
        self.assertEqual(vn.keep_names([csvp]), {"H1", "H3"})
        out = os.path.join(self.d, "c_numerical.txt")
        sj = os.path.join(self.d, "s.json")
        with contextlib.redirect_stdout(io.StringIO()):
            rc = vn.main([self.put("g.vcf", VCF1), out, "--keep", csvp, "--summary", sj])
        self.assertEqual(rc, 0)
        with open(sj, encoding="utf-8") as fh:
            self.assertEqual(json.load(fh)["markers_written"], 1)

    @unittest.skipUnless(ge is not None, "g2f_entry not importable here")
    def test_chain_finds_the_output(self):
        self.assertEqual(ge.role_of("5_Genotype_Data_All_2014_2026_Hybrids_numerical.txt"), "geno_numeric")
        self.assertEqual(ge.role_of("5_Genotype_Data_All_2014_2026_Hybrids.vcf"), "vcf")

    @unittest.skipUnless(gb is not None, "g2f_baseline (numpy, pandas) not importable here")
    def test_chain_reads_the_output(self):
        out = os.path.join(self.d, "r_numerical.txt")
        vn.convert(self.put("g.vcf", VCF1), out)
        names, G = gb.read_numeric(out, ["H1", "H2", "H3", "H4"])
        self.assertEqual(names, ["H1", "H2", "H3", "H4"])
        self.assertEqual(G.shape, (4, 2))
        self.assertAlmostEqual(float(G[1, 0]), 0.5, places=4)
        self.assertTrue(math.isnan(float(G[1, 1])))
        self.assertAlmostEqual(float(G[3, 1]), 0.5, places=4)


if __name__ == "__main__":
    unittest.main()
