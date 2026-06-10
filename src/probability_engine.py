import math


def poisson_probability(k, expected_goals):
    return (expected_goals ** k) * math.exp(-expected_goals) / math.factorial(k)


def total_goals_probability(home_xg, away_xg, line, direction):
    """
    Calculates probability of Over/Under a goals line using a simple Poisson model.

    Under 2.5 = total goals <= 2
    Over 2.5 = total goals >= 3
    """

    max_goals = 10
    probability = 0.0

    for home_goals in range(max_goals + 1):
        for away_goals in range(max_goals + 1):
            total_goals = home_goals + away_goals

            p_home = poisson_probability(home_goals, home_xg)
            p_away = poisson_probability(away_goals, away_xg)
            p_score = p_home * p_away

            if direction == "under" and total_goals < line:
                probability += p_score

            if direction == "over" and total_goals > line:
                probability += p_score

    return probability


def btts_probability(home_xg, away_xg):
    """
    Probability that both teams score at least one goal.
    """

    p_home_zero = poisson_probability(0, home_xg)
    p_away_zero = poisson_probability(0, away_xg)

    p_home_scores = 1 - p_home_zero
    p_away_scores = 1 - p_away_zero

    return p_home_scores * p_away_scores


def team_over_probability(team_xg, line):
    """
    Probability a team scores over a goal line.

    Over 0.5 = at least 1 goal
    Over 1.5 = at least 2 goals
    """

    max_goals = 10
    probability = 0.0

    for goals in range(max_goals + 1):
        p = poisson_probability(goals, team_xg)

        if goals > line:
            probability += p

    return probability


def estimate_expected_goals(home_stats, away_stats):
    """
    Simple expected goals estimate using recent goals for and goals against.
    """

    home_xg = (
        float(home_stats["avg_goals_for"])
        + float(away_stats["avg_goals_against"])
    ) / 2

    away_xg = (
        float(away_stats["avg_goals_for"])
        + float(home_stats["avg_goals_against"])
    ) / 2

    return home_xg, away_xg


def build_probability_summary(home_stats, away_stats):
    home_xg, away_xg = estimate_expected_goals(home_stats, away_stats)

    under_2_5 = total_goals_probability(home_xg, away_xg, 2.5, "under")
    over_2_5 = total_goals_probability(home_xg, away_xg, 2.5, "over")
    under_3_5 = total_goals_probability(home_xg, away_xg, 3.5, "under")
    over_1_5 = total_goals_probability(home_xg, away_xg, 1.5, "over")

    btts_yes = btts_probability(home_xg, away_xg)
    btts_no = 1 - btts_yes

    home_over_0_5 = team_over_probability(home_xg, 0.5)
    away_over_0_5 = team_over_probability(away_xg, 0.5)

    home_over_1_5 = team_over_probability(home_xg, 1.5)
    away_over_1_5 = team_over_probability(away_xg, 1.5)

    return {
        "home_xg": home_xg,
        "away_xg": away_xg,
        "expected_total_goals": home_xg + away_xg,

        "under_2_5": under_2_5,
        "over_2_5": over_2_5,
        "under_3_5": under_3_5,
        "over_1_5": over_1_5,

        "btts_yes": btts_yes,
        "btts_no": btts_no,

        "home_over_0_5": home_over_0_5,
        "away_over_0_5": away_over_0_5,
        "home_over_1_5": home_over_1_5,
        "away_over_1_5": away_over_1_5,
    }


def get_best_statistical_angle(probabilities):
    """
    Picks the highest-probability simple market.
    This is NOT the same as best value bet.
    """

    candidates = {
        "Under 2.5 Goals": probabilities["under_2_5"],
        "Over 2.5 Goals": probabilities["over_2_5"],
        "Under 3.5 Goals": probabilities["under_3_5"],
        "Over 1.5 Goals": probabilities["over_1_5"],
        "Both Teams To Score - Yes": probabilities["btts_yes"],
        "Both Teams To Score - No": probabilities["btts_no"],
    }

    best_market = max(candidates, key=candidates.get)
    best_probability = candidates[best_market]

    return best_market, best_probability


def get_probability_profile(probability):
    if probability >= 0.72:
        return "Strong statistical lean"

    if probability >= 0.62:
        return "Moderate statistical lean"

    return "Caution watch"


def format_probability(value):
    return f"{float(value):.0%}"