# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
"""Offline tests for g2f_refcheck 0.1.1 (synthetic data only)."""
import json
import os
import tempfile
import unittest

import numpy as np
import pandas as pd

import g2f_refcheck as rc


class TestCategories(unittest.TestCase):
    def test_parents(self):
        self.assertEqual(rc.parents("A1/B2"), ("A1", "B2"))
        self.assertEqual(rc.parents(" A1 / B2 "), ("A1", "B2"))
        self.assertEqual(rc.parents("SOLO"), ("SOLO",))

    def test_categorize(self):
        train = ["A/B", "C/D"]
        cats = rc.categorize(train, ["A/B", "A/D", "A/X", "X/Y", "C/B"])
        self.assertEqual(cats, ["seen", "new_both", "new_one", "new_none", "new_both"])


class TestScoring(unittest.TestCase):
    def frame(self):
        return pd.DataFrame({"Env": ["E1"] * 4 + ["E2"] * 4,
                             "Hybrid": list("abcdabcd"),
                             "obs": [1, 2, 3, 4, 4, 3, 2, 1],
                             "p": [1, 2, 3, 4, 1, 2, 3, 4],
                             "k": [5, 5, 5, 5, 5, 5, 5, 5]})

    def test_mean_r(self):
        r, n = rc.mean_r(self.frame(), "p")
        self.assertEqual(n, 2)
        self.assertAlmostEqual(r, 0.0, places=4)   # +1 and -1

    def test_constant_scores_zero(self):
        rs = rc.env_r(self.frame(), "k")
        self.assertEqual(rs, {"E1": 0.0, "E2": 0.0})

    def test_too_few_rows_skipped(self):
        df = self.frame().iloc[[0, 1, 4, 5, 6, 7]]
        self.assertEqual(sorted(rc.env_r(df, "p")), ["E2"])

    def test_agreement(self):
        df = self.frame()
        df["q"] = df["p"] * 2 + 1
        a, n = rc.agreement(df, "p", "q")
        self.assertEqual(n, 2)
        self.assertAlmostEqual(a, 1.0, places=4)

    def test_place(self):
        self.assertEqual(rc.place(0.46), 1)
        self.assertEqual(rc.place(0.4416), 3)
        self.assertEqual(rc.place(0.3018), 40)
        self.assertIsNone(rc.place(None))


class TestSplit(unittest.TestCase):
    def test_split_fold(self):
        rng = np.random.default_rng(1)
        hyb = ["A/B", "A/D", "A/X", "X/Y", "C/D", "A/B", "A/D", "A/X", "X/Y", "C/B"]
        base = pd.DataFrame({"Env": ["E1"] * 5 + ["E2"] * 5, "Hybrid": hyb,
                             "obs": rng.normal(size=10)})
        preds = base[["Env", "Hybrid"]].copy()
        preds["full"] = base["obs"].to_numpy()
        preds["b2"] = base["obs"].to_numpy()
        res = rc.split_fold(base, preds, ["A/B", "C/D"])
        self.assertEqual(res["rows_observed"]["all"], 10)
        self.assertEqual(res["rows_observed"]["seen"], 3)
        self.assertEqual(sum(res["rows_observed"][c] for c in rc.CATEGORIES), 10)
        self.assertAlmostEqual(res["score"]["all"]["full"], 1.0, places=4)
        self.assertNotIn("allloc", res["score"]["all"])

    def test_grade_split(self):
        res = {"2022": {"rows_observed": {"seen": 816, "new_one": 9126, "new_both": 1900},
                        "score": {"new_one": {"full": 0.20}, "new_both": {"full": 0.40}}},
               "2024": {"rows_observed": {"seen": 1172, "new_one": 7676, "new_both": 638},
                        "score": {"new_one": {"full": 0.31}}}}
        g = rc.grade_split(res)
        self.assertTrue(g["S1_categories_match_newshrink"]["held"])
        self.assertTrue(g["P7_full_beats_M4_2022_new_one"]["held"])
        self.assertTrue(g["P8_full_below_M4_2022_new_both"]["held"])
        self.assertTrue(g["P9_full_2024_new_one_at_least_0.30"]["held"])
        res["2022"]["rows_observed"]["new_both"] = 2000      # 5.5% off
        res["2022"]["score"]["new_one"]["full"] = 0.1435      # not strictly above
        g = rc.grade_split(res)
        self.assertFalse(g["S1_categories_match_newshrink"]["held"])
        self.assertFalse(g["P7_full_beats_M4_2022_new_one"]["held"])

    def test_grade_r0(self):
        g = rc.grade_r0(None, None)
        self.assertIsNone(g["G1_harness_matches_leaderboard"]["held"])
        g = rc.grade_r0(0.4400, 0.995)
        self.assertTrue(g["G1_harness_matches_leaderboard"]["held"])
        self.assertTrue(g["G2_reimplementation_matches_reference"]["held"])
        self.assertTrue(g["P10_reference_and_full_agree_0.99"]["held"])
        g = rc.grade_r0(0.4200, 0.90)
        self.assertFalse(g["G1_harness_matches_leaderboard"]["held"])
        self.assertFalse(g["G2_reimplementation_matches_reference"]["held"])
        self.assertFalse(g["P10_reference_and_full_agree_0.99"]["held"])


class TestCommands(unittest.TestCase):
    def write_release(self, d):
        rng = np.random.default_rng(7)
        rows = []
        for year in (2021, 2022, 2023):
            for e in ("IAH1", "NEH1"):
                for h in ("A/B", "C/D", "E/F", "C/X", "G/H"):
                    rows.append({"Env": "%s_%d" % (e, year), "Year": year, "Hybrid": h,
                                 "Yield_Mg_ha": rng.normal(10, 1)})
        pd.DataFrame(rows).to_csv(os.path.join(d, rc.FILES["trait"]), index=False)
        tmpl = pd.DataFrame({"Env": ["IAH1_2024"] * 4 + ["NEH1_2024"] * 4,
                             "Hybrid": ["A/B", "A/D", "Z/Q", "C/X"] * 2})
        tmpl.to_csv(os.path.join(d, rc.FILES["template"]), index=False)
        obs = tmpl.copy()
        obs["Yield_Mg_ha"] = rng.normal(10, 1, size=len(obs))
        obs.to_csv(os.path.join(d, rc.FILES["observed"]), index=False)
        preds = {}
        for fold in ("2024", "2023", "2022"):
            base = tmpl if fold == "2024" else \
                pd.DataFrame(rows).query("Year == %s" % fold)[["Env", "Hybrid"]]
            p = base.copy()
            for v in ("full", "b2", "b1", "allloc"):
                p[v] = rng.normal(size=len(p))
            p.to_csv(os.path.join(d, "g2f_refmodel_%s_predictions.csv" % fold), index=False)
            preds[fold] = p
        m4 = tmpl.copy()
        m4["M4"] = 0.0
        m4["seen"] = ["True", "True", "False", "True"] * 2
        m4.to_csv(os.path.join(d, "m4.csv"), index=False)
        ref = tmpl.copy()
        ref["Yield_Mg_ha"] = preds["2024"]["full"].to_numpy() * 3 + 10
        ref.to_csv(os.path.join(d, "ref.csv"), index=False)

    def test_split_and_r0_end_to_end(self):
        with tempfile.TemporaryDirectory() as d:
            self.write_release(d)
            out = os.path.join(d, "out")
            self.assertEqual(rc.main(["split", "--data-dir", d, "--out-dir", out, "--pred-dir", d]), 0)
            with open(os.path.join(out, "g2f_refsplit.json"), encoding="utf-8") as fh:
                res = json.load(fh)
            self.assertEqual(res["folds"]["2024"]["rows_observed"]["all"], 8)
            self.assertEqual(res["folds"]["2024"]["rows_observed"]["seen"], 4)
            self.assertEqual(res["folds"]["2024"]["rows_observed"]["new_both"], 2)
            self.assertEqual(res["folds"]["2024"]["rows_observed"]["new_none"], 2)
            self.assertIn("S1_categories_match_newshrink", res["grading"])
            self.assertEqual(rc.main(["r0", "--data-dir", d, "--out-dir", out,
                                      "--ref-pred", os.path.join(d, "ref.csv"),
                                      "--ref-script", os.path.join(d, "none.R"),
                                      "--full-pred", os.path.join(d, "g2f_refmodel_2024_predictions.csv"),
                                      "--m4-pred", os.path.join(d, "m4.csv")]), 0)
            with open(os.path.join(out, "g2f_refr0.json"), encoding="utf-8") as fh:
                r0 = json.load(fh)
            self.assertTrue(r0["reference_ran"])
            self.assertAlmostEqual(r0["agreement_ref_full"]["mean_r"], 1.0, places=4)
            self.assertEqual(r0["score"]["ref"], r0["score"]["full"])
            self.assertTrue(r0["grading"]["P10_reference_and_full_agree_0.99"]["held"])

    def test_r0_not_run(self):
        with tempfile.TemporaryDirectory() as d:
            self.write_release(d)
            out = os.path.join(d, "out")
            rc.main(["r0", "--data-dir", d, "--out-dir", out, "--ref-pred", os.path.join(d, "missing.csv"),
                     "--ref-script", os.path.join(d, "none.R")])
            with open(os.path.join(out, "g2f_refr0.json"), encoding="utf-8") as fh:
                r0 = json.load(fh)
            self.assertFalse(r0["reference_ran"])
            self.assertIsNone(r0["grading"]["G1_harness_matches_leaderboard"]["held"])


if __name__ == "__main__":
    unittest.main()
