# JSONiq / RumbleDB performance benchmark

Times the T2/T3 queries (biomedical + organic-polymer) on
[RumbleDB](https://rumbledb.org/) over the full §6.4 performance datasets. RumbleDB reads
JSON documents directly via `json-doc(...)`, so there is no separate database-load step;
"loading" just stages the converted JSON files where the queries expect them.

## Files

- **1_convert.py** — Builds the JSON documents RumbleDB queries, from the raw data at the
  repo root. Biomedical: merges full `clinical.cohort.json` + `biospecimen.cohort.json` by
  `case_id` into one `cases.json` collection. Polymer: translates `DCQL/oql/{polyamide,processing,pa6t}.json`
  into `materials_library.json`, `processing_logs.json`, `pa6t_library.json`. Mirrors the
  conciseness conversion pipeline; writes to `./data/`.
- **2_load.sh** — Stages the `./data/*.json` documents into a working directory (`./work/`)
  so the queries' bare relative `json-doc("cases.json")` etc. paths resolve. (No real DB load.)
- **3_benchmark.sh** — Runs and times the four queries on RumbleDB with both cold-cache and
  hot-cache methodology. Query text is loaded from the conciseness folder
  (`../../conciseness/JSONiq/{biomedical,organic-polymer}/T2.jq,T3.jq`), not from local files.
  Reports runs / mean / sample stddev per query.

## Run order

```bash
python3 1_convert.py        # raw data -> ./data/*.json
bash 2_load.sh              # stage ./data -> ./work
bash 3_benchmark.sh         # time the 4 queries (hot + cold)
```

Place `rumbledb-1.22.0-standalone.jar` in this folder (or set `JAR=...`). The cold-cache
pass drops the page cache and needs `sudo`; skip it with `DO_COLD=0`. Adjust runs with
`RUNS=N`.
