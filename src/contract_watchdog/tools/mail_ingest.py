"""Extension point: pulling new contracts out of a real inbox.

NOT wired into the agent's default tool set (see tools/__init__.py) and NOT
live for this hackathon submission. Real inbox access needs a per-provider
OAuth consent flow (Gmail API, Microsoft Graph for Outlook, or a plain IMAP
login) — fragile to demo live on a deadline, and orthogonal to what's
actually being judged here (the autonomous decision loop, not inbox
plumbing). This module exists so that story is architecturally real, not
just claimed: the interface below is what load_contracts would sit behind
once wired up, and each _fetch_from_* function is a clearly-marked seam
where a real provider integration drops in.

To make this live post-hackathon:
1. Implement one _fetch_from_<provider> function using that provider's SDK
   (google-api-python-client for Gmail, msgraph-sdk for Outlook, imaplib
   for generic IMAP).
2. Have it return contract dicts in the same shape load_contracts produces
   (see contracts.py's docstring for the expected fields).
3. Register fetch_contract_attachments_from_inbox in tools/__init__.py's
   ALL_TOOLS so the agent can call it directly instead of (or alongside)
   load_contracts.
"""

from strands import tool

SUPPORTED_PROVIDERS = {"gmail", "outlook", "imap"}


def _fetch_from_gmail(mailbox: str, lookback_days: int) -> list[dict]:
    """Seam for the Gmail API (google-api-python-client, OAuth 2.0). Not implemented."""
    raise NotImplementedError("Wire up google-api-python-client here.")


def _fetch_from_outlook(mailbox: str, lookback_days: int) -> list[dict]:
    """Seam for Microsoft Graph (msgraph-sdk, OAuth 2.0). Not implemented."""
    raise NotImplementedError("Wire up msgraph-sdk here.")


def _fetch_from_imap(mailbox: str, lookback_days: int) -> list[dict]:
    """Seam for generic IMAP (imaplib, app password or OAuth2 SASL). Not implemented."""
    raise NotImplementedError("Wire up imaplib here.")


_PROVIDER_FETCHERS = {
    "gmail": _fetch_from_gmail,
    "outlook": _fetch_from_outlook,
    "imap": _fetch_from_imap,
}


@tool
def fetch_contract_attachments_from_inbox(provider: str, mailbox: str, lookback_days: int = 30) -> dict:
    """Find new contract documents (PDF/DOCX attachments) in an inbox and parse them into contract records.

    NOT implemented for this hackathon submission — see module docstring.
    Left in the codebase (and out of the agent's default tools) as the
    documented next integration step for turning this into a true
    all-in-one legal assistant that doesn't require manually dropping
    contract JSON into a folder.

    Args:
        provider: One of "gmail", "outlook", "imap".
        mailbox: The mailbox/email address to scan.
        lookback_days: How many days back to search for new attachments.

    Returns:
        A dict describing why this is a stub, and what load_contracts to
        use instead for the current demo.
    """
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(f"provider must be one of {sorted(SUPPORTED_PROVIDERS)}, got {provider!r}")

    return {
        "provider": provider,
        "mailbox": mailbox,
        "lookback_days": lookback_days,
        "status": "not_implemented",
        "note": (
            "Mail ingestion is an architected extension point, not wired up "
            "live for this hackathon build (see mail_ingest.py docstring for "
            "why). Use load_contracts against sample_data/contracts/ for now."
        ),
    }
