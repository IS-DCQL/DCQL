# Answer Key & Grading Rubric — XQuery (BaseX)

Language category: Schema-less (MQL/N1QL/XQuery/JSONiq)

Grading uses the four error classes from §6.3: **S** syntax-structure, **L** semantic-logic, **V** numeric, **M** minor-language. The writing / reading / prediction sub-scores total 70 / 15 / 15.

## Part 1 — Biomedical

### Question 1.1  [Query Writing]

**Business intent:** Establish the gene-variant entity and its 1:N association to Case (schema-bearing: define the schema; schema-less: establish the structure implicitly through the first embedded record).

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```xquery
(: BaseX is schema-less: no schema definition is required. :)
(: A gene_variant element is simply inserted under its related case: :)
insert node
  <gene_variant>
    <gene_name>TP53</gene_name>
    <variant_type>SNP</variant_type>
    <variant_allele_frequency>0.12</variant_allele_frequency>
    <reference_genome_version>GRCh38</reference_genome_version>
  </gene_variant>
into db:open("tcga_cases")/json/_[case_id = "00016c8f-a0be-4319-9c42-4f3bcd90ac92"]
```

**Grading notes:** S: basic DDL/write form; L: incorrect 1:N modeling (not attached to Case); V: wrong field name/type; M: minor omissions such as a missing semicolon or bracket.

### Question 1.2  [Query Writing]

**Business intent:** Write one data record into the gene-variant entity established in Question 1.

**Reference answer (reference implementation):**
```xquery
insert node
  <gene_variant>
    <gene_name>BRCA1</gene_name>
    <variant_type>INDEL</variant_type>
    <variant_allele_frequency>0.07</variant_allele_frequency>
    <reference_genome_version>GRCh38</reference_genome_version>
  </gene_variant>
into db:open("tcga_cases")/json/_[case_id = "00016c8f-a0be-4319-9c42-4f3bcd90ac92"]
```

**Grading notes:** S: insert/write syntax; L: wrong target or association (not attached to the correct Case); V: wrong literal value (0.07); M: minor symbols.

### Question 1.3  [Query Writing]

**Business intent:** Retire Legacy_Risk_Factors (schema-bearing: drop the schema; schema-less: delete the data).

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```xquery
db:drop("legacy_risk_factors")
```

**Grading notes:** S: DROP/delete syntax; L: wrong deletion scope (too much / too little); V: entity-name spelling; M: minor symbols.

### Question 1.4  [Result Prediction]

**Business intent:** Complex multi-condition chained retrieval: project_id in {TCGA-KIRC, TARGET-WT}, and (demographic.vital_status = Dead, OR a diagnosis whose primary_diagnosis contains "Renal Cell Carcinoma" with vital_status = Dead), and Sample.sample_type = Primary Tumor with preservation_method in {Snap Frozen, OCT}, and a terminal Analyte with analyte_type = RNA and concentration > 0.1. Return the Case identifier, the available Aliquot_ID, and the corresponding RNA concentration.

**Expected result:** On the biomedical teaching dataset (20 records, see dataset/biomedical/), only the case case_id="28011111-4a01-4cdc-8d6b-7223fb2c501b" satisfies the full chain. The query returns that case and its two RNA aliquots: aliquot_id="19f0514a-35c8-4490-886f-1accf6ce4d9c" (concentration 0.17 ug/uL) and aliquot_id="957fa2bd-2222-43a4-b046-d2f78bf506a5" (concentration 0.17 ug/uL). The other 19 cases are excluded (wrong project_id, or the sample/analyte chain is not satisfied), so the result is exactly these two rows.

**Query shown on the paper (for reference):**
```xquery
for $c in db:open("tcga_cases")/json/_
where $c/project/project_id = ("TCGA-KIRC", "TARGET-WT")
  and $c/demographic/vital_status = "Dead"
  and (some $d in $c/diagnoses/_
       satisfies contains(string($d/primary_diagnosis), "Renal Cell Carcinoma"))
for $s in $c/samples/_
where $s/sample_type = "Primary Tumor"
  and $s/preservation_method = ("Snap Frozen", "OCT")
for $al in $s/portions/_/analytes/_[analyte_type = "RNA"]/aliquots/_
where $al/concentration > 0.1
return
  <result>
    <case_id>{ data($c/case_id) }</case_id>
    <aliquot_id>{ data($al/aliquot_id) }</aliquot_id>
    <concentration>{ data($al/concentration) }</concentration>
  </result>
```

**Grading notes:** Result-prediction: full credit for correctly listing all matching Cases with their Aliquot_IDs and concentrations; a missed or spurious row counts as L; a wrong value (e.g., concentration) counts as V.

## Part 2 — Stainless Steel

### Question 2.1  [Query Reading]

**Business intent:** Write the first record of the PESR_HNS_Protocol entity (a schema-less language establishes the structure implicitly through the data it writes).

**Statement shown on the paper (for reference):**
```xquery
db:create("pesr_hns_protocol",
  <protocol>
    <composition/>
    <process_parameters/>
    <microstructure/>
    <performance_indicators/>
  </protocol>,
  "pesr_hns_protocol.xml")
```

**Grading notes:** Query-reading: full credit for correctly stating that the statement builds/writes the PESR_HNS_Protocol structure and listing its four parts; misreading the operation (e.g., taking it for a query) counts as L; omitting a sub-structure counts as V.

### Question 2.2  [Query Writing]

**Business intent:** Retire G48_Immersion_Legacy (schema-bearing: drop the schema; schema-less: delete the data).

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```xquery
db:drop("G48_Immersion_Legacy")
```

**Grading notes:** S: delete syntax; L: wrong deletion scope; V: name spelling; M: minor symbols.

### Question 2.3  [Query Writing]

**Business intent:** Schema-level retrieval (schema-bearing: query the schema-library metadata; schema-less: approximate via a data scan): locate the schemas/collections that carry the above electrochemical attributes.

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```xquery
for $db in db:list()
for $n in db:open($db)//*[matches(name(), "protection_potential|repassivation_potential|hysteresis_loop")]
return <attr db="{ $db }">{ name($n) }</attr>
```

**Grading notes:** S: retrieval syntax; L: wrong condition logic (the "or" relation); V: attribute-name spelling; M: minor symbols.

### Question 2.4  [Result Prediction]

**Business intent:** Joint multi-group filter: environment (medium contains NaCl, concentration = 3.5%, temperature = 20C), corrosion resistance (pitting potential > 1000 mV), and mechanics (yield strength > 550 MPa).

**Expected result:** On the stainless-steel teaching dataset (20 records, see dataset/stainless-steel/), exactly two records satisfy all of the environmental, corrosion, and mechanical conditions: data_number="pitting_potential_2023_0187" (grade 2205, yield strength 615 MPa) and data_number="pitting_potential_2023_0188" (grade 2205, yield strength 580 MPa). The rest are excluded because the NaCl/temperature/pitting-potential conditions are not met or the yield strength is <= 550 MPa.

**Query shown on the paper (for reference):**
```xquery
for $d in db:open("pitting_corrosion")/json/_
where number($d/content/solution_environment/_/NaCl_wt) = 3.5
  and number($d/content/experimental_conditions/_/temperature_c) = 20
  and number($d/content/result_characterization/_/pitting_potential_eb_v) > 1.0
  and number($d/content/material_performance/_/yield_strength_mpa) > 550
return $d/content/material_info/_/grade
```

**Grading notes:** Result-prediction: full credit for listing all matching batches; a missed/spurious row counts as L; misreading a threshold or unit counts as V.

## Part 3 — Organic Polymer

### Question 3.1  [Query Writing]

**Business intent:** Rename an attribute (schema-bearing: change the schema definition; schema-less: bulk-rewrite the data field).

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```xquery
for $a in db:open("materials_library")//*[@key="glass_temperature"]/@key
return replace value of node $a with "Tg_DSC_Onset"
```

**Grading notes:** S: ALTER/rewrite syntax; L: incomplete migration (some records missed); V: old/new identifier spelling; M: minor symbols.

### Question 3.2  [Query Reading]

**Business intent:** Locate the anomalous WAXD record with data_id = 195540 whose alpha-crystallinity exceeds 100% (physically impossible) and null out that invalid crystallinity value (flagging it for re-measurement), fixing the data-quality problem.

**Statement shown on the paper (for reference):**
```xquery
for $a in db:get("processing_logs")//map[*[@key="data_id"]=195540]//number[@key="alpha_crystallinity"][. > 100]
return replace value of node $a with "NaN"
```

**Grading notes:** Query-reading: full credit for stating that it locates record 195540 with the anomalous crystallinity and nulls/fixes the invalid value; misreading the locate condition or the modified target counts as L; omitting the threshold condition counts as V.

### Question 3.3  [Query Writing]

**Business intent:** Schema-level retrieval (co-occurrence): locate the schemas/collections that declare both the SMILES-code and the thermal-decomposition-temperature attributes.

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```xquery
for $db in db:list()
where db:open($db)//map[*[@key="smiles"] and *[@key="thermal_decomposition"]]
return <schema>{ $db }</schema>
```

**Grading notes:** S: retrieval syntax; L: wrong co-occurrence (AND) logic; V: attribute-name spelling; M: minor symbols.

### Question 3.4  [Query Writing]

**Business intent:** Multi-dimensional joint filter across "material" and "processing", returning the joined result.

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```xquery
for $mat in db:get("materials_library")//map
for $proc in db:get("processing_logs")//map
where $mat//string[@key="name"] = $proc//string[@key="material_name"]
  and $mat//string[@key="category"] = "Semi-Aromatic"
  and $mat//number[@key="glass_temperature"] > 280
  and $mat//number[@key="tensile_strength"] > 150
  and (some $stage in $proc//number[@key="stages"] satisfies $stage > 50)
return
  <match>
    <material>{ $mat//string[@key="name"] }</material>
  </match>
```

**Grading notes:** S: query/join syntax; L: wrong join key or condition combination; V: wrong threshold (280/150/50); M: minor symbols.

## Part 4 — High-Energy Physics

### Question 4.1  [Query Reading]

**Business intent:** Bulk-rename/migrate the pid field to pdg_id across all particle records (a schema-less language realizes this by rewriting the data).

**Statement shown on the paper (for reference):**
```xquery
for $a in db:open("events")//particles/_/pid
return rename node $a as "pdg_id"
```

**Grading notes:** Query-reading: full credit for stating that it renames pid to pdg_id (schema-bearing: at the schema level; schema-less: per-record migration); misreading the modified target counts as L; spelling counts as V.

### Question 4.2  [Query Writing]

**Business intent:** Conditional delete with referential-integrity maintenance: delete particles with status != 1 and clean up the dangling parent_ids/child_ids references.

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```xquery
delete nodes db:open("events")//particles/_[status != 1]
(: then remove dangling parent/child id references among the remaining particles :)
```

**Grading notes:** S: delete/traversal syntax; L: integrity not maintained, or the delete condition inverted; V: wrong status value; M: minor symbols.

### Question 4.3  [Result Prediction]

**Business intent:** Within each event, select the particle entities with pid (or pdg_id) equal to 11 or -11 (electron/positron) and status = 1 (visible final state).

**Expected result:** On the high-energy-physics teaching dataset (20 events, see dataset/high-energy-physics/), every particle with pid in {11, -11} and status = 1 in each event is matched, 75 in total; the per-event match counts (by event number) are: 1:2, 2:4, 3:4, 4:11, 5:8, 6:2, 7:2, 8:4, 9:4, 10:2, 11:4, 12:2, 13:2, 14:4, 15:4, 16:2, 17:2, 18:2, 19:4, 20:6.

**Query shown on the paper (for reference):**
```xquery
for $e in db:open("events")/json/_
for $p in $e/particles/_
where ($p/pid = 11 or $p/pid = -11) and $p/status = 1
return <particle event="{ data($e/event_number) }">{ data($p/id) }</particle>
```

**Grading notes:** Result-prediction: full credit for listing the matching electron/positron particles per event; a missed/spurious match counts as L; misreading the pid value counts as V.

### Question 4.4  [Query Writing]

**Business intent:** Per-event aggregation of the transverse-momentum components of visible particles, computing the magnitude MET and filtering the events with MET > 50000 MeV.

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```xquery
for $e in db:open("events")/json/_
let $vis := $e/particles/_[status = 1]
let $met := math:sqrt(math:pow(sum($vis/momentum/px), 2) + math:pow(sum($vis/momentum/py), 2))
where $met > 50000
return <event id="{ data($e/event_number) }" met="{ $met }"/>
```

**Grading notes:** S: aggregation/grouping syntax; L: wrong aggregation scope (only status = 1) or magnitude computation; V: wrong threshold 50000; M: minor symbols.
