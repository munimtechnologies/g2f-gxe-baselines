# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
# Offline checks of g2f_baseline on small synthetic data (no download).
import os
import tempfile
import unittest

import numpy as np
import pandas as pd

import g2f_baseline as gb


class Names(unittest.TestCase):
    def test_env_parts(self):
        self.assertEqual(gb.env_location("DEH1_2024"), "DEH1")
        self.assertEqual(gb.env_location("TXH1-Early_2022"), "TXH1-Early")
        self.assertEqual(gb.env_year("DEH1_2024"), 2024)
        self.assertIsNone(gb.env_year("DEH1"))


class Metric(unittest.TestCase):
    def frame(self):
        return pd.DataFrame({"Env": ["A"] * 4 + ["B"] * 4 + ["C"] * 2,
                             "obs": [1, 2, 3, 4, 4, 3, 2, 1, 1, 2],
                             "good": [1, 2, 3, 4, 4, 3, 2, 1, 5, 6],
                             "flat": [1, 1, 1, 1, 2, 3, 4, 5, 0, 0]})

    def test_perfect_and_skips(self):
        rs = gb.env_r(self.frame(), "good")
        self.assertEqual(sorted(rs), ["A", "B"])  # C has 2 rows: skipped
        self.assertAlmostEqual(rs["A"], 1.0)
        self.assertAlmostEqual(rs["B"], 1.0)

    def test_constant_prediction_scores_zero(self):
        rs = gb.env_r(self.frame(), "flat")
        self.assertEqual(rs["A"], 0.0)
        self.assertAlmostEqual(rs["B"], -1.0)
        self.assertEqual(gb.score(self.frame(), ("flat",))["flat"], {"mean_r": -0.5, "envs": 2})

    def test_environment_offsets_do_not_matter(self):
        df = self.frame()
        df["shifted"] = df["good"] + df["Env"].map({"A": 100, "B": -7, "C": 3})
        plain, shifted = gb.env_r(df, "good"), gb.env_r(df, "shifted")
        self.assertEqual(sorted(plain), sorted(shifted))
        for env in plain:
            self.assertAlmostEqual(plain[env], shifted[env], places=9)


class Genotypes(unittest.TestCase):
    G = np.array([[0, 1, 2], [2, 1, 0], [1, 1, 1]], dtype=float)
    NAMES = ["H1/P", "H2/P", "H3/P"]

    def write(self, text):
        fd, path = tempfile.mkstemp(suffix=".txt")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        self.addCleanup(os.remove, path)
        return path

    def test_rows_are_hybrids_tab(self):
        text = "<Numeric>\n<Marker>\tm1\tm2\tm3\n" + "".join(
            "%s\t%s\n" % (n, "\t".join(str(int(v)) for v in r)) for n, r in zip(self.NAMES, self.G))
        names, mat = gb.read_numeric(self.write(text), set(self.NAMES))
        self.assertEqual(names, self.NAMES)
        np.testing.assert_array_equal(mat, self.G)

    def test_rows_are_markers_comma(self):
        text = "marker,%s\n" % ",".join(self.NAMES) + "".join(
            "m%d,%s\n" % (j, ",".join(str(int(v)) for v in self.G[:, j])) for j in range(3))
        names, mat = gb.read_numeric(self.write(text), set(self.NAMES) | {"other"})
        self.assertEqual(names, self.NAMES)
        np.testing.assert_array_equal(mat, self.G)

    def test_unknown_names_raise(self):
        text = "id\tm1\nX\t1\n"
        with self.assertRaises(ValueError):
            gb.read_numeric(self.write(text), {"H1/P"})

    def test_vcf(self):
        text = ("##fileformat=VCFv4.2\n"
                "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tH1/P\tskip\tH2/P\n"
                "1\t10\tm1\tA\tG\t.\t.\t.\tGT\t0/0\t1/1\t0|1\n"
                "1\t20\tm2\tC\tT\t.\t.\t.\tGT:DP\t1/1:5\t0/0:3\t./.:0\n")
        names, mat = gb.read_vcf(self.write(text), {"H1/P", "H2/P"})
        self.assertEqual(names, ["H1/P", "H2/P"])
        self.assertEqual(mat[0].tolist(), [0.0, 2.0])
        self.assertEqual(mat[1, 0], 1.0)
        self.assertTrue(np.isnan(mat[1, 1]))

    def test_standardize(self):
        G = np.array([[0, 1, np.nan, 5], [2, 1, np.nan, np.nan], [1, 1, np.nan, 7]], dtype=float)
        Z = gb.standardize(G)
        self.assertEqual(Z.shape, (3, 2))  # constant and empty markers dropped
        np.testing.assert_allclose(Z.mean(axis=0), 0, atol=1e-12)
        np.testing.assert_allclose(Z.std(axis=0), 1)


def synthetic(seed=1, hybrids=120, markers=60, envs=6):
    rng = np.random.default_rng(seed)
    G = rng.integers(0, 3, size=(hybrids, markers)).astype(float)
    effect = rng.normal(size=markers)
    gval = G @ effect
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
    return names, G, pd.DataFrame(rows), gval


class Model(unittest.TestCase):
    def test_ridge_recovers_signal(self):
        rng = np.random.default_rng(0)
        Z = rng.normal(size=(200, 30)) @ rng.normal(size=(30, 30))  # correlated markers
        y = Z @ rng.normal(size=30) + rng.normal(scale=0.3, size=200)
        mu, zmean, beta = gb.ridge_fit(Z[:150], y[:150], 1.0)
        pred = mu + (Z[150:] - zmean) @ beta
        self.assertGreater(np.corrcoef(pred, y[150:])[0, 1], 0.95)
        lam, scores = gb.choose_lambda(Z, y, (1.0, 1e6))
        self.assertEqual(lam, 1.0)
        self.assertGreater(scores[1.0], scores[1e6])

    def test_fit_predict_end_to_end(self):
        names, G, trait, gval = synthetic()
        Z = gb.standardize(G)
        train, test = gb.holdout(trait, 2021)
        self.assertEqual(sorted(train["Year"].unique()), [2019, 2020])
        preds, info = gb.fit_predict(train, test, names, Z, lambdas=(1.0, 10.0, 100.0))
        self.assertEqual(list(preds.columns), ["Env", "Hybrid", "obs", "M0", "M1", "M2", "M3"])
        self.assertEqual(info["test_envs"], 2)
        self.assertEqual(info["share_rows_hybrid_genotyped"], 1.0)
        s = gb.score(preds)
        for m in gb.MODELS:
            self.assertEqual(s[m]["envs"], 2)
            self.assertGreater(s[m]["mean_r"], 0.5, m)
        # M2 lies between M1 and the hybrid mean for a tested hybrid
        h = test["Hybrid"][test["Hybrid"].isin(train["Hybrid"])].iloc[0]
        r = preds[preds["Hybrid"] == h].iloc[0]
        self.assertTrue(min(r["M0"], r["M1"]) - 1e-12 <= r["M2"] <= max(r["M0"], r["M1"]) + 1e-12)

    def test_untested_ungenotyped_hybrid_gets_zero(self):
        names, G, trait, _ = synthetic()
        Z = gb.standardize(G)
        test = pd.DataFrame({"Env": ["L0_2024", "L0_2024"], "Hybrid": ["NEW/X", names[0]], "obs": [1.0, 2.0]})
        preds, info = gb.fit_predict(trait, test, names, Z, lambdas=(10.0,))
        new = preds[preds["Hybrid"] == "NEW/X"].iloc[0]
        self.assertEqual((new["M0"], new["M1"], new["M2"], new["M3"]), (0.0, 0.0, 0.0, 0.0))
        self.assertEqual(info["share_rows_hybrid_genotyped"], 0.5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
