# Contract Watchdog Agent

**AWS "Agents for Humans" Hackathon — Professional Agents track**

An autonomous legal-obligation assistant that watches every contract a
small business or individual holds — vendor/SaaS subscriptions, leases,
employment agreements, NDAs — catches renewal traps, price hikes, and
risky clauses before they land on your desk, drafts the cancel/renegotiate
email, and only interrupts you when there's a real decision to make. Built
with the [Strands Agents SDK](https://github.com/strands-agents/sdk-python).

## Why this exists

Founders and small teams accumulate contracts of every kind — hosting,
SaaS tools, office leases, employment agreements, NDAs — many of which
silently auto-renew or lock in obligations, often with terms buried in the
fine print. Nobody has time to re-read every contract 30 days before its
deadline. This agent does that job in the background across every
contract type at once, and only surfaces when a human actually needs to
decide something — not on every contract, every day.

## How it works

1. **`load_contracts`** — reads structured contract records (counterparty,
   contract type, price history, renewal date, notice period, and a text
   excerpt of the relevant clause) from `sample_data/contracts/`.
2. **`scan_for_renewals`** — computes which contracts fall inside their
   notice window (i.e. the deadline to cancel/renegotiate is approaching).
3. **`detect_price_changes`** — flags contracts where the current price
   has increased over the previous term, past a configurable threshold
   (skipped for contract types with no recurring price, like an NDA).
4. **`detect_unfavorable_clauses`** — scans the contract excerpt for
   known-risky legal language, using a general risk set plus a
   `contract_type`-specific set (auto-renew traps and no-refund clauses
   for vendor/SaaS; deposit and entry terms for leases; non-competes and
   at-will language for employment; perpetual/survival terms for NDAs).
5. **`draft_email`** — for any contract the agent decides needs action,
   drafts a cancellation or renegotiation email ready for a human to review
   and send. Can optionally include a `reference_pricing_note` — a general
   sense of market rate from the model's own knowledge — but only ever as
   an internal note explicitly labeled *unverified, confirm before using*,
   never stated as fact to the counterparty. There's no real pricing data
   source wired in; pretending otherwise would be worse than omitting it.
6. **`notify_human`** — the one tool that actually interrupts a person.
   The agent is instructed to call this *only* when a real decision is
   needed (imminent deadline + risk found), not for every contract it
   reviews. In this scaffold it writes to `outbox/pending_decisions.jsonl`
   — swap this for a Slack webhook or SES email call for a live demo.

### Memory and trust controls

Two more tools close a real gap: without them, running the agent twice
over the same contracts would re-notify on everything again every time,
which undercuts the "autonomous" pitch — a human learns to ignore repeat
pings fast.

- **`check_recent_decisions`** — called first, every run. Loads what the
  agent already decided recently (`outbox/decision_log.jsonl`) so it
  doesn't waste a full re-analysis on a contract already handled within
  the cooldown window (`DECISION_COOLDOWN_DAYS` in `.env`, default 7).
- **`record_decision`** — called once per contract reviewed, every run
  (flagged or not), so the next run has something to check against.

**The actual enforcement lives in `notify_human` itself, not in the
prompt.** A live two-run test during development caught a real failure
mode: the model saw `check_recent_decisions` correctly return the prior
"flagged_notified" entry, re-notified anyway, and narrated a false
justification for why it was fine ("the timestamp fell outside the
cooldown window" — it hadn't; the two runs were a minute apart). That's
the concrete risk of relying on prompting alone for something that needs
to actually be reliable. The fix: `notify_human` now checks
`is_recently_flagged()` itself before writing anything, and no-ops on a
within-cooldown duplicate regardless of what the model decides to do —
verified with a regression test (`test_notify_human_blocks_duplicate_within_cooldown`)
and re-confirmed live: a second run correctly logged 2 contracts as
already-known/deduplicated instead of re-notifying.

`MIN_FLAG_VALUE_USD` (`.env`) sets a dollar floor: contracts below it only
get surfaced for high-confidence risk (2+ matched clauses, or a real
consequence like an NDA expiring), not a single keyword match on a
trivial subscription. Set it to `0` (default) to judge purely on risk,
ignoring price.

`mail_ingest.py` documents (but does not implement) pulling new contracts
straight from Gmail/Outlook/IMAP instead of a local folder — see that
file's docstring for why it's an intentional extension point rather than a
live integration in this submission, and what wiring it up for real looks
like. `email_sender.py` is the opposite case: a fully working SMTP sender
(Gmail app-password auth, no OAuth needed) that's deliberately *not*
registered as a default agent tool — an agent that can email a real
counterparty unattended is a meaningfully bigger blast radius than one
that drafts and waits for a human to hit send, and that's not a decision
to default into silently. See that file's docstring to enable it.

The agent runs the whole loop end-to-end from one prompt: "review the
contracts, handle what needs handling, only bother me with real decisions."
That's the core thing the hackathon is judging for — see
[the brief](https://agentsforhumans.devpost.com/) itself: *"Instead of
another app people open and manage, the agent runs autonomously and only
surfaces when there's a real decision to make."*

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in credentials for **one** model
provider (Gemini is the default — free tier, no card required):

```bash
copy .env.example .env
```

Generate fresh sample data (dates are computed relative to *today* so the
demo always has a contract that's urgently due):

```bash
python scripts/generate_sample_data.py
```

Run the agent:

```bash
python -m contract_watchdog.main
```

Check what it decided to do:

```bash
type outbox\pending_decisions.jsonl
```

## Model provider

Set `MODEL_PROVIDER` in `.env` to one of:

| Value | Provider | Cost | Setup |
|---|---|---|---|
| `gemini` (default) | Google Gemini (`gemini-flash-lite-latest`) | **Free tier, no card.** The flagship `gemini-3.6-flash` is capped at 20 requests/**day** on the free tier — not enough for one full run of this agent (needs 15-20+ model turns across 5 contracts). The `-lite` tier carries much more free headroom and is what this project is actually verified against; swap `GEMINI_MODEL_ID` if you want the flagship model instead | API key from [aistudio.google.com](https://aistudio.google.com/apikey) |
| `bedrock` | AWS Bedrock (Claude) | Pay-per-token (cents for a demo) | AWS credentials with `bedrock:InvokeModel` |
| `ollama` | Local open model | Free, no quota, runs on your machine | [ollama.com](https://ollama.com) + `ollama pull llama3` |

Using Bedrock is a nice-to-have for the "built on AWS" story in the demo
video, not a requirement — the hackathon only requires the **Strands
Agents SDK**, not a specific model backend. If you hit the Gemini daily
cap while testing, a second free key from a different Google account
gets its own separate quota — faster than waiting for reset.

## Portfolio dashboard (frontend/)

A real Next.js app for the same agent output — a two-tab view (Portfolio /
Audit Trail) showing flagged vs. reviewed contracts, matched risk clauses,
drafted emails with an Approve & Send interaction, and a full audit trail
of every decision the agent made.

It's genuinely wired to real data: a React Server Component reads
`outbox/portfolio_snapshot.json` straight off disk at request time — no
mocked content. That snapshot is built by `scripts/build_portfolio_snapshot.py`,
which joins the deterministic tool output (price/risk detection) with
what the agent actually decided and the real email text it drafted.

```bash
# after running the agent at least once (python -m contract_watchdog.main):
python scripts/build_portfolio_snapshot.py

cd frontend
npm install
npm run dev
# open http://localhost:3000
```

Re-run the snapshot script (and refresh the page — it always reads fresh
from disk, no caching) any time you want the dashboard to reflect a new
agent run.

## Project structure

```
contract-watchdog-agent/
├── src/contract_watchdog/
│   ├── agent.py             # builds the Strands Agent + system prompt
│   ├── main.py               # CLI entrypoint
│   └── tools/
│       ├── contracts.py      # load_contracts, scan_for_renewals
│       ├── analysis.py       # detect_price_changes, detect_unfavorable_clauses
│       ├── drafting.py       # draft_email (+ reference_pricing_note)
│       ├── notify.py         # notify_human (the "surface to a human" tool)
│       ├── memory.py         # check_recent_decisions, record_decision
│       ├── mail_ingest.py    # Gmail/Outlook/IMAP extension point (not live)
│       └── email_sender.py   # real SMTP send, opt-in, not a default tool
├── scripts/
│   ├── generate_sample_data.py
│   └── build_portfolio_snapshot.py   # real data pipeline behind the dashboard
├── frontend/                 # Next.js portfolio dashboard (reads outbox/portfolio_snapshot.json)
├── sample_data/contracts/    # generated demo contracts
├── outbox/                   # notify_human + decision_log + portfolio_snapshot
├── deploy/agentcore/         # optional Bedrock AgentCore deployment notes
└── tests/test_tools.py
```

## Business model (for the pitch, not the code)

Charge a percentage of dollars actually renegotiated or saved, not a flat
subscription — "we only make money when we save you money." Incentive-
aligned, and it's a strong one-liner for a demo close. Distribution: sell
through fractional CFOs and bookkeeping firms (Bench/Pilot-style) as a
feature they offer their existing clients, rather than direct-to-founder
acquisition from scratch.

## Submission checklist

See [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md).

## License

MIT — see [LICENSE](LICENSE).
