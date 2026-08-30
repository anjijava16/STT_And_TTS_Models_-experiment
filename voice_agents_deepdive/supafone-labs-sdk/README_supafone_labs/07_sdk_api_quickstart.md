# 07 · SDK / API Quickstart

Both Supafone Labs paths — hosted complete agents *and* bring-your-stack supervision —
through one key.

## 1. Install

```bash
pip install "supafone-labs[all]"     # Python
npm i supafone-labs                  # TypeScript / Node
```

## 2. Get a key (one key, both APIs)

Since 0.4.4, one `sl_` Labs key authenticates on both APIs:

- **Labs Cloud** (`api.labs.supafone.ai`) — natively
- **Product API** (`api.supafone.ai`) — via key introspection, as long as an
  `app.supafone.ai` account exists with the same email

```bash
curl -X POST https://api.labs.supafone.ai/v1/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com"}'

export SUPAFONE_TOKEN=sl_live_...   # one env var: MCP + both SDKs
```

A legacy scoped `sf_live_...` key still works for the hosted-agent surface, but the `sl_`
key already covers it — so `sl_` is the default, `sf_` is the exception.

## 3. Supervise a framework you already run

```python
import supafone_labs

brain = supafone_labs.supercharge(my_agent, scenario="legal_intake")

result = await brain.observe(raw_platform_event)

if result.actions:
    await my_agent.deliver(result.actions[0])
```

With `SUPAFONE_LABS_API_KEY=sl_live_...`, the supervisor, TTS, and STT can use Labs Cloud.
Without it, the SDK runs with your own vendor keys or offline fake providers for tests.

## 4. Create a managed Agent Factory agent

### TypeScript

```typescript
import { Supafone } from "supafone-labs";

const supafone = new Supafone({ apiKey: process.env.SUPAFONE_TOKEN! });

const agent = await supafone.labs.agents.createInboundWithNumber({
  agentKey: "northline-intake",
  name: "Northline intake",
  assistantName: "Maya",
  businessName: "Northline",
  description: "Answer new inquiries, understand the request, and book the right next step.",
  websiteUrl: "https://northline.example",
  number: { search: { areaCode: "415" }, numberStrategy: "default_pool" },
  voice: { provider: "cartesia", voiceId: "Jacqueline" },
  labs: { enabled: true, model: "gemma" },
  tools: {
    callRouting: true, scheduling: true, sms: true,
    email: true, firmKnowledge: true, voicemail: true
  }
});

console.log(agent.agent.agent_key);
console.log(agent.number?.number.phone_number);
console.log(agent.widget?.snippet);
console.log(agent.call_plan?.call_stages);   // reviewed JSON now running
```

### Python

```python
from supafone_labs import Supafone

supafone = Supafone(api_key="sl_live_...")  # supervision on by default

agent = supafone.labs.agents.create_inbound_with_number({
    "agentKey": "northline-intake",
    "name": "Northline intake",
    "assistantName": "Maya",
    "businessName": "Northline",
    "description": "Answer new inquiries, understand the request, and book the right next step.",
    "websiteUrl": "https://northline.example",
    "number": {"search": {"areaCode": "415"}, "numberStrategy": "default_pool"},
    "voice": {"provider": "cartesia", "voiceId": "Jacqueline"},
    "labs": {"enabled": True, "model": "gemma"},
    "tools": {
        "callRouting": True, "scheduling": True, "sms": True,
        "email": True, "firmKnowledge": True, "voicemail": True,
    },
})

print(agent["agent"]["agent_key"])
print(agent.get("number", {}).get("number", {}).get("phone_number"))
print(agent["call_plan"]["call_stages"])
```

One description is enough for the default hosted planner to write the agent-wide prompt and
a validated five-stage flow. Preview first with
`generateCallStages()` / `generate_call_stages()`, edit the JSON, or pass an explicit stage
array. Supafone's model credential stays on the server.

## 5. Check balance and logs

```bash
curl https://api.labs.supafone.ai/v1/billing/balance \
  -H "Authorization: Bearer $SUPAFONE_TOKEN"

curl https://api.labs.supafone.ai/v1/logs?limit=20 \
  -H "Authorization: Bearer $SUPAFONE_TOKEN"
```

## 6. Smoke-test hosted agents

```bash
cd supafone-labs
SUPAFONE_API_KEY=sl_live_... \
SUPAFONE_API_BASE_URL=https://api.supafone.ai \
npx tsx examples/smoke-hosted-agent.ts
```

Checks capabilities, presets, voices, agent creation, fetch-by-key, managed providers,
no-required-dev-provider-keys, and a web widget snippet.

## Surfaces & parity

| Surface | Package / endpoint |
| --- | --- |
| Python | [pypi.org/project/supafone-labs](https://pypi.org/project/supafone-labs/) |
| TypeScript | [npmjs.com/package/supafone-labs](https://www.npmjs.com/package/supafone-labs) |
| REST + WebSocket | `https://api.labs.supafone.ai` / `https://api.supafone.ai` |
| MCP | agent creation, calls, QA, logs from AI dev tools |
| API reference | [api.labs.supafone.ai/docs](https://api.labs.supafone.ai/docs) |

All four interfaces share one plan contract and one credential. Naming differs by idiom
(TS camelCase `createInbound`, Python snake_case `create_inbound_with_number`, MCP tool
names like `generate_call_stages`).

## Recommended reading order (from the docs "Start here")

1. Read the production problems
2. Follow the quickstart
3. Understand Supafone Supervisor
4. Review all supported frameworks
5. Install the Python or TypeScript SDK
6. Choose managed delivery or BYOK
7. Run the voice-agent QA workflow

---

*Next: [08_pricing_and_credits.md](08_pricing_and_credits.md)*
