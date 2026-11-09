# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
"""Tests for g2f_release_census on small synthetic files (no real data)."""
import json
import os
import tempfile
import unittest

import g2f_release_census as rc

TRAIT = (
    "Env,Year,Hybrid,Yield_Mg_ha\n"
    "IAH1_2022,2022,A/B,10.1\n"
    "IAH1_2022,2022,A/C,NA\n"
    "IAH1_2023,2023,A/B,9.0\n"
    "NEH2_2023,2023,D/E,\n"
    "NEH2_2023,2023,C/F,8.5\n"
    "\n"
)
TEMPLATE = (
    "Env,Hybrid,Yield_Mg_ha\n"
    "IAH1_2024,A/B,\n"      # hybrid seen, location seen, seen at location, both parents seen
    "IAH1_2024,C/B,\n"      # new hybrid, both parents seen (C from C/F, B from A/B)
    "TXH1_2024,A/B,\n"      # hybrid seen, new location
    "TXH1_2024,X/Y,\n"      # nothing seen
    "NEH2_2024,D/E,\n"      # D/E only had an empty yield: not seen
    "NEH2_2024,Q,\n"        # unparsed name
)
OBSERVED = (
    "Env,Hybrid,Yield_Mg_ha\n"
    "IAH1_2024,A/B,11\n"
    "IAH1_2024,C/B,12\n"
    "TXH1_2024,A/B,7\n"
    "TXH1_2024,X/Y,NA\n"
    "NEH2_2024,D/E,6\n"
    "ZZH1_2024,A/B,5\n"
)
GENO = (
    "<Numeric>\n"
    "<Marker>\tm1\tm2\tm3\n"
    "A/B\t0\t1\t2\n"
    "C/B\t1\t1\t0\n"
    "X/Y\t2\t0\t0\n"
    "A/C\t0\t0\t0\n"
    "Z/Z\t1\t0\t1\n"
)


def write(folder, name, text):
    path = os.path.join(folder, name)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    return path


class Helpers(unittest.TestCase):
    def test_roles(self):
        self.assertEqual(rc.role_of("1_Training_Trait_Data_2014_2023.csv"), "trait")
        self.assertEqual(rc.role_of("Testing_data/1_Submission_Template_2024.csv"), "template")
        self.assertEqual(rc.role_of("7_Testing_Observed_Values.csv"), "observed")
        self.assertEqual(rc.role_of("5_Genotype_Data_All_2014_2025_Hybrids_numerical.txt"), "geno_numeric")
        self.assertEqual(rc.role_of("5_Genotype_Data_All_2014_2025_Hybrids.vcf"), "vcf")
        self.assertEqual(rc.role_of("4_Training_Weather_Data_2014_2023_full_year.csv"), "weather")
        self.assertEqual(rc.role_of("readme.txt"), "other")
        self.assertEqual(rc.split_of("Training_data/x.csv"), "training")
        self.assertEqual(rc.split_of("2_Testing_Meta_Data_2024.csv"), "testing")

    def test_env_helpers(self):
        self.assertEqual(rc.env_year("IAH1_2024"), 2024)
        self.assertIsNone(rc.env_year("IAH1"))
        self.assertEqual(rc.env_location("IAH1_2024"), "IAH1")
        self.assertEqual(rc.env_location("ODD"), "ODD")
        self.assertEqual(rc.loc_prefix("onh1"), "ON")
        self.assertEqual(rc.parents("A/B"), ("A", "B"))
        self.assertIsNone(rc.parents("Q"))
        self.assertIsNone(rc.parents("A/B/C"))
        self.assertTrue(rc.is_number("10.1"))
        self.assertFalse(rc.is_number("NA"))
        self.assertFalse(rc.is_number(""))
        self.assertFalse(rc.is_number("nan"))

    def test_check(self):
        flat = {"a": 5, "b": 10, "c": [1]}
        res = rc.check(flat, {"a": {"eq": 5}, "b": {"min": 11}, "c": {"eq": 1}, "d": {"eq": 0},
                              "e": {"min": 0, "max": 10, "source": "x"}})
        self.assertTrue(res["a"]["held"])
        self.assertFalse(res["b"]["held"])
        self.assertFalse(res["c"]["held"])
        self.assertFalse(res["d"]["held"])
        self.assertIsNone(res["d"]["value"])
        self.assertFalse(res["e"]["held"])


class Census(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = self.tmp.name
        write(d, "1_Training_Trait_Data_2014_2023.csv", TRAIT)
        write(d, "1_Submission_Template_2024.csv", TEMPLATE)
        write(d, "7_Testing_Observed_Values.csv", OBSERVED)
        write(d, "5_Genotype_Data_All_2014_2025_Hybrids_numerical.txt", GENO)
        write(d, "readme.txt", "hello\n\nworld\n")
        self.res = rc.census(d)
        self.flat = rc.flatten(self.res)

    def tearDown(self):
        self.tmp.cleanup()

    def test_files(self):
        self.assertEqual(self.res["data_dir_files"], 5)
        roles = {f["file"]: f["role"] for f in self.res["files"]}
        self.assertEqual(roles["readme.txt"], "other")
        other = [f for f in self.res["files"] if f["file"] == "readme.txt"][0]
        self.assertEqual(other["nonblank_lines"], 2)
        self.assertEqual(len(other["sha256"]), 64)

    def test_trait(self):
        t = self.res["by_role"]["trait"]
        self.assertEqual(t["rows"], 5)               # the blank line is skipped
        self.assertEqual(t["hybrids"], 4)            # A/B, A/C, D/E, C/F
        self.assertEqual(t["env"]["envs"], 3)
        self.assertEqual(t["env"]["locations"], 2)
        self.assertEqual(t["env"]["years"], [2022, 2023])
        self.assertEqual(t["env"]["envs_by_prefix"], {"IA": 2, "NE": 1})
        self.assertEqual(t["rows_with_numeric_yield"], 3)
        self.assertEqual(t["hybrids_with_numeric_yield"], 2)   # A/B, C/F
        self.assertEqual(t["envs_with_numeric_yield"], 3)
        self.assertEqual(t["year_values"], ["2022", "2023"])

    def test_template_cross(self):
        f = self.flat
        self.assertEqual(f["template_rows"], 6)
        self.assertEqual(f["template_pairs"], 6)
        self.assertEqual(f["template_envs"], 3)
        self.assertEqual(f["template_hybrids"], 5)              # A/B, C/B, X/Y, D/E, Q
        self.assertEqual(f["template_hybrids_seen"], 1)         # A/B
        self.assertEqual(f["template_pairs_hybrid_seen"], 2)    # A/B at IAH1 and TXH1
        self.assertEqual(f["template_pairs_location_seen"], 4)  # IAH1 x2, NEH2 x2
        self.assertEqual(f["template_pairs_hybrid_seen_at_location"], 1)
        self.assertEqual(f["template_pairs_both_parents_seen"], 3)  # A/B, C/B, A/B
        self.assertEqual(f["template_pairs_one_parent_seen"], 0)    # X/Y none; D/E none (no yield)
        self.assertEqual(f["template_pairs_unparsed_hybrid"], 1)
        self.assertEqual(f["template_envs_in_training"], 0)
        self.assertEqual(f["template_rows_with_numeric_yield"], 0)

    def test_genotype(self):
        g = self.res["by_role"]["geno_numeric"]
        self.assertEqual(g["header_lines_skipped"], 1)
        self.assertEqual(g["first_header_cell"], "<Marker>")
        self.assertEqual(g["orientation"], "taxa_in_rows")
        self.assertEqual(g["taxa"], 5)
        self.assertEqual(g["markers"], 3)
        self.assertEqual(g["row_widths"], [4])
        self.assertEqual(g["taxa_matching_trait_hybrids"], 2)   # A/B, A/C
        self.assertEqual(self.flat["geno_taxa"], 5)
        self.assertEqual(self.flat["geno_markers"], 3)
        self.assertEqual(self.flat["template_hybrids_genotyped"], 3)  # A/B, C/B, X/Y
        self.assertEqual(self.flat["template_pairs_genotyped"], 4)
        self.assertEqual(self.flat["geno_taxa_outside_trait_and_template"], 1)  # Z/Z

    def test_year_overlap(self):
        self.assertEqual(self.flat["trait_year_overlap"], [
            {"year": 2022, "hybrids": 1, "in_previous_year": 0, "in_any_earlier_year": 0},
            {"year": 2023, "hybrids": 2, "in_previous_year": 1, "in_any_earlier_year": 1}])
        self.assertEqual(self.flat["last_training_year"], 2023)
        self.assertEqual(self.flat["template_hybrids_in_last_training_year"], 1)   # A/B
        self.assertEqual(self.flat["template_pairs_hybrid_in_last_training_year"], 2)
        self.assertEqual(rc.year_overlap({2020: {"a"}, 2022: {"a", "b"}}), [
            {"year": 2020, "hybrids": 1, "in_previous_year": 0, "in_any_earlier_year": 0},
            {"year": 2022, "hybrids": 2, "in_previous_year": 0, "in_any_earlier_year": 1}])

    def test_observed(self):
        f = self.flat
        self.assertEqual(f["template_pairs_with_observation"], 4)   # X/Y is NA
        self.assertEqual(f["observed_pairs_outside_template"], 1)   # ZZH1
        self.assertEqual(f["observed_envs_with_3plus"], 0)
        self.assertEqual(f["template_envs_without_3_observed"], ["IAH1_2024", "NEH2_2024", "TXH1_2024"])

    def test_transposed_genotype(self):
        with tempfile.TemporaryDirectory() as d:
            p = write(d, "g_numerical.txt", "marker,A/B,C/B\nm1,0,1\nm2,1,1\n")
            s, taxa = rc.numeric_census(p, {"A/B"})
            self.assertEqual(s["orientation"], "taxa_in_columns")
            self.assertEqual(s["markers"], 2)
            self.assertEqual(taxa, {"A/B", "C/B"})

    def test_main_with_expect(self):
        with tempfile.TemporaryDirectory() as out:
            exp = write(out, "expect.json", json.dumps(
                {"checks": {"template_pairs": {"eq": 6}, "geno_markers": {"eq": 4}}}))
            self.assertEqual(rc.main(["--data-dir", self.tmp.name, "--out-dir", out,
                                      "--expect", exp, "--name", "c"]), 0)
            with open(os.path.join(out, "c.json"), encoding="utf-8") as fh:
                res = json.load(fh)
            self.assertEqual(res["expect_held"], 1)
            self.assertEqual(res["expect_total"], 2)
            self.assertFalse(res["expect"]["geno_markers"]["held"])


if __name__ == "__main__":
    unittest.main()
