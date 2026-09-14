"""Tools for loading contract records and finding which ones are approaching renewal."""

import json
import os
from datetime import date, datetime

from strands import tool


@tool
def load_contracts(directory: str = "sample_data/contracts") -> list[dict]:
    """Load all vendor contract records from a directory of JSON files.

    Args:
        directory: Path to a folder containing one JSON file per contract.
            Each file is expected to have: vendor, contract_id, service,
            current_price_monthly_usd, previous_price_monthly_usd,
            renewal_date (YYYY-MM-DD), auto_renew, notice_period_days,
            contract_excerpt, owner_email.

    Returns:
        A list of contract records as dicts, each tagged with its source file.
    """
    contracts = []
    if not os.path.isdir(directory):
        return contracts

    for filename in sorted(os.listdir(directory)):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(directory, filename)
        with open(path, "r", encoding="utf-8") as f:
            record = json.load(f)
        record["_source_file"] = filename
        contracts.append(record)

    return contracts


@tool
def scan_for_renewals(contracts: list[dict], within_days: int = 45) -> list[dict]:
    """Find contracts whose cancel/renegotiate notice deadline falls within a lookahead window.

    A contract's "notice deadline" is its renewal_date minus notice_period_days —
    the last day a human could act before the contract silently auto-renews.

    Args:
        contracts: Contract records, as returned by load_contracts.
        within_days: How many days from today counts as "coming up soon".

    Returns:
        The subset of contracts whose notice deadline is within `within_days`
        days from today, each annotated with days_until_notice_deadline and
        notice_deadline (ISO date string).
    """
    today = date.today()
    due = []

    for contract in contracts:
        renewal_date = datetime.strptime(contract["renewal_date"], "%Y-%m-%d").date()
        notice_period = int(contract.get("notice_period_days", 0))
        notice_deadline = date.fromordinal(renewal_date.toordinal() - notice_period)
        days_until = (notice_deadline - today).days

        if days_until <= within_days:
            annotated = dict(contract)
            annotated["notice_deadline"] = notice_deadline.isoformat()
            annotated["days_until_notice_deadline"] = days_until
            due.append(annotated)

    return due
