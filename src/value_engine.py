import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv

from model import calculate_match_probabilities


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

DATA_MODE = os.getenv("DATA_MODE", "mock").lower()

RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

if DATA_MODE == "api":
    FIXTURES_PATH = os.path.join(RAW_DIR, "fixtures_api.csv")
    ODDS_PATH = os.path.join(RAW_DIR, "odds_api.csv")
    RATINGS_PATH = os.path.join(RAW_DIR, "team_ratings_api.csv")
else:
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
    
def get_risk_label(decimal_odds: float, model_probability: float, value_gap: float) -> str:
    """
    Classifies the risk level of a pick.

    This is not a guarantee. It is a simple risk label based on:
    - odds size
    - model probability
    - value gap
    """

    if decimal_odds >= 5.00:
        return "VERY HIGH RISK"

    if decimal_odds >= 3.50:
        return "HIGH RISK"

    if model_probability < 0.30:
        return "HIGH RISK"

    if value_gap >= 0.10 and model_probability >= 0.35:
        return "MEDIUM RISK"

    if decimal_odds <= 2.00 and model_probability >= 0.45:
        return "LOW RISK"

    return "MEDIUM RISK"   

def get_risk_penalty(risk_label: str) -> float:
    """
    Converts risk label into a numeric penalty.

    Higher risk = higher penalty.
    """

    risk_penalties = {
        "LOW RISK": 0.00,
        "MEDIUM RISK": 0.03,
        "HIGH RISK": 0.06,
        "VERY HIGH RISK": 0.10,
    }

    return risk_penalties.get(risk_label, 0.06)


def calculate_confidence_score(
    model_probability: float,
    value_gap: float,
    risk_label: str
) -> float:
    """
    Calculates a practical confidence score.

    This is not a guarantee.
    It is a ranking score to prioritize picks.

    Formula:
    confidence_score = model_probability + value_gap - risk_penalty
    """

    risk_penalty = get_risk_penalty(risk_label)

    confidence_score = model_probability + value_gap - risk_penalty

    return confidence_score

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
            risk_label = get_risk_label(
                decimal_odds=decimal_odds,
                model_probability=model_probability,
                value_gap=value_gap
            )

            confidence_score = calculate_confidence_score(
                model_probability=model_probability,
                value_gap=value_gap,
                risk_label=risk_label
            )

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
                "risk_label": risk_label,
                "confidence_score": round(confidence_score, 4),
            })

    picks = pd.DataFrame(all_rows)

    signal_rank = {
        "STRONG VALUE": 1,
        "POSSIBLE VALUE": 2,
        "NO BET": 3,
    }

    picks["signal_rank"] = picks["signal"].map(signal_rank)

    picks = picks.sort_values(
        by=["signal_rank", "confidence_score", "value_gap"],
        ascending=[True, False, False]
    )

    picks = picks.drop(columns=["signal_rank"])

    os.makedirs(PROCESSED_DIR, exist_ok=True)
    picks.to_csv(PICKS_OUTPUT_PATH, index=False)

    return picks



