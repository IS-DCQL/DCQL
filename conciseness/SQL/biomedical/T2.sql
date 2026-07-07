SELECT
    c.case_id,
    dm.gender,
    dm.race,
    d.primary_diagnosis
FROM clinical.table_case c
JOIN clinical.table_demographic dm
    ON c.case_id = dm.case_id
JOIN clinical.table_diagnosis d
    ON c.case_id = d.case_id
WHERE c.case_id = '00016c8f-a0be-4319-9c42-4f3bcd90ac92';
