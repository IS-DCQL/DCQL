# §6.2 Metrics — Measurement Script & Results

Computes the three syntactic-conciseness metrics behind **Figure 5** over the 112 query
files in `../‹LANGUAGE›/‹domain›/‹task›.‹ext›`.

## Files
- `measure.py` — reads every query file and emits the metrics. Run: `python3 measure.py`.
- `metrics_results.csv` — one row per **language**: `loc_total`, `loc_T1..T4`,
  `syntactic_noise`, `halstead`. This is what aggregates into Figure 5(a/b/c) and the radar
  Figure 10.
- `metrics_by_file.csv` — one row per **cell** (`language, domain, task`): `loc`, `noise`,
  `halstead`, for auditing.
- `noise_schemes.py` — the six candidate syntactic-noise definitions (A–F) that were
  compared; scheme **E** (character-level punctuation density, comments stripped) is the one
  `measure.py` uses and the paper reports.

## Metric definitions (from §6.2)

| Metric | Definition | How `measure.py` computes it |
|---|---|---|
| **Lines of code** | non-blank, non-comment statement lines, also split by life-cycle stage T1–T4 | comment/blank lines stripped per language |
| **Syntactic noise** | character-level punctuation density: special (non-alphanumeric, non-`_`, non-CJK) characters over all non-whitespace characters, comments excluded (Stefik & Siebert, scheme E) | per-language comment syntax handled; path-navigation `.`/`[]` treated as business logic |
| **Halstead** `E` | `E = (n1/2)·(N2/n2)·(N1+N2)·log2(n1+n2)`, n1/n2 = distinct operators/operands, N1/N2 = totals | uniform tokenizer; keywords / `$`-operators / function names → operators, identifiers + literals → operands |

## Keeping the figure consistent

`measure.py` is the source of the published numbers. If the query files change, re-run it
and copy the new per-language arrays into `../../performance/plot_figures.py`
(`fig5a/b/c` and the radar `fig10`), then regenerate `els-cas-templates/figs/fig5*.pdf`
and `fig10.pdf`, so the figures, the §6.2 text, and this CSV stay in agreement. The current
files are already consistent with the as-run query corpus.
