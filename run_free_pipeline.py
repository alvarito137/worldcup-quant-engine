import subprocess
import sys


def run_step(name, command):
    print("")
    print("=" * 70)
    print(f"Running: {name}")
    print("=" * 70)

    result = subprocess.run(command)

    if result.returncode != 0:
        print("")
        print(f"ERROR: Step failed: {name}")
        print("Pipeline stopped.")
        sys.exit(result.returncode)

    print(f"OK: {name}")


def main():
    python = sys.executable

    steps = [
        (
            "Fetch API-Football World Cup fixtures",
            [python, "data_sources/fetch_api_football.py"],
        ),
        (
            "Fetch API-Football recent stats and H2H",
            [python, "data_sources/fetch_api_football_context.py"],
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
            "Match market angles with odds",
            [python, "src/market_odds_matcher.py"],
        ),
        (
            "Generate free Telegram intelligence",
            [python, "src/free_telegram_intelligence_generator.py"],
        ),
    ]

    for name, command in steps:
        run_step(name, command)

    print("")
    print("=" * 70)
    print("FREE PIPELINE COMPLETED")
    print("=" * 70)
    print("Generated file:")
    print("reports/telegram_free_intelligence.md")
    print("")
    print("Next optional step:")
    print("python telegram_bot/send_alerts.py")


if __name__ == "__main__":
    main()