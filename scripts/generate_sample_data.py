"""Generate demo contract records with dates relative to today.

Run this right before a demo/recording so the "urgent" contract is always
genuinely inside its notice window, no matter what day you present.

Spans multiple contract types on purpose — vendor/SaaS, lease, employment,
NDA — to demonstrate the agent isn't hardcoded to one kind of agreement.
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
        "contract_type": "vendor_saas",
        "counterparty": "CloudHost Inc.",
        "contract_id": "CH-2024-118",
        "description": "production cloud hosting",
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
        "contract_type": "vendor_saas",
        "counterparty": "Northwind Payroll",
        "contract_id": "NP-2025-002",
        "description": "payroll processing",
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
        "contract_type": "vendor_saas",
        "counterparty": "SignalCRM",
        "contract_id": "SC-2026-044",
        "description": "CRM platform",
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
    {
        # Should get flagged: office lease, no price field, but a tight notice
        # window plus real lease-specific risk language.
        "contract_type": "lease",
        "counterparty": "Meridian Properties LLC",
        "contract_id": "LEASE-2023-07",
        "description": "office space lease, Suite 400",
        "current_price_monthly_usd": 0,
        "previous_price_monthly_usd": 0,
        "renewal_date": _future(35),
        "auto_renew": True,
        "notice_period_days": 30,
        "contract_excerpt": (
            "Lease renews automatically for a one-year term. Tenant's security "
            "deposit is non-refundable upon renewal. Landlord may enter without "
            "notice for inspection purposes. Early termination fee equal to two "
            "months' rent applies."
        ),
        "owner_email": "founder@example.com",
    },
    {
        # Should NOT get flagged: NDA with a distant, low-risk expiry.
        "contract_type": "nda",
        "counterparty": "Anthea Design Studio",
        "contract_id": "NDA-2026-011",
        "description": "mutual NDA for contract design work",
        "current_price_monthly_usd": 0,
        "previous_price_monthly_usd": 0,
        "renewal_date": _future(400),
        "auto_renew": False,
        "notice_period_days": 0,
        "contract_excerpt": (
            "Confidential information disclosed under this Agreement shall "
            "remain confidential for a period of two (2) years following "
            "disclosure. Either party may terminate this Agreement with 30 "
            "days notice."
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
