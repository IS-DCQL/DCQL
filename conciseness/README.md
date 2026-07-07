# §6.2 Syntactic Conciseness — Query Corpus, Converters, Metrics

Everything behind the **syntactic-conciseness** study of §6.2 (Figure 5): the query
statements of all 7 languages over the 16 workloads, the data converters that ground
those queries in real storage structures, and the measurement script that produces the
LOC / syntactic-noise / Halstead numbers.

## 1. Query corpus — `‹LANGUAGE›/‹domain›/‹task›.‹ext›`

```
conciseness/<LANGUAGE>/<domain>/<task>.<ext>
```
- **7 languages**: `DCQL SQL OQL MQL N1QL XQuery JSONiq`
- **4 domains**: `biomedical  stainless-steel  organic-polymer  high-energy-physics`
- **16 workloads** (4 per domain, matching Appendix Table A.1). Task file names per domain:
  biomedical `T1 T2 T3 T4`; stainless-steel `T1-1 T1-2 T3 T4`; organic-polymer `T1 T2 T3 T4`;
  high-energy-physics `T2 T3-1 T3-2 T4`.
- 7 × 16 = **112 query files**. Extensions: `DCQL.dcql`, `SQL.sql`, `OQL.jpql`
  (organic-polymer T2/T3 are `.sql`, run as native SQL through Hibernate), `MQL.js`,
  `N1QL.n1ql`, `XQuery.xq`, `JSONiq.jq`.

Each file is the **standard implementation** of that workload in that language — pure
statements, no execution scaffolding. **Every language completes every workload's intent:**
where a language cannot do a task natively, the realistic workaround is written and counted
(e.g. OQL/JPQL renames an attribute via a persistent-class change + a Java migration;
JSONiq performs mutations by rewriting documents). DCQL cells use real DCQL syntax (from
`grammar/DCQL.g4`), not an Elasticsearch backend.

These same files are the single source of truth for §6.4: the `performance/` benchmark
scripts load their T2/T3 queries from here.

## 2. Data converters — `_‹domain›_conversion/`

Each domain has a pipeline (`_biomedical_conversion/`, `_stainless_conversion/`,
`_polymer_conversion/`, `_hep_conversion/`) that renders the same logical data into the
**four** storage structures of **Table 2**, so the queries are written against real schemas:

| script | structure | language(s) | Table 2 row |
|---|---|---|---|
| `to_relational.py` | relational tables (CSV) | SQL | relational (tables) |
| `to_document.py` | nested document collections | MQL / N1QL / XQuery / JSONiq / DCQL backend | document (collections) |
| `to_schema.py` | **DCM schemas** (DCM templates) | DCQL's native storage unit | DCM structure (schemas) |
| `to_object.py` | object classes (`*.java` + extents) | OQL | object (classes) |

The relational/document/object counts reproduce the as-run §6.4 storage schema; the DCM
schema count equals the document-collection count. See each folder's `README.md` for the
per-domain table/collection/class/schema lists, the source data, and (stainless/polymer)
the Chinese→English translation. Generated outputs (`relational/ document/ object/ schema/
*_en.json`) are **derived and gitignored** — regenerate with the scripts; the scripts, the
committed `object/*.java`, and the READMEs ship.

## 3. Metrics — `metrics/`

`measure.py` computes the three §6.2 metrics over the 112 query files and writes
`metrics_results.csv` (per language) + `metrics_by_file.csv` (per cell); `noise_schemes.py`
holds the syntactic-noise variants that were compared. These feed Figure 5(a–c) and the
radar Figure 10 in `../../performance/plot_figures.py`. See `metrics/README.md`.

## Notes
- **organic-polymer T3** dropped its monomer sub-condition: the §6.4 polymer data has no
  monomer field, so the as-run T3 had none either. Details + the §6.2↔§6.4 alignment are in
  `QUERY_CONSISTENCY_biomedical_polymer.md`.
- The two schema-retrieval workloads (stainless `T1-2`, organic-polymer `T1`) use DCQL's
  `select schema where exist …` form (§3.2 two-level retrieval).
