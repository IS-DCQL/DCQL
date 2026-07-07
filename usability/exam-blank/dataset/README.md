# Teaching datasets handed out with the exam (illustrative)

The four-domain teaching datasets distributed together with the exam papers, ~20 core
records per domain. Students use them to answer every question; the "Expected result" of
each prediction question (Biomedical-Q4, Stainless-Q4, HEP-Q3) is computed on this data.

> **Note (important):** This is **illustrative** teaching data, selected/assembled from the
> real sources, with the same goal as §6.3 — "about 20 core records, ensuring the query
> results are predictable", i.e. making the three complex result-prediction questions return
> **small, definite, non-empty** results on a small dataset. It is **not** the exact curated
> set actually handed out at exam time (that file was not retained), nor is it the same as
> the full `conciseness/` data used for the §6.2 syntactic comparison. Regenerate it with
> `../_build_teaching_data.py`.

## Layout
```
dataset/<domain>/document/<collection>.json
  biomedical/document/cases.json                          (20 cases, nested)
  stainless-steel/document/{pitting_corrosion,mechanical_properties}.json   (20 each)
  high-energy-physics/document/events.json                (20 events)
  organic-polymer/document/{materials_library,processing_logs,pa6t_library}.json (20 each)
```
What is shipped here is the **document (nested) form**. The **relational** form seen by SQL
students and the **object** form seen by OQL students are two other renderings of the same
logical data, produced by running the repository's `conciseness/_<domain>_conversion/`
scripts (`to_relational.py` / `to_object.py`) on this data.

## Three deliberate edits (to keep the prediction questions answerable)
- **Biomedical**: the 20 cases include one **real qualifying TCGA case**,
  `28011111-4a01-4cdc-8d6b-7223fb2c501b` (taken from the full TCGA data), so Biomedical-Q4
  returns a small result; the other 19 are the §6.2 teaching subset.
- **Stainless steel**: the real pitting-corrosion files leave `material_performance` (yield
  strength) empty, while Q4 requires "yield strength > 550 MPa". A yield-strength field is
  therefore **injected** into the chosen records so that exactly 2 of them satisfy NaCl=3.5%,
  20 C, pitting potential > 1000 mV, and yield > 550 MPa.
- **High-energy physics**: the 20 real events are used unchanged — the electron filter
  already returns results.
- **Organic polymer**: 20 representative records (including semi-aromatic ones); this domain
  has no prediction question, so the data only backs the writing/reading questions.

## Concrete results of the three prediction questions on this data
| Question | Expected result |
|---|---|
| Biomedical-Q4 | case `28011111-...`, 2 RNA aliquots (`19f0514a-...`, `957fa2bd-...`, both concentration 0.17 ug/uL) |
| Stainless-Q4 | 2 records: `pitting_potential_2023_0187` (grade 2205, yield 615 MPa), `pitting_potential_2023_0188` (grade 2205, yield 580 MPa) |
| HEP-Q3 | 20 events, 75 e+/e- total (status=1); per-event counts in `../../exam-key/*.md`, Question 4.3 |

This data is a derived artifact, **gitignored and not committed** (see `.gitignore` here);
regenerate it with `../../_build_teaching_data.py` before use.
