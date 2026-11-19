"""Non-parametric SDT measures used by the paper (Section 2.3).

- Hit rate / false-alarm rate (Eqs. 2, 3, 7). Outcome counts may be fractional
  (veracity "0.5 credit" outcomes and fuzzy memberships).
- A'    sensitivity (Eq. 4)
- B''_D bias        (Eq. 5)
"""
from __future__ import annotations

import math

NAN = float("nan")


def hit_fa_rates(h: float, m: float, fa: float, cr: float) -> tuple[float, float]:
    """HR = H / (H + M), FAR = FA / (FA + CR).

    H + M is the (possibly fuzzy) number of signal trials and FA + CR the number
    of noise trials, so this matches Eq. (2)/(3) for crisp outcomes and Eq. (7)
    for fuzzy ones. Returns NaN for a rate whose denominator is 0.
    """
    n_signal = h + m
    n_noise = fa + cr
    hr = h / n_signal if n_signal > 0 else NAN
    far = fa / n_noise if n_noise > 0 else NAN
    return hr, far


def a_prime(hr: float, far: float) -> float:
    """A' (Eq. 4).

    NOTE: the manuscript prints (HR x FAR)(1 + HR x FAR); the standard formula
    (Macmillan; Stanislaw & Todorov, 1999) uses the *difference* HR - FAR.
    With the product, perfect discrimination (HR=1, FAR=0) would give 0.5,
    so the difference is used here.
    """
    if math.isnan(hr) or math.isnan(far):
        return NAN
    if math.isclose(hr, far):
        return 0.5
    if hr > far:
        d = hr - far
        return 0.5 + (d * (1 + d)) / (4 * hr * (1 - far))
    d = far - hr
    return 0.5 - (d * (1 + d)) / (4 * far * (1 - hr))


def b_double_prime_d(hr: float, far: float) -> float:
    """B''_D (Eq. 5). > 0 conservative, < 0 liberal, 0 neutral."""
    if math.isnan(hr) or math.isnan(far):
        return NAN
    num = (1 - hr) * (1 - far) - hr * far
    den = (1 - hr) * (1 - far) + hr * far
    if den == 0:  # (HR, FAR) = (1, 0) or (0, 1): no bias is defined
        return 0.0
    return num / den
