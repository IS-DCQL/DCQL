# OQL-Hibernate performance benchmark

Measures OQL-style query performance using **JPQL/HQL + native SQL over
Hibernate**, backed by **PostgreSQL**. OQL has no standalone engine, so the
object queries run through Hibernate (JPA) on a relational store. Two datasets
are covered: the biomedical **TCGA** tables (queried as JPQL over entity
classes) and the organic-**polymer** tables (queried as native SQL).

## Run order

1. **`1_convert.py`** — raw JSON dumps → relational CSVs.
   Streams the TCGA dump into 8 tables (projects, demographics, cases,
   diagnoses, samples, portions, analytes, aliquots) and the polymer dumps
   (polyamide / processing / pa6t) into 5 tables (materials, processing_cases,
   waxd_results, performance_results, pa6t_simulations). Edit the input paths
   and `DATASETS` at the top of the file. Needs `pip install ijson`.

2. **`2_load.py`** — create schema + import CSVs into PostgreSQL.
   Drops/recreates each table, `COPY`s the CSVs through temp tables, and builds
   the indexes the queries rely on. Edit DB connection / `CSV_DIR` / `DATASETS`
   at the top. Needs `pip install psycopg2` and `PG_PASSWORD` in the env.

3. **`3_benchmark.java`** — run + time the four T2/T3 queries.
   The query TEXT is loaded at runtime from the shared conciseness folder
   (`../../conciseness/OQL/...`), not hardcoded, so the same statements measured
   for conciseness are executed here. Biomedical T2/T3 run as JPQL via
   `createQuery`; polymer T2/T3 run as native SQL via `createNativeQuery`. Each
   query is warmed up then measured (point query 500 rounds, heavy screens 20),
   timing `getResultList()` with `System.nanoTime()` plus Hibernate
   `Statistics`; the fastest/slowest 20% are trimmed and mean + sample std-dev
   reported.

   The compilable class lives at
   `src/main/java/com/example/oqltest/runner/QueryBenchmarkRunner.java`
   (`3_benchmark.java` at the root is an identical reference copy). Build/run
   with Maven from this folder:

   ```bash
   export PG_PASSWORD=...            # and optionally PG_USER
   mvn -q spring-boot:run            # queries dir defaults to ../../conciseness/OQL
   # override the location if running from elsewhere:
   mvn -q spring-boot:run -Dspring-boot.run.jvmArguments="-Dqueries.dir=/abs/path/conciseness/OQL"
   ```

## Layout

```
1_convert.py     raw data -> relational CSVs (TCGA 8 tables + polymer 5 tables)
2_load.py        create schema + import CSVs into PostgreSQL
3_benchmark.java reference copy of the Hibernate benchmark runner
pom.xml          Spring Boot + JPA (Hibernate) + PostgreSQL build
src/             entity classes (Project, CaseEntity, Demographic, Diagnosis,
                 Sample, Portion, Analyte, Aliquot), JpqlOqlTestApplication,
                 runner/QueryBenchmarkRunner.java (the compiled benchmark),
                 resources/application.properties (datasource + Hibernate stats)
```

## Query sources (read at runtime)

| Benchmark               | File                                          | Executed as |
|-------------------------|-----------------------------------------------|-------------|
| biomedical T2           | `../../conciseness/OQL/biomedical/T2.jpql`    | JPQL        |
| biomedical T3           | `../../conciseness/OQL/biomedical/T3.jpql`    | JPQL        |
| organic-polymer T2      | `../../conciseness/OQL/organic-polymer/T2.sql`| native SQL  |
| organic-polymer T3      | `../../conciseness/OQL/organic-polymer/T3.sql`| native SQL  |
