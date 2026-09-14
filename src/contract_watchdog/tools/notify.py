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

OUTBOX_PATH = os.path.join("outbox", "pending_decisions.jsonl")


@tool
def notify_human(
    contract_id: str,
    vendor: str,
    summary: str,
    recommended_action: str,
    urgency: str = "normal",
) -> dict:
    """Surface a contract decision to the human owner. Use only for contracts that genuinely need a decision — not a status update on every contract reviewed.

    Args:
        contract_id: The contract this notification is about.
        vendor: The vendor name, for a scannable notification.
        summary: A short (1-3 sentence) explanation of what was found and why
            it matters — assume the human hasn't read the contract recently.
        recommended_action: What the agent recommends doing (e.g. "cancel
            before Oct 1 to avoid the 22% price increase").
        urgency: One of "low", "normal", "high" — how soon the human needs
            to look at this.

    Returns:
        A dict confirming the notification was recorded, with a path to
        where a human can review it.
    """
    os.makedirs(os.path.dirname(OUTBOX_PATH), exist_ok=True)

    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "contract_id": contract_id,
        "vendor": vendor,
        "summary": summary,
        "recommended_action": recommended_action,
        "urgency": urgency,
    }

    with open(OUTBOX_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    return {"notified": True, "recorded_at": OUTBOX_PATH, **entry}
