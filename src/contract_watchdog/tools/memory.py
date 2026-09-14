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


def _load_recent(cooldown_days: int) -> dict[str, dict]:
    """Latest decision per contract_id within the cooldown window. Plain helper, not an agent tool.

    Shared by check_recent_decisions (what the agent sees) and
    is_recently_flagged (a deterministic guard other tools call directly —
    see notify.py). Enforcement lives in the guard, not in whether the
    model correctly acts on what this returns: a live test showed the
    model can see this data and still re-notify anyway, rationalizing it
    after the fact. Prompting alone wasn't reliable enough here.
    """
    if not os.path.exists(DECISION_LOG_PATH):
        return {}

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

    return latest_by_contract


def is_recently_flagged(contract_id: str, cooldown_days: int = 7) -> bool:
    """Deterministic check: was this contract already flagged and notified within the cooldown window?

    Not an agent tool — called directly by notify_human so the "don't
    duplicate a notification" rule is enforced in code, not left to the
    model to honor on its own.
    """
    entry = _load_recent(cooldown_days).get(contract_id)
    return bool(entry and entry.get("decision") == "flagged_notified")


@tool
def check_recent_decisions(cooldown_days: int = 7) -> list[dict]:
    """Load prior decisions recorded within the cooldown window, before reviewing contracts this run.

    Call this first, before load_contracts, so your summary can mention
    what's already been handled. You do not need to remember to skip
    notify_human yourself for these — it enforces the cooldown on its own
    — but re-evaluating a contract from scratch when it's already been
    flagged and notified recently is wasted work, so skip straight to a
    brief note for those instead of redoing the full analysis.

    Args:
        cooldown_days: How many days a prior decision stays valid before
            the contract should be treated as unreviewed again.

    Returns:
        A list of {contract_id, decision, notes, timestamp}, most recent
        decision per contract only.
    """
    return list(_load_recent(cooldown_days).values())


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
