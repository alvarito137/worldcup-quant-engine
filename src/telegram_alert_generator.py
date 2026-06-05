import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REPORTS_DIR = os.path.join(BASE_DIR, "reports")
TELEGRAM_OUTPUT_PATH = os.path.join(REPORTS_DIR, "telegram_alerts.md")


def generate_telegram_alerts(picks):
    """
    Generates Telegram-ready alert messages based on value picks.

    Output:
    - reports/telegram_alerts.md
    """

    value_picks = picks[picks["signal"] != "NO BET"].copy()

    value_picks = value_picks.sort_values(
        by=["confidence_score", "value_gap"],
        ascending=[False, False]
    )

    lines = []

    lines.append("# Telegram Alerts")
    lines.append("")

    lines.append("## Daily Summary")
    lines.append("")
    lines.append("⚽ World Cup Quant Alert")
    lines.append("")
    lines.append(
        "Data-driven signals comparing model probability vs market-implied probability."
    )
    lines.append("")
    lines.append(
        "Not financial advice. No guaranteed profit. Bet responsibly."
    )
    lines.append("")

    if value_picks.empty:
        lines.append("No clear value signals found today.")
        lines.append("")
        lines.append("Best action: avoid forcing bets.")
    else:
        lines.append(f"Found {len(value_picks)} potential value signal(s).")
        lines.append("")

        for i, (_, row) in enumerate(value_picks.head(5).iterrows(), start=1):
            lines.append(f"## Alert {i}")
            lines.append("")
            lines.append(f"🚨 {row['signal']}")
            lines.append("")
            lines.append(f"Match: {row['team_a']} vs {row['team_b']}")
            lines.append(f"Selection: {row['selection']}")
            lines.append(f"Odds: {row['decimal_odds']}")
            lines.append(f"Market probability: {row['implied_probability']:.2%}")
            lines.append(f"Model probability: {row['model_probability']:.2%}")
            lines.append(f"Value gap: {row['value_gap']:.2%}")
            lines.append(f"Risk: {row['risk_label']}")
            lines.append(f"Confidence score: {row['confidence_score']:.2%}")
            lines.append(f"Kelly 25% stake: {row['kelly_stake_pct']:.2%} of bankroll")
            lines.append("")
            lines.append(
                "Reminder: value does not mean certainty. "
                "This is only a data signal."
            )
            lines.append("")

    os.makedirs(REPORTS_DIR, exist_ok=True)

    with open(TELEGRAM_OUTPUT_PATH, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))

    print(f"Telegram alerts generated: {TELEGRAM_OUTPUT_PATH}")