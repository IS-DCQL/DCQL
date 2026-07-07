(: RumbleDB is read-only and has no drop-collection statement; the G48_Immersion_Legacy
   collection (a JSON file) is removed at the storage layer. :)
for $d in json-doc("g48_immersion_legacy.json")[]
where false
return $d
