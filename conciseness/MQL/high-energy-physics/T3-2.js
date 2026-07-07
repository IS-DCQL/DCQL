db.events.aggregate([
  { $unwind: "$particles" },
  { $match: { "particles.status": 1 } },
  { $group: { _id: "$event_number",
      sumPx: { $sum: "$particles.momentum.px" },
      sumPy: { $sum: "$particles.momentum.py" } } },
  { $project: { _id: 0, event_number: "$_id",
      met: { $sqrt: { $add: [ { $pow: ["$sumPx", 2] }, { $pow: ["$sumPy", 2] } ] } } } },
  { $match: { met: { $gt: 50000 } } }
])
