SELECT pe.exp_id, pe.grade
FROM pitting_experiment pe
JOIN solution_environment se   ON se.exp_id = pe.exp_id
JOIN experimental_condition ec ON ec.exp_id = pe.exp_id
JOIN corrosion_result cr       ON cr.exp_id = pe.exp_id
WHERE se.nacl_wt = 3.5
  AND ec.temperature_c = 20
  AND cr.pitting_potential_eb_v > 1.0
  AND pe.yield_strength_mpa > 550;
