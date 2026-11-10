# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
"""Tests for g2f_predict 0.1.0 on a tiny synthetic 2026-style release (no network, no real model)."""
import csv
import json
import os
import shutil
import tempfile
import unittest
import urllib.request

import numpy as np
import pandas as pd

import g2f_predict as gp

HYBRIDS = ["P1/T1", "P4/T1", "P5/P6", "P1/P2"]          # seen, new_one, new_none, new_both
M4 = {"P1/T1": 1.0, "P4/T1": 0.0, "P5/P6": -1.0, "P1/P2": 0.5}
FULL = {"P1/T1": 0.2, "P4/T1": 0.8, "P5/P6": 0.4, "P1/P2": 0.6}
OBS = {"A_2026": [10.0, 8.0, 7.0, 9.0], "C_2026": [9.0, 8.5, 7.0, 9.5]}


def write_csv(path, header, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def fake_m4(trait, template, geno_path):
    out = template[["Env", "Hybrid"]].copy()
    out["M4"] = out["Hybrid"].map(M4)
    return out, {"fake": True}


def zpop(vals):
    v = np.asarray(vals, dtype=float)
    return (v - v.mean()) / v.std()


class ReleaseCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.data = os.path.join(self.tmp, "release")
        self.out = os.path.join(self.tmp, "out")
        trait = []
        for env, ys in (("A_2025", (8, 9, 10)), ("B_2025", (6, 7, 8))):
            for h, y in zip(("P1/T1", "P2/T1", "P3/T1"), ys):
                trait.append([env, "2025", h, str(y)])
        write_csv(os.path.join(self.data, "Training_data", "1_Training_Trait_Data_2014_2025.csv"),
                  ["Env", "Year", "Hybrid", "Yield_Mg_ha"], trait)
        with open(os.path.join(self.data, "Training_data",
                               "5_Genotype_Data_All_2014_2026_Hybrids_numerical.txt"), "w") as fh:
            fh.write("placeholder\n")
        tmpl = [[e, h, ""] for e in ("A_2026", "C_2026") for h in HYBRIDS]
        write_csv(os.path.join(self.data, "Testing_data", "1_Submission_Template_2026.csv"),
                  ["Env", "Hybrid", "Yield_Mg_ha"], tmpl)
        full = [[e, h, str(FULL[h])] for e in ("A_2026", "C_2026") for h in HYBRIDS
                if not (e == "C_2026" and h == "P5/P6")]
        self.full = os.path.join(self.tmp, "full.csv")
        write_csv(self.full, ["Env", "Hybrid", "full"], full)
        self._orig = urllib.request.urlretrieve

        def no_download(*a, **k):
            raise AssertionError("g2f_predict must not download")
        urllib.request.urlretrieve = no_download

    def tearDown(self):
        urllib.request.urlretrieve = self._orig
        shutil.rmtree(self.tmp, ignore_errors=True)

    def add_observed(self):
        rows = [[e, h, str(OBS[e][i])] for e in ("A_2026", "C_2026") for i, h in enumerate(HYBRIDS)]
        write_csv(os.path.join(self.data, "Testing_data", "7_Testing_Observed_Values.csv"),
                  ["Env", "Hybrid", "Yield_Mg_ha"], rows)

    def test_release_and_season(self):
        rel = gp.release(self.data)
        for role in ("trait", "template", "geno_numeric"):
            self.assertIn(role, rel)
        self.assertTrue(rel["template"].endswith("1_Submission_Template_2026.csv"))
        self.assertEqual(gp.test_season(rel["template"]), 2026)
        self.assertEqual(gp.test_season("template.csv", ["X_2025", "Y_2026", "Z_2026"]), 2026)

    def test_missing_genotypes_is_an_error_not_a_download(self):
        os.remove(os.path.join(self.data, "Training_data", "5_Genotype_Data_All_2014_2026_Hybrids_numerical.txt"))
        with self.assertRaises(FileNotFoundError):
            gp.release(self.data)
        with self.assertRaises(FileNotFoundError):
            gp.build(self.data, self.out, m4_fn=fake_m4, min_hybrids=2)

    def test_categories(self):
        c = gp.category_counts(["P1/T1", "P2/T1", "P3/T1"], HYBRIDS * 2)
        self.assertEqual(c, {"seen": 2, "new_both": 2, "new_one": 2, "new_none": 2})

    def test_build_with_full(self):
        res = gp.build(self.data, self.out, self.full, m4_fn=fake_m4, min_hybrids=2)
        self.assertEqual(res["test_season"], 2026)
        self.assertEqual(res["template_pairs"], 8)
        self.assertEqual(res["rows_without_M4"], 0)
        self.assertEqual(res["full"]["rows_without_full"], 1)
        self.assertEqual(sorted(res["submissions"]), ["M4", "full", "mix"])
        for col, s in res["submissions"].items():
            self.assertTrue(s["validate"]["ok"], (col, s["validate"]))
            self.assertEqual(s["validate"]["rows"], 8)
        self.assertEqual(res["submissions"]["M4"]["write"]["filled_by_env_mean"], 0)
        self.assertEqual(res["submissions"]["mix"]["write"]["filled_by_env_mean"], 0)
        self.assertEqual(res["submissions"]["full"]["write"]["filled_by_env_mean"], 1)
        self.assertNotIn("scores_raw", res)
        pred = pd.read_csv(os.path.join(self.out, "predictions_2026.csv"))
        a = pred[pred["Env"] == "A_2026"]
        self.assertEqual(list(a["Hybrid"]), HYBRIDS)
        self.assertEqual(list(a["cat"]), ["seen", "new_one", "new_none", "new_both"])
        want = 0.5 * zpop([FULL[h] for h in HYBRIDS]) + 0.5 * zpop([M4[h] for h in HYBRIDS])
        for got, w in zip(a["mix"], want):
            self.assertAlmostEqual(got, w, places=6)
        # C_2026: full is missing for P5/P6, so its z is 0 there and the others are z-scored without it
        c = pred[pred["Env"] == "C_2026"]
        zf = zpop([FULL["P1/T1"], FULL["P4/T1"], FULL["P1/P2"]])
        zf = [zf[0], zf[1], 0.0, zf[2]]
        want_c = 0.5 * np.asarray(zf) + 0.5 * zpop([M4[h] for h in HYBRIDS])
        for got, w in zip(c["mix"], want_c):
            self.assertAlmostEqual(got, w, places=6)
        # Mg/ha file: template order kept, A_2026 centred on its location level (mean of A_2025 = 9),
        # C_2026 on the recent-season fallback (8), and the M4 ranking unchanged
        sub = pd.read_csv(os.path.join(self.out, "submission_2026_M4.csv"))
        self.assertEqual(list(sub["Hybrid"][:4]), HYBRIDS)
        sa = sub[sub["Env"] == "A_2026"]["Yield_Mg_ha"].to_numpy()
        sc = sub[sub["Env"] == "C_2026"]["Yield_Mg_ha"].to_numpy()
        self.assertAlmostEqual(sa.mean(), 9.0, places=4)
        self.assertAlmostEqual(sc.mean(), 8.0, places=4)
        self.assertEqual(list(np.argsort(sa)), list(np.argsort([M4[h] for h in HYBRIDS])))

    def test_build_m4_only(self):
        res = gp.build(self.data, self.out, None, m4_fn=fake_m4, min_hybrids=2)
        self.assertEqual(sorted(res["submissions"]), ["M4"])
        self.assertTrue(res["submissions"]["M4"]["validate"]["ok"])
        self.assertNotIn("mix", res)

    def test_build_with_observed_scores_and_grade(self):
        self.add_observed()
        res = gp.build(self.data, self.out, self.full, m4_fn=fake_m4, min_hybrids=2)
        self.assertIn("observed", res["files"])
        for col in ("M4", "mix"):
            raw, s = res["scores_raw"][col], res["submissions"][col]["score"]
            self.assertEqual(s["envs"], 2)
            self.assertLessEqual(abs(s["mean_r"] - raw), 0.0002)
        self.assertEqual(res["scores_by_category"]["seen"]["rows_observed"], 2)
        expect = {"season": 2026, "M4": res["scores_raw"]["M4"], "mix": res["scores_raw"]["mix"],
                  "tol": 0.0005, "envs": 2}
        g = gp.grade_expect(res, expect)
        self.assertEqual({k: v["held"] for k, v in g.items()},
                         {"P1_release_and_season": True, "P2_M4_reproduced": True, "P3_mix_reproduced": True,
                          "P4_files_validate": True, "P5_mgha_keeps_score": True})
        bad = dict(expect, M4=expect["M4"] + 0.01, season=2024)
        g2 = gp.grade_expect(res, bad)
        self.assertFalse(g2["P1_release_and_season"]["held"])
        self.assertFalse(g2["P2_M4_reproduced"]["held"])

    def test_plan(self):
        res = gp.plan(self.data)
        self.assertEqual(res["test_season"], 2026)
        self.assertEqual(res["categories"], {"seen": 2, "new_both": 2, "new_one": 2, "new_none": 2})
        self.assertEqual(res["seen"]["pairs_hybrid_seen"], 2)
        json.dumps(res)


if __name__ == "__main__":
    unittest.main()
