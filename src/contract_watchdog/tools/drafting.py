"""Tool for turning a decision into a ready-to-send email draft."""

from strands import tool

_TEMPLATES = {
    "cancel": (
        "Subject: Notice of Non-Renewal — {contract_id}\n\n"
        "Hi {vendor} team,\n\n"
        "Please treat this as formal written notice that we will not be renewing "
        "{service} (contract {contract_id}), effective at the end of the current term "
        "({renewal_date}). Per the notice terms in our agreement, we understand this "
        "notice satisfies the {notice_period_days}-day requirement.\n\n"
        "Please confirm receipt and the effective cancellation date.\n\n"
        "Thanks,\n{owner_name}"
    ),
    "renegotiate": (
        "Subject: Renewal Terms for {contract_id} — Requesting a Call\n\n"
        "Hi {vendor} team,\n\n"
        "Our {service} contract ({contract_id}) is coming up for renewal on "
        "{renewal_date}. We've noticed the price has moved from "
        "${previous_price_monthly_usd:.0f}/mo to ${current_price_monthly_usd:.0f}/mo, "
        "and before we renew we'd like to discuss the new terms. Could we get 15 "
        "minutes this week to talk through options?\n\n"
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

    fields = {
        "contract_id": contract.get("contract_id", ""),
        "vendor": contract.get("vendor", ""),
        "service": contract.get("service", ""),
        "renewal_date": contract.get("renewal_date", ""),
        "notice_period_days": contract.get("notice_period_days", 0),
        "previous_price_monthly_usd": float(contract.get("previous_price_monthly_usd", 0)),
        "current_price_monthly_usd": float(contract.get("current_price_monthly_usd", 0)),
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
