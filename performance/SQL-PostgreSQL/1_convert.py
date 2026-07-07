#!/usr/bin/env python3
"""
Step 1 — Convert the raw data into relational CSV tables.

This is the conversion step of the §6.4 SQL/PostgreSQL performance run. It
produces TWO sets of CSV tables, one per domain:

  * BIOMEDICAL: stream the large TCGA clinical+biospecimen JSON and split it
    into the 16 relational tables that back the `clinical.*` schema. Output ->
    ./csv_exports/ (projects.csv, cases.csv, ... aliquots.csv). The parser is
    fully streaming with batched CSV writes, progress logging and resumable
    checkpointing so it can process the multi-GB raw dump.

  * ORGANIC-POLYMER: mirror the logic of
    ../../conciseness/_polymer_conversion/to_relational.py, reading the three
    prepared (already-translated) source files and emitting the 5 denormalised
    `public.*` tables. Output -> ./csv_exports_polymer/ (materials.csv,
    processing_cases.csv, waxd_results.csv, performance_results.csv,
    pa6t_simulations.csv).

Run order: 1_convert.py -> 2_load.py -> 3_benchmark.py
"""

import json
import os
import gc
import gzip
import csv
from datetime import datetime
import logging
from collections import defaultdict
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============ Biomedical config ============
JSON_FILE_PATH = '/home/sal/expanded_100.json'
OUTPUT_DIR = './csv_exports'
BATCH_SIZE = 100000  # 100k cases per batch, more stable
PROGRESS_FILE = './etl_progress.txt'

# ============ Polymer config ============
# The three prepared (translated) source files live next to to_relational.py
# in the conciseness folder. They are derived/gitignored — regenerate them with
# the conciseness conversion scripts if missing.
POLYMER_SRC_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 '..', '..', 'conciseness', '_polymer_conversion'))
POLYMER_OUTPUT_DIR = './csv_exports_polymer'

# ============ CSV headers for the 16 tables (comma-separated) ============
HEADERS = {
    'projects': 'project_id,project_name\n',
    'cases': 'case_id,primary_site,disease_type,project_id,submitter_id,created_datetime,updated_datetime,state,days_to_consent,consent_type,lost_to_followup,index_date\n',
    'demographics': 'demographic_id,case_id,ethnicity,gender,race,vital_status,sex_at_birth,days_to_birth,age_at_index,country_of_residence,cause_of_death,days_to_death,created_datetime,updated_datetime,state\n',
    'diagnoses': 'diagnosis_id,case_id,primary_diagnosis,morphology,tissue_or_organ_of_origin,site_of_resection_or_biopsy,age_at_diagnosis,days_to_diagnosis,classification_of_tumor,tumor_grade,tumor_stage,ajcc_pathologic_stage,ajcc_pathologic_t,ajcc_pathologic_n,ajcc_pathologic_m,progression_or_recurrence,last_known_disease_status,year_of_diagnosis,created_datetime,updated_datetime,state,diagnosis_is_primary_disease,prior_malignancy,prior_treatment,residual_disease,icd_10_code\n',
    'treatments': 'treatment_id,diagnosis_id,treatment_type,treatment_intent_type,treatment_or_therapy,days_to_treatment_start,initial_disease_status,number_of_cycles,residual_disease,protocol_identifier,created_datetime,updated_datetime,state\n',
    'pathology_details': 'pathology_detail_id,diagnosis_id,consistent_pathology_review,vascular_invasion_present,vascular_invasion_type,lymph_nodes_tested,lymph_nodes_positive,perineural_invasion_present,additional_pathology_findings,created_datetime,updated_datetime,state\n',
    'follow_ups': 'follow_up_id,case_id,days_to_follow_up,timepoint_category,disease_response,progression_or_recurrence,progression_or_recurrence_type,progression_or_recurrence_anatomic_site,days_to_recurrence,ecog_performance_status,karnofsky_performance_status,imaging_type,imaging_result,created_datetime,updated_datetime,state\n',
    'molecular_tests': 'molecular_test_id,follow_up_id,laboratory_test,test_value,test_units,test_result,timepoint_category,gene_symbol,molecular_analysis_method,antigen,days_to_test,created_datetime,updated_datetime,state\n',
    'other_clinical_attributes': 'other_clinical_attribute_id,follow_up_id,weight,height,bmi,timepoint_category,created_datetime,updated_datetime,state\n',
    'exposures': 'exposure_id,case_id,exposure_type,tobacco_smoking_status,pack_years_smoked,cigarettes_per_day,alcohol_history,alcohol_intensity,created_datetime,updated_datetime,state\n',
    'family_histories': 'family_history_id,case_id,relative_with_cancer_history,relatives_with_cancer_history_count,relationship_primary_diagnosis,created_datetime,updated_datetime,state\n',
    'samples': 'sample_id,case_id,sample_type,tissue_type,specimen_type,tumor_descriptor,preservation_method,days_to_collection,days_to_sample_procurement,initial_weight,current_weight,created_datetime,updated_datetime,state\n',
    'portions': 'portion_id,sample_id,portion_number,weight,is_ffpe,creation_datetime,created_datetime,updated_datetime,state\n',
    'slides': 'slide_id,portion_id,section_location,percent_tumor_nuclei,percent_tumor_cells,percent_stromal_cells,percent_necrosis,percent_normal_cells,percent_lymphocyte_infiltration,created_datetime,updated_datetime,state\n',
    'analytes': 'analyte_id,portion_id,analyte_type,concentration,spectrophotometer_method,rna_integrity_number,a260_a280_ratio,experimental_protocol_type,created_datetime,updated_datetime,state\n',
    'aliquots': 'aliquot_id,analyte_id,aliquot_quantity,aliquot_volume,concentration,source_center,analyte_type,created_datetime,updated_datetime,state\n'
}


def ensure_output_dir():
    """Make sure the output directory exists."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def init_csv_files():
    """Initialize all CSV files (write the header row)."""
    for name, header in HEADERS.items():
        filepath = os.path.join(OUTPUT_DIR, f'{name}.csv')
        if not os.path.exists(filepath):
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(header)
            logger.debug(f"Created file: {name}.csv")


def safe_str(value):
    """Safely convert a value to a string."""
    return '' if value is None else str(value)


def safe_int(value):
    """Safely convert a value to an integer."""
    if value is None or value == '':
        return ''
    try:
        return int(value)
    except (ValueError, TypeError):
        return ''


def safe_float(value):
    """Safely convert a value to a float."""
    if value is None or value == '':
        return ''
    try:
        return float(value)
    except (ValueError, TypeError):
        return ''


def parse_datetime(dt_str):
    """Parse a datetime string."""
    if not dt_str:
        return ''
    try:
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except:
        return ''


def parse_case(case):
    """Parse a single case and return row data for all 16 tables."""
    results = defaultdict(list)

    case_id = case.get('case_id')
    if not case_id:
        return results

    # 1. Projects table
    project = case.get('project', {})
    project_id = project.get('project_id')
    if project_id:
        results['projects'].append({
            'project_id': project_id,
            'project_name': ''
        })

    # 2. Cases table
    results['cases'].append({
        'case_id': case_id,
        'primary_site': safe_str(case.get('primary_site')),
        'disease_type': safe_str(case.get('disease_type')),
        'project_id': safe_str(project_id),
        'submitter_id': safe_str(case.get('submitter_id')),
        'created_datetime': parse_datetime(case.get('created_datetime')),
        'updated_datetime': parse_datetime(case.get('updated_datetime')),
        'state': safe_str(case.get('state')),
        'days_to_consent': safe_int(case.get('days_to_consent')),
        'consent_type': safe_str(case.get('consent_type')),
        'lost_to_followup': safe_str(case.get('lost_to_followup')),
        'index_date': safe_str(case.get('index_date'))
    })

    # 3. Demographics table
    demo = case.get('demographic')
    if demo:
        results['demographics'].append({
            'demographic_id': safe_str(demo.get('demographic_id')),
            'case_id': case_id,
            'ethnicity': safe_str(demo.get('ethnicity')),
            'gender': safe_str(demo.get('gender')),
            'race': safe_str(demo.get('race')),
            'vital_status': safe_str(demo.get('vital_status')),
            'sex_at_birth': safe_str(demo.get('sex_at_birth')),
            'days_to_birth': safe_int(demo.get('days_to_birth')),
            'age_at_index': safe_int(demo.get('age_at_index')),
            'country_of_residence': safe_str(demo.get('country_of_residence_at_enrollment')),
            'cause_of_death': safe_str(demo.get('cause_of_death')),
            'days_to_death': safe_int(demo.get('days_to_death')),
            'created_datetime': parse_datetime(demo.get('created_datetime')),
            'updated_datetime': parse_datetime(demo.get('updated_datetime')),
            'state': safe_str(demo.get('state'))
        })

    # 4. Diagnoses table + 5. Treatments table + 6. Pathology details table
    for diag in case.get('diagnoses', []):
        diagnosis_id = diag.get('diagnosis_id')
        if not diagnosis_id:
            continue

        results['diagnoses'].append({
            'diagnosis_id': diagnosis_id,
            'case_id': case_id,
            'primary_diagnosis': safe_str(diag.get('primary_diagnosis')),
            'morphology': safe_str(diag.get('morphology')),
            'tissue_or_organ_of_origin': safe_str(diag.get('tissue_or_organ_of_origin')),
            'site_of_resection_or_biopsy': safe_str(diag.get('site_of_resection_or_biopsy')),
            'age_at_diagnosis': safe_int(diag.get('age_at_diagnosis')),
            'days_to_diagnosis': safe_int(diag.get('days_to_diagnosis')),
            'classification_of_tumor': safe_str(diag.get('classification_of_tumor')),
            'tumor_grade': safe_str(diag.get('tumor_grade')),
            'tumor_stage': safe_str(diag.get('ajcc_pathologic_stage') or diag.get('tumor_stage')),
            'ajcc_pathologic_stage': safe_str(diag.get('ajcc_pathologic_stage')),
            'ajcc_pathologic_t': safe_str(diag.get('ajcc_pathologic_t')),
            'ajcc_pathologic_n': safe_str(diag.get('ajcc_pathologic_n')),
            'ajcc_pathologic_m': safe_str(diag.get('ajcc_pathologic_m')),
            'progression_or_recurrence': safe_str(diag.get('progression_or_recurrence')),
            'last_known_disease_status': safe_str(diag.get('last_known_disease_status')),
            'year_of_diagnosis': safe_int(diag.get('year_of_diagnosis')),
            'created_datetime': parse_datetime(diag.get('created_datetime')),
            'updated_datetime': parse_datetime(diag.get('updated_datetime')),
            'state': safe_str(diag.get('state')),
            'diagnosis_is_primary_disease': safe_str(diag.get('diagnosis_is_primary_disease')),
            'prior_malignancy': safe_str(diag.get('prior_malignancy')),
            'prior_treatment': safe_str(diag.get('prior_treatment')),
            'residual_disease': safe_str(diag.get('residual_disease')),
            'icd_10_code': safe_str(diag.get('icd_10_code'))
        })

        # Treatments table
        for treat in diag.get('treatments', []):
            results['treatments'].append({
                'treatment_id': safe_str(treat.get('treatment_id')),
                'diagnosis_id': diagnosis_id,
                'treatment_type': safe_str(treat.get('treatment_type')),
                'treatment_intent_type': safe_str(treat.get('treatment_intent_type')),
                'treatment_or_therapy': safe_str(treat.get('treatment_or_therapy')),
                'days_to_treatment_start': safe_int(treat.get('days_to_treatment_start')),
                'initial_disease_status': safe_str(treat.get('initial_disease_status')),
                'number_of_cycles': safe_int(treat.get('number_of_cycles')),
                'residual_disease': safe_str(treat.get('residual_disease')),
                'protocol_identifier': safe_str(treat.get('protocol_identifier')),
                'created_datetime': parse_datetime(treat.get('created_datetime')),
                'updated_datetime': parse_datetime(treat.get('updated_datetime')),
                'state': safe_str(treat.get('state'))
            })

        # Pathology details table
        for path in diag.get('pathology_details', []):
            results['pathology_details'].append({
                'pathology_detail_id': safe_str(path.get('pathology_detail_id')),
                'diagnosis_id': diagnosis_id,
                'consistent_pathology_review': safe_str(path.get('consistent_pathology_review')),
                'vascular_invasion_present': safe_str(path.get('vascular_invasion_present')),
                'vascular_invasion_type': safe_str(path.get('vascular_invasion_type')),
                'lymph_nodes_tested': safe_int(path.get('lymph_nodes_tested')),
                'lymph_nodes_positive': safe_int(path.get('lymph_nodes_positive')),
                'perineural_invasion_present': safe_str(path.get('perineural_invasion_present')),
                'additional_pathology_findings': safe_str(path.get('additional_pathology_findings')),
                'created_datetime': parse_datetime(path.get('created_datetime')),
                'updated_datetime': parse_datetime(path.get('updated_datetime')),
                'state': safe_str(path.get('state'))
            })

    # 7. Follow-ups table + 8. Molecular tests table + 9. Other clinical attributes table
    for fu in case.get('follow_ups', []):
        follow_up_id = fu.get('follow_up_id')
        if not follow_up_id:
            continue

        results['follow_ups'].append({
            'follow_up_id': follow_up_id,
            'case_id': case_id,
            'days_to_follow_up': safe_int(fu.get('days_to_follow_up')),
            'timepoint_category': safe_str(fu.get('timepoint_category')),
            'disease_response': safe_str(fu.get('disease_response')),
            'progression_or_recurrence': safe_str(fu.get('progression_or_recurrence')),
            'progression_or_recurrence_type': safe_str(fu.get('progression_or_recurrence_type')),
            'progression_or_recurrence_anatomic_site': safe_str(fu.get('progression_or_recurrence_anatomic_site')),
            'days_to_recurrence': safe_int(fu.get('days_to_recurrence')),
            'ecog_performance_status': safe_str(fu.get('ecog_performance_status')),
            'karnofsky_performance_status': safe_str(fu.get('karnofsky_performance_status')),
            'imaging_type': safe_str(fu.get('imaging_type')),
            'imaging_result': safe_str(fu.get('imaging_result')),
            'created_datetime': parse_datetime(fu.get('created_datetime')),
            'updated_datetime': parse_datetime(fu.get('updated_datetime')),
            'state': safe_str(fu.get('state'))
        })

        # Molecular tests table
        for test in fu.get('molecular_tests', []):
            results['molecular_tests'].append({
                'molecular_test_id': safe_str(test.get('molecular_test_id')),
                'follow_up_id': follow_up_id,
                'laboratory_test': safe_str(test.get('laboratory_test')),
                'test_value': safe_float(test.get('test_value')),
                'test_units': safe_str(test.get('test_units')),
                'test_result': safe_str(test.get('test_result')),
                'timepoint_category': safe_str(test.get('timepoint_category')),
                'gene_symbol': safe_str(test.get('gene_symbol')),
                'molecular_analysis_method': safe_str(test.get('molecular_analysis_method')),
                'antigen': safe_str(test.get('antigen')),
                'days_to_test': safe_int(test.get('days_to_test')),
                'created_datetime': parse_datetime(test.get('created_datetime')),
                'updated_datetime': parse_datetime(test.get('updated_datetime')),
                'state': safe_str(test.get('state'))
            })

        # Other clinical attributes table
        for attr in fu.get('other_clinical_attributes', []):
            results['other_clinical_attributes'].append({
                'other_clinical_attribute_id': safe_str(attr.get('other_clinical_attribute_id')),
                'follow_up_id': follow_up_id,
                'weight': safe_float(attr.get('weight')),
                'height': safe_float(attr.get('height')),
                'bmi': safe_float(attr.get('bmi')),
                'timepoint_category': safe_str(attr.get('timepoint_category')),
                'created_datetime': parse_datetime(attr.get('created_datetime')),
                'updated_datetime': parse_datetime(attr.get('updated_datetime')),
                'state': safe_str(attr.get('state'))
            })

    # 10. Exposures table
    for exp in case.get('exposures', []):
        results['exposures'].append({
            'exposure_id': safe_str(exp.get('exposure_id')),
            'case_id': case_id,
            'exposure_type': safe_str(exp.get('exposure_type')),
            'tobacco_smoking_status': safe_str(exp.get('tobacco_smoking_status')),
            'pack_years_smoked': safe_float(exp.get('pack_years_smoked')),
            'cigarettes_per_day': safe_int(exp.get('cigarettes_per_day')),
            'alcohol_history': safe_str(exp.get('alcohol_history')),
            'alcohol_intensity': safe_str(exp.get('alcohol_intensity')),
            'created_datetime': parse_datetime(exp.get('created_datetime')),
            'updated_datetime': parse_datetime(exp.get('updated_datetime')),
            'state': safe_str(exp.get('state'))
        })

    # 11. Family histories table
    for fh in case.get('family_histories', []):
        results['family_histories'].append({
            'family_history_id': safe_str(fh.get('family_history_id')),
            'case_id': case_id,
            'relative_with_cancer_history': safe_str(fh.get('relative_with_cancer_history')),
            'relatives_with_cancer_history_count': safe_int(fh.get('relatives_with_cancer_history_count')),
            'relationship_primary_diagnosis': safe_str(fh.get('relationship_primary_diagnosis')),
            'created_datetime': parse_datetime(fh.get('created_datetime')),
            'updated_datetime': parse_datetime(fh.get('updated_datetime')),
            'state': safe_str(fh.get('state'))
        })

    # 12. Samples table + 13. Portions table + 14. Slides table + 15. Analytes table + 16. Aliquots table
    for sample in case.get('samples', []):
        sample_id = sample.get('sample_id')
        if not sample_id:
            continue

        results['samples'].append({
            'sample_id': sample_id,
            'case_id': case_id,
            'sample_type': safe_str(sample.get('sample_type')),
            'tissue_type': safe_str(sample.get('tissue_type')),
            'specimen_type': safe_str(sample.get('specimen_type')),
            'tumor_descriptor': safe_str(sample.get('tumor_descriptor')),
            'preservation_method': safe_str(sample.get('preservation_method')),
            'days_to_collection': safe_int(sample.get('days_to_collection')),
            'days_to_sample_procurement': safe_int(sample.get('days_to_sample_procurement')),
            'initial_weight': safe_float(sample.get('initial_weight')),
            'current_weight': safe_float(sample.get('current_weight')),
            'created_datetime': parse_datetime(sample.get('created_datetime')),
            'updated_datetime': parse_datetime(sample.get('updated_datetime')),
            'state': safe_str(sample.get('state'))
        })

        for portion in sample.get('portions', []):
            portion_id = portion.get('portion_id')
            if not portion_id:
                continue

            # Portions table
            results['portions'].append({
                'portion_id': portion_id,
                'sample_id': sample_id,
                'portion_number': safe_str(portion.get('portion_number')),
                'weight': safe_float(portion.get('weight')),
                'is_ffpe': safe_str(portion.get('is_ffpe')),
                'creation_datetime': safe_str(portion.get('creation_datetime')),
                'created_datetime': parse_datetime(portion.get('created_datetime')),
                'updated_datetime': parse_datetime(portion.get('updated_datetime')),
                'state': safe_str(portion.get('state'))
            })

            # Slides table
            for slide in portion.get('slides', []):
                results['slides'].append({
                    'slide_id': safe_str(slide.get('slide_id')),
                    'portion_id': portion_id,
                    'section_location': safe_str(slide.get('section_location')),
                    'percent_tumor_nuclei': safe_float(slide.get('percent_tumor_nuclei')),
                    'percent_tumor_cells': safe_float(slide.get('percent_tumor_cells')),
                    'percent_stromal_cells': safe_float(slide.get('percent_stromal_cells')),
                    'percent_necrosis': safe_float(slide.get('percent_necrosis')),
                    'percent_normal_cells': safe_float(slide.get('percent_normal_cells')),
                    'percent_lymphocyte_infiltration': safe_float(slide.get('percent_lymphocyte_infiltration')),
                    'created_datetime': parse_datetime(slide.get('created_datetime')),
                    'updated_datetime': parse_datetime(slide.get('updated_datetime')),
                    'state': safe_str(slide.get('state'))
                })

            # Analytes table
            for analyte in portion.get('analytes', []):
                analyte_id = analyte.get('analyte_id')
                if not analyte_id:
                    continue

                results['analytes'].append({
                    'analyte_id': analyte_id,
                    'portion_id': portion_id,
                    'analyte_type': safe_str(analyte.get('analyte_type')),
                    'concentration': safe_float(analyte.get('concentration')),
                    'spectrophotometer_method': safe_str(analyte.get('spectrophotometer_method')),
                    'rna_integrity_number': safe_float(analyte.get('rna_integrity_number')),
                    'a260_a280_ratio': safe_float(analyte.get('a260_a280_ratio')),
                    'experimental_protocol_type': safe_str(analyte.get('experimental_protocol_type')),
                    'created_datetime': parse_datetime(analyte.get('created_datetime')),
                    'updated_datetime': parse_datetime(analyte.get('updated_datetime')),
                    'state': safe_str(analyte.get('state'))
                })

                # Aliquots table
                for aliquot in analyte.get('aliquots', []):
                    results['aliquots'].append({
                        'aliquot_id': safe_str(aliquot.get('aliquot_id')),
                        'analyte_id': analyte_id,
                        'aliquot_quantity': safe_float(aliquot.get('aliquot_quantity')),
                        'aliquot_volume': safe_float(aliquot.get('aliquot_volume')),
                        'concentration': safe_float(aliquot.get('concentration')),
                        'source_center': safe_str(aliquot.get('source_center')),
                        'analyte_type': safe_str(aliquot.get('analyte_type')),
                        'created_datetime': parse_datetime(aliquot.get('created_datetime')),
                        'updated_datetime': parse_datetime(aliquot.get('updated_datetime')),
                        'state': safe_str(aliquot.get('state'))
                    })

    return results


def write_batch_results(results, batch_num):
    """Append a batch of results to the CSV files (append mode)."""
    for table_name, rows in results.items():
        if not rows:
            continue

        filepath = os.path.join(OUTPUT_DIR, f'{table_name}.csv')

        with open(filepath, 'a', encoding='utf-8') as f:
            for row in rows:
                # Build the comma-separated row, escaping special characters
                line_parts = []
                for v in row.values():
                    v_str = str(v) if v is not None else ''
                    if ',' in v_str or '\n' in v_str or '"' in v_str:
                        v_str = '"' + v_str.replace('"', '""') + '"'
                    line_parts.append(v_str)
                f.write(','.join(line_parts) + '\n')


def stream_json_chunks(filepath, batch_size=100000):
    """Stream-read the JSON file and yield it batch by batch."""
    if filepath.endswith('.gz'):
        f = gzip.open(filepath, 'rt', encoding='utf-8', buffering=1024*1024*10)
    else:
        f = open(filepath, 'r', encoding='utf-8', buffering=1024*1024*10)

    logger.info("Scanning the JSON file to locate the start of the array...")
    # Skip to the opening [
    scanned = 0
    ch = f.read(1)
    while ch and ch != '[':
        scanned += 1
        if scanned % 100000000 == 0:
            logger.info(f"  Scanned {scanned/1e9:.1f} GB")
        ch = f.read(1)
    logger.info("Located the array; starting to parse JSON objects...")

    batch = []
    brace_count = 0
    in_string = False
    escape = False
    buffer = []
    obj_start = -1
    batch_num = 0
    obj_count = 0

    # Read and parse JSON objects
    bytes_read = 0
    while True:
        chunk = f.read(1024 * 1024)  # 1 MB buffer
        if not chunk:
            break

        bytes_read += len(chunk)
        if bytes_read % (500 * 1024 * 1024) == 0:  # Log every 500 MB
            logger.info(f"  Read {bytes_read / (1024**3):.1f} GB of data")

        for ch in chunk:
            buffer.append(ch)

            if escape:
                escape = False
                continue

            if ch == '\\':
                escape = True
                continue

            if ch == '"':
                in_string = not in_string
                continue

            if not in_string:
                if ch == '{':
                    if brace_count == 0:
                        obj_start = len(buffer) - 1
                    brace_count += 1
                elif ch == '}':
                    brace_count -= 1
                    if brace_count == 0 and obj_start >= 0:
                        try:
                            obj = json.loads(''.join(buffer[obj_start:]))
                            batch.append(obj)
                            obj_count += 1
                            buffer = []
                            obj_start = -1

                            if obj_count % 50000 == 0:
                                logger.info(f"  Parsed {obj_count:,} JSON objects")

                            if len(batch) >= batch_size:
                                batch_num += 1
                                logger.info(f"Collected batch {batch_num}: {len(batch)} cases")
                                yield batch_num, batch
                                batch = []
                        except json.JSONDecodeError as e:
                            logger.warning(f"JSON parse error, skipping: {e}")
                            buffer = []
                            obj_start = -1
                            brace_count = 0
                            in_string = False
                            escape = False

    if batch:
        batch_num += 1
        logger.info(f"Collected final batch {batch_num}: {len(batch)} cases")
        yield batch_num, batch

    f.close()
    logger.info(f"Parsed {obj_count:,} JSON objects in total")


def load_progress():
    """Load the processing progress."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return int(f.read().strip())
    return 0


def save_progress(batch_num):
    """Save the processing progress."""
    with open(PROGRESS_FILE, 'w') as f:
        f.write(str(batch_num))
        f.flush()  # Flush to disk immediately
        os.fsync(f.fileno())  # Make sure it is written to disk


def convert_biomedical():
    """Biomedical: stream-parse the TCGA clinical JSON and split it into 16 relational CSV tables."""
    start_time = time.time()
    logger.info("=" * 60)
    logger.info("Biomedical conversion: streaming ETL (full set of 16 tables)")
    logger.info(f"JSON file: {JSON_FILE_PATH}")
    logger.info(f"Output directory: {OUTPUT_DIR}")
    logger.info(f"Batch size: {BATCH_SIZE:,} cases")
    logger.info("=" * 60)

    ensure_output_dir()
    init_csv_files()

    # Load progress
    last_batch = load_progress()
    if last_batch > 0:
        logger.info(f"Resuming from last interruption, skipping the first {last_batch} batches")

    # Get the file size
    file_size = os.path.getsize(JSON_FILE_PATH)
    logger.info(f"File size: {file_size / (1024**3):.2f} GB")

    total_processed = last_batch * BATCH_SIZE
    batch_count = 0

    try:
        for batch_num, batch in stream_json_chunks(JSON_FILE_PATH, BATCH_SIZE):
            if batch_num <= last_batch:
                logger.info(f"Skipping batch {batch_num} (already processed)")
                total_processed += len(batch)
                continue

            batch_start = time.time()
            logger.info(f"\nProcessing batch {batch_num}... ({len(batch):,} cases)")

            # Parse the cases in the batch
            batch_results = defaultdict(list)
            case_counter = 0
            for case in batch:
                results = parse_case(case)
                for table, rows in results.items():
                    batch_results[table].extend(rows)
                case_counter += 1
                if case_counter % 50000 == 0:
                    logger.info(f"  Parsed {case_counter:,}/{len(batch):,} cases")

            # Write the results
            logger.info(f"  Writing CSV files...")
            write_batch_results(batch_results, batch_num)

            # Save progress immediately
            save_progress(batch_num)
            logger.info(f"  Progress saved: batch {batch_num}")

            # Statistics
            batch_time = time.time() - batch_start
            rate = len(batch) / batch_time
            total_processed += len(batch)
            batch_count += 1

            elapsed = time.time() - start_time
            overall_rate = total_processed / elapsed if elapsed > 0 else 0

            logger.info(f"  Batch {batch_num} done: {batch_time:.1f} s, {rate:.0f} rows/s")
            logger.info(f"  Cumulative: {total_processed:,} cases, average throughput: {overall_rate:.0f} rows/s")

            # Force GC after each batch
            gc.collect()

        elapsed = time.time() - start_time
        logger.info("=" * 60)
        logger.info(f"Biomedical conversion complete! {total_processed:,} cases in total")
        logger.info(f"Total elapsed time: {elapsed/3600:.2f} hours")
        logger.info("=" * 60)

        # Delete the progress file
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)

    except KeyboardInterrupt:
        logger.warning(f"\nInterrupted by user! Processed {total_processed:,} cases so far")
        if 'batch_num' in locals():
            logger.info(f"Progress saved up to batch {batch_num}")
            logger.info(f"The next run will resume from batch {batch_num + 1}")
    except Exception as e:
        logger.exception(f"Error: {e}")
        logger.info("Progress has been saved; you can resume after fixing the issue")


# ============ Organic polymer conversion ============
# Same logic as ../../conciseness/_polymer_conversion/to_relational.py: read the
# three already-translated source files and emit 5 denormalised public.* CSV tables.

POLYMER_COLUMNS = {
    "materials": ["material_id", "name", "smiles", "repeat_unit_smiles", "pid", "category",
                  "average_mw", "tensile_modulus", "tensile_strength", "thermal_decomposition",
                  "glass_temperature", "melting_temperature", "heat_deflection_temperature",
                  "raw_source"],
    "processing_cases": ["process_id", "material_name", "material_id", "sample_no",
                         "formulation", "speed", "pressure", "pressure_time",
                         "cooling_temperature", "cooling_time", "injection_rate",
                         "processing_temperature", "raw_source"],
    "waxd_results": ["waxd_id", "process_id", "sample_no", "pa_content", "waxd_peak",
                     "crystallinity", "crystal_size", "orientation", "quality_value",
                     "raw_value"],
    "performance_results": ["performance_id", "process_id", "sample_no", "tensile_strength",
                            "tensile_modulus", "elongation", "impact_strength",
                            "composite_mechanical_property", "raw_source"],
    "pa6t_simulations": ["simulation_id", "pa6t_content", "temperature", "density", "energy",
                         "transition_temperature", "raw_source"],
}


def convert_polymer():
    """Organic polymer: convert the three prepared source files into 5 public.* CSV tables."""
    logger.info("=" * 60)
    logger.info("Organic polymer conversion: 5 denormalised relational tables")
    logger.info(f"Source directory: {POLYMER_SRC_DIR}")
    logger.info(f"Output directory: {POLYMER_OUTPUT_DIR}")
    logger.info("=" * 60)

    materials_path = os.path.join(POLYMER_SRC_DIR, "materials_library_en.json")
    processing_path = os.path.join(POLYMER_SRC_DIR, "processing_logs_en.json")
    pa6t_path = os.path.join(POLYMER_SRC_DIR, "pa6t_library_en.json")

    for p in (materials_path, processing_path, pa6t_path):
        if not os.path.exists(p):
            logger.warning(f"Polymer source file missing: {p}")
            logger.warning("Generate the *_en.json files first with the conciseness/_polymer_conversion scripts; skipping polymer conversion")
            return

    os.makedirs(POLYMER_OUTPUT_DIR, exist_ok=True)
    rows = {t: [] for t in POLYMER_COLUMNS}

    materials = json.load(open(materials_path, encoding="utf-8"))
    processing = json.load(open(processing_path, encoding="utf-8"))
    pa6t = json.load(open(pa6t_path, encoding="utf-8"))

    for i, m in enumerate(materials, 1):
        mid = f"PM{i:05d}"
        bi, s0 = m["basic_info"], (m["samples"][0] if m["samples"] else {})
        th, mech = s0.get("thermal", {}), s0.get("mechanical", {})
        rows["materials"].append({
            "material_id": mid, "name": bi.get("name"), "smiles": bi.get("smiles"),
            "repeat_unit_smiles": bi.get("repeat_unit_smiles"), "pid": bi.get("pid"),
            "category": bi.get("category"), "average_mw": s0.get("average_mw"),
            "tensile_modulus": mech.get("tensile_modulus"),
            "tensile_strength": mech.get("tensile_strength"),
            "thermal_decomposition": th.get("thermal_decomposition"),
            "glass_temperature": th.get("glass_temperature"),
            "melting_temperature": th.get("melting_temperature"),
            "heat_deflection_temperature": None, "raw_source": "polyamide"})

    for i, p in enumerate(processing, 1):
        eid = f"PROC{i:05d}"
        ms = p.get("machine_settings", {})
        inj = ms.get("injection", {}).get("stages", []) or []
        hold_p = ms.get("holding", {}).get("pressures", []) or []
        hold_t = ms.get("holding", {}).get("times", []) or []
        cool = ms.get("cooling", {})
        rows["processing_cases"].append({
            "process_id": eid, "material_name": p.get("material_name"), "material_id": None,
            "sample_no": p["meta"].get("data_id"), "formulation": p.get("material_name"),
            "speed": inj[0] if inj else None, "pressure": hold_p[0] if hold_p else None,
            "pressure_time": hold_t[0] if hold_t else None,
            "cooling_temperature": cool.get("mold_temperature"),
            "cooling_time": cool.get("cooling_time"),
            "injection_rate": inj[0] if inj else None,
            "processing_temperature": cool.get("mold_temperature"), "raw_source": "processing"})
        w = p.get("WAXD_result", {})
        rows["waxd_results"].append({
            "waxd_id": f"{eid}_W", "process_id": eid, "sample_no": p["meta"].get("data_id"),
            "pa_content": None, "waxd_peak": None, "crystallinity": w.get("alpha_crystallinity"),
            "crystal_size": None, "orientation": None,
            "quality_value": w.get("alpha_100"), "raw_value": w.get("gamma")})
        me = p.get("mechanical", {})
        rows["performance_results"].append({
            "performance_id": f"{eid}_P", "process_id": eid, "sample_no": p["meta"].get("data_id"),
            "tensile_strength": me.get("tensile_strength"), "tensile_modulus": me.get("elastic_modulus"),
            "elongation": me.get("elongation_at_break"), "impact_strength": None,
            "composite_mechanical_property": me.get("yield_stress"), "raw_source": "processing"})

    for i, r in enumerate(pa6t, 1):
        cv = r.get("composition_variation", {})
        rows["pa6t_simulations"].append({
            "simulation_id": f"PA6T{i:06d}", "pa6t_content": cv.get("pa6t_content"),
            "temperature": r.get("temperature"), "density": r.get("density"),
            "energy": r.get("energy"),
            "transition_temperature": (r.get("temperature_range") or {}).get("lb"),
            "raw_source": "pa6t"})

    for t, cols in POLYMER_COLUMNS.items():
        with open(os.path.join(POLYMER_OUTPUT_DIR, t + ".csv"), "w", newline="", encoding="utf-8") as fh:
            wr = csv.DictWriter(fh, fieldnames=cols)
            wr.writeheader()
            wr.writerows(rows[t])
        logger.info(f"  {t:22} {len(rows[t]):>6} rows")
    logger.info(f"Organic polymer conversion complete! {len(POLYMER_COLUMNS)} tables in total")


def main():
    logger.info("############ Step 1: Data conversion (biomedical + organic polymer) ############")
    convert_biomedical()
    convert_polymer()
    logger.info("############ Step 1 complete ############")


if __name__ == "__main__":
    main()
