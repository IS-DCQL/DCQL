# Answer Key & Grading Rubric — SQL (PostgreSQL)

Language category: Schema-bearing (DCQL/SQL/OQL)

Grading uses the four error classes from §6.3: **S** syntax-structure, **L** semantic-logic, **V** numeric, **M** minor-language. The writing / reading / prediction sub-scores total 70 / 15 / 15.

## Part 1 — Biomedical

### Question 1.1  [Query Writing]

**Business intent:** Establish the gene-variant entity and its 1:N association to Case (schema-bearing: define the schema; schema-less: establish the structure implicitly through the first embedded record).

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```sql
CREATE TABLE clinical.gene_variant (
    variant_id                VARCHAR PRIMARY KEY,
    case_id                   VARCHAR NOT NULL REFERENCES clinical.table_case(case_id),
    gene_name                 VARCHAR,
    variant_type              VARCHAR,
    variant_allele_frequency  NUMERIC,
    reference_genome_version  VARCHAR
);
```

**Grading notes:** S: basic DDL/write form; L: incorrect 1:N modeling (not attached to Case); V: wrong field name/type; M: minor omissions such as a missing semicolon or bracket.

### Question 1.2  [Query Writing]

**Business intent:** Write one data record into the gene-variant entity established in Question 1.

**Reference answer (reference implementation):**
```sql
INSERT INTO clinical.gene_variant
    (variant_id, case_id, gene_name, variant_type, variant_allele_frequency, reference_genome_version)
VALUES ('GV-0001', '00016c8f-a0be-4319-9c42-4f3bcd90ac92', 'BRCA1', 'INDEL', 0.07, 'GRCh38');
```

**Grading notes:** S: insert/write syntax; L: wrong target or association (not attached to the correct Case); V: wrong literal value (0.07); M: minor symbols.

### Question 1.3  [Query Writing]

**Business intent:** Retire Legacy_Risk_Factors (schema-bearing: drop the schema; schema-less: delete the data).

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```sql
DROP TABLE clinical.legacy_risk_factors;
```

**Grading notes:** S: DROP/delete syntax; L: wrong deletion scope (too much / too little); V: entity-name spelling; M: minor symbols.

### Question 1.4  [Result Prediction]

**Business intent:** Complex multi-condition chained retrieval: project_id in {TCGA-KIRC, TARGET-WT}, and (demographic.vital_status = Dead, OR a diagnosis whose primary_diagnosis contains "Renal Cell Carcinoma" with vital_status = Dead), and Sample.sample_type = Primary Tumor with preservation_method in {Snap Frozen, OCT}, and a terminal Analyte with analyte_type = RNA and concentration > 0.1. Return the Case identifier, the available Aliquot_ID, and the corresponding RNA concentration.

**Expected result:** On the biomedical teaching dataset (20 records, see dataset/biomedical/), only the case case_id="28011111-4a01-4cdc-8d6b-7223fb2c501b" satisfies the full chain. The query returns that case and its two RNA aliquots: aliquot_id="19f0514a-35c8-4490-886f-1accf6ce4d9c" (concentration 0.17 ug/uL) and aliquot_id="957fa2bd-2222-43a4-b046-d2f78bf506a5" (concentration 0.17 ug/uL). The other 19 cases are excluded (wrong project_id, or the sample/analyte chain is not satisfied), so the result is exactly these two rows.

**Query shown on the paper (for reference):**
```sql
SELECT DISTINCT
    c.case_id,
    c.project_id,
    d.primary_diagnosis,
    al.aliquot_id,
    al.concentration
FROM clinical.table_case c
JOIN clinical.table_diagnosis d
    ON c.case_id = d.case_id
JOIN clinical.table_demographic dm
    ON c.case_id = dm.case_id
JOIN clinical.table_sample s
    ON c.case_id = s.case_id
JOIN clinical.table_portion p
    ON s.sample_id = p.sample_id
JOIN clinical.table_analyte an
    ON p.portion_id = an.portion_id
JOIN clinical.table_aliquot al
    ON an.analyte_id = al.analyte_id
WHERE c.project_id IN ('TCGA-KIRC', 'TARGET-WT')
  AND d.primary_diagnosis LIKE '%Renal Cell Carcinoma%'
  AND dm.vital_status = 'Dead'
  AND s.sample_type = 'Primary Tumor'
  AND s.preservation_method IN ('Snap Frozen', 'OCT')
  AND al.analyte_type = 'RNA'
  AND al.concentration > 0.1;
```

**Grading notes:** Result-prediction: full credit for correctly listing all matching Cases with their Aliquot_IDs and concentrations; a missed or spurious row counts as L; a wrong value (e.g., concentration) counts as V.

## Part 2 — Stainless Steel

### Question 2.1  [Query Reading]

**Business intent:** Create a new entity schema named PESR_HNS_Protocol with four parts: composition system, process parameters, microstructure, and performance indicators.

**Statement shown on the paper (for reference):**
```sql
CREATE TABLE pesr_hns_protocol (
    protocol_id VARCHAR PRIMARY KEY,
    grade       VARCHAR
);
CREATE TABLE composition (
    protocol_id VARCHAR REFERENCES pesr_hns_protocol(protocol_id),
    element VARCHAR, content NUMERIC, unit VARCHAR DEFAULT '%'
);
CREATE TABLE process_parameter (
    protocol_id VARCHAR REFERENCES pesr_hns_protocol(protocol_id),
    name VARCHAR, value VARCHAR
);
CREATE TABLE microstructure (
    protocol_id VARCHAR REFERENCES pesr_hns_protocol(protocol_id),
    description VARCHAR
);
CREATE TABLE performance_indicator (
    protocol_id VARCHAR REFERENCES pesr_hns_protocol(protocol_id),
    name VARCHAR, value NUMERIC, unit VARCHAR
);
```

**Grading notes:** Query-reading: full credit for correctly stating that the statement builds/writes the PESR_HNS_Protocol structure and listing its four parts; misreading the operation (e.g., taking it for a query) counts as L; omitting a sub-structure counts as V.

### Question 2.2  [Query Writing]

**Business intent:** Retire G48_Immersion_Legacy (schema-bearing: drop the schema; schema-less: delete the data).

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```sql
DROP TABLE g48_immersion_legacy;
```

**Grading notes:** S: delete syntax; L: wrong deletion scope; V: name spelling; M: minor symbols.

### Question 2.3  [Query Writing]

**Business intent:** Schema-level retrieval (schema-bearing: query the schema-library metadata; schema-less: approximate via a data scan): locate the schemas/collections that carry the above electrochemical attributes.

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```sql
SELECT DISTINCT table_name, column_name
FROM information_schema.columns
WHERE column_name LIKE '%protection_potential%'
   OR column_name LIKE '%repassivation_potential%'
   OR column_name LIKE '%hysteresis_loop%';
```

**Grading notes:** S: retrieval syntax; L: wrong condition logic (the "or" relation); V: attribute-name spelling; M: minor symbols.

### Question 2.4  [Result Prediction]

**Business intent:** Joint multi-group filter: environment (medium contains NaCl, concentration = 3.5%, temperature = 20C), corrosion resistance (pitting potential > 1000 mV), and mechanics (yield strength > 550 MPa).

**Expected result:** On the stainless-steel teaching dataset (20 records, see dataset/stainless-steel/), exactly two records satisfy all of the environmental, corrosion, and mechanical conditions: data_number="pitting_potential_2023_0187" (grade 2205, yield strength 615 MPa) and data_number="pitting_potential_2023_0188" (grade 2205, yield strength 580 MPa). The rest are excluded because the NaCl/temperature/pitting-potential conditions are not met or the yield strength is <= 550 MPa.

**Query shown on the paper (for reference):**
```sql
SELECT pe.exp_id, pe.grade
FROM pitting_experiment pe
JOIN solution_environment se   ON se.exp_id = pe.exp_id
JOIN experimental_condition ec ON ec.exp_id = pe.exp_id
JOIN corrosion_result cr       ON cr.exp_id = pe.exp_id
WHERE se.nacl_wt = 3.5
  AND ec.temperature_c = 20
  AND cr.pitting_potential_eb_v > 1.0
  AND pe.yield_strength_mpa > 550;
```

**Grading notes:** Result-prediction: full credit for listing all matching batches; a missed/spurious row counts as L; misreading a threshold or unit counts as V.

## Part 3 — Organic Polymer

### Question 3.1  [Query Writing]

**Business intent:** Rename an attribute (schema-bearing: change the schema definition; schema-less: bulk-rewrite the data field).

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```sql
ALTER TABLE public.materials
  RENAME COLUMN glass_temperature TO "Tg_DSC_Onset";
```

**Grading notes:** S: ALTER/rewrite syntax; L: incomplete migration (some records missed); V: old/new identifier spelling; M: minor symbols.

### Question 3.2  [Query Reading]

**Business intent:** Locate the anomalous WAXD record with data_id = 195540 whose alpha-crystallinity exceeds 100% (physically impossible) and null out that invalid crystallinity value (flagging it for re-measurement), fixing the data-quality problem.

**Statement shown on the paper (for reference):**
```sql
UPDATE waxd_results
SET crystallinity = NULL
WHERE sample_no = 195540 AND crystallinity > 100;
```

**Grading notes:** Query-reading: full credit for stating that it locates record 195540 with the anomalous crystallinity and nulls/fixes the invalid value; misreading the locate condition or the modified target counts as L; omitting the threshold condition counts as V.

### Question 3.3  [Query Writing]

**Business intent:** Schema-level retrieval (co-occurrence): locate the schemas/collections that declare both the SMILES-code and the thermal-decomposition-temperature attributes.

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```sql
SELECT DISTINCT c1.table_schema, c1.table_name
FROM information_schema.columns c1
JOIN information_schema.columns c2
  ON c1.table_schema = c2.table_schema AND c1.table_name = c2.table_name
WHERE c1.column_name ILIKE '%smiles%'
  AND c2.column_name ILIKE '%thermal_decomposition%';
```

**Grading notes:** S: retrieval syntax; L: wrong co-occurrence (AND) logic; V: attribute-name spelling; M: minor symbols.

### Question 3.4  [Query Writing]

**Business intent:** Multi-dimensional joint filter across "material" and "processing", returning the joined result.

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```sql
SELECT DISTINCT m.material_id, m.name, m.category
FROM materials m
WHERE m.category = 'Semi-Aromatic'
  AND m.glass_temperature > 280
  AND m.tensile_strength > 150
  AND EXISTS (SELECT 1 FROM processing_cases pc
              WHERE pc.material_id = m.material_id AND pc.speed > 50);
```

**Grading notes:** S: query/join syntax; L: wrong join key or condition combination; V: wrong threshold (280/150/50); M: minor symbols.

## Part 4 — High-Energy Physics

### Question 4.1  [Query Reading]

**Business intent:** Rename the attribute pid to pdg_id at the particle-entity schema level.

**Statement shown on the paper (for reference):**
```sql
ALTER TABLE particle RENAME COLUMN pid TO pdg_id;
```

**Grading notes:** Query-reading: full credit for stating that it renames pid to pdg_id (schema-bearing: at the schema level; schema-less: per-record migration); misreading the modified target counts as L; spelling counts as V.

### Question 4.2  [Query Writing]

**Business intent:** Conditional delete with referential-integrity maintenance: delete particles with status != 1 and clean up the dangling parent_ids/child_ids references.

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```sql
DELETE FROM particle WHERE status <> 1;
DELETE FROM particle_link
WHERE particle_id NOT IN (SELECT particle_id FROM particle)
   OR child_id    NOT IN (SELECT particle_id FROM particle);
```

**Grading notes:** S: delete/traversal syntax; L: integrity not maintained, or the delete condition inverted; V: wrong status value; M: minor symbols.

### Question 4.3  [Result Prediction]

**Business intent:** Within each event, select the particle entities with pid (or pdg_id) equal to 11 or -11 (electron/positron) and status = 1 (visible final state).

**Expected result:** On the high-energy-physics teaching dataset (20 events, see dataset/high-energy-physics/), every particle with pid in {11, -11} and status = 1 in each event is matched, 75 in total; the per-event match counts (by event number) are: 1:2, 2:4, 3:4, 4:11, 5:8, 6:2, 7:2, 8:4, 9:4, 10:2, 11:4, 12:2, 13:2, 14:4, 15:4, 16:2, 17:2, 18:2, 19:4, 20:6.

**Query shown on the paper (for reference):**
```sql
SELECT event_number, particle_id
FROM particle
WHERE pid IN (11, -11) AND status = 1;
```

**Grading notes:** Result-prediction: full credit for listing the matching electron/positron particles per event; a missed/spurious match counts as L; misreading the pid value counts as V.

### Question 4.4  [Query Writing]

**Business intent:** Per-event aggregation of the transverse-momentum components of visible particles, computing the magnitude MET and filtering the events with MET > 50000 MeV.

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```sql
SELECT event_number,
       SQRT(POWER(SUM(px), 2) + POWER(SUM(py), 2)) AS met
FROM particle
WHERE status = 1
GROUP BY event_number
HAVING SQRT(POWER(SUM(px), 2) + POWER(SUM(py), 2)) > 50000;
```

**Grading notes:** S: aggregation/grouping syntax; L: wrong aggregation scope (only status = 1) or magnitude computation; V: wrong threshold 50000; M: minor symbols.
