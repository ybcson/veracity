"""Steps called by main/main_pseudo-study.py and main/main_human-study.py."""
from __future__ import annotations

from pathlib import Path

from .io import format_table, load_feedback, read_system_csv, write_csv
from .outcomes import FEEDBACK_TYPES, FUZZY_MAPPINGS
from .scoring import Config, score_system
from .stats import paired_t, pearson

ROOT = Path(__file__).resolve().parents[1]

# Section 5.3: paired t-tests between the standard veracity formulations.
COMPARISONS = [("Vp", "Vr"), ("Vp", "Va"), ("Va", "Vr")]

# Section 6.7: correlations per dimension, pooling the formulations of that dimension.
DIMENSIONS = {
    "Fidelity": ("F", "Fx"),
    "Attunement": ("A", "Ax"),
    "Veracity": ("Va", "Vr", "Vp", "Vx"),
}


# --------------------------------------------------------------------------- #
# setup
# --------------------------------------------------------------------------- #
def setup(input_files: list[str], output_dir: str, threshold: float, feedback_type: str, fuzzy_mapping: str):
    """Validate parameters and resolve paths (relative to the repo root)."""
    if feedback_type not in FEEDBACK_TYPES:
        raise ValueError(f"feedback_type must be one of {FEEDBACK_TYPES}")
    if fuzzy_mapping not in FUZZY_MAPPINGS:
        raise ValueError(f"fuzzy_mapping must be one of {FUZZY_MAPPINGS}")
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be in [0, 1]")

    paths = [ROOT / "data" / f for f in input_files]
    missing = [str(p) for p in paths if not p.exists()]
    if missing:
        raise FileNotFoundError(f"input files not found: {missing}")

    cfg = Config(threshold=threshold, feedback_type=feedback_type, fuzzy_mapping=fuzzy_mapping)
    out_dir = ROOT / output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"[setup] {cfg}\n[setup] input: {[p.name for p in paths]}\n[setup] output: {out_dir}\n")
    return cfg, paths, out_dir


# --------------------------------------------------------------------------- #
# steps
# --------------------------------------------------------------------------- #
def load_data(paths: list[Path]) -> list[dict]:
    records = [r for p in paths for r in load_feedback(p)]
    n_users = len({(r["domain"], r["user_id"]) for r in records})
    print(f"[load] {len(records)} assertions, {n_users} users")
    return records


def compute_scores(records: list[dict], cfg: Config, out_dir: Path):
    """Fidelity / attunement / veracity per user, then averaged per (domain, case)."""
    user_rows, system_rows = score_system(records, cfg)
    write_csv(user_rows, out_dir / "user_scores.csv")
    write_csv(system_rows, out_dir / "system_scores.csv")
    print("\n[score] system-level scores (mean of user-level A' and B''_D)")
    print(format_table(system_rows))
    return user_rows, system_rows


def compare_formulations(user_rows: list[dict], out_dir: Path) -> list[dict]:
    """Paired t-tests on user-level scores across (domain, case, user) units."""
    tests = []
    print("\n[t-test] veracity formulations")
    for a, b in COMPARISONS:
        res = paired_t([r[a] for r in user_rows], [r[b] for r in user_rows])
        tests.append({"comparison": f"{a} vs {b}", **res})
        print(f"  {a} vs {b}: mean diff = {res['mean_diff']:+.4f}, t({res['df']}) = {res['t']:.3f}, p = {res['p']:.4g}")
    write_csv(tests, out_dir / "ttests.csv")
    return tests


def correlate_with_pseudo(system_rows: list[dict], pseudo_scores: str, pseudo_domain: str | None, out_dir: Path):
    """Pearson r between pseudo-user and human system-level scores, per dimension."""
    path = ROOT / pseudo_scores
    if not path.exists():
        print(f"\n[corr] skipped — {path} not found (run main_pseudo-study first)")
        return None

    pseudo = {str(r["case"]): r for r in read_system_csv(path) if pseudo_domain is None or r["domain"] == pseudo_domain}
    results = []
    print(f"\n[corr] Pearson correlation with pseudo-user study ({pseudo_domain})")
    for dim, metrics in DIMENSIONS.items():
        xs, ys = [], []
        for h in system_rows:
            p = pseudo.get(str(h["case"]))
            if p is None:
                continue
            for m in metrics:
                xs.append(p[m])
                ys.append(h[m])
        res = pearson(xs, ys)
        results.append({"dimension": dim, "metrics": "+".join(metrics), **res})
        print(f"  {dim:<10} ({'+'.join(metrics)}): r = {res['r']:.3f}, p = {res['p']:.4g}, n = {res['n']}")
    write_csv(results, out_dir / "correlation_with_pseudo.csv")
    return results
