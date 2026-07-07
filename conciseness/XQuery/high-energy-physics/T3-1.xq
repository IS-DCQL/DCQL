for $e in db:open("events")/json/_
for $p in $e/particles/_
where ($p/pid = 11 or $p/pid = -11) and $p/status = 1
return <particle event="{ data($e/event_number) }">{ data($p/id) }</particle>
