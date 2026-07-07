#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the 7 final-exam papers (exam-blank/) + answer keys (exam-key/) for §6.3.

Mirrors Appendix Table A.2 (tab:app): 4 domains x 4 questions = 16 items, in the same
order as Table A.1 (tab:wl-full). Three language categories share two question-stem sets
(schema-bearing: DCQL/SQL/OQL; schema-less: MQL/N1QL/XQuery/JSONiq); OQL is treated as
schema-bearing (it owns persistent classes). The 3 query-reading + 3 result-prediction
items embed each language's own query, pulled from ../conciseness/<LANG>/<domain>/<task>;
writing-question reference answers in the key come from the same files. Two items
(biomedical-Q2 insert, polymer-Q2 data-fix) have no conciseness counterpart and are
authored below.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CONC = os.path.normpath(os.path.join(HERE, "..", "conciseness"))
BLANK = os.path.join(HERE, "exam-blank")
KEY = os.path.join(HERE, "exam-key")

SCHEMA_LANGS = ["DCQL", "SQL", "OQL"]
LESS_LANGS = ["MQL", "N1QL", "XQuery", "JSONiq"]
LANGS = SCHEMA_LANGS + LESS_LANGS
GROUP = {**{l: "schema" for l in SCHEMA_LANGS}, **{l: "less" for l in LESS_LANGS}}
EXT = {"DCQL": "dcql", "SQL": "sql", "OQL": "jpql", "MQL": "js",
       "N1QL": "n1ql", "XQuery": "xq", "JSONiq": "jq"}
FENCE = {"DCQL": "sql", "SQL": "sql", "OQL": "java", "MQL": "javascript",
         "N1QL": "sql", "XQuery": "xquery", "JSONiq": "xquery"}
ENGINE = {"DCQL": "DCQL (NMDMS)", "SQL": "SQL (PostgreSQL)", "OQL": "OQL / JPQL (Hibernate)",
          "MQL": "MQL (MongoDB)", "N1QL": "N1QL (Couchbase)", "XQuery": "XQuery (BaseX)",
          "JSONiq": "JSONiq (RumbleDB)"}

DOMAINS = ["biomedical", "stainless-steel", "organic-polymer", "high-energy-physics"]
DOMAIN_EN = {"biomedical": "Biomedical", "stainless-steel": "Stainless Steel",
             "organic-polymer": "Organic Polymer", "high-energy-physics": "High-Energy Physics"}

INTRO = {
 "biomedical": {
  "schema": "This part concerns biomedical clinical and genomic data (from TCGA). In your storage the patient entity Case is organized under an explicit schema and is linked to sub-structures such as Demographic, Diagnosis, and the specimen lineage Sample -> Portion -> Analyte -> Aliquot. Complete the following schema-definition, data-writing, and complex-retrieval tasks against this schema.",
  "less": "This part concerns biomedical clinical and genomic data (from TCGA). In your storage each patient is a single nested document (collection `cases`) holding `demographic`, `diagnoses[]`, and `samples[] -> portions[] -> analytes[] -> aliquots[]`. Complete the following tasks against this document structure."},
 "stainless-steel": {
  "schema": "This part concerns full-life-cycle experimental data for stainless steel (from NMDMS). The entity schemas cover composition, process parameters, microstructure, and performance indicators, and the schema-library metadata itself is queryable. Complete the following tasks against this schema.",
  "less": "This part concerns full-life-cycle experimental data for stainless steel (from NMDMS). The data is stored as collections/documents whose records cover composition, process, microstructure, and performance fields. Complete the following tasks against this data structure."},
 "organic-polymer": {
  "schema": "This part concerns structure-processing-property data for organic polymers (polyamides, from NMDMS). The material entity carries attributes such as category, monomer/chain structure, and thermal and mechanical properties; the processing entity carries injection/holding/cooling parameters and WAXD characterization results. Complete the following tasks against this schema.",
  "less": "This part concerns structure-processing-property data for organic polymers (polyamides, from NMDMS). The data is stored as document collections such as `materials_library` (materials) and `processing_logs` (processing, including `WAXD_result`). Complete the following tasks against this data structure."},
 "high-energy-physics": {
  "schema": "This part concerns high-energy-physics particle-collision event data (from CERN Open Data). Each Event encapsulates a variable-length set of Particle entities, where a particle carries `pid`, `status`, `momentum (p_x, p_y, p_z, e)`, and `parent_ids`/`child_ids` associations. Complete the following tasks against this schema.",
  "less": "This part concerns high-energy-physics particle-collision event data (from CERN Open Data). The data is stored as the `events` document collection; each event holds a `particles[]` array, and a particle carries `pid`, `status`, `momentum`, and `parent_ids`/`child_ids` fields. Complete the following tasks against this data structure."},
}

# ---- authored statements (no conciseness counterpart) ------------------------------
BIO_Q2 = {
 "DCQL": 'update template Case dataset cases\nset gene_variant = table ((string BRCA1, choice INDEL, number 0.07, string GRCh38))\nwhere case_id = "00016c8f-a0be-4319-9c42-4f3bcd90ac92"',
 "SQL": "INSERT INTO clinical.gene_variant\n    (variant_id, case_id, gene_name, variant_type, variant_allele_frequency, reference_genome_version)\nVALUES ('GV-0001', '00016c8f-a0be-4319-9c42-4f3bcd90ac92', 'BRCA1', 'INDEL', 0.07, 'GRCh38');",
 "OQL": 'GeneVariant gv = new GeneVariant();\ngv.setVariantId("GV-0001");\ngv.setCaseRef(em.find(CaseEntity.class, "00016c8f-a0be-4319-9c42-4f3bcd90ac92"));\ngv.setGeneName("BRCA1");\ngv.setVariantType("INDEL");\ngv.setVariantAlleleFrequency(0.07);\ngv.setReferenceGenomeVersion("GRCh38");\nem.persist(gv);',
 "MQL": 'db.cases.updateOne(\n  { case_id: "00016c8f-a0be-4319-9c42-4f3bcd90ac92" },\n  { $push: { gene_variants: {\n      gene_name: "BRCA1", variant_type: "INDEL",\n      variant_allele_frequency: 0.07, reference_genome_version: "GRCh38"\n  } } }\n)',
 "N1QL": 'INSERT INTO `dcql`._default.gene_variant (KEY, VALUE)\nVALUES ("GV-0001", {\n  "case_id": "00016c8f-a0be-4319-9c42-4f3bcd90ac92",\n  "gene_name": "BRCA1", "variant_type": "INDEL",\n  "variant_allele_frequency": 0.07, "reference_genome_version": "GRCh38"\n});',
 "XQuery": 'insert node\n  <gene_variant>\n    <gene_name>BRCA1</gene_name>\n    <variant_type>INDEL</variant_type>\n    <variant_allele_frequency>0.07</variant_allele_frequency>\n    <reference_genome_version>GRCh38</reference_genome_version>\n  </gene_variant>\ninto db:open("tcga_cases")/json/_[case_id = "00016c8f-a0be-4319-9c42-4f3bcd90ac92"]',
 "JSONiq": 'for $c in json-doc("cases.json")[]\nreturn if ($c.case_id eq "00016c8f-a0be-4319-9c42-4f3bcd90ac92")\n       then {| $c, { "gene_variants": [ $c.gene_variants[],\n              {"gene_name":"BRCA1","variant_type":"INDEL","variant_allele_frequency":0.07,"reference_genome_version":"GRCh38"} ] } |}\n       else $c',
}
POLY_Q2 = {
 "DCQL": 'update template Polymer dataset processing\nset WAXD_result.alpha_crystallinity = null\nwhere meta.data_id = 195540 and WAXD_result.alpha_crystallinity > 100',
 "SQL": "UPDATE waxd_results\nSET crystallinity = NULL\nWHERE sample_no = 195540 AND crystallinity > 100;",
 "OQL": "UPDATE public.waxd_results\nSET crystallinity = NULL\nWHERE sample_no = 195540 AND crystallinity > 100",
 "MQL": 'db.processing_logs.updateOne(\n  { "meta.data_id": 195540, "WAXD_result.alpha_crystallinity": { $gt: 100 } },\n  { $set: { "WAXD_result.alpha_crystallinity": null } }\n)',
 "N1QL": "UPDATE `dcql`._default.processing_logs\nSET WAXD_result.alpha_crystallinity = NULL\nWHERE meta.data_id = 195540 AND WAXD_result.alpha_crystallinity > 100;",
 "XQuery": 'for $a in db:get("processing_logs")//map[*[@key="data_id"]=195540]//number[@key="alpha_crystallinity"][. > 100]\nreturn replace value of node $a with "NaN"',
 "JSONiq": 'for $doc in json-doc("processing_logs.json")[]\nreturn if ($doc.meta.data_id eq 195540 and $doc.WAXD_result.alpha_crystallinity gt 100)\n       then {| $doc, { "WAXD_result": {| $doc.WAXD_result, { "alpha_crystallinity": null } |} } |}\n       else $doc',
}

# ---- per-question metadata ---------------------------------------------------------
# type: write | read | predict ; conc: task stem in conciseness, or None (authored)
Q = {
 "biomedical": [
  {"no":1,"type":"write","conc":"T1",
   "stem_schema":"Define a new business entity \"gene_variant\" with the attributes gene name (gene_name), variant type (variant_type), variant allele frequency (variant_allele_frequency), and reference-genome version (reference_genome_version), and establish a 1:N association from the patient entity Case to the gene-variant entity. Write the statement(s) that create this schema.",
   "stem_less":"The database has no gene-variant information yet. For the patient with case_id=\"00016c8f-a0be-4319-9c42-4f3bcd90ac92\", write its first gene-variant record (gene_name=\"TP53\", variant_type=\"SNP\", variant_allele_frequency=0.12, reference_genome_version=\"GRCh38\") as an embedded array under that patient's document, thereby establishing the 1:N association.",
   "intent":"Establish the gene-variant entity and its 1:N association to Case (schema-bearing: define the schema; schema-less: establish the structure implicitly through the first embedded record).",
   "grade":"S: basic DDL/write form; L: incorrect 1:N modeling (not attached to Case); V: wrong field name/type; M: minor omissions such as a missing semicolon or bracket."},
  {"no":2,"type":"write","conc":None,"authored":BIO_Q2,
   "stem_schema":"For the patient with case_id=\"00016c8f-a0be-4319-9c42-4f3bcd90ac92\", insert a new gene-variant record: gene_name=\"BRCA1\", variant_type=\"INDEL\", variant_allele_frequency=0.07, reference_genome_version=\"GRCh38\".",
   "stem_less":"For the patient with case_id=\"00016c8f-a0be-4319-9c42-4f3bcd90ac92\", insert a new gene-variant record: gene_name=\"BRCA1\", variant_type=\"INDEL\", variant_allele_frequency=0.07, reference_genome_version=\"GRCh38\".",
   "intent":"Write one data record into the gene-variant entity established in Question 1.",
   "grade":"S: insert/write syntax; L: wrong target or association (not attached to the correct Case); V: wrong literal value (0.07); M: minor symbols."},
  {"no":3,"type":"write","conc":"T4",
   "stem_schema":"The entity \"Legacy_Risk_Factors\" has been deprecated. Remove its entity definition and all of its attribute descriptions (drop the schema).",
   "stem_less":"The entity \"Legacy_Risk_Factors\" has been deprecated. Delete all legacy_risk_factors data from the database (delete data).",
   "intent":"Retire Legacy_Risk_Factors (schema-bearing: drop the schema; schema-less: delete the data).",
   "grade":"S: DROP/delete syntax; L: wrong deletion scope (too much / too little); V: entity-name spelling; M: minor symbols."},
  {"no":4,"type":"predict","conc":"T3",
   "intent":"Complex multi-condition chained retrieval: project_id in {TCGA-KIRC, TARGET-WT}, and (demographic.vital_status = Dead, OR a diagnosis whose primary_diagnosis contains \"Renal Cell Carcinoma\" with vital_status = Dead), and Sample.sample_type = Primary Tumor with preservation_method in {Snap Frozen, OCT}, and a terminal Analyte with analyte_type = RNA and concentration > 0.1. Return the Case identifier, the available Aliquot_ID, and the corresponding RNA concentration.",
   "predict":"On the biomedical teaching dataset (20 records, see dataset/biomedical/), only the case case_id=\"28011111-4a01-4cdc-8d6b-7223fb2c501b\" satisfies the full chain. The query returns that case and its two RNA aliquots: aliquot_id=\"19f0514a-35c8-4490-886f-1accf6ce4d9c\" (concentration 0.17 ug/uL) and aliquot_id=\"957fa2bd-2222-43a4-b046-d2f78bf506a5\" (concentration 0.17 ug/uL). The other 19 cases are excluded (wrong project_id, or the sample/analyte chain is not satisfied), so the result is exactly these two rows.",
   "grade":"Result-prediction: full credit for correctly listing all matching Cases with their Aliquot_IDs and concentrations; a missed or spurious row counts as L; a wrong value (e.g., concentration) counts as V."},
 ],
 "stainless-steel": [
  {"no":1,"type":"read","conc":"T1-1",
   "intent_schema":"Create a new entity schema named PESR_HNS_Protocol with four parts: composition system, process parameters, microstructure, and performance indicators.",
   "intent_less":"Write the first record of the PESR_HNS_Protocol entity (a schema-less language establishes the structure implicitly through the data it writes).",
   "grade":"Query-reading: full credit for correctly stating that the statement builds/writes the PESR_HNS_Protocol structure and listing its four parts; misreading the operation (e.g., taking it for a query) counts as L; omitting a sub-structure counts as V."},
  {"no":2,"type":"write","conc":"T4",
   "stem_schema":"The data schema \"G48_Immersion_Legacy\" has been deprecated. Remove its schema definition from the metadata-management system.",
   "stem_less":"Delete all G48_Immersion_Legacy data from the database.",
   "intent":"Retire G48_Immersion_Legacy (schema-bearing: drop the schema; schema-less: delete the data).",
   "grade":"S: delete syntax; L: wrong deletion scope; V: name spelling; M: minor symbols."},
  {"no":3,"type":"write","conc":"T1-2",
   "stem_schema":"Retrieve metadata: scan the attribute definitions of all entity schemas and select those whose attribute names contain \"protection potential\", \"repassivation potential\", or \"hysteresis loop\"; return the matching schema metadata.",
   "stem_less":"Scan the data and find the collections/documents whose records carry fields such as \"protection potential\", \"repassivation potential\", or \"hysteresis loop\", and return them (a schema-less language cannot query the schema directly, so this is approximated by a data scan).",
   "intent":"Schema-level retrieval (schema-bearing: query the schema-library metadata; schema-less: approximate via a data scan): locate the schemas/collections that carry the above electrochemical attributes.",
   "grade":"S: retrieval syntax; L: wrong condition logic (the \"or\" relation); V: attribute-name spelling; M: minor symbols."},
  {"no":4,"type":"predict","conc":"T3",
   "intent":"Joint multi-group filter: environment (medium contains NaCl, concentration = 3.5%, temperature = 20C), corrosion resistance (pitting potential > 1000 mV), and mechanics (yield strength > 550 MPa).",
   "predict":"On the stainless-steel teaching dataset (20 records, see dataset/stainless-steel/), exactly two records satisfy all of the environmental, corrosion, and mechanical conditions: data_number=\"pitting_potential_2023_0187\" (grade 2205, yield strength 615 MPa) and data_number=\"pitting_potential_2023_0188\" (grade 2205, yield strength 580 MPa). The rest are excluded because the NaCl/temperature/pitting-potential conditions are not met or the yield strength is <= 550 MPa.",
   "grade":"Result-prediction: full credit for listing all matching batches; a missed/spurious row counts as L; misreading a threshold or unit counts as V."},
 ],
 "organic-polymer": [
  {"no":1,"type":"write","conc":"T4",
   "stem_schema":"Across all data structures involving polymer thermal properties, locate the attribute describing the glass-transition temperature and rename its identifier to \"Tg_DSC_Onset\" (modify the schema).",
   "stem_less":"Rename/migrate the \"glass-transition temperature\" field to \"Tg_DSC_Onset\" in place across all records (bulk data modification; a schema-less language cannot rename a schema).",
   "intent":"Rename an attribute (schema-bearing: change the schema definition; schema-less: bulk-rewrite the data field).",
   "grade":"S: ALTER/rewrite syntax; L: incomplete migration (some records missed); V: old/new identifier spelling; M: minor symbols."},
  {"no":2,"type":"read","conc":None,"authored":POLY_Q2,
   "intent":"Locate the anomalous WAXD record with data_id = 195540 whose alpha-crystallinity exceeds 100% (physically impossible) and null out that invalid crystallinity value (flagging it for re-measurement), fixing the data-quality problem.",
   "grade":"Query-reading: full credit for stating that it locates record 195540 with the anomalous crystallinity and nulls/fixes the invalid value; misreading the locate condition or the modified target counts as L; omitting the threshold condition counts as V."},
  {"no":3,"type":"write","conc":"T1",
   "stem_schema":"Retrieve metadata: find all schemas whose attribute identifiers contain both \"SMILES code\" and \"thermal-decomposition temperature\", and return their metadata.",
   "stem_less":"Scan the data and find the collections/documents whose records carry both a \"SMILES code\" field and a \"thermal-decomposition temperature\" field (a schema-less language cannot query the schema directly, so this is approximated by a data scan).",
   "intent":"Schema-level retrieval (co-occurrence): locate the schemas/collections that declare both the SMILES-code and the thermal-decomposition-temperature attributes.",
   "grade":"S: retrieval syntax; L: wrong co-occurrence (AND) logic; V: attribute-name spelling; M: minor symbols."},
  {"no":4,"type":"write","conc":"T3",
   "stem_schema":"Query the semi-aromatic (Semi-Aromatic) polymer instances, join their associated processing data, and require glass-transition temperature (Tg) > 280C, tensile strength > 150 MPa, and the existence of an injection stage with speed > 50 mm/s. Return the material name together with its thermal, mechanical, and processing performance.",
   "stem_less":"Query the semi-aromatic (Semi-Aromatic) polymer instances, join their associated processing data, and require glass-transition temperature (Tg) > 280C, tensile strength > 150 MPa, and the existence of an injection stage with speed > 50 mm/s. Return the material name and the related performance.",
   "intent":"Multi-dimensional joint filter across \"material\" and \"processing\", returning the joined result.",
   "grade":"S: query/join syntax; L: wrong join key or condition combination; V: wrong threshold (280/150/50); M: minor symbols."},
 ],
 "high-energy-physics": [
  {"no":1,"type":"read","conc":"T4",
   "intent_schema":"Rename the attribute pid to pdg_id at the particle-entity schema level.",
   "intent_less":"Bulk-rename/migrate the pid field to pdg_id across all particle records (a schema-less language realizes this by rewriting the data).",
   "grade":"Query-reading: full credit for stating that it renames pid to pdg_id (schema-bearing: at the schema level; schema-less: per-record migration); misreading the modified target counts as L; spelling counts as V."},
  {"no":2,"type":"write","conc":"T2",
   "stem_schema":"Traverse the particle entities in every event and delete the particles with status != 1; after deletion, the parent_ids/child_ids associations among the remaining particles must remain consistent.",
   "stem_less":"Traverse the particle entities in every event and delete the particles with status != 1; after deletion, the parent_ids/child_ids associations among the remaining particles must remain consistent.",
   "intent":"Conditional delete with referential-integrity maintenance: delete particles with status != 1 and clean up the dangling parent_ids/child_ids references.",
   "grade":"S: delete/traversal syntax; L: integrity not maintained, or the delete condition inverted; V: wrong status value; M: minor symbols."},
  {"no":3,"type":"predict","conc":"T3-1",
   "intent":"Within each event, select the particle entities with pid (or pdg_id) equal to 11 or -11 (electron/positron) and status = 1 (visible final state).",
   "predict":"On the high-energy-physics teaching dataset (20 events, see dataset/high-energy-physics/), every particle with pid in {11, -11} and status = 1 in each event is matched, 75 in total; the per-event match counts (by event number) are: 1:2, 2:4, 3:4, 4:11, 5:8, 6:2, 7:2, 8:4, 9:4, 10:2, 11:4, 12:2, 13:2, 14:4, 15:4, 16:2, 17:2, 18:2, 19:4, 20:6.",
   "grade":"Result-prediction: full credit for listing the matching electron/positron particles per event; a missed/spurious match counts as L; misreading the pid value counts as V."},
  {"no":4,"type":"write","conc":"T3-2",
   "stem_schema":"For each event, traverse all of its visible particles (status = 1), sum the p_x and p_y components of momentum separately to obtain the total transverse-momentum vector, and compute its magnitude (MET). Select and return the events with MET > 50000 MeV, labeled \"anomalous high missing-energy events\".",
   "stem_less":"For each event, traverse all of its visible particles (status = 1), sum the p_x and p_y components of momentum separately to obtain the total transverse-momentum vector, and compute its magnitude (MET). Select and return the events with MET > 50000 MeV, labeled \"anomalous high missing-energy events\".",
   "intent":"Per-event aggregation of the transverse-momentum components of visible particles, computing the magnitude MET and filtering the events with MET > 50000 MeV.",
   "grade":"S: aggregation/grouping syntax; L: wrong aggregation scope (only status = 1) or magnitude computation; V: wrong threshold 50000; M: minor symbols."},
 ],
}

TYPE_EN = {"write": "Query Writing", "read": "Query Reading", "predict": "Result Prediction"}


def read_conc(lang, domain, task):
    # OQL organic-polymer mixes .sql (T2/T3) and .jpql (T1/T4); try candidates in order.
    cands = [EXT[lang]]
    if lang == "OQL" and domain == "organic-polymer":
        cands = ["sql", "jpql"]
    for ext in cands:
        path = os.path.join(CONC, lang, domain, f"{task}.{ext}")
        if os.path.exists(path):
            return open(path, encoding="utf-8").read().strip()
    raise FileNotFoundError(f"{lang}/{domain}/{task} (tried {cands})")


def code_for(lang, domain, q):
    if q["conc"] is None:
        return q["authored"][lang]
    return read_conc(lang, domain, q["conc"])


def stem_for(lang, q):
    g = GROUP[lang]
    if "stem_schema" in q:
        return q["stem_schema"] if g == "schema" else q["stem_less"]
    return None  # read/predict use a generic instruction + embedded code


def intent_for(lang, q):
    g = GROUP[lang]
    if "intent_schema" in q:
        return q["intent_schema"] if g == "schema" else q["intent_less"]
    return q["intent"]


def cat_label(g):
    return "Schema-bearing (DCQL/SQL/OQL)" if g == "schema" else "Schema-less (MQL/N1QL/XQuery/JSONiq)"


def build_paper(lang):
    g = GROUP[lang]
    out = [f"# Final Examination — {ENGINE[lang]}", "",
           f"Language category: {cat_label(g)}  |  16 questions "
           "(10 query-writing + 3 query-reading + 3 result-prediction)  |  Total: 100 points",
           "",
           f"> Closed book; answer in plain text. Write each answer in {ENGINE[lang]}; "
           "for query-reading questions explain in English, and for result-prediction questions "
           "state the expected returned result.",
           "> Each domain's teaching dataset (~20 core records) is provided with the paper under "
           "`dataset/<domain>/` (document form; the relational and object renderings of the same "
           "data are produced by the conciseness conversion scripts).", ""]
    for di, domain in enumerate(DOMAINS, 1):
        out += [f"## Part {di} — {DOMAIN_EN[domain]}", "", INTRO[domain][g], ""]
        for q in Q[domain]:
            out.append(f"### Question {di}.{q['no']}  [{TYPE_EN[q['type']]}]")
            if q["type"] == "write":
                out += ["", stem_for(lang, q), "", "(Write your answer here.)", ""]
            elif q["type"] == "read":
                out += ["", "Read the statement below and explain, in English, the business operation "
                        "it performs (including the role of each main clause/step):", "",
                        f"```{FENCE[lang]}", code_for(lang, domain, q), "```", "",
                        "(Write your answer here.)", ""]
            else:  # predict
                out += ["", f"Read the query below and, using this domain's teaching dataset provided "
                        f"with the paper (dataset/{domain}/), predict the result it returns "
                        "(list the returned fields and the matching records):", "",
                        f"```{FENCE[lang]}", code_for(lang, domain, q), "```", "",
                        "(Write your answer here.)", ""]
    return "\n".join(out).rstrip() + "\n"


def build_key(lang):
    g = GROUP[lang]
    out = [f"# Answer Key & Grading Rubric — {ENGINE[lang]}", "",
           f"Language category: {cat_label(g)}", "",
           "Grading uses the four error classes from §6.3: **S** syntax-structure, **L** semantic-logic, "
           "**V** numeric, **M** minor-language. The writing / reading / prediction sub-scores total "
           "70 / 15 / 15.", ""]
    for di, domain in enumerate(DOMAINS, 1):
        out += [f"## Part {di} — {DOMAIN_EN[domain]}", ""]
        for q in Q[domain]:
            out.append(f"### Question {di}.{q['no']}  [{TYPE_EN[q['type']]}]")
            out += ["", f"**Business intent:** {intent_for(lang, q)}", ""]
            if q["type"] == "predict":
                out += [f"**Expected result:** {q['predict']}", ""]
                out += ["**Query shown on the paper (for reference):**",
                        f"```{FENCE[lang]}", code_for(lang, domain, q), "```", ""]
            elif q["type"] == "read":
                out += ["**Statement shown on the paper (for reference):**",
                        f"```{FENCE[lang]}", code_for(lang, domain, q), "```", ""]
            else:  # write -> reference answer
                src = ("(standard implementation for this language, from the conciseness corpus)"
                       if q["conc"] else "(reference implementation)")
                out += [f"**Reference answer {src}:**",
                        f"```{FENCE[lang]}", code_for(lang, domain, q), "```", ""]
            out += [f"**Grading notes:** {q['grade']}", ""]
    return "\n".join(out).rstrip() + "\n"


def main():
    os.makedirs(BLANK, exist_ok=True)
    os.makedirs(KEY, exist_ok=True)
    for lang in LANGS:
        open(os.path.join(BLANK, f"{lang}.md"), "w", encoding="utf-8").write(build_paper(lang))
        open(os.path.join(KEY, f"{lang}.md"), "w", encoding="utf-8").write(build_key(lang))
        print(f"wrote exam-blank/{lang}.md + exam-key/{lang}.md")


if __name__ == "__main__":
    main()
