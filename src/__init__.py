"""Veracity: SDT-based information quality metric for recommender-system explanations."""
from .scoring import METRICS, Config, score_system, score_user
from .sdt import a_prime, b_double_prime_d, hit_fa_rates

__all__ = ["METRICS", "Config", "score_system", "score_user", "a_prime", "b_double_prime_d", "hit_fa_rates"]
