"""Unit tests for the watchdog tools — no model/API key needed.

@tool-wrapped functions stay directly callable with their original
signature, so these call them the same way the agent's own reasoning
would, just without a model in the loop.
"""

import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from contract_watchdog.tools.analysis import detect_price_changes, detect_unfavorable_clauses
from contract_watchdog.tools.contracts import scan_for_renewals
from contract_watchdog.tools.drafting import draft_email
import contract_watchdog.tools.memory as memory


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


def test_draft_email_reference_pricing_note_is_labeled_unverified():
    contract = {
        "contract_id": "A",
        "counterparty": "CloudHost",
        "description": "hosting",
        "renewal_date": "2026-10-04",
        "current_price_monthly_usd": 1450,
        "previous_price_monthly_usd": 1100,
        "owner_email": "founder@example.com",
    }

    result = draft_email(
        contract,
        decision="renegotiate",
        reasoning="price hike",
        reference_pricing_note="similar hosting plans often run 15-20% lower",
    )

    assert "unverified" in result["email_body"].lower()
    assert "not for the counterparty" in result["email_body"].lower()
    assert result["reference_pricing_note"] == "similar hosting plans often run 15-20% lower"


def test_draft_email_omits_reference_block_when_not_given():
    contract = {
        "contract_id": "A",
        "counterparty": "CloudHost",
        "description": "hosting",
        "renewal_date": "2026-10-04",
        "owner_email": "founder@example.com",
    }

    result = draft_email(contract, decision="renegotiate", reasoning="price hike")

    assert "unverified" not in result["email_body"].lower()
    assert result["reference_pricing_note"] is None


def test_decision_memory_roundtrip(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(memory, "DECISION_LOG_PATH", str(tmp_path / "outbox" / "decision_log.jsonl"))

    assert memory.check_recent_decisions(cooldown_days=7) == []

    record_decision_fn = memory.record_decision
    result = record_decision_fn("C1", "flagged_notified", notes="price hike")
    assert result["recorded"] is True

    recent = memory.check_recent_decisions(cooldown_days=7)
    assert len(recent) == 1
    assert recent[0]["contract_id"] == "C1"
    assert recent[0]["decision"] == "flagged_notified"


def test_decision_memory_respects_cooldown_window(tmp_path, monkeypatch):
    log_path = tmp_path / "outbox" / "decision_log.jsonl"
    log_path.parent.mkdir(parents=True)
    old_entry = {
        "timestamp": (datetime.now() - timedelta(days=30)).isoformat(timespec="seconds"),
        "contract_id": "C1",
        "decision": "flagged_notified",
        "notes": "",
    }
    log_path.write_text(json.dumps(old_entry) + "\n", encoding="utf-8")
    monkeypatch.setattr(memory, "DECISION_LOG_PATH", str(log_path))

    recent = memory.check_recent_decisions(cooldown_days=7)

    assert recent == []


def test_decision_memory_keeps_only_latest_per_contract(tmp_path, monkeypatch):
    log_path = tmp_path / "outbox" / "decision_log.jsonl"
    log_path.parent.mkdir(parents=True)
    now = datetime.now()
    entries = [
        {"timestamp": (now - timedelta(days=2)).isoformat(timespec="seconds"), "contract_id": "C1", "decision": "reviewed_no_action", "notes": ""},
        {"timestamp": (now - timedelta(hours=1)).isoformat(timespec="seconds"), "contract_id": "C1", "decision": "flagged_notified", "notes": ""},
    ]
    log_path.write_text("\n".join(json.dumps(e) for e in entries) + "\n", encoding="utf-8")
    monkeypatch.setattr(memory, "DECISION_LOG_PATH", str(log_path))

    recent = memory.check_recent_decisions(cooldown_days=7)

    assert len(recent) == 1
    assert recent[0]["decision"] == "flagged_notified"
