# Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
import csv
import os
import tempfile
import unittest

import g2f_cathistory as gc

TRAIT = [
    ["Env", "Year", "Hybrid", "Hybrid_Parent1", "Hybrid_Parent2", "Yield_Mg_ha"],
    ["A_2014", "2014", "P1/T1", "P1", "T1", "10"],
    ["A_2014", "2014", "P2/T1", "P2", "T1", "11"],
    ["B_2014", "2014", "P1/T1", "P1", "T1", ""],
    ["A_2015", "2015", "P1/T1", "P1", "T1", "9"],
    ["A_2015", "2015", "P3/T1", "P3", "T1", "9"],
    ["A_2015", "2015", "P1/P2", "P1", "P2", "9"],
    ["A_2015", "2015", "X/Y", "X", "Z", "9"],
    ["A_2015", "2015", "P2/T1", "P2", "T1", "NA"],
    ["B_2015", "2015", "lh195/phz51", "lh195", "phz51", "8"],
    ["B_2015", "2015", "PHN82/B73", "PHN82", "B73", "8"],
]
OBSERVED = [
    ["Env", "Hybrid", "Yield_Mg_ha"],
    ["C_2024", "P3/T1", "8"],
    ["C_2024", "Q/R", "8"],
    ["C_2024", "B73/MO17", "7"],
    ["D_2024", "Q/T1", ""],
]


def write(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerows(rows)


class TestPieces(unittest.TestCase):
    def test_parents_and_categorize(self):
        self.assertEqual(gc.parents(" A / B "), ("A", "B"))
        self.assertEqual(gc.parents("A"), ("A",))
        train, pool = {"A/B"}, {"A", "B"}
        self.assertEqual(gc.categorize("A/B", train, pool), "seen")
        self.assertEqual(gc.categorize("B/A", train, pool), "new_both")
        self.assertEqual(gc.categorize("A/C", train, pool), "new_one")
        self.assertEqual(gc.categorize("C/D", train, pool), "new_none")

    def test_is_number(self):
        self.assertTrue(gc.is_number(" 9.5 "))
        self.assertFalse(gc.is_number("NA"))
        self.assertFalse(gc.is_number(""))
        self.assertFalse(gc.is_number("nan"))


class TestEndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = self.tmp.name
        write(os.path.join(d, "1_Training_Trait_Data_2014_2023.csv"), TRAIT)
        write(os.path.join(d, "7_Testing_Observed_Values.csv"), OBSERVED)
        self.recs = gc.load_records(gc.find_file(d, "training_trait"),
                                    gc.find_file(d, "testing_observed"))

    def tearDown(self):
        self.tmp.cleanup()

    def test_seasons(self):
        s = gc.season_table(self.recs)
        self.assertEqual(sorted(s), ["2015", "2024"])
        self.assertEqual(s["2015"]["pairs"], 6)
        self.assertEqual(s["2015"]["pairs_by_category"],
                         {"seen": 1, "new_both": 1, "new_one": 1, "new_none": 3})
        self.assertEqual(s["2015"]["train_hybrids"], 2)
        self.assertEqual(s["2015"]["new_one_top_seen_parent"], ["T1", 1.0])
        self.assertEqual(s["2024"]["pairs_by_category"],
                         {"seen": 1, "new_both": 0, "new_one": 1, "new_none": 1})
        self.assertEqual(s["2024"]["share_by_category"]["seen"], round(1 / 3, 4))
        self.assertEqual(s["2024"]["train_hybrids"], 7)
        self.assertEqual(s["2024"]["unparsed_pairs"], 0)

    def test_parent_table(self):
        rows = {r["parent"]: r for r in gc.parent_table(self.recs)}
        self.assertEqual(rows["T1"]["hybrids"], 3)
        self.assertEqual(rows["T1"]["env_hybrid_pairs"], 5)
        self.assertEqual((rows["T1"]["first_year"], rows["T1"]["last_year"]), (2014, 2024))
        self.assertEqual(rows["T1"]["years"], "2014;2015;2024")
        self.assertEqual(rows["P1"]["env_hybrid_pairs"], 3)
        self.assertNotIn("MO", rows)

    def test_name_check(self):
        n = gc.name_check(self.recs)
        self.assertEqual((n["combos"], n["agree"], n["disagree"]), (7, 6, 1))
        self.assertEqual(n["disagree_examples"], [["X/Y", "X", "Z"]])

    def test_check_lookup(self):
        c = gc.check_lookup(self.recs)
        by = {r["check"]: r for r in c["checks"]}
        self.assertEqual(len(c["checks"]), 19)
        self.assertEqual((by["B73/MO17"]["match"], by["B73/MO17"]["years"]), ("exact", [2024]))
        self.assertEqual((by["LH195/PHZ51"]["match"], by["LH195/PHZ51"]["years"]), ("case", [2015]))
        self.assertEqual(by["B73/PHN82"]["match"], "swapped")
        self.assertEqual((c["exact"], c["case"], c["swapped"], c["none"]), (1, 1, 1, 16))

    def test_grade_on_synthetic_mostly_fails(self):
        s = gc.season_table(self.recs)
        g = gc.grade(s, gc.check_lookup(self.recs), gc.name_check(self.recs))
        self.assertFalse(g["K1_2024_counts_match_newshrink"]["held"])
        self.assertFalse(g["H1_new_none_at_most_5pct_every_season"]["held"])
        self.assertEqual(g["H1_new_none_at_most_5pct_every_season"]["value"], ("2015", 0.5))
        self.assertFalse(g["H4_at_least_15_checks_exact"]["held"])
        self.assertFalse(g["H6_name_split_agrees_99pct"]["held"])


class TestGrade(unittest.TestCase):
    def season(self, seen, both, one, none, top=None):
        n = seen + both + one + none
        c = {"seen": seen, "new_both": both, "new_one": one, "new_none": none}
        return {"pairs": n, "pairs_by_category": c,
                "share_by_category": {k: round(v / n, 4) for k, v in c.items()},
                "top_parents_by_hybrids": top or []}

    def test_all_hold(self):
        s = {"2024": self.season(1172, 638, 7676, 0, [["PHP02", 500], ["LH287", 480], ["X", 3]]),
             "2022": self.season(816, 1896, 9126, 0)}
        for y in ("2016", "2018", "2020"):
            s[y] = self.season(10, 20, 100, 1)
        for y in ("2017", "2019", "2021", "2023"):
            s[y] = self.season(90, 5, 5, 0)
        g = gc.grade(s, {"exact": 17}, {"agree_share": 0.995})
        self.assertTrue(all(v["held"] for v in g.values()), g)
        s["2022"]["pairs_by_category"]["new_both"] = 1940   # 2.3% off
        s["2019"]["share_by_category"]["seen"] = 0.74
        g = gc.grade(s, {"exact": 14}, {"agree_share": None})
        self.assertFalse(g["K2_2022_counts_match_newshrink"]["held"])
        self.assertFalse(g["H3_seen_at_least_75pct_in_odd_seasons"]["held"])
        self.assertFalse(g["H4_at_least_15_checks_exact"]["held"])
        self.assertFalse(g["H6_name_split_agrees_99pct"]["held"])
        self.assertTrue(g["H5_PHP02_LH287_top_two_2024"]["held"])

    def test_missing_seasons(self):
        g = gc.grade({}, {}, {})
        self.assertFalse(any(v["held"] for v in g.values()))


if __name__ == "__main__":
    unittest.main()
