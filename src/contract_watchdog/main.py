"""CLI entrypoint: run the Contract Watchdog agent over a directory of contracts."""

import argparse

from dotenv import load_dotenv

from .agent import build_agent


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Run the Contract Watchdog agent.")
    parser.add_argument(
        "--contracts-dir",
        default="sample_data/contracts",
        help="Directory of contract JSON files to review.",
    )
    args = parser.parse_args()

    agent = build_agent()
    prompt = (
        f"Review every contract in '{args.contracts_dir}'. Handle what needs "
        "handling and only notify me about contracts that genuinely need a "
        "decision. Give me a short summary when you're done."
    )

    result = agent(prompt)
    print("\n=== Agent summary ===")
    print(result)


if __name__ == "__main__":
    main()
