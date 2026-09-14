# Architecture

```mermaid
flowchart TD
    subgraph Input
        A[sample_data/contracts/*.json]
        M["fetch_contract_attachments_from_inbox\n(Gmail / Outlook / IMAP — extension point,\nnot wired up for this submission)"]
    end

    CRD[check_recent_decisions\ndecision_log.jsonl] --> REASON{Agent reasoning\nStrands Agents SDK}

    A --> LC[load_contracts]
    M -.future path.-> LC

    LC --> SR[scan_for_renewals]
    SR -->|contracts within notice window| REASON

    REASON --> PC[detect_price_changes]
    REASON --> UC[detect_unfavorable_clauses\ntype-aware: vendor_saas / lease / employment / nda]
    PC --> REASON
    UC --> REASON

    REASON -->|decision: cancel / renegotiate| DE[draft_email\n+ optional caveated\nreference_pricing_note]
    DE --> REASON

    REASON -->|needs a human decision| NH{notify_human\nis_recently_flagged() guard}
    REASON -->|routine, no action needed| SKIP[quietly skip —\nno tool call]

    NH -->|not a recent duplicate| OUT[outbox/pending_decisions.jsonl]
    NH -->|already flagged within cooldown\nblocked regardless of model reasoning| SKIP2[no-op —\nnot re-written]
    NH --> RD[record_decision]
    SKIP --> RD
    RD --> LOG[outbox/decision_log.jsonl]

    style SKIP fill:transparent,stroke-dasharray: 5 5
    style SKIP2 fill:transparent,stroke-dasharray: 5 5
```

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
