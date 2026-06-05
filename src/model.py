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
    Baseline football probability model.

    Inputs:
    - team_a_rating
    - team_b_rating

    Outputs:
    - team_a_win_probability
    - draw_probability
    - team_b_win_probability

    Important:
    This is a simple baseline model, not a final professional betting model.
    """

    rating_diff = team_a_rating - team_b_rating

    # Convert rating difference into strength probability.
    raw_team_a_strength = sigmoid(rating_diff / 400)

    # Base draw probability in football.
    base_draw_probability = 0.26

    # If teams are similar in strength, draw probability increases.
    closeness = max(0, 1 - abs(rating_diff) / 500)
    draw_probability = base_draw_probability + (0.06 * closeness)

    # Remaining probability goes to both teams.
    remaining_probability = 1 - draw_probability

    team_a_win_probability = remaining_probability * raw_team_a_strength
    team_b_win_probability = remaining_probability * (1 - raw_team_a_strength)

    return {
        "team_a_win_probability": team_a_win_probability,
        "draw_probability": draw_probability,
        "team_b_win_probability": team_b_win_probability,
    }