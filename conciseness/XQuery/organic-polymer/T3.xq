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
