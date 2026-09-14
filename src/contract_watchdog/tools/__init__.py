from .contracts import load_contracts, scan_for_renewals
from .analysis import detect_price_changes, detect_unfavorable_clauses
from .drafting import draft_email
from .notify import notify_human
from .memory import check_recent_decisions, record_decision

ALL_TOOLS = [
    check_recent_decisions,
    load_contracts,
    scan_for_renewals,
    detect_price_changes,
    detect_unfavorable_clauses,
    draft_email,
    notify_human,
    record_decision,
]

__all__ = [
    "load_contracts",
    "scan_for_renewals",
    "detect_price_changes",
    "detect_unfavorable_clauses",
    "draft_email",
    "notify_human",
    "check_recent_decisions",
    "record_decision",
    "ALL_TOOLS",
]
