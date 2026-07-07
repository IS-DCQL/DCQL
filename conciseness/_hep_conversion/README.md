# High-energy-physics data conversion (for §6.2 queries)

Takes the CERN HEP raw data (`high-energy-physics-CERN/output_events.json`, 20 events; already in
English) and produces the four storage structures at the **Table 2** counts for HEP
(relational = 3 tables, document = 1 collection, DCM schema = 1 schema, object = 3 classes).

## Run
```
python3 to_document.py     # -> document/   (1 collection: events)
python3 to_relational.py   # -> relational/ (3 tables)
python3 to_object.py       # -> object/     (3 class defs + object graph)
python3 to_schema.py       # -> schema/     (1 DCM schema; reads document/)
```

## DCM schema — 1 schema
**events** — the DCM template (schema) DCQL stores the data under. `schema/events.schema.json`
is in the native DCM template format (`{_type, r, …}` per attribute, English DCM type names,
nested for the `particles[]` array), inferred from the document output. The schema count
equals the document-collection count (Table 2, "DCM structure" row).

## (1) Relational — 3 tables
- **event**(event_number, momentum_unit, length_unit)
- **particle**(event_number, particle_id, pid, status, mass, px, py, pz, e)
- **particle_link**(event_number, particle_id, child_id)  -- parent→child edges

## (2) Document — 1 collection
- **events**: each document = one event with nested `particles[]`
  (`particles[].momentum.px`, `particles[].pid`, `particles[].status`, ...).

## (3) Object — 3 classes
- **Event** (1:N **Particle**), **Particle** (1:1 **Momentum**), **Momentum**
  (class defs in `object/*.java`).

## Notes
- Generated data (`document/`, `relational/`, `object/object_instances.json`) is
  derived and gitignored; scripts + `object/*.java` + this README are committed.
- The HEP §6.2 queries under `../<language>/high-energy-physics/` are written against
  these structures. (BaseX maps JSON keys containing `_` to `__`, e.g.
  `event_number` → `event__number`, matching the existing biomedical XQuery.)
