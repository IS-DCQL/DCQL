# DCQL — Performance & Scalability Benchmark (Paper §6.4)

Code and scripts to reproduce the **performance and scalability** experiments
(§6.4 *Performance and Scalability Testing*) of the DCQL paper.

Folders are named `QueryLanguage-Database`, and each contains the **same three steps**:

| step | file | role |
|---|---|---|
| 1 | `1_convert.*` | raw data → this engine's storage structure (the conversion + data selection of §6.4: biomedical = clinical+biospecimen merged by `case_id`; organic-polymer = the three prepared files `polyamide.json` + `processing.json` + `pa6t.json`) |
| 2 | `2_load.*` | create the schema (if any) + import the converted data + build indexes |
| 3 | `3_benchmark.*` | run + time the four T2/T3 queries (two domains), **loading each query's text from `../../conciseness/<LANG>/<domain>/<task>.<ext>`** rather than embedding it |

The query statements are therefore single-sourced from `conciseness/` (the §6.2
artifacts); the benchmark scripts only supply the timing harness and execution wiring.
DCQL is single-sourced as the `.dcql` statement, executed by the NMDMS read engine (see
`DCQL-NMDMS/README.md`).

> Tasks T1 and T4 are schema-definition / structure-evolution operations whose
> cost is dominated by one-off DDL; §6.4 therefore reports only the read tasks
> **T2** (basic read/write) and **T3** (complex analysis and navigation), which is
> why only T2/T3 queries appear here.

## Language → folder map

| Paper language | Folder | Engine used by the code |
|---|---|---|
| **DCQL** | `DCQL-NMDMS/` | NMDMS platform (this study) |
| **SQL** | `SQL-PostgreSQL/` | PostgreSQL 14.2 |
| **OQL** | `OQL-Hibernate/` | JPQL / Hibernate over PostgreSQL |
| **MQL** | `MQL-MongoDB/` | MongoDB 8.2.6 |
| **N1QL** | `N1QL-Couchbase/` | Couchbase 7.0.3 |
| **XQuery** | `XQuery-BaseX/` | BaseX 10.7 |
| **JSONiq** | `JSONiq-RumbleDB/` | RumbleDB 1.22.0 |

## Repository layout

```
performance/
├── environment.yml                 # conda env (Python deps for all scripts)
├── results/                        # raw timing outputs + aggregated values behind Figs 11-12 (see results/README.md)
├── expand_data/
│   └── expand.py                   # synthetic data scaling 1X..1000X (§6.4.3); seeded, same distribution, non-repeating
├── DCQL-NMDMS/      { 1_convert.py, 2_load.py, 3_benchmark.py }     # read engine: NMDMS inverted index
├── SQL-PostgreSQL/  { 1_convert.py, 2_load.py, 3_benchmark.py }     # 16 `clinical` tables + 5 `public` polymer tables
├── OQL-Hibernate/   { 1_convert.py, 2_load.py, 3_benchmark.java, pom.xml, src/ }   # JPQL (biomedical) + native SQL (polymer)
├── MQL-MongoDB/     { 1_convert.py, 2_load.py, 3_benchmark.py }
├── N1QL-Couchbase/  { 1_convert.py, 2_load.py, 3_benchmark.py, json_array_to_ndjson.py }
├── XQuery-BaseX/    { 1_convert.py, 2_load.sh, 3_benchmark.sh, create_db_and_indexes.bxs }
└── JSONiq-RumbleDB/ { 1_convert.py, 2_load.sh, 3_benchmark.sh }
```

Storage-unit counts match Table 2: biomedical = 16 relational tables / 1 document
collection / 8 object classes; organic-polymer = 5 / 3 / 5.

## Datasets (not stored in this repo)

The raw and derived data files are large (hundreds of MB to ~1 GB) and are **not**
committed here (GitHub rejects files >100 MB). They are published separately:

- **Raw data** — biomedical (`db.json`, GDC/TCGA) and the material files
  (`pa6t.json`, `polyamide.json`, `processing.json`): **<ADD Zenodo/figshare DOI or release link>**.
- **Derived formats are regenerated from the raw data by each folder's `1_convert.*`**,
  so they need not be archived (`expand_data/expand.py` produces the scaled
  `expanded_<FACTOR>.json` datasets for §6.4.3).

Place the raw files where each script expects them (see the path constants near the
top of every script) or edit those constants.

## Credentials (set via environment variables)

No passwords are stored in the code. Export the following before running:

```bash
export COUCHBASE_PASSWORD=...      # N1QL-Couchbase/*.py
export PG_USER=dcql                # OQL-Hibernate (optional; defaults to dcql)
export PG_PASSWORD=...             # OQL-Hibernate import_*.py and Spring application.properties
export DCQL_USER=... DCQL_PASSWORD=...  # DCQL-NMDMS, only if the store enables security
```

## Environment & engine versions

Python dependencies: `conda env create -f environment.yml`.
OQL additionally needs JDK 17+ and Maven (`cd OQL-Hibernate && mvn spring-boot:run`).

Engine versions used by the code (paper §6.4.1 has been aligned to these):

| Engine | Version |
|---|---|
| PostgreSQL (SQL, OQL backend) | 14.2 |
| MongoDB (MQL) | 8.2.6 |
| Couchbase (N1QL) | 7.0.3 |
| BaseX (XQuery) | 10.7 |
| RumbleDB (JSONiq) | 1.22.0 |
| NMDMS platform (DCQL) | this study |

## Benchmark methodology (as implemented)

- **Cold cache**: drop the OS page cache (`sync; echo 3 > /proc/sys/vm/drop_caches`)
  and the DB, then measure the first execution (see `JSONiq-RumbleDB/bench_cold.sh`).
- **Hot cache**: run the same query 10 times, discard the first 2 warm-ups, and
  report the mean and standard deviation of the last 8 runs.
- All reported times are **server-side query-execution time** (e.g. Hibernate
  `Statistics` API for OQL), excluding network/end-to-end overhead.
- The Python harnesses (`time.py`, `time_*.py`) additionally support a
  trimmed mean (drop the fastest/slowest 20%) for stability.

## Status / TODO

- [x] All seven folders normalised to `{1_convert, 2_load, 3_benchmark}` with queries single-sourced from `conciseness/`.
- [x] **`results/`**: aggregated tables behind Figures 11–12 (`latency_fig11.csv`, `scalability_fig12.csv`).
- [ ] Add the dataset DOI / download link above.
