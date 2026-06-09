import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REPORTS_DIR = os.path.join(BASE_DIR, "reports")
FREE_SAMPLE_OUTPUT_PATH = os.path.join(REPORTS_DIR, "free_sample.md")


def generate_free_sample(picks):
    """
    Generates a free public-facing sample report.

    This is designed for social media, Substack, Reddit, or lead capture.
    """

    value_picks = picks[picks["quality_label"] == "PUBLIC_SIGNAL"].copy()
    value_picks = value_picks.sort_values(
        by=["confidence_score", "value_gap"],
        ascending=[False, False]
    )

    lines = []

    lines.append("# Free World Cup Quant Sample")
    lines.append("")
    lines.append("## Today's Public Data Signal")
    lines.append("")

    lines.append(
        "I built a Python model that compares market-implied probability "
        "against my own estimated probability to detect possible pricing gaps."
    )
    lines.append("")

    lines.append(
        "This is not a guaranteed pick. It is a data signal."
    )
    lines.append("")

    if value_picks.empty:
        lines.append("## Signal")
        lines.append("")
        lines.append(
            "No clear value signal today. Sometimes the best decision is no bet."
        )
        lines.append("")
    else:
        top_pick = value_picks.iloc[0]

        lines.append("## Signal")
        lines.append("")
        lines.append(
            f"Match: **{top_pick['team_a']} vs {top_pick['team_b']}**"
        )
        lines.append("")
        lines.append(
            f"Selection: **{top_pick['selection']}**"
        )
        lines.append("")
        lines.append(
            f"Market probability: **{top_pick['implied_probability']:.2%}**"
        )
        lines.append("")
        lines.append(
            f"Model probability: **{top_pick['model_probability']:.2%}**"
        )
        lines.append("")
        lines.append(
            f"Value gap: **{top_pick['value_gap']:.2%}**"
        )
        lines.append("")
        lines.append(
            f"Risk: **{top_pick['risk_label']}**"
        )
        lines.append("")

        lines.append("## Simple Explanation")
        lines.append("")
        lines.append(
            f"The market odds imply {top_pick['selection']} has around "
            f"{top_pick['implied_probability']:.2%} chance."
        )
        lines.append("")
        lines.append(
            f"My model estimates it closer to {top_pick['model_probability']:.2%}."
        )
        lines.append("")
        lines.append(
            "That difference is the value gap. It does not mean the pick will win. "
            "It means the price may be different from the model estimate."
        )
        lines.append("")

    lines.append("## Responsible Betting Note")
    lines.append("")
    lines.append(
        "Betting involves risk. This content is educational and informational only. "
        "Never bet money you cannot afford to lose."
    )
    lines.append("")

    lines.append("## Want the Full Report?")
    lines.append("")
    lines.append(
        "The premium version includes all matches, model probabilities, "
        "value gaps, risk labels, confidence scores, bankroll notes, CSV access, "
        "and Telegram alerts."
    )

    os.makedirs(REPORTS_DIR, exist_ok=True)

    with open(FREE_SAMPLE_OUTPUT_PATH, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))

    print(f"Free sample generated: {FREE_SAMPLE_OUTPUT_PATH}")