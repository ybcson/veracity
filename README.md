# Veracity

SDT-based information quality metric for XRS explanations (Son & Bolton).
Pure Python 3.10+, no dependencies.

```bash
python src/make_synthetic_data.py   # synthetic data for testing -> data/
python main/main_pseudo-study.py    # default input: data/pseudo_movie.csv data/pseudo_game.csv
python main/main_human-study.py     # default input: data/human_movie.csv (+ output/pseudo for correlation)
```

```
data/    input feedback CSVs
main/    main_pseudo-study.py, main_human-study.py
src/     sdt.py, outcomes.py, scoring.py, io.py, stats.py, make_synthetic_data.py
output/  pseudo/, human/ results
```

## Input format (long CSV, one row = one reason/assertion)

| column | required | meaning |
|---|---|---|
| `user_id` | ✓ | user / participant ID |
| `claim_fid` | ✓ | what the explanation says about the item: `1` = item **has** the feature, `0` = item does **not** have it |
| `claim_att` | ✓ | what the explanation says about the user: `1` = user **likes** the feature, `0` = user **dislikes** it |
| `fid_feedback` | ✓ | fidelity feedback in [0, 1] |
| `att_feedback` | ✓ | attunement feedback in [0, 1] |
| `case` | | explanation quality level (1–4). Scored separately; defaults to `all` |
| `domain` | | `movie`, `game`, ... ; defaults to `all` |
| `item_id`, `reason_id`, ... | | extra columns are ignored |

Meaning of the feedback (`--feedback-type`):
- `correctness` (default): "how correct is this reason" (the human-study sliders)
- `presence`: "how much the item has the feature / the user likes it" (Figure 5 columns)

Standard SDT dichotomises feedback at `>= --threshold` (0.5); fuzzy SDT uses the values directly.

## Output
- `system_scores.csv`: per domain × case, the **user-averaged** A′ (Eq. 6) and B″_D for
  F, A, Va, Vr, Vp, Fx, Ax, Vx → the system's veracity
- `user_scores.csv`: per-user scores, plus HR and FAR
- pseudo: `ttests.csv` (Vp–Vr, Vp–Va, Va–Vr paired t-tests)
- human: `correlation_with_pseudo.csv` (Pearson r per dimension)
