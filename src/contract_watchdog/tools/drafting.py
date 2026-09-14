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
        "Could we get 15 minutes this week to talk through options?{reference_line}\n\n"
        "Thanks,\n{owner_name}"
    ),
}


@tool
def draft_email(
    contract: dict,
    decision: str,
    reasoning: str,
    reference_pricing_note: str = "",
) -> dict:
    """Draft a cancellation or renegotiation email for a contract.

    Args:
        contract: The contract record this email is about.
        decision: One of "cancel" or "renegotiate".
        reasoning: A short explanation of why this decision was made — included
            in the returned dict so a human reviewer can see the agent's logic
            alongside the draft, without it being baked into the email text.
        reference_pricing_note: Optional — a general sense of market rate for
            this kind of service, drawn from the model's own knowledge, to
            strengthen a renegotiation ask (e.g. "similar hosting plans in
            this range often run 15-20% lower"). This is NOT verified market
            data — there is no pricing data source wired into this agent —
            so it is inserted into the email as an internal negotiating note
            explicitly labeled unverified, never stated as fact to the
            counterparty. Leave blank if you don't have a reasonable basis
            for one; a fabricated-sounding number is worse than no number.

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

    reference_line = ""
    if reference_pricing_note and decision == "renegotiate":
        reference_line = (
            f"\n\n[Internal note, not for the counterparty — unverified estimate, "
            f"confirm before using in the actual ask: {reference_pricing_note}]"
        )

    fields = {
        "contract_id": contract.get("contract_id", ""),
        "counterparty": contract.get("counterparty", ""),
        "description": contract.get("description", "this agreement"),
        "renewal_date": contract.get("renewal_date", ""),
        "notice_period_days": contract.get("notice_period_days", 0),
        "price_line": price_line,
        "reference_line": reference_line,
        "owner_name": owner_name,
    }

    body = _TEMPLATES[decision].format(**fields)
    subject, _, message = body.partition("\n\n")

    return {
        "contract_id": fields["contract_id"],
        "decision": decision,
        "reasoning": reasoning,
        "reference_pricing_note": reference_pricing_note or None,
        "email_subject": subject.replace("Subject: ", "", 1),
        "email_body": message.strip(),
    }
