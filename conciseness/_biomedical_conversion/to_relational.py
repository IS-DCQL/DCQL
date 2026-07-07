#!/usr/bin/env python3
"""Relational structure for the biomedical data: 16 tables (Table 2).

3NF normalisation of the TCGA clinical+biospecimen model.  This reproduces *exactly* the
relational schema used in the §6.4 performance test (`SQL-PostgreSQL/data_importer.py`,
schema `clinical`, 16 `table_*` tables); the §6.4 run carries the full cohort, the §6.2
teaching subset populates the entity types it actually contains.  Table & column names
match the SQL/OQL §6.2 queries (`clinical.table_case`, `clinical.table_aliquot`, ...).

Tables (16): table_project, table_case, table_demographic, table_diagnosis,
table_treatment, table_pathology_detail, table_follow_up, table_molecular_test,
table_other_clinical_attribute, table_exposure, table_family_history, table_sample,
table_portion, table_slide, table_analyte, table_aliquot.
"""
import csv, os
from _common import load_cases

HERE = os.path.dirname(__file__)

COLUMNS = {
    "table_project": ["project_id", "project_name"],
    "table_case": ["case_id", "project_id", "primary_site", "disease_type",
                   "submitter_id", "state", "created_datetime", "updated_datetime"],
    "table_demographic": ["demographic_id", "case_id", "ethnicity", "gender", "race",
                          "vital_status", "sex_at_birth", "days_to_birth",
                          "created_datetime", "updated_datetime", "state"],
    "table_diagnosis": ["diagnosis_id", "case_id", "primary_diagnosis", "morphology",
                        "tissue_or_organ_of_origin", "site_of_resection_or_biopsy",
                        "age_at_diagnosis", "classification_of_tumor", "tumor_grade",
                        "last_known_disease_status", "progression_or_recurrence",
                        "created_datetime", "updated_datetime", "state"],
    "table_treatment": ["treatment_id", "diagnosis_id", "treatment_type",
                        "treatment_intent_type", "treatment_or_therapy",
                        "days_to_treatment_start", "number_of_cycles", "state"],
    "table_pathology_detail": ["pathology_detail_id", "diagnosis_id",
                               "consistent_pathology_review", "vascular_invasion_present",
                               "vascular_invasion_type", "lymph_nodes_tested",
                               "lymph_nodes_positive", "perineural_invasion_present",
                               "additional_pathology_findings", "state"],
    "table_follow_up": ["follow_up_id", "case_id", "days_to_follow_up",
                        "disease_response", "progression_or_recurrence",
                        "ecog_performance_status", "state"],
    "table_molecular_test": ["molecular_test_id", "follow_up_id", "laboratory_test",
                             "test_value", "test_units", "test_result", "gene_symbol",
                             "molecular_analysis_method", "state"],
    "table_other_clinical_attribute": ["other_clinical_attribute_id", "follow_up_id",
                                       "weight", "height", "bmi", "timepoint_category",
                                       "state"],
    "table_exposure": ["exposure_id", "case_id", "exposure_type",
                       "tobacco_smoking_status", "pack_years_smoked", "alcohol_history",
                       "alcohol_intensity", "state"],
    "table_family_history": ["family_history_id", "case_id",
                             "relative_with_cancer_history",
                             "relatives_with_cancer_history_count",
                             "relationship_primary_diagnosis", "state"],
    "table_sample": ["sample_id", "case_id", "sample_type", "tissue_type",
                     "specimen_type", "tumor_descriptor", "preservation_method",
                     "created_datetime", "updated_datetime", "state"],
    "table_portion": ["portion_id", "sample_id", "portion_number", "weight", "is_ffpe"],
    "table_slide": ["slide_id", "portion_id", "section_location",
                    "percent_tumor_nuclei", "percent_tumor_cells", "percent_necrosis",
                    "created_datetime", "updated_datetime", "state"],
    "table_analyte": ["analyte_id", "portion_id", "analyte_type", "concentration",
                      "rna_integrity_number", "a260_a280_ratio",
                      "created_datetime", "updated_datetime", "state"],
    "table_aliquot": ["aliquot_id", "analyte_id", "analyte_type", "aliquot_quantity",
                      "aliquot_volume", "concentration", "source_center", "state"],
}


def pick(d, cols):
    return {c: d.get(c) for c in cols}


def main():
    out_dir = os.path.join(HERE, "relational")
    os.makedirs(out_dir, exist_ok=True)
    rows = {t: [] for t in COLUMNS}
    seen_project = set()

    for c in load_cases():
        pid = (c.get("project") or {}).get("project_id")
        if pid and pid not in seen_project:
            seen_project.add(pid)
            rows["table_project"].append({"project_id": pid, "project_name": None})
        cid = c["case_id"]
        rows["table_case"].append(pick({**c, "project_id": pid}, COLUMNS["table_case"]))

        dm = c.get("demographic") or {}
        if dm:
            rows["table_demographic"].append(pick({**dm, "case_id": cid},
                                                  COLUMNS["table_demographic"]))
        for d in c.get("diagnoses", []):
            rows["table_diagnosis"].append(pick({**d, "case_id": cid},
                                                COLUMNS["table_diagnosis"]))
            for t in d.get("treatments", []) or []:
                rows["table_treatment"].append(pick({**t, "diagnosis_id": d.get("diagnosis_id")},
                                                    COLUMNS["table_treatment"]))
            for pd in d.get("pathology_details", []) or []:
                rows["table_pathology_detail"].append(
                    pick({**pd, "diagnosis_id": d.get("diagnosis_id")},
                         COLUMNS["table_pathology_detail"]))
        for fu in c.get("follow_ups", []) or []:
            rows["table_follow_up"].append(pick({**fu, "case_id": cid},
                                                COLUMNS["table_follow_up"]))
            for mt in fu.get("molecular_tests", []) or []:
                rows["table_molecular_test"].append(
                    pick({**mt, "follow_up_id": fu.get("follow_up_id")},
                         COLUMNS["table_molecular_test"]))
            for oc in fu.get("other_clinical_attributes", []) or []:
                rows["table_other_clinical_attribute"].append(
                    pick({**oc, "follow_up_id": fu.get("follow_up_id")},
                         COLUMNS["table_other_clinical_attribute"]))
        for ex in c.get("exposures", []) or []:
            rows["table_exposure"].append(pick({**ex, "case_id": cid},
                                               COLUMNS["table_exposure"]))
        for fh in c.get("family_histories", []) or []:
            rows["table_family_history"].append(pick({**fh, "case_id": cid},
                                                     COLUMNS["table_family_history"]))
        for s in c.get("samples", []):
            rows["table_sample"].append(pick({**s, "case_id": cid},
                                             COLUMNS["table_sample"]))
            for p in s.get("portions", []) or []:
                rows["table_portion"].append(pick({**p, "sample_id": s.get("sample_id")},
                                                  COLUMNS["table_portion"]))
                for sl in p.get("slides", []) or []:
                    rows["table_slide"].append(pick({**sl, "portion_id": p.get("portion_id")},
                                                    COLUMNS["table_slide"]))
                for an in p.get("analytes", []) or []:
                    rows["table_analyte"].append(pick({**an, "portion_id": p.get("portion_id")},
                                                      COLUMNS["table_analyte"]))
                    for al in an.get("aliquots", []) or []:
                        rows["table_aliquot"].append(
                            pick({**al, "analyte_id": an.get("analyte_id")},
                                 COLUMNS["table_aliquot"]))

    for t, cols in COLUMNS.items():
        with open(os.path.join(out_dir, t + ".csv"), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            w.writerows(rows[t])
        print(f"{t:24} {len(rows[t]):>4} rows")
    print(f"total tables: {len(COLUMNS)}")


if __name__ == "__main__":
    main()
