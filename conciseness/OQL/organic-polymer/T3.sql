SELECT DISTINCT m.material_id, m.name, m.category
FROM public.materials m
WHERE m.category = 'Semi-Aromatic'
  AND m.glass_temperature > 280
  AND m.tensile_strength > 150
  AND EXISTS (SELECT 1 FROM public.processing_cases pc
              WHERE pc.material_id = m.material_id AND pc.speed > 50);
