# Architecture

![Architecture diagram](architecture.svg)

## Why it's shaped this way

- **Every tool except `notify_human` is invisible background work.** The
  hackathon brief's core requirement is an agent that "runs autonomously
  and only surfaces when there's a real decision to make" — so the
  architecture makes `notify_human` the single chokepoint a human ever
  sees, and puts the judgment call about *when* to use it inside the
  agent's own reasoning (system prompt), not hardcoded business logic.
- **Analysis tools are type-aware, not type-specific.** `detect_unfavorable_clauses`
  takes a general risk-phrase set and layers on a `contract_type`-specific
  set (lease/employment/nda/vendor_saas) rather than branching into
  separate code paths per contract type — one agent handles every kind of
  agreement.
- **Ingestion is decoupled from the reasoning loop.** `load_contracts`
  reads from a local directory today; `mail_ingest.py` documents the same
  shape for a real inbox (Gmail/Outlook/IMAP) as a drop-in replacement,
  without needing to touch `scan_for_renewals` or anything downstream.
- **Model provider is swappable**, not hardcoded to Bedrock — `agent.py`
  builds whichever provider `MODEL_PROVIDER` selects (Gemini by default,
  Bedrock for the optional AgentCore deployment path, or local Ollama).
- **Decisions persist across runs, and the guard is in the tool, not the
  prompt.** `check_recent_decisions` / `record_decision` close a real gap
  a one-shot batch job would otherwise have: without them, running the
  agent twice over the same contracts re-notifies on everything, every
  time. The system prompt tells the agent to check first — but a live
  test proved that instruction alone isn't reliable: the model saw the
  prior decision, re-notified anyway, and narrated a false justification
  for doing so. `notify_human` now enforces the cooldown itself
  (`is_recently_flagged()`), so a duplicate notification is blocked
  regardless of what the model's reasoning concludes.
