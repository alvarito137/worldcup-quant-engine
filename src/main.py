import os
import math
import pandas as pd
import numpy as np


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")


FIXTURES_PATH = os.path.join(RAW_DIR, "fixtures.csv")
ODDS_PATH = os.path.join(RAW_DIR, "odds.csv")
RATINGS_PATH = os.path.join(RAW_DIR, "team_ratings.csv")
PICKS_OUTPUT_PATH = os.path.join(PROCESSED_DIR, "picks.csv")
REPORT_OUTPUT_PATH = os.path.join(REPORTS_DIR, "daily_report.md")


def ensure_directories():
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)


def create_mock_data():
    fixtures = pd.DataFrame([
        {
            "match_id": 1,
            "date": "2026-06-11",
            "team_a": "Mexico",
            "team_b": "South Africa",
            "stage": "Group Stage"
        },
        {
            "match_id": 2,
            "date": "2026-06-12",
            "team_a": "Canada",
            "team_b": "Qatar",
            "stage": "Group Stage"
        },
        {
            "match_id": 3,
            "date": "2026-06-13",
            "team_a": "Brazil",
            "team_b": "Morocco",
            "stage": "Group Stage"
        },
        {
            "match_id": 4,
            "date": "2026-06-14",
            "team_a": "Argentina",
            "team_b": "Austria",
            "stage": "Group Stage"
        },
        {
            "match_id": 5,
            "date": "2026-06-15",
            "team_a": "Spain",
            "team_b": "Uruguay",
            "stage": "Group Stage"
        }
    ])

    odds = pd.DataFrame([
        {"match_id": 1, "selection": "Mexico", "decimal_odds": 1.65},
        {"match_id": 1, "selection": "Draw", "decimal_odds": 3.70},
        {"match_id": 1, "selection": "South Africa", "decimal_odds": 5.20},

        {"match_id": 2, "selection": "Canada", "decimal_odds": 2.05},
        {"match_id": 2, "selection": "Draw", "decimal_odds": 3.25},
        {"match_id": 2, "selection": "Qatar", "decimal_odds": 3.60},

        {"match_id": 3, "selection": "Brazil", "decimal_odds": 1.80},
        {"match_id": 3, "selection": "Draw", "decimal_odds": 3.50},
        {"match_id": 3, "selection": "Morocco", "decimal_odds": 4.70},

        {"match_id": 4, "selection": "Argentina", "decimal_odds": 1.55},
        {"match_id": 4, "selection": "Draw", "decimal_odds": 4.00},
        {"match_id": 4, "selection": "Austria", "decimal_odds": 6.00},

        {"match_id": 5, "selection": "Spain", "decimal_odds": 1.95},
        {"match_id": 5, "selection": "Draw", "decimal_odds": 3.40},
        {"match_id": 5, "selection": "Uruguay", "decimal_odds": 3.90},
    ])

    ratings = pd.DataFrame([
        {"team": "Mexico", "rating": 1770},
        {"team": "South Africa", "rating": 1580},
        {"team": "Canada", "rating": 1700},
        {"team": "Qatar", "rating": 1600},
        {"team": "Brazil", "rating": 1900},
        {"team": "Morocco", "rating": 1810},
        {"team": "Argentina", "rating": 1920},
        {"team": "Austria", "rating": 1740},
        {"team": "Spain", "rating": 1880},
        {"team": "Uruguay", "rating": 1820},
    ])

    fixtures.to_csv(FIXTURES_PATH, index=False)
    odds.to_csv(ODDS_PATH, index=False)
    ratings.to_csv(RATINGS_PATH, index=False)

    print("Mock data created.")


def implied_probability(decimal_odds: float) -> float:
    if decimal_odds <= 1:
        raise ValueError("Decimal odds must be greater than 1.")
    return 1 / decimal_odds


def sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def calculate_match_probabilities(team_a_rating: float, team_b_rating: float) -> dict:
    """
    Simple baseline model.

    This is not a final betting model.
    It is a first approximation using rating difference.

    Outputs:
    - probability of team A win
    - probability of draw
    - probability of team B win
    """

    rating_diff = team_a_rating - team_b_rating

    # Strength advantage from ratings.
    raw_team_a_strength = sigmoid(rating_diff / 400)

    # Base draw rate in football.
    # Later this should be calibrated with historical data.
    base_draw_probability = 0.26

    # If teams are close in rating, draw probability increases slightly.
    closeness = max(0, 1 - abs(rating_diff) / 500)
    draw_probability = base_draw_probability + (0.06 * closeness)

    # Remaining probability goes to team A and team B.
    remaining_probability = 1 - draw_probability

    team_a_win_probability = remaining_probability * raw_team_a_strength
    team_b_win_probability = remaining_probability * (1 - raw_team_a_strength)

    return {
        "team_a_win_probability": team_a_win_probability,
        "draw_probability": draw_probability,
        "team_b_win_probability": team_b_win_probability
    }


def fractional_kelly(decimal_odds: float, model_probability: float, fraction: float = 0.25) -> float:
    """
    Fractional Kelly staking.
    Returns recommended percentage of bankroll.

    If result is negative, stake is 0.
    """

    b = decimal_odds - 1
    p = model_probability
    q = 1 - p

    kelly = ((b * p) - q) / b

    if kelly <= 0:
        return 0

    return kelly * fraction


def build_picks():
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

        probabilities = calculate_match_probabilities(team_a_rating, team_b_rating)

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

            if value_gap >= 0.10:
                signal = "STRONG VALUE"
            elif value_gap >= 0.05:
                signal = "POSSIBLE VALUE"
            else:
                signal = "NO BET"

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
                "signal": signal
            })

    picks = pd.DataFrame(all_rows)
    picks = picks.sort_values(by="value_gap", ascending=False)

    picks.to_csv(PICKS_OUTPUT_PATH, index=False)

    return picks


def generate_markdown_report(picks: pd.DataFrame):
    top_picks = picks[picks["signal"] != "NO BET"].copy()
    top_picks = top_picks.sort_values(by="value_gap", ascending=False)

    lines = []

    lines.append("# World Cup Quant Report")
    lines.append("")
    lines.append("## Disclaimer")
    lines.append("")
    lines.append(
        "This report is for informational and educational purposes only. "
        "It is not financial advice and does not guarantee profit. "
        "Betting involves risk. Only bet what you can afford to lose. "
        "Do not use this content if you are under the legal gambling age in your jurisdiction."
    )
    lines.append("")

    lines.append("## Top Value Picks")
    lines.append("")

    if top_picks.empty:
        lines.append("No value bets found with the current model thresholds.")
    else:
        for _, row in top_picks.iterrows():
            lines.append(
                f"- **{row['selection']}** in {row['team_a']} vs {row['team_b']} "
                f"| Odds: {row['decimal_odds']} "
                f"| Market probability: {row['implied_probability']:.2%} "
                f"| Model probability: {row['model_probability']:.2%} "
                f"| Value gap: {row['value_gap']:.2%} "
                f"| Signal: {row['signal']} "
                f"| Kelly 25% stake: {row['kelly_stake_pct']:.2%} of bankroll"
            )

    lines.append("")
    lines.append("## All Matches")
    lines.append("")

    for match_id, group in picks.groupby("match_id"):
        first = group.iloc[0]
        lines.append(f"### {first['team_a']} vs {first['team_b']} — {first['date']}")
        lines.append("")
        for _, row in group.iterrows():
            lines.append(
                f"- {row['selection']}: odds {row['decimal_odds']}, "
                f"model {row['model_probability']:.2%}, "
                f"market {row['implied_probability']:.2%}, "
                f"value gap {row['value_gap']:.2%}, "
                f"{row['signal']}"
            )
        lines.append("")

    with open(REPORT_OUTPUT_PATH, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))

    print(f"Report generated: {REPORT_OUTPUT_PATH}")


def generate_content_scripts(picks: pd.DataFrame):
    content_path = os.path.join(REPORTS_DIR, "tiktok_scripts.md")

    top_picks = picks[picks["signal"] != "NO BET"].head(3)

    lines = []
    lines.append("# TikTok / YouTube Shorts Scripts")
    lines.append("")

    if top_picks.empty:
        lines.append("No strong content angles today because the model did not find clear value.")
    else:
        for i, (_, row) in enumerate(top_picks.iterrows(), start=1):
            lines.append(f"## Script {i}")
            lines.append("")
            lines.append(
                f"Hook: My World Cup model found a possible market gap in "
                f"{row['team_a']} vs {row['team_b']}."
            )
            lines.append("")
            lines.append(
                f"The market implies {row['selection']} has about "
                f"{row['implied_probability']:.1%} chance based on the odds."
            )
            lines.append("")
            lines.append(
                f"But my model estimates it closer to {row['model_probability']:.1%}."
            )
            lines.append("")
            lines.append(
                f"That creates a value gap of {row['value_gap']:.1%}."
            )
            lines.append("")
            lines.append(
                "This is not a guaranteed bet. It is just a data signal. "
                "The goal is not to gamble emotionally, but to compare price vs probability."
            )
            lines.append("")

    with open(content_path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))

    print(f"Content scripts generated: {content_path}")


def main():
    ensure_directories()

    if not os.path.exists(FIXTURES_PATH) or not os.path.exists(ODDS_PATH) or not os.path.exists(RATINGS_PATH):
        create_mock_data()

    picks = build_picks()

    print("\nTop picks:")
    print(picks.head(10).to_string(index=False))

    generate_markdown_report(picks)
    generate_content_scripts(picks)

    print(f"\nPicks saved to: {PICKS_OUTPUT_PATH}")


if __name__ == "__main__":
    main()