import os
import pandas as pd


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RAW_DIR = os.path.join(BASE_DIR, "data", "raw")

ODDS_API_SNAPSHOT_PATH = os.path.join(RAW_DIR, "odds_api_snapshot.csv")

FIXTURES_API_OUTPUT_PATH = os.path.join(RAW_DIR, "fixtures_api.csv")
ODDS_API_OUTPUT_PATH = os.path.join(RAW_DIR, "odds_api.csv")
TEAM_RATINGS_API_OUTPUT_PATH = os.path.join(RAW_DIR, "team_ratings_api.csv")

EXISTING_RATINGS_PATH = os.path.join(RAW_DIR, "team_ratings.csv")


def load_odds_snapshot() -> pd.DataFrame:
    """
    Loads raw odds snapshot from The Odds API.
    """

    if not os.path.exists(ODDS_API_SNAPSHOT_PATH):
        raise FileNotFoundError(
            f"Missing odds snapshot: {ODDS_API_SNAPSHOT_PATH}. "
            "Run python data_sources/fetch_odds.py first."
        )

    return pd.read_csv(ODDS_API_SNAPSHOT_PATH)


def create_match_id_map(snapshot: pd.DataFrame) -> dict:
    """
    Creates a clean internal match_id for each event_id.
    """

    unique_events = snapshot["event_id"].drop_duplicates().reset_index(drop=True)

    return {
        event_id: index + 1
        for index, event_id in enumerate(unique_events)
    }


def build_fixtures(snapshot: pd.DataFrame, match_id_map: dict) -> pd.DataFrame:
    """
    Converts API event data into internal fixtures format.
    """

    fixtures = snapshot[
        [
            "event_id",
            "commence_time",
            "home_team",
            "away_team",
            "sport_title",
        ]
    ].drop_duplicates(subset=["event_id"]).copy()

    fixtures["match_id"] = fixtures["event_id"].map(match_id_map)

    fixtures["date"] = pd.to_datetime(fixtures["commence_time"]).dt.date.astype(str)
    fixtures["team_a"] = fixtures["home_team"]
    fixtures["team_b"] = fixtures["away_team"]
    fixtures["stage"] = fixtures["sport_title"]

    fixtures = fixtures[
        [
            "match_id",
            "date",
            "team_a",
            "team_b",
            "stage",
        ]
    ]

    fixtures = fixtures.sort_values(by=["date", "match_id"])

    return fixtures


def build_average_odds(snapshot: pd.DataFrame, match_id_map: dict) -> pd.DataFrame:
    """
    Converts API odds into internal odds format.

    We average odds across bookmakers for each event and selection.
    This is better than randomly choosing one bookmaker.
    """

    odds = snapshot.copy()

    odds = odds[odds["market_key"] == "h2h"].copy()

    odds["match_id"] = odds["event_id"].map(match_id_map)

    odds = odds[
        [
            "match_id",
            "selection",
            "decimal_odds",
        ]
    ].copy()

    odds["decimal_odds"] = pd.to_numeric(odds["decimal_odds"], errors="coerce")
    odds = odds.dropna(subset=["decimal_odds"])

    average_odds = (
        odds.groupby(["match_id", "selection"], as_index=False)
        .agg(decimal_odds=("decimal_odds", "mean"))
    )

    average_odds["decimal_odds"] = average_odds["decimal_odds"].round(2)

    average_odds = average_odds.sort_values(by=["match_id", "selection"])

    return average_odds


def build_team_ratings(fixtures: pd.DataFrame) -> pd.DataFrame:
    """
    Builds team ratings for API teams.

    If a team already exists in team_ratings.csv, keep its rating.
    Otherwise assign a temporary default rating.

    Later, we should replace these with real ELO/FIFA/model ratings.
    """

    teams = sorted(
        set(fixtures["team_a"].dropna().tolist())
        | set(fixtures["team_b"].dropna().tolist())
    )

    existing_rating_map = {}

    if os.path.exists(EXISTING_RATINGS_PATH):
        existing = pd.read_csv(EXISTING_RATINGS_PATH)
        existing_rating_map = dict(zip(existing["team"], existing["rating"]))

    rows = []

    for team in teams:
        rating = existing_rating_map.get(team, 1600)

        rows.append({
            "team": team,
            "rating": rating,
        })

    ratings = pd.DataFrame(rows)

    return ratings


def main():
    snapshot = load_odds_snapshot()

    if snapshot.empty:
        print("odds_api_snapshot.csv is empty. Nothing to adapt.")
        return

    match_id_map = create_match_id_map(snapshot)

    fixtures = build_fixtures(snapshot, match_id_map)
    odds = build_average_odds(snapshot, match_id_map)
    ratings = build_team_ratings(fixtures)

    fixtures.to_csv(FIXTURES_API_OUTPUT_PATH, index=False)
    odds.to_csv(ODDS_API_OUTPUT_PATH, index=False)
    ratings.to_csv(TEAM_RATINGS_API_OUTPUT_PATH, index=False)

    print(f"Fixtures API file created: {FIXTURES_API_OUTPUT_PATH}")
    print(f"Odds API file created: {ODDS_API_OUTPUT_PATH}")
    print(f"Team ratings API file created: {TEAM_RATINGS_API_OUTPUT_PATH}")
    print("")
    print(f"Fixtures: {len(fixtures)}")
    print(f"Odds rows: {len(odds)}")
    print(f"Teams: {len(ratings)}")


if __name__ == "__main__":
    main()