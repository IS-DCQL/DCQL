for $a in db:open("materials_library")//*[@key="glass_temperature"]/@key
return replace value of node $a with "Tg_DSC_Onset"
