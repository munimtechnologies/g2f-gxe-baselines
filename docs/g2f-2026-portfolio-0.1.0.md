# g2f-2026-portfolio 0.1.0: which files to upload, fixed before the 2026 data exist (provisional)

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed it yet. Text CC BY 4.0; code
Apache-2.0. Not agronomic advice.

PREREG-MARKER: g2f-2026-portfolio-0.1.0

Written 2026-11-11, five days before the 2026 training data go to registered participants
(2026-11-16) and before any 2026 rule beyond the timeline is public. The 2026 leaderboard opens on
2026-12-15 and the last submission is due 2027-01-15 (maizegxeprediction.org, read 2026-11-11).

## Why fix this now

In 2024 each team could upload 5 files and its best file counted. With several close candidates, the
easiest way to fool oneself is to pick the upload order after seeing the leaderboard or the 2026 data.
This note fixes the order now, from 2022-2024 evidence only. A final version (0.2.0) will be filed
after the 2026 rules are read and before the first upload. Any change from the order below will be
listed there with its reason.

## Candidates (all built by `g2f_predict.py predict`, then validated)

Weights (a, b) mix the z-scored kernel model ("full") and M4 by hybrid category: a on new hybrids with
one parent seen, b on every other row (g2f-switch). Evidence so far, mean within-environment r:

| Candidate | 2022 | 2024 | Where it comes from |
|---|---|---|---|
| refold choice (a*, b*) | - | - | g2f-refold 0.1.0 `choose` on the 2026 release's own hold-out seasons of the 2026 type |
| (0.5, 0.5) | 0.362 | 0.433 | g2f-switch default, chosen on 2022, checked on 2024 (6 of 6 held) |
| (1.0, 0.5) | - | 0.462 | best on 2024 in hindsight (reported, never claimed) |
| (0.75, 0.5) | - | - | best mean over the 2022 and 2024 folds (0.406), so partly hindsight |
| full alone (1, 1) | 0.299 | 0.442 | the organisers' kernel model, re-implemented |
| M4 alone (0, 0) | 0.326 | 0.302 | marker ridge + parent combining ability |

2026 is an even season, which since 2018 has meant a new set of hybrids crossed to known testers, so
the new-hybrid rows (where full is stronger) should dominate again, as in 2022 and 2024.

## The order (provisional)

1. the refold choice (a*, b*); if the refold dry run fails its registered checks, (0.5, 0.5) instead;
2. (0.5, 0.5);
3. (1.0, 0.5);
4. (0.75, 0.5);
5. full alone;
6. M4 alone (only used to fill a slot freed by a duplicate).

Duplicates are skipped and the next candidate moves up. Then:

- **Best file counts, N uploads allowed:** upload the first N in this order.
- **Last file counts, or only one upload:** upload only number 1.
- **Pearson-type metric (mean within-environment r, as in 2024):** the Mg/ha levels cannot change the
  score; every file uses `g2f_entry.py mgha` with site-history levels, as in g2f-predict 0.1.0.
- **Error-type metric (RMSE or similar, as in 2022):** the level of each environment matters far more
  than the ranking (g2f-entry 0.2.0: 2.95 Mg/ha from levels alone, 2.90 with the ranking). Every file
  uses the level procedure decided by g2f-levelmeta 0.1.0 (run queued); if N >= 3, slot 3 instead
  repeats number 1 with the level rule that came second in the levelmeta replay, because a level miss
  costs more than any ranking change.
- **Any other metric:** no upload until a new note says how this order maps to it.

## What this does not decide

- Whether MV2 enters at all: the registration (per person, by 2026-12-14) is still open on Sheehan's
  side, and uploads go only through his EvalAI session when he agrees.
- The 2026 rules on external data, file names and units, which are read on release day.
- New studies (for example new hybrids with neither parent seen, if the 2026 paired crosses bring many).
  Any new candidate enters this order only through version 0.2.0 with its evidence.
