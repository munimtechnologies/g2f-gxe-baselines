# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
"""Tests for g2f_refold 0.1.0 on a tiny synthetic release (no network, no real model).

Seasons: 2021 grows H1-H3 x T; 2022 grows a new set H4-H6 x T (a "new_hybrids" season); 2023 repeats
the 2022 set ("repeated_hybrids"); the 2024 template has three new hybrids and H4/T (2 of 8 pairs grown
in 2023, share 0.25, so the test season is "new_hybrids" and the 2022 fold is the one to choose on).
On the 2022 fold the fake M4 is a fixed pattern and full equals the observed yield, so only a = 1 scores
r = 1. On the 2023 fold (every row a seen hybrid) M4 equals the yield and full is the pattern, so only
b = 0 scores r = 1; ties go to the smaller a + b, then the smaller a.

Test fix 1 (2026-11-11): the fake M4 no longer assigns an empty selection with .loc, which pandas 3.1
refuses for an empty object Series ("Invalid value '[]' for dtype 'float64'"). Only this helper changed;
g2f_refold.py and every expected value are unchanged.
"""
import csv
import os
import shutil
import tempfile
import unittest
import urllib.request

import numpy as np
import pandas as pd

import g2f_refold as rf

TRAIT = {
    "A_2021": [("H1/T", 8), ("H2/T", 9), ("H3/T", 10)],
    "B_2021": [("H1/T", 6), ("H2/T", 7), ("H3/T", 8)],
    "A_2022": [("H4/T", 7), ("H5/T", 9), ("H6/T", 8)],
    "B_2022": [("H4/T", 5), ("H5/T", 8), ("H6/T", 6)],
    "A_2023": [("H4/T", 9), ("H5/T", 8), ("H6/T", 10)],
    "B_2023": [("H4/T", 7), ("H5/T", 6), ("H6/T", 9)],
}
TEMPLATE = [(e, h) for e in ("A_2024", "B_2024") for h in ("H7/T", "H8/T", "H9/T", "H4/T")]
PATTERN = {"H4/T": 0.0, "H5/T": 0.0, "H6/T": 1.0}


def write_csv(path, header, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def fake_m4(train, test):
    """M4 = the fixed PATTERN on 2022 rows, the observed yield on every other row."""
    out = test.copy()
    is22 = out["Env"].astype(str).str.endswith("_2022").to_numpy(dtype=bool)
    pattern = pd.to_numeric(out["Hybrid"].astype(str).map(PATTERN), errors="coerce").to_numpy(dtype=float)
    obs = pd.to_numeric(out["obs"], errors="coerce").to_numpy(dtype=float)
    out["M4"] = np.where(is22, pattern, obs)
    return out, {"lambda": 1.0, "train_rows": int(len(train)), "test_rows": int(len(test))}


class RefoldCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.data = os.path.join(self.tmp, "release")
        rows = [[e, e[-4:], h, str(y)] for e, hs in TRAIT.items() for h, y in hs]
        write_csv(os.path.join(self.data, "Training_data", "1_Training_Trait_Data_2014_2025.csv"),
                  ["Env", "Year", "Hybrid", "Yield_Mg_ha"], rows)
        with open(os.path.join(self.data, "Training_data",
                               "5_Genotype_Data_All_2014_2026_Hybrids_numerical.txt"), "w") as fh:
            fh.write("placeholder\n")
        write_csv(os.path.join(self.data, "Testing_data", "1_Submission_Template_2024.csv"),
                  ["Env", "Hybrid", "Yield_Mg_ha"], [[e, h, ""] for e, h in TEMPLATE])
        self.preds = os.path.join(self.tmp, "preds")
        write_csv(os.path.join(self.preds, "2022.csv"), ["Env", "Hybrid", "full"],
                  [[e, h, str(float(y))] for e, hs in TRAIT.items() if e.endswith("2022") for h, y in hs])
        write_csv(os.path.join(self.preds, "2023.csv"), ["Env", "Hybrid", "full"],
                  [[e, h, str(PATTERN[h])] for e, hs in TRAIT.items() if e.endswith("2023") for h, _y in hs])
        self.p22 = os.path.join(self.preds, "2022.csv")
        self.p23 = os.path.join(self.preds, "2023.csv")
        self._orig = urllib.request.urlretrieve

        def no_download(*a, **k):
            raise AssertionError("g2f_refold must not download")
        urllib.request.urlretrieve = no_download

    def tearDown(self):
        urllib.request.urlretrieve = self._orig
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_both(self):
        return rf.run(self.data, full_paths={2022: self.p22, 2023: self.p23}, m4_fn=fake_m4)

    def test_fake_m4_helper(self):
        test = pd.DataFrame({"Env": ["A_2023", "B_2023"], "Hybrid": ["H4/T", "H6/T"], "obs": [9.0, 9.0]})
        out, _info = fake_m4(test.iloc[:0], test)
        self.assertEqual(list(out["M4"]), [9.0, 9.0])
        test22 = pd.DataFrame({"Env": ["A_2022", "B_2022"], "Hybrid": ["H4/T", "H6/T"], "obs": [7.0, 6.0]})
        out22, _info = fake_m4(test22.iloc[:0], test22)
        self.assertEqual(list(out22["M4"]), [0.0, 1.0])

    def test_season_types(self):
        res = self.run_both()
        t = res["test"]
        self.assertEqual(t["season"], 2024)
        self.assertEqual(t["pairs"], 8)
        self.assertEqual(t["last_training_year"], 2023)
        self.assertEqual(t["pairs_hybrid_in_last_year"], 2)
        self.assertAlmostEqual(t["share_in_last_year"], 0.25)
        self.assertEqual(t["setting"], "new_hybrids")
        folds = res["folds_considered"]
        self.assertEqual([f["season"] for f in folds], [2023, 2022])
        self.assertEqual([f["last_training_year"] for f in folds], [2022, 2021])
        self.assertEqual([f["share_in_last_year"] for f in folds], [1.0, 0.0])
        self.assertEqual([f["setting"] for f in folds], ["repeated_hybrids", "new_hybrids"])
        self.assertEqual(res["choose_on"], [2022])
        self.assertTrue(res["matched"])

    def test_fold_scores_and_entry(self):
        res = self.run_both()
        f22, f23 = res["folds"]["2022"], res["folds"]["2023"]
        self.assertAlmostEqual(f22["raw"]["full"], 1.0, places=4)
        self.assertLess(f22["raw"]["M4"], 0.5)
        self.assertEqual((f22["chosen"]["a"], f22["chosen"]["b"]), (1.0, 0.0))
        self.assertAlmostEqual(f22["chosen"]["score"], 1.0, places=4)
        self.assertEqual(f22["rows_observed_by_category"]["new_one"], 6)
        self.assertEqual(f22["fit"]["rows_without_full"], 0)
        self.assertAlmostEqual(f23["raw"]["M4"], 1.0, places=4)
        self.assertLess(f23["raw"]["full"], 0.99)
        self.assertEqual((f23["chosen"]["a"], f23["chosen"]["b"]), (0.0, 0.0))
        self.assertEqual(f23["rows_observed_by_category"]["seen"], 6)
        self.assertEqual(res["entry"]["name"], "a1.00_b0.00")
        self.assertAlmostEqual(res["entry"]["score"], 1.0, places=4)
        self.assertEqual(res["choice_grid"], f22["grid"])

    def test_full_dir_and_fold_cap(self):
        res = rf.run(self.data, full_dir=self.preds, n_folds=5, m4_fn=fake_m4)
        self.assertEqual([f["season"] for f in res["folds_considered"]], [2023, 2022])
        self.assertEqual(res["entry"]["name"], "a1.00_b0.00")

    def test_no_matching_fold_with_full(self):
        res = rf.run(self.data, full_paths={2023: self.p23}, m4_fn=fake_m4)
        self.assertEqual(res["choose_on"], [2023])
        self.assertFalse(res["matched"])
        self.assertIn("skipped", res["folds"]["2022"])
        self.assertEqual(res["entry"]["name"], "a0.00_b0.00")

    def test_no_full_at_all(self):
        res = rf.run(self.data, m4_fn=fake_m4)
        self.assertEqual(res["choose_on"], [])
        self.assertIsNone(res["entry"]["score"])
        self.assertIn("why", res["entry"])

    def test_pick_folds_and_mean_grid(self):
        new, rep = "new_hybrids", "repeated_hybrids"
        folds = [{"season": 2025, "setting": rep}, {"season": 2024, "setting": new},
                 {"season": 2023, "setting": rep}, {"season": 2022, "setting": new}]
        self.assertEqual(rf.pick_folds({"setting": new}, folds), ([2024, 2022], True))
        self.assertEqual(rf.pick_folds({"setting": new}, folds, {2025, 2022}), ([2022], True))
        self.assertEqual(rf.pick_folds({"setting": new}, folds[:1] + folds[2:3]), ([2025], False))
        self.assertEqual(rf.pick_folds({"setting": new}, folds, set()), ([], False))
        self.assertEqual(rf.mean_grid([{"x": 0.25, "y": None}, {"x": 0.5, "y": 0.2}]), {"x": 0.375})
        self.assertEqual(rf.mean_grid([]), {})
        self.assertEqual(rf.parse_full(["2024=a.csv", "2022=b/c.csv"]), {2024: "a.csv", 2022: "b/c.csv"})

    def test_grade_expect(self):
        res = self.run_both()
        expect = {"season": 2024, "test_setting": "new_hybrids",
                  "folds": {"2023": "repeated_hybrids", "2022": "new_hybrids"}, "choose_on": [2022],
                  "raw": {"2022": {"full": 1.0}}, "tol": 0.0005, "entry": "a1.00_b0.00", "entry_score": 1.0,
                  "report_fold": "2023"}
        g = rf.grade_expect(res, expect)
        self.assertEqual({k: v["held"] for k, v in g.items()},
                         {"D1_season_and_settings": True, "D2_choose_on": True, "D3_fold_reproduced": True,
                          "D4_entry": True, "D5_report_fold_M4_beats_full": True,
                          "D6_report_fold_b_at_most_half": True})
        bad = dict(expect, choose_on=[2023], entry="a0.50_b0.50", raw={"2022": {"full": 0.9}})
        g2 = rf.grade_expect(res, bad)
        self.assertFalse(g2["D2_choose_on"]["held"])
        self.assertFalse(g2["D3_fold_reproduced"]["held"])
        self.assertFalse(g2["D4_entry"]["held"])


if __name__ == "__main__":
    unittest.main()
