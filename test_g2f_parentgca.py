# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
# Offline checks of g2f_parentgca on small synthetic data (no download).
import unittest

import numpy as np
import pandas as pd

import g2f_baseline as gb
import g2f_parentgca as pg

LAMBDAS = (1.0, 10.0, 100.0)


def crosses(seed=3, females=40, testers=4, markers=50, held_out=30):
    """Inbred females x testers. A hybrid's genotype and genetic value are the mean of its parents', so
    its yield is exactly additive in parent effects. Training envs 2019-2020 grow only training crosses;
    the test env T_2021 grows the held-out crosses (new hybrids, mostly from seen parents)."""
    rng = np.random.default_rng(seed)
    Gf = 2.0 * rng.integers(0, 2, size=(females, markers))
    Gt = 2.0 * rng.integers(0, 2, size=(testers, markers))
    beta = rng.normal(size=markers)
    names, G = [], []
    for i in range(females):
        for t in range(testers):
            names.append("F%02d/T%d" % (i, t))
            G.append((Gf[i] + Gt[t]) / 2.0)
    G = np.array(G)
    gv = G @ beta
    gv = (gv - gv.mean()) / gv.std()
    order = rng.permutation(len(names))
    test_i, train_i = order[:held_out], order[held_out:]
    rows = []
    for e in range(4):
        year = 2019 + e // 2
        base = rng.normal(10, 2)
        for i in rng.choice(train_i, size=100, replace=False):
            rows.append({"Env": "L%d_%d" % (e, year), "Year": year, "Hybrid": names[i],
                         "Yield_Mg_ha": base + gv[i] + rng.normal(scale=0.3)})
    test = pd.DataFrame({"Env": "T_2021", "Hybrid": [names[i] for i in test_i],
                         "obs": 9.0 + gv[test_i] + rng.normal(scale=0.3, size=held_out)})
    return names, G, pd.DataFrame(rows), test


class Names(unittest.TestCase):
    def test_parents(self):
        self.assertEqual(pg.parents("A/B"), ("A", "B"))
        self.assertEqual(pg.parents(" w10010_0346 / php02 "), ("W10010_0346", "PHP02"))
        self.assertEqual(pg.parents("DKC62-08"), ())
        self.assertEqual(pg.parents("A/B/C"), ())
        self.assertEqual(pg.parents("A/"), ())

    def test_design(self):
        X = pg.design(["A/B", "B/C", "A/A", "X/Y", "CHECK1"], {"A": 0, "B": 1, "C": 2})
        np.testing.assert_array_equal(X, [[1, 1, 0], [0, 1, 1], [1, 0, 0], [0, 0, 0], [0, 0, 0]])

    def test_coverage(self):
        c = pg.coverage(["A/B", "A/Z", "Y/Z", "CHECK1"], {"A": 0, "B": 1})
        self.assertEqual(c, {"rows": 4, "named_cross": 0.75, "one_parent_seen": 0.5,
                             "both_parents_seen": 0.25})
        self.assertIsNone(pg.coverage([], {})["one_parent_seen"])


class Model(unittest.TestCase):
    def setUp(self):
        self.names, self.G, self.trait, self.test = crosses()
        self.Z = gb.standardize(self.G)

    def test_gca_ranks_new_crosses_of_seen_parents(self):
        gca = pg.fit_gca(self.trait, pg.GCA_LAMBDAS)
        self.assertEqual(gca["gca_hybrids"], gca["train_hybrids"])
        self.assertLessEqual(gca["parents"], 44)
        pred = pg.predict_gca(gca, list(self.test["Hybrid"]))
        r = np.corrcoef(pred, self.test["obs"])[0, 1]
        self.assertGreater(r, 0.7, r)

    def test_unknown_parents_share_one_value(self):
        gca = pg.fit_gca(self.trait, pg.GCA_LAMBDAS)
        p = pg.predict_gca(gca, ["NEW1/NEW2", "CHECK-9", "Q/R"])
        self.assertAlmostEqual(p[0], p[1])
        self.assertAlmostEqual(p[0], p[2])

    def test_baseline_columns_unchanged_and_m4(self):
        base, _ = gb.fit_predict(self.trait, self.test, self.names, self.Z, lambdas=LAMBDAS)
        out, info = pg.fit_predict(self.trait, self.test, self.names, self.Z, lambdas=LAMBDAS)
        for m in gb.MODELS:
            np.testing.assert_allclose(out[m].to_numpy(), base[m].to_numpy(), atol=1e-12)
        self.assertFalse(out["seen"].any())
        np.testing.assert_allclose(out["M4"], 0.5 * out["M1"] + 0.5 * out["G1"], atol=1e-12)
        self.assertEqual(info["coverage_new_rows"]["rows"], 30)
        self.assertEqual(info["coverage_new_rows"]["named_cross"], 1.0)
        self.assertGreater(info["coverage_new_rows"]["one_parent_seen"], 0.9)

    def test_zero_weight_is_m2_for_seen_hybrids(self):
        seen = self.trait[self.trait["Year"] == 2020].groupby(
            ["Env", "Hybrid"], as_index=False)["Yield_Mg_ha"].mean().rename(columns={"Yield_Mg_ha": "obs"})
        train = self.trait[self.trait["Year"] < 2020]
        test = pd.concat([seen, self.test], ignore_index=True)
        out, _ = pg.fit_predict(train, test, self.names, self.Z, lambdas=LAMBDAS, w_gca=0.0)
        np.testing.assert_allclose(out["M4"].to_numpy(), out["M2"].to_numpy(), atol=1e-12)
        self.assertTrue(out["seen"].any() and not out["seen"].all())
        out5, _ = pg.fit_predict(train, test, self.names, self.Z, lambdas=LAMBDAS)
        s = out5["seen"].to_numpy()
        self.assertFalse(np.allclose(out5["M4"].to_numpy()[s], out5["M2"].to_numpy()[s]))


class Grade(unittest.TestCase):
    @staticmethod
    def fold(m2, m4, g1_new=None, one=None, both=None):
        f = {"score": {"M2": {"mean_r": m2}, "M4": {"mean_r": m4}}}
        if g1_new is not None:
            f["score_new"] = {"G1": {"mean_r": g1_new}}
            f["fit"] = {"coverage_new_rows": {"one_parent_seen": one, "both_parents_seen": both}}
        return f

    def test_adopt(self):
        g = pg.grade({"2022": self.fold(0.32, 0.318), "2023": self.fold(0.43, 0.44),
                      "2024": self.fold(0.28, 0.295, 0.08, 0.9, 0.3)})
        self.assertTrue(all(v["held"] for v in g.values()), g)
        self.assertEqual(g["H1_adopt_M4"]["value"]["2024"], 0.015)

    def test_reject(self):
        g = pg.grade({"2022": self.fold(0.32, 0.31), "2023": self.fold(0.43, 0.44),
                      "2024": self.fold(0.28, 0.295, 0.03, 0.4, 0.1)})
        self.assertFalse(g["H1_adopt_M4"]["held"])  # 2022 fell by 0.01
        self.assertFalse(g["P1_one_parent_seen_ge_0.50"]["held"])
        self.assertFalse(g["P2_both_parents_seen_ge_0.20"]["held"])
        self.assertFalse(g["P3_G1_new_gt_0.05"]["held"])
        self.assertTrue(g["P4_M4_minus_M2_2024_in_-0.02_0.04"]["held"])

    def test_reproduces(self):
        ok = {m: {"mean_r": v + 0.004} for m, v in pg.BASELINE_2024.items()}
        self.assertTrue(pg.reproduces(ok))
        ok["M2"]["mean_r"] = 0.29
        self.assertFalse(pg.reproduces(ok))


if __name__ == "__main__":
    unittest.main(verbosity=2)
