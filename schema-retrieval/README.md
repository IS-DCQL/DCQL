# §6.6 Schema-Reuse Case Study (RQ4)

Artifacts for the §6.6 case study "Reusing a stainless-steel corrosion schema" (Table rq4 in
the paper). DCQL promotes **schema retrieval** to a first-class operation; this study shows
that, before defining a new schema, a researcher can locate reusable existing schemas and
grade how completely each one covers the new modeling need.

Built on the running **StainlessSteel** example (Sections 3–5, Figure 2).

## Setup

A researcher needs a schema for a new round of stainless-steel corrosion + mechanical tests.
The **6 required fields** are given not just as names but as `(name . path . type)` triples:

`info.batch` (String), `info.comp` (Array{String}),
`perform.corr.corrInfo.elec` (Number), `perform.corr.corrInfo.density` (Number),
`perform.mech.mechInfo.yield` (Number), `perform.mech.mechInfo.hard` (Number).

Before defining a new schema, the researcher issues the schema-level query in `query.dcql`
(**Scheme C** — one precise condition + two deliberately relaxed ones), executed on the
platform through the DCQL execution layer:

```sql
SELECT SCHEMA
WHERE perform.corr.corrInfo.elec = Number   -- exact: pin the pitting-potential column (path + type)
  AND ANY yield = Number               -- relaxed (position): some numeric yield, any nesting
  AND EXIST perform.corr.corrInfo.density      -- relaxed (type): density column present, type-free
```

The `AND` joins a corrosion and a mechanical condition in one query because a schema tree
keeps both branches of the `perform` generator, even though any record instantiates one.

## Graded field coverage

Retrieval only certifies that a candidate satisfies the query; it does not say how completely
the candidate covers the full six-field need. Because a DCQL schema condition constrains three
things at once — attribute **name**, nesting **path**, and DCM **type** — each required field
is graded along those dimensions rather than as a binary hit:

| verdict | score | meaning |
|---|---|---|
| `exact`    | 1.0 | name, path, and type all match |
| `var_path` | 0.5 | a same-named field of the required type sits at a **different path** |
| `var_type` | 0.5 | the required **path exists** but carries a different DCM type |
| `missing`  | 0.0 | no corresponding field |

`coverage = mean field score`; the reuse decision follows fixed thresholds:
`= 1.0` reuse directly · `[0.7, 1.0)` reuse with minor extension ·
`[0.4, 0.7)` partial reference · `< 0.4` not reusable.

The two relaxed conditions are what let variants surface **on the queried fields themselves**
(`ANY yield` admits a yield at a different path → `var_path`; `EXIST density` admits a density
of a different type → `var_type`); a strict conjunctive query would have discarded them.

## Files
- `query.dcql` — the DCQL schema-level retrieval statement (Scheme C, as in the paper).
- `schemas/` — the **seven candidates of this illustration** as DCM schema templates
  (path/type format, the same format emitted by
  `../conciseness/_<domain>_conversion/to_schema.py`). They were constructed for this example
  to span a range of match qualities, S1 being the running StainlessSteel schema of the paper;
  shipping them makes the study self-contained and reproducible.
- `match_schemas.py` — an **offline reproduction** of the query, for readers without access to
  the platform. The case study itself runs on NMDMS: the query is parsed, validated, translated
  into a schema-metadata index request and evaluated by the read side (Section 5 of the paper),
  and `schemas/` holds what it returned. This script re-implements the same path/type semantics
  in plain Python: it flattens each schema to a
  path/type map (the `perform` generator contributes its own path segment (Definition 3), so its
  branches are addressed as `perform.corr.*` / `perform.mech.*`), keeps the schemas that satisfy the three query conditions, grades the
  six required fields, and writes `candidates.csv`. To run over the real library instead, set
  `SCHEMA_LIB` (env var) to your exported NMDMS schema library.
- `candidates.csv` — the per-field match matrix of Table rq4, produced by `match_schemas.py`:
  `candidate_schema, <6 required fields>, coverage, reuse_decision`, one row per returned
  candidate, sorted by decreasing coverage.

Reproduce with:

```bash
python3 match_schemas.py      # -> candidates.csv + the K / R / precision summary below
```

## Candidate schemas (`schemas/`)

The seven candidates span a coverage gradient from a full duplicate down to a schema that
clears the filter but is not reusable:

| # | schema | coverage | decision | distinguishing structure |
|---|---|---|---|---|
| S1 | `StainlessSteel`              | 1.00 | reuse directly            | the running example; all six fields exact |
| S2 | `StainlessSteelPerfProfile`  | 0.92 | reuse with minor extension | hardness at `perform.mech.summary.hard` (var_path) |
| S3 | `StainlessSteelCorrMech`     | 0.83 | reuse with minor extension | no hardness column (missing) |
| S4 | `StainlessSteelCorrTensile`  | 0.75 | reuse with minor extension | yield under `perform.mech.tensile` (var_path); no hardness |
| S5 | `StainlessSteelProcCorr`     | 0.67 | partial reference         | density as `Range` (var_type); yield var_path; no hardness |
| S6 | `StainlessSteelPittingScreen`| 0.58 | partial reference         | no composition (missing); density `Range` (var_type); no hardness |
| S7 | `StainlessSteelLegacyLog`    | 0.33 | not reusable              | only pitting potential; density `Range`; yield var_path; no batch/composition/hardness |

## Summary
- Schema-library size of the deployed platform: **N > 2000** (a property of the real NMDMS
  library; the illustration below does not query it).
- Candidates returned by the query over the seven shipped schemas: **K = 7**.
- Reusable candidates (coverage ≥ 0.4): **R = 6**.
- Top-k precision: **R/K = 86%**.

These numbers also fill the paper's Table rq4 sentence. Mixing one exact condition with two
relaxed ones keeps recall high enough to surface the variants, while the exact anchor and the
coverage thresholds screen out the single candidate (S7) that clears the filter but is too
incomplete to reuse.
