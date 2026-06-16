import os
import sys
import subprocess
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def run_step(name, command):
    print("")
    print("=" * 80)
    print(f"Running step: {name}")
    print("=" * 80)

    result = subprocess.run(
        command,
        cwd=BASE_DIR,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"Step failed: {name}")

    print(f"Finished step: {name}")


def main():
    python = sys.executable

    print("")
    print("World Cup Quant Daily Pipeline")
    print(f"Started at: {datetime.utcnow().isoformat()} UTC")

    steps = [
        (
            "Fetch World Cup fixtures",
            [python, "data_sources/fetch_api_football.py"],
        ),
        (
            "Fetch recent team stats and H2H",
            [python, "data_sources/fetch_api_football_context.py"],
        ),
        (
            "Fetch advanced team stats",
            [python, "data_sources/fetch_api_football_advanced_context.py"],
        ),
        (
            "Fetch market odds",
            [python, "data_sources/fetch_market_odds.py"],
        ),
        (
            "Generate market angles",
            [python, "src/market_angle_engine.py"],
        ),
        (
            "Match angles with odds",
            [python, "src/market_odds_matcher.py"],
        ),
        (
            "Generate free report",
            [python, "src/free_telegram_intelligence_generator.py"],
        ),
        (
            "Generate premium report",
            [python, "src/premium_telegram_report_generator.py"],
        ),
    ]

    for name, command in steps:
        run_step(name, command)

    send_premium = os.getenv("SEND_PREMIUM_REPORT", "false").lower() == "true"

    if send_premium:
        run_step(
            "Send premium report to Telegram premium group",
            [python, "telegram_bot/send_premium_alerts.py"],
        )
    else:
        print("")
        print("SEND_PREMIUM_REPORT is false. Premium report generated but not sent.")

    print("")
    print("Daily pipeline completed successfully.")


if __name__ == "__main__":
    main()