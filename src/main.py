import os
import pandas as pd

from data_loader import load_or_create_mock_data
from value_engine import build_picks
from report_generator import generate_markdown_report
from content_generator import generate_content_scripts
from newsletter_generator import generate_newsletter
from exporter import export_premium_picks


def main():
    load_or_create_mock_data()

    picks = build_picks()

    print("\nTop picks:")
    print(picks.head(10).to_string(index=False))

    generate_markdown_report(picks)
    generate_content_scripts(picks)
    generate_newsletter(picks)
    export_premium_picks(picks)


if __name__ == "__main__":
    main()