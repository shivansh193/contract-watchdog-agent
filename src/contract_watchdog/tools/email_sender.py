"""Real email sending — opt-in, not wired into the agent's default tools.

Unlike mail_ingest.py, this one IS fully implemented (Gmail SMTP with an
app password needs no OAuth flow, so it's cheap to make real rather than
stubbed). It's kept out of ALL_TOOLS by default for the same reason the
system prompt tells the agent to draft-and-notify rather than send
unattended: an agent that can email a real counterparty on your behalf
without a human in the loop is a meaningfully bigger blast radius than one
that drafts and waits, and that's not a decision to default into silently.

To actually let the agent send email:
1. Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_APP_PASSWORD in .env (for
   Gmail: smtp.gmail.com, 587, your address, and an App Password from
   https://myaccount.google.com/apppasswords — not your regular password).
2. Add `send_email` to ALL_TOOLS in tools/__init__.py.
3. Update the system prompt in agent.py to tell the agent it may call
   send_email after notify_human, instead of leaving drafts for manual
   send — and under what conditions (e.g. only after explicit human
   approval recorded some other way, if you want to keep a human in the
   loop rather than fully autonomous sending).
"""

import os
import smtplib
from email.mime.text import MIMEText

from strands import tool


@tool
def send_email(to_address: str, subject: str, body: str) -> dict:
    """Send an email via SMTP using the credentials in .env.

    Not registered as an agent tool by default — see this module's
    docstring for why, and what to change to enable it.

    Args:
        to_address: Recipient email address.
        subject: Email subject line.
        body: Plain-text email body.

    Returns:
        A dict confirming the send, or raising if SMTP credentials are
        missing or the send fails.
    """
    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_APP_PASSWORD"]

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_address

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, password)
        server.sendmail(user, [to_address], msg.as_string())

    return {"sent": True, "to": to_address, "subject": subject}
