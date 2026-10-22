# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
# Offline checks of g2f_checkhybrid on small crafted data (no download).
import unittest

import g2f_checkhybrid as ch


def make_rows():
    """Two identical environments, each 4 seen (M0 != 0) and 4 new (M0 == 0) rows.
    Seen: M0 and M2 track obs (r=+1), M1 is reversed (r=-1). New: M0=0, M2==M1 track obs (r=+1)."""
    rows = []
    for env in ("E1", "E2"):
        for obs, m1 in [(5.0, 8.0), (6.0, 7.0), (7.0, 6.0), (8.0, 5.0)]:
            rows.append({"Env": env, "Hybrid": "S", "obs": obs,
                         "M0": obs, "M1": m1, "M2": obs, "M3": obs})
        for obs in (5.0, 6.0, 7.0, 8.0):
            rows.append({"Env": env, "Hybrid": "N", "obs": obs,
                         "M0": 0.0, "M1": obs, "M2": obs, "M3": obs})
    return rows


class Parse(unittest.TestCase):
    def test_blank_obs_is_none(self):
        rows = ch.parse("Env,Hybrid,obs,M0,M1,M2,M3\nE1,A,,0.1,0.2,0.3,0.4\nE1,B,5.0,1,2,3,4\n")
        self.assertIsNone(rows[0]["obs"])
        self.assertEqual(rows[1]["obs"], 5.0)
        self.assertEqual(rows[0]["M0"], 0.1)


class Pearson(unittest.TestCase):
    def test_cases(self):
        self.assertAlmostEqual(ch.pearson([1, 2, 3], [1, 2, 3]), 1.0)
        self.assertAlmostEqual(ch.pearson([1, 2, 3], [3, 2, 1]), -1.0)
        self.assertIsNone(ch.pearson([1, 2], [1, 2]))          # < 3 rows
        self.assertIsNone(ch.pearson([1, 1, 1], [1, 2, 3]))    # constant prediction


class Subsets(unittest.TestCase):
    def test_masks(self):
        rows = make_rows()
        self.assertEqual(sum(ch.subset_mask(rows, "all")), 16)
        self.assertEqual(sum(ch.subset_mask(rows, "seen")), 8)
        self.assertEqual(sum(ch.subset_mask(rows, "new")), 8)


class Analyze(unittest.TestCase):
    def setUp(self):
        self.r = ch.analyze(make_rows())

    def test_counts_and_checks(self):
        self.assertEqual(self.r["n_rows_seen"], 8)
        self.assertEqual(self.r["n_rows_new"], 8)
        self.assertEqual(self.r["new_m2_equals_m1_violations"], 0)
        # synthetic data does not match the real baseline scores
        self.assertFalse(self.r["reproduces_baseline"])

    def test_m0_undefined_on_new(self):
        # M0 is constant (0) on every new subset -> no within-env r anywhere
        self.assertIsNone(self.r["means"]["new"]["M0"]["mean_r"])
        self.assertEqual(self.r["means"]["new"]["M0"]["envs"], 0)

    def test_means(self):
        self.assertAlmostEqual(self.r["means"]["seen"]["M0"]["mean_r"], 1.0)
        self.assertAlmostEqual(self.r["means"]["seen"]["M1"]["mean_r"], -1.0)
        self.assertAlmostEqual(self.r["means"]["seen"]["M2"]["mean_r"], 1.0)
        self.assertAlmostEqual(self.r["means"]["new"]["M2"]["mean_r"], 1.0)

    def test_grading(self):
        g = self.r["grading"]
        self.assertFalse(g["P1_seen_defined_ge_15"]["held"])   # only 2 envs here
        self.assertEqual(g["P1_seen_defined_ge_15"]["value"], 2)
        self.assertTrue(g["P2_M0_seen_gt_0.40"]["held"])
        self.assertTrue(g["P3_M2_new_gt_0.10"]["held"])
        self.assertTrue(g["P4_abs_M2_minus_M0_seen_lt_0.10"]["held"])
        self.assertTrue(g["H1_M2_gt_M1_seen"]["held"])

    def test_violation_detected(self):
        rows = make_rows()
        rows[4]["M2"] = rows[4]["M1"] + 1.0  # a new row where M2 != M1
        self.assertEqual(ch.analyze(rows)["new_m2_equals_m1_violations"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
