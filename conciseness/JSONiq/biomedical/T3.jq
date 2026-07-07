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
