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
