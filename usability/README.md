# §6.3 Usability & Learning Curve — Materials and De-identified Data

Backs the controlled learning experiment with 49 interdisciplinary participants reported in
§6.3 (Figures 6–10: scores, completion time, error patterns, memory retention, overall
capability). It also holds the final-exam instruments built from the §6.2 query corpus.

## Contents

| Path | What it is |
|---|---|
| `exam-blank/` | The **blank** final-exam papers, one per language (4 parts × 4 questions), mirroring Appendix Table A.2. See `exam-blank/README.md`. |
| `exam-blank/dataset/` | The ~20-record **teaching datasets** handed out with the papers (illustrative; curated so the prediction questions have small, definite answers). See `exam-blank/dataset/README.md`. |
| `exam-key/` | Reference answers + the S/L/V/M grading rubric for the 7 papers. |
| `_generate_exams.py` | Regenerates `exam-blank/` + `exam-key/` from the §6.2 `../conciseness/` corpus. |
| `_build_teaching_data.py` | Regenerates `exam-blank/dataset/` from the raw sources. |
| `figure-data/` | Per-language aggregated means/SDs behind Figures 6–10 (group-level only, no individual records). See `figure-data/README.md`. |
| `THREATS-TO-VALIDITY.md` | Threats-to-validity note for the usability experiment. |

The **per-participant scores are intentionally not released**: only the group-level
aggregates in `figure-data/` are published, and the individual `P1…P49` records are
available from the corresponding author on reasonable request (the paper carries a
matching data-availability statement). The §6.5 schema-reuse case study (RQ4) lives in its
own top-level [`../schema-retrieval/`](../schema-retrieval/) folder.

## Privacy / ethics — important

- **Do NOT publish** completed exam papers, handwriting, free-text answers, or any
  identifiers — they are not needed to reproduce the reported statistics.
- The per-participant scores are **not released**; the paper states they are "available from
  the corresponding author on reasonable request."
- Keep this folder consistent with the ethics / informed-consent statement in the paper.
  (Note: `THREATS-TO-VALIDITY.md` currently labels the experiment "§6.4 / RQ2"; align the
  section number with the final manuscript.)
