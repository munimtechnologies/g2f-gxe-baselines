# g2f-2026-portfolio 0.2.0: the 2026 upload order, mapped to the published 2026 rules

PORTFOLIO-MARKER: g2f-2026-portfolio-0.2.0

By MV2 of Munim, Inc. Made with AI agents working in MV2's name; no human has reviewed it yet.
Text CC BY 4.0; code in this repository Apache-2.0. Not agronomic advice.

Written 2026-11-12 (about 01:50 UTC), **before the 2026 training data exist** (release 2026-11-16) and
before any 2026 leaderboard. It replaces the provisional parts of `docs/g2f-2026-portfolio-0.1.0.md`,
which fixed the upload order from 2022-2024 evidence and said a 0.2.0 would map that order to the 2026
rules once they were published. No candidate is added, removed or reordered here.

## 1. What the 2026 rules say (About tab, read 2026-11-12)

The About tab of maizegxeprediction.org now states that registration is open for the 2026 competition.
Quoted from it:

- Metric: "The winner will be determined based on having the highest average Pearson Correlation
  Coefficient (r)", computed "on a per location basis between the participant's submission and the
  observed 2026 data", then averaged "for a single representative r value". Other metrics may be used in
  the paper but do not decide the winner.
- Which file counts: "the highest scoring prediction from each team will be used for the final
  evaluation." No numeric limit on submissions is given on the About tab.
- Format: "Final predictions of absolute grain yield for each hybrid in each test environment in Mg/ha
  adjusted to 15.5% moisture." A template will be provided. Only submissions made with EvalAI's
  "Public" option are considered.
- Data: registered participants receive trial data from 2014-2025 on 2026-11-16. Test inputs include
  2026 field locations, field information, genotypic data and weather data. Outside data must have been
  publicly and freely available by 2026-02-01 (G2F DOI releases excepted).
- Teams: teams of one are allowed; one person is team leader; each person may be on only one team.
  Proprietary models cannot win. An ORCiD is required for authorship. The rules do not mention AI tools;
  "Any modeling strategy is permitted".
- Dates: registration form by 2026-12-14; leaderboard opens 2026-12-15; last submissions 2027-01-15;
  winners 2027-02-01.

## 2. Which branch of 0.1.0 applies

0.1.0 fixed four branches in advance. The 2026 rules select two of them:

| Question | 2026 answer | Branch taken (fixed in 0.1.0) |
|---|---|---|
| Metric | mean per-location Pearson r | **correlation**: yield levels cannot change the score, so every file uses the site-history levels (`g2f_entry.py mgha`, the default). The g2f-levelmeta `--folds 4` decision is **not used** (it applied only to an error metric). |
| Which file counts | the highest-scoring one | **best counts**: upload the candidates in the fixed order |

Why "per location" is read as "per environment": in 2024 the same organisers scored the mean r inside
each location-season, and this repository's per-environment scorer reproduces the organisers' public
reference script at exactly its 2024 leaderboard figure (0.4377, g2f-refmodel 0.1.2). A 2026 test season
has one season, so each location-season is one environment. Release-day check (no decision rides on
it): if the 2026 template has two environments at one location, note it in the release result; the
levels stay site-history per environment either way.

## 3. The upload order (unchanged from 0.1.0)

1. the g2f-refold choice (a*, b*) on the 2026 release, or (0.5, 0.5) if refold fails its checks
2. (0.5, 0.5), the default mix
3. (1.0, 0.5)
4. (0.75, 0.5)
5. full alone
6. M4 alone

**One change of use, with its reason.** 0.1.0 kept M4 alone (slot 6) only to fill a slot freed by a
duplicate, because it assumed a small cap. The About tab sets no cap and counts the best file, so each
extra distinct file can only raise or keep the counted score. Therefore: upload every distinct
candidate, 1 to 6, in order, skipping any file identical to an earlier one (for example, if refold
chooses (0.5, 0.5), slot 2 is skipped). If EvalAI's own phase settings show a cap of N in total or per
day when the leaderboard opens, upload the first N distinct candidates (per day: continue in order on
the next day). Six files is the most this portfolio will ever upload; no file is added because of a
leaderboard reading.

The leaderboard is scored on the 2026 data, so choosing among six candidates on it is a mild selection
on the test set. The rules allow it, and the order and the set of six are fixed here, before any
leaderboard exists.

## 4. Compliance notes for release day

- Units: files are absolute Mg/ha. On release day, read the release's description of its yield column.
  If training yields are not at 15.5% moisture, convert the levels; r does not change.
- Outside data: every candidate uses only the G2F release, so the 2026-02-01 cut-off is met.
- Not proprietary: all code here is Apache-2.0 and public; the kernel model runs on bWGR (GPL-3, CRAN).
- 2026 weather is given as a test input. No candidate uses it. Under per-location r, weather could only
  help through hybrid-by-weather interaction, and the one such study here (g2f-ecreaction 0.1.0: a
  marker-by-covariate reaction norm) found that every positive weight lowered the 2024 hold-out score. A
  weather-aware candidate would need its own pre-registration and 2022/2024 back-tests before 2026-12-15;
  none is planned.
- Each upload uses EvalAI's "Public" option. The team description says the entry was made with AI
  agents working in MV2's name.
- Whether MV2 enters is still open: it needs the team leader's registration (form by 2026-12-14 and an
  EvalAI team whose name matches). Nothing is uploaded without it.

## 5. Next version

A 0.3.0 is filed only if the 2026 template or EvalAI's settings contradict section 1 (for example, a
different metric on EvalAI than on the About tab). Otherwise this note stands through 2027-01-15.

Contact: MV2, Munim, Inc., mv2@munimtech.com.
