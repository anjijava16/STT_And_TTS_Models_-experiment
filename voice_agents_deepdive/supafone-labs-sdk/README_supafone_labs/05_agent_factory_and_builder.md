# 05 · Agent Factory & Hosted Builder

Agent Factory is the "provision a complete agent" path. It collapses the usual five-key
integration (telephony + TTS + STT + LLM + supervision) into **one API key**. Supervision
is on by default for factory agents.

## Two builder modes

| Mode | Endpoint base | Purpose |
| --- | --- | --- |
| **Programmatic builder** | `https://api.supafone.ai/api/v1/labs` | TypeScript/Python/REST calls with your one `sl_live_...` key |
| **Labs Cloud test builder** | `https://api.labs.supafone.ai` (`/v1/builder/*`) | Session-scoped supervised test calls, grading, QA, optimizer feedback |

## Create an inbound agent (full example)

```typescript
import { Supafone } from "supafone-labs";

const supafone = new Supafone({ apiKey: process.env.SUPAFONE_TOKEN! });

const inbound = await supafone.labs.agents.createInbound({
  agentKey: "northline-intake",
  name: "Northline intake",
  assistantName: "Maya",
  businessName: "Northline",
  description: "Answer new inquiries, capture the facts that matter, and book or route the next step.",
  websiteUrl: "https://northline.example",
  presetKey: "general_intake_receptionist",
  runtimeMode: "multi_stage",
  labs: { enabled: true, model: "gemma" },
  tools: {
    callRouting: true,
    scheduling: true,
    sms: true,
    email: true,
    firmKnowledge: true,
    voicemail: true
  }
});

console.log(inbound.call_plan?.call_stages); // reviewed JSON now running
```

## Add a phone number in one call

```typescript
const withNumber = await supafone.labs.agents.createInboundWithNumber({
  agentKey: "northline-phone",
  name: "Northline phone intake",
  number: {
    search: { areaCode: "415" },
    numberStrategy: "default_pool"      // safe default; pooled, free
  },
  labs: { enabled: true, model: "gemma" }
});
```

Use `numberStrategy: "dedicated"` or `"premium"` **only** after the customer explicitly
chooses a paid reserved number. Don't silently upgrade a shared-pool user.

## Review before creation (approval flow)

Products that need an approval step can preview the plan, show it in their own UI, let an
operator edit it, and create from the approved JSON:

```typescript
const plan = await supafone.generateCallStages({
  direction: "inbound",
  businessName: "Northline",
  description: "Answer new inquiries, capture the facts that matter, and book or route the next step.",
  stageCount: 5,
  stageDetail: "detailed",
});

await supafone.labs.agents.createInbound({
  agentKey: "northline-intake",
  name: "Northline intake",
  callStages: plan.call_stages,
});
```

The equivalent surfaces all share one plan contract and one Supafone credential:

| Interface | Call |
| --- | --- |
| REST | `POST /api/v1/labs/agent-plans` |
| Python | `generate_call_stages()` |
| MCP | `generate_call_stages` |

## Discovery before creation

Render UI options from live inventory instead of hard-coding provider lists:

```typescript
const capabilities = await supafone.labs.capabilities();
const presets      = await supafone.labs.presets.list();
const tools        = await supafone.labs.tools.list();
const voices       = await supafone.labs.voices.list({ provider: "cartesia" });
```

## Labs Cloud test builder (supervised test turns)

Runs supervised test turns and saves config under the logged-in account. Call `login()`
first.

```typescript
await supafone.login(process.env.SM_EMAIL!, process.env.SM_PASSWORD!);

await supafone.builder.saveConfig({
  agent_prompt: "You are a warm intake agent. Never quote fees.",
  agent_label: "intake",
  framework: "ultravox",
  llm: { provider: "hosted" }
});

const turn = await supafone.builder.chat("call-1", [
  { role: "agent",  text: "Hi, how can I help?" },
  { role: "caller", text: "What do you charge? Give me a number." }
]);

console.log(turn.whisper);      // the silent directive
console.log(turn.agent_reply);  // what the agent says after coaching
```

Finish a test call to grade it and feed the optimizer:

```typescript
await supafone.builder.finish("call-1", [
  { role: "agent",   text: "Hi, how can I help?" },
  { role: "caller",  text: "What do you charge?" },
  { role: "whisper", text: "Do not quote fees; offer to connect them." },
  { role: "agent",   text: "I cannot quote fees, but I can connect you with the team." }
]);
```

## Builder Copilot Wizard

`POST /v1/builder/wizard` powers the conversational copilot: one turn takes developer prose
in and returns validated field updates out. Deterministic contract — every value is clamped
to the caller's `fields` catalog:

```http
POST https://api.labs.supafone.ai/v1/builder/wizard
Authorization: Bearer sl_live_...

{
  "message": "Outbound roofing quotes, warm tone, 415 number",
  "draft": { "direction": "" },
  "fields": [
    { "key": "direction", "label": "Direction", "type": "choice", "options": ["inbound","outbound"] },
    { "key": "agent_prompt", "label": "Prompt", "type": "text" }
  ]
}
```

Response is `{updates, reply}`. Bills one oracle call per turn (only when the model ran).

## What the builder stores (builder contract)

- agent prompt and agent label
- framework label + optional framework key
- optional BYO agent/provider-stack settings
- optional BYO telephony settings
- optional BYO TTS settings
- recording, transcription, retention, and artifact settings
- LLM provider selection
- masked secret fields on readback (blank secret in update = "keep previously saved value")

## Export parity

After a working agent is created, the builder can export the **exact same configuration**
as TypeScript, Python, REST, MCP, and JSON.

## Related capabilities (linked from docs)

Agent Factory · Call Stages · Multi-stage flows · IVR/DTMF navigation · Language routing ·
Browser WebRTC calls · Outbound campaigns (YAML "campaigns as code") · Phone numbers ·
Call recording & artifacts · Log streaming · Grounded knowledge (approved websites/docs).

---

*Next: [06_stt_tts_in_supafone.md](06_stt_tts_in_supafone.md)*
