for $db in db:list()
where db:open($db)//map[*[@key="smiles"] and *[@key="thermal_decomposition"]]
return <schema>{ $db }</schema>
