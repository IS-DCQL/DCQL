# N1QL / Couchbase performance run (§6.4)

Document-store baseline for the DCQL paper using Couchbase + N1QL. Couchbase uses aggregate
document storage, so each logical record is one nested JSON document. Everything lives in one
bucket (`dcql`, scope `_default`): biomedical is one collection `cases`; organic-polymer is
three collections `materials_library`, `processing_logs`, `pa6t_library`. The three scripts
run in order.

| Script | What it does |
| --- | --- |
| `1_convert.py` | Raw data -> Couchbase document structure. Merges the full TCGA `clinical.cohort.json` + `biospecimen.cohort.json` by `case_id` into one `cases` collection (biomedical), and translates the full `polyamide/processing/pa6t.json` into `materials_library` / `processing_logs` / `pa6t_library` with English keys (organic-polymer). Mirrors the §6.2 conversion scripts under `../../conciseness/_biomedical_conversion/` and `_polymer_conversion/`, applied to the full cohort instead of the `_20` subset. Writes JSON to `document/<domain>/`. |
| `2_load.py` | Creates the collections, waits for KV readiness (avoids `key_value_collection_outdated`), imports the JSON via batched threaded `upsert` (retry on failure), then builds the GSI secondary indexes the queries need and waits for them ONLINE. `cases` is keyed by `case_id`; `materials_library` by `basic_info.name` (the T3 join key); `processing_logs` by `meta.data_id`. |
| `3_benchmark.py` | Runs + times the T2/T3 queries. Query text is **read from the conciseness folder** (`../../conciseness/N1QL/{biomedical,organic-polymer}/T2.n1ql,T3.n1ql`), the keyspace is normalised to the loaded bucket/collection, and each query is timed server-side via `metadata().metrics().execution_time()` (same method as the original `time_*.py`). Reports trimmed-mean stats. |

## Run order

```bash
python3 1_convert.py     # raw -> document/<domain>/*.json
python3 2_load.py        # document/* -> Couchbase collections + indexes
python3 3_benchmark.py   # time T2/T3 read from the conciseness .n1ql queries
```

## Configuration (environment variables)

Connection / behaviour are env-driven (defaults shown):

- `CB_CONN_STR` = `couchbase://127.0.0.1`, `CB_USERNAME` = `admin`, `COUCHBASE_PASSWORD` (required)
- `CB_BUCKET` = `dcql`, `CB_SCOPE` = `_default`, `BIO_COLLECTION` = `cases`
- `RUNS` = 50, `WARMUP` = 1, `SLEEP_SECONDS` = 2, `TRIM_FAST_RATIO` = 0.2, `TRIM_SLOW_RATIO` = 0.2, `PRINT_EACH_RUN` = 0
- Raw data paths: `BIO_RAW_DIR` / `CLINICAL_JSON` / `BIOSPECIMEN_JSON`,
  `POLY_RAW_DIR` / `POLYAMIDE_JSON` / `PROCESSING_JSON` / `PA6T_JSON`
- `CONVERT_OUT_DIR` (document output dir), `N1QL_QUERY_ROOT` (defaults to `../../conciseness/N1QL`)

The full TCGA cohort is obtained via the GDC link and the polymer files via the NMDMS link in
the paper (see `../../data/README.md`); the conversion mirrors the §6.2 teaching scripts on the
full data. `json_array_to_ndjson.py` is a helper: `2_load.py` imports its `iter_json_docs`
reader, and it also works standalone to stream a huge top-level JSON array into NDJSON.

The published `.n1ql` files mix bucket names (`medical` / `dcql`); `3_benchmark.py` normalises
the keyspace to `CB_BUCKET` and points the biomedical default-keyspace reference at the `cases`
collection, leaving the rest of each query verbatim.

Queries timed: biomedical T2 (find by `case_id` on `cases`), biomedical T3 (RNA / primary-tumor
nested-array filter on `cases`), organic-polymer T2 (find on `processing_logs`), organic-polymer
T3 (semi-aromatic `materials_library` INNER JOIN `processing_logs`).
