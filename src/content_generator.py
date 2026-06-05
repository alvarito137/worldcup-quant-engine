import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REPORTS_DIR = os.path.join(BASE_DIR, "reports")
CONTENT_OUTPUT_PATH = os.path.join(REPORTS_DIR, "tiktok_scripts.md")


def generate_content_scripts(picks):
    """
    Generates short-form content scripts based on the top value picks.

    Output:
    - reports/tiktok_scripts.md
    """

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

            lines.append("### Hook")
            lines.append(
                f"My World Cup model found a possible market gap in "
                f"{row['team_a']} vs {row['team_b']}."
            )
            lines.append("")

            lines.append("### Simple Explanation")
            lines.append(
                f"The market odds imply that **{row['selection']}** has about "
                f"{row['implied_probability']:.1%} chance."
            )
            lines.append("")
            lines.append(
                f"My model estimates the probability closer to "
                f"{row['model_probability']:.1%}."
            )
            lines.append("")
            lines.append(
                f"That creates a value gap of **{row['value_gap']:.1%}**."
            )
            lines.append("")

            lines.append("### Closing")
            lines.append(
                "This is not a guaranteed bet. It is just a data signal. "
                "The goal is to compare price vs probability, not gamble emotionally."
            )
            lines.append("")

            lines.append("### Caption")
            lines.append(
                f"Data signal for {row['team_a']} vs {row['team_b']}: "
                f"{row['selection']} shows a {row['value_gap']:.1%} value gap. "
                "#WorldCup2026 #SportsAnalytics #BettingData #FootballAnalytics"
            )
            lines.append("")

    os.makedirs(REPORTS_DIR, exist_ok=True)

    with open(CONTENT_OUTPUT_PATH, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))

    print(f"Content scripts generated: {CONTENT_OUTPUT_PATH}")