# Stainless-steel data conversion (for §6.2 queries)

Pipeline that takes the NMDMS raw stainless-steel data (DCM format, originally
Chinese) and produces the four storage structures used by the §6.2 conciseness
queries, at the counts given in **Table 2** (relational = 8 tables, document = 2
collections, DCM schema = 2 schemas, object = 5 classes).

## Run order
```
python3 translate_to_english.py   # Chinese -> English  (raw stainless-NMDMS/*.json -> *_en.json)
python3 to_document.py            # -> document/   (2 collections)
python3 to_relational.py          # -> relational/ (8 tables, CSV)
python3 to_object.py              # -> object/     (5 class defs + object graph)
python3 to_schema.py              # -> schema/     (2 DCM schemas; reads document/)
```

## (4) DCM schema — 2 schemas
**mechanical_properties** and **pitting_corrosion** — the DCM templates (schemas) DCQL
stores the data under, one per collection. Each `schema/<name>.schema.json` is in the native
DCM template format (`{_type, r, …}` per attribute, English DCM type names, nested for
containers/arrays), inferred from the document output. The schema count equals the
document-collection count (Table 2, "DCM structure" row).

## Translation
`translate_to_english.py` translates all attribute keys, the DCM `_type` values, and a
dictionary of common categorical values (material category, microstructure, specimen
shape, method, heat-treatment terms). Numeric strings, element symbols, grade codes,
and free text are kept as-is. Output: `stainless_mechanical_en.json` (265 records),
`stainless_pitting_en.json` (352 records).

## (1) Relational — 8 tables
From `mechanical_properties`: **steel**, **composition**, **mechanical_property**.
From `pitting_corrosion`: **pitting_experiment**, **element_content**,
**solution_environment**, **experimental_condition**, **corrosion_result**.
Key columns used by the T3 query: `solution_environment.NaCl_wt`,
`experimental_condition.temperature_c`, `corrosion_result.pitting_potential_eb_v`,
`pitting_experiment.yield_strength_mpa`, `pitting_experiment.grade`.

## (2) Document — 2 collections
**mechanical_properties** (composition + mechanical) and **pitting_corrosion**
(corrosion experiments). Each document keeps the nested `{meta, content}` form;
fields are arrays-of-one (DCM table type), e.g.
`content.solution_environment[0].NaCl_wt`, `content.result_characterization[0].pitting_potential_eb_v`.

## (3) Object — 5 classes
**Steel** (1:N `Composition`, 1:1 `MechanicalProperty`) and **PittingExperiment**
(1:1 `CorrosionResult`; element content / solution environment / conditions embedded).
Class defs in `object/*.java`.

## Notes
- The generated data (`*_en.json`, `relational/*.csv`, `document/*.json`,
  `object/object_instances.json`) is **derived** and gitignored — regenerate with the
  scripts. The scripts, the 5 `object/*.java` class definitions, and this README are
  committed.
- The §6.2 stainless queries under `../<language>/stainless-steel/` are written against
  these structures.
