import subprocess
import sys


def run_command(command: list[str], step_name: str):
    """
    Runs a terminal command and stops the pipeline if the command fails.
    """

    print(f"\n=== {step_name} ===")
    print(f"Running: {' '.join(command)}")

    result = subprocess.run(command)

    if result.returncode != 0:
        raise RuntimeError(f"Step failed: {step_name}")

    print(f"Completed: {step_name}")


def main():
    """
    Runs the full World Cup Quant pipeline.

    Steps:
    1. Generate picks
    2. Generate reports
    3. Generate newsletter
    4. Generate premium CSV
    5. Generate Telegram alert text
    6. Send Telegram alert
    """

    python_executable = sys.executable

    run_command(
        [python_executable, "src/main.py"],
        "Generate picks, reports, newsletter, content, premium CSV and Telegram alert text"
    )

    run_command(
        [python_executable, "telegram_bot/send_alerts.py"],
        "Send Telegram alert"
    )

    print("\nPipeline completed successfully.")


if __name__ == "__main__":
    main()