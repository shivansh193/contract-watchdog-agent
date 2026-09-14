"""Build a consolidated portfolio snapshot from real tool output + the agent's actual recorded decisions.

Run this after `python -m contract_watchdog.main` (so outbox/*.jsonl
exists). It re-runs the same deterministic tools the agent used
(scan_for_renewals, detect_price_changes, detect_unfavorable_clauses —
none of these call a model, so this is cheap and reproducible) and joins
the result with what the agent actually decided (outbox/decision_log.jsonl)
and what it actually notified about (outbox/pending_decisions.jsonl,
including the drafted email if one exists).

This is the real data pipeline behind the portfolio dashboard concept —
the design/ dashboard currently embeds a snapshot in this same shape
rather than fetching it live (published artifacts can't reach back into
your filesystem), but this script is what would feed a real one.
"""

import json
import os
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from contract_watchdog.tools.analysis import detect_price_changes, detect_unfavorable_clauses
from contract_watchdog.tools.contracts import load_contracts, scan_for_renewals

CONTRACTS_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_data", "contracts")
DECISION_LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "outbox", "decision_log.jsonl")
PENDING_PATH = os.path.join(os.path.dirname(__file__), "..", "outbox", "pending_decisions.jsonl")
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "outbox", "portfolio_snapshot.json")


def _read_jsonl(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main() -> None:
    contracts = load_contracts(CONTRACTS_DIR)
    due = {c["contract_id"]: c for c in scan_for_renewals(contracts, within_days=10_000)}

    decisions = {d["contract_id"]: d for d in _read_jsonl(DECISION_LOG_PATH)}
    notifications = {n["contract_id"]: n for n in _read_jsonl(PENDING_PATH)}

    today = date.today()
    snapshot = []

    for contract in contracts:
        cid = contract["contract_id"]
        annotated = due.get(cid, contract)
        price = detect_price_changes(contract)
        risk = detect_unfavorable_clauses(contract)
        decision = decisions.get(cid)
        notification = notifications.get(cid)

        renewal_date = datetime.strptime(contract["renewal_date"], "%Y-%m-%d").date()
        notice_deadline = annotated.get("notice_deadline")
        days_until = (
            (datetime.strptime(notice_deadline, "%Y-%m-%d").date() - today).days
            if notice_deadline
            else None
        )

        snapshot.append({
            "id": cid,
            "counterparty": contract.get("counterparty"),
            "type": contract.get("contract_type"),
            "description": contract.get("description"),
            "hasPrice": bool(contract.get("current_price_monthly_usd")),
            "prevPrice": price["previous_price_monthly_usd"],
            "currPrice": price["current_price_monthly_usd"],
            "pctChange": price["pct_change"],
            "renewalDate": renewal_date.isoformat(),
            "noticeDeadline": notice_deadline,
            "daysUntil": days_until,
            "risks": risk["risk_matches"],
            "decision": decision["decision"] if decision else "not_yet_reviewed",
            "decisionNotes": decision["notes"] if decision else None,
            "notified": notification is not None,
            "notificationSummary": notification["summary"] if notification else None,
            "recommendedAction": notification["recommended_action"] if notification else None,
            "urgency": notification["urgency"] if notification else None,
        })

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump({"generated_at": datetime.now().isoformat(timespec="seconds"), "contracts": snapshot}, f, indent=2)

    print(f"wrote {OUT_PATH} ({len(snapshot)} contracts)")


if __name__ == "__main__":
    main()
