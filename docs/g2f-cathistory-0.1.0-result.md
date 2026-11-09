# g2f-cathistory 0.1.0: result (which kinds of new hybrid each G2F season tested)

RESULT-MARKER: g2f-cathistory-0.1.0-result

Made with AI agents working in MV2's (Munim, Inc.) name; no human has checked the counts. Code:
Apache-2.0. Text and data: CC BY 4.0. Graded 2026-11-09 (about 22:40 UTC) against
[the pre-registration](g2f-cathistory-0.1.0-prereg.md), written before the sealed job
`g2f-cathistory-v1` read the data (it finished 2026-11-09 21:26 UTC). Raw output:
[`results/g2f_cathistory.json`](../results/g2f_cathistory.json) and the parent table
[`results/g2f_parents_2014_2024.csv`](../results/g2f_parents_2014_2024.csv).

## Grades: 6 of 8 held

| Check | Value | Held? |
|---|---|---|
| **K1** 2024 counts = g2f-newshrink (seen 1,172, new_one 7,676, new_both 638, new_none 0) | exact | **yes** |
| **K2** 2022 counts = g2f-newshrink (816 / 9,126 / 1,896) | exact | **yes** |
| **H1** new_none never above 5% of a season's pairs | **2016: 23.7%** | **no** |
| **H2** new_one is the largest category in every even season | 2016, 2018, 2020, 2022, 2024 | **yes** |
| **H3** at least 75% of pairs seen in every odd season | 2017 95.1%, 2019 77.8%, 2021 99.8%, 2023 99.4% | **yes** |
| **H4** at least 15 of the 19 named 2026 core checks grown before, same name | **19 of 19** | **yes** |
| **H5** PHP02 and LH287 are the two parents with most 2024 hybrids | LH287 506, PHP02 506 | **yes** |
| **H6** name split gives the trait file's parent columns for 99% of combinations | **96.7%** (176 of 5,268 disagree) | **no** |

H6 missed because of hybrids whose names have no `/`. All 10 disagreements the job printed are
commercial hybrid names (for example `31G66`, `38B13`) whose parent columns are empty. The job
printed only those 10, so the other 166 are not confirmed to be the same kind.

## Test pairs by category, every season (each measured against all earlier seasons)

| Season | Pairs | Hybrids | seen | new_both | new_one | new_none | Parents with most hybrids |
|---|---|---|---|---|---|---|---|
| 2015 | 10,790 | 1,155 | 26.2% | 29.3% | 44.4% | 0.1% | PHB47 276, PHZ51 248 |
| 2016 | 7,415 | 579 | 22.3% | 13.2% | 40.8% | **23.7%** | **DK3IIH6 147**, LH195 96 |
| 2017 | 6,039 | 503 | 95.1% | 3.7% | 1.2% | 0 | DK3IIH6 128, LH195 57 |
| 2018 | 13,982 | 1,054 | 7.1% | 2.5% | 90.4% | 0.1% | PHT69 505, LH195 428 |
| 2019 | 15,541 | 1,201 | 77.8% | 15.6% | 6.6% | 0 | PHT69 594, LH195 582 |
| 2020 | 11,305 | 1,176 | 6.7% | 6.6% | 86.7% | 0 | PHZ51 382, PHK76 379, PHP02 375 |
| 2021 | 13,628 | 1,181 | 99.8% | 0.1% | 0.1% | 0 | PHZ51 387, PHK76 379, PHP02 375 |
| 2022 | 11,838 | 553 | 6.9% | 16.0% | 77.1% | 0 | LH244 512 |
| 2023 | 11,615 | 556 | 99.4% | 0.6% | 0.1% | 0.0% | LH244 514 |
| 2024 | 9,486 | 1,063 | 12.4% | 6.7% | 80.9% | 0 | LH287 506, PHP02 506 |

Since 2018, every even season has been a new set of lines crossed to one or two testers. In 2016,
by contrast, 137 hybrids (1,761 pairs) had **neither parent seen before**. DK3IIH6, the most used
parent that year, first appears as a parent in 2016 (parent table: first_year 2016). In 2022 every one-parent new hybrid
shared the same seen parent (LH244). In 2024, 58% shared PHP02.

## The 2026 core checks

All 19 check hybrids named on G2F's 2026 page were grown before under exactly the same name. 11
appear in 8 or more of the 11 seasons, and the two newest (`01DIB2/LH287`, `01CSI6/LH287`) only in 2024. Both
2026 testers, LH287 and LH244, are well-known parents (LH244 was the tester in 2022-2023, LH287 in
2024). So the ~150 topcrosses will be at worst new hybrids with one parent seen. Whether the ~300
paired crosses have any parent seen depends on where the 150 new lines come from, which G2F has not
said.

## What this changes (rule fixed in the pre-registration)

- **H1 failed: one past season can test the kind of row 2026 may bring.** If the 2026 template has at
  least 20% of pairs with neither parent seen (A5), the pre-registration said the model for those
  rows would be chosen on a parents-held-out fold, because "no past season can test those rows". That
  is not true: **2016** had 1,761 such pairs in 137 hybrids. The 2016 season (training 2014-2015)
  becomes the forward check for new_none rows, next to a parents-held-out fold. It is a small fold
  with only two training seasons, and its new_none hybrids mostly share one new tester, so it is
  weaker than 2022 or 2024.
- A1-A5 are graded on the 2026 release's first census. The parent table above is the lookup for the
  2026 template's parents.

## Limits

- Names are compared exactly after trimming. A renamed line counts as new, so the seen shares are
  lower bounds.
- "Parent seen" means the name appeared as a parent of an earlier hybrid with a yield, not that the
  inbred itself was grown or genotyped.
- Counts only. Nothing here is agronomic advice.

MV2, Munim, Inc., mv2@munimtech.com
