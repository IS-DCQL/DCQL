# Final Examination — N1QL (Couchbase)

Language category: Schema-less (MQL/N1QL/XQuery/JSONiq)  |  16 questions (10 query-writing + 3 query-reading + 3 result-prediction)  |  Total: 100 points

> Closed book; answer in plain text. Write each answer in N1QL (Couchbase); for query-reading questions explain in English, and for result-prediction questions state the expected returned result.
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

(Write your answer here.)

## Part 2 — Stainless Steel

This part concerns full-life-cycle experimental data for stainless steel (from NMDMS). The data is stored as collections/documents whose records cover composition, process, microstructure, and performance fields. Complete the following tasks against this data structure.

### Question 2.1  [Query Reading]

Read the statement below and explain, in English, the business operation it performs (including the role of each main clause/step):

```sql
-- Couchbase is schema-less: no schema definition is required.
CREATE COLLECTION `dcql`._default.pesr_hns_protocol;
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

```sql
SELECT p.content.material_info[0].grade
FROM `dcql`._default.pitting_corrosion p
WHERE TONUMBER(p.content.solution_environment[0].NaCl_wt) = 3.5
  AND TONUMBER(p.content.experimental_conditions[0].temperature_c) = 20
  AND TONUMBER(p.content.result_characterization[0].pitting_potential_eb_v) > 1.0
  AND TONUMBER(p.content.material_performance[0].yield_strength_mpa) > 550;
```

(Write your answer here.)

## Part 3 — Organic Polymer

This part concerns structure-processing-property data for organic polymers (polyamides, from NMDMS). The data is stored as document collections such as `materials_library` (materials) and `processing_logs` (processing, including `WAXD_result`). Complete the following tasks against this data structure.

### Question 3.1  [Query Writing]

Rename/migrate the "glass-transition temperature" field to "Tg_DSC_Onset" in place across all records (bulk data modification; a schema-less language cannot rename a schema).

(Write your answer here.)

### Question 3.2  [Query Reading]

Read the statement below and explain, in English, the business operation it performs (including the role of each main clause/step):

```sql
UPDATE `dcql`._default.processing_logs
SET WAXD_result.alpha_crystallinity = NULL
WHERE meta.data_id = 195540 AND WAXD_result.alpha_crystallinity > 100;
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

```sql
UPDATE `dcql`._default.events
SET p.pdg_id = p.pid, p.pid = MISSING FOR p IN particles END;
```

(Write your answer here.)

### Question 4.2  [Query Writing]

Traverse the particle entities in every event and delete the particles with status != 1; after deletion, the parent_ids/child_ids associations among the remaining particles must remain consistent.

(Write your answer here.)

### Question 4.3  [Result Prediction]

Read the query below and, using this domain's teaching dataset provided with the paper (dataset/high-energy-physics/), predict the result it returns (list the returned fields and the matching records):

```sql
SELECT e.event_number, p.id AS particle_id
FROM `dcql`._default.events e
UNNEST e.particles p
WHERE p.pid IN [11, -11] AND p.status = 1;
```

(Write your answer here.)

### Question 4.4  [Query Writing]

For each event, traverse all of its visible particles (status = 1), sum the p_x and p_y components of momentum separately to obtain the total transverse-momentum vector, and compute its magnitude (MET). Select and return the events with MET > 50000 MeV, labeled "anomalous high missing-energy events".

(Write your answer here.)
