import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REPORTS_DIR = os.path.join(BASE_DIR, "reports")
NEWSLETTER_OUTPUT_PATH = os.path.join(REPORTS_DIR, "newsletter.md")


def generate_newsletter(picks):
    """
    Generates a simple premium-style newsletter from the picks table.

    Output:
    - reports/newsletter.md
    """

    value_picks = picks[picks["signal"] != "NO BET"].copy()
    value_picks = value_picks.sort_values(
        by=["confidence_score", "value_gap"],
        ascending=[False, False]
    )

    lines = []

    lines.append("# World Cup Quant Brief")
    lines.append("")
    lines.append("## Today's Data-Driven Betting Intelligence")
    lines.append("")
    lines.append(
        "This brief compares market-implied probabilities against a simple internal model "
        "to identify potential pricing gaps. This is not a guarantee of profit."
    )
    lines.append("")

    if value_picks.empty:
        lines.append("## Main Takeaway")
        lines.append("")
        lines.append(
            "No clear value spots were found today using the current model thresholds. "
            "The best decision may be to avoid forcing bets."
        )
        lines.append("")
    else:
        best_pick = value_picks.iloc[0]

        lines.append("## Main Takeaway")
        lines.append("")
        lines.append(
            f"The strongest signal today is **{best_pick['selection']}** "
            f"in **{best_pick['team_a']} vs {best_pick['team_b']}**."
        )
        lines.append("")
        lines.append(
            f"The market implies a probability of **{best_pick['implied_probability']:.2%}**, "
            f"while the model estimates **{best_pick['model_probability']:.2%}**."
        )
        lines.append("")
        lines.append(
            f"That creates a value gap of **{best_pick['value_gap']:.2%}**."
        )
        lines.append("")
        lines.append(
            f"Risk label: **{best_pick['risk_label']}**. "
            f"Confidence score: **{best_pick['confidence_score']:.2%}**."
        )
        lines.append("")

        lines.append("## Top Value Signals")
        lines.append("")

        for i, (_, row) in enumerate(value_picks.head(5).iterrows(), start=1):
            lines.append(
                f"{i}. **{row['selection']}** — {row['team_a']} vs {row['team_b']} "
                f"| Odds: {row['decimal_odds']} "
                f"| Value gap: {row['value_gap']:.2%} "
                f"| Risk: {row['risk_label']} "
                f"| Confidence: {row['confidence_score']:.2%}"
            )

        lines.append("")

    lines.append("## Bankroll Note")
    lines.append("")
    lines.append(
        "Use conservative staking. The model uses fractional Kelly sizing, "
        "but even positive-value bets can lose. Avoid chasing losses."
    )
    lines.append("")

    lines.append("## Responsible Betting Disclaimer")
    lines.append("")
    lines.append(
        "This newsletter is for educational and informational purposes only. "
        "It is not financial advice and does not guarantee profit. "
        "Betting involves risk. Only bet what you can afford to lose. "
        "Do not use this content if you are under the legal gambling age in your jurisdiction."
    )
    lines.append("")

    lines.append("## CTA")
    lines.append("")
    lines.append(
        "Want the full CSV, daily model probabilities, value gaps, and Telegram alerts? "
        "Join the premium World Cup Quant list."
    )

    os.makedirs(REPORTS_DIR, exist_ok=True)

    with open(NEWSLETTER_OUTPUT_PATH, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))

    print(f"Newsletter generated: {NEWSLETTER_OUTPUT_PATH}")