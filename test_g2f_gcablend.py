# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
# Offline checks of g2f_gcablend on small synthetic data (no download).
import unittest

import numpy as np
import pandas as pd

import g2f_baseline as gb
import g2f_parentgca as pg
import g2f_gcablend as gcb
from test_g2f_parentgca import crosses

W = gcb.wkey


class Keys(unittest.TestCase):
    def test_wkey(self):
        self.assertEqual(gcb.wkey(0.0), "w=0")
        self.assertEqual(gcb.wkey(0.25), "w=0.25")
        self.assertEqual(gcb.wkey(0.5), "w=0.5")
        self.assertEqual(gcb.wkey(1.0), "w=1")


class Grid(unittest.TestCase):
    def setUp(self):
        self.names, self.G, self.trait, self.test = crosses()
        self.Z = gb.standardize(self.G)

    def test_w0_is_m2_and_half_is_parentgca_m4(self):
        base, cols, info = gcb.m4_grid(self.trait, self.test, self.names, self.Z)
        # w = 0 must reproduce M2 exactly; w = 0.5 must reproduce g2f_parentgca's M4 exactly.
        np.testing.assert_allclose(cols[0.0], base["M2"].to_numpy(), atol=1e-12)
        ref, _ = pg.fit_predict(self.trait, self.test, self.names, self.Z)
        np.testing.assert_allclose(base["G1"].to_numpy(), ref["G1"].to_numpy(), atol=1e-12)
        np.testing.assert_allclose(cols[0.5], ref["M4"].to_numpy(), atol=1e-12)
        self.assertEqual(set(cols), set(gcb.W_GRID))

    def test_seen_hybrids_shrink_like_parentgca(self):
        # A test set mixing seen (2020) and new (held-out) hybrids, as in g2f_parentgca's own test.
        seen = self.trait[self.trait["Year"] == 2020].groupby(
            ["Env", "Hybrid"], as_index=False)["Yield_Mg_ha"].mean().rename(
            columns={"Yield_Mg_ha": "obs"})
        train = self.trait[self.trait["Year"] < 2020]
        test = pd.concat([seen, self.test], ignore_index=True)
        base, cols, _ = gcb.m4_grid(train, test, self.names, self.Z)
        ref0, _ = pg.fit_predict(train, test, self.names, self.Z, w_gca=0.0)
        ref5, _ = pg.fit_predict(train, test, self.names, self.Z, w_gca=0.5)
        np.testing.assert_allclose(cols[0.0], ref0["M4"].to_numpy(), atol=1e-12)
        np.testing.assert_allclose(cols[0.5], ref5["M4"].to_numpy(), atol=1e-12)
        self.assertTrue(base["seen"].any() and not base["seen"].all())

    def test_grid_scores_all_weights(self):
        base, cols, _ = gcb.m4_grid(self.trait, self.test, self.names, self.Z)
        g = gcb.grid_scores(base, cols)
        self.assertEqual(set(g), {W(w) for w in gcb.W_GRID})
        self.assertAlmostEqual(g[W(0.0)], gb.score(base.assign(M4=base["M2"]), ("M4",))["M4"]["mean_r"])


class Select(unittest.TestCase):
    def grid(self, vals):
        return {W(w): v for w, v in zip(gcb.W_GRID, vals)}

    def test_best_mean(self):
        g22 = self.grid([0.30, 0.31, 0.32, 0.31, 0.30])
        g23 = self.grid([0.40, 0.40, 0.40, 0.40, 0.40])
        w, mean = gcb.select([g22, g23])
        self.assertEqual(w, 0.5)
        self.assertAlmostEqual(mean[W(0.5)], 0.36)

    def test_ties_go_nearest_default_then_larger(self):
        flat = self.grid([0.3, 0.3, 0.3, 0.3, 0.3])
        w, _ = gcb.select([flat, flat])
        self.assertEqual(w, 0.5)                       # all tied -> nearest default
        tied = self.grid([0.3, 0.4, 0.3, 0.4, 0.3])
        w2, _ = gcb.select([tied, tied])
        self.assertEqual(w2, 0.75)                     # 0.25 and 0.75 tie; equidistant -> larger w

    def test_argmax_w(self):
        self.assertEqual(gcb.argmax_w(self.grid([0.1, 0.2, 0.9, 0.2, 0.1])), 0.5)
        self.assertEqual(gcb.argmax_w(self.grid([0.9, 0.2, 0.1, 0.2, 0.9])), 1.0)  # ties -> larger w


class Grade(unittest.TestCase):
    @staticmethod
    def results(wstar, vals):
        return {"chosen": {"w": wstar}, "folds": {"2024": {"grid": {W(w): v for w, v
                                                                    in zip(gcb.W_GRID, vals)}}}}

    def test_adopt(self):
        g = gcb.grade(self.results(0.75, [0.28, 0.29, 0.30, 0.31, 0.31]))
        self.assertTrue(g["H1_adopt_tuned_weight"]["held"])
        self.assertEqual(g["H1_adopt_tuned_weight"]["value"]["diff_2024"], 0.01)
        self.assertFalse(g["P1_wstar_le_0.25"]["held"])
        self.assertFalse(g["P2_2024_tuned_not_above_default"]["held"])
        self.assertTrue(g["P3_2024_grid_increasing_to_default"]["held"])

    def test_reject(self):
        g = gcb.grade(self.results(0.0, [0.28, 0.29, 0.30, 0.295, 0.29]))
        self.assertTrue(g["P1_wstar_le_0.25"]["held"])
        self.assertTrue(g["P2_2024_tuned_not_above_default"]["held"])
        self.assertTrue(g["P3_2024_grid_increasing_to_default"]["held"])
        self.assertFalse(g["H1_adopt_tuned_weight"]["held"])
        self.assertEqual(g["H1_adopt_tuned_weight"]["value"]["diff_2024"], -0.02)

    def test_tie_at_default_is_not_adoption(self):
        g = gcb.grade(self.results(0.5, [0.28, 0.29, 0.30, 0.29, 0.28]))
        self.assertFalse(g["H1_adopt_tuned_weight"]["held"])  # w* == default
        self.assertEqual(g["P2_2024_tuned_not_above_default"]["value"], 0.0)

    def test_reproduces(self):
        f24 = {"grid": {W(0.0): 0.2802 + 0.004, W(0.5): 0.3018 - 0.004}}
        self.assertTrue(gcb.reproduces(f24))
        f24["grid"][W(0.5)] = 0.33
        self.assertFalse(gcb.reproduces(f24))


if __name__ == "__main__":
    unittest.main(verbosity=2)
