delete nodes db:open("events")//particles/_[status != 1]
(: then remove dangling parent/child id references among the remaining particles :)
