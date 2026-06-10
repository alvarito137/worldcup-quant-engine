import os
import pandas as pd


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

INPUT_PATH = os.path.join(PROCESSED_DIR, "market_angles_with_odds.csv")
OUTPUT_PATH = os.path.join(REPORTS_DIR, "telegram_free_intelligence.md")


def generate_free_telegram_intelligence():
    if not os.path.exists(INPUT_PATH):
        raise FileNotFoundError(
            f"Missing {INPUT_PATH}. Run python src/market_odds_matcher.py first."
        )

    df = pd.read_csv(INPUT_PATH)

    lines = []
    lines.append("⚽ World Cup Free Betting Intelligence")
    lines.append("")
    lines.append("Top 3 data-backed markets to watch.")
    lines.append("No guaranteed bets. Educational only.")
    lines.append("Bet responsibly.")
    lines.append("")

    if df.empty:
        lines.append("No data-backed markets found today.")
    else:
        df = df[df["odds_found"] == True].copy()

        df = df.sort_values(
            by=["adjusted_confidence_score", "best_decimal_odds"],
            ascending=[False, False]
        )

        top = df.head(3)

        for i, (_, row) in enumerate(top.iterrows(), start=1):
            lines.append(f"{i}) {row['match']}")
            lines.append(f"Market: {row['market_type']}")
            lines.append(f"Model angle: {row['selection']}")

            if pd.isna(row["matched_point"]):
                lines.append(f"Available line: {row['matched_selection']}")
            else:
                lines.append(
                    f"Available line: {row['matched_selection']} {row['matched_point']}"
                )

            lines.append(f"Best odds: {row['best_decimal_odds']}")
            lines.append(f"Best bookmaker: {row['best_bookmaker']}")
            lines.append(f"Adjusted profile: {row['adjusted_profile']}")
            lines.append(f"Adjusted confidence: {row['adjusted_confidence_score']:.1%}")
            lines.append(f"Note: {row['line_note']}")
            lines.append("")

        lines.append("Premium report includes:")
        lines.append("- all matches")
        lines.append("- full odds comparison")
        lines.append("- H2H context")
        lines.append("- recent form")
        lines.append("- CSV access")
        lines.append("- daily Telegram alerts")
        lines.append("")
        lines.append("No model can guarantee outcomes.")

    os.makedirs(REPORTS_DIR, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))

    print(f"Free Telegram intelligence generated: {OUTPUT_PATH}")


def main():
    generate_free_telegram_intelligence()


if __name__ == "__main__":
    main()
    