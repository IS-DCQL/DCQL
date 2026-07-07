# Final Examination — JSONiq (RumbleDB)

Language category: Schema-less (MQL/N1QL/XQuery/JSONiq)  |  16 questions (10 query-writing + 3 query-reading + 3 result-prediction)  |  Total: 100 points

> Closed book; answer in plain text. Write each answer in JSONiq (RumbleDB); for query-reading questions explain in English, and for result-prediction questions state the expected returned result.
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

```xquery
for $c in json-doc("cases.json")[]
where ($c.project.project_id = "TCGA-KIRC" or $c.project.project_id = "TARGET-WT")
  and (some $d in $c.diagnoses[]
       satisfies contains($d.primary_diagnosis, "Renal Cell Carcinoma"))
  and $c.demographic.vital_status = "Dead"
for $s in $c.samples[]
where $s.sample_type = "Primary Tumor"
  and ($s.preservation_method = "Snap Frozen" or $s.preservation_method = "OCT")
for $al in $s.portions[].analytes[]
where $al.analyte_type = "RNA"
for $aq in $al.aliquots[]
where $aq.concentration > 0.1
return {
  "case_id": $c.case_id,
  "aliquot_id": $aq.aliquot_id,
  "concentration": $aq.concentration
}
```

(Write your answer here.)

## Part 2 — Stainless Steel

This part concerns full-life-cycle experimental data for stainless steel (from NMDMS). The data is stored as collections/documents whose records cover composition, process, microstructure, and performance fields. Complete the following tasks against this data structure.

### Question 2.1  [Query Reading]

Read the statement below and explain, in English, the business operation it performs (including the role of each main clause/step):

```xquery
(: Schema-less: the PESR_HNS_Protocol entity is established by writing its structure. :)
{ "protocol_id": "",
  "composition": [],
  "process_parameters": [],
  "microstructure": [],
  "performance_indicators": [] }
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

```xquery
for $d in json-doc("pitting_corrosion.json")[]
where number($d.content.solution_environment[[1]].NaCl_wt) = 3.5
  and number($d.content.experimental_conditions[[1]].temperature_c) = 20
  and number($d.content.result_characterization[[1]].pitting_potential_eb_v) > 1.0
  and number($d.content.material_performance[[1]].yield_strength_mpa) > 550
return $d.content.material_info[[1]].grade
```

(Write your answer here.)

## Part 3 — Organic Polymer

This part concerns structure-processing-property data for organic polymers (polyamides, from NMDMS). The data is stored as document collections such as `materials_library` (materials) and `processing_logs` (processing, including `WAXD_result`). Complete the following tasks against this data structure.

### Question 3.1  [Query Writing]

Rename/migrate the "glass-transition temperature" field to "Tg_DSC_Onset" in place across all records (bulk data modification; a schema-less language cannot rename a schema).

(Write your answer here.)

### Question 3.2  [Query Reading]

Read the statement below and explain, in English, the business operation it performs (including the role of each main clause/step):

```xquery
for $doc in json-doc("processing_logs.json")[]
return if ($doc.meta.data_id eq 195540 and $doc.WAXD_result.alpha_crystallinity gt 100)
       then {| $doc, { "WAXD_result": {| $doc.WAXD_result, { "alpha_crystallinity": null } |} } |}
       else $doc
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

```xquery
(: RumbleDB/JSONiq is read-only: rename pid -> pdg_id by rewriting each particle. :)
for $e in json-doc("events.json")[]
return {| { "event_number": $e.event_number },
  { "particles": [ for $p in $e.particles[] return {| { "pdg_id": $p.pid },
      { for $k in keys($p) where $k ne "pid" return { $k : $p.$k } } |} ] } |}
```

(Write your answer here.)

### Question 4.2  [Query Writing]

Traverse the particle entities in every event and delete the particles with status != 1; after deletion, the parent_ids/child_ids associations among the remaining particles must remain consistent.

(Write your answer here.)

### Question 4.3  [Result Prediction]

Read the query below and, using this domain's teaching dataset provided with the paper (dataset/high-energy-physics/), predict the result it returns (list the returned fields and the matching records):

```xquery
for $e in json-doc("events.json")[]
for $p in $e.particles[]
where ($p.pid = 11 or $p.pid = -11) and $p.status = 1
return { "event_number": $e.event_number, "particle_id": $p.id }
```

(Write your answer here.)

### Question 4.4  [Query Writing]

For each event, traverse all of its visible particles (status = 1), sum the p_x and p_y components of momentum separately to obtain the total transverse-momentum vector, and compute its magnitude (MET). Select and return the events with MET > 50000 MeV, labeled "anomalous high missing-energy events".

(Write your answer here.)
