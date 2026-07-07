# Final Examination — MQL (MongoDB)

Language category: Schema-less (MQL/N1QL/XQuery/JSONiq)  |  16 questions (10 query-writing + 3 query-reading + 3 result-prediction)  |  Total: 100 points

> Closed book; answer in plain text. Write each answer in MQL (MongoDB); for query-reading questions explain in English, and for result-prediction questions state the expected returned result.
> Each domain's teaching dataset (~20 core records) is provided with the paper under `dataset/<domain>/` (document form; the relational and object renderings of the same data are produced by the conciseness conversion scripts).

## Part 1 — Biomedical

This part concerns biomedical clinical and genomic data (from TCGA). In your storage each patient is a single nested document (collection `cases`) holding `demographic`, `diagnoses[]`, and `samples[] -> portions[] -> analytes[] -> aliquots[]`. Complete the following tasks against this document structure.

### Question 1.1  [Query Writing]

The database has no gene-variant information yet. For the patient with case_id="00016c8f-a0be-4319-9c42-4f3bcd90ac92", write its first gene-variant record (gene_name="TP53", variant_type="SNP", variant_allele_frequency=0.12, reference_genome_version="GRCh38") as an embedded array under that patient's document, thereby establishing the 1:N association.

(Write your answer here.)

### Question 1.2  [Query Writing]

For the patient with case_id="00016c8f-a0be-4319-9c42-4f3bcd90ac92", insert a new gene-variant record: gene_name="BRCA1", variant_type="INDEL", variant_allele_frequency=0.07, reference_genome_version="GRCh38".

(Write your answer here.)

### Question 1.3  [Query Writing]

The entity "Legacy_Risk_Factors" has been deprecated. Delete all legacy_risk_factors data from the database (delete data).

(Write your answer here.)

### Question 1.4  [Result Prediction]

Read the query below and, using this domain's teaching dataset provided with the paper (dataset/biomedical/), predict the result it returns (list the returned fields and the matching records):

```javascript
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
```

(Write your answer here.)

## Part 2 — Stainless Steel

This part concerns full-life-cycle experimental data for stainless steel (from NMDMS). The data is stored as collections/documents whose records cover composition, process, microstructure, and performance fields. Complete the following tasks against this data structure.

### Question 2.1  [Query Reading]

Read the statement below and explain, in English, the business operation it performs (including the role of each main clause/step):

```javascript
// MongoDB is schema-less: no schema definition is required. A PESR_HNS_Protocol
// document carries its nested composition / process / microstructure / performance
// fields and is created on first insert.
db.createCollection("pesr_hns_protocol")
```

(Write your answer here.)

### Question 2.2  [Query Writing]

Delete all G48_Immersion_Legacy data from the database.

(Write your answer here.)

### Question 2.3  [Query Writing]

Scan the data and find the collections/documents whose records carry fields such as "protection potential", "repassivation potential", or "hysteresis loop", and return them (a schema-less language cannot query the schema directly, so this is approximated by a data scan).

(Write your answer here.)

### Question 2.4  [Result Prediction]

Read the query below and, using this domain's teaching dataset provided with the paper (dataset/stainless-steel/), predict the result it returns (list the returned fields and the matching records):

```javascript
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
```

(Write your answer here.)

## Part 3 — Organic Polymer

This part concerns structure-processing-property data for organic polymers (polyamides, from NMDMS). The data is stored as document collections such as `materials_library` (materials) and `processing_logs` (processing, including `WAXD_result`). Complete the following tasks against this data structure.

### Question 3.1  [Query Writing]

Rename/migrate the "glass-transition temperature" field to "Tg_DSC_Onset" in place across all records (bulk data modification; a schema-less language cannot rename a schema).

(Write your answer here.)

### Question 3.2  [Query Reading]

Read the statement below and explain, in English, the business operation it performs (including the role of each main clause/step):

```javascript
db.processing_logs.updateOne(
  { "meta.data_id": 195540, "WAXD_result.alpha_crystallinity": { $gt: 100 } },
  { $set: { "WAXD_result.alpha_crystallinity": null } }
)
```

(Write your answer here.)

### Question 3.3  [Query Writing]

Scan the data and find the collections/documents whose records carry both a "SMILES code" field and a "thermal-decomposition temperature" field (a schema-less language cannot query the schema directly, so this is approximated by a data scan).

(Write your answer here.)

### Question 3.4  [Query Writing]

Query the semi-aromatic (Semi-Aromatic) polymer instances, join their associated processing data, and require glass-transition temperature (Tg) > 280C, tensile strength > 150 MPa, and the existence of an injection stage with speed > 50 mm/s. Return the material name and the related performance.

(Write your answer here.)

## Part 4 — High-Energy Physics

This part concerns high-energy-physics particle-collision event data (from CERN Open Data). The data is stored as the `events` document collection; each event holds a `particles[]` array, and a particle carries `pid`, `status`, `momentum`, and `parent_ids`/`child_ids` fields. Complete the following tasks against this data structure.

### Question 4.1  [Query Reading]

Read the statement below and explain, in English, the business operation it performs (including the role of each main clause/step):

```javascript
db.events.updateMany({}, [
  { $set: { particles: { $map: { input: "$particles", as: "p",
      in: { $mergeObjects: ["$$p", { pdg_id: "$$p.pid" }] } } } } },
  { $set: { particles: { $map: { input: "$particles", as: "p",
      in: { $arrayToObject: { $filter: { input: { $objectToArray: "$$p" },
            as: "f", cond: { $ne: ["$$f.k", "pid"] } } } } } } } }
])
```

(Write your answer here.)

### Question 4.2  [Query Writing]

Traverse the particle entities in every event and delete the particles with status != 1; after deletion, the parent_ids/child_ids associations among the remaining particles must remain consistent.

(Write your answer here.)

### Question 4.3  [Result Prediction]

Read the query below and, using this domain's teaching dataset provided with the paper (dataset/high-energy-physics/), predict the result it returns (list the returned fields and the matching records):

```javascript
db.events.aggregate([
  { $unwind: "$particles" },
  { $match: { "particles.pid": { $in: [11, -11] }, "particles.status": 1 } },
  { $project: { _id: 0, event_number: 1, particle_id: "$particles.id" } }
])
```

(Write your answer here.)

### Question 4.4  [Query Writing]

For each event, traverse all of its visible particles (status = 1), sum the p_x and p_y components of momentum separately to obtain the total transverse-momentum vector, and compute its magnitude (MET). Select and return the events with MET > 50000 MeV, labeled "anomalous high missing-energy events".

(Write your answer here.)
