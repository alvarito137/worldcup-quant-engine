import os
import time
import requests
from dotenv import load_dotenv


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_PATH)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Missing TELEGRAM_BOT_TOKEN in .env")

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def send_message(chat_id, text):
    url = f"{BASE_URL}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text[:4000],
    }

    response = requests.post(url, json=payload, timeout=30)

    if response.status_code != 200:
        print("Telegram error:")
        print(response.text)

    return response


def handle_start(chat_id):
    message = (
        "⚽ Welcome to World Cup Betting Intelligence\n\n"
        "This bot shares data-backed football market watchlists.\n\n"
        "Free version includes:\n"
        "- Top 3 markets to watch\n"
        "- Sportsbook lines\n"
        "- Best available odds\n"
        "- Risk/profile notes\n\n"
        "Important:\n"
        "These are not guaranteed bets. Educational only. Bet responsibly.\n\n"
        "Commands:\n"
        "/start - Start the bot\n"
        "/free - Get the latest free watchlist"
        "/premium - See premium intelligence info"
    )

    send_message(chat_id, message)


def handle_free(chat_id):
    report_path = os.path.join(
        BASE_DIR,
        "reports",
        "telegram_free_intelligence.md"
    )

    if not os.path.exists(report_path):
        send_message(
            chat_id,
            "No free report generated yet. Please try again later."
        )
        return

    with open(report_path, "r", encoding="utf-8") as file:
        message = file.read()

    send_message(chat_id, message)

def handle_premium(chat_id):
    message = (
        "⚽ World Cup Premium Intelligence\n\n"
        "The free bot gives you a simple top watchlist.\n\n"
        "Premium gives you the full daily betting intelligence report.\n\n"
        "Included:\n"
        "✅ All matches today/tomorrow\n"
        "✅ Full probability table for each match\n"
        "✅ Goals markets: Over/Under\n"
        "✅ Both teams to score probabilities\n"
        "✅ Team goal projections\n"
        "✅ Market watchlist\n"
        "✅ Odds comparison\n"
        "✅ CSV access\n"
        "✅ Premium Telegram alerts\n"
        "✅ Future lineup/player alerts\n\n"
        "Early access:\n"
        "$29 beta pass\n\n"
        "Important:\n"
        "This is statistical analysis, not guaranteed betting advice.\n"
        "No model can guarantee outcomes. Bet responsibly.\n\n"
        "To join:\n"
        "Reply with: I want Premium"
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

    if text == "/start":
        handle_start(chat_id)
    elif text == "/free":
        handle_free(chat_id)
    elif text == "/premium":
        handle_premium(chat_id)
    else:
        send_message(
            chat_id,
            "Command not recognized. Use /start or /free."
        )


def main():
    print("Telegram bot listener started...")
    print("Press Ctrl + C to stop.")

    offset = None

    while True:
        try:
            params = {
                "timeout": 30,
            }

            if offset is not None:
                params["offset"] = offset

            response = requests.get(
                f"{BASE_URL}/getUpdates",
                params=params,
                timeout=35
            )

            if response.status_code != 200:
                print("Telegram getUpdates error:")
                print(response.text)
                time.sleep(5)
                continue

            data = response.json()

            for update in data.get("result", []):
                offset = update["update_id"] + 1
                handle_update(update)

        except KeyboardInterrupt:
            print("Bot listener stopped.")
            break

        except Exception as error:
            print(f"Error: {error}")
            time.sleep(5)


if __name__ == "__main__":
    main()