import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
PREMIUM_OUTPUT_PATH = os.path.join(PROCESSED_DIR, "premium_picks.csv")


def generate_bankroll_note(row):
    """
    Creates a simple bankroll note for users.
    """

    if row["signal"] == "NO BET":
        return "No bet suggested."

    if row["risk_label"] == "VERY HIGH RISK":
        return "Tiny stake only. High variance pick."

    if row["risk_label"] == "HIGH RISK":
        return "Small stake only. Do not overexpose bankroll."

    if row["risk_label"] == "MEDIUM RISK":
        return "Moderate caution. Follow fractional Kelly only."

    return "Lower risk compared to other picks, but still not guaranteed."


def export_premium_picks(picks):
    """
    Exports a cleaner premium-facing CSV.
    """

    premium = picks.copy()

    premium["match"] = premium["team_a"] + " vs " + premium["team_b"]
    premium["market_probability"] = premium["implied_probability"]
    premium["bankroll_note"] = premium.apply(generate_bankroll_note, axis=1)

    premium = premium[
        [
            "date",
            "stage",
            "match",
            "selection",
            "decimal_odds",
            "market_probability",
            "model_probability",
            "value_gap",
            "signal",
            "risk_label",
            "confidence_score",
            "kelly_stake_pct",
            "bankroll_note",
            "quality_label",
        ]
    ]

    os.makedirs(PROCESSED_DIR, exist_ok=True)

    premium.to_csv(PREMIUM_OUTPUT_PATH, index=False)

    print(f"Premium picks exported: {PREMIUM_OUTPUT_PATH}")