from .contracts import load_contracts, scan_for_renewals
from .analysis import detect_price_changes, detect_unfavorable_clauses
from .drafting import draft_email
from .notify import notify_human

ALL_TOOLS = [
    load_contracts,
    scan_for_renewals,
    detect_price_changes,
    detect_unfavorable_clauses,
    draft_email,
    notify_human,
]

__all__ = [
    "load_contracts",
    "scan_for_renewals",
    "detect_price_changes",
    "detect_unfavorable_clauses",
    "draft_email",
    "notify_human",
    "ALL_TOOLS",
]
