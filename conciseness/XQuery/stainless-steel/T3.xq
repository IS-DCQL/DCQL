for $d in db:open("pitting_corrosion")/json/_
where number($d/content/solution_environment/_/NaCl_wt) = 3.5
  and number($d/content/experimental_conditions/_/temperature_c) = 20
  and number($d/content/result_characterization/_/pitting_potential_eb_v) > 1.0
  and number($d/content/material_performance/_/yield_strength_mpa) > 550
return $d/content/material_info/_/grade
