# §6.3 Figure Data — Aggregated (per-language) Statistics

These tables are the **per-language aggregated** statistics behind Figures 6–10,
extracted from `../../performance/plot_figures.py` (functions `fig6`–`fig10`). They are
group-level means/SDs only — **no individual-participant records** — so they are safe
to release as-is.

| File | Figures | Contents |
|---|---|---|
| `exam_score_time_retention.csv` | Fig 6, 9, 10 | per language: final-exam score mean/SD, completion-time mean/SD (min), skill-decline rate, memory-retention score |
| `score_by_question_type.csv` | Fig 7 | per language × question type (Query Writing / Reading / Result Prediction): score mean/SD |
| `error_distribution.csv` | Fig 8 | per language: error-rate distribution over Syntactic (S) / Semantic (L) / Value (V) / Minor (M) |
| `welch_anova.py` | §6.4.2 | recomputes the between-group test from the summary statistics above: Welch's ANOVA (reported), the classical one-way ANOVA as a cross-check, and the per-language mean / SD / 95% CI the paper points here for |

Notes:
- `memory_retention_score = final_exam_score_mean × (1 − skill_decline_rate)` (derived).
- The paper reports **Welch's ANOVA**, not the classical one-way test: the group variances
  differ by 16.2x (score) and 22.1x (time), so homogeneity does not hold. Welch's test is a
  function of group means, variances and sizes alone, so `welch_anova.py` reproduces the
  paper's F, df and p from this group-level data — no per-participant records needed.
- The radar chart (Fig 10) also uses the §6.2 conciseness metrics (LOC, syntactic
  noise, Halstead); those live under `../../conciseness/`, not here.

## Individual 49-participant scores are NOT here

`plot_figures.py` stores only the aggregates above; the **individual per-student scores
are not in it**, and the per-participant (`P1…P49`) score records are **not released** —
they are available from the corresponding author on reasonable request (see the paper's
data-availability statement). Only the group-level aggregates here are published.

## Note on the standard error

The error bars in Figure 6 use the standard error of the mean with **N = 5**
(`Score_SEM = Score_SD / sqrt(5)`), retained as-is by author decision.
