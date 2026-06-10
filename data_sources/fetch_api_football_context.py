import os
import requests
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")

RAW_DIR = os.path.join(BASE_DIR, "data", "raw")

FIXTURES_INPUT_PATH = os.path.join(RAW_DIR, "api_football_fixtures.csv")
TEAM_RECENT_OUTPUT_PATH = os.path.join(RAW_DIR, "api_football_team_recent_stats.csv")
H2H_OUTPUT_PATH = os.path.join(RAW_DIR, "api_football_h2h_stats.csv")

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


def calculate_recent_stats(matches, team_id, team_name):
    """
    Calculates simple recent-form metrics from fixture results.
    """

    rows = []

    for item in matches:
        fixture = item.get("fixture", {})
        teams = item.get("teams", {})
        goals = item.get("goals", {})
        league = item.get("league", {})

        home = teams.get("home") or {}
        away = teams.get("away") or {}

        home_id = home.get("id")
        away_id = away.get("id")

        home_goals = goals.get("home")
        away_goals = goals.get("away")

        if home_goals is None or away_goals is None:
            continue

        is_home = team_id == home_id

        if is_home:
            goals_for = home_goals
            goals_against = away_goals
            opponent = away.get("name")
            result = "W" if home_goals > away_goals else "D" if home_goals == away_goals else "L"
        else:
            goals_for = away_goals
            goals_against = home_goals
            opponent = home.get("name")
            result = "W" if away_goals > home_goals else "D" if away_goals == home_goals else "L"

        total_goals = home_goals + away_goals

        rows.append({
            "date": fixture.get("date"),
            "team_id": team_id,
            "team": team_name,
            "opponent": opponent,
            "league_name": league.get("name"),
            "season": league.get("season"),
            "result": result,
            "goals_for": goals_for,
            "goals_against": goals_against,
            "total_goals": total_goals,
            "over_2_5": total_goals > 2.5,
            "btts": home_goals > 0 and away_goals > 0,
            "clean_sheet": goals_against == 0,
            "failed_to_score": goals_for == 0,
        })

    df = pd.DataFrame(rows)

    if df.empty:
        return {
            "team_id": team_id,
            "team": team_name,
            "matches_found": 0,
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "goals_for": 0,
            "goals_against": 0,
            "avg_goals_for": 0,
            "avg_goals_against": 0,
            "over_2_5_rate": 0,
            "btts_rate": 0,
            "clean_sheet_rate": 0,
            "failed_to_score_rate": 0,
        }

    return {
        "team_id": team_id,
        "team": team_name,
        "matches_found": len(df),
        "wins": int((df["result"] == "W").sum()),
        "draws": int((df["result"] == "D").sum()),
        "losses": int((df["result"] == "L").sum()),
        "goals_for": int(df["goals_for"].sum()),
        "goals_against": int(df["goals_against"].sum()),
        "avg_goals_for": round(df["goals_for"].mean(), 2),
        "avg_goals_against": round(df["goals_against"].mean(), 2),
        "over_2_5_rate": round(df["over_2_5"].mean(), 2),
        "btts_rate": round(df["btts"].mean(), 2),
        "clean_sheet_rate": round(df["clean_sheet"].mean(), 2),
        "failed_to_score_rate": round(df["failed_to_score"].mean(), 2),
    }


def fetch_recent_matches_for_team(team_id, team_name, last=10):
    """
    Fetches recent finished fixtures for a team.
    """

    data = api_get(
        "fixtures",
        params={
            "team": team_id,
            "last": last
        }
    )

    matches = data.get("response", [])

    return calculate_recent_stats(
        matches=matches,
        team_id=team_id,
        team_name=team_name
    )


def calculate_h2h_stats(matches, home_team_id, away_team_id, home_team_name, away_team_name):
    """
    Calculates H2H stats from the last direct meetings.
    """

    rows = []

    for item in matches:
        fixture = item.get("fixture", {})
        teams = item.get("teams", {})
        goals = item.get("goals", {})

        home = teams.get("home") or {}
        away = teams.get("away") or {}

        home_goals = goals.get("home")
        away_goals = goals.get("away")

        if home_goals is None or away_goals is None:
            continue

        total_goals = home_goals + away_goals

        if home_goals > away_goals:
            winner_id = home.get("id")
        elif away_goals > home_goals:
            winner_id = away.get("id")
        else:
            winner_id = None

        rows.append({
            "date": fixture.get("date"),
            "home_team": home.get("name"),
            "away_team": away.get("name"),
            "home_goals": home_goals,
            "away_goals": away_goals,
            "total_goals": total_goals,
            "winner_id": winner_id,
            "over_2_5": total_goals > 2.5,
            "btts": home_goals > 0 and away_goals > 0,
        })

    df = pd.DataFrame(rows)

    if df.empty:
        return {
            "home_team_id": home_team_id,
            "away_team_id": away_team_id,
            "home_team": home_team_name,
            "away_team": away_team_name,
            "h2h_matches_found": 0,
            "home_team_h2h_wins": 0,
            "away_team_h2h_wins": 0,
            "h2h_draws": 0,
            "h2h_avg_goals": 0,
            "h2h_over_2_5_rate": 0,
            "h2h_btts_rate": 0,
        }

    return {
        "home_team_id": home_team_id,
        "away_team_id": away_team_id,
        "home_team": home_team_name,
        "away_team": away_team_name,
        "h2h_matches_found": len(df),
        "home_team_h2h_wins": int((df["winner_id"] == home_team_id).sum()),
        "away_team_h2h_wins": int((df["winner_id"] == away_team_id).sum()),
        "h2h_draws": int(df["winner_id"].isna().sum()),
        "h2h_avg_goals": round(df["total_goals"].mean(), 2),
        "h2h_over_2_5_rate": round(df["over_2_5"].mean(), 2),
        "h2h_btts_rate": round(df["btts"].mean(), 2),
    }


def fetch_h2h_for_match(home_team_id, away_team_id, home_team_name, away_team_name, last=5):
    """
    Fetches H2H fixtures between two teams.
    """

    data = api_get(
        "fixtures/headtohead",
        params={
            "h2h": f"{home_team_id}-{away_team_id}",
            "last": last
        }
    )

    matches = data.get("response", [])

    return calculate_h2h_stats(
        matches=matches,
        home_team_id=home_team_id,
        away_team_id=away_team_id,
        home_team_name=home_team_name,
        away_team_name=away_team_name
    )

def filter_fixtures_today_tomorrow(fixtures, window_days=2):
    """
    Filters fixtures for today and tomorrow based on UTC date.

    If no matches are found, it falls back to the next 5 upcoming fixtures.
    """

    fixtures = fixtures.copy()

    fixtures["date_parsed"] = pd.to_datetime(
        fixtures["date"],
        utc=True,
        errors="coerce"
    )

    now = datetime.now(timezone.utc)

    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=window_days)

    filtered = fixtures[
        (fixtures["date_parsed"] >= start)
        & (fixtures["date_parsed"] < end)
    ].copy()

    if filtered.empty:
        print("No fixtures found for today/tomorrow.")
        print("Fallback: using next 5 upcoming fixtures.")

        future_fixtures = fixtures[
            fixtures["date_parsed"] >= now
        ].copy()

        future_fixtures = future_fixtures.sort_values(
            by="date_parsed",
            ascending=True
        )

        return future_fixtures.head(5).drop(columns=["date_parsed"])

    filtered = filtered.sort_values(
        by="date_parsed",
        ascending=True
    )

    return filtered.drop(columns=["date_parsed"])

def main():
    if not os.path.exists(FIXTURES_INPUT_PATH):
        raise FileNotFoundError(
            f"Missing {FIXTURES_INPUT_PATH}. Run fetch_api_football.py first."
        )

    fixtures = pd.read_csv(FIXTURES_INPUT_PATH)

    # Use today's and tomorrow's fixtures for the real daily report.
    test_fixtures = filter_fixtures_today_tomorrow(
    fixtures=fixtures,
    window_days=2
)

    print("")
    print("Fixtures selected for today's report:")
    print(
     test_fixtures[
        ["date", "home_team", "away_team"]
    ].to_string(index=False)
)

    teams = []

    for _, row in test_fixtures.iterrows():
        teams.append({
            "team_id": int(row["home_team_id"]),
            "team": row["home_team"]
        })
        teams.append({
            "team_id": int(row["away_team_id"]),
            "team": row["away_team"]
        })

    unique_teams = pd.DataFrame(teams).drop_duplicates()

    recent_rows = []

    print("")
    print("Fetching recent team stats...")

    for _, team in unique_teams.iterrows():
        recent_rows.append(
            fetch_recent_matches_for_team(
                team_id=int(team["team_id"]),
                team_name=team["team"],
                last=10
            )
        )

    recent_df = pd.DataFrame(recent_rows)
    recent_df.to_csv(TEAM_RECENT_OUTPUT_PATH, index=False)

    print(f"Saved recent team stats to: {TEAM_RECENT_OUTPUT_PATH}")
    print(recent_df.to_string(index=False))

    h2h_rows = []

    print("")
    print("Fetching H2H stats...")

    for _, row in test_fixtures.iterrows():
        h2h_rows.append(
            fetch_h2h_for_match(
                home_team_id=int(row["home_team_id"]),
                away_team_id=int(row["away_team_id"]),
                home_team_name=row["home_team"],
                away_team_name=row["away_team"],
                last=5
            )
        )

    h2h_df = pd.DataFrame(h2h_rows)
    h2h_df.to_csv(H2H_OUTPUT_PATH, index=False)

    print(f"Saved H2H stats to: {H2H_OUTPUT_PATH}")
    print(h2h_df.to_string(index=False))


if __name__ == "__main__":
    main()