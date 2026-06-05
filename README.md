# World Cup Quant Betting + Content Engine

A Python-based sports analytics MVP for generating World Cup match probabilities, market-implied probabilities, value gaps, betting signals, bankroll sizing, reports, and short-form content scripts.

## Current MVP Features

- Loads mock World Cup fixtures
- Loads mock decimal odds
- Loads team ratings
- Calculates implied market probability
- Estimates model probability
- Calculates value gap
- Generates value betting signals
- Applies fractional Kelly bankroll sizing
- Exports picks to CSV
- Generates daily Markdown report
- Generates TikTok/YouTube Shorts scripts

## Project Structure

```text
worldcup-quant-engine/
├── data/
│   ├── raw/
│   │   ├── fixtures.csv
│   │   ├── odds.csv
│   │   └── team_ratings.csv
│   └── processed/
│       └── picks.csv
├── reports/
│   ├── daily_report.md
│   └── tiktok_scripts.md
├── src/
│   ├── main.py
│   ├── data_loader.py
│   ├── value_engine.py
│   ├── report_generator.py
│   └── content_generator.py
├── requirements.txt
└── README.md