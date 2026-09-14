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

## Demo script (suggested, fits in ~4 min)

1. One line on the problem: contracts silently auto-renew with price hikes
   and nobody re-reads the fine print in time.
2. Run `python -m contract_watchdog.main` live, on camera.
3. While it runs, narrate: it's loading contracts across types (SaaS,
   lease, employment, NDA), checking which ones have a notice deadline
   coming up, analyzing each for price changes and risky language.
4. Show the terminal summary output — flag that it correctly *skipped* the
   borderline contract (risky language present, but flat price and a
   distant deadline) — that's judgment, not keyword matching.
5. Switch to the [portfolio dashboard](README.md#portfolio-dashboard-frontend)
   (`npm run dev` in `frontend/`, reading the real `outbox/portfolio_snapshot.json`):
   click through the flagged contracts, show the matched risk clauses and
   drafted email, click Approve & Send, then flip to the Audit Trail tab
   to show every decision with its reasoning — all real data from the run
   you just did, not a mock.
6. **Run it a second time, live.** Show it does NOT re-notify on the
   contracts it already flagged — `check_recent_decisions` /
   `record_decision` remembering across runs is what makes "autonomous"
   real instead of "re-sends the same alert every time you run it."
7. Close on the architecture diagram for 10 seconds — one sentence on why
   only `notify_human` interrupts a person.

Cut #5-6 if you're tight on time — #1-4 alone is a complete, honest demo.
