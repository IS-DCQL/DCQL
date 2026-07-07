SELECT DISTINCT table_name, column_name
FROM information_schema.columns
WHERE column_name LIKE '%protection_potential%'
   OR column_name LIKE '%repassivation_potential%'
   OR column_name LIKE '%hysteresis_loop%';
