for $e in db:open("events")/json/_
let $vis := $e/particles/_[status = 1]
let $met := math:sqrt(math:pow(sum($vis/momentum/px), 2) + math:pow(sum($vis/momentum/py), 2))
where $met > 50000
return <event id="{ data($e/event_number) }" met="{ $met }"/>
