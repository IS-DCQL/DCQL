db.processing_logs.find(
  {
    "meta.data_id": 195540,
    "WAXD_result.alpha_crystallinity": { $gt: 100 }
  },
  { _id: 0, "meta.data_id": 1, "WAXD_result.alpha_crystallinity": 1 }
)
