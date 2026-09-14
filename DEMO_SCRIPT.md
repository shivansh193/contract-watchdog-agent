# Demo Script — Contract Watchdog

Target: ~4 minutes. Cut steps 6-7 if you're tight on time — steps 1-5 alone are a complete, honest demo.

**Folder:** `C:\Development\contract-watchdog-agent`
**Dashboard:** `http://localhost:3000` (already running — just open it)

---

## 1. The problem (10s)

> "Contracts silently auto-renew with price hikes buried in the fine print, and nobody has time to re-read every contract 30 days before the deadline."

## 2. Run the agent live (on camera)

```bash
python -m contract_watchdog.main
```

While it runs, narrate:
> "It's loading contracts across four types — vendor/SaaS, lease, employment, NDA — checking which ones have a notice deadline coming up, and analyzing each for price changes and risky clause language."

## 3. Show the terminal summary

Point out it reviewed 5 contracts and only flagged 2. Then the key line:

> "Notice it correctly *skipped* SignalCRM — it has risky clause language, but the price is unchanged and the deadline is 90 days out. That's judgment, not keyword matching."

## 4. Switch to the dashboard (`http://localhost:3000`)

- Walk through the "This week" section: CloudHost's 31.8% price hike, the matched risk clauses, the real drafted email
- Click **Approve & Send** — show the state change to "✓ Approved, queued to send"
- Scroll to "Reviewed — no action needed" — show the three quiet ones
- Click the **Audit Trail** tab — show the full chronological log with real reasoning for every contract, flagged and skipped

Say once: *"This is reading real output from the run I just did — not mock data."*

## 5. Close on the core idea

> "Every tool except `notify_human` is invisible background work. The agent decides on its own when a contract actually needs a human — that's the difference between an autonomous agent and a chatbot that waits to be asked."

---

## 6. (Optional, if time allows) Run it a second time, live

```bash
python -m contract_watchdog.main
```

Show it does **NOT** re-notify on CloudHost or Meridian — they're already flagged. This proves the agent has memory across runs (`check_recent_decisions` / `record_decision`), not just within one session. Refresh the dashboard afterward if you want to show the Audit Trail picked up the new "already-known" entries.

## 7. (Optional) Architecture diagram

10 seconds on `ARCHITECTURE.md`'s diagram — one sentence on why only `notify_human` interrupts a person.

---

## If something goes sideways

- **Gemini rate limit hit mid-run:** the SDK auto-retries with backoff — just let it sit for ~10-15s, it recovers on its own. Don't restart.
- **Dashboard shows stale/old data:** run `python scripts/build_portfolio_snapshot.py`, then refresh the page (no server restart needed — it reads fresh from disk every request).
- **Want a completely clean run:** `rm outbox/*.jsonl outbox/*.json` first, then step 2.
