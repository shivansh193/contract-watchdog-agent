# Submission checklist — Agents for Humans (Professional Agents track)

Pulled directly from the [hackathon's submission requirements](https://agentsforhumans.devpost.com/).

- [ ] **Text description** — what the project does, who it's for, how it works
- [ ] **Public GitHub repo URL** — currently **private**:
      https://github.com/shivansh193/contract-watchdog-agent
      → flip to public in Settings → Danger Zone before submitting
- [ ] **MIT or Apache license visible in the repo's "About" section** —
      LICENSE file is in place (MIT); GitHub should pick it up
      automatically once the repo is public. Verify the About sidebar
      actually shows it.
- [ ] **README** — done ([README.md](README.md))
- [ ] **Architecture diagram** — done ([ARCHITECTURE.md](ARCHITECTURE.md),
      mermaid — render/screenshot it if the submission form wants an image)
- [ ] **Demo video, ≤5 minutes**, must cover:
  - [ ] The problem you're solving
  - [ ] Who it's for
  - [ ] Why it matters
  - [ ] The project working end-to-end (live demo, not slides)
- [ ] **AWS Builder ID** — free signup, required regardless of which model
      provider you actually used to build
- [ ] Track selected: **Professional Agents**
- [ ] (Optional) Live demo link
- [ ] (Optional bonus) Build-story post on builder.aws.com mentioning
      "Agents for Humans" in the title

## Demo script (suggested, fits in ~3 min)

1. One line on the problem: contracts silently auto-renew with price hikes
   and nobody re-reads the fine print in time.
2. Run `python -m contract_watchdog.main` live, on camera.
3. While it runs, narrate: it's loading contracts across types (SaaS,
   lease, NDA), checking which ones have a notice deadline coming up,
   analyzing each for price changes and risky language.
4. Show the terminal summary output.
5. Open `outbox/pending_decisions.jsonl` — show it only flagged the
   contracts that actually needed a human, not all five.
6. Show one of the drafted emails (via the agent's tool calls in the
   transcript, or re-run with verbose logging) to prove it did real work,
   not just a summary.
7. Close on the architecture diagram for 10 seconds — one sentence on why
   only `notify_human` interrupts a person.
