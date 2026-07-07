SELECT w.sample_no, w.crystallinity
FROM waxd_results w
WHERE w.sample_no = 195540
  AND w.crystallinity > 100;
