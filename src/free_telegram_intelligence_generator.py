import os
import pandas as pd
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from probability_engine import (
    build_probability_summary,
    get_best_statistical_angle,
    get_probability_profile,
    format_probability,
)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

REPORT_TIMEZONE = os.getenv("REPORT_TIMEZONE", "America/Toronto")

RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

ANGLES_INPUT_PATH = os.path.join(PROCESSED_DIR, "market_angles_with_odds.csv")
RECENT_STATS_PATH = os.path.join(RAW_DIR, "api_football_team_recent_stats.csv")
H2H_STATS_PATH = os.path.join(RAW_DIR, "api_football_h2h_stats.csv")
FIXTURES_PATH = os.path.join(RAW_DIR, "api_football_fixtures.csv")

OUTPUT_PATH = os.path.join(REPORTS_DIR, "telegram_free_intelligence.md")


def format_record(row):
    return f"{int(row['wins'])}W-{int(row['draws'])}D-{int(row['losses'])}L"


def format_percent(value):
    try:
        return f"{float(value):.0%}"
    except Exception:
        return "N/A"


def get_profile_text(profile):
    if profile == "CONSERVATIVE":
        return "Safer watch"
    if profile == "BALANCED":
        return "Balanced watch"
    if profile == "AGGRESSIVE":
        return "Caution watch"
    return "Watch"


def get_simple_market_text(row):
    """
    Converts technical model angle into simple betting language.
    """

    selection = str(row["selection"])
    matched_selection = str(row["matched_selection"])
    matched_point = row["matched_point"]

    if pd.isna(matched_point):
        available_line = matched_selection
    else:
        available_line = f"{matched_selection} {matched_point}"

    if "Under" in selection:
        return f"Goals market: Watch {available_line} goals"

    if "Over" in selection:
        return f"Goals market: Watch {available_line} goals"

    if "BTTS Yes" in selection:
        return "Both Teams To Score: Watch YES"

    if "BTTS No" in selection:
        return "Both Teams To Score: Watch NO"

    if "+" in selection or "-" in selection:
        return f"Handicap/Spread: Watch {selection}"

    return f"Market to watch: {selection}"


def get_plain_english_reason(row, home_stats, away_stats, h2h_stats):
    """
    Writes a simple explanation for normal users.
    """

    selection = str(row["selection"])
    line_note = str(row["line_note"])

    home_team = row["home_team"]
    away_team = row["away_team"]

    home_ga = float(home_stats["avg_goals_against"])
    away_ga = float(away_stats["avg_goals_against"])

    home_gf = float(home_stats["avg_goals_for"])
    away_gf = float(away_stats["avg_goals_for"])

    projected_reason = str(row["reason"])

    if "Under" in selection:
        return (
            f"The model leans toward a lower-scoring game. "
            f"{home_team} concede about {home_ga:.2f} goals per match recently, "
            f"while {away_team} concede about {away_ga:.2f}. "
            f"The available sportsbook line is stricter than the original model angle, "
            f"so this is a watchlist spot, not a lock."
        )

    if "Over" in selection:
        return (
            f"The model sees enough attacking activity for a goals angle. "
            f"{home_team} average {home_gf:.2f} goals scored recently, "
            f"while {away_team} average {away_gf:.2f}. "
            f"The available line is more demanding than the original model angle, "
            f"so risk is higher."
        )

    if "BTTS" in selection:
        return (
            f"This angle comes from recent scoring and conceding trends. "
            f"{home_team} and {away_team} both show enough goal activity to monitor this market."
        )

    if "+" in selection or "-" in selection:
        return (
            f"This handicap angle is based on the projected margin between both teams. "
            f"The model does not expect the gap to be as wide as the market may suggest."
        )

    return projected_reason


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


def add_team_block(lines, label, stats):
    lines.append(f"{label}")
    lines.append(f"Record: {format_record(stats)}")
    lines.append(
        f"Goals: {int(stats['goals_for'])} scored / {int(stats['goals_against'])} conceded"
    )
    lines.append(
        f"Avg goals: {float(stats['avg_goals_for']):.2f} scored / "
        f"{float(stats['avg_goals_against']):.2f} conceded"
    )
    lines.append(f"Over 2.5 trend: {format_percent(stats['over_2_5_rate'])}")
    lines.append(f"Both teams scored trend: {format_percent(stats['btts_rate'])}")

    if "clean_sheet_rate" in stats:
        lines.append(f"Clean sheet rate: {format_percent(stats['clean_sheet_rate'])}")

    if "failed_to_score_rate" in stats:
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
    lines.append(
        f"Games over 2.5 goals: {format_percent(h2h['h2h_over_2_5_rate'])}"
    )
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

    lines.append("Other probabilities:")
    lines.append(f"Under 2.5 goals: {format_probability(probabilities['under_2_5'])}")
    lines.append(f"Over 2.5 goals: {format_probability(probabilities['over_2_5'])}")
    lines.append(f"Over 1.5 goals: {format_probability(probabilities['over_1_5'])}")
    lines.append(f"Both teams score - Yes: {format_probability(probabilities['btts_yes'])}")
    lines.append(f"Both teams score - No: {format_probability(probabilities['btts_no'])}")
    lines.append("")

def attach_fixture_dates(angles, fixtures):
    fixtures = fixtures.copy()

    fixtures["match"] = (
        fixtures["home_team"].astype(str)
        + " vs "
        + fixtures["away_team"].astype(str)
    )

    fixtures["fixture_date"] = pd.to_datetime(
        fixtures["date"],
        utc=True,
        errors="coerce"
    )

    fixture_dates = fixtures[["match", "fixture_date"]].drop_duplicates()

    angles = angles.merge(
        fixture_dates,
        on="match",
        how="left"
    )

    return angles


def select_main_free_match(angles):
    """
    Selects the next upcoming match with real available odds.
    It does not select matches that already passed.
    """

    angles = angles.copy()

    angles = angles[
        (angles["odds_found"] == True)
        & (angles["best_decimal_odds"].notna())
        & (angles["matched_selection"].notna())
        & (angles["fixture_date"].notna())
    ].copy()

    if angles.empty:
        return angles

    angles["fixture_date"] = pd.to_datetime(
        angles["fixture_date"],
        utc=True,
        errors="coerce"
    )

    now = pd.Timestamp.now(tz="UTC")

    upcoming = angles[
        (angles["fixture_date"].notna())
        & (angles["fixture_date"] >= now)
    ].copy()

    if upcoming.empty:
        print("No upcoming free match found.")
        return upcoming

    upcoming = upcoming.sort_values(
        by=["fixture_date", "adjusted_confidence_score"],
        ascending=[True, False]
    )

    return upcoming.head(1)

def format_kickoff_time(fixture_date):
    if pd.isna(fixture_date):
        return None

    utc_time = pd.to_datetime(
        fixture_date,
        utc=True,
        errors="coerce"
    )

    if pd.isna(utc_time):
        return None

    local_time = utc_time.tz_convert(ZoneInfo(REPORT_TIMEZONE))

    return local_time.strftime("%b %d, %I:%M %p %Z")

def get_available_line(row):
    matched_selection = str(row["matched_selection"])
    matched_point = row["matched_point"]

    if pd.isna(matched_point):
        return matched_selection

    return f"{matched_selection} {matched_point}"


def extract_goal_line(text):
    if pd.isna(text):
        return None

    text = str(text)

    for part in text.replace("Goals", "").split():
        try:
            return float(part)
        except ValueError:
            continue

    return None


def get_free_market_risk(model_angle, available_line, adjusted_profile):
    model_line = extract_goal_line(model_angle)
    market_line = extract_goal_line(available_line)

    if model_line is None or market_line is None:
        return get_profile_text(adjusted_profile), "Use this as a watchlist spot, not as a guaranteed position."

    difference = abs(market_line - model_line)

    if difference >= 1.5:
        return (
            "Watch only",
            "The available sportsbook line is much harder than the model angle."
        )

    if difference >= 1.0:
        return (
            "High caution watch",
            "The model likes the general direction, but the available line is stricter."
        )

    return (
        get_profile_text(adjusted_profile),
        "The available line is reasonably close to the model direction."
    )


def build_quick_read(row, home_team, away_team, home_stats, away_stats, probabilities, risk_profile):
    selection = str(row["selection"])

    home_gf = float(home_stats["avg_goals_for"])
    home_ga = float(home_stats["avg_goals_against"])
    away_gf = float(away_stats["avg_goals_for"])
    away_ga = float(away_stats["avg_goals_against"])

    expected_total = probabilities["expected_total_goals"]

    if "Under" in selection:
        return (
            f"{home_team} enter this matchup with a recent defensive profile of "
            f"{home_ga:.2f} goals conceded per match, while {away_team} concede around "
            f"{away_ga:.2f}. The model projects {expected_total:.2f} total goals, "
            f"which points toward a lower-goals watch.\n\n"
            f"Risk view: {risk_profile}. This is a statistical watchlist spot, not a guaranteed bet."
        )

    if "Over" in selection:
        return (
            f"{home_team} average {home_gf:.2f} goals scored recently, while "
            f"{away_team} average {away_gf:.2f}. The model projects "
            f"{expected_total:.2f} total goals, which supports a goals-market watch.\n\n"
            f"Risk view: {risk_profile}. The available line still matters, so this should not be treated as automatic value."
        )

    return (
        f"The model sees this match as worth monitoring based on recent form, goals profile, "
        f"and available market lines.\n\n"
        f"Risk view: {risk_profile}. Educational only, not guaranteed betting advice."
    )


def add_free_probability_block(lines, home_team, away_team, home_stats, away_stats):
    probabilities = build_probability_summary(home_stats, away_stats)

    best_market, best_probability = get_best_statistical_angle(probabilities)
    profile = get_probability_profile(best_probability)

    lines.append("🧠 Model probabilities")
    lines.append("")
    lines.append("Projected goals:")
    lines.append(f"{home_team}: {probabilities['home_xg']:.2f}")
    lines.append(f"{away_team}: {probabilities['away_xg']:.2f}")
    lines.append(f"Projected total: {probabilities['expected_total_goals']:.2f}")
    lines.append("")
    lines.append(f"Strongest statistical angle: {best_market}")
    lines.append(f"Estimated probability: {format_probability(best_probability)}")
    lines.append(f"Model profile: {profile}")
    lines.append("")
    lines.append("Key probabilities:")
    lines.append(f"Under 2.5 goals: {format_probability(probabilities['under_2_5'])}")
    lines.append(f"Over 2.5 goals: {format_probability(probabilities['over_2_5'])}")
    lines.append(f"Under 3.5 goals: {format_probability(probabilities['under_3_5'])}")
    lines.append(f"Over 1.5 goals: {format_probability(probabilities['over_1_5'])}")
    lines.append(f"Both teams score - Yes: {format_probability(probabilities['btts_yes'])}")
    lines.append(f"Both teams score - No: {format_probability(probabilities['btts_no'])}")
    lines.append("")

    return probabilities, best_market, best_probability, profile

def generate_free_telegram_intelligence():
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
    fixtures = pd.read_csv(FIXTURES_PATH)

    angles = angles[
        (angles["odds_found"] == True)
        & (angles["best_decimal_odds"].notna())
        & (angles["matched_selection"].notna())
    ].copy()

    angles = attach_fixture_dates(angles, fixtures)

    top = select_main_free_match(angles)

    lines = []

    lines.append("⚽ World Cup Free Match Intelligence")
    lines.append("")
    lines.append("One selected match. Data-backed football analysis before the game.")
    lines.append("No guaranteed bets. Educational only. Bet responsibly.")
    lines.append("")

    if top.empty:
        lines.append("No upcoming free match with available odds found right now.")
        lines.append("")
        lines.append("Try again later or use /premium for the full watchlist.")
    else:
        row = top.iloc[0]

        home_team = row["home_team"]
        away_team = row["away_team"]

        home_stats = find_team_stats(recent_stats, home_team)
        away_stats = find_team_stats(recent_stats, away_team)
        h2h = find_h2h_stats(h2h_stats, home_team, away_team)

        if home_stats is None or away_stats is None:
            lines.append("Not enough team data available for today’s free report.")
        else:
            available_line = get_available_line(row)

            risk_profile, risk_reason = get_free_market_risk(
                model_angle=str(row["selection"]),
                available_line=available_line,
                adjusted_profile=row["adjusted_profile"]
            )

            lines.append(f"Today’s selected match:")
            lines.append(f"⚽ {home_team} vs {away_team}")

            kickoff_time = None

            if "fixture_date" in row and pd.notna(row["fixture_date"]):
                kickoff_time = format_kickoff_time(row["fixture_date"])

            if kickoff_time:
                lines.append(f"Kickoff: {kickoff_time}")
            
            lines.append(
              "Why selected: Upcoming match with available odds and a clear statistical watchlist angle."
              )

            lines.append("")
            lines.append("━━━━━━━━━━━━━━")
            lines.append("")

            probabilities, best_market, best_probability, model_profile = add_free_probability_block(
                lines=lines,
                home_team=home_team,
                away_team=away_team,
                home_stats=home_stats,
                away_stats=away_stats,
            )

            lines.append("━━━━━━━━━━━━━━")
            lines.append("")

            lines.append("📌 Quick read")
            lines.append(
                build_quick_read(
                    row=row,
                    home_team=home_team,
                    away_team=away_team,
                    home_stats=home_stats,
                    away_stats=away_stats,
                    probabilities=probabilities,
                    risk_profile=risk_profile,
                )
            )
            lines.append("")

            lines.append("━━━━━━━━━━━━━━")
            lines.append("")

            lines.append("📊 Recent form")
            add_team_block(lines, home_team, home_stats)
            lines.append("")
            add_team_block(lines, away_team, away_stats)
            lines.append("")

            lines.append("━━━━━━━━━━━━━━")
            lines.append("")

            add_h2h_block(lines, h2h, home_team, away_team)
            lines.append("")

            lines.append("━━━━━━━━━━━━━━")
            lines.append("")

            lines.append("🎯 Market watch")
            lines.append(f"Model angle: {row['selection']}")
            lines.append(f"Available line: {available_line}")
            lines.append(f"Odds around: {row['best_decimal_odds']}")
            lines.append(f"Model confidence on this line: {float(row['adjusted_confidence_score']):.1%}")
            lines.append("")
            lines.append(f"Risk profile: {risk_profile}")
            lines.append(f"Reason: {risk_reason}")
            lines.append("")
            lines.append("Verdict: Watchlist spot, not a guaranteed bet.")
            lines.append("")

            lines.append("━━━━━━━━━━━━━━")
            lines.append("")

            lines.append("🔒 Want the full board?")
            lines.append("")
            lines.append("Premium includes:")
            lines.append("- Next 5 upcoming matches")
            lines.append("- Full model probabilities")
            lines.append("- Odds comparison")
            lines.append("- Risk labels for each market")
            lines.append("- Strong watch / caution watch filters")
            lines.append("- Deeper match reasoning")
            lines.append("- Private premium Telegram access")
            lines.append("")
            lines.append("Use /premium to see access info.")
            lines.append("")
            lines.append("No model can guarantee outcomes.")

    os.makedirs(REPORTS_DIR, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))

    print(f"Free Telegram intelligence generated: {OUTPUT_PATH}")


def main():
    generate_free_telegram_intelligence()


if __name__ == "__main__":
    main()