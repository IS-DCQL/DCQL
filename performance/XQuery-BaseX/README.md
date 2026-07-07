# XQuery / BaseX — §6.4 performance run

Hot-cache execution-time benchmark for the XQuery engine (BaseX), over the two
workloads used in the paper: **biomedical** (TCGA) and **organic-polymer**.

## Files

| File | What it does |
|---|---|
| `1_convert.py` | Raw data → the form BaseX imports. Biomedical: merges `biomedical-TCGA/clinical.cohort.json` + `biospecimen.cohort.json` by `case_id` into one `cases` document set → `prepared_for_basex.xml` (single-underscore element names). Polymer: translates + consolidates `DCQL/oql/{polyamide,processing,pa6t}.json` into the 3 collections → `materials_library_en.json`, `processing_logs_en.json`, `pa6t_library_en.json`. Mirrors `conciseness/_biomedical_conversion` and `_polymer_conversion`. |
| `2_load.sh` | Creates the 4 BaseX databases + TEXT indexes via `create_db_and_indexes.bxs`: `tcga_cases` (XML), and `materials_library` / `processing_logs` / `pa6t_library` (native JSON, served as `map`/`<string\|number key=..>`). |
| `3_benchmark.sh` | Runs + times the four §6.2 queries (biomedical T2/T3 + polymer T2/T3). Query **text is read verbatim** from `../../conciseness/XQuery/{biomedical,organic-polymer}/{T2,T3}.xq` (not hardcoded). Per query: 1 discarded warm-up + `RUNS` (10) hot runs; time parsed from BaseX's `<testsuite time="PT..S">`. |

`create_db_and_indexes.bxs` is the BaseX import script invoked by `2_load.sh`.

## Run order

```bash
python3 1_convert.py     # raw -> prepared_for_basex.xml + 3 *_en.json
./2_load.sh              # create DBs + indexes
./3_benchmark.sh         # time biomedical T2/T3 + polymer T2/T3
```

The BaseX executable is expected at `./bin/basex` (or on `$PATH`); override with
`BASEX=/path/to/basex`. Conversion outputs (`prepared_for_basex.xml`, `*_en.json`)
are derived and git-ignored — regenerate with `1_convert.py`.

Raw sources are resolved relative to this folder at `../../../` (repo root):
`biomedical-TCGA/` and `DCQL/oql/`. The full TCGA cohort (~50k cases) is the §6.4
performance data; the `conciseness` §6.2 scripts use the `_20` teaching subset.
