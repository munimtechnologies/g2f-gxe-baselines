# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
"""Tests for g2f_levelmeta 0.1.0 on a hand-traced fixture (three rules, folds 2015-2020, check 2021)."""
import json
import os
import tempfile
import unittest

import g2f_levelmeta as gm

# level RMSE per season: (site_all, site_recent3, recent_mean)
ROWS = {2015: (2.0, 3.0, 2.5), 2016: (2.0, 3.0, 2.5), 2017: (3.0, 1.0, 2.5), 2018: (3.0, 1.0, 2.5),
        2019: (1.0, 2.0, 3.0), 2020: (2.0, 1.0, 3.0)}
CHECK = (1.5, 2.5, 3.5)
NAMES = ("site_all", "site_recent3", "recent_mean")


def rules(vals):
    return {n: {"rmse": v, "bias": 0.0} for n, v in zip(NAMES, vals)}


def level_res():
    return {"version": "0.1.0", "test_season": 2021, "fold_years": sorted(ROWS, reverse=True),
            "folds": {str(y): {"season": y, "rules": rules(v)} for y, v in ROWS.items()},
            "check": {"rules": rules(CHECK)}}


EXPECT = {"repro": {"2020": {"site_all": 2.0, "site_recent3": 1.0}, "2021": {"recent_mean": 3.5}},
          "targets": [2019, 2020, 2021], "tol": 0.0001, "gain_bar": 0.15, "floor": 1.2}


class LevelMetaTest(unittest.TestCase):
    def setUp(self):
        self.tab = gm.season_table(level_res())
        self.meta = gm.evaluate(self.tab)

    def test_table_has_folds_and_check(self):
        self.assertEqual(sorted(self.tab), [2015, 2016, 2017, 2018, 2019, 2020, 2021])
        self.assertEqual(self.tab[2021], {"site_all": 1.5, "site_recent3": 2.5, "recent_mean": 3.5})

    def test_pick_tie_goes_to_earlier_rule(self):
        self.assertEqual(gm.pick(self.tab, [2019, 2020]), "site_all")  # 1.5 vs 1.5
        self.assertEqual(gm.pick(self.tab, [2017, 2018]), "site_recent3")
        self.assertIsNone(gm.pick(self.tab, []))

    def test_targets_and_choices(self):
        m = self.meta
        self.assertEqual(m["targets"], [2019, 2020, 2021])
        p = m["per_target"]
        self.assertEqual({k: v["rule"] for k, v in p["2019"]["k"].items()},
                         {"1": "site_recent3", "2": "site_recent3", "4": "site_recent3", "all": "site_recent3"})
        self.assertEqual({k: v["rule"] for k, v in p["2020"]["k"].items()},
                         {"1": "site_all", "2": "site_recent3", "4": "site_recent3", "all": "site_recent3"})
        self.assertEqual({k: v["rule"] for k, v in p["2021"]["k"].items()},
                         {"1": "site_recent3", "2": "site_all", "4": "site_recent3", "all": "site_recent3"})
        self.assertEqual([p[s]["best"] for s in ("2019", "2020", "2021")],
                         ["site_all", "site_recent3", "site_all"])
        self.assertEqual(p["2021"]["k"]["2"]["rmse"], 1.5)

    def test_means_wins_and_decision(self):
        m = self.meta
        want = {"k=1": 2.1667, "k=2": 1.5, "k=4": 1.8333, "k=all": 1.8333}
        for k, v in want.items():
            self.assertAlmostEqual(m["procedures"][k], v, places=4)
        self.assertAlmostEqual(m["fixed"]["site_all"], 1.5, places=4)
        self.assertAlmostEqual(m["fixed"]["site_recent3"], 1.8333, places=4)
        self.assertAlmostEqual(m["fixed"]["recent_mean"], 3.1667, places=4)
        self.assertIsNone(m["fixed"]["site_anomaly"])
        self.assertEqual(m["wins"]["site_all"], 2)
        self.assertEqual(m["wins"]["site_recent3"], 1)
        self.assertEqual(m["wins"]["recent_mean"], 0)
        self.assertEqual(m["decision"], "fixed:site_all")  # ties k=2 at 1.5; the default wins ties
        self.assertEqual(m["choice_after"],
                         {"1": "site_all", "2": "site_all", "4": "site_recent3", "all": "site_recent3"})

    def test_grade(self):
        g = gm.grade(self.meta, self.tab, EXPECT)
        self.assertEqual({k: v["held"] for k, v in g.items()},
                         {"M1_reproduces_two_fold_run": True, "M2_all_seasons_beat_two": False,
                          "M3_recent_mean_worst_fixed_rule": True, "M4_choosing_gains_little": True,
                          "M5_level_floor_every_target": False})
        bad = dict(EXPECT, repro={"2020": {"site_all": 2.1}})
        self.assertFalse(gm.grade(self.meta, self.tab, bad)["M1_reproduces_two_fold_run"]["held"])
        wrong_targets = dict(EXPECT, targets=[2020, 2021])
        self.assertFalse(gm.grade(self.meta, self.tab, wrong_targets)["M1_reproduces_two_fold_run"]["held"])

    def test_main_writes_json(self):
        with tempfile.TemporaryDirectory() as d:
            lj = os.path.join(d, "level.json")
            ej = os.path.join(d, "expect.json")
            with open(lj, "w", encoding="utf-8") as fh:
                json.dump(level_res(), fh)
            with open(ej, "w", encoding="utf-8") as fh:
                json.dump(EXPECT, fh)
            self.assertEqual(gm.main(["--level-json", lj, "--out-dir", d, "--expect", ej, "--name", "m"]), 0)
            with open(os.path.join(d, "m.json"), encoding="utf-8") as fh:
                res = json.load(fh)
            self.assertEqual(res["held"], 3)
            self.assertEqual(res["total"], 5)
            self.assertEqual(res["decision"], "fixed:site_all")
            self.assertEqual(res["table"]["2021"]["recent_mean"], 3.5)


if __name__ == "__main__":
    unittest.main()
