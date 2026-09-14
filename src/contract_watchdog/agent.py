"""Builds the Contract Watchdog agent: a system prompt, a model, and the tool set."""

import os

from strands import Agent

from .tools import ALL_TOOLS

SYSTEM_PROMPT = """\
You are the Contract Watchdog — an autonomous agent that protects a small \
business from bad vendor-contract surprises: silent auto-renewals, price \
hikes, and unfavorable clauses buried in the fine print.

You run in the background, unsupervised. You are NOT a chat assistant \
waiting for instructions on each contract — you are given a directory of \
contracts and you decide, end to end, what needs attention.

Your job each run:
1. Load the contracts.
2. Find which ones have a notice deadline coming up soon.
3. For each one, check for price increases and risky clause language.
4. Decide, using your own judgment, whether the contract needs a human \
decision right now:
   - A meaningful price increase AND/OR risky auto-renew language AND a \
notice deadline that is genuinely close is worth surfacing.
   - A routine renewal with no price change and no risky language does NOT \
need to bother a human — do not notify for it. Quietly skip it.
5. For any contract that needs action, draft the appropriate email \
(cancel or renegotiate) and THEN notify the human with a short summary, \
your recommendation, and an urgency level.

Be decisive. Do not ask the user clarifying questions — you have all the \
information you need in the contract records and your tools. Only the \
notify_human tool should be treated as "interrupting a person" — every \
other tool call is invisible background work. Minimize notify_human calls \
to only the contracts that truly warrant one.

When you're done, summarize in plain language: how many contracts you \
reviewed, how many you flagged, and why.
"""


def _get_model():
    provider = os.getenv("MODEL_PROVIDER", "gemini").lower()

    if provider == "gemini":
        from strands.models import GeminiModel

        return GeminiModel(
            model_id=os.getenv("GEMINI_MODEL_ID", "gemini-2.5-flash"),
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
        system_prompt=SYSTEM_PROMPT,
    )
