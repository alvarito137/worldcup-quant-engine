import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REPORTS_DIR = os.path.join(BASE_DIR, "reports")
TELEGRAM_OUTPUT_PATH = os.path.join(REPORTS_DIR, "telegram_alerts.md")


def get_bankroll_note(row) -> str:
    """
    Creates a conservative bankroll note for Telegram alerts.
    """

    if row["risk_label"] == "LOW RISK":
        return "Conservative stake only. No guarantee."

    if row["risk_label"] == "MEDIUM RISK":
        return "Small stake only. Avoid overexposure."

    if row["risk_label"] == "HIGH RISK":
        return "Very small stake only. High variance."

    if row["risk_label"] == "VERY HIGH RISK":
        return "Watchlist only. Avoid aggressive staking."

    return "Use caution. Betting involves risk."


def generate_telegram_alerts(picks):
    """
    Generates Telegram-ready alert messages based on quality-filtered picks.

    Output:
    - reports/telegram_alerts.md
    """

    model_signals = picks[picks["signal"] != "NO BET"].copy()

    alert_picks = picks[
        picks["quality_label"].isin(["PUBLIC_SIGNAL", "PREMIUM_SIGNAL"])
    ].copy()

    quality_rank = {
        "PUBLIC_SIGNAL": 1,
        "PREMIUM_SIGNAL": 2,
    }

    alert_picks["quality_rank"] = alert_picks["quality_label"].map(quality_rank)

    alert_picks = alert_picks.sort_values(
        by=["quality_rank", "confidence_score", "value_gap"],
        ascending=[True, False, False]
    )

    alert_picks = alert_picks.head(5)

    lines = []

    lines.append("⚽ World Cup Quant Alert")
    lines.append("")
    lines.append(
        f"Found {len(model_signals)} model signal(s) today."
    )
    lines.append(
        f"Showing top {len(alert_picks)} after quality and risk filtering."
    )
    lines.append("")
    lines.append("This is not financial advice.")
    lines.append("No guaranteed profit.")
    lines.append("Bet responsibly.")
    lines.append("")

    if alert_picks.empty:
        lines.append("No public or premium-quality signals today.")
        lines.append("")
        lines.append("Best action: avoid forcing bets.")
    else:
        for i, (_, row) in enumerate(alert_picks.iterrows(), start=1):
            lines.append(f"{i}) {row['quality_label']}")
            lines.append("")
            lines.append(f"Match: {row['team_a']} vs {row['team_b']}")
            lines.append(f"Selection: {row['selection']}")
            lines.append(f"Odds: {row['decimal_odds']}")
            lines.append(f"Market probability: {row['implied_probability']:.2%}")
            lines.append(f"Model probability: {row['model_probability']:.2%}")
            lines.append(f"Value gap: {row['value_gap']:.2%}")
            lines.append(f"Risk: {row['risk_label']}")
            lines.append(f"Confidence score: {row['confidence_score']:.2%}")
            lines.append(f"Bankroll note: {get_bankroll_note(row)}")
            lines.append("")
            lines.append(
                "Reminder: value does not mean certainty. This is only a data signal."
            )
            lines.append("")

    lines.append("Full report includes:")
    lines.append("- all model signals")
    lines.append("- premium signals")
    lines.append("- CSV access")
    lines.append("- risk labels")
    lines.append("- confidence scores")
    lines.append("- bankroll notes")
    lines.append("- performance tracking")

    os.makedirs(REPORTS_DIR, exist_ok=True)

    with open(TELEGRAM_OUTPUT_PATH, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))

    print(f"Telegram alerts generated: {TELEGRAM_OUTPUT_PATH}")