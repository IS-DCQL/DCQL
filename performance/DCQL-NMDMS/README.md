# DCQL on NMDMS — performance scripts

DCQL runs on the NMDMS read path, whose execution layer is an inverted-index engine. The
three scripts follow the shared `performance/` convention:

| step | script | what it does |
|---|---|---|
| 1 | `1_convert.py` | raw data → document collections: biomedical `cases` (clinical+biospecimen merged by case_id) and organic-polymer `materials_library` / `processing_logs` / `pa6t_library` |
| 2 | `2_load.py` | create one index per collection (nested mappings) + bulk-load the converted documents |
| 3 | `3_benchmark.py` | time T2/T3 for both domains |

**Storage unit.** DCQL's logical storage unit is the **DCM schema** (one schema per
document collection — Table 2, "DCM structure" row): biomedical = 1, organic-polymer = 3.
On this read path each schema is materialised as one inverted index (step 2). The DCM
schema templates themselves are produced by `../../conciseness/_<domain>_conversion/to_schema.py`.

**Queries.** The canonical query for each task is the **DCQL statement**, loaded at run
time from `../../conciseness/DCQL/<domain>/{T2,T3}.dcql` (single source of truth, printed
for provenance). The read engine executes the corresponding translation held in
`DSL_TRANSLATION` (the biomedical-T3 body is the one used in the §6.4 run, kept verbatim);
server-side time is read from the engine's `took`.

Connection via env vars (`DCQL_HOST`, optionally `DCQL_USER`/`DCQL_PASSWORD`); knobs
`RUNS`, `SLEEP_SECONDS`. For a quick smoke test point `CLINICAL_JSON`/`BIOSPECIMEN_JSON`
at the `*_20.json` teaching files.
