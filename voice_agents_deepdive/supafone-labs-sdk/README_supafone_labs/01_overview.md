# 01 · Overview — What Supafone Labs Is

## The core insight

> A voice demo can be assembled quickly. A dependable voice product cannot.

A production voice agent is split across a realtime model, telephony, TTS, STT, tools,
retrieval, state, recordings, compliance, monitoring, and post-call workflows. Every
vendor exposes a **different event format**, and the speaking model is still expected to
notice and correct its own mistakes *while talking*.

Supafone Labs is built around the failures that appear at those boundaries.

## The problems it targets

| Production problem | Supafone's answer |
| --- | --- |
| The speaking agent must supervise itself | A live supervisor runs *beside* the call and issues one bounded directive only when evidence is strong |
| Every voice platform has different events/controls | A canonical runtime + 14 audited adapters normalize events and compile guidance into each platform's native control |
| Prompts make claims tools never confirmed | "Truth state" tracks verified bookings, transfers, deliveries, consent, and failures separately from model language |
| Every new agent is another prompt-engineering project | Agent Factory turns a job description into editable stages, tools, routing, numbers, voices, artifacts |
| Testing is manual role-play | Adversarial QA + SSR grading generate scenarios and compare supervised vs unsupervised behavior |
| Calls disappear into provider dashboards | Durable activity APIs retain agents, plans, calls, recordings, transcripts, supervision events, outcomes |
| Multilingual calls lose context or wrong voice | Language-aware transcription + opt-in language/voice profiles preserve the workflow while the language changes |
| Phone, WebRTC, SMS, campaigns, signing are separate systems | One SDK + one account model connect delivery, messaging, campaigns, artifacts, writebacks |

## Two ways to use the package

### 1. Supervise an agent you already run ("supercharge")

```python
import supafone_labs

supervisor = supafone_labs.supercharge(my_agent)
result = await supervisor.observe(provider_event)
```

The package auto-detects supported agents, normalizes their events, and returns the
provider-appropriate action. **This is the defining product** — it works even when
Supafone did not create the agent.

### 2. Provision the complete agent ("Agent Factory")

```typescript
import { Supafone } from "supafone-labs";

const supafone = new Supafone({ apiKey: process.env.SUPAFONE_TOKEN! });

const agent = await supafone.labs.agents.createInboundWithNumber({
  agentKey: "northline-intake",
  name: "Northline intake",
  description: "Understand the request and book the right next step.",
  number: { search: { areaCode: "415" } },
});
```

Agent Factory adds the plan, number, voice, stages, tools, call artifacts, and live
supervision. You can inspect and edit the generated plan before creation.

## Who it's for

- **Teams that already run a voice stack** (Vapi/Retell/OpenAI Realtime/etc.) and want
  reliability + QA + telemetry *without ripping out their provider*.
- **Builders who want a complete agent fast** — one key instead of a five-key integration
  (telephony + TTS + STT + LLM + supervision).
- **Product teams** needing multilingual continuity, provider switching, safety policy,
  and auditable call evidence.

## Package surfaces

| Surface | Use it for |
| --- | --- |
| **Python** | Local runtime, adapters, replay, supervision, STT/TTS components, backend automation |
| **TypeScript** | Node, React, browser, Agent Factory, campaigns, activity, product integrations |
| **REST + WebSocket** | Hosted agents, realtime services, events, recordings, transcripts, custom clients |
| **MCP** | Agent creation, calls, QA, logs, and operational workflows from AI dev tools |

## Positioning vs. the rest of this workspace

The parent `deep_dive_notes` folder studies STT, TTS, and the STT→LLM→TTS pipeline in the
abstract. Supafone Labs is a concrete, opinionated implementation of *everything around*
that pipeline — plus a novel supervision layer the generic pipeline notes don't cover. See
[06_stt_tts_in_supafone.md](06_stt_tts_in_supafone.md) for the direct STT/TTS mapping.

---

*Next: [02_architecture_sidecar_oracle.md](02_architecture_sidecar_oracle.md)*
