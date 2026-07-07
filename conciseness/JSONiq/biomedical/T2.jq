for $c in json-doc("cases.json")[]
where $c.case_id = "00016c8f-a0be-4319-9c42-4f3bcd90ac92"
return $c
