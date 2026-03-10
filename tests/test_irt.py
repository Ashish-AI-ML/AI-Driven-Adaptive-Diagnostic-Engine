"""
Unit tests for IRT (Item Response Theory) core functions.
Tests probability computation, theta updates, SEM, and normalization.
"""

import math
import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.engine.irt import (
    probability_3pl,
    update_theta,
    compute_sem,
    theta_to_difficulty,
    difficulty_to_theta,
    get_theta_descriptor,
    get_difficulty_band_label,
)


class TestProbability3PL:
    """Tests for the IRT 3PL probability function."""

    def test_output_in_valid_range(self):
        """P(correct) should always be between c and 1.0."""
        test_cases = [
            (0.0, 1.0, 0.0, 0.25),
            (2.0, 2.0, 0.5, 0.10),
            (-3.0, 1.0, -1.0, 0.30),
            (3.0, 0.5, 2.0, 0.20),
        ]
        for theta, a, b, c in test_cases:
            p = probability_3pl(theta, a, b, c)
            assert c <= p <= 1.0, f"P={p} out of range for theta={theta}, a={a}, b={b}, c={c}"

    def test_higher_ability_higher_probability(self):
        """Higher theta should yield higher P(correct), all else equal."""
        a, b, c = 1.5, 0.0, 0.20
        p_low = probability_3pl(-2.0, a, b, c)
        p_mid = probability_3pl(0.0, a, b, c)
        p_high = probability_3pl(2.0, a, b, c)
        assert p_low < p_mid < p_high

    def test_at_difficulty_level(self):
        """When theta = b (no guessing), P ≈ 0.5."""
        p = probability_3pl(0.5, 1.0, 0.5, 0.0)
        assert abs(p - 0.5) < 0.01

    def test_high_discrimination_sharper_transition(self):
        """Higher discrimination (a) should create sharper probability transitions."""
        b, c = 0.0, 0.0
        # With high discrimination, P below difficulty drops faster
        p_low_a = probability_3pl(-0.5, 0.5, b, c)
        p_high_a = probability_3pl(-0.5, 3.0, b, c)
        assert p_high_a < p_low_a  # High discrimination → lower P below b

    def test_guessing_floor(self):
        """Even very low ability should have at least c probability (guessing)."""
        c = 0.25
        p = probability_3pl(-10.0, 1.0, 0.0, c)
        assert p >= c - 0.01  # Allow tiny float tolerance


class TestUpdateTheta:
    """Tests for theta (ability) updating."""

    def test_correct_answer_increases_theta(self):
        """Correct answer should increase theta."""
        theta = 0.0
        new_theta = update_theta(theta, a=1.0, b=0.0, c=0.25, correct=True)
        assert new_theta > theta

    def test_incorrect_answer_decreases_theta(self):
        """Incorrect answer should decrease theta."""
        theta = 0.0
        new_theta = update_theta(theta, a=1.0, b=0.0, c=0.25, correct=False)
        assert new_theta < theta

    def test_theta_bounded(self):
        """Theta should never exceed [-3, +3] bounds."""
        # Test upper bound
        theta = update_theta(2.9, a=2.0, b=-2.0, c=0.0, correct=True)
        assert theta <= 3.0

        # Test lower bound
        theta = update_theta(-2.9, a=2.0, b=2.0, c=0.0, correct=False)
        assert theta >= -3.0

    def test_convergence_on_correct_streak(self):
        """Repeated correct answers should steadily increase theta."""
        theta = 0.0
        for _ in range(5):
            new_theta = update_theta(theta, a=1.0, b=0.0, c=0.25, correct=True)
            assert new_theta >= theta
            theta = new_theta

    def test_convergence_on_incorrect_streak(self):
        """Repeated incorrect answers should steadily decrease theta."""
        theta = 0.0
        for _ in range(5):
            new_theta = update_theta(theta, a=1.0, b=0.0, c=0.25, correct=False)
            assert new_theta <= theta
            theta = new_theta


class TestComputeSEM:
    """Tests for Standard Error of Measurement."""

    def test_empty_responses_returns_infinity(self):
        """No responses should return infinite SEM."""
        assert compute_sem([]) == float('inf')

    def test_more_responses_lower_sem(self):
        """More responses should generally yield lower SEM (more confidence)."""
        resp_1 = [{"theta_after": 0.0, "discrimination": 1.0, "difficulty": 0.5, "guessing": 0.25}]
        resp_5 = resp_1 * 5
        sem_1 = compute_sem(resp_1)
        sem_5 = compute_sem(resp_5)
        assert sem_5 < sem_1

    def test_sem_is_positive(self):
        """SEM should always be positive."""
        responses = [
            {"theta_after": 0.5, "discrimination": 1.5, "difficulty": 0.5, "guessing": 0.20}
        ]
        sem = compute_sem(responses)
        assert sem > 0


class TestNormalization:
    """Tests for theta ↔ difficulty mapping."""

    def test_theta_to_difficulty_range(self):
        """theta_to_difficulty should map [-3, +3] to [0.1, 1.0]."""
        assert abs(theta_to_difficulty(-3.0) - 0.1) < 0.01
        assert abs(theta_to_difficulty(3.0) - 1.0) < 0.01

    def test_difficulty_to_theta_range(self):
        """difficulty_to_theta should map [0.1, 1.0] to [-3, +3]."""
        assert abs(difficulty_to_theta(0.1) - (-3.0)) < 0.01
        assert abs(difficulty_to_theta(1.0) - 3.0) < 0.01

    def test_round_trip(self):
        """theta → difficulty → theta should be identity."""
        for theta in [-2.0, -1.0, 0.0, 1.0, 2.0]:
            recovered = difficulty_to_theta(theta_to_difficulty(theta))
            assert abs(recovered - theta) < 0.01


class TestDescriptors:
    """Tests for human-readable labels."""

    def test_theta_descriptors(self):
        assert get_theta_descriptor(-2.0) == "Well Below Average"
        assert get_theta_descriptor(-1.0) == "Below Average"
        assert get_theta_descriptor(0.0) == "Average"
        assert get_theta_descriptor(1.0) == "Above Average"
        assert get_theta_descriptor(2.0) == "Strong"
        assert get_theta_descriptor(3.0) == "Exceptional"

    def test_difficulty_band_labels(self):
        assert get_difficulty_band_label(0.2) == "Easy"
        assert get_difficulty_band_label(0.5) == "Medium"
        assert get_difficulty_band_label(0.8) == "Hard"
