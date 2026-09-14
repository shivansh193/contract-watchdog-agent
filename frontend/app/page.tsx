import fs from "node:fs";
import path from "node:path";
import Dashboard from "./Dashboard";
import type { AuditEntry, PortfolioSnapshot } from "./types";

const OUTBOX_DIR = path.join(process.cwd(), "..", "outbox");

function readSnapshot(): PortfolioSnapshot {
  const snapshotPath = path.join(OUTBOX_DIR, "portfolio_snapshot.json");
  if (!fs.existsSync(snapshotPath)) {
    return { generatedAt: "", contracts: [] };
  }
  return JSON.parse(fs.readFileSync(snapshotPath, "utf-8"));
}

function readAuditLog(): AuditEntry[] {
  const logPath = path.join(OUTBOX_DIR, "decision_log.jsonl");
  if (!fs.existsSync(logPath)) return [];
  return fs
    .readFileSync(logPath, "utf-8")
    .split("\n")
    .filter((line) => line.trim())
    .map((line) => {
      const entry = JSON.parse(line);
      return {
        timestamp: entry.timestamp,
        contractId: entry.contract_id,
        decision: entry.decision,
        notes: entry.notes,
      } as AuditEntry;
    })
    .sort((a, b) => b.timestamp.localeCompare(a.timestamp));
}

export default function Page() {
  const snapshot = readSnapshot();
  const auditLog = readAuditLog();

  return <Dashboard snapshot={snapshot} auditLog={auditLog} />;
}

// Always read the latest snapshot from disk instead of a build-time cache,
// since it's meant to reflect whatever the agent produced on its last run.
export const dynamic = "force-dynamic";
