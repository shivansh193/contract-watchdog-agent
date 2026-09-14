"""Tools for spotting cost changes and risky obligation language in a contract.

Works across contract types (vendor/SaaS agreements, leases, employment
contracts, NDAs, service agreements, ...) — the risk-phrase set is general
by default and extended with type-specific phrases when the contract
record has a `contract_type`.
"""

from strands import tool

# Phrases that commonly signal a renewal or obligation trap. Deliberately
# simple/keyword-based — the agent's own reasoning does the nuanced judgment
# call; this tool just gives it concrete, citable evidence to reason over
# (and a real "tool call" for the judges to see, rather than everything
# happening inside one LLM call).
GENERAL_RISK_PHRASES = {
    "automatically renew": "Auto-renews without active opt-in from the counterparty.",
    "auto-renew": "Auto-renews without active opt-in from the counterparty.",
    "sole discretion": "Other party can change terms unilaterally.",
    "without notice": "Other party may act (e.g. change price) without warning.",
    "unilaterally": "Other party can change terms unilaterally.",
    "no refund": "No refund path if you cancel after billing.",
    "non-refundable": "No refund path if you cancel after billing.",
    "written notice": "Cancellation requires formal written notice — easy to miss the window.",
}

TYPE_SPECIFIC_RISK_PHRASES = {
    "lease": {
        "security deposit is non-refundable": "Deposit forfeiture regardless of unit condition.",
        "joint and several liability": "Any one tenant can be held liable for the full amount.",
        "landlord may enter without": "Landlord can enter with little/no notice.",
        "early termination fee": "Breaking the lease early carries a penalty — check the amount.",
    },
    "employment": {
        "non-compete": "Restricts working for competitors after leaving.",
        "at-will": "Employment can be terminated without cause.",
        "assignment of inventions": "Broad IP assignment — check scope (may extend beyond work hours/projects).",
        "no severance": "No severance obligation on termination.",
    },
    "nda": {
        "perpetual": "Confidentiality obligation never expires.",
        "survives termination": "Obligations continue indefinitely after the relationship ends.",
        "liquidated damages": "Pre-set penalty for breach, regardless of actual harm.",
    },
    "vendor_saas": {
        # Covered by GENERAL_RISK_PHRASES already; kept as an explicit,
        # empty override point so a vendor-specific phrase can be added
        # without touching the general set.
    },
}


def _risk_phrases_for(contract_type: str) -> dict:
    phrases = dict(GENERAL_RISK_PHRASES)
    phrases.update(TYPE_SPECIFIC_RISK_PHRASES.get(contract_type, {}))
    return phrases


@tool
def detect_price_changes(contract: dict, threshold_pct: float = 8.0) -> dict:
    """Check whether a contract's price has increased past a threshold since last term.

    Args:
        contract: A single contract record with current_price_monthly_usd and
            previous_price_monthly_usd.
        threshold_pct: Minimum percentage increase to flag as significant.

    Returns:
        A dict with contract_id, previous and current price, the percent
        change, and whether it crosses the threshold.
    """
    current = float(contract.get("current_price_monthly_usd", 0))
    previous = float(contract.get("previous_price_monthly_usd", current))

    pct_change = 0.0 if previous == 0 else ((current - previous) / previous) * 100

    return {
        "contract_id": contract.get("contract_id"),
        "counterparty": contract.get("counterparty"),
        "previous_price_monthly_usd": previous,
        "current_price_monthly_usd": current,
        "pct_change": round(pct_change, 1),
        "flagged": pct_change >= threshold_pct,
    }


@tool
def detect_unfavorable_clauses(contract: dict) -> dict:
    """Scan a contract's text excerpt for known risk language, tuned to its contract_type.

    Args:
        contract: A single contract record with a contract_excerpt field and
            (optionally) a contract_type — "vendor_saas", "lease",
            "employment", or "nda". Unrecognized/missing types fall back to
            the general risk-phrase set only.

    Returns:
        A dict with contract_id and a list of {phrase, reason} matches found
        in the excerpt.
    """
    excerpt = contract.get("contract_excerpt", "").lower()
    phrases = _risk_phrases_for(contract.get("contract_type", ""))
    matches = [
        {"phrase": phrase, "reason": reason}
        for phrase, reason in phrases.items()
        if phrase in excerpt
    ]

    return {
        "contract_id": contract.get("contract_id"),
        "counterparty": contract.get("counterparty"),
        "contract_type": contract.get("contract_type", "general"),
        "risk_matches": matches,
        "risk_count": len(matches),
    }
