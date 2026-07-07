(: Establish the gene_variant 1:N set as an embedded array on each case. :)
for $c in json-doc("cases.json")[]
return {| $c, { "gene_variants": [] } |}
