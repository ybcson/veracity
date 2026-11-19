"""User-level and system-level scores (Algorithm 1, Eq. 6)."""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass

from .outcomes import (
    OUTCOMES,
    combine_fuzzy,
    combine_standard,
    feedback_to_truth,
    fuzzy_outcome,
    standard_outcome,
)
from .sdt import a_prime, b_double_prime_d, hit_fa_rates

# F/A/Va/Vr/Vp: standard SDT.  Fx/Ax/Vx: fuzzy SDT.
METRICS = ("F", "A", "Va", "Vr", "Vp", "Fx", "Ax", "Vx")


@dataclass(frozen=True)
class Config:
    threshold: float = 0.5               # standard SDT: feedback >= threshold -> "yes"
    feedback_type: str = "correctness"   # see outcomes.feedback_to_truth
    fuzzy_mapping: str = "fig3"          # see outcomes.fuzzy_outcome


def record_outcomes(rec: dict, cfg: Config) -> dict[str, dict[str, float]]:
    """All eight outcome vectors (H, M, FA, CR) for one assertion record."""
    cf, ca = rec["claim_fid"], rec["claim_att"]
    ff, fa = rec["fid_feedback"], rec["att_feedback"]

    # standard: dichotomise feedback, then read truth off the confusion matrix
    t_fid = round(feedback_to_truth(cf, 1.0 if ff >= cfg.threshold else 0.0, cfg.feedback_type))
    t_att = round(feedback_to_truth(ca, 1.0 if fa >= cfg.threshold else 0.0, cfg.feedback_type))
    o_fid = standard_outcome(cf, t_fid)
    o_att = standard_outcome(ca, t_att)

    # fuzzy: feedback used directly as membership degree
    x_fid = fuzzy_outcome(cf, feedback_to_truth(cf, ff, cfg.feedback_type), cfg.fuzzy_mapping)
    x_att = fuzzy_outcome(ca, feedback_to_truth(ca, fa, cfg.feedback_type), cfg.fuzzy_mapping)

    return {
        "F": {k: float(k == o_fid) for k in OUTCOMES},
        "A": {k: float(k == o_att) for k in OUTCOMES},
        "Va": combine_standard(o_fid, o_att, "average"),
        "Vr": combine_standard(o_fid, o_att, "restrictive"),
        "Vp": combine_standard(o_fid, o_att, "permissive"),
        "Fx": x_fid,
        "Ax": x_att,
        "Vx": combine_fuzzy(x_fid, x_att),
    }


def score_user(records: list[dict], cfg: Config) -> dict[str, dict[str, float]]:
    """User-level sensitivity (A') and bias (B''_D) for every metric."""
    sums = {m: {k: 0.0 for k in OUTCOMES} for m in METRICS}
    for rec in records:
        for m, vec in record_outcomes(rec, cfg).items():
            for k in OUTCOMES:
                sums[m][k] += vec[k]

    out = {}
    for m in METRICS:
        s = sums[m]
        hr, far = hit_fa_rates(s["H"], s["M"], s["FA"], s["CR"])
        out[m] = {
            "sens": a_prime(hr, far),
            "bias": b_double_prime_d(hr, far),
            "HR": hr,
            "FAR": far,
            **s,
        }
    return out


def _nanmean(xs: list[float]) -> float:
    vals = [x for x in xs if not math.isnan(x)]
    return sum(vals) / len(vals) if vals else float("nan")


def score_system(records: list[dict], cfg: Config):
    """Score every (domain, case) condition.

    Returns
      user_rows   : one row per (domain, case, user) with per-user scores
      system_rows : one row per (domain, case) with the user-averaged scores
                    (Eq. 6: V = mean_u v_u) -- the system's veracity.
    Users whose HR or FAR is undefined for a metric are excluded from that
    metric's mean; the counts are reported in n_valid_<metric>.
    """
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for rec in records:
        groups[(rec["domain"], rec["case"], rec["user_id"])].append(rec)

    user_rows = []
    for (domain, case, user), recs in sorted(groups.items(), key=lambda kv: _sort_key(kv[0])):
        scores = score_user(recs, cfg)
        row = {"domain": domain, "case": case, "user_id": user, "n_assertions": len(recs)}
        for m in METRICS:
            row[m] = scores[m]["sens"]
            row[f"{m}_bias"] = scores[m]["bias"]
            row[f"{m}_HR"] = scores[m]["HR"]
            row[f"{m}_FAR"] = scores[m]["FAR"]
        user_rows.append(row)

    by_cond: dict[tuple, list[dict]] = defaultdict(list)
    for row in user_rows:
        by_cond[(row["domain"], row["case"])].append(row)

    system_rows = []
    for (domain, case), rows in sorted(by_cond.items(), key=lambda kv: _sort_key(kv[0])):
        srow = {"domain": domain, "case": case, "n_users": len(rows)}
        for m in METRICS:
            srow[m] = _nanmean([r[m] for r in rows])
            srow[f"{m}_bias"] = _nanmean([r[f"{m}_bias"] for r in rows])
        for m in METRICS:
            srow[f"n_valid_{m}"] = sum(not math.isnan(r[m]) for r in rows)
        system_rows.append(srow)
    return user_rows, system_rows


def _sort_key(key: tuple) -> tuple:
    """Sort numerically where possible (case '10' after case '2')."""
    return tuple((0, float(k), "") if _is_number(k) else (1, 0.0, str(k)) for k in key)


def _is_number(x) -> bool:
    try:
        float(x)
        return True
    except (TypeError, ValueError):
        return False
