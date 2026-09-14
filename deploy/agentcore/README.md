# Optional: Deploy to Bedrock AgentCore

The hackathon brief calls out AgentCore deployment as something that
"strengthens your Technical Implementation score" but is explicitly **not
required**. The CLI (`python -m contract_watchdog.main`) is a complete
submission by itself — treat this as a bonus, not a blocker.

This path also switches the model provider to Bedrock (see
`MODEL_PROVIDER` in `.env`), since AgentCore Runtime executes inside AWS.

## Install

```bash
pip install bedrock-agentcore bedrock-agentcore-starter-toolkit boto3
```

## Local smoke test

```bash
python deploy/agentcore/app.py
```

In another terminal:

```bash
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Review the contracts and handle what needs handling."}'
```

## Deploy to AWS

From the repo root:

```bash
agentcore configure --entrypoint deploy/agentcore/app.py --name contract-watchdog --region us-west-2
agentcore launch --env MODEL_PROVIDER=bedrock --env BEDROCK_MODEL_ID=global.anthropic.claude-sonnet-4-6
```

`configure` needs an execution role with `bedrock:InvokeModel` permission
for the model you're using — pass `--execution-role <arn>` or let it create
one interactively.

## Invoke the deployed agent

```bash
agentcore invoke '{"prompt": "Review the contracts and handle what needs handling."}'
agentcore status
```

## Notes

- `sample_data/contracts/` needs to ship with the deployment package (or be
  swapped for a real data source) since the default prompt points at it.
- This has **not been deployed/verified against a live AWS account** as
  part of this scaffold — the CLI/API surface above was checked against
  the installed `bedrock-agentcore` / `bedrock-agentcore-starter-toolkit`
  packages, but actual `agentcore launch` execution (container build, IAM
  role creation, runtime provisioning) has not been run. Budget time to
  debug IAM/region issues if you go this route close to the deadline.
