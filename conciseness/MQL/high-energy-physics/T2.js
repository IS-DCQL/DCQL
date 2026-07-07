db.events.updateMany({}, [
  { $set: { particles: { $filter: { input: "$particles", as: "p", cond: { $eq: ["$$p.status", 1] } } } } },
  { $set: { _kept: "$particles.id" } },
  { $set: { particles: { $map: { input: "$particles", as: "p", in: { $mergeObjects: ["$$p", {
      parent_ids: { $setIntersection: ["$$p.parent_ids", "$_kept"] },
      child_ids:  { $setIntersection: ["$$p.child_ids",  "$_kept"] } }] } } } } },
  { $unset: "_kept" }
])
