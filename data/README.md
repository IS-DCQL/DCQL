# §6.1 Datasets — Source Links

The study uses four public scientific datasets, one per domain. Raw and derived data
files are large and are **not** stored in git; they are hosted at the sources below
(and, where applicable, mirrored on Zenodo/figshare for a citable DOI).

| Domain | Source | Link |
|---|---|---|
| Biomedical (clinical + genomic) | TCGA via the GDC Data Portal | https://portal.gdc.cancer.gov/analysis_page?app=Downloads |
| High-energy physics | CERN Open Data Portal | https://opendata.cern.ch/search?q=&f=type%3ADataset&l=list&order=desc&p=1&s=10&sort=mostrecent |
| Stainless-steel materials | NMDMS | https://mged.nmdms.ustb.edu.cn/search/#/206334 |
| Organic polymer | NMDMS | https://mged.nmdms.ustb.edu.cn/search/#/206336 |

- The **performance and scalability tests (§6.4)** were run on the **biomedical** and
  **organic-polymer** datasets; all four are used for the conciseness (§6.2) and
  usability (§6.3) studies.
- **Author-archived copy / DOI:** `<ADD Zenodo/figshare DOI>` (recommended, so the
  exact data version referenced by the paper is pinned).
- Derived formats (scaled `expanded_*.json`, NDJSON, XML, relational CSV) are
  **regenerated** by the scripts in `../performance/`, so they are not archived.
