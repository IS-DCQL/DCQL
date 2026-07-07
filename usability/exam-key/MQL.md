# Answer Key & Grading Rubric — MQL (MongoDB)

Language category: Schema-less (MQL/N1QL/XQuery/JSONiq)

Grading uses the four error classes from §6.3: **S** syntax-structure, **L** semantic-logic, **V** numeric, **M** minor-language. The writing / reading / prediction sub-scores total 70 / 15 / 15.

## Part 1 — Biomedical

### Question 1.1  [Query Writing]

**Business intent:** Establish the gene-variant entity and its 1:N association to Case (schema-bearing: define the schema; schema-less: establish the structure implicitly through the first embedded record).

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```javascript
// MongoDB is schema-less: the gene_variant entity needs no schema definition.
// The 1:N link from a case is an embedded array, created on first insert:
db.cases.updateOne(
  { case_id: "00016c8f-a0be-4319-9c42-4f3bcd90ac92" },
  { $push: { gene_variants: {
      gene_name: "TP53",
      variant_type: "SNP",
      variant_allele_frequency: 0.12,
      reference_genome_version: "GRCh38"
  } } }
)
```

**Grading notes:** S: basic DDL/write form; L: incorrect 1:N modeling (not attached to Case); V: wrong field name/type; M: minor omissions such as a missing semicolon or bracket.

### Question 1.2  [Query Writing]

**Business intent:** Write one data record into the gene-variant entity established in Question 1.

**Reference answer (reference implementation):**
```javascript
db.cases.updateOne(
  { case_id: "00016c8f-a0be-4319-9c42-4f3bcd90ac92" },
  { $push: { gene_variants: {
      gene_name: "BRCA1", variant_type: "INDEL",
      variant_allele_frequency: 0.07, reference_genome_version: "GRCh38"
  } } }
)
```

**Grading notes:** S: insert/write syntax; L: wrong target or association (not attached to the correct Case); V: wrong literal value (0.07); M: minor symbols.

### Question 1.3  [Query Writing]

**Business intent:** Retire Legacy_Risk_Factors (schema-bearing: drop the schema; schema-less: delete the data).

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```javascript
db.legacy_risk_factors.drop()
```

**Grading notes:** S: DROP/delete syntax; L: wrong deletion scope (too much / too little); V: entity-name spelling; M: minor symbols.

### Question 1.4  [Result Prediction]

**Business intent:** Complex multi-condition chained retrieval: project_id in {TCGA-KIRC, TARGET-WT}, and (demographic.vital_status = Dead, OR a diagnosis whose primary_diagnosis contains "Renal Cell Carcinoma" with vital_status = Dead), and Sample.sample_type = Primary Tumor with preservation_method in {Snap Frozen, OCT}, and a terminal Analyte with analyte_type = RNA and concentration > 0.1. Return the Case identifier, the available Aliquot_ID, and the corresponding RNA concentration.

**Expected result:** On the biomedical teaching dataset (20 records, see dataset/biomedical/), only the case case_id="28011111-4a01-4cdc-8d6b-7223fb2c501b" satisfies the full chain. The query returns that case and its two RNA aliquots: aliquot_id="19f0514a-35c8-4490-886f-1accf6ce4d9c" (concentration 0.17 ug/uL) and aliquot_id="957fa2bd-2222-43a4-b046-d2f78bf506a5" (concentration 0.17 ug/uL). The other 19 cases are excluded (wrong project_id, or the sample/analyte chain is not satisfied), so the result is exactly these two rows.

**Query shown on the paper (for reference):**
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

**Grading notes:** Result-prediction: full credit for correctly listing all matching Cases with their Aliquot_IDs and concentrations; a missed or spurious row counts as L; a wrong value (e.g., concentration) counts as V.

## Part 2 — Stainless Steel

### Question 2.1  [Query Reading]

**Business intent:** Write the first record of the PESR_HNS_Protocol entity (a schema-less language establishes the structure implicitly through the data it writes).

**Statement shown on the paper (for reference):**
```javascript
// MongoDB is schema-less: no schema definition is required. A PESR_HNS_Protocol
// document carries its nested composition / process / microstructure / performance
// fields and is created on first insert.
db.createCollection("pesr_hns_protocol")
```

**Grading notes:** Query-reading: full credit for correctly stating that the statement builds/writes the PESR_HNS_Protocol structure and listing its four parts; misreading the operation (e.g., taking it for a query) counts as L; omitting a sub-structure counts as V.

### Question 2.2  [Query Writing]

**Business intent:** Retire G48_Immersion_Legacy (schema-bearing: drop the schema; schema-less: delete the data).

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```javascript
db.G48_Immersion_Legacy.drop()
```

**Grading notes:** S: delete syntax; L: wrong deletion scope; V: name spelling; M: minor symbols.

### Question 2.3  [Query Writing]

**Business intent:** Schema-level retrieval (schema-bearing: query the schema-library metadata; schema-less: approximate via a data scan): locate the schemas/collections that carry the above electrochemical attributes.

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```javascript
// MongoDB has no schema catalog; scan the attribute keys of each document.
db.pitting_corrosion.aggregate([
  { $project: { ks: { $objectToArray: { $arrayElemAt: ["$content.result_characterization", 0] } } } },
  { $unwind: "$ks" },
  { $match: { "ks.k": { $regex: "protection_potential|repassivation_potential|hysteresis_loop" } } },
  { $group: { _id: "$ks.k" } }
])
```

**Grading notes:** S: retrieval syntax; L: wrong condition logic (the "or" relation); V: attribute-name spelling; M: minor symbols.

### Question 2.4  [Result Prediction]

**Business intent:** Joint multi-group filter: environment (medium contains NaCl, concentration = 3.5%, temperature = 20C), corrosion resistance (pitting potential > 1000 mV), and mechanics (yield strength > 550 MPa).

**Expected result:** On the stainless-steel teaching dataset (20 records, see dataset/stainless-steel/), exactly two records satisfy all of the environmental, corrosion, and mechanical conditions: data_number="pitting_potential_2023_0187" (grade 2205, yield strength 615 MPa) and data_number="pitting_potential_2023_0188" (grade 2205, yield strength 580 MPa). The rest are excluded because the NaCl/temperature/pitting-potential conditions are not met or the yield strength is <= 550 MPa.

**Query shown on the paper (for reference):**
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

**Grading notes:** Result-prediction: full credit for listing all matching batches; a missed/spurious row counts as L; misreading a threshold or unit counts as V.

## Part 3 — Organic Polymer

### Question 3.1  [Query Writing]

**Business intent:** Rename an attribute (schema-bearing: change the schema definition; schema-less: bulk-rewrite the data field).

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```javascript
// glass_temperature lives inside each samples[] element, so the rename is a pipeline update.
db.materials_library.updateMany(
  { "samples.thermal.glass_temperature": { $exists: true } },
  [ { $set: { samples: { $map: { input: "$samples", as: "s", in: { $mergeObjects: [
        "$$s", { thermal: { $mergeObjects: [ "$$s.thermal",
          { Tg_DSC_Onset: "$$s.thermal.glass_temperature" } ] } } ] } } } } },
    { $unset: "samples.thermal.glass_temperature" } ]
)
```

**Grading notes:** S: ALTER/rewrite syntax; L: incomplete migration (some records missed); V: old/new identifier spelling; M: minor symbols.

### Question 3.2  [Query Reading]

**Business intent:** Locate the anomalous WAXD record with data_id = 195540 whose alpha-crystallinity exceeds 100% (physically impossible) and null out that invalid crystallinity value (flagging it for re-measurement), fixing the data-quality problem.

**Statement shown on the paper (for reference):**
```javascript
db.processing_logs.updateOne(
  { "meta.data_id": 195540, "WAXD_result.alpha_crystallinity": { $gt: 100 } },
  { $set: { "WAXD_result.alpha_crystallinity": null } }
)
```

**Grading notes:** Query-reading: full credit for stating that it locates record 195540 with the anomalous crystallinity and nulls/fixes the invalid value; misreading the locate condition or the modified target counts as L; omitting the threshold condition counts as V.

### Question 3.3  [Query Writing]

**Business intent:** Schema-level retrieval (co-occurrence): locate the schemas/collections that declare both the SMILES-code and the thermal-decomposition-temperature attributes.

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```javascript
// MongoDB has no schema catalog; scan document keys to find collections whose
// records carry both attributes.
db.materials_library.aggregate([
  { $project: { has_smiles: { $ne: ["$basic_info.smiles", null] },
                has_decomp: { $anyElementTrue: { $map: { input: "$samples", as: "s", in: { $ne: ["$$s.thermal.thermal_decomposition", null] } } } } } },
  { $match: { has_smiles: true, has_decomp: true } },
  { $group: { _id: "materials_library" } }
])
```

**Grading notes:** S: retrieval syntax; L: wrong co-occurrence (AND) logic; V: attribute-name spelling; M: minor symbols.

### Question 3.4  [Query Writing]

**Business intent:** Multi-dimensional joint filter across "material" and "processing", returning the joined result.

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```javascript
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
```

**Grading notes:** S: query/join syntax; L: wrong join key or condition combination; V: wrong threshold (280/150/50); M: minor symbols.

## Part 4 — High-Energy Physics

### Question 4.1  [Query Reading]

**Business intent:** Bulk-rename/migrate the pid field to pdg_id across all particle records (a schema-less language realizes this by rewriting the data).

**Statement shown on the paper (for reference):**
```javascript
db.events.updateMany({}, [
  { $set: { particles: { $map: { input: "$particles", as: "p",
      in: { $mergeObjects: ["$$p", { pdg_id: "$$p.pid" }] } } } } },
  { $set: { particles: { $map: { input: "$particles", as: "p",
      in: { $arrayToObject: { $filter: { input: { $objectToArray: "$$p" },
            as: "f", cond: { $ne: ["$$f.k", "pid"] } } } } } } } }
])
```

**Grading notes:** Query-reading: full credit for stating that it renames pid to pdg_id (schema-bearing: at the schema level; schema-less: per-record migration); misreading the modified target counts as L; spelling counts as V.

### Question 4.2  [Query Writing]

**Business intent:** Conditional delete with referential-integrity maintenance: delete particles with status != 1 and clean up the dangling parent_ids/child_ids references.

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```javascript
db.events.updateMany({}, [
  { $set: { particles: { $filter: { input: "$particles", as: "p", cond: { $eq: ["$$p.status", 1] } } } } },
  { $set: { _kept: "$particles.id" } },
  { $set: { particles: { $map: { input: "$particles", as: "p", in: { $mergeObjects: ["$$p", {
      parent_ids: { $setIntersection: ["$$p.parent_ids", "$_kept"] },
      child_ids:  { $setIntersection: ["$$p.child_ids",  "$_kept"] } }] } } } } },
  { $unset: "_kept" }
])
```

**Grading notes:** S: delete/traversal syntax; L: integrity not maintained, or the delete condition inverted; V: wrong status value; M: minor symbols.

### Question 4.3  [Result Prediction]

**Business intent:** Within each event, select the particle entities with pid (or pdg_id) equal to 11 or -11 (electron/positron) and status = 1 (visible final state).

**Expected result:** On the high-energy-physics teaching dataset (20 events, see dataset/high-energy-physics/), every particle with pid in {11, -11} and status = 1 in each event is matched, 75 in total; the per-event match counts (by event number) are: 1:2, 2:4, 3:4, 4:11, 5:8, 6:2, 7:2, 8:4, 9:4, 10:2, 11:4, 12:2, 13:2, 14:4, 15:4, 16:2, 17:2, 18:2, 19:4, 20:6.

**Query shown on the paper (for reference):**
```javascript
db.events.aggregate([
  { $unwind: "$particles" },
  { $match: { "particles.pid": { $in: [11, -11] }, "particles.status": 1 } },
  { $project: { _id: 0, event_number: 1, particle_id: "$particles.id" } }
])
```

**Grading notes:** Result-prediction: full credit for listing the matching electron/positron particles per event; a missed/spurious match counts as L; misreading the pid value counts as V.

### Question 4.4  [Query Writing]

**Business intent:** Per-event aggregation of the transverse-momentum components of visible particles, computing the magnitude MET and filtering the events with MET > 50000 MeV.

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```javascript
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
```

**Grading notes:** S: aggregation/grouping syntax; L: wrong aggregation scope (only status = 1) or magnitude computation; V: wrong threshold 50000; M: minor symbols.
