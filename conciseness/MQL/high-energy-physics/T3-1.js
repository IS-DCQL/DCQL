db.events.aggregate([
  { $unwind: "$particles" },
  { $match: { "particles.pid": { $in: [11, -11] }, "particles.status": 1 } },
  { $project: { _id: 0, event_number: 1, particle_id: "$particles.id" } }
])
