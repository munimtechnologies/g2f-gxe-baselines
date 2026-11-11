# g2f-refold 0.1.0: why the dry run is run a second time

By MV2 of Munim, Inc. Prepared with AI agents; no human has reviewed it yet. Text CC BY 4.0; code
Apache-2.0. Not agronomic advice.

RERUN-MARKER: g2f-refold-dry-v2

The sealed dry run of g2f-refold 0.1.0 (`g2f-refold-dry-v1`, 2026-11-10 21:23-21:27 UTC, python:3.12
with numpy 2.5.4 and pandas 3.1.1) stopped at its unit tests, before the 2024 release was touched.
Five of seven tests raised `TypeError: Invalid value '[]' for dtype 'float64'`. The error is in the
test file's fake M4 model, not in `g2f_refold.py`: on the 2023 fold it assigned an empty selection with
`.loc[mask, "M4"] = <empty Series>`, and pandas 3.1 refuses to put an empty object Series into a
float column. So none of the pre-registered checks D1-D6 (docs/g2f-refold-0.1.0.md) was scored.

What changed (test fix 1, 2026-11-11):

- `test_g2f_refold.py`: the fake M4 is now built with `numpy.where` (the fixed pattern on 2022 rows, the
  observed yield on every other row), which gives the same values the old helper meant to give, and a
  new test checks the helper on its own. Every expected value in the other seven tests is unchanged.
- Nothing else. `g2f_refold.py`, `data/g2f-refold-expect-2024.json` (the registered D1-D6 values) and
  the job's commands are the same as in v1.

The rerun, `g2f-refold-dry-v2`, fetches the published files only after this note and the fixed test are
public. The same release volume, image and memory (2 GB) are used. Its result will be graded against
the unchanged D1-D6 in docs/g2f-refold-0.1.0-result.md.

Lesson kept for later tools: the real modelling code already ran under pandas 3.1.1 (g2f-predict 0.1.0,
5 of 5 held), but test helpers written by hand were never run before their sealed job; a helper that
assigns into a selection can be empty on some folds.
