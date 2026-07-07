#!/usr/bin/env python3
"""
Step 2 — Create the schema and import the converted CSV tables into PostgreSQL.

Loads BOTH domains produced by 1_convert.py:

  * BIOMEDICAL: create the `clinical` schema with the 16 `table_*` tables
    (3NF), bulk-load the CSVs from ./csv_exports/ via COPY (temp-table +
    DISTINCT-ON dedup), then add indexes and foreign keys.

  * ORGANIC-POLYMER: create the 5 denormalised tables in the `public` schema
    and bulk-load the CSVs from ./csv_exports_polymer/.

`cleanup_db()` (folded in from the old cleanup_db.py) drops and recreates the
`clinical` schema; it is called at the start of the biomedical load.

DB credentials come from environment variables (no hardcoded password).
Run order: 1_convert.py -> 2_load.py -> 3_benchmark.py
"""

import os
import gzip
import psycopg2
from psycopg2 import sql
import logging
import subprocess
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection settings (the password is read from an environment variable, not hardcoded)
DB_CONFIG = {
    'dbname': os.environ.get('PG_DATABASE', 'clinical_db'),
    'user': os.environ.get('PG_USER', 'sal'),
    'password': os.environ.get('PG_PASSWORD', ''),
    'host': os.environ.get('PG_HOST', 'localhost'),
    'port': int(os.environ.get('PG_PORT', 5432)),
}
DB_USER = DB_CONFIG['user']

# CSV directories
CSV_DIR = './csv_exports'              # biomedical
POLYMER_CSV_DIR = './csv_exports_polymer'  # organic polymer
SCHEMA_NAME = 'clinical'               # biomedical schema
POLYMER_SCHEMA = 'public'              # organic polymer schema


def get_db_connection():
    """Open a database connection."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to the database: {e}")
        raise


def cleanup_db():
    """Drop and recreate the clinical schema (folded in from the original cleanup_db.py)."""
    logger.info("Cleaning up and recreating the clinical schema...")
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()
    try:
        # Terminate other connections (optional)
        cur.execute("""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = %s AND pid <> pg_backend_pid()
        """, (DB_CONFIG['dbname'],))
        cur.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(SCHEMA_NAME)))
        logger.info(f"Schema {SCHEMA_NAME} dropped")
        cur.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(SCHEMA_NAME)))
        logger.info(f"Schema {SCHEMA_NAME} created")
        cur.execute(sql.SQL("GRANT ALL ON SCHEMA {} TO {}").format(
            sql.Identifier(SCHEMA_NAME), sql.Identifier(DB_USER)))
        logger.info("Privileges granted")
    except Exception as e:
        logger.warning(f"Failed to clean up the schema: {e}")
    finally:
        cur.close()
        conn.close()


def create_schema(conn):
    """Create the clinical schema."""
    logger.info(f"Creating schema: {SCHEMA_NAME}")

    cur = conn.cursor()
    try:
        cur.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(SCHEMA_NAME)))
        cur.execute(sql.SQL("GRANT ALL ON SCHEMA {} TO {}").format(
            sql.Identifier(SCHEMA_NAME), sql.Identifier(DB_USER)))
        conn.commit()
        logger.info(f"Schema {SCHEMA_NAME} is ready")
    except Exception as e:
        logger.error(f"Failed to create the schema: {e}")
        raise
    finally:
        cur.close()


def create_tables(conn):
    """Create all tables in the clinical schema (tables only; foreign keys are added later)."""
    logger.info(f"Creating database tables in schema {SCHEMA_NAME}...")

    # First drop all tables (in dependency order)
    tables_in_order = [
        'table_aliquot', 'table_analyte', 'table_slide', 'table_portion',
        'table_sample', 'table_family_history', 'table_exposure',
        'table_other_clinical_attribute', 'table_molecular_test',
        'table_follow_up', 'table_pathology_detail', 'table_treatment',
        'table_diagnosis', 'table_demographic', 'table_case', 'table_project'
    ]

    cur = conn.cursor()

    for table in tables_in_order:
        try:
            cur.execute(sql.SQL("DROP TABLE IF EXISTS {}.{} CASCADE").format(
                sql.Identifier(SCHEMA_NAME), sql.Identifier(table)))
            logger.debug(f"Dropped table {table}")
        except Exception as e:
            logger.warning(f"Failed to drop table {table}: {e}")

    create_table_sqls = [
        # 1. Project table
        f"""
        CREATE TABLE {SCHEMA_NAME}.table_project (
            project_id VARCHAR(100) PRIMARY KEY,
            project_name VARCHAR(200)
        )
        """,

        # 2. Case table
        f"""
        CREATE TABLE {SCHEMA_NAME}.table_case (
            case_id VARCHAR(100) PRIMARY KEY,
            primary_site VARCHAR(500),
            disease_type VARCHAR(500),
            project_id VARCHAR(100),
            submitter_id VARCHAR(200),
            created_datetime TIMESTAMP,
            updated_datetime TIMESTAMP,
            state VARCHAR(50),
            days_to_consent INTEGER,
            consent_type VARCHAR(200),
            lost_to_followup VARCHAR(20),
            index_date VARCHAR(100)
        )
        """,

        # 3. Demographic table
        f"""
        CREATE TABLE {SCHEMA_NAME}.table_demographic (
            demographic_id VARCHAR(100) PRIMARY KEY,
            case_id VARCHAR(100) UNIQUE,
            ethnicity VARCHAR(200),
            gender VARCHAR(50),
            race VARCHAR(200),
            vital_status VARCHAR(50),
            sex_at_birth VARCHAR(50),
            days_to_birth INTEGER,
            age_at_index INTEGER,
            country_of_residence VARCHAR(200),
            cause_of_death VARCHAR(200),
            days_to_death INTEGER,
            created_datetime TIMESTAMP,
            updated_datetime TIMESTAMP,
            state VARCHAR(50)
        )
        """,

        # 4. Diagnosis table
        f"""
        CREATE TABLE {SCHEMA_NAME}.table_diagnosis (
            diagnosis_id VARCHAR(100) PRIMARY KEY,
            case_id VARCHAR(100),
            primary_diagnosis VARCHAR(500),
            morphology VARCHAR(100),
            tissue_or_organ_of_origin VARCHAR(500),
            site_of_resection_or_biopsy VARCHAR(500),
            age_at_diagnosis INTEGER,
            days_to_diagnosis INTEGER,
            classification_of_tumor VARCHAR(200),
            tumor_grade VARCHAR(100),
            tumor_stage VARCHAR(100),
            ajcc_pathologic_stage VARCHAR(100),
            ajcc_pathologic_t VARCHAR(100),
            ajcc_pathologic_n VARCHAR(100),
            ajcc_pathologic_m VARCHAR(100),
            progression_or_recurrence VARCHAR(100),
            last_known_disease_status VARCHAR(200),
            year_of_diagnosis INTEGER,
            created_datetime TIMESTAMP,
            updated_datetime TIMESTAMP,
            state VARCHAR(50),
            diagnosis_is_primary_disease VARCHAR(20),
            prior_malignancy VARCHAR(20),
            prior_treatment VARCHAR(20),
            residual_disease VARCHAR(20),
            icd_10_code VARCHAR(20)
        )
        """,

        # 5. Treatment table
        f"""
        CREATE TABLE {SCHEMA_NAME}.table_treatment (
            treatment_id VARCHAR(100) PRIMARY KEY,
            diagnosis_id VARCHAR(100),
            treatment_type VARCHAR(500),
            treatment_intent_type VARCHAR(200),
            treatment_or_therapy VARCHAR(20),
            days_to_treatment_start INTEGER,
            initial_disease_status VARCHAR(200),
            number_of_cycles INTEGER,
            residual_disease VARCHAR(20),
            protocol_identifier VARCHAR(200),
            created_datetime TIMESTAMP,
            updated_datetime TIMESTAMP,
            state VARCHAR(50)
        )
        """,

        # 6. Pathology detail table
        f"""
        CREATE TABLE {SCHEMA_NAME}.table_pathology_detail (
            pathology_detail_id VARCHAR(100) PRIMARY KEY,
            diagnosis_id VARCHAR(100),
            consistent_pathology_review VARCHAR(20),
            vascular_invasion_present VARCHAR(20),
            vascular_invasion_type VARCHAR(200),
            lymph_nodes_tested INTEGER,
            lymph_nodes_positive INTEGER,
            perineural_invasion_present VARCHAR(20),
            additional_pathology_findings TEXT,
            created_datetime TIMESTAMP,
            updated_datetime TIMESTAMP,
            state VARCHAR(50)
        )
        """,

        # 7. Follow-up table
        f"""
        CREATE TABLE {SCHEMA_NAME}.table_follow_up (
            follow_up_id VARCHAR(100) PRIMARY KEY,
            case_id VARCHAR(100),
            days_to_follow_up INTEGER,
            timepoint_category VARCHAR(200),
            disease_response VARCHAR(200),
            progression_or_recurrence VARCHAR(20),
            progression_or_recurrence_type VARCHAR(200),
            progression_or_recurrence_anatomic_site VARCHAR(500),
            days_to_recurrence INTEGER,
            ecog_performance_status VARCHAR(50),
            karnofsky_performance_status VARCHAR(50),
            imaging_type VARCHAR(200),
            imaging_result VARCHAR(500),
            created_datetime TIMESTAMP,
            updated_datetime TIMESTAMP,
            state VARCHAR(50)
        )
        """,

        # 8. Molecular test table
        f"""
        CREATE TABLE {SCHEMA_NAME}.table_molecular_test (
            molecular_test_id VARCHAR(100) PRIMARY KEY,
            follow_up_id VARCHAR(100),
            laboratory_test VARCHAR(500),
            test_value NUMERIC,
            test_units VARCHAR(100),
            test_result VARCHAR(500),
            timepoint_category VARCHAR(200),
            gene_symbol VARCHAR(200),
            molecular_analysis_method VARCHAR(500),
            antigen VARCHAR(500),
            days_to_test INTEGER,
            created_datetime TIMESTAMP,
            updated_datetime TIMESTAMP,
            state VARCHAR(50)
        )
        """,

        # 9. Other clinical attributes table
        f"""
        CREATE TABLE {SCHEMA_NAME}.table_other_clinical_attribute (
            other_clinical_attribute_id VARCHAR(100) PRIMARY KEY,
            follow_up_id VARCHAR(100),
            weight NUMERIC,
            height NUMERIC,
            bmi NUMERIC,
            timepoint_category VARCHAR(200),
            created_datetime TIMESTAMP,
            updated_datetime TIMESTAMP,
            state VARCHAR(50)
        )
        """,

        # 10. Exposure history table
        f"""
        CREATE TABLE {SCHEMA_NAME}.table_exposure (
            exposure_id VARCHAR(100) PRIMARY KEY,
            case_id VARCHAR(100),
            exposure_type VARCHAR(200),
            tobacco_smoking_status VARCHAR(500),
            pack_years_smoked NUMERIC,
            cigarettes_per_day INTEGER,
            alcohol_history VARCHAR(200),
            alcohol_intensity VARCHAR(200),
            created_datetime TIMESTAMP,
            updated_datetime TIMESTAMP,
            state VARCHAR(50)
        )
        """,

        # 11. Family history table
        f"""
        CREATE TABLE {SCHEMA_NAME}.table_family_history (
            family_history_id VARCHAR(100) PRIMARY KEY,
            case_id VARCHAR(100),
            relative_with_cancer_history VARCHAR(20),
            relatives_with_cancer_history_count INTEGER,
            relationship_primary_diagnosis VARCHAR(500),
            created_datetime TIMESTAMP,
            updated_datetime TIMESTAMP,
            state VARCHAR(50)
        )
        """,

        # 12. Sample table
        f"""
        CREATE TABLE {SCHEMA_NAME}.table_sample (
            sample_id VARCHAR(100) PRIMARY KEY,
            case_id VARCHAR(100),
            sample_type VARCHAR(200),
            tissue_type VARCHAR(100),
            specimen_type VARCHAR(200),
            tumor_descriptor VARCHAR(200),
            preservation_method VARCHAR(200),
            days_to_collection INTEGER,
            days_to_sample_procurement INTEGER,
            initial_weight NUMERIC,
            current_weight NUMERIC,
            created_datetime TIMESTAMP,
            updated_datetime TIMESTAMP,
            state VARCHAR(50)
        )
        """,

        # 13. Portion table
        f"""
        CREATE TABLE {SCHEMA_NAME}.table_portion (
            portion_id VARCHAR(100) PRIMARY KEY,
            sample_id VARCHAR(100),
            portion_number VARCHAR(100),
            weight NUMERIC,
            is_ffpe VARCHAR(20),
            creation_datetime NUMERIC,
            created_datetime TIMESTAMP,
            updated_datetime TIMESTAMP,
            state VARCHAR(50)
        )
        """,

        # 14. Slide table
        f"""
        CREATE TABLE {SCHEMA_NAME}.table_slide (
            slide_id VARCHAR(100) PRIMARY KEY,
            portion_id VARCHAR(100),
            section_location VARCHAR(500),
            percent_tumor_nuclei NUMERIC,
            percent_tumor_cells NUMERIC,
            percent_stromal_cells NUMERIC,
            percent_necrosis NUMERIC,
            percent_normal_cells NUMERIC,
            percent_lymphocyte_infiltration NUMERIC,
            created_datetime TIMESTAMP,
            updated_datetime TIMESTAMP,
            state VARCHAR(50)
        )
        """,

        # 15. Analyte table
        f"""
        CREATE TABLE {SCHEMA_NAME}.table_analyte (
            analyte_id VARCHAR(100) PRIMARY KEY,
            portion_id VARCHAR(100),
            analyte_type VARCHAR(100),
            concentration NUMERIC,
            spectrophotometer_method VARCHAR(200),
            rna_integrity_number NUMERIC,
            a260_a280_ratio NUMERIC,
            experimental_protocol_type VARCHAR(500),
            created_datetime TIMESTAMP,
            updated_datetime TIMESTAMP,
            state VARCHAR(50)
        )
        """,

        # 16. Aliquot table
        f"""
        CREATE TABLE {SCHEMA_NAME}.table_aliquot (
            aliquot_id VARCHAR(100) PRIMARY KEY,
            analyte_id VARCHAR(100),
            aliquot_quantity NUMERIC,
            aliquot_volume NUMERIC,
            concentration NUMERIC,
            source_center VARCHAR(100),
            analyte_type VARCHAR(100),
            created_datetime TIMESTAMP,
            updated_datetime TIMESTAMP,
            state VARCHAR(50)
        )
        """
    ]

    for sql_stmt in create_table_sqls:
        try:
            cur.execute(sql_stmt)
            logger.debug(f"SQL executed successfully")
        except Exception as e:
            logger.error(f"SQL execution failed: {e}")
            raise

    conn.commit()
    cur.close()
    logger.info(f"Database tables created (in the {SCHEMA_NAME} schema)")


def add_foreign_keys(conn):
    """Add foreign key constraints after all data has been imported."""
    logger.info("Adding foreign key constraints...")

    fk_sqls = [
        f"ALTER TABLE {SCHEMA_NAME}.table_case ADD CONSTRAINT fk_case_project FOREIGN KEY (project_id) REFERENCES {SCHEMA_NAME}.table_project(project_id)",
        f"ALTER TABLE {SCHEMA_NAME}.table_demographic ADD CONSTRAINT fk_demographic_case FOREIGN KEY (case_id) REFERENCES {SCHEMA_NAME}.table_case(case_id)",
        f"ALTER TABLE {SCHEMA_NAME}.table_diagnosis ADD CONSTRAINT fk_diagnosis_case FOREIGN KEY (case_id) REFERENCES {SCHEMA_NAME}.table_case(case_id)",
        f"ALTER TABLE {SCHEMA_NAME}.table_treatment ADD CONSTRAINT fk_treatment_diagnosis FOREIGN KEY (diagnosis_id) REFERENCES {SCHEMA_NAME}.table_diagnosis(diagnosis_id)",
        f"ALTER TABLE {SCHEMA_NAME}.table_pathology_detail ADD CONSTRAINT fk_pathology_diagnosis FOREIGN KEY (diagnosis_id) REFERENCES {SCHEMA_NAME}.table_diagnosis(diagnosis_id)",
        f"ALTER TABLE {SCHEMA_NAME}.table_follow_up ADD CONSTRAINT fk_followup_case FOREIGN KEY (case_id) REFERENCES {SCHEMA_NAME}.table_case(case_id)",
        f"ALTER TABLE {SCHEMA_NAME}.table_molecular_test ADD CONSTRAINT fk_molecular_followup FOREIGN KEY (follow_up_id) REFERENCES {SCHEMA_NAME}.table_follow_up(follow_up_id)",
        f"ALTER TABLE {SCHEMA_NAME}.table_other_clinical_attribute ADD CONSTRAINT fk_other_followup FOREIGN KEY (follow_up_id) REFERENCES {SCHEMA_NAME}.table_follow_up(follow_up_id)",
        f"ALTER TABLE {SCHEMA_NAME}.table_exposure ADD CONSTRAINT fk_exposure_case FOREIGN KEY (case_id) REFERENCES {SCHEMA_NAME}.table_case(case_id)",
        f"ALTER TABLE {SCHEMA_NAME}.table_family_history ADD CONSTRAINT fk_family_case FOREIGN KEY (case_id) REFERENCES {SCHEMA_NAME}.table_case(case_id)",
        f"ALTER TABLE {SCHEMA_NAME}.table_sample ADD CONSTRAINT fk_sample_case FOREIGN KEY (case_id) REFERENCES {SCHEMA_NAME}.table_case(case_id)",
        f"ALTER TABLE {SCHEMA_NAME}.table_portion ADD CONSTRAINT fk_portion_sample FOREIGN KEY (sample_id) REFERENCES {SCHEMA_NAME}.table_sample(sample_id)",
        f"ALTER TABLE {SCHEMA_NAME}.table_slide ADD CONSTRAINT fk_slide_portion FOREIGN KEY (portion_id) REFERENCES {SCHEMA_NAME}.table_portion(portion_id)",
        f"ALTER TABLE {SCHEMA_NAME}.table_analyte ADD CONSTRAINT fk_analyte_portion FOREIGN KEY (portion_id) REFERENCES {SCHEMA_NAME}.table_portion(portion_id)",
        f"ALTER TABLE {SCHEMA_NAME}.table_aliquot ADD CONSTRAINT fk_aliquot_analyte FOREIGN KEY (analyte_id) REFERENCES {SCHEMA_NAME}.table_analyte(analyte_id)"
    ]

    cur = conn.cursor()
    for fk_sql in fk_sqls:
        try:
            cur.execute(fk_sql)
            conn.commit()
            logger.info(f"  Foreign key constraint added successfully")
        except Exception as e:
            logger.warning(f"  Failed to add foreign key constraint: {e}")
    cur.close()


def find_csv_file(base_path):
    """Locate a CSV file, also accepting a .gz extension."""
    if os.path.exists(base_path):
        return base_path
    gz_path = base_path + '.gz'
    if os.path.exists(gz_path):
        return gz_path
    return None


def get_file_size_mb(filepath):
    """Return the file size in MB."""
    if os.path.exists(filepath):
        return os.path.getsize(filepath) / 1024 / 1024
    return 0


def import_csv_to_table_optimized(conn, table_name, csv_file, columns, key_column=None,
                                  csv_dir=CSV_DIR, schema=SCHEMA_NAME):
    """
    Optimized import routine - uses a temporary table and streaming
    to avoid loading the entire CSV into memory.
    """
    csv_path = os.path.join(csv_dir, csv_file)
    csv_path = find_csv_file(csv_path)

    if not csv_path:
        logger.warning(f"File not found: {os.path.join(csv_dir, csv_file)} or its .gz version; skipping import of {table_name}")
        return 0

    file_size_mb = get_file_size_mb(csv_path)
    logger.info(f"  File: {os.path.basename(csv_path)} ({file_size_mb:.2f} MB)")

    cur = conn.cursor()
    temp_table = None

    try:
        temp_table = f"temp_{table_name}_{int(datetime.now().timestamp())}"
        cur.execute(f"""
            CREATE TEMP TABLE {temp_table} (LIKE {schema}.{table_name} INCLUDING DEFAULTS)
        """)
        logger.info(f"  Created temporary table: {temp_table}")

        logger.info(f"  Streaming data into the temporary table...")

        if csv_path.endswith('.gz'):
            gunzip = subprocess.Popen(['gunzip', '-c', csv_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            cur.copy_expert(
                f"COPY {temp_table} ({','.join(columns)}) FROM STDIN WITH CSV HEADER",
                gunzip.stdout
            )
            gunzip.wait()
        else:
            with open(csv_path, 'r', encoding='utf-8') as f:
                cur.copy_expert(
                    f"COPY {temp_table} ({','.join(columns)}) FROM STDIN WITH CSV HEADER",
                    f
                )

        conn.commit()

        cur.execute(f"SELECT COUNT(*) FROM {temp_table}")
        temp_count = cur.fetchone()[0]
        logger.info(f"  The temporary table contains {temp_count:,} records")

        if temp_count == 0:
            logger.info(f"  No data to import")
            return 0

        if key_column and key_column in columns:
            logger.info(f"  Deduplicating on {key_column}...")

            dedup_table = f"{temp_table}_dedup"
            cur.execute(f"""
                CREATE TEMP TABLE {dedup_table} AS
                SELECT DISTINCT ON ({key_column}) *
                FROM {temp_table}
                ORDER BY {key_column}
            """)

            cur.execute(f"SELECT COUNT(*) FROM {dedup_table}")
            dedup_count = cur.fetchone()[0]

            logger.info(f"  Dedup: {temp_count:,} -> {dedup_count:,} records ({temp_count - dedup_count:,} duplicates removed)")

            source_table = dedup_table
        else:
            source_table = temp_table

        logger.info(f"  Emptying the target table...")
        try:
            cur.execute(f"TRUNCATE TABLE {schema}.{table_name} CASCADE")
        except Exception as e:
            logger.warning(f"  TRUNCATE failed, falling back to DELETE: {e}")
            cur.execute(f"DELETE FROM {schema}.{table_name}")

        logger.info(f"  Inserting data into the target table...")
        columns_str = ', '.join(columns)
        cur.execute(f"""
            INSERT INTO {schema}.{table_name} ({columns_str})
            SELECT {columns_str}
            FROM {source_table}
        """)

        conn.commit()

        cur.execute(f"SELECT COUNT(*) FROM {schema}.{table_name}")
        final_count = cur.fetchone()[0]

        logger.info(f"  Successfully imported {final_count:,} records")
        return final_count

    except Exception as e:
        logger.error(f"  Import failed: {e}")
        conn.rollback()
        raise
    finally:
        if temp_table:
            try:
                cur.execute(f"DROP TABLE IF EXISTS {temp_table}")
                if key_column:
                    cur.execute(f"DROP TABLE IF EXISTS {temp_table}_dedup")
                conn.commit()
            except:
                pass
        cur.close()


def import_all_data(conn):
    """Import all biomedical data (using the optimized routine)."""
    logger.info("Starting the biomedical data import...")

    tables_config = {
        'table_project': {
            'file': 'projects.csv',
            'columns': ['project_id', 'project_name'],
            'key_column': 'project_id'
        },
        'table_case': {
            'file': 'cases.csv',
            'columns': ['case_id', 'primary_site', 'disease_type', 'project_id',
                       'submitter_id', 'created_datetime', 'updated_datetime',
                       'state', 'days_to_consent', 'consent_type',
                       'lost_to_followup', 'index_date'],
            'key_column': 'case_id'
        },
        'table_demographic': {
            'file': 'demographics.csv',
            'columns': ['demographic_id', 'case_id', 'ethnicity', 'gender', 'race',
                       'vital_status', 'sex_at_birth', 'days_to_birth', 'age_at_index',
                       'country_of_residence', 'cause_of_death', 'days_to_death',
                       'created_datetime', 'updated_datetime', 'state'],
            'key_column': 'demographic_id'
        },
        'table_diagnosis': {
            'file': 'diagnoses.csv',
            'columns': ['diagnosis_id', 'case_id', 'primary_diagnosis', 'morphology',
                       'tissue_or_organ_of_origin', 'site_of_resection_or_biopsy',
                       'age_at_diagnosis', 'days_to_diagnosis', 'classification_of_tumor',
                       'tumor_grade', 'tumor_stage', 'ajcc_pathologic_stage',
                       'ajcc_pathologic_t', 'ajcc_pathologic_n', 'ajcc_pathologic_m',
                       'progression_or_recurrence', 'last_known_disease_status',
                       'year_of_diagnosis', 'created_datetime', 'updated_datetime',
                       'state', 'diagnosis_is_primary_disease', 'prior_malignancy',
                       'prior_treatment', 'residual_disease', 'icd_10_code'],
            'key_column': 'diagnosis_id'
        },
        'table_treatment': {
            'file': 'treatments.csv',
            'columns': ['treatment_id', 'diagnosis_id', 'treatment_type',
                       'treatment_intent_type', 'treatment_or_therapy',
                       'days_to_treatment_start', 'initial_disease_status',
                       'number_of_cycles', 'residual_disease', 'protocol_identifier',
                       'created_datetime', 'updated_datetime', 'state'],
            'key_column': 'treatment_id'
        },
        'table_pathology_detail': {
            'file': 'pathology_details.csv',
            'columns': ['pathology_detail_id', 'diagnosis_id', 'consistent_pathology_review',
                       'vascular_invasion_present', 'vascular_invasion_type',
                       'lymph_nodes_tested', 'lymph_nodes_positive',
                       'perineural_invasion_present', 'additional_pathology_findings',
                       'created_datetime', 'updated_datetime', 'state'],
            'key_column': 'pathology_detail_id'
        },
        'table_follow_up': {
            'file': 'follow_ups.csv',
            'columns': ['follow_up_id', 'case_id', 'days_to_follow_up', 'timepoint_category',
                       'disease_response', 'progression_or_recurrence',
                       'progression_or_recurrence_type', 'progression_or_recurrence_anatomic_site',
                       'days_to_recurrence', 'ecog_performance_status', 'karnofsky_performance_status',
                       'imaging_type', 'imaging_result', 'created_datetime', 'updated_datetime', 'state'],
            'key_column': 'follow_up_id'
        },
        'table_molecular_test': {
            'file': 'molecular_tests.csv',
            'columns': ['molecular_test_id', 'follow_up_id', 'laboratory_test', 'test_value',
                       'test_units', 'test_result', 'timepoint_category', 'gene_symbol',
                       'molecular_analysis_method', 'antigen', 'days_to_test',
                       'created_datetime', 'updated_datetime', 'state'],
            'key_column': 'molecular_test_id'
        },
        'table_other_clinical_attribute': {
            'file': 'other_clinical_attributes.csv',
            'columns': ['other_clinical_attribute_id', 'follow_up_id', 'weight', 'height',
                       'bmi', 'timepoint_category', 'created_datetime', 'updated_datetime', 'state'],
            'key_column': 'other_clinical_attribute_id'
        },
        'table_exposure': {
            'file': 'exposures.csv',
            'columns': ['exposure_id', 'case_id', 'exposure_type', 'tobacco_smoking_status',
                       'pack_years_smoked', 'cigarettes_per_day', 'alcohol_history',
                       'alcohol_intensity', 'created_datetime', 'updated_datetime', 'state'],
            'key_column': 'exposure_id'
        },
        'table_family_history': {
            'file': 'family_histories.csv',
            'columns': ['family_history_id', 'case_id', 'relative_with_cancer_history',
                       'relatives_with_cancer_history_count', 'relationship_primary_diagnosis',
                       'created_datetime', 'updated_datetime', 'state'],
            'key_column': 'family_history_id'
        },
        'table_sample': {
            'file': 'samples.csv',
            'columns': ['sample_id', 'case_id', 'sample_type', 'tissue_type', 'specimen_type',
                       'tumor_descriptor', 'preservation_method', 'days_to_collection',
                       'days_to_sample_procurement', 'initial_weight', 'current_weight',
                       'created_datetime', 'updated_datetime', 'state'],
            'key_column': 'sample_id'
        },
        'table_portion': {
            'file': 'portions.csv',
            'columns': ['portion_id', 'sample_id', 'portion_number', 'weight', 'is_ffpe',
                       'creation_datetime', 'created_datetime', 'updated_datetime', 'state'],
            'key_column': 'portion_id'
        },
        'table_slide': {
            'file': 'slides.csv',
            'columns': ['slide_id', 'portion_id', 'section_location', 'percent_tumor_nuclei',
                       'percent_tumor_cells', 'percent_stromal_cells', 'percent_necrosis',
                       'percent_normal_cells', 'percent_lymphocyte_infiltration',
                       'created_datetime', 'updated_datetime', 'state'],
            'key_column': 'slide_id'
        },
        'table_analyte': {
            'file': 'analytes.csv',
            'columns': ['analyte_id', 'portion_id', 'analyte_type', 'concentration',
                       'spectrophotometer_method', 'rna_integrity_number', 'a260_a280_ratio',
                       'experimental_protocol_type', 'created_datetime', 'updated_datetime', 'state'],
            'key_column': 'analyte_id'
        },
        'table_aliquot': {
            'file': 'aliquots.csv',
            'columns': ['aliquot_id', 'analyte_id', 'aliquot_quantity', 'aliquot_volume',
                       'concentration', 'source_center', 'analyte_type',
                       'created_datetime', 'updated_datetime', 'state'],
            'key_column': 'aliquot_id'
        }
    }

    import_order = [
        'table_project',
        'table_case',
        'table_demographic',
        'table_diagnosis',
        'table_treatment',
        'table_pathology_detail',
        'table_follow_up',
        'table_molecular_test',
        'table_other_clinical_attribute',
        'table_exposure',
        'table_family_history',
        'table_sample',
        'table_portion',
        'table_slide',
        'table_analyte',
        'table_aliquot'
    ]

    total_records = 0
    for i, table_name in enumerate(import_order, 1):
        config = tables_config[table_name]
        logger.info(f"[{i}/{len(import_order)}] Importing {SCHEMA_NAME}.{table_name}...")
        count = import_csv_to_table_optimized(conn, table_name, config['file'], config['columns'],
                                              config.get('key_column'))
        total_records += count

    logger.info(f"Biomedical data import complete! {total_records:,} records imported in total")
    return total_records


def create_indexes(conn):
    """Create indexes after the data import (to improve query performance)."""
    logger.info("Creating indexes...")

    index_sqls = [
        f"CREATE INDEX IF NOT EXISTS idx_case_project ON {SCHEMA_NAME}.table_case(project_id)",
        f"CREATE INDEX IF NOT EXISTS idx_diagnosis_case ON {SCHEMA_NAME}.table_diagnosis(case_id)",
        f"CREATE INDEX IF NOT EXISTS idx_treatment_diagnosis ON {SCHEMA_NAME}.table_treatment(diagnosis_id)",
        f"CREATE INDEX IF NOT EXISTS idx_follow_up_case ON {SCHEMA_NAME}.table_follow_up(case_id)",
        f"CREATE INDEX IF NOT EXISTS idx_molecular_test_follow_up ON {SCHEMA_NAME}.table_molecular_test(follow_up_id)",
        f"CREATE INDEX IF NOT EXISTS idx_sample_case ON {SCHEMA_NAME}.table_sample(case_id)",
        f"CREATE INDEX IF NOT EXISTS idx_portion_sample ON {SCHEMA_NAME}.table_portion(sample_id)",
        f"CREATE INDEX IF NOT EXISTS idx_slide_portion ON {SCHEMA_NAME}.table_slide(portion_id)",
        f"CREATE INDEX IF NOT EXISTS idx_analyte_portion ON {SCHEMA_NAME}.table_analyte(portion_id)",
        f"CREATE INDEX IF NOT EXISTS idx_aliquot_analyte ON {SCHEMA_NAME}.table_aliquot(analyte_id)"
    ]

    cur = conn.cursor()
    for sql_stmt in index_sqls:
        try:
            cur.execute(sql_stmt)
            conn.commit()
            logger.info(f"  Index created successfully")
        except Exception as e:
            logger.warning(f"  Failed to create index: {e}")
    cur.close()
    logger.info("Index creation complete")


def verify_import(conn):
    """Verify the results of the data import."""
    logger.info("Verifying the data import results...")

    tables_to_verify = [
        'table_project',
        'table_case',
        'table_demographic',
        'table_diagnosis',
        'table_treatment',
        'table_follow_up',
        'table_sample',
        'table_portion',
        'table_slide'
    ]

    cur = conn.cursor()
    for table in tables_to_verify:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {SCHEMA_NAME}.{table}")
            count = cur.fetchone()[0]
            logger.info(f"  {SCHEMA_NAME}.{table}: {count:,} records")
        except Exception as e:
            logger.warning(f"  {SCHEMA_NAME}.{table}: query failed - {e}")

    cur.close()


def set_search_path(conn):
    """Set the default search path."""
    logger.info(f"Setting the default search path to include {SCHEMA_NAME}")

    cur = conn.cursor()
    try:
        cur.execute(sql.SQL("ALTER USER {} SET search_path = {}, public").format(
            sql.Identifier(DB_USER), sql.Identifier(SCHEMA_NAME)))
        conn.commit()
        logger.info(f"search_path set to include {SCHEMA_NAME}")
    except Exception as e:
        logger.warning(f"Failed to set search_path: {e}")
    finally:
        cur.close()


# ============ Organic-polymer load ============
# 5 denormalized tables created in the public schema (matching the identifiers used by the §6.2 polymer queries).

POLYMER_TABLES = {
    'materials': {
        'file': 'materials.csv',
        'ddl': f"""
            CREATE TABLE {POLYMER_SCHEMA}.materials (
                material_id VARCHAR(50) PRIMARY KEY,
                name TEXT,
                smiles TEXT,
                repeat_unit_smiles TEXT,
                pid VARCHAR(100),
                category VARCHAR(100),
                average_mw NUMERIC,
                tensile_modulus NUMERIC,
                tensile_strength NUMERIC,
                thermal_decomposition NUMERIC,
                glass_temperature NUMERIC,
                melting_temperature NUMERIC,
                heat_deflection_temperature NUMERIC,
                raw_source VARCHAR(100)
            )
        """,
        'columns': ['material_id', 'name', 'smiles', 'repeat_unit_smiles', 'pid', 'category',
                    'average_mw', 'tensile_modulus', 'tensile_strength', 'thermal_decomposition',
                    'glass_temperature', 'melting_temperature', 'heat_deflection_temperature',
                    'raw_source'],
        'key_column': 'material_id',
    },
    'processing_cases': {
        'file': 'processing_cases.csv',
        'ddl': f"""
            CREATE TABLE {POLYMER_SCHEMA}.processing_cases (
                process_id VARCHAR(50) PRIMARY KEY,
                material_name TEXT,
                material_id VARCHAR(50),
                sample_no VARCHAR(100),
                formulation TEXT,
                speed NUMERIC,
                pressure NUMERIC,
                pressure_time NUMERIC,
                cooling_temperature NUMERIC,
                cooling_time NUMERIC,
                injection_rate NUMERIC,
                processing_temperature NUMERIC,
                raw_source VARCHAR(100)
            )
        """,
        'columns': ['process_id', 'material_name', 'material_id', 'sample_no', 'formulation',
                    'speed', 'pressure', 'pressure_time', 'cooling_temperature', 'cooling_time',
                    'injection_rate', 'processing_temperature', 'raw_source'],
        'key_column': 'process_id',
    },
    'waxd_results': {
        'file': 'waxd_results.csv',
        'ddl': f"""
            CREATE TABLE {POLYMER_SCHEMA}.waxd_results (
                waxd_id VARCHAR(50) PRIMARY KEY,
                process_id VARCHAR(50),
                sample_no VARCHAR(100),
                pa_content NUMERIC,
                waxd_peak NUMERIC,
                crystallinity NUMERIC,
                crystal_size NUMERIC,
                orientation NUMERIC,
                quality_value NUMERIC,
                raw_value NUMERIC
            )
        """,
        'columns': ['waxd_id', 'process_id', 'sample_no', 'pa_content', 'waxd_peak',
                    'crystallinity', 'crystal_size', 'orientation', 'quality_value', 'raw_value'],
        'key_column': 'waxd_id',
    },
    'performance_results': {
        'file': 'performance_results.csv',
        'ddl': f"""
            CREATE TABLE {POLYMER_SCHEMA}.performance_results (
                performance_id VARCHAR(50) PRIMARY KEY,
                process_id VARCHAR(50),
                sample_no VARCHAR(100),
                tensile_strength NUMERIC,
                tensile_modulus NUMERIC,
                elongation NUMERIC,
                impact_strength NUMERIC,
                composite_mechanical_property NUMERIC,
                raw_source VARCHAR(100)
            )
        """,
        'columns': ['performance_id', 'process_id', 'sample_no', 'tensile_strength',
                    'tensile_modulus', 'elongation', 'impact_strength',
                    'composite_mechanical_property', 'raw_source'],
        'key_column': 'performance_id',
    },
    'pa6t_simulations': {
        'file': 'pa6t_simulations.csv',
        'ddl': f"""
            CREATE TABLE {POLYMER_SCHEMA}.pa6t_simulations (
                simulation_id VARCHAR(50) PRIMARY KEY,
                pa6t_content NUMERIC,
                temperature NUMERIC,
                density NUMERIC,
                energy NUMERIC,
                transition_temperature NUMERIC,
                raw_source VARCHAR(100)
            )
        """,
        'columns': ['simulation_id', 'pa6t_content', 'temperature', 'density', 'energy',
                    'transition_temperature', 'raw_source'],
        'key_column': 'simulation_id',
    },
}

# Table creation order (materials/processing first for readability; denormalized, no foreign key constraints)
POLYMER_IMPORT_ORDER = ['materials', 'processing_cases', 'waxd_results',
                        'performance_results', 'pa6t_simulations']


def load_polymer(conn):
    """Create and load the 5 organic-polymer public.* tables."""
    logger.info("=" * 60)
    logger.info(f"Loading organic-polymer data (schema {POLYMER_SCHEMA}, 5 tables)")
    logger.info("=" * 60)

    if not os.path.isdir(POLYMER_CSV_DIR):
        logger.warning(f"Polymer CSV directory not found: {POLYMER_CSV_DIR}; skipping the polymer load (please run 1_convert.py first)")
        return 0

    cur = conn.cursor()
    # Create tables (drop first, then create)
    for name in reversed(POLYMER_IMPORT_ORDER):
        cur.execute(sql.SQL("DROP TABLE IF EXISTS {}.{} CASCADE").format(
            sql.Identifier(POLYMER_SCHEMA), sql.Identifier(name)))
    for name in POLYMER_IMPORT_ORDER:
        cur.execute(POLYMER_TABLES[name]['ddl'])
    conn.commit()
    cur.close()
    logger.info("Organic-polymer tables created")

    total = 0
    for i, name in enumerate(POLYMER_IMPORT_ORDER, 1):
        cfg = POLYMER_TABLES[name]
        logger.info(f"[{i}/{len(POLYMER_IMPORT_ORDER)}] Importing {POLYMER_SCHEMA}.{name}...")
        count = import_csv_to_table_optimized(
            conn, name, cfg['file'], cfg['columns'], cfg.get('key_column'),
            csv_dir=POLYMER_CSV_DIR, schema=POLYMER_SCHEMA)
        total += count

    # Indexes used by the polymer queries
    cur = conn.cursor()
    for idx_sql in [
        f"CREATE INDEX IF NOT EXISTS idx_waxd_sample ON {POLYMER_SCHEMA}.waxd_results(sample_no)",
        f"CREATE INDEX IF NOT EXISTS idx_materials_category ON {POLYMER_SCHEMA}.materials(category)",
        f"CREATE INDEX IF NOT EXISTS idx_processing_material ON {POLYMER_SCHEMA}.processing_cases(material_id)",
    ]:
        try:
            cur.execute(idx_sql)
            conn.commit()
        except Exception as e:
            logger.warning(f"  Failed to create polymer index: {e}")
    cur.close()

    logger.info(f"Organic-polymer data import complete! {total:,} records imported in total")
    return total


def main():
    """Main entry point: clean up + create schema/tables + import both domains + foreign keys/indexes."""
    logger.info("=" * 60)
    logger.info("Step 2: Create the schema and import the converted tables (biomedical + organic polymer)")
    logger.info(f"Biomedical schema: {SCHEMA_NAME}  |  Organic-polymer schema: {POLYMER_SCHEMA}")
    logger.info("=" * 60)

    # First clean up and recreate the clinical schema (folded in from cleanup_db.py)
    cleanup_db()

    conn = None
    try:
        conn = get_db_connection()
        logger.info("Database connection established")

        # ---- Biomedical ----
        create_schema(conn)
        create_tables(conn)
        bio_records = import_all_data(conn)
        add_foreign_keys(conn)
        create_indexes(conn)
        verify_import(conn)
        set_search_path(conn)

        # ---- Organic polymer ----
        poly_records = load_polymer(conn)

        logger.info("=" * 60)
        logger.info(f"Data import completed successfully!")
        logger.info(f"  Biomedical: {bio_records:,} records (clinical schema, 16 tables)")
        logger.info(f"  Organic polymer: {poly_records:,} records (public schema, 5 tables)")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error during the import process: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed")


if __name__ == "__main__":
    main()
