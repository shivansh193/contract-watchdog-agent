# Contract Watchdog Agent

**AWS "Agents for Humans" Hackathon — Professional Agents track**

An autonomous agent that watches your vendor/SaaS contracts, catches renewal
traps and price hikes before they land on your card, drafts the
cancel/renegotiate email, and only interrupts you when there's a real
decision to make. Built with the [Strands Agents SDK](https://github.com/strands-agents/sdk-python).

## Why this exists

Founders and small teams rack up vendor contracts (hosting, SaaS tools,
payment processors) that silently auto-renew, often with price increases
buried in the fine print. Nobody has time to re-read every contract 30 days
before its renewal date. This agent does that job in the background and
only surfaces when a human actually needs to decide something — not on
every contract, every day.

## How it works

1. **`load_contracts`** — reads structured contract records (vendor, price
   history, renewal date, notice period, and a text excerpt of the
   renewal/pricing clause) from `sample_data/contracts/`.
2. **`scan_for_renewals`** — computes which contracts fall inside their
   notice window (i.e. the deadline to cancel/renegotiate is approaching).
3. **`detect_price_changes`** — flags contracts where the current price
   has increased over the previous term, past a configurable threshold.
4. **`detect_unfavorable_clauses`** — scans the contract excerpt for
   known-risky legal language (auto-renew traps, unilateral price changes,
   no-refund clauses, silent-consent windows).
5. **`draft_email`** — for any contract the agent decides needs action,
   drafts a cancellation or renegotiation email ready for a human to review
   and send.
6. **`notify_human`** — the one tool that actually interrupts a person.
   The agent is instructed to call this *only* when a real decision is
   needed (imminent deadline + risk found), not for every contract it
   reviews. In this scaffold it writes to `outbox/pending_decisions.jsonl`
   — swap this for a Slack webhook or SES email call for a live demo.

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
| `gemini` (default) | Google Gemini 2.5 Flash | **Free tier, no card** | API key from [aistudio.google.com](https://aistudio.google.com/apikey) |
| `bedrock` | AWS Bedrock (Claude) | Pay-per-token (cents for a demo) | AWS credentials with `bedrock:InvokeModel` |
| `ollama` | Local open model | Free, runs on your machine | [ollama.com](https://ollama.com) + `ollama pull llama3` |

Using Bedrock is a nice-to-have for the "built on AWS" story in the demo
video, not a requirement — the hackathon only requires the **Strands
Agents SDK**, not a specific model backend.

## Project structure

```
contract-watchdog-agent/
├── src/contract_watchdog/
│   ├── agent.py            # builds the Strands Agent + system prompt
│   ├── main.py              # CLI entrypoint
│   └── tools/
│       ├── contracts.py     # load_contracts, scan_for_renewals
│       ├── analysis.py      # detect_price_changes, detect_unfavorable_clauses
│       ├── drafting.py      # draft_email
│       └── notify.py        # notify_human (the "surface to a human" tool)
├── scripts/generate_sample_data.py
├── sample_data/contracts/   # generated demo contracts
├── outbox/                  # where notify_human writes flagged decisions
├── deploy/agentcore/        # optional Bedrock AgentCore deployment notes
└── tests/test_tools.py
```

## Submission checklist

See [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md).

## License

MIT — see [LICENSE](LICENSE).
