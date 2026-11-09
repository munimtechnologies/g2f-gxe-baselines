# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
"""Tests for g2f_entry.py on small synthetic files (standard library only)."""
import csv
import os
import shutil
import tempfile
import unittest

import g2f_entry as ge


def write_csv(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)
    return path


TEMPLATE_ROWS = [["A_2024", "P1/T1", ""], ["A_2024", "P2/T1", ""], ["A_2024", "P3/T1", ""],
                 ["A_2024", "P4/T1", ""], ["B_2024", "P1/T1", ""], ["B_2024", "P5/T2", ""],
                 ["B_2024", "P6/T2", ""], ["B_2024", "P7/T2", ""]]
PRED = {("A_2024", "P1/T1"): 1.0, ("A_2024", "P2/T1"): 2.0, ("A_2024", "P3/T1"): 3.0,
        ("A_2024", "P4/T1"): 4.0, ("B_2024", "P1/T1"): 1.0, ("B_2024", "P5/T2"): 2.0,
        ("B_2024", "P6/T2"): 3.0, ("B_2024", "P7/T2"): 4.0}


class EntryTest(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.template = write_csv(os.path.join(self.d, "1_Submission_Template_2024.csv"),
                                  ["Env", "Hybrid", "Yield_Mg_ha"], TEMPLATE_ROWS)

    def tearDown(self):
        shutil.rmtree(self.d)

    def p(self, name):
        return os.path.join(self.d, name)

    def test_write_keeps_template_order_and_validates(self):
        out = self.p("sub.csv")
        info = ge.write_submission(self.template, dict(reversed(list(PRED.items()))), out)
        self.assertEqual(info, {"rows": 8, "missing_predictions": 0, "filled_by_env_mean": 0})
        header, rows = ge.read_csv(out)
        self.assertEqual(header, ["Env", "Hybrid", "Yield_Mg_ha"])
        self.assertEqual([r[:2] for r in rows], [r[:2] for r in TEMPLATE_ROWS])
        self.assertEqual(rows[1][2], "2.000000")
        v = ge.validate_submission(self.template, out)
        self.assertTrue(v["ok"], v)
        self.assertEqual(v["errors"], [])
        self.assertEqual(v["warnings"], [])
        self.assertEqual(v["envs"], 2)

    def test_missing_prediction_raises_or_fills_env_mean(self):
        preds = dict(PRED)
        del preds[("A_2024", "P4/T1")]
        with self.assertRaises(ValueError):
            ge.write_submission(self.template, preds, self.p("sub.csv"))
        info = ge.write_submission(self.template, preds, self.p("sub.csv"), fill="env_mean")
        self.assertEqual(info["missing_predictions"], 1)
        self.assertEqual(info["filled_by_env_mean"], 1)
        _h, rows = ge.read_csv(self.p("sub.csv"))
        self.assertEqual(rows[3][2], "2.000000")  # mean of 1, 2, 3 in A_2024

    def test_non_finite_prediction_raises(self):
        preds = dict(PRED)
        preds[("A_2024", "P1/T1")] = float("nan")
        with self.assertRaises(ValueError):
            ge.write_submission(self.template, preds, self.p("sub.csv"))

    def test_template_without_yield_column_gets_one(self):
        t = write_csv(self.p("t2_submission_template.csv"), ["Env", "Hybrid"], [r[:2] for r in TEMPLATE_ROWS])
        out = self.p("sub.csv")
        ge.write_submission(t, PRED, out)
        header, _rows = ge.read_csv(out)
        self.assertEqual(header, ["Env", "Hybrid", "Yield_Mg_ha"])
        self.assertTrue(ge.validate_submission(t, out)["ok"])

    def test_every_fault_is_rejected(self):
        out = self.p("sub.csv")
        ge.write_submission(self.template, PRED, out)
        res = ge.fault_checks(self.template, out, self.d)
        self.assertEqual(sorted(res), sorted(ge.FAULTS))
        for kind, r in res.items():
            self.assertTrue(r["rejected"], kind)
            self.assertTrue(r["errors"], kind)
        self.assertFalse(any(n.startswith("fault_") for n in os.listdir(self.d)))

    def test_constant_environment_warns(self):
        preds = dict(PRED)
        for k in [k for k in preds if k[0] == "B_2024"]:
            preds[k] = 5.0
        out = self.p("sub.csv")
        ge.write_submission(self.template, preds, out)
        v = ge.validate_submission(self.template, out)
        self.assertTrue(v["ok"])
        self.assertEqual(len(v["warnings"]), 1)
        self.assertIn("B_2024", v["warnings"][0])

    def test_out_of_range_warns(self):
        preds = {k: v - 2.5 for k, v in PRED.items()}
        out = self.p("sub.csv")
        ge.write_submission(self.template, preds, out)
        v = ge.validate_submission(self.template, out)
        self.assertTrue(v["ok"])
        self.assertTrue(any("outside 0-30" in w for w in v["warnings"]))

    def test_conflicting_duplicate_raises_equal_duplicate_ok(self):
        f = write_csv(self.p("pred.csv"), ["Env", "Hybrid", "M4"],
                      [["A_2024", "P1/T1", "1"], ["A_2024", "P1/T1", "2"]])
        with self.assertRaises(ValueError):
            ge.read_values(f, "M4")
        self.assertEqual(ge.read_values(f, "M4", dup="mean"), {("A_2024", "P1/T1"): 1.5})
        g = write_csv(self.p("pred2.csv"), ["Env", "Hybrid", "M4"],
                      [["A_2024", "P1/T1", "1"], ["A_2024", "P1/T1", "1.0"], ["A_2024", "P2/T1", "NA"]])
        self.assertEqual(ge.read_values(g, "M4"), {("A_2024", "P1/T1"): 1.0})

    def test_score_by_hand(self):
        out = self.p("sub.csv")
        ge.write_submission(self.template, PRED, out)
        # A: obs rise with predictions (r = 1). B: obs fall (r = -1). C has 2 rows only (skipped).
        obs = write_csv(self.p("7_Testing_Observed_Values.csv"), ["Env", "Hybrid", "Yield_Mg_ha"],
                        [["A_2024", "P1/T1", "5"], ["A_2024", "P2/T1", "6"], ["A_2024", "P3/T1", "7"],
                         ["A_2024", "P4/T1", "8"], ["B_2024", "P1/T1", "9"], ["B_2024", "P5/T2", "8"],
                         ["B_2024", "P6/T2", "7"], ["B_2024", "P7/T2", "6"], ["C_2024", "P1/T1", "1"]])
        s = ge.score_submission(out, obs)
        self.assertEqual(s["envs"], 2)
        self.assertEqual(s["env_r"], {"A_2024": 1.0, "B_2024": -1.0})
        self.assertEqual(s["mean_r"], 0.0)
        self.assertEqual(s["pairs_scored"], 8)

    def test_score_constant_prediction_is_zero_and_constant_obs_skipped(self):
        preds = dict(PRED)
        for k in [k for k in preds if k[0] == "A_2024"]:
            preds[k] = 3.0
        out = self.p("sub.csv")
        ge.write_submission(self.template, preds, out)
        obs = write_csv(self.p("obs_observed_values.csv"), ["Env", "Hybrid", "Yield_Mg_ha"],
                        [["A_2024", "P1/T1", "5"], ["A_2024", "P2/T1", "6"], ["A_2024", "P3/T1", "7"],
                         ["B_2024", "P1/T1", "4"], ["B_2024", "P5/T2", "4"], ["B_2024", "P6/T2", "4"]])
        s = ge.score_submission(out, obs)
        self.assertEqual(s["env_r"], {"A_2024": 0.0})
        self.assertEqual(s["mean_r"], 0.0)

    def test_pearson_known_value(self):
        self.assertAlmostEqual(ge.pearson([1, 2, 3], [1, 3, 2]), 0.5)

    def test_seen_share_and_decide(self):
        trait = write_csv(self.p("1_Training_Trait_Data_2014_2023.csv"),
                          ["Env", "Year", "Hybrid", "Yield_Mg_ha"],
                          [["X_2022", "2022", "P1/T1", "9.1"], ["X_2023", "2023", "P1/T1", "9.3"],
                           ["X_2023", "2023", "P2/T1", ""], ["Y_2022", "", "P5/T2", "8.0"],
                           ["Y_2023", "2023", "P6/T2", "NA"]])
        s = ge.seen_share(trait, self.template)
        self.assertEqual(s["template_pairs"], 8)
        self.assertEqual(s["training_years"], [2022, 2023])
        self.assertEqual(s["last_training_year"], 2023)
        self.assertEqual(s["pairs_hybrid_seen"], 3)        # P1/T1 in A and B, P5/T2 in B
        self.assertEqual(s["pairs_hybrid_in_last_year"], 2)  # P1/T1 only (P2/T1 has no yield)
        self.assertEqual(s["share_seen"], 0.375)
        self.assertEqual(s["share_in_last_year"], 0.25)
        self.assertEqual(ge.decide(0.25)["setting"], "new_hybrids")
        self.assertEqual(ge.decide(0.70)["setting"], "repeated_hybrids")
        self.assertEqual(ge.decide(None)["setting"], "unknown")

    def test_find_release_and_name_years(self):
        sub = os.path.join(self.d, "Training_data")
        os.makedirs(sub)
        write_csv(os.path.join(sub, "1_Training_Trait_Data_2014_2024.csv"), ["Env", "Hybrid"], [["a", "b"]])
        with open(os.path.join(sub, "5_Genotype_Data_All_2014_2025_Hybrids_numerical.txt"), "w") as fh:
            fh.write("x\n")
        with open(os.path.join(sub, "notes_trait_data.txt"), "w") as fh:
            fh.write("not a csv\n")
        rel = ge.find_release(self.d)
        self.assertEqual(sorted(rel), ["geno_numeric", "template", "trait"])
        self.assertTrue(rel["trait"].endswith("1_Training_Trait_Data_2014_2024.csv"))
        self.assertEqual(ge.name_years(rel["trait"]), [2014, 2024])
        self.assertEqual(ge.name_years("1_Submission_Template_2025.csv"), [2025])

    def test_dryrun_end_to_end(self):
        data = os.path.join(self.d, "data")
        os.makedirs(data)
        write_csv(os.path.join(data, "1_Submission_Template_2024.csv"),
                  ["Env", "Hybrid", "Yield_Mg_ha"], TEMPLATE_ROWS)
        write_csv(os.path.join(data, "7_Testing_Observed_Values.csv"), ["Env", "Hybrid", "Yield_Mg_ha"],
                  [["A_2024", "P1/T1", "5"], ["A_2024", "P2/T1", "6"], ["A_2024", "P3/T1", "7"],
                   ["A_2024", "P4/T1", "8"], ["B_2024", "P1/T1", "9"], ["B_2024", "P5/T2", "8"],
                   ["B_2024", "P6/T2", "7"], ["B_2024", "P7/T2", "6"]])
        write_csv(os.path.join(data, "1_Training_Trait_Data_2014_2023.csv"),
                  ["Env", "Year", "Hybrid", "Yield_Mg_ha"], [["X_2023", "2023", "P1/T1", "9"]])
        with open(os.path.join(data, "5_Genotype_numerical.txt"), "w") as fh:
            fh.write("x\n")
        pred = write_csv(self.p("pred.csv"), ["Env", "Hybrid", "obs", "M4"],
                         [[e, h, "", str(v)] for (e, h), v in PRED.items()])
        out = os.path.join(self.d, "out")
        expect = {"score": 0.0, "envs": 2, "share_seen": [0.2, 0.3], "setting": "new_hybrids"}
        res = ge.dryrun(data, out, pred, "M4", expect)
        self.assertEqual(res["expect_total"], 6)
        self.assertEqual(res["expect_held"], 6, res["expect"])
        self.assertEqual(res["seen"]["share_seen"], 0.25)
        self.assertTrue(os.path.exists(os.path.join(out, "submission_dryrun.csv")))
        self.assertEqual(ge.main(["validate", "--template", os.path.join(data, "1_Submission_Template_2024.csv"),
                                  "--sub", os.path.join(out, "submission_dryrun.csv")]), 0)


if __name__ == "__main__":
    unittest.main()
