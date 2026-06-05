import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REPORTS_DIR = os.path.join(BASE_DIR, "reports")
REPORT_OUTPUT_PATH = os.path.join(REPORTS_DIR, "daily_report.md")


def generate_markdown_report(picks):
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

    os.makedirs(REPORTS_DIR, exist_ok=True)

    with open(REPORT_OUTPUT_PATH, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))

    print(f"Report generated: {REPORT_OUTPUT_PATH}")