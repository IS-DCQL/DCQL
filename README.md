# DCQL — Supplementary Materials

Supplementary code, artifacts, and data pointers for the DCQL paper. Folders are organized
by the paper's evaluation sections (§6).

> **Bilingual READMEs.** Every `README.md` here has a Chinese companion `README_zh.md` for
> reading convenience. The English `README.md` is authoritative; the `README_zh.md` files are
> a courtesy translation and are meant to be **deleted before publishing to GitHub**.

## Folder → paper section

| Folder | Paper section | Contents |
|---|---|---|
| [`data/`](data/) | §6.1 Datasets | Pointers (links/DOIs) to the four source datasets; raw files are hosted externally, not in git. |
| [`conciseness/`](conciseness/) | §6.2 Syntactic Conciseness | The 16 workloads × 7 languages query corpus (112 files), the per-domain data converters (4 storage structures), and the metric script behind Figure 5. |
| [`usability/`](usability/) | §6.3 Usability & Learning Curve | The blank final-exam papers + answer keys (7 languages), the teaching datasets, and the aggregated figure data (Figs 6–10). Per-participant scores are not released. |
| [`schema-retrieval/`](schema-retrieval/) | §6.5 Schema-Reuse Case Study (RQ4) | The schema-level retrieval query, an offline path/type matching script, and the candidate-schema table (skeleton with `[TODO]`, matching Table rq4). |
| [`performance/`](performance/) | §6.4 Performance & Scalability | Per-language convert/load/benchmark scripts (the four T2/T3 queries are imported from `conciseness/`), and `results/` (the values behind Figs 11–12). |

## How the pieces fit together

- **`conciseness/` is the hub.** Its query files are the *single source of truth* for the
  query statements: `performance/<engine>/3_benchmark.*` loads its T2/T3 queries from there,
  and `usability/`'s exam papers embed them in the reading/prediction questions.
- **The data converters live in `conciseness/_<domain>_conversion/`** and render each
  dataset into the four storage structures of **Table 2** (relational / document / DCM
  schema / object). `performance/` re-uses the same conversion logic on the full cohort, and
  `usability/exam-blank/dataset/` uses it on a curated ~20-record teaching subset.
- **All figures are plotted by one script, `plot_figures.py`** (in the repository root, not
  in this folder). Figure 5/10 come from `conciseness/metrics/`; the Figures 6–10 aggregates
  are mirrored in `usability/figure-data/`; the Figures 11–12 values are mirrored in
  `performance/results/`.

## Notes

- **Large files are not committed** (GitHub rejects files >100 MB). Raw and derived
  datasets are linked from [`data/`](data/); derived per-domain outputs (`document/`,
  `relational/`, `object/`, `schema/`, `*_en.json`) are gitignored and regenerate from the
  scripts.
- **Human-subjects data (§6.3):** only de-identified, aggregated data are released, and only
  as the participants' informed consent permits. No completed exam papers or identifiable
  records are published. See [`usability/README.md`](usability/README.md).
- **Placeholders to fill before submission:** [`schema-retrieval/`](schema-retrieval/) (§6.5)
  is a skeleton whose candidate-schema table and summary numbers are still `[TODO]`; and
  [`data/`](data/) needs the archived-data DOI/links. (The §6.3 teaching materials and the
  per-participant scores are deliberately not included.)
- **Reproducibility / DOI:** consider archiving this repository on Zenodo to mint a citable
  DOI pinned to the version the paper references.
