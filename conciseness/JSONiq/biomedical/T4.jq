(: Remove the Legacy_Risk_Factors entity by rewriting each case without that field. :)
for $c in json-doc("cases.json")[]
return {| { for $k in keys($c) where $k ne "legacy_risk_factors" return { $k : $c.$k } } |}
