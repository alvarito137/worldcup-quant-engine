import os
import pandas as pd


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
PICK_HISTORY_PATH = os.path.join(PROCESSED_DIR, "pick_history.csv")


def build_history_rows(picks: pd.DataFrame) -> pd.DataFrame:
    """
    Converts current picks into a pick history format.

    Results are initially marked as PENDING.
    Later, they can be updated with WON / LOST / PUSH.
    """

    value_picks = picks[picks["signal"] != "NO BET"].copy()

    if value_picks.empty:
        return pd.DataFrame()

    history = pd.DataFrame()

    history["date"] = value_picks["date"]
    history["match_id"] = value_picks["match_id"]
    history["match"] = value_picks["team_a"] + " vs " + value_picks["team_b"]
    history["selection"] = value_picks["selection"]
    history["odds_taken"] = value_picks["decimal_odds"]
    history["implied_probability"] = value_picks["implied_probability"]
    history["model_probability"] = value_picks["model_probability"]
    history["value_gap"] = value_picks["value_gap"]
    history["signal"] = value_picks["signal"]
    history["risk_label"] = value_picks["risk_label"]
    history["confidence_score"] = value_picks["confidence_score"]
    history["stake_pct"] = value_picks["kelly_stake_pct"]

    history["result"] = "PENDING"
    history["profit_loss_units"] = 0.0
    history["closing_odds"] = None
    history["closing_line_value"] = None
    history["status"] = "OPEN"

    return history


def create_pick_id(row) -> str:
    """
    Creates a unique ID for each pick to avoid duplicates.
    """

    return (
        str(row["date"])
        + "_"
        + str(row["match_id"])
        + "_"
        + str(row["selection"])
    ).replace(" ", "_").lower()


def update_pick_history(picks: pd.DataFrame):
    """
    Appends new value picks to pick_history.csv without duplicating existing picks.
    """

    os.makedirs(PROCESSED_DIR, exist_ok=True)

    new_history = build_history_rows(picks)

    if new_history.empty:
        print("No value picks to add to history.")
        return

    new_history["pick_id"] = new_history.apply(create_pick_id, axis=1)

    if os.path.exists(PICK_HISTORY_PATH):
        existing_history = pd.read_csv(PICK_HISTORY_PATH)

        if "pick_id" not in existing_history.columns:
            existing_history["pick_id"] = existing_history.apply(create_pick_id, axis=1)

        existing_pick_ids = set(existing_history["pick_id"])

        new_rows = new_history[~new_history["pick_id"].isin(existing_pick_ids)]

        combined_history = pd.concat(
            [existing_history, new_rows],
            ignore_index=True
        )
    else:
        new_rows = new_history
        combined_history = new_history

    combined_history.to_csv(PICK_HISTORY_PATH, index=False)

    print(f"Pick history updated: {PICK_HISTORY_PATH}")
    print(f"New picks added to history: {len(new_rows)}")