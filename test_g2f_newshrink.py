# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
# Offline checks of g2f_newshrink on small hand-made and synthetic data (no download).
import unittest

import numpy as np
import pandas as pd

import g2f_baseline as gb
import g2f_newshrink as ns
from test_g2f_parentgca import crosses

LAMBDAS = (1.0, 10.0, 100.0)
K = ns.key


class Recalibrate(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame({"Env": ["A", "A", "A", "B", "B"],
                                "seen": [True, False, False, False, False],
                                "M4": [5.0, 1.0, 3.0, 10.0, 20.0]})

    def test_scale_and_offset_per_env(self):
        np.testing.assert_allclose(ns.recalibrate(self.df, 0.5, 0.1), [5.0, 1.6, 2.6, 12.6, 17.6])
        np.testing.assert_allclose(ns.recalibrate(self.df, 0.0, 0.0), [5.0, 2.0, 2.0, 15.0, 15.0])

    def test_identity_and_all_seen(self):
        np.testing.assert_allclose(ns.recalibrate(self.df, 1.0, 0.0), self.df["M4"])
        seen = self.df.assign(seen=True)
        np.testing.assert_allclose(ns.recalibrate(seen, 0.0, 0.5), self.df["M4"])


class Choose(unittest.TestCase):
    def test_ties_go_to_m4(self):
        scores = {K(s, o): 0.3 for s in ns.S_GRID for o in ns.O_GRID}
        self.assertEqual(ns.choose(scores), (1.0, 0.0))
        scores[K(0.5, 0.0)] = scores[K(0.75, 0.0)] = 0.4
        self.assertEqual(ns.choose(scores), (0.75, 0.0))
        scores[K(0.5, -0.25)] = 0.5
        self.assertEqual(ns.choose(scores), (0.5, -0.25))
        self.assertEqual(ns.choose(scores, o_grid=(0.0,)), (0.75, 0.0))


class Diagnostics(unittest.TestCase):
    def test_known_parents(self):
        train = pd.DataFrame({"Env": ["E1"] * 3, "Hybrid": ["A/B", "C/D", "CHECK"],
                              "Yield_Mg_ha": [1.0, 2.0, 3.0]})
        k = ns.known_parents(train, ["A/X", "A/C", "X/Y", "CHECK", "B/B"])
        np.testing.assert_array_equal(k, [1, 2, 0, 0, 2])

    def test_new_split(self):
        df = pd.DataFrame({"Env": ["A"] * 8,
                           "seen": [False] * 7 + [True],
                           "obs": [1, 2, 3, 4, 1, 2, 3, 9.0],
                           "G1": [1, 2, 3, 4, 3, 2, 1, 0.0],
                           "M4": [4, 3, 2, 1, 1, 2, 3, 0.0]})
        res = ns.new_split(df, np.array([1, 1, 1, 1, 2, 2, 2, 0]))
        self.assertEqual(res["one_parent_seen"]["rows"], 4)
        self.assertAlmostEqual(res["one_parent_seen"]["G1"]["mean_r"], 1.0)
        self.assertAlmostEqual(res["one_parent_seen"]["M4"]["mean_r"], -1.0)
        self.assertEqual(res["both_parents_seen"]["rows"], 3)
        self.assertAlmostEqual(res["both_parents_seen"]["G1"]["mean_r"], -1.0)

    def test_level_gap(self):
        df = pd.DataFrame({"Env": ["A"] * 5 + ["B"] * 2,
                           "seen": [True, True, False, False, False, True, True],
                           "obs": [1, 3, 5, 7, np.nan, 2, 4],
                           "M4": [0, 0, 1, 1, 100, 0, 0.0]})
        self.assertAlmostEqual(ns.level_gap(df, "obs"), 1.5492, places=3)
        self.assertAlmostEqual(ns.level_gap(df, "M4"), 1.0)


class Fold(unittest.TestCase):
    def test_grid_contains_m4_and_s0_is_flat(self):
        names, G, trait, test = crosses()
        Z = gb.standardize(G)
        seen = trait[trait["Year"] == 2020].groupby(
            ["Env", "Hybrid"], as_index=False)["Yield_Mg_ha"].mean().rename(columns={"Yield_Mg_ha": "obs"})
        train = trait[trait["Year"] < 2020]
        preds, entry = ns.fold(train, pd.concat([seen, test], ignore_index=True), names, Z, lambdas=LAMBDAS)
        self.assertEqual(len(entry["grid"]), 25)
        m4 = gb.score(preds, ("M4",))["M4"]["mean_r"]
        self.assertAlmostEqual(entry["grid"][K(1.0, 0.0)], m4, places=4)
        self.assertTrue(preds["seen"].any() and not preds["seen"].all())
        self.assertGreater(entry["new_split"]["both_parents_seen"]["rows"], 0)
        p = preds.assign(M5=ns.recalibrate(preds, 0.0, 0.25))
        new = ~p["seen"]
        self.assertTrue((p[new].groupby("Env")["M5"].nunique() == 1).all())
        np.testing.assert_allclose(p.loc[~new, "M5"], p.loc[~new, "M4"])


class Grade(unittest.TestCase):
    @staticmethod
    def results(chosen, grid24, m5_24, one):
        def f(m4, m5, g=None, o=None):
            return {"score": {"M4": {"mean_r": m4}, "M5": {"mean_r": m5}}, "grid": g,
                    "new_split": {"one_parent_seen": {"G1": {"mean_r": o}}}}
        return {"chosen": {"s": chosen[0], "o": chosen[1]},
                "folds": {"2022": f(0.32, 0.33), "2023": f(0.44, 0.44), "2024": f(0.30, m5_24, grid24, one)}}

    @staticmethod
    def grid24(points):
        g = {K(s, o): 0.28 for s in ns.S_GRID for o in ns.O_GRID}
        g.update(points)
        return g

    def test_adopt(self):
        g24 = self.grid24({K(1.0, 0.0): 0.30, K(0.75, 0.0): 0.31, K(0.0, 0.0): 0.25})
        g = ns.grade(self.results((0.75, 0.0), g24, 0.31, 0.08))
        self.assertTrue(all(v["held"] for v in g.values()), g)
        self.assertEqual(g["P2_2024_best_s_at_o0_lt_1"]["value"], 0.75)
        self.assertEqual(g["P4_M4_minus_s0_2024_ge_0.02"]["value"], 0.05)

    def test_reject(self):
        g24 = self.grid24({K(1.0, 0.0): 0.30, K(0.0, 0.0): 0.29})
        g = ns.grade(self.results((1.0, 0.5), g24, 0.30, None))
        self.assertTrue(g["P1_chosen_s_ge_0.75"]["held"])
        for name in ("P2_2024_best_s_at_o0_lt_1", "P3_G1_new_one_parent_gt_0.05",
                     "P4_M4_minus_s0_2024_ge_0.02", "P5_abs_chosen_o_le_0.25", "H1_adopt_M5"):
            self.assertFalse(g[name]["held"], name)

    def test_reproduces(self):
        f24 = {"score": {"M2": {"mean_r": 0.2802}, "M4": {"mean_r": 0.3018}}, "grid": {K(1.0, 0.0): 0.3018}}
        self.assertTrue(ns.reproduces(f24))
        f24["grid"][K(1.0, 0.0)] = 0.31
        self.assertFalse(ns.reproduces(f24))
        f24["grid"][K(1.0, 0.0)] = 0.3018
        f24["score"]["M2"]["mean_r"] = 0.29
        self.assertFalse(ns.reproduces(f24))


if __name__ == "__main__":
    unittest.main(verbosity=2)
