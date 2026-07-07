db.materials_library.aggregate([
  {
    $match: {
      "basic_info.category": "Semi-Aromatic",
      samples: { $elemMatch: { "thermal.glass_temperature": { $gt: 280 }, "mechanical.tensile_strength": { $gt: 150 } } }
    }
  },
  {
    $lookup: {
      from: "processing_logs",
      localField: "basic_info.name",
      foreignField: "material_name",
      as: "proc"
    }
  },
  { $unwind: "$proc" },
  { $match: { "proc.machine_settings.injection.stages": { $gt: 50 } } },
  {
    $project: {
      _id: 0,
      name: "$basic_info.name",
      glass_temperature: { $arrayElemAt: ["$samples.thermal.glass_temperature", 0] }
    }
  }
])
