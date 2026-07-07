for $e in json-doc("events.json")[]
for $p in $e.particles[]
where ($p.pid = 11 or $p.pid = -11) and $p.status = 1
return { "event_number": $e.event_number, "particle_id": $p.id }
