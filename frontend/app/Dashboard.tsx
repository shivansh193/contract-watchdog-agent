"use client";

import { useMemo, useState } from "react";
import type { AuditEntry, ContractRecord, PortfolioSnapshot } from "./types";
import TryItYourself from "./TryItYourself";

const ACCENT = "#7a2e22";

const TYPE_LABELS: Record<string, string> = {
  vendor_saas: "Vendor / SaaS",
  lease: "Lease",
  employment: "Employment",
  nda: "NDA",
};

function typeLabel(type: string): string {
  return TYPE_LABELS[type] ?? type;
}

function formatTime(iso: string): string {
  if (!iso) return "";
  const d = new Date(iso.replace(" ", "T"));
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", second: "2-digit" });
}

function formatDate(iso: string): string {
  if (!iso) return "";
  const d = new Date(iso + "T00:00:00");
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

export default function Dashboard({
  snapshot,
  auditLog,
}: {
  snapshot: PortfolioSnapshot;
  auditLog: AuditEntry[];
}) {
  const [tab, setTab] = useState<"portfolio" | "audit" | "try">("portfolio");
  const [approved, setApproved] = useState<Record<string, boolean>>({});

  const { flagged, reviewed, flaggedCount, reviewedCount, totalMonthly, pricedCount } =
    useMemo(() => {
      const flagged = snapshot.contracts.filter((c) => c.status === "flagged");
      const reviewed = snapshot.contracts.filter((c) => c.status === "reviewed");
      const priced = snapshot.contracts.filter((c) => c.hasPrice);
      return {
        flagged,
        reviewed,
        flaggedCount: flagged.length,
        reviewedCount: reviewed.length,
        totalMonthly: priced.reduce((sum, c) => sum + c.currPrice, 0),
        pricedCount: priced.length,
      };
    }, [snapshot]);

  const [headlineLead, headlineRest] =
    flaggedCount === 0
      ? ["Nothing", " needs you this week."]
      : flaggedCount === 1
        ? ["One", " contract needs your attention this week."]
        : [String(flaggedCount), " contracts need your attention this week."];

  if (snapshot.contracts.length === 0) {
    return (
      <main className="max-w-[780px] mx-auto px-8 py-16 font-sans text-sm text-[#8a887c]">
        No portfolio snapshot found. Run the agent, then{" "}
        <code className="font-mono">python scripts/build_portfolio_snapshot.py</code>.
      </main>
    );
  }

  return (
    <main className="max-w-[780px] mx-auto px-8 pt-16 pb-24">
      <div className="flex justify-between items-baseline gap-4 flex-wrap mb-[18px]">
        <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[#8a887c]">
          Contract Watchdog
        </div>
        <div className="font-mono text-[11px] text-[#a3a196] tracking-wide">
          Generated {formatTime(snapshot.generatedAt)} &middot; {formatDate(snapshot.generatedAt.slice(0, 10))}
        </div>
      </div>

      <h1 className="font-serif font-semibold text-[44px] leading-[1.14] tracking-[-0.018em] text-[#1a1815] max-w-[600px]">
        <span style={{ color: ACCENT }}>{headlineLead}</span>
        {headlineRest}
      </h1>

      <div className="font-mono text-xs text-[#8a887c] mt-[22px] tracking-wide">
        {snapshot.contracts.length} contracts monitored &middot; ${totalMonthly.toLocaleString()}/mo across{" "}
        {pricedCount} priced agreements
      </div>

      <div className="flex gap-1 mt-10 pb-2.5 border-b border-[#e2ddd0]">
        <button
          onClick={() => setTab("portfolio")}
          className="cursor-pointer text-[13px] font-semibold px-3 pt-2 pb-2.5 -mb-[11px] border-b-2 transition-colors"
          style={{
            color: tab === "portfolio" ? "#1a1815" : "#a3a196",
            borderColor: tab === "portfolio" ? "#1a1815" : "transparent",
          }}
        >
          Portfolio
        </button>
        <button
          onClick={() => setTab("audit")}
          className="cursor-pointer text-[13px] font-semibold px-3 pt-2 pb-2.5 -mb-[11px] border-b-2 transition-colors"
          style={{
            color: tab === "audit" ? "#1a1815" : "#a3a196",
            borderColor: tab === "audit" ? "#1a1815" : "transparent",
          }}
        >
          Audit Trail
        </button>
        <button
          onClick={() => setTab("try")}
          className="cursor-pointer text-[13px] font-semibold px-3 pt-2 pb-2.5 -mb-[11px] border-b-2 transition-colors"
          style={{
            color: tab === "try" ? "#1a1815" : "#a3a196",
            borderColor: tab === "try" ? "#1a1815" : "transparent",
          }}
        >
          Try It Yourself
        </button>
      </div>

      {tab === "try" && <TryItYourself />}

      {tab === "portfolio" && (
        <div>
          {flaggedCount > 0 && (
            <div className="mt-12">
              <div className="text-[11px] font-semibold uppercase tracking-[0.12em]" style={{ color: "#9a5a12" }}>
                This week
              </div>
              {flagged.map((c, i) => (
                <FlaggedContract
                  key={c.id}
                  contract={c}
                  index={i + 1}
                  isApproved={!!approved[c.id]}
                  onApprove={() => setApproved((prev) => ({ ...prev, [c.id]: true }))}
                />
              ))}
            </div>
          )}

          <div className="mt-14">
            <div className="text-[11px] font-semibold uppercase tracking-[0.12em] text-[#8a887c]">
              Reviewed &mdash; no action needed
            </div>
            <div className="mt-4">
              {reviewed.map((c) => (
                <div key={c.id} className="flex gap-5 py-3.5 border-t border-[#ece7da] text-[13px]">
                  <div className="font-semibold text-[#4a4940] w-40 shrink-0">{c.counterparty}</div>
                  <div className="text-[#a3a196]">{c.reasoning}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {tab === "audit" && (
        <div className="bg-white border border-[#e6e2d6] rounded-sm">
          {auditLog.map((entry, i) => {
            const contract = snapshot.contracts.find((c) => c.id === entry.contractId);
            const isFlagged = entry.decision === "flagged_notified";
            return (
              <div key={i} className="flex gap-6 px-6 py-4 border-b border-[#eeebe2] last:border-b-0">
                <div className="font-mono text-[11px] text-[#a3a196] w-[84px] shrink-0 pt-0.5">
                  {formatTime(entry.timestamp)}
                </div>
                <div>
                  <div className="text-[13px]">
                    <span className="font-semibold text-[#1a1815]">
                      {contract?.counterparty ?? entry.contractId}
                    </span>
                    <span className="font-semibold" style={{ color: isFlagged ? "#9a5a12" : "#8a887c" }}>
                      {" "}
                      &mdash; {isFlagged ? "flagged" : "no action"}
                    </span>
                  </div>
                  <div className="text-[13px] text-[#8a887c] mt-1 leading-relaxed max-w-[540px]">
                    {entry.notes}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </main>
  );
}

function FlaggedContract({
  contract: c,
  index,
  isApproved,
  onApprove,
}: {
  contract: ContractRecord;
  index: number;
  isApproved: boolean;
  onApprove: () => void;
}) {
  const hasIncrease = c.hasPrice && c.pctChange > 0;

  return (
    <div className="flex gap-5 mt-9 pt-9 border-t border-[#e2ddd0]">
      <div
        className="font-serif font-light text-[36px] leading-none w-11 shrink-0"
        style={{ color: ACCENT, opacity: 0.55 }}
      >
        {String(index).padStart(2, "0")}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex justify-between items-baseline gap-4 flex-wrap">
          <div className="font-serif text-[23px] font-semibold text-[#1a1815]">{c.counterparty}</div>
          {c.urgency && (
            <div className="text-[11px] font-semibold uppercase tracking-wide" style={{ color: "#9a5a12" }}>
              {c.urgency} urgency
            </div>
          )}
        </div>
        <div className="text-[13px] text-[#8a887c] mt-[3px]">
          {typeLabel(c.type)} &middot; {c.description}
        </div>

        {c.reasoning && (
          <div
            className="font-serif italic text-[17px] leading-[1.55] text-[#3a3833] pl-[18px] mt-5 max-w-[560px] border-l-2"
            style={{ borderColor: ACCENT }}
          >
            {c.reasoning}
          </div>
        )}

        <div className="font-mono text-[11px] tracking-wide text-[#a3a196] mt-5">
          renewal {formatDate(c.renewalDate)} &middot; notice {c.noticeDeadline ? formatDate(c.noticeDeadline) : "—"} (
          {c.daysUntil}d)
          {hasIncrease && (
            <>
              {" "}
              &middot; ${c.prevPrice}&rarr;${c.currPrice}/mo ({c.pctChange}%)
            </>
          )}
        </div>

        {c.risks.length > 0 && (
          <div className="mt-[22px] space-y-2">
            {c.risks.map((r, i) => (
              <div key={i} className="text-[13px] py-2 border-t border-[#ece7da]">
                <span className="italic text-[#3a3833]">&ldquo;{r.phrase}&rdquo;</span>
                <span className="text-[#8a887c]"> &mdash; {r.reason}</span>
              </div>
            ))}
          </div>
        )}

        {c.hasEmail && (
          <div className="mt-6 pt-6 border-t border-[#eeebe2] pl-[18px] border-l-2 border-l-[#e2ddd0]">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-[#a3a196] mb-2.5">
              Drafted response
            </div>
            <div className="text-[13px] font-semibold text-[#1a1815] mb-2">{c.emailSubject}</div>
            <div className="font-serif text-sm text-[#4a4940] leading-[1.65] whitespace-pre-line">
              {c.emailBody}
            </div>
            <div className="mt-4">
              {isApproved ? (
                <div className="text-[13px] font-semibold" style={{ color: "#4a6b4a" }}>
                  &#10003;&nbsp; Approved, queued to send
                </div>
              ) : (
                <button
                  onClick={onApprove}
                  className="cursor-pointer text-[13px] font-semibold px-3 py-2 -mx-3 -my-2 hover:opacity-70 transition-opacity"
                  style={{ color: ACCENT }}
                >
                  Approve &amp; send &nbsp;&rarr;
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
