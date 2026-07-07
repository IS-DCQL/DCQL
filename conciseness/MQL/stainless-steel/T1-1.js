// MongoDB is schema-less: no schema definition is required. A PESR_HNS_Protocol
// document carries its nested composition / process / microstructure / performance
// fields and is created on first insert.
db.createCollection("pesr_hns_protocol")
