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

# from ai_match_analyst import (
#    build_match_data_payload,
#    generate_ai_premium_read,
# )

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
ADVANCED_STATS_PATH = os.path.join(RAW_DIR, "api_football_advanced_team_stats.csv")

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

    return probabilities, best_market, best_probability, profile


def build_market_text(row):
    model_angle = str(row["selection"])
    matched_selection = str(row["matched_selection"])
    matched_point = row["matched_point"]

    if pd.isna(matched_point):
        available_line = matched_selection
    else:
        available_line = f"{matched_selection} {matched_point}"

    line_aggression = get_line_aggression_note(
        model_angle=model_angle,
        available_line=available_line
    )

    lines = []

    lines.append("🎯 Available market watch")
    lines.append(f"Model angle: {model_angle}")
    lines.append(f"Available betting line: {available_line}")
    lines.append(f"Available odds around: {row['best_decimal_odds']}")

    if line_aggression["status"] != "normal":
        lines.append(f"Market profile: {line_aggression['profile']}")
        lines.append(f"Line warning: {line_aggression['warning']}")
        lines.append(f"Action: {line_aggression['action']}")
    else:
        lines.append(f"Market profile: {get_profile_text(row['adjusted_profile'])}")

    lines.append(f"Model confidence on this line: {float(row['adjusted_confidence_score']):.1%}")

    if line_aggression["status"] != "normal":
        lines.append(
            "Interpretation: The model likes the general direction, "
            "but the sportsbook line is much harder than the model angle."
        )
    else:
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

def build_premium_summary(top):
    summary_lines = []

    summary_lines.append("🔥 Next 5 Premium Watchlist Summary")
    summary_lines.append("")
    summary_lines.append("Top model angles:")

    summary_candidates = top.copy()

    summary_candidates = summary_candidates.sort_values(
        by="adjusted_confidence_score",
        ascending=False
    ).head(3)

    for index, (_, row) in enumerate(summary_candidates.iterrows(), start=1):
        match = row.get("match", "Unknown match")
        model_angle = row.get("selection", "Market watch")
        confidence = row.get("adjusted_confidence_score", 0)

        try:
          confidence_value = float(confidence)

          if confidence_value <= 1:
           confidence_value = confidence_value * 100

          confidence_text = f"{confidence_value:.0f}%"

        except Exception:
          confidence_text = "N/A"

        summary_lines.append(
            f"{index}. {match} — {model_angle} — {confidence_text}"
        )

    summary_lines.append("")
    summary_lines.append("Next 5 match breakdown below.")
    summary_lines.append("")
    summary_lines.append("━━━━━━━━━━━━━━")
    summary_lines.append("")

    return summary_lines

def extract_goal_line(text):
    """
    Extracts a numeric goal line from text like:
    'Over 2.5', 'Under 3.5 Goals', 'Over 4.0'
    """

    if pd.isna(text):
        return None

    text = str(text)

    for part in text.replace("Goals", "").split():
        try:
            return float(part)
        except ValueError:
            continue

    return None


def get_line_aggression_note(model_angle, available_line):
    """
    Compares the model's preferred market with the available sportsbook line.

    Example:
    Model angle: Over 1.5 Goals
    Available line: Over 4.0

    That is too aggressive and should be flagged.
    """

    model_line = extract_goal_line(model_angle)
    market_line = extract_goal_line(available_line)

    if model_line is None or market_line is None:
        return {
            "status": "normal",
            "profile": None,
            "warning": None,
            "action": None,
        }

    difference = abs(market_line - model_line)

    if difference >= 1.5:
        return {
            "status": "too_aggressive",
            "profile": "Watch only",
            "warning": "Available line is too aggressive compared with the model angle.",
            "action": "Do not treat this as a strong betting spot.",
        }

    if difference >= 1.0:
        return {
            "status": "aggressive",
            "profile": "High caution watch",
            "warning": "Available line is meaningfully stricter than the model angle.",
            "action": "Use extra caution before considering this market.",
        }

    return {
        "status": "normal",
        "profile": None,
        "warning": None,
        "action": None,
    }

def find_advanced_stats(advanced_stats, team_name):
    if advanced_stats is None:
        return None

    row = advanced_stats[advanced_stats["team"] == team_name]

    if row.empty:
        return None

    return row.iloc[0]

def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def classify_corner_pressure(total_corners):
    if total_corners >= 10.5:
        return "High"
    if total_corners >= 8.0:
        return "Moderate"
    return "Low"


def classify_discipline_pressure(total_yellows):
    if total_yellows >= 4.0:
        return "High"
    if total_yellows >= 2.5:
        return "Moderate"
    return "Low"


def classify_fouls_tempo(total_fouls):
    if total_fouls >= 27:
        return "High"
    if total_fouls >= 20:
        return "Moderate"
    return "Low"


def classify_red_card_risk(total_reds):
    if total_reds >= 0.25:
        return "Elevated, but volatile"
    if total_reds >= 0.11:
        return "Slightly elevated"
    return "Normal rare-event baseline"

def is_missing_advanced_stats(stats):
    if stats is None:
        return True

    try:
        if hasattr(stats, "empty") and stats.empty:
            return True
    except Exception:
        return True

    return False


def classify_sample_reliability(home_advanced, away_advanced):
    home_matches = 0
    away_matches = 0

    if not is_missing_advanced_stats(home_advanced):
        home_matches = int(safe_float(home_advanced.get("matches_used", 0)))

    if not is_missing_advanced_stats(away_advanced):
        away_matches = int(safe_float(away_advanced.get("matches_used", 0)))

    min_sample = min(home_matches, away_matches)

    if min_sample < 4:
        return "Low sample"
    if min_sample < 7:
        return "Usable but limited"
    return "Usable baseline"

    min_sample = min(home_matches, away_matches)

    if min_sample < 4:
        return "Low sample"
    if min_sample < 7:
        return "Usable but limited"
    return "Usable baseline"


def get_dominant_corner_side(
    home_team,
    away_team,
    projected_home_corners,
    projected_away_corners
):
    difference = abs(projected_home_corners - projected_away_corners)

    if difference < 1.0:
        return "Balanced"

    if projected_home_corners > projected_away_corners:
        return home_team

    return away_team


def get_corner_trend_alignment(
    dominant_side,
    corner_pressure
):
    if dominant_side == "Balanced":
        if corner_pressure == "High":
            return "High total corner activity, but no clear dominant side"
        if corner_pressure == "Moderate":
            return "Moderate total corner activity with a balanced split"
        return "Low corner activity with no clear dominant side"

    if corner_pressure == "High":
        return f"Strong corner pressure leaning toward {dominant_side}"

    if corner_pressure == "Moderate":
        return f"{dominant_side} pressure side"

    return f"Limited corner activity, slight lean toward {dominant_side}"


def get_discipline_trend_alignment(discipline_pressure, fouls_tempo):
    if discipline_pressure == "Low" and fouls_tempo == "Low":
        return "Low-card profile supported by low foul tempo"

    if discipline_pressure == "High" and fouls_tempo == "High":
        return "High discipline pressure supported by high foul tempo"

    if discipline_pressure == "Moderate" and fouls_tempo in ["Moderate", "High"]:
        return "Moderate discipline pressure with enough foul volume to monitor"

    if discipline_pressure == "Low" and fouls_tempo in ["Moderate", "High"]:
        return "Mixed signal: low yellow-card baseline but higher foul tempo"

    if discipline_pressure in ["Moderate", "High"] and fouls_tempo == "Low":
        return "Mixed signal: card baseline is higher than foul tempo suggests"

    return "Neutral discipline trend"


def build_corner_read(
    dominant_side,
    corner_pressure,
    projected_total_corners
):
    if dominant_side == "Balanced":
        return (
            f"The total corner projection sits around {projected_total_corners:.1f}. "
            "The profile does not show a clear dominant corner side, so this is better treated "
            "as a general corner activity read rather than a team-specific corner lean."
        )

    if corner_pressure == "High":
        return (
            f"The corner profile leans strongly toward {dominant_side} territory and attacking pressure. "
            "The total projection is in a high range, which makes corners worth monitoring if the available line is reasonable."
        )

    if corner_pressure == "Moderate":
        return (
            f"The corner profile leans more toward {dominant_side} territory and attacking pressure. "
            "The total corner projection is moderate, so this is a watchlist signal rather than an aggressive corner angle."
        )

    return (
        f"The model gives a slight corner-pressure lean toward {dominant_side}, but the total corner projection is low. "
        "This is not a strong corners-market signal without a favorable sportsbook line."
    )


def build_discipline_read(discipline_pressure, fouls_tempo):
    if discipline_pressure == "Low" and fouls_tempo == "Low":
        return (
            "Recent team behavior does not point to a naturally aggressive cards match. "
            "The yellow-card baseline is low and the foul tempo is also low, but this should not be treated "
            "as a strong cards-market signal until referee profile and match context are added."
        )

    if discipline_pressure == "High" and fouls_tempo == "High":
        return (
            "Recent team behavior points toward elevated discipline pressure. "
            "Both the yellow-card baseline and foul tempo are high, which makes cards worth monitoring, "
            "especially if the referee profile also supports cards."
        )

    if discipline_pressure == "Moderate":
        return (
            "The discipline profile sits in a moderate range. "
            "There is enough team-discipline activity to monitor cards, but the signal is not strong without referee data."
        )

    if fouls_tempo == "High":
        return (
            "The foul tempo is elevated, but the yellow-card baseline is not equally high. "
            "This creates a mixed cards signal: physical activity may be present, but card conversion depends heavily on the referee."
        )

    return (
        "The discipline profile is mixed. "
        "This should be treated as a context note rather than a direct cards-market signal."
    )


def build_red_card_read(red_card_risk):
    if red_card_risk.startswith("Elevated"):
        return (
            "Recent red-card activity is higher than normal, but red cards remain rare and volatile events. "
            "This should be treated only as a risk note, not as a direct betting angle."
        )

    if red_card_risk == "Slightly elevated":
        return (
            "There is a slight recent red-card signal, but the sample is not strong enough to create a reliable market angle. "
            "Red-card risk should remain a secondary context factor."
        )

    return (
        "Red cards are rare-event outcomes. "
        "No strong red-card signal is generated from team data alone."
    )

def add_advanced_match_block(lines, home_team, away_team, home_advanced, away_advanced):
    lines.append("📈 Advanced match profile")

    if is_missing_advanced_stats(home_advanced) or is_missing_advanced_stats(away_advanced):
        lines.append("Advanced team data is not available for both teams.")
        lines.append("")
        return

    home_corners_for = safe_float(home_advanced.get("avg_corners_for"))
    home_corners_against = safe_float(home_advanced.get("avg_corners_against"))
    away_corners_for = safe_float(away_advanced.get("avg_corners_for"))
    away_corners_against = safe_float(away_advanced.get("avg_corners_against"))

    home_yellows = safe_float(home_advanced.get("avg_yellow_cards"))
    away_yellows = safe_float(away_advanced.get("avg_yellow_cards"))

    home_reds = safe_float(home_advanced.get("avg_red_cards"))
    away_reds = safe_float(away_advanced.get("avg_red_cards"))

    home_fouls = safe_float(home_advanced.get("avg_fouls"))
    away_fouls = safe_float(away_advanced.get("avg_fouls"))

    home_shots_on_goal = safe_float(home_advanced.get("avg_shots_on_goal"))
    away_shots_on_goal = safe_float(away_advanced.get("avg_shots_on_goal"))

    home_total_shots = safe_float(home_advanced.get("avg_total_shots"))
    away_total_shots = safe_float(away_advanced.get("avg_total_shots"))

    home_xg = safe_float(home_advanced.get("avg_expected_goals"))
    away_xg = safe_float(away_advanced.get("avg_expected_goals"))

    projected_home_corners = (home_corners_for + away_corners_against) / 2
    projected_away_corners = (away_corners_for + home_corners_against) / 2
    projected_total_corners = projected_home_corners + projected_away_corners

    yellow_card_baseline = home_yellows + away_yellows
    fouls_baseline = home_fouls + away_fouls
    red_card_baseline = home_reds + away_reds

    corner_pressure = classify_corner_pressure(projected_total_corners)
    discipline_pressure = classify_discipline_pressure(yellow_card_baseline)
    fouls_tempo = classify_fouls_tempo(fouls_baseline)
    red_card_risk = classify_red_card_risk(red_card_baseline)
    reliability = classify_sample_reliability(home_advanced, away_advanced)

    dominant_corner_side = get_dominant_corner_side(
        home_team,
        away_team,
        projected_home_corners,
        projected_away_corners
    )

    corner_trend_alignment = get_corner_trend_alignment(
        dominant_corner_side,
        corner_pressure
    )

    discipline_trend_alignment = get_discipline_trend_alignment(
        discipline_pressure,
        fouls_tempo
    )

    home_xg_text = "N/A" if home_xg == 0 else f"{home_xg:.2f}"
    away_xg_text = "N/A" if away_xg == 0 else f"{away_xg:.2f}"

    lines.append("🚩 Corners trend read")
    lines.append(f"{home_team} projected corners: {projected_home_corners:.1f}")
    lines.append(f"{away_team} projected corners: {projected_away_corners:.1f}")
    lines.append(f"Projected total corners: {projected_total_corners:.1f}")
    lines.append(f"Dominant corner side: {dominant_corner_side}")
    lines.append(f"Corner pressure: {corner_pressure}")
    lines.append(f"Trend alignment: {corner_trend_alignment}")
    lines.append(f"Reliability: {reliability}")
    lines.append(f"Read: {build_corner_read(dominant_corner_side, corner_pressure, projected_total_corners)}")
    lines.append("")

    lines.append("🟨 Discipline / fouls trend read")
    lines.append(f"{home_team} yellow cards avg: {home_yellows:.1f}")
    lines.append(f"{away_team} yellow cards avg: {away_yellows:.1f}")
    lines.append(f"Yellow-card baseline: {yellow_card_baseline:.1f}")
    lines.append(f"Fouls baseline: {fouls_baseline:.1f}")
    lines.append(f"Discipline pressure: {discipline_pressure}")
    lines.append(f"Fouls tempo: {fouls_tempo}")
    lines.append(f"Trend alignment: {discipline_trend_alignment}")
    lines.append(f"Reliability: {reliability}, but limited without referee data")
    lines.append(f"Read: {build_discipline_read(discipline_pressure, fouls_tempo)}")
    lines.append("")

    lines.append("🟥 Red-card risk")
    lines.append(f"{home_team} red cards avg: {home_reds:.2f}")
    lines.append(f"{away_team} red cards avg: {away_reds:.2f}")
    lines.append(f"Combined red-card baseline: {red_card_baseline:.2f}")
    lines.append(f"Recent red-card signal: {red_card_risk}")
    lines.append("Reliability: Low")
    lines.append(f"Read: {build_red_card_read(red_card_risk)}")
    lines.append("")

    lines.append("🎯 Shots / xG profile")
    lines.append(f"{home_team} total shots avg: {home_total_shots:.1f}")
    lines.append(f"{away_team} total shots avg: {away_total_shots:.1f}")
    lines.append(f"{home_team} shots on goal avg: {home_shots_on_goal:.1f}")
    lines.append(f"{away_team} shots on goal avg: {away_shots_on_goal:.1f}")
    lines.append(f"{home_team} recent xG avg: {home_xg_text}")
    lines.append(f"{away_team} recent xG avg: {away_xg_text}")
    lines.append("")

    lines.append(
        "Advanced data note: Corners, cards and fouls are trend profiles based on recent team behavior. "
        "They are not full market predictions yet because referee profile, lineup context and match importance are not included."
    )
    lines.append("")

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
    fixtures = pd.read_csv(FIXTURES_PATH)

    advanced_stats = None

    if os.path.exists(ADVANCED_STATS_PATH):
     advanced_stats = pd.read_csv(ADVANCED_STATS_PATH)

    angles = angles[
    (angles["odds_found"] == True)
    & (angles["best_decimal_odds"].notna())
    & (angles["matched_selection"].notna())
    ].copy()

    angles = attach_fixture_dates(angles, fixtures)

    angles["fixture_date"] = pd.to_datetime(
    angles["fixture_date"],
    utc=True,
    errors="coerce"
   )

    now = pd.Timestamp.now(tz="UTC")

    angles = angles[
    (angles["fixture_date"].notna())
    & (angles["fixture_date"] >= now)
    ].copy()

    angles = angles.sort_values(
    by=["fixture_date", "adjusted_confidence_score"],
    ascending=[True, False]
    )

    top = angles.head(5)

    lines = []

    lines.append("⚽ World Cup Premium Intelligence")
    lines.append("")
    lines.append("Premium betting intelligence report for the next 5 upcoming matches.")
    lines.append(
      "Based on recent form, goal trends, previous meetings, model probabilities and betting lines."
       )
    lines.append("")
    lines.append("No guaranteed bets. Educational only. Bet responsibly.")
    lines.append("")

    if top.empty:
        lines.append("No premium market watchlist available today.")
    else:
        lines.extend(build_premium_summary(top))

    

    for i, (_, row) in enumerate(top.iterrows(), start=1):
            home_team = row["home_team"]
            away_team = row["away_team"]

            home_stats = find_team_stats(recent_stats, home_team)
            away_stats = find_team_stats(recent_stats, away_team)
            h2h = find_h2h_stats(h2h_stats, home_team, away_team)
            home_advanced = find_advanced_stats(advanced_stats, home_team)
            away_advanced = find_advanced_stats(advanced_stats, away_team)

            if home_stats is None or away_stats is None:
                continue

            lines.append(f"{i}) {home_team} vs {away_team}")

            kickoff_time = None

            if "fixture_date" in row and pd.notna(row["fixture_date"]):
             kickoff_time = format_kickoff_time(row["fixture_date"])

            if kickoff_time:
             lines.append(f"Kickoff: {kickoff_time}")

            lines.append("")

            lines.append("📊 Last 10 matches")
            add_team_block(lines, home_team, home_stats)
            lines.append("")
            add_team_block(lines, away_team, away_stats)
            lines.append("")

            add_h2h_block(lines, h2h, home_team, away_team)
            lines.append("")

            probabilities, best_market, best_probability, model_profile = add_probability_block(
            lines,
            home_team,
            away_team,
            home_stats,
            away_stats
          )
            
            add_advanced_match_block(
              lines=lines,
              home_team=home_team,
              away_team=away_team,
              home_advanced=home_advanced,
              away_advanced=away_advanced,
)
            market_lines = build_market_text(row)
            lines.extend(market_lines)
            lines.append("")

            matched_selection = str(row["matched_selection"])
            matched_point = row["matched_point"]

            if pd.isna(matched_point):
             available_line = matched_selection
            else:
             available_line = f"{matched_selection} {matched_point}"

            market_data = {
              "model_angle": str(row["selection"]),
              "available_betting_line": available_line,
              "available_odds": float(row["best_decimal_odds"]),
              "market_profile": get_profile_text(row["adjusted_profile"]),
              "confidence_on_available_line": float(row["adjusted_confidence_score"]),
              "line_note": str(row["line_note"]),
               }

            kickoff_for_ai = kickoff_time if kickoff_time else "Unknown"
            
            lines.append("🧠 Premium read")
            lines.append(build_premium_reason(row, home_team, away_team, home_stats, away_stats))
            lines.append("")
            lines.append("━━━━━━━━━━━━━━")
            lines.append("")

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