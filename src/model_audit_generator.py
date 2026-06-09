import os
import pandas as pd


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REPORTS_DIR = os.path.join(BASE_DIR, "reports")
MODEL_AUDIT_PATH = os.path.join(REPORTS_DIR, "model_audit_report.md")


def calculate_model_audit_metrics(picks: pd.DataFrame) -> dict:
    """
    Calculates diagnostic metrics to detect whether the model is producing
    too many risky or unrealistic value signals.
    """

    total_rows = len(picks)

    value_picks = picks[picks["signal"] != "NO BET"].copy()
    strong_value_picks = picks[picks["signal"] == "STRONG VALUE"].copy()
    possible_value_picks = picks[picks["signal"] == "POSSIBLE VALUE"].copy()

    odds_over_5 = value_picks[value_picks["decimal_odds"] > 5]
    odds_over_10 = value_picks[value_picks["decimal_odds"] > 10]

    high_risk = value_picks[value_picks["risk_label"].isin(["HIGH RISK", "VERY HIGH RISK"])]
    very_high_risk = value_picks[value_picks["risk_label"] == "VERY HIGH RISK"]

    draw_picks = value_picks[value_picks["selection"] == "Draw"]

    avg_odds = value_picks["decimal_odds"].mean() if not value_picks.empty else 0
    avg_value_gap = value_picks["value_gap"].mean() if not value_picks.empty else 0
    avg_model_probability = value_picks["model_probability"].mean() if not value_picks.empty else 0
    avg_confidence_score = value_picks["confidence_score"].mean() if not value_picks.empty else 0

    value_pick_count = len(value_picks)

    pct_value_picks = value_pick_count / total_rows if total_rows > 0 else 0
    pct_strong_value = len(strong_value_picks) / value_pick_count if value_pick_count > 0 else 0
    pct_odds_over_5 = len(odds_over_5) / value_pick_count if value_pick_count > 0 else 0
    pct_odds_over_10 = len(odds_over_10) / value_pick_count if value_pick_count > 0 else 0
    pct_high_risk = len(high_risk) / value_pick_count if value_pick_count > 0 else 0
    pct_very_high_risk = len(very_high_risk) / value_pick_count if value_pick_count > 0 else 0
    pct_draw_picks = len(draw_picks) / value_pick_count if value_pick_count > 0 else 0

    return {
        "total_rows": total_rows,
        "value_pick_count": value_pick_count,
        "strong_value_count": len(strong_value_picks),
        "possible_value_count": len(possible_value_picks),
        "odds_over_5_count": len(odds_over_5),
        "odds_over_10_count": len(odds_over_10),
        "high_risk_count": len(high_risk),
        "very_high_risk_count": len(very_high_risk),
        "draw_pick_count": len(draw_picks),
        "avg_odds": avg_odds,
        "avg_value_gap": avg_value_gap,
        "avg_model_probability": avg_model_probability,
        "avg_confidence_score": avg_confidence_score,
        "pct_value_picks": pct_value_picks,
        "pct_strong_value": pct_strong_value,
        "pct_odds_over_5": pct_odds_over_5,
        "pct_odds_over_10": pct_odds_over_10,
        "pct_high_risk": pct_high_risk,
        "pct_very_high_risk": pct_very_high_risk,
        "pct_draw_picks": pct_draw_picks,
    }


def get_audit_warnings(metrics: dict) -> list[str]:
    """
    Creates warning messages based on model behavior.
    """

    warnings = []

    if metrics["pct_value_picks"] > 0.25:
        warnings.append(
            "Too many value picks. The model may be over-detecting value."
        )

    if metrics["pct_strong_value"] > 0.50:
        warnings.append(
            "Too many STRONG VALUE signals. Thresholds may be too loose."
        )

    if metrics["pct_odds_over_5"] > 0.40:
        warnings.append(
            "Too many high-odds picks. The model may be too longshot-heavy."
        )

    if metrics["pct_odds_over_10"] > 0.15:
        warnings.append(
            "Too many extreme longshots. Add stricter filters for odds above 10."
        )

    if metrics["pct_very_high_risk"] > 0.40:
        warnings.append(
            "Too many VERY HIGH RISK picks. Reduce exposure or tighten signal rules."
        )

    if metrics["pct_draw_picks"] > 0.40:
        warnings.append(
            "Too many draw picks. Draw probability may be too generous."
        )

    if not warnings:
        warnings.append(
            "No major audit warnings detected. Still validate with real results."
        )

    return warnings


def generate_model_audit_report(picks: pd.DataFrame):
    """
    Generates a Markdown audit report to diagnose model behavior.
    """

    os.makedirs(REPORTS_DIR, exist_ok=True)

    metrics = calculate_model_audit_metrics(picks)
    warnings = get_audit_warnings(metrics)

    lines = []

    lines.append("# World Cup Quant Model Audit Report")
    lines.append("")
    lines.append("## Purpose")
    lines.append("")
    lines.append(
        "This report checks whether the model is producing too many risky, "
        "longshot-heavy, or unrealistic value signals."
    )
    lines.append("")

    lines.append("## Core Audit Metrics")
    lines.append("")
    lines.append(f"- Total market rows analyzed: **{metrics['total_rows']}**")
    lines.append(f"- Value picks: **{metrics['value_pick_count']}**")
    lines.append(f"- STRONG VALUE picks: **{metrics['strong_value_count']}**")
    lines.append(f"- POSSIBLE VALUE picks: **{metrics['possible_value_count']}**")
    lines.append(f"- Value pick rate: **{metrics['pct_value_picks']:.2%}**")
    lines.append("")

    lines.append("## Risk Profile")
    lines.append("")
    lines.append(f"- Picks with odds > 5.00: **{metrics['odds_over_5_count']}**")
    lines.append(f"- Picks with odds > 10.00: **{metrics['odds_over_10_count']}**")
    lines.append(f"- High risk picks: **{metrics['high_risk_count']}**")
    lines.append(f"- Very high risk picks: **{metrics['very_high_risk_count']}**")
    lines.append(f"- Draw picks: **{metrics['draw_pick_count']}**")
    lines.append("")

    lines.append("## Averages")
    lines.append("")
    lines.append(f"- Average odds on value picks: **{metrics['avg_odds']:.2f}**")
    lines.append(f"- Average value gap: **{metrics['avg_value_gap']:.2%}**")
    lines.append(f"- Average model probability: **{metrics['avg_model_probability']:.2%}**")
    lines.append(f"- Average confidence score: **{metrics['avg_confidence_score']:.2%}**")
    lines.append("")

    lines.append("## Warnings")
    lines.append("")

    for warning in warnings:
        lines.append(f"- {warning}")

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "If the report shows too many high-odds or very-high-risk selections, "
        "the model should not be used for public selling yet. Tighten filters, "
        "improve ratings, and track real results first."
    )

    with open(MODEL_AUDIT_PATH, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))

    print(f"Model audit report generated: {MODEL_AUDIT_PATH}")