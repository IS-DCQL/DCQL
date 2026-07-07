for $doc in json-doc("materials_library.json")[]
where (some $k in keys($doc.basic_info) satisfies $k = "smiles")
  and (some $s in $doc.samples[] satisfies
       (some $k in keys($s.thermal) satisfies $k = "thermal_decomposition"))
return { "schema": "materials_library", "id": $doc.basic_info.pid }
