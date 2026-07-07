# Biomedical (TCGA) data conversion (for §6.2 queries)

Pipeline that takes the raw GDC/TCGA exports and produces the four storage structures
used by the §6.2 conciseness queries, at the counts given in **Table 2** (relational =
16 tables, document = 1 collection, DCM schema = 1 schema, object = 8 classes). The
relational/document/object structures reproduce exactly the as-run §6.4 performance schema
(`performance/SQL-PostgreSQL/data_importer.py`, schema `clinical`); the DCM schema is the
storage unit DCQL itself uses.

The raw exports are already in English (GDC field names), so no translation step is
needed — unlike the stainless-steel / polymer pipelines.

## Run order
```
python3 to_document.py     # -> document/   (1 collection)
python3 to_relational.py   # -> relational/ (16 tables, CSV)
python3 to_object.py       # -> object/     (8 class extents + object graph)
python3 to_schema.py       # -> schema/     (1 DCM schema; reads document/)
```
to_document / to_relational / to_object read the same merged case records via `_common.py`;
to_schema infers the DCM template from the document output.

## (4) DCM schema — 1 schema
**cases** — the DCM template (schema) DCQL stores the data under. `schema/cases.schema.json`
is in the native DCM template format: each attribute maps to `{_type, r, …}` with English
DCM type names (string / number / container / array / …), nested for containers and arrays.
The schema count equals the document-collection count (Table 2, "DCM structure" row).

## Source
- `biomedical-TCGA/clinical.cohort_20.json`     — case + project + demographic + diagnoses[]
- `biomedical-TCGA/biospecimen.cohort_20.json`  — samples[] → portions[] → {slides[], analytes[] → aliquots[]}

This is the **20-record teaching subset** used for §6.2 (and §6.5 usability). The full
~50 000-case cohort used in the §6.4 performance test is obtained via the GDC link in the
paper; it is not shipped here.

## (1) Document — 1 collection
**cases** — the entire patient record as one nested document (aggregate storage). Shared
by MQL / N1QL / XQuery / JSONiq / DCQL. Path examples used by the queries:
`demographic.vital_status`, `diagnoses[].primary_diagnosis`,
`samples[].portions[].analytes[].aliquots[].concentration`.

## (2) Relational — 16 tables
3NF split of the same data; table & column names match the SQL/OQL §6.2 queries and the
as-run `clinical` schema (`clinical.table_case`, `clinical.table_aliquot`, …):
`table_project, table_case, table_demographic, table_diagnosis, table_treatment,
table_pathology_detail, table_follow_up, table_molecular_test,
table_other_clinical_attribute, table_exposure, table_family_history, table_sample,
table_portion, table_slide, table_analyte, table_aliquot`.

The 20-record subset populates the entity types it contains (project, case, demographic,
diagnosis, **treatment**, sample, portion, slide, analyte, aliquot). The longitudinal /
clinical-supplement tables (`pathology_detail`, `follow_up`, `molecular_test`,
`other_clinical_attribute`, `exposure`, `family_history`) are part of the full TCGA model
but carry no rows in the teaching subset; their headers are emitted so the schema stays
complete and matches Table 2.

## (3) Object — 8 classes
`Project, Case, Demographic, Diagnosis, Sample, Portion, Analyte, Aliquot`
(`object/*.java`). Slides and the clinical supplements are embedded value lists, not
first-class persistent classes — hence 8 classes vs. 14 tables. `to_object.py` emits the
materialised graph + per-class extent sizes.

## Notes
- Generated data (`document/`, `relational/`, `object/object_instances.json`) is
  **derived** and gitignored — regenerate with the scripts. The scripts, the 8
  `object/*.java` class definitions, and this README are committed.
- The §6.2 biomedical queries under `../<language>/biomedical/` are written against these
  structures.
