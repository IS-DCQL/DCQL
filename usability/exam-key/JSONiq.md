# Answer Key & Grading Rubric — JSONiq (RumbleDB)

Language category: Schema-less (MQL/N1QL/XQuery/JSONiq)

Grading uses the four error classes from §6.3: **S** syntax-structure, **L** semantic-logic, **V** numeric, **M** minor-language. The writing / reading / prediction sub-scores total 70 / 15 / 15.

## Part 1 — Biomedical

### Question 1.1  [Query Writing]

**Business intent:** Establish the gene-variant entity and its 1:N association to Case (schema-bearing: define the schema; schema-less: establish the structure implicitly through the first embedded record).

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```xquery
(: Establish the gene_variant 1:N set as an embedded array on each case. :)
for $c in json-doc("cases.json")[]
return {| $c, { "gene_variants": [] } |}
```

**Grading notes:** S: basic DDL/write form; L: incorrect 1:N modeling (not attached to Case); V: wrong field name/type; M: minor omissions such as a missing semicolon or bracket.

### Question 1.2  [Query Writing]

**Business intent:** Write one data record into the gene-variant entity established in Question 1.

**Reference answer (reference implementation):**
```xquery
for $c in json-doc("cases.json")[]
return if ($c.case_id eq "00016c8f-a0be-4319-9c42-4f3bcd90ac92")
       then {| $c, { "gene_variants": [ $c.gene_variants[],
              {"gene_name":"BRCA1","variant_type":"INDEL","variant_allele_frequency":0.07,"reference_genome_version":"GRCh38"} ] } |}
       else $c
```

**Grading notes:** S: insert/write syntax; L: wrong target or association (not attached to the correct Case); V: wrong literal value (0.07); M: minor symbols.

### Question 1.3  [Query Writing]

**Business intent:** Retire Legacy_Risk_Factors (schema-bearing: drop the schema; schema-less: delete the data).

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```xquery
(: Remove the Legacy_Risk_Factors entity by rewriting each case without that field. :)
for $c in json-doc("cases.json")[]
return {| { for $k in keys($c) where $k ne "legacy_risk_factors" return { $k : $c.$k } } |}
```

**Grading notes:** S: DROP/delete syntax; L: wrong deletion scope (too much / too little); V: entity-name spelling; M: minor symbols.

### Question 1.4  [Result Prediction]

**Business intent:** Complex multi-condition chained retrieval: project_id in {TCGA-KIRC, TARGET-WT}, and (demographic.vital_status = Dead, OR a diagnosis whose primary_diagnosis contains "Renal Cell Carcinoma" with vital_status = Dead), and Sample.sample_type = Primary Tumor with preservation_method in {Snap Frozen, OCT}, and a terminal Analyte with analyte_type = RNA and concentration > 0.1. Return the Case identifier, the available Aliquot_ID, and the corresponding RNA concentration.

**Expected result:** On the biomedical teaching dataset (20 records, see dataset/biomedical/), only the case case_id="28011111-4a01-4cdc-8d6b-7223fb2c501b" satisfies the full chain. The query returns that case and its two RNA aliquots: aliquot_id="19f0514a-35c8-4490-886f-1accf6ce4d9c" (concentration 0.17 ug/uL) and aliquot_id="957fa2bd-2222-43a4-b046-d2f78bf506a5" (concentration 0.17 ug/uL). The other 19 cases are excluded (wrong project_id, or the sample/analyte chain is not satisfied), so the result is exactly these two rows.

**Query shown on the paper (for reference):**
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

**Grading notes:** Result-prediction: full credit for correctly listing all matching Cases with their Aliquot_IDs and concentrations; a missed or spurious row counts as L; a wrong value (e.g., concentration) counts as V.

## Part 2 — Stainless Steel

### Question 2.1  [Query Reading]

**Business intent:** Write the first record of the PESR_HNS_Protocol entity (a schema-less language establishes the structure implicitly through the data it writes).

**Statement shown on the paper (for reference):**
```xquery
(: Schema-less: the PESR_HNS_Protocol entity is established by writing its structure. :)
{ "protocol_id": "",
  "composition": [],
  "process_parameters": [],
  "microstructure": [],
  "performance_indicators": [] }
```

**Grading notes:** Query-reading: full credit for correctly stating that the statement builds/writes the PESR_HNS_Protocol structure and listing its four parts; misreading the operation (e.g., taking it for a query) counts as L; omitting a sub-structure counts as V.

### Question 2.2  [Query Writing]

**Business intent:** Retire G48_Immersion_Legacy (schema-bearing: drop the schema; schema-less: delete the data).

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```xquery
(: RumbleDB is read-only and has no drop-collection statement; the G48_Immersion_Legacy
   collection (a JSON file) is removed at the storage layer. :)
for $d in json-doc("g48_immersion_legacy.json")[]
where false
return $d
```

**Grading notes:** S: delete syntax; L: wrong deletion scope; V: name spelling; M: minor symbols.

### Question 2.3  [Query Writing]

**Business intent:** Schema-level retrieval (schema-bearing: query the schema-library metadata; schema-less: approximate via a data scan): locate the schemas/collections that carry the above electrochemical attributes.

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```xquery
for $doc in json-doc("pitting_corrosion.json")[]
for $k in keys($doc.content.result_characterization[[1]])
where contains($k, "protection_potential") or contains($k, "repassivation_potential") or contains($k, "hysteresis_loop")
return { "attribute": $k }
```

**Grading notes:** S: retrieval syntax; L: wrong condition logic (the "or" relation); V: attribute-name spelling; M: minor symbols.

### Question 2.4  [Result Prediction]

**Business intent:** Joint multi-group filter: environment (medium contains NaCl, concentration = 3.5%, temperature = 20C), corrosion resistance (pitting potential > 1000 mV), and mechanics (yield strength > 550 MPa).

**Expected result:** On the stainless-steel teaching dataset (20 records, see dataset/stainless-steel/), exactly two records satisfy all of the environmental, corrosion, and mechanical conditions: data_number="pitting_potential_2023_0187" (grade 2205, yield strength 615 MPa) and data_number="pitting_potential_2023_0188" (grade 2205, yield strength 580 MPa). The rest are excluded because the NaCl/temperature/pitting-potential conditions are not met or the yield strength is <= 550 MPa.

**Query shown on the paper (for reference):**
```xquery
for $d in json-doc("pitting_corrosion.json")[]
where number($d.content.solution_environment[[1]].NaCl_wt) = 3.5
  and number($d.content.experimental_conditions[[1]].temperature_c) = 20
  and number($d.content.result_characterization[[1]].pitting_potential_eb_v) > 1.0
  and number($d.content.material_performance[[1]].yield_strength_mpa) > 550
return $d.content.material_info[[1]].grade
```

**Grading notes:** Result-prediction: full credit for listing all matching batches; a missed/spurious row counts as L; misreading a threshold or unit counts as V.

## Part 3 — Organic Polymer

### Question 3.1  [Query Writing]

**Business intent:** Rename an attribute (schema-bearing: change the schema definition; schema-less: bulk-rewrite the data field).

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```xquery
(: RumbleDB/JSONiq is read-only: renaming the glass-temperature attribute is done by
   rewriting each document, projecting the value onto the new key "Tg_DSC_Onset". :)
for $doc in json-doc("materials_library.json")[]
return {| { "basic_info": $doc.basic_info },
          { "samples": [ for $s in $doc.samples[]
              return {| { "Tg_DSC_Onset": $s.thermal.glass_temperature },
                        { for $k in keys($s.thermal) where $k ne "glass_temperature"
                          return { $k: $s.thermal.$k } } |} ] } |}
```

**Grading notes:** S: ALTER/rewrite syntax; L: incomplete migration (some records missed); V: old/new identifier spelling; M: minor symbols.

### Question 3.2  [Query Reading]

**Business intent:** Locate the anomalous WAXD record with data_id = 195540 whose alpha-crystallinity exceeds 100% (physically impossible) and null out that invalid crystallinity value (flagging it for re-measurement), fixing the data-quality problem.

**Statement shown on the paper (for reference):**
```xquery
for $doc in json-doc("processing_logs.json")[]
return if ($doc.meta.data_id eq 195540 and $doc.WAXD_result.alpha_crystallinity gt 100)
       then {| $doc, { "WAXD_result": {| $doc.WAXD_result, { "alpha_crystallinity": null } |} } |}
       else $doc
```

**Grading notes:** Query-reading: full credit for stating that it locates record 195540 with the anomalous crystallinity and nulls/fixes the invalid value; misreading the locate condition or the modified target counts as L; omitting the threshold condition counts as V.

### Question 3.3  [Query Writing]

**Business intent:** Schema-level retrieval (co-occurrence): locate the schemas/collections that declare both the SMILES-code and the thermal-decomposition-temperature attributes.

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```xquery
for $doc in json-doc("materials_library.json")[]
where (some $k in keys($doc.basic_info) satisfies $k = "smiles")
  and (some $s in $doc.samples[] satisfies
       (some $k in keys($s.thermal) satisfies $k = "thermal_decomposition"))
return { "schema": "materials_library", "id": $doc.basic_info.pid }
```

**Grading notes:** S: retrieval syntax; L: wrong co-occurrence (AND) logic; V: attribute-name spelling; M: minor symbols.

### Question 3.4  [Query Writing]

**Business intent:** Multi-dimensional joint filter across "material" and "processing", returning the joined result.

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```xquery
for $mat in json-doc("materials_library.json")[]
for $proc in json-doc("processing_logs.json")[]
where $mat.basic_info.name = $proc.material_name
  and $mat.basic_info.category = "Semi-Aromatic"
  and (some $s in $mat.samples[] satisfies
       $s.thermal.glass_temperature > 280 and $s.mechanical.tensile_strength > 150)
  and (some $stage in $proc.machine_settings.injection.stages[] satisfies $stage > 50)
return {
  "match": {
    "material": $mat.basic_info.name
  }
}
```

**Grading notes:** S: query/join syntax; L: wrong join key or condition combination; V: wrong threshold (280/150/50); M: minor symbols.

## Part 4 — High-Energy Physics

### Question 4.1  [Query Reading]

**Business intent:** Bulk-rename/migrate the pid field to pdg_id across all particle records (a schema-less language realizes this by rewriting the data).

**Statement shown on the paper (for reference):**
```xquery
(: RumbleDB/JSONiq is read-only: rename pid -> pdg_id by rewriting each particle. :)
for $e in json-doc("events.json")[]
return {| { "event_number": $e.event_number },
  { "particles": [ for $p in $e.particles[] return {| { "pdg_id": $p.pid },
      { for $k in keys($p) where $k ne "pid" return { $k : $p.$k } } |} ] } |}
```

**Grading notes:** Query-reading: full credit for stating that it renames pid to pdg_id (schema-bearing: at the schema level; schema-less: per-record migration); misreading the modified target counts as L; spelling counts as V.

### Question 4.2  [Query Writing]

**Business intent:** Conditional delete with referential-integrity maintenance: delete particles with status != 1 and clean up the dangling parent_ids/child_ids references.

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```xquery
(: RumbleDB/JSONiq is read-only: keep only status = 1 particles and drop dangling
   parent/child references, by rewriting each event. :)
for $e in json-doc("events.json")[]
let $kept := $e.particles[][$$.status = 1]
let $ids := [ $kept.id ]
return { "event_number": $e.event_number,
  "particles": [ for $p in $kept return {
      "id": $p.id, "pid": $p.pid, "status": $p.status, "mass": $p.mass, "momentum": $p.momentum,
      "parent_ids": [ $p.parent_ids[][. = $ids[]] ],
      "child_ids":  [ $p.child_ids[][. = $ids[]] ] } ] }
```

**Grading notes:** S: delete/traversal syntax; L: integrity not maintained, or the delete condition inverted; V: wrong status value; M: minor symbols.

### Question 4.3  [Result Prediction]

**Business intent:** Within each event, select the particle entities with pid (or pdg_id) equal to 11 or -11 (electron/positron) and status = 1 (visible final state).

**Expected result:** On the high-energy-physics teaching dataset (20 events, see dataset/high-energy-physics/), every particle with pid in {11, -11} and status = 1 in each event is matched, 75 in total; the per-event match counts (by event number) are: 1:2, 2:4, 3:4, 4:11, 5:8, 6:2, 7:2, 8:4, 9:4, 10:2, 11:4, 12:2, 13:2, 14:4, 15:4, 16:2, 17:2, 18:2, 19:4, 20:6.

**Query shown on the paper (for reference):**
```xquery
for $e in json-doc("events.json")[]
for $p in $e.particles[]
where ($p.pid = 11 or $p.pid = -11) and $p.status = 1
return { "event_number": $e.event_number, "particle_id": $p.id }
```

**Grading notes:** Result-prediction: full credit for listing the matching electron/positron particles per event; a missed/spurious match counts as L; misreading the pid value counts as V.

### Question 4.4  [Query Writing]

**Business intent:** Per-event aggregation of the transverse-momentum components of visible particles, computing the magnitude MET and filtering the events with MET > 50000 MeV.

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```xquery
for $e in json-doc("events.json")[]
let $vis := $e.particles[][$$.status = 1]
let $sumpx := sum($vis.momentum.px)
let $sumpy := sum($vis.momentum.py)
where $sumpx * $sumpx + $sumpy * $sumpy > 50000 * 50000
return { "event_number": $e.event_number,
         "met": $sumpx * $sumpx + $sumpy * $sumpy }
```

**Grading notes:** S: aggregation/grouping syntax; L: wrong aggregation scope (only status = 1) or magnitude computation; V: wrong threshold 50000; M: minor symbols.
