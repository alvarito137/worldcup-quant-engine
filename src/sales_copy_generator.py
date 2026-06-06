import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LANDING_DIR = os.path.join(BASE_DIR, "landing")
SALES_COPY_PATH = os.path.join(LANDING_DIR, "sales_copy.md")


def generate_sales_copy():
    """
    Generates landing page copy for the World Cup Quant Intelligence product.
    """

    lines = []

    lines.append("# World Cup Quant Intelligence")
    lines.append("")
    lines.append("## Data-driven World Cup betting intelligence without hype.")
    lines.append("")
    lines.append(
        "World Cup Quant Intelligence helps you compare market-implied probabilities "
        "against model-estimated probabilities to identify possible pricing gaps, "
        "risk levels, and bankroll discipline signals during the World Cup."
    )
    lines.append("")

    lines.append("## This is not a pick-selling hype page.")
    lines.append("")
    lines.append(
        "No guaranteed wins. No fake screenshots. No emotional gambling. "
        "This product is built around probability, risk labels, value gaps, "
        "confidence scores, and transparent tracking."
    )
    lines.append("")

    lines.append("## What You Get")
    lines.append("")
    lines.append("- Daily model probabilities for selected World Cup matches")
    lines.append("- Market-implied probabilities from betting odds")
    lines.append("- Value gap calculation")
    lines.append("- Risk labels for every signal")
    lines.append("- Confidence score ranking")
    lines.append("- Fractional Kelly bankroll notes")
    lines.append("- Premium CSV data pack")
    lines.append("- Daily written brief")
    lines.append("- Telegram alerts")
    lines.append("- Performance tracking summary")
    lines.append("")

    lines.append("## Who This Is For")
    lines.append("")
    lines.append("- Football fans who want data-driven analysis")
    lines.append("- Bettors who care about price vs probability")
    lines.append("- People who want disciplined bankroll thinking")
    lines.append("- Sports analytics learners")
    lines.append("- Data-driven World Cup followers")
    lines.append("")

    lines.append("## Who This Is Not For")
    lines.append("")
    lines.append("- People looking for guaranteed betting profits")
    lines.append("- Anyone under the legal gambling age")
    lines.append("- People chasing losses")
    lines.append("- People looking for emotional picks or hype")
    lines.append("- Anyone who cannot afford to lose money")
    lines.append("")

    lines.append("## How It Works")
    lines.append("")
    lines.append("1. The system loads World Cup matches, team ratings, and odds.")
    lines.append("2. It converts odds into market-implied probabilities.")
    lines.append("3. It estimates probabilities using an internal model.")
    lines.append("4. It calculates the gap between market probability and model probability.")
    lines.append("5. It labels potential value signals and risk levels.")
    lines.append("6. It generates reports, CSV files, newsletter text, and Telegram alerts.")
    lines.append("7. Every signal can be tracked for transparency.")
    lines.append("")

    lines.append("## Example Signal")
    lines.append("")
    lines.append("```text")
    lines.append("Match: Spain vs Uruguay")
    lines.append("Selection: Uruguay")
    lines.append("Market probability: 25.64%")
    lines.append("Model probability: 31.79%")
    lines.append("Value gap: 6.15%")
    lines.append("Signal: POSSIBLE VALUE")
    lines.append("Risk: HIGH RISK")
    lines.append("Confidence score: 31.94%")
    lines.append("```")
    lines.append("")

    lines.append("## Product Options")
    lines.append("")
    lines.append("### Free Quant Brief")
    lines.append("")
    lines.append("A free public sample with one daily data signal and simple explanation.")
    lines.append("")
    lines.append("### Early Access")
    lines.append("")
    lines.append(
        "Designed for early supporters who want access to the model outputs, "
        "daily reports, and premium data before the tournament."
    )
    lines.append("")
    lines.append("### Premium Tournament Pass")
    lines.append("")
    lines.append(
        "Designed for people who want the full daily intelligence package: "
        "CSV data, reports, alerts, bankroll notes, and performance tracking."
    )
    lines.append("")

    lines.append("## Responsible Betting Disclaimer")
    lines.append("")
    lines.append(
        "This product is for educational and informational purposes only. "
        "It is not financial advice and does not guarantee profit. "
        "Betting involves risk. Only bet what you can afford to lose. "
        "Do not use this product if you are under the legal gambling age in your jurisdiction."
    )
    lines.append("")

    lines.append("## Call To Action")
    lines.append("")
    lines.append(
        "Join the free World Cup Quant Brief to get public model signals and updates. "
        "Premium access will be opened after the system has enough tracked samples."
    )

    os.makedirs(LANDING_DIR, exist_ok=True)

    with open(SALES_COPY_PATH, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))

    print(f"Sales copy generated: {SALES_COPY_PATH}")