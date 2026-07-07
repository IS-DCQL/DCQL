db.events.updateMany({}, [
  { $set: { particles: { $map: { input: "$particles", as: "p",
      in: { $mergeObjects: ["$$p", { pdg_id: "$$p.pid" }] } } } } },
  { $set: { particles: { $map: { input: "$particles", as: "p",
      in: { $arrayToObject: { $filter: { input: { $objectToArray: "$$p" },
            as: "f", cond: { $ne: ["$$f.k", "pid"] } } } } } } } }
])
