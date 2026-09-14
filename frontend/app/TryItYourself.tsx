"use client";

import { useMemo, useState } from "react";
import { CONTRACT_TYPE_OPTIONS, SAMPLE_CONTRACTS, scanForRisks } from "./riskPhrases";

const ACCENT = "#7a2e22";

export default function TryItYourself() {
  const [excerpt, setExcerpt] = useState(SAMPLE_CONTRACTS[0].excerpt);
  const [contractType, setContractType] = useState(SAMPLE_CONTRACTS[0].type);
  const [apiKey, setApiKey] = useState("");
  const [aiReasoning, setAiReasoning] = useState<string | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);

  const risks = useMemo(() => scanForRisks(excerpt, contractType), [excerpt, contractType]);

  function randomize() {
    const sample = SAMPLE_CONTRACTS[Math.floor(Math.random() * SAMPLE_CONTRACTS.length)];
    setExcerpt(sample.excerpt);
    setContractType(sample.type);
    setAiReasoning(null);
    setAiError(null);
  }

  async function getAiRead() {
    if (!apiKey.trim() || !excerpt.trim()) return;
    setAiLoading(true);
    setAiError(null);
    setAiReasoning(null);
    try {
      const res = await fetch(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent",
        {
          method: "POST",
          headers: { "Content-Type": "application/json", "x-goog-api-key": apiKey.trim() },
          body: JSON.stringify({
            systemInstruction: {
              parts: [
                {
                  text: "You are the Contract Watchdog agent. Given a contract excerpt, give a 2-3 sentence plain-language read on whether it contains terms a business owner should be concerned about, and why. Be direct and specific to the actual text, not generic. Do not invent facts not in the excerpt.",
                },
              ],
            },
            contents: [
              {
                role: "user",
                parts: [{ text: `Contract type: ${contractType}\n\nExcerpt:\n${excerpt}` }],
              },
            ],
          }),
        }
      );

      if (!res.ok) {
        const body = await res.text();
        throw new Error(`${res.status} ${res.statusText}: ${body.slice(0, 200)}`);
      }

      const data = await res.json();
      const text = data?.candidates?.[0]?.content?.parts?.[0]?.text ?? "No response text returned.";
      setAiReasoning(text);
    } catch (err) {
      setAiError(err instanceof Error ? err.message : "Request failed.");
    } finally {
      setAiLoading(false);
    }
  }

  return (
    <div className="mt-4">
      <div className="text-[13px] text-[#8a887c] max-w-[560px] leading-relaxed">
        Paste a contract excerpt, or randomize an example. The risk scan below runs the exact
        same phrase-matching logic as the real agent, live, in your browser. Add your own free{" "}
        <a
          href="https://aistudio.google.com/apikey"
          target="_blank"
          rel="noreferrer"
          className="underline"
          style={{ color: ACCENT }}
        >
          Gemini API key
        </a>{" "}
        to also get an AI read — it's used directly from your browser to Google, never sent to or
        stored on this site.
      </div>

      <div className="flex gap-3 items-center mt-5 flex-wrap">
        <button
          onClick={randomize}
          className="cursor-pointer text-[13px] font-semibold px-3 py-2 border rounded-sm hover:bg-[#f7f5f0] transition-colors"
          style={{ borderColor: "#d8d3c5", color: "#4a4940" }}
        >
          Randomize example →
        </button>

        <select
          value={contractType}
          onChange={(e) => setContractType(e.target.value)}
          className="text-[13px] px-2 py-2 border rounded-sm bg-white"
          style={{ borderColor: "#d8d3c5", color: "#4a4940" }}
        >
          {CONTRACT_TYPE_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      <textarea
        value={excerpt}
        onChange={(e) => setExcerpt(e.target.value)}
        rows={5}
        placeholder="Paste a contract clause or excerpt here..."
        className="w-full mt-3 p-3 text-[13px] font-serif border rounded-sm resize-y max-w-[680px]"
        style={{ borderColor: "#d8d3c5", background: "#faf8f2" }}
      />

      <div className="mt-5">
        <div className="text-[11px] font-semibold uppercase tracking-wider text-[#8a887c] mb-2">
          Risk clauses detected (live, deterministic)
        </div>
        {risks.length === 0 ? (
          <div className="text-[13px] text-[#a3a196] italic">No known risk phrases matched.</div>
        ) : (
          <div className="space-y-2">
            {risks.map((r, i) => (
              <div key={i} className="text-[13px] py-2 border-t border-[#ece7da]">
                <span className="italic text-[#3a3833]">&ldquo;{r.phrase}&rdquo;</span>
                <span className="text-[#8a887c]"> &mdash; {r.reason}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="mt-6 pt-5 border-t border-[#eeebe2] max-w-[680px]">
        <div className="text-[11px] font-semibold uppercase tracking-wider text-[#8a887c] mb-2">
          Optional: AI read (bring your own key)
        </div>
        <div className="flex gap-2 flex-wrap">
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="Paste your Gemini API key"
            className="flex-1 min-w-[220px] text-[13px] px-3 py-2 border rounded-sm font-mono"
            style={{ borderColor: "#d8d3c5" }}
          />
          <button
            onClick={getAiRead}
            disabled={!apiKey.trim() || aiLoading}
            className="cursor-pointer text-[13px] font-semibold px-4 py-2 rounded-sm text-white disabled:opacity-40 disabled:cursor-not-allowed"
            style={{ background: ACCENT }}
          >
            {aiLoading ? "Asking…" : "Get AI read"}
          </button>
        </div>

        {aiError && <div className="text-[12px] text-[#a04a3a] mt-3">{aiError}</div>}

        {aiReasoning && (
          <div
            className="font-serif italic text-[15px] leading-relaxed text-[#3a3833] mt-4 pl-4 border-l-2"
            style={{ borderColor: ACCENT }}
          >
            {aiReasoning}
          </div>
        )}
      </div>
    </div>
  );
}
