// MongoDB has no schema catalog; scan the attribute keys of each document.
db.pitting_corrosion.aggregate([
  { $project: { ks: { $objectToArray: { $arrayElemAt: ["$content.result_characterization", 0] } } } },
  { $unwind: "$ks" },
  { $match: { "ks.k": { $regex: "protection_potential|repassivation_potential|hysteresis_loop" } } },
  { $group: { _id: "$ks.k" } }
])
