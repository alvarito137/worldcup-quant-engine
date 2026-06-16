import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_PATH)

API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
API_FOOTBALL_HOST = os.getenv("API_FOOTBALL_HOST", "v3.football.api-sports.io")

FIXTURES_PATH = os.path.join(BASE_DIR, "data", "raw", "api_football_fixtures.csv")
OUTPUT_PATH = os.path.join(BASE_DIR, "data", "raw", "api_football_advanced_team_stats.csv")


HEADERS = {
    "x-rapidapi-key": API_FOOTBALL_KEY,
    "x-rapidapi-host": API_FOOTBALL_HOST,
}


def api_get(endpoint, params):
    url = f"https://{API_FOOTBALL_HOST}/{endpoint}"

    response = requests.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=30
    )

    response.raise_for_status()
    return response.json()


def value_to_number(value):
    if value is None:
        return 0.0

    if isinstance(value, str):
        value = value.replace("%", "").strip()

    try:
        return float(value)
    except Exception:
        return 0.0


def get_stat(statistics, stat_name):
    for stat in statistics:
        if stat.get("type") == stat_name:
            return value_to_number(stat.get("value"))

    return 0.0


def get_last_finished_fixtures(team_id, limit=10):
    data = api_get(
        "fixtures",
        {
            "team": team_id,
            "last": limit,
            "status": "FT",
        }
    )

    return data.get("response", [])


def get_fixture_statistics(fixture_id):
    data = api_get(
        "fixtures/statistics",
        {
            "fixture": fixture_id
        }
    )

    return data.get("response", [])


def extract_team_stats_from_fixture(fixture_stats, team_id):
    for team_block in fixture_stats:
        team = team_block.get("team", {})
        current_team_id = team.get("id")

        if int(current_team_id) == int(team_id):
            return team_block.get("statistics", [])

    return []


def extract_opponent_stats_from_fixture(fixture_stats, team_id):
    for team_block in fixture_stats:
        team = team_block.get("team", {})
        current_team_id = team.get("id")

        if int(current_team_id) != int(team_id):
            return team_block.get("statistics", [])

    return []


def build_team_advanced_stats(team_id, team_name):
    last_fixtures = get_last_finished_fixtures(team_id, limit=10)

    rows = []

    for fixture in last_fixtures:
        fixture_id = fixture.get("fixture", {}).get("id")

        if not fixture_id:
            continue

        try:
            fixture_stats = get_fixture_statistics(fixture_id)
            time.sleep(0.4)

            team_stats = extract_team_stats_from_fixture(fixture_stats, team_id)
            opponent_stats = extract_opponent_stats_from_fixture(fixture_stats, team_id)

            if not team_stats:
                continue

            row = {
                "team_id": team_id,
                "team": team_name,
                "fixture_id": fixture_id,

                "corners_for": get_stat(team_stats, "Corner Kicks"),
                "corners_against": get_stat(opponent_stats, "Corner Kicks"),

                "yellow_cards": get_stat(team_stats, "Yellow Cards"),
                "red_cards": get_stat(team_stats, "Red Cards"),

                "fouls": get_stat(team_stats, "Fouls"),
                "shots_total": get_stat(team_stats, "Total Shots"),
                "shots_on_goal": get_stat(team_stats, "Shots on Goal"),
                "shots_off_goal": get_stat(team_stats, "Shots off Goal"),

                "possession": get_stat(team_stats, "Ball Possession"),
                "expected_goals": get_stat(team_stats, "expected_goals"),
                "goalkeeper_saves": get_stat(team_stats, "Goalkeeper Saves"),
            }

            rows.append(row)

        except Exception as error:
            print(f"Could not fetch stats for fixture {fixture_id}: {error}")

    if not rows:
        return None

    df = pd.DataFrame(rows)

    summary = {
        "team_id": team_id,
        "team": team_name,
        "matches_used": len(df),

        "avg_corners_for": df["corners_for"].mean(),
        "avg_corners_against": df["corners_against"].mean(),

        "avg_yellow_cards": df["yellow_cards"].mean(),
        "avg_red_cards": df["red_cards"].mean(),

        "avg_fouls": df["fouls"].mean(),
        "avg_total_shots": df["shots_total"].mean(),
        "avg_shots_on_goal": df["shots_on_goal"].mean(),
        "avg_shots_off_goal": df["shots_off_goal"].mean(),

        "avg_possession": df["possession"].mean(),
        "avg_expected_goals": df["expected_goals"].mean(),
        "avg_goalkeeper_saves": df["goalkeeper_saves"].mean(),
    }

    return summary


def main():
    if not os.path.exists(FIXTURES_PATH):
        raise FileNotFoundError(
            "Missing api_football_fixtures.csv. Run fetch_api_football.py first."
        )

    fixtures = pd.read_csv(FIXTURES_PATH)

    fixtures["date_parsed"] = pd.to_datetime(
        fixtures["date"],
        utc=True,
        errors="coerce"
    )

    now = pd.Timestamp.now(tz="UTC")

    upcoming = fixtures[
        fixtures["date_parsed"] >= now
    ].copy()

    upcoming = upcoming.sort_values(
        by="date_parsed",
        ascending=True
    ).head(5)

    teams = []

    for _, row in upcoming.iterrows():
        teams.append(
            {
                "team_id": int(row["home_team_id"]),
                "team": row["home_team"],
            }
        )

        teams.append(
            {
                "team_id": int(row["away_team_id"]),
                "team": row["away_team"],
            }
        )

    unique_teams = {
        team["team_id"]: team
        for team in teams
    }

    summaries = []

    for team_id, team_data in unique_teams.items():
        print(f"Fetching advanced stats for {team_data['team']}...")

        summary = build_team_advanced_stats(
            team_id=team_id,
            team_name=team_data["team"]
        )

        if summary:
            summaries.append(summary)

        time.sleep(0.5)

    output_df = pd.DataFrame(summaries)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    output_df.to_csv(OUTPUT_PATH, index=False)

    print("")
    print(f"Advanced team stats saved to: {OUTPUT_PATH}")
    print(output_df.to_string(index=False))


if __name__ == "__main__":
    main()