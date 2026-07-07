for $doc in json-doc("processing_logs.json")[]
where $doc.meta.data_id = 195540
and $doc.WAXD_result.alpha_crystallinity > 100
return {
"error": {
"data_id": $doc.meta.data_id,
"alpha": $doc.WAXD_result.alpha_crystallinity
}
}
