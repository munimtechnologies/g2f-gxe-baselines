# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
# Offline checks of g2f_parentloc on small hand-made and synthetic data (no download).
import unittest

import numpy as np
import pandas as pd

import g2f_baseline as gb
import g2f_parentloc as pl
from test_g2f_parentgca import crosses

LAMBDAS = (1.0, 10.0, 100.0)
K = pl.key


def hand_train():
    """E1: z -1, 0, 1 for A/T, B/T, C/U. E2: z 1, -1, 0 for A/T, C/U, D/U."""
    return pd.DataFrame({"Env": ["E1_2020"] * 3 + ["E2_2020"] * 3, "Year": 2020,
                         "Hybrid": ["A/T", "B/T", "C/U", "A/T", "C/U", "D/U"],
                         "Yield_Mg_ha": [1.0, 3.0, 5.0, 4.0, 2.0, 3.0]})


class Table(unittest.TestCase):
    def test_residuals_keep_hybrids_in_two_envs(self):
        res = pl.residuals(hand_train()).sort_values(["Hybrid", "loc"]).reset_index(drop=True)
        self.assertEqual(list(res["Hybrid"]), ["A/T", "A/T", "C/U", "C/U"])
        self.assertEqual(list(res["loc"]), ["E1", "E2", "E1", "E2"])
        np.testing.assert_allclose(res["resid"], [-1.0, 1.0, 1.0, -1.0])

    def test_parent_loc_and_effect(self):
        acc = pl.parent_loc(pl.residuals(hand_train()))
        self.assertEqual(acc[("T", "E1")], (-1.0, 1))
        self.assertEqual(acc[("U", "E2")], (-1.0, 1))
        self.assertNotIn(("B", "E1"), acc)
        e = pl.effect(acc, ["X/T", "A/U", "X/Y", "T/T", "C/U"],
                      ["E1_2021", "E1_2021", "E1_2021", "E2_2021", "E9_2021"], 1.0)
        np.testing.assert_allclose(e, [-0.5, 0.0, 0.0, 0.5, 0.0])
        np.testing.assert_allclose(pl.effect(acc, ["X/T"], ["E1_2021"], 3.0), [-0.25])
        np.testing.assert_allclose(pl.effect(acc, ["X/T"], ["E1_2021"], None), [0.0])


class Choose(unittest.TestCase):
    def test_ties_go_to_larger_k_and_off(self):
        scores = {K(k): 0.3 for k in pl.K_GRID + (None,)}
        self.assertIsNone(pl.choose(scores))
        scores[K(20.0)] = scores[K(80.0)] = 0.4
        self.assertEqual(pl.choose(scores), 80.0)
        scores[K(5.0)] = 0.5
        self.assertEqual(pl.choose(scores), 5.0)


class Diagnostics(unittest.TestCase):
    def test_coverage_diversity_and_constant_g1(self):
        acc = {("T", "E1"): (1.0, 2)}
        seen_parents = {"T", "U", "A"}
        df = pd.DataFrame({
            "Env": ["E1_2021"] * 4 + ["E2_2021"] * 4,
            "Hybrid": ["N1/T", "N2/T", "N3/T", "A/T", "N4/T", "N5/U", "N6/T", "N7/X"],
            "seen": [False, False, False, True, False, False, False, False],
            "obs": [1.0, 2.0, 3.0, 4.0, 1.0, 2.0, 3.0, np.nan],
            "G1": [0.2, 0.2, 0.2, 0.9, 0.2, 0.5, 0.2, 0.0]})
        d = pl.diagnostics(df, acc, seen_parents)
        self.assertEqual(d["new_rows"], 6)
        self.assertAlmostEqual(d["share_new_rows_parent_at_location"], 0.5)
        self.assertEqual(d["distinct_seen_parents_per_env"], {"median": 1.5, "min": 1, "envs": 2})
        self.assertEqual(d["one_parent_envs"], 2)
        self.assertAlmostEqual(d["share_one_parent_envs_constant_G1"], 0.5)
        empty = pl.diagnostics(df.assign(seen=True), acc, seen_parents)
        self.assertEqual(empty["new_rows"], 0)
        self.assertIsNone(empty["share_one_parent_envs_constant_G1"])


class Fold(unittest.TestCase):
    def setUp(self):
        self.names, self.G, self.trait, self.test = crosses()
        self.Z = gb.standardize(self.G)

    def test_new_location_gives_m4(self):
        preds, acc, entry = pl.fold(self.trait, self.test, self.names, self.Z, lambdas=LAMBDAS)
        self.assertEqual(len(entry["grid"]), len(pl.K_GRID) + 1)
        self.assertGreater(entry["parent_locations"], 0)
        for k in pl.K_GRID:
            np.testing.assert_allclose(pl.with_m6(preds, acc, k)["M6"], preds["M4"])
            self.assertAlmostEqual(entry["grid"][K(k)], entry["grid"]["off"], places=6)
        self.assertEqual(entry["diagnostics"]["share_new_rows_parent_at_location"], 0.0)

    def test_seen_location_moves_predictions(self):
        test = self.test.assign(Env="L0_2021")
        preds, acc, entry = pl.fold(self.trait, test, self.names, self.Z, lambdas=LAMBDAS)
        m4 = gb.score(preds, ("M4",))["M4"]["mean_r"]
        self.assertAlmostEqual(entry["grid"]["off"], m4, places=6)
        self.assertGreater(entry["diagnostics"]["share_new_rows_parent_at_location"], 0.9)
        m6 = pl.with_m6(preds, acc, 5.0)["M6"].to_numpy()
        self.assertFalse(np.allclose(m6, preds["M4"].to_numpy()))
        big = pl.with_m6(preds, acc, 1e9)["M6"].to_numpy()
        np.testing.assert_allclose(big, preds["M4"].to_numpy(), atol=1e-6)


class Grade(unittest.TestCase):
    @staticmethod
    def results(m6_24, m6_23, new, at_loc, distinct, const):
        def f(m4, m6, diag=None, new_m4=None, new_m6=None):
            return {"score": {"M4": {"mean_r": m4}, "M6": {"mean_r": m6}},
                    "score_new": {"M4": {"mean_r": new_m4}, "M6": {"mean_r": new_m6}},
                    "diagnostics": diag}
        d24 = {"share_new_rows_parent_at_location": at_loc,
               "distinct_seen_parents_per_env": {"median": distinct, "min": 1, "envs": 22}}
        d22 = {"share_one_parent_envs_constant_G1": const}
        return {"folds": {"2022": f(0.33, 0.34, d22), "2023": f(0.44, m6_23),
                          "2024": f(0.30, m6_24, d24, 0.12, new)}}

    def test_adopt(self):
        g = pl.grade(self.results(0.315, 0.437, 0.13, 0.9, 4.0, 0.6))
        self.assertTrue(all(v["held"] for v in g.values()), g)
        self.assertEqual(g["H1_adopt_M6"]["value"], {"2023": -0.003, "2024": 0.015})
        self.assertEqual(g["P5_M6_minus_M4_2024_new_rows_gt_0"]["value"], 0.01)

    def test_reject(self):
        g = pl.grade(self.results(0.33, 0.43, 0.11, 0.5, 2.0, None))
        for name in g:
            self.assertFalse(g[name]["held"], name)

    def test_reproduces(self):
        f24 = {"score": {"M2": {"mean_r": 0.2802}, "M4": {"mean_r": 0.3018}}, "grid": {"off": 0.3018}}
        self.assertTrue(pl.reproduces(f24))
        f24["grid"]["off"] = 0.31
        self.assertFalse(pl.reproduces(f24))
        f24["grid"]["off"] = 0.3018
        f24["score"]["M4"]["mean_r"] = 0.32
        self.assertFalse(pl.reproduces(f24))


if __name__ == "__main__":
    unittest.main(verbosity=2)
