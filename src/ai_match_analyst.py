import os
import json
from dotenv import load_dotenv
from openai import OpenAI


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_PATH)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AI_ANALYST_ENABLED = os.getenv("AI_ANALYST_ENABLED", "false").lower() == "true"

client = OpenAI(api_key=OPENAI_API_KEY)


def build_match_data_payload(
    home_team,
    away_team,
    kickoff_time,
    home_stats,
    away_stats,
    h2h,
    probabilities,
    market_data,
):
    payload = {
        "match": f"{home_team} vs {away_team}",
        "kickoff": kickoff_time,
        "home_team": {
            "name": home_team,
            "record_last_10": f"{int(home_stats['wins'])}W-{int(home_stats['draws'])}D-{int(home_stats['losses'])}L",
            "goals_for": float(home_stats["goals_for"]),
            "goals_against": float(home_stats["goals_against"]),
            "avg_goals_for": float(home_stats["avg_goals_for"]),
            "avg_goals_against": float(home_stats["avg_goals_against"]),
            "over_2_5_rate": float(home_stats["over_2_5_rate"]),
            "btts_rate": float(home_stats["btts_rate"]),
            "clean_sheet_rate": float(home_stats["clean_sheet_rate"]),
            "failed_to_score_rate": float(home_stats["failed_to_score_rate"]),
        },
        "away_team": {
            "name": away_team,
            "record_last_10": f"{int(away_stats['wins'])}W-{int(away_stats['draws'])}D-{int(away_stats['losses'])}L",
            "goals_for": float(away_stats["goals_for"]),
            "goals_against": float(away_stats["goals_against"]),
            "avg_goals_for": float(away_stats["avg_goals_for"]),
            "avg_goals_against": float(away_stats["avg_goals_against"]),
            "over_2_5_rate": float(away_stats["over_2_5_rate"]),
            "btts_rate": float(away_stats["btts_rate"]),
            "clean_sheet_rate": float(away_stats["clean_sheet_rate"]),
            "failed_to_score_rate": float(away_stats["failed_to_score_rate"]),
        },
        "model_probabilities": {
            "home_xg": float(probabilities["home_xg"]),
            "away_xg": float(probabilities["away_xg"]),
            "expected_total_goals": float(probabilities["expected_total_goals"]),
            "under_2_5": float(probabilities["under_2_5"]),
            "over_2_5": float(probabilities["over_2_5"]),
            "under_3_5": float(probabilities["under_3_5"]),
            "over_1_5": float(probabilities["over_1_5"]),
            "btts_yes": float(probabilities["btts_yes"]),
            "btts_no": float(probabilities["btts_no"]),
            "home_over_0_5": float(probabilities["home_over_0_5"]),
            "away_over_0_5": float(probabilities["away_over_0_5"]),
            "home_over_1_5": float(probabilities["home_over_1_5"]),
            "away_over_1_5": float(probabilities["away_over_1_5"]),
        },
        "market_data": market_data,
    }

    if h2h is not None:
        payload["h2h"] = {
            "matches_found": int(h2h["h2h_matches_found"]),
            "home_team_wins": int(h2h["home_team_h2h_wins"]),
            "away_team_wins": int(h2h["away_team_h2h_wins"]),
            "draws": int(h2h["h2h_draws"]),
            "avg_goals": float(h2h["h2h_avg_goals"]),
            "over_2_5_rate": float(h2h["h2h_over_2_5_rate"]),
            "btts_rate": float(h2h["h2h_btts_rate"]),
        }
    else:
        payload["h2h"] = None

    return payload


def generate_ai_premium_read(match_payload):
    if not AI_ANALYST_ENABLED:
        return None

    if not OPENAI_API_KEY:
        return None

    try:
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY)

        prompt = f"""
You are a professional football betting intelligence analyst.

Use ONLY the data provided below.
Do NOT invent injuries, lineups, referee information, weather, motivation, rankings, or news.
Do NOT guarantee outcomes.
Do NOT say "best bet", "lock", "guaranteed", or "safe bet".

Write a concise premium analysis in English for Telegram.

Structure:
1. Tactical/data read: 2-3 sentences.
2. Market risk read: 1-2 sentences.
3. Final verdict line using one of:
   - Strong watch
   - Moderate watch
   - High caution
   - Watch only

Data:
{json.dumps(match_payload, indent=2)}
"""

        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
        )

        return response.output_text.strip()

    except Exception as error:
        print(f"AI analyst error: {error}")
        return None