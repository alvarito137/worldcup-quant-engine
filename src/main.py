import os
import pandas as pd

from data_loader import load_or_create_mock_data
from value_engine import build_picks
from report_generator import generate_markdown_report
from content_generator import generate_content_scripts
from newsletter_generator import generate_newsletter
from exporter import export_premium_picks
from telegram_alert_generator import generate_telegram_alerts
from free_sample_generator import generate_free_sample
from performance_tracker import update_pick_history
from performance_summary_generator import generate_performance_summary
from sales_copy_generator import generate_sales_copy
from pricing_strategy_generator import generate_pricing_strategy


def main():
    load_or_create_mock_data()

    picks = build_picks()

    print("\nTop picks:")
    print(picks.head(10).to_string(index=False))

    generate_markdown_report(picks)
    generate_content_scripts(picks)
    generate_newsletter(picks)
    export_premium_picks(picks)
    generate_telegram_alerts(picks)
    generate_free_sample(picks)
    update_pick_history(picks)
    generate_performance_summary()
    generate_sales_copy()
    generate_pricing_strategy()
    


if __name__ == "__main__":
    main()