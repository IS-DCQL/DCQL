# §6.4 Results — Aggregated Values Behind Figures 11–12

The aggregated measurements that produced the §6.4 figures, extracted from the
paper's plotting script `plot_figures.py` (functions `fig11()` and `fig12()`). These let
a reader verify the figures and the numbers quoted in the text.

## `latency_fig11.csv` — Figure 11 (query-latency comparison)

Cold-cache and hot-cache latency for all 7 languages on the four task groups
(biomedical T2/T3, organic-polymer T2/T3).

| Column | Meaning |
|---|---|
| `domain`, `task` | task group (Biomedical / Organic Polymer × T2 / T3) |
| `language` | SQL, OQL, MQL, N1QL, XQuery, JSONiq, DCQL |
| `cold_ms` | cold-cache latency (first execution after dropping caches), ms |
| `hot_mean_ms` | hot-cache mean over the last 8 of 10 runs, ms |
| `hot_sd_ms` | hot-cache sample standard deviation, ms |

Note: `MQL, Biomedical T2, hot_mean_ms = 0` means the hot-cache latency was below the
measurement resolution (shown as "≈0" in Figure 11(a)).

## `scalability_fig12.csv` — Figure 12 (scalability, 1X–1000X)

Hot-cache latency on the **biomedical T3** task as the data size scales from 1X to
1000X. Wide format: one row per scale factor, one column per language. Matches the six
languages plotted in Figure 12.

- An **empty cell** = the run did not complete (storage-capacity limit or query
  timeout), drawn as a ✕ truncation in Figure 12. N1QL fails beyond 100X; XQuery fails
  beyond 50X.
- **JSONiq is excluded from Figure 12** (off-scale): it is ~three orders of magnitude
  higher and would compress the other curves. The text-reported values are
  **1X = 11866 ms** and **50X = 267311 ms**; beyond 50X it times out. (5X/10X were not
  separately reported.)
- The 1X column equals the biomedical-T3 `hot_mean_ms` in `latency_fig11.csv`.

## Provenance and reproduction

These CSVs are transcribed verbatim from the hardcoded data in `plot_figures.py`
(`fig11()` / `fig12()`), which renders `fig11a–d.pdf` and `fig12.pdf`. The raw
per-run timing logs emitted by the harnesses (`*_times.txt`) are not included; add
them here under `raw/` if you want to ship the un-aggregated measurements.
