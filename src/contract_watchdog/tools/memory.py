"""Decision memory — lets the agent avoid re-flagging a contract it already handled.

Without this, running the agent twice over the same contracts would
re-notify on everything again every time, which undercuts the "runs
autonomously" story — a human would quickly learn to ignore repeat pings,
which is worse than not having the agent at all. check_recent_decisions
and record_decision give the agent a simple way to remember what it
already decided and skip re-notifying within a cooldown window, while
still re-evaluating once the cooldown expires (so a genuinely new problem
on a previously-reviewed contract still gets caught).
"""

import json
import os
from datetime import datetime, timedelta

from strands import tool

DECISION_LOG_PATH = os.path.join("outbox", "decision_log.jsonl")


@tool
def check_recent_decisions(cooldown_days: int = 7) -> list[dict]:
    """Load prior decisions recorded within the cooldown window, before reviewing contracts this run.

    Call this first, before load_contracts. For any contract_id that
    already has a recent "flagged_notified" decision, don't notify again
    this run — the human has already been told. Re-evaluate it normally
    once its most recent decision falls outside the cooldown window.

    Args:
        cooldown_days: How many days a prior decision stays valid before
            the contract should be treated as unreviewed again.

    Returns:
        A list of {contract_id, decision, notes, timestamp}, most recent
        decision per contract only.
    """
    if not os.path.exists(DECISION_LOG_PATH):
        return []

    cutoff = datetime.now() - timedelta(days=cooldown_days)
    latest_by_contract: dict[str, dict] = {}

    with open(DECISION_LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            ts = datetime.fromisoformat(entry["timestamp"])
            if ts < cutoff:
                continue
            existing = latest_by_contract.get(entry["contract_id"])
            if existing is None or ts > datetime.fromisoformat(existing["timestamp"]):
                latest_by_contract[entry["contract_id"]] = entry

    return list(latest_by_contract.values())


@tool
def record_decision(contract_id: str, decision: str, notes: str = "") -> dict:
    """Record what the agent decided about a contract this run, for future runs to check via check_recent_decisions.

    Call this once per contract reviewed, every run — including contracts
    that needed no action, so the memory reflects everything that was
    actually looked at, not just the flagged ones.

    Args:
        contract_id: The contract this decision is about.
        decision: A short label, e.g. "flagged_notified", "reviewed_no_action".
        notes: Optional short context for a human reading the raw log later.

    Returns:
        A dict confirming the record was written.
    """
    os.makedirs(os.path.dirname(DECISION_LOG_PATH), exist_ok=True)

    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "contract_id": contract_id,
        "decision": decision,
        "notes": notes,
    }

    with open(DECISION_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    return {"recorded": True, **entry}
