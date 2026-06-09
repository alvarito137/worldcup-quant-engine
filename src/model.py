import math


def sigmoid(x: float) -> float:
    """
    Converts any number into a value between 0 and 1.

    In this project, we use it to convert rating difference
    into a probability-like value.
    """

    return 1 / (1 + math.exp(-x))


def calculate_match_probabilities(team_a_rating: float, team_b_rating: float) -> dict:
    """
    Conservative football probability model.

    This model uses rating difference to estimate:
    - Team A win probability
    - Draw probability
    - Team B win probability

    It is intentionally more conservative with underdogs.
    """

    rating_diff = team_a_rating - team_b_rating

    # More sensitive than the previous /400 version.
    # Lower denominator = stronger effect from rating differences.
    raw_team_a_strength = sigmoid(rating_diff / 220)

    # Base draw probability.
    base_draw_probability = 0.22

    # Draw is higher when teams are close.
    closeness = max(0, 1 - abs(rating_diff) / 400)
    draw_probability = base_draw_probability + (0.05 * closeness)

    # Draw should not become too high.
    draw_probability = min(draw_probability, 0.27)

    remaining_probability = 1 - draw_probability

    team_a_win_probability = remaining_probability * raw_team_a_strength
    team_b_win_probability = remaining_probability * (1 - raw_team_a_strength)

    return {
        "team_a_win_probability": team_a_win_probability,
        "draw_probability": draw_probability,
        "team_b_win_probability": team_b_win_probability,
    }