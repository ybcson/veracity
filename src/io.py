"""Loading feedback files and writing / printing results."""
from __future__ import annotations

import csv
import math
from pathlib import Path

from .scoring import METRICS

REQUIRED = ("user_id", "claim_fid", "claim_att", "fid_feedback", "att_feedback")
OPTIONAL_DEFAULTS = {"domain": "all", "case": "all"}

_TRUE = {"1", "yes", "y", "true", "t", "has", "like", "likes"}
_FALSE = {"0", "no", "n", "false", "f", "not", "dislike", "dislikes"}


def _parse_claim(value: str, col: str, line: int) -> int:
    v = str(value).strip().lower()
    if v in _TRUE:
        return 1
    if v in _FALSE:
        return 0
    raise ValueError(f"line {line}: {col}={value!r} must be 1/0 (yes/no)")


def _parse_feedback(value: str, col: str, line: int) -> float:
    try:
        x = float(value)
    except ValueError:
        raise ValueError(f"line {line}: {col}={value!r} is not a number") from None
    if not (0.0 <= x <= 1.0) or math.isnan(x):
        raise ValueError(f"line {line}: {col}={x} must be in [0, 1]")
    return x


def load_feedback(path: str | Path) -> list[dict]:
    """Read a long-format feedback CSV (one row per explanation reason / assertion)."""
    records = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = [c for c in REQUIRED if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{path}: missing required columns {missing}")
        for i, row in enumerate(reader, start=2):
            rec = dict(row)
            for col, default in OPTIONAL_DEFAULTS.items():
                rec[col] = (row.get(col) or default).strip()
            rec["user_id"] = row["user_id"].strip()
            rec["claim_fid"] = _parse_claim(row["claim_fid"], "claim_fid", i)
            rec["claim_att"] = _parse_claim(row["claim_att"], "claim_att", i)
            rec["fid_feedback"] = _parse_feedback(row["fid_feedback"], "fid_feedback", i)
            rec["att_feedback"] = _parse_feedback(row["att_feedback"], "att_feedback", i)
            records.append(rec)
    if not records:
        raise ValueError(f"{path}: no rows")
    return records


def write_csv(rows: list[dict], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.6f}" if isinstance(v, float) else v) for k, v in r.items()})


def read_system_csv(path: str | Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for m in METRICS:
            r[m] = float(r[m]) if r.get(m) not in (None, "") else float("nan")
    return rows


def format_table(system_rows: list[dict]) -> str:
    """Table 2 / Table 3 layout: sensitivity and B''_D per metric, per case."""
    head = f"{'domain':<10} {'case':<6} {'n':>3}  " + "  ".join(f"{m:>6} {'B″D':>6}" for m in METRICS)
    lines = [head, "-" * len(head)]
    for r in system_rows:
        cells = "  ".join(f"{_fmt(r[m])} {_fmt(r[f'{m}_bias'])}" for m in METRICS)
        lines.append(f"{str(r['domain']):<10} {str(r['case']):<6} {r['n_users']:>3}  {cells}")
    return "\n".join(lines)


def _fmt(x: float) -> str:
    return f"{'nan':>6}" if math.isnan(x) else f"{x:>6.3f}"
