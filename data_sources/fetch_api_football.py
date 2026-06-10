import os
import requests
import pandas as pd
from dotenv import load_dotenv


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")

RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
LEAGUES_OUTPUT_PATH = os.path.join(RAW_DIR, "api_football_leagues.csv")
FIXTURES_OUTPUT_PATH = os.path.join(RAW_DIR, "api_football_fixtures.csv")

load_dotenv(ENV_PATH)

API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
API_FOOTBALL_HOST = os.getenv("API_FOOTBALL_HOST", "v3.football.api-sports.io")

BASE_URL = f"https://{API_FOOTBALL_HOST}"


def get_headers():
    if not API_FOOTBALL_KEY:
        raise ValueError("Missing API_FOOTBALL_KEY in .env")

    return {
        "x-apisports-key": API_FOOTBALL_KEY
    }


def api_get(endpoint, params=None):
    url = f"{BASE_URL}/{endpoint}"

    response = requests.get(
        url,
        headers=get_headers(),
        params=params or {},
        timeout=30
    )

    print(f"GET {response.url}")
    print(f"Status code: {response.status_code}")

    if response.status_code != 200:
        print(response.text)
        response.raise_for_status()

    data = response.json()

    if data.get("errors"):
        print("API errors:")
        print(data["errors"])

    return data


def fetch_world_cup_leagues():
    """
    Finds leagues/cups matching World Cup.
    We need this to confirm the league ID used by API-Football.
    """

    print("Searching World Cup leagues...")

    data = api_get(
        "leagues",
        params={
            "search": "World Cup"
        }
    )

    rows = []

    for item in data.get("response", []):
        league = item.get("league", {})
        country = item.get("country", {})
        seasons = item.get("seasons", [])

        available_seasons = ",".join(
            str(season.get("year")) for season in seasons if season.get("year")
        )

        rows.append({
            "league_id": league.get("id"),
            "league_name": league.get("name"),
            "league_type": league.get("type"),
            "country_name": country.get("name"),
            "available_seasons": available_seasons,
        })

    os.makedirs(RAW_DIR, exist_ok=True)

    df = pd.DataFrame(rows)
    df.to_csv(LEAGUES_OUTPUT_PATH, index=False)

    print(f"Saved leagues to: {LEAGUES_OUTPUT_PATH}")
    print(df.to_string(index=False))

    return df


def fetch_fixtures_for_league(league_id, season):
    """
    Fetches fixtures for a chosen league_id and season.
    """

    print(f"Fetching fixtures for league_id={league_id}, season={season}...")

    data = api_get(
        "fixtures",
        params={
            "league": league_id,
            "season": season
        }
    )

    rows = []

    for item in data.get("response", []):
        fixture = item.get("fixture", {})
        league = item.get("league", {})
        teams = item.get("teams", {})
        goals = item.get("goals", {})
        score = item.get("score", {})

        rows.append({
            "fixture_id": fixture.get("id"),
            "date": fixture.get("date"),
            "timezone": fixture.get("timezone"),
            "venue_name": (fixture.get("venue") or {}).get("name"),
            "venue_city": (fixture.get("venue") or {}).get("city"),
            "status_long": (fixture.get("status") or {}).get("long"),
            "status_short": (fixture.get("status") or {}).get("short"),
            "league_id": league.get("id"),
            "league_name": league.get("name"),
            "season": league.get("season"),
            "round": league.get("round"),
            "home_team_id": (teams.get("home") or {}).get("id"),
            "home_team": (teams.get("home") or {}).get("name"),
            "away_team_id": (teams.get("away") or {}).get("id"),
            "away_team": (teams.get("away") or {}).get("name"),
            "home_goals": goals.get("home"),
            "away_goals": goals.get("away"),
            "winner_home": (teams.get("home") or {}).get("winner"),
            "winner_away": (teams.get("away") or {}).get("winner"),
            "halftime_home": (score.get("halftime") or {}).get("home"),
            "halftime_away": (score.get("halftime") or {}).get("away"),
            "fulltime_home": (score.get("fulltime") or {}).get("home"),
            "fulltime_away": (score.get("fulltime") or {}).get("away"),
        })

    df = pd.DataFrame(rows)
    df.to_csv(FIXTURES_OUTPUT_PATH, index=False)

    print(f"Saved fixtures to: {FIXTURES_OUTPUT_PATH}")
    print(f"Rows saved: {len(df)}")

    if not df.empty:
        print(df.head(20).to_string(index=False))

    return df


def main():
    fetch_world_cup_leagues()

    # FIFA World Cup in API-Football
    WORLD_CUP_LEAGUE_ID = 1
    WORLD_CUP_SEASON = 2026

    fetch_fixtures_for_league(
        league_id=WORLD_CUP_LEAGUE_ID,
        season=WORLD_CUP_SEASON
    )


if __name__ == "__main__":
    main()