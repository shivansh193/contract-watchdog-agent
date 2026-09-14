"""Bedrock AgentCore entrypoint — optional deployment path.

Wraps the same Contract Watchdog agent used by src/contract_watchdog/main.py
behind a BedrockAgentCoreApp so it can run as a managed AgentCore Runtime
instead of a local CLI process. This is the "strengthen your Technical
Implementation score" path the hackathon brief mentions — it's not required
to enter, and the CLI path (`python -m contract_watchdog.main`) is a
complete, working submission on its own.

Local test:
    pip install bedrock-agentcore
    python deploy/agentcore/app.py
    # then, in another terminal:
    curl -X POST http://localhost:8080/invocations \
        -H "Content-Type: application/json" \
        -d '{"prompt": "Review the contracts and handle what needs handling."}'

Deploy: see deploy/agentcore/README.md.
"""

import sys
from pathlib import Path

from bedrock_agentcore.runtime import BedrockAgentCoreApp

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from contract_watchdog.agent import build_agent  # noqa: E402

app = BedrockAgentCoreApp()

DEFAULT_PROMPT = (
    "Review every contract in 'sample_data/contracts'. Handle what needs "
    "handling and only notify me about contracts that genuinely need a "
    "decision. Give me a short summary when you're done."
)


@app.entrypoint
def invoke(payload: dict) -> dict:
    """AgentCore invocation entrypoint. `payload` is the JSON body of the invoke request."""
    prompt = payload.get("prompt", DEFAULT_PROMPT)
    agent = build_agent()
    result = agent(prompt)
    return {"result": str(result)}


if __name__ == "__main__":
    app.run()
