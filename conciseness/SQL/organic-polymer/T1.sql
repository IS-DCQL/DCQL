SELECT DISTINCT c1.table_schema, c1.table_name
FROM information_schema.columns c1
JOIN information_schema.columns c2
  ON c1.table_schema = c2.table_schema AND c1.table_name = c2.table_name
WHERE c1.column_name ILIKE '%smiles%'
  AND c2.column_name ILIKE '%thermal_decomposition%';
