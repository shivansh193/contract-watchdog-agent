"""Unit tests for the watchdog tools — no model/API key needed.

@tool-wrapped functions stay directly callable with their original
signature, so these call them the same way the agent's own reasoning
would, just without a model in the loop.
"""

import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from contract_watchdog.tools.analysis import detect_price_changes, detect_unfavorable_clauses
from contract_watchdog.tools.contracts import scan_for_renewals


def _future(days: int) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


def test_scan_for_renewals_flags_close_deadline():
    contracts = [
        {
            "contract_id": "A",
            "renewal_date": _future(10),
            "notice_period_days": 5,
        },
        {
            "contract_id": "B",
            "renewal_date": _future(300),
            "notice_period_days": 30,
        },
    ]

    due = scan_for_renewals(contracts, within_days=45)

    assert [c["contract_id"] for c in due] == ["A"]
    assert due[0]["days_until_notice_deadline"] == 5


def test_detect_price_changes_flags_increase_past_threshold():
    contract = {
        "contract_id": "A",
        "counterparty": "CloudHost",
        "current_price_monthly_usd": 1450,
        "previous_price_monthly_usd": 1100,
    }

    result = detect_price_changes(contract, threshold_pct=8.0)

    assert result["flagged"] is True
    assert result["pct_change"] > 8.0


def test_detect_price_changes_ignores_small_increase():
    contract = {
        "contract_id": "B",
        "current_price_monthly_usd": 91,
        "previous_price_monthly_usd": 89,
    }

    result = detect_price_changes(contract, threshold_pct=8.0)

    assert result["flagged"] is False


def test_detect_unfavorable_clauses_finds_known_risk_language():
    contract = {
        "contract_id": "A",
        "contract_excerpt": (
            "This Agreement shall automatically renew unless the customer "
            "provides written notice. Fees are non-refundable."
        ),
    }

    result = detect_unfavorable_clauses(contract)

    phrases = {m["phrase"] for m in result["risk_matches"]}
    assert "automatically renew" in phrases
    assert "non-refundable" in phrases
    assert result["risk_count"] >= 2


def test_detect_unfavorable_clauses_clean_contract_has_no_matches():
    contract = {
        "contract_id": "B",
        "contract_excerpt": "This Agreement renews annually at a fixed price.",
    }

    result = detect_unfavorable_clauses(contract)

    assert result["risk_count"] == 0


def test_detect_unfavorable_clauses_applies_type_specific_phrases():
    lease = {
        "contract_id": "L1",
        "contract_type": "lease",
        "contract_excerpt": (
            "Tenant's security deposit is non-refundable. Landlord may enter "
            "without notice."
        ),
    }

    result = detect_unfavorable_clauses(lease)

    phrases = {m["phrase"] for m in result["risk_matches"]}
    assert "security deposit is non-refundable" in phrases
    assert "landlord may enter without" in phrases
