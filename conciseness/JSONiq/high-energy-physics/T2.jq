(: RumbleDB/JSONiq is read-only: keep only status = 1 particles and drop dangling
   parent/child references, by rewriting each event. :)
for $e in json-doc("events.json")[]
let $kept := $e.particles[][$$.status = 1]
let $ids := [ $kept.id ]
return { "event_number": $e.event_number,
  "particles": [ for $p in $kept return {
      "id": $p.id, "pid": $p.pid, "status": $p.status, "mass": $p.mass, "momentum": $p.momentum,
      "parent_ids": [ $p.parent_ids[][. = $ids[]] ],
      "child_ids":  [ $p.child_ids[][. = $ids[]] ] } ] }
