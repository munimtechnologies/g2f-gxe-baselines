# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
"""Unit tests for g2f_level 0.1.0 (standard library only). Every expected number is traced by hand in
the comments from the small fixture below."""
import csv
import os
import shutil
import tempfile
import unittest

import g2f_entry as ge
import g2f_level as gl

# Two locations; IAH1 grown 2019-2022, NEH1 2020-2022. Season means: 2019 9, 2020 8, 2021 10, 2022 10.
MEANS = (("IAH1_2019", 2019, 9.0), ("IAH1_2020", 2020, 10.0), ("IAH1_2021", 2021, 12.0),
         ("IAH1_2022", 2022, 11.0), ("NEH1_2020", 2020, 6.0), ("NEH1_2021", 2021, 8.0),
         ("NEH1_2022", 2022, 9.0))
ENVS_2023 = ("IAH1_2023", "NEH1_2023", "IAH9_2023", "ONH3_2023")


def stats():
    return {e: {"year": y, "mean": m, "sd": 1.0, "hybrids": 3} for e, y, m in MEANS}


def lv(rule, envs=ENVS_2023, year=2023, st=None):
    return {e: v["level"] for e, v in gl.levels(rule, st or stats(), envs, year).items()}


class Rules(unittest.TestCase):
    def test_recent_mean(self):
        # seasons 2020-2022: (10 + 12 + 11 + 6 + 8 + 9) / 6 = 9.3333
        self.assertAlmostEqual(gl.recent_mean(stats()), 56.0 / 6, places=6)

    def test_site_all_matches_scale_plan(self):
        got = gl.levels("site_all", stats(), ENVS_2023, 2023)
        plan = ge.scale_plan(stats(), ENVS_2023, min_hybrids=1)
        for e in ENVS_2023:
            self.assertEqual(got[e]["level"], plan["envs"][e]["level"])
        # IAH1 (9 + 10 + 12 + 11) / 4 = 10.5; NEH1 23 / 3; others fall back to 9.3333
        self.assertAlmostEqual(got["IAH1_2023"]["level"], 10.5, places=6)
        self.assertAlmostEqual(got["NEH1_2023"]["level"], 23.0 / 3, places=6)
        self.assertEqual(got["IAH9_2023"]["source"], "fallback")

    def test_site_recent3(self):
        v = lv("site_recent3")
        self.assertAlmostEqual(v["IAH1_2023"], 11.0, places=6)  # 2020-2022: (10 + 12 + 11) / 3
        self.assertAlmostEqual(v["NEH1_2023"], 23.0 / 3, places=6)
        self.assertAlmostEqual(v["ONH3_2023"], 56.0 / 6, places=6)

    def test_recent_rule_is_constant(self):
        v = lv("recent_mean")
        self.assertEqual(len(set(v.values())), 1)

    def test_anomalies(self):
        site, state = gl.anomalies(stats())
        # IAH1: 9-9, 10-8, 12-10, 11-10 -> mean 1.25; NEH1: 6-8, 8-10, 9-10 -> mean -5/3
        self.assertAlmostEqual(sum(site["IAH1"]) / 4, 1.25, places=6)
        self.assertAlmostEqual(sum(site["NEH1"]) / 3, -5.0 / 3, places=6)
        self.assertEqual(sorted(state), ["IA", "NE"])

    def test_site_anomaly(self):
        d = gl.levels("site_anomaly", stats(), ENVS_2023, 2023)
        self.assertAlmostEqual(d["IAH1_2023"]["level"], 56.0 / 6 + 1.25, places=6)   # 10.5833
        self.assertAlmostEqual(d["NEH1_2023"]["level"], 56.0 / 6 - 5.0 / 3, places=6)  # 7.6667
        self.assertEqual(d["IAH9_2023"]["source"], "state")  # state IA has IAH1's anomalies
        self.assertAlmostEqual(d["IAH9_2023"]["level"], 56.0 / 6 + 1.25, places=6)
        self.assertEqual(d["ONH3_2023"]["source"], "fallback")
        self.assertAlmostEqual(d["ONH3_2023"]["level"], 56.0 / 6, places=6)

    def test_site_anomaly_shrunk(self):
        v = lv("site_anomaly_shrunk")
        self.assertAlmostEqual(v["IAH1_2023"], 56.0 / 6 + 1.25 * 4 / 6, places=6)  # 10.1667
        self.assertAlmostEqual(v["NEH1_2023"], 56.0 / 6 - 1.0, places=6)          # -5/3 * 3/5 = -1

    def test_trend(self):
        # x - 2019: 0,1,1,2,2,3,3; y: 9,10,6,12,8,11,9. slope (32/7)/(52/7) = 8/13;
        # at 2023: 65/7 + 8/13 * (4 - 12/7) = 973/91 = 10.6923
        value, slope = gl.trend_at(stats(), 2023)
        self.assertAlmostEqual(slope, 8.0 / 13, places=6)
        self.assertAlmostEqual(value, 973.0 / 91, places=6)
        v = lv("site_anomaly_trend")
        self.assertAlmostEqual(v["IAH1_2023"], 973.0 / 91 + 1.25, places=6)
        self.assertAlmostEqual(v["ONH3_2023"], 973.0 / 91, places=6)

    def test_unknown_rule(self):
        with self.assertRaises(ValueError):
            gl.levels("nope", stats(), ENVS_2023, 2023)


class Folds(unittest.TestCase):
    def test_fold_years(self):
        self.assertEqual(gl.fold_years(stats(), 2), [2022, 2021])
        self.assertEqual(gl.fold_years(stats(), 10), [2022, 2021, 2020])

    def test_fold_2022(self):
        f = gl.fold(stats(), 2022)
        self.assertEqual((f["train_envs"], f["target_envs"]), (5, 2))
        r = f["rules"]
        # site_all: IAH1 31/3 vs 11, NEH1 7 vs 9 -> sqrt((4/9 + 4) / 2) = 1.4907
        self.assertAlmostEqual(r["site_all"]["rmse"], 1.4907, places=4)
        self.assertAlmostEqual(r["site_all"]["bias"], -1.3333, places=4)
        self.assertAlmostEqual(r["recent_mean"]["rmse"], 1.4142, places=4)        # errors -2, 0
        self.assertAlmostEqual(r["site_anomaly_shrunk"]["rmse"], 1.1045, places=4)  # errors -1.2, -1
        self.assertAlmostEqual(r["site_anomaly_trend"]["rmse"], 0.6684, places=4)  # 0.6190, -0.7143

    def test_fold_2021(self):
        r = gl.fold(stats(), 2021)["rules"]
        self.assertAlmostEqual(r["site_all"]["rmse"], 2.2638, places=4)            # -2.5, -2
        self.assertAlmostEqual(r["site_anomaly"]["rmse"], 2.2236, places=4)        # -2.6667, -1.6667
        self.assertAlmostEqual(r["site_anomaly_shrunk"]["rmse"], 2.2515, places=4)  # -3.1667, -0.3333
        self.assertAlmostEqual(r["site_anomaly_trend"]["rmse"], 3.5355, places=4)  # slope -1: -4, -3

    def test_choose(self):
        folds = [gl.fold(stats(), y) for y in (2022, 2021)]
        rule, table = gl.choose(folds)
        # means: site_all 1.877, recent 2.009, recent3 1.877, anomaly 1.857, shrunk 1.678, trend 2.102
        self.assertEqual(rule, "site_anomaly_shrunk")
        self.assertEqual(sorted(table), sorted(gl.RULES))
        self.assertAlmostEqual(table["site_anomaly_shrunk"], 1.678, places=3)

    def test_choose_tie_goes_to_earlier_rule(self):
        f = {"rules": {r: {"rmse": 1.0} for r in gl.RULES}}
        self.assertEqual(gl.choose([f])[0], "site_all")

    def test_level_errors_empty(self):
        self.assertIsNone(gl.level_errors({}, {"X_2023": 1.0})["rmse"])


def write(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


class Release(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        rows = []
        for e, y, m in MEANS:  # hybrids H1-H3 at m - 1, m, m + 1: env mean m, 3 hybrids
            for i, h in enumerate(("H1", "H2", "H3")):
                rows.append([e, h, y, m - 1 + i])
        write(os.path.join(self.d, "1_Training_Trait_Data_2019_2022.csv"),
              ["Env", "Hybrid", "Year", "Yield_Mg_ha"], rows)
        tmpl = [["IAH1_2023", "H1", ""], ["IAH1_2023", "H2", ""], ["IAH1_2023", "H3", ""],
                ["NEH1_2023", "H1", ""], ["NEH1_2023", "H2", ""], ["IAH9_2023", "H1", ""],
                ["ONH3_2023", "H2", ""]]
        write(os.path.join(self.d, "1_Submission_Template_2023.csv"), ["Env", "Hybrid", "Yield_Mg_ha"], tmpl)
        obs = [["IAH1_2023", "H1", 11], ["IAH1_2023", "H2", 12], ["IAH1_2023", "H3", 13],
               ["NEH1_2023", "H1", 8], ["NEH1_2023", "H2", 10], ["IAH9_2023", "H1", 10]]
        write(os.path.join(self.d, "Observed_Values_2023.csv"), ["Env", "Hybrid", "Yield_Mg_ha"], obs)

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_run_and_check(self):
        res = gl.run(self.d, 2)
        self.assertEqual(res["test_season"], 2023)
        self.assertEqual(res["fold_years"], [2022, 2021])
        self.assertEqual(res["chosen"], "site_anomaly_shrunk")
        self.assertAlmostEqual(res["levels"]["NEH1_2023"]["level"], 8.3333, places=4)
        c = res["check"]
        self.assertEqual(c["envs_observed"], 3)
        s = c["rules"]["site_all"]
        # levels 10.5, 7.6667, 9.3333 vs env means 12, 9, 10: errors -1.5, -1.3333, -0.6667
        self.assertAlmostEqual(s["rmse"], 1.2210, places=4)
        self.assertAlmostEqual(s["bias"], -1.1667, places=4)
        self.assertAlmostEqual(s["mae"], 1.1667, places=4)
        # pairs: (0.25 + 2.25 + 6.25 + 1/9 + 49/9 + 4/9) / 6 = 14.75 / 6 -> 1.5679
        self.assertAlmostEqual(s["pooled_rmse"], 1.5679, places=4)
        # per env: sqrt(8.75/3) 1.7078, sqrt(25/9) 1.6667, 0.6667 -> mean 1.3471
        self.assertAlmostEqual(s["env_rmse_mean_2022_metric"], 1.3471, places=4)

    def test_grade(self):
        res = gl.run(self.d, 2)
        expect = {"season": 2023, "folds": [2022, 2021], "tol": 0.0005, "rmse_floor": 0.5,
                  "repro": {"site_all": {"rmse": 1.2210, "bias": -1.1667, "pooled_rmse": 1.5679}}}
        g = gl.grade_expect(res, expect)
        self.assertEqual(len(g), 6)
        self.assertTrue(g["L1_reproduces_entry_levels"]["held"])
        self.assertTrue(g["L2_choice_is_not_site_all"]["held"])
        self.assertTrue(g["L6_shrinking_helps_on_folds"]["held"])
        bad = dict(expect, repro={"site_all": {"rmse": 9.0}})
        self.assertFalse(gl.grade_expect(res, bad)["L1_reproduces_entry_levels"]["held"])

    def test_entry_plan(self):
        rel = ge.find_release(self.d)
        plan = gl.entry_plan(rel["trait"], rel["template"], "site_anomaly_shrunk", min_hybrids=3)
        self.assertEqual(plan["level_rule"], "site_anomaly_shrunk")
        self.assertAlmostEqual(plan["envs"]["IAH1_2023"]["level"], 56.0 / 6 + 1.25 * 4 / 6, places=6)
        mg, info = ge.rescale({("IAH1_2023", "H1"): 1.0, ("IAH1_2023", "H2"): 2.0}, plan)
        self.assertAlmostEqual((mg[("IAH1_2023", "H1")] + mg[("IAH1_2023", "H2")]) / 2,
                               plan["envs"]["IAH1_2023"]["level"], places=6)


if __name__ == "__main__":
    unittest.main()
