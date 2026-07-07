(: RumbleDB/JSONiq is read-only: renaming the glass-temperature attribute is done by
   rewriting each document, projecting the value onto the new key "Tg_DSC_Onset". :)
for $doc in json-doc("materials_library.json")[]
return {| { "basic_info": $doc.basic_info },
          { "samples": [ for $s in $doc.samples[]
              return {| { "Tg_DSC_Onset": $s.thermal.glass_temperature },
                        { for $k in keys($s.thermal) where $k ne "glass_temperature"
                          return { $k: $s.thermal.$k } } |} ] } |}
