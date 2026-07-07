# MQL / MongoDB performance run (§6.4)

Document-store baseline for the DCQL paper. MongoDB uses aggregate document storage, so
each logical record is one nested document. The three scripts run in order:

| Script | What it does |
| --- | --- |
| `1_convert.py` | Raw data -> MongoDB document structure. Merges the full TCGA `clinical.cohort.json` + `biospecimen.cohort.json` by `case_id` into one collection `cases` (biomedical), and translates the full `polyamide/processing/pa6t.json` into three collections `materials_library`, `processing_logs`, `pa6t_library` (organic-polymer). Writes JSON to `document/<domain>/`. |
| `2_load.py` | Imports those JSON collections into MongoDB (batched `insert_many`) and builds the indexes used by the queries. Biomedical -> db `dcql_bio`; polymer -> db `dcql_poly`. |
| `3_benchmark.py` | Runs + times the T2/T3 queries. Query text is **read from the conciseness folder** (`../../conciseness/MQL/{biomedical,organic-polymer}/T2.js,T3.js`), parsed into find/aggregate commands, and timed server-side via `explain('executionStats').executionTimeMillis` (same method as the original `time.py`). Reports trimmed-mean stats. |

## Run order

```bash
python3 1_convert.py     # raw -> document/<domain>/*.json
python3 2_load.py        # document/* -> MongoDB + indexes
python3 3_benchmark.py   # time T2/T3 from the conciseness .js queries
```

## Configuration (environment variables)

Connection / behaviour are env-driven (defaults shown):

- `MONGO_URI` = `mongodb://localhost:27017`
- `BIO_DB` = `dcql_bio`, `POLY_DB` = `dcql_poly`
- `RUNS` = 100, `WARMUP` = 1, `TRIM_RATIO` = 0.2, `PRINT_EACH_RUN` = 0
- Raw data paths: `BIO_RAW_DIR` / `CLINICAL_JSON` / `BIOSPECIMEN_JSON`,
  `POLY_RAW_DIR` / `POLYAMIDE_JSON` / `PROCESSING_JSON` / `PA6T_JSON`
- `MQL_QUERY_ROOT` (defaults to `../../conciseness/MQL`)

The full TCGA cohort is obtained via the GDC link in the paper; the conversion logic mirrors
the §6.2 teaching scripts under `../../conciseness/_biomedical_conversion/` and
`../../conciseness/_polymer_conversion/`, applied to the full data instead of the `_20` subset.

Queries timed: biomedical T2 (find by `case_id` on `cases`), biomedical T3 (RNA / primary-tumor
aggregate on `cases`), organic-polymer T2 (find on `processing_logs`), organic-polymer T3
(semi-aromatic aggregate + `$lookup` on `materials_library`).
