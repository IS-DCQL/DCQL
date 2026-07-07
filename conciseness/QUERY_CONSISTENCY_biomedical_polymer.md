# Query consistency: §6.2 conciseness ↔ §6.4 performance (biomedical & organic-polymer)

**Status: resolved by single-sourcing.** The §6.4 timing scripts now load their T2/T3
query text directly from the §6.2 conciseness files
(`performance/<LANG>-<DB>/3_benchmark.*` reads `conciseness/<LANG>/<domain>/{T2,T3}.<ext>`),
so the two sections execute the *same* query text by construction. This note records how
the two were aligned.

## Ground rule
- **Performance data is authoritative** (it is the experiment that was actually run).
  Table 2 and the conversion scripts follow what §6.4 did.
- **Query language statements live in `conciseness/`** and are imported by §6.4.

## Data selection reproduced by the converters
- **Biomedical**: merge `clinical.cohort.json` + `biospecimen.cohort.json` by `case_id`
  into one document per patient → **16 relational tables / 1 collection / 8 classes**.
- **Organic-polymer**: only the three prepared files `polyamide.json` + `processing.json` +
  `pa6t.json` → **5 tables / 3 collections / 5 classes** (`materials`, `processing_cases`,
  `waxd_results`, `performance_results`, `pa6t_simulations`; collections
  `materials_library`, `processing_logs`, `pa6t_library`). The denormalised `materials`
  table carries the property columns inline (`glass_temperature`, `tensile_strength`, …).

Table 2 was updated to these counts (biomedical 16/1/8, polymer 5/3/5); the §6.2 figures
and analysis numbers were regenerated against the synced queries.

## Biomedical — consistent (identical text)
The conciseness biomedical queries already referenced the as-run `clinical.table_*`
schema, so no change was needed; the benchmark imports them verbatim. DCQL: the canonical
query is the `.dcql` statement, executed by the NMDMS read engine (its biomedical-T3 DSL
translation is the one used in the §6.4 run, preserved verbatim).

## Organic-polymer — query identifiers synced to the as-run schema
The conciseness polymer queries originally used a more-normalised, differently-named
schema. Their **identifiers were synced** to the as-run names (`materials`,
`processing_cases.speed`, `waxd_results.crystallinity/sample_no`,
`materials.glass_temperature/tensile_strength`, `basic_info.category`,
`machine_settings.injection.stages`, collections `materials_library/processing_logs/pa6t_library`).
Query **logic is unchanged except** for one forced edit:

- **Monomer sub-condition dropped from T3.** The three as-run polymer files contain **no
  monomer data** (the monomer-bearing `semi_aromatic_PAS.json` was not part of the §6.4
  selection), and the as-run polymer T3 indeed had no monomer filter. So the §6.2 T3
  monomer clause (terephthalic acid) was removed across all 7 languages and **Appendix A.1's
  T3 description was updated to match**. The remaining T3 logic (semi-aromatic +
  glass-temperature > 280 + tensile > 150 + injection speed > 50) maps cleanly.

`category` is translated to English in the converters (the original semi-aromatic label is
mapped to `Semi-Aromatic`, and so on) so the `category = "Semi-Aromatic"` filters bind.

## Effect on §6.2 metrics (re-measured)
Syncing identifiers + dropping the monomer clause shifted the metrics slightly; figures
fig5a/b/c + fig10 were regenerated and the §6.2 numbers updated. Notable: DCQL total LOC
67 (lowest); SQL Halstead is now second-lowest (text corrected accordingly).
