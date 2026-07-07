for $db in db:list()
for $n in db:open($db)//*[matches(name(), "protection_potential|repassivation_potential|hysteresis_loop")]
return <attr db="{ $db }">{ name($n) }</attr>
