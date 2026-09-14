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

    REASON -->|already flagged within cooldown| SKIP2[skip re-notifying —\nrecord_decision only]
    REASON -->|decision: cancel / renegotiate| DE[draft_email\n+ optional caveated\nreference_pricing_note]
    DE --> REASON

    REASON -->|needs a human decision| NH[notify_human]
    REASON -->|routine, no action needed| SKIP[quietly skip —\nno tool call]

    NH --> OUT[outbox/pending_decisions.jsonl]
    NH --> RD[record_decision]
    SKIP2 --> RD
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
- **Decisions persist across runs.** `check_recent_decisions` /
  `record_decision` close a real gap a one-shot batch job would otherwise
  have: without them, running the agent twice over the same contracts
  re-notifies on everything, every time — which quietly turns "autonomous"
  into "spam a human learns to ignore." A cooldown window
  (`DECISION_COOLDOWN_DAYS`) lets an already-handled contract go quiet
  until it's actually due for re-review.
