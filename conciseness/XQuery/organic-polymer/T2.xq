for $doc in db:get("processing_logs")//map
let $id := $doc//number[@key="data_id"]
let $alpha := $doc//number[@key="alpha_crystallinity"]
where $id = 195540 and $alpha > 100
return
  <error>
    <data_id>{ $id }</data_id>
    <alpha>{ $alpha }</alpha>
  </error>
