import os
import pandas as pd

from data_loader import load_or_create_mock_data
from value_engine import build_picks
from report_generator import generate_markdown_report
from content_generator import generate_content_scripts


def main():
    load_or_create_mock_data()

    picks = build_picks()

    print("\nTop picks:")
    print(picks.head(10).to_string(index=False))

    generate_markdown_report(picks)
    generate_content_scripts(picks)


if __name__ == "__main__":
    main()