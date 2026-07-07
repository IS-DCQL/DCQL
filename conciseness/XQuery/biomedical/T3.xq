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
