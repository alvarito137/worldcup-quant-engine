def classify_pick_quality(row) -> str:
    """
    Classifies whether a pick is suitable for public/premium output.

    This does not mean the pick will win.
    It only controls how aggressively we present the signal.
    """

    signal = row["signal"]
    risk_label = row["risk_label"]
    decimal_odds = row["decimal_odds"]
    confidence_score = row["confidence_score"]
    value_gap = row["value_gap"]
    model_probability = row["model_probability"]
    selection = row["selection"]

    if signal == "NO BET":
        return "NO_BET"

    # Extreme risk should not be promoted as a main public pick.
    if risk_label == "VERY HIGH RISK":
        return "WATCHLIST_ONLY"

    # Draws are volatile. Do not make them main public picks.
    if selection == "Draw":
        return "WATCHLIST_ONLY"

    # Avoid public promotion of high odds unless confidence is strong.
    if decimal_odds > 5.00:
        return "WATCHLIST_ONLY"

    # Main public pick criteria.
    if (
        signal in ["STRONG VALUE", "POSSIBLE VALUE"]
        and risk_label in ["LOW RISK", "MEDIUM RISK", "HIGH RISK"]
        and decimal_odds <= 5.00
        and confidence_score >= 0.35
        and value_gap >= 0.06
        and model_probability >= 0.30
    ):
        return "PUBLIC_SIGNAL"

    # Premium users can still see these, but with caution.
    return "PREMIUM_SIGNAL"