"""Build a consolidated portfolio snapshot from real tool output + the agent's actual recorded decisions.

Run this after `python -m contract_watchdog.main` (so outbox/*.jsonl
exists). It re-runs the same deterministic tools the agent used
(scan_for_renewals, detect_price_changes, detect_unfavorable_clauses —
none of these call a model, so this is cheap and reproducible) and joins
the result with what the agent actually decided (decision_log.jsonl),
what it actually notified about (pending_decisions.jsonl), and the real
drafted email text (drafted_emails.jsonl).

This is the file the Next.js frontend reads — see frontend/app/page.tsx.
There is no live backend call between the two; the frontend just reads
this JSON snapshot off disk. Re-run this script (and restart/refresh the
frontend) any time you want it to reflect a fresh agent run.
"""

import json
import os
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from contract_watchdog.tools.analysis import detect_price_changes, detect_unfavorable_clauses
from contract_watchdog.tools.contracts import load_contracts, scan_for_renewals

ROOT = os.path.join(os.path.dirname(__file__), "..")
CONTRACTS_DIR = os.path.join(ROOT, "sample_data", "contracts")
DECISION_LOG_PATH = os.path.join(ROOT, "outbox", "decision_log.jsonl")
PENDING_PATH = os.path.join(ROOT, "outbox", "pending_decisions.jsonl")
EMAILS_PATH = os.path.join(ROOT, "outbox", "drafted_emails.jsonl")
OUT_PATH = os.path.join(ROOT, "outbox", "portfolio_snapshot.json")


def _read_jsonl(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _latest_by_contract(entries: list[dict]) -> dict:
    """Keep only the most recent entry per contract_id (a contract may be reviewed more than once)."""
    latest: dict[str, dict] = {}
    for entry in entries:
        cid = entry["contract_id"]
        if cid not in latest or entry["timestamp"] > latest[cid]["timestamp"]:
            latest[cid] = entry
    return latest


def main() -> None:
    contracts = load_contracts(CONTRACTS_DIR)
    due = {c["contract_id"]: c for c in scan_for_renewals(contracts, within_days=10_000)}

    decisions = _latest_by_contract(_read_jsonl(DECISION_LOG_PATH))
    notifications = {n["contract_id"]: n for n in _read_jsonl(PENDING_PATH)}
    emails = {e["contract_id"]: e for e in _read_jsonl(EMAILS_PATH)}

    today = date.today()
    snapshot = []

    for contract in contracts:
        cid = contract["contract_id"]
        annotated = due.get(cid, contract)
        price = detect_price_changes(contract)
        risk = detect_unfavorable_clauses(contract)
        decision = decisions.get(cid)
        notification = notifications.get(cid)
        email = emails.get(cid)

        renewal_date = datetime.strptime(contract["renewal_date"], "%Y-%m-%d").date()
        notice_deadline = annotated.get("notice_deadline")
        days_until = (
            (datetime.strptime(notice_deadline, "%Y-%m-%d").date() - today).days
            if notice_deadline
            else None
        )

        is_flagged = notification is not None
        reasoning = (
            notification["summary"] if notification
            else decision["notes"] if decision
            else None
        )

        snapshot.append({
            "id": cid,
            "counterparty": contract.get("counterparty"),
            "type": contract.get("contract_type"),
            "description": contract.get("description"),
            "status": "flagged" if is_flagged else "reviewed",
            "urgency": notification["urgency"] if notification else None,
            "hasPrice": bool(contract.get("current_price_monthly_usd")),
            "prevPrice": price["previous_price_monthly_usd"],
            "currPrice": price["current_price_monthly_usd"],
            "pctChange": price["pct_change"],
            "renewalDate": renewal_date.isoformat(),
            "noticeDeadline": notice_deadline,
            "daysUntil": days_until,
            "risks": risk["risk_matches"],
            "reasoning": reasoning,
            "recommendedAction": notification["recommended_action"] if notification else None,
            "hasEmail": email is not None,
            "emailSubject": email["email_subject"] if email else None,
            "emailBody": email["email_body"] if email else None,
            "referencePricingNote": email["reference_pricing_note"] if email else None,
            "reviewedAt": decision["timestamp"] if decision else None,
        })

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump({"generatedAt": datetime.now().isoformat(timespec="seconds"), "contracts": snapshot}, f, indent=2)

    print(f"wrote {OUT_PATH} ({len(snapshot)} contracts)")


if __name__ == "__main__":
    main()
