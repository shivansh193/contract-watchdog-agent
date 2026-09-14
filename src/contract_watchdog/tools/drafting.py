"""Tool for turning a decision into a ready-to-send email draft.

Covers the two actions that make sense across contract types: canceling
before an auto-renewal locks in, or opening a renegotiation conversation
(price, terms, or a flagged clause). For contract types where "send an
email" isn't the right next step (e.g. an NDA nearing the end of its
confidentiality term), the agent is expected to use notify_human directly
with its recommendation instead of calling this tool.
"""

from strands import tool

_TEMPLATES = {
    "cancel": (
        "Subject: Notice of Non-Renewal — {contract_id}\n\n"
        "Hi {counterparty} team,\n\n"
        "Please treat this as formal written notice that we will not be renewing "
        "{description} (contract {contract_id}), effective at the end of the current term "
        "({renewal_date}). Per the notice terms in our agreement, we understand this "
        "notice satisfies the {notice_period_days}-day requirement.\n\n"
        "Please confirm receipt and the effective cancellation date.\n\n"
        "Thanks,\n{owner_name}"
    ),
    "renegotiate": (
        "Subject: Renewal Terms for {contract_id} — Requesting a Call\n\n"
        "Hi {counterparty} team,\n\n"
        "Our {description} agreement ({contract_id}) is coming up for renewal on "
        "{renewal_date}.{price_line} Before we renew, we'd like to discuss the terms. "
        "Could we get 15 minutes this week to talk through options?\n\n"
        "Thanks,\n{owner_name}"
    ),
}


@tool
def draft_email(contract: dict, decision: str, reasoning: str) -> dict:
    """Draft a cancellation or renegotiation email for a contract.

    Args:
        contract: The contract record this email is about.
        decision: One of "cancel" or "renegotiate".
        reasoning: A short explanation of why this decision was made — included
            in the returned dict so a human reviewer can see the agent's logic
            alongside the draft, without it being baked into the email text.

    Returns:
        A dict with the drafted subject/body and the reasoning behind it.
    """
    if decision not in _TEMPLATES:
        raise ValueError(f"decision must be one of {list(_TEMPLATES)}, got {decision!r}")

    owner_email = contract.get("owner_email", "")
    owner_name = owner_email.split("@")[0].replace(".", " ").title() or "Team"

    previous_price = float(contract.get("previous_price_monthly_usd", 0))
    current_price = float(contract.get("current_price_monthly_usd", 0))
    price_line = ""
    if current_price and previous_price and current_price != previous_price:
        price_line = (
            f" We've noticed the price has moved from ${previous_price:.0f}/mo "
            f"to ${current_price:.0f}/mo."
        )

    fields = {
        "contract_id": contract.get("contract_id", ""),
        "counterparty": contract.get("counterparty", ""),
        "description": contract.get("description", "this agreement"),
        "renewal_date": contract.get("renewal_date", ""),
        "notice_period_days": contract.get("notice_period_days", 0),
        "price_line": price_line,
        "owner_name": owner_name,
    }

    body = _TEMPLATES[decision].format(**fields)
    subject, _, message = body.partition("\n\n")

    return {
        "contract_id": fields["contract_id"],
        "decision": decision,
        "reasoning": reasoning,
        "email_subject": subject.replace("Subject: ", "", 1),
        "email_body": message.strip(),
    }
