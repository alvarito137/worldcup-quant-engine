import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REPORTS_DIR = os.path.join(BASE_DIR, "reports")
PUBLIC_BRIEF_PATH = os.path.join(REPORTS_DIR, "public_brief.md")


def generate_public_brief(picks):
    """
    Generates a short public-facing brief for social media or free posts.

    Uses only PUBLIC_SIGNAL picks.
    """

    public_picks = picks[picks["quality_label"] == "PUBLIC_SIGNAL"].copy()

    public_picks = public_picks.sort_values(
        by=["confidence_score", "value_gap"],
        ascending=[False, False]
    )

    lines = []

    lines.append("# Public World Cup Quant Brief")
    lines.append("")

    if public_picks.empty:
        lines.append("No public signal today.")
        lines.append("")
        lines.append(
            "The model did not find a signal strong enough to publish publicly. "
            "Sometimes the best decision is no bet."
        )
        lines.append("")
        lines.append(
            "Full premium watchlist still includes model probabilities, market gaps, "
            "risk labels, and bankroll notes."
        )
    else:
        top_pick = public_picks.iloc[0]

        lines.append("## Today's Public Signal")
        lines.append("")
        lines.append(
            f"Match: **{top_pick['team_a']} vs {top_pick['team_b']}**"
        )
        lines.append("")
        lines.append(
            f"Signal: **{top_pick['selection']}**"
        )
        lines.append("")
        lines.append(
            f"The market implies around **{top_pick['implied_probability']:.2%}**."
        )
        lines.append("")
        lines.append(
            f"The model estimates around **{top_pick['model_probability']:.2%}**."
        )
        lines.append("")
        lines.append(
            f"Value gap: **{top_pick['value_gap']:.2%}**."
        )
        lines.append("")
        lines.append(
            f"Risk label: **{top_pick['risk_label']}**."
        )
        lines.append("")
        lines.append(
            "This is not a guaranteed pick. It is a data signal based on price vs probability."
        )
        lines.append("")

        lines.append("## Short Post Version")
        lines.append("")
        lines.append(
            f"My World Cup model found a public signal in {top_pick['team_a']} vs {top_pick['team_b']}."
        )
        lines.append("")
        lines.append(
            f"Selection: {top_pick['selection']}"
        )
        lines.append(
            f"Market probability: {top_pick['implied_probability']:.1%}"
        )
        lines.append(
            f"Model probability: {top_pick['model_probability']:.1%}"
        )
        lines.append(
            f"Value gap: {top_pick['value_gap']:.1%}"
        )
        lines.append(
            f"Risk: {top_pick['risk_label']}"
        )
        lines.append("")
        lines.append(
            "Not a guarantee. Just a data signal. Betting involves risk."
        )
        lines.append("")

        lines.append("## CTA")
        lines.append("")
        lines.append(
            "The full version includes all matches, premium signals, watchlist picks, "
            "CSV access, risk labels, confidence scores, bankroll notes, and Telegram alerts."
        )

    os.makedirs(REPORTS_DIR, exist_ok=True)

    with open(PUBLIC_BRIEF_PATH, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))

    print(f"Public brief generated: {PUBLIC_BRIEF_PATH}")