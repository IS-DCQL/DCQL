# Final-exam papers (§6.3) — blank instruments

The seven blank final-exam papers, one per query language, used in the controlled
learning experiment (§6.3). Reference answers + grading rubric are in `../exam-key/`.
Both are produced by `../_generate_exams.py` (re-run it to regenerate).

## Structure (mirrors Appendix Table A.2)

- **4 parts = 4 domains** (Biomedical / Stainless Steel / Organic Polymer / High-Energy
  Physics). Each part opens with a domain prompt (storage + retrieval context) followed by
  **4 questions**.
- **16 questions per paper**, in the same order as Appendix Table A.1, = **10 query-writing
  + 3 query-reading + 3 result-prediction** (each tagged Query Writing / Query Reading /
  Result Prediction).
- Reading positions: Stainless-Q1, Polymer-Q2, HEP-Q1. Prediction positions:
  Biomedical-Q4, Stainless-Q4, HEP-Q3. (Same positions in all 7 papers.)

## Three categories -> two question-stem sets

Per Table A.2 the 7 languages fall into three categories, but they reduce to **two shared
stem sets**:

| category | languages | schema operations |
|---|---|---|
| schema-bearing | **DCQL, SQL, OQL** | create/drop/alter/query **schema** |
| schema-less | **MQL, N1QL, XQuery, JSONiq** | the **data**-equivalent op |

**OQL is grouped with the schema-bearing set**: OQL/JPQL owns persistent classes (an
explicit schema), so its per-question operation type matches the schema-bearing column —
schema create = define a class, schema query = JPA-metamodel reflection, and so on. The
blank object-oriented column of Table A.2 therefore equals the schema-bearing column. (Only
the *answer language* differs; OQL students write JPQL / reflection / migration code.)

## Why the 7 papers are not byte-identical within a category

The **3 query-reading + 3 result-prediction** questions present a concrete query *in the
examinee's own language* to interpret / predict, so each paper embeds its own language's code
at those 6 items (pulled from `../../conciseness/<LANG>/<domain>/<task>`). The 10
writing-question stems are shared within a category (natural-language tasks).

## Two authored items (no conciseness counterpart)

- **Biomedical-Q2 (insert)** — per Table A.2 row 2 this is a pure data-insert task (it
  differs from A.1's T2 query; confirmed authoritative). It inserts a `gene_variant` record
  into the entity built in Q1; the statement is authored per language.
- **Organic-polymer-Q2 (modify data, reading)** — A.1 frames this as "locate the anomalous
  WAXD record to correct it"; A.2 labels it a data modification, so the reading item shows an
  UPDATE that nulls the impossible alpha-crystallinity (>100%) value of `data_id=195540` for
  re-measurement. Authored per language.

All other items' code/answers come verbatim from the §6.2 `conciseness/` corpus.

## Files
```
exam-blank/  DCQL.md SQL.md OQL.md MQL.md N1QL.md XQuery.md JSONiq.md   (+ this README)
             dataset/<domain>/document/*.json  — the ~20-record teaching data handed out
exam-key/    same 7 names — reference answers + S/L/V/M grading rubric
```
Markdown, plain-text-friendly (the exam was electronic-paper / plain-text editor).

The ~20-record teaching dataset is shipped in `dataset/` (illustrative — see
`dataset/README.md`), curated so the three prediction questions return small, definite
results. The prediction answer keys therefore give **concrete** expected results:
Biomedical-Q4 -> 1 case / 2 RNA aliquots; Stainless-Q4 -> 2 records; HEP-Q3 -> 75 e+/e-
over 20 events (per-event counts). The teaching set is built by `../_build_teaching_data.py`.
