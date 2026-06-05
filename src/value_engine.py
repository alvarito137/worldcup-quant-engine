import math
import os
import pandas as pd
import numpy as np


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

FIXTURES_PATH = os.path.join(RAW_DIR, "fixtures.csv")
ODDS_PATH = os.path.join(RAW_DIR, "odds.csv")
RATINGS_PATH = os.path.join(RAW_DIR, "team_ratings.csv")
PICKS_OUTPUT_PATH = os.path.join(PROCESSED_DIR, "picks.csv")


def implied_probability(decimal_odds: float) -> float:
    """
    Converts decimal odds into implied market probability.

    Example:
    odds = 2.50
    implied_probability = 1 / 2.50 = 0.40 = 40%
    """

    if decimal_odds <= 1:
        raise ValueError("Decimal odds must be greater than 1.")

    return 1 / decimal_odds


def sigmoid(x: float) -> float:
    """
    Converts a rating difference into a probability-like number between 0 and 1.
    """

    return 1 / (1 + math.exp(-x))


def calculate_match_probabilities(team_a_rating: float, team_b_rating: float) -> dict:
    """
    Simple baseline football model.

    This is not a final betting model.
    This model uses team rating difference to estimate:

    - Team A win probability
    - Draw probability
    - Team B win probability
    """

    rating_diff = team_a_rating - team_b_rating

    # Rating advantage.
    raw_team_a_strength = sigmoid(rating_diff / 400)

    # Base draw probability in football.
    base_draw_probability = 0.26

    # If two teams are close in rating, draw probability increases.
    closeness = max(0, 1 - abs(rating_diff) / 500)
    draw_probability = base_draw_probability + (0.06 * closeness)

    # Remaining probability is split between team A and team B.
    remaining_probability = 1 - draw_probability

    team_a_win_probability = remaining_probability * raw_team_a_strength
    team_b_win_probability = remaining_probability * (1 - raw_team_a_strength)

    return {
        "team_a_win_probability": team_a_win_probability,
        "draw_probability": draw_probability,
        "team_b_win_probability": team_b_win_probability,
    }


def fractional_kelly(decimal_odds: float, model_probability: float, fraction: float = 0.25) -> float:
    """
    Fractional Kelly staking.

    Returns recommended percentage of bankroll.

    Example:
    return 0.02 means 2% of bankroll.

    Important:
    Kelly can be aggressive. We use fractional Kelly to reduce risk.
    """

    b = decimal_odds - 1
    p = model_probability
    q = 1 - p

    kelly = ((b * p) - q) / b

    if kelly <= 0:
        return 0

    return kelly * fraction


def get_signal(value_gap: float) -> str:
    """
    Converts value gap into a simple betting signal.
    """

    if value_gap >= 0.10:
        return "STRONG VALUE"
    elif value_gap >= 0.05:
        return "POSSIBLE VALUE"
    else:
        return "NO BET"


def build_picks() -> pd.DataFrame:
    """
    Main value betting engine.

    Loads:
    - fixtures.csv
    - odds.csv
    - team_ratings.csv

    Generates:
    - implied probability
    - model probability
    - value gap
    - Kelly stake
    - signal

    Saves:
    - data/processed/picks.csv
    """

    fixtures = pd.read_csv(FIXTURES_PATH)
    odds = pd.read_csv(ODDS_PATH)
    ratings = pd.read_csv(RATINGS_PATH)

    rating_map = dict(zip(ratings["team"], ratings["rating"]))

    all_rows = []

    for _, match in fixtures.iterrows():
        match_id = match["match_id"]
        team_a = match["team_a"]
        team_b = match["team_b"]

        team_a_rating = rating_map[team_a]
        team_b_rating = rating_map[team_b]

        probabilities = calculate_match_probabilities(
            team_a_rating=team_a_rating,
            team_b_rating=team_b_rating
        )

        match_odds = odds[odds["match_id"] == match_id]

        for _, odd_row in match_odds.iterrows():
            selection = odd_row["selection"]
            decimal_odds = odd_row["decimal_odds"]

            if selection == team_a:
                model_probability = probabilities["team_a_win_probability"]
            elif selection == "Draw":
                model_probability = probabilities["draw_probability"]
            elif selection == team_b:
                model_probability = probabilities["team_b_win_probability"]
            else:
                model_probability = np.nan

            market_probability = implied_probability(decimal_odds)
            value_gap = model_probability - market_probability

            kelly_stake_pct = fractional_kelly(
                decimal_odds=decimal_odds,
                model_probability=model_probability,
                fraction=0.25
            )

            signal = get_signal(value_gap)

            all_rows.append({
                "match_id": match_id,
                "date": match["date"],
                "stage": match["stage"],
                "team_a": team_a,
                "team_b": team_b,
                "selection": selection,
                "decimal_odds": round(decimal_odds, 2),
                "implied_probability": round(market_probability, 4),
                "model_probability": round(model_probability, 4),
                "value_gap": round(value_gap, 4),
                "kelly_stake_pct": round(kelly_stake_pct, 4),
                "signal": signal,
            })

    picks = pd.DataFrame(all_rows)

    picks = picks.sort_values(
        by="value_gap",
        ascending=False
    )

    os.makedirs(PROCESSED_DIR, exist_ok=True)
    picks.to_csv(PICKS_OUTPUT_PATH, index=False)

    return picks