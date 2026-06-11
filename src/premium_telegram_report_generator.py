import os
import pandas as pd

from probability_engine import (
    build_probability_summary,
    get_best_statistical_angle,
    get_probability_profile,
    format_probability,
)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

ANGLES_INPUT_PATH = os.path.join(PROCESSED_DIR, "market_angles_with_odds.csv")
RECENT_STATS_PATH = os.path.join(RAW_DIR, "api_football_team_recent_stats.csv")
H2H_STATS_PATH = os.path.join(RAW_DIR, "api_football_h2h_stats.csv")

OUTPUT_PATH = os.path.join(REPORTS_DIR, "telegram_premium_report.md")


def format_record(row):
    return f"{int(row['wins'])}W-{int(row['draws'])}D-{int(row['losses'])}L"


def format_percent(value):
    try:
        return f"{float(value):.0%}"
    except Exception:
        return "N/A"


def find_team_stats(recent_stats, team_name):
    row = recent_stats[recent_stats["team"] == team_name]

    if row.empty:
        return None

    return row.iloc[0]


def find_h2h_stats(h2h_stats, home_team, away_team):
    row = h2h_stats[
        (h2h_stats["home_team"] == home_team)
        & (h2h_stats["away_team"] == away_team)
    ]

    if row.empty:
        return None

    return row.iloc[0]


def get_profile_text(profile):
    if profile == "CONSERVATIVE":
        return "Conservative watch"
    if profile == "BALANCED":
        return "Balanced watch"
    if profile == "AGGRESSIVE":
        return "Caution watch"
    return "Watch"


def add_team_block(lines, team_name, stats):
    lines.append(f"{team_name}: {format_record(stats)}")
    lines.append(
        f"Goals: {int(stats['goals_for'])} scored / {int(stats['goals_against'])} conceded"
    )
    lines.append(
        f"Average: {float(stats['avg_goals_for']):.2f} scored / "
        f"{float(stats['avg_goals_against']):.2f} conceded"
    )
    lines.append(f"Games over 2.5 goals: {format_percent(stats['over_2_5_rate'])}")
    lines.append(f"Games where both teams scored: {format_percent(stats['btts_rate'])}")
    lines.append(f"Clean sheet rate: {format_percent(stats['clean_sheet_rate'])}")
    lines.append(f"Failed to score rate: {format_percent(stats['failed_to_score_rate'])}")


def add_h2h_block(lines, h2h, home_team, away_team):
    lines.append("🤝 Previous meetings between both teams")

    if h2h is None or int(h2h["h2h_matches_found"]) == 0:
        lines.append("Not enough recent direct-meeting data found.")
        return

    lines.append(f"Games found: {int(h2h['h2h_matches_found'])}")
    lines.append(
        f"Results: {home_team} wins {int(h2h['home_team_h2h_wins'])} / "
        f"{away_team} wins {int(h2h['away_team_h2h_wins'])} / "
        f"Draws {int(h2h['h2h_draws'])}"
    )
    lines.append(f"Average goals: {float(h2h['h2h_avg_goals']):.2f}")
    lines.append(f"Games over 2.5 goals: {format_percent(h2h['h2h_over_2_5_rate'])}")
    lines.append(
        f"Games where both teams scored: {format_percent(h2h['h2h_btts_rate'])}"
    )


def add_probability_block(lines, home_team, away_team, home_stats, away_stats):
    probabilities = build_probability_summary(home_stats, away_stats)

    best_market, best_probability = get_best_statistical_angle(probabilities)
    profile = get_probability_profile(best_probability)

    lines.append("🧠 Most likely by stats")
    lines.append(f"Most likely market: {best_market}")
    lines.append(f"Estimated probability: {format_probability(best_probability)}")
    lines.append(f"Profile: {profile}")
    lines.append("")

    lines.append("Projected goals:")
    lines.append(f"{home_team}: {probabilities['home_xg']:.2f}")
    lines.append(f"{away_team}: {probabilities['away_xg']:.2f}")
    lines.append(f"Projected total goals: {probabilities['expected_total_goals']:.2f}")
    lines.append("")

    lines.append("Full probability table:")
    lines.append(f"Under 2.5 goals: {format_probability(probabilities['under_2_5'])}")
    lines.append(f"Over 2.5 goals: {format_probability(probabilities['over_2_5'])}")
    lines.append(f"Under 3.5 goals: {format_probability(probabilities['under_3_5'])}")
    lines.append(f"Over 1.5 goals: {format_probability(probabilities['over_1_5'])}")
    lines.append(f"Both teams score - Yes: {format_probability(probabilities['btts_yes'])}")
    lines.append(f"Both teams score - No: {format_probability(probabilities['btts_no'])}")
    lines.append(f"{home_team} over 0.5 goals: {format_probability(probabilities['home_over_0_5'])}")
    lines.append(f"{away_team} over 0.5 goals: {format_probability(probabilities['away_over_0_5'])}")
    lines.append(f"{home_team} over 1.5 goals: {format_probability(probabilities['home_over_1_5'])}")
    lines.append(f"{away_team} over 1.5 goals: {format_probability(probabilities['away_over_1_5'])}")
    lines.append("")


def build_market_text(row):
    matched_selection = str(row["matched_selection"])
    matched_point = row["matched_point"]

    if pd.isna(matched_point):
        available_line = matched_selection
    else:
        available_line = f"{matched_selection} {matched_point}"

    lines = []
    lines.append("🎯 Available market watch")
    lines.append(f"Model angle: {row['selection']}")
    lines.append(f"Available betting line: {available_line}")
    lines.append(f"Available odds around: {row['best_decimal_odds']}")
    lines.append(f"Market profile: {get_profile_text(row['adjusted_profile'])}")
    lines.append(f"Confidence on this available line: {float(row['adjusted_confidence_score']):.1%}")
    lines.append(f"Line note: {row['line_note']}")
    lines.append(
    "Interpretation: The safest statistical direction and the available betting line may not be identical. "
    "When they differ, treat the available line with extra caution."
)

    return lines


def build_premium_reason(row, home_team, away_team, home_stats, away_stats):
    selection = str(row["selection"])

    home_gf = float(home_stats["avg_goals_for"])
    home_ga = float(home_stats["avg_goals_against"])
    away_gf = float(away_stats["avg_goals_for"])
    away_ga = float(away_stats["avg_goals_against"])

    if "Under" in selection:
        return (
            f"The main signal comes from the defensive side of the matchup. "
            f"{home_team} are averaging {home_ga:.2f} goals conceded recently, "
            f"while {away_team} are averaging {away_ga:.2f}. "
            f"The safer statistical direction is lower goals, but the available betting line may be stricter, "
            f"so this should be treated as a watchlist market rather than a guaranteed pick."
        )

    if "Over" in selection:
        return (
            f"The goals angle comes from recent attacking and conceding trends. "
            f"{home_team} are averaging {home_gf:.2f} goals scored recently, "
            f"while {away_team} are averaging {away_gf:.2f}. "
            f"The model sees enough attacking profile for a goals watch, but risk depends on the available line."
        )

    if "BTTS" in selection:
        return (
            f"This angle comes from both teams' scoring and conceding patterns. "
            f"The model is watching whether both sides can get on the scoreboard."
        )

    return str(row["reason"])


def generate_premium_telegram_report():
    if not os.path.exists(ANGLES_INPUT_PATH):
        raise FileNotFoundError(
            f"Missing {ANGLES_INPUT_PATH}. Run python src/market_odds_matcher.py first."
        )

    if not os.path.exists(RECENT_STATS_PATH):
        raise FileNotFoundError(
            f"Missing {RECENT_STATS_PATH}. Run python data_sources/fetch_api_football_context.py first."
        )

    if not os.path.exists(H2H_STATS_PATH):
        raise FileNotFoundError(
            f"Missing {H2H_STATS_PATH}. Run python data_sources/fetch_api_football_context.py first."
        )

    angles = pd.read_csv(ANGLES_INPUT_PATH)
    recent_stats = pd.read_csv(RECENT_STATS_PATH)
    h2h_stats = pd.read_csv(H2H_STATS_PATH)

    angles = angles[angles["odds_found"] == True].copy()

    lines = []
    lines.append("⚽ World Cup Premium Intelligence")
    lines.append("")
    lines.append("Full daily betting intelligence report.")
    lines.append("Based on recent form, goal trends, previous meetings, model probabilities and betting lines.")
    lines.append("")
    lines.append("No guaranteed bets. Educational only. Bet responsibly.")
    lines.append("")

    if angles.empty:
        lines.append("No premium market watchlist available today.")
    else:
        angles = angles.sort_values(
            by=["adjusted_confidence_score"],
            ascending=False
        )

        for i, (_, row) in enumerate(angles.iterrows(), start=1):
            home_team = row["home_team"]
            away_team = row["away_team"]

            home_stats = find_team_stats(recent_stats, home_team)
            away_stats = find_team_stats(recent_stats, away_team)
            h2h = find_h2h_stats(h2h_stats, home_team, away_team)

            if home_stats is None or away_stats is None:
                continue

            lines.append(f"{i}) {home_team} vs {away_team}")
            lines.append("")

            lines.append("📊 Last 10 matches")
            add_team_block(lines, home_team, home_stats)
            lines.append("")
            add_team_block(lines, away_team, away_stats)
            lines.append("")

            add_h2h_block(lines, h2h, home_team, away_team)
            lines.append("")

            add_probability_block(lines, home_team, away_team, home_stats, away_stats)

            market_lines = build_market_text(row)
            lines.extend(market_lines)
            lines.append("")

            lines.append("🧠 Premium read")
            lines.append(build_premium_reason(row, home_team, away_team, home_stats, away_stats))
            lines.append("")
            lines.append("━━━━━━━━━━━━━━")
            lines.append("")

    lines.append("Premium beta note:")
    lines.append("This product is still improving. Future updates may include lineup alerts, player scoring watch, corners and cards once reliable data is connected.")
    lines.append("")
    lines.append("No model can guarantee outcomes.")

    os.makedirs(REPORTS_DIR, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))

    print(f"Premium Telegram report generated: {OUTPUT_PATH}")


def main():
    generate_premium_telegram_report()


if __name__ == "__main__":
    main()