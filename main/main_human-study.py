import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.pipeline import compute_scores, correlate_with_pseudo, load_data, setup


def main():
    # parameters
    input_files = ["human_movie.csv"]                       # data/<file name> ; participant feedback from the web app (sliders 0–1, one row = one reason)
    output_dir = "output/human"                             # results folder (relative to repo root)
    threshold = 0.5                                         # standard SDT dichotomization ; slider >= 0.5 -> "yes" (Section 6.4)
    feedback_type = "correctness"                           # "correctness" (how correct the reason is) · "presence" (how much the item has / user likes the feature, Fig. 5)
    fuzzy_mapping = "fig3"                                  # "fig3" (consistent with standard; equals standard for 0/1 feedback) · "fig5" (manuscript Fig. 5 as written)
    pseudo_scores = "output/pseudo/system_scores.csv"       # output of main_pseudo-study ; correlation is skipped if missing
    pseudo_domain = "movie"                                 # domain in the pseudo results to compare against

    # run
    cfg, paths, out_dir = setup(input_files, output_dir, threshold, feedback_type, fuzzy_mapping)

    # 1. load feedback
    records = load_data(paths)

    # 2. fidelity · attunement · veracity scores (per participant -> averaged per case)
    _, system_rows = compute_scores(records, cfg, out_dir)

    # 3. Pearson correlation with the pseudo-user study
    correlate_with_pseudo(system_rows, pseudo_scores, pseudo_domain, out_dir)


if __name__ == "__main__":
    main()
