#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§6.4 (RQ2) between-group statistics — Welch's ANOVA, Games-Howell post-hoc, 95% CIs.

Why Welch. The seven groups have markedly unequal variances (largest-to-smallest variance
ratio 16.2 on score, 22.1 on time), so the homogeneity-of-variance assumption behind the
classical one-way ANOVA does not hold. Welch's ANOVA does not assume it. With n = 7 per
group the classical test is exactly where a reviewer would push, so the robust test is the
one the paper reports.

What it needs. Welch's ANOVA is a function of the group means, variances and sizes alone --
no per-participant records are required. `exam_score_time_retention.csv` carries all three
(n = 7 per group), which is why this reproduces the paper's numbers from the released
group-level data.

Reproduces (paper §6.4.2):
    score  Welch F(6, 18.3) = 12.54, p < 0.001, eta^2 = 0.58
    time   Welch F(6, 18.4) = 27.43, p < 0.001, eta^2 = 0.72
    post-hoc on score: DCQL > MQL, XQuery, JSONiq, OQL; DCQL vs SQL and N1QL not significant
    post-hoc on time : DCQL faster than every baseline (all p < 0.05)

The post-hoc is Games-Howell, not Tukey HSD: Tukey assumes the equal variances that the
variance ratios above rule out, so pairing it with a Welch omnibus test would be
inconsistent. Games-Howell makes the same Welch-style adjustment pairwise. It reaches the
same verdicts the Tukey test originally reported.

The classical F(6, 42) = 9.81 / 18.05 is also recomputed below as a cross-check: it matches
the value the paper reported before the switch, which confirms the summary statistics and
the formulas agree with the original run.

Also prints the per-language mean, SD and 95% confidence interval that §6.4.2 refers to
(CI = mean +/- t(0.975, 6) * SD / sqrt(n); the paper cites the repository for these).

Run:  python3 welch_anova.py          (scipy optional; a hardcoded t critical value is used
                                      when it is absent, and p-values are then omitted)
"""
import csv, math, os

try:
    from scipy import stats
    HAVE_SCIPY = True
except ImportError:
    HAVE_SCIPY = False

T_CRIT_975_DF6 = 2.446912  # t(0.975, df = n-1 = 6); used when scipy is unavailable

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "exam_score_time_retention.csv")
N_PER_GROUP = 7


def welch_anova(means, sds, n):
    """Welch's ANOVA from summary statistics. Returns (F, df1, df2).

    w_i = n_i / s_i^2 are the precision weights; groups with larger variance count less,
    which is exactly what the classical test fails to do.
    """
    k = len(means)
    w = [n / (s ** 2) for s in sds]
    sw = sum(w)
    mw = sum(wi * mi for wi, mi in zip(w, means)) / sw
    A = sum(wi * (mi - mw) ** 2 for wi, mi in zip(w, means)) / (k - 1)
    lam = sum(((1 - wi / sw) ** 2) / (n - 1) for wi in w)
    B = 1 + (2 * (k - 2) / (k ** 2 - 1)) * lam
    df2 = 1 / ((3 / (k ** 2 - 1)) * lam)
    return A / B, k - 1, df2


def classic_anova(means, sds, n):
    """Classical one-way ANOVA from summary statistics. Returns (F, df1, df2, eta^2)."""
    k = len(means)
    N = k * n
    grand = sum(n * m for m in means) / N
    ssb = sum(n * (m - grand) ** 2 for m in means)
    ssw = sum((n - 1) * s ** 2 for s in sds)
    return (ssb / (k - 1)) / (ssw / (N - k)), k - 1, N - k, ssb / (ssb + ssw)


def variance_ratio(sds):
    """Largest-to-smallest variance ratio (Hartley's F_max). > 4 signals heterogeneity."""
    v = [s ** 2 for s in sds]
    return max(v) / min(v)


def games_howell(mi, mj, si, sj, n, k):
    """Games-Howell pairwise comparison. Returns (q, df, p or None).

    The variance-heterogeneous counterpart of Tukey HSD: a studentized-range statistic on
    a Welch-Satterthwaite df, so it needs only the two group means, SDs and sizes.
    """
    vi, vj = si ** 2 / n, sj ** 2 / n
    q = abs(mi - mj) / math.sqrt((vi + vj) / 2)
    df = (vi + vj) ** 2 / ((vi ** 2) / (n - 1) + (vj ** 2) / (n - 1))
    p = None
    if HAVE_SCIPY:
        from scipy.stats import studentized_range
        p = studentized_range.sf(q, k, df)
    return q, df, p


def ci95(mean, sd, n):
    """Two-sided 95% CI for a group mean: mean +/- t(0.975, n-1) * SD / sqrt(n)."""
    t = stats.t.ppf(0.975, n - 1) if HAVE_SCIPY else T_CRIT_975_DF6
    h = t * sd / math.sqrt(n)
    return mean - h, mean + h


def main():
    rows = list(csv.DictReader(open(CSV, encoding="utf-8")))
    n = N_PER_GROUP
    for label, mkey, skey in [
        ("score", "final_exam_score_mean", "final_exam_score_sd"),
        ("time ", "final_exam_time_min_mean", "final_exam_time_min_sd"),
    ]:
        means = [float(r[mkey]) for r in rows]
        sds = [float(r[skey]) for r in rows]

        Fw, d1w, d2w = welch_anova(means, sds, n)
        Fc, d1c, d2c, eta2 = classic_anova(means, sds, n)
        fmax = variance_ratio(sds)

        pw = f"p = {stats.f.sf(Fw, d1w, d2w):.2e}" if HAVE_SCIPY else "p: install scipy"
        pc = f"p = {stats.f.sf(Fc, d1c, d2c):.2e}" if HAVE_SCIPY else "p: install scipy"

        print(f"[{label}] variance ratio F_max = {fmax:.1f} "
              f"({'heterogeneous -> Welch' if fmax > 4 else 'homogeneous'})")
        print(f"         Welch     F({d1w}, {d2w:.1f}) = {Fw:.2f}, {pw}, eta^2 = {eta2:.2f}   <- reported")
        print(f"         classical F({d1c}, {d2c}) = {Fc:.2f}, {pc}   (cross-check only)")
        print()

    langs = [r["language"] for r in rows]
    d = langs.index("DCQL")
    for label, mkey, skey, unit in [
        ("score", "final_exam_score_mean", "final_exam_score_sd", ""),
        ("time", "final_exam_time_min_mean", "final_exam_time_min_sd", " min"),
    ]:
        ms = [float(r[mkey]) for r in rows]
        ss = [float(r[skey]) for r in rows]
        print(f"Games-Howell post-hoc on {label}, DCQL vs each baseline (k = {len(langs)}):")
        for i, L in enumerate(langs):
            if L == "DCQL":
                continue
            q, df, p = games_howell(ms[d], ms[i], ss[d], ss[i], n, len(langs))
            ps = f"p = {p:.4f}" if p is not None else "p: install scipy"
            verdict = ("significant" if (p is not None and p < 0.05)
                       else "not significant" if p is not None else "")
            print(f"    DCQL vs {L:<8} diff {ms[d]-ms[i]:+6.1f}{unit}   q = {q:5.2f}   "
                  f"df = {df:5.1f}   {ps}   {verdict}")
        print()
    print("eta^2 is the classical between-group variance share, reported as the effect size.")
    print("Group sizes are equal (n = 7), so it is unaffected by the Welch adjustment.")
    print()
    for label, mkey, skey, unit in [
        ("score", "final_exam_score_mean", "final_exam_score_sd", ""),
        ("time", "final_exam_time_min_mean", "final_exam_time_min_sd", " min"),
    ]:
        print(f"Per-language {label}: mean, SD, 95% CI (n = {n} per group)")
        for r in rows:
            m, sd = float(r[mkey]), float(r[skey])
            lo, hi = ci95(m, sd, n)
            print(f"    {r['language']:<8} {m:6.1f}{unit}   SD {sd:5.2f}   "
                  f"95% CI [{lo:6.2f}, {hi:6.2f}]")
        print()


if __name__ == "__main__":
    main()
