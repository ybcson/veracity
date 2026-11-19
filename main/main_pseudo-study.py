import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.pipeline import compare_formulations, compute_scores, load_data, setup


def main():
    # parameters
    input_files = ["pseudo_movie.csv", "pseudo_game.csv"]   # data/<file name> ; LLM pseudo-user feedback (one row = one reason, input format in README)
    output_dir = "output/pseudo"                            # results folder (relative to repo root)
    threshold = 0.5                                         # standard SDT dichotomization ; feedback >= threshold -> "yes"
    feedback_type = "correctness"                           # "correctness" (how correct the reason is) · "presence" (how much the item has / user likes the feature, Fig. 5)
    fuzzy_mapping = "fig3"                                  # "fig3" (consistent with standard; equals standard for 0/1 feedback) · "fig5" (manuscript Fig. 5 as written)

    # run
    cfg, paths, out_dir = setup(input_files, output_dir, threshold, feedback_type, fuzzy_mapping)

    # 1. load feedback
    records = load_data(paths)

    # 2. fidelity · attunement · veracity scores (per user -> averaged per domain x case)
    user_rows, _ = compute_scores(records, cfg, out_dir)

    # 3. paired t-tests between veracity formulations (Vp vs Vr · Vp vs Va · Va vs Vr)
    compare_formulations(user_rows, out_dir)


if __name__ == "__main__":
    main()
