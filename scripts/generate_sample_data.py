"""Generate demo contract records with dates relative to today.

Run this right before a demo/recording so the "urgent" contract is always
genuinely inside its notice window, no matter what day you present.
"""

import json
import os
from datetime import date, timedelta

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_data", "contracts")


def _future(days: int) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


CONTRACTS = [
    {
        # Should get flagged: price hike + auto-renew trap language + deadline is close.
        "vendor": "CloudHost Inc.",
        "contract_id": "CH-2024-118",
        "service": "Production cloud hosting",
        "current_price_monthly_usd": 1450,
        "previous_price_monthly_usd": 1100,
        "renewal_date": _future(20),
        "auto_renew": True,
        "notice_period_days": 15,
        "contract_excerpt": (
            "This Agreement shall automatically renew for successive one-year "
            "terms unless either party provides written notice at least fifteen "
            "(15) days prior to the renewal date. Vendor may, in its sole "
            "discretion, adjust pricing for the renewal term without notice."
        ),
        "owner_email": "founder@example.com",
    },
    {
        # Should NOT get flagged: routine renewal, flat price, plain terms, far off.
        "vendor": "Northwind Payroll",
        "contract_id": "NP-2025-002",
        "service": "Payroll processing",
        "current_price_monthly_usd": 89,
        "previous_price_monthly_usd": 89,
        "renewal_date": _future(210),
        "auto_renew": True,
        "notice_period_days": 30,
        "contract_excerpt": (
            "This Agreement renews annually. Either party may cancel by "
            "providing thirty (30) days written notice prior to renewal. "
            "Pricing is fixed for the term of this Agreement."
        ),
        "owner_email": "founder@example.com",
    },
    {
        # Borderline: risky language present, but no price change and deadline is far out.
        # Good test of the agent's judgment, not just its keyword matching.
        "vendor": "SignalCRM",
        "contract_id": "SC-2026-044",
        "service": "CRM platform",
        "current_price_monthly_usd": 240,
        "previous_price_monthly_usd": 240,
        "renewal_date": _future(150),
        "auto_renew": True,
        "notice_period_days": 60,
        "contract_excerpt": (
            "Subscription automatically renews. Fees are non-refundable. "
            "Vendor reserves the right to modify these terms unilaterally "
            "with notice posted to the Vendor's website."
        ),
        "owner_email": "founder@example.com",
    },
]


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    for contract in CONTRACTS:
        path = os.path.join(OUT_DIR, f"{contract['contract_id']}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(contract, f, indent=2)
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
