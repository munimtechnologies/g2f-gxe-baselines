# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
# Offline checks of g2f_ecreaction on small hand-made and synthetic data (no download).
import os
import tempfile
import unittest

import numpy as np
import pandas as pd

import g2f_baseline as gb
import g2f_ecreaction as ec
from test_g2f_parentgca import crosses

LAMBDAS = (1.0, 10.0, 100.0)
A = ec.akey


def env_map(trait, test, l=2, seed=1):
    """A random standardized EC-PC vector for every environment in the folds."""
    rng = np.random.default_rng(seed)
    envs = sorted(set(trait["Env"]) | set(test["Env"]))
    V = ec._standardize_cols(rng.normal(size=(len(envs), l)))
    return {e: V[i] for i, e in enumerate(envs)}


class Features(unittest.TestCase):
    def test_kron_layout(self):
        U = np.array([[1.0, 2.0], [3.0, 4.0]])
        E = np.array([[5.0, 6.0, 7.0], [8.0, 9.0, 10.0]])
        X = ec.features(U, E)
        self.assertEqual(X.shape, (2, 2 + 3 + 6))
        np.testing.assert_allclose(X[0, :2], [1.0, 2.0])
        np.testing.assert_allclose(X[0, 2:5], [5.0, 6.0, 7.0])
        np.testing.assert_allclose(X[0, 5:], [5.0, 6.0, 7.0, 10.0, 12.0, 14.0])

    def test_r_int_is_bilinear(self):
        umap = {"A/B": np.array([1.0, 0.0]), "C/D": np.array([0.0, 2.0])}
        emap = {"E1_2020": np.array([1.0, -1.0, 0.5]), "E2_2020": np.array([0.0, 0.0, 0.0])}
        B = np.arange(6, dtype=float).reshape(2, 3)
        preds = pd.DataFrame({"Hybrid": ["A/B", "C/D", "X/Y", "A/B"],
                              "Env": ["E1_2020", "E1_2020", "E1_2020", "E2_2020"]})
        r = ec.r_int(preds, umap, emap, B)
        np.testing.assert_allclose(r[0], np.array([1.0, 0.0]) @ B @ np.array([1.0, -1.0, 0.5]))
        np.testing.assert_allclose(r[1], np.array([0.0, 2.0]) @ B @ np.array([1.0, -1.0, 0.5]))
        self.assertEqual(r[2], 0.0)   # unknown hybrid
        self.assertEqual(r[3], 0.0)   # zero EC vector


class Choose(unittest.TestCase):
    def test_ties_go_to_smaller_alpha(self):
        grid = {A(a): 0.3 for a in (0.0,) + ec.ALPHA_GRID}
        self.assertEqual(ec.choose(grid), 0.0)
        grid[A(1.0)] = grid[A(2.0)] = 0.4
        self.assertEqual(ec.choose(grid), 1.0)
        grid[A(0.5)] = 0.5
        self.assertEqual(ec.choose(grid), 0.5)


class LoadEC(unittest.TestCase):
    def test_pcs_and_standardized(self):
        rng = np.random.default_rng(0)
        envs = ["L%d_2020" % i for i in range(8)]
        df = pd.DataFrame(rng.normal(size=(8, 6)), columns=["c%d" % j for j in range(6)])
        df.insert(0, "Env", envs)
        df["Year"] = 2020
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "ec.csv")
            df.to_csv(path, index=False)
            emap, info = ec.load_ec([path], l=3)
        self.assertEqual(info["ec_pcs"], 3)
        self.assertEqual(info["ec_columns"], 6)   # Year dropped
        self.assertEqual(set(emap), set(envs))
        M = np.array([emap[e] for e in envs])
        np.testing.assert_allclose(M.mean(axis=0), 0.0, atol=1e-9)
        np.testing.assert_allclose(M.std(axis=0), 1.0, atol=1e-9)


class Fit(unittest.TestCase):
    def setUp(self):
        self.names, self.G, self.trait, self.test = crosses()
        self.Z = gb.standardize(self.G)
        self.umap, self.k = ec.marker_scores(self.names, self.Z, k=3)
        self.emap = env_map(self.trait, self.test, l=2)

    def test_marker_scores_standardized(self):
        M = np.array([self.umap[n] for n in self.names])
        self.assertEqual(M.shape[1], 3)
        np.testing.assert_allclose(M.mean(axis=0), 0.0, atol=1e-9)
        np.testing.assert_allclose(M.std(axis=0), 1.0, atol=1e-9)

    def test_fold_alpha0_is_m4_and_interaction_active(self):
        preds, rint, entry = ec.fold(self.trait, self.test, self.names, self.Z, self.umap, self.emap,
                                     self.k, 2, lambdas=LAMBDAS)
        m4 = gb.score(preds, ("M4",))["M4"]["mean_r"]
        self.assertAlmostEqual(entry["grid"][A(0.0)], m4, places=6)
        np.testing.assert_allclose(ec.with_m7(preds, rint, 0.0)["M7"], preds["M4"])
        self.assertEqual(len(entry["grid"]), len(ec.ALPHA_GRID) + 1)
        self.assertGreater(entry["fit"]["interaction_features"], 0)
        self.assertTrue(np.any(rint != 0.0))   # a reaction norm that moves at least some rows
        m7 = ec.with_m7(preds, rint, 1.0)["M7"].to_numpy()
        self.assertFalse(np.allclose(m7, preds["M4"].to_numpy()))

    def test_fit_rn_too_few_rows_returns_zero_block(self):
        tiny = self.trait.head(5)
        rn = ec.fit_rn(tiny, self.umap, self.emap, self.k, 2, lambdas=LAMBDAS)
        np.testing.assert_array_equal(rn["B"], np.zeros((self.k, 2)))

    def test_cv_grouped_returns_a_lambda(self):
        U, E, y, groups = ec.observations(self.trait, self.umap, self.emap)
        X = ec.features(U, E)
        lam, scores = ec.cv_grouped(X, y, groups, lambdas=LAMBDAS)
        self.assertIn(lam, LAMBDAS)
        self.assertEqual(set(scores), set(LAMBDAS))


class Grade(unittest.TestCase):
    @staticmethod
    def results(m7_24, m7_23, new_m7, cv24, ratio24, alpha):
        def f(m4, m7, new_m4=None, new_m7=None, cv=None, ratio=None):
            return {"score": {"M4": {"mean_r": m4}, "M7": {"mean_r": m7}},
                    "score_new": {"M4": {"mean_r": new_m4}, "M7": {"mean_r": new_m7}},
                    "rn_cv_r": cv, "diagnostics": {"int_main_sd_ratio": ratio}}
        return {"chosen": {"alpha": alpha},
                "folds": {"2022": f(0.33, 0.34), "2023": f(0.44, m7_23),
                          "2024": f(0.30, m7_24, 0.12, new_m7, cv24, ratio24)}}

    def test_adopt(self):
        g = ec.grade(self.results(0.315, 0.437, 0.13, 0.45, 0.2, 1.0))
        self.assertTrue(all(v["held"] for v in g.values()), g)
        self.assertEqual(g["H1_adopt_M7"]["value"], {"2023": -0.003, "2024": 0.015})
        self.assertEqual(g["P5_M7_minus_M4_2024_new_rows_gt_0"]["value"], 0.01)

    def test_reject(self):
        g = ec.grade(self.results(0.285, 0.43, 0.11, 0.2, 0.01, 0.0))
        for name in g:
            self.assertFalse(g[name]["held"], name)

    def test_reproduces(self):
        f24 = {"score": {"M2": {"mean_r": 0.2802}, "M4": {"mean_r": 0.3018}}, "grid": {"a=0": 0.3018}}
        self.assertTrue(ec.reproduces(f24))
        f24["grid"]["a=0"] = 0.31
        self.assertFalse(ec.reproduces(f24))
        f24["grid"]["a=0"] = 0.3018
        f24["score"]["M4"]["mean_r"] = 0.32
        self.assertFalse(ec.reproduces(f24))


if __name__ == "__main__":
    unittest.main(verbosity=2)
