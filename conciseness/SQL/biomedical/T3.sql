SELECT DISTINCT
    c.case_id,
    c.project_id,
    d.primary_diagnosis,
    al.aliquot_id,
    al.concentration
FROM clinical.table_case c
JOIN clinical.table_diagnosis d
    ON c.case_id = d.case_id
JOIN clinical.table_demographic dm
    ON c.case_id = dm.case_id
JOIN clinical.table_sample s
    ON c.case_id = s.case_id
JOIN clinical.table_portion p
    ON s.sample_id = p.sample_id
JOIN clinical.table_analyte an
    ON p.portion_id = an.portion_id
JOIN clinical.table_aliquot al
    ON an.analyte_id = al.analyte_id
WHERE c.project_id IN ('TCGA-KIRC', 'TARGET-WT')
  AND d.primary_diagnosis LIKE '%Renal Cell Carcinoma%'
  AND dm.vital_status = 'Dead'
  AND s.sample_type = 'Primary Tumor'
  AND s.preservation_method IN ('Snap Frozen', 'OCT')
  AND al.analyte_type = 'RNA'
  AND al.concentration > 0.1;
