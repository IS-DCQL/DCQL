(: RumbleDB/JSONiq is read-only: rename pid -> pdg_id by rewriting each particle. :)
for $e in json-doc("events.json")[]
return {| { "event_number": $e.event_number },
  { "particles": [ for $p in $e.particles[] return {| { "pdg_id": $p.pid },
      { for $k in keys($p) where $k ne "pid" return { $k : $p.$k } } |} ] } |}
