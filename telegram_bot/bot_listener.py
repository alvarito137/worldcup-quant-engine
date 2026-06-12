import os
import time
import json
import sys
import subprocess
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_PATH)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
REPORT_TIMEZONE = os.getenv("REPORT_TIMEZONE", "America/Toronto")

REPORTS_DIR = os.path.join(BASE_DIR, "reports")
FREE_REPORT_PATH = os.path.join(REPORTS_DIR, "telegram_free_intelligence.md")
FREE_REPORT_META_PATH = os.path.join(REPORTS_DIR, "free_report_meta.json")


def send_message(chat_id, message):
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN in .env")

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message,
    }

    response = requests.post(url, json=payload, timeout=30)

    if response.status_code != 200:
        print("Telegram send error:")
        print(response.text)

    response.raise_for_status()


def get_updates(offset=None):
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN in .env")

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"

    params = {
        "timeout": 30,
    }

    if offset is not None:
        params["offset"] = offset

    response = requests.get(url, params=params, timeout=35)
    response.raise_for_status()

    data = response.json()

    return data.get("result", [])


def get_today_key():
    timezone = ZoneInfo(REPORT_TIMEZONE)
    return datetime.now(timezone).strftime("%Y-%m-%d")


def is_free_report_fresh():
    if not os.path.exists(FREE_REPORT_PATH):
        return False

    if not os.path.exists(FREE_REPORT_META_PATH):
        return False

    try:
        with open(FREE_REPORT_META_PATH, "r", encoding="utf-8") as file:
            meta = json.load(file)

        return meta.get("report_date") == get_today_key()

    except Exception:
        return False


def save_free_report_meta():
    os.makedirs(REPORTS_DIR, exist_ok=True)

    meta = {
        "report_date": get_today_key(),
        "generated_at": datetime.now(ZoneInfo(REPORT_TIMEZONE)).isoformat(),
    }

    with open(FREE_REPORT_META_PATH, "w", encoding="utf-8") as file:
        json.dump(meta, file, indent=2)


def run_pipeline_step(name, command):
    print("")
    print("=" * 70)
    print(f"Running: {name}")
    print("=" * 70)

    result = subprocess.run(
        command,
        cwd=BASE_DIR,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"Pipeline step failed: {name}")


def regenerate_free_report():
    python = sys.executable

    steps = [
        (
            "Fetch API-Football fixtures",
            [python, "data_sources/fetch_api_football.py"],
        ),
        (
            "Fetch recent stats and H2H",
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
            "Match angles with odds",
            [python, "src/market_odds_matcher.py"],
        ),
        (
            "Generate free Telegram report",
            [python, "src/free_telegram_intelligence_generator.py"],
        ),
    ]

    for name, command in steps:
        run_pipeline_step(name, command)

    save_free_report_meta()


def handle_start(chat_id):
    message = (
        "⚽ Welcome to World Cup Betting Intelligence\n\n"
        "This bot shares data-backed football match analysis for people who want to understand games before betting responsibly.\n\n"
        "Free version includes:\n"
        "- Main match watchlist of the day\n"
        "- Last 10 matches for each team\n"
        "- Goals scored and conceded\n"
        "- Previous meetings between both teams\n"
        "- Estimated probabilities\n"
        "- Betting line to watch\n\n"
        "Premium version includes:\n"
        "- All matches today/tomorrow\n"
        "- Full probability tables\n"
        "- Odds comparison\n"
        "- Deeper match analysis\n"
        "- Private premium Telegram access\n"
        "- Future lineup/player alerts\n\n"
        "Important:\n"
        "These are not guaranteed bets. Educational only. Bet responsibly.\n\n"
        "Commands:\n"
        "/start - Start the bot\n"
        "/free - Get the latest free match watchlist\n"
        "/premium - See premium intelligence info"
    )

    send_message(chat_id, message)


def handle_free(chat_id):
    try:
        if not is_free_report_fresh():
            print("Free report is not fresh. Regenerating...")
            regenerate_free_report()

        if not os.path.exists(FREE_REPORT_PATH):
            send_message(
                chat_id,
                "No free report generated yet. Please try again later."
            )
            return

        with open(FREE_REPORT_PATH, "r", encoding="utf-8") as file:
            message = file.read()

        send_message(chat_id, message)

    except Exception as error:
        print(f"Free report error: {error}")
        send_message(
            chat_id,
            "I could not generate today's free report right now. Please try again later."
        )


def handle_premium(chat_id):
    message = (
        "⚽ World Cup Premium Intelligence\n\n"
        "Premium gives you the full daily betting intelligence report.\n\n"
        "Included:\n"
        "✅ All matches today/tomorrow\n"
        "✅ Full probability tables\n"
        "✅ Goals markets: Over/Under\n"
        "✅ Both teams score probabilities\n"
        "✅ Team goal projections\n"
        "✅ Market watchlist\n"
        "✅ Odds comparison\n"
        "✅ Private premium Telegram access\n"
        "✅ Future lineup/player alerts\n\n"
        "Early beta access:\n"
        "$30 CAD one-time pass\n\n"
        "Payment link:\n"
        "https://buy.stripe.com/4gMcN57gY3kJ2w8g9xgEg00\n\n"
        "After payment, send your payment email here.\n\n"
        "Important:\n"
        "This is statistical football analysis, not guaranteed betting advice.\n"
        "No model can guarantee outcomes. Bet responsibly."
    )

    send_message(chat_id, message)


def handle_update(update):
    message = update.get("message")

    if not message:
        return

    chat = message.get("chat", {})
    chat_id = chat.get("id")
    text = message.get("text", "")

    if not chat_id:
        return

    if not text:
        return

    command = text.split()[0].split("@")[0].lower()

    print(f"Received command: {command} from chat_id: {chat_id}")

    if command == "/start":
        handle_start(chat_id)

    elif command == "/free":
        handle_free(chat_id)

    elif command == "/premium":
        handle_premium(chat_id)

    else:
        send_message(
            chat_id,
            "Command not recognized. Use /start, /free or /premium."
        )


def clear_old_updates():
    print("Clearing old Telegram updates...")

    updates = get_updates()

    if not updates:
        print("No old updates found.")
        return None

    last_update_id = updates[-1].get("update_id")

    if last_update_id is None:
        return None

    print(f"Last old update id: {last_update_id}")
    return last_update_id + 1


def main():
    print("Bot listener started...")
    print("Press CTRL + C to stop the bot safely.")

    offset = clear_old_updates()

    while True:
        try:
            updates = get_updates(offset)

            for update in updates:
                update_id = update.get("update_id")

                if update_id is not None:
                    offset = update_id + 1

                handle_update(update)

            time.sleep(1)

        except Exception as error:
            print(f"Bot listener error: {error}")
            time.sleep(5)


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        print("")
        print("Bot stopped by user. Goodbye.")