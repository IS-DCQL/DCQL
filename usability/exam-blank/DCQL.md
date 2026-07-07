# Final Examination — DCQL (NMDMS)

Language category: Schema-bearing (DCQL/SQL/OQL)  |  16 questions (10 query-writing + 3 query-reading + 3 result-prediction)  |  Total: 100 points

> Closed book; answer in plain text. Write each answer in DCQL (NMDMS); for query-reading questions explain in English, and for result-prediction questions state the expected returned result.
> Each domain's teaching dataset (~20 core records) is provided with the paper under `dataset/<domain>/` (document form; the relational and object renderings of the same data are produced by the conciseness conversion scripts).

## Part 1 — Biomedical

This part concerns biomedical clinical and genomic data (from TCGA). In your storage the patient entity Case is organized under an explicit schema and is linked to sub-structures such as Demographic, Diagnosis, and the specimen lineage Sample -> Portion -> Analyte -> Aliquot. Complete the following schema-definition, data-writing, and complex-retrieval tasks against this schema.

### Question 1.1  [Query Writing]

Define a new business entity "gene_variant" with the attributes gene name (gene_name), variant type (variant_type), variant allele frequency (variant_allele_frequency), and reference-genome version (reference_genome_version), and establish a 1:N association from the patient entity Case to the gene-variant entity. Write the statement(s) that create this schema.

(Write your answer here.)

### Question 1.2  [Query Writing]

For the patient with case_id="00016c8f-a0be-4319-9c42-4f3bcd90ac92", insert a new gene-variant record: gene_name="BRCA1", variant_type="INDEL", variant_allele_frequency=0.07, reference_genome_version="GRCh38".

(Write your answer here.)

### Question 1.3  [Query Writing]

The entity "Legacy_Risk_Factors" has been deprecated. Remove its entity definition and all of its attribute descriptions (drop the schema).

(Write your answer here.)

### Question 1.4  [Result Prediction]

Read the query below and, using this domain's teaching dataset provided with the paper (dataset/biomedical/), predict the result it returns (list the returned fields and the matching records):

```sql
select case_id,
       samples[].portions[].analytes[].aliquots[].aliquot_id,
       samples[].portions[].analytes[].aliquots[].concentration
from template Case dataset gdc
where project.project_id in ("TCGA-KIRC", "TARGET-WT")
  and (demographic.vital_status = "Dead"
       or any (diagnoses[].vital_status = "Dead"
               and diagnoses[].primary_diagnosis like "%Renal Cell Carcinoma%"))
  and any (samples[].sample_type = "Primary Tumor"
           and samples[].preservation_method in ("Snap Frozen", "OCT"))
  and any (samples[].portions[].analytes[].analyte_type = "RNA"
           and samples[].portions[].analytes[].aliquots[].concentration > 0.1)
```

(Write your answer here.)

## Part 2 — Stainless Steel

This part concerns full-life-cycle experimental data for stainless steel (from NMDMS). The entity schemas cover composition, process parameters, microstructure, and performance indicators, and the schema-library metadata itself is queryable. Complete the following tasks against this schema.

### Question 2.1  [Query Reading]

Read the statement below and explain, in English, the business operation it performs (including the role of each main clause/step):

```sql
create template PESR_HNS_Protocol
(
    container(composition_system).table(element).string(name),
    container(composition_system).table(element).number(content, unit=percent),
    container(process_parameters).string(smelting),
    container(process_parameters).string(heat_treatment),
    container(microstructure).string(phase),
    container(microstructure).string(grain_size),
    container(performance_indicators).number(yield_strength, unit=MPa),
    container(performance_indicators).number(pitting_potential, unit=mV)
)
```

(Write your answer here.)

### Question 2.2  [Query Writing]

The data schema "G48_Immersion_Legacy" has been deprecated. Remove its schema definition from the metadata-management system.

(Write your answer here.)

### Question 2.3  [Query Writing]

Retrieve metadata: scan the attribute definitions of all entity schemas and select those whose attribute names contain "protection potential", "repassivation potential", or "hysteresis loop"; return the matching schema metadata.

(Write your answer here.)

### Question 2.4  [Result Prediction]

Read the query below and, using this domain's teaching dataset provided with the paper (dataset/stainless-steel/), predict the result it returns (list the returned fields and the matching records):

```sql
select material_info.grade
from template StainlessExperiment dataset pitting
where solution_environment.NaCl = 3.5
  and experimental_conditions.temperature = 20
  and result_characterization.pitting_potential_eb > 1.0
  and material_performance.yield_strength > 550
```

(Write your answer here.)

## Part 3 — Organic Polymer

This part concerns structure-processing-property data for organic polymers (polyamides, from NMDMS). The material entity carries attributes such as category, monomer/chain structure, and thermal and mechanical properties; the processing entity carries injection/holding/cooling parameters and WAXD characterization results. Complete the following tasks against this schema.

### Question 3.1  [Query Writing]

Across all data structures involving polymer thermal properties, locate the attribute describing the glass-transition temperature and rename its identifier to "Tg_DSC_Onset" (modify the schema).

(Write your answer here.)

### Question 3.2  [Query Reading]

Read the statement below and explain, in English, the business operation it performs (including the role of each main clause/step):

```sql
update template Polymer dataset processing
set WAXD_result.alpha_crystallinity = null
where meta.data_id = 195540 and WAXD_result.alpha_crystallinity > 100
```

(Write your answer here.)

### Question 3.3  [Query Writing]

Retrieve metadata: find all schemas whose attribute identifiers contain both "SMILES code" and "thermal-decomposition temperature", and return their metadata.

(Write your answer here.)

### Question 3.4  [Query Writing]

Query the semi-aromatic (Semi-Aromatic) polymer instances, join their associated processing data, and require glass-transition temperature (Tg) > 280C, tensile strength > 150 MPa, and the existence of an injection stage with speed > 50 mm/s. Return the material name together with its thermal, mechanical, and processing performance.

(Write your answer here.)

## Part 4 — High-Energy Physics

This part concerns high-energy-physics particle-collision event data (from CERN Open Data). Each Event encapsulates a variable-length set of Particle entities, where a particle carries `pid`, `status`, `momentum (p_x, p_y, p_z, e)`, and `parent_ids`/`child_ids` associations. Complete the following tasks against this schema.

### Question 4.1  [Query Reading]

Read the statement below and explain, in English, the business operation it performs (including the role of each main clause/step):

```sql
alter template Event
alter particles.pid, pdg_id
```

(Write your answer here.)

### Question 4.2  [Query Writing]

Traverse the particle entities in every event and delete the particles with status != 1; after deletion, the parent_ids/child_ids associations among the remaining particles must remain consistent.

(Write your answer here.)

### Question 4.3  [Result Prediction]

Read the query below and, using this domain's teaching dataset provided with the paper (dataset/high-energy-physics/), predict the result it returns (list the returned fields and the matching records):

```sql
select event_number, particles[].id
from template Event dataset collision
where particles[].pid in (11, -11) and particles[].status = 1
```

(Write your answer here.)

### Question 4.4  [Query Writing]

For each event, traverse all of its visible particles (status = 1), sum the p_x and p_y components of momentum separately to obtain the total transverse-momentum vector, and compute its magnitude (MET). Select and return the events with MET > 50000 MeV, labeled "anomalous high missing-energy events".

(Write your answer here.)
