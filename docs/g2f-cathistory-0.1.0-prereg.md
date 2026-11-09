# g2f-cathistory 0.1.0: which kinds of new hybrid has each G2F season tested? (pre-registration)

PREREG-MARKER: g2f-cathistory-0.1.0

Made with AI agents working in MV2's (Munim, Inc.) name. Code: Apache-2.0. Text: CC BY 4.0.
Written 2026-11-09, before the sealed job `g2f-cathistory-v1` reads the data, and before the 2026
competition data are released (expected 2026-11-16). The job waits until this file is public.

## Why

The G2F competition scores yield predictions for hybrids in a new season. A test hybrid is either
**seen** (grown in an earlier season) or new. If it is new, both of its parents may be seen (`new_both`),
only one (`new_one`), or neither (`new_none`), where "seen" means the parent of some earlier hybrid. These
kinds call for different models. Seen hybrids are ranked by their own past yields. `new_one` hybrids
are ranked by markers and the seen parent's record. `new_none` hybrids are ranked by markers alone.

In the 2024 test season, 12% of pairs were seen, 81% had exactly one parent seen, and **none had
neither parent seen** (g2f-release-census 0.1.0 result). The 2026 trials begin a new design. G2F's
project page (read 2026-11-09) lists about 300 paired-cross hybrids between 50 Stiff Stalk and 100
Non-Stiff Stalk lines, topcrosses of those lines to LH287 and LH244, and 25 core checks. The page does
not say whether those 150 lines were parents in earlier G2F seasons. If they were not, most paired
crosses would be `new_none`. We want to know whether any past season tested that kind of hybrid, since
every forward-season check in this repository, our 2024 placings included, depends on the answer.

The 2022 competition paper (Washburn et al. 2024, Genetics iyae195) says test-hybrid parents were
"largely different" from training. A search on 2026-11-09 found no published count of test hybrids by
parent category per season.

## What the job does

`g2f_cathistory.py` (standard library only; `test_g2f_cathistory.py` tests it on synthetic files)
reads the trait file (2014-2023) and the observed 2024 values from the 2024 release (CyVerse DOI
10.25739/78mn-4394; data key `g2f-2024-release`). For each season Y from 2015 to 2024:

- It puts every (Env, Hybrid) pair with a numeric yield into one category, measured against all
  hybrids with a numeric yield before Y. The rule is the same as `g2f_refcheck.categorize`, with parents
  split from "PARENT1/PARENT2" names.
- It reports the count and share of each category, distinct parents, the five parents with the most
  hybrids, and the share of `new_one` pairs whose seen parent is the single most common one (a tester).

Also:

- `results/g2f_parents_2014_2024.csv`: every parent name with its hybrid count, pair count and seasons.
  This is the lookup for the 2026 template on release day.
- Name check: does splitting the hybrid name give the trait file's own `Hybrid_Parent1/2` columns?
- The 19 named 2026 core checks (from G2F's page) are looked up in 2014-2024: exact, case-insensitive or
  parent-swapped match.

It prints counts and names only, never a yield.

## Checks and predictions (graded by the job's own code, `grade()`)

Tool checks against this repository's g2f-newshrink 0.1.0 counts:

- **K1:** 2024 pairs: seen 1,172, new_one 7,676, new_both 638, each within 1%, and new_none = 0.
- **K2:** 2022 pairs: seen 816, new_one 9,126, new_both 1,896, each within 2%.

Predictions:

- **H1:** in no season 2015-2024 do `new_none` pairs exceed 5% of the season's pairs. (G2F has mostly
  tested lines crossed to established testers.) Confidence 0.6.
- **H2:** in every even season (2016, 2018, 2020, 2022, 2024), `new_one` is the largest category of
  pairs. Confidence 0.5.
- **H3:** in every odd season (2017, 2019, 2021, 2023), at least 75% of pairs are `seen`. Confidence 0.8.
- **H4:** at least 15 of the 19 named 2026 core checks appear, with exactly the same name, as a hybrid
  with a yield in 2014-2024. Confidence 0.75.
- **H5:** PHP02 and LH287 (the 2024-2025 testers) are the two parents with the most 2024 hybrids.
  Confidence 0.7.
- **H6:** for at least 99% of distinct trait-file combinations, splitting the hybrid name gives the
  same two parents as the parent columns. Confidence 0.8.

## Corrected predictions for the 2026 release (graded on its first census)

The census pre-registration (`g2f-release-census-0.1.0.md`) assumed that the 2026 competition would
test the 2025 season. The competition site says it tests the **2026** trials. Its R1-R4 stand as
written. We expect R1 and R3 to fail. These replace them for planning:

- **A1:** the training trait data end with the 2025 season. Confidence 0.8.
- **A2:** at least 80% of 2025 hybrids with a yield were also grown in 2024. Confidence 0.85.
- **A3:** at most 15% of template pairs have a hybrid seen in training. Confidence 0.8.
- **A4:** the template has 300 to 600 hybrids. Confidence 0.6.
- **A5:** at least 20% of template pairs have neither parent seen (pairs minus both-seen, one-seen and
  unparsed). Confidence 0.5. This turns on where the 150 new lines come from, which we do not know.

## Use (fixed now)

- If **A5 holds** on release day, `new_none` rows are predicted by the marker parts of a model alone.
  If H1 also holds, no past season can test those rows. The model for them is then chosen on a
  parents-held-out fold built from the training seasons, pre-registered once the 2026 parent lists are
  known, and not on the 2022-2024 forward folds.
- If **A5 fails** and at least 50% of template pairs have both parents seen, the paired-cross lines were
  tested before. Parent-record models (M4's G1 and the organisers' reference) are compared by category,
  using the g2f-refmodel 0.1.1 split.
- Otherwise (mostly `new_one`, like 2024), the g2f-refmodel 0.1.1 rule decides.

## Limits

- Names are compared exactly (after trimming), so renamed hybrids or lines look new. The shares of
  seen hybrids and parents are lower bounds.
- "Parent seen" means it named a parent of an earlier hybrid with a yield, not that the line itself
  was grown or genotyped as an inbred.
- The check names came from G2F's web page through a summarising reader, and any typo there would
  count as a miss in H4. The exact names are in the job's output.
- No person has checked these counts. Nothing here is agronomic advice.

MV2, Munim, Inc., mv2@munimtech.com
