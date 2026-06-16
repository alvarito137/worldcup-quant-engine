import os
import requests
import pandas as pd
from dotenv import load_dotenv


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_PATH)

API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
API_FOOTBALL_HOST = os.getenv("API_FOOTBALL_HOST", "v3.football.api-sports.io")

FIXTURES_PATH = os.path.join(BASE_DIR, "data", "raw", "api_football_fixtures.csv")


def get_fixture_statistics(fixture_id):
    url = f"https://{API_FOOTBALL_HOST}/fixtures/statistics"

    headers = {
        "x-rapidapi-key": API_FOOTBALL_KEY,
        "x-rapidapi-host": API_FOOTBALL_HOST,
    }

    params = {
        "fixture": fixture_id
    }

    response = requests.get(url, headers=headers, params=params, timeout=30)
    response.raise_for_status()

    return response.json()


def main():
    if not os.path.exists(FIXTURES_PATH):
        raise FileNotFoundError(
            "Missing api_football_fixtures.csv. Run fetch_api_football.py first."
        )

    fixtures = pd.read_csv(FIXTURES_PATH)

    print("")
    print("Available fixture columns:")
    print(fixtures.columns.tolist())

    print("")
    print("First 10 fixtures:")
    print(fixtures.head(10).to_string(index=False))

    fixture_id_column = None

    for possible_name in ["fixture_id", "id", "fixture"]:
        if possible_name in fixtures.columns:
            fixture_id_column = possible_name
            break

    if fixture_id_column is None:
        raise ValueError(
            "Could not find fixture id column. Look at printed columns and update the script."
        )

    fixture_id = fixtures.iloc[0][fixture_id_column]

    print("")
    print(f"Testing fixture id: {fixture_id}")

    data = get_fixture_statistics(fixture_id)

    print("")
    print("Raw API response:")
    print(data)

    print("")
    print("Detected statistics:")

    response = data.get("response", [])

    for team_block in response:
        team_name = team_block.get("team", {}).get("name", "Unknown")
        print("")
        print(f"Team: {team_name}")

        for stat in team_block.get("statistics", []):
            print(f"- {stat.get('type')}: {stat.get('value')}")


if __name__ == "__main__":
    main()