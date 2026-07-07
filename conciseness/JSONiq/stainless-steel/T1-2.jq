for $doc in json-doc("pitting_corrosion.json")[]
for $k in keys($doc.content.result_characterization[[1]])
where contains($k, "protection_potential") or contains($k, "repassivation_potential") or contains($k, "hysteresis_loop")
return { "attribute": $k }
