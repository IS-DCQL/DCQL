for $d in json-doc("pitting_corrosion.json")[]
where number($d.content.solution_environment[[1]].NaCl_wt) = 3.5
  and number($d.content.experimental_conditions[[1]].temperature_c) = 20
  and number($d.content.result_characterization[[1]].pitting_potential_eb_v) > 1.0
  and number($d.content.material_performance[[1]].yield_strength_mpa) > 550
return $d.content.material_info[[1]].grade
