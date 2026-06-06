import os
import requests
import pandas as pd
from dotenv import load_dotenv


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
ODDS_SNAPSHOT_PATH = os.path.join(RAW_DIR, "odds_api_snapshot.csv")
SPORTS_SNAPSHOT_PATH = os.path.join(RAW_DIR, "sports_api_snapshot.csv")

load_dotenv()

ODDS_API_KEY = os.getenv("ODDS_API_KEY")

BASE_URL = "https://api.the-odds-api.com/v4"


def validate_api_key():
    """
    Ensures the API key exists in .env.
    """

    if not ODDS_API_KEY:
        raise ValueError(
            "Missing ODDS_API_KEY in .env. "
            "Add ODDS_API_KEY=your_api_key_here to your .env file."
        )


def get_sports(all_sports: bool = True) -> list[dict]:
    """
    Fetches sports available from The Odds API.

    all_sports=True returns both active and inactive sports.
    This helps us inspect available soccer competitions.
    """

    validate_api_key()

    url = f"{BASE_URL}/sports/"
    params = {
        "apiKey": ODDS_API_KEY,
        "all": str(all_sports).lower(),
    }

    response = requests.get(url, params=params, timeout=20)

    if response.status_code != 200:
        raise RuntimeError(
            f"Sports API error: {response.status_code} - {response.text}"
        )

    return response.json()


def save_sports_snapshot(sports: list[dict]):
    """
    Saves available sports to CSV so we can inspect sport_key values.
    """

    os.makedirs(RAW_DIR, exist_ok=True)

    sports_df = pd.DataFrame(sports)
    sports_df.to_csv(SPORTS_SNAPSHOT_PATH, index=False)

    print(f"Sports snapshot saved: {SPORTS_SNAPSHOT_PATH}")

    soccer_df = sports_df[
        sports_df["group"].astype(str).str.contains("Soccer", case=False, na=False)
        | sports_df["title"].astype(str).str.contains("Soccer", case=False, na=False)
        | sports_df["description"].astype(str).str.contains("Soccer", case=False, na=False)
    ].copy()

    if not soccer_df.empty:
        print("\nPossible soccer sport keys:")
        print(
            soccer_df[
                ["key", "group", "title", "description", "active"]
            ].to_string(index=False)
        )
    else:
        print("\nNo soccer sport keys found in sports list.")


def fetch_odds_for_sport(
    sport_key: str,
    regions: str = "us",
    markets: str = "h2h",
    odds_format: str = "decimal",
) -> list[dict]:
    """
    Fetches odds for a sport key.

    Common params:
    - regions: us, uk, eu, au
    - markets: h2h
    - odds_format: decimal
    """

    validate_api_key()

    url = f"{BASE_URL}/sports/{sport_key}/odds"

    params = {
        "apiKey": ODDS_API_KEY,
        "regions": regions,
        "markets": markets,
        "oddsFormat": odds_format,
        "dateFormat": "iso",
    }

    response = requests.get(url, params=params, timeout=20)

    print(f"\nAPI requests remaining: {response.headers.get('x-requests-remaining')}")
    print(f"API requests used: {response.headers.get('x-requests-used')}")

    if response.status_code != 200:
        raise RuntimeError(
            f"Odds API error: {response.status_code} - {response.text}"
        )

    return response.json()


def flatten_odds_response(events: list[dict]) -> pd.DataFrame:
    """
    Converts The Odds API JSON response into a flat CSV-friendly table.

    One row per outcome per bookmaker.
    """

    rows = []

    for event in events:
        event_id = event.get("id")
        sport_key = event.get("sport_key")
        sport_title = event.get("sport_title")
        commence_time = event.get("commence_time")
        home_team = event.get("home_team")
        away_team = event.get("away_team")

        bookmakers = event.get("bookmakers", [])

        for bookmaker in bookmakers:
            bookmaker_key = bookmaker.get("key")
            bookmaker_title = bookmaker.get("title")
            bookmaker_last_update = bookmaker.get("last_update")

            markets = bookmaker.get("markets", [])

            for market in markets:
                market_key = market.get("key")
                market_last_update = market.get("last_update")

                outcomes = market.get("outcomes", [])

                for outcome in outcomes:
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
                        "decimal_odds": outcome.get("price"),
                    })

    return pd.DataFrame(rows)


def save_odds_snapshot(odds_df: pd.DataFrame):
    """
    Saves flattened odds to data/raw/odds_api_snapshot.csv.
    """

    os.makedirs(RAW_DIR, exist_ok=True)
    odds_df.to_csv(ODDS_SNAPSHOT_PATH, index=False)

    print(f"Odds snapshot saved: {ODDS_SNAPSHOT_PATH}")
    print(f"Rows saved: {len(odds_df)}")


def main():
    """
    First:
    - Fetch and save sports list.
    - Print soccer sport keys.

    Then:
    - If you already know a sport key, fetch odds for it.
    """

    sports = get_sports(all_sports=True)
    save_sports_snapshot(sports)

    print("\nNext step:")
    print("Open data/raw/sports_api_snapshot.csv and choose a soccer sport_key.")
    print("Then edit SPORT_KEY_TO_TEST below in this file.")

    # Change this after checking sports_api_snapshot.csv.
    # Examples may include soccer_epl, soccer_uefa_champs_league, etc.
    # World Cup-specific key may not be active until available in the API.
    SPORT_KEY_TO_TEST = "soccer_fifa_world_cup"

    if SPORT_KEY_TO_TEST:
        events = fetch_odds_for_sport(
            sport_key=SPORT_KEY_TO_TEST,
            regions="us",
            markets="h2h",
            odds_format="decimal",
        )

        odds_df = flatten_odds_response(events)
        save_odds_snapshot(odds_df)
    else:
        print("\nSPORT_KEY_TO_TEST is empty. No odds downloaded yet.")


if __name__ == "__main__":
    main()