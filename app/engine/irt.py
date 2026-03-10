"""
IRT (Item Response Theory) core functions.
Pure mathematical functions — no HTTP or database knowledge.

Implements the 3-Parameter Logistic (3PL) Model:
P(correct | θ) = c + (1 - c) × [1 / (1 + e^(-a(θ - b)))]

Where:
    a = discrimination (how sharply the item separates high vs. low ability)
    b = difficulty (ability level where P ≈ 0.5 ignoring guessing)
    c = pseudo-guessing (probability of lucky guess)
    θ = student ability (latent trait being estimated)
"""

import math
from typing import List, Tuple
from app.config import settings


def probability_3pl(theta: float, a: float, b: float, c: float) -> float:
    """
    Compute the probability of a correct response using the IRT 3PL model.

    Args:
        theta: Student ability estimate (typically -3 to +3)
        a: Item discrimination parameter (0.5 to 3.0)
        b: Item difficulty parameter (mapped to theta scale)
        c: Pseudo-guessing parameter (0.0 to 0.35)

    Returns:
        Probability of correct response, in range [c, 1.0]
    """
    exponent = -a * (theta - b)
    # Clamp exponent to prevent overflow
    exponent = max(-30, min(30, exponent))
    logistic = 1.0 / (1.0 + math.exp(exponent))
    return c + (1.0 - c) * logistic


def update_theta(
    theta: float,
    a: float,
    b: float,
    c: float,
    correct: bool,
    learning_rate: float = 0.4
) -> float:
    """
    Update theta (ability estimate) after a response using an MLE-inspired step.

    Uses the derivative of the log-likelihood scaled by a learning rate:
        Δθ = learning_rate × a × (response - P(θ)) × (P(θ) - c) / (P(θ) × (1 - c))

    This approximation avoids full Newton-Raphson iteration while still
    producing sensible updates for a 10-question adaptive test.

    Args:
        theta: Current ability estimate
        a: Item discrimination
        b: Item difficulty (on theta scale)
        c: Pseudo-guessing
        correct: Whether the student answered correctly
        learning_rate: Step size for the update (default 0.4)

    Returns:
        Updated theta, bounded to [THETA_MIN, THETA_MAX]
    """
    p = probability_3pl(theta, a, b, c)

    # Avoid division by zero
    p = max(p, 0.001)
    p = min(p, 0.999)

    response = 1.0 if correct else 0.0

    # Weight factor: adjusts for guessing
    # When c > 0, correct answers contribute less if the student might have guessed
    weight = (p - c) / (p * (1.0 - c)) if (1.0 - c) > 0 else 1.0

    # MLE step
    delta = learning_rate * a * (response - p) * weight

    new_theta = theta + delta
    return max(settings.THETA_MIN, min(settings.THETA_MAX, new_theta))


def compute_sem(responses: List[dict]) -> float:
    """
    Compute the Standard Error of Measurement (SEM) based on response history.

    SEM = 1 / sqrt(Information), where Information is the sum of Fisher
    Information values across all answered items.

    Fisher Information for 3PL:
        I(θ) = a² × [(P - c)² / ((1 - c)² × P × (1 - P))]

    Args:
        responses: List of response dicts, each containing 'theta_after',
                   and the question's a, b, c parameters.

    Returns:
        SEM value. Lower = more confident estimate.
    """
    if not responses:
        return float('inf')

    total_info = 0.0

    for resp in responses:
        a = resp.get("discrimination", 1.0)
        b = resp.get("difficulty", 0.5)
        c = resp.get("guessing", 0.25)
        theta = resp.get("theta_after", 0.0)

        p = probability_3pl(theta, a, b, c)
        p = max(p, 0.001)
        p = min(p, 0.999)

        numerator = (p - c) ** 2
        denominator = (1.0 - c) ** 2 * p * (1.0 - p)

        if denominator > 0:
            fisher_info = (a ** 2) * (numerator / denominator)
            total_info += fisher_info

    if total_info <= 0:
        return float('inf')

    return 1.0 / math.sqrt(total_info)


def theta_to_difficulty(theta: float) -> float:
    """
    Map theta from [-3, +3] to difficulty scale [0.1, 1.0].

    Linear normalization:
        difficulty = (theta - THETA_MIN) / (THETA_MAX - THETA_MIN) × (DIFF_MAX - DIFF_MIN) + DIFF_MIN
    """
    theta_range = settings.THETA_MAX - settings.THETA_MIN
    diff_range = settings.DIFFICULTY_MAX - settings.DIFFICULTY_MIN

    normalized = (theta - settings.THETA_MIN) / theta_range
    difficulty = normalized * diff_range + settings.DIFFICULTY_MIN

    return max(settings.DIFFICULTY_MIN, min(settings.DIFFICULTY_MAX, difficulty))


def difficulty_to_theta(difficulty: float) -> float:
    """
    Map difficulty from [0.1, 1.0] back to theta scale [-3, +3].
    Inverse of theta_to_difficulty.
    """
    theta_range = settings.THETA_MAX - settings.THETA_MIN
    diff_range = settings.DIFFICULTY_MAX - settings.DIFFICULTY_MIN

    normalized = (difficulty - settings.DIFFICULTY_MIN) / diff_range
    theta = normalized * theta_range + settings.THETA_MIN

    return max(settings.THETA_MIN, min(settings.THETA_MAX, theta))


def get_theta_descriptor(theta: float) -> str:
    """
    Map theta to a human-readable ability descriptor.

    Ranges:
        θ < -1.5  → "Well Below Average"
        -1.5 ≤ θ < -0.5 → "Below Average"
        -0.5 ≤ θ < 0.5  → "Average"
        0.5 ≤ θ < 1.5   → "Above Average"
        1.5 ≤ θ < 2.5   → "Strong"
        θ ≥ 2.5          → "Exceptional"
    """
    if theta < -1.5:
        return "Well Below Average"
    elif theta < -0.5:
        return "Below Average"
    elif theta < 0.5:
        return "Average"
    elif theta < 1.5:
        return "Above Average"
    elif theta < 2.5:
        return "Strong"
    else:
        return "Exceptional"


def get_difficulty_band_label(difficulty: float) -> str:
    """Map difficulty float to human-readable band label."""
    if difficulty <= 0.35:
        return "Easy"
    elif difficulty <= 0.65:
        return "Medium"
    else:
        return "Hard"
