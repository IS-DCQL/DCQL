CREATE TABLE clinical.gene_variant (
    variant_id                VARCHAR PRIMARY KEY,
    case_id                   VARCHAR NOT NULL REFERENCES clinical.table_case(case_id),
    gene_name                 VARCHAR,
    variant_type              VARCHAR,
    variant_allele_frequency  NUMERIC,
    reference_genome_version  VARCHAR
);
