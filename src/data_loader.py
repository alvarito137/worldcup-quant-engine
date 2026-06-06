import os
import pandas as pd
from dotenv import load_dotenv


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

DATA_MODE = os.getenv("DATA_MODE", "mock").lower()

RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

FIXTURES_PATH = os.path.join(RAW_DIR, "fixtures.csv")
ODDS_PATH = os.path.join(RAW_DIR, "odds.csv")
RATINGS_PATH = os.path.join(RAW_DIR, "team_ratings.csv")


def ensure_directories():
    """
    Creates all required project folders if they do not exist.
    """

    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)


def create_mock_data():
    """
    Creates mock data for the MVP.

    Files created:
    - data/raw/fixtures.csv
    - data/raw/odds.csv
    - data/raw/team_ratings.csv
    """

    fixtures = pd.DataFrame([
        {
            "match_id": 1,
            "date": "2026-06-11",
            "team_a": "Mexico",
            "team_b": "South Africa",
            "stage": "Group Stage"
        },
        {
            "match_id": 2,
            "date": "2026-06-12",
            "team_a": "Canada",
            "team_b": "Qatar",
            "stage": "Group Stage"
        },
        {
            "match_id": 3,
            "date": "2026-06-13",
            "team_a": "Brazil",
            "team_b": "Morocco",
            "stage": "Group Stage"
        },
        {
            "match_id": 4,
            "date": "2026-06-14",
            "team_a": "Argentina",
            "team_b": "Austria",
            "stage": "Group Stage"
        },
        {
            "match_id": 5,
            "date": "2026-06-15",
            "team_a": "Spain",
            "team_b": "Uruguay",
            "stage": "Group Stage"
        }
    ])

    odds = pd.DataFrame([
        {"match_id": 1, "selection": "Mexico", "decimal_odds": 1.65},
        {"match_id": 1, "selection": "Draw", "decimal_odds": 3.70},
        {"match_id": 1, "selection": "South Africa", "decimal_odds": 5.20},

        {"match_id": 2, "selection": "Canada", "decimal_odds": 2.05},
        {"match_id": 2, "selection": "Draw", "decimal_odds": 3.25},
        {"match_id": 2, "selection": "Qatar", "decimal_odds": 3.60},

        {"match_id": 3, "selection": "Brazil", "decimal_odds": 1.80},
        {"match_id": 3, "selection": "Draw", "decimal_odds": 3.50},
        {"match_id": 3, "selection": "Morocco", "decimal_odds": 4.70},

        {"match_id": 4, "selection": "Argentina", "decimal_odds": 1.55},
        {"match_id": 4, "selection": "Draw", "decimal_odds": 4.00},
        {"match_id": 4, "selection": "Austria", "decimal_odds": 6.00},

        {"match_id": 5, "selection": "Spain", "decimal_odds": 1.95},
        {"match_id": 5, "selection": "Draw", "decimal_odds": 3.40},
        {"match_id": 5, "selection": "Uruguay", "decimal_odds": 3.90},
    ])

    ratings = pd.DataFrame([
        {"team": "Mexico", "rating": 1770},
        {"team": "South Africa", "rating": 1580},
        {"team": "Canada", "rating": 1700},
        {"team": "Qatar", "rating": 1600},
        {"team": "Brazil", "rating": 1900},
        {"team": "Morocco", "rating": 1810},
        {"team": "Argentina", "rating": 1920},
        {"team": "Austria", "rating": 1740},
        {"team": "Spain", "rating": 1880},
        {"team": "Uruguay", "rating": 1820},
    ])

    fixtures.to_csv(FIXTURES_PATH, index=False)
    odds.to_csv(ODDS_PATH, index=False)
    ratings.to_csv(RATINGS_PATH, index=False)

    print("Mock data created.")


def load_or_create_mock_data():
    """
    Checks if required raw data exists.
    If DATA_MODE=api, it does not create mock data.
    """

    ensure_directories()

    if DATA_MODE == "api":
        print("DATA_MODE=api. Using API data files.")
        return

    if (
        not os.path.exists(FIXTURES_PATH)
        or not os.path.exists(ODDS_PATH)
        or not os.path.exists(RATINGS_PATH)
    ):
        create_mock_data()
    else:
        print("Raw mock data already exists.")