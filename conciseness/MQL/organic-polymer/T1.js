// MongoDB has no schema catalog; scan document keys to find collections whose
// records carry both attributes.
db.materials_library.aggregate([
  { $project: { has_smiles: { $ne: ["$basic_info.smiles", null] },
                has_decomp: { $anyElementTrue: { $map: { input: "$samples", as: "s", in: { $ne: ["$$s.thermal.thermal_decomposition", null] } } } } } },
  { $match: { has_smiles: true, has_decomp: true } },
  { $group: { _id: "materials_library" } }
])
