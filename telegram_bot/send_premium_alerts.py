import os
import requests
from dotenv import load_dotenv


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_PATH)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_PREMIUM_CHAT_ID = os.getenv("TELEGRAM_PREMIUM_CHAT_ID")

REPORT_PATH = os.path.join(BASE_DIR, "reports", "telegram_premium_report.md")


def split_message(message, max_length=3800):
    parts = []
    current_part = ""

    blocks = message.split("━━━━━━━━━━━━━━")

    for block in blocks:
        block = block.strip()

        if not block:
            continue

        candidate = current_part + "\n\n" + block + "\n\n━━━━━━━━━━━━━━"

        if len(candidate) > max_length:
            if current_part:
                parts.append(current_part.strip())

            current_part = block + "\n\n━━━━━━━━━━━━━━"
        else:
            current_part = candidate

    if current_part.strip():
        parts.append(current_part.strip())

    return parts


def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN in .env")

    if not TELEGRAM_PREMIUM_CHAT_ID:
        raise ValueError("Missing TELEGRAM_PREMIUM_CHAT_ID in .env")

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    message_parts = split_message(message)

    for index, part in enumerate(message_parts, start=1):
        payload = {
            "chat_id": TELEGRAM_PREMIUM_CHAT_ID,
            "text": part,
        }

        response = requests.post(url, json=payload, timeout=30)

        if response.status_code != 200:
            print("Telegram error:")
            print(response.text)
            response.raise_for_status()

        print(f"Premium alert part {index}/{len(message_parts)} sent successfully.")


def main():
    if not os.path.exists(REPORT_PATH):
        raise FileNotFoundError(
            f"Missing {REPORT_PATH}. Run python src/premium_telegram_report_generator.py first."
        )

    with open(REPORT_PATH, "r", encoding="utf-8") as file:
        message = file.read()

    send_telegram_message(message)


if __name__ == "__main__":
    main()