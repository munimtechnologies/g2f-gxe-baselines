# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
# Offline checks of g2f_envkernel on small synthetic data (no download).
import os
import tempfile
import unittest

import numpy as np
import pandas as pd

import g2f_baseline as gb
import g2f_envkernel as ek

LAMBDAS = (1.0, 10.0, 100.0)


def synthetic(seed=1, hybrids=120, markers=60, envs=6):
    """Same design as test_g2f_baseline.synthetic: one genetic value, no GxE."""
    rng = np.random.default_rng(seed)
    G = rng.integers(0, 3, size=(hybrids, markers)).astype(float)
    gval = G @ rng.normal(size=markers)
    gval = (gval - gval.mean()) / gval.std()
    names = ["H%03d" % i for i in range(hybrids)]
    rows = []
    for e in range(envs):
        year = 2019 + e // 2
        env = "L%d_%d" % (e % 3, year)
        base = rng.normal(10, 2)
        for i in rng.choice(hybrids, size=70, replace=False):
            rows.append({"Env": env, "Year": year, "Hybrid": names[i],
                         "Yield_Mg_ha": base + gval[i] + rng.normal(scale=0.5)})
    return names, G, pd.DataFrame(rows)


def gxe(seed=2, hybrids=150, markers=60, trained=100):
    """Two environment clusters that rank hybrids by different genetic values (gA vs gB).
    Training envs 2018-2020 (2 per cluster per year) see only the first `trained` hybrids;
    the test env T_2021 sits in cluster A and grows only untested hybrids."""
    rng = np.random.default_rng(seed)
    G = rng.integers(0, 3, size=(hybrids, markers)).astype(float)
    gA, gB = G @ rng.normal(size=markers), G @ rng.normal(size=markers)
    gA, gB = (gA - gA.mean()) / gA.std(), (gB - gB.mean()) / gB.std()
    names = ["H%03d" % i for i in range(hybrids)]
    rows, pcs = [], {}
    for year in (2018, 2019, 2020):
        for c, centre, g in (("A", 0.0, gA), ("B", 5.0, gB)):
            for k in range(2):
                env = "%s%d_%d" % (c, k, year)
                pcs[env] = np.array([centre, centre]) + rng.normal(scale=0.3, size=2)
                base = rng.normal(10, 2)
                for i in rng.choice(trained, size=80, replace=False):
                    rows.append({"Env": env, "Year": year, "Hybrid": names[i],
                                 "Yield_Mg_ha": base + g[i] + rng.normal(scale=0.3)})
    pcs["T_2021"] = np.array([0.2, 0.1])
    test = pd.DataFrame({"Env": "T_2021", "Hybrid": names[trained:],
                         "obs": 9.0 + gA[trained:] + rng.normal(scale=0.3, size=hybrids - trained)})
    return names, G, pd.DataFrame(rows), test, pcs


class EC(unittest.TestCase):
    def write(self, text):
        fd, path = tempfile.mkstemp(suffix=".csv")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        self.addCleanup(os.remove, path)
        return path

    def test_load_and_reduce(self):
        train = self.write("Env,Year,a,b,c,const,sparse,note\n"
                           "E1_2020,2020,1,5,0.1,7,,x\n"
                           "E2_2020,2020,2,3,0.4,7,,y\n"
                           "E3_2021,2021,3,9,0.2,7,1,z\n"
                           " E4_2021 ,2021,4,1,0.9,7,,w\n")
        test = self.write("a,Env,b,c\n2.5,T1_2024,4,0.5\n")
        pcs, info = ek.load_ec([train, test])
        self.assertEqual(sorted(pcs), ["E1_2020", "E2_2020", "E3_2021", "E4_2021", "T1_2024"])
        # Year, const (constant after filling), sparse (80% missing) and note (text) are dropped
        self.assertEqual(info["ec_columns"], 3)
        self.assertEqual(info["pcs"], 3)
        self.assertEqual(len(pcs["T1_2024"]), 3)
        self.assertAlmostEqual(info["variance_explained"], 1.0)


class Weights(unittest.TestCase):
    PCS = {"A": np.array([0.0, 0.0]), "B": np.array([1.0, 0.0]), "C": np.array([3.0, 0.0]),
           "T": np.array([0.1, 0.0])}
    ENVS = ["A", "B", "C", "D"]  # D has no EC row

    def test_uniform_cases(self):
        np.testing.assert_array_equal(ek.env_weights("T", self.ENVS, self.PCS, None, 1.0), np.ones(4))
        np.testing.assert_array_equal(ek.env_weights("X", self.ENVS, self.PCS, 1.0, 1.0), np.ones(4))

    def test_closer_is_heavier(self):
        w = ek.env_weights("T", self.ENVS, self.PCS, 1.0, 1.0)
        self.assertAlmostEqual(w.mean(), 1.0)
        self.assertTrue(w[0] > w[1] > w[2] > 0)
        self.assertAlmostEqual(w[3], w[1])  # missing EC row gets the median weight

    def test_scale(self):
        self.assertAlmostEqual(ek.distance_scale(["A", "B", "C", "D"], self.PCS), 4.0)  # 1, 9, 4
        self.assertEqual(ek.distance_scale(["A", "D"], self.PCS), 1.0)


class Choose(unittest.TestCase):
    def test_best_then_widest(self):
        s = {ek.label(h): {"mean_r": v, "envs": 3}
             for h, v in zip(ek.BANDWIDTHS, (0.30, 0.41, 0.41, 0.20, 0.35))}
        self.assertEqual(ek.choose(s), 1.0)
        s["uniform"]["mean_r"] = 0.41
        self.assertIsNone(ek.choose(s))
        empty = {ek.label(h): {"mean_r": None, "envs": 0} for h in ek.BANDWIDTHS}
        self.assertIsNone(ek.choose(empty))


class Model(unittest.TestCase):
    def test_uniform_reproduces_baseline_m2(self):
        names, G, trait = synthetic()
        Z = gb.standardize(G)
        train, test = gb.holdout(trait, 2021)
        base, _ = gb.fit_predict(train, test, names, Z, lambdas=LAMBDAS)
        new = pd.concat([test, pd.DataFrame({"Env": ["L0_2021"], "Hybrid": ["NEW/X"], "obs": [1.0]})],
                        ignore_index=True)
        base_new, _ = gb.fit_predict(train, new, names, Z, lambdas=LAMBDAS)
        got = ek.predict(ek.prepare(train, names, Z, LAMBDAS), new, {}, (None,))
        np.testing.assert_allclose(got["uniform"].to_numpy(), base_new["M2"].to_numpy(), atol=1e-8)
        self.assertEqual(got["uniform"].iloc[-1], 0.0)  # untested, ungenotyped hybrid
        np.testing.assert_allclose(base_new["M2"].to_numpy()[:-1], base["M2"].to_numpy(), atol=1e-12)

    def test_kernel_recovers_cluster_ranking(self):
        names, G, trait, test, pcs = gxe()
        Z = gb.standardize(G)
        preds = ek.predict(ek.prepare(trait, names, Z, LAMBDAS), test, pcs)
        r = {c: np.corrcoef(preds[c], preds["obs"])[0, 1] for c in ("h0.25", "uniform")}
        self.assertGreater(r["h0.25"], r["uniform"] + 0.1, r)
        self.assertGreater(r["h0.25"], 0.6, r)

    def test_run_fold_picks_a_kernel(self):
        names, G, trait, test, pcs = gxe()
        Z = gb.standardize(G)
        preds, info = ek.run_fold(trait, test, names, Z, pcs, 2020)
        self.assertEqual(info["inner_year"], 2020)
        self.assertIn(info["chosen"], [ek.label(h) for h in ek.BANDWIDTHS])
        self.assertNotEqual(info["chosen"], "uniform")
        self.assertGreater(info["chosen_minus_uniform"], 0.1)
        self.assertEqual(info["share_test_envs_with_ec"], 1.0)
        self.assertEqual(info["outer_scores"]["uniform"]["envs"], 1)
        self.assertEqual(len(preds), 50)


if __name__ == "__main__":
    unittest.main(verbosity=2)
