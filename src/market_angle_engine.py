import os
import pandas as pd


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

FIXTURES_PATH = os.path.join(RAW_DIR, "api_football_fixtures.csv")
RECENT_STATS_PATH = os.path.join(RAW_DIR, "api_football_team_recent_stats.csv")
H2H_STATS_PATH = os.path.join(RAW_DIR, "api_football_h2h_stats.csv")

MARKET_ANGLES_OUTPUT_PATH = os.path.join(PROCESSED_DIR, "market_angles.csv")
REPORT_OUTPUT_PATH = os.path.join(REPORTS_DIR, "daily_betting_intelligence.md")


def risk_from_confidence(confidence_score):
    if confidence_score >= 0.75:
        return "CONSERVATIVE"
    if confidence_score >= 0.60:
        return "BALANCED"
    return "AGGRESSIVE"


def clamp(value, min_value=0, max_value=1):
    return max(min_value, min(value, max_value))


def get_team_stats(recent_stats, team_id):
    row = recent_stats[recent_stats["team_id"] == team_id]

    if row.empty:
        return None

    return row.iloc[0].to_dict()


def get_h2h_stats(h2h_stats, home_team_id, away_team_id):
    row = h2h_stats[
        (h2h_stats["home_team_id"] == home_team_id)
        & (h2h_stats["away_team_id"] == away_team_id)
    ]

    if row.empty:
        return None

    return row.iloc[0].to_dict()


def get_market_priority(market_type, selection):
    """
    Lower number = better commercial priority.
    """

    if market_type == "Total Goals" and "Under 3.5" in selection:
        return 1

    if market_type == "Total Goals" and "Over 1.5" in selection:
        return 2

    if market_type == "Handicap / Spread":
        return 3

    if market_type == "Both Teams To Score":
        return 4

    if market_type == "Total Goals" and "Over 2.5" in selection:
        return 5

    if market_type == "Team Total" and "Over 1.5" in selection:
        return 6

    if market_type == "Team Total" and "Over 0.5" in selection:
        return 9

    return 10


def add_angle(angles, fixture, market_type, selection, confidence_score, reason):
    angles.append({
        "date": fixture["date"],
        "match": f"{fixture['home_team']} vs {fixture['away_team']}",
        "home_team": fixture["home_team"],
        "away_team": fixture["away_team"],
        "market_type": market_type,
        "selection": selection,
        "confidence_score": round(confidence_score, 3),
        "risk_label": risk_from_confidence(confidence_score),
        "market_priority": get_market_priority(market_type, selection),
        "reason": reason,
    })


def build_market_angles():
    fixtures = pd.read_csv(FIXTURES_PATH)
    recent_stats = pd.read_csv(RECENT_STATS_PATH)
    h2h_stats = pd.read_csv(H2H_STATS_PATH)

    angles = []

    # Use only fixtures that were processed in the H2H file.
    # This prevents the engine from generating angles for later matches
    # involving the same teams before we fetch their specific context.
    allowed_matches = set(
    zip(
        h2h_stats["home_team_id"].astype(int),
        h2h_stats["away_team_id"].astype(int)
    )
   )

    fixtures = fixtures[
    fixtures.apply(
        lambda row: (
            int(row["home_team_id"]),
            int(row["away_team_id"])
        ) in allowed_matches,
        axis=1
    )
        ].copy()

    for _, fixture in fixtures.iterrows():
        home_team_id = int(fixture["home_team_id"])
        away_team_id = int(fixture["away_team_id"])

        home = get_team_stats(recent_stats, home_team_id)
        away = get_team_stats(recent_stats, away_team_id)
        h2h = get_h2h_stats(h2h_stats, home_team_id, away_team_id)

        if home is None or away is None:
            continue

        home_attack = float(home["avg_goals_for"])
        home_defense = float(home["avg_goals_against"])
        away_attack = float(away["avg_goals_for"])
        away_defense = float(away["avg_goals_against"])

        projected_home_goals = round((home_attack + away_defense) / 2, 2)
        projected_away_goals = round((away_attack + home_defense) / 2, 2)
        projected_total_goals = round(projected_home_goals + projected_away_goals, 2)
        projected_goal_diff = round(projected_home_goals - projected_away_goals, 2)

        home_clean_sheet_rate = float(home["clean_sheet_rate"])
        away_clean_sheet_rate = float(away["clean_sheet_rate"])

        home_btts_rate = float(home["btts_rate"])
        away_btts_rate = float(away["btts_rate"])

        home_over_2_5_rate = float(home["over_2_5_rate"])
        away_over_2_5_rate = float(away["over_2_5_rate"])

        home_failed_to_score = float(home["failed_to_score_rate"])
        away_failed_to_score = float(away["failed_to_score_rate"])

        combined_over_2_5 = (home_over_2_5_rate + away_over_2_5_rate) / 2
        combined_btts = (home_btts_rate + away_btts_rate) / 2

        # 1. Under 3.5 goals
        if projected_total_goals <= 2.7:
            confidence = clamp(0.65 + (2.7 - projected_total_goals) * 0.10)
            add_angle(
                angles,
                fixture,
                "Total Goals",
                "Under 3.5 Goals",
                confidence,
                f"Projected total goals: {projected_total_goals}. Recent goal profile suggests controlled scoring."
            )

        # 2. Over 1.5 goals
        if projected_total_goals >= 2.0:
            confidence = clamp(0.60 + (projected_total_goals - 2.0) * 0.12)
            add_angle(
                angles,
                fixture,
                "Total Goals",
                "Over 1.5 Goals",
                confidence,
                f"Projected total goals: {projected_total_goals}. Both teams combine for enough attacking volume."
            )

        # 3. Over 2.5 goals
        if projected_total_goals >= 2.65 and combined_over_2_5 >= 0.50:
            confidence = clamp(0.58 + (projected_total_goals - 2.65) * 0.10 + combined_over_2_5 * 0.10)
            add_angle(
                angles,
                fixture,
                "Total Goals",
                "Over 2.5 Goals",
                confidence,
                f"Projected total goals: {projected_total_goals}. Combined Over 2.5 recent rate: {combined_over_2_5:.0%}."
            )

        # 4. BTTS Yes
        if combined_btts >= 0.60 and home_failed_to_score <= 0.30 and away_failed_to_score <= 0.30:
            confidence = clamp(0.55 + combined_btts * 0.20)
            add_angle(
                angles,
                fixture,
                "Both Teams To Score",
                "BTTS Yes",
                confidence,
                f"Combined BTTS rate: {combined_btts:.0%}. Both teams have reasonable scoring consistency."
            )

        # 5. BTTS No
        if home_clean_sheet_rate >= 0.50 or away_clean_sheet_rate >= 0.50 or home_failed_to_score >= 0.40 or away_failed_to_score >= 0.40:
            confidence = clamp(0.58 + max(home_clean_sheet_rate, away_clean_sheet_rate) * 0.18)
            add_angle(
                angles,
                fixture,
                "Both Teams To Score",
                "BTTS No",
                confidence,
                f"Clean sheet / failed-to-score profile supports BTTS No. Home CS: {home_clean_sheet_rate:.0%}, Away CS: {away_clean_sheet_rate:.0%}."
            )

        # 6. Home -0.5 handicap / moneyline style
        if projected_goal_diff >= 0.55:
            confidence = clamp(0.58 + projected_goal_diff * 0.12)
            add_angle(
                angles,
                fixture,
                "Handicap / Spread",
                f"{fixture['home_team']} -0.5",
                confidence,
                f"Projected goal edge: {projected_goal_diff}. Home team profiles stronger in expected goals."
            )

        # 7. Away +1.5 handicap
        if projected_goal_diff <= 0.80:
            confidence = clamp(0.60 + (0.80 - projected_goal_diff) * 0.08)
            add_angle(
                angles,
                fixture,
                "Handicap / Spread",
                f"{fixture['away_team']} +1.5",
                confidence,
                f"Projected margin is not large. Goal difference estimate: {projected_goal_diff}."
            )

        # 8. Home team total over 0.5
        if projected_home_goals >= 1.20:
            confidence = clamp(0.60 + projected_home_goals * 0.08)
            add_angle(
                angles,
                fixture,
                "Team Total",
                f"{fixture['home_team']} Over 0.5 Team Goals",
                confidence,
                f"Projected home goals: {projected_home_goals}."
            )

        # 9. Away team total over 0.5
        if projected_away_goals >= 1.20:
            confidence = clamp(0.60 + projected_away_goals * 0.08)
            add_angle(
                angles,
                fixture,
                "Team Total",
                f"{fixture['away_team']} Over 0.5 Team Goals",
                confidence,
                f"Projected away goals: {projected_away_goals}."
            )

        # 10. Home team total over 1.5
        if projected_home_goals >= 1.55:
            confidence = clamp(0.55 + projected_home_goals * 0.08)
            add_angle(
                angles,
                fixture,
                "Team Total",
                f"{fixture['home_team']} Over 1.5 Team Goals",
                confidence,
                f"Projected home goals: {projected_home_goals}."
            )

        # 11. Away team total over 1.5
        if projected_away_goals >= 1.55:
            confidence = clamp(0.55 + projected_away_goals * 0.08)
            add_angle(
                angles,
                fixture,
                "Team Total",
                f"{fixture['away_team']} Over 1.5 Team Goals",
                confidence,
                f"Projected away goals: {projected_away_goals}."
            )

    angles_df = pd.DataFrame(angles)

    if not angles_df.empty:
      angles_df = angles_df.sort_values(
    by=["match", "market_priority", "confidence_score"],
    ascending=[True, True, False]
    )

    angles_df = (
        angles_df
        .groupby("match")
        .head(1)
        .reset_index(drop=True)
    )

    angles_df = angles_df.sort_values(
    by=["market_priority", "confidence_score"],
    ascending=[True, False]
    ).reset_index(drop=True)

    os.makedirs(PROCESSED_DIR, exist_ok=True)
    angles_df.to_csv(MARKET_ANGLES_OUTPUT_PATH, index=False)

    return angles_df


def generate_daily_betting_intelligence(angles_df):
    lines = []

    lines.append("# World Cup Daily Betting Intelligence")
    lines.append("")
    lines.append("## Purpose")
    lines.append("")
    lines.append(
        "This report ranks data-backed betting angles using recent team form, goals profile, and head-to-head context."
    )
    lines.append("")
    lines.append(
        "These are not guaranteed bets. They are market angles to watch based on statistical signals."
    )
    lines.append("")
    lines.append(
    "The goal is to identify markets where recent form, goals profile, and matchup context point in the same direction."
    )
    lines.append("")

    if angles_df.empty:
        lines.append("No market angles generated today.")
    else:
        top_angles = angles_df.head(10)

        lines.append("## Top 10 Markets To Watch")
        lines.append("")

        for i, (_, row) in enumerate(top_angles.iterrows(), start=1):
            lines.append(f"### {i}. {row['match']}")
            lines.append("")
            lines.append(f"Market: **{row['market_type']}**")
            lines.append(f"Selection: **{row['selection']}**")
            lines.append(f"Profile: **{row['risk_label']}**")
            lines.append(f"Confidence: **{row['confidence_score']:.1%}**")
            lines.append("")
            lines.append(f"Reason: {row['reason']}")
            lines.append("")

    lines.append("## Responsible Betting Note")
    lines.append("")
    lines.append(
        "Betting involves risk. This report is educational and informational only. No model can guarantee outcomes."
    )

    os.makedirs(REPORTS_DIR, exist_ok=True)

    with open(REPORT_OUTPUT_PATH, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))

    print(f"Market angles saved to: {MARKET_ANGLES_OUTPUT_PATH}")
    print(f"Daily betting intelligence report generated: {REPORT_OUTPUT_PATH}")


def main():
    angles_df = build_market_angles()
    generate_daily_betting_intelligence(angles_df)

    print("")
    print("Top angles:")
    if angles_df.empty:
        print("No angles generated.")
    else:
        print(angles_df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()