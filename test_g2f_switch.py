# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
"""Tests for g2f_switch 0.1.0 on small synthetic tables (no release data needed)."""
import os
import tempfile
import unittest

import numpy as np
import pandas as pd

import g2f_switch as sw

Z1 = 1.224744871391589  # z of 3 in (1, 2, 3) with the population SD


class ZscoreTest(unittest.TestCase):
    def test_within_env_missing_and_constant(self):
        df = pd.DataFrame({"Env": ["A", "A", "A", "B", "B", "A"],
                           "v": [1.0, 2.0, 3.0, 5.0, 5.0, np.nan]})
        z = sw.zscore_env(df, "v").to_numpy()
        np.testing.assert_allclose(z, [-Z1, 0.0, Z1, 0.0, 0.0, 0.0], atol=1e-9)


class MixTest(unittest.TestCase):
    def test_weights_by_category(self):
        df = pd.DataFrame({"cat": ["new_one", "seen", "new_both"], "zf": [1.0, 1.0, 1.0],
                           "zm": [0.0, 0.0, 0.0]})
        np.testing.assert_allclose(sw.mix(df, 1.0, 0.0), [1.0, 0.0, 0.0])
        np.testing.assert_allclose(sw.mix(df, 0.25, 0.75), [0.25, 0.75, 0.75])


class ChooseTest(unittest.TestCase):
    def test_ties_go_toward_m4(self):
        scores = {sw.key(a, b): 0.1 for a in sw.GRID for b in sw.GRID}
        self.assertEqual(len(scores), 25)
        scores[sw.key(1.0, 0.0)] = 0.3
        scores[sw.key(0.5, 0.5)] = 0.3
        self.assertEqual(sw.choose(scores), (0.5, 0.5))
        scores[sw.key(0.25, 0.25)] = 0.3
        self.assertEqual(sw.choose(scores), (0.25, 0.25))

    def test_missing_scores(self):
        self.assertIsNone(sw.choose({}))
        self.assertEqual(sw.choose({sw.key(0.0, 0.0): None, sw.key(1.0, 1.0): 0.2}), (1.0, 1.0))


class GridTest(unittest.TestCase):
    def test_full_perfect_m4_reversed(self):
        obs = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        df = pd.DataFrame({"Env": ["E"] * 6, "obs": obs, "full": obs,
                           "M4": [7.0 - v for v in obs],
                           "cat": ["new_one"] * 3 + ["seen"] * 3})
        df, r = sw.evaluate(df)
        grid = r["grid"]
        self.assertEqual(len(grid), 25)
        self.assertEqual(grid[sw.key(1.0, 1.0)], 1.0)
        self.assertEqual(grid[sw.key(0.0, 0.0)], -1.0)
        self.assertEqual(r["raw"], {"M4": -1.0, "full": 1.0})
        # (0.75, 0.75) also scores 1.0 and has the smaller a + b
        self.assertEqual(sw.choose(grid), (0.75, 0.75))


def _res(m4_22=0.3262, full_22=0.2987, m4_24=0.3018, full_24=0.4416, chosen_24=0.40):
    g22 = {sw.key(a, b): 0.2 for a in sw.GRID for b in sw.GRID}
    g22[sw.key(0.0, 0.0)] = 0.3262
    g22[sw.key(1.0, 1.0)] = 0.2987
    g22[sw.key(0.75, 0.25)] = 0.34
    g24 = {sw.key(a, b): 0.3 for a in sw.GRID for b in sw.GRID}
    g24[sw.key(0.0, 0.0)] = 0.3018
    g24[sw.key(1.0, 1.0)] = 0.4416
    g24[sw.key(0.75, 0.25)] = chosen_24
    return {"2022": {"raw": {"M4": m4_22, "full": full_22}, "grid": g22},
            "2024": {"raw": {"M4": m4_24, "full": full_24}, "grid": g24}}


class GradeTest(unittest.TestCase):
    def test_all_hold(self):
        g, ch = sw.grade(_res())
        self.assertEqual(ch, (0.75, 0.25))
        self.assertTrue(g["R1_reproduces_published"]["held"])
        self.assertTrue(g["Q1_chosen_a_at_least_0.5"]["held"])
        self.assertTrue(g["Q2_chosen_b_at_most_0.5"]["held"])
        self.assertEqual(g["Q3_chosen_beats_both_2022_by_0.005"]["bar"], 0.3312)
        self.assertTrue(g["Q3_chosen_beats_both_2022_by_0.005"]["held"])
        self.assertTrue(g["Q4_chosen_beats_M4_2024"]["held"])
        self.assertTrue(g["Q5_chosen_below_full_2024"]["held"])
        self.assertEqual(sw.entry_default(g, ch), "a0.75_b0.25")

    def test_failures(self):
        g, ch = sw.grade(_res(full_24=0.4425, chosen_24=0.29))
        self.assertFalse(g["R1_reproduces_published"]["held"])
        self.assertEqual(g["R1_reproduces_published"]["value"]["full_2024"]["abs_dev"], 0.0009)
        self.assertFalse(g["Q4_chosen_beats_M4_2024"]["held"])
        self.assertTrue(g["Q5_chosen_below_full_2024"]["held"])
        self.assertEqual(sw.entry_default(g, ch), "M4")

    def test_nothing_scored(self):
        g, ch = sw.grade({})
        self.assertIsNone(ch)
        self.assertFalse(g["R1_reproduces_published"]["held"])
        self.assertIsNone(g["Q4_chosen_beats_M4_2024"]["held"])
        self.assertEqual(sw.entry_default(g, ch), "M4")


class ApplyTest(unittest.TestCase):
    def test_apply_mix(self):
        df = pd.DataFrame({"Env": ["E", "E", "E"], "Hybrid": ["A/Q", "A/X", "B/Y"],
                           "M4": [1.0, 2.0, 3.0], "full": [3.0, 2.0, 1.0]})
        out = sw.apply_mix(df, ["A/Q"], 1.0, 0.0)
        self.assertEqual(list(out["cat"]), ["seen", "new_one", "new_none"])
        np.testing.assert_allclose(out["mix"].to_numpy(), [-Z1, 0.0, Z1], atol=1e-9)

    def test_apply_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            pred = os.path.join(tmp, "pred.csv")
            trait = os.path.join(tmp, "trait.csv")
            out = os.path.join(tmp, "mix.csv")
            pd.DataFrame({"Env": ["E", "E", "E"], "Hybrid": ["A/Q", "A/X", "B/Y"],
                          "m": [1.0, 2.0, 3.0], "f": [3.0, 2.0, 1.0]}).to_csv(pred, index=False)
            pd.DataFrame({"Env": ["E_2023"], "Hybrid": ["A/Q"],
                          "Yield_Mg_ha": [10.0]}).to_csv(trait, index=False)
            rc = sw.main(["apply", "--pred", pred, "--trait", trait, "--m4-col", "m", "--full-col", "f",
                          "--a", "1", "--b", "0", "--out", out])
            self.assertEqual(rc, 0)
            got = pd.read_csv(out)
            self.assertEqual(list(got.columns), ["Env", "Hybrid", "cat", "mix"])
            np.testing.assert_allclose(got["mix"].to_numpy(), [-Z1, 0.0, Z1], atol=1e-6)


if __name__ == "__main__":
    unittest.main()
