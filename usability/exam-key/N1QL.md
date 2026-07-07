# Answer Key & Grading Rubric — N1QL (Couchbase)

Language category: Schema-less (MQL/N1QL/XQuery/JSONiq)

Grading uses the four error classes from §6.3: **S** syntax-structure, **L** semantic-logic, **V** numeric, **M** minor-language. The writing / reading / prediction sub-scores total 70 / 15 / 15.

## Part 1 — Biomedical

### Question 1.1  [Query Writing]

**Business intent:** Establish the gene-variant entity and its 1:N association to Case (schema-bearing: define the schema; schema-less: establish the structure implicitly through the first embedded record).

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```sql
-- Couchbase is schema-less: no schema definition is required.
-- A 1:N gene-variant set may optionally be held in its own collection:
CREATE COLLECTION `dcql`._default.gene_variant;
```

**Grading notes:** S: basic DDL/write form; L: incorrect 1:N modeling (not attached to Case); V: wrong field name/type; M: minor omissions such as a missing semicolon or bracket.

### Question 1.2  [Query Writing]

**Business intent:** Write one data record into the gene-variant entity established in Question 1.

**Reference answer (reference implementation):**
```sql
INSERT INTO `dcql`._default.gene_variant (KEY, VALUE)
VALUES ("GV-0001", {
  "case_id": "00016c8f-a0be-4319-9c42-4f3bcd90ac92",
  "gene_name": "BRCA1", "variant_type": "INDEL",
  "variant_allele_frequency": 0.07, "reference_genome_version": "GRCh38"
});
```

**Grading notes:** S: insert/write syntax; L: wrong target or association (not attached to the correct Case); V: wrong literal value (0.07); M: minor symbols.

### Question 1.3  [Query Writing]

**Business intent:** Retire Legacy_Risk_Factors (schema-bearing: drop the schema; schema-less: delete the data).

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```sql
DROP COLLECTION `dcql`._default.legacy_risk_factors;
```

**Grading notes:** S: DROP/delete syntax; L: wrong deletion scope (too much / too little); V: entity-name spelling; M: minor symbols.

### Question 1.4  [Result Prediction]

**Business intent:** Complex multi-condition chained retrieval: project_id in {TCGA-KIRC, TARGET-WT}, and (demographic.vital_status = Dead, OR a diagnosis whose primary_diagnosis contains "Renal Cell Carcinoma" with vital_status = Dead), and Sample.sample_type = Primary Tumor with preservation_method in {Snap Frozen, OCT}, and a terminal Analyte with analyte_type = RNA and concentration > 0.1. Return the Case identifier, the available Aliquot_ID, and the corresponding RNA concentration.

**Expected result:** On the biomedical teaching dataset (20 records, see dataset/biomedical/), only the case case_id="28011111-4a01-4cdc-8d6b-7223fb2c501b" satisfies the full chain. The query returns that case and its two RNA aliquots: aliquot_id="19f0514a-35c8-4490-886f-1accf6ce4d9c" (concentration 0.17 ug/uL) and aliquot_id="957fa2bd-2222-43a4-b046-d2f78bf506a5" (concentration 0.17 ug/uL). The other 19 cases are excluded (wrong project_id, or the sample/analyte chain is not satisfied), so the result is exactly these two rows.

**Query shown on the paper (for reference):**
```sql
SELECT DISTINCT c.case_id
FROM `dcql` c
WHERE c.project.project_id IN ["TCGA-KIRC", "TARGET-WT"]
AND (
    c.demographic.vital_status = "Dead"
    OR ANY d IN c.diagnoses SATISFIES
        d.vital_status = "Dead"
        AND LOWER(d.primary_diagnosis) LIKE "%renal cell carcinoma%"
    END
)
AND ANY s IN c.samples SATISFIES
    s.sample_type = "Primary Tumor"
    AND s.preservation_method IN ["Snap Frozen", "Snap-Frozen", "OCT"]
    AND ANY p IN s.portions SATISFIES
        ANY a IN p.analytes SATISFIES
            a.analyte_type = "RNA"
            AND ANY al IN a.aliquots SATISFIES
                al.concentration > 0.1
            END
        END
    END
END;
```

**Grading notes:** Result-prediction: full credit for correctly listing all matching Cases with their Aliquot_IDs and concentrations; a missed or spurious row counts as L; a wrong value (e.g., concentration) counts as V.

## Part 2 — Stainless Steel

### Question 2.1  [Query Reading]

**Business intent:** Write the first record of the PESR_HNS_Protocol entity (a schema-less language establishes the structure implicitly through the data it writes).

**Statement shown on the paper (for reference):**
```sql
-- Couchbase is schema-less: no schema definition is required.
CREATE COLLECTION `dcql`._default.pesr_hns_protocol;
```

**Grading notes:** Query-reading: full credit for correctly stating that the statement builds/writes the PESR_HNS_Protocol structure and listing its four parts; misreading the operation (e.g., taking it for a query) counts as L; omitting a sub-structure counts as V.

### Question 2.2  [Query Writing]

**Business intent:** Retire G48_Immersion_Legacy (schema-bearing: drop the schema; schema-less: delete the data).

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```sql
DROP COLLECTION `dcql`._default.G48_Immersion_Legacy;
```

**Grading notes:** S: delete syntax; L: wrong deletion scope; V: name spelling; M: minor symbols.

### Question 2.3  [Query Writing]

**Business intent:** Schema-level retrieval (schema-bearing: query the schema-library metadata; schema-less: approximate via a data scan): locate the schemas/collections that carry the above electrochemical attributes.

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```sql
-- Couchbase has no schema catalog; infer the schema and keep the matching attributes.
INFER `dcql`._default.pitting_corrosion;
-- retain attribute names matching protection_potential / repassivation_potential / hysteresis_loop
```

**Grading notes:** S: retrieval syntax; L: wrong condition logic (the "or" relation); V: attribute-name spelling; M: minor symbols.

### Question 2.4  [Result Prediction]

**Business intent:** Joint multi-group filter: environment (medium contains NaCl, concentration = 3.5%, temperature = 20C), corrosion resistance (pitting potential > 1000 mV), and mechanics (yield strength > 550 MPa).

**Expected result:** On the stainless-steel teaching dataset (20 records, see dataset/stainless-steel/), exactly two records satisfy all of the environmental, corrosion, and mechanical conditions: data_number="pitting_potential_2023_0187" (grade 2205, yield strength 615 MPa) and data_number="pitting_potential_2023_0188" (grade 2205, yield strength 580 MPa). The rest are excluded because the NaCl/temperature/pitting-potential conditions are not met or the yield strength is <= 550 MPa.

**Query shown on the paper (for reference):**
```sql
SELECT p.content.material_info[0].grade
FROM `dcql`._default.pitting_corrosion p
WHERE TONUMBER(p.content.solution_environment[0].NaCl_wt) = 3.5
  AND TONUMBER(p.content.experimental_conditions[0].temperature_c) = 20
  AND TONUMBER(p.content.result_characterization[0].pitting_potential_eb_v) > 1.0
  AND TONUMBER(p.content.material_performance[0].yield_strength_mpa) > 550;
```

**Grading notes:** Result-prediction: full credit for listing all matching batches; a missed/spurious row counts as L; misreading a threshold or unit counts as V.

## Part 3 — Organic Polymer

### Question 3.1  [Query Writing]

**Business intent:** Rename an attribute (schema-bearing: change the schema definition; schema-less: bulk-rewrite the data field).

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```sql
UPDATE `dcql`._default.materials_library AS mat
SET s.thermal.Tg_DSC_Onset = s.thermal.glass_temperature,
    s.thermal.glass_temperature = MISSING
    FOR s IN mat.samples END
WHERE ANY s IN mat.samples SATISFIES s.thermal.glass_temperature IS NOT MISSING END;
```

**Grading notes:** S: ALTER/rewrite syntax; L: incomplete migration (some records missed); V: old/new identifier spelling; M: minor symbols.

### Question 3.2  [Query Reading]

**Business intent:** Locate the anomalous WAXD record with data_id = 195540 whose alpha-crystallinity exceeds 100% (physically impossible) and null out that invalid crystallinity value (flagging it for re-measurement), fixing the data-quality problem.

**Statement shown on the paper (for reference):**
```sql
UPDATE `dcql`._default.processing_logs
SET WAXD_result.alpha_crystallinity = NULL
WHERE meta.data_id = 195540 AND WAXD_result.alpha_crystallinity > 100;
```

**Grading notes:** Query-reading: full credit for stating that it locates record 195540 with the anomalous crystallinity and nulls/fixes the invalid value; misreading the locate condition or the modified target counts as L; omitting the threshold condition counts as V.

### Question 3.3  [Query Writing]

**Business intent:** Schema-level retrieval (co-occurrence): locate the schemas/collections that declare both the SMILES-code and the thermal-decomposition-temperature attributes.

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```sql
-- Couchbase has no declarative schema query; infer the schema and check that both
-- attributes appear, then return the matching keyspace.
INFER `dcql`._default.materials_library WITH {"sample_size": 1000};
-- inspect the inferred flavor for fields "smiles" and "thermal_decomposition"
```

**Grading notes:** S: retrieval syntax; L: wrong co-occurrence (AND) logic; V: attribute-name spelling; M: minor symbols.

### Question 3.4  [Query Writing]

**Business intent:** Multi-dimensional joint filter across "material" and "processing", returning the joined result.

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```sql
SELECT mat.basic_info.name AS material_name,
       mat.samples[0].thermal.glass_temperature AS glass_temperature,
       mat.samples[0].mechanical.tensile_strength AS tensile_strength
FROM `dcql`._default.materials_library AS mat
INNER JOIN `dcql`._default.processing_logs AS proc
    ON mat.basic_info.name = proc.material_name
WHERE mat.basic_info.category = "Semi-Aromatic"
  AND ANY s IN mat.samples SATISFIES
      s.thermal.glass_temperature > 280 AND s.mechanical.tensile_strength > 150 END
  AND ANY stage IN proc.machine_settings.injection.stages
      SATISFIES stage > 50 END
ORDER BY mat.samples[0].thermal.glass_temperature DESC;
```

**Grading notes:** S: query/join syntax; L: wrong join key or condition combination; V: wrong threshold (280/150/50); M: minor symbols.

## Part 4 — High-Energy Physics

### Question 4.1  [Query Reading]

**Business intent:** Bulk-rename/migrate the pid field to pdg_id across all particle records (a schema-less language realizes this by rewriting the data).

**Statement shown on the paper (for reference):**
```sql
UPDATE `dcql`._default.events
SET p.pdg_id = p.pid, p.pid = MISSING FOR p IN particles END;
```

**Grading notes:** Query-reading: full credit for stating that it renames pid to pdg_id (schema-bearing: at the schema level; schema-less: per-record migration); misreading the modified target counts as L; spelling counts as V.

### Question 4.2  [Query Writing]

**Business intent:** Conditional delete with referential-integrity maintenance: delete particles with status != 1 and clean up the dangling parent_ids/child_ids references.

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```sql
UPDATE `dcql`._default.events AS e
SET e.particles = ARRAY {"id": p.id, "pid": p.pid, "status": p.status, "mass": p.mass,
      "momentum": p.momentum,
      "parent_ids": ARRAY x FOR x IN p.parent_ids WHEN x IN (ARRAY q.id FOR q IN e.particles WHEN q.status = 1 END) END,
      "child_ids":  ARRAY x FOR x IN p.child_ids  WHEN x IN (ARRAY q.id FOR q IN e.particles WHEN q.status = 1 END) END}
    FOR p IN e.particles WHEN p.status = 1 END;
```

**Grading notes:** S: delete/traversal syntax; L: integrity not maintained, or the delete condition inverted; V: wrong status value; M: minor symbols.

### Question 4.3  [Result Prediction]

**Business intent:** Within each event, select the particle entities with pid (or pdg_id) equal to 11 or -11 (electron/positron) and status = 1 (visible final state).

**Expected result:** On the high-energy-physics teaching dataset (20 events, see dataset/high-energy-physics/), every particle with pid in {11, -11} and status = 1 in each event is matched, 75 in total; the per-event match counts (by event number) are: 1:2, 2:4, 3:4, 4:11, 5:8, 6:2, 7:2, 8:4, 9:4, 10:2, 11:4, 12:2, 13:2, 14:4, 15:4, 16:2, 17:2, 18:2, 19:4, 20:6.

**Query shown on the paper (for reference):**
```sql
SELECT e.event_number, p.id AS particle_id
FROM `dcql`._default.events e
UNNEST e.particles p
WHERE p.pid IN [11, -11] AND p.status = 1;
```

**Grading notes:** Result-prediction: full credit for listing the matching electron/positron particles per event; a missed/spurious match counts as L; misreading the pid value counts as V.

### Question 4.4  [Query Writing]

**Business intent:** Per-event aggregation of the transverse-momentum components of visible particles, computing the magnitude MET and filtering the events with MET > 50000 MeV.

**Reference answer (standard implementation for this language, from the conciseness corpus):**
```sql
SELECT e.event_number,
       SQRT(POWER(SUM(p.momentum.px), 2) + POWER(SUM(p.momentum.py), 2)) AS met
FROM `dcql`._default.events e
UNNEST e.particles p
WHERE p.status = 1
GROUP BY e.event_number
HAVING SQRT(POWER(SUM(p.momentum.px), 2) + POWER(SUM(p.momentum.py), 2)) > 50000;
```

**Grading notes:** S: aggregation/grouping syntax; L: wrong aggregation scope (only status = 1) or magnitude computation; V: wrong threshold 50000; M: minor symbols.
