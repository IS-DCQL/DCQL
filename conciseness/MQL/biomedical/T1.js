// MongoDB is schema-less: the gene_variant entity needs no schema definition; its 1:N
// array is created on a case on first insert. Optionally materialize it as a collection:
db.createCollection("gene_variant")
