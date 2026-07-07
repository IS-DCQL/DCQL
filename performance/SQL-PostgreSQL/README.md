# SQL (PostgreSQL) — §6.4 performance baseline

PostgreSQL 14 baseline for the §6.4 latency experiment. Two domains are loaded
into one database: the **biomedical** TCGA data as a 3NF `clinical` schema of 16
tables, and the **organic-polymer** data as 5 denormalised tables in `public`.
The T2/T3 query latencies are then measured.

## Scripts (run in order)

| # | Script | What it does |
|---|--------|--------------|
| 1 | `1_convert.py` | Raw data → relational CSV tables. Streams the TCGA clinical JSON into the 16 biomedical tables (`./csv_exports/`), and mirrors `../../conciseness/_polymer_conversion/to_relational.py` to emit the 5 polymer tables (`./csv_exports_polymer/`). |
| 2 | `2_load.py` | Creates the schema and imports the converted tables. Builds the `clinical` 16-table schema (+FKs, indexes) and loads its CSVs via `COPY`; also creates and loads the 5 `public` polymer tables. Drops/recreates the `clinical` schema first (folded-in `cleanup_db()`). |
| 3 | `3_benchmark.py` | Runs and times the T2/T3 queries. Loads the four query texts from `../../conciseness/SQL/{biomedical,organic-polymer}/{T2,T3}.sql`, then times each with the as-run methodology (Nested-Loop/Index-Scan optimizer pinning, 5 warm-up runs discarded + 25 measured runs, mean/median/stddev/CV). Writes `performance_result.txt`. |

## Credentials & config

Connection settings are read from environment variables (no hardcoded password):

```bash
export PG_PASSWORD=...        # required
export PG_DATABASE=clinical_db   # optional, defaults shown
export PG_USER=sal
export PG_HOST=localhost
export PG_PORT=5432
```

The biomedical raw-JSON path is a config constant at the top of `1_convert.py`
(`JSON_FILE_PATH`). The polymer source files (`*_en.json`) are read from
`../../conciseness/_polymer_conversion/`; both the raw JSON and those `*_en.json`
are **derived** and not committed — regenerate them before running.

## Run

```bash
python 1_convert.py
python 2_load.py
python 3_benchmark.py
```
