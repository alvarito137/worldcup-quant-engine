import os
import re
import pandas as pd


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

MARKET_ANGLES_PATH = os.path.join(PROCESSED_DIR, "market_angles.csv")
ODDS_MARKETS_PATH = os.path.join(RAW_DIR, "odds_markets_api_snapshot.csv")

OUTPUT_CSV_PATH = os.path.join(PROCESSED_DIR, "market_angles_with_odds.csv")
OUTPUT_REPORT_PATH = os.path.join(REPORTS_DIR, "daily_betting_intelligence_with_odds.md")


def normalize_team_name(name):
    """
    Normalizes team names so API-Football and The Odds API names can match.
    """

    if pd.isna(name):
        return ""

    name = str(name).lower().strip()

    replacements = {
        "usa": "united states",
        "u.s.a.": "united states",
        "united states": "united states",
        "czechia": "czech republic",
        "czech republic": "czech republic",
        "côte d'ivoire": "ivory coast",
        "cote d'ivoire": "ivory coast",
        "ivory coast": "ivory coast",
        "korea republic": "south korea",
        "south korea": "south korea",
        "bosnia and herzegovina": "bosnia & herzegovina",
        "bosnia & herzegovina": "bosnia & herzegovina",
        "turkiye": "turkey",
        "türkiye": "turkey",
        "turkey": "turkey",
        "curacao": "curaçao",
        "curaçao": "curaçao",
        "dr congo": "congo dr",
        "congo dr": "congo dr",
    }

    return replacements.get(name, name)


def normalize_match_key(home_team, away_team):
    home = normalize_team_name(home_team)
    away = normalize_team_name(away_team)
    return f"{home} vs {away}"


def profile_from_confidence(confidence_score):
    """
    Converts confidence score into a commercial profile label.
    """

    confidence_score = float(confidence_score)

    if confidence_score >= 0.75:
        return "CONSERVATIVE"

    if confidence_score >= 0.60:
        return "BALANCED"

    return "AGGRESSIVE"


def extract_model_line(selection):
    """
    Extracts direction and line from model angle text.

    Examples:
    - Under 3.5 Goals -> Under, 3.5
    - Over 1.5 Goals -> Over, 1.5
    """

    selection = str(selection)

    match = re.search(
        r"(Under|Over)\s+([0-9.]+)",
        selection,
        re.IGNORECASE
    )

    if not match:
        return None, None

    direction = match.group(1).title()
    point = float(match.group(2))

    return direction, point


def parse_angle_selection(selection):
    """
    Converts our internal market angle selection into something that can be
    matched against The Odds API.

    Examples:
    - Under 3.5 Goals -> totals / Under / 3.5
    - Over 1.5 Goals -> totals / Over / 1.5
    - Switzerland +1.5 -> spreads / Switzerland / +1.5
    - BTTS No -> btts / No
    """

    selection = str(selection)

    total_match = re.search(
        r"(Under|Over)\s+([0-9.]+)\s+Goals",
        selection,
        re.IGNORECASE
    )

    if total_match:
        return {
            "target_market_key": "totals",
            "target_selection": total_match.group(1).title(),
            "target_point": float(total_match.group(2)),
        }

    spread_match = re.search(r"(.+?)\s+([+-][0-9.]+)", selection)

    if spread_match:
        return {
            "target_market_key": "spreads",
            "target_selection": spread_match.group(1).strip(),
            "target_point": float(spread_match.group(2)),
        }

    if "BTTS Yes" in selection:
        return {
            "target_market_key": "btts",
            "target_selection": "Yes",
            "target_point": None,
        }

    if "BTTS No" in selection:
        return {
            "target_market_key": "btts",
            "target_selection": "No",
            "target_point": None,
        }

    return {
        "target_market_key": None,
        "target_selection": None,
        "target_point": None,
    }


def points_match(angle_point, odds_point):
    """
    Exact point match.
    """

    if angle_point is None or pd.isna(angle_point):
        return True

    if odds_point is None or pd.isna(odds_point):
        return False

    try:
        angle_point = float(angle_point)
        odds_point = float(odds_point)
    except ValueError:
        return False

    return abs(angle_point - odds_point) < 0.001


def selections_match(angle_selection, odds_selection):
    """
    Checks if the selection name matches.
    For totals, this is Over/Under.
    For spreads, this is the team name.
    """

    angle_selection = normalize_team_name(angle_selection)
    odds_selection = normalize_team_name(odds_selection)

    return angle_selection == odds_selection


def summarize_candidate_odds(
    candidate_odds,
    target_market_key,
    target_selection,
    matched_point,
    exact_line_match
):
    """
    Builds the odds summary from matching bookmaker rows.
    """

    decimal_odds = candidate_odds["decimal_odds"].astype(float)

    best_row = candidate_odds.sort_values(
        by="decimal_odds",
        ascending=False
    ).iloc[0]

    return {
        "odds_found": True,
        "avg_decimal_odds": round(decimal_odds.mean(), 3),
        "best_decimal_odds": round(decimal_odds.max(), 3),
        "bookmakers_count": int(candidate_odds["bookmaker_key"].nunique()),
        "best_bookmaker": best_row["bookmaker_title"],
        "matched_market_key": target_market_key,
        "matched_selection": target_selection,
        "matched_point": matched_point,
        "exact_line_match": exact_line_match,
    }


def find_matching_odds(angle, odds):
    """
    Matches one market angle with sportsbook odds.

    Logic:
    1. Match same fixture.
    2. Match same market type.
    3. Match same selection.
    4. Prefer exact line.
    5. If exact line does not exist, use closest available line.
    """

    parsed = parse_angle_selection(angle["selection"])

    target_market_key = parsed["target_market_key"]
    target_selection = parsed["target_selection"]
    target_point = parsed["target_point"]

    if target_market_key is None:
        return None

    match_key = normalize_match_key(angle["home_team"], angle["away_team"])

    candidate_odds = odds[
        (odds["match_key"] == match_key)
        & (odds["market_key"] == target_market_key)
    ].copy()

    if candidate_odds.empty:
        return None

    candidate_odds = candidate_odds[
        candidate_odds["selection"].apply(
            lambda value: selections_match(target_selection, value)
        )
    ].copy()

    if candidate_odds.empty:
        return None

    # For markets with no point, such as BTTS if available.
    if target_point is None or pd.isna(target_point):
        return summarize_candidate_odds(
            candidate_odds=candidate_odds,
            target_market_key=target_market_key,
            target_selection=target_selection,
            matched_point=None,
            exact_line_match=True,
        )

    # First try exact line.
    exact_candidate_odds = candidate_odds[
        candidate_odds["point"].apply(
            lambda value: points_match(target_point, value)
        )
    ].copy()

    if not exact_candidate_odds.empty:
        return summarize_candidate_odds(
            candidate_odds=exact_candidate_odds,
            target_market_key=target_market_key,
            target_selection=target_selection,
            matched_point=target_point,
            exact_line_match=True,
        )

    # Fallback: use closest available line.
    # Example:
    # model angle asks Under 3.5,
    # sportsbook only has Under 2.5.
    candidate_odds = candidate_odds.dropna(subset=["point"]).copy()

    if candidate_odds.empty:
        return None

    candidate_odds["point"] = candidate_odds["point"].astype(float)

    candidate_odds["point_distance"] = candidate_odds["point"].apply(
        lambda value: abs(value - float(target_point))
    )

    closest_point = candidate_odds.sort_values(
        by=["point_distance", "decimal_odds"],
        ascending=[True, False]
    ).iloc[0]["point"]

    closest_candidate_odds = candidate_odds[
        candidate_odds["point"] == float(closest_point)
    ].copy()

    if closest_candidate_odds.empty:
        return None

    return summarize_candidate_odds(
        candidate_odds=closest_candidate_odds,
        target_market_key=target_market_key,
        target_selection=target_selection,
        matched_point=closest_point,
        exact_line_match=False,
    )


def get_line_adjustment(row):
    """
    Adjusts confidence when the exact sportsbook line does not match the model angle.

    Example:
    Model angle: Under 3.5 Goals
    Sportsbook line: Under 2.5

    Under 2.5 is harder than Under 3.5, so confidence should be reduced.
    """

    original_confidence = float(row["confidence_score"])

    if not bool(row["odds_found"]):
        return {
            "adjusted_confidence_score": round(original_confidence, 3),
            "adjusted_profile": profile_from_confidence(original_confidence),
            "line_note": "No sportsbook odds found for this market yet.",
        }

    if bool(row["exact_line_match"]):
        return {
            "adjusted_confidence_score": round(original_confidence, 3),
            "adjusted_profile": profile_from_confidence(original_confidence),
            "line_note": "Exact sportsbook line matched the model angle.",
        }

    model_direction, model_point = extract_model_line(row["selection"])

    try:
        matched_point = float(row["matched_point"])
    except (TypeError, ValueError):
        matched_point = None

    if model_direction is None or model_point is None or matched_point is None:
        adjusted = max(0, original_confidence - 0.10)

        return {
            "adjusted_confidence_score": round(adjusted, 3),
            "adjusted_profile": profile_from_confidence(adjusted),
            "line_note": "Closest available line differs from the model angle.",
        }

    # Under 3.5 -> Under 2.5 is harder.
    if model_direction == "Under" and matched_point < model_point:
        adjusted = max(0, original_confidence - 0.12)

        return {
            "adjusted_confidence_score": round(adjusted, 3),
            "adjusted_profile": profile_from_confidence(adjusted),
            "line_note": "Closest available line is more aggressive than the model angle.",
        }

    # Over 1.5 -> Over 2.0 / Over 2.5 is harder.
    if model_direction == "Over" and matched_point > model_point:
        adjusted = max(0, original_confidence - 0.12)

        return {
            "adjusted_confidence_score": round(adjusted, 3),
            "adjusted_profile": profile_from_confidence(adjusted),
            "line_note": "Closest available line is more aggressive than the model angle.",
        }

    # If the available line is easier than the model angle, apply smaller penalty.
    adjusted = max(0, original_confidence - 0.04)

    return {
        "adjusted_confidence_score": round(adjusted, 3),
        "adjusted_profile": profile_from_confidence(adjusted),
        "line_note": "Closest available line differs from the model angle.",
    }


def match_angles_with_odds():
    if not os.path.exists(MARKET_ANGLES_PATH):
        raise FileNotFoundError(
            f"Missing {MARKET_ANGLES_PATH}. Run python src/market_angle_engine.py first."
        )

    if not os.path.exists(ODDS_MARKETS_PATH):
        raise FileNotFoundError(
            f"Missing {ODDS_MARKETS_PATH}. Run python data_sources/fetch_market_odds.py first."
        )

    angles = pd.read_csv(MARKET_ANGLES_PATH)
    odds = pd.read_csv(ODDS_MARKETS_PATH)

    odds["match_key"] = odds.apply(
        lambda row: normalize_match_key(row["home_team"], row["away_team"]),
        axis=1
    )

    matched_rows = []

    for _, angle in angles.iterrows():
        row = angle.to_dict()

        match_result = find_matching_odds(angle, odds)

        if match_result is None:
            row.update({
                "odds_found": False,
                "avg_decimal_odds": None,
                "best_decimal_odds": None,
                "bookmakers_count": 0,
                "best_bookmaker": None,
                "matched_market_key": None,
                "matched_selection": None,
                "matched_point": None,
                "exact_line_match": False,
            })
        else:
            row.update(match_result)

        matched_rows.append(row)

    matched_df = pd.DataFrame(matched_rows)

    if not matched_df.empty:
        adjustments = matched_df.apply(get_line_adjustment, axis=1)
        adjustments_df = pd.DataFrame(adjustments.tolist())

        matched_df = pd.concat(
            [
                matched_df.reset_index(drop=True),
                adjustments_df.reset_index(drop=True)
            ],
            axis=1
        )

        matched_df = matched_df.sort_values(
            by=["odds_found", "market_priority", "adjusted_confidence_score"],
            ascending=[False, True, False]
        ).reset_index(drop=True)

    os.makedirs(PROCESSED_DIR, exist_ok=True)
    matched_df.to_csv(OUTPUT_CSV_PATH, index=False)

    return matched_df


def generate_report(matched_df):
    lines = []

    lines.append("# World Cup Daily Betting Intelligence With Odds")
    lines.append("")
    lines.append("## Purpose")
    lines.append("")
    lines.append(
        "This report combines statistical market angles with available sportsbook odds."
    )
    lines.append("")
    lines.append(
        "These are not guaranteed bets. They are data-backed markets to watch."
    )
    lines.append("")
    lines.append(
        "If the exact model line is not available, the report may show the closest available sportsbook line."
    )
    lines.append("")

    if matched_df.empty:
        lines.append("No market angles available.")
    else:
        top_angles = matched_df.head(10)

        lines.append("## Top Markets To Watch")
        lines.append("")

        for i, (_, row) in enumerate(top_angles.iterrows(), start=1):
            lines.append(f"### {i}. {row['match']}")
            lines.append("")
            lines.append(f"Market: **{row['market_type']}**")
            lines.append(f"Model angle: **{row['selection']}**")
            lines.append(f"Original profile: **{row['risk_label']}**")
            lines.append(f"Original confidence: **{row['confidence_score']:.1%}**")
            lines.append(f"Adjusted profile: **{row['adjusted_profile']}**")
            lines.append(f"Adjusted confidence: **{row['adjusted_confidence_score']:.1%}**")
            lines.append("")

            if bool(row["odds_found"]):
                lines.append(f"Available market: **{row['matched_market_key']}**")

                if pd.isna(row["matched_point"]):
                    lines.append(f"Matched line: **{row['matched_selection']}**")
                else:
                    lines.append(
                        f"Matched line: **{row['matched_selection']} {row['matched_point']}**"
                    )

                lines.append(f"Exact line match: **{bool(row['exact_line_match'])}**")
                lines.append(f"Line note: **{row['line_note']}**")
                lines.append(f"Average odds: **{row['avg_decimal_odds']}**")
                lines.append(f"Best odds: **{row['best_decimal_odds']}**")
                lines.append(f"Best bookmaker: **{row['best_bookmaker']}**")
                lines.append(f"Bookmakers found: **{row['bookmakers_count']}**")
            else:
                lines.append("Odds: **Not found for this market yet**")
                lines.append(f"Line note: **{row['line_note']}**")

            lines.append("")
            lines.append(f"Reason: {row['reason']}")
            lines.append("")

    lines.append("## Responsible Betting Note")
    lines.append("")
    lines.append(
        "Betting involves risk. This report is educational and informational only. "
        "No model can guarantee outcomes. Only bet what you can afford to lose."
    )

    os.makedirs(REPORTS_DIR, exist_ok=True)

    with open(OUTPUT_REPORT_PATH, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))

    print(f"Matched market odds saved to: {OUTPUT_CSV_PATH}")
    print(f"Report generated: {OUTPUT_REPORT_PATH}")


def main():
    matched_df = match_angles_with_odds()
    generate_report(matched_df)

    print("")
    print("Top matched angles:")

    if matched_df.empty:
        print("No matched angles.")
    else:
        columns_to_show = [
            "match",
            "market_type",
            "selection",
            "risk_label",
            "confidence_score",
            "adjusted_confidence_score",
            "adjusted_profile",
            "line_note",
            "odds_found",
            "matched_market_key",
            "matched_selection",
            "matched_point",
            "exact_line_match",
            "avg_decimal_odds",
            "best_decimal_odds",
            "best_bookmaker",
        ]

        existing_columns = [
            column for column in columns_to_show if column in matched_df.columns
        ]

        print(matched_df.head(10)[existing_columns].to_string(index=False))


if __name__ == "__main__":
    main()