"""Generate synthetic feedback CSVs in the expected input format (for testing only).

    python src/make_synthetic_data.py
"""
from __future__ import annotations

import csv
import random
from pathlib import Path

# P(assertion is correct) for (fidelity, attunement) per explanation quality case.
CASES = {1: (0.95, 0.95), 2: (0.90, 0.25), 3: (0.25, 0.90), 4: (0.20, 0.20)}
FIELDS = ["domain", "user_id", "case", "item_id", "reason_id",
          "claim_fid", "claim_att", "fid_feedback", "att_feedback"]


def feedback(correct: bool, rng: random.Random, sharp: float) -> float:
    """Correctness-type slider value: high if the assertion is correct."""
    x = rng.betavariate(sharp, 2) if correct else rng.betavariate(2, sharp)
    return round(x, 2)


def make(path: Path, domain: str, n_users: int, n_items: int, n_reasons: int, sharp: float, seed: int) -> None:
    rng = random.Random(seed)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for u in range(1, n_users + 1):
            for case, (p_fid, p_att) in CASES.items():
                for i in range(1, n_items + 1):
                    for k in range(1, n_reasons + 1):
                        w.writerow({
                            "domain": domain, "user_id": f"u{u:02d}", "case": case,
                            "item_id": f"item{i}", "reason_id": k,
                            "claim_fid": int(rng.random() < 0.7),   # mostly "item has feature"
                            "claim_att": int(rng.random() < 0.7),   # mostly "you like feature"
                            "fid_feedback": feedback(rng.random() < p_fid, rng, sharp),
                            "att_feedback": feedback(rng.random() < p_att, rng, sharp),
                        })


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1] / "data"
    make(root / "pseudo_movie.csv", "movie", n_users=20, n_items=10, n_reasons=1, sharp=8, seed=1)
    make(root / "pseudo_game.csv", "game", n_users=20, n_items=10, n_reasons=1, sharp=8, seed=2)
    make(root / "human_movie.csv", "movie", n_users=30, n_items=3, n_reasons=3, sharp=4, seed=3)
    print(f"wrote synthetic CSVs to {root}")
