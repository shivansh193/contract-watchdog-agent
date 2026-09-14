# Contract Watchdog — Portfolio Dashboard

A Next.js dashboard for the Contract Watchdog agent's real output: flagged
vs. reviewed contracts, matched risk clauses, drafted renegotiation
emails, and a full audit trail of every decision the agent made.

## How it's wired

`app/page.tsx` is a React Server Component that reads
`../outbox/portfolio_snapshot.json` and `../outbox/decision_log.jsonl`
directly off disk on every request (`export const dynamic =
"force-dynamic"` — no build-time caching). There's no API layer and no
mock data: it's the real output of the agent's last run, joined with
deterministic risk/price analysis by `../scripts/build_portfolio_snapshot.py`.

## Running it

From the repo root, after the agent has run at least once:

```bash
python -m contract_watchdog.main            # produces outbox/*.jsonl
python scripts/build_portfolio_snapshot.py   # produces outbox/portfolio_snapshot.json
```

Then, from this directory:

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

Re-run the two Python commands above any time you want the dashboard to
reflect a fresh agent run — just refresh the page, no restart needed.

## Structure

```
frontend/
├── app/
│   ├── page.tsx       # server component: reads outbox/ off disk
│   ├── Dashboard.tsx  # client component: tabs, Approve & Send state
│   ├── types.ts        # shared TypeScript types for the snapshot
│   ├── layout.tsx      # fonts (Spectral / IBM Plex Sans / IBM Plex Mono)
│   └── globals.css
```
