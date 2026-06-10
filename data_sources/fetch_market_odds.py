import os
import requests
import pandas as pd
from dotenv import load_dotenv


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")

RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
OUTPUT_PATH = os.path.join(RAW_DIR, "odds_markets_api_snapshot.csv")

load_dotenv(ENV_PATH)

ODDS_API_KEY = os.getenv("ODDS_API_KEY")

SPORT_KEY = "soccer_fifa_world_cup"
REGIONS = "us"
MARKETS = "h2h,totals,spreads"
ODDS_FORMAT = "decimal"


def fetch_market_odds():
    if not ODDS_API_KEY:
        raise ValueError("Missing ODDS_API_KEY in .env")

    url = f"https://api.the-odds-api.com/v4/sports/{SPORT_KEY}/odds"

    params = {
        "apiKey": ODDS_API_KEY,
        "regions": REGIONS,
        "markets": MARKETS,
        "oddsFormat": ODDS_FORMAT,
    }

    response = requests.get(url, params=params, timeout=30)

    print(f"GET {response.url}")
    print(f"Status code: {response.status_code}")

    if response.status_code != 200:
        print(response.text)
        response.raise_for_status()

    data = response.json()

    rows = []

    for event in data:
        event_id = event.get("id")
        sport_key = event.get("sport_key")
        sport_title = event.get("sport_title")
        commence_time = event.get("commence_time")
        home_team = event.get("home_team")
        away_team = event.get("away_team")

        for bookmaker in event.get("bookmakers", []):
            bookmaker_key = bookmaker.get("key")
            bookmaker_title = bookmaker.get("title")
            bookmaker_last_update = bookmaker.get("last_update")

            for market in bookmaker.get("markets", []):
                market_key = market.get("key")
                market_last_update = market.get("last_update")

                for outcome in market.get("outcomes", []):
                    rows.append({
                        "event_id": event_id,
                        "sport_key": sport_key,
                        "sport_title": sport_title,
                        "commence_time": commence_time,
                        "home_team": home_team,
                        "away_team": away_team,
                        "bookmaker_key": bookmaker_key,
                        "bookmaker_title": bookmaker_title,
                        "bookmaker_last_update": bookmaker_last_update,
                        "market_key": market_key,
                        "market_last_update": market_last_update,
                        "selection": outcome.get("name"),
                        "point": outcome.get("point"),
                        "decimal_odds": outcome.get("price"),
                    })

    os.makedirs(RAW_DIR, exist_ok=True)

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_PATH, index=False)

    print(f"Saved market odds to: {OUTPUT_PATH}")
    print(f"Rows saved: {len(df)}")

    if not df.empty:
        print(df.head(30).to_string(index=False))

    return df


def main():
    fetch_market_odds()


if __name__ == "__main__":
    main()