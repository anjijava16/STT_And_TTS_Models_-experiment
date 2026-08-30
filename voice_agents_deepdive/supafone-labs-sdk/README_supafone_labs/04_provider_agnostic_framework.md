# 04 · Provider-Agnostic Framework

The provider-agnostic framework **is** Supafone Supervisor. It is the "supercharge" path:
it upgrades an agent the developer already runs instead of forcing them into
Supafone-hosted telephony or a hosted Supafone agent.

```python
import supafone_labs

brain = supafone_labs.supercharge(my_agent, scenario="legal_intake")
```

## What it does

1. Normalize vendor events into canonical call events.
2. Maintain deterministic runtime state (stage, consent, tool state, caller intent, risk flags).
3. Run the oracle only when supervision is enabled.
4. Emit a silent directive or provider-native action.
5. Log the decision, latency, provider, model, and billing metadata.

## The substrate problem (why this is hard)

Voice-AI serving stacks fall into three classes, each with a different (or absent) control
channel, and wire formats drift quarterly:

| Class | Examples | Injection reality |
| --- | --- | --- |
| **Speech-to-speech agents** | OpenAI Realtime, Grok Voice, Ultravox | No out-of-band channel beyond a live session patch |
| **Pipeline agents** | Vapi, Retell, ElevenLabs, Deepgram VA, Bland | Injection lands in LLM context between turns — *when a channel exists at all* |
| **Frameworks / components** | Pipecat, LiveKit; Cartesia, Inworld, raw STT | The integrator owns the loop, or nothing is injectable |

> This heterogeneity, not the oracle, is the engineering problem.

## Capability-aware injection compilation

One abstract decision compiles across **14 audited runtime integrations**:

| Runtime | Class | Native control primitive |
| --- | --- | --- |
| Supafone / Ultravox | managed / S2S | deferred `user_text_message` |
| OpenAI Realtime / Inworld Realtime | S2S | `system conversation.item.create` |
| Grok Voice | S2S | per-response `response.create.instructions` |
| Gemini Developer Live | S2S | observation only (ordinary `clientContent` is not hidden system control) |
| Vapi | pipeline | `system` add-message via live-call `controlUrl` |
| Retell (custom LLM) | pipeline | `system` message prepended to next turn |
| ElevenLabs Agents | pipeline | `contextual_update` (read, never spoken) |
| Deepgram Voice Agent | pipeline | `UpdatePrompt` (additive) |
| Pipecat | framework | `LLMMessagesAppendFrame`, `run_llm=false` |
| LiveKit Agents | framework | chat-context system append |
| Bland | pipeline | **none** — observation-only, honestly declared |
| Cartesia Line | component / agent hook | **none** until the agent handles a custom event |

### Adapter families

| Family | Members |
| --- | --- |
| Realtime agent platforms | Ultravox, Vapi, Retell, Bland |
| Realtime model APIs | OpenAI Realtime, Grok, Gemini Live |
| Voice infrastructure | LiveKit, Pipecat, Twilio media streams, SIP/generic |
| TTS/STT providers | Deepgram, Cartesia, ElevenLabs, Inworld |

Each adapter reports what it supports, including whether it can update stageful session
context directly or needs a generic prompt/message injection. The **Bland** adapter is
honest about being observe-only. An **extension path** — `GenericWebhookAdapter` — covers
proprietary systems.

## Labs must be explicit

Hosted agents and builder UI should **only** instantiate the supervisor when
`labs.enabled` is true:

```json
{ "labs": { "enabled": true, "mode": "supafone_managed", "model": "gemma" } }
```

When `labs.enabled` is false or omitted, create the agent **without** the sidecar. Do not
silently turn it on because the user selected a voice or telephony provider.

## Managed vs BYOK

**Supafone-managed mode** (the default):

```json
{ "labs": { "enabled": true, "mode": "supafone_managed", "managedInfrastructure": true } }
```

**BYOK mode** (bring your own keys):

```json
{
  "labs": {
    "enabled": true,
    "mode": "byok",
    "managedInfrastructure": false,
    "stt": { "provider": "deepgram", "model": "nova-3" },
    "llm": { "provider": "openai", "model": "gpt-4.1-mini" },
    "tts": { "provider": "elevenlabs" }
  }
}
```

### BYOK is not one thing — it has independent provisioning lanes

| Lane | Options | Notes |
| --- | --- | --- |
| Agent / provider stack | 14 audited runtime adapters | Depth ranges from managed native control to observation or an explicit host hook |
| Telephony | Twilio, Telnyx, Plivo, SignalWire, SIP/custom trunks | Carrier credentials & routing stay in the customer's account |
| TTS | Cartesia, ElevenLabs, Inworld, Deepgram, custom | Voice rendering managed or customer-owned |
| STT | Deepgram or provider-native transcript streams | **Exactly one** transcript authority per call |
| Supervisor LLM | Supafone hosted, Anthropic, OpenAI, xAI, custom | The directive model can change without replacing the speaking agent |

The framework accepts **mixed deployments** — e.g. BYOK Telnyx + managed Supervisor + BYOK
ElevenLabs; or bring Ultravox + Twilio while using Supafone only for supervision, logs, QA,
and optimizer output.

### Hosted runtime status

For Supafone's own hosted runtime, **Ultravox** is available managed or BYOK. The other
hosted runtimes (Vapi, Retell, Bland, LiveKit, Pipecat) were listed as **coming soon** at
time of writing — but the *supervision adapters* for those providers already exist. (Adapter
support and Supafone-hosted-runtime support are different claims — always check the
Framework Coverage matrix.)

---

*Next: [05_agent_factory_and_builder.md](05_agent_factory_and_builder.md)*
