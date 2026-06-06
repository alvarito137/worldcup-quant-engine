import os
import pandas as pd


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
PICK_HISTORY_PATH = os.path.join(PROCESSED_DIR, "pick_history.csv")


def calculate_profit_loss_units(result: str, odds_taken: float, stake_pct: float) -> float:
    """
    Calculates profit/loss in units.

    We treat stake_pct as the staking unit.

    WON:
        profit = stake * (odds - 1)

    LOST:
        profit = -stake

    PUSH:
        profit = 0
    """

    result = result.upper()

    if result == "WON":
        return stake_pct * (odds_taken - 1)

    if result == "LOST":
        return -stake_pct

    if result == "PUSH":
        return 0.0

    raise ValueError("Result must be WON, LOST, or PUSH.")


def show_open_picks(history: pd.DataFrame):
    """
    Displays open picks so the user can choose which one to update.
    """

    open_picks = history[history["status"] == "OPEN"].copy()

    if open_picks.empty:
        print("No open picks found.")
        return open_picks

    print("\nOpen picks:")
    print("-" * 100)

    for index, row in open_picks.iterrows():
        print(
            f"[{index}] "
            f"{row['date']} | "
            f"{row['match']} | "
            f"Selection: {row['selection']} | "
            f"Odds: {row['odds_taken']} | "
            f"Signal: {row['signal']} | "
            f"Risk: {row['risk_label']}"
        )

    print("-" * 100)

    return open_picks


def update_single_pick():
    """
    Allows manual update of one open pick.
    """

    if not os.path.exists(PICK_HISTORY_PATH):
        print(f"No pick history found at: {PICK_HISTORY_PATH}")
        print("Run python run_pipeline.py first.")
        return

    history = pd.read_csv(PICK_HISTORY_PATH)

    open_picks = show_open_picks(history)

    if open_picks.empty:
        return

    try:
        pick_index = int(input("\nEnter the index of the pick to update: ").strip())
    except ValueError:
        print("Invalid index. Please enter a number.")
        return

    if pick_index not in history.index:
        print("Invalid pick index.")
        return

    if history.loc[pick_index, "status"] != "OPEN":
        print("This pick is not open.")
        return

    result = input("Enter result (WON / LOST / PUSH): ").strip().upper()

    if result not in ["WON", "LOST", "PUSH"]:
        print("Invalid result. Must be WON, LOST, or PUSH.")
        return

    odds_taken = float(history.loc[pick_index, "odds_taken"])
    stake_pct = float(history.loc[pick_index, "stake_pct"])

    profit_loss_units = calculate_profit_loss_units(
        result=result,
        odds_taken=odds_taken,
        stake_pct=stake_pct
    )

    closing_odds_input = input("Enter closing odds, or press Enter to skip: ").strip()

    if closing_odds_input:
        closing_odds = float(closing_odds_input)
        closing_line_value = closing_odds - odds_taken
    else:
        closing_odds = None
        closing_line_value = None

    history.loc[pick_index, "result"] = result
    history.loc[pick_index, "profit_loss_units"] = round(profit_loss_units, 4)
    history.loc[pick_index, "closing_odds"] = closing_odds
    history.loc[pick_index, "closing_line_value"] = closing_line_value
    history.loc[pick_index, "status"] = "CLOSED"

    history.to_csv(PICK_HISTORY_PATH, index=False)

    print("\nPick updated successfully.")
    print(f"Result: {result}")
    print(f"Profit/Loss units: {profit_loss_units:.4f}")


def main():
    update_single_pick()


if __name__ == "__main__":
    main()