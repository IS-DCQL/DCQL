# Organic-polymer data conversion (for §6.2 queries)

Reproduces the storage structures used by the **§6.4 performance run**, at the counts in
**Table 2** (relational = 5 tables, document = 3 collections, DCM schema = 3 schemas,
object = 5 classes). The performance run selected **three prepared files** (not the full
NMDMS dump):

| collection / source | records |
|---|---|
| `materials_library` ← `DCQL/oql/polyamide.json` | 1093 polymer-structure records (fully aromatic + semi-aromatic + aliphatic, with `category`) |
| `processing_logs` ← `DCQL/oql/processing.json` | 128 injection/holding/cooling + WAXD/SAXS + mechanical records |
| `pa6t_library` ← `DCQL/oql/pa6t.json` | ~31.9k PA6T-copolymer Tg-vs-density/energy simulation rows |

## Run order
```
python3 translate_to_english.py   # 3 source files -> *_en.json (keys translated)
python3 to_document.py            # -> document/   (3 collections)
python3 to_relational.py          # -> relational/ (5 tables, CSV; schema `public`)
python3 to_object.py              # -> object/     (5 class extents + object graph)
python3 to_schema.py              # -> schema/     (3 DCM schemas; reads document/)
```

## (4) DCM schema — 3 schemas
**materials_library**, **processing_logs**, **pa6t_library** — the DCM templates (schemas)
DCQL stores the data under, one per collection. Each `schema/<name>.schema.json` is in the
native DCM template format (`{_type, r, …}` per attribute, English DCM type names, nested
for containers/arrays), inferred from the document output. The schema count equals the
document-collection count (Table 2, "DCM structure" row).

## Translation
Attribute keys and DCM `_type` values are translated to English; `category` is already
present in the source. **Chemical entity names / SMILES / categorical values are kept
verbatim** (the §6.2 queries match on them).

## (1) Document — 3 collections
`materials_library, processing_logs, pa6t_library`. Path examples used by the queries:
`basic_info.category`, `samples[].thermal.glass_temperature`,
`samples[].mechanical.tensile_strength` (materials_library);
`WAXD_result.alpha_crystallinity`, `machine_settings.injection.stages` (processing_logs).

## (2) Relational — 5 tables (as-run, schema `public`, denormalised)
`materials` (property columns inline: `glass_temperature`, `tensile_strength`, …),
`processing_cases` (`speed`, `injection_rate`, …), `waxd_results` (`crystallinity`),
`performance_results`, `pa6t_simulations`. Column names reproduce
`DCQL/oql/csv_output/*.csv` exactly.

## (3) Object — 5 classes
`Material, ProcessingCase, WaxdResult, PerformanceResult, Pa6tSimulation` (`object/*.java`),
one per storage unit. The performance run reached polymer data via Hibernate over these
5 `public` tables (raw SQL), so the object model mirrors the relational tables 1:1.

## Note on the §6.2 vs. as-run task
The as-run polymer relational schema is denormalised and has **no separate `monomers`
table**; the §6.2 polymer T3 query's monomer sub-condition has no column to bind to in
this schema (see `../QUERY_CONSISTENCY_biomedical_polymer.md`). The §6.2 query identifiers
are synced to these table/column names; where a concept is absent from the as-run schema
it is documented there.

## Notes
- Generated data (`*_en.json`, `document/`, `relational/`, `object/object_instances.json`)
  is **derived** and gitignored — regenerate with the scripts. Scripts, the 5
  `object/*.java`, and this README are committed.
