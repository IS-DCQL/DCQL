for $c in /json/_
where $c/case_id = "00016c8f-a0be-4319-9c42-4f3bcd90ac92"
return
  <result>
    { $c/case_id }
    { $c/demographic/gender }
    { $c/demographic/race }
    { $c/diagnoses/_/primary_diagnosis }
  </result>
