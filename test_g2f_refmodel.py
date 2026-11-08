# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
"""Tests for g2f_refmodel 0.1.0 (scoring, leaderboard place, blend and grading; no data needed)."""
import math
import os
import tempfile
import unittest

import numpy as np
import pandas as pd

import g2f_refmodel as gr


def frame(rows):
    return pd.DataFrame(rows, columns=["Env", "Hybrid", "obs", "p"])


class Metric(unittest.TestCase):
    def setUp(self):
        rows = []
        for i, (o, p) in enumerate(zip([1, 2, 3], [1, 2, 3])):
            rows.append(("A", "h%d" % i, o, p))          # r = 1
        for i, (o, p) in enumerate(zip([1, 2, 3], [3, 2, 1])):
            rows.append(("B", "h%d" % i, o, p))          # r = -1
        for i, (o, p) in enumerate(zip([1, 2], [1, 2])):
            rows.append(("C", "h%d" % i, o, p))          # 2 rows: skipped
        for i, o in enumerate([1, 2, 3]):
            rows.append(("D", "h%d" % i, o, 5.0))        # constant prediction: 0
        for i, p in enumerate([1, 2, 3]):
            rows.append(("E", "h%d" % i, 4.0, p))        # constant observations: skipped
        for i, (o, p) in enumerate(zip([1, 2, 3, 4], [1, 2, 3, float("nan")])):
            rows.append(("F", "h%d" % i, o, p))          # NaN row dropped, 3 left: r = 1
        self.df = frame(rows)

    def test_env_r(self):
        rs = gr.env_r(self.df, "p")
        self.assertEqual(sorted(rs), ["A", "B", "D", "F"])
        self.assertAlmostEqual(rs["A"], 1.0, places=9)
        self.assertAlmostEqual(rs["B"], -1.0, places=9)
        self.assertEqual(rs["D"], 0.0)
        self.assertAlmostEqual(rs["F"], 1.0, places=9)

    def test_mean_r(self):
        self.assertEqual(gr.mean_r(self.df, "p"), (0.25, 4))
        self.assertEqual(gr.mean_r(self.df, "missing"), (None, 0))
        self.assertEqual(gr.mean_r(self.df[self.df["Env"] == "C"], "p"), (None, 0))


class Leaderboard(unittest.TestCase):
    def test_board(self):
        b = gr.LEADERBOARD_2024
        self.assertEqual(len(b), 64)
        self.assertTrue(all(b[i] >= b[i + 1] for i in range(63)))
        self.assertEqual(b[0], 0.450054)
        self.assertEqual(b[39], 0.301745)
        self.assertEqual(b[63], -0.024543)

    def test_place(self):
        self.assertEqual(gr.place(0.3018), 40)                       # M4
        self.assertEqual(gr.place(gr.REFERENCE_LEADERBOARD), 3)      # 0.43766 vs rounded 0.437658
        self.assertEqual(gr.place(0.5), 1)
        self.assertEqual(gr.place(-0.5), 65)
        self.assertIsNone(gr.place(None))


class Blend(unittest.TestCase):
    def test_zwithin(self):
        df = pd.DataFrame({"Env": ["A", "A", "A", "K", "K"], "x": [1.0, 2.0, 3.0, 7.0, 7.0]})
        z = gr.zwithin(df, "x").to_numpy()
        self.assertAlmostEqual(z[0], -math.sqrt(1.5), places=9)
        self.assertAlmostEqual(z[1], 0.0, places=12)
        self.assertAlmostEqual(z[2], math.sqrt(1.5), places=9)
        self.assertEqual(list(z[3:]), [0.0, 0.0])

    def test_blend_opposites_cancel(self):
        df = pd.DataFrame({"Env": ["A"] * 3, "a": [1.0, 2.0, 3.0], "b": [3.0, 2.0, 1.0]})
        out = gr.blend(df, "a", "b").to_numpy()
        for v in out:
            self.assertAlmostEqual(v, 0.0, places=12)
        same = gr.blend(df, "a", "a").to_numpy()
        self.assertAlmostEqual(same[2], math.sqrt(1.5), places=9)


class Files(unittest.TestCase):
    def test_read_pairs_averages_duplicates(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.csv")
            pd.DataFrame({"Env": ["E1", "E1 ", "E1"], "Hybrid": ["H1", "H1", "H2"],
                          "Yield_Mg_ha": [5.0, 7.0, 3.0]}).to_csv(p, index=False)
            out = gr.read_pairs(p, "ref").set_index("Hybrid")["ref"]
            self.assertEqual(out["H1"], 6.0)
            self.assertEqual(out["H2"], 3.0)
            self.assertEqual(len(gr.read_pairs(p)), 2)

    def test_fold_obs(self):
        t = pd.DataFrame({"Env": ["X_2022", "X_2022", "X_2023"], "Year": [2022, 2022, 2023],
                          "Hybrid": ["H", "H", "H"], "Yield_Mg_ha": [8.0, 10.0, 1.0]})
        o = gr.fold_obs(t, "2022")
        self.assertEqual(list(o.columns), ["Env", "Hybrid", "obs"])
        self.assertEqual(o["obs"].tolist(), [9.0])


class Grade(unittest.TestCase):
    def test_all_hold(self):
        s = {"2024": {"ref": 0.4377, "full": 0.4370, "b1": 0.40, "b2": 0.42, "allloc": 0.43,
                      "blend": 0.41, "full_new": 0.30},
             "2023": {"full": 0.44}, "2022": {"full": 0.33}}
        g = gr.grade(s)
        self.assertEqual(g["G1_harness_matches_leaderboard"], {"value": 0.0, "held": True})
        self.assertEqual(g["G2_reimplementation_matches_reference"], {"value": 0.0007, "held": True})
        self.assertEqual(g["P1_reference_beats_M4_2024_by_0.10"], {"value": 0.1359, "held": True})
        self.assertEqual(g["P2_full_beats_M4_2022_and_2023"], {"value": [0.0038, 0.0046], "held": True})
        self.assertEqual(g["P3_state_effects_at_least_global_2024"], {"value": 0.02, "held": True})
        self.assertEqual(g["P4_test_state_filter_helps_2024"], {"value": 0.007, "held": True})
        self.assertEqual(g["P5_blend_with_M4_below_full_2024"], {"value": -0.027, "held": True})
        self.assertEqual(g["P6_full_new_hybrids_at_least_0.25"], {"value": 0.30, "held": True})
        self.assertEqual(g["H1_switch_entry_baseline"]["value"],
                         {"gain_2024": 0.1359, "full_mean_2022_2023": 0.385, "m4_mean_2022_2023": 0.3808})
        self.assertTrue(g["H1_switch_entry_baseline"]["held"])

    def test_missing_reference_and_folds(self):
        g = gr.grade({"2024": {"full": 0.35}})
        self.assertEqual(g["G1_harness_matches_leaderboard"], {"value": None, "held": False})
        self.assertEqual(g["G2_reimplementation_matches_reference"], {"value": None, "held": False})
        self.assertEqual(g["P1_reference_beats_M4_2024_by_0.10"], {"value": 0.0482, "held": False})
        self.assertEqual(g["P2_full_beats_M4_2022_and_2023"], {"value": [None, None], "held": False})
        for k in ("P3_state_effects_at_least_global_2024", "P4_test_state_filter_helps_2024",
                  "P5_blend_with_M4_below_full_2024", "P6_full_new_hybrids_at_least_0.25"):
            self.assertEqual(g[k], {"value": None, "held": False}, k)
        self.assertFalse(g["H1_switch_entry_baseline"]["held"])

    def test_thresholds_are_inclusive(self):
        g = gr.grade({"2024": {"ref": 0.4018, "full": 0.4068, "b1": 0.3, "b2": 0.3, "allloc": 0.4018,
                               "full_new": 0.25}})
        self.assertEqual(g["P1_reference_beats_M4_2024_by_0.10"], {"value": 0.1, "held": True})
        self.assertEqual(g["G2_reimplementation_matches_reference"], {"value": 0.005, "held": True})
        self.assertEqual(g["P3_state_effects_at_least_global_2024"], {"value": 0.0, "held": True})
        self.assertEqual(g["P4_test_state_filter_helps_2024"], {"value": 0.005, "held": True})
        self.assertEqual(g["P6_full_new_hybrids_at_least_0.25"], {"value": 0.25, "held": True})
        self.assertEqual(g["G1_harness_matches_leaderboard"], {"value": 0.0359, "held": False})


if __name__ == "__main__":
    unittest.main()
