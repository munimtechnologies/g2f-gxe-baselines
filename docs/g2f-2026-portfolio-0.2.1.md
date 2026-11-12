# g2f-2026-portfolio 0.2.1: the registration form says "five submissions"

PORTFOLIO-MARKER: g2f-2026-portfolio-0.2.1

Written 2026-11-12 (about 22:40 UTC), **before the 2026 training data exist** (release 2026-11-16), before
the leaderboard opens (2026-12-15) and before MV2 is registered. By MV2 of Munim, Inc.; written by AI
agents working in his name, with no human review yet. Text: CC BY 4.0. Code in this repository:
Apache-2.0.

This note changes one sentence of `docs/g2f-2026-portfolio-0.2.0.md`: the cap rule. The six candidates
and their order are unchanged.

## 1. What was read

- **The Step One registration form** ("Registration: 2026 G2F GxE Yield Prediction Competition", the
  Google Form linked from the About tab), read 2026-11-12 at about 22:30 UTC. Its required confirmation
  question asks each registrant to agree to the rules on the About tab and lists the key ones, among them
  "Only participating on ONE team (five submissions)". It does not say whether five is a total or a daily
  figure.
- **The About tab** (maizegxeprediction.org/about), re-read at the same time. It still gives no number of
  submissions. It says "the highest scoring prediction from each team will be used for the final
  evaluation", that submissions must use the "Public" option on EvalAI, that the evaluation phase opens
  2026-12-15 and that nothing is accepted after 2027-01-15.

Version 0.2.0 read only the About tab and so recorded "no submission limit is stated". Every registrant
must confirm the form, so from now on MV2 treats five as binding.

## 2. The rule (replaces the cap sentence of 0.2.0, section 3)

1. **The cap is N = 5 in total.** If EvalAI's phase settings, read when the leaderboard opens, show a
   smaller total cap, use that smaller number. A daily limit on EvalAI does not raise the total above five.
2. **Upload the first N distinct candidates of the fixed six, in order.** A candidate is skipped as a
   duplicate if it is identical to an earlier one, or if it is the same model with different scaling:
   the mix (1, 1) is "full alone" and the mix (0, 0) is "M4 alone". Both inputs are z-scored inside each
   environment, which does not change a per-environment Pearson r.
3. **Check every file before uploading:** one row per test hybrid-environment pair, the template's
   columns, and no missing or non-numeric yields. A rejected upload might still use up one of the five.
4. As before, no file is added, removed or reordered because of a leaderboard reading. Nothing is
   uploaded until the team leader is registered and the EvalAI team name matches the form.

## 3. What this drops, fixed now

The six candidates are: 1 the g2f-refold choice (a\*, b\*) on the 2026 release, or (0.5, 0.5) if refold
fails its checks; 2 (0.5, 0.5); 3 (1.0, 0.5); 4 (0.75, 0.5); 5 full alone; 6 M4 alone. Refold picks from
the 5 x 5 grid a, b in {0, 0.25, 0.5, 0.75, 1}.

| What refold returns | Distinct candidates | Uploaded under a cap of 5 | Dropped |
|---|---|---|---|
| fails its checks, so slot 1 is (0.5, 0.5) | 5 (slot 2 is a duplicate) | 1, 3, 4, 5, 6 | nothing |
| (0.5, 0.5), (1.0, 0.5) or (0.75, 0.5) | 5 (the matching slot 2, 3 or 4 is a duplicate) | the other five | nothing |
| (1, 1), which is full alone | 5 (slot 5 is a duplicate) | 1, 2, 3, 4, 6 | nothing |
| (0, 0), which is M4 alone | 5 (slot 6 is a duplicate) | 1 to 5 | nothing |
| any of the other 20 grid pairs | 6 | 1 to 5 | slot 6, M4 alone |

If a smaller total cap applies, the same rule keeps the first N distinct candidates in this order.

## 4. Why losing M4 alone costs little

These are graded numbers already in this repository, not new results. M4 alone was the weakest of the
three candidates on both scored new-hybrid seasons: 0.326 on 2022 (mix 0.362) and 0.302 on 2024 (full
0.442, mix 0.433). M4 was stronger only on the repeated-hybrid 2023 fold (0.435 against full's 0.389).
The 2026 test season is an even year, when G2F starts a new hybrid set, so that case is not expected.
This reasoning does not change the order. Slot 6 was already last in 0.1.0, fixed before any rules were
published.

## 5. Unchanged

The scoring branch (mean per-location Pearson r; the error-metric level decision is not used), the
yield unit (Mg/ha at 15.5% moisture), "Public" visibility and the compliance notes for release day all
stay as in 0.2.0. The release predictions R1-R6 (`docs/g2f-2026-release-0.1.0.md`) are not affected.

Made with AI agents working in MV2's (Munim, Inc.) name. Questions: MV2, Munim, Inc.,
mv2@munimtech.com.
