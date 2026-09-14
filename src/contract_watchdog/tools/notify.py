"""The one tool that actually interrupts a human.

This is the tool the agent should call sparingly — the whole point of the
hackathon brief is an agent that runs quietly and "only surfaces when
there's a real decision to make." Everything else (loading contracts,
scanning, drafting) happens silently; this is the surfacing action.

For the hackathon demo this just appends to a local JSONL file, which is
what a human would check. Swap the body of this function for a Slack
webhook POST or an SES `send_email` call to make it a live notification —
the tool's signature and the agent's behavior don't need to change.
"""

import json
import os
from datetime import datetime

from strands import tool

from .memory import is_recently_flagged

OUTBOX_PATH = os.path.join("outbox", "pending_decisions.jsonl")


@tool
def notify_human(
    contract_id: str,
    counterparty: str,
    summary: str,
    recommended_action: str,
    urgency: str = "normal",
) -> dict:
    """Surface a contract decision to the human owner. Use only for contracts that genuinely need a decision — not a status update on every contract reviewed.

    Safe to call even if you're not sure whether this contract was already
    flagged recently — this tool checks for you and no-ops rather than
    duplicating a notification within the cooldown window
    (DECISION_COOLDOWN_DAYS in .env, default 7).

    Args:
        contract_id: The contract this notification is about.
        counterparty: The other party's name (vendor, landlord, employer, ...), for a scannable notification.
        summary: A short (1-3 sentence) explanation of what was found and why
            it matters — assume the human hasn't read the contract recently.
        recommended_action: What the agent recommends doing (e.g. "cancel
            before Oct 1 to avoid the 22% price increase").
        urgency: One of "low", "normal", "high" — how soon the human needs
            to look at this.

    Returns:
        A dict confirming the notification was recorded (notified: True),
        or confirming it was skipped as a within-cooldown duplicate
        (notified: False, skipped_reason: ...).
    """
    cooldown_days = int(os.getenv("DECISION_COOLDOWN_DAYS", "7"))

    if is_recently_flagged(contract_id, cooldown_days=cooldown_days):
        return {
            "notified": False,
            "contract_id": contract_id,
            "skipped_reason": (
                f"Already flagged and notified for {contract_id} within the "
                f"last {cooldown_days} days — not duplicating the notification."
            ),
        }

    os.makedirs(os.path.dirname(OUTBOX_PATH), exist_ok=True)

    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "contract_id": contract_id,
        "counterparty": counterparty,
        "summary": summary,
        "recommended_action": recommended_action,
        "urgency": urgency,
    }

    with open(OUTBOX_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    return {"notified": True, "recorded_at": OUTBOX_PATH, **entry}
