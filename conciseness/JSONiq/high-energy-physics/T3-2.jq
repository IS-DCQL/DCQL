for $e in json-doc("events.json")[]
let $vis := $e.particles[][$$.status = 1]
let $sumpx := sum($vis.momentum.px)
let $sumpy := sum($vis.momentum.py)
where $sumpx * $sumpx + $sumpy * $sumpy > 50000 * 50000
return { "event_number": $e.event_number,
         "met": $sumpx * $sumpx + $sumpy * $sumpy }
