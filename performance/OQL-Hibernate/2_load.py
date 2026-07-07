#!/usr/bin/env python3
"""Step 2 — create schema + import CSVs into PostgreSQL.

Loads the CSVs produced by `1_convert.py` into the `public` schema that the
Hibernate benchmark (`3_benchmark.java`) queries. Covers BOTH datasets:

  * medical   8 tables: projects, demographics, cases, diagnoses,
              samples, portions, analytes, aliquots (FK chain + indexes)
  * material  5 tables: materials, processing_cases, waxd_results,
              performance_results, pa6t_simulations (+ indexes)

For each table it: drops & recreates (optional), COPYs the CSV into a temp
table with a progress bar, then INSERT ... ON CONFLICT DO NOTHING into the real
table, and finally builds the indexes the queries rely on.

Run `python 1_convert.py` first.
"""
import os
import sys
from pathlib import Path
import psycopg2


# =========================
# Edit the parameters here
# =========================

DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "test"
DB_USER = "dcql"
DB_PASSWORD = os.environ.get("PG_PASSWORD", "")

CSV_DIR = Path("/home/sal/joql/csv_output")

# which datasets to load: any of {"medical", "material"}
DATASETS = {"medical", "material"}

# Whether to delete old data/old tables before each run
CLEAN_DATABASE_FIRST = True
# Whether to rebuild the tables. True is recommended for the first import.
DROP_AND_RECREATE_TABLES = True

# =========================
# Usually no need to change anything below
# =========================


MEDICAL_TABLES = [
    {"table": "projects", "file": "projects.csv", "columns": ["project_id"]},
    {"table": "demographics", "file": "demographics.csv", "columns": [
        "demographic_id", "case_id", "gender", "race", "ethnicity",
        "vital_status", "sex_at_birth", "age_at_index"]},
    {"table": "cases", "file": "cases.csv", "columns": [
        "case_id", "primary_site", "disease_type", "submitter_id",
        "state", "project_id", "demographic_id"]},
    {"table": "diagnoses", "file": "diagnoses.csv", "columns": [
        "diagnosis_id", "case_id", "primary_diagnosis", "vital_status",
        "age_at_diagnosis", "morphology", "classification_of_tumor",
        "tumor_grade", "tissue_or_organ_of_origin"]},
    {"table": "samples", "file": "samples.csv", "columns": [
        "sample_id", "case_id", "sample_type", "tissue_type",
        "specimen_type", "tumor_descriptor", "preservation_method"]},
    {"table": "portions", "file": "portions.csv", "columns": [
        "portion_id", "sample_id", "portion_number", "is_ffpe"]},
    {"table": "analytes", "file": "analytes.csv", "columns": [
        "analyte_id", "portion_id", "analyte_type", "concentration"]},
    {"table": "aliquots", "file": "aliquots.csv", "columns": [
        "aliquot_id", "analyte_id", "submitter_id", "state",
        "concentration", "aliquot_quantity", "aliquot_volume"]},
]

MATERIAL_TABLES = [
    {"table": "materials", "file": "materials.csv", "columns": [
        "material_id", "name", "smiles", "repeat_unit_smiles", "pid",
        "category", "average_mw", "tensile_modulus", "tensile_strength",
        "thermal_decomposition", "glass_temperature", "melting_temperature",
        "heat_deflection_temperature", "raw_source"]},
    {"table": "processing_cases", "file": "processing_cases.csv", "columns": [
        "process_id", "material_name", "material_id", "sample_no",
        "formulation", "speed", "pressure", "pressure_time",
        "cooling_temperature", "cooling_time", "injection_rate",
        "processing_temperature", "raw_source"]},
    {"table": "waxd_results", "file": "waxd_results.csv", "columns": [
        "waxd_id", "process_id", "sample_no", "pa_content", "waxd_peak",
        "crystallinity", "crystal_size", "orientation", "quality_value",
        "raw_value"]},
    {"table": "performance_results", "file": "performance_results.csv", "columns": [
        "performance_id", "process_id", "sample_no", "tensile_strength",
        "tensile_modulus", "elongation", "impact_strength",
        "composite_mechanical_property", "raw_source"]},
    {"table": "pa6t_simulations", "file": "pa6t_simulations.csv", "columns": [
        "simulation_id", "pa6t_content", "temperature", "density",
        "energy", "transition_temperature", "raw_source"]},
]


MEDICAL_DROP_SQL = """
DROP TABLE IF EXISTS aliquots CASCADE;
DROP TABLE IF EXISTS analytes CASCADE;
DROP TABLE IF EXISTS portions CASCADE;
DROP TABLE IF EXISTS samples CASCADE;
DROP TABLE IF EXISTS diagnoses CASCADE;
DROP TABLE IF EXISTS cases CASCADE;
DROP TABLE IF EXISTS demographics CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
"""

MEDICAL_CREATE_SQL = """
CREATE TABLE projects (
    project_id TEXT PRIMARY KEY
);

CREATE TABLE demographics (
    demographic_id TEXT PRIMARY KEY,
    case_id TEXT,
    gender TEXT,
    race TEXT,
    ethnicity TEXT,
    vital_status TEXT,
    sex_at_birth TEXT,
    age_at_index INTEGER
);

CREATE TABLE cases (
    case_id TEXT PRIMARY KEY,
    primary_site TEXT,
    disease_type TEXT,
    submitter_id TEXT,
    state TEXT,
    project_id TEXT REFERENCES projects(project_id),
    demographic_id TEXT REFERENCES demographics(demographic_id)
);

CREATE TABLE diagnoses (
    diagnosis_id TEXT PRIMARY KEY,
    case_id TEXT REFERENCES cases(case_id),
    primary_diagnosis TEXT,
    vital_status TEXT,
    age_at_diagnosis INTEGER,
    morphology TEXT,
    classification_of_tumor TEXT,
    tumor_grade TEXT,
    tissue_or_organ_of_origin TEXT
);

CREATE TABLE samples (
    sample_id TEXT PRIMARY KEY,
    case_id TEXT REFERENCES cases(case_id),
    sample_type TEXT,
    tissue_type TEXT,
    specimen_type TEXT,
    tumor_descriptor TEXT,
    preservation_method TEXT
);

CREATE TABLE portions (
    portion_id TEXT PRIMARY KEY,
    sample_id TEXT REFERENCES samples(sample_id),
    portion_number TEXT,
    is_ffpe TEXT
);

CREATE TABLE analytes (
    analyte_id TEXT PRIMARY KEY,
    portion_id TEXT REFERENCES portions(portion_id),
    analyte_type TEXT,
    concentration DOUBLE PRECISION
);

CREATE TABLE aliquots (
    aliquot_id TEXT PRIMARY KEY,
    analyte_id TEXT REFERENCES analytes(analyte_id),
    submitter_id TEXT,
    state TEXT,
    concentration DOUBLE PRECISION,
    aliquot_quantity DOUBLE PRECISION,
    aliquot_volume DOUBLE PRECISION
);
"""

MEDICAL_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_cases_project_id ON cases(project_id);
CREATE INDEX IF NOT EXISTS idx_cases_demographic_id ON cases(demographic_id);
CREATE INDEX IF NOT EXISTS idx_demographics_vital_status ON demographics(vital_status);
CREATE INDEX IF NOT EXISTS idx_diagnoses_case_id ON diagnoses(case_id);
CREATE INDEX IF NOT EXISTS idx_diagnoses_vital_status ON diagnoses(vital_status);
CREATE INDEX IF NOT EXISTS idx_samples_case_id ON samples(case_id);
CREATE INDEX IF NOT EXISTS idx_samples_type_preservation_case
    ON samples(sample_type, preservation_method, case_id);
CREATE INDEX IF NOT EXISTS idx_portions_sample_id ON portions(sample_id);
CREATE INDEX IF NOT EXISTS idx_analytes_portion_id ON analytes(portion_id);
CREATE INDEX IF NOT EXISTS idx_analytes_type_portion ON analytes(analyte_type, portion_id);
CREATE INDEX IF NOT EXISTS idx_aliquots_analyte_id ON aliquots(analyte_id);
CREATE INDEX IF NOT EXISTS idx_aliquots_concentration_analyte
    ON aliquots(concentration, analyte_id);

CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX IF NOT EXISTS idx_diagnoses_primary_diagnosis_trgm
    ON diagnoses USING gin (LOWER(primary_diagnosis) gin_trgm_ops);
"""


MATERIAL_DROP_SQL = """
DROP TABLE IF EXISTS pa6t_simulations CASCADE;
DROP TABLE IF EXISTS performance_results CASCADE;
DROP TABLE IF EXISTS waxd_results CASCADE;
DROP TABLE IF EXISTS processing_cases CASCADE;
DROP TABLE IF EXISTS materials CASCADE;
"""

MATERIAL_CREATE_SQL = """
CREATE TABLE materials (
    material_id TEXT PRIMARY KEY,
    name TEXT,
    smiles TEXT,
    repeat_unit_smiles TEXT,
    pid TEXT,
    category TEXT,
    average_mw DOUBLE PRECISION,
    tensile_modulus DOUBLE PRECISION,
    tensile_strength DOUBLE PRECISION,
    thermal_decomposition DOUBLE PRECISION,
    glass_temperature DOUBLE PRECISION,
    melting_temperature DOUBLE PRECISION,
    heat_deflection_temperature DOUBLE PRECISION,
    raw_source TEXT
);

CREATE TABLE processing_cases (
    process_id TEXT PRIMARY KEY,
    material_name TEXT,
    material_id TEXT,
    sample_no TEXT,
    formulation TEXT,
    speed DOUBLE PRECISION,
    pressure DOUBLE PRECISION,
    pressure_time DOUBLE PRECISION,
    cooling_temperature DOUBLE PRECISION,
    cooling_time DOUBLE PRECISION,
    injection_rate DOUBLE PRECISION,
    processing_temperature DOUBLE PRECISION,
    raw_source TEXT
);

CREATE TABLE waxd_results (
    waxd_id TEXT PRIMARY KEY,
    process_id TEXT REFERENCES processing_cases(process_id),
    sample_no TEXT,
    pa_content DOUBLE PRECISION,
    waxd_peak TEXT,
    crystallinity DOUBLE PRECISION,
    crystal_size DOUBLE PRECISION,
    orientation DOUBLE PRECISION,
    quality_value DOUBLE PRECISION,
    raw_value TEXT
);

CREATE TABLE performance_results (
    performance_id TEXT PRIMARY KEY,
    process_id TEXT REFERENCES processing_cases(process_id),
    sample_no TEXT,
    tensile_strength DOUBLE PRECISION,
    tensile_modulus DOUBLE PRECISION,
    elongation DOUBLE PRECISION,
    impact_strength DOUBLE PRECISION,
    composite_mechanical_property DOUBLE PRECISION,
    raw_source TEXT
);

CREATE TABLE pa6t_simulations (
    simulation_id TEXT PRIMARY KEY,
    pa6t_content DOUBLE PRECISION,
    temperature DOUBLE PRECISION,
    density DOUBLE PRECISION,
    energy DOUBLE PRECISION,
    transition_temperature DOUBLE PRECISION,
    raw_source TEXT
);
"""

MATERIAL_INDEX_SQL = """
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX IF NOT EXISTS idx_materials_name ON materials(name);
CREATE INDEX IF NOT EXISTS idx_materials_name_trgm
    ON materials USING gin (LOWER(name) gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_materials_smiles_trgm
    ON materials USING gin (LOWER(smiles) gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_materials_repeat_unit_smiles_trgm
    ON materials USING gin (LOWER(repeat_unit_smiles) gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_materials_category ON materials(category);
CREATE INDEX IF NOT EXISTS idx_materials_tensile_strength ON materials(tensile_strength);
CREATE INDEX IF NOT EXISTS idx_materials_tm ON materials(melting_temperature);
CREATE INDEX IF NOT EXISTS idx_materials_hdt ON materials(heat_deflection_temperature);
CREATE INDEX IF NOT EXISTS idx_materials_glass_temperature ON materials(glass_temperature);

CREATE INDEX IF NOT EXISTS idx_processing_material_id ON processing_cases(material_id);
CREATE INDEX IF NOT EXISTS idx_processing_material_name ON processing_cases(material_name);
CREATE INDEX IF NOT EXISTS idx_processing_material_name_trgm
    ON processing_cases USING gin (LOWER(material_name) gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_processing_sample_no ON processing_cases(sample_no);
CREATE INDEX IF NOT EXISTS idx_processing_speed ON processing_cases(speed);
CREATE INDEX IF NOT EXISTS idx_processing_injection_rate ON processing_cases(injection_rate);
CREATE INDEX IF NOT EXISTS idx_processing_temperature ON processing_cases(processing_temperature);

CREATE INDEX IF NOT EXISTS idx_waxd_process_id ON waxd_results(process_id);
CREATE INDEX IF NOT EXISTS idx_waxd_sample_no ON waxd_results(sample_no);
CREATE INDEX IF NOT EXISTS idx_waxd_quality_value ON waxd_results(quality_value);
CREATE INDEX IF NOT EXISTS idx_waxd_crystallinity ON waxd_results(crystallinity);

CREATE INDEX IF NOT EXISTS idx_performance_process_id ON performance_results(process_id);
CREATE INDEX IF NOT EXISTS idx_performance_sample_no ON performance_results(sample_no);
CREATE INDEX IF NOT EXISTS idx_performance_tensile_strength ON performance_results(tensile_strength);

CREATE INDEX IF NOT EXISTS idx_pa6t_content_temperature
    ON pa6t_simulations(pa6t_content, temperature);
CREATE INDEX IF NOT EXISTS idx_pa6t_density ON pa6t_simulations(density);
CREATE INDEX IF NOT EXISTS idx_pa6t_energy ON pa6t_simulations(energy);
"""


# dataset registry: name -> (tables, drop_sql, create_sql, index_sql)
DATASET_CONFIG = {
    "medical": (MEDICAL_TABLES, MEDICAL_DROP_SQL, MEDICAL_CREATE_SQL, MEDICAL_INDEX_SQL),
    "material": (MATERIAL_TABLES, MATERIAL_DROP_SQL, MATERIAL_CREATE_SQL, MATERIAL_INDEX_SQL),
}


class ProgressFile:
    def __init__(self, path, label):
        self.path = Path(path)
        self.label = label
        self.total_size = os.path.getsize(self.path)
        self.read_size = 0
        self.last_percent = -1
        self.file = open(self.path, "r", encoding="utf-8", newline="")

    def read(self, size=-1):
        chunk = self.file.read(size)
        if chunk:
            self.read_size += len(chunk.encode("utf-8"))
            self.show_progress()
        return chunk

    def show_progress(self):
        if self.total_size <= 0:
            return
        percent = int(self.read_size * 100 / self.total_size)
        if percent != self.last_percent:
            self.last_percent = percent
            bar_width = 40
            filled = int(bar_width * percent / 100)
            bar = "█" * filled + "-" * (bar_width - filled)
            sys.stdout.write(f"\rImporting {self.label}: |{bar}| {percent:3d}%")
            sys.stdout.flush()

    def close(self):
        self.file.close()
        sys.stdout.write("\n")
        sys.stdout.flush()


def connect_db():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD)


def check_csv_files(tables):
    if not CSV_DIR.exists():
        raise FileNotFoundError(f"CSV directory does not exist: {CSV_DIR.resolve()}")
    missing = [str(CSV_DIR / t["file"]) for t in tables
               if not (CSV_DIR / t["file"]).exists()]
    if missing:
        raise FileNotFoundError("The following CSV files do not exist:\n" + "\n".join(missing))


def clean_database(conn, drop_sql):
    print("Step 0/4: Dropping old data, old tables, and temporary tables")
    with conn.cursor() as cur:
        cur.execute(drop_sql)
    conn.commit()
    print("Old data cleanup complete")


def create_tables(conn, create_sql):
    print("Step 1/4: Creating tables")
    with conn.cursor() as cur:
        cur.execute(create_sql)
    conn.commit()
    print("Table creation complete")


def import_csv_files(conn, tables):
    print("Step 2/4: Importing CSVs")
    with conn.cursor() as cur:
        for item in tables:
            table = item["table"]
            csv_file = CSV_DIR / item["file"]
            columns = ", ".join(item["columns"])
            temp_table = f"tmp_{table}"

            print(f"\nPreparing to import {item['file']} -> {table}")
            cur.execute(f"DROP TABLE IF EXISTS {temp_table};")
            cur.execute(f"CREATE TEMP TABLE {temp_table} (LIKE {table});")
            conn.commit()

            copy_sql = f"""
                COPY {temp_table} ({columns})
                FROM STDIN
                WITH (FORMAT CSV, HEADER TRUE, NULL '')
            """
            pf = ProgressFile(csv_file, item["file"])
            try:
                cur.copy_expert(copy_sql, pf)
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                pf.close()

            insert_sql = f"""
                INSERT INTO {table} ({columns})
                SELECT {columns} FROM {temp_table}
                ON CONFLICT DO NOTHING;
            """
            cur.execute(insert_sql)
            inserted_count = cur.rowcount
            conn.commit()

            cur.execute(f"SELECT COUNT(*) FROM {table};")
            total_count = cur.fetchone()[0]
            cur.execute(f"SELECT COUNT(*) FROM {temp_table};")
            temp_count = cur.fetchone()[0]
            skipped_count = temp_count - inserted_count

            print(f"{table} import complete")
            print(f"  CSV rows:           {temp_count}")
            print(f"  Rows inserted:      {inserted_count}")
            print(f"  Duplicate rows skipped: {skipped_count}")
            print(f"  Current table total:    {total_count}")

            cur.execute(f"DROP TABLE IF EXISTS {temp_table};")
            conn.commit()
    print("CSV import complete")


def create_indexes(conn, index_sql):
    print("Step 3/4: Creating indexes")
    with conn.cursor() as cur:
        cur.execute(index_sql)
    conn.commit()
    print("Index creation complete")


def show_table_counts(conn, tables):
    print("\nStep 4/4: Table row count summary")
    with conn.cursor() as cur:
        for item in tables:
            table = item["table"]
            cur.execute(f"SELECT COUNT(*) FROM {table};")
            count = cur.fetchone()[0]
            print(f"{table:25s} {count}")


def load_dataset(conn, name):
    tables, drop_sql, create_sql, index_sql = DATASET_CONFIG[name]
    print(f"\n========== Loading dataset: {name} ==========")
    check_csv_files(tables)
    if CLEAN_DATABASE_FIRST:
        clean_database(conn, drop_sql)
    else:
        print("Skipping old data cleanup: CLEAN_DATABASE_FIRST = False")
    if DROP_AND_RECREATE_TABLES:
        create_tables(conn, create_sql)
    else:
        print("Skipping table creation step: DROP_AND_RECREATE_TABLES = False")
    import_csv_files(conn, tables)
    create_indexes(conn, index_sql)
    show_table_counts(conn, tables)


def main():
    print(f"CSV directory: {CSV_DIR.resolve()}")
    print(f"Datasets to load: {', '.join(sorted(DATASETS))}")

    conn = connect_db()
    try:
        for name in ["medical", "material"]:
            if name in DATASETS:
                load_dataset(conn, name)
        print("\nAll done. You can now run the query benchmark (3_benchmark.java).")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
