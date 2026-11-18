# Evaluation data

`python manage.py evaluate` runs every case in `cases.csv` through the same extractors and
rule functions as the web app, then compares Maapdand's verdicts with the expected ones.

## What is here now

| Cases | What they are | What they prove |
|---|---|---|
| `t01`–`t20` (text) | Made-up labels, each changing one thing from a compliant label | The rule and parser logic, rule by rule |
| `i01`, `i02` (images) | `t01` and `t14` rendered as flat images in Chrome | That the image path (preprocessing + OCR, English and Hindi) works end to end |

All 22 are marked `synthetic=yes`. **They do not measure accuracy on real packs.** The command
reports real and synthetic cases separately, so made-up cases never inflate real-pack numbers.

## Adding real label photos (the numbers that matter)

1. Photograph each pack: every side that has text, one photo per side. Save them in
   `images/real/`, named after the product, e.g. `parle-g-front.jpg`, `parle-g-back.jpg`.
2. Add one row per product to `cases.csv`:
   - `id`: a short name, e.g. `r01_parle_g`
   - `input`: the photos separated by `;`, e.g. `images/real/parle-g-front.jpg;images/real/parle-g-back.jpg`
   - `is_imported`: `yes`, `no`, or blank if unknown (what an officer would answer)
   - `synthetic`: `no`
   - `notes`: anything unusual (glare, curved pack, small print)
   - `R01`…`M02`: the verdict each rule **should** give, decided by reading the label yourself
     against the rule (see `/rules/` in the app). Use `PASS`, `FAIL` or `CANNOT_DETERMINE`.
     Leave a cell blank if you can't decide; it is then not scored.
3. Run `python manage.py evaluate --real-only --errors --save`. The report is saved in
   `evaluation/results/` and lists every wrong verdict with Maapdand's reason.

Decide the expected verdicts **before** running the command, and don't change them to match
its output. A disagreement is either a Maapdand error (fix the code) or a labelling mistake
(fix the CSV, with a note saying why).

A good set for the submission: 25–40 real products, mixing food and non-food, English-only
and bilingual labels, and a few with known problems (missing MRP tax note, "gm", no
consumer care).

## Reading the report

- **Accuracy**: share of labelled cells where Maapdand gave exactly the expected verdict.
- **Missed violations**: expected Fail, got Pass. The error a screening aid must avoid.
- **False alarms**: expected Pass, got Fail.
- **Sent to a person**: Cannot determine where a firm verdict was expected (safe, but extra work).
- **Overreach**: a firm verdict where Cannot determine was expected.
- **Overall verdict**: same scope as the web app (pack checks M01/M02 not counted).
