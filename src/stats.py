"""Paired t-test and Pearson correlation without SciPy dependencies."""
from __future__ import annotations

import math


def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction for the incomplete beta function (Numerical Recipes)."""
    max_iter, eps, fpmin = 300, 3e-14, 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > fpmin else fpmin)
    h = d
    for m in range(1, max_iter + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > fpmin else fpmin)
        c = 1.0 + aa / c
        c = c if abs(c) > fpmin else fpmin
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > fpmin else fpmin)
        c = 1.0 + aa / c
        c = c if abs(c) > fpmin else fpmin
        de = d * c
        h *= de
        if abs(de - 1.0) < eps:
            break
    return h


def _betai(a: float, b: float, x: float) -> float:
    """Regularised incomplete beta I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbt = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x)
    bt = math.exp(lbt)
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def t_two_sided_p(t: float, df: int) -> float:
    if math.isinf(t):
        return 0.0
    return _betai(df / 2.0, 0.5, df / (df + t * t))


def _pairs(x, y):
    return [(a, b) for a, b in zip(x, y) if not (math.isnan(a) or math.isnan(b))]


def paired_t(x: list[float], y: list[float]) -> dict:
    """Paired t-test of x - y (NaN pairs dropped)."""
    pairs = _pairs(x, y)
    n = len(pairs)
    if n < 2:
        return {"n": n, "mean_diff": float("nan"), "t": float("nan"), "df": n - 1, "p": float("nan")}
    diffs = [a - b for a, b in pairs]
    mean = sum(diffs) / n
    var = sum((d - mean) ** 2 for d in diffs) / (n - 1)
    if var == 0:
        t = 0.0 if mean == 0 else math.copysign(math.inf, mean)
    else:
        t = mean / math.sqrt(var / n)
    return {"n": n, "mean_diff": mean, "t": t, "df": n - 1, "p": t_two_sided_p(t, n - 1)}


def pearson(x: list[float], y: list[float]) -> dict:
    pairs = _pairs(x, y)
    n = len(pairs)
    if n < 3:
        return {"n": n, "r": float("nan"), "p": float("nan")}
    mx = sum(a for a, _ in pairs) / n
    my = sum(b for _, b in pairs) / n
    sxy = sum((a - mx) * (b - my) for a, b in pairs)
    sxx = sum((a - mx) ** 2 for a, _ in pairs)
    syy = sum((b - my) ** 2 for _, b in pairs)
    if sxx == 0 or syy == 0:
        return {"n": n, "r": float("nan"), "p": float("nan")}
    r = max(-1.0, min(1.0, sxy / math.sqrt(sxx * syy)))
    if abs(r) == 1.0:
        return {"n": n, "r": r, "p": 0.0}
    t = r * math.sqrt((n - 2) / (1 - r * r))
    return {"n": n, "r": r, "p": t_two_sided_p(t, n - 2)}
