db.pitting_corrosion.aggregate([
  { $unwind: "$content.solution_environment" },
  { $unwind: "$content.experimental_conditions" },
  { $unwind: "$content.result_characterization" },
  { $unwind: "$content.material_performance" },
  { $unwind: "$content.material_info" },
  { $match: { $expr: { $and: [
      { $eq: [ { $toDouble: "$content.solution_environment.NaCl_wt" }, 3.5 ] },
      { $eq: [ { $toDouble: "$content.experimental_conditions.temperature_c" }, 20 ] },
      { $gt: [ { $toDouble: "$content.result_characterization.pitting_potential_eb_v" }, 1.0 ] },
      { $gt: [ { $toDouble: "$content.material_performance.yield_strength_mpa" }, 550 ] }
  ] } } },
  { $project: { _id: 0, grade: "$content.material_info.grade" } }
])
