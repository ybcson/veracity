"""Per-assertion SDT outcomes for fidelity, attunement and veracity (Section 3).

Every explanation reason makes two assertions:
  * fidelity claim   : "the item HAS (1) / does NOT have (0) [feature]"
  * attunement claim : "you LIKE (1) / DISLIKE (0) [feature]"

The user's feedback tells us the truth of each assertion. Following Figure 3,
the *truth* (item really has the feature / user really likes it) is the signal
and the XRS claim is the response:

                     truth = 1     truth = 0
    XRS claim = 1      Hit           FA
    XRS claim = 0      Miss          CR
"""
from __future__ import annotations

OUTCOMES = ("H", "M", "FA", "CR")
CORRECT = frozenset({"H", "CR"})

COMBINE_RULES = ("average", "restrictive", "permissive")
FUZZY_MAPPINGS = ("fig3", "fig5")
FEEDBACK_TYPES = ("correctness", "presence")


# --------------------------------------------------------------------------- #
# Feedback -> truth
# --------------------------------------------------------------------------- #
def feedback_to_truth(claim: int, feedback: float, feedback_type: str) -> float:
    """Turn a feedback value into the degree to which the feature is truly present / liked.

    feedback_type
      "correctness": feedback = how correct the reason is (the human study's sliders:
                     "how accurate is this reason", "how well does it match you").
                     truth = feedback if the claim is positive, else 1 - feedback.
      "presence"   : feedback = degree the item has the feature / user likes it
                     (the "Item Has Feature" / "User Likes Feature" columns of Fig. 5).
    """
    if feedback_type == "correctness":
        return feedback if claim == 1 else 1.0 - feedback
    if feedback_type == "presence":
        return feedback
    raise ValueError(f"unknown feedback_type: {feedback_type!r}")


# --------------------------------------------------------------------------- #
# Standard (crisp) SDT
# --------------------------------------------------------------------------- #
def standard_outcome(claim: int, truth: int) -> str:
    """Fidelity / attunement outcome from the Figure 3 confusion matrix."""
    if truth:
        return "H" if claim else "M"
    return "FA" if claim else "CR"


def _one_hot(label: str) -> dict[str, float]:
    return {k: (1.0 if k == label else 0.0) for k in OUTCOMES}


def combine_standard(o_fid: str, o_att: str, rule: str) -> dict[str, float]:
    """Veracity outcome from fidelity + attunement outcomes (Figure 4).

    average     : 0.5 credit to each outcome.
    restrictive : if exactly one is incorrect (M/FA), it takes full credit.
    permissive  : if exactly one is correct (H/CR), it takes full credit.
    Identical outcomes -> that outcome. Both correct or both incorrect but
    different -> 0.5 / 0.5 under every rule.
    """
    if rule not in COMBINE_RULES:
        raise ValueError(f"unknown rule: {rule!r}")
    if o_fid == o_att:
        return _one_hot(o_fid)

    half = {k: 0.0 for k in OUTCOMES}
    half[o_fid] = 0.5
    half[o_att] = 0.5
    if rule == "average":
        return half

    fid_ok, att_ok = o_fid in CORRECT, o_att in CORRECT
    if fid_ok == att_ok:
        return half
    if rule == "restrictive":
        return _one_hot(o_att if fid_ok else o_fid)
    return _one_hot(o_fid if fid_ok else o_att)  # permissive


# --------------------------------------------------------------------------- #
# Fuzzy SDT (Parasuraman, Masalonis & Hancock, 2000)
# --------------------------------------------------------------------------- #
def fuzzy_outcome(claim: int, truth: float, mapping: str = "fig3") -> dict[str, float]:
    """Fuzzy outcome memberships with signal s and response r in [0, 1]:

        H = min(s, r)   M = max(s - r, 0)   FA = max(r - s, 0)   CR = min(1 - s, 1 - r)

    mapping
      "fig3": s = truth (fuzzy), r = claim (crisp). Same roles as Figure 3, so with
              0/1 feedback it reduces exactly to the standard formulation.
      "fig5": s = claim (crisp), r = truth (fuzzy). Reproduces Figure 5 / Section 3.2.1
              literally ("claims has -> H = f, M = 1 - f; claims not -> FA = f, CR = 1 - f").
    """
    if mapping == "fig3":
        s, r = truth, float(claim)
    elif mapping == "fig5":
        s, r = float(claim), truth
    else:
        raise ValueError(f"unknown fuzzy mapping: {mapping!r}")
    return {
        "H": min(s, r),
        "M": max(s - r, 0.0),
        "FA": max(r - s, 0.0),
        "CR": min(1.0 - s, 1.0 - r),
    }


def combine_fuzzy(o_fid: dict[str, float], o_att: dict[str, float]) -> dict[str, float]:
    """Fuzzy veracity outcome = average of fidelity and attunement memberships."""
    return {k: (o_fid[k] + o_att[k]) / 2.0 for k in OUTCOMES}
