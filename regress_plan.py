# SPDX-License-Identifier: Apache-2.0
"""regress_plan.py: checks the `plan` output of g2f_refmodel.R 0.2.1 (standard library only).

K1  2024 release, default: version 0.2.1, test fold 2024, hold-outs "2023 2022" (the folds 0.1.0 fit)
K2  simulated 2026-style layout (renamed links in sub-folders): test fold 2026, the renamed trait,
    template and genotype files are the ones found, hold-outs "2023 2022"
K4  2024 release, n_holdouts 4: hold-outs "2023 2022 2021 2020"
K5  2024 release, n_holdouts 0: hold-outs "none"
(K3, the 0.4416 reproduction of the test fold, was graded on 0.2.0 by g2f-refmodel2-regress-v2; 0.2.1
changes no fitting line.) Made with AI agents working in MV2's (Munim, Inc.) name.
Usage: python3 regress_plan.py <out_dir>
"""
import json
import os
import sys


def read_plan(path):
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            k, _, v = line.strip().partition(" ")
            out[k] = v
    return out


def main(out_dir):
    plans = {k: read_plan(os.path.join(out_dir, k, "refmodel_plan.txt")) for k in ("plan2024", "sim", "plan4", "plan0")}
    p1, p2, p4, p0 = plans["plan2024"], plans["sim"], plans["plan4"], plans["plan0"]
    checks = {
        "K1_plan_2024": p1.get("version") == "0.2.1" and p1.get("test_fold") == "2024"
        and p1.get("holdout_folds") == "2023 2022",
        "K2_plan_sim_2026": p2.get("test_fold") == "2026"
        and p2.get("trait_file", "").endswith("Training_data/1_Training_Trait_Data_2014_2025.csv")
        and p2.get("template_file", "").endswith("Testing_data/1_Submission_Template_2026.csv")
        and p2.get("geno_file", "").endswith("_numerical.txt")
        and p2.get("holdout_folds") == "2023 2022",
        "K4_four_holdouts": p4.get("holdout_folds") == "2023 2022 2021 2020",
        "K5_zero_holdouts": p0.get("holdout_folds") == "none",
    }
    res = {"version": "0.2.0", "plans": plans, "checks": {k: {"held": bool(v)} for k, v in checks.items()}}
    res["held"] = sum(1 for v in checks.values() if v)
    res["total"] = len(checks)
    with open(os.path.join(out_dir, "g2f_refmodel_plan_regress.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, sort_keys=True)
    print(json.dumps(res, indent=1, sort_keys=True))
    return 0 if res["held"] == res["total"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "/out"))
