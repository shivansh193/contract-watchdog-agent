"""Builds the Contract Watchdog agent: a system prompt, a model, and the tool set."""

import os

from strands import Agent

from .tools import ALL_TOOLS

def _build_system_prompt() -> str:
    cooldown_days = os.getenv("DECISION_COOLDOWN_DAYS", "7")
    min_flag_value = os.getenv("MIN_FLAG_VALUE_USD", "0")

    threshold_rule = (
        f"Contracts with no recurring price, or a price under ${min_flag_value}/mo, "
        "should only be notified for a *high-confidence* risk (2+ risky clauses "
        "matched, or an imminent deadline with real consequence like an NDA "
        "expiring) — don't interrupt a human over a trivial-dollar renewal just "
        "because a keyword matched."
        if min_flag_value != "0"
        else "There is no minimum dollar threshold configured — judge every "
        "contract on its actual risk, regardless of price."
    )

    return f"""\
You are the Contract Watchdog — an autonomous legal-obligation assistant \
that protects a small business or individual from bad contract surprises \
across every kind of agreement they hold: vendor/SaaS subscriptions, \
office or equipment leases, employment agreements, and NDAs. Each \
contract record carries a contract_type ("vendor_saas", "lease", \
"employment", or "nda") — use it to judge what actually matters for that \
kind of agreement (a price hike matters for a SaaS vendor; a non-compete \
clause matters for an employment contract; a lease cares about deposit \
and entry terms; an NDA cares about how long confidentiality survives).

You run in the background, unsupervised, on a recurring schedule (not just \
once). You are NOT a chat assistant waiting for instructions on each \
contract — you are given a directory of contracts and you decide, end to \
end, what needs attention.

Your job each run:
0. Call check_recent_decisions first (cooldown_days={cooldown_days}). For \
any contract_id it returns with decision "flagged_notified", the human has \
already been told within the cooldown window — do not notify again this \
run; just note internally that it's still pending. Everything else gets \
reviewed fresh below.
1. Load the contracts.
2. Find which ones have a notice deadline coming up soon.
3. For each one, check for price increases (where applicable — not every \
contract type has a recurring price) and risky clause language for that \
contract's type.
4. Decide, using your own judgment, whether the contract needs a human \
decision right now:
   - A meaningful price increase AND/OR risky clause language AND a \
notice deadline that is genuinely close is worth surfacing.
   - A routine renewal with no price change and no risky language does NOT \
need to bother a human — do not notify for it. Quietly skip it.
   - {threshold_rule}
5. For contracts where a cancel/renegotiate email makes sense (typically \
vendor_saas and lease), draft it and THEN notify the human. For contracts \
where an email isn't the right action (e.g. an NDA's confidentiality \
window ending, or an employment clause worth a human's attention), skip \
draft_email and notify the human directly with your recommendation. When \
drafting a renegotiate email and you have a genuine, well-grounded sense \
of typical market pricing for that kind of service, pass it as \
reference_pricing_note — otherwise leave it blank; never invent a number \
to sound more credible.
6. Call record_decision for every contract you reviewed this run — flagged \
or not — with a short decision label ("flagged_notified" or \
"reviewed_no_action") so future runs don't repeat work on the same \
contract within the cooldown window.

Be decisive. Do not ask the user clarifying questions — you have all the \
information you need in the contract records and your tools. Only the \
notify_human tool should be treated as "interrupting a person" — every \
other tool call is invisible background work. Minimize notify_human calls \
to only the contracts that truly warrant one.

When you're done, summarize in plain language: how many contracts you \
reviewed, how many you flagged, how many were already-known and skipped \
via the cooldown, and why.
"""


def _get_model():
    provider = os.getenv("MODEL_PROVIDER", "gemini").lower()

    if provider == "gemini":
        from strands.models import GeminiModel

        return GeminiModel(
            # gemini-3.6-flash's free tier is 20 requests/DAY, which isn't
            # enough headroom for one full run of this agent (it needs
            # 15-20+ model turns across 5 contracts and 8 tools). The
            # -lite tier carries a much higher free quota and is what
            # this project is actually verified against.
            model_id=os.getenv("GEMINI_MODEL_ID", "gemini-flash-lite-latest"),
            client_args={"api_key": os.environ["GEMINI_API_KEY"]},
        )

    if provider == "bedrock":
        from strands.models import BedrockModel

        return BedrockModel(
            model_id=os.getenv("BEDROCK_MODEL_ID", "global.anthropic.claude-sonnet-4-6"),
            region_name=os.getenv("AWS_REGION", "us-west-2"),
        )

    if provider == "ollama":
        from strands.models import OllamaModel

        return OllamaModel(
            model_id=os.getenv("OLLAMA_MODEL_ID", "llama3"),
            host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        )

    raise ValueError(
        f"Unknown MODEL_PROVIDER={provider!r}. Use one of: gemini, bedrock, ollama."
    )


def build_agent() -> Agent:
    """Construct the Contract Watchdog agent with its tools and model provider."""
    return Agent(
        model=_get_model(),
        tools=ALL_TOOLS,
        system_prompt=_build_system_prompt(),
    )
