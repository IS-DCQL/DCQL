db.cases.aggregate([
  {
    $match: {
      "project.project_id": { $in: ["TCGA-KIRC", "TARGET-WT"] },
      $or: [
        // Case A: vital_status is on the demographic
        { "demographic.vital_status": "Dead" },
        // Case B: vital_status is on a diagnoses element (same element as primary_diagnosis)
        {
          diagnoses: {
            $elemMatch: {
              vital_status: "Dead",
              primary_diagnosis: { $regex: "renal cell carcinoma", $options: "i" }
            }
          }
        }
      ]
    }
  },

  { $unwind: "$samples" },
  {
    $match: {
      "samples.sample_type": "Primary Tumor",
      "samples.preservation_method": { $in: ["Snap Frozen", "Snap-Frozen", "OCT"] }
    }
  },

  { $unwind: "$samples.portions" },
  { $unwind: "$samples.portions.analytes" },
  { $unwind: "$samples.portions.analytes.aliquots" },

  // cast concentration to double to avoid string-comparison pitfalls
  {
    $addFields: {
      _conc: { $toDouble: "$samples.portions.analytes.aliquots.concentration" }
    }
  },
  {
    $match: {
      "samples.portions.analytes.analyte_type": "RNA",
      _conc: { $gt: 0.1 }
    }
  },

  {
    $project: {
      _id: 0,
      case_id: 1,
      aliquot_id: "$samples.portions.analytes.aliquots.aliquot_id",
      concentration: "$_conc"
    }
  },

  { $limit: 50 }
]);
