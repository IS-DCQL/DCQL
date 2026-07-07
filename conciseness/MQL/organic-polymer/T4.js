// glass_temperature lives inside each samples[] element, so the rename is a pipeline update.
db.materials_library.updateMany(
  { "samples.thermal.glass_temperature": { $exists: true } },
  [ { $set: { samples: { $map: { input: "$samples", as: "s", in: { $mergeObjects: [
        "$$s", { thermal: { $mergeObjects: [ "$$s.thermal",
          { Tg_DSC_Onset: "$$s.thermal.glass_temperature" } ] } } ] } } } } },
    { $unset: "samples.thermal.glass_temperature" } ]
)
