(: BaseX is schema-less: gene_variant needs no schema definition; its elements are
   inserted under a case on first write. Optionally create a database for it: :)
db:create("gene_variant")
